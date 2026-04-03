import functools, os, shutil, struct, tempfile, time
from pathlib import Path
from dataclasses import dataclass


from hw import *
from hw import worker_cores as _worker_cores
from pcie import PCIDevice
from dispatch import *
from cq import *
from dram import DramBuffer, Allocator, Shape, tilize, untilize, build_transfer_program

@dataclass(frozen=True)
class BoardConfig:
  tensix_x: tuple[int, ...]
  prefetch: tuple[int, int]
  dispatch: tuple[int, int]

P100 = BoardConfig(
  tensix_x=(*range(1, 8), *range(10, 15)),
  prefetch=(14, 2),
  dispatch=(14, 3),
)
P150 = BoardConfig(
  tensix_x=(*range(1, 8), *range(10, 17)),
  prefetch=(16, 2),
  dispatch=(16, 3),
)
_BOARDS = {"p100": P100, "p150": P150}
ARC_CSM_BASE = 0x10000000
ARC_CSM_SIZE = 1 << 19


def _is_range_within_arc_csm(addr: int, length: int = 1) -> bool:
  return ARC_CSM_BASE <= addr <= (ARC_CSM_BASE + ARC_CSM_SIZE) - length

class Device:
  @functools.cached_property
  def cores(self) -> list[Core]:
    if self._use_fast_dispatch:
      return [c for c in self._all_worker_cores if c not in self._CQ_CORES]
    return list(self._all_worker_cores)

  def __init__(self, device: int | None = None):
    if device is None:
      device = int(os.getenv("DEV", "0"))
    self.device = device
    self.dev = PCIDevice(index=device)

    gddr_enabled, tensix_enabled = self._read_arc_enabled_masks()
    core_count = active_tensix_core_count(tensix_enabled)
    if core_count <= 120:
      self.board = "p100"
    elif core_count <= 140:
      self.board = "p150"
    else:
      self.dev.close()
      raise SystemExit(f"unsupported tensix core count {core_count}")
    self.arch = self.board
    print(f"device {self.device}: {self.board} ({core_count} cores, bdf={self.dev.bdf})")
    self._core_layout = self.board
    board = _BOARDS[self._core_layout]
    self._tensix_x = board.tensix_x
    self._all_worker_cores = _worker_cores(self._tensix_x)
    self._PREFETCH_CORE = board.prefetch
    self._DISPATCH_CORE = board.dispatch
    self._CQ_CORES = {self._PREFETCH_CORE, self._DISPATCH_CORE}

    self._init_dram_tiles(gddr_enabled)
    self._num_dram_banks = Dram.BANK_COUNT - len(self.harvested_dram_banks)
    self._num_l1_banks = len(self._all_worker_cores)
    self.dram = Allocator(self.dev, self.dram_tiles)
    self._dispatch_mode = DevMsgs.DISPATCH_MODE_HOST if USE_USB_DISPATCH else DevMsgs.DISPATCH_MODE_DEV
    self._use_fast_dispatch = not USE_USB_DISPATCH

    from compiler import Compiler
    self.compiler = Compiler(
      num_dram_banks=self._num_dram_banks,
      num_l1_banks=self._num_l1_banks,
      prefetch_core=self._PREFETCH_CORE,
      dispatch_core=self._DISPATCH_CORE,
    )
    self._upload_firmware()

    self._dram_sysmem = Sysmem(self.dev) if self._use_fast_dispatch else None
    self.cq = CommandQueue()
    self._cq_hw = None
    if self._use_fast_dispatch:
      from compiler import PROFILER
      profiler_cores = len(self._all_worker_cores) - len(self._CQ_CORES) if PROFILER else 0
      self._cq_hw = CQSysmem(
        self.dev,
        prefetch_win=TLBWindow(self.dev, start=self._PREFETCH_CORE),
        dispatch_win=TLBWindow(self.dev, start=self._DISPATCH_CORE),
        profiler_cores=profiler_cores,
      )
      self._start_dispatch_cores()

    self._programs = []
    self.last_profile = None
    self._profile_accumulated = []  # collect profiler data across multiple run() calls

    from compiler import PROFILER
    self._profiler = PROFILER and self._use_fast_dispatch
    self._profiler_flat_ids = {}
    if self._profiler:
      self._init_profiler_layout()

  def _read_arc_enabled_masks(self) -> tuple[int, int]:
    table_base = self.dev.read_arc_apb32(Arc.SCRATCH_RAM_13)
    data_base = self.dev.read_arc_apb32(Arc.SCRATCH_RAM_12)
    if not _is_range_within_arc_csm(table_base) or not _is_range_within_arc_csm(data_base):
      raise RuntimeError(f"ARC not ready: telemetry pointers table=0x{table_base:x} data=0x{data_base:x}")

    tlb = self.dev.alloc_tlb(TLBWindow.SIZE_2M)
    try:
      def _rd(addr):
        return self.dev._read_arc_noc32(addr, tlb=tlb)
      entry_count = _rd(table_base + 4)
      if entry_count in (0, 0xFFFFFFFF) or entry_count > 4096:
        raise RuntimeError(f"invalid ARC telemetry entry_count 0x{entry_count:x} at 0x{table_base:x}")
      tag_to_offset = {}
      for i in range(entry_count):
        tag_offset = _rd(table_base + 8 + i * 4)
        tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF
      off = tag_to_offset.get(Arc.TAG_TENSIX_ENABLED_COL)
      tensix_enabled = Arc.DEFAULT_TENSIX_ENABLED if off is None else _rd(data_base + off * 4)
      off = tag_to_offset.get(Arc.TAG_GDDR_ENABLED)
      gddr_enabled = Arc.DEFAULT_GDDR_ENABLED if off is None else _rd(data_base + off * 4)
    finally:
      self.dev.free_tlb(tlb)
    return gddr_enabled, tensix_enabled

  def _init_dram_tiles(self, gddr_enabled: int):
    harvested = [bank for bank in range(Dram.BANK_COUNT) if ((gddr_enabled >> bank) & 1) == 0]
    self.harvested_dram_banks = harvested
    harvested_set = set(harvested)
    self.dram_tiles = [
      (bank, Dram.BANK_X[bank], y)
      for bank in range(Dram.BANK_COUNT)
      if bank not in harvested_set
      for y in Dram.BANK_TILE_YS[bank]
    ]

  def _set_power(self, busy: bool):
    self.dev.set_power_state(busy)

  def _halt_cores(self, cores: list[Core]):
    mmio_base, _ = align_down(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TLBWindow.SIZE_2M)
    reset_off = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - mmio_base
    with TLBWindow(self.dev, start=cores[0], addr=mmio_base) as win:
      for core in cores:
        win.target(core, addr=mmio_base)
        win.write32(reset_off, TensixMMIO.SOFT_RESET_ALL)

  def _upload_firmware(self):
    fw = self.compiler._fw
    mmio_base, mmio_off = align_down(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TLBWindow.SIZE_2M)
    reset_off = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - mmio_base
    staged = {}
    for name, cfw in fw.items():
      scratch = cfw.scratch_base
      spans = []
      for s in cfw.segments:
        if not s.data and s.memsz == 0:
          continue
        data = s.data if s.memsz <= len(s.data) else s.data + b"\0" * (s.memsz - len(s.data))
        addr = s.paddr
        if TensixMMIO.LOCAL_RAM_START <= addr <= TensixMMIO.LOCAL_RAM_END:
          addr = scratch + (addr - TensixMMIO.LOCAL_RAM_START)
        assert 0 <= addr < TensixL1.SIZE, f"{name}: bad paddr 0x{s.paddr:x} -> 0x{addr:x}"
        spans.append((addr, data))
      staged[name] = spans

    brisc_base = TensixL1.BRISC_FIRMWARE_BASE
    jal = ((brisc_base & 0xFF000) | ((brisc_base & 0x800) << 9) | ((brisc_base & 0x7FE) << 20) | 0x6F).to_bytes(4, "little")
    go_init = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_INIT)
    all_cores = list(self._all_worker_cores)
    bank_table = build_bank_noc_table(self.harvested_dram_banks, all_cores)

    rects = mcast_rects(all_cores)
    # UC for MMIO/polling; WC for bulk L1 writes.
    with TLBWindow(self.dev, start=all_cores[0]) as uc, \
         TLBWindow(self.dev, start=all_cores[0], wc=True) as wc:
      # assert soft reset on all cores via multicast
      for x0, x1, y0, y1 in rects:
        uc.target((x0, y0), (x1, y1), addr=mmio_base)
        uc.write32(reset_off, TensixMMIO.SOFT_RESET_ALL)

      # upload firmware segments + bootstrap to all cores via multicast
      for x0, x1, y0, y1 in rects:
        wc.target((x0, y0), (x1, y1))
        for spans in staged.values():
          for addr, data in spans:
            wc.write(addr, data)
        wc.write(0, jal)
        wc.write(TensixL1.GO_MSG, go_init)
        wc.write(TensixL1.MEM_BANK_TO_NOC_SCRATCH, bank_table)

      # drain WC writes before dependent UC MMIO updates
      wc.mm[0]

      # set subordinate reset PCs on all cores via multicast
      for x0, x1, y0, y1 in rects:
        uc.target((x0, y0), (x1, y1), addr=mmio_base)
        for reg, text_base in [
          (TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, fw["ncrisc"].text_base),
          (TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, fw["trisc0"].text_base),
          (TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, fw["trisc1"].text_base),
          (TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, fw["trisc2"].text_base),
        ]:
          uc.write32(reg - mmio_base, text_base)

      # release BRISC from reset on all cores via multicast
      for x0, x1, y0, y1 in rects:
        uc.target((x0, y0), (x1, y1), addr=mmio_base)
        uc.write32(reset_off, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)

      probe = (1, 2) if (1, 2) in all_cores else all_cores[0]
      uc.target(probe)
      deadline = time.perf_counter() + 2.0
      polls = 0
      while uc.mm[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
        polls += 1
        if time.perf_counter() > deadline:
          for off in [0, 4, TensixL1.GO_MSG, TensixL1.GO_MSG+4]:
            v = uc.read32(off)
            print(f"  fw: L1[0x{off:x}] = 0x{v:08x}")
          raise TimeoutError(f"firmware not ready on {probe} -- try tt-smi -r")
        time.sleep(0.001)

  def _start_dispatch_cores(self):
    cq_kernels = self.compiler.compile_cq_kernels()

    kernel_off = L1_ALIGN + 2 * L1_ALIGN
    pref_img = b"\0" * L1_ALIGN + struct.pack("<I", CQ_DISPATCH_CB_PAGES).ljust(L1_ALIGN, b"\0") + b"\0" * L1_ALIGN
    pref_launch = self._build_cq_launch(kernel_off, 0, sem_off=L1_ALIGN)

    disp_img = b"\0" * L1_ALIGN + b"\0" * L1_ALIGN + b"\0" * L1_ALIGN
    ncrisc_off = align_up(kernel_off + len(cq_kernels["dispatch_brisc"].xip), L1_ALIGN)
    disp_launch = self._build_cq_launch(kernel_off, ncrisc_off, sem_off=L1_ALIGN)

    self._upload_cq_core(
      self._PREFETCH_CORE, pref_img, pref_launch,
      [(kernel_off, cq_kernels["prefetch_brisc"].xip)],
    )
    # init dispatch core L1 state before launching firmware
    dwin = self._cq_hw._dispatch_win
    dwin.target(self._DISPATCH_CORE)
    base_16b = self._cq_hw._completion_base_16b
    dwin.write32(CQ_COMPLETION_WR_PTR, base_16b)
    dwin.write32(CQ_COMPLETION_RD_PTR, base_16b)
    dwin.write32(CQ_COMPLETION_Q0_EVENT, 0)
    dwin.write32(CQ_COMPLETION_Q1_EVENT, 0)
    dwin.mm[CQ_DISPATCH_SYNC_SEM : CQ_DISPATCH_SYNC_SEM + 8 * L1_ALIGN] = b"\0" * (8 * L1_ALIGN)
    self._upload_cq_core(
      self._DISPATCH_CORE, disp_img, disp_launch,
      [(kernel_off, cq_kernels["dispatch_brisc"].xip),
       (ncrisc_off, cq_kernels["dispatch_s_ncrisc"].xip)],
    )

  @staticmethod
  def _build_cq_launch(brisc_text_off: int, ncrisc_text_off: int = 0, sem_off: int = 16) -> LaunchMsg:
    launch = LaunchMsg()
    kc = launch.kernel_config
    for i in range(3):
      kc.kernel_config_base[i] = TensixL1.KERNEL_CONFIG_BASE
    kc.sem_offset[0] = sem_off
    kc.rta_offset[0].rta_offset = 0
    kc.rta_offset[0].crta_offset = L1_ALIGN
    kc.kernel_text_offset[0] = brisc_text_off
    kc.kernel_text_offset[1] = ncrisc_text_off
    kc.enables = 1 | (2 if ncrisc_text_off else 0)
    kc.mode = DevMsgs.DISPATCH_MODE_HOST
    kc.local_cb_mask = 0
    kc.min_remote_cb_start_index = FAST_CQ_NUM_CIRCULAR_BUFFERS
    return launch

  def _upload_cq_core(self, core: Core, img: bytes, launch: LaunchMsg, kernels: list[tuple[int, bytes]]):
    win = self._cq_hw._prefetch_win if core == self._PREFETCH_CORE else self._cq_hw._dispatch_win
    win.target(core)
    win.write(TensixL1.KERNEL_CONFIG_BASE, img)
    for off, xip in kernels:
      win.write(TensixL1.KERNEL_CONFIG_BASE + off, xip)
    win.write(TensixL1.LAUNCH, as_bytes(launch))
    go = GoMsg()
    go.bits.signal = DevMsgs.RUN_MSG_GO
    win.write(TensixL1.GO_MSG, struct.pack("<I", go.all))

  def _go_word(self) -> int:
    go = GoMsg()
    go.bits.signal = DevMsgs.RUN_MSG_GO
    go.bits.master_x, go.bits.master_y = self._DISPATCH_CORE
    go.bits.dispatch_message_offset = 0
    return go.all

  def _init_profiler_layout(self):
    cores = sorted(self.cores, key=lambda xy: (xy[0], xy[1]))
    self._profiler_flat_ids = {core: i for i, core in enumerate(cores)}

  def _collect_profiler_data(self):
    import profiler
    programs_info = profiler.build_programs_info(self._programs, self.cores)
    if not programs_info: return
    needed = sorted({c for info in programs_info for c in info["cores"]})
    ctrl_regs = {}
    for core in needed:
      with TLBWindow(self.dev, start=core) as win:
        ctrl_regs[core] = bytes(win.mm[TensixL1.PROFILER_CONTROL : TensixL1.PROFILER_CONTROL + 128])
    batch = profiler.collect(
      programs_info,
      self._cq_hw.read_profiler_data(),
      ctrl_regs,
      layout={"flat_ids": self._profiler_flat_ids},
      harvested_dram_bank=self.harvested_dram_banks[0] if self.harvested_dram_banks else None,
    )
    self._profile_accumulated.extend(batch.get("programs", []))

  def _finalize_profile(self):
    if not self._profile_accumulated: return
    if getattr(self, "_profile_disasm_dir", None):
      shutil.rmtree(self._profile_disasm_dir, ignore_errors=True)
      self._profile_disasm_dir = None
    # re-index programs sequentially
    for i, prog in enumerate(self._profile_accumulated):
      prog["index"] = i
    self._profile_disasm_dir = tempfile.mkdtemp(prefix="bh-prof-disasm-")
    for prog in self._profile_accumulated:
      prog_dir = Path(self._profile_disasm_dir) / f"program-{prog['index']}"
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
      "harvested_dram_bank": self.harvested_dram_banks[0] if self.harvested_dram_banks else None,
      "tensix_x": list(self._tensix_x),
      "dispatch_cores": [list(self._PREFETCH_CORE), list(self._DISPATCH_CORE)],
      "programs": self._profile_accumulated,
    }
    self._profile_accumulated = []

  def alloc_write(self, data: bytes, dtype: Dtype, shape: Shape, name: str = "") -> DramBuffer:
    buf = self.dram.alloc(len(data) // dtype.tile_size, dtype, name, shape)
    self.dram_write(buf, data)
    return buf

  def _run_dram_transfer(self, buf: DramBuffer, direction: str):
    """Run a single fill/drain DMA program synchronously."""
    assert not self._programs, "queue must be empty for DRAM transfers"
    prog, _ = build_transfer_program(buf, direction, len(self.cores), self._dram_sysmem.noc_addr)
    self.queue(prog)
    self.run()

  def dram_write(self, buf: DramBuffer, data: bytes):
    assert len(data) <= buf.size
    if buf.shape is not None:
      data = tilize(data, buf.dtype.bpe, buf.shape)
    if self._use_fast_dispatch:
      assert len(data) <= self._dram_sysmem.size
      self._dram_sysmem.buf[:len(data)] = data
      self._run_dram_transfer(buf, "fill")
      return
    self.dram.write(buf, data)

  def dram_read(self, buf: DramBuffer) -> bytes:
    if self._programs:
      self.run()
    if self._use_fast_dispatch:
      assert buf.size <= self._dram_sysmem.size
      self._run_dram_transfer(buf, "drain")
      result = bytes(self._dram_sysmem.buf[:buf.size])
      if buf.shape is not None:
        return untilize(result, buf.dtype.bpe, buf.shape)
      return result
    result = self.dram.read(buf)
    if buf.shape is not None:
      return untilize(result, buf.dtype.bpe, buf.shape)
    return result

  def queue(self, program: Program): self._programs.append(program)

  def _compile_ir(self, program: Program, dispatch_mode, host_assigned_id: int = 0) -> list:
    writer = self.compiler.compile_dataflow(program.writer_kernel, "brisc") if program.writer_kernel else None
    reader = self.compiler.compile_dataflow(program.reader_kernel, "ncrisc") if program.reader_kernel else None
    compute = self.compiler.compile_compute(program.compute_kernel, program) if program.compute_kernel else None
    disassembly = {}
    if self._profiler:
      if reader is not None:
        disassembly["reader"] = self.compiler.disassemble(reader)
      if writer is not None:
        disassembly["writer"] = self.compiler.disassemble(writer)
      if compute is not None:
        for i, kernel in enumerate(compute):
          disassembly[f"trisc{i}"] = self.compiler.disassemble(kernel)
      setattr(program, "_profile_disassembly", disassembly)

    if program.grid is not None:
      rows, cols = program.grid
      grid = [[(x, y) for x in cols] for y in rows]
      all_cores = sorted([c for row in grid for c in row], key=lambda c: (c[0], c[1]))
      n = len(all_cores)
      per_core_args = [
        (resolve_args(program.writer_args, i, c, n), resolve_args(program.reader_args, i, c, n),
         resolve_args(program.compute_args, i, c, n))
        for i, c in enumerate(all_cores)
      ]
      r_recv = self.compiler.compile_dataflow(program.reader_recv_kernel, "ncrisc") if program.reader_recv_kernel else reader
      w_recv = self.compiler.compile_dataflow(program.writer_recv_kernel, "brisc") if program.writer_recv_kernel else writer
      if self._profiler and (program.reader_recv_kernel or program.writer_recv_kernel):
        core_disassembly = {}
        col_index = {x: i for i, x in enumerate(cols)}
        row_index = {y: i for i, y in enumerate(rows)}
        r_recv_disassembly = self.compiler.disassemble(r_recv) if r_recv is not None else ""
        w_recv_disassembly = self.compiler.disassemble(w_recv) if w_recv is not None else ""
        for core in all_cores:
          ds = dict(disassembly)
          if col_index[core[0]] != 0 and r_recv_disassembly:
            ds["reader"] = r_recv_disassembly
          if row_index[core[1]] != 0 and w_recv_disassembly:
            ds["writer"] = w_recv_disassembly
          core_disassembly[f"{core[0]},{core[1]}"] = ds
        setattr(program, "_profile_core_disassembly", core_disassembly)
      elif self._profiler:
        setattr(program, "_profile_core_disassembly", None)
      top_left = [grid[0][0]]
      top_row = [grid[0][c] for c in range(1, len(cols))]
      left_col = [grid[r][0] for r in range(1, len(rows))]
      interior = [grid[r][c] for r in range(1, len(rows)) for c in range(1, len(cols))]
      roles = [Role(cs, rk, wk) for cs, rk, wk in [
        (top_left, reader, writer), (top_row, r_recv, writer), (left_col, reader, w_recv), (interior, r_recv, w_recv),
      ] if cs]
    else:
      if self._profiler:
        setattr(program, "_profile_core_disassembly", None)
      cores = self.cores if program.cores == "all" else self.cores[:program.cores]
      all_cores = cores
      n = len(cores)
      per_core_args = [
        (resolve_args(program.writer_args, i, c, n), resolve_args(program.reader_args, i, c, n),
         resolve_args(program.compute_args, i, c, n))
        for i, c in enumerate(cores)
      ]
      roles = [Role(cores, reader, writer)]

    return build_ir(program, roles, compute, all_cores, per_core_args, dispatch_mode, host_assigned_id=host_assigned_id)

  def run(self):
    self._set_power(True)
    try:
      if self._use_fast_dispatch: self._run_fast_dispatch()
      else: self._run_slow_dispatch()
    finally:
      self._programs.clear()
      self._set_power(False)

  def _run_fast_dispatch(self):
    n = len(self._programs)

    programs = []
    for i, program in enumerate(self._programs):
      prof_id = (i + 1) if self._profiler else 0
      ir = self._compile_ir(program, self._dispatch_mode, host_assigned_id=prof_id)
      programs.append((ir, self._profiler))

    self.cq.extend(lower_fast(
      programs, self._go_word(), self.cores,
      profiler_flat_ids=self._profiler_flat_ids or None,
      profiler_sysmem_noc_local=self._cq_hw.profiler_noc_local if self._profiler else 0,
    ))

    self._cq_hw._event_id += 1
    self.cq.append(CQHostEvent(self._cq_hw._event_id))

    self._cq_hw.flush(self.cq)
    self._cq_hw.wait_completion(self._cq_hw._event_id)

    if self._profiler:
      self._collect_profiler_data()

  def _run_slow_dispatch(self):
    t0 = time.perf_counter()
    with TLBWindow(self.dev, start=self.cores[0]) as win:
      for program in self._programs:
        ir = self._compile_ir(program, self._dispatch_mode)
        slow_dispatch(win, ir)
    elapsed_us = (time.perf_counter() - t0) * 1e6
    print(f"  slow dispatch: {elapsed_us:,.1f} us total (host wall-clock, {len(self._programs)} programs)")


  def serve_profile(self, port: int = int(os.environ.get("PORT", 8000))):
    self._finalize_profile()
    data = self.last_profile
    if os.environ.get("PROFILE_JSON"):
      import json
      path = os.environ["PROFILE_JSON"]
      with open(path, "w") as f: json.dump(data, f)
      print(f"profiler data written to {path}")
      return
    from profiler import ui as profiler_ui
    profiler_ui.serve(data, port=port, disasm_dir=self._profile_disasm_dir)

  def close(self):
    self._set_power(False)
    if getattr(self, "_profile_disasm_dir", None):
      shutil.rmtree(self._profile_disasm_dir, ignore_errors=True)
      self._profile_disasm_dir = None
    # halt dispatch cores before tearing down sysmem — they read from
    # IOMMU-mapped host memory and will fault if it's unmapped first
    if self._cq_hw is not None:
      self._halt_cores([self._PREFETCH_CORE, self._DISPATCH_CORE])
    if self._dram_sysmem is not None:
      self._dram_sysmem.close()
    if self._cq_hw is not None:
      self._cq_hw.close()
    self.dram.close()
    self.dev.close()
