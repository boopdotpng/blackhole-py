from emu.device import Device
from emu.memory import (
  Semaphores, NUM_CBS, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE,
  DATA_BUFFER_SPACE_BASE, L1_SIZE,
  STREAM_BASE, STREAM_STRIDE, STREAM_TILES_ACKED, STREAM_TILES_RECEIVED,
  STREAM_SYNC_REG, DISPATCH_MESSAGE_ADDR,
  cb_stream_id, cb_tiles_received_addr, cb_tiles_acked_addr,
  PCBUF_T0, PCBUF_SEM_BASE,
  NIU_CMD_BUF_STRIDE, NIU_TARG_ADDR_LO, NIU_TARG_ADDR_MID, NIU_TARG_ADDR_HI,
  NIU_RET_ADDR_LO, NIU_AT_LEN_BE, NIU_AT_DATA, NIU_CTRL, NIU_CMD_CTRL,
  NOC_CTRL_AT, NOC0_BASE,
)
from emu.noc import AT_INCR_GET
from emu.tests._helpers import mini_device


# -- Semaphores ----------------------------------------------------------------

def test_semaphore_init():
  sem = Semaphores()
  sem.init(1, value=0, max_value=1)
  assert sem.value[1] == 0
  assert sem.max[1] == 1

def test_semaphore_post_get():
  sem = Semaphores()
  sem.init(2, value=0, max_value=4)
  sem.post(2)
  assert sem.value[2] == 1
  sem.post(2)
  assert sem.value[2] == 2
  sem.get(2)
  assert sem.value[2] == 1

def test_semaphore_saturates_at_max():
  sem = Semaphores()
  sem.init(0, value=0, max_value=2)
  sem.post(0); sem.post(0); sem.post(0)  # 3 posts, max is 2
  assert sem.value[0] == 2

def test_semaphore_floors_at_zero():
  sem = Semaphores()
  sem.init(0, value=1, max_value=4)
  sem.get(0)
  assert sem.value[0] == 0
  sem.get(0)  # already 0
  assert sem.value[0] == 0

def test_semaphore_pcbuf_window_read():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  tile.semaphores.init(3, value=5, max_value=15)
  # Read sem[3] via TRISC0's address map
  addr = PCBUF_T0 + PCBUF_SEM_BASE + 3 * 4  # 0xFFE8002C
  assert tile.trisc0.mem.read32(addr) == 5

def test_semaphore_pcbuf_window_post():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  tile.semaphores.init(1, value=0, max_value=1)
  addr = PCBUF_T0 + PCBUF_SEM_BASE + 1 * 4  # 0xFFE80024
  tile.trisc0.mem.write32(addr, 0)  # bit 0 = 0 → SEMPOST
  assert tile.semaphores.value[1] == 1

def test_semaphore_pcbuf_window_get():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  tile.semaphores.init(2, value=3, max_value=4)
  addr = PCBUF_T0 + PCBUF_SEM_BASE + 2 * 4  # 0xFFE80028
  tile.trisc1.mem.write32(addr, 1)  # bit 0 = 1 → SEMGET
  assert tile.semaphores.value[2] == 2

def test_semaphore_shared_across_triscs():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  tile.semaphores.init(1, value=0, max_value=4)
  addr = PCBUF_T0 + PCBUF_SEM_BASE + 1 * 4
  # TRISC0 posts
  tile.trisc0.mem.write32(addr, 0)
  # TRISC1 reads
  assert tile.trisc1.mem.read32(addr) == 1
  # TRISC2 posts
  tile.trisc2.mem.write32(addr, 0)
  assert tile.trisc0.mem.read32(addr) == 2


# -- CB configuration ---------------------------------------------------------

def test_configure_cbs_basic():
  dev = mini_device()
  dev.configure_cbs({
    0: (2, 2048),   # 2 pages of 2048 bytes
    1: (4, 1024),   # 4 pages of 1024 bytes
  })
  tile = dev.tiles[(1, 2)]

  # CB 0: starts at DATA_BUFFER_SPACE_BASE
  base0 = CB_L1_CONFIG_BASE + 0 * CB_CONFIG_BYTES
  assert tile.l1.read32(base0 + 0) == DATA_BUFFER_SPACE_BASE  # addr
  assert tile.l1.read32(base0 + 4) == 2 * 2048                # size
  assert tile.l1.read32(base0 + 8) == 2                       # num_pages
  assert tile.l1.read32(base0 + 12) == 2048                   # page_size

  # CB 1: starts right after CB 0
  base1 = CB_L1_CONFIG_BASE + 1 * CB_CONFIG_BYTES
  assert tile.l1.read32(base1 + 0) == DATA_BUFFER_SPACE_BASE + 4096
  assert tile.l1.read32(base1 + 4) == 4 * 1024
  assert tile.l1.read32(base1 + 8) == 4
  assert tile.l1.read32(base1 + 12) == 1024

def test_configure_cbs_all_tiles():
  dev = mini_device()
  dev.configure_cbs({0: (1, 512)})
  for tile in dev.tiles.values():
    base = CB_L1_CONFIG_BASE
    assert tile.l1.read32(base + 0) == DATA_BUFFER_SPACE_BASE
    assert tile.l1.read32(base + 4) == 512
    assert tile.l1.read32(base + 8) == 1
    assert tile.l1.read32(base + 12) == 512

