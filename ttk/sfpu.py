from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum
import struct

from isa import R
from ttk.tensix import Tensix, TensixRegs, TensixStall, TensixWait, ThreadCfg, tt_word

class SfpuFormat(IntEnum):
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO, INT32_SIGN_MAGNITUDE = range(10, 13)
  INT8_COMPAT, LO16_ONLY, HI16_ONLY = range(13, 16)

class LReg(IntEnum):
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)
  CONST_0, CONST_1, CONST_NEG1 = 9, 10, 11

@dataclass(frozen=True)
class LaneConfig:
  enable_fp16_infinity: bool = False
  disable_backdoor_load: bool = False
  enable_destination_index: bool = False
  capture_default_destination_index: bool = False
  block_destination_write: bool = False
  block_destination_read: bool = False
  destination_read_column_exchange: bool = False
  destination_write_column_exchange: bool = False
  exchange_srcb_srcc: bool = False
  block_destination_move: int = 0
  row_mask: int = 0

  def word(self):
    if not 0 <= self.block_destination_move < 4: raise ValueError("block_destination_move must fit in two bits")
    if not 0 <= self.row_mask < 16: raise ValueError("row_mask must fit in four bits")
    flags = (self.enable_fp16_infinity, self.disable_backdoor_load, self.enable_destination_index,
             self.capture_default_destination_index, self.block_destination_write, self.block_destination_read,
             self.destination_read_column_exchange, self.destination_write_column_exchange, self.exchange_srcb_srcc)
    return sum(int(flag) << bit for bit, flag in enumerate(flags)) | self.block_destination_move << 9 | self.row_mask << 12

@dataclass(frozen=True)
class DstRef:
  offset: int = 0
  format: SfpuFormat = SfpuFormat.SRCB
  addr_mod: int = 7

@dataclass(frozen=True)
class LRegRef:
  index: int
  owner: int
  name: str | None = None

  def __repr__(self): return self.name or f"L{self.index}"

@dataclass(frozen=True)
class SfpuProgram:
  words: tuple[int, ...]

@dataclass(frozen=True)
class InstalledSfpuProgram:
  program: SfpuProgram
  start: int
  owner: int

def _bf16(value): return struct.unpack("<I", struct.pack("<f", float(value)))[0] >> 16
def _nop(): return tt_word("TTSFPNOP")

class SfpuProgramBuilder:
  def __init__(self):
    self.owner, self.words, self.cycle, self.finished = id(self), [], 0, False
    self.allocated, self.initialized, self.ready_at = {}, set(), {}

  def _open(self):
    if self.finished: raise RuntimeError("SFPU program is already finished")

  def reg(self, index=None, *, name=None, initialized=False):
    self._open()
    if index is None: index = next((x for x in range(8) if x not in self.allocated), None)
    if index is None: raise MemoryError("SFPU program has no free LRegs")
    if not 0 <= index < 8 or index in self.allocated: raise ValueError(f"invalid or allocated L{index}")
    reg = self.allocated[index] = LRegRef(index, self.owner, name)
    if initialized: self.initialized.add(index); self.ready_at[index] = 0
    return reg

  def _index(self, reg, read=True):
    if not isinstance(reg, LRegRef) or reg.owner != self.owner or self.allocated.get(reg.index) is not reg:
      raise ValueError("SFPU register belongs to another program")
    if read and reg.index not in self.initialized: raise RuntimeError(f"read from uninitialized {reg!r}")
    return reg.index

  def _emit(self, word, *, reads=(), writes=(), latency=1):
    self._open(); read = [self._index(x) for x in reads]; write = [self._index(x, False) for x in writes]
    ready = max((self.ready_at.get(x, 0) for x in read), default=0)
    while self.cycle < ready: self.words.append(_nop()); self.cycle += 1
    issued = self.cycle; self.words.append(word); self.cycle += 1
    for index in write: self.initialized.add(index); self.ready_at[index] = issued + latency
    return self

  def load(self, source=DstRef(), *, into=None):
    if into is None: into = self.reg(name="value")
    self._emit(tt_word("TTSFPLOAD", self._index(into, False), int(source.format), source.addr_mod, source.offset), writes=(into,))
    return into

  def store(self, value, destination=DstRef()):
    return self._emit(tt_word("TTSFPSTORE", self._index(value), int(destination.format),
                              destination.addr_mod, destination.offset), reads=(value,))

  def add_immediate(self, value, immediate):
    return self._emit(tt_word("TTSFPADDI", _bf16(immediate), self._index(value), 0),
                      reads=(value,), writes=(value,), latency=2)

  def advance_dst(self, amount=2):
    if not 0 <= amount < 16: raise ValueError("Dst increment must fit in four bits")
    return self._emit(tt_word("TTINCRWC", 0, amount, 0, 0))

  def finish(self): self._open(); self.finished = True; return SfpuProgram(tuple(self.words))

