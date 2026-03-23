import re, struct

from hw import *
from compiler import hash16

RISC_NAMES = ("BRISC", "NCRISC", "TRISC0", "TRISC1", "TRISC2")
PERF_COUNTER_ID = 9090

# Must match PerfCounterType enum in perf_counters.hpp
_PERF_COUNTER_NAME_LIST = [
  "UNDEF",
  "FPU",
  "SFPU",
  "MATH",
  "DATA_HAZARD_STALLS_MOVD2A",
  "MATH_INSTRN_STARTED",
  "MATH_INSTRN_AVAILABLE",
  "SRCB_WRITE_AVAILABLE",
  "SRCA_WRITE_AVAILABLE",
  "UNPACK0_BUSY_THREAD0",
  "UNPACK1_BUSY_THREAD0",
  "UNPACK0_BUSY_THREAD1",
  "UNPACK1_BUSY_THREAD1",
  "SRCB_WRITE",
  "SRCA_WRITE",
  "PACKER_DEST_READ_AVAILABLE",
  "PACKER_BUSY",
  "AVAILABLE_MATH",
  "CFG_INSTRN_AVAILABLE_0",
  "CFG_INSTRN_AVAILABLE_1",
  "CFG_INSTRN_AVAILABLE_2",
  "SYNC_INSTRN_AVAILABLE_0",
  "SYNC_INSTRN_AVAILABLE_1",
  "SYNC_INSTRN_AVAILABLE_2",
  "THCON_INSTRN_AVAILABLE_0",
  "THCON_INSTRN_AVAILABLE_1",
  "THCON_INSTRN_AVAILABLE_2",
  "XSEARCH_INSTRN_AVAILABLE_0",
  "XSEARCH_INSTRN_AVAILABLE_1",
  "XSEARCH_INSTRN_AVAILABLE_2",
  "MOVE_INSTRN_AVAILABLE_0",
  "MOVE_INSTRN_AVAILABLE_1",
  "MOVE_INSTRN_AVAILABLE_2",
  "FPU_INSTRN_AVAILABLE_0",
  "FPU_INSTRN_AVAILABLE_1",
  "FPU_INSTRN_AVAILABLE_2",
  "UNPACK_INSTRN_AVAILABLE_0",
  "UNPACK_INSTRN_AVAILABLE_1",
  "UNPACK_INSTRN_AVAILABLE_2",
  "PACK_INSTRN_AVAILABLE_0",
  "PACK_INSTRN_AVAILABLE_1",
  "PACK_INSTRN_AVAILABLE_2",
  "THREAD_STALLS_0",
  "THREAD_STALLS_1",
  "THREAD_STALLS_2",
  "WAITING_FOR_SRCA_CLEAR",
  "WAITING_FOR_SRCB_CLEAR",
  "WAITING_FOR_SRCA_VALID",
  "WAITING_FOR_SRCB_VALID",
  "WAITING_FOR_THCON_IDLE_0",
  "WAITING_FOR_THCON_IDLE_1",
  "WAITING_FOR_THCON_IDLE_2",
  "WAITING_FOR_UNPACK_IDLE_0",
  "WAITING_FOR_UNPACK_IDLE_1",
  "WAITING_FOR_UNPACK_IDLE_2",
  "WAITING_FOR_PACK_IDLE_0",
  "WAITING_FOR_PACK_IDLE_1",
  "WAITING_FOR_PACK_IDLE_2",
  "WAITING_FOR_MATH_IDLE_0",
  "WAITING_FOR_MATH_IDLE_1",
  "WAITING_FOR_MATH_IDLE_2",
  "WAITING_FOR_NONZERO_SEM_0",
  "WAITING_FOR_NONZERO_SEM_1",
  "WAITING_FOR_NONZERO_SEM_2",
  "WAITING_FOR_NONFULL_SEM_0",
  "WAITING_FOR_NONFULL_SEM_1",
  "WAITING_FOR_NONFULL_SEM_2",
  "WAITING_FOR_MOVE_IDLE_0",
  "WAITING_FOR_MOVE_IDLE_1",
  "WAITING_FOR_MOVE_IDLE_2",
  "WAITING_FOR_MMIO_IDLE_0",
  "WAITING_FOR_MMIO_IDLE_1",
  "WAITING_FOR_MMIO_IDLE_2",
  "WAITING_FOR_SFPU_IDLE_0",
  "WAITING_FOR_SFPU_IDLE_1",
  "WAITING_FOR_SFPU_IDLE_2",
  "THREAD_INSTRUCTIONS_0",
  "THREAD_INSTRUCTIONS_1",
  "THREAD_INSTRUCTIONS_2",
  "NOC_RING0_INCOMING_1",
  "NOC_RING0_INCOMING_0",
  "NOC_RING0_OUTGOING_1",
  "NOC_RING0_OUTGOING_0",
  "L1_ARB_TDMA_BUNDLE_1",
  "L1_ARB_TDMA_BUNDLE_0",
  "L1_ARB_UNPACKER",
  "L1_NO_ARB_UNPACKER",
  "NOC_RING1_INCOMING_1",
  "NOC_RING1_INCOMING_0",
  "NOC_RING1_OUTGOING_1",
  "NOC_RING1_OUTGOING_0",
  "TDMA_BUNDLE_1_ARB",
  "TDMA_BUNDLE_0_ARB",
  "TDMA_EXT_UNPACK_9_10",
  "TDMA_PACKER_2_WR",
]
PERF_COUNTER_NAMES = {i: name for i, name in enumerate(_PERF_COUNTER_NAME_LIST) if i != 0}

