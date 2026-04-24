import struct
from dataclasses import dataclass, field

from .memory import (
  Memory, Router, L1_SIZE, MAILBOX_BASE, SUBORDINATE_SYNC,
  LAUNCH_MSG_RD_PTR, LAUNCH_MSG_RING, GO_MESSAGES, GO_MESSAGE_INDEX,
  ZEROS_BASE, BRISC_FW_BASE, NCRISC_FW_BASE, TRISC0_FW_BASE,
  TRISC1_FW_BASE, TRISC2_FW_BASE, KERNEL_CONFIG_BASE,
  BANK_TO_NOC_SCRATCH, DATA_BUFFER_SPACE_BASE,
  LDM_SCRATCH, LDM_BASE, LDM_END_8K,
  LDM_SLOW_BRISC, LDM_SLOW_STRIDE,
  WALL_CLOCK_L, WALL_CLOCK_H,
  NOC0_BASE, NOC1_BASE, NOC_SIZE,
  MOP_CFG_BASE, MOP_CFG_END,
  INSTRN_BUF_T0, INSTRN_BUF_END,
  TENSIX_CFG_BASE, TENSIX_CFG_END,
  TDMA_BASE, TDMA_END,
  NUM_CBS, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE,
  STREAM_BASE, STREAM_END, L1_BASE, L1_END,
  BOOT_JAL, SOFT_RESET_0,
  TRISC0_RESET_PC, TRISC1_RESET_PC, TRISC2_RESET_PC, TRISC_RESET_PC_OVR,
  NCRISC_RESET_PC, NCRISC_RESET_PC_OVR,
  _SEM_WIN_LO, _SEM_WIN_HI,
)
from .core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from .noc import NOC, StreamRegisters, noc_key
from .tensix import TensixCoprocessor, Semaphores, TDMA

M32 = 0xFFFFFFFF
L1_ALIGN = 16
PCIE_NOC_XY = (19, 24)
LOGICAL_TO_VIRTUAL_SCRATCH = BANK_TO_NOC_SCRATCH + 2048

def _align_up(value: int, align: int) -> int:
  return (value + align - 1) & ~(align - 1)

def _pack_rta(writer_args, reader_args, compute_args, num_sems, sem_off):
  pack = lambda xs: b"".join(int(x & M32).to_bytes(4, "little") for x in xs)
  rta = pack(writer_args) + pack(reader_args) + pack(compute_args)
  if num_sems > 0:
    if sem_off > len(rta):
      rta = rta.ljust(sem_off, b"\0")
    rta += b"\0" * (num_sems * 16)
  return rta

def _build_cb_blob(cbs):
  """cbs: list of (index, page_size, num_tiles). Returns (mask, blob)."""
  if not cbs:
    return 0, b""
  mask = 0
  for idx, _ps, _nt in cbs:
    mask |= 1 << idx
  end = mask.bit_length()
  arr = bytearray(end * 16)
  addr = DATA_BUFFER_SPACE_BASE
  for idx, page_size, num_tiles in cbs:
    size = page_size * num_tiles
    struct.pack_into("<IIII", arr, idx * 16, addr, size, num_tiles, page_size)
    addr += size
  return mask, bytes(arr)

# -- P100A layout constants ---------------------------------------------------

P100A_TENSIX_X = (*range(1, 8), *range(10, 15))  # 12 columns
P100A_Y_RANGE  = range(2, 12)                      # 10 rows

# DRAM bank geometry (P100A: 8 banks, up to 1 harvested; each bank exposes 3 ports).
DRAM_BANK_COUNT = 8
DRAM_PORTS = 3
DRAM_BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]

# Runtime dispatch protocol constants (RUN_MSG_INIT for boot is below).
RUN_MSG_GO   = 0x80
RUN_MSG_DONE = 0x00

def _compute_bank_xy(harvested_banks: list[int]) -> dict[int, tuple[int, int]]:
  if len(harvested_banks) == 0:
    bank_xy = {}
    for b in range(DRAM_BANK_COUNT):
      x = 17 if b < 4 else 18
      bank_xy[b] = (x, 12 + (b % 4) * DRAM_PORTS)
    return bank_xy
  elif len(harvested_banks) == 1:
    h = harvested_banks[0]
    half = 4
    mirror = h + half - 1 if h < half else h - half
    if h < half:
      right = list(range(half - 1))
      left = [b for b in range(half - 1, DRAM_BANK_COUNT - 1) if b != mirror] + [mirror]
    else:
      left = [b for b in range(half) if b != mirror] + [mirror]
      right = list(range(half, DRAM_BANK_COUNT - 1))
    bank_xy = {}
    for i, b in enumerate(right):
      bank_xy[b] = (18, 12 + i * DRAM_PORTS)
    for i, b in enumerate(left):
      bank_xy[b] = (17, 12 + i * DRAM_PORTS)
    return bank_xy
  raise ValueError(f"unsupported harvested DRAM bank count: {len(harvested_banks)}")

