from dataclasses import dataclass
from enum import IntEnum
import struct

from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk import Dst
from ttk.mop import LoopTemplate, Mop, REPLAY_SIZE, Replay
from ttk.sync import Sem, SemWait, Stall, Wait, sem_get, sem_post, sem_wait, stall


_CFG_STATE_ID = 0
_DST_ROW_BASE = 1
_ALU_CONFIG = TensixMMIO.CFG_BASE + 4
_FACE_STEP = TT.TTSETRWC(0, 4, 8, 0, 0, 4)
_VECTOR_STEP = TT.TTINCRWC(0, 2, 0, 0)
_RESET_DST = TT.TTSETRWC(0, 0, 0, 0, 0, 4)


class SfpuFormat(IntEnum):
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO, INT32_SIGN_MAGNITUDE = range(10, 13)
  INT8_COMPAT, LO16_ONLY, HI16_ONLY = range(13, 16)


class LReg(IntEnum):
  # Ordinary read/write registers.
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)

  # Read-only hardware constants.
  CONST_0_8373 = 8
  ZERO = 9
  ONE = 10
  NEG_ONE = 11

  # SFPCONFIG-programmable vector constants.
  CONFIG0, CONFIG1, CONFIG2 = range(12, 15)

  # Read-only lane values 0, 2, ..., 62.
  LANE_X2 = 15

  # SFPLOADMACRO-only pipeline register; never an ordinary operand.
  LOAD_MACRO = 16


class _LoadImmediate(IntEnum):
  FLOATB = 0
  FLOATA = 1
  USHORT = 2
  SHORT = 4
  UPPER = 8
  LOWER = 10


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
class SfpuProgram:
  setup_words: tuple[int, ...]
  words: tuple[int, ...]

  def __post_init__(self):
    if not self.words:
      raise ValueError("an SFPU program must contain at least one instruction")


def _float_bits(value):
  return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def _bf16(value): return _float_bits(value) >> 16
def _nop(): return TT.TTSFPNOP()


