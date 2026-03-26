from __future__ import annotations

import json
import os
import sys
import threading
import time
from array import array
from bisect import bisect_right
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cq import CQSysmem
from compiler import iter_pt_load
from debug.symbols import list_symbols, resolve_assembly_line, resolve_source_location
from debug.regs import DBG_BUS_CTRL, DBG_BUS_RD_DATA, DEBUG_TLB_BASE, dbg_bus_cntl
from dispatch import LaunchMsg, Write
from hw import Core, NocOrdering, TLBWindow
from hw import TensixL1

_TT_EXALENS_REPO = Path(__file__).resolve().parents[2] / "tt-exalens"
if _TT_EXALENS_REPO.exists() and str(_TT_EXALENS_REPO) not in sys.path:
  sys.path.insert(0, str(_TT_EXALENS_REPO))

from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.blackhole.functional_worker_debug_bus_signals import debug_bus_signal_map, group_map


DEBUG_BUS_INIT = DebugBusSignalStore.create_initialization(group_map, debug_bus_signal_map)

# --- Tensix instruction decoder ---
# Built from tt-exalens tensix_ops.py: opcode is bits[31:24], params are bits[23:0].
_TENSIX_OPCODES: dict[int, tuple[str, list[tuple[str, int, int]]]] = {}

def _build_opcode_table():
  import re
  ops_path = _TT_EXALENS_REPO / "ttexalens" / "hardware" / "blackhole" / "tensix_ops.py"
  if not ops_path.exists():
    return
  src = ops_path.read_text()
  blocks = re.split(r'\ndef ', src)
  for block in blocks:
    m = re.match(r'(TT_OP_\w+)\(([^)]*)\)', block)
    if not m or m.group(1) == 'TT_OP':
      continue
    name = m.group(1).replace('TT_OP_', '')
    params = [p.strip() for p in m.group(2).split(',') if p.strip()]
    om = re.search(r'TT_OP\(0x([0-9a-fA-F]+)', block)
    if not om:
      continue
    opcode = int(om.group(1), 16)
    fields = []
    for p in params:
      sm = re.search(rf'\({p}\)\s*<<\s*(\d+)', block)
      shift = int(sm.group(1)) if sm else 0
      fields.append((p, shift))
    _TENSIX_OPCODES[opcode] = (name, fields)

_build_opcode_table()

def decode_tensix_instruction(raw: int) -> str:
  if raw == 0:
    return "(idle)"
  opcode = (raw >> 24) & 0xFF
  entry = _TENSIX_OPCODES.get(opcode)
  if entry is None:
    return f"0x{raw:08x}"
  name, fields = entry
  if not fields:
    return name
  params_bits = raw & 0xFFFFFF
  # Compute each field's width from the sorted shift positions
  shifts_asc = sorted({s for _, s in fields})
  shift_to_width = {}
  for i, s in enumerate(shifts_asc):
    next_s = shifts_asc[i + 1] if i + 1 < len(shifts_asc) else 24
    shift_to_width[s] = next_s - s
  parts = []
  for pname, shift in fields:
    width = shift_to_width.get(shift, 8)
    val = (params_bits >> shift) & ((1 << width) - 1)
    parts.append(f"{pname}={val}")
  return f"{name}({', '.join(parts)})"
_TRACE_PRESETS = {
  "br": ("group", "brisc_group_a"),
  "nc": ("group", "ncrisc_group_a"),
  "tr0": ("group", "trisc0_group_a"),
  "tr1": ("group", "trisc1_group_a"),
  "tr2": ("group", "trisc2_group_a"),
  "tf0": ("group", "tensix_frontend_t0"),
  "tf1": ("group", "tensix_frontend_t1"),
  "tf2": ("group", "tensix_frontend_t2"),
  "brisc": ("group", "brisc_group_a"),
  "ncrisc": ("group", "ncrisc_group_a"),
  "trisc0": ("group", "trisc0_group_a"),
  "trisc1": ("group", "trisc1_group_a"),
  "trisc2": ("group", "trisc2_group_a"),
  "writer": ("group", "brisc_group_a"),
  "reader": ("group", "ncrisc_group_a"),
  "unpack": ("group", "trisc0_group_a"),
  "math": ("group", "trisc1_group_a"),
  "pack": ("group", "trisc2_group_a"),
  "frontend_t0": ("group", "tensix_frontend_t0"),
  "frontend_t1": ("group", "tensix_frontend_t1"),
  "frontend_t2": ("group", "tensix_frontend_t2"),
  "math_pipeline": ("group", "rwc_math_pipeline"),
  "pack_unpack": ("group", "rwc_pack_unpack_signals"),
  "tdma_core": ("group", "rwc_tdma_core_signals"),
}


def _mask_shift(mask: int) -> int:
  return 0 if mask == 0 else (mask & -mask).bit_length() - 1


def _decode_group_samples(group_name: str, raw_words: list[int], words_per_sample: int) -> dict[str, list[int]]:
  signal_group = DEBUG_BUS_INIT.signal_groups[group_name]
  decoded = {name: [] for name in sorted(signal_group)}
  if words_per_sample <= 0:
    return decoded
  samples = len(raw_words) // words_per_sample
  for sample_index in range(samples):
    raw = 0
    base = sample_index * words_per_sample
    for word_index in range(words_per_sample):
      raw |= int(raw_words[base + word_index]) << (32 * word_index)
    for name, shift_mask in signal_group.items():
      decoded[name].append((raw & shift_mask.mask) >> shift_mask.shift)
  return decoded


