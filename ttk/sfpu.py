from dataclasses import dataclass
from enum import IntEnum
import struct

from ttk.tensix import Tensix, TensixStall, TensixWait, ThreadCfg, tt_word

class SfpuFormat(IntEnum):
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO, INT32_SIGN_MAGNITUDE = range(10, 13)
  INT8_COMPAT, LO16_ONLY, HI16_ONLY = range(13, 16)

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
    if tensix.pipe != 1: raise ValueError("SFPU belongs to the math pipe")
    self.tensix, self.owner, self.installed = tensix, id(self), {}

  def initialize(self, lane_config=LaneConfig()):
    self.configure_lane(lane_config)
    for reg, value in ((ThreadCfg.SFPU_DEST_FMT, 0), (ThreadCfg.ADDR_MOD_AB_SEC6, 0),
      (ThreadCfg.ADDR_MOD_DST_SEC6, 2), (ThreadCfg.ADDR_MOD_BIAS_SEC6, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC7, 0), (ThreadCfg.ADDR_MOD_DST_SEC7, 0), (ThreadCfg.ADDR_MOD_BIAS_SEC7, 0)):
      self.tensix.set_thread_cfg(reg, value)
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF)); return self

  def configure_lane(self, config):
    if not isinstance(config, LaneConfig): raise TypeError("lane configuration must be LaneConfig")
    word, old = config.word(), self.tensix.state.sfpu_lane_config
    if old == word: return self
    self.tensix.issue(tt_word("TTSFPCONFIG", word, 15, 1))
    if old is None or (old ^ word) & 2: self.tensix.issue(_nop())
    self.tensix.state.sfpu_lane_config = word; return self

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

  def run_tile(self, program):
    if not isinstance(program, InstalledSfpuProgram) or program.owner != self.owner:
      raise ValueError("SFPU program belongs to another engine")
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.stall(TensixStall.SFPU, TensixWait.MATH)
    for _ in range(4):
      for _ in range(8): self.tensix.replay(program.start, len(program.program.words))
      for _ in range(2): self.tensix.issue(tt_word("TTSETRWC", 0, 4, 8, 0, 0, 4))
    self.tensix.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    self.tensix.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    return self
