#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "blackhole-py-old" / "firmware" / "disasms"
sys.path.insert(0, str(ROOT))

import dsl
from dsl import Reg, TTInst, decode, decode_tensix
from examples import add1
from ttk import addrs
from ttk.debug import Debug
from ttk.tensix import TensixRegs

INSTRN_BUF = TensixRegs.INSTRN_BUF_BASE
PC_BUF_BASE = 0xFFE80000
MOP_CFG = add1.TENSIX_MOP_CFG
CFG_BASE = TensixRegs.CFG_BASE
REGFILE_BASE = TensixRegs.REGFILE_BASE

REG_ALIASES = {
  "zero": 0, "ra": 1, "sp": 2, "gp": 3, "tp": 4,
  "t0": 5, "t1": 6, "t2": 7, "s0": 8, "fp": 8, "s1": 9,
  "a0": 10, "a1": 11, "a2": 12, "a3": 13, "a4": 14, "a5": 15,
  "a6": 16, "a7": 17, "s2": 18, "s3": 19, "s4": 20, "s5": 21,
  "s6": 22, "s7": 23, "s8": 24, "s9": 25, "s10": 26, "s11": 27,
  "t3": 28, "t4": 29, "t5": 30, "t6": 31,
}
REG_NAMES = {v: k for k, v in REG_ALIASES.items()}
REG_NAMES[8] = "s0"


def _collect_constant_names() -> dict[int, list[str]]:
  names: dict[int, list[str]] = {}

  def add(value: object, name: str):
    if isinstance(value, int):
      names.setdefault(value & 0xFFFFFFFF, []).append(name)

  for module, prefix in ((add1, "add1"),):
    for name, value in vars(module).items():
      if name.isupper():
        add(value, f"{prefix}.{name}")

  for cls_name in (
    "TensixL1", "TensixMMIO", "NOC", "Launch", "Mailbox", "CircularBuffer",
    "BriscMailbox", "NcriscMailbox", "TriscMailbox", "Dispatch",
  ):
    cls = getattr(addrs, cls_name)
    for name, value in vars(cls).items():
      if name.startswith("_"):
        continue
      if isinstance(value, dict):
        for key, inner in value.items():
          if isinstance(inner, int):
            add(inner, f"{cls_name}.{name}[{key!r}]")
      else:
        add(value, f"{cls_name}.{name}")

  for name, value in vars(TensixRegs).items():
    if not name.startswith("_"):
      add(value, f"TensixRegs.{name}")

  for value in names.values():
    value.sort(key=lambda s: (len(s), s))
  return names


CONSTANT_NAMES = _collect_constant_names()


def _load_ttsim_tile_regs() -> tuple[list[tuple[int, int, str]], dict[str, dict[int, str]]]:
  path = ROOT.parent / "ttsim" / "data" / "bh" / "tile_regs.json"
  if not path.exists():
    return [], {}
  data = json.loads(path.read_text())
  ranges = [
    (int(entry["base"], 0), int(entry["limit"], 0), entry["name"])
    for entry in data.get("address_map", [])
  ]
  regs: dict[str, dict[int, str]] = {}
  for group in data.get("regs", []):
    regs[group["name"]] = {
      int(reg["offset"], 0): reg["name"]
      for reg in group.get("regs", [])
    }
  return ranges, regs


TTSIM_ADDR_RANGES, TTSIM_REGS = _load_ttsim_tile_regs()


def _load_ttsim_tensix_regs() -> dict:
  path = ROOT.parent / "ttsim" / "data" / "bh" / "tensix_regs.json"
  if not path.exists():
    return {}
  return json.loads(path.read_text())


TTSIM_TENSIX_REGS = _load_ttsim_tensix_regs()

CB_INTERFACE_FIELDS = {
  0: "fifo_size",
  4: "fifo_limit",
  8: "page_size",
  12: "num_pages",
  16: "rd_ptr",
  20: "wr_ptr",
  24: "tiles_acked_received",
}

