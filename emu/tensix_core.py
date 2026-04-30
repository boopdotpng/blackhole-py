from __future__ import annotations

from functools import cache
from dataclasses import dataclass
from types import SimpleNamespace

from dsl import decode_tensix
from .memory import (
  PCBUF_COPROC_DONE, PCBUF_MOP_DONE, PCBUF_SEM_BASE, STREAM_BASE, STREAM_END,
  Memory,
)
from .tensix.frontend import WaitGate
from .tensix.state import (
  ADCState, AddrModState, DestRegFile, GPRFile, RWCState, Semaphores,
  SrcRegFile,
)
from .tensix.sync import MutexSet, SyncUnit
from .tensix.thcon import ConfigUnit, ScalarUnit
from .tensix.math import FPU, SFPU
from .tensix.mover import Mover
from .tensix.pack import Packer
from .tensix.tdma import TDMA
from .tensix.unpack import Unpacker, UnpackerState

from .frontend import InstructionFIFO
from .isa import Instruction, OpKind
from .resources import Resource, Scoreboard
from .sim import Phase, SimContext
from .timing import tensix_timing
from .units import TimedUnit


_UNIT_BY_OPCODE = {
  0xA0: Resource.TENSIX_SYNC,
  0xA1: Resource.TENSIX_SYNC,
  0xA2: Resource.TENSIX_SYNC,
  0xA3: Resource.TENSIX_SYNC,
  0xA4: Resource.TENSIX_SYNC,
  0xA5: Resource.TENSIX_SYNC,
  0xA6: Resource.TENSIX_SYNC,
  0xA7: Resource.TENSIX_SYNC,
  0x42: Resource.TENSIX_UNPACK,
  0x43: Resource.TENSIX_UNPACK,
  0x41: Resource.TENSIX_PACK,
  0x45: Resource.TENSIX_THCON,
  0x46: Resource.TENSIX_THCON,
}

_MATH_OPCODES = {
  0x08, 0x0A, 0x10, 0x11, 0x12, 0x13, 0x16, 0x17, 0x18, 0x21, 0x26,
  0x27, 0x28, 0x29, 0x30, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38,
}

_decode_tensix_cached = cache(decode_tensix)


class CfgMMIO:
  STATE1_OFFSET = 0x380

  def __init__(self, config_unit: ConfigUnit):
    self.config_unit = config_unit
    self.mem = Memory()

  def _decode_cfg_addr(self, addr):
    addr = addr & ~3
    if addr >= self.STATE1_OFFSET:
      state_id = 1
      addr32 = (addr - self.STATE1_OFFSET) >> 2
    else:
      state_id = 0
      addr32 = addr >> 2
    if addr32 < self.config_unit.CFG_WORDS:
      return state_id, addr32
    return None

  def _cfg_word(self, addr):
    decoded = self._decode_cfg_addr(addr)
    if decoded is None:
      return self.mem.read32(addr & ~3)
    state_id, addr32 = decoded
    return self.config_unit.cfg[state_id][addr32]

  def _write_word(self, addr, value):
    self.mem.write32(addr & ~3, value)
    decoded = self._decode_cfg_addr(addr)
    if decoded is not None:
      state_id, addr32 = decoded
      self.config_unit._write_cfg_word(state_id, addr32, value)

  def read8(self, addr):
    return (self._cfg_word(addr) >> (8 * (addr & 3))) & 0xFF

  def read16(self, addr):
    return (self._cfg_word(addr) >> (8 * (addr & 2))) & 0xFFFF

  def read32(self, addr):
    return self._cfg_word(addr)

  def write8(self, addr, val):
    shift = 8 * (addr & 3)
    self._write_word(addr, (self._cfg_word(addr) & ~(0xFF << shift)) | ((val & 0xFF) << shift))

  def write16(self, addr, val):
    shift = 8 * (addr & 2)
    self._write_word(addr, (self._cfg_word(addr) & ~(0xFFFF << shift)) | ((val & 0xFFFF) << shift))

  def write32(self, addr, val):
    self._write_word(addr, val)


class GPRMMIO:
  def __init__(self, gpr: GPRFile):
    self.gpr = gpr

  def _decode(self, addr):
    return (addr >> 8) & 0x3, (addr >> 2) & 0x3F

  def read8(self, addr):
    return (self.read32(addr & ~3) >> (8 * (addr & 3))) & 0xFF

  def read16(self, addr):
    return (self.read32(addr & ~3) >> (8 * (addr & 2))) & 0xFFFF

  def read32(self, addr):
    thread, reg = self._decode(addr)
    return self.gpr.read32(thread, reg) if thread < 3 else 0

  def write8(self, addr, val):
    shift = 8 * (addr & 3)
    self.write32(addr & ~3, (self.read32(addr) & ~(0xFF << shift)) | ((val & 0xFF) << shift))

  def write16(self, addr, val):
    shift = 8 * (addr & 2)
    self.write32(addr & ~3, (self.read32(addr) & ~(0xFFFF << shift)) | ((val & 0xFFFF) << shift))

  def write32(self, addr, val):
    thread, reg = self._decode(addr)
    if thread < 3:
      self.gpr.write32(thread, reg, val)


