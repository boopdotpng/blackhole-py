import re, struct

from hw import *
from compiler import hash16

RISC_NAMES = ("BRISC", "NCRISC", "TRISC0", "TRISC1", "TRISC2")
PERF_COUNTER_ID = 9090

# Must match PerfCounterType enum in perf_counters.hpp
_PERF_COUNTER_NAME_LIST = [
 "UNDEF", "FPU", "SFPU", "MATH", "DATA_HAZARD_STALLS_MOVD2A",
 "MATH_INSTRN_STARTED", "MATH_INSTRN_AVAILABLE", "SRCB_WRITE_AVAILABLE", "SRCA_WRITE_AVAILABLE",
 "UNPACK0_BUSY_THREAD0", "UNPACK1_BUSY_THREAD0", "UNPACK0_BUSY_THREAD1", "UNPACK1_BUSY_THREAD1",
 "SRCB_WRITE", "SRCA_WRITE", "PACKER_DEST_READ_AVAILABLE", "PACKER_BUSY", "AVAILABLE_MATH",
 "CFG_INSTRN_AVAILABLE_0", "CFG_INSTRN_AVAILABLE_1", "CFG_INSTRN_AVAILABLE_2",
 "SYNC_INSTRN_AVAILABLE_0", "SYNC_INSTRN_AVAILABLE_1", "SYNC_INSTRN_AVAILABLE_2",
 "THCON_INSTRN_AVAILABLE_0", "THCON_INSTRN_AVAILABLE_1", "THCON_INSTRN_AVAILABLE_2",
 "XSEARCH_INSTRN_AVAILABLE_0", "XSEARCH_INSTRN_AVAILABLE_1", "XSEARCH_INSTRN_AVAILABLE_2",
 "MOVE_INSTRN_AVAILABLE_0", "MOVE_INSTRN_AVAILABLE_1", "MOVE_INSTRN_AVAILABLE_2",
 "FPU_INSTRN_AVAILABLE_0", "FPU_INSTRN_AVAILABLE_1", "FPU_INSTRN_AVAILABLE_2",
 "UNPACK_INSTRN_AVAILABLE_0", "UNPACK_INSTRN_AVAILABLE_1", "UNPACK_INSTRN_AVAILABLE_2",
 "PACK_INSTRN_AVAILABLE_0", "PACK_INSTRN_AVAILABLE_1", "PACK_INSTRN_AVAILABLE_2",
 "THREAD_STALLS_0", "THREAD_STALLS_1", "THREAD_STALLS_2",
 "WAITING_FOR_SRCA_CLEAR", "WAITING_FOR_SRCB_CLEAR", "WAITING_FOR_SRCA_VALID", "WAITING_FOR_SRCB_VALID",
 "WAITING_FOR_THCON_IDLE_0", "WAITING_FOR_THCON_IDLE_1", "WAITING_FOR_THCON_IDLE_2",
 "WAITING_FOR_UNPACK_IDLE_0", "WAITING_FOR_UNPACK_IDLE_1", "WAITING_FOR_UNPACK_IDLE_2",
 "WAITING_FOR_PACK_IDLE_0", "WAITING_FOR_PACK_IDLE_1", "WAITING_FOR_PACK_IDLE_2",
 "WAITING_FOR_MATH_IDLE_0", "WAITING_FOR_MATH_IDLE_1", "WAITING_FOR_MATH_IDLE_2",
 "WAITING_FOR_NONZERO_SEM_0", "WAITING_FOR_NONZERO_SEM_1", "WAITING_FOR_NONZERO_SEM_2",
 "WAITING_FOR_NONFULL_SEM_0", "WAITING_FOR_NONFULL_SEM_1", "WAITING_FOR_NONFULL_SEM_2",
 "WAITING_FOR_MOVE_IDLE_0", "WAITING_FOR_MOVE_IDLE_1", "WAITING_FOR_MOVE_IDLE_2",
 "WAITING_FOR_MMIO_IDLE_0", "WAITING_FOR_MMIO_IDLE_1", "WAITING_FOR_MMIO_IDLE_2",
 "WAITING_FOR_SFPU_IDLE_0", "WAITING_FOR_SFPU_IDLE_1", "WAITING_FOR_SFPU_IDLE_2",
 "THREAD_INSTRUCTIONS_0", "THREAD_INSTRUCTIONS_1", "THREAD_INSTRUCTIONS_2",
 "NOC_RING0_INCOMING_1", "NOC_RING0_INCOMING_0", "NOC_RING0_OUTGOING_1", "NOC_RING0_OUTGOING_0",
 "L1_ARB_TDMA_BUNDLE_1", "L1_ARB_TDMA_BUNDLE_0", "L1_ARB_UNPACKER", "L1_NO_ARB_UNPACKER",
 "NOC_RING1_INCOMING_1", "NOC_RING1_INCOMING_0", "NOC_RING1_OUTGOING_1", "NOC_RING1_OUTGOING_0",
 "TDMA_BUNDLE_1_ARB", "TDMA_BUNDLE_0_ARB", "TDMA_EXT_UNPACK_9_10", "TDMA_PACKER_2_WR",
]
PERF_COUNTER_NAMES = {i: name for i, name in enumerate(_PERF_COUNTER_NAME_LIST) if i != 0}

