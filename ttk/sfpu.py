from dataclasses import dataclass
from enum import IntEnum
import struct

from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk.dst import Dst
from ttk.mop import Mop, Replay
from ttk.sync import Sem, SemWait, Stall, Wait, sem_wait, stall


_CFG_STATE_ID = 0
_DST_ROW_BASE = 1
_ALU_CONFIG = TensixMMIO.CFG_BASE + 4


class SfpuFormat(IntEnum):
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO, INT32_SIGN_MAGNITUDE = range(10, 13)
  INT8_COMPAT, LO16_ONLY, HI16_ONLY = range(13, 16)


class LReg(IntEnum):
  # Ordinary read/write registers.
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)

  # Hardware constants.
  CONST_0_8373 = 8
  ZERO = 9
  ONE = 10

  # SFPCONFIG-programmable vector constants. Reset initializes CONFIG0 to -1.
  CONFIG0, CONFIG1, CONFIG2, CONFIG3 = range(11, 15)
  NEG_ONE = CONFIG0

  # Read-only lane values 0, 2, ..., 62.
  LANE_X2 = 15

  # SFPLOADMACRO-only pipeline register; never an ordinary operand.
  LOAD_MACRO = 16


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
    if not 0 <= self.block_destination_move < 4:
      raise ValueError("block_destination_move must fit in two bits")
    if not 0 <= self.row_mask < 16:
      raise ValueError("row_mask must fit in four bits")
    flags = (
      self.enable_fp16_infinity,
      self.disable_backdoor_load,
      self.enable_destination_index,
      self.capture_default_destination_index,
      self.block_destination_write,
      self.block_destination_read,
      self.destination_read_column_exchange,
      self.destination_write_column_exchange,
      self.exchange_srcb_srcc,
    )
    return (
      sum(int(flag) << bit for bit, flag in enumerate(flags)) |
      self.block_destination_move << 9 |
      self.row_mask << 12
    )


@dataclass(frozen=True)
class Vec:
  index: int
  owner: int
  name: str | None = None

  def __repr__(self): return self.name or f"v{self.index}"


@dataclass(frozen=True)
class _SfpuCode:
  words: tuple[int, ...]


def _bf16(value): return struct.unpack("<I", struct.pack("<f", float(value)))[0] >> 16
def _nop(): return TT.TTSFPNOP()


class SfpuProgramBuilder:
  """Builds one 32-lane, tile-relative SFPU iteration."""

  def __init__(self):
    self.owner, self.words, self.cycle, self.finished = id(self), [], 0, False
    self.allocated, self.initialized, self.ready_at = {}, set(), {}
    self.code = None

  def _open(self):
    if self.finished: raise RuntimeError("SFPU program is already finished")

  def vec(self, name=None):
    self._open()
    index = next((x for x in range(8) if x not in self.allocated), None)
    if index is None: raise MemoryError("SFPU program needs more than eight writable LRegs")
    value = self.allocated[index] = Vec(index, self.owner, name)
    return value

  def _index(self, value, read=True):
    if not isinstance(value, Vec) or value.owner != self.owner or self.allocated.get(value.index) is not value:
      raise ValueError("SFPU value belongs to another program")
    if read and value.index not in self.initialized:
      raise RuntimeError(f"read from uninitialized {value!r}")
    return value.index

  def _emit(self, word, reads=(), writes=(), latency=1):
    self._open()
    read = [self._index(value) for value in reads]
    write = [self._index(value, False) for value in writes]
    ready = max((self.ready_at.get(index, 0) for index in read), default=0)
    while self.cycle < ready:
      self.words.append(_nop()); self.cycle += 1
    issued = self.cycle
    self.words.append(word); self.cycle += 1
    for index in write:
      self.initialized.add(index)
      self.ready_at[index] = issued + latency
    return self

  def load(self, *, format=SfpuFormat.DEFAULT, offset=0, into=None):
    if type(offset) is not int or not 0 <= offset < 1024:
      raise ValueError("SFPU Dst offset must be in range 0..1023")
    if into is None: into = self.vec("value")
    self._emit(
      TT.TTSFPLOAD(self._index(into, False), int(format), 7, offset),
      writes=(into,),
    )
    return into

  def store(self, value, *, format=SfpuFormat.DEFAULT, offset=0):
    if type(offset) is not int or not 0 <= offset < 1024:
      raise ValueError("SFPU Dst offset must be in range 0..1023")
    return self._emit(
      TT.TTSFPSTORE(self._index(value), int(format), 7, offset),
      reads=(value,),
    )

  def add_immediate(self, value, immediate):
    return self._emit(
      TT.TTSFPADDI(_bf16(immediate), self._index(value), 0),
      reads=(value,), writes=(value,), latency=2,
    )

  def _finish(self):
    if self.code is None:
      self._emit(TT.TTINCRWC(0, 2, 0, 0))
      self.finished = True
      self.code = _SfpuCode(tuple(self.words))
    return self.code


class Sfpu:
  """Tile-level SFPU runner plus a one-vector program builder."""

  def __init__(self, kernel, dst: Dst):
    if kernel.role != "trisc1": raise RuntimeError("SFPU must run on trisc1")
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 1)
    self.prepared = {}

  def program(self): return SfpuProgramBuilder()

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _rmw_cfg_byte(self, register, byte, mask, data):
    opcode = (TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte]
    address = (int(register) - TensixMMIO.CFG_BASE) >> 2
    return self._issue(opcode(mask, data & mask, address))

  def _configure_dst(self, tile, lane_config):
    self._set_thread_cfg(_CFG_STATE_ID, 0)
    self._set_thread_cfg(_DST_ROW_BASE, self.dst.row_base(tile))
    stall(self.k, Stall.CFG, Wait.SFPU)
    self._rmw_cfg_byte(_ALU_CONFIG, 3, 0x40, 0x40 if self.dst.fp32 else 0)
    self._issue(TT.TTSFPCONFIG(lane_config.word(), int(LReg.LANE_X2), 1))
    self._issue(_nop())
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def _prepare(self, program):
    if not isinstance(program, SfpuProgramBuilder):
      raise TypeError("expected a program created by sfpu.program()")
    code = program._finish()
    if code not in self.prepared:
      start = self._mop.state.replay.allocate(
        len(code.words), lower=0, upper=16,
      )
      self._mop.load(Replay(start, code.words), initialize=True)
      self.prepared[code] = start
    return code, self.prepared[code]

  def run(self, program, *, tile, lane_config=LaneConfig()):
    code, start = self._prepare(program)
    sem_wait(
      self.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    self._configure_dst(tile, lane_config)
    stall(self.k, Stall.SFPU, Wait.MATH)
    for _ in range(4):
      for _ in range(8):
        self._mop._replay(start, len(code.words))
      for _ in range(2):
        self._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
    stall(self.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
    return self

  def add_scalar(self, value, *, tile, format=SfpuFormat.DEFAULT):
    program = self.program()
    vector = program.load(format=format)
    program.add_immediate(vector, value)
    program.store(vector, format=format)
    return self.run(program, tile=tile)
