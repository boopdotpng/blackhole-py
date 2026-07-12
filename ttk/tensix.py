"""Blackhole Tensix constants and typed configuration state.

The state model keeps TRISC configuration independent from firmware policy.
Addresses are byte addresses; ``addr32`` is the operand used by TTWRCFG and
TTRMWCIB instructions.
"""
from dataclasses import dataclass, field
from enum import IntEnum
from isa import Tensix as TensixISA


CFG_BASE = 0xFFEF0000


class Cfg(IntEnum):
  ALU_FORMAT_SPEC_REG = CFG_BASE + 0x00
  ALU = CFG_BASE + 0x04
  ALU_ACC_CTRL = CFG_BASE + 0x08
  ECC_SCRUBBER = CFG_BASE + 0x0C
  PCK0_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0x30
  PCK0_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0x34
  PCK_DEST_RD_CTRL = CFG_BASE + 0x48
  UNP0_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0xB0
  UNP0_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0xB4
  UNP1_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0xB8
  UNP1_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0xBC
  UNP0 = CFG_BASE + 0xC8
  UNP0_ADDR_CTRL_XY_REG_1 = CFG_BASE + 0xE0
  UNP0_ADDR_CTRL_ZW_REG_1 = CFG_BASE + 0xE4
  UNP1_ADDR_CTRL_XY_REG_1 = CFG_BASE + 0xE8
  UNP1_ADDR_CTRL_ZW_REG_1 = CFG_BASE + 0xEC
  THCON_SEC0_REG0_TileDescriptor = CFG_BASE + 0x100
  THCON_SEC0_REG0_TileDescriptor_1 = CFG_BASE + 0x104
  THCON_SEC0_REG1 = CFG_BASE + 0x110
  THCON_SEC0_REG1_1 = CFG_BASE + 0x114
  THCON_SEC0_REG2 = CFG_BASE + 0x120
  THCON_SEC0_REG2_1 = CFG_BASE + 0x124
  THCON_SEC0_REG3_Base_address = CFG_BASE + 0x130
  THCON_SEC0_REG3_Base_cntx1_address = CFG_BASE + 0x134
  THCON_SEC0_REG5_Dest_cntx = CFG_BASE + 0x150
  THCON_SEC0_REG5_Dest_cntx1 = CFG_BASE + 0x154
  THCON_SEC0_REG5_Tile_x_dim_cntx = CFG_BASE + 0x158
  THCON_SEC0_REG5_Tile_x_dim_cntx1 = CFG_BASE + 0x15C
  THCON_SEC0_REG7_Offset_address = CFG_BASE + 0x170
  THCON_SEC0_REG7_Offset_cntx1_address = CFG_BASE + 0x174
  PACK_COUNTERS_SEC0 = CFG_BASE + 0x70
  PCK_EDGE = CFG_BASE + 0x60
  TILE_ROW_SET_MAPPING_0 = CFG_BASE + 0x50
  DEST_TARGET_REG_CFG_PACK_SEC0 = CFG_BASE + 0x2D0
  DEST_TARGET_REG_CFG_PACK_SEC1 = CFG_BASE + 0x2D4
  DEST_TARGET_REG_CFG_PACK_SEC2 = CFG_BASE + 0x2D8
  DEST_TARGET_REG_CFG_PACK_SEC3 = CFG_BASE + 0x2DC
  THCON_SEC1_REG0_TileDescriptor = CFG_BASE + 0x1C0
  THCON_SEC1_REG0_TileDescriptor_1 = CFG_BASE + 0x1C4
  THCON_SEC1_REG3_Base_address = CFG_BASE + 0x1F0
  THCON_SEC1_REG3_Base_cntx1_address = CFG_BASE + 0x1F4
  THCON_SEC1_REG2 = CFG_BASE + 0x1E0
  THCON_SEC1_REG2_1 = CFG_BASE + 0x1E4
  THCON_SEC1_REG7_Offset_address = CFG_BASE + 0x230
  THCON_SEC1_REG7_Offset_cntx1_address = CFG_BASE + 0x234

  @property
  def addr32(self):
    return (int(self) - CFG_BASE) >> 2


class ThreadCfg(IntEnum):
  CFG_STATE_ID = 0
  SRCA_SET = 5
  UNPACK_MISC_CFG = 41


class TensixStall(IntEnum):
  UNPACK = 0x008
  SYNC = 0x002
  CFG = 0x080


class TensixWait(IntEnum):
  UNPACK0 = 0x002
  PACK0 = 0x008
  THCON = 0x001
  MATH = 0x010
  SFPU = 0x800