def decode_tensix_minimal(word: int) -> Instruction:
  opcode = (word >> 24) & 0xFF
  unit = _UNIT_BY_OPCODE.get(opcode)
  if opcode in (0x26, 0x98):
    # Blackhole MVMUL uses a 3-bit ADDR_MOD field. Replay/MOP expansion emits
    # opcode 0x26 words with the high bit in bit 16; some raw disassemblies also
    # show opcode 0x98 ttmvmul encodings in the SFPU range.
    addr_shift = 16 if opcode == 0x98 else 14
    decoded = SimpleNamespace(
      name="MVMUL",
      word=word,
      clear_dvalid=(word >> 22) & 0x3,
      instr_mod19=(word >> 19) & 0x7,
      addr_mode=(word >> addr_shift) & 0x7,
      dst=word & 0x3FF,
      broadcast_srcb=(word >> 19) & 0x1,
    )
    unit = Resource.TENSIX_MATH
  else:
    decoded = _decode_tensix_cached(word)
  if unit is None:
    if 0x70 <= opcode <= 0x99:
      unit = Resource.TENSIX_SFPU
    elif opcode in _MATH_OPCODES:
      unit = Resource.TENSIX_MATH
    else:
      unit = Resource.TENSIX_CFG
  timing = tensix_timing(decoded.name, unit)
  return Instruction(
    word=word,
    name=decoded.name,
    kind=OpKind.TENSIX,
    unit=timing.unit,
    latency=timing.latency,
    payload=decoded,
  )


@dataclass
class TensixThread:
  thread_id: int
  fifo: InstructionFIFO
  held: Instruction | None = None
  frontend_busy_until: int = 0
  mop_cfg: list[int] | None = None
  mop_mask_hi: int = 0
  mop_expansion: object | None = None
  replay_buffer: list[int] | None = None
  replay_playback: object | None = None
  replay_recording: dict | None = None
  wait_gate: WaitGate | None = None

  def next_instruction(self) -> Instruction | None:
    if self.held is not None:
      insn = self.held
      self.held = None
      return insn

    if self.replay_playback is not None:
      try:
        return decode_tensix_minimal(next(self.replay_playback))
      except StopIteration:
        self.replay_playback = None
        return None

    if self.replay_recording is not None:
      word = self._next_mop_word()
      if word is None:
        return None
      rec = self.replay_recording
      self.replay_buffer[(rec["start"] + rec["count"]) % 32] = word
      rec["count"] += 1
      if rec["count"] >= rec["total"]:
        self.replay_recording = None
      return decode_tensix_minimal(word) if rec["exec"] else None

    while True:
      word = self._next_mop_word()
      if word is None:
        return None

      opcode = (word >> 24) & 0xFF
      if opcode != 0x04:  # REPLAY
        return decode_tensix_minimal(word)

      start_idx = (word >> 14) & 0x1F
      length = (word >> 4) & 0x3F
      if length == 0:
        length = 64
      exec_while = bool((word >> 1) & 1)
      load_mode = bool(word & 1)
      if load_mode:
        self.replay_recording = {
          "start": start_idx,
          "total": length,
          "count": 0,
          "exec": exec_while,
        }
        return None

      self.replay_playback = self._play_replay(start_idx, length)
      try:
        return decode_tensix_minimal(next(self.replay_playback))
      except StopIteration:
        self.replay_playback = None
        return None

  def _next_mop_word(self) -> int | None:
    while True:
      if self.mop_expansion is not None:
        try:
          return next(self.mop_expansion)
        except StopIteration:
          self.mop_expansion = None
          return None

      insn = self.fifo.pop()
      if insn is None:
        return None

      opcode = (insn.word >> 24) & 0xFF
      if opcode == 0x03:  # MOP_CFG
        self.mop_mask_hi = insn.word & 0xFFFF
        continue
      if opcode == 0x01:  # MOP
        self.mop_expansion = self._expand_mop(insn.word)
        continue
      return insn.word

  def _play_replay(self, start: int, count: int):
    for i in range(count):
      yield self.replay_buffer[(start + i) % 32]

  @property
  def frontend_active(self) -> bool:
    return (
      self.mop_expansion is not None
      or self.replay_playback is not None
      or self.replay_recording is not None
    )

  @staticmethod
  def _is_nop(word: int) -> bool:
    return ((word >> 24) & 0xFF) == 0x02

  def _expand_mop(self, word: int):
    template = (word >> 23) & 1
    if template == 0:
      return self._expand_mop_template0(word)
    return self._expand_mop_template1()

  def _expand_mop_template0(self, word: int):
    count1 = (word >> 16) & 0x7F
    mask = (self.mop_mask_hi << 16) | (word & 0xFFFF)
    flags = self.mop_cfg[1]
    insn_b = self.mop_cfg[2]
    insn_a0 = self.mop_cfg[3]
    insn_a1 = self.mop_cfg[4]
    insn_a2 = self.mop_cfg[5]
    insn_a3 = self.mop_cfg[6]
    skip_a0 = self.mop_cfg[7]
    skip_b = self.mop_cfg[8]
    has_b = flags & 1
    has_a123 = flags & 2
    for _ in range(count1 + 1):
      if (mask & 1) == 0:
        yield insn_a0
        if has_a123:
          yield insn_a1
          yield insn_a2
          yield insn_a3
        if has_b:
          yield insn_b
      else:
        yield skip_a0
        if has_b:
          yield skip_b
      mask >>= 1

  def _expand_mop_template1(self):
    outer_count = self.mop_cfg[0] & 0x7F
    inner_count = self.mop_cfg[1] & 0x7F
    start_op = self.mop_cfg[2]
    end_op0 = self.mop_cfg[3]
    end_op1 = self.mop_cfg[4]
    loop_op = self.mop_cfg[5]
    loop_op1 = self.mop_cfg[6]
    loop0_last = self.mop_cfg[7]
    loop1_last = self.mop_cfg[8]

    if self._is_nop(loop_op1):
      loop_op_flip = 0
    else:
      loop_op_flip = loop_op ^ loop_op1
      inner_count *= 2

    # Preserve the hardware MOP template-1 quirk used by LLKs.
    if (outer_count == 1 and self._is_nop(start_op)
        and inner_count == 0 and not self._is_nop(end_op0)):
      outer_count += 128

    cur_loop_op = loop_op
    for j in range(outer_count):
      if not self._is_nop(start_op):
        yield start_op
      for i in range(inner_count):
        if i != inner_count - 1:
          yield cur_loop_op
        elif j != outer_count - 1:
          yield loop1_last
        else:
          yield loop0_last
        cur_loop_op ^= loop_op_flip
      if not self._is_nop(end_op0):
        yield end_op0
        if not self._is_nop(end_op1):
          yield end_op1

  def replay(self, insn: Instruction) -> None:
    self.held = insn

  def __post_init__(self):
    if self.mop_cfg is None:
      self.mop_cfg = [0] * 9
    if self.replay_buffer is None:
      self.replay_buffer = [0] * 32
    if self.wait_gate is None:
      self.wait_gate = WaitGate()


