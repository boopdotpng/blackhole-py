"""Emulated Blackhole P100A device.

Creates 120 Tensix tiles (each with 5 RISC-V cores sharing L1, NIU regs, cfg,
and mmio) plus 7 DRAM banks, wired through two independent NOCs.  Mirrors the init
sequence of the real device.py: host writes firmware + bootstrap to L1, then
lets firmware run to completion via round-robin stepping.
"""
import struct
from dataclasses import dataclass, field

from .memory import (
    Memory, Semaphores, L1_SIZE, MAILBOX_BASE, SUBORDINATE_SYNC,
    LAUNCH_MSG_RD_PTR, LAUNCH_MSG_RING, GO_MESSAGES, GO_MESSAGE_INDEX,
    ZEROS_BASE, BRISC_FW_BASE, NCRISC_FW_BASE, TRISC0_FW_BASE,
    TRISC1_FW_BASE, TRISC2_FW_BASE, KERNEL_CONFIG_BASE,
    BANK_TO_NOC_SCRATCH, DATA_BUFFER_SPACE_BASE,
    LDM_SCRATCH, LDM_BASE, LDM_END_8K,
    WALL_CLOCK_L, WALL_CLOCK_H,
    NOC0_BASE, NOC1_BASE,
    NUM_CBS, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE,
)
from .core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from .noc import NOC, noc_key

M32 = 0xFFFFFFFF

# -- P100A layout constants ---------------------------------------------------

P100A_TENSIX_X = (*range(1, 8), *range(10, 15))  # 12 columns
P100A_Y_RANGE  = range(2, 12)                      # 10 rows

# DRAM bank geometry (P100A: 7 active banks, 1 harvested)
DRAM_BANK_COUNT = 8
DRAM_PORTS = 3
DRAM_BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]

# PCIe endpoint
PCIE_X, PCIE_Y = 19, 24

# Protocol constants (matching dispatch.py DevMsgs)
RUN_MSG_INIT = 0x40
RUN_MSG_GO   = 0x80
RUN_MSG_DONE = 0x00


@dataclass
class Dram:
    """Global DRAM: wraps per-bank Memory objects with interleaved access.

    The individual banks are registered on the NOC at their port coordinates —
    firmware addresses them directly.  The read/write_interleaved methods are
    host-side convenience for scattering/gathering tiles across banks.
    """
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

    def read_tensor(self, base_addr: int, num_tiles: int,
                    tile_bytes: int) -> bytes:
        """Read a full interleaved tensor back as contiguous bytes."""
        return b''.join(
            self.read_interleaved(base_addr, t, tile_bytes)
            for t in range(num_tiles)
        )

    def write_tensor(self, base_addr: int, data: bytes, tile_bytes: int):
        """Write contiguous tile data, scattering across banks."""
        num_tiles = len(data) // tile_bytes
        for t in range(num_tiles):
            self.write_interleaved(
                base_addr, t, tile_bytes,
                data[t * tile_bytes : (t + 1) * tile_bytes],
            )


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
    noc: list  # [noc0, noc1] — per-tile NOC interface units (NIU)
    semaphores: Semaphores = field(repr=False)
    shared_mmio: Memory = field(repr=False)

    @property
    def cores(self) -> list:
        return [self.brisc, self.ncrisc, self.trisc0, self.trisc1, self.trisc2]


def _compute_bank_xy(harvested_banks: list[int]) -> dict[int, tuple[int, int]]:
    """Compute DRAM bank → (x, y0) mapping. Same logic as hw.py:build_bank_noc_table."""
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
    """Build the DRAM+L1 bank-to-NOC table. Same as hw.py:build_bank_noc_table."""
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