class TensixRegs:
  INSTRN_BUF_BASE = 0xFFE40000
  REGFILE_BASE = 0xFFE00000
  PC_BUF_SYNC = 0xFFE80004
  PC_BUF_MOP_SYNC = 0xFFE80008
  PC_UNPACK_SYNC = 0xFFE80034
  MOP_CFG = 0xFFB80000
  CFG_BASE = CFG_BASE
  PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4
  RISCV_IC_INVALIDATE = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F
  CFG_RESET_WORDS = 256
  ECC_SCRUBBER_ENABLE_MASK = 0x1
  ECC_SCRUBBER_SCRUB_ON_ERROR_MASK = 0x2
  ECC_SCRUBBER_DELAY_MASK = 0x3FF8
  ECC_SCRUBBER_DELAY_SHAMT = 3

class TensixSem:
  FPU_SFPU, MATH_PACK, UNPACK_TO_DEST, UNPACK_OPERAND_SYNC = range(4)
  PACK_DONE, UNPACK_SYNC, UNPACK_MATH_DONE, MATH_DONE = range(4, 8)

  @staticmethod
  def mask(index: int):
    if not 0 <= index < 8:
      raise ValueError(f"Tensix semaphore index out of range: {index}")
    return 1 << index


@dataclass(frozen=True)
class UnpackState:
  """Exact high-level unpack state that a kernel may observe or mutate."""

  src_format: int = 5
  dst_format: int = 5
  fp32_dest: bool = False
  cfg_context: int = 0
  srca_set: int = 0
  tile_descriptor: int = 0x15
  tile_descriptor_1: int = 0x00040001
  sec0_reg2: int = 0x25
  sec1_reg2: int = 0x25

@dataclass
class MopCfg:
  """The nine words consumed by one Tensix MOP engine.

  A MOP is a tiny two-level loop around seven instruction slots: the first two
  words are the outer/inner loop counts and the remaining seven words are
  Tensix instructions.  It is not a second instruction buffer and it does not
  own data; it only repeats the slot program against the current address
  counters and engine state.
  """
  loop_outer: int
  loop_inner: int
  template: list[int | object] = field(default_factory=list)

  @classmethod
  def slots(cls, *, outer: int, inner: int, fill=0, **slots):
    """Build a MOP with readable ``slot0=...`` through ``slot6=...`` args."""
    template = [fill] * 7
    for name, word in slots.items():
      if not name.startswith("slot") or not name[4:].isdigit():
        raise TypeError(f"unknown MOP slot {name!r}")
      index = int(name[4:])
      if not 0 <= index < 7: raise ValueError("MOP slots are numbered 0 through 6")
      template[index] = word
    return cls(outer, inner, template)

  @classmethod
  def pack_tile(cls):
    """The standard four-face pack tile program."""
    return cls.slots(
      outer=4, inner=4, fill=nop_word(),
      slot3=pack_word(), slot5=pack_word(addr_mode=1, last=True),
      slot6=pack_word(addr_mode=2),
    )

  @classmethod
  def unpack_ab(cls, replay_a=(0, 6), replay_b=(6, 6)):
    """Matmul A/B loader: execute two replay windows from MOP slots."""
    return cls.slots(
      outer=0, inner=0,
      slot1=tt_word("TTREPLAY", *replay_a),
      slot5=tt_word("TTREPLAY", *replay_b),
    )

  @classmethod
  def unpack_one(cls, *, block=0, addr_mode=1, valid=True):
    """One ordinary SrcA/SrcB face, useful for simple kernels and reloads."""
    return cls.slots(
      outer=0, inner=0, fill=nop_word(),
      slot0=unpack_word(block=block, addr_mode=addr_mode, valid=valid),
    )

  @classmethod
  def direct_to_dst(cls, *, addr_mode=0x11):
    """Four-face unpack-to-Dst program; callers serialize the faces when needed."""
    return cls.slots(
      outer=4, inner=1, fill=nop_word(),
      slot0=unpack_word(addr_mode=addr_mode, valid=False),
    )

  @classmethod
  def unpack_faces(cls, *, addr_mode=1, valid=True):
    """Repeat one unpack face over the four face positions of a tile."""
    return cls.slots(
      outer=4, inner=1, fill=nop_word(),
      slot0=unpack_word(addr_mode=addr_mode, valid=valid),
    )

  @classmethod
  def row_broadcast(cls):
    """RMSNorm row-broadcast loader."""
    return cls.slots(
      outer=2, inner=2, fill=nop_word(),
      slot1=tt_word("TTSETADCZW", 2, 0, 0, 0, 0, 1),
      slot3=unpack_word(block=1), slot4=unpack_word(block=0),
      slot5=unpack_word(block=0), slot6=unpack_word(block=0),
    )


  def words(self):
    if len(self.template) > 7:
      raise ValueError("unpack MOP templates have at most seven instructions")
    slots = list(self.template) + [nop_word()] * (7 - len(self.template))
    return [self.loop_outer, self.loop_inner, *(_raw_word(word) for word in slots)]