def _perf_counter_group(counter_type):
  if 1 <= counter_type <= 3:
    return "FPU"
  if 4 <= counter_type <= 14:
    return "UNPACK"
  if 15 <= counter_type <= 17:
    return "PACK"
  if 18 <= counter_type <= 78:
    return "INSTRN"
  if 79 <= counter_type <= 86:
    return "L1_0"
  if 87 <= counter_type <= 94:
    return "L1_1"
  return "UNKNOWN"

class P:
  HOST_BUF_END = 0             # per RISC (indices 0-4)
  GUARANTEED_FW_START = 4
  GUARANTEED_FW_END = 6
  GUARANTEED_KERN_START = 8
  GUARANTEED_KERN_END = 10
  CUSTOM_START = 12
  ZONE_START = 0
  ZONE_END = 1
  ZONE_TOTAL = 2
  TS_DATA = 3
  TS_DATA_16B = 5

_HOST_BUF_BYTES_PER_RISC = TensixL1.PROFILER_HOST_BUFFER_BYTES_PER_RISC
_HOST_BUF_WORDS_PER_RISC = _HOST_BUF_BYTES_PER_RISC // 4

_ZONE_RE = re.compile(r'DeviceZoneScopedN\s*\(\s*"([^"]+)"')

def _parse_ts(w0, w1):
  if not (w0 & 0x80000000):
    return None
  return ((w0 & 0xFFF) << 32) | w1

def _parse_ctrl(raw_128_bytes):
  return struct.unpack("<32I", raw_128_bytes)