_PERF_COUNTER_GROUPS = [(3, "FPU"), (14, "UNPACK"), (17, "PACK"), (78, "INSTRN"), (86, "L1_0"), (94, "L1_1")]

def _perf_counter_group(ct):
 for threshold, name in _PERF_COUNTER_GROUPS:
  if ct <= threshold: return name
 return "UNKNOWN"

class P:
 HOST_BUF_END, GUARANTEED_FW_START, GUARANTEED_FW_END = 0, 4, 6  # per RISC (indices 0-4)
 GUARANTEED_KERN_START, GUARANTEED_KERN_END, CUSTOM_START = 8, 10, 12
 ZONE_START, ZONE_END, ZONE_TOTAL, TS_DATA, TS_DATA_16B = 0, 1, 2, 3, 5

_HOST_BUF_BYTES_PER_RISC = TensixL1.PROFILER_HOST_BUFFER_BYTES_PER_RISC
_HOST_BUF_WORDS_PER_RISC = _HOST_BUF_BYTES_PER_RISC // 4

_ZONE_RE = re.compile(r'DeviceZoneScopedN\s*\(\s*"([^"]+)"')

def _parse_ts(w0, w1):
 return ((w0 & 0xFFF) << 32) | w1 if w0 & 0x80000000 else None

def _validate_run(words, start, end, program_ids):
 if end - start < P.CUSTOM_START or words[start + 3] not in program_ids:
  return False
 for off in (P.GUARANTEED_FW_START, P.GUARANTEED_FW_END, P.GUARANTEED_KERN_START, P.GUARANTEED_KERN_END):
  w0 = words[start + off]
  if not (w0 & 0x80000000) or ((w0 >> 12) & 0x7FFFF) >> 16 not in (P.ZONE_START, P.ZONE_END):
   return False
 return True

def _parse_run(words, start, end, program_ids):
 if not _validate_run(words, start, end, program_ids):
  return None
 prog_id = words[start + 3]
 ts = lambda off: _parse_ts(words[start + off], words[start + off + 1])
 fw_start, fw_end = ts(P.GUARANTEED_FW_START), ts(P.GUARANTEED_FW_END)
 kern_start, kern_end = ts(P.GUARANTEED_KERN_START), ts(P.GUARANTEED_KERN_END)
 fw = max(0, fw_end - fw_start) if fw_start and fw_end else 0
 kern = max(0, kern_end - kern_start) if kern_start and kern_end else 0

 custom, perf_counters = [], []
 i = start + P.CUSTOM_START
 while i + 1 < end:
  w0, w1 = words[i], words[i + 1]
  if w0 == 0 and w1 == 0: break
  if not (w0 & 0x80000000): i += 2; continue
  timer_id = (w0 >> 12) & 0x7FFFF
  ptype = (timer_id >> 16) & 0x7
  if ptype in (P.ZONE_START, P.ZONE_END, P.ZONE_TOTAL):
   t = w1 if ptype == P.ZONE_TOTAL else ((w0 & 0xFFF) << 32) | w1
   custom.append((timer_id & 0xFFFF, ptype, t))
  if ptype == P.TS_DATA:
   zone_hash = timer_id & 0xFFFF
   if zone_hash == (PERF_COUNTER_ID & 0xFFFF) and i + 3 < end:
    raw_hi, raw_lo = words[i + 2], words[i + 3]
    ref_cnt, counter_type = raw_hi & 0x00FFFFFF, (raw_hi >> 24) & 0xFF
    util_pct = (raw_lo / ref_cnt * 100.0) if ref_cnt > 0 else 0.0
    perf_counters.append({
     "name": PERF_COUNTER_NAMES.get(counter_type, f"UNKNOWN_{counter_type}"),
     "counter_type": counter_type, "group": _perf_counter_group(counter_type),
     "counter_value": raw_lo, "ref_cnt": ref_cnt, "util_pct": round(util_pct, 2),
    })
   i += 4
  elif ptype == P.TS_DATA_16B: i += 6
  else: i += 2

 return prog_id, fw, kern, kern_start, kern_end, custom, perf_counters