class Sfpu:
  def __init__(self, tensix: Tensix):
    self.tensix, self.owner, self.installed = tensix, id(self), {}

  def initialize(self, lane_config=LaneConfig()):
    self.configure_lane(lane_config)
    for reg, value in ((ThreadCfg.SFPU_DEST_FMT, 0), (ThreadCfg.ADDR_MOD_AB_SEC6, 0),
      (ThreadCfg.ADDR_MOD_DST_SEC6, 2), (ThreadCfg.ADDR_MOD_BIAS_SEC6, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC7, 0), (ThreadCfg.ADDR_MOD_DST_SEC7, 0), (ThreadCfg.ADDR_MOD_BIAS_SEC7, 0)):
      self.tensix.set_thread_cfg(reg, value)
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF)); return self

  def configure_lane(self, config):
    word, old = config.word(), self.tensix.state.sfpu_lane_config
    if old == word: return self
    self.tensix.issue(tt_word("TTSFPCONFIG", word, 15, 1))
    if old is None or (old ^ word) & 2: self.tensix.issue(_nop())
    self.tensix.state.sfpu_lane_config = word; return self

  def _issue(self, opcode, *args):
    self.tensix.issue(tt_word(opcode, *args)); return self

  def _dst_memory(self, opcode, value, offset, *, format, addr_mod, delta):
    value, format = int(value), int(format)
    if isinstance(offset, R):
      k = self.tensix.k
      with k.scope():
        address = k.reg(exclude=offset)
        if delta: k.addi(address, offset, delta)
        else: k.mv(address, offset)
        instruction = k.reg(exclude=(offset, address))
        k.li(instruction, tt_word(opcode, value, format, addr_mod, 0))
        k.add(instruction, instruction, address)
        k.write32(TensixRegs.INSTRN_BUF_BASE, instruction)
      return self
    offset += delta
    if not 0 <= offset < 1 << 12: raise ValueError("SFPU Dst offset must fit in 12 bits")
    return self._issue(opcode, value, format, addr_mod, offset)

  def load_dst(self, into, offset=0, *, format=SfpuFormat.DEFAULT, addr_mod=7, delta=0):
    return self._dst_memory("TTSFPLOAD", into, offset, format=format, addr_mod=addr_mod, delta=delta)

  def store_dst(self, value, offset=0, *, format=SfpuFormat.DEFAULT, addr_mod=7, delta=0):
    return self._dst_memory("TTSFPSTORE", value, offset, format=format, addr_mod=addr_mod, delta=delta)

  def move(self, source, destination): return self._issue("TTSFPMOV", 0, int(source), int(destination), 0)

  def multiply(self, left, right, destination, *, negate=False):
    return self._issue(
      "TTSFPMUL", int(left), int(right), int(LReg.CONST_0), int(destination), int(negate),
    )

  def add(self, left, right, destination):
    return self._issue("TTSFPADD", int(LReg.CONST_1), int(left), int(right), int(destination), 0)

  def add_into(self, destination, source): return self.add(destination, source, destination)

  def maximum_into(self, destination, source):
    return self._issue("TTSFPSWAP", 0, int(destination), int(source), 1)

  def horizontal_max(self, value=LReg.L0, scratch=LReg.L1):
    for shifts in (4, 2, 1):
      self.move(value, scratch)
      for _ in range(shifts): self._issue("TTSFPSHFT2", 0, int(scratch), int(scratch), 3)
      self.maximum_into(value, scratch)
    return self

  def horizontal_sum(self, value=LReg.L0, scratch=LReg.L1):
    for shifts in (4, 2, 1):
      self.move(value, scratch)
      for _ in range(shifts): self._issue("TTSFPSHFT2", 0, int(scratch), int(scratch), 3)
      self.add_into(value, scratch)
    return self

  @staticmethod
  def _float_bits(value): return struct.unpack("<I", struct.pack("<f", float(value)))[0]

  def load_float(self, destination, value):
    bits = self._float_bits(value)
    self._issue("TTSFPLOADI", int(destination), 10, bits & 0xFFFF)
    return self._issue("TTSFPLOADI", int(destination), 8, bits >> 16)

  @staticmethod
  def _scratch(scratch, avoid, count):
    result = []
    for reg in map(int, scratch):
      if reg in avoid or not 0 <= reg < 8 or reg in result: continue
      result.append(reg)
      if len(result) == count: return result
    raise ValueError(f"need {count} SFPU scratch LRegs avoiding {sorted(avoid)}")

  def exp(self, source, destination, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
    """Natural exponent using Blackhole's device-validated FP32-LReg path."""
    source, destination = int(source), int(destination)
    c, exponent, mantissa, polynomial = self._scratch(scratch, {source, destination}, 4)
    self.load_float(c, 1.4426950216293334961)
    self.multiply(source, c, destination)._issue("TTSFPNOP")
    self._issue("TTSFPADDI", self._float_bits(127.0) >> 16, destination, 0)._issue("TTSFPNOP")
    self._issue("TTSFPLOADI", c, 0, 0)._issue("TTSFPSWAP", 0, destination, c, 1)._issue("TTSFPNOP")
    self._issue("TTSFPLOADI", c, 0, self._float_bits(255.0) >> 16)
    self._issue("TTSFPSWAP", 0, c, destination, 1)._issue("TTSFPNOP")
    self._issue("TTSFPEXEXP", 0, destination, exponent, 0)
    self._issue("TTSFPEXMAN", 0, destination, mantissa, 0)
    self._issue("TTSFPSHFT", 0, exponent, mantissa, 0)._issue("TTSFPNOP")
    self._issue("TTSFPEXEXP", 0, mantissa, exponent, 1)
    self._issue("TTSFPEXMAN", 0, mantissa, mantissa, 1)
    self._issue("TTSFPCAST", mantissa, mantissa, 0)._issue("TTSFPNOP")
    self.load_float(polynomial, 4.791750143340323e-15)
    self.multiply(polynomial, mantissa, polynomial)._issue("TTSFPNOP")
    self.load_float(c, 7.839635491371155e-08)
    self.add(polynomial, c, polynomial)._issue("TTSFPNOP")
    self.multiply(polynomial, mantissa, polynomial)._issue("TTSFPNOP")
    self.load_float(c, 1.0017248)
    self.add(polynomial, c, polynomial)._issue("TTSFPNOP")
    self._issue("TTSFPSETEXP", 0, polynomial, exponent, 0)._issue("TTSFPNOP")
    if exponent != destination: self.move(exponent, destination)
    return self

  def reciprocal(self, source, destination, *, scratch=(0, 1, 2, 3, 4, 5, 6, 7), iterations=2):
    """Approximate reciprocal followed by FP32 Newton-Raphson refinement."""
    if iterations < 0: raise ValueError("reciprocal iteration count must be non-negative")
    source, destination = int(source), int(destination)
    x = source
    if source == destination and iterations:
      x = self._scratch(scratch, {source, destination}, 1)[0]
      self.move(source, x)
    two, temporary = self._scratch(scratch, {source, destination, x}, 2)
    self.load_float(two, 2.0)._issue("TTSFPARECIP", 0, source, destination, 0)._issue("TTSFPNOP")
    for _ in range(iterations):
      self._issue("TTSFPMAD", x, destination, two, temporary, 2)._issue("TTSFPNOP")
      self.multiply(temporary, destination, destination, negate=True)._issue("TTSFPNOP")
    return self

  def reciprocal_positive(self, source, destination, *, maximum, scratch=(0, 1, 2, 3, 4, 5, 6, 7), iterations=18):
    """Reciprocal for ``0 < source <= maximum`` using a bounded FP32 Newton seed."""
    if maximum <= 0 or iterations < 0:
      raise ValueError("positive reciprocal needs a positive bound and iteration count")
    source, destination = int(source), int(destination)
    x = source
    if source == destination:
      x = self._scratch(scratch, {source, destination}, 1)[0]
      self.move(source, x)
    two, temporary = self._scratch(scratch, {source, destination, x}, 2)
    self.load_float(destination, 1.0 / float(maximum)); self.load_float(two, 2.0)
    for _ in range(iterations):
      self._issue("TTSFPMAD", x, destination, two, temporary, 2)._issue("TTSFPNOP")
      self.multiply(temporary, destination, destination, negate=True)._issue("TTSFPNOP")
    return self

  @contextmanager
  def tile(self):
    """Synchronize Math/SFPU around direct operations on the current Dst tile."""
    self.tensix.k.write32(TensixRegs.INSTRN_BUF_BASE, 0xB2010000)
    self._issue("TTSETRWC", 0, 0, 0, 0, 0, 4)
    self.tensix.stall(TensixStall.SFPU, TensixWait.MATH)
    yield self
    self.tensix.k.write32(TensixRegs.INSTRN_BUF_BASE, tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.k.write32(TensixRegs.INSTRN_BUF_BASE, tt_word(
      "TTSTALLWAIT", int(TensixStall.SYNC), int(TensixWait.MATH | TensixWait.SFPU),
    ))

  def add_immediate_program(self, immediate, *, format=SfpuFormat.SRCB):
    builder, dst = SfpuProgramBuilder(), DstRef(format=format)
    value = builder.load(dst); builder.add_immediate(value, immediate); builder.store(value, dst); builder.advance_dst()
    return builder.finish()

  def install(self, program, *, start=None, replay_range=(0, 16)):
    if start is None and program in self.installed: return self.installed[program]
    lower, upper = replay_range
    start = self.tensix.state.mop[1].replay.allocate(len(program.words), start=start, lower=lower, upper=upper)
    self.tensix.load_replay(program.words, start=start)
    installed = InstalledSfpuProgram(program, start, self.owner); self.installed[program] = installed
    return installed

  def run(self, program, *, wait=True):
    """Issue an arbitrary-length SFPU program from the kernel text.

    ``install`` is ideal for small programs that fit in the 32-word replay
    buffer.  Reduction and normalization programs are often larger, so this
    path emits their words inline while preserving the same program object.
    """
    if not isinstance(program, SfpuProgram): raise TypeError("expected an SfpuProgram")
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.stall(TensixStall.SFPU, TensixWait.MATH)
    for word in program.words: self.tensix.issue(word)
    if wait: self.tensix.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    return self

  def run_tile(self, program):
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.stall(TensixStall.SFPU, TensixWait.MATH)
    for _ in range(4):
      for _ in range(8): self.tensix.replay(program.start, len(program.program.words))
      for _ in range(2): self.tensix.issue(tt_word("TTSETRWC", 0, 4, 8, 0, 0, 4))
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    return self