def _parse_run(words, start, end, program_ids):
  n = end - start
  if n < P.CUSTOM_START:
    return None
  prog_id = words[start + 3]
  if prog_id not in program_ids:
    return None

  # Validate guaranteed markers
  for off in (
    P.GUARANTEED_FW_START,
    P.GUARANTEED_FW_END,
    P.GUARANTEED_KERN_START,
    P.GUARANTEED_KERN_END,
  ):
    w0 = words[start + off]
    if not (w0 & 0x80000000):
      return None
    ptype = ((w0 >> 12) & 0x7FFFF) >> 16
    if ptype not in (P.ZONE_START, P.ZONE_END):
      return None

  fw_start = _parse_ts(
    words[start + P.GUARANTEED_FW_START], words[start + P.GUARANTEED_FW_START + 1]
  )
  fw_end = _parse_ts(
    words[start + P.GUARANTEED_FW_END], words[start + P.GUARANTEED_FW_END + 1]
  )
  kern_start = _parse_ts(
    words[start + P.GUARANTEED_KERN_START], words[start + P.GUARANTEED_KERN_START + 1]
  )
  kern_end = _parse_ts(
    words[start + P.GUARANTEED_KERN_END], words[start + P.GUARANTEED_KERN_END + 1]
  )

  fw = (
    (fw_end - fw_start)
    if (fw_start is not None and fw_end is not None and fw_end > fw_start)
    else 0
  )
  kern = (
    (kern_end - kern_start)
    if (kern_start is not None and kern_end is not None and kern_end > kern_start)
    else 0
  )

  # Parse custom zone markers and perf counter data
  custom = []  # list of (zone_hash, ptype, ts)
  perf_counters = []  # list of {"name": str, "counter_value": int, "ref_cnt": int, "util_pct": float}
  i = start + P.CUSTOM_START
  while i + 1 < end:
    w0, w1 = words[i], words[i + 1]
    if w0 == 0 and w1 == 0:
      break
    if not (w0 & 0x80000000):
      i += 2
      continue
    timer_id = (w0 >> 12) & 0x7FFFF
    ptype = (timer_id >> 16) & 0x7
    if ptype in (P.ZONE_START, P.ZONE_END, P.ZONE_TOTAL):
      ts = w1 if ptype == P.ZONE_TOTAL else ((w0 & 0xFFF) << 32) | w1
      custom.append((timer_id & 0xFFFF, ptype, ts))
    if ptype == P.TS_DATA:
      zone_hash = timer_id & 0xFFFF
      if zone_hash == (PERF_COUNTER_ID & 0xFFFF) and i + 3 < end:
        # Decode PerfCounter: words[i+2] = high 32 bits, words[i+3] = low 32 bits
        raw_hi = words[i + 2]
        raw_lo = words[i + 3]
        counter_value = raw_lo
        ref_cnt = raw_hi & 0x00FFFFFF
        counter_type = (raw_hi >> 24) & 0xFF
        name = PERF_COUNTER_NAMES.get(counter_type, f"UNKNOWN_{counter_type}")
        util_pct = (counter_value / ref_cnt * 100.0) if ref_cnt > 0 else 0.0
        perf_counters.append({
          "name": name,
          "counter_type": counter_type,
          "group": _perf_counter_group(counter_type),
          "counter_value": counter_value,
          "ref_cnt": ref_cnt,
          "util_pct": round(util_pct, 2),
        })
      i += 4
    elif ptype == P.TS_DATA_16B:
      i += 6
    else:
      i += 2

  return prog_id, fw, kern, kern_start, kern_end, custom, perf_counters

def _find_runs(words, program_ids):
  n = len(words)
  starts = []
  for i in range(0, n - 3, 2):
    if words[i] != 0 or words[i + 1] != 0:
      continue
    if i + P.CUSTOM_START > n:
      continue
    if words[i + 3] not in program_ids:
      continue
    # Check guaranteed markers are valid
    valid = True
    for off in (
      P.GUARANTEED_FW_START,
      P.GUARANTEED_FW_END,
      P.GUARANTEED_KERN_START,
      P.GUARANTEED_KERN_END,
    ):
      w0 = words[i + off]
      if not (w0 & 0x80000000):
        valid = False
        break
      ptype = ((w0 >> 12) & 0x7FFFF) >> 16
      if ptype not in (P.ZONE_START, P.ZONE_END):
        valid = False
        break
    if valid:
      starts.append(i)
  return starts

def _parse_risc(words, risc_id, program_ids):
  n = len(words)
  if n < P.CUSTOM_START:
    return {}
  starts = _find_runs(words, program_ids)
  if not starts:
    return {}

  out = {}
  for idx, start in enumerate(starts):
    end = starts[idx + 1] if idx + 1 < len(starts) else n
    parsed = _parse_run(words, start, end, program_ids)
    if parsed is None:
      continue
    prog_id, fw, kern, kern_start, kern_end, custom, perf_counters = parsed
    prev = out.get(prog_id)
    if prev is None or (prev[1] == 0 and kern > 0):
      out[prog_id] = (fw, kern, kern_start, kern_end, custom, perf_counters)
  return out

