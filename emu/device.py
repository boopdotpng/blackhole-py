from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .memory import (
  BANK_TO_NOC_SCRATCH, DATA_BUFFER_SPACE_BASE,
  KERNEL_CONFIG_BASE, LAUNCH_MSG_RD_PTR, LAUNCH_MSG_RING, LDM_BASE,
  LDM_END_8K, LDM_SCRATCH, INSTRN_BUF_END, INSTRN_BUF_T0, L1_BASE, L1_END,
  L1_SIZE, LDM_SLOW_BRISC, LDM_SLOW_STRIDE, MOP_CFG_BASE, MOP_CFG_END,
  NOC0_BASE, NOC1_BASE, NOC_SIZE, SOFT_RESET_0, STREAM_BASE, STREAM_END,
  TENSIX_CFG_BASE, TENSIX_CFG_END, TDMA_BASE, TDMA_END, TRISC0_RESET_PC,
  TRISC1_RESET_PC, TRISC2_RESET_PC, TRISC_RESET_PC_OVR, NCRISC_RESET_PC,
  NCRISC_RESET_PC_OVR, WALL_CLOCK_H, WALL_CLOCK_L, GPR_BASE, GPR_END,
  BOOT_JAL, ZEROS_BASE, Memory, Router,
)
from .resources import Scoreboard
from .noc import TimedNOC, StreamRegisters, noc_key
from .rv import BRISC, NCRISC, TRISC0, TRISC1, TRISC2, Core
from .runtime import RuntimeLayout
from .sim import Phase, SimContext, Simulator
from .tensix_core import Tensix


PCIE_NOC_XY = (19, 24)
P100A_TENSIX_X = (*range(1, 8), *range(10, 15))
P100A_Y_RANGE = range(2, 12)
DRAM_BANK_COUNT = 8
DRAM_PORTS = 3
DRAM_BANK_PORT = [[2, 1], [0, 1], [0, 1], [0, 1],
                  [2, 1], [2, 1], [2, 1], [2, 1]]
SOFT_RESET_ALL = 0x47800
SOFT_RESET_BRISC_ONLY = 0x47000
RUN_MSG_INIT = 0x40
RUN_MSG_GO = 0x80
RUN_MSG_DONE = 0x00
L1_ALIGN = 16
FIRMWARE_GO_MESSAGES = 0x3F0
FIRMWARE_GO_MESSAGE_INDEX = 0x420
FIRMWARE_LAUNCH_STRIDE = 112


@dataclass
class Dram:
  num_banks: int
  banks: list[Memory]
  bank_xy: dict[int, tuple[int, int]]

  def read_interleaved(self, base_addr: int, tile_idx: int,
                       tile_bytes: int) -> bytes:
    bank = tile_idx % self.num_banks
    slot = tile_idx // self.num_banks
    addr = base_addr + slot * tile_bytes
    data = self.banks[bank]._data
    return bytes(data.get(addr + i, 0) for i in range(tile_bytes))

  def write_interleaved(self, base_addr: int, tile_idx: int,
                        tile_bytes: int, data: bytes):
    bank = tile_idx % self.num_banks
    slot = tile_idx // self.num_banks
    addr = base_addr + slot * tile_bytes
    self.banks[bank].load(addr, data)


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
  mmio: Memory = field(repr=False)
  stream_regs: StreamRegisters = field(repr=False)
  tensix: Tensix = field(repr=False)
  tdma: Memory = field(repr=False)

  @property
  def cores(self) -> list[Core]:
    return [self.brisc, self.ncrisc, self.trisc0, self.trisc1, self.trisc2]


@dataclass(frozen=True)
class CoreRange:
  x0: int
  y0: int
  x1: int
  y1: int

  def cores(self) -> list[tuple[int, int]]:
    return [
      (x, y)
      for y in range(self.y0, self.y1 + 1)
      for x in range(self.x0, self.x1 + 1)
    ]

  @classmethod
  def row(cls, start_x: int, y: int, count: int) -> "CoreRange":
    if count <= 0:
      raise ValueError("core count must be positive")
    return cls(start_x, y, start_x + count - 1, y)