def dynamic_constant_name(addr: int, role: str | None = None) -> str | None:
  addr &= 0xFFFFFFFF
  cb_bases = []
  if role == "brisc":
    cb_bases.append(("BriscCB", addrs.BriscMailbox.CB_INTERFACE))
  elif role == "ncrisc":
    cb_bases.append(("NcriscCB", addrs.NcriscMailbox.CB_INTERFACE))
  elif role and role.startswith("trisc"):
    cb_bases.append(("TriscCB", addrs.TriscMailbox.DATA_COMMON["cb_interface"]))
  else:
    cb_bases.extend([
      ("BriscCB", addrs.BriscMailbox.CB_INTERFACE),
      ("NcriscCB", addrs.NcriscMailbox.CB_INTERFACE),
      ("TriscCB", addrs.TriscMailbox.DATA_COMMON["cb_interface"]),
    ])

  for prefix, base in cb_bases:
    off = addr - base
    if 0 <= off < addrs.CircularBuffer.NUM_CIRCULAR_BUFFERS * addrs.CircularBuffer.LOCAL_INTERFACE_SIZE:
      cb_index, field_off = divmod(off, addrs.CircularBuffer.LOCAL_INTERFACE_SIZE)
      field = CB_INTERFACE_FIELDS.get(field_off)
      if field is not None:
        return f"{prefix}[{cb_index}].{field}"

  for base, name in (
    (addrs.CircularBuffer.SYNC_TILES_ACKED_BASE, "CB_SYNC.tiles_acked"),
    (addrs.CircularBuffer.SYNC_TILES_RECEIVED_BASE, "CB_SYNC.tiles_received"),
  ):
    off = addr - base
    if 0 <= off < addrs.CircularBuffer.NUM_CIRCULAR_BUFFERS * addrs.CircularBuffer.SYNC_STRIDE and off % addrs.CircularBuffer.SYNC_STRIDE == 0:
      return f"{name}[{off // addrs.CircularBuffer.SYNC_STRIDE}]"

  if 0xFFB20000 <= addr < 0xFFB40000:
    noc = 1 if addr >= 0xFFB30000 else 0
    base = 0xFFB30000 if noc else 0xFFB20000
    off = addr - base
    noc_regs = TTSIM_REGS.get("noc_regs", {})
    cmd_buf = off >> addrs.NOC.CMD_BUF_OFFSET_BIT
    reg_off = off - (cmd_buf << addrs.NOC.CMD_BUF_OFFSET_BIT)
    reg_name = noc_regs.get(reg_off)
    if reg_name is not None:
      if reg_off < 0x80:
        return f"NOC{noc}.{reg_name}[buf{cmd_buf}]"
      return f"NOC{noc}.{reg_name}"
    return f"NOC{noc}.regs+0x{off:x}"

  for base, limit, range_name in TTSIM_ADDR_RANGES:
    if base <= addr <= limit:
      regs = TTSIM_REGS.get(range_name, {})
      off = addr - base
      reg_name = regs.get(off)
      if reg_name is not None:
        return f"{range_name}.{reg_name}"
      if range_name != "riscv_local_mem":
        return f"{range_name}+0x{off:x}"

  return None


def _name_allowed_for_role(name: str, addr: int, role: str | None) -> bool:
  if role is None:
    return True
  if role.startswith("trisc") and 0xFFB00000 <= addr < 0xFFB02000:
    return (
      name.startswith("add1.") or
      name.startswith("TriscMailbox.") or
      name.startswith("TensixMMIO.") or
      name.startswith("TensixL1.")
    )
  if role == "brisc" and 0xFFB00000 <= addr < 0xFFB02000:
    return (
      name.startswith("BriscMailbox.") or
      name.startswith("CircularBuffer.") or
      name.startswith("TensixL1.")
    )
  if role == "ncrisc" and 0xFFB00000 <= addr < 0xFFB02000:
    return (
      name.startswith("NcriscMailbox.") or
      name.startswith("CircularBuffer.") or
      name.startswith("TensixL1.")
    )
  return True


def _name_preference(name: str, role: str | None) -> tuple[int, int, str]:
  role_prefix = {
    "brisc": "BriscMailbox.",
    "ncrisc": "NcriscMailbox.",
    "trisc0": "TriscMailbox.",
    "trisc1": "TriscMailbox.",
    "trisc2": "TriscMailbox.",
  }.get(role)
  prefixes = [
    "add1.",
    role_prefix,
    "CircularBuffer.",
    "NOC.",
    "TensixRegs.",
    "TensixMMIO.",
    "TensixL1.",
    "Mailbox.",
    "Dispatch.",
    "Launch.",
  ]
  for i, prefix in enumerate(p for p in prefixes if p is not None):
    if name.startswith(prefix):
      return i, len(name), name
  return len(prefixes), len(name), name


def constant_name(addr: int, role: str | None = None) -> str | None:
  names = CONSTANT_NAMES.get(addr & 0xFFFFFFFF)
  filtered = []
  if names:
    filtered = [name for name in names if _name_allowed_for_role(name, addr, role)]
  dynamic_name = dynamic_constant_name(addr, role)
  if dynamic_name is not None:
    filtered.append(dynamic_name)
  if not filtered:
    return None
  filtered.sort(key=lambda s: _name_preference(s, role))
  return filtered[0]


def named_target(addr: int, fallback: str, role: str | None = None) -> str:
  name = constant_name(addr, role)
  return fallback if name is None else f"{name} ({fallback})"


@dataclass
class Event:
  role: str
  source: str
  pc: int
  kind: str
  target: str
  value: int | None
  detail: str
  key: str = ""

  def as_dict(self) -> dict:
    return {
      "role": self.role, "source": self.source, "pc": f"0x{self.pc:08x}",
      "kind": self.kind, "target": self.target,
      "value": None if self.value is None else f"0x{self.value:08x}",
      "detail": self.detail, "key": self.key,
    }


def reg_name(reg: Reg | int) -> str:
  return REG_NAMES.get(int(reg), f"x{int(reg)}")


def reg_idx(token: str) -> int:
  token = token.strip()
  if token.startswith("x") and token[1:].isdigit():
    return int(token[1:])
  return REG_ALIASES[token]


def sext32(x: int) -> int:
  x &= 0xFFFFFFFF
  return x - 0x100000000 if x & 0x80000000 else x


def parse_int(s: str) -> int:
  s = s.strip()
  return int(s, 0)