def _find_runs(words, program_ids):
 n = len(words)
 return [i for i in range(0, n - 3, 2) if words[i] == 0 and words[i + 1] == 0 and _validate_run(words, i, n, program_ids)]

def _parse_risc(words, risc_id, program_ids):
 if len(words) < P.CUSTOM_START: return {}
 starts = _find_runs(words, program_ids)
 if not starts: return {}
 out = {}
 for idx, start in enumerate(starts):
  end = starts[idx + 1] if idx + 1 < len(starts) else len(words)
  parsed = _parse_run(words, start, end, program_ids)
  if parsed is None: continue
  prog_id, fw, kern, kern_start, kern_end, custom, perf_counters = parsed
  if out.get(prog_id) is None or (out[prog_id][1] == 0 and kern > 0):
   out[prog_id] = (fw, kern, kern_start, kern_end, custom, perf_counters)
 return out

def _aggregate_zones(custom, zone_names):
 from collections import defaultdict
 starts, ends, totals = defaultdict(list), defaultdict(list), defaultdict(int)
 for zh, ptype, ts in custom:
  if ptype == P.ZONE_START: starts[zh].append(ts)
  elif ptype == P.ZONE_END: ends[zh].append(ts)
  elif ptype == P.ZONE_TOTAL: totals[zh] += ts
 zones = {}
 for zh in set(starts) | set(totals):
  s_list, e_list = starts.get(zh, []), ends.get(zh, [])
  n = min(len(s_list), len(e_list))
  if n > 0:
   durs = [e - s for s, e in zip(s_list[:n], e_list[:n]) if e > s]
   if not durs: continue
   total, count, mn, mx = sum(durs), len(durs), min(durs), max(durs)
  elif zh in totals: total, count, mn, mx = totals[zh], 1, totals[zh], totals[zh]
  else: continue
  zones[zone_names.get(zh, f"0x{zh:04x}")] = {"total": total, "count": count, "min": mn, "max": mx}
 return zones

def _resolve_zone_names(programs_info):
 from compiler import _zone_map
 names = {}
 for info in programs_info:
  for label, src in info.get("sources", {}).items():
   if not src: continue
   for lineno, line in enumerate(src.splitlines(), start=1):
    m = _ZONE_RE.search(line)
    if not m: continue
    name = m.group(1)
    for fpath in ("./kernel_includes.hpp", "kernel_includes.hpp", label):
     names.setdefault(hash16(f"{name},{fpath},{lineno},KERNEL_PROFILER"), name)
    names.setdefault(hash16(name), name)
 for h, (name, _, _) in _zone_map.items():
  names.setdefault(h, name)
 return names