def tt_word(opcode: str, *args, **kwargs) -> int:
  """Build a raw Tensix instruction for reusable MOP descriptions."""
  encoded = getattr(TensixISA(), opcode)(*args, **kwargs)
  return ((encoded >> 2) | (encoded << 30)) & 0xFFFFFFFF


def nop_word() -> int:
  return tt_word("TTNOP")


def unpack_word(*, block=0, addr_mode=1, override_thread=True,
                valid=True, srcb_bcast=False, last=True) -> int:
  return tt_word(
    "TTUNPACR", block, addr_mode, 0, 0, 0,
    int(override_thread), int(valid), int(srcb_bcast), 0, 0, 0, 0, int(last),
  )


def pack_word(*, addr_mode=0, last=False, read_intf=0, flush=False) -> int:
  return tt_word(
    "TTPACR", 0, 0, 0, addr_mode, 0, 0, read_intf,
    0, 0, 0, int(flush), int(last),
  )


def _raw_word(word) -> int:
  if hasattr(word, "raw_word"):
    word = word.raw_word()
  if type(word) is not int or not 0 <= word <= 0xFFFFFFFF:
    raise TypeError("Tensix words must be 32-bit integers or expose raw_word()")
  return word


@dataclass
class MopState:
  """MOP/replay shadow for one TRISC instruction pipe."""
  config: tuple[int, ...] = (0,) * 9
  zmask_hi16: int = 0
  replay: "ReplayBuffer" = field(default_factory=lambda: ReplayBuffer())

  def configure(self, cfg: MopCfg | list[int] | tuple[int, ...]):
    words = cfg.words() if isinstance(cfg, MopCfg) else list(cfg)
    if len(words) != 9:
      raise ValueError("MOP configuration must contain exactly nine words")
    self.config = tuple(_raw_word(word) for word in words)
    return self

  def load_replay(self, words, start=0):
    self.replay.write(start, words)
    return self


@dataclass
class ReplayBuffer:
  """The 32-entry instruction replay RAM for one Tensix pipe.

  Replay RAM stores Tensix words, not MOP configuration.  A MOP slot can issue
  ``TTREPLAY(start, length)`` to execute a window from this RAM.  Loading it is
  itself a runtime TTREPLAY operation, which is why replay and MOP state are
  related but separate.
  """
  words: list[int] = field(default_factory=lambda: [0] * 32)

  def write(self, start: int, words):
    values = [_raw_word(word) for word in words]
    if not 0 <= start < 32 or not values or start + len(values) > 32:
      raise ValueError("replay write must fit within the 32-entry replay buffer")
    self.words[start:start + len(values)] = values
    return self

  def window(self, start: int, length: int) -> tuple[int, ...]:
    if not 0 <= start < 32 or not 1 <= length <= 32 or start + length > 32:
      raise ValueError("replay window must fit within the 32-entry replay buffer")
    return tuple(self.words[start:start + length])

  def __getitem__(self, index):
    return self.words[index]


@dataclass
class TensixState:
  """Software shadow of the state relevant to TTK lowering."""
  contexts: list[dict[int, int]] = field(default_factory=lambda: [{}, {}])
  selected_context: list[int] = field(default_factory=lambda: [0, 0, 0])
  thread_cfg: list[dict[int, int]] = field(default_factory=lambda: [{}, {}, {}])
  mop: list[MopState] = field(default_factory=lambda: [MopState(), MopState(), MopState()])

  def reset(self):
    """Forget the software shadow of the hardware reset state."""
    self.contexts = [{}, {}]
    self.selected_context = [0, 0, 0]
    self.thread_cfg = [{}, {}, {}]
    self.mop = [MopState(), MopState(), MopState()]
    return self

  def set_context(self, pipe: int, context: int):
    if pipe not in (0, 1, 2) or context not in (0, 1):
      raise ValueError("Tensix pipe/context out of range")
    self.selected_context[pipe] = context

  def cfg(self, pipe: int, register: Cfg):
    return self.contexts[self.selected_context[pipe]].get(int(register), 0)

  def set_cfg(self, pipe: int, register: Cfg, value: int):
    shadow = self.contexts[self.selected_context[pipe]]
    value &= 0xFFFFFFFF
    previous = shadow.get(int(register), 0)
    shadow[int(register)] = value
    return previous != value

  def set_thread_cfg(self, pipe: int, register: int, value: int):
    shadow = self.thread_cfg[pipe]
    value &= 0xFFFF
    # Thread configuration is not cleared by BRISC's CFG-MMIO reset.  The
    # first assignment in every specialized kernel must therefore be emitted,
    # including an assignment of zero after a prior kernel selected context 1.
    previous = shadow.get(int(register))
    shadow[int(register)] = value
    return previous != value