def _top_values(values: list[int], limit: int = 12, *, include_zero: bool = False, decode_instrn: bool = False) -> list[dict[str, Any]]:
  filtered = values if include_zero else [value for value in values if value]
  out = []
  for value, count in Counter(filtered).most_common(limit):
    entry: dict[str, Any] = {"value": value, "hex": f"0x{value:x}", "count": count}
    if decode_instrn and _TENSIX_OPCODES:
      entry["decoded"] = decode_tensix_instruction(value)
    out.append(entry)
  return out


def _bit_counts(decoded: dict[str, list[int]], names: list[str]) -> list[dict[str, Any]]:
  result = []
  for name in names:
    values = decoded.get(name, [])
    count = sum(1 for value in values if value)
    result.append({"name": name, "count": count, "pct": (count * 100.0 / len(values)) if values else 0.0})
  return result


def _summarize_risc_group_a(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  if not group_name.endswith("_group_a"):
    return None
  risc = group_name[: -len("_group_a")]
  commit_pc_name = f"{risc}_dbg_obs_cmt_pc"
  commit_valid_name = f"{risc}_dbg_obs_cmt_vld"
  mem_addr_name = f"{risc}_dbg_obs_mem_addr"
  mem_rden_name = f"{risc}_dbg_obs_mem_rden"
  mem_wren_name = f"{risc}_dbg_obs_mem_wren"
  instr_name = f"{risc}_i_instrn"
  fetch_pc_name = f"{risc}_o_instrn_addr"
  if commit_pc_name not in decoded or commit_valid_name not in decoded:
    return None

  commit_valid = decoded[commit_valid_name]
  commit_pcs = [pc for pc, valid in zip(decoded[commit_pc_name], commit_valid) if valid]
  fetch_pcs = decoded.get(fetch_pc_name, [])
  mem_addrs = decoded.get(mem_addr_name, [])
  mem_rden = decoded.get(mem_rden_name, [])
  mem_wren = decoded.get(mem_wren_name, [])
  instr_words = decoded.get(instr_name, [])

  reads = sum(1 for value in mem_rden if value)
  writes = sum(1 for value in mem_wren if value)
  return {
    "kind": "risc_group_a",
    "risc": risc,
    "signals": {
      "commit_pc": commit_pc_name,
      "commit_valid": commit_valid_name,
      "fetch_pc": fetch_pc_name,
      "mem_addr": mem_addr_name,
      "mem_rden": mem_rden_name,
      "mem_wren": mem_wren_name,
      "instr": instr_name,
    },
    "commit_samples": sum(1 for valid in commit_valid if valid),
    "fetch_samples": sum(1 for value in fetch_pcs if value),
    "mem_reads": reads,
    "mem_writes": writes,
    "top_commit_pcs": _top_values(commit_pcs),
    "top_fetch_pcs": _top_values(fetch_pcs),
    "top_mem_addrs": _top_values([addr for addr, rd, wr in zip(mem_addrs, mem_rden, mem_wren) if addr and (rd or wr)]),
    "top_instr_words": _top_values(instr_words),
  }


def _summarize_tensix_frontend(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  if not group_name.startswith("tensix_frontend_t"):
    return None
  thread = group_name.split("tensix_frontend_t", 1)[1]
  if thread.endswith("_risc_stall"):
    base = f"tensix_frontend_t{thread.split('_', 1)[0]}"
    stall_names = [
      f"{base}_ibuffer_stall",
      f"{base}_risc_cfg_stall",
      f"{base}_risc_gpr_stall",
      f"{base}_risc_tdma_stall",
    ]
    return {
      "kind": "tensix_frontend_risc_stall",
      "thread": int(thread.split("_", 1)[0]),
      "signals": {"stall": stall_names},
      "stall_counts": _bit_counts(decoded, stall_names),
    }

  base = group_name
  active_names = [
    f"{base}_math_inst",
    f"{base}_move_inst",
    f"{base}_pack_inst",
    f"{base}_unpack_inst",
    f"{base}_sfpu_inst",
    f"{base}_sync_inst",
    f"{base}_tdma_inst",
    f"{base}_thcon_inst",
    f"{base}_xsearch_inst",
    f"{base}_cfg_inst",
  ]
  stall_names = [
    f"{base}_stalled_math_inst",
    f"{base}_stalled_move_inst",
    f"{base}_stalled_pack_inst",
    f"{base}_stalled_unpack_inst",
    f"{base}_stalled_sfpu_inst",
    f"{base}_stalled_sync_inst",
    f"{base}_stalled_tdma_inst",
    f"{base}_stalled_thcon_inst",
    f"{base}_stalled_xsearch_inst",
    f"{base}_stalled_cfg_inst",
  ]
  queue_names = [
    f"{base}_ibuffer_empty",
    f"{base}_lsq_full",
    f"{base}_rq_full",
    f"{base}_machine_busy",
    f"{base}_packer_busy",
    f"{base}_unpacker_busy",
    f"{base}_thcon_busy",
    f"{base}_move_busy",
    f"{base}_xsearch_busy",
    f"{base}_tdma_status_busy",
  ]
  return {
    "kind": "tensix_frontend",
    "thread": int(thread),
    "signals": {
      "active": active_names,
      "stall": stall_names,
      "queue": queue_names,
      "thread_inst": f"{base}_thread_inst",
      "lsq_head_gen_no": f"{base}_lsq_head_gen_no",
      "rq_head_gen_no": f"{base}_rq_head_gen_no",
    },
    "active_counts": _bit_counts(decoded, active_names),
    "stall_counts": _bit_counts(decoded, stall_names),
    "queue_counts": _bit_counts(decoded, queue_names),
    "top_thread_inst": _top_values(decoded.get(f"{base}_thread_inst", []), include_zero=True, decode_instrn=True),
    "top_lsq_gen": _top_values(decoded.get(f"{base}_lsq_head_gen_no", []), include_zero=True),
    "top_rq_gen": _top_values(decoded.get(f"{base}_rq_head_gen_no", []), include_zero=True),
  }


def _summarize_rwc_math_pipeline(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  if group_name != "rwc_math_pipeline":
    return None
  bool_names = [
    "rwc0_dec_instr_single_output_row_d",
    "rwc0_fpu_rd_data_required_d",
  ]
  return {
    "kind": "rwc_math_pipeline",
    "signals": {
      "math_instrn": "rwc_math_instrn",
      "winner": "rwc_math_winner",
      "winner_thread": "rwc_math_winner_thread",
      "srca": "rwc0_srca_reg_addr_d",
      "srcb": "rwc0_srcb_reg_addr_d",
      "dst": "rwc0_dst_reg_addr_d",
      "flags": bool_names,
    },
    "flag_counts": _bit_counts(decoded, bool_names),
    "top_math_instrn": _top_values(decoded.get("rwc_math_instrn", []), include_zero=True, decode_instrn=True),
    "top_winner": _top_values(decoded.get("rwc_math_winner", []), include_zero=True),
    "top_winner_thread": _top_values(decoded.get("rwc_math_winner_thread", []), include_zero=True),
    "top_srca": _top_values(decoded.get("rwc0_srca_reg_addr_d", []), include_zero=True),
    "top_srcb": _top_values(decoded.get("rwc0_srcb_reg_addr_d", []), include_zero=True),
    "top_dst": _top_values(decoded.get("rwc0_dst_reg_addr_d", []), include_zero=True),
  }


def _summarize_rwc_pack_unpack(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  if group_name != "rwc_pack_unpack_signals":
    return None
  busy_names = [
    "rwc_tdma_move_busy",
    "rwc_tdma_pack_busy",
    "rwc_tdma_tc_busy",
    "rwc_tdma_unpack_busy",
    "rwc_tdma_xsearch_busy",
    "rwc_cg_regblocks_busy_d",
    "rwc_i_cg_regblocks_en",
    "rwc_dest_apply_relu",
  ]
  return {
    "kind": "rwc_pack_unpack",
    "signals": {
      "busy": busy_names,
      "state": "rwc_tdma_dstac_regif_state_id",
      "srcb": "rwc_srcb_reg_addr",
      "srcb_d": "rwc_srcb_reg_addr_d",
    },
    "busy_counts": _bit_counts(decoded, busy_names),
    "top_state": _top_values(decoded.get("rwc_tdma_dstac_regif_state_id", []), include_zero=True),
    "top_srcb": _top_values(decoded.get("rwc_srcb_reg_addr", []), include_zero=True),
    "top_srcb_d": _top_values(decoded.get("rwc_srcb_reg_addr_d", []), include_zero=True),
  }


def _summarize_rwc_tdma_core(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  if group_name != "rwc_tdma_core_signals":
    return None
  bool_names = [
    "rwc_tdma_srca_regif_wren",
    "rwc_tdma_srcb_regif_wren",
    "rwc0_tdma_srca_unpack_src_reg_set_upd",
    "rwc_tdma_srcb_unpack_src_reg_set_upd",
    "rwc_debug_issue0_in_3_srca_write_ready",
    "rwc_debug_issue0_in_3_srcb_write_ready",
  ]
  return {
    "kind": "rwc_tdma_core",
    "signals": {
      "flags": bool_names,
      "srca_addr": "rwc_tdma_srca_regif_addr",
      "srcb_addr": "rwc_tdma_srcb_regif_addr",
      "srca_thread": "rwc_tdma_srca_regif_thread_id",
      "srcb_thread": "rwc_tdma_srcb_regif_thread_id",
      "srca_state": "rwc_tdma_srca_regif_state_id",
      "srcb_state": "rwc_tdma_srcb_regif_state_id",
      "dst_thread": "rwc_tdma_dstac_regif_thread_id",
    },
    "flag_counts": _bit_counts(decoded, bool_names),
    "top_srca_addr": _top_values(decoded.get("rwc_tdma_srca_regif_addr", []), include_zero=True),
    "top_srcb_addr": _top_values(decoded.get("rwc_tdma_srcb_regif_addr", []), include_zero=True),
    "top_srca_thread": _top_values(decoded.get("rwc_tdma_srca_regif_thread_id", []), include_zero=True),
    "top_srcb_thread": _top_values(decoded.get("rwc_tdma_srcb_regif_thread_id", []), include_zero=True),
    "top_srca_state": _top_values(decoded.get("rwc_tdma_srca_regif_state_id", []), include_zero=True),
    "top_srcb_state": _top_values(decoded.get("rwc_tdma_srcb_regif_state_id", []), include_zero=True),
    "top_dst_thread": _top_values(decoded.get("rwc_tdma_dstac_regif_thread_id", []), include_zero=True),
  }


def _summarize_group(group_name: str, decoded: dict[str, list[int]]) -> dict[str, Any] | None:
  for func in (
    _summarize_risc_group_a,
    _summarize_tensix_frontend,
    _summarize_rwc_math_pipeline,
    _summarize_rwc_pack_unpack,
    _summarize_rwc_tdma_core,
  ):
    summary = func(group_name, decoded)
    if summary is not None:
      return summary
  return None


def _elf_text_base(elf_bytes: bytes) -> int:
  text_segments = [segment for segment in iter_pt_load(elf_bytes) if segment.flags & 1]
  if not text_segments:
    raise RuntimeError("no executable PT_LOAD segment found in ELF")
  return text_segments[0].paddr


def _elf_text_limit(elf_bytes: bytes) -> int:
  text_segments = [segment for segment in iter_pt_load(elf_bytes) if segment.flags & 1]
  if not text_segments:
    raise RuntimeError("no executable PT_LOAD segment found in ELF")
  return max(segment.paddr + max(segment.memsz, len(segment.data)) for segment in text_segments)


def _trace_target_risc(target: str) -> str | None:
  if target.endswith("_pc"):
    return target[: -len("_pc")]
  for suffix in ("_group_a", "_group_b", "_group_c", "_group_d"):
    if target.endswith(suffix):
      return target[: -len(suffix)]
  return None


def build_symbol_context(program: Any, ir_commands: list[Any], trace_core: Core, target: str) -> TraceSymbolContext | None:
  risc = _trace_target_risc(target)
  if risc is None:
    return None
  elf_bytes = getattr(program, "_trace_elfs", {}).get(risc)
  firmware_elf = getattr(program, "_trace_firmware_elfs", {}).get(risc)
  proc_index = {"brisc": 0, "ncrisc": 1, "trisc0": 2, "trisc1": 3, "trisc2": 4}.get(risc)
  if proc_index is None:
    return None
  runtime_text_base = None
  for cmd in ir_commands:
    if not isinstance(cmd, Write) or cmd.addr != TensixL1.LAUNCH or trace_core not in cmd.cores:
      continue
    if isinstance(cmd.data, list):
      blob = cmd.data[cmd.cores.index(trace_core)]
    else:
      blob = cmd.data
    launch = LaunchMsg.from_buffer_copy(blob)
    runtime_text_offset = int(launch.kernel_config.kernel_text_offset[proc_index])
    if runtime_text_offset:
      runtime_text_base = TensixL1.KERNEL_CONFIG_BASE + runtime_text_offset
      break
  if elf_bytes is None and firmware_elf is None:
    return None
  kernel_text_base = _elf_text_base(elf_bytes) if elf_bytes else None
  kernel_text_limit = _elf_text_limit(elf_bytes) if elf_bytes and runtime_text_base is not None else None
  firmware_text_base = _elf_text_base(firmware_elf) if firmware_elf else None
  firmware_text_limit = _elf_text_limit(firmware_elf) if firmware_elf else None
  return TraceSymbolContext(
    risc=risc,
    kernel_runtime_base=runtime_text_base,
    kernel_runtime_limit=(runtime_text_base + (kernel_text_limit - kernel_text_base)) if (runtime_text_base is not None and kernel_text_base is not None and kernel_text_limit is not None) else None,
    kernel_elf_text_base=kernel_text_base,
    kernel_elf_bytes=elf_bytes,
    firmware_text_base=firmware_text_base,
    firmware_text_limit=firmware_text_limit,
    firmware_elf_bytes=firmware_elf,
    kernel_symbols=[(symbol.address, symbol.name) for symbol in list_symbols(elf_bytes, demangle=True)] if elf_bytes else [],
    firmware_symbols=[(symbol.address, symbol.name) for symbol in list_symbols(firmware_elf, demangle=True)] if firmware_elf else [],
    cache={},
  )


def _nearest_symbol(symbols: list[tuple[int, str]], elf_pc: int) -> str | None:
  if not symbols:
    return None
  addresses = [address for address, _ in symbols]
  idx = bisect_right(addresses, elf_pc) - 1
  if idx < 0:
    return None
  address, name = symbols[idx]
  offset = elf_pc - address
  return name if offset == 0 else f"{name}+0x{offset:x}"


def symbolize_runtime_pc(context: TraceSymbolContext | None, runtime_pc: int) -> dict[str, Any] | None:
  if context is None or runtime_pc <= 0:
    return None
  cached = context.cache.get(runtime_pc)
  if cached is not None:
    return cached
  image = "unknown"
  elf_bytes = None
  elf_pc = runtime_pc
  symbols: list[tuple[int, str]] = []
  if (
    context.kernel_elf_bytes is not None
    and context.kernel_runtime_base is not None
    and context.kernel_elf_text_base is not None
    and runtime_pc >= context.kernel_runtime_base
  ):
    image = "kernel"
    elf_bytes = context.kernel_elf_bytes
    elf_pc = context.kernel_elf_text_base + (runtime_pc - context.kernel_runtime_base)
    symbols = context.kernel_symbols
  elif (
    context.firmware_elf_bytes is not None
    and context.firmware_text_base is not None
    and context.firmware_text_limit is not None
    and context.firmware_text_base <= runtime_pc < context.firmware_text_limit
  ):
    image = "firmware"
    elf_bytes = context.firmware_elf_bytes
    symbols = context.firmware_symbols
  elif context.kernel_elf_bytes is not None:
    image = "kernel"
    elf_bytes = context.kernel_elf_bytes
    if context.kernel_runtime_base is not None and context.kernel_elf_text_base is not None:
      elf_pc = context.kernel_elf_text_base + (runtime_pc - context.kernel_runtime_base)
    symbols = context.kernel_symbols
  elif context.firmware_elf_bytes is not None:
    image = "firmware"
    elf_bytes = context.firmware_elf_bytes
    symbols = context.firmware_symbols
  if elf_bytes is None:
    return None
  try:
    location = resolve_source_location(elf_bytes, elf_pc)
  except Exception:
    location = None
  try:
    asm = resolve_assembly_line(elf_bytes, elf_pc)
  except Exception:
    asm = None
  line = location.line if location and location.line and location.line > 0 else None
  entry = {
    "runtime_pc": runtime_pc,
    "runtime_pc_hex": f"0x{runtime_pc:x}",
    "elf_pc": elf_pc,
    "elf_pc_hex": f"0x{elf_pc:x}",
    "function": (location.function if location and location.function != "??" else _nearest_symbol(symbols, elf_pc)) or "??",
    "file": location.file if location else "??",
    "line": line,
    "asm": asm.text if asm else None,
    "risc": context.risc,
    "image": image,
  }
  context.cache[runtime_pc] = entry
  return entry


def enrich_trace_with_symbols(trace: dict[str, Any], context: TraceSymbolContext | None) -> dict[str, Any]:
  if context is None:
    return trace
  trace["symbol_context"] = {
    "risc": context.risc,
    "kernel_runtime_base": context.kernel_runtime_base,
    "kernel_runtime_base_hex": None if context.kernel_runtime_base is None else f"0x{context.kernel_runtime_base:x}",
    "kernel_elf_text_base": context.kernel_elf_text_base,
    "kernel_elf_text_base_hex": None if context.kernel_elf_text_base is None else f"0x{context.kernel_elf_text_base:x}",
    "firmware_text_base": context.firmware_text_base,
    "firmware_text_base_hex": None if context.firmware_text_base is None else f"0x{context.firmware_text_base:x}",
  }
  group = trace.get("group")
  if not group:
    return trace
  summary = group.get("summary")
  if not summary:
    return trace
  for key in ("top_commit_pcs", "top_fetch_pcs"):
    enriched = []
    for entry in summary.get(key, []):
      symbol = symbolize_runtime_pc(context, entry.get("value", 0))
      merged = dict(entry)
      if symbol is not None:
        merged["symbol"] = symbol
      enriched.append(merged)
    summary[key] = enriched
  return trace


def _resolve_trace_spec(raw: str) -> tuple[str, str]:
  if raw in _TRACE_PRESETS:
    return _TRACE_PRESETS[raw]
  if raw == "pc":
    return "signal", "trisc1_pc"
  if raw.startswith("group:"):
    return "group", raw.split(":", 1)[1]
  if raw in debug_bus_signal_map:
    return "signal", raw
  if raw in group_map:
    return "group", raw
  raise ValueError(
    f"unsupported TRACE spec {raw!r}; use a preset like br/nc/tr0/tr1/tr2/tf0/tf1/tf2, "
    "a tt-exalens signal name, or a group name"
  )


@dataclass(frozen=True)
class TraceConfig:
  spec: str
  mode: str
  target: str
  core_index: int
  max_samples: int
  json_path: str | None
  summarize_top: int

  @classmethod
  def from_env(cls) -> TraceConfig | None:
    raw = os.environ.get("TRACE", "").strip()
    if not raw or raw.lower() in {"0", "false", "no", "off"}:
      return None
    spec = raw
    mode, target = _resolve_trace_spec(raw)
    core_index = int(os.environ.get("TRACE_CORE_INDEX", "0"), 0)
    max_samples = int(os.environ.get("TRACE_MAX_SAMPLES", "500000"), 0)
    summarize_top = int(os.environ.get("TRACE_TOP", "5"), 0)
    json_path = os.environ.get("TRACE_JSON") or None
    return cls(
      spec=spec,
      mode=mode,
      target=target,
      core_index=core_index,
      max_samples=max_samples,
      json_path=json_path,
      summarize_top=max(0, summarize_top),
    )


@dataclass(frozen=True)
class TraceBoundary:
  program_index: int
  event_id: int
  sample_count: int
  timestamp_ns: int
  source: str


@dataclass
class TraceSymbolContext:
  risc: str
  kernel_runtime_base: int | None
  kernel_runtime_limit: int | None
  kernel_elf_text_base: int | None
  kernel_elf_bytes: bytes | None
  firmware_text_base: int | None
  firmware_text_limit: int | None
  firmware_elf_bytes: bytes | None
  kernel_symbols: list[tuple[int, str]]
  firmware_symbols: list[tuple[int, str]]
  cache: dict[int, dict[str, Any]]


class _TraceSampler(threading.Thread):
  def __init__(self, fd: int, core: Core, cq_hw: CQSysmem, config: TraceConfig, event_ids: list[int]):
    super().__init__(name="bh-trace", daemon=True)
    self.fd = fd
    self.core = core
    self.cq_hw = cq_hw
    self.config = config
    self.event_ids = event_ids
    self.event_to_program = {event_id: i for i, event_id in enumerate(event_ids)}
    self.capture_start_ns = 0
    self.capture_end_ns = 0
    self.count = 0
    self.truncated = False
    self.boundaries: list[TraceBoundary] = []
    self._host_waits: dict[int, int] = {}
    self._stop_requested = threading.Event()
    self._graceful_stop = True
    self._target_shift = 0
    self._seen_event_ids: set[int] = set()

    if config.mode == "signal":
      signal = debug_bus_signal_map[config.target]
      if signal.across_groups or "/" in config.target:
        raise ValueError(f"TRACE signal {config.target!r} is not atomically readable")
      self.words_per_sample = 1
      self.config_words = [dbg_bus_cntl(signal.sig_sel, signal.daisy_sel, signal.rd_sel)]
      self._target_mask = signal.mask
      self._target_shift = _mask_shift(signal.mask)
    else:
      daisy_sel, sig_sel = group_map[config.target]
      self.words_per_sample = 4
      self.config_words = [dbg_bus_cntl(sig_sel, daisy_sel, rd_sel) for rd_sel in range(4)]
      self._target_mask = 0xFFFFFFFF

    if config.max_samples <= 0:
      raise ValueError("TRACE_MAX_SAMPLES must be positive")
    self.timestamps_ns = array("Q", [0]) * config.max_samples
    self.raw_words = array("I", [0]) * (config.max_samples * self.words_per_sample)
    self._cursor_16b, self._cursor_toggle = cq_hw.completion_cursor

  def stop(self, graceful: bool):
    self._graceful_stop = graceful
    self._stop_requested.set()

  def note_host_completion(self, event_id: int):
    self._host_waits[event_id] = time.perf_counter_ns()

  def _advance_completion_cursor(self):
    self._cursor_16b += self.cq_hw.completion_page_16b
    if self._cursor_16b >= self.cq_hw.completion_end_16b:
      self._cursor_16b = self.cq_hw.completion_base_16b
      self._cursor_toggle ^= 1

  def _poll_completion_events(self):
    wr_16b, wr_toggle = self.cq_hw.peek_completion_write_pointer()
    while self._cursor_16b != wr_16b or self._cursor_toggle != wr_toggle:
      event_id = self.cq_hw.peek_completion_event(self._cursor_16b)
      if event_id in self.event_to_program and event_id not in self._seen_event_ids:
        self._seen_event_ids.add(event_id)
        self.boundaries.append(
          TraceBoundary(
            program_index=self.event_to_program[event_id],
            event_id=event_id,
            sample_count=self.count,
            timestamp_ns=time.perf_counter_ns(),
            source="trace",
          )
        )
      self._advance_completion_cursor()

  def run(self):
    import ctypes
    from profiler.trace_sampler_ffi import CSampler
    cs = CSampler()
    stop_flag = ctypes.c_int(0)
    ctrl_off = DBG_BUS_CTRL - DEBUG_TLB_BASE
    data_off = DBG_BUS_RD_DATA - DEBUG_TLB_BASE

    def _watch_stop():
      self._stop_requested.wait()
      stop_flag.value = 1
    watcher = threading.Thread(target=_watch_stop, daemon=True)
    watcher.start()

    with TLBWindow(self.fd, start=self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT) as win:
      result, c_boundaries = cs.run(
        tlb_mm=win.mm,
        ctrl_off=ctrl_off,
        data_off=data_off,
        config_words=self.config_words,
        max_samples=self.config.max_samples,
        timestamps_ns=self.timestamps_ns,
        raw_words=self.raw_words,
        event_ids=self.event_ids,
        cq_hw=self.cq_hw,
        stop_flag=stop_flag,
        fast=True,
      )

    self.count = result.sample_count
    self.truncated = bool(result.truncated)
    self.capture_start_ns = result.capture_start_ns
    self.capture_end_ns = result.capture_end_ns
    for b in c_boundaries:
      eid = b.event_id
      if eid in self.event_to_program and eid not in self._seen_event_ids:
        self._seen_event_ids.add(eid)
        self.boundaries.append(TraceBoundary(
          program_index=self.event_to_program[eid],
          event_id=eid,
          sample_count=b.sample_count,
          timestamp_ns=b.timestamp_ns,
          source="trace",
        ))
    self.mmio_profile = {
      "write_count": result.mmio_write_count,
      "read_count": result.mmio_read_count,
      "write_total_ns": result.mmio_write_ns,
      "read_total_ns": result.mmio_read_ns,
      "bytes_per_read": 4,
      "bytes_per_write": 4,
    }

  def finalize(self, program_names: list[str], timings: list[dict[str, Any]]) -> dict[str, Any]:
    boundaries_by_event = {boundary.event_id: boundary for boundary in self.boundaries}
    count = self.count
    records = []
    prev_end = 0
    for index, event_id in enumerate(self.event_ids):
      boundary = boundaries_by_event.get(event_id)
      if boundary is None:
        boundary = TraceBoundary(
          program_index=index,
          event_id=event_id,
          sample_count=count,
          timestamp_ns=self._host_waits.get(event_id, self.capture_end_ns),
          source="host-fallback",
        )
      sample_end = max(prev_end, min(boundary.sample_count, count))
      timing = timings[index] if index < len(timings) else {}
      records.append({
        "index": index,
        "name": program_names[index],
        "event_id": event_id,
        "sample_start": prev_end,
        "sample_end": sample_end,
        "samples": sample_end - prev_end,
        "completion_timestamp_ns": boundary.timestamp_ns,
        "boundary_source": boundary.source,
        "device_cycles": timing.get("cycles"),
        "device_us": timing.get("us"),
      })
      prev_end = sample_end

    elapsed_ns = max(1, self.capture_end_ns - self.capture_start_ns)
    mmio = getattr(self, "mmio_profile", None)
    if mmio and mmio["read_count"] > 0:
      mmio["read_avg_ns"] = mmio["read_total_ns"] / mmio["read_count"]
      mmio["write_avg_ns"] = mmio["write_total_ns"] / mmio["write_count"]
      mmio["total_ns"] = mmio["read_total_ns"] + mmio["write_total_ns"]
      mmio["total_bytes_read"] = mmio["read_count"] * 4
      mmio["total_bytes_written"] = mmio["write_count"] * 4
      mmio["pct_of_capture"] = 100.0 * mmio["total_ns"] / elapsed_ns
    result = {
      "config": {
        "spec": self.config.spec,
        "mode": self.config.mode,
        "target": self.config.target,
        "core": list(self.core),
        "core_index": self.config.core_index,
        "words_per_sample": self.words_per_sample,
        "max_samples": self.config.max_samples,
      },
      "capture": {
        "sample_count": count,
        "capture_start_ns": self.capture_start_ns,
        "capture_end_ns": self.capture_end_ns,
        "elapsed_ns": elapsed_ns,
        "sample_rate_hz": count * 1e9 / elapsed_ns,
        "truncated": self.truncated,
        "mmio": mmio,
      },
      "programs": records,
      "samples": {
        "timestamps_ns": self.timestamps_ns[:count].tolist(),
        "raw_words": self.raw_words[: count * self.words_per_sample].tolist(),
      },
    }
    if self.config.mode == "signal":
      values = [
        (self.raw_words[i] & self._target_mask) >> self._target_shift
        for i in range(count)
      ]
      result["signal"] = {
        "name": self.config.target,
        "mask": self._target_mask,
        "shift": self._target_shift,
        "values": values,
      }
    else:
      result["group"] = {
        "name": self.config.target,
        "signals": sorted(DEBUG_BUS_INIT.signal_groups[self.config.target].keys()),
      }
    return result


class TraceCapture:
  def __init__(self, fd: int, cq_hw: CQSysmem, cores: list[Core], config: TraceConfig, event_ids: list[int]):
    if config.core_index < 0 or config.core_index >= len(cores):
      raise ValueError(f"TRACE_CORE_INDEX={config.core_index} is out of range for {len(cores)} worker cores")
    self.config = config
    self.core = cores[config.core_index]
    self.sampler = _TraceSampler(fd, self.core, cq_hw, config, event_ids)

  def start(self):
    self.sampler.start()

  def note_host_completion(self, event_id: int):
    self.sampler.note_host_completion(event_id)

  def stop(self, graceful: bool = True):
    self.sampler.stop(graceful=graceful)
    self.sampler.join()

  def finalize(self, program_names: list[str], timings: list[dict[str, Any]]) -> dict[str, Any]:
    result = self.sampler.finalize(program_names, timings)
    self._print_summary(result)
    if self.config.json_path:
      path = Path(self.config.json_path)
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(json.dumps(result))
      print(f"  trace: wrote raw data to {path}")
    return result

  def _print_summary(self, result: dict[str, Any]):
    capture = result["capture"]
    config = result["config"]
    rate_khz = capture["sample_rate_hz"] / 1e3
    print(
      f"  trace: {config['target']} on core ({self.core[0]},{self.core[1]}) "
      f"captured {capture['sample_count']:,} samples at {rate_khz:,.1f} kHz"
    )
    mmio = capture.get("mmio")
    if mmio and mmio.get("read_count"):
      read_avg_us = mmio["read_avg_ns"] / 1e3
      write_avg_us = mmio["write_avg_ns"] / 1e3
      total_ms = mmio["total_ns"] / 1e6
      pct = mmio["pct_of_capture"]
      print(
        f"  trace: mmio profiling — {mmio['read_count']:,} reads, {mmio['write_count']:,} writes "
        f"(4 bytes each)"
      )
      print(
        f"  trace: read avg {read_avg_us:.2f} us, write avg {write_avg_us:.2f} us, "
        f"total {total_ms:,.1f} ms ({pct:.1f}% of capture wall time)"
      )
      print(
        f"  trace: total read {mmio['total_bytes_read']:,} bytes, "
        f"total written {mmio['total_bytes_written']:,} bytes"
      )
    if capture["truncated"]:
      print(f"  trace: sample buffer filled at TRACE_MAX_SAMPLES={config['max_samples']:,}")
    if self.config.mode == "signal" and self.config.summarize_top > 0:
      values = result["signal"]["values"]
      if values:
        top = Counter(values).most_common(self.config.summarize_top)
        summary = ", ".join(f"0x{value:x} ({count})" for value, count in top)
        print(f"  trace: top values {summary}")
    elif self.config.mode == "group":
      decoded = _decode_group_samples(config["target"], result["samples"]["raw_words"], config["words_per_sample"])
      summary = _summarize_group(config["target"], decoded)
      if summary and summary.get("kind") == "risc_group_a" and summary["top_commit_pcs"]:
        top = ", ".join(f"{entry['hex']} ({entry['count']})" for entry in summary["top_commit_pcs"][: self.config.summarize_top])
        print(f"  trace: top commit PCs {top}")
      elif summary and summary.get("kind") == "tensix_frontend":
        active = [entry for entry in summary["active_counts"] if entry["count"] > 0][: self.config.summarize_top]
        if active:
          top = ", ".join(f"{entry['name'].split('_t', 1)[1]} ({entry['count']})" for entry in active)
          print(f"  trace: active frontend states {top}")
    for program in result["programs"]:
      duration = program.get("device_us")
      duration_text = f", {duration:,.1f} us" if isinstance(duration, (int, float)) else ""
      print(
        f"  trace[{program['index']}]: {program['samples']:,} samples for "
        f"{program['name'] or '<unnamed>'}{duration_text}"
      )


def build_trace_capture(fd: int, cq_hw: CQSysmem, cores: list[Core], event_ids: list[int]) -> TraceCapture | None:
  config = TraceConfig.from_env()
  if config is None:
    return None
  return TraceCapture(fd, cq_hw, cores, config, event_ids)


def estimate_sampling_rate(spec: str | None = None) -> dict[str, Any] | None:
  raw = spec or os.environ.get("TRACE", "").strip()
  if not raw:
    return None
  mode, target = _resolve_trace_spec(raw)
  config = TraceConfig(spec=raw, mode=mode, target=target, core_index=0, max_samples=1, json_path=None, summarize_top=0)
  reads_per_sample = 1 if config.mode == "signal" else 4
  per_read_us = 10.0
  sample_rate_hz = 1e6 / (per_read_us * reads_per_sample)
  return {
    "mode": config.mode,
    "target": config.target,
    "reads_per_sample": reads_per_sample,
    "estimated_sample_rate_hz": sample_rate_hz,
    "estimated_period_us": per_read_us * reads_per_sample,
  }


def attach_trace_to_profile(
  profile_data: dict[str, Any] | None,
  trace_data: dict[str, Any] | None,
  *,
  tensix_x: list[int] | None = None,
  dispatch_cores: list[list[int]] | None = None,
  harvested_dram_bank: int | None = None,
) -> dict[str, Any] | None:
  if profile_data is None and trace_data is None:
    return None

  if profile_data is None:
    merged: dict[str, Any] = {
      "dispatch_mode": "fast",
      "harvested_dram_bank": harvested_dram_bank,
      "tensix_x": tensix_x or [],
      "dispatch_cores": dispatch_cores or [],
      "programs": [],
    }
    if trace_data:
      for trace_prog in trace_data.get("programs", []):
        merged["programs"].append({
          "index": trace_prog["index"],
          "name": trace_prog.get("name"),
          "cores": [],
          "profiles": {},
          "sources": {},
          "disassembly": {},
        })
  else:
    merged = deepcopy(profile_data)

  if tensix_x is not None and "tensix_x" not in merged:
    merged["tensix_x"] = list(tensix_x)
  if dispatch_cores is not None and "dispatch_cores" not in merged:
    merged["dispatch_cores"] = [list(core) for core in dispatch_cores]
  if harvested_dram_bank is not None and merged.get("harvested_dram_bank") is None:
    merged["harvested_dram_bank"] = harvested_dram_bank

  if trace_data is None:
    return merged

  merged["trace_capture"] = {
    "config": trace_data.get("config", {}),
    "capture": trace_data.get("capture", {}),
  }
  by_index = {prog.get("index"): prog for prog in merged.get("programs", [])}
  for trace_prog in trace_data.get("programs", []):
    prog = by_index.get(trace_prog.get("index"))
    if prog is None:
      prog = {
        "index": trace_prog["index"],
        "name": trace_prog.get("name"),
        "cores": [],
        "profiles": {},
        "sources": {},
        "disassembly": {},
      }
      merged.setdefault("programs", []).append(prog)
      by_index[trace_prog["index"]] = prog
    prog["trace"] = slice_program_trace(trace_data, trace_prog)
  merged["programs"].sort(key=lambda prog: prog.get("index", 0))
  return merged


def slice_program_trace(trace_data: dict[str, Any], trace_prog: dict[str, Any]) -> dict[str, Any]:
  lo = int(trace_prog.get("sample_start", 0))
  hi = int(trace_prog.get("sample_end", lo))
  config = trace_data.get("config", {})
  capture = trace_data.get("capture", {})
  words_per_sample = int(config.get("words_per_sample", 1))
  samples = trace_data.get("samples", {})
  timestamps_ns = list(samples.get("timestamps_ns", [])[lo:hi])
  raw_words = list(samples.get("raw_words", [])[lo * words_per_sample : hi * words_per_sample])
  elapsed_ns = max(1, timestamps_ns[-1] - timestamps_ns[0]) if len(timestamps_ns) > 1 else 0
  trace = {
    "config": dict(config),
    "capture": dict(capture),
    "event_id": trace_prog.get("event_id"),
    "sample_start": lo,
    "sample_end": hi,
    "samples": hi - lo,
    "completion_timestamp_ns": trace_prog.get("completion_timestamp_ns"),
    "boundary_source": trace_prog.get("boundary_source"),
    "device_cycles": trace_prog.get("device_cycles"),
    "device_us": trace_prog.get("device_us"),
    "sample_rate_hz": ((hi - lo - 1) * 1e9 / elapsed_ns) if elapsed_ns and hi - lo > 1 else 0,
    "timestamps_ns": timestamps_ns,
    "raw_words": raw_words,
  }
  if "signal" in trace_data:
    values = list(trace_data["signal"].get("values", [])[lo:hi])
    top_values = []
    for value, count in Counter(values).most_common(16):
      top_values.append({"value": value, "hex": f"0x{value:x}", "count": count})
    trace["signal"] = {
      "name": trace_data["signal"].get("name"),
      "mask": trace_data["signal"].get("mask"),
      "shift": trace_data["signal"].get("shift"),
      "values": values,
      "top_values": top_values,
    }
  if "group" in trace_data:
    group_name = trace_data["group"].get("name")
    decoded = _decode_group_samples(group_name, raw_words, words_per_sample)
    trace["group"] = dict(trace_data["group"])
    trace["group"]["decoded_signals"] = decoded
    summary = _summarize_group(group_name, decoded)
    if summary is not None:
      trace["group"]["summary"] = summary
  return trace