@dataclass
class Dram:
  num_banks: int
  banks: list  # list[Memory], one per active bank
  bank_xy: dict  # bank_id → (x, y0)

  def read_interleaved(self, base_addr: int, tile_idx: int,
            tile_bytes: int) -> bytes:
    bank = tile_idx % self.num_banks
    slot = tile_idx // self.num_banks
    addr = base_addr + slot * tile_bytes
    mem = self.banks[bank]
    return bytes(mem.read8(addr + i) for i in range(tile_bytes))

  def write_interleaved(self, base_addr: int, tile_idx: int,
             tile_bytes: int, data: bytes):
    bank = tile_idx % self.num_banks
    slot = tile_idx // self.num_banks
    addr = base_addr + slot * tile_bytes
    mem = self.banks[bank]
    for i, b in enumerate(data):
      mem.write8(addr + i, b)

@dataclass
class Tile:
  x: int
  y: int
  l1: Memory
  brisc: BRISC
  ncrisc: NCRISC
  trisc0: TRISC0
  trisc1: TRISC1
  trisc2: TRISC2
  noc0: NOC
  noc1: NOC
  semaphores: Semaphores = field(repr=False)
  mmio: Memory = field(repr=False)                   # catch-all MMIO (wall clock, reset PCs, TDMA, PIC, …)
  stream_regs: StreamRegisters = field(default=None, repr=False)   # 0xFFB40000..0xFFB7FFFF — CB sync, dispatch msg, sync ptr
  tensix: TensixCoprocessor = field(default=None, repr=False)

  @property
  def cores(self) -> list:
    return [self.brisc, self.ncrisc, self.trisc0, self.trisc1, self.trisc2]


# Slow-path LDM slot layout: (base address, core attribute name).
# A `Memory` (the peer core's LDM) is registered at each slot base with
# offset=base so the handler sees a zero-based address — no adapter needed.
_SLOW_LDM_SLOTS = [
  (LDM_SLOW_BRISC + 0 * LDM_SLOW_STRIDE, 'brisc'),
  (LDM_SLOW_BRISC + 1 * LDM_SLOW_STRIDE, 'ncrisc'),
  (LDM_SLOW_BRISC + 2 * LDM_SLOW_STRIDE, 'trisc0'),
  (LDM_SLOW_BRISC + 3 * LDM_SLOW_STRIDE, 'trisc1'),
  (LDM_SLOW_BRISC + 4 * LDM_SLOW_STRIDE, 'trisc2'),
]

# SOFT_RESET_0 values
SOFT_RESET_ALL = 0x47800   # all 5 RISCs held in reset

# SOFT_RESET_0 bit → (core_attr, pc_reg, ovr_reg, ovr_bit).  BRISC (bit 11)
# always boots from PC 0 (the JAL stub at L1[0]); the other cores honour
# their RESET_PC when the matching override bit is set.
_RESET_MAP = [
  (11, 'brisc',  None,            None,                None),
  (12, 'trisc0', TRISC0_RESET_PC, TRISC_RESET_PC_OVR,  0),
  (13, 'trisc1', TRISC1_RESET_PC, TRISC_RESET_PC_OVR,  1),
  (14, 'trisc2', TRISC2_RESET_PC, TRISC_RESET_PC_OVR,  2),
  (18, 'ncrisc', NCRISC_RESET_PC, NCRISC_RESET_PC_OVR, 0),
]

def _make_reset_hook(tile):
  def hook(old, new):
    mmio = tile.mmio
    for bit, attr, pc_reg, ovr_reg, ovr_bit in _RESET_MAP:
      was_held = bool(old & (1 << bit))
      now_held = bool(new & (1 << bit))
      core = getattr(tile, attr)
      core.in_reset = now_held
      if was_held and not now_held:
        if   pc_reg is None:                          core.pc = 0
        elif mmio.read32(ovr_reg) & (1 << ovr_bit):   core.pc = mmio.read32(pc_reg)
        else:                                         core.pc = 0
  return hook

