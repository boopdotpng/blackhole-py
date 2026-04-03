from profiler.profiler import build_programs_info, collect

import json, os, shutil, tempfile
from pathlib import Path

from hw import TensixL1


class DeviceProfiler:
  """Manages profiler state and data collection for a Device."""

  def __init__(self, cores):
    self.last_profile = None
    self._accumulated = []
    self._disasm_dir = None
    sorted_cores = sorted(cores, key=lambda xy: (xy[0], xy[1]))
    self.flat_ids = {core: i for i, core in enumerate(sorted_cores)}

  def collect_data(self, programs, cores, cq_hw, harvested_dram_banks):
    programs_info = build_programs_info(programs, cores)
    if not programs_info: return
    needed = sorted({c for info in programs_info for c in info["cores"]})
    ctrl_regs = {}
    for core in needed:
      from dispatch import TLBWindow
      with TLBWindow(cq_hw.dev, start=core) as win:
        ctrl_regs[core] = bytes(win.mm[TensixL1.PROFILER_CONTROL : TensixL1.PROFILER_CONTROL + 128])
    batch = collect(
      programs_info,
      cq_hw.read_profiler_data(),
      ctrl_regs,
      layout={"flat_ids": self.flat_ids},
      harvested_dram_bank=harvested_dram_banks[0] if harvested_dram_banks else None,
    )
    self._accumulated.extend(batch.get("programs", []))

  def finalize(self, harvested_dram_banks, tensix_x, prefetch_core, dispatch_core):
    if not self._accumulated: return
    if self._disasm_dir:
      shutil.rmtree(self._disasm_dir, ignore_errors=True)
      self._disasm_dir = None
    for i, prog in enumerate(self._accumulated):
      prog["index"] = i
    self._disasm_dir = tempfile.mkdtemp(prefix="bh-prof-disasm-")
    for prog in self._accumulated:
      prog_dir = Path(self._disasm_dir) / f"program-{prog['index']}"
      disassembly = prog.pop("disassembly", None) or {}
      prog["has_disassembly"] = bool(disassembly)
      if disassembly:
        out_dir = prog_dir / "global"
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, text in disassembly.items():
          (out_dir / f"{name}.S").write_text(text)
      for core_key, profile in prog["profiles"].items():
        core_disassembly = profile.pop("disassembly", None) or {}
        profile["has_disassembly"] = bool(core_disassembly)
        if core_disassembly:
          out_dir = prog_dir / "cores" / core_key.replace(",", "-")
          out_dir.mkdir(parents=True, exist_ok=True)
          for name, text in core_disassembly.items():
            (out_dir / f"{name}.S").write_text(text)
    self.last_profile = {
      "dispatch_mode": "fast",
      "harvested_dram_bank": harvested_dram_banks[0] if harvested_dram_banks else None,
      "tensix_x": list(tensix_x),
      "dispatch_cores": [list(prefetch_core), list(dispatch_core)],
      "programs": self._accumulated,
    }
    self._accumulated = []

  def serve(self, port: int = int(os.environ.get("PORT", 8000))):
    if os.environ.get("PROFILE_JSON"):
      path = os.environ["PROFILE_JSON"]
      with open(path, "w") as f: json.dump(self.last_profile, f)
      print(f"profiler data written to {path}")
      return
    from profiler import ui as profiler_ui
    profiler_ui.serve(self.last_profile, port=port, disasm_dir=self._disasm_dir)

  def close(self):
    if self._disasm_dir:
      shutil.rmtree(self._disasm_dir, ignore_errors=True)
      self._disasm_dir = None