def _aggregate_zones(custom, zone_names):
  starts = {}  # hash -> [ts, ...]
  ends = {}  # hash -> [ts, ...]
  totals = {}  # hash -> accumulated cycles (for ZONE_TOTAL packets)
  for zone_hash, ptype, ts in custom:
    if ptype == P.ZONE_START:
      starts.setdefault(zone_hash, []).append(ts)
    elif ptype == P.ZONE_END:
      ends.setdefault(zone_hash, []).append(ts)
    elif ptype == P.ZONE_TOTAL:
      totals[zone_hash] = totals.get(zone_hash, 0) + ts

  zones = {}
  for zone_hash in set(starts) | set(totals):
    s_list = starts.get(zone_hash, [])
    e_list = ends.get(zone_hash, [])
    n = min(len(s_list), len(e_list))

    if n > 0:
      durations = [e - s for s, e in zip(s_list[:n], e_list[:n]) if e > s]
      if not durations:
        continue
      total = sum(durations)
      count = len(durations)
      mn, mx = min(durations), max(durations)
    elif zone_hash in totals:
      total = totals[zone_hash]
      count, mn, mx = 1, total, total
    else:
      continue

    name = zone_names.get(zone_hash, f"0x{zone_hash:04x}")
    zones[name] = {"total": total, "count": count, "min": mn, "max": mx}
  return zones

def _hash_msg(name, fpath, lineno):
  return hash16(f"{name},{fpath},{lineno},KERNEL_PROFILER")

def _resolve_zone_names(programs_info):
  from compiler import _zone_map

  names = {}  # int hash -> str name
  for info in programs_info:
    for label, src in info.get("sources", {}).items():
      if not src:
        continue
      for lineno, line in enumerate(src.splitlines(), start=1):
        m = _ZONE_RE.search(line)
        if not m:
          continue
        name = m.group(1)
        for fpath in ("./kernel_includes.hpp", "kernel_includes.hpp", label):
          names.setdefault(_hash_msg(name, fpath, lineno), name)
        names.setdefault(hash16(name), name)

  for h, (name, _, _) in _zone_map.items():
    names.setdefault(h, name)
  return names

def init_layout(cores, bank_count=0):
  cores = sorted(cores, key=lambda xy: (xy[0], xy[1]))
  return {
    "flat_ids": {core: i for i, core in enumerate(cores)},
  }

def build_programs_info(programs, device_cores):
  result = []
  for i, prog in enumerate(programs):
    sources = {}
    disassembly = getattr(prog, "_profile_disassembly", None)
    if prog.reader_kernel: sources["reader"] = prog.reader_kernel
    if prog.writer_kernel: sources["writer"] = prog.writer_kernel
    if prog.compute_kernel: sources["compute"] = prog.compute_kernel
    core_sources = None
    core_disassembly = getattr(prog, "_profile_core_disassembly", None)
    if prog.grid is not None:
      rows, cols = prog.grid
      cores = sorted([(x, y) for x in cols for y in rows], key=lambda c: (c[0], c[1]))
      if prog.reader_recv_kernel or prog.writer_recv_kernel:
        core_sources = {}
        for core in cores:
          cs = {}
          if prog.compute_kernel: cs["compute"] = prog.compute_kernel
          c_idx = list(cols).index(core[0])
          r_idx = list(rows).index(core[1])
          reader_src = prog.reader_kernel if c_idx == 0 else (prog.reader_recv_kernel or prog.reader_kernel)
          writer_src = prog.writer_kernel if r_idx == 0 else (prog.writer_recv_kernel or prog.writer_kernel)
          if reader_src: cs["reader"] = reader_src
          if writer_src: cs["writer"] = writer_src
          core_sources[f"{core[0]},{core[1]}"] = cs
    else:
      cores = device_cores if prog.cores == "all" else device_cores[:prog.cores]
    info = {"index": i, "name": prog.name or None, "cores": cores, "sources": sources}
    if disassembly: info["disassembly"] = disassembly
    if core_sources is not None: info["core_sources"] = core_sources
    if core_disassembly is not None: info["core_disassembly"] = core_disassembly
    result.append(info)
  return result

