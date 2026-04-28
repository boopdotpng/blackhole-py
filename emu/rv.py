from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache

from dsl import decode_rv
from .memory import (
  L1_BASE, L1_END, LDM_BASE, INSTRN_BUF_T0, INSTRN_BUF_END,
  MOP_CFG_BASE, MOP_CFG_END, PCBUF_T0, PCBUF_END, Memory, Router,
)

from .sim import Phase, SimContext
from .snapshots import dest_valid_sample, nonzero_counts, nonzero_row_sample
from .tensix_core import Tensix
from .timing import rv_timing


M32 = 0xFFFFFFFF
MSTATUS = 0x300
MCYCLE = 0xB00
MINSTRET = 0xB02
MCYCLEH = 0xB80
MINSTRETH = 0xB82


def _sext(v, b):
  return v - (1 << b) if v & (1 << (b - 1)) else v


_decode_rv_cached = cache(decode_rv)


class FifoFull(Exception):
  """Backpressure from the Tensix instruction FIFO."""


class BlockingRead(Exception):
  """An MMIO read is waiting for hardware state to become ready."""


class _InstrnHandler:
  def __init__(self, tensix: Tensix, thread_of_addr):
    self.tensix = tensix
    self._thread_of_addr = thread_of_addr

  def read8(self, addr): return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val): pass
  def write16(self, addr, val): pass

  def write32(self, addr, val):
    if not self.tensix.push_word(self._thread_of_addr(addr), val):
      raise FifoFull()


def _brisc_thread_of_addr(addr):
  return (addr - INSTRN_BUF_T0) >> 16


def _const(x):
  def f(_addr):
    return x
  return f


class _MopCfgHandler:
  def __init__(self, tensix: Tensix, thread: int):
    self.tensix = tensix
    self.thread = thread

  def read8(self, addr): return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val): pass
  def write16(self, addr, val): pass

  def write32(self, addr, val):
    self.tensix.write_mop_cfg(self.thread, (addr >> 2) & 0x1F, val)


class _PCBufHandler:
  def __init__(self, tensix: Tensix):
    self.tensix = tensix

  def _read_word(self, addr):
    thread = (addr - PCBUF_T0) >> 16
    offset = addr & 0xFFFF
    value = self.tensix.read_pcbuf(thread, offset)
    if value is None:
      raise BlockingRead()
    return value & M32

  def read8(self, addr):
    return (self._read_word(addr & ~3) >> (8 * (addr & 3))) & 0xFF

  def read16(self, addr):
    return (self._read_word(addr & ~3) >> (8 * (addr & 2))) & 0xFFFF

  def read32(self, addr):
    return self._read_word(addr)

  def write8(self, addr, val): self.write32(addr & ~3, val)
  def write16(self, addr, val): self.write32(addr & ~3, val)

  def write32(self, addr, val):
    thread = (addr - PCBUF_T0) >> 16
    offset = addr & 0xFFFF
    self.tensix.write_pcbuf(thread, offset, val)


@dataclass(frozen=True)
class PendingInstruction:
  pc: int
  word: int
  decoded: object | None
  latency: int


