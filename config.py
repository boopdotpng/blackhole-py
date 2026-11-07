from __future__ import annotations
from dataclasses import dataclass, field, fields
from enum import Enum, IntEnum, auto

class Space(Enum): MMIO = auto(); SFPU = auto(); REPLAY = auto(); SEM = auto()

class Thread(IntEnum): UNPACK = 0; MATH = 1; PACK = 2; READ = 3; WRITE = 4

class DataFormat(IntEnum):
  FLOAT32 = 0; FLOAT16 = 1; BFP8 = 2; BFP4 = 3; TF32 = 4; FLOAT16_B = 5; BFP8_B = 6; BFP4_B = 7
  INT32 = 8; UINT16 = 9; LF8 = 10; BFP2 = 11; INT8 = 14; BFP2_B = 15; UINT32 = 24; FP8_E4M3 = 26; UINT8 = 30

# A field's "at" is (unit, shift, width): a config word, thread config register, MMIO address or slot, and the bits in it.
# With one "at" per index (Regs.INDEX) instead, None marks an index that lacks the field. stride overrides Regs.STRIDE.
def F(*at, stride=None, default=None): return field(default=default, metadata={"at": at, "stride": stride})
def per_context(*at): return F(*at, *at)  # unpacker contexts 4..7 sit where 0..3 do
def K(): return field(metadata={"key": True})  # identifies the instance (which unpacker, thread, slot...), not written

def l1_addr(byte_addr: int) -> int: return (byte_addr >> 4) - 1

class Bank(IntEnum): B0 = 0; B1 = 1; BOTH = 2

CFG_BASE, CFG_BANK_STRIDE, CFG_DUAL_WRITE = 0xFFEF0000, 0x380, 0xFFEF0700
THREAD_CFG_BASE, THREAD_CFG_STRIDE = 0xFFEF0A80, 68 * 4
GLOBAL_CFG_BASE = 180
REGFILE_BASE, REGFILE_STRIDE = 0xFFE00000, 64 * 4
MOP_CFG = 0xFFB80000

def banked(word: int) -> bool: return word < GLOBAL_CFG_BASE
def cfg_address(word: int, bank: Bank | None = Bank.B0) -> int:
  if bank is None or not banked(word): return CFG_BASE + 4 * word
  return CFG_DUAL_WRITE + 4 * word if bank == Bank.BOTH else CFG_BASE + CFG_BANK_STRIDE * bank + 4 * word
def thread_cfg_address(thread: int, reg: int) -> int: return THREAD_CFG_BASE + THREAD_CFG_STRIDE * thread + 4 * reg

NOC_BASE, NOC_END = 0xFFB20000, 0xFFB40000

class Region(Enum):
  CONFIG = auto(); THREAD_CONFIG = auto(); MOP = auto(); NOC = auto(); GPR = auto(); SFPU = auto(); REPLAY = auto(); SEM = auto()

def region(key) -> Region:
  space, _, addr = key
  if space is not Space.MMIO: return Region[space.name]
  if CFG_BASE <= addr < CFG_DUAL_WRITE: return Region.CONFIG
  if THREAD_CFG_BASE <= addr < THREAD_CFG_BASE + 3 * THREAD_CFG_STRIDE: return Region.THREAD_CONFIG
  if MOP_CFG <= addr < MOP_CFG + 9 * 4: return Region.MOP
  if NOC_BASE <= addr < NOC_END: return Region.NOC
  if REGFILE_BASE <= addr < REGFILE_BASE + 3 * REGFILE_STRIDE: return Region.GPR
  raise ValueError(f"{addr:#x} is not a known config location")