class Tensix:
  def __init__(self, scoreboard: Scoreboard | None = None, l1: Memory | None = None):
    self.scoreboard = scoreboard or Scoreboard()
    self.l1 = l1 if l1 is not None else Memory()
    self.semaphores = Semaphores()
    self.gpr = GPRFile()
    self.srca = SrcRegFile("SrcA")
    self.srcb = SrcRegFile("SrcB")
    self.dest = DestRegFile()
    self.rwc = [RWCState() for _ in range(3)]
    self.addr_mod = AddrModState()
    self.adc = [ADCState() for _ in range(3)]
    self.sync = SyncUnit(self.semaphores)
    self.config_unit = ConfigUnit(self.gpr)
    self.scalar = ScalarUnit(self.gpr)
    self.cfg = CfgMMIO(self.config_unit)
    self.gpr_mmio = GPRMMIO(self.gpr)
    self.unpackers = [UnpackerState(), UnpackerState()]
    self.unpack = Unpacker(self.srca, self.srcb)
    self.fpu = FPU(self.srca, self.srcb, self.dest, cfg=self.config_unit)
    self.sfpu = SFPU(self.dest, cfg=self.config_unit)
    self.packer = Packer(dest=self.dest, cfg=self.config_unit,
                         adc=self.adc, l1=self.l1)
    self.mover = Mover(l1=self.l1, cfg=self.cfg)
    self.tdma = TDMA(mover=self.mover, packer=self.packer)
    self.mutexes = MutexSet()
    self.stream_regs = None
    self._backend_inflight = [0, 0, 0]
    self.cycle = 0
    self.threads = [
      TensixThread(i, InstructionFIFO()) for i in range(3)
    ]
    self.units = {
      resource: TimedUnit(resource.name, resource, self.scoreboard)
      for resource in (
        Resource.TENSIX_SYNC, Resource.TENSIX_CFG, Resource.TENSIX_THCON,
        Resource.TENSIX_UNPACK, Resource.TENSIX_MATH, Resource.TENSIX_SFPU,
        Resource.TENSIX_PACK, Resource.TENSIX_MOVER,
      )
    }

  def push_word(self, thread_id: int, word: int) -> bool:
    return self.threads[thread_id].fifo.push(decode_tensix_minimal(word))

  def write_mop_cfg(self, thread_id: int, reg_index: int, value: int) -> None:
    if 0 <= thread_id < len(self.threads) and 0 <= reg_index < 9:
      self.threads[thread_id].mop_cfg[reg_index] = value & 0xFFFFFFFF

  def read_pcbuf(self, thread_id: int, offset: int) -> int | None:
    offset &= 0xFFFF
    if offset == PCBUF_MOP_DONE:
      return 0 if self.thread_frontend_idle(thread_id) else None
    if offset == PCBUF_COPROC_DONE:
      return 0 if self.thread_coprocessor_idle(thread_id) else None
    if PCBUF_SEM_BASE <= offset < PCBUF_SEM_BASE + 8 * 4:
      return self.semaphores.value[(offset - PCBUF_SEM_BASE) >> 2]
    return 0

  def write_pcbuf(self, thread_id: int, offset: int, value: int) -> None:
    offset &= 0xFFFF
    if PCBUF_SEM_BASE <= offset < PCBUF_SEM_BASE + 8 * 4:
      idx = (offset - PCBUF_SEM_BASE) >> 2
      if value & 1:
        self.semaphores.get(idx)
      else:
        self.semaphores.post(idx)

  def thread_frontend_idle(self, thread_id: int, cycle: int | None = None) -> bool:
    if not 0 <= thread_id < len(self.threads):
      return True
    thread = self.threads[thread_id]
    if cycle is None:
      cycle = self.cycle
    return (
      len(thread.fifo) == 0
      and thread.held is None
      and not thread.frontend_active
      and thread.frontend_busy_until <= cycle
    )

  def thread_coprocessor_idle(self, thread_id: int, cycle: int | None = None) -> bool:
    return self.thread_frontend_idle(thread_id, cycle) and self._backend_inflight[thread_id] == 0

  def tick(self, ctx: SimContext, phase: Phase) -> None:
    self.cycle = ctx.cycle
    if phase is Phase.COMMIT:
      for unit in self.units.values():
        unit.tick(ctx, phase)
    if phase is not Phase.ISSUE:
      return
    for thread in self.threads:
      if thread.frontend_busy_until > ctx.cycle:
        continue
      insn = thread.next_instruction()
      if insn is None:
        continue
      if thread.wait_gate.is_blocking(insn.word, _HwState(self), thread.thread_id):
        thread.replay(insn)
        continue
      if self._issue_frontend_macro(thread, insn, ctx):
        continue
      if self._issue_sync(thread, insn, ctx):
        continue
      if self._issue_thcon(thread, insn, ctx):
        continue
      if self._issue_datapath(thread, insn, ctx):
        continue
      unit = self.units[insn.unit]
      owner = f"t{thread.thread_id}"
      if not self._issue_backend(unit, owner, thread.thread_id, insn, ctx):
        thread.replay(insn)

  def _issue_backend(self, unit: TimedUnit, owner: str, thread_id: int,
                     insn: Instruction, ctx: SimContext, on_commit=None) -> bool:
    def commit(_ctx: SimContext) -> None:
      if on_commit is not None:
        on_commit(_ctx)
      self._backend_inflight[thread_id] -= 1

    issued = unit.issue(owner, insn, ctx, commit=commit)
    if issued:
      self._backend_inflight[thread_id] += 1
    return issued

  def _issue_sync(self, thread: TensixThread, insn: Instruction,
                  ctx: SimContext) -> bool:
    d = insn.payload
    if d is None:
      return False
    owner = f"t{thread.thread_id}"

    def commit(_ctx: SimContext) -> None:
      match d.name:
        case "SEMINIT": self.sync.execute_seminit(d)
        case "SEMPOST": self.sync.execute_sempost(d)
        case "SEMGET":  self.sync.execute_semget(d)
        case "STALLWAIT": self.sync.execute_stallwait(thread.wait_gate, d)
        case "SEMWAIT": self.sync.execute_semwait(thread.wait_gate, d)
        case "ATGETM":
          self.mutexes.acquire(d.mutex_index, thread.thread_id)
        case "ATRELM": self.mutexes.release(d.mutex_index, thread.thread_id)

    match d.name:
      case "ATGETM":
        owner = self.mutexes[d.mutex_index] if 0 <= d.mutex_index < len(self.mutexes) else None
        if owner is not None and owner != thread.thread_id:
          thread.replay(insn)
          return True
      case "ATRELM" | "SEMINIT" | "SEMPOST" | "SEMGET" | "STALLWAIT" | "SEMWAIT":
        pass
      case _:
        return False

    unit = self.units[Resource.TENSIX_SYNC]
    if not self._issue_backend(unit, owner, thread.thread_id, insn, ctx,
                               on_commit=commit):
      thread.replay(insn)
    return True

  def _issue_datapath(self, thread: TensixThread, insn: Instruction,
                      ctx: SimContext) -> bool:
    d = insn.payload
    if d is None:
      return False
    owner = f"t{thread.thread_id}"
    thread_id = thread.thread_id

    def commit(_ctx: SimContext) -> None:
      rwc = self.rwc[thread_id]
      adc = self.adc[thread_id]
      dest_offset_rows = self.config_unit.thread_cfg[thread_id][1] & 0x3FF
      self.fpu.dest_offset_rows = dest_offset_rows
      self.sfpu.dest_offset_rows = dest_offset_rows
      match d.name:
        # ADC
        case "SETADC": adc.execute_setadc(d)
        case "SETADCXY": adc.execute_setadcxy(d)
        case "SETADCZW": adc.execute_setadczw(d)
        case "INCADCZW": adc.execute_incadczw(d)
        case "SETADCXX": adc.execute_setadcxx(d)

        # Unpack
        case "UNPACR": self.unpack.handle_unpacr(d, thread_id, self)
        case "UNPACR_NOP": self.unpack.handle_unpacr_nop(d)

        # Matrix/FPU
        case "ZEROACC":
          self.fpu.zeroacc(d)
          if d.clear_mode in (0, 1):
            self._apply_addr_mod(thread_id, d.addr_mode)
        case "ZEROSRC": self.fpu.zerosrc(d)
        case "MOVA2D":
          self.fpu.mova2d(d, rwc)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "MOVB2D":
          self.fpu.movb2d(d, rwc)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "TRNSPSRCB": self.fpu.trnspsrcb(d)
        case "SHIFTXA": self.fpu.shiftxa(d)
        case "SHIFTXB": self.fpu.shiftxb(d)
        case "MVMUL":
          self.fpu.mvmul(d, rwc)
          self._clear_dvalid(thread_id, d)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "DOTPV":
          self.fpu.dotpv(d, rwc)
          self._clear_dvalid(thread_id, d)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "GAPOOL":
          self.fpu.gapool(d, rwc)
          self._clear_dvalid(thread_id, d)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "ELWADD":
          self.fpu.elwadd(d, rwc)
          self._clear_dvalid(thread_id, d)
          self._apply_addr_mod(thread_id, d.addr_mode)
        case "GMPOOL":
          self.fpu.gmpool(d, rwc)
          self._clear_dvalid(thread_id, d)
          self._apply_addr_mod(thread_id, d.pool_addr_mode & 3)
        case "CLEARDVALID": self.fpu.cleardvalid(d)
        case "MOVD2A": self.fpu.movd2a(d, rwc)
        case "MOVD2B": self.fpu.movd2b(d, rwc)
        case "SETRWC":
          clear_ab = rwc.execute_setrwc(d)
          if clear_ab & 1:
            self.srca.release_from_fpu(self._dvalid_clear_enabled(thread_id, 0))
          if clear_ab & 2:
            self.srcb.release_from_fpu(self._dvalid_clear_enabled(thread_id, 1))
        case "INCRWC": rwc.execute_incrwc(d)

        # SFPU
        case "SFPLOAD":
          self.sfpu.sfpload(d, rwc, thread_id)
          self._apply_addr_mod(thread_id, d.sfpu_addr_mode, update_fidelity=False)
        case "SFPLOADI": self.sfpu.sfploadi(d)
        case "SFPSTORE":
          self.sfpu.sfpstore(d, rwc, thread_id)
          self._apply_addr_mod(thread_id, d.sfpu_addr_mode, update_fidelity=False)
        case "SFPMULI": self.sfpu.sfpmuli(d)
        case "SFPADDI": self.sfpu.sfpaddi(d)
        case "SFPDIVP2": self.sfpu.sfpdivp2(d)
        case "SFPEXEXP": self.sfpu.sfpexexp(d)
        case "SFPEXMAN": self.sfpu.sfpexman(d)
        case "SFPSETEXP": self.sfpu.sfpsetexp(d)
        case "SFPIADD": self.sfpu.sfpiadd(d)
        case "SFPMUL24": self.sfpu.sfpmul24(d)
        case "SFPSHFT": self.sfpu.sfpshft(d)
        case "SFPSHFT2": self.sfpu.sfpshft2(d)
        case "SFPSETCC": self.sfpu.sfpsetcc(d)
        case "SFPGT": self.sfpu.sfpgt(d)
        case "SFPMOV": self.sfpu.sfpmov(d)
        case "SFPABS": self.sfpu.sfpabs(d)
        case "SFPSETSGN": self.sfpu.sfpsetsgn(d)
        case "SFPAND": self.sfpu.sfpand(d)
        case "SFPOR": self.sfpu.sfpor(d)
        case "SFPNOT": self.sfpu.sfpnot(d)
        case "SFPLZ": self.sfpu.sfplz(d)
        case "SFPXOR": self.sfpu.sfpxor(d)
        case "SFPMAD": self.sfpu.sfpmad(d)
        case "SFPADD": self.sfpu.sfpadd(d)
        case "SFPMUL": self.sfpu.sfpmul(d)
        case "SFPPUSHC": self.sfpu.sfppushc(d)
        case "SFPPOPC": self.sfpu.sfppopc(d)
        case "SFPENCC": self.sfpu.sfpencc(d)
        case "SFPCOMPC": self.sfpu.sfpcompc(d)
        case "SFPSTOCHRND": self.sfpu.sfpstochrnd(d)
        case "SFPCAST": self.sfpu.sfpcast(d)
        case "SFPCONFIG": self.sfpu.sfpconfig(d)
        case "SFPSWAP": self.sfpu.sfpswap(d)
        case "SFPLOADMACRO":
          self.sfpu.sfpload(d, rwc)
          if all(self.sfpu.lregs[d.lreg_ind][lane] == 0 for lane in range(1, 32)):
            recip = type("_SfpRecipD", (), {
              "lreg_c": d.lreg_ind, "lreg_dest": d.lreg_ind, "instr_mod1": 0
            })()
            self.sfpu.sfparecip(recip)
        case "SFPLUTFP32": self.sfpu.sfplutfp32(d)
        case "SFPARECIP": self.sfpu.sfparecip(d)
        case "SFPTRANSP": self.sfpu.sfptransp(d)
        case "SFPNOP": pass

        # Pack / mover
        case "PACR": self.packer.handle_pacr(d, thread_id)
        case "XMOV":
          cfg = self.config_unit
          sid = cfg._state_id(thread_id)
          if sid < cfg.NUM_STATES:
            src = cfg.cfg[sid][88] << 4
            dst = cfg.cfg[sid][89] << 4
            reg90 = cfg.cfg[sid][90]
            size = (reg90 & 0xFFFF) << 4
            direction = (reg90 >> 30) & 0x3
            self.mover.transfer(dst, src, size, direction)
        case _:
          pass

    names = {
      "SETADC", "SETADCXY", "SETADCZW", "INCADCZW", "SETADCXX",
      "UNPACR", "UNPACR_NOP",
      "ZEROACC", "ZEROSRC", "MOVA2D", "MOVB2D", "TRNSPSRCB", "SHIFTXA",
      "SHIFTXB", "MVMUL", "DOTPV", "GAPOOL", "ELWADD", "GMPOOL",
      "CLEARDVALID", "MOVD2A", "MOVD2B", "SETRWC", "INCRWC",
      "SFPLOAD", "SFPLOADI", "SFPSTORE", "SFPMULI", "SFPADDI", "SFPDIVP2",
      "SFPEXEXP", "SFPEXMAN", "SFPSETEXP", "SFPIADD", "SFPMUL24",
      "SFPSHFT", "SFPSHFT2", "SFPSETCC", "SFPGT", "SFPMOV", "SFPABS",
      "SFPSETSGN", "SFPAND", "SFPOR", "SFPNOT", "SFPLZ", "SFPXOR",
      "SFPMAD", "SFPADD", "SFPMUL", "SFPPUSHC", "SFPPOPC", "SFPENCC",
      "SFPCOMPC", "SFPSTOCHRND", "SFPCAST", "SFPCONFIG", "SFPSWAP",
      "SFPLOADMACRO", "SFPLUTFP32", "SFPARECIP", "SFPTRANSP", "SFPNOP",
      "PACR", "XMOV",
    }
    if d.name not in names:
      return False
    if not self._operands_ready(thread_id, d):
      thread.replay(insn)
      return True
    unit = self.units[insn.unit]
    if not self._issue_backend(unit, owner, thread_id, insn, ctx,
                               on_commit=commit):
      thread.replay(insn)
    return True

  def _operands_ready(self, thread_id, d):
    match d.name:
      case "UNPACR":
        # Regular UNPACR writes data into the current unpack bank whether or
        # not this specific instruction also performs SETDVALID.  Hardware's
        # wait gate blocks the write until that bank is owned by unpackers.
        # The final UNPACR in an LLK pair usually has SetDatValid=1, but the
        # earlier SetDatValid=0 UNPACR must obey the same ownership rule.
        src = self.srca if d.Unpack_block_selection == 0 else self.srcb
        if src.banks[src.unpack_bank].allowed_client != "unpackers":
          return False
      case _:
        pass
    match d.name:
      case "MOVA2D" | "MVMUL" | "DOTPV" | "GAPOOL" | "ELWADD" | "GMPOOL":
        if self.srca.banks[self.srca.fpu_bank].allowed_client != "matrix_unit":
          return False
      case _:
        pass
    match d.name:
      case "MOVB2D" | "MVMUL" | "DOTPV" | "ELWADD":
        if self.srcb.banks[self.srcb.fpu_bank].allowed_client != "matrix_unit":
          return False
      case _:
        pass
    return True

  def _dvalid_clear_enabled(self, thread_id, src_idx):
    return (self.config_unit.thread_cfg[thread_id][7] & (1 << src_idx)) == 0

  def _clear_dvalid(self, thread_id, d):
    if d.clear_dvalid & 1:
      self.srca.release_from_fpu(self._dvalid_clear_enabled(thread_id, 0))
    if d.clear_dvalid & 2:
      self.srcb.release_from_fpu(self._dvalid_clear_enabled(thread_id, 1))

  def _apply_addr_mod(self, thread_id, addr_mode, update_fidelity=True):
    rwc = self.rwc[thread_id]
    idx = addr_mode & 0x7
    cfg = self.config_unit.thread_cfg[thread_id]
    ab = cfg[12 + idx] & 0xFFFF
    dst = cfg[28 + idx] & 0xFFFF

    srca_incr = ab & 0x3F
    if ab & 0x80:
      rwc.a = 0; rwc.a_cr = 0
    elif ab & 0x40:
      rwc.a_cr = (rwc.a_cr + srca_incr) & 0x3F
      rwc.a = rwc.a_cr
    else:
      rwc.a = (rwc.a + srca_incr) & 0x3F

    srcb_incr = (ab >> 8) & 0x3F
    if ab & 0x8000:
      rwc.b = 0; rwc.b_cr = 0
    elif ab & 0x4000:
      rwc.b_cr = (rwc.b_cr + srcb_incr) & 0x3F
      rwc.b = rwc.b_cr
    else:
      rwc.b = (rwc.b + srcb_incr) & 0x3F

    dest_incr = dst & 0x3FF
    if dest_incr & 0x200:
      dest_incr -= 0x400
    if dst & 0x0800:
      rwc.d = 0; rwc.d_cr = 0
    elif dst & 0x1000:
      rwc.d = (rwc.d + dest_incr) & 0x3FF
      rwc.d_cr = rwc.d
    elif dst & 0x0400:
      rwc.d_cr = (rwc.d_cr + dest_incr) & 0x3FF
      rwc.d = rwc.d_cr
    else:
      rwc.d = (rwc.d + dest_incr) & 0x3FF

    if update_fidelity:
      if dst & 0x8000:
        rwc.cr = 0
      else:
        rwc.cr = (rwc.cr + ((dst >> 13) & 0x3)) & 0x7

  def _issue_thcon(self, thread: TensixThread, insn: Instruction,
                   ctx: SimContext) -> bool:
    d = insn.payload
    if d is None:
      return False
    owner = f"t{thread.thread_id}"

    def commit(_ctx: SimContext) -> None:
      match d.name:
        case "WRCFG" | "WRCFG32":
          self.config_unit.execute_wrcfg(d, thread.thread_id)
        case "RDCFG":
          self.config_unit.execute_rdcfg(d, thread.thread_id)
        case "SETC16":
          self.config_unit.execute_setc16(d, thread.thread_id)
        case "RMWCIB0":
          self.config_unit.execute_rmwcib(d, byte_index=0)
        case "RMWCIB1":
          self.config_unit.execute_rmwcib(d, byte_index=1)
        case "RMWCIB2":
          self.config_unit.execute_rmwcib(d, byte_index=2)
        case "RMWCIB3":
          self.config_unit.execute_rmwcib(d, byte_index=3)
        case "CFGSHIFTMASK":
          self.config_unit.execute_cfgshiftmask(d, thread.thread_id)
        case "STREAMWRCFG":
          self.config_unit.execute_streamwrcfg(d, thread.thread_id, self._read_stream_cfg)
        case "REG2FLOP":
          self.config_unit.execute_reg2flop(d, thread.thread_id)
        case "SETDMAREG":
          self.scalar.execute_setdmareg(d, thread.thread_id)
        case "ADDDMAREG":
          self.scalar.execute_adddmareg(d, thread.thread_id)
        case "MULDMAREG":
          self.scalar.execute_muldmareg(d, thread.thread_id)
        case "BITWOPDMAREG":
          self.scalar.execute_bitwopdmareg(d, thread.thread_id)
        case "SHIFTDMAREG":
          self.scalar.execute_shiftdmareg(d, thread.thread_id)
        case "CMPDMAREG":
          self.scalar.execute_cmpdmareg(d, thread.thread_id)
        case "STOREREG":
          self._store_reg(thread.thread_id, d)
        case "FLUSHDMA":
          pass

    match d.name:
      case ("WRCFG" | "WRCFG32" | "RDCFG" | "SETC16" | "RMWCIB0" | "RMWCIB1"
            | "RMWCIB2" | "RMWCIB3" | "CFGSHIFTMASK" | "STREAMWRCFG"
            | "REG2FLOP"):
        unit = self.units[Resource.TENSIX_CFG]
      case ("SETDMAREG" | "ADDDMAREG" | "MULDMAREG" | "BITWOPDMAREG"
            | "SHIFTDMAREG" | "CMPDMAREG" | "STOREREG" | "FLUSHDMA"):
        unit = self.units[Resource.TENSIX_THCON]
      case _:
        return False

    if not self._issue_backend(unit, owner, thread.thread_id, insn, ctx,
                               on_commit=commit):
      thread.replay(insn)
    return True

  def _read_stream_cfg(self, stream_sel, stream_reg_addr):
    if self.stream_regs is None:
      return 0
    stream_id = stream_sel & 3
    addr = (stream_id * 4096) + ((stream_reg_addr & 0x3FF) * 4)
    return self.stream_regs.read32(addr)

  def _store_reg(self, thread_id, d):
    if self.stream_regs is None:
      return
    addr = 0xFFB00000 | ((d.RegAddr & 0x3FFFF) << 2)
    if STREAM_BASE <= addr <= STREAM_END:
      self.stream_regs.write32(addr - STREAM_BASE, self.gpr.read32(thread_id, d.TdmaDataRegIndex))

  def _issue_frontend_macro(self, thread: TensixThread, insn: Instruction,
                            ctx: SimContext) -> bool:
    opcode = (insn.word >> 24) & 0xFF
    owner = f"t{thread.thread_id}"
    if opcode == 0x03:  # MOP_CFG mask-hi instruction
      thread.mop_mask_hi = insn.word & 0xFFFF
      return True
    if opcode == 0x01:  # MOP
      cycles = max(1, _estimate_mop_cycles(thread, insn.word))
      thread.frontend_busy_until = ctx.cycle + cycles
      return True
    if opcode == 0x04:  # REPLAY
      cycles = _estimate_replay_cycles(insn.word)
      if cycles is None:
        return False
      thread.frontend_busy_until = ctx.cycle + cycles
      return True
    return False


