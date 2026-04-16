"""Tests for circular buffers and hardware semaphores."""
from emu.device import Device
from emu.memory import (
    Semaphores, NUM_CBS, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE,
    DATA_BUFFER_SPACE_BASE, L1_SIZE,
    STREAM_BASE, STREAM_STRIDE, STREAM_TILES_ACKED, STREAM_TILES_RECEIVED,
    PCBUF_T0, PCBUF_SEM_BASE,
)


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
    """TRISC can read semaphore value via PCBuf window."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    tile.semaphores.init(3, value=5, max_value=15)
    # Read sem[3] via TRISC0's address map
    addr = PCBUF_T0 + PCBUF_SEM_BASE + 3 * 4  # 0xFFE8002C
    assert tile.trisc0.read32(addr) == 5

def test_semaphore_pcbuf_window_post():
    """Write with bit 0 clear = SEMPOST."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    tile.semaphores.init(1, value=0, max_value=1)
    addr = PCBUF_T0 + PCBUF_SEM_BASE + 1 * 4  # 0xFFE80024
    tile.trisc0.write32(addr, 0)  # bit 0 = 0 → SEMPOST
    assert tile.semaphores.value[1] == 1

def test_semaphore_pcbuf_window_get():
    """Write with bit 0 set = SEMGET."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    tile.semaphores.init(2, value=3, max_value=4)
    addr = PCBUF_T0 + PCBUF_SEM_BASE + 2 * 4  # 0xFFE80028
    tile.trisc1.write32(addr, 1)  # bit 0 = 1 → SEMGET
    assert tile.semaphores.value[2] == 2

def test_semaphore_shared_across_triscs():
    """All TRISCs see the same semaphore state."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    tile.semaphores.init(1, value=0, max_value=4)
    addr = PCBUF_T0 + PCBUF_SEM_BASE + 1 * 4
    # TRISC0 posts
    tile.trisc0.write32(addr, 0)
    # TRISC1 reads
    assert tile.trisc1.read32(addr) == 1
    # TRISC2 posts
    tile.trisc2.write32(addr, 0)
    assert tile.trisc0.read32(addr) == 2


# -- CB configuration ---------------------------------------------------------

def test_configure_cbs_basic():
    """CB config writes 4 words per CB to L1."""
    dev = Device(firmware=None)
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
    """CB config is written to every tile."""
    dev = Device(firmware=None)
    dev.configure_cbs({0: (1, 512)})
    for tile in dev.tiles.values():
        base = CB_L1_CONFIG_BASE
        assert tile.l1.read32(base + 0) == DATA_BUFFER_SPACE_BASE
        assert tile.l1.read32(base + 4) == 512
        assert tile.l1.read32(base + 8) == 1
        assert tile.l1.read32(base + 12) == 512

def test_configure_cbs_overflow():
    """Raises ValueError if CBs exceed available L1 space."""
    dev = Device(firmware=None)
    available = L1_SIZE - DATA_BUFFER_SPACE_BASE
    try:
        dev.configure_cbs({0: (1, available + 1)})
        assert False, "should have raised ValueError"
    except ValueError:
        pass

def test_configure_cbs_bad_index():
    """Raises ValueError for out-of-range CB index."""
    dev = Device(firmware=None)
    try:
        dev.configure_cbs({64: (1, 512)})
        assert False, "should have raised ValueError"
    except ValueError:
        pass

def test_configure_cbs_returns_configs():
    """configure_cbs returns the computed config dict."""
    dev = Device(firmware=None)
    configs = dev.configure_cbs({
        0: (2, 1024),
        3: (1, 512),
    })
    assert 0 in configs
    assert 3 in configs
    addr0, size0, npages0, psize0 = configs[0]
    assert addr0 == DATA_BUFFER_SPACE_BASE
    assert size0 == 2048
    assert npages0 == 2
    assert psize0 == 1024


# -- Stream register CB sync (tiles_acked / tiles_received) -------------------

def test_stream_reg_write_read():
    """Stream registers for CB sync are readable/writable via MMIO."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    cb = 5
    # Write tiles_received for CB 5
    recv_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_RECEIVED
    tile.brisc.write32(recv_addr, 42)
    # Another core reads it
    assert tile.trisc0.read32(recv_addr) == 42

def test_stream_reg_cb_sync_pattern():
    """Simulate a producer/consumer CB sync pattern via stream registers."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    cb = 0
    acked_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_ACKED
    recv_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_RECEIVED

    # Initial state: both counters at 0
    assert tile.brisc.read32(recv_addr) == 0
    assert tile.trisc0.read32(acked_addr) == 0

    # Producer (NCRISC) pushes 3 tiles
    tile.ncrisc.write32(recv_addr, 3)

    # Consumer (TRISC0) checks: received - acked >= 1 (cb_wait_front)
    received = tile.trisc0.read32(recv_addr)
    acked = tile.trisc0.read32(acked_addr)
    assert received - acked == 3  # 3 tiles available

    # Consumer pops 2 tiles (cb_pop_front)
    tile.trisc0.write32(acked_addr, acked + 2)

    # Producer checks space: num_pages - (received - acked) >= 1 (cb_reserve_back)
    dev.configure_cbs({0: (4, 1024)})  # 4 pages
    received = tile.ncrisc.read32(recv_addr)
    acked = tile.ncrisc.read32(acked_addr)
    assert 4 - (received - acked) == 3  # 3 slots free