def collect(
  programs_info,
  raw_dram,
  ctrl_regs,
  layout,
  harvested_dram_bank,
):
  program_ids = {info["index"] + 1 for info in programs_info}
  zone_names = _resolve_zone_names(programs_info)

  needed = set()
  for info in programs_info:
    needed.update(info["cores"])

  # Parse all RISC data from sysmem, keyed by (core, prog_id)
  # core_data[core][prog_id] = list of (risc_name, fw, kern, kern_start, kern_end, zones)
  core_data = {}

  flat_ids = layout["flat_ids"]

  for core in sorted(needed):
    flat_id = flat_ids[core]
    ctrl = _parse_ctrl(ctrl_regs[core])

    by_program = {}  # prog_id -> list of risc dicts
    for risc in range(5):
      host_end = min(ctrl[P.HOST_BUF_END + risc], _HOST_BUF_WORDS_PER_RISC)
      # Flat sysmem layout: core * (5 * per_risc) + risc * per_risc
      base = flat_id * 5 * _HOST_BUF_BYTES_PER_RISC + risc * _HOST_BUF_BYTES_PER_RISC
      raw = raw_dram[base : base + host_end * 4]
      words = struct.unpack(f"<{len(raw) // 4}I", raw) if raw else ()

      for prog_id, (fw, kern, kern_start, kern_end, custom, perf_counters) in _parse_risc(
        words, risc, program_ids
      ).items():
        zones = _aggregate_zones(custom, zone_names)
        entry = {
          "name": RISC_NAMES[risc],
          "fw": fw,
          "kern": kern,
          "kern_start": kern_start,
          "kern_end": kern_end,
          "zones": zones,
        }
        if perf_counters:
          entry["perf_counters"] = perf_counters
        by_program.setdefault(prog_id, []).append(entry)
    core_data[core] = by_program

  # Build output programs
  programs = []
  for info in programs_info:
    prog_id = info["index"] + 1
    core_sources = info.get("core_sources", {})
    profiles = {}
    for core in info["cores"]:
      by_prog = core_data.get(core, {})
      riscs = by_prog.get(prog_id, [])
      # Fill missing RISCs
      present = {r["name"] for r in riscs}
      for name in RISC_NAMES:
        if name not in present:
          riscs.append(
            {
              "name": name,
              "fw": 0,
              "kern": 0,
              "kern_start": None,
              "kern_end": None,
              "zones": {},
            }
          )
      riscs.sort(key=lambda r: RISC_NAMES.index(r["name"]))
      # Compute total wall time across RISCs (only include RISCs that ran kernel code)
      starts = [
        r["kern_start"]
        for r in riscs
        if r["kern_start"] is not None and r["kern_end"] is not None and r["kern"] > 0
      ]
      ends = [
        r["kern_end"]
        for r in riscs
        if r["kern_start"] is not None and r["kern_end"] is not None and r["kern"] > 0
      ]
      total = max(0, max(ends) - min(starts)) if starts and ends else 0
      # Strip internal fields from output
      out_riscs = []
      for r in riscs:
        rd = {
          "name": r["name"],
          "fw": r["fw"],
          "kern": r["kern"],
          "zones": r["zones"],
        }
        if r.get("perf_counters"):
          rd["perf_counters"] = r["perf_counters"]
        out_riscs.append(rd)
      core_key = f"{core[0]},{core[1]}"
      entry = {"total": total, "riscs": out_riscs}
      if core_key in core_sources:
        entry["sources"] = core_sources[core_key]
      core_disassembly = info.get("core_disassembly", {})
      if core_key in core_disassembly:
        entry["disassembly"] = core_disassembly[core_key]
      profiles[core_key] = entry

    programs.append(
      {
        "index": info["index"],
        "name": info.get("name"),
        "cores": [list(c) for c in info["cores"]],
        "sources": info.get("sources", {}),
        "disassembly": info.get("disassembly", {}),
        "profiles": profiles,
      }
    )

  return {
    "dispatch_mode": "fast",
    "harvested_dram_bank": harvested_dram_bank,
    "programs": programs,
  }

def print_summary(data):
  programs = data.get("programs", [])
  print(f"Profiler collected {len(programs)} program(s)")
  for prog in programs:
    totals = [p["total"] for p in prog["profiles"].values() if p["total"] > 0]
    n = len(prog["profiles"])
    if not totals:
      print(
        f"  program {prog['index']} ({prog.get('name') or 'unnamed'}): {n} core(s), no cycles"
      )
      continue
    mn, mx = min(totals), max(totals)
    avg = sum(totals) / len(totals)
    print(
      f"  program {prog['index']} ({prog.get('name') or 'unnamed'}): {n} core(s), min/avg/max = {mn}/{avg:.1f}/{mx} cycles"
    )