def build_programs_info(programs, device_cores):
 result = []
 for i, prog in enumerate(programs):
  sources = {}
  if prog.reader_kernel: sources["reader"] = prog.reader_kernel
  if prog.writer_kernel: sources["writer"] = prog.writer_kernel
  if prog.compute_kernel: sources["compute"] = prog.compute_kernel
  core_sources, core_disassembly = None, getattr(prog, "_profile_core_disassembly", None)
  if prog.grid is not None:
   rows, cols = prog.grid
   cores = sorted([(x, y) for x in cols for y in rows])
   if prog.reader_recv_kernel or prog.writer_recv_kernel:
    core_sources = {}
    cols_list, rows_list = list(cols), list(rows)
    for cx, cy in cores:
     cs = {}
     if prog.compute_kernel: cs["compute"] = prog.compute_kernel
     r = prog.reader_kernel if cols_list.index(cx) == 0 else (prog.reader_recv_kernel or prog.reader_kernel)
     w = prog.writer_kernel if rows_list.index(cy) == 0 else (prog.writer_recv_kernel or prog.writer_kernel)
     if r: cs["reader"] = r
     if w: cs["writer"] = w
     core_sources[f"{cx},{cy}"] = cs
  else:
   cores = device_cores if prog.cores == "all" else device_cores[:prog.cores]
  info = {"index": i, "name": prog.name or None, "cores": cores, "sources": sources}
  disasm = getattr(prog, "_profile_disassembly", None)
  if disasm: info["disassembly"] = disasm
  if core_sources is not None: info["core_sources"] = core_sources
  if core_disassembly is not None: info["core_disassembly"] = core_disassembly
  result.append(info)
 return result

_EMPTY_RISC = {"fw": 0, "kern": 0, "kern_start": None, "kern_end": None, "zones": {}}

def collect(programs_info, raw_dram, ctrl_regs, layout, harvested_dram_bank):
 program_ids = {info["index"] + 1 for info in programs_info}
 zone_names = _resolve_zone_names(programs_info)
 needed = set()
 for info in programs_info: needed.update(info["cores"])
 flat_ids = layout["flat_ids"]

 # Parse all RISC data from sysmem — core_data[core][prog_id] = list of risc dicts
 core_data = {}
 for core in sorted(needed):
  flat_id, ctrl = flat_ids[core], struct.unpack("<32I", ctrl_regs[core])
  by_program = {}
  for risc in range(5):
   host_end = min(ctrl[P.HOST_BUF_END + risc], _HOST_BUF_WORDS_PER_RISC)
   base = (flat_id * 5 + risc) * _HOST_BUF_BYTES_PER_RISC
   raw = raw_dram[base : base + host_end * 4]
   words = struct.unpack(f"<{len(raw) // 4}I", raw) if raw else ()
   for prog_id, (fw, kern, ks, ke, custom, pc) in _parse_risc(words, risc, program_ids).items():
    entry = {"name": RISC_NAMES[risc], "fw": fw, "kern": kern, "kern_start": ks, "kern_end": ke,
        "zones": _aggregate_zones(custom, zone_names)}
    if pc: entry["perf_counters"] = pc
    by_program.setdefault(prog_id, []).append(entry)
  core_data[core] = by_program

 # Build output programs
 programs = []
 for info in programs_info:
  prog_id = info["index"] + 1
  core_sources, core_disasm = info.get("core_sources", {}), info.get("core_disassembly", {})
  profiles = {}
  for core in info["cores"]:
   riscs = core_data.get(core, {}).get(prog_id, [])
   present = {r["name"] for r in riscs}
   for name in RISC_NAMES:
    if name not in present:
     riscs.append({"name": name, **_EMPTY_RISC})
   riscs.sort(key=lambda r: RISC_NAMES.index(r["name"]))
   active = [r for r in riscs if r["kern_start"] and r["kern_end"] and r["kern"] > 0]
   total = max(0, max(r["kern_end"] for r in active) - min(r["kern_start"] for r in active)) if active else 0
   out_riscs = []
   for r in riscs:
    rd = {"name": r["name"], "fw": r["fw"], "kern": r["kern"], "zones": r["zones"]}
    if r.get("perf_counters"): rd["perf_counters"] = r["perf_counters"]
    out_riscs.append(rd)
   ck = f"{core[0]},{core[1]}"
   entry = {"total": total, "riscs": out_riscs}
   if ck in core_sources: entry["sources"] = core_sources[ck]
   if ck in core_disasm: entry["disassembly"] = core_disasm[ck]
   profiles[ck] = entry
  programs.append({
   "index": info["index"], "name": info.get("name"),
   "cores": [list(c) for c in info["cores"]],
   "sources": info.get("sources", {}), "disassembly": info.get("disassembly", {}),
   "profiles": profiles,
  })
 return {"dispatch_mode": "fast", "harvested_dram_bank": harvested_dram_bank, "programs": programs}