class Device:
  def __init__(self, harvested_banks: list[int] | None = None,
               tensix_x=None, tensix_y=None):
    if harvested_banks is None:
      harvested_banks = [0]
    self.harvested_banks = harvested_banks
    self._clock = 0

    # Compute layout — optionally restrict the worker grid (tests use a
    # 1-tile device to cut construction time; Tensix regfile alloc is ~60ms/tile).
    if tensix_x is None: tensix_x = P100A_TENSIX_X
    if tensix_y is None: tensix_y = P100A_Y_RANGE
    self.worker_xy = [(x, y) for x in tensix_x for y in tensix_y]
    num_dram_banks = DRAM_BANK_COUNT - len(harvested_banks)

    # Two independent NOC networks — routing tables keyed by (y<<6)|x.
    # Each NOC NIU on a tile reads/writes through its own network.
    self.networks: list[dict[int, Memory]] = [{}, {}]
    self.pcie = Memory()
    for net in self.networks:
      net[noc_key(*PCIE_NOC_XY)] = self.pcie

    # Create tiles.  Each tile's _create_tile registers its L1 on both
    # networks at its (x, y) coordinate and installs all router handlers.
    self.tiles: dict[tuple[int, int], Tile] = {}
    for x, y in self.worker_xy:
      self.tiles[(x, y)] = self._create_tile(x, y)
    self._populate_logical_to_virtual_tables()

    # DRAM banks — each bank exposes DRAM_PORTS NOC coordinates; register
    # the bank Memory on both networks at every port coordinate.
    self.bank_xy = _compute_bank_xy(harvested_banks)
    dram_banks: list[Memory] = []
    for bank_id in sorted(self.bank_xy.keys()):
      bank_mem = Memory()
      dram_banks.append(bank_mem)
      x, y0 = self.bank_xy[bank_id]
      for port in range(DRAM_PORTS):
        key = noc_key(x, y0 + port)
        self.networks[0][key] = bank_mem
        self.networks[1][key] = bank_mem
    self.dram_banks = dram_banks
    self.dram = Dram(num_banks=num_dram_banks, banks=dram_banks,
            bank_xy=self.bank_xy)

  @property
  def cores(self) -> list[tuple[int, int]]:
    return list(self.worker_xy)

  def _create_tile(self, x: int, y: int) -> Tile:
    l1 = Memory()
    brisc  = BRISC(l1=l1)
    ncrisc = NCRISC(l1=l1)
    trisc0 = TRISC0(l1=l1)
    trisc1 = TRISC1(l1=l1)
    trisc2 = TRISC2(l1=l1)
    cores = [brisc, ncrisc, trisc0, trisc1, trisc2]

    # Tile-level state.
    mmio = Memory()                          # fallback MMIO (wall clock, reset PCs, SOFT_RESET_0, PIC, …)
    mmio.write32(SOFT_RESET_0, SOFT_RESET_ALL)  # power-on: all 5 RISCs held in reset
    stream_regs = StreamRegisters()          # 0xFFB40000..0xFFB7FFFF — CB tiles_acked/received, sync ptr, dispatch msg
    tensix = TensixCoprocessor(l1=l1)        # Mover reads/writes l1 directly
    tensix.stream_regs = stream_regs
    tdma = TDMA(mover=tensix.mover,          # 0xFFB11000 — XMOV MMIO front-end
                packer=tensix.packer)        # + FIFO_PACKED_TILE_* sideband

    # Per-tile NIU controllers — one per physical NOC network.
    noc0 = NOC(0, l1, self.networks[0], x, y)
    noc1 = NOC(1, l1, self.networks[1], x, y)
    noc0.pre_populate()
    noc1.pre_populate()

    # Register this tile on both networks at its (x, y) coordinate.  Remote
    # cores reach L1 and stream regs through one tile-level bus, so NOC atomic
    # increments targeting a CB's tiles_received / tiles_acked land in the
    # same StreamRegisters the local RISCs poll on.
    tile_bus = Router()
    tile_bus.register(L1_BASE, L1_END, l1)
    tile_bus.register(STREAM_BASE, STREAM_END, stream_regs)
    key = noc_key(x, y)
    self.networks[0][key] = tile_bus
    self.networks[1][key] = tile_bus

    tile = Tile(
      x=x, y=y, l1=l1,
      brisc=brisc, ncrisc=ncrisc, trisc0=trisc0, trisc1=trisc1, trisc2=trisc2,
      noc0=noc0, noc1=noc1,
      semaphores=tensix.semaphores, mmio=mmio, stream_regs=stream_regs, tensix=tensix,
    )

    reset_hook = _make_reset_hook(tile)
    for core in cores:
      bus = core.mem
      bus.default = mmio                     # unmapped addrs → tile catch-all
      bus.register(NOC0_BASE,       NOC0_BASE + NOC_SIZE - 1, noc0)
      bus.register(NOC1_BASE,       NOC1_BASE + NOC_SIZE - 1, noc1)
      bus.register(STREAM_BASE,     STREAM_END, stream_regs)
      bus.register(TENSIX_CFG_BASE, TENSIX_CFG_END, tensix.cfg, offset=TENSIX_CFG_BASE)
      bus.register(TDMA_BASE,       TDMA_END, tdma, offset=TDMA_BASE)
      bus.register(_SEM_WIN_LO,     _SEM_WIN_HI, tensix.semaphores)
      # Cross-core LDM: this core can reach every peer's slow-path slot.
      # TRISC upper 4 KiB padding naturally falls through to mmio.
      for base, attr in _SLOW_LDM_SLOTS:
        peer = getattr(tile, attr)
        bus.register(base, base + peer.LDM_SIZE - 1, peer.ldm, offset=base)
      # Per-role Tensix handlers (None if this core can't access the region).
      ih = tensix.instrn_handler_for(core.ROLE)
      if ih: bus.register(INSTRN_BUF_T0, INSTRN_BUF_END, ih)
      mh = tensix.mop_handler_for(core.ROLE)
      if mh: bus.register(MOP_CFG_BASE, MOP_CFG_END, mh)
      bus.on_write32(SOFT_RESET_0, reset_hook)

    return tile

  def _populate_logical_to_virtual_tables(self):
    cols = list(dict.fromkeys(x for x, _ in self.worker_xy))
    col_table = cols + [0] * max(0, 20 - len(cols))
    row_table = list(P100A_Y_RANGE) + [0, 0]
    data = bytes((col_table[:20] + row_table[:12]))
    for tile in self.tiles.values():
      tile.l1.load(LOGICAL_TO_VIRTUAL_SCRATCH, data)

  def configure_cbs(self, cbs: dict[int, tuple[int, int]]):
    for idx in cbs:
      if not 0 <= idx < NUM_CBS:
        raise ValueError(f"CB index {idx} out of range 0..{NUM_CBS - 1}")

    # Allocate data buffers sequentially
    available = L1_SIZE - DATA_BUFFER_SPACE_BASE
    buf_addr = DATA_BUFFER_SPACE_BASE
    configs = {}  # idx -> (addr, total_size, num_pages, page_size)

    for idx in sorted(cbs):
      num_pages, page_size = cbs[idx]
      total_size = num_pages * page_size
      if buf_addr + total_size > L1_SIZE:
        used = buf_addr - DATA_BUFFER_SPACE_BASE
        raise ValueError(
          f"CB {idx}: needs {total_size} bytes but only "
          f"{available - used} of {available} bytes remain")
      configs[idx] = (buf_addr, total_size, num_pages, page_size)
      buf_addr += total_size

    # Write config to every tile's L1
    for tile in self.tiles.values():
      for idx, (addr, size, num_pages, page_size) in configs.items():
        base = CB_L1_CONFIG_BASE + idx * CB_CONFIG_BYTES
        tile.l1.write32(base + 0, addr)
        tile.l1.write32(base + 4, size)
        tile.l1.write32(base + 8, num_pages)
        tile.l1.write32(base + 12, page_size)

    return configs

  def _step_loop(self, tiles: list[Tile], done_check, max_steps: int):
    for _ in range(max_steps):
      self._clock += 1
      for tile in tiles:
        tile.mmio.write32(WALL_CLOCK_L, self._clock & M32)
        tile.mmio.write32(WALL_CLOCK_H, (self._clock >> 32) & M32)
        # Step all RISC-V cores
        for core in tile.cores:
          if not core.in_reset:
            core.step()
        # Step Tensix coprocessor (process one instruction per thread)
        tile.tensix.step()
      if done_check():
        return
    raise TimeoutError(
      f"emulated device did not complete within {max_steps} steps "
      f"(clock={self._clock})"
    )

  def run(self, *,
      brisc: bytes = b'',
      ncrisc: bytes = b'',
      trisc: tuple[bytes, bytes, bytes] = (b'', b'', b''),
      writer_args=None,        # list[list[int]] or callable(i)->list[int]
      reader_args=None,
      compute_args=None,
      cbs: list[tuple[int, int, int]] | None = None,   # (index, page_size, num_tiles)
      num_semaphores: int = 0,
      max_steps: int = 50_000_000):
    """Dispatch a program to all tiles.

    Mirrors the tt-metal slow-dispatch payload layout (see
    blackhole-py/dispatch.py:build_payload) so real firmware/kernels see
    the same launch_msg fields and KERNEL_CONFIG_BASE blob.

    Layout at KERNEL_CONFIG_BASE:
      +0                RTAs: writer | reader | compute
      +sem_off          semaphores (num_sems × 16)
      +local_cb_off     CB config blob (16 B × mask.bit_length())
      +remote_cb_off    remote CBs (unused)
      +kernel_off       BRISC | NCRISC | TRISC0 | TRISC1 | TRISC2 text
    """
    tiles = list(self.tiles.values())
    num_cores = len(tiles)

    def _resolve(args):
      if args is None: return [[] for _ in range(num_cores)]
      if callable(args): return [args(i) for i in range(num_cores)]
      return args

    writer_rta = _resolve(writer_args)
    reader_rta = _resolve(reader_args)
    compute_rta = _resolve(compute_args)

    max_w = max((len(a) for a in writer_rta), default=0) * 4
    max_r = max((len(a) for a in reader_rta), default=0) * 4
    max_c = max((len(a) for a in compute_rta), default=0) * 4
    sem_off = _align_up(max_w + max_r + max_c, L1_ALIGN)

    cb_mask, cb_blob = _build_cb_blob(cbs)
    local_cb_off = _align_up(sem_off + num_semaphores * 16, L1_ALIGN)
    remote_cb_off = local_cb_off + len(cb_blob)

    kernels = [brisc, ncrisc, trisc[0], trisc[1], trisc[2]]
    text_offsets = [0] * 5
    enables = 0
    off = _align_up(remote_cb_off, L1_ALIGN)
    for idx, code in enumerate(kernels):
      if code:
        text_offsets[idx] = off
        off = _align_up(off + len(code), L1_ALIGN)
        enables |= 1 << idx

    rta_offs = [0, max_w, max_w + max_r, max_w + max_r, max_w + max_r]

    for i, tile in enumerate(tiles):
      l1 = tile.l1

      rta_blob = _pack_rta(writer_rta[i], reader_rta[i], compute_rta[i],
                           num_semaphores, sem_off)
      if rta_blob:
        l1.load(KERNEL_CONFIG_BASE, rta_blob)
      if cb_blob:
        l1.load(KERNEL_CONFIG_BASE + local_cb_off, cb_blob)
      for idx, code in enumerate(kernels):
        if code:
          l1.load(KERNEL_CONFIG_BASE + text_offsets[idx], code)

      rd_ptr = l1.read32(LAUNCH_MSG_RD_PTR)
      lm = LAUNCH_MSG_RING + (rd_ptr % 8) * 96
      l1.load(lm, b'\0' * 96)

      for j in range(3):
        l1.write32(lm + 0 + j * 4, KERNEL_CONFIG_BASE)     # kernel_config_base[0..2]
        l1.write16(lm + 12 + j * 2, sem_off)                # sem_offset[0..2]
      l1.write16(lm + 18, local_cb_off)
      l1.write16(lm + 20, remote_cb_off)
      for j in range(5):
        l1.write16(lm + 22 + j * 4 + 0, rta_offs[j])
        l1.write16(lm + 22 + j * 4 + 2, local_cb_off)       # crta shares CB region base
      l1.write8(lm + 42, 1)                                 # mode = DISPATCH_MODE_HOST
      for j in range(5):
        l1.write32(lm + 44 + j * 4, text_offsets[j])
      l1.write32(lm + 64, cb_mask)
      l1.write8(lm + 68, 0)                                 # brisc_noc_id
      l1.write8(lm + 69, 0)                                 # brisc_noc_mode
      l1.write8(lm + 70, 32)                                # min_remote_cb_start_index
      l1.write32(lm + 76, enables)

      l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)

    def all_done():
      return all(t.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE for t in tiles)

    self._step_loop(tiles, all_done, max_steps)

  def read_l1(self, x: int, y: int, addr: int, length: int) -> bytes:
    l1 = self.tiles[(x, y)].l1
    return bytes(l1.read8(addr + i) for i in range(length))

  def write_l1(self, x: int, y: int, addr: int, data: bytes):
    l1 = self.tiles[(x, y)].l1
    l1.load(addr, data)

  def read_dram(self, bank: int, addr: int, length: int) -> bytes:
    mem = self.dram_banks[bank]
    return bytes(mem.read8(addr + i) for i in range(length))

  def write_dram(self, bank: int, addr: int, data: bytes):
    mem = self.dram_banks[bank]
    for i, b in enumerate(data):
      mem.write8(addr + i, b)