def config_bank(addr: int) -> Bank | None:
  bank, word = divmod(addr - CFG_BASE, CFG_BANK_STRIDE)
  return Bank(bank) if banked(word // 4) else None

def full_mask(key) -> int: return {Region.THREAD_CONFIG: 0xFFFF, Region.SEM: 0xFF}.get(region(key), 0xFFFFFFFF)
def partial(key) -> bool: return region(key) is Region.CONFIG

# Ordering is codegen's job: Auto TTSync stays off (ThreadConfig reg 56 = 0), so nothing orders RISC stores against
# Tensix instructions. Rewrite rules find these edges and insert the sync:
#   SW to Config, then a Tensix instruction that reads it     -> STALLWAIT(TRISC_CFG / C10) before the reader
#   Tensix write (WRCFG/RMWCIB/SETC16), then a RISC lw of it   -> pc_sync (store then load) before the lw; stale without it
#   in-stream reconfig of state a unit is still using          -> STALLWAIT draining that unit before the write
#   WRCFG / WRCFG128, then an instruction reading that value   -> one NOP between them (WRCFG takes 2 cycles)
#   SW to MOP config                                           -> mop_sync first; the expander samples it during expansion
#   template-0 MOP                                             -> MOP_CFG(mask >> 16) immediately before, every time
#   REPLAY load                                                -> the replay range must not be executing
#   SETC16 to CFG_STATE_ID (bank switch)                       -> sync before the next access that depends on the bank
# Accesses that hang the core, never emit them:
#   RISC load from MOP config (0xFFB80000); BRISC access past the 3 GPR blocks (>= 0xFFE00300); any NCRISC GPR access.
class Method(Enum):
  SW = auto(); SW_DUAL = auto(); RMWCIB = auto(); WRCFG = auto(); WRCFG128 = auto(); SETC16 = auto(); SETDMAREG = auto()
  SFPCONFIG = auto(); REPLAY = auto(); SEMINIT = auto()

METHODS = {
  Region.CONFIG: (Method.RMWCIB, Method.WRCFG128, Method.SW_DUAL, Method.SW, Method.WRCFG),
  Region.THREAD_CONFIG: (Method.SETC16,),
  Region.MOP: (Method.SW,),
  Region.NOC: (Method.SW,),
  Region.GPR: (Method.SETDMAREG, Method.SW),
  Region.SFPU: (Method.SFPCONFIG,),
  Region.REPLAY: (Method.REPLAY,),
  Region.SEM: (Method.SEMINIT,),
}
TENSIX_WRITES = {Method.RMWCIB, Method.WRCFG, Method.WRCFG128, Method.SETC16, Method.SETDMAREG, Method.SFPCONFIG, Method.REPLAY,
                 Method.SEMINIT}
RISC_READABLE = {Region.CONFIG, Region.THREAD_CONFIG, Region.NOC, Region.GPR}

def touched_bytes(mask: int) -> int: return sum(1 for b in range(4) if mask >> 8 * b & 0xFF)

def methods(key, mask: int | None = None, *, issuing_bank: Bank | None = None, both_banks: bool = False) -> tuple[Method, ...]:
  if (r := region(key)) is not Region.CONFIG: return METHODS[r]
  bank, full = config_bank(key[2]), mask is None or mask == 0xFFFFFFFF
  def legal(m):
    if m is Method.SW_DUAL: return both_banks and full and bank is not None
    if m in (Method.WRCFG, Method.WRCFG128) and not full: return False
    return m not in TENSIX_WRITES or bank is None or bank == issuing_bank  # Tensix writes land in the issuing bank
  # SW_DUAL first, and a full-word write prefers anything over RMWCIB's read-modify-write
  rank = lambda m: 0 if m is Method.SW_DUAL else 2 if full and m is Method.RMWCIB else 1
  return tuple(sorted(filter(legal, METHODS[r]), key=rank))

def choose(key, mask: int | None = None, *, prefer: tuple[Method, ...] = (), **context) -> Method:
  legal = [m for m in methods(key, mask, **context) if m is not Method.WRCFG128]
  for m in (*prefer, *legal):
    if m in legal: return m
  raise ValueError(f"no write method for {key} with {context}")

# A word can hold fields of several threads. plan() treats it like any other register: a partial write replaces whole
# bytes on the issuing core. Keeping threads from updating the same word at the same time is codegen's job.
def plan(writes: dict, *, issuing_bank: Bank | None = Bank.B0, prefer: tuple[Method, ...] = ()) -> list[tuple[Method, tuple]]:
  steps, done = [], set()
  def step(method, keys):
    steps.append((method, keys))
    done.update(keys)
  for key, (value, mask) in writes.items():
    if key in done: continue
    if region(key) is Region.CONFIG:
      space, thread, addr = key
      # the same full word for both banks: one dual-bank store
      twin = (space, thread, addr + CFG_BANK_STRIDE)
      if config_bank(addr) == Bank.B0 and mask == 0xFFFFFFFF and writes.get(twin) == (value, mask) \
         and Method.SW_DUAL in methods(key, mask, issuing_bank=issuing_bank, both_banks=True):
        step(Method.SW_DUAL, (key, twin)); continue
      # all four words of an aligned 16 bytes fully written: one WRCFG128
      group = tuple((space, thread, (addr & ~0xF) + 4 * i) for i in range(4))
      if all(writes.get(g, (0, 0))[1] == 0xFFFFFFFF for g in group) and not done & set(group) \
         and Method.WRCFG128 in methods(key, mask, issuing_bank=issuing_bank):
        step(Method.WRCFG128, group); continue
    step(choose(key, mask, prefer=prefer, issuing_bank=issuing_bank), (key,))
  return steps

class Regs:
  SPACE: Space
  INDEX: str | None = None
  COUNT: int = 1
  STRIDE: int | tuple[int, ...] = 0

  def base(self) -> int: return 0
  def index(self) -> int: return getattr(self, self.INDEX) if self.INDEX else 0
  def key(self) -> tuple: return (type(self),) + tuple(getattr(self, f.name) for f in fields(self) if f.metadata.get("key"))
  def derived(self): return ()
  def locations(self, unit: int) -> tuple: return ((self.SPACE, None, unit),)

  def where(self, name: str) -> tuple[int, int, int]:
    f = next(f for f in fields(self) if f.name == name)
    return self.place(name, f.metadata["at"], f.metadata["stride"])

  def place(self, name: str, at: tuple, stride=None) -> tuple[int, int, int]:
    if not 0 <= (i := self.index()) < self.COUNT: raise ValueError(f"{self.key()} does not exist")
    if not isinstance(at[0], int): at = at[i]
    if at is None: raise ValueError(f"{type(self).__name__}.{name} does not exist for {self.key()}")
    unit, shift, width = at
    stride = self.STRIDE if stride is None else stride
    return unit + self.base() + (stride[i] if isinstance(stride, tuple) else stride * i), shift, width

  def values(self):
    """(name, (unit, shift, width), value) for every field that is set, then the derived ones."""
    for f in fields(self):
      if "at" in f.metadata and (v := getattr(self, f.name)) is not None:
        yield f.name, self.place(f.name, f.metadata["at"], f.metadata["stride"]), v
    for name, at, v in self.derived(): yield name, self.place(name, at), v

  def writes(self) -> dict[tuple[Space, int | None, int], tuple[int, int]]:
    """{(space, thread, unit): (value, mask)}: every set field packed into the words it lives in."""
    out: dict = {}
    for name, (unit, shift, width), v in self.values():
      v = int(v) & 0xF if isinstance(v, DataFormat) else int(v)
      if not 0 <= v < 1 << width: raise ValueError(f"{type(self).__name__}.{name}={v} does not fit in {width} bits")
      for k in self.locations(unit):
        value, mask = out.get(k, (0, 0))
        out[k] = (value | v << shift, mask | ((1 << width) - 1) << shift)
    return out

  def merge(self, other: Regs) -> Regs:
    assert self.key() == other.key(), f"{self.key()} vs {other.key()}"
    new = {}
    for f in fields(self):
      a, b = getattr(self, f.name), getattr(other, f.name)
      if a is not None and b is not None and a != b and "at" in f.metadata: raise ValueError(f"{type(self).__name__}.{f.name}: {a} vs {b}")
      new[f.name] = a if a is not None else b
    return type(self)(**new)

def as_written(writes: dict) -> dict:
  return {k: (v, m if partial(k) else full_mask(k)) for k, (v, m) in writes.items()}

@dataclass(frozen=True)
class ConfigRegs(Regs):
  SPACE = Space.MMIO
  bank: Bank = field(default=Bank.B0, kw_only=True, metadata={"key": True})
  def locations(self, word):
    if not banked(word): return ((Space.MMIO, None, cfg_address(word, None)),)
    banks = (Bank.B0, Bank.B1) if self.bank == Bank.BOTH else (self.bank,)
    return tuple((Space.MMIO, None, cfg_address(word, b)) for b in banks)

class ThreadConfigRegs(Regs):
  SPACE = Space.MMIO
  def locations(self, reg): return ((Space.MMIO, None, thread_cfg_address(self.thread, reg)),)

class Mop(Regs):
  SPACE = Space.MMIO
  def locations(self, addr): return ((Space.MMIO, self.thread, addr),)

class Noc(Regs): SPACE = Space.MMIO

class Gprs(Regs):
  SPACE = Space.MMIO
  def locations(self, reg): return ((Space.MMIO, None, REGFILE_BASE + REGFILE_STRIDE * self.thread + 4 * reg),)

class Sfpu(Regs): SPACE = Space.SFPU

class Replay(Regs):
  SPACE = Space.REPLAY
  def locations(self, slot): return ((Space.REPLAY, self.thread, slot),)

class Sem(Regs): SPACE = Space.SEM

@dataclass(frozen=True)
class UnpackerCfg(ConfigRegs):
  INDEX, COUNT, STRIDE = "unpacker", 2, 48
  unpacker: int = K()
  src_format: DataFormat | None = F(64, 0, 4)
  uncompressed: bool | None = F(64, 4, 1)
  blobs_per_xy_plane: int | None = F(64, 8, 4)
  in_x_dim: int | None = F(64, 16, 16)
  in_y_dim: int | None = F(65, 0, 16)
  in_z_dim: int | None = F(65, 16, 16)
  in_w_dim: int | None = F(66, 0, 16)
  blobs_y_start_lo: int | None = F(66, 16, 16)
  blobs_y_start_hi: int | None = F(67, 0, 16)
  digest_type: int | None = F(67, 16, 8)
  digest_size: int | None = F(67, 24, 8)
  dst_format: DataFormat | None = F(72, 0, 4)
  throttle_mode: int | None = F(72, 4, 2)
  context_count: int | None = F(72, 6, 2)
  transpose_xy: bool | None = F(72, 8, 1)
  tilize: bool | None = F(72, 9, 1)
  src_reg_set_update: bool | None = F(72, 10, 1)
  unpack_if_sel: bool | None = F(72, 11, 1)
  upsample_rate: int | None = F(72, 12, 2)
  upsample_interleave: bool | None = F(72, 15, 1)
  per_context_formats: bool | None = F(72, 14, 1)
  force_shared_exp: bool | None = F(73, 8, 1)
  context_count_non_log2: int | None = F(73, 9, 3)
  context_count_non_log2_en: bool | None = F(73, 12, 1)
  metadata_x_end: int | None = F(73, 24, 8)
  limit_address: int | None = F(74, 0, 17)
  fifo_size: int | None = F(75, 0, 17)
  tile_offset: int | None = F(98, 19, 5)
  reg10_limit_address: int | None = F(104, 0, 17)
  reg10_fifo_size: int | None = F(105, 0, 17)
  reg10_limit_address_en: bool | None = F(105, 17, 1)
  reg_wr_addr: int | None = F(106, 0, 24)
  metadata_l1_addr: int | None = F(108, 0, 32)
  metadata_limit_addr: int | None = F(109, 0, 32)
  metadata_fifo_size: int | None = F(110, 0, 32)
  metadata_z_cntr_rst_unpacr_count: int | None = F(111, 0, 8)
  metadata_cntxt_switch_unpacr_count: int | None = F(111, 8, 8)
  fp8_e4m3: bool | None = F(71, 22, 1)
  in_x_stride: int | None = F(44, 0, 16, stride=2)
  in_y_stride: int | None = F(44, 16, 16, stride=2)
  in_z_stride: int | None = F(45, 0, 16, stride=2)
  in_w_stride: int | None = F(45, 16, 16, stride=2)
  out_x_stride: int | None = F(56, 0, 16, stride=2)
  out_y_stride: int | None = F(56, 16, 16, stride=2)
  out_z_stride: int | None = F(57, 0, 16, stride=2)
  out_w_stride: int | None = F(57, 16, 16, stride=2)
  in_counter_base: int | None = F(48, 0, 18, stride=12)
  out_counter_base: int | None = F(49, 0, 18, stride=12)
  add_dest_addr_counter: bool | None = F(50, 8, 1, stride=12)
  forced_shared_exp: int | None = F(50, 0, 8, stride=12)
  nop_clear_value: int | None = F(53, 0, 32, stride=10)
  blobs_y_start_cntx01: int | None = F((51, 0, 32), None)
  blobs_y_start_cntx23: int | None = F((52, 0, 32), None)

@dataclass(frozen=True)
class UnpackerContext(ConfigRegs):
  COUNT = 8
  unpacker: int = K()
  context: int = K()
  l1_base: int | None = F(76, 0, 32, stride=1)
  offset_address: int | None = per_context((92, 0, 16), (93, 0, 16), (94, 0, 16), (95, 0, 16))
  dest_address: int | None = per_context((84, 0, 16), (84, 16, 16), (85, 0, 16), (85, 16, 16))
  tile_x_dim: int | None = per_context((86, 0, 16), (86, 16, 16), (87, 0, 16), (87, 16, 16))
  shift_amount: int | None = per_context((72, 16, 4), (72, 20, 4), (72, 24, 4), (72, 28, 4))
  disable_zero_compress: bool | None = F((73, 0, 1), (73, 1, 1), (73, 2, 1), (73, 3, 1), (73, 16, 1), (73, 17, 1), (73, 18, 1), (73, 19, 1))
  to_dest: bool | None = F((73, 4, 1), (73, 5, 1), (73, 6, 1), (73, 7, 1), (73, 20, 1), (73, 21, 1), (73, 22, 1), (73, 23, 1))
  src_format: DataFormat | None = F((92, 16, 4), (93, 16, 4), (94, 16, 4), (95, 16, 4), (92, 24, 4), (93, 24, 4), (94, 24, 4), (95, 24, 4))
  dst_format: DataFormat | None = F((92, 20, 4), (93, 20, 4), (94, 20, 4), (95, 20, 4), (92, 28, 4), (93, 28, 4), (94, 28, 4), (95, 28, 4))
  def base(self): return 48 * self.unpacker
  def index(self): return self.context if self.unpacker == 0 or self.context < 2 else -1  # unpacker 1 has contexts 0, 1

@dataclass(frozen=True)
class PackerContext(ConfigRegs):
  INDEX, COUNT, STRIDE = "context", 4, (0, 28, 48, 76)
  context: int = K()
  src_format: DataFormat | None = F(70, 8, 4)
  dst_format: DataFormat | None = F(70, 4, 4)
  fp8_e4m3: bool | None = F((71, 23, 1), None, (71, 23, 1), None)
  l1_dest: int | None = F(69, 0, 32)
  row_start_section_size: int | None = F(68, 0, 16)
  exp_section_size: int | None = F(68, 16, 16)
  disable_zero_compress: bool | None = F(70, 0, 1)
  disable_zero_flags: bool | None = F(70, 2, 1)
  throttle_mode_override: bool | None = F((70, 3, 1), None, (70, 3, 1), None)
  add_l1_dest_offset: bool | None = F(70, 1, 1)
  disable_shared_exp_assembler: bool | None = F(70, 12, 1)
  auto_set_last_pacr_intf_sel: bool | None = F(70, 13, 1)
  enable_out_fifo: bool | None = F(70, 14, 1)
  sub_tile_header_size: bool | None = F(70, 15, 1)
  add_tile_header_size: bool | None = F((70, 22, 1), (70, 17, 1), (70, 22, 1), (70, 17, 1))
  source_interface: int | None = F(70, 16, 1)
  start_intf_pos: int | None = F((70, 17, 4), None, (70, 17, 4), None)
  all_disable_zero_compress_override: bool | None = F((70, 21, 1), None, (70, 21, 1), None)
  dis_y_pos_start_offset: bool | None = F((70, 23, 1), (70, 18, 1), (70, 23, 1), (70, 18, 1))
  l1_source_addr: int | None = F(70, 24, 8)
  downsample_mask: int | None = F(71, 0, 16)
  downsample_rate: int | None = F(71, 16, 3)
  l1_accumulate: bool | None = F(71, 19, 1)
  exp_threshold_enable: bool | None = F(71, 20, 1)
  exp_threshold: int | None = F(71, 24, 8)
  packs_per_xy_plane: int | None = F(28, 0, 8, stride=1)
  reads_per_xy_plane: int | None = F(28, 8, 8, stride=1)
  xys_per_tile: int | None = F(28, 16, 7, stride=1)
  yz_transposed: bool | None = F(28, 23, 1, stride=1)
  auto_context_inc_xys: int | None = F(28, 24, 8, stride=1)
  dest_row_offset: int | None = F(180, 0, 12, stride=1)
  dest_z_offset: int | None = F(180, 12, 6, stride=1)
  concat_mask: int | None = F(32, 0, 16, stride=1)

@dataclass(frozen=True)
class PackCommonCfg(ConfigRegs):
  read_32b_dest: bool | None = F(18, 0, 1)
  read_unsigned: bool | None = F(18, 1, 1)
  read_int8: bool | None = F(18, 2, 1)
  round_10b_mantissa: bool | None = F(18, 3, 1)
  in_x_stride: int | None = F(12, 0, 16)
  in_y_stride: int | None = F(12, 16, 16)
  in_z_stride: int | None = F(13, 0, 16)
  in_w_stride: int | None = F(13, 16, 16)
  out_x_stride: int | None = F(14, 0, 16)
  out_y_stride: int | None = F(14, 16, 16)
  out_z_stride: int | None = F(15, 0, 16)
  out_w_stride: int | None = F(15, 16, 16)
  in_counter_base: int | None = F(16, 0, 18)
  out_counter_base: int | None = F(17, 0, 18)
  edge_mask_0: int | None = F(24, 0, 16)
  edge_mask_1: int | None = F(25, 0, 16)
  edge_mask_2: int | None = F(26, 0, 16)
  edge_mask_3: int | None = F(27, 0, 16)
  edge_mode: bool | None = F(24, 16, 1)
  row_set_select_0: int | None = F(24, 17, 2)
  row_set_select_1: int | None = F(24, 19, 2)
  row_set_select_2: int | None = F(24, 21, 2)
  row_set_select_3: int | None = F(24, 23, 2)
  row_set_mapping_0: int | None = F(20, 0, 32)
  row_set_mapping_1: int | None = F(21, 0, 32)
  row_set_mapping_2: int | None = F(22, 0, 32)
  row_set_mapping_3: int | None = F(23, 0, 32)
  face_set_select: int | None = F(19, 0, 8)
  face_set_select_enable: bool | None = F(19, 8, 1)
  face_set_mapping_0: int | None = F(36, 0, 32)
  face_set_mapping_1: int | None = F(37, 0, 32)
  face_set_mapping_2: int | None = F(38, 0, 32)
  face_set_mapping_3: int | None = F(39, 0, 32)
  disable_fast_tile_end_drain: bool | None = F(40, 0, 1)

@dataclass(frozen=True)
class PackerSection(ConfigRegs):
  INDEX, COUNT, STRIDE = "sec", 2, 48
  sec: int = K()
  pack_0_2_limit_address: int | None = F(100, 0, 17)
  pack_0_2_fifo_size: int | None = F(101, 0, 17)
  pack_1_3_limit_address: int | None = F(102, 0, 17)
  pack_1_3_fifo_size: int | None = F(103, 0, 17)
  reg_wr_addr: int | None = F(107, 0, 24)

@dataclass(frozen=True)
class AluCfg(ConfigRegs):
  srca_format: DataFormat | None = F(1, 17, 4)
  srcb_format: DataFormat | None = F(1, 21, 4)
  dest_format: DataFormat | None = F(1, 25, 4)
  srca_unsigned: bool | None = F(1, 15, 1)
  srcb_unsigned: bool | None = F(1, 16, 1)
  srca_format_override: DataFormat | None = F(0, 0, 4)
  srca_override: bool | None = F(0, 4, 1)
  srcb_format_override: DataFormat | None = F(0, 5, 4)
  srcb_override: bool | None = F(0, 9, 1)
  dest_format_override: DataFormat | None = F(0, 10, 4)
  dest_override: bool | None = F(0, 14, 1)
  fp32_dest: bool | None = F(1, 29, 1)
  sfpu_fp32: bool | None = F(1, 30, 1)
  int8_math: bool | None = F(1, 31, 1)
  fpu_stochastic_round: bool | None = F(1, 0, 1)
  gasket_stochastic_round: bool | None = F(1, 1, 1)
  packer_stochastic_round: bool | None = F(1, 2, 1)
  round_gs_lf: bool | None = F(1, 13, 1)
  round_bfp8_hf: bool | None = F(1, 14, 1)
  disable_src_zero_flags: bool | None = F(2, 0, 1)
  disable_dest_zero_flags: bool | None = F(2, 1, 1)
  relu_mode: int | None = F(2, 2, 4)
  relu_threshold: int | None = F(2, 6, 16)
  state_reset: bool | None = F(4, 0, 1)
  dest_offset_enable: bool | None = F(5, 0, 1)
  dest_regw_base: int | None = F(6, 0, 16)
  dest_sp_base: int | None = F(7, 0, 16)
  int_descale_enable: bool | None = F(8, 0, 1)
  int_descale_mode: int | None = F(8, 1, 1)

@dataclass(frozen=True)
class IntDescale(ConfigRegs):
  INDEX, COUNT, STRIDE = "n", 16, 1
  n: int = K()
  value: int | None = F(187, 0, 32)

@dataclass(frozen=True)
class DestAccessCfg(ConfigRegs):
  swizzle_32b: bool | None = F(220, 0, 1)
  remap_addrs: bool | None = F(220, 1, 1)
  disable_write_bypass: bool | None = F(220, 2, 1)
  zeroacc_absolute_tile: bool | None = F(220, 3, 1)

@dataclass(frozen=True)
class SrcAccessCfg(ConfigRegs):
  gate_srca_pipe: bool | None = F(184, 0, 1)
  gate_srcb_pipe: bool | None = F(184, 1, 1)
  srca_as_one_bank: bool | None = F(221, 0, 1)
  srcb_as_one_bank: bool | None = F(221, 1, 1)
  disable_contig_srca_dvalid_phase: bool | None = F(221, 2, 1)
  disable_contig_srcb_dvalid_phase: bool | None = F(221, 3, 1)

@dataclass(frozen=True)
class RiscDestAccess(ConfigRegs):
  INDEX, COUNT = "trisc", 3
  trisc: int = K()
  no_swizzle: bool | None = F((3, 14, 1), (3, 19, 1), (3, 24, 1))
  unsigned_int: bool | None = F((3, 15, 1), (3, 20, 1), (3, 25, 1))
  fmt: int | None = F((3, 16, 3), (3, 21, 3), (3, 26, 3))

@dataclass(frozen=True)
class RiscCfg(ConfigRegs):
  disable_bp_brisc: bool | None = F(2, 22, 1)
  disable_bp_trisc: int | None = F(2, 23, 3)
  disable_bp_ncrisc: bool | None = F(2, 26, 1)
  disable_bmp_clear_brisc: bool | None = F(2, 27, 1)
  disable_bmp_clear_trisc: int | None = F(2, 28, 3)
  disable_bmp_clear_ncrisc: bool | None = F(2, 31, 1)
  ecc_scrubber_enable: bool | None = F(3, 0, 1)
  ecc_scrub_on_error: bool | None = F(3, 1, 1)
  ecc_scrub_on_error_immediately: bool | None = F(3, 2, 1)
  ecc_scrubber_delay: int | None = F(3, 3, 11)
  icache_invalidate: int | None = F(185, 0, 5)
  trisc0_end_pc: int | None = F(203, 0, 32)
  trisc1_end_pc: int | None = F(204, 0, 32)
  trisc2_end_pc: int | None = F(205, 0, 32)
  brisc_end_pc: int | None = F(206, 0, 32)
  ncrisc_end_pc: int | None = F(207, 0, 32)
  prefetch_trisc: int | None = F(208, 0, 3)
  prefetch_brisc: bool | None = F(208, 3, 1)
  prefetch_ncrisc: bool | None = F(208, 4, 1)
  prefetch_max_req_count: int | None = F(208, 5, 8)
  scratch_0: int | None = F(209, 0, 32)
  scratch_1: int | None = F(210, 0, 32)
  scratch_2: int | None = F(211, 0, 32)

@dataclass(frozen=True)
class GlobalCfg(ConfigRegs):
  prng_seed: int | None = F(186, 0, 32)
  sfpu_scoreboard_disable: bool | None = F(222, 0, 1)

@dataclass(frozen=True)
class L1TagSearch(ConfigRegs):
  enable: bool | None = F(212, 0, 1)
  start_addr: int | None = F(212, 1, 17)
  end_addr: int | None = F(213, 0, 17)
  tag_value_lo: int | None = F(214, 0, 32)
  tag_value_hi: int | None = F(215, 0, 32)
  tag_width: int | None = F(216, 0, 2)
  valid_bit_section_start_addr: int | None = F(216, 2, 17)
  valid_bit_section_end_addr: int | None = F(217, 0, 17)
  data_valid_bit_section_start_addr: int | None = F(218, 0, 17)
  data_valid_check: bool | None = F(218, 17, 1)
  data_valid_offset: int | None = F(219, 0, 24)
  tag_invalidate: bool | None = F(219, 24, 1)
  tag_invalidate_all: bool | None = F(219, 25, 1)
  tag_alloc: bool | None = F(219, 26, 1)

@dataclass(frozen=True)
class ThreadCfg(ThreadConfigRegs):
  thread: Thread = K()
  state_id: int | None = F(0, 0, 1)
  math_dest_offset: int | None = F(1, 0, 12)
  disable_implied_srca_fmt: bool | None = F(2, 0, 1)
  disable_implied_srcb_fmt: bool | None = F(3, 0, 1)
  sfpu_dest_fmt_enable: bool | None = F(4, 0, 1)
  sfpu_dest_fmt: int | None = F(4, 1, 4)
  srca_bank: int | None = F(5, 0, 2)
  srca_bank_override: bool | None = F(5, 2, 1)
  srcb_bank: int | None = F(6, 0, 2)
  keep_srca_dvalid: bool | None = F(7, 0, 1)
  keep_srcb_dvalid: bool | None = F(7, 1, 1)
  scbd_bank_mask_32b: bool | None = F(8, 0, 1)
  pack_scbd_bank_mask_32b: bool | None = F(9, 0, 1)
  unpack_scbd_bank_mask_32b: bool | None = F(10, 0, 1)
  fidelity_base: int | None = F(11, 0, 2)
  sfpu_stack_incr: int | None = F(36, 0, 10)
  # Context counter (UNPACR use_context_counter): one per unpacker per thread, wraps at context_count_non_log2 + 1 when
  # _en is set, else at 1 << context_count. Survives kernel launches and soft resets; tt-smi -r clears it.
  # unpackN_context_reset only lands while the unpacker is active, and only from the owning thread (bit 4 / bit 12):
  #   SETC16(41, 0); UNPACR_NOP(u); SETC16(41, reset bit); STALLWAIT; UNPACR_NOP(u); STALLWAIT; SETC16(41, 0)
  unpack0_context: int | None = F(41, 0, 4)
  unpack0_context_reset: bool | None = F(41, 4, 1)
  unpack0_context_inc: bool | None = F(41, 5, 1)
  unpack1_context: int | None = F(41, 8, 4)
  unpack1_context_reset: bool | None = F(41, 12, 1)
  unpack1_context_inc: bool | None = F(41, 13, 1)
  unpack_context_cnt_reset_metadata: bool | None = F(41, 14, 1)
  unpack_context_cnt_reset_metadata_zstart: bool | None = F(41, 15, 1)
  overlay_msg_clear_stream_0: int | None = F(42, 0, 6)
  overlay_msg_clear_msg_num_0: int | None = F(42, 8, 3)
  overlay_msg_clear_stream_1: int | None = F(43, 0, 6)
  overlay_msg_clear_msg_num_1: int | None = F(43, 8, 3)
  perf_cnt_0_start: bool | None = F(44, 0, 1)
  perf_cnt_0_stop: bool | None = F(44, 1, 1)
  perf_cnt_1_start: bool | None = F(44, 2, 1)
  perf_cnt_1_stop: bool | None = F(44, 3, 1)
  perf_cnt_2_start: bool | None = F(44, 4, 1)
  perf_cnt_2_stop: bool | None = F(44, 5, 1)
  perf_cnt_3_start: bool | None = F(44, 6, 1)
  perf_cnt_3_stop: bool | None = F(44, 7, 1)
  enable_acc_stats: bool | None = F(45, 0, 1)
  fpu_bias_sel: bool | None = F(46, 0, 1)
  fp16a_force: bool | None = F(55, 0, 1)
  trisc_sync_track_global_cfg: bool | None = F(56, 0, 1)
  trisc_sync_subdivided_cfg_for_unpacr: bool | None = F(56, 1, 1)
  trisc_sync_track_gpr: bool | None = F(56, 2, 1)
  trisc_sync_track_tdma_regs: bool | None = F(56, 3, 1)
  trisc_sync_track_tensix_instructions: bool | None = F(56, 4, 1)
  streamwait_phase_hi: int | None = F(57, 0, 10)
  streamwait_num_msgs_hi: int | None = F(58, 0, 7)
  stream_id_sync_0: int | None = F(59, 0, 6)
  stream_id_sync_1: int | None = F(60, 0, 6)
  stream_id_sync_2: int | None = F(61, 0, 6)
  stream_id_sync_3: int | None = F(62, 0, 6)
  stream_id_trisc_0: int | None = F(63, 0, 6)
  stream_id_trisc_1: int | None = F(64, 0, 6)
  stream_id_trisc_2: int | None = F(65, 0, 6)
  stream_id_trisc_3: int | None = F(66, 0, 6)
  raw_busy_status: bool | None = F(67, 0, 1)

@dataclass(frozen=True)
class AddrMod(ThreadConfigRegs):
  INDEX, COUNT, STRIDE = "slot", 8, 1
  thread: Thread = K()
  slot: int = K()
  srca_incr: int = F(12, 0, 6, default=0)
  srca_carry: bool = F(12, 6, 1, default=False)
  srca_clear: bool = F(12, 7, 1, default=False)
  srcb_incr: int = F(12, 8, 6, default=0)
  srcb_carry: bool = F(12, 14, 1, default=False)
  srcb_clear: bool = F(12, 15, 1, default=False)
  ab2_srca_incr: bool | None = F(20, 0, 1)
  ab2_srcb_incr: bool | None = F(20, 1, 1)
  dest_incr: int = F(28, 0, 10, default=0)
  dest_carry: bool = F(28, 10, 1, default=False)
  dest_clear: bool = F(28, 11, 1, default=False)
  dest_counter_to_carry: bool = F(28, 12, 1, default=False)
  fidelity_incr: int = F(28, 13, 2, default=0)
  fidelity_clear: bool = F(28, 15, 1, default=False)
  bias_incr: int = F(47, 0, 4, default=0)
  bias_clear: bool = F(47, 4, 1, default=False)

@dataclass(frozen=True)
class PackAddrMod(ThreadConfigRegs):
  INDEX, COUNT, STRIDE = "slot", 4, 1
  slot: int = K()
  thread: Thread = field(default=Thread.PACK, metadata={"key": True})
  y_src_incr: int = F(37, 0, 4, default=0)
  y_src_carry: bool = F(37, 4, 1, default=False)
  y_src_clear: bool = F(37, 5, 1, default=False)
  y_dst_incr: int = F(37, 6, 4, default=0)
  y_dst_carry: bool = F(37, 10, 1, default=False)
  y_dst_clear: bool = F(37, 11, 1, default=False)
  z_src_incr: int = F(37, 12, 1, default=0)
  z_src_clear: bool = F(37, 13, 1, default=False)
  z_dst_incr: int = F(37, 14, 1, default=0)
  z_dst_clear: bool = F(37, 15, 1, default=False)

@dataclass(frozen=True)
class MopLoop(Mop):
  thread: Thread = K()
  outer_count: int | None = F(MOP_CFG + 0x00, 0, 32)
  inner_count: int | None = F(MOP_CFG + 0x04, 0, 32)
  start: int | None = F(MOP_CFG + 0x08, 0, 32)
  end_0: int | None = F(MOP_CFG + 0x0C, 0, 32)
  end_1: int | None = F(MOP_CFG + 0x10, 0, 32)
  body: int | None = F(MOP_CFG + 0x14, 0, 32)
  body_alt: int | None = F(MOP_CFG + 0x18, 0, 32)
  last_body: int | None = F(MOP_CFG + 0x1C, 0, 32)
  outer_last_body: int | None = F(MOP_CFG + 0x20, 0, 32)

@dataclass(frozen=True)
class MopMask(Mop):
  thread: Thread = K()
  has_b: bool | None = F(MOP_CFG + 0x04, 0, 1)
  has_a123: bool | None = F(MOP_CFG + 0x04, 1, 1)
  b: int | None = F(MOP_CFG + 0x08, 0, 32)
  a0: int | None = F(MOP_CFG + 0x0C, 0, 32)
  a1: int | None = F(MOP_CFG + 0x10, 0, 32)
  a2: int | None = F(MOP_CFG + 0x14, 0, 32)
  a3: int | None = F(MOP_CFG + 0x18, 0, 32)
  skip_a0: int | None = F(MOP_CFG + 0x1C, 0, 32)
  skip_b: int | None = F(MOP_CFG + 0x20, 0, 32)

@dataclass(frozen=True)
class ReplaySlot(Replay):
  INDEX, COUNT, STRIDE = "slot", 32, 1
  thread: Thread = K()
  slot: int = K()
  word: int | None = F(0, 0, 32)

def replay(thread: Thread, start: int, words) -> list[ReplaySlot]:
  return [ReplaySlot(thread=thread, slot=start + i, word=w) for i, w in enumerate(words)]

@dataclass(frozen=True)
class SfpuLaneCfg(Sfpu):
  enable_fp16_infinity: bool | None = F(15, 0, 1)
  disable_backdoor_load: bool | None = F(15, 1, 1)
  enable_dest_index: bool | None = F(15, 2, 1)
  capture_default_dest_index: bool | None = F(15, 3, 1)
  block_dest_write: bool | None = F(15, 4, 1)
  block_dest_read: bool | None = F(15, 5, 1)
  dest_read_column_exchange: bool | None = F(15, 6, 1)
  dest_write_column_exchange: bool | None = F(15, 7, 1)
  exchange_srcb_srcc: bool | None = F(15, 8, 1)
  block_dest_move: int | None = F(15, 9, 2)
  row_mask: int | None = F(15, 12, 4)

@dataclass(frozen=True)
class SfpuConstant(Sfpu):
  COUNT, STRIDE = 15, 1
  lreg: int = K()
  value: int | None = F(0, 0, 32)
  def index(self): return self.lreg if 11 <= self.lreg <= 14 else -1  # LREG 11..14 are the programmable constants

@dataclass(frozen=True)
class SfpuMacro(Sfpu):
  INDEX, COUNT, STRIDE = "slot", 9, 1
  slot: int = K()
  value: int | None = F(0, 0, 32)

@dataclass(frozen=True)
class SemInit(Sem):
  INDEX, COUNT, STRIDE = "sem", 8, 1
  sem: int = K()
  init: int | None = F(0, 0, 4)
  max: int | None = F(0, 4, 4)

@dataclass(frozen=True)
class Gpr(Gprs):
  INDEX, COUNT, STRIDE = "reg", 64, 1
  thread: Thread = K()
  reg: int = K()
  value: int | None = F(0, 0, 32)

class NocCmd(IntEnum): READ = 0; ATOMIC = 1; WRITE = 2

@dataclass(frozen=True)
class NocCmdBuf(Noc):
  noc: int = K()
  buf: int = K()
  targ_addr: int | None = F(0x00, 0, 32)
  targ_addr_mid: int | None = F(0x04, 0, 32)
  targ_coord: int | None = F(0x08, 0, 32)
  ret_addr: int | None = F(0x0C, 0, 32)
  ret_addr_mid: int | None = F(0x10, 0, 32)
  ret_coord: int | None = F(0x14, 0, 32)
  stream_id: int = F(0x18, 0, 6, default=0)
  deliver_to_overlay: bool = F(0x18, 6, 1, default=False)
  first_packet: bool = F(0x18, 7, 1, default=False)
  last_packet: bool = F(0x18, 8, 1, default=False)
  header_store: bool = F(0x18, 9, 1, default=False)
  transaction_id: int | None = F(0x18, 10, 4)
  cmd: NocCmd | None = F(0x1C, 0, 2)
  posted: bool | None = None
  byte_enable: bool = F(0x1C, 2, 1, default=False)
  inline: bool = F(0x1C, 3, 1, default=False)
  multicast: bool = F(0x1C, 5, 1, default=False)
  linked: bool = F(0x1C, 6, 1, default=False)
  static_vc: bool = F(0x1C, 7, 1, default=True)
  path_reserve: bool = F(0x1C, 8, 1, default=False)
  drop_read_ack: bool = F(0x1C, 9, 1, default=False)
  vc: int | None = F(0x1C, 13, 3)
  multicast_along_y: bool = F(0x1C, 16, 1, default=False)
  multicast_include_sender: bool = F(0x1C, 17, 1, default=False)
  priority: int = F(0x1C, 27, 4, default=0)
  l1_accumulate: bool = F(0x1C, 31, 1, default=False)
  length: int | None = F(0x20, 0, 32)
  length_hi: int = F(0x24, 0, 32, default=0)
  at_data: int | None = F(0x28, 0, 32)
  multicast_exclude: int = F(0x2C, 0, 32, default=0)

  def base(self): return NOC_BASE + (self.noc << 16) + (self.buf << 11)
  def derived(self):
    if self.cmd is None: return
    yield "resp_marked", (0x1C, 4, 1), not (self.posted and self.cmd is NocCmd.WRITE)
    if self.vc is None: yield "vc", (0x1C, 13, 3), 4 if self.multicast else 1
