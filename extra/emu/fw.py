import struct

from .memory import (
  SOFT_RESET_0,
  LDM_BASE, LDM_END_8K, LDM_SCRATCH,
  GO_MESSAGES, BANK_TO_NOC_SCRATCH, ZEROS_BASE,
  BRISC_FW_BASE, BOOT_JAL,
  TRISC0_RESET_PC, TRISC1_RESET_PC, TRISC2_RESET_PC,
  NCRISC_RESET_PC,
)

SOFT_RESET_BRISC_ONLY = 0x47000   # BRISC released, TRISCs + NCRISC held

RUN_MSG_INIT = 0x40   # BRISC in firmware init; host wrote it before releasing reset

# DRAM bank geometry (P100A: 8 banks, up to 1 harvested; each bank exposes 3 ports).
DRAM_BANK_COUNT = 8
DRAM_PORTS = 3
DRAM_BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]


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
  from .device import RUN_MSG_DONE

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

  # Step until firmware init completes.
  # BRISC will:
  #   - run do_crt1, noc_init, device_setup
  #   - enable RESET_PC overrides for subordinates
  #   - write SOFT_RESET_0 = 0 (releases subordinates via callback)
  #   - wait for all subordinates to signal DONE
  #   - write go_msg.signal = RUN_MSG_DONE
  tiles = list(device.tiles.values())

  def all_done():
    return all(t.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE for t in tiles)

  device._step_loop(tiles, all_done, max_steps)