class Device:
    """Emulated Blackhole P100A device.

    Args:
        firmware: dict mapping core name ('brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2')
                  to a dict with keys:
                    'segments': list of (addr, bytes) — ELF load segments for L1
                    'text_base': int — .text section base address
                  If None, no firmware is loaded and cores are not started.
        harvested_banks: list of harvested DRAM bank indices (default [0] for P100A).
    """

    def __init__(self, firmware: dict | None = None,
                 harvested_banks: list[int] | None = None):
        if harvested_banks is None:
            harvested_banks = [0]
        self.harvested_banks = harvested_banks
        self._clock = 0

        # Compute layout
        self.worker_xy = [(x, y) for x in P100A_TENSIX_X for y in P100A_Y_RANGE]
        num_dram_banks = DRAM_BANK_COUNT - len(harvested_banks)

        # Step 1: Create two NOC fabrics (routing tables for each physical network)
        self.fabric = [{}, {}]

        # Step 2: Create tiles
        self.tiles: dict[tuple[int, int], Tile] = {}
        for x, y in self.worker_xy:
            tile = self._create_tile(x, y)
            self.tiles[(x, y)] = tile

        # Step 3: Create DRAM banks
        self.bank_xy = _compute_bank_xy(harvested_banks)
        dram_banks: list[Memory] = []
        active_banks = sorted(self.bank_xy.keys())
        for bank_id in active_banks:
            bank_mem = Memory()
            dram_banks.append(bank_mem)
            x, y0 = self.bank_xy[bank_id]
            for port in range(DRAM_PORTS):
                key = noc_key(x, y0 + port)
                self.fabric[0][key] = bank_mem
                self.fabric[1][key] = bank_mem
        self.dram_banks = dram_banks  # raw per-bank access (legacy)
        self.dram = Dram(num_banks=num_dram_banks, banks=dram_banks,
                         bank_xy=self.bank_xy)

        # Step 4: Register PCIe endpoint (host sysmem)
        self.pcie_mem = Memory()
        pcie_key = noc_key(PCIE_X, PCIE_Y)
        self.fabric[0][pcie_key] = self.pcie_mem
        self.fabric[1][pcie_key] = self.pcie_mem

        # Step 5: Upload firmware (if provided)
        if firmware is not None:
            self._upload_firmware(firmware)

    @property
    def cores(self) -> list[tuple[int, int]]:
        return list(self.worker_xy)

    def _create_tile(self, x: int, y: int) -> Tile:
        """Create a Tile with 5 cores sharing L1, mmio, noc regs, and cfg."""
        l1 = Memory()
        brisc  = BRISC(l1=l1)
        ncrisc = NCRISC(l1=l1)
        trisc0 = TRISC0(l1=l1)
        trisc1 = TRISC1(l1=l1)
        trisc2 = TRISC2(l1=l1)

        # Shared tile-level resources (replaces per-core defaults)
        shared_noc0 = Memory()
        shared_noc1 = Memory()
        shared_cfg  = Memory()
        shared_mmio = Memory()
        sems = Semaphores()
        # Slow/cross-core LDM: each core can access any core's LDM via fixed addresses
        slow_ldm = [
            (brisc.ldm,  BRISC.LDM_SIZE),
            (ncrisc.ldm, NCRISC.LDM_SIZE),
            (trisc0.ldm, TRISC0.LDM_SIZE),
            (trisc1.ldm, TRISC1.LDM_SIZE),
            (trisc2.ldm, TRISC2.LDM_SIZE),
        ]
        for core in [brisc, ncrisc, trisc0, trisc1, trisc2]:
            core.mem.noc = [shared_noc0, shared_noc1]
            core.mem.cfg = shared_cfg
            core.mem.mmio = shared_mmio
            core.mem.semaphores = sems
            core.mem.slow_ldm = slow_ldm

        # Register tile L1 in both fabrics
        key = noc_key(x, y)
        self.fabric[0][key] = l1
        self.fabric[1][key] = l1

        # Create NOC pair (per-tile NIU controllers, one per physical network)
        noc0 = NOC(0, shared_noc0, l1, self.fabric[0], x, y)
        noc1 = NOC(1, shared_noc1, l1, self.fabric[1], x, y)
        noc0.pre_populate()
        noc1.pre_populate()

        # Wire NOC callback for all cores
        for core in [brisc, ncrisc, trisc0, trisc1, trisc2]:
            core.mem.on_noc_cmd = (
                lambda noc_id, buf, n0=noc0, n1=noc1: [n0, n1][noc_id]._fire(buf)
            )

        return Tile(
            x=x, y=y, l1=l1,
            brisc=brisc, ncrisc=ncrisc,
            trisc0=trisc0, trisc1=trisc1, trisc2=trisc2,
            noc=[noc0, noc1], semaphores=sems, shared_mmio=shared_mmio,
        )

    def _upload_firmware(self, firmware: dict):
        """Load firmware into every tile's L1 and set core PCs."""
        bank_table = _build_bank_noc_table(self.harvested_banks, self.worker_xy)
        go_init = struct.pack("<BBBB", 0, 0, 0, RUN_MSG_INIT)

        for tile in self.tiles.values():
            l1 = tile.l1

            # Upload firmware segments to L1.  Segments whose paddr falls in
            # LDM range (0xFFB00000+) are redirected to per-core L1 scratch
            # areas so that do_crt1() can later copy them into real LDM.
            for name, fw in firmware.items():
                for addr, data in fw['segments']:
                    if LDM_BASE <= addr <= LDM_END_8K:
                        scratch = LDM_SCRATCH[name] + (addr - LDM_BASE)
                        l1.load(scratch, data)
                    else:
                        l1.load(addr, data)

            # Boot data
            l1.load(GO_MESSAGES, go_init)
            l1.load(BANK_TO_NOC_SCRATCH, bank_table)
            l1.load(ZEROS_BASE, b'\x00' * 512)

            # Set PCs directly — all cores start running immediately
            tile.brisc.pc  = firmware['brisc']['text_base']
            tile.ncrisc.pc = firmware['ncrisc']['text_base']
            tile.trisc0.pc = firmware['trisc0']['text_base']
            tile.trisc1.pc = firmware['trisc1']['text_base']
            tile.trisc2.pc = firmware['trisc2']['text_base']

        # Step all tiles until firmware init completes
        self._run_firmware_init()

    def _run_firmware_init(self, max_steps: int = 50_000_000):
        """Step all tiles until every tile's go_msg.signal == RUN_MSG_DONE."""
        tiles = list(self.tiles.values())

        def all_done():
            return all(t.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE for t in tiles)

        self._step_loop(tiles, all_done, max_steps)

    # -- circular buffer configuration ------------------------------------------

    def configure_cbs(self, cbs: dict[int, tuple[int, int]]):
        """Configure circular buffers for all tiles.

        Args:
            cbs: {cb_index: (num_pages, page_size)} where:
                 cb_index  = 0..63
                 num_pages = number of pages/tiles the CB can hold
                 page_size = size of each page in bytes

        Writes the 4-word CB config block to L1 for each active CB and
        allocates data buffer space sequentially from DATA_BUFFER_SPACE_BASE.
        Raises ValueError if total allocation exceeds available L1.
        """
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
        """Round-robin step all cores until done_check() returns True."""
        for _ in range(max_steps):
            self._clock += 1
            for tile in tiles:
                tile.shared_mmio.write32(WALL_CLOCK_L, self._clock & M32)
                tile.shared_mmio.write32(WALL_CLOCK_H, (self._clock >> 32) & M32)
                for core in tile.cores:
                    core.step()
            if done_check():
                return
        raise TimeoutError(
            f"emulated device did not complete within {max_steps} steps "
            f"(clock={self._clock})"
        )

    # -- kernel dispatch (slow dispatch, all cores same program) ---------------

    def run(self, *,
            brisc: bytes = b'',
            ncrisc: bytes = b'',
            trisc: tuple[bytes, bytes, bytes] = (b'', b'', b''),
            writer_args: list[list[int]] | None = None,
            reader_args: list[list[int]] | None = None,
            compute_args: list[list[int]] | None = None,
            max_steps: int = 50_000_000):
        """Run a kernel on all 120 cores (slow dispatch).

        Writes kernel code and launch message to every tile, sets GO, and
        steps until firmware signals DONE.

        Args:
            brisc:  BRISC kernel machine code bytes.
            ncrisc: NCRISC kernel machine code bytes.
            trisc:  Tuple of (trisc0, trisc1, trisc2) kernel machine code bytes.
            writer_args:  Per-core runtime args for BRISC.  List of 120 int lists.
            reader_args:  Per-core runtime args for NCRISC. List of 120 int lists.
            compute_args: Per-core runtime args for TRISC.  List of 120 int lists.
            max_steps: Maximum stepping iterations before timeout.
        """
        tiles = list(self.tiles.values())
        num_cores = len(tiles)

        # Compute kernel text offsets within KERNEL_CONFIG_BASE
        # Layout: [semaphores | rta | crta | cb_config | brisc_text | ncrisc_text | t0 | t1 | t2]
        # For simplicity, pack kernels sequentially after a small header region
        HEADER_SIZE = 0x400  # 1024 bytes for CB config (64 * 16) + sems + RTAs
        offsets = {}
        pos = HEADER_SIZE
        for name, code in [('brisc', brisc), ('ncrisc', ncrisc),
                           ('trisc0', trisc[0]), ('trisc1', trisc[1]), ('trisc2', trisc[2])]:
            offsets[name] = pos
            pos += len(code)
            # Align to 16 bytes
            pos = (pos + 15) & ~15

        # Compute enables bitmask
        enables = 0
        if brisc:   enables |= 1
        if ncrisc:  enables |= 2
        if trisc[0]: enables |= 4
        if trisc[1]: enables |= 8
        if trisc[2]: enables |= 16

        for i, tile in enumerate(tiles):
            l1 = tile.l1
            base = KERNEL_CONFIG_BASE

            # Write kernel code to L1
            if brisc:   l1.load(base + offsets['brisc'],  brisc)
            if ncrisc:  l1.load(base + offsets['ncrisc'], ncrisc)
            if trisc[0]: l1.load(base + offsets['trisc0'], trisc[0])
            if trisc[1]: l1.load(base + offsets['trisc1'], trisc[1])
            if trisc[2]: l1.load(base + offsets['trisc2'], trisc[2])

            # Write per-core runtime args (RTAs) at HEADER_SIZE - 0x80
            rta_base = base + 0x40  # after semaphores
            if writer_args and i < len(writer_args):
                for j, val in enumerate(writer_args[i]):
                    l1.write32(rta_base + j * 4, val)
            if reader_args and i < len(reader_args):
                rta_off = rta_base + 0x20  # NCRISC RTA after BRISC RTA
                for j, val in enumerate(reader_args[i]):
                    l1.write32(rta_off + j * 4, val)
            if compute_args and i < len(compute_args):
                rta_off = rta_base + 0x40  # compute RTA
                for j, val in enumerate(compute_args[i]):
                    l1.write32(rta_off + j * 4, val)

            # Build launch_msg_t at LAUNCH_MSG_RING
            rd_ptr = l1.read32(LAUNCH_MSG_RD_PTR)
            launch_addr = LAUNCH_MSG_RING + (rd_ptr % 8) * 96

            # kernel_config_base[0] (TENSIX)
            l1.write32(launch_addr + 0, base)
            # kernel_text_offset[0..4] (offset 36 in kernel_config_msg_t)
            text_off_base = launch_addr + 36
            l1.write32(text_off_base + 0, offsets['brisc'])
            l1.write32(text_off_base + 4, offsets['ncrisc'])
            l1.write32(text_off_base + 8, offsets['trisc0'])
            l1.write32(text_off_base + 12, offsets['trisc1'])
            l1.write32(text_off_base + 16, offsets['trisc2'])
            # enables (offset 72 in kernel_config_msg_t)
            l1.write32(launch_addr + 72, enables)
            # mode = DISPATCH_MODE_HOST (1) at offset 32
            l1.write8(launch_addr + 32, 1)

            # Set go_msg.signal = RUN_MSG_GO
            l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)

        # Step all tiles until go_msg == DONE on all
        def all_done():
            return all(t.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE for t in tiles)

        self._step_loop(tiles, all_done, max_steps)

    # -- utility methods -------------------------------------------------------

    def read_l1(self, x: int, y: int, addr: int, length: int) -> bytes:
        """Read bytes from a tile's L1 memory."""
        l1 = self.tiles[(x, y)].l1
        return bytes(l1.read8(addr + i) for i in range(length))

    def write_l1(self, x: int, y: int, addr: int, data: bytes):
        """Write bytes to a tile's L1 memory."""
        l1 = self.tiles[(x, y)].l1
        l1.load(addr, data)

    def read_dram(self, bank: int, addr: int, length: int) -> bytes:
        """Read bytes from a DRAM bank."""
        mem = self.dram_banks[bank]
        return bytes(mem.read8(addr + i) for i in range(length))

    def write_dram(self, bank: int, addr: int, data: bytes):
        """Write bytes to a DRAM bank."""
        mem = self.dram_banks[bank]
        for i, b in enumerate(data):
            mem.write8(addr + i, b)

    def read_sysmem(self, addr: int, length: int) -> bytes:
        """Read bytes from host sysmem (PCIe endpoint)."""
        return bytes(self.pcie_mem.read8(addr + i) for i in range(length))

    def write_sysmem(self, addr: int, data: bytes):
        """Write bytes to host sysmem (PCIe endpoint)."""
        self.pcie_mem.load(addr, data)