class SfpuProgramBuilder:
  def __init__(self):
    self.owner, self.words, self.cycle, self.finished = id(self), [], 0, False
    self.allocated, self.initialized, self.ready_at = {}, set(), {}
    self.persistent, self.config_constants = {}, {}
    self._program = None

  def _open(self):
    if self.finished: raise RuntimeError("SFPU program is already finished")

  def vec(self, name=None):
    self._open()
    index = next((x for x in range(8) if x not in self.allocated), None)
    if index is None:
      raise MemoryError("SFPU program needs more than eight writable LRegs")
    value = self.allocated[index] = Vec(index, self.owner, name)
    return value

  def free(self, value):
    self._open()
    index = self._ordinary_index(value, read=False)
    if index in self.persistent:
      raise ValueError("a program constant must remain live for the whole program")
    del self.allocated[index]
    self.initialized.discard(index)
    self.ready_at.pop(index, None)
    return self

  def _ordinary_index(self, value, read=True):
    if (
      not isinstance(value, Vec) or value.owner != self.owner or
      self.allocated.get(value.index) is not value
    ):
      raise ValueError("SFPU value belongs to another program or has been freed")
    if read and value.index not in self.initialized:
      raise RuntimeError(f"read from uninitialized {value!r}")
    return value.index

  def _read_index(self, value):
    if isinstance(value, LReg):
      if value not in (LReg.ZERO, LReg.ONE, LReg.NEG_ONE):
        raise ValueError("raw LRegs are not public SFPU program values")
      return int(value)
    if isinstance(value, Vec) and value.owner == self.owner:
      if self.config_constants.get(value.index) is value:
        return value.index
      return self._ordinary_index(value)
    raise ValueError("SFPU value belongs to another program or has been freed")

  def _write_index(self, value):
    index = self._ordinary_index(value, read=False)
    if index in self.persistent:
      raise ValueError("a program constant is read-only")
    return index

  def _destination(self, into, name):
    return self.vec(name) if into is None else into

  def _emit(self, word, reads=(), writes=(), latency=1, forced_nop=False):
    self._open()
    read = [self._read_index(value) for value in reads]
    write = [self._write_index(value) for value in writes]
    ready = max((self.ready_at.get(index, 0) for index in read), default=0)
    while self.cycle < ready:
      self.words.append(_nop())
      self.cycle += 1
    issued = self.cycle
    self.words.append(word)
    self.cycle += 1
    for index in write:
      self.initialized.add(index)
      self.ready_at[index] = issued + latency
    if forced_nop:
      self.words.append(_nop())
      self.cycle += 1
    return self

  def load(self, *, format=SfpuFormat.DEFAULT, offset=0, into=None):
    if type(offset) is not int or not 0 <= offset < 1024:
      raise ValueError("SFPU Dst offset must be in range 0..1023")
    into = self._destination(into, "load")
    self._emit(
      TT.TTSFPLOAD(self._write_index(into), int(format), 7, offset),
      writes=(into,),
    )
    return into

  def store(self, value, *, format=SfpuFormat.DEFAULT, offset=0):
    if type(offset) is not int or not 0 <= offset < 1024:
      raise ValueError("SFPU Dst offset must be in range 0..1023")
    self._emit(
      TT.TTSFPSTORE(self._read_index(value), int(format), 7, offset),
      reads=(value,),
    )
    return self

  def load_float(self, value, *, into=None):
    into = self._destination(into, "constant")
    bits = _float_bits(value)
    self._emit(
      TT.TTSFPLOADI(self._write_index(into), _LoadImmediate.LOWER, bits & 0xffff),
      writes=(into,),
    )
    self._emit(
      TT.TTSFPLOADI(self._write_index(into), _LoadImmediate.UPPER, bits >> 16),
      writes=(into,),
    )
    return into

  def constant(self, value, *, name=None):
    bits = _float_bits(value)
    for index, existing in self.persistent.items():
      if index < 8 and existing == bits: return self.allocated[index]
    result = self.vec(name or f"{float(value):g}")
    self.persistent[result.index] = bits
    self.initialized.add(result.index)
    self.ready_at[result.index] = 0
    return result

  def _config_bits(self, bits, name):
    self._open()
    bits &= 0xffffffff
    for index, value in self.persistent.items():
      if index >= int(LReg.CONFIG0) and value == bits:
        return self.config_constants[index]
    index = next(
      (x for x in range(int(LReg.CONFIG0), int(LReg.CONFIG2) + 1)
       if x not in self.config_constants),
      None,
    )
    if index is None:
      raise MemoryError("SFPU program needs more than three programmable constants")
    result = Vec(index, self.owner, name)
    self.config_constants[index] = result
    self.persistent[index] = bits
    return result

  def _config_constant(self, value, name=None):
    return self._config_bits(_float_bits(value), name or f"{float(value):g}")

  def move(self, value, *, into=None):
    into = self._destination(into, "move")
    self._emit(
      TT.TTSFPMOV(0, self._read_index(value), self._write_index(into), 0),
      reads=(value,), writes=(into,),
    )
    return into

  def rand_fast(self, *, into=None):
    into = self._destination(into, "rand_fast")
    index = self._write_index(into)
    self._emit(
      TT.TTSFPMOV(0, 9, index, 8),
      writes=(into,),
    )
    self._emit(
      TT.TTSFPSETSGN(0, index, index, 1),
      reads=(into,), writes=(into,),
    )
    self._emit(
      TT.TTSFPSETEXP(127, index, index, 1),
      reads=(into,), writes=(into,),
    )
    self._emit(
      TT.TTSFPADDI(_bf16(-1.0), index, 0),
      reads=(into,), writes=(into,), latency=2,
    )
    self.mad(into, LReg.ONE, LReg.ZERO, into=into)
    return into

  def add(self, left, right, *, into=None):
    into = self._destination(into, "add")
    self._emit(
      TT.TTSFPADD(
        LReg.ONE, self._read_index(left), self._read_index(right),
        self._write_index(into), 0,
      ),
      reads=(left, right), writes=(into,), latency=2,
    )
    return into

  def sub(self, left, right, *, into=None):
    into = self._destination(into, "sub")
    self._emit(
      TT.TTSFPMAD(
        self._read_index(right), LReg.NEG_ONE, self._read_index(left),
        self._write_index(into), 0,
      ),
      reads=(left, right), writes=(into,), latency=2,
    )
    return into

  def mul(self, left, right, *, into=None):
    into = self._destination(into, "mul")
    self._emit(
      TT.TTSFPMUL(
        self._read_index(left), self._read_index(right), LReg.ZERO,
        self._write_index(into), 0,
      ),
      reads=(left, right), writes=(into,), latency=2,
    )
    return into

  def mad(self, left, right, addend, *, into=None,
          negate_product=False, negate_addend=False):
    into = self._destination(into, "mad")
    modifier = int(negate_product) | int(negate_addend) << 1
    self._emit(
      TT.TTSFPMAD(
        self._read_index(left), self._read_index(right),
        self._read_index(addend), self._write_index(into), modifier,
      ),
      reads=(left, right, addend), writes=(into,), latency=2,
    )
    return into

  def add_scalar(self, value, immediate, *, into=None):
    into = value if into is None else into
    if into is not value: self.move(value, into=into)
    self._emit(
      TT.TTSFPADDI(_bf16(immediate), self._read_index(into), 0),
      reads=(into,), writes=(into,), latency=2,
    )
    return into

  def mul_scalar(self, value, immediate, *, into=None):
    into = value if into is None else into
    if into is not value: self.move(value, into=into)
    self._emit(
      TT.TTSFPMULI(_bf16(immediate), self._read_index(into), 0),
      reads=(into,), writes=(into,), latency=2,
    )
    return into

  def neg(self, value, *, into=None):
    into = self._destination(into, "neg")
    self._emit(
      TT.TTSFPMUL(
        self._read_index(value), LReg.NEG_ONE, LReg.ZERO,
        self._write_index(into), 0,
      ),
      reads=(value,), writes=(into,), latency=2,
    )
    return into

  def _swap_min_max(self, source, destination):
    # VEC_MIN_MAX leaves min(source, destination) in destination.  Blackhole
    # requires an SFP NOP in the cycle following SFPSWAP.
    self._emit(
      TT.TTSFPSWAP(
        0, self._read_index(source), self._write_index(destination), 1,
      ),
      reads=(source, destination), writes=(destination,),
      latency=2, forced_nop=True,
    )

  def exp(self, value, *, into=None):
    self._read_index(value)
    result = value if into is None else into
    if result is not value: self._write_index(result)
    work = value if result is value else self.move(value, into=result)

    bias = self.constant(127.0, name="exp_bias")
    c1 = self.constant(7.839635491371155e-08, name="exp_c1")
    c0 = self.constant(1.0017248, name="exp_c0")
    log2e = self._config_constant(1.4426950216293335, "log2e")
    c2 = self._config_constant(4.791750143340323e-15, "exp_c2")
    exponent = self.vec("exp_exponent")
    polynomial = self.vec("exp_polynomial")
    xlog2 = self.vec("exp_xlog2")

    self.mad(work, log2e, bias, into=xlog2)
    self._emit(
      TT.TTSFPLOADI(
        self._write_index(exponent), _LoadImmediate.FLOATB, 0x437f,
      ),
      writes=(exponent,),
    )
    self._swap_min_max(exponent, xlog2)
    self._emit(
      TT.TTSFPEXEXP(0, self._read_index(xlog2), self._write_index(exponent), 0),
      reads=(xlog2,), writes=(exponent,),
    )
    self._emit(
      TT.TTSFPEXMAN(0, self._read_index(xlog2), self._write_index(work), 0),
      reads=(xlog2,), writes=(work,),
    )
    self._emit(
      TT.TTSFPSHFT(0, self._read_index(exponent), self._write_index(work), 0),
      reads=(exponent, work), writes=(work,),
    )
    self._emit(
      TT.TTSFPEXMAN(0, self._read_index(work), self._write_index(exponent), 1),
      reads=(work,), writes=(exponent,),
    )
    self._emit(
      TT.TTSFPCAST(
        self._read_index(exponent), self._write_index(exponent), 0,
      ),
      reads=(exponent,), writes=(exponent,),
    )
    self.mad(exponent, c2, c1, into=polynomial)
    self._emit(
      TT.TTSFPGT(0, LReg.ZERO, self._write_index(xlog2), 8),
      reads=(xlog2,), writes=(xlog2,),
    )
    self.mad(polynomial, exponent, c0, into=exponent)
    self._emit(
      TT.TTSFPAND(
        self._read_index(work), self._read_index(xlog2),
        self._write_index(work), 1,
      ),
      reads=(work, xlog2), writes=(work,),
    )
    self._emit(
      TT.TTSFPSETEXP(
        0, self._read_index(exponent), self._write_index(work), 2,
      ),
      reads=(exponent, work), writes=(work,),
    )

    for scratch in (exponent, polynomial, xlog2): self.free(scratch)
    return result

  def reciprocal(self, value, *, into=None):
    self._read_index(value)
    result = value if into is None else into
    if result is not value: self._write_index(result)
    y, error, correction = (
      self.vec("reciprocal_y"),
      self.vec("reciprocal_error"),
      self.vec("reciprocal_correction"),
    )

    self._emit(
      TT.TTSFPARECIP(0, self._read_index(value), self._write_index(y), 0),
      reads=(value,), writes=(y,),
    )
    self.mad(value, y, LReg.ONE, into=error, negate_product=True)
    self.mad(error, error, error, into=correction)
    self.mad(correction, error, error, into=correction)
    self._swap_min_max(LReg.ONE, correction)
    self.mad(correction, y, y, into=result)

    for scratch in (y, error, correction): self.free(scratch)
    return result

  def rsqrt_positive(self, value, *, into=None):
    self._read_index(value)
    result = value if into is None else into
    if result is not value: self._write_index(result)
    magic = self._config_bits(0x5f1110a0, "rsqrt_magic")
    c1 = self._config_constant(2.2825186, "rsqrt_c1")
    c2 = self._config_constant(2.2533049, "rsqrt_c2")
    y, xy, correction, polynomial, half_y = (
      self.vec("rsqrt_y"),
      self.vec("rsqrt_xy"),
      self.vec("rsqrt_correction"),
      self.vec("rsqrt_polynomial"),
      self.vec("rsqrt_half_y"),
    )

    self.move(value, into=y)
    self._emit(
      TT.TTSFPSHFT(0xfff, LReg.ZERO, self._write_index(y), 1),
      reads=(y,), writes=(y,),
    )
    self._emit(
      TT.TTSFPIADD(0, self._read_index(magic), self._write_index(y), 6),
      reads=(magic, y), writes=(y,),
    )
    self.mul(value, y, into=xy)
    self.mad(y, xy, LReg.ZERO, into=correction, negate_product=True)
    self.add(c2, correction, into=polynomial)
    self.mad(correction, polynomial, c1, into=polynomial)
    self.mul(y, polynomial, into=y)
    self.mul(value, y, into=xy)
    self.mad(y, xy, LReg.ZERO, into=correction, negate_product=True)
    self.add(LReg.ONE, correction, into=correction)
    self.mul_scalar(y, 0.5, into=half_y)
    self.mad(correction, half_y, y, into=result)

    for scratch in (y, xy, correction, polynomial, half_y): self.free(scratch)
    return result

  def finish(self):
    if self._program is not None: return self._program
    self._open()
    setup = []

    # SFPCONFIG copies L0 into a programmable constant.  Do these first:
    # ordinary constants may themselves live in L0 and must be restored last.
    for index in sorted(self.config_constants):
      bits = self.persistent[index]
      setup.extend((
        TT.TTSFPLOADI(LReg.L0, _LoadImmediate.LOWER, bits & 0xffff),
        TT.TTSFPLOADI(LReg.L0, _LoadImmediate.UPPER, bits >> 16),
        TT.TTSFPCONFIG(0, index, 0),
      ))
    for index in sorted(x for x in self.persistent if x < 8):
      bits = self.persistent[index]
      setup.extend((
        TT.TTSFPLOADI(index, _LoadImmediate.LOWER, bits & 0xffff),
        TT.TTSFPLOADI(index, _LoadImmediate.UPPER, bits >> 16),
      ))

    self.finished = True
    self._program = SfpuProgram(tuple(setup), tuple(self.words))
    return self._program