def target_name(addr: int, role: str | None = None) -> str:
  if addr == INSTRN_BUF:
    return named_target(addr, "Tensix FIFO", role)
  if MOP_CFG <= addr < MOP_CFG + 0x40:
    return named_target(addr, f"MOP_CFG[{(addr - MOP_CFG) // 4}]", role)
  if PC_BUF_BASE <= addr < PC_BUF_BASE + 0x100:
    off = addr - PC_BUF_BASE
    if off == 4:
      return named_target(addr, "PC_BUF_SYNC", role)
    if off == 8:
      return named_target(addr, "PC_BUF_MOP_SYNC", role)
    if 0x20 <= off < 0x40 and off % 4 == 0:
      return named_target(addr, f"PC_BUF_SEM[{(off - 0x20) // 4}]", role)
    return named_target(addr, f"PC_BUF+0x{off:x}", role)
  if CFG_BASE <= addr < CFG_BASE + 0x1000 and addr % 4 == 0:
    off = addr - CFG_BASE
    bank = 1 if off >= 0x380 else 0
    if bank:
      off -= 0x380
    addr32 = off // 4
    fields = _reg_fields("cfg", addr32)
    bank_s = f"bank{bank}."
    for name, value in vars(TensixRegs).items():
      if name.endswith("_ADDR32") and value == addr32:
        suffix = f" {name}"
        if fields:
          suffix += f" {fields}"
        return named_target(addr, f"{bank_s}CFG[{addr32}]{suffix}", role)
    suffix = f" {fields}" if fields else ""
    return named_target(addr, f"{bank_s}CFG[{addr32}]{suffix}", role)
  if REGFILE_BASE <= addr < REGFILE_BASE + 0x1000:
    off = addr - REGFILE_BASE
    if off % 4 == 0 and 0 <= off <= 0xFC:
      return named_target(addr, f"dma_reg[{off // 4}]", role)
    return named_target(addr, f"REGFILE+0x{off:x}", role)
  if 0xFFB00000 <= addr < 0xFFC00000:
    return named_target(addr, f"MMIO/L1+0x{addr - 0xFFB00000:x}", role)
  if 0xFFDF0000 <= addr < 0xFFF00000:
    return named_target(addr, f"Tensix/NOC MMIO+0x{addr - 0xFFDF0000:x}", role)
  return named_target(addr, f"0x{addr:08x}", role)


def target_key(addr: int | None, target: str) -> str:
  if addr is None:
    return "tensix_instr"
  if addr == INSTRN_BUF:
    return "tensix_instr"
  if CFG_BASE <= addr < CFG_BASE + 0x1000 and addr % 4 == 0:
    off = addr - CFG_BASE
    bank = 1 if off >= 0x380 else 0
    if bank:
      off -= 0x380
    return f"cfg:{bank}:{off // 4}"
  if REGFILE_BASE <= addr < REGFILE_BASE + 0x1000 and addr % 4 == 0:
    return f"dma_reg:{(addr - REGFILE_BASE) // 4}"
  if MOP_CFG <= addr < MOP_CFG + 0x40 and addr % 4 == 0:
    return f"mop:{(addr - MOP_CFG) // 4}"
  if PC_BUF_BASE <= addr < PC_BUF_BASE + 0x100 and addr % 4 == 0:
    return f"pcbuf:{addr - PC_BUF_BASE:#x}"
  return f"addr:{addr & 0xFFFFFFFF:08x}"


def describe_value(target: str, value: int | None) -> str:
  if value is None:
    return "unknown"
  if "Tensix FIFO" in target or "INSTRN_BUF" in target:
    try:
      return repr(decode_tensix(value))
    except Exception:
      return f"word 0x{value:08x}"
  return f"0x{value:08x}"


def _reg_fields(group: str, index: int, limit: int = 3) -> str:
  entries = TTSIM_TENSIX_REGS.get(group, {}).get(str(index), [])
  if not entries:
    return ""
  names = [entry["name"] for entry in entries]
  common = names[0].split("_")
  if len(names) > 1:
    for name in names[1:]:
      parts = name.split("_")
      i = 0
      while i < min(len(common), len(parts)) and common[i] == parts[i]:
        i += 1
      common = common[:i]
  prefix = "_".join(common)
  if prefix and len(prefix) >= 8:
    return prefix
  if len(names) <= limit:
    return ", ".join(names)
  return ", ".join(names[:limit]) + ", ..."