class _TileClock:
  def __init__(self, tiles: dict[tuple[int, int], Tile]):
    self.tiles = tiles

  def tick(self, ctx: SimContext, phase: Phase) -> None:
    if phase is not Phase.COMMIT:
      return
    for tile in self.tiles.values():
      tile.mmio.write32(WALL_CLOCK_L, ctx.cycle & 0xFFFFFFFF)
      tile.mmio.write32(WALL_CLOCK_H, (ctx.cycle >> 32) & 0xFFFFFFFF)


_RESET_MAP = [
  (11, "brisc", None, None, None),
  (12, "trisc0", TRISC0_RESET_PC, TRISC_RESET_PC_OVR, 0),
  (13, "trisc1", TRISC1_RESET_PC, TRISC_RESET_PC_OVR, 1),
  (14, "trisc2", TRISC2_RESET_PC, TRISC_RESET_PC_OVR, 2),
  (18, "ncrisc", NCRISC_RESET_PC, NCRISC_RESET_PC_OVR, 0),
]


_SLOW_LDM_SLOTS = [
  (LDM_SLOW_BRISC + 0 * LDM_SLOW_STRIDE, "brisc"),
  (LDM_SLOW_BRISC + 1 * LDM_SLOW_STRIDE, "ncrisc"),
  (LDM_SLOW_BRISC + 2 * LDM_SLOW_STRIDE, "trisc0"),
  (LDM_SLOW_BRISC + 3 * LDM_SLOW_STRIDE, "trisc1"),
  (LDM_SLOW_BRISC + 4 * LDM_SLOW_STRIDE, "trisc2"),
]


def _make_reset_hook(tile: Tile):
  def hook(old, new):
    mmio = tile.mmio
    for bit, attr, pc_reg, ovr_reg, ovr_bit in _RESET_MAP:
      was_held = bool(old & (1 << bit))
      now_held = bool(new & (1 << bit))
      core = getattr(tile, attr)
      core.in_reset = now_held
      if was_held and not now_held:
        if pc_reg is None:
          core.pc = 0
        elif mmio.read32(ovr_reg) & (1 << ovr_bit):
          core.pc = mmio.read32(pc_reg)
        else:
          core.pc = 0
  return hook


def _compute_bank_xy(harvested_banks: list[int]) -> dict[int, tuple[int, int]]:
  if not harvested_banks:
    return {b: (17 if b < 4 else 18, 12 + (b % 4) * DRAM_PORTS)
            for b in range(DRAM_BANK_COUNT)}
  if len(harvested_banks) == 1:
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


def _align_up(value: int, align: int = L1_ALIGN) -> int:
  return (value + align - 1) & ~(align - 1)


def _make_jal(target: int) -> bytes:
  return ((target & 0xFF000)
          | ((target & 0x800) << 9)
          | ((target & 0x7FE) << 20)
          | 0x6F).to_bytes(4, "little")


def _addi(rd: int, rs1: int, imm: int) -> int:
  return ((imm & 0xFFF) << 20) | (rs1 << 15) | (rd << 7) | 0x13


def _pack_words(words) -> bytes:
  return b"".join(int(word & 0xFFFFFFFF).to_bytes(4, "little")
                  for word in words)


def _pack_rta(writer_args, reader_args, compute_args, num_sems, sem_off):
  rta = _pack_words(writer_args) + _pack_words(reader_args) + _pack_words(compute_args)
  if num_sems > 0:
    if sem_off > len(rta):
      rta = rta.ljust(sem_off, b"\0")
    rta += b"\0" * (num_sems * 16)
  return rta


def _build_cb_blob(cbs):
  if not cbs:
    return 0, b""
  mask = 0
  for idx, _page_size, _num_pages in cbs:
    mask |= 1 << idx
  arr = bytearray(mask.bit_length() * 16)
  addr = DATA_BUFFER_SPACE_BASE
  for idx, page_size, num_pages in cbs:
    size = page_size * num_pages
    struct.pack_into("<IIII", arr, idx * 16, addr, size, num_pages, page_size)
    addr += size
  return mask, bytes(arr)