class Core:
  ROLE = None
  LDM_SIZE = 0
  PIPELINES = frozenset()

  def __init__(self, l1=None, pc=0, tensix: Tensix | None = None):
    self.l1 = l1 or Memory()
    self.ldm = Memory()
    self.mem = Router(default=Memory())
    self.mem.register(L1_BASE, L1_END, self.l1)
    if self.LDM_SIZE:
      self.mem.register(LDM_BASE, LDM_BASE + self.LDM_SIZE - 1,
                        self.ldm, offset=LDM_BASE)
    self.regs = [0] * 32
    self.csrs = {}
    self.pc = pc
    self.in_reset = True
    self.cycles = 0
    self.blocked_cycles = 0
    self.minstret = 0
    self._pending: PendingInstruction | None = None
    self._waiting_for_commit = False
    self._blocked = False
    self.tensix = None
    self.snapshots = None
    self.snapshot_core = "unknown"
    self.state_watchpoints: dict[int, dict] = {}
    if tensix is not None:
      self.attach_tensix(tensix)

  def attach_tensix(self, tensix: Tensix):
    self.tensix = tensix
    if self.ROLE == "brisc":
      self.mem.register(INSTRN_BUF_T0, INSTRN_BUF_END,
                        _InstrnHandler(tensix, _brisc_thread_of_addr))
    elif self.ROLE == "trisc0":
      self.mem.register(INSTRN_BUF_T0, INSTRN_BUF_END,
                        _InstrnHandler(tensix, _const(0)))
      self.mem.register(MOP_CFG_BASE, MOP_CFG_END, _MopCfgHandler(tensix, 0),
                        offset=MOP_CFG_BASE)
    elif self.ROLE == "trisc1":
      self.mem.register(INSTRN_BUF_T0, INSTRN_BUF_END,
                        _InstrnHandler(tensix, _const(1)))
      self.mem.register(MOP_CFG_BASE, MOP_CFG_END, _MopCfgHandler(tensix, 1),
                        offset=MOP_CFG_BASE)
    elif self.ROLE == "trisc2":
      self.mem.register(INSTRN_BUF_T0, INSTRN_BUF_END,
                        _InstrnHandler(tensix, _const(2)))
      self.mem.register(MOP_CFG_BASE, MOP_CFG_END, _MopCfgHandler(tensix, 2),
                        offset=MOP_CFG_BASE)
    self.mem.register(PCBUF_T0, PCBUF_END, _PCBufHandler(tensix))

  def _wr(self, rd, val):
    if rd != 0:
      self.regs[rd] = val & M32

  def load(self, addr, insns):
    for i, insn in enumerate(insns):
      self.mem.write32(addr + i * 4, int(insn))

  def add_state_watchpoint(self, pc: int, *, label: str | None = None,
                           once: bool = False,
                           l1: list[dict] | None = None,
                           ldm: list[dict] | None = None) -> None:
    self.state_watchpoints[pc & M32] = {
      "label": label or f"{self.ROLE}@0x{pc & M32:08x}",
      "once": bool(once),
      "hits": 0,
      "l1": l1 or [],
      "ldm": ldm or [],
    }

  def tick(self, ctx: SimContext, phase: Phase) -> None:
    if phase is Phase.LATCH and not self.in_reset:
      self.cycles += 1
      if self._blocked:
        self.blocked_cycles += 1
      return
    if phase is not Phase.ISSUE or self.in_reset or self._waiting_for_commit:
      return
    self.issue(ctx)

  def issue(self, ctx: SimContext) -> bool:
    pc = self.pc
    word = self.mem.read32(pc)
    self._maybe_snapshot_state(ctx, pc, word)
    self.pc = (pc + 4) & M32

    if (word & 0x3) != 0x3:
      pending = PendingInstruction(pc, word, None, 1)
    else:
      decoded = _decode_rv_cached(word)
      pending = PendingInstruction(pc, word, decoded,
                                   self._latency(decoded))

    self._pending = pending
    self._waiting_for_commit = True

    def commit(commit_ctx: SimContext) -> None:
      self._commit_pending(commit_ctx)

    ctx.schedule(pending.latency, commit, f"{self.ROLE or 'rv'}:{self._pending_name(pending)}")
    return True

  def _maybe_snapshot_state(self, ctx: SimContext, pc: int, word: int) -> None:
    watch = self.state_watchpoints.get(pc)
    if watch is None or self.snapshots is None:
      return
    if watch["once"] and watch["hits"]:
      return
    watch["hits"] += 1
    self.snapshots.record(
      self.snapshot_core,
      "STATE",
      cycle=ctx.cycle,
      core_role=self.ROLE,
      label=watch["label"],
      pc=f"0x{pc:08x}",
      word=f"0x{word:08x}",
      instr=self._word_name(word),
      hit=watch["hits"],
      reset=bool(self.in_reset),
      regs=self._nonzero_regs(),
      pending=self._pending_state(),
      l1=self._l1_samples(watch.get("l1", [])),
      ldm=self._ldm_samples(watch.get("ldm", [])),
      tensix=self._tensix_state(),
    )

  def _word_name(self, word: int) -> str:
    if (word & 0x3) != 0x3:
      return "TT_PUSH"
    try:
      return _decode_rv_cached(word).name
    except Exception:
      return "UNKNOWN"

  def _nonzero_regs(self) -> dict[str, str]:
    return {f"x{i}": f"0x{v:08x}" for i, v in enumerate(self.regs) if v}

  def _pending_state(self):
    if self._pending is None:
      return None
    return {
      "pc": f"0x{self._pending.pc:08x}",
      "word": f"0x{self._pending.word:08x}",
      "name": self._pending_name(self._pending),
      "latency": self._pending.latency,
    }

  def _l1_samples(self, ranges: list[dict]) -> dict[str, str]:
    out = {}
    for item in ranges:
      name = item.get("name") or str(item.get("addr", "range"))
      addr = int(str(item["addr"]), 0)
      size = int(item.get("bytes", item.get("size", 64)))
      out[name] = bytes(self.l1.read8(addr + i) for i in range(size)).hex()
    return out

  def _ldm_samples(self, ranges: list[dict]) -> dict[str, str]:
    out = {}
    for item in ranges:
      name = item.get("name") or str(item.get("addr", "range"))
      addr = int(str(item["addr"]), 0)
      if addr >= LDM_BASE:
        addr -= LDM_BASE
      size = int(item.get("bytes", item.get("size", 64)))
      out[name] = bytes(self.ldm.read8(addr + i) for i in range(size)).hex()
    return out

  def _tensix_state(self):
    t = self.tensix
    if t is None:
      return None
    return {
      "cycle": t.cycle,
      "backend_inflight": list(t._backend_inflight),
      "semaphores": list(t.semaphores.value),
      "rwc": [
        {"a": r.a, "b": r.b, "d": r.d, "cr": r.cr,
         "a_cr": r.a_cr, "b_cr": r.b_cr, "d_cr": r.d_cr}
        for r in t.rwc
      ],
      "srca": {
        "fpu_bank": t.srca.fpu_bank,
        "unpack_bank": t.srca.unpack_bank,
        "nz_banks": nonzero_counts(t.srca),
        "fpu_rows": nonzero_row_sample(t.srca.banks[t.srca.fpu_bank]),
      },
      "srcb": {
        "fpu_bank": t.srcb.fpu_bank,
        "unpack_bank": t.srcb.unpack_bank,
        "nz_banks": nonzero_counts(t.srcb),
        "fpu_rows": nonzero_row_sample(t.srcb.banks[t.srcb.fpu_bank]),
      },
      "dest": {
        "valid_rows": dest_valid_sample(t.dest),
      },
      "adc": self._tensix_adc_state(t),
      "cfg": self._tensix_cfg_state(t),
    }

  def _tensix_adc_state(self, t):
    def counter(c):
      return {"val": c.val, "cr": c.cr}

    def channel(ch):
      return {
        "x": counter(ch.x),
        "y": counter(ch.y),
        "z": counter(ch.z),
        "w": counter(ch.w),
      }

    return [
      {
        "unpackers": [
          [channel(ch) for ch in unp.channels]
          for unp in adc.unpackers
        ],
        "packers": [channel(ch) for ch in adc.packers.channels],
      }
      for adc in t.adc
    ]

  def _tensix_cfg_state(self, t):
    cfg = t.config_unit
    def words(state_id: int, start: int, count: int) -> list[str]:
      return [f"0x{cfg.cfg[state_id][start + i]:08x}" for i in range(count)]
    return {
      "thread_cfg": [
        {
          "cfg_state_id": cfg.thread_cfg[i][0] & 1,
          "cfg_context": cfg.thread_cfg[i][41],
          "srca_set": cfg.thread_cfg[i][5],
        }
        for i in range(len(cfg.thread_cfg))
      ],
      "state0": {
        "unp_addr_ctrl": words(0, 44, 20),
        "unp0_desc": words(0, 64, 32),
        "unp1_desc": words(0, 112, 32),
      },
      "state1": {
        "unp_addr_ctrl": words(1, 44, 20),
        "unp0_desc": words(1, 64, 32),
        "unp1_desc": words(1, 112, 32),
      },
    }

  def _commit_pending(self, ctx: SimContext) -> None:
    pending = self._pending
    self._pending = None
    self._waiting_for_commit = False
    if pending is None:
      return
    try:
      if pending.decoded is None:
        tensix_word = ((pending.word >> 2) | (pending.word << 30)) & M32
        if os.environ.get("EMU_TRACE_TT_PUSH"):
          print(
              "EMU_TRACE_TT_PUSH",
              f"core={self.snapshot_core}",
              f"role={self.ROLE}",
              f"cycle={ctx.cycle}",
              f"pc=0x{pending.pc:08x}",
              f"raw=0x{pending.word:08x}",
              f"word=0x{tensix_word:08x}",
          )
        self.mem.write32(INSTRN_BUF_T0, tensix_word)
      else:
        self._execute(pending.pc, pending.decoded, ctx)
    except BlockingRead:
      self._blocked = True
      self._pending = pending
      self._waiting_for_commit = True

      def retry(retry_ctx: SimContext) -> None:
        self._commit_pending(retry_ctx)

      ctx.schedule(1, retry, f"{self.ROLE or 'rv'}:{self._pending_name(pending)}:retry")
      return
    except FifoFull:
      self._blocked = True
      self.pc = pending.pc
      return
    self._blocked = False
    self.regs[0] = 0
    self.minstret = (self.minstret + 1) & 0xFFFFFFFFFFFFFFFF

  def _pending_name(self, pending: PendingInstruction) -> str:
    if pending.decoded is None:
      return "TT_PUSH"
    return pending.decoded.name

  def _latency(self, d) -> int:
    return rv_timing(d.name).latency

  def _csr_read(self, csr, ctx: SimContext):
    if csr == MCYCLE:
      return ctx.cycle & M32
    if csr == MCYCLEH:
      return (ctx.cycle >> 32) & M32
    if csr == MINSTRET:
      return self.minstret & M32
    if csr == MINSTRETH:
      return (self.minstret >> 32) & M32
    return self.csrs.get(csr, 0)

  def _csr_write(self, csr, value):
    if csr in (MCYCLE, MCYCLEH, MINSTRET, MINSTRETH):
      return
    self.csrs[csr] = value & M32

  def _execute(self, pc, d, ctx: SimContext):
    rd, rs1, imm, shamt = d.rd, d.rs1, d.imm, d.shamt
    v1, v2 = self.regs[d.rs1], self.regs[d.rs2]
    match d.name:
      case 'ADD':    self._wr(rd, v1 + v2)
      case 'SUB':    self._wr(rd, v1 - v2)
      case 'SLL':    self._wr(rd, v1 << (v2 & 0x1F))
      case 'SLT':    self._wr(rd, 1 if _sext(v1, 32) < _sext(v2, 32) else 0)
      case 'SLTU':   self._wr(rd, 1 if v1 < v2 else 0)
      case 'XOR':    self._wr(rd, v1 ^ v2)
      case 'SRL':    self._wr(rd, v1 >> (v2 & 0x1F))
      case 'SRA':    self._wr(rd, _sext(v1, 32) >> (v2 & 0x1F))
      case 'OR':     self._wr(rd, v1 | v2)
      case 'AND':    self._wr(rd, v1 & v2)

      case 'MUL':    self._wr(rd, v1 * v2)
      case 'MULH':   self._wr(rd, (_sext(v1, 32) * _sext(v2, 32)) >> 32)
      case 'MULHSU': self._wr(rd, (_sext(v1, 32) * v2) >> 32)
      case 'MULHU':  self._wr(rd, (v1 * v2) >> 32)
      case 'DIV':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        if s2 == 0: self._wr(rd, M32)
        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, s1)
        else:
          q = abs(s1) // abs(s2)
          if (s1 < 0) != (s2 < 0): q = -q
          self._wr(rd, q)
      case 'DIVU':   self._wr(rd, v1 // v2 if v2 else M32)
      case 'REM':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        if s2 == 0: self._wr(rd, v1)
        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, 0)
        else:
          r = abs(s1) % abs(s2)
          if s1 < 0: r = -r
          self._wr(rd, r)
      case 'REMU':   self._wr(rd, v1 % v2 if v2 else v1)

      case 'SH1ADD': self._wr(rd, (v1 << 1) + v2)
      case 'SH2ADD': self._wr(rd, (v1 << 2) + v2)
      case 'SH3ADD': self._wr(rd, (v1 << 3) + v2)
      case 'ZEXT_H': self._wr(rd, v1 & 0xFFFF)
      case 'MIN':    self._wr(rd, min(_sext(v1, 32), _sext(v2, 32)))
      case 'MINU':   self._wr(rd, min(v1, v2))
      case 'MAX':    self._wr(rd, max(_sext(v1, 32), _sext(v2, 32)))
      case 'MAXU':   self._wr(rd, max(v1, v2))
      case 'XNOR':   self._wr(rd, ~(v1 ^ v2))
      case 'ORN':    self._wr(rd, v1 | ~v2)
      case 'ANDN':   self._wr(rd, v1 & ~v2)
      case 'ROL':
        sh = v2 & 0x1F
        self._wr(rd, (v1 << sh) | (v1 >> (32 - sh)))
      case 'ROR':
        sh = v2 & 0x1F
        self._wr(rd, (v1 >> sh) | (v1 << (32 - sh)))

      case 'ADDI':   self._wr(rd, v1 + imm)
      case 'SLTI':   self._wr(rd, 1 if _sext(v1, 32) < imm else 0)
      case 'SLTIU':  self._wr(rd, 1 if v1 < (imm & M32) else 0)
      case 'XORI':   self._wr(rd, v1 ^ (imm & M32))
      case 'ORI':    self._wr(rd, v1 | (imm & M32))
      case 'ANDI':   self._wr(rd, v1 & (imm & M32))
      case 'SLLI':   self._wr(rd, v1 << shamt)
      case 'SRLI':   self._wr(rd, v1 >> shamt)
      case 'SRAI':   self._wr(rd, _sext(v1, 32) >> shamt)
      case 'CLZ':    self._wr(rd, 32 - v1.bit_length())
      case 'CTZ':    self._wr(rd, (v1 & -v1).bit_length() - 1 if v1 else 32)
      case 'CPOP':   self._wr(rd, bin(v1).count('1'))
      case 'SEXT_B': self._wr(rd, _sext(v1 & 0xFF, 8))
      case 'SEXT_H': self._wr(rd, _sext(v1 & 0xFFFF, 16))
      case 'RORI':   self._wr(rd, (v1 >> shamt) | (v1 << (32 - shamt)))
      case 'ORC_B':
        r = 0
        for j in range(4):
          r |= (0xFF if (v1 >> j * 8) & 0xFF else 0) << j * 8
        self._wr(rd, r)
      case 'REV8':
        self._wr(rd, ((v1 & 0xFF) << 24) | ((v1 >> 8 & 0xFF) << 16)
                 | ((v1 >> 16 & 0xFF) << 8) | (v1 >> 24 & 0xFF))

      case 'LB':
        addr = (v1 + imm) & M32
        value = self.mem.read8(addr)
        if os.environ.get("EMU_TRACE_LAUNCH_LOADS") and 0x68 <= addr <= 0x6B:
          print(
              "EMU_TRACE_LAUNCH_LOAD",
              f"core={self.snapshot_core}",
              f"role={self.ROLE}",
              f"cycle={ctx.cycle}",
              f"pc=0x{pc:08x}",
              f"op=LB",
              f"addr=0x{addr:08x}",
              f"value=0x{value & 0xff:02x}",
          )
        self._wr(rd, _sext(value, 8))
      case 'LH':     self._wr(rd, _sext(self.mem.read16((v1 + imm) & M32), 16))
      case 'LW':     self._wr(rd, self.mem.read32((v1 + imm) & M32))
      case 'LBU':
        addr = (v1 + imm) & M32
        value = self.mem.read8(addr)
        if os.environ.get("EMU_TRACE_LAUNCH_LOADS") and 0x68 <= addr <= 0x6B:
          print(
              "EMU_TRACE_LAUNCH_LOAD",
              f"core={self.snapshot_core}",
              f"role={self.ROLE}",
              f"cycle={ctx.cycle}",
              f"pc=0x{pc:08x}",
              f"op=LBU",
              f"addr=0x{addr:08x}",
              f"value=0x{value & 0xff:02x}",
          )
        self._wr(rd, value)
      case 'LHU':    self._wr(rd, self.mem.read16((v1 + imm) & M32))

      case 'SB':
        addr = (v1 + imm) & M32
        if os.environ.get("EMU_TRACE_LAUNCH_STORES") and (0x68 <= addr <= 0x6B or addr == 0x373):
          print(
              "EMU_TRACE_LAUNCH_STORE",
              f"core={self.snapshot_core}",
              f"role={self.ROLE}",
              f"cycle={ctx.cycle}",
              f"pc=0x{pc:08x}",
              f"op=SB",
              f"addr=0x{addr:08x}",
              f"value=0x{v2 & 0xff:02x}",
          )
        self.mem.write8(addr, v2)
      case 'SH':     self.mem.write16((v1 + imm) & M32, v2)
      case 'SW':
        addr = (v1 + imm) & M32
        if os.environ.get("EMU_TRACE_LAUNCH_STORES") and addr == 0x68:
          print(
              "EMU_TRACE_LAUNCH_STORE",
              f"core={self.snapshot_core}",
              f"role={self.ROLE}",
              f"cycle={ctx.cycle}",
              f"pc=0x{pc:08x}",
              f"op=SW",
              f"addr=0x{addr:08x}",
              f"value=0x{v2 & M32:08x}",
          )
        self.mem.write32(addr, v2)

      case 'BEQ' | 'BNE' | 'BLT' | 'BGE' | 'BLTU' | 'BGEU':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        taken = {'BEQ': v1 == v2, 'BNE': v1 != v2, 'BLT': s1 < s2,
                 'BGE': s1 >= s2, 'BLTU': v1 < v2, 'BGEU': v1 >= v2}[d.name]
        if os.environ.get("EMU_TRACE_LAUNCH_BRANCHES") and self.ROLE in {"trisc0", "trisc1", "trisc2", "ncrisc"}:
          if 0x5400 <= pc <= 0x6B00:
            print(
                "EMU_TRACE_LAUNCH_BRANCH",
                f"core={self.snapshot_core}",
                f"role={self.ROLE}",
                f"cycle={ctx.cycle}",
                f"pc=0x{pc:08x}",
                f"name={d.name}",
                f"rs1={d.rs1}",
                f"v1=0x{v1 & M32:08x}",
                f"rs2={d.rs2}",
                f"v2=0x{v2 & M32:08x}",
                f"imm={imm}",
                f"taken={int(taken)}",
            )
        if taken:
          self.pc = (pc + imm) & M32

      case 'LUI':    self._wr(rd, imm)
      case 'AUIPC':  self._wr(rd, (pc + imm) & M32)
      case 'JAL':
        self._wr(rd, (pc + 4) & M32)
        self.pc = (pc + imm) & M32
      case 'JALR':
        self._wr(rd, (pc + 4) & M32)
        self.pc = (v1 + imm) & 0xFFFFFFFE

      case 'CSRRW' | 'CSRRS' | 'CSRRC' | 'CSRRWI' | 'CSRRSI' | 'CSRRCI':
        src = v1 if d.name in ('CSRRW', 'CSRRS', 'CSRRC') else rs1
        old = self._csr_read(d.csr, ctx)
        self._wr(rd, old)
        if d.name in ('CSRRW', 'CSRRWI'):
          self._csr_write(d.csr, src)
        elif src != 0 and d.name in ('CSRRS', 'CSRRSI'):
          self._csr_write(d.csr, old | src)
        elif src != 0 and d.name in ('CSRRC', 'CSRRCI'):
          self._csr_write(d.csr, old & ~src)

      case 'FENCE':
        pass
      case _:
        pass


class BRISC(Core):
  ROLE = 'brisc'
  LDM_SIZE = 0x2000
  PIPELINES = frozenset({0, 1, 2})


class NCRISC(Core):
  ROLE = 'ncrisc'
  LDM_SIZE = 0x2000
  PIPELINES = frozenset()


class TRISC0(Core):
  ROLE = 'trisc0'
  LDM_SIZE = 0x1000
  PIPELINES = frozenset({0})


class TRISC1(Core):
  ROLE = 'trisc1'
  LDM_SIZE = 0x1000
  PIPELINES = frozenset({1})


class TRISC2(Core):
  ROLE = 'trisc2'
  LDM_SIZE = 0x1000
  PIPELINES = frozenset({2})


# Backwards-compatible alias for older callers.
ProgramCore = Core