SOFT_RESET_BRISC_ONLY = 0x47000   # BRISC released, TRISCs + NCRISC held
RUN_MSG_INIT          = 0x40      # BRISC in firmware init; host set before reset release

def _build_bank_noc_table(harvested_banks: list[int], worker_cores: list) -> bytes:
  num_dram_banks = DRAM_BANK_COUNT - len(harvested_banks)
  num_l1_banks = len(worker_cores)
  NOCS = 2
  bank_xy = _compute_bank_xy(harvested_banks)

  def noc_xy(x, y):
    return ((y << 6) | x) & 0xFFFF

  dram = []
  for noc in range(NOCS):
    for b in range(num_dram_banks):
      x, y0 = bank_xy[b]
      dram.append(noc_xy(x, y0 + DRAM_BANK_PORT[b][noc]))

  cols = sorted({x for x, _ in worker_cores})
  l1 = []
  for _ in range(NOCS):
    for i in range(num_l1_banks):
      l1.append(noc_xy(cols[i % len(cols)], 2 + (i // len(cols)) % 10))

  return struct.pack(
    f"<{len(dram)}H{len(l1)}H{num_dram_banks + num_l1_banks}i",
    *dram, *l1, *([0] * (num_dram_banks + num_l1_banks))
  )

def _make_jal(target: int) -> bytes:
  return ((target & 0xFF000)
          | ((target & 0x800) << 9)
          | ((target & 0x7FE) << 20)
          | 0x6F).to_bytes(4, "little")

def boot(device, firmware: dict, *, max_steps: int = 50_000_000):
  bank_table = _build_bank_noc_table(device.harvested_banks, device.worker_xy)
  go_init = struct.pack("<BBBB", 0, 0, 0, RUN_MSG_INIT)
  jal = _make_jal(BRISC_FW_BASE)

  for tile in device.tiles.values():
    l1 = tile.l1
    mmio = tile.mmio

    # Upload firmware segments to L1.
    # Segments whose paddr falls in LDM range (0xFFB00000-0xFFB01FFF)
    # are redirected to per-core L1 scratch areas.  do_crt1() will
    # later copy them from scratch into real LDM.
    for name, fw in firmware.items():
      for addr, data in fw['segments']:
        if LDM_BASE <= addr <= LDM_END_8K:
          scratch = LDM_SCRATCH[name] + (addr - LDM_BASE)
          l1.load(scratch, data)
        else:
          l1.load(addr, data)

    # Write boot data.
    l1.load(BOOT_JAL, jal)                        # JAL x0, BRISC_FW_BASE
    l1.load(GO_MESSAGES, go_init)                  # go_msg.signal = RUN_MSG_INIT
    l1.load(BANK_TO_NOC_SCRATCH, bank_table)       # DRAM/L1 bank-to-NOC tables
    l1.load(ZEROS_BASE, b'\x00' * 512)             # pre-zeroed region

    # Write subordinate reset PCs to MMIO registers.
    # BRISC's device_setup() later enables the override bits so the
    # hardware uses these values when subordinates exit reset.
    mmio.write32(NCRISC_RESET_PC, firmware['ncrisc']['text_base'])
    mmio.write32(TRISC0_RESET_PC, firmware['trisc0']['text_base'])
    mmio.write32(TRISC1_RESET_PC, firmware['trisc1']['text_base'])
    mmio.write32(TRISC2_RESET_PC, firmware['trisc2']['text_base'])

    # Release BRISC only.
    # Routes through BRISC's bus so the reset callback fires:
    # BRISC transitions held→running (PC=0), others stay held.
    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)

  tiles = list(device.tiles.values())

  def all_done():
    return all(t.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE for t in tiles)

  device._step_loop(tiles, all_done, max_steps)