def _is_nop(word: int) -> bool:
  return ((word >> 24) & 0xFF) == 0x02


def _estimate_mop_cycles(thread: TensixThread, word: int) -> int:
  template = (word >> 23) & 1
  if template == 0:
    count1 = (word >> 16) & 0x7F
    mask = (thread.mop_mask_hi << 16) | (word & 0xFFFF)
    flags = thread.mop_cfg[1]
    has_b = flags & 1
    has_a123 = flags & 2
    emitted = 0
    for _ in range(count1 + 1):
      if (mask & 1) == 0:
        emitted += 1
        if has_a123:
          emitted += 3
        if has_b:
          emitted += 1
      else:
        emitted += 1
        if has_b:
          emitted += 1
      mask >>= 1
    return emitted + 1  # include the documented end transition bubble

  cfg = thread.mop_cfg
  outer_count = cfg[0] & 127
  inner_count = cfg[1] & 127
  start_op = cfg[2]
  end_op0, end_op1 = cfg[3], cfg[4]
  loop_op1 = cfg[6]
  if not _is_nop(loop_op1):
    inner_count *= 2
  if outer_count == 1 and _is_nop(start_op) and inner_count == 0 and not _is_nop(end_op0):
    outer_count += 128
  per_outer = inner_count
  if not _is_nop(start_op):
    per_outer += 1
  if not _is_nop(end_op0):
    per_outer += 1
    if not _is_nop(end_op1):
      per_outer += 1
  return outer_count * per_outer + 1


def _estimate_replay_cycles(word: int) -> int | None:
  length = (word >> 4) & 0x3F
  load_mode = word & 1
  if length == 0:
    length = 64
  # Playback can be collapsed safely. Record modes consume following frontend
  # instructions, so leave those on the precise path until replay buffers exist.
  if load_mode:
    return None
  return length


class _HwState:
  def __init__(self, tensix: Tensix):
    self.semaphores = tensix.semaphores
    self.math_busy = tensix._backend_inflight
    self.srca_unpack_bank_owner = (
      tensix.srca.banks[tensix.srca.unpack_bank].allowed_client)
    self.srcb_unpack_bank_owner = (
      tensix.srcb.banks[tensix.srcb.unpack_bank].allowed_client)
    self.srca_fpu_bank_owner = (
      tensix.srca.banks[tensix.srca.fpu_bank].allowed_client)
    self.srcb_fpu_bank_owner = (
      tensix.srcb.banks[tensix.srcb.fpu_bank].allowed_client)