class Tensix:
  """Pipe-aware lowering primitives shared by unpack, math, and pack."""

  def __init__(self, kernel, pipe: int, state: TensixState | None = None):
    if pipe not in (0, 1, 2):
      raise ValueError("Tensix pipe must be 0, 1, or 2")
    self.k, self.pipe = kernel, pipe
    self.state = state if state is not None else TensixState()
    self.mop = MopController(self)

  def push(self, word):
    return self.k.push_tensix_word(_raw_word(word))

  @staticmethod
  def init(kernel):
    """Clear the issuing Tensix thread's architectural register file."""
    kernel.zero_words(TensixRegs.REGFILE_BASE, 64)
    return kernel

  @staticmethod
  def reset_hardware(kernel):
    """Emit the Blackhole Tensix cold-state reset sequence.

    This is intentionally a hardware helper rather than BRISC policy:
    firmware decides when to call it, while this method owns the exact CFG,
    SFPU, ECC, and semaphore initialization sequence.
    """
    kernel.zero_words(CFG_BASE, TensixRegs.CFG_RESET_WORDS)
    push = kernel.push_tensix_word
    word = kernel.tensix_word
    push(word("TTZEROACC", 3, 0, 0, 0, 0))
    push(word("TTSFPENCC", 3, 0, 0, 10))
    push(word("TTNOP"))
    push(word("TTSFPLOADI", 0, 0, 0xBF80))
    push(word("TTSFPCONFIG", 0, 11, 0))
    # Equivalent to the three legacy RMW operations after CFG was cleared:
    # enable scrubber, scrub on error, delay=0x100.
    kernel.write32(Cfg.ECC_SCRUBBER, (
      TensixRegs.ECC_SCRUBBER_ENABLE_MASK |
      TensixRegs.ECC_SCRUBBER_SCRUB_ON_ERROR_MASK |
      (0x100 << TensixRegs.ECC_SCRUBBER_DELAY_SHAMT)
    ))
    for sem in (TensixSem.MATH_PACK, TensixSem.UNPACK_TO_DEST, TensixSem.MATH_DONE):
      push(word("TTSEMINIT", 1, 0, 1 << sem))
    return kernel

  def reset(self):
    """Reset the physical Tensix state and clear this engine's shadow."""
    self.state.reset()
    self.reset_hardware(self.k)
    return self

  def write_cfg(self, register: Cfg, value: int):
    value = _raw_word(value)
    if self.state.set_cfg(self.pipe, register, value):
      self.k.write32(int(register), value)
    return self

  def set_thread_cfg(self, register: int | IntEnum, value: int):
    value = int(value)
    if self.state.set_thread_cfg(self.pipe, int(register), value):
      self.push(self.k.tensix_word("TTSETC16", int(register), value))
    return self

  def configure_mop(self, cfg: MopCfg | list[int] | tuple[int, ...]):
    mop = self.state.mop[self.pipe]
    previous = mop.config
    mop.configure(cfg)
    if mop.config == previous:
      return self
    for index, word in enumerate(self.state.mop[self.pipe].config):
      self.k.write32(TensixRegs.MOP_CFG + index * 4, word)
    return self

  def load_replay(self, words, start=0):
    words = tuple(_raw_word(word) for word in words)
    self.state.mop[self.pipe].load_replay(words, start)
    self.push(self.k.tensix_word("TTREPLAY", start, len(words), 1, 1))
    for word in words:
      self.push(word)
    return self

  def run_mop(self, *, loop_count: int = 0, zmask: int = 0, mop_type: int = 1):
    self.push(self.k.tensix_word("TTMOP", mop_type, loop_count, zmask))
    return self

  def replay(self, start: int, length: int):
    self.state.mop[self.pipe].replay.window(start, length)
    self.push(self.k.tensix_word("TTREPLAY", start, length, 0, 0))
    return self


class MopController:
  """Readable engine-local facade for MOP and replay operations."""

  def __init__(self, tensix: Tensix):
    self.tensix = tensix

  @property
  def state(self):
    return self.tensix.state.mop[self.tensix.pipe]

  def configure(self, program: MopCfg | list[int] | tuple[int, ...]):
    self.tensix.configure_mop(program)
    return self

  def load_replay(self, words, *, start=0):
    self.tensix.load_replay(words, start=start)
    return self

  def run(self, *, repeat: int = 1, zmask: int = 0, mop_type: int = 1):
    if repeat < 1: raise ValueError("repeat must be positive")
    return self.tensix.run_mop(loop_count=repeat - 1, zmask=zmask, mop_type=mop_type)