def test_configure_cbs_overflow():
  dev = mini_device()
  available = L1_SIZE - DATA_BUFFER_SPACE_BASE
  try:
    dev.configure_cbs({0: (1, available + 1)})
    assert False, "should have raised ValueError"
  except ValueError:
    pass

def test_configure_cbs_bad_index():
  dev = mini_device()
  try:
    dev.configure_cbs({64: (1, 512)})
    assert False, "should have raised ValueError"
  except ValueError:
    pass


# -- Stream register CB sync (tiles_acked / tiles_received) -------------------

def test_stream_reg_write_read():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  cb = 5
  # Write tiles_received for CB 5
  recv_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_RECEIVED
  tile.brisc.mem.write32(recv_addr, 42)
  # Another core reads it
  assert tile.trisc0.mem.read32(recv_addr) == 42

def test_stream_reg_cb_sync_pattern():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  cb = 0
  acked_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_ACKED
  recv_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_RECEIVED

  # Initial state: both counters at 0
  assert tile.brisc.mem.read32(recv_addr) == 0
  assert tile.trisc0.mem.read32(acked_addr) == 0

  # Producer (NCRISC) pushes 3 tiles
  tile.ncrisc.mem.write32(recv_addr, 3)

  # Consumer (TRISC0) checks: received - acked >= 1 (cb_wait_front)
  received = tile.trisc0.mem.read32(recv_addr)
  acked = tile.trisc0.mem.read32(acked_addr)
  assert received - acked == 3  # 3 tiles available

  # Consumer pops 2 tiles (cb_pop_front)
  tile.trisc0.mem.write32(acked_addr, acked + 2)

  # Producer checks space: num_pages - (received - acked) >= 1 (cb_reserve_back)
  dev.configure_cbs({0: (4, 1024)})  # 4 pages
  received = tile.ncrisc.mem.read32(recv_addr)
  acked = tile.ncrisc.mem.read32(acked_addr)
  assert 4 - (received - acked) == 3  # 3 slots free


def test_cb_stream_mapping_starts_at_stream_8():
  # Blackhole firmware convention (per fw_trisc0.S disasm and rvlib):
  # CB N lives at stream (8 + N).
  assert cb_stream_id(0) == 8
  assert cb_stream_id(5) == 13
  assert cb_tiles_received_addr(0) == 0xFFB48028
  assert cb_tiles_acked_addr(0)    == 0xFFB48020


def test_dispatch_message_addr_matches_disasm():
  # fw_brisc.S:131 pins s11 to 0xffb70438 — stream 48, reg 270.
  assert DISPATCH_MESSAGE_ADDR == 0xFFB70438


def test_stream_regs_isolated_from_mmio():
  # Writing a stream reg must not touch the tile mmio fallback, and vice
  # versa — they're separate Memory instances now.
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  addr = cb_tiles_received_addr(3)
  tile.brisc.mem.write32(addr, 0xDEADBEEF)
  assert tile.stream_regs.read32(addr) == 0xDEADBEEF
  assert tile.mmio.read32(addr) == 0


def test_cb_push_back_via_remote_noc_atomic():
  # Producer on tile A issues a NOC atomic increment targeting tile B's
  # tiles_received for CB 2.  On real HW this is how cb_push_back reaches
  # the consumer: the write has to land in the consumer's stream register
  # block, not its L1.
  dev = Device(tensix_x=(1, 2), tensix_y=(2,))
  tile_a = dev.tiles[(1, 2)]
  tile_b = dev.tiles[(2, 2)]
  cb = 2
  recv_addr = cb_tiles_received_addr(cb)

  # Program NOC0 buf 0 on tile A: atomic INCR_GET at B[recv_addr], +1.
  # Writes go through the BRISC bus so the NIU fires via NOC.write32's
  # CMD_CTRL hook.
  bus = tile_a.brisc.mem
  buf = NOC0_BASE + 0 * NIU_CMD_BUF_STRIDE
  bus.write32(buf + NIU_TARG_ADDR_LO,  recv_addr)
  bus.write32(buf + NIU_TARG_ADDR_MID, 0)
  bus.write32(buf + NIU_TARG_ADDR_HI,  (2 << 6) | 2)
  bus.write32(buf + NIU_RET_ADDR_LO,   0x1000)
  bus.write32(buf + NIU_AT_LEN_BE,     (AT_INCR_GET << 12) | (1 << 6))
  bus.write32(buf + NIU_AT_DATA,       0)
  bus.write32(buf + NIU_CTRL,          NOC_CTRL_AT)
  bus.write32(buf + NIU_CMD_CTRL,      1)                # fire

  # tile B's stream reg now holds 1; tile B's L1 at recv_addr is untouched.
  assert tile_b.stream_regs.read32(recv_addr) == 1
  assert tile_b.trisc0.mem.read32(recv_addr) == 1
  assert tile_b.l1.read32(recv_addr) == 0