def tensix_semantic_detail(value: int | None, detail: str = "") -> str:
  if value is None:
    return ""
  try:
    text = detail.strip().lower()
    if text.startswith("tt") or text.startswith("sfp"):
      inst = decode(value)
    else:
      inst = decode_tensix(value)
  except Exception:
    return ""
  name = getattr(inst, "name", type(inst).__name__).upper()
  if name == "SETC16":
    reg = inst.setc16_reg
    fields = _reg_fields("thread_cfg", reg)
    suffix = f" ({fields})" if fields else ""
    return f"thread_cfg[{reg}] := 0x{inst.setc16_value:x}{suffix}"
  if name == "WRCFG":
    reg = inst.CfgReg
    fields = _reg_fields("cfg", reg)
    width = "128b" if inst.wr128b else "32b"
    suffix = f" ({fields})" if fields else ""
    return f"cfg[{reg}] := dma_reg[{inst.GprAddress}] {width}{suffix}"
  if name.startswith("RMWCIB"):
    reg = inst.CfgRegAddr
    byte = int(name[-1])
    fields = _reg_fields("cfg", reg)
    suffix = f" ({fields})" if fields else ""
    return f"cfg[{reg}].byte{byte} rmw data=0x{inst.Data:x} mask=0x{inst.Mask:x}{suffix}"
  if name == "SETDMAREG":
    half = "hi16" if inst.RegIndex16b & 1 else "lo16"
    reg = inst.RegIndex16b >> 1
    data = inst.Payload_SigSel | (inst.Payload_SigSelSize << 14)
    return f"dma_reg[{reg}].{half} := 0x{data:x}"
  if name == "STOREREG":
    addr = 0xFFB00000 | (inst.RegAddr << 2)
    return f"store dma_reg[{inst.TdmaDataRegIndex}] -> {target_name(addr)}"
  if name == "SETADC":
    return f"addr_counter dim={inst.DimensionIndex} ch={inst.ChannelIndex} := {inst.Value} mask=0x{inst.CntSetMask:x}"
  if name == "SETADCXY":
    return f"addr_counter XY ch0=({inst.Ch0_X},{inst.Ch0_Y}) ch1=({inst.Ch1_X},{inst.Ch1_Y}) mask=0x{inst.BitMask:x}"
  if name == "SETADCZW":
    return f"addr_counter ZW ch0=({inst.Ch0_Z},{inst.Ch0_W}) ch1=({inst.Ch1_Z},{inst.Ch1_W}) mask=0x{inst.BitMask:x}"
  if name == "SETADCXX":
    return f"addr_counter X start={inst.x_start} end2={inst.x_end2} mask=0x{inst.CntSetMask:x}"
  if name in {"TTSETADCXY", "TTSETADCZW"}:
    return ""
  return ""


def cfg_value_detail(addr: int, value: int | None) -> str:
  if value is None or not (CFG_BASE <= addr < CFG_BASE + 0x1000) or addr % 4:
    return ""
  off = addr - CFG_BASE
  bank = 1 if off >= 0x380 else 0
  if bank:
    off -= 0x380
  index = off // 4
  entries = TTSIM_TENSIX_REGS.get("cfg", {}).get(str(index), [])
  if not entries:
    return ""
  decoded = []
  for entry in entries[:4]:
    mask = (1 << entry["size"]) - 1
    decoded.append(f"{entry['name']}={(value >> entry['shift']) & mask}")
  if len(entries) > 4:
    decoded.append("...")
  return f"bank{bank}.cfg[{index}] value: " + ", ".join(decoded)


def regfile_value_detail(addr: int, value: int | None) -> str:
  if value is None or not (REGFILE_BASE <= addr < REGFILE_BASE + 0x1000) or addr % 4:
    return ""
  off = addr - REGFILE_BASE
  if not (0 <= off <= 0xFC):
    return ""
  index = off // 4
  lo = value & 0xFFFF
  hi = (value >> 16) & 0xFFFF
  return f"dma_reg[{index}] value: lo16=0x{lo:04x}, hi16=0x{hi:04x}"


def interesting_addr(addr: int, role: str | None = None) -> bool:
  if constant_name(addr, role) is not None:
    return True
  return (
    addr == INSTRN_BUF or
    MOP_CFG <= addr < MOP_CFG + 0x40 or
    PC_BUF_BASE <= addr < PC_BUF_BASE + 0x100 or
    CFG_BASE <= addr < CFG_BASE + 0x1000 or
    REGFILE_BASE <= addr < REGFILE_BASE + 0x1000 or
    0xFFDF0000 <= addr < 0xFFF00000
  )


def add_event(events: list[Event], role: str, source: str, pc: int, kind: str,
              addr: int | None, value: int | None, detail: str = ""):
  target = "Tensix instruction" if addr is None else target_name(addr, role)
  if not detail:
    detail = describe_value(target, value)
  elif addr is not None:
    semantic = cfg_value_detail(addr, value)
    if not semantic:
      semantic = regfile_value_detail(addr, value)
    if semantic and semantic not in detail:
      detail = f"{detail} | {semantic}"
  if addr is None:
    semantic = tensix_semantic_detail(value, detail)
    if semantic and semantic not in detail:
      detail = f"{detail} | {semantic}"
  key = target_key(addr, target)
  if addr is None:
    lower = detail.lower()
    m = re.search(r"ttsem(?:post|get|wait)\s+(\d+)", lower)
    if m:
      key = f"tensix_sem:{m.group(1)}"
  events.append(Event(role, source, pc, kind, target, value, detail, key))


def update_regs_for_inst(regs: dict[int, int | None], inst):
  name = getattr(inst, "name", None)
  if name == "lui":
    regs[int(inst.rd)] = inst.imm << 12
  elif name == "addi":
    base = regs.get(int(inst.rs1))
    regs[int(inst.rd)] = None if base is None else (base + inst.imm) & 0xFFFFFFFF
  elif name in {"slli", "srli", "andi", "ori", "xori"}:
    base = regs.get(int(inst.rs1))
    if base is None:
      regs[int(inst.rd)] = None
    elif name == "slli":
      regs[int(inst.rd)] = (base << (inst.imm & 31)) & 0xFFFFFFFF
    elif name == "srli":
      regs[int(inst.rd)] = (base & 0xFFFFFFFF) >> (inst.imm & 31)
    elif name == "andi":
      regs[int(inst.rd)] = base & inst.imm
    elif name == "ori":
      regs[int(inst.rd)] = base | inst.imm
    elif name == "xori":
      regs[int(inst.rd)] = base ^ inst.imm
  elif name in {"add", "sub", "and", "or"}:
    a, b = regs.get(int(inst.rs1)), regs.get(int(inst.rs2))
    if a is None or b is None:
      regs[int(inst.rd)] = None
    elif name == "add":
      regs[int(inst.rd)] = (a + b) & 0xFFFFFFFF
    elif name == "sub":
      regs[int(inst.rd)] = (a - b) & 0xFFFFFFFF
    elif name == "and":
      regs[int(inst.rd)] = a & b
    elif name == "or":
      regs[int(inst.rd)] = a | b
  elif name in {"lw", "lbu", "lhu", "jal", "jalr", "csrrs", "csrrc"}:
    regs[int(inst.rd)] = None
  if 0 in regs:
    regs[0] = 0