def _build_bank_noc_table(harvested_banks: list[int],
                          core_coords: list[tuple[int, int]]) -> bytes:
  num_dram_banks = DRAM_BANK_COUNT - len(harvested_banks)
  num_l1_banks = len(core_coords)
  bank_xy = _compute_bank_xy(harvested_banks)

  def noc_xy(x, y):
    return ((y << 6) | x) & 0xFFFF

  dram = []
  for noc in range(2):
    for b in range(num_dram_banks):
      x, y0 = bank_xy[b]
      dram.append(noc_xy(x, y0 + DRAM_BANK_PORT[b][noc]))

  cols = sorted({x for x, _ in core_coords}) or [0]
  l1 = []
  for _noc in range(2):
    for i in range(num_l1_banks):
      l1.append(noc_xy(cols[i % len(cols)], 2 + (i // len(cols)) % 10))

  return struct.pack(
    f"<{len(dram)}H{len(l1)}H{num_dram_banks + num_l1_banks}i",
    *dram, *l1, *([0] * (num_dram_banks + num_l1_banks)),
  )


def _patch_firmware_sync_addresses(l1: Memory) -> None:
  """Patch checked-in firmware to use this emulator's mailbox sync layout.

  The firmware binaries carry pointer globals in their LDM data images.  Those
  images are version-sensitive, while the emulator has a deliberately small
  fixed mailbox map.  For bring-up, materialize SUBORDINATE_SYNC (0x68)
  directly at the handful of subordinate-sync pointer loads.
  """
  sync = 0x68
  # BRISC subordinate_sync loads.
  for addr, rd in (
      (0x3CAC, 14), (0x3CD4, 15), (0x3D04, 15),
      (0x3D1C, 15), (0x3D2C, 15), (0x4C6C, 15)):
    l1.write32(addr, _addi(rd, 0, sync))
  # NCRISC ncrisc_run loads.
  for addr, rd in ((0x5EAC, 15), (0x6124, 8), (0x613C, 15)):
    l1.write32(addr, _addi(rd, 0, sync))


class Device:
  """Cycle-structured device shell with real tile/core memory wiring."""

  def __init__(self, harvested_banks: list[int] | None = None, *,
               cores: list[tuple[int, int]] | None = None,
               core_range: CoreRange | None = None,
               core_count: int | None = None,
               runtime_layout: RuntimeLayout | None = None,
               boot_firmware: bool = True,
               firmware_image: dict | None = None,
               firmware_boot_max_cycles: int = 50_000_000):
    if harvested_banks is None:
      harvested_banks = [0]
    if cores is not None and core_range is not None:
      raise ValueError("pass either cores or core_range, not both")
    if cores is not None and core_count is not None:
      raise ValueError("pass either cores or core_count, not both")
    if core_range is not None and core_count is not None:
      raise ValueError("pass either core_range or core_count, not both")
    if cores is None:
      if core_range is not None:
        cores = core_range.cores()
      elif core_count is not None:
        cores = CoreRange.row(1, 2, core_count).cores()
      else:
        cores = [(1, 2)]

    self.harvested_banks = harvested_banks
    self.runtime_layout = runtime_layout or RuntimeLayout()
    self.sim = Simulator()
    self.core_xy = list(cores)
    self.go_messages_addr = FIRMWARE_GO_MESSAGES
    self.go_message_index_addr = FIRMWARE_GO_MESSAGE_INDEX
    self.launch_stride = FIRMWARE_LAUNCH_STRIDE
    self.firmware_boot_cycles = 0
    self.networks: list[dict[int, Memory]] = [{}, {}]
    self.pcie = Memory()
    for net in self.networks:
      net[noc_key(*PCIE_NOC_XY)] = self.pcie

    self.tiles: dict[tuple[int, int], Tile] = {}
    self.cores: list[Core] = []
    for x, y in self.core_xy:
      tile = self._create_tile(x, y)
      self.tiles[(x, y)] = tile
      self.cores.extend(tile.cores)

    self._populate_logical_to_virtual_tables()
    self._create_dram(harvested_banks)
    self._upload_bank_noc_tables()
    self.sim.add(_TileClock(self.tiles))

    first = self.tiles[self.core_xy[0]]
    self.l1 = first.l1
    self.tensix = first.tensix
    self.brisc = first.brisc
    self.ncrisc = first.ncrisc
    self.trisc0 = first.trisc0
    self.trisc1 = first.trisc1
    self.trisc2 = first.trisc2

    if boot_firmware:
      if firmware_image is None:
        import firmware
        firmware_image = firmware.build_all()
      self.firmware_boot_cycles = self.boot_firmware(
        firmware_image,
        max_cycles=firmware_boot_max_cycles,
      )

  def _create_tile(self, x: int, y: int) -> Tile:
    l1 = Memory()
    tensix = Tensix(Scoreboard(), l1=l1)
    core_label = f"{x},{y}"
    tensix.debug_label = core_label
    brisc = BRISC(l1=l1, tensix=tensix)
    ncrisc = NCRISC(l1=l1, tensix=tensix)
    trisc0 = TRISC0(l1=l1, tensix=tensix)
    trisc1 = TRISC1(l1=l1, tensix=tensix)
    trisc2 = TRISC2(l1=l1, tensix=tensix)
    cores = [brisc, ncrisc, trisc0, trisc1, trisc2]

    mmio = Memory()
    mmio.write32(SOFT_RESET_0, SOFT_RESET_ALL)
    stream_regs = StreamRegisters()
    tensix.stream_regs = stream_regs

    noc0 = TimedNOC(0, l1, self.networks[0], x, y, self.sim)
    noc1 = TimedNOC(1, l1, self.networks[1], x, y, self.sim)
    noc0.pre_populate()
    noc1.pre_populate()

    tile_bus = Router()
    tile_bus.register(L1_BASE, L1_END, l1)
    tile_bus.register(STREAM_BASE, STREAM_END, stream_regs, offset=STREAM_BASE)
    key = noc_key(x, y)
    self.networks[0][key] = tile_bus
    self.networks[1][key] = tile_bus

    tile = Tile(
      x=x, y=y, l1=l1,
      brisc=brisc, ncrisc=ncrisc, trisc0=trisc0, trisc1=trisc1, trisc2=trisc2,
      noc0=noc0, noc1=noc1, mmio=mmio, stream_regs=stream_regs,
      tensix=tensix, tdma=tensix.tdma,
    )

    reset_hook = _make_reset_hook(tile)
    for core in cores:
      bus = core.mem
      bus.default = mmio
      bus.register(NOC0_BASE, NOC0_BASE + NOC_SIZE - 1, noc0)
      bus.register(NOC1_BASE, NOC1_BASE + NOC_SIZE - 1, noc1)
      bus.register(STREAM_BASE, STREAM_END, stream_regs, offset=STREAM_BASE)
      bus.register(GPR_BASE, GPR_END, tensix.gpr_mmio, offset=GPR_BASE)
      bus.register(TENSIX_CFG_BASE, TENSIX_CFG_END, tensix.cfg, offset=TENSIX_CFG_BASE)
      bus.register(TDMA_BASE, TDMA_END, tensix.tdma, offset=TDMA_BASE)
      for base, attr in _SLOW_LDM_SLOTS:
        peer = getattr(tile, attr)
        bus.register(base, base + peer.LDM_SIZE - 1, peer.ldm, offset=base)
      bus.on_write32(SOFT_RESET_0, reset_hook)
      self.sim.add(core)
    self.sim.add(tensix)
    return tile

  def _create_dram(self, harvested_banks: list[int]) -> None:
    self.bank_xy = _compute_bank_xy(harvested_banks)
    dram_banks: list[Memory] = []
    for bank_id in sorted(self.bank_xy):
      bank_mem = Memory()
      dram_banks.append(bank_mem)
      x, y0 = self.bank_xy[bank_id]
      for port in range(DRAM_PORTS):
        key = noc_key(x, y0 + port)
        self.networks[0][key] = bank_mem
        self.networks[1][key] = bank_mem
    self.dram_banks = dram_banks
    self.dram = Dram(DRAM_BANK_COUNT - len(harvested_banks), dram_banks, self.bank_xy)

  def _upload_bank_noc_tables(self) -> None:
    bank_table = _build_bank_noc_table(self.harvested_banks, self.core_xy)
    for tile in self.tiles.values():
      tile.l1.load(self.runtime_layout.bank_table_base, bank_table)

  def set_runtime_layout(self, runtime_layout: RuntimeLayout) -> None:
    self.runtime_layout = runtime_layout
    self._upload_bank_noc_tables()

  def _populate_logical_to_virtual_tables(self):
    cols = list(dict.fromkeys(x for x, _ in self.core_xy))
    col_table = cols + [0] * max(0, 20 - len(cols))
    row_table = list(P100A_Y_RANGE) + [0, 0]
    data = bytes((col_table[:20] + row_table[:12]))
    for tile in self.tiles.values():
      tile.l1.load(BANK_TO_NOC_SCRATCH + 2048, data)

  @property
  def clock(self) -> int:
    return self.elapsed_cycles

  @property
  def cycles(self) -> int:
    return self.elapsed_cycles

  @property
  def sim_cycle(self) -> int:
    return self.sim.cycle

  @property
  def core_cycles(self) -> dict[str, int]:
    if len(self.tiles) == 1:
      return {core.ROLE: core.cycles for core in self.cores}
    return {
      f"{tile.x},{tile.y}:{core.ROLE}": core.cycles
      for tile in self.tiles.values() for core in tile.cores
    }

  @property
  def core_blocked_cycles(self) -> dict[str, int]:
    if len(self.tiles) == 1:
      return {core.ROLE: core.blocked_cycles for core in self.cores}
    return {
      f"{tile.x},{tile.y}:{core.ROLE}": core.blocked_cycles
      for tile in self.tiles.values() for core in tile.cores
    }

  @property
  def elapsed_cycles(self) -> int:
    return max(self.core_cycles.values(), default=0)

  def configure_cbs(self, cbs: dict[int, tuple[int, int]]):
    configs = {}
    buf_addr = DATA_BUFFER_SPACE_BASE
    for idx in sorted(cbs):
      num_pages, page_size = cbs[idx]
      total_size = num_pages * page_size
      if buf_addr + total_size > L1_SIZE:
        raise ValueError(f"CB {idx}: not enough L1 space")
      configs[idx] = (buf_addr, total_size, num_pages, page_size)
      buf_addr += total_size
    for tile in self.tiles.values():
      for idx, (addr, size, num_pages, page_size) in configs.items():
        base = self.runtime_layout.cb_config_addr(idx)
        tile.l1.write32(base + 0, addr)
        tile.l1.write32(base + 4, size)
        tile.l1.write32(base + 8, num_pages)
        tile.l1.write32(base + 12, page_size)
    return configs

  def load_core(self, core: Core, addr: int, insns) -> Core:
    core.load(addr, insns)
    return core

  def run(self, cycles: int) -> int:
    self.sim.run(cycles)
    return self.elapsed_cycles

  def run_until(self, done_check, max_cycles: int,
                *, tiles: list[Tile] | None = None) -> int:
    start = self.elapsed_cycles
    for _ in range(max_cycles):
      self.run(1)
      if done_check():
        return self.elapsed_cycles - start
    raise TimeoutError(
      f"emu device did not complete within {max_cycles} cycles "
      f"(elapsed={self.elapsed_cycles}, sim={self.sim_cycle})\n"
      + self.timeout_diagnostics(tiles)
    )

  def timeout_diagnostics(self, tiles: list[Tile] | None = None) -> str:
    if tiles is None:
      tiles = list(self.tiles.values())
    lines = ["timeout diagnostics:"]
    for tile in tiles:
      l1 = tile.l1
      rd_ptr = l1.read32(LAUNCH_MSG_RD_PTR)
      lm = LAUNCH_MSG_RING + (rd_ptr % 8) * 96
      lines.append(
        f"  tile ({tile.x},{tile.y}): "
        f"go=0x{l1.read8(self.go_messages_addr + 3):02x} "
        f"rdptr={rd_ptr} enables=0x{l1.read32(lm + 76):08x}"
      )
      for name in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2"):
        core = getattr(tile, name)
        try:
          word = core.mem.read32(core.pc)
          word_desc = f"0x{word:08x}"
        except Exception as e:
          word_desc = f"{type(e).__name__}:{e}"
        lines.append(
          f"    {name:<6} reset={int(core.in_reset)} "
          f"cycles={core.cycles} blocked={core.blocked_cycles} "
          f"pc=0x{core.pc:08x} word={word_desc} "
          f"ra=0x{core.regs[1]:08x} sp=0x{core.regs[2]:08x}"
        )
      for thread_id, thread in enumerate(tile.tensix.threads):
        gate = thread.wait_gate
        gate_desc = "-"
        if gate.opcode is not None:
          gate_desc = (
            f"{gate.opcode}"
            f"(block=0x{gate.block_mask:x},cond=0x{gate.cond_mask:x},"
            f"sem=0x{gate.sem_mask:x},sem_cond=0x{gate.sem_cond:x})"
          )
        held_desc = "-"
        if thread.held is not None:
          held_desc = thread.held.name
          payload = thread.held.payload
          fields = getattr(payload, "_fields", None)
          if fields:
            payload_desc = ",".join(
              f"{k}={v}" for k, v in sorted(fields.items()))
            held_desc += f"({payload_desc})"
        lines.append(
          f"    tensix t{thread_id}: fifo={len(thread.fifo)} "
          f"held={held_desc} wait={gate_desc} "
          f"busy_until={thread.frontend_busy_until} "
          f"inflight={tile.tensix._backend_inflight[thread_id]}"
        )
      sem = tile.tensix.semaphores
      lines.append(
        "    tensix sem: "
        f"value={sem.value} max={sem.max}"
      )
      srca = tile.tensix.srca
      srcb = tile.tensix.srcb
      lines.append(
        "    tensix src: "
        f"A(unpack={srca.unpack_bank},fpu={srca.fpu_bank},"
        f"owners={[b.allowed_client for b in srca.banks]}) "
        f"B(unpack={srcb.unpack_bank},fpu={srcb.fpu_bank},"
        f"owners={[b.allowed_client for b in srcb.banks]})"
      )
    return "\n".join(lines)

  def boot_firmware(self, firmware: dict, *, max_cycles: int = 50_000_000,
                    patch_sync_addresses: bool = True,
                    go_messages_addr: int | None = None) -> int:
    if go_messages_addr is None:
      go_messages_addr = self.go_messages_addr
    go_init = struct.pack("<BBBB", 0, 0, 0, RUN_MSG_INIT)
    jal = _make_jal(firmware["brisc"]["text_base"])

    for tile in self.tiles.values():
      l1 = tile.l1
      mmio = tile.mmio
      for name, fw in firmware.items():
        for addr, data in fw["segments"]:
          if LDM_BASE <= addr <= LDM_END_8K:
            l1.load(LDM_SCRATCH[name] + (addr - LDM_BASE), data)
          else:
            l1.load(addr, data)
      if patch_sync_addresses:
        _patch_firmware_sync_addresses(l1)

      l1.load(BOOT_JAL, jal)
      l1.load(go_messages_addr, go_init)
      l1.load(ZEROS_BASE, b"\0" * 512)
      mmio.write32(NCRISC_RESET_PC, firmware["ncrisc"]["text_base"])
      mmio.write32(TRISC0_RESET_PC, firmware["trisc0"]["text_base"])
      mmio.write32(TRISC1_RESET_PC, firmware["trisc1"]["text_base"])
      mmio.write32(TRISC2_RESET_PC, firmware["trisc2"]["text_base"])
      tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)

    self._upload_bank_noc_tables()

    return self.run_until(
      lambda: all(t.l1.read8(go_messages_addr + 3) == RUN_MSG_DONE
                  for t in self.tiles.values()),
      max_cycles,
    )

  def dispatch(self, *,
               brisc: bytes = b"",
               ncrisc: bytes = b"",
               trisc: tuple[bytes, bytes, bytes] = (b"", b"", b""),
               brisc_recv: bytes = b"",
               ncrisc_recv: bytes = b"",
               grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None,
               writer_args=None,
               reader_args=None,
               compute_args=None,
               cbs: list[tuple[int, int, int]] | None = None,
               num_semaphores: int = 0,
               max_cycles: int = 50_000_000,
               go_messages_addr: int | None = None,
               go_message_index_addr: int | None = None,
               launch_stride: int | None = None) -> int:
    if go_messages_addr is None:
      go_messages_addr = self.go_messages_addr
    if go_message_index_addr is None:
      go_message_index_addr = self.go_message_index_addr
    if launch_stride is None:
      launch_stride = self.launch_stride
    tiles = list(self.tiles.values())
    num_cores = len(tiles)

    def resolve(args):
      if args is None:
        return [[] for _ in range(num_cores)]
      if callable(args):
        return [args(i) for i in range(num_cores)]
      return args

    writer_rta = resolve(writer_args)
    reader_rta = resolve(reader_args)
    compute_rta = resolve(compute_args)
    max_w = max((len(a) for a in writer_rta), default=0) * 4
    max_r = max((len(a) for a in reader_rta), default=0) * 4
    max_c = max((len(a) for a in compute_rta), default=0) * 4
    sem_off = _align_up(max_w + max_r + max_c)
    cb_mask, cb_blob = _build_cb_blob(cbs)
    local_cb_off = _align_up(sem_off + num_semaphores * 16)
    remote_cb_off = local_cb_off + len(cb_blob)

    brisc_recv = brisc_recv or brisc
    ncrisc_recv = ncrisc_recv or ncrisc
    if grid is None:
      kernel_roles = {core_xy: (brisc, ncrisc) for core_xy in self.core_xy}
    else:
      rows, cols = grid
      grid_cores = [[(x, y) for x in cols] for y in rows]
      kernel_roles = {}
      for row_idx, row in enumerate(grid_cores):
        for col_idx, core_xy in enumerate(row):
          kernel_roles[core_xy] = (
            brisc if col_idx == 0 else brisc_recv,
            ncrisc if row_idx == 0 else ncrisc_recv,
          )

    trisc_kernels = (trisc[0], trisc[1], trisc[2])
    rta_offs = [0, max_w, max_w + max_r, max_w + max_r, max_w + max_r]

    for i, tile in enumerate(tiles):
      l1 = tile.l1
      brisc_kernel, ncrisc_kernel = kernel_roles.get((tile.x, tile.y), (brisc, ncrisc))
      kernels = [brisc_kernel, ncrisc_kernel, *trisc_kernels]
      text_offsets = [0] * 5
      enables = 0
      off = _align_up(remote_cb_off)
      for idx, code in enumerate(kernels):
        if code:
          text_offsets[idx] = off
          off = _align_up(off + len(code))
          enables |= 1 << idx
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
      lm = LAUNCH_MSG_RING + (rd_ptr % 8) * launch_stride
      l1.load(lm, b"\0" * launch_stride)
      for j in range(3):
        l1.write32(lm + j * 4, KERNEL_CONFIG_BASE)
        l1.write16(lm + 12 + j * 2, sem_off)
      l1.write16(lm + 18, local_cb_off)
      l1.write16(lm + 20, remote_cb_off)
      for j in range(5):
        l1.write16(lm + 22 + j * 4, rta_offs[j])
        l1.write16(lm + 22 + j * 4 + 2, local_cb_off)
      l1.write8(lm + 42, 1)
      for j, text_off in enumerate(text_offsets):
        l1.write32(lm + 44 + j * 4, text_off)
      l1.write32(lm + 64, cb_mask)
      l1.write8(lm + 68, 0)
      l1.write8(lm + 69, 0)
      l1.write8(lm + 70, 32)
      l1.write32(lm + 76, enables)
      l1.write32(go_message_index_addr, 0)
      l1.write8(go_messages_addr + 3, RUN_MSG_GO)

    return self.run_until(
      lambda: all(t.l1.read8(go_messages_addr + 3) == RUN_MSG_DONE
                  for t in tiles),
      max_cycles,
      tiles=tiles,
    )

  def read_l1(self, x: int, y: int, addr: int, length: int) -> bytes:
    data = self.tiles[(x, y)].l1._data
    return bytes(data.get(addr + i, 0) for i in range(length))

  def write_l1(self, x: int, y: int, addr: int, data: bytes):
    self.tiles[(x, y)].l1.load(addr, data)

  def read_dram(self, bank: int, addr: int, length: int) -> bytes:
    data = self.dram_banks[bank]._data
    return bytes(data.get(addr + i, 0) for i in range(length))

  def write_dram(self, bank: int, addr: int, data: bytes):
    self.dram_banks[bank].load(addr, data)