class Sfpu:
  def __init__(self, kernel, dst: Dst, seed_kernel=None):
    if kernel.role != "trisc1": raise RuntimeError("SFPU must run on trisc1")
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 1)
    self.seed_k = seed_kernel
    self.prepared = {}

  def program(self): return SfpuProgramBuilder()

  def seed(self, value):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
      raise ValueError("SFPU PRNG seed must be a 32-bit unsigned integer")
    if self.seed_k is None:
      raise RuntimeError("SFPU seed requires a BRISC coordinator")
    self.seed_k.write(TensixMMIO.PRNG_SEED_SEED_VAL, value)
    for _ in self.seed_k.range(600):
      pass
    sem_post(self.seed_k, Sem.FPU_SFPU)
    sem_wait(
      self.k, Sem.FPU_SFPU, SemWait.STALL_ON_ZERO,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    sem_get(self.k, Sem.FPU_SFPU)
    return self

  def publish(self):
    stall(self.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
    sem_post(self.k, Sem.MATH_PACK)
    return self

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
    if not isinstance(program, SfpuProgram):
      raise TypeError("expected SfpuProgram; call builder.finish() first")
    if program not in self.prepared:
      body = (*program.words, _VECTOR_STEP)
      try:
        start = self._mop.state.replay.allocate(
          len(body), lower=0, upper=REPLAY_SIZE,
        )
      except (ValueError, MemoryError):
        start = None
      if start is not None:
        self._mop.load(Replay(start, body), initialize=True)
      self.prepared[program] = (start, body)
    return self.prepared[program]

  def _inline_faces(self, body, faces):
    for _ in range(faces):
      for _ in range(8):
        for word in body: self._issue(word)
      self._issue(_FACE_STEP)
      self._issue(_FACE_STEP)

  def _configure_replay_mop(self, start, length):
    replay = TT.TTREPLAY(start, length, 0, 0)
    self._mop.configure(LoopTemplate(
      outer=1, inner=8, loop=replay,
      end0=_FACE_STEP, end1=_FACE_STEP,
      last=replay, outer_last=replay,
    ))

  def _replay_faces(self, faces):
    # Keep each MOP expansion to one face.  A four-face MOP containing
    # replay instructions can saturate the FIFO between the MOP and Replay
    # Expanders on Blackhole.
    for _ in range(faces): self._mop.run()

  def _run_faces(self, start, body, faces):
    if start is None: self._inline_faces(body, faces)
    else: self._replay_faces(faces)

  def _map(self, program, *, tile, faces, column, lane_config):
    start, body = self._prepare(program)
    sem_wait(
      self.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    self._configure_dst(tile, lane_config)
    stall(self.k, Stall.SFPU, Wait.MATH)
    for word in program.setup_words: self._issue(word)
    if start is not None: self._configure_replay_mop(start, len(body))

    if column:
      # Column mode visits faces 0 and 2.  A one-face MOP leaves us at face 1,
      # so skip it explicitly before running the second face.
      self._run_faces(start, body, 1)
      self._issue(_FACE_STEP)
      self._issue(_FACE_STEP)
      self._run_faces(start, body, 1)
    else: self._run_faces(start, body, faces)

    self._issue(_RESET_DST)
    stall(self.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
    return self

  def map(self, program, *, tile, region="tile", lane_config=LaneConfig()):
    if region not in ("tile", "row", "column"):
      raise ValueError("SFPU region must be tile, row, or column")
    return self._map(program, tile=tile, faces=4 if region == "tile" else 2,
                     column=region == "column", lane_config=lane_config)