def analyze_ours(role: str, kernel) -> list[Event]:
  events: list[Event] = []
  regs: dict[int, int | None] = {0: 0}
  for i, inst in enumerate(kernel.instructions()):
    pc = kernel.base + i * 4
    if isinstance(inst, TTInst):
      add_event(events, role, "ours", pc, "tensix", None, inst.raw_word(), repr(inst))
      continue
    name = getattr(inst, "name", None)
    if name in {"sw", "sb", "sh"}:
      base = regs.get(int(inst.rs1))
      addr = None if base is None else (base + inst.imm) & 0xFFFFFFFF
      value = regs.get(int(inst.rs2))
      if addr is not None and interesting_addr(addr, role):
        add_event(
          events, role, "ours", pc, name, addr, value,
          f"{reg_name(inst.rs2)}={describe_value(target_name(addr, role), value)}",
        )
    update_regs_for_inst(regs, inst)
  return events


OLD_RE = re.compile(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$")
COMMENT_ADDR_RE = re.compile(r"#.*?\b([0-9a-fA-F]{8,16})\b")


def parse_old_operand_mem(op: str) -> tuple[int, str] | None:
  m = re.match(r"(-?(?:0x)?[0-9a-fA-F]+)\(([^)]+)\)", op.strip())
  if not m:
    return None
  return parse_int(m.group(1)), m.group(2).strip()


def analyze_old(role: str, path: Path) -> list[Event]:
  events: list[Event] = []
  regs: dict[int, int | None] = {0: 0}
  for line in path.read_text().splitlines():
    m = OLD_RE.match(line)
    if not m:
      continue
    pc = int(m.group(1), 16)
    full_asm = m.group(3).strip()
    if "#" in full_asm and re.search(r"\b(__stack|__ldm|__global_pointer\$)\b", full_asm):
      continue
    comment_addr = None
    cm = COMMENT_ADDR_RE.search(full_asm)
    if cm:
      comment_addr = int(cm.group(1)[-8:], 16)
    asm = full_asm.split("#", 1)[0].strip()
    parts = asm.split(None, 1)
    if not parts:
      continue
    op = parts[0]
    ops = [x.strip() for x in parts[1].split(",")] if len(parts) > 1 else []
    if op.startswith("tt") or op.startswith("sfp"):
      word = int(m.group(2), 16)
      add_event(events, role, "old", pc, "tensix", None, word, asm)
      continue
    try:
      if op == "lui" and len(ops) == 2:
        regs[reg_idx(ops[0])] = parse_int(ops[1]) << 12
      elif op in {"li"} and len(ops) == 2:
        regs[reg_idx(ops[0])] = parse_int(ops[1]) & 0xFFFFFFFF
      elif op in {"mv"} and len(ops) == 2:
        regs[reg_idx(ops[0])] = regs.get(reg_idx(ops[1]))
      elif op == "addi" and len(ops) == 3:
        base = regs.get(reg_idx(ops[1]))
        regs[reg_idx(ops[0])] = None if base is None else (base + parse_int(ops[2])) & 0xFFFFFFFF
      elif op in {"slli", "srli"} and len(ops) == 3:
        base = regs.get(reg_idx(ops[1]))
        sh = parse_int(ops[2])
        if base is None:
          regs[reg_idx(ops[0])] = None
        elif op == "slli":
          regs[reg_idx(ops[0])] = (base << sh) & 0xFFFFFFFF
        else:
          regs[reg_idx(ops[0])] = (base & 0xFFFFFFFF) >> sh
      elif op in {"andi", "ori", "xori"} and len(ops) == 3:
        base = regs.get(reg_idx(ops[1]))
        imm = parse_int(ops[2])
        if base is None:
          regs[reg_idx(ops[0])] = None
        elif op == "andi":
          regs[reg_idx(ops[0])] = base & imm
        elif op == "ori":
          regs[reg_idx(ops[0])] = base | imm
        else:
          regs[reg_idx(ops[0])] = base ^ imm
      elif op in {"add", "sub", "and", "or"} and len(ops) == 3:
        a, b = regs.get(reg_idx(ops[1])), regs.get(reg_idx(ops[2]))
        if a is None or b is None:
          regs[reg_idx(ops[0])] = None
        elif op == "add":
          regs[reg_idx(ops[0])] = (a + b) & 0xFFFFFFFF
        elif op == "sub":
          regs[reg_idx(ops[0])] = (a - b) & 0xFFFFFFFF
        elif op == "and":
          regs[reg_idx(ops[0])] = a & b
        else:
          regs[reg_idx(ops[0])] = a | b
      elif op in {"lw", "lbu", "lhu"} and len(ops) == 2:
        mem = parse_old_operand_mem(ops[1])
        if mem is not None:
          off, base_reg = mem
          base = regs.get(reg_idx(base_reg))
          addr = None if base is None else (base + off) & 0xFFFFFFFF
          if addr is None and comment_addr is not None:
            addr = comment_addr
          if addr is not None and interesting_addr(addr, role):
            add_event(events, role, "old", pc, op, addr, None, f"{ops[0]} <- {target_name(addr, role)}")
        regs[reg_idx(ops[0])] = None
      elif op in {"sw", "sb", "sh"} and len(ops) == 2:
        mem = parse_old_operand_mem(ops[1])
        if mem is None:
          continue
        off, base_reg = mem
        base = regs.get(reg_idx(base_reg))
        addr = None if base is None else (base + off) & 0xFFFFFFFF
        if addr is None and comment_addr is not None:
          addr = comment_addr
        value = regs.get(reg_idx(ops[0]))
        if addr is not None and interesting_addr(addr, role):
          add_event(
            events, role, "old", pc, op, addr, value,
            f"{ops[0]}={describe_value(target_name(addr, role), value)}",
          )
      elif op in {"jal", "jalr"}:
        pass
    except Exception:
      continue
    regs[0] = 0
  return events


def phase(detail: str, target: str) -> str:
  text = f"{target} {detail}".lower()
  if "noc" in text:
    return "noc"
  if "cb[" in text or "cb_sync" in text or "circularbuffer" in text or "tiles_acked" in text or "tiles_received" in text:
    return "cb/dataflow"
  if "mailbox" in text or ".data" in text or "_msg" in text:
    return "mailbox"
  if "sem" in text:
    return "semaphore"
  if "mop" in text:
    return "mop"
  if "unpac" in text or "pacr" in text or "pack" in text:
    return "pack/unpack"
  if "sfp" in text or "replay" in text:
    return "math/sfpu"
  if "cfg" in text or "regfile" in text:
    return "config"
  if "sync" in text or "stallwait" in text:
    return "sync/stall"
  return "other"


def write_timeline(path: Path, events: list[Event]):
  lines = []
  for e in events:
    val = "" if e.value is None else f" 0x{e.value:08x}"
    lines.append(f"{e.source:4s} {e.role:6s} {e.pc:08x} {e.kind:6s} {e.target:18s}{val:11s} {e.detail}")
  path.write_text("\n".join(lines) + "\n")


def shorten(text: str, limit: int = 64) -> str:
  text = re.sub(r"\s+", " ", text).strip()
  return text if len(text) <= limit else text[:limit - 1] + "..."


def event_title(e: Event) -> str:
  target = e.target
  if e.key == "tensix_instr" or e.kind == "tensix":
    return "Tensix instruction"
  target = re.sub(r" \([^)]*\)", "", target)
  target = target.replace("TensixRegs.", "")
  target = target.replace("CircularBuffer.", "CB.")
  target = target.replace("TriscMailbox.", "TM.")
  target = target.replace("BriscMailbox.", "BM.")
  target = target.replace("NcriscMailbox.", "NM.")
  return shorten(target, 54)


def display_detail(e: Event) -> str:
  detail = e.detail
  detail = re.sub(r"^inline\s*\|\s*", "", detail)
  detail = detail.replace("INSTRN_BUF_BASE", "Tensix FIFO")
  detail = detail.replace("INSTRN_BUF", "Tensix FIFO")
  detail = re.sub(r" \((?:MMIO/L1|Tensix/NOC MMIO|0x)[^)]*\)", "", detail)
  detail = detail.replace("TensixRegs.", "")
  detail = detail.replace("CircularBuffer.", "CB.")
  detail = detail.replace("TriscMailbox.", "TM.")
  detail = detail.replace("BriscMailbox.", "BM.")
  detail = detail.replace("NcriscMailbox.", "NM.")
  return detail


def html_wrap(text: str, width: int = 42, max_lines: int = 3) -> str:
  text = re.sub(r"\s+", " ", text).strip()
  if not text:
    return ""
  lines = []
  rest = text
  while rest and len(lines) < max_lines:
    if len(rest) <= width:
      lines.append(rest)
      rest = ""
      break
    cut = rest.rfind(" ", 0, width + 1)
    if cut <= 0:
      cut = width
    lines.append(rest[:cut].rstrip())
    rest = rest[cut:].lstrip()
  if rest and lines:
    lines[-1] = lines[-1].rstrip(".") + "..."
  return "<BR ALIGN=\"LEFT\"/>".join(html.escape(line) for line in lines)


def node_label(e: Event, seq: int) -> str:
  kind = "tensix" if e.key == "tensix_instr" or e.kind == "inline" else e.kind
  header = html.escape(f"{seq:03d}  {e.role}  {e.pc:08x}  {kind}")
  target = html_wrap(event_title(e), width=46, max_lines=2)
  detail = html_wrap(display_detail(e), width=54, max_lines=3)
  return (
    "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"3\">"
    f"<TR><TD ALIGN=\"LEFT\"><FONT POINT-SIZE=\"9\" COLOR=\"#f4f7fb\"><B>{header}</B></FONT></TD></TR>"
    f"<TR><TD ALIGN=\"LEFT\"><FONT POINT-SIZE=\"8\" COLOR=\"#e4eaf2\">{target}</FONT></TD></TR>"
    f"<TR><TD ALIGN=\"LEFT\"><FONT POINT-SIZE=\"7\" COLOR=\"#b7c0cc\">{detail}</FONT></TD></TR>"
    "</TABLE>>"
  )


def sem_access(e: Event) -> tuple[str, str] | None:
  text = e.detail.lower()
  m = re.search(r"ttsem(wait|post|get)\s+([0-9]+)(?:,([0-9]+))?", text)
  if not m:
    return None
  op = m.group(1)
  sem = m.group(3) if op == "wait" and m.group(3) is not None else m.group(2)
  kind = "read" if op == "wait" else "write"
  return kind, f"tensix_sem:{sem}"


def write_dot(path: Path, events: list[Event], *, title: str = "add1 flow", events_per_column: int = 32):
  legend_label = (
    "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLSPACING=\"8\" CELLPADDING=\"6\">"
    "<TR>"
    "<TD BGCOLOR=\"#6f5300\"><FONT POINT-SIZE=\"10\" COLOR=\"#fff0b8\">semaphore</FONT></TD>"
    "<TD BGCOLOR=\"#124f47\"><FONT POINT-SIZE=\"10\" COLOR=\"#bcfff2\">CB / dataflow</FONT></TD>"
    "<TD BGCOLOR=\"#453399\"><FONT POINT-SIZE=\"10\" COLOR=\"#ddd7ff\">NOC</FONT></TD>"
    "<TD BGCOLOR=\"#5e4523\"><FONT POINT-SIZE=\"10\" COLOR=\"#f7dfbd\">mailbox</FONT></TD>"
    "<TD BGCOLOR=\"#164f7a\"><FONT POINT-SIZE=\"10\" COLOR=\"#c6eaff\">MOP / replay</FONT></TD>"
    "<TD BGCOLOR=\"#225d24\"><FONT POINT-SIZE=\"10\" COLOR=\"#cfffd0\">SFPU math</FONT></TD>"
    "<TD BGCOLOR=\"#343943\"><FONT POINT-SIZE=\"10\" COLOR=\"#e6edf5\">config / MMIO</FONT></TD>"
    "<TD BGCOLOR=\"#6e2645\"><FONT POINT-SIZE=\"10\" COLOR=\"#ffd4e6\">pack / unpack</FONT></TD>"
    "<TD BGCOLOR=\"#704314\"><FONT POINT-SIZE=\"10\" COLOR=\"#ffe1b8\">sync / stall</FONT></TD>"
    "</TR>"
    "</TABLE>>"
  )
  lines = [
    "digraph add1_flow {",
    "  rankdir=TB;",
    "  graph [fontname=\"DejaVu Sans\", bgcolor=\"#0f1117\", fontcolor=\"#e6edf5\", pad=0.2, nodesep=0.22, ranksep=0.42, compound=true, concentrate=true, splines=polyline, labelloc=t, fontsize=18, label=\"" + title.replace('"', '\\"') + "\"];",
    "  node [shape=box, style=\"rounded,filled\", fontname=\"DejaVu Sans Mono\", fontsize=8, margin=\"0.04,0.03\", penwidth=1.2, color=\"#56616f\", fontcolor=\"#e6edf5\"];",
    "  edge [arrowsize=0.45, penwidth=0.8, fontsize=7, fontname=\"DejaVu Sans Mono\", color=\"#536071\", fontcolor=\"#aeb8c6\"];",
    f"  legend_top [shape=plain, label={legend_label}];",
    "  { rank=min; legend_top; }",
  ]
  node_ids: dict[int, str] = {}
  first_nodes: list[str] = []
  key_writers: dict[str, str] = {}
  cross_edges: list[tuple[str, str, str]] = []
  role_order = {role: i for i, role in enumerate(("brisc", "trisc0", "trisc1", "trisc2", "ncrisc"))}
  for role in sorted({e.role for e in events}, key=lambda r: role_order.get(r, 99)):
    for source in ("old", "ours"):
      subset = [e for e in events if e.role == role and e.source == source]
      if not subset:
        continue
      lines.append(f"  subgraph cluster_{source}_{role} {{")
      cluster_label = role if len({e.source for e in events}) == 1 else f"{source} {role}"
      lines.append(f"    label=\"{cluster_label}\";")
      lines.append("    style=\"rounded\"; color=\"#303844\"; fontcolor=\"#d6deeb\"; penwidth=1.2; fontsize=14;")
      prev = None
      first = None
      chunk_firsts: list[str] = []
      for i, e in enumerate(subset):
        node = f"{source}_{role}_{i}".replace("-", "_")
        node_ids[id(e)] = node
        if first is None:
          first = node
        if i % events_per_column == 0:
          chunk_firsts.append(node)
        phase_name = phase(e.detail, e.target)
        color, border = {
          "semaphore": ("#6f5300", "#d9a824"),
          "cb/dataflow": ("#124f47", "#44c3ad"),
          "noc": ("#453399", "#9a88ff"),
          "mailbox": ("#5e4523", "#d1a15e"),
          "mop": ("#164f7a", "#55b7f0"),
          "pack/unpack": ("#6e2645", "#ef7aa8"),
          "math/sfpu": ("#225d24", "#71d46f"),
          "config": ("#343943", "#8c98a8"),
          "sync/stall": ("#704314", "#e59a3d"),
          "other": ("#171b22", "#586170"),
        }[phase_name]
        tooltip = f"{e.role} {e.pc:08x} {e.target} {e.detail}".replace('"', '\\"')
        lines.append(f"    {node} [label={node_label(e, i)}, tooltip=\"{tooltip}\", fillcolor=\"{color}\", color=\"{border}\"];")
        if prev is not None:
          if i % events_per_column == 0:
            lines.append(f"    {prev} -> {node} [style=dotted, color=\"#6f7c91\", constraint=false];")
          else:
            lines.append(f"    {prev} -> {node} [weight=10];")
        sem = sem_access(e)
        if sem is not None:
          access, key = sem
          if access == "write":
            if key in key_writers and key_writers[key] != node:
              cross_edges.append((key_writers[key], node, key))
            key_writers[key] = node
          elif key in key_writers:
            cross_edges.append((key_writers[key], node, key))
        elif e.kind in {"sw", "sb", "sh"} and e.key:
          if e.key in key_writers and key_writers[e.key] != node:
            cross_edges.append((key_writers[e.key], node, e.key))
          key_writers[e.key] = node
        elif e.kind in {"lw", "lbu", "lhu"} and e.key in key_writers:
          cross_edges.append((key_writers[e.key], node, e.key))
        prev = node
      if len(chunk_firsts) > 1:
        lines.append("    { rank=same; " + "; ".join(chunk_firsts) + "; }")
        for left, right in zip(chunk_firsts, chunk_firsts[1:]):
          lines.append(f"    {left} -> {right} [style=invis, weight=50, constraint=false];")
      lines.append("  }")
      if first is not None:
        first_nodes.append(first)
  for node in first_nodes:
    lines.append(f"  legend_top -> {node} [style=invis, weight=100];")
  for src, dst, key in cross_edges:
    label = "" if key.startswith("addr:") else key.replace('"', '\\"')
    label_attr = "" if not label else f", label=\"{label}\""
    lines.append(f"  {src} -> {dst} [style=dashed, color=\"#8aa2d3\", fontcolor=\"#b7c8ee\", penwidth=1.1, constraint=false{label_attr}];")
  lines.append("}")
  path.write_text("\n".join(lines) + "\n")


def render_dot(dot_path: Path) -> tuple[Path, Path] | None:
  dot = shutil.which("dot")
  if dot is None:
    return None
  svg_path = dot_path.with_suffix(".svg")
  png_path = dot_path.with_suffix(".png")
  subprocess.run([dot, "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
  subprocess.run([dot, "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
  return svg_path, png_path


def summarize(events: list[Event]) -> str:
  lines = []
  for role in ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc"):
    lines.append(f"## {role}")
    for source in ("old", "ours"):
      subset = [e for e in events if e.role == role and e.source == source]
      if not subset:
        continue
      counts = {}
      for e in subset:
        counts[phase(e.detail, e.target)] = counts.get(phase(e.detail, e.target), 0) + 1
      counts_s = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
      lines.append(f"- {source}: {len(subset)} events ({counts_s})")
      for e in subset:
        if phase(e.detail, e.target) in {"semaphore", "mop", "pack/unpack", "math/sfpu", "sync/stall"}:
          lines.append(f"  - {e.pc:08x} {e.target}: {e.detail}")
    lines.append("")
  return "\n".join(lines)


def main() -> int:
  ap = argparse.ArgumentParser()
  ap.add_argument("--out", type=Path, default=Path("/tmp/add1_static_flow"))
  ap.add_argument("--source", choices=("both", "ours", "old"), default="both")
  args = ap.parse_args()
  args.out.mkdir(parents=True, exist_ok=True)

  ours = {
    "trisc0": add1.add1_trisc_compute(0),
    "trisc1": add1.add1_trisc_compute(1),
    "trisc2": add1.add1_trisc_compute(2),
  }
  old_paths = {
    "brisc": OLD / "add1_writer_brisc.kernel.dis",
    "trisc0": OLD / "add1_compute_trisc0.kernel.dis",
    "trisc1": OLD / "add1_compute_trisc1.kernel.dis",
    "trisc2": OLD / "add1_compute_trisc2.kernel.dis",
    "ncrisc": OLD / "add1_reader_ncrisc.kernel.dis",
  }
  events: list[Event] = []
  roles = ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc")
  for role in roles:
    if args.source in ("both", "ours") and role in ours:
      kernel = ours[role]
      events.extend(analyze_ours(role, kernel))
    if args.source in ("both", "old"):
      events.extend(analyze_old(role, old_paths[role]))

  role_order = {role: i for i, role in enumerate(roles)}
  events.sort(key=lambda e: (e.source, role_order.get(e.role, 99), e.pc))
  (args.out / "events.json").write_text(json.dumps([e.as_dict() for e in events], indent=2) + "\n")
  write_timeline(args.out / "timeline.txt", events)
  dot_path = args.out / "flow_full.dot"
  write_dot(dot_path, events, title=f"add1 {args.source} 5-core hardware/state dependency trace")
  rendered_paths = render_dot(dot_path)
  (args.out / "summary.md").write_text(summarize(events))
  print(f"wrote {args.out}/events.json")
  print(f"wrote {args.out}/timeline.txt")
  print(f"wrote {dot_path}")
  if rendered_paths is not None:
    svg_path, png_path = rendered_paths
    print(f"wrote {svg_path}")
    print(f"wrote {png_path}")
  print(f"wrote {args.out}/summary.md")
  Debug.clear_debug()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
