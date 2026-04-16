"""Blackhole Tensix tile address map and memory routing."""

# =============================================================================
# L1 shared tile memory
# =============================================================================
L1_BASE                = 0x00000000
L1_END                 = 0x0017FFFF
L1_SIZE                = 0x00180000  # 1.5 MiB
# L1 low-address layout
BOOT_JAL               = 0x000000
NOC_ATOMIC_RET_VAL     = 0x000004
L1_BARRIER             = 0x00000C
ARC_FW_SCRATCH         = 0x000010
INLINE_BASE            = 0x000020
MAILBOX_BASE           = 0x000060
SUBORDINATE_SYNC       = 0x000068   # 4 bytes: [ncrisc, trisc0, trisc1, trisc2]
LAUNCH_MSG_RD_PTR      = 0x00006C
LAUNCH_MSG_RING        = 0x000070   # 8 × 96-byte launch_msg_t
GO_MESSAGES            = 0x000370   # 9 × 4-byte go_msg_t
GO_MESSAGE_INDEX       = 0x0003A0
ZEROS_BASE             = 0x003240
LLK_DEBUG_BASE         = 0x003440
BRISC_FW_BASE          = 0x003840
NCRISC_FW_BASE         = 0x005440
TRISC0_FW_BASE         = 0x005A40
TRISC1_FW_BASE         = 0x006040
TRISC2_FW_BASE         = 0x006A40
KERNEL_CONFIG_BASE     = 0x0086B0
BANK_TO_NOC_SCRATCH    = 0x0116B0
DATA_BUFFER_SPACE_BASE = 0x037000

# =============================================================================
# LDM init scratch areas in L1 (ephemeral — overwritten by kernel config after
# firmware init completes).  The host redirects PT_LOAD segments whose paddr
# falls in 0xFFB00000–0xFFB01FFF into these per-core L1 slots.  do_crt1() then
# copies the data image from the scratch area into real LDM and zeroes BSS.
# =============================================================================
BRISC_LDM_SCRATCH      = KERNEL_CONFIG_BASE                    # 0x086B0
NCRISC_LDM_SCRATCH     = BRISC_LDM_SCRATCH  + 0x2000          # 0x0A6B0
TRISC0_LDM_SCRATCH     = NCRISC_LDM_SCRATCH + 0x2000          # 0x0C6B0
TRISC1_LDM_SCRATCH     = TRISC0_LDM_SCRATCH + 0x1000          # 0x0D6B0
TRISC2_LDM_SCRATCH     = TRISC1_LDM_SCRATCH + 0x1000          # 0x0E6B0
LDM_SCRATCH = {
    'brisc':  BRISC_LDM_SCRATCH,
    'ncrisc': NCRISC_LDM_SCRATCH,
    'trisc0': TRISC0_LDM_SCRATCH,
    'trisc1': TRISC1_LDM_SCRATCH,
    'trisc2': TRISC2_LDM_SCRATCH,
}

# =============================================================================
# Core-private SRAM (LDM) — fast path (aliased per-core at same address)
# =============================================================================
LDM_BASE               = 0xFFB00000
LDM_END_8K             = 0xFFB01FFF  # BRISC/NCRISC
LDM_END_4K             = 0xFFB00FFF  # TRISC0/1/2
# Slow / cross-core paths (fixed per-core, accessible by any core)
LDM_SLOW_BRISC         = 0xFFB14000
LDM_SLOW_NCRISC        = 0xFFB16000
LDM_SLOW_TRISC0        = 0xFFB18000
LDM_SLOW_TRISC1        = 0xFFB1A000
LDM_SLOW_TRISC2        = 0xFFB1C000
LDM_SLOW_STRIDE        = 0x2000     # uniform slot stride for slow-path decoding

# =============================================================================
# TDMA mover registers (0xFFB11000)
# =============================================================================
TDMA_BASE              = 0xFFB11000
TDMA_XMOV_SRC_ADDR    = 0xFFB11000
TDMA_XMOV_DST_ADDR    = 0xFFB11004
TDMA_XMOV_SIZE         = 0xFFB11008
TDMA_XMOV_DIRECTION    = 0xFFB1100C
TDMA_COMMAND           = 0xFFB11010
TDMA_STATUS            = 0xFFB11014
TDMA_PACKED_SIZE       = 0xFFB11018
TDMA_ACC_PACKED_SIZE   = 0xFFB1101C  # read: accumulated; write: initial
TDMA_CLK_GATE_EN       = 0xFFB11024
TDMA_CLK_GATE_HYST     = 0xFFB11028
TDMA_XMOV_L1_BASE     = 0xFFB1102C
TDMA_END               = 0xFFB11FFF

# =============================================================================
# Debug / control registers (0xFFB12000)
# =============================================================================
DEBUG_BASE             = 0xFFB12000
DBG_BUS_CTRL           = 0xFFB12054
DBG_RD_DATA            = 0xFFB1205C
SOFT_RESET_0           = 0xFFB121B0  # 0x47800=all reset, 0x47000=BRISC released
ECC_CTRL               = 0xFFB121D0
WATCHDOG_TIMER         = 0xFFB121E0
WALL_CLOCK_L           = 0xFFB121F0
WALL_CLOCK_H           = 0xFFB121F8
TRISC0_RESET_PC        = 0xFFB12228
TRISC1_RESET_PC        = 0xFFB1222C
TRISC2_RESET_PC        = 0xFFB12230
TRISC_RESET_PC_OVR     = 0xFFB12234  # enable bits (0b111 = all TRISCs)
NCRISC_RESET_PC        = 0xFFB12238
NCRISC_RESET_PC_OVR    = 0xFFB1223C
DEST_CG_CTRL           = 0xFFB12240
DEBUG_END              = 0xFFB12FFF

# =============================================================================
# PIC registers (0xFFB13000)
# =============================================================================
PIC_BASE               = 0xFFB13000
RISC_PC_READBACK       = 0xFFB13138  # 5 × 4 bytes (BRISC..TRISC2)
PIC_END                = 0xFFB13FFF

# =============================================================================
# NIU registers — per-instance offsets (add NOC0_BASE or NOC1_BASE)
# =============================================================================
NOC0_BASE              = 0xFFB20000
NOC1_BASE              = 0xFFB30000
NOC_SIZE               = 0x00010000  # 64 KiB each
# Command buffer stride
NIU_CMD_BUF_STRIDE     = 0x800      # 4 buffers: buf0=+0x000, buf1=+0x800, buf2=+0x1000, buf3=+0x1800
# Registers within each command buffer (offset from buf start)
NIU_TARG_ADDR_LO       = 0x00
NIU_TARG_ADDR_MID      = 0x04
NIU_TARG_ADDR_HI       = 0x08
NIU_RET_ADDR_LO        = 0x0C
NIU_RET_ADDR_MID       = 0x10
NIU_RET_ADDR_HI        = 0x14
NIU_PACKET_TAG         = 0x18
NIU_CTRL               = 0x1C
NIU_AT_LEN_BE          = 0x20
NIU_AT_LEN_BE_1        = 0x24
NIU_AT_DATA            = 0x28
NIU_BRCST_EXCLUDE      = 0x2C
NIU_L1_ACC_AT_INSTRN   = 0x30
NIU_SEC_CTRL           = 0x34
NIU_CMD_CTRL           = 0x40       # write 1 to fire; reads 0 when ready
NIU_NODE_ID            = 0x44       # read-only: physical (y<<6)|x
NIU_ENDPOINT_ID        = 0x48
# Conventional buffer assignments
WR_CMD_BUF             = 0          # large DMA writes
RD_CMD_BUF             = 1          # all DMA reads
WR_REG_CMD_BUF         = 2          # small register/semaphore writes
AT_CMD_BUF             = 3          # atomics
# Misc control (offset from NIU base)
NIU_NUM_MEM_PARITY_ERR = 0x50
NIU_CMD_BUF_AVAIL      = 0x64
NIU_CMD_BUF_OVFL       = 0x68
# Config registers (offset from NIU base, index × 4 starting at 0x100)
NIU_CFG_BASE           = 0x100
NIU_CFG_0              = 0x100
NIU_ROUTER_CFG_0       = 0x104
NIU_ID_LOGICAL         = 0x148      # (y<<6)|x — firmware reads this in noc_init()
NIU_ID_TRANSLATE_COL   = 0x150
NIU_ID_TRANSLATE_ROW   = 0x154
# Status counters (offset from NIU base, index × 4 starting at 0x200)
NIU_STATUS_BASE                    = 0x200
NIU_MST_ATOMIC_RESP_RECEIVED       = 0x200  # +0x00
NIU_MST_WR_ACK_RECEIVED            = 0x204  # +0x04
NIU_MST_RD_RESP_RECEIVED           = 0x208  # +0x08
NIU_MST_CMD_ACCEPTED               = 0x210  # +0x10
NIU_MST_RD_REQ_SENT                = 0x214  # +0x14
NIU_MST_NONPOSTED_WR_REQ_SENT     = 0x228  # +0x28
NIU_MST_POSTED_WR_REQ_SENT        = 0x22C  # +0x2C
# NOC_CTRL bitfield
NOC_CTRL_AT            = 1 << 0
NOC_CTRL_WR            = 1 << 1
NOC_CTRL_WR_BE         = 1 << 2
NOC_CTRL_WR_INLINE     = 1 << 3
NOC_CTRL_RESP_MARKED   = 1 << 4
NOC_CTRL_BRCST         = 1 << 5
NOC_CTRL_BRCST_SRC_INCLUDE = 1 << 17
NOC_CTRL_L1_ACC_AT_EN      = 1 << 31

# =============================================================================
# Stream / NOC overlay registers (0xFFB40000)
# =============================================================================
STREAM_BASE            = 0xFFB40000
STREAM_STRIDE          = 0x1000     # 64 streams × 4 KiB each
STREAM_END             = 0xFFB7FFFF
STREAM_TILES_ACKED     = 0x020      # per-stream offset: reg 8
STREAM_TILES_RECEIVED  = 0x028      # per-stream offset: reg 10

# =============================================================================
# Circular buffer constants
# =============================================================================
NUM_CBS                = 64         # 64 CBs per tile on Blackhole
CB_CONFIG_WORDS        = 4          # words per CB slot: addr, size, num_pages, page_size
CB_CONFIG_BYTES        = CB_CONFIG_WORDS * 4  # 16 bytes per CB slot
CB_L1_CONFIG_BASE      = KERNEL_CONFIG_BASE   # CB config block in L1

# =============================================================================
# MOP expander config (0xFFB80000)
# =============================================================================
MOP_CFG_BASE           = 0xFFB80000
MOP_CFG_END            = 0xFFB800FF

# =============================================================================
# Dest register debug window (0xFFBD8000)
# =============================================================================
DEST_DBG_BASE          = 0xFFBD8000
DEST_DBG_END           = 0xFFBDFFFF

# =============================================================================
# Tensix GPR regfile (0xFFE00000) — 3 threads × 64 regs × 4 bytes
# =============================================================================
GPR_BASE               = 0xFFE00000
GPR_T0                 = 0xFFE00000  # 256 bytes
GPR_T1                 = 0xFFE00100
GPR_T2                 = 0xFFE00200
GPR_END                = 0xFFE002FF

# =============================================================================
# Tensix instruction buffer FIFOs (write-only from RISC-V)
# =============================================================================
INSTRN_BUF_T0          = 0xFFE40000
INSTRN_BUF_T1          = 0xFFE50000
INSTRN_BUF_T2          = 0xFFE60000
INSTRN_BUF_STRIDE      = 0x10000
INSTRN_BUF_END         = 0xFFE6FFFF

# =============================================================================
# PCBuf / semaphore windows
# =============================================================================
PCBUF_T0               = 0xFFE80000
PCBUF_T1               = 0xFFE90000
PCBUF_T2               = 0xFFEA0000
PCBUF_STRIDE           = 0x10000
PCBUF_END              = 0xFFEAFFFF
PCBUF_FIFO_POP         = 0x00       # per-PCBuf offset
PCBUF_COPROC_DONE      = 0x04       # blocks until coprocessor idle
PCBUF_MOP_DONE         = 0x08
PCBUF_SEM_BASE         = 0x20       # +0x20..+0x3C = 8 hardware semaphores

# =============================================================================
# Hardware mailboxes
# =============================================================================
HW_MAILBOX_BRISC       = 0xFFEC0000
HW_MAILBOX_TRISC0      = 0xFFEC1000
HW_MAILBOX_TRISC1      = 0xFFEC2000
HW_MAILBOX_TRISC2      = 0xFFEC3000
HW_MAILBOX_END         = 0xFFEC3FFF

# =============================================================================
# Tensix backend config registers
# =============================================================================
TENSIX_CFG_BASE        = 0xFFEF0000
TENSIX_CFG_END         = 0xFFEFFFFF

# =============================================================================
# Hardware semaphores — 8 per tile, 4-bit value + 4-bit max
# =============================================================================
class Semaphores:
    """8 hardware semaphores per Tensix tile.

    Accessed by TRISCs via the PCBuf semaphore window (0xFFE80020-0xFFE8003C).
    Read returns value. Write with bit 0 clear = SEMPOST, bit 0 set = SEMGET.
    """
    def __init__(self):
        self.value = [0] * 8
        self.max = [0] * 8

    def init(self, idx, value, max_value):
        self.value[idx] = value & 0xF
        self.max[idx] = max_value & 0xF

    def post(self, idx):
        if self.value[idx] < self.max[idx]:
            self.value[idx] += 1

    def get(self, idx):
        if self.value[idx] > 0:
            self.value[idx] -= 1

# Precomputed semaphore window address range
_SEM_WIN_LO = PCBUF_T0 + PCBUF_SEM_BASE        # 0xFFE80020
_SEM_WIN_HI = _SEM_WIN_LO + 7 * 4              # 0xFFE8003C

# =============================================================================
# Sparse memory
# =============================================================================
class Memory:
    """Sparse byte-addressable memory. Reads to unwritten addresses return 0."""
    def __init__(self):
        self._data: dict[int, int] = {}
    def read8(self, addr):          return self._data.get(addr, 0)
    def write8(self, addr, val):    self._data[addr] = val & 0xFF
    def read16(self, addr):         return self.read8(addr) | (self.read8(addr + 1) << 8)
    def write16(self, addr, val):   self.write8(addr, val & 0xFF); self.write8(addr + 1, (val >> 8) & 0xFF)
    def read32(self, addr):
        return (self.read8(addr) | (self.read8(addr+1) << 8)
                | (self.read8(addr+2) << 16) | (self.read8(addr+3) << 24))
    def write32(self, addr, val):
        for i in range(4): self.write8(addr + i, (val >> (8*i)) & 0xFF)
    def load(self, addr, data):
        for i, b in enumerate(data): self._data[addr + i] = b

# =============================================================================
# Address map — routes core memory accesses to the correct backing store
# =============================================================================
class AddressMap:
    """Routes a core's load/store to L1, LDM, NIU regs, or MMIO stubs.

    Regions:
      L1          0x00000000..0x0017FFFF  shared tile memory (accurate)
      LDM         0xFFB00000+ldm_size     core-private SRAM (accurate)
      NOC0 regs   0xFFB20000..0xFFB2FFFF  NIU register file (stub, noc.py later)
      NOC1 regs   0xFFB30000..0xFFB3FFFF  NIU register file (stub, noc.py later)
      Instrn FIFO 0xFFE40000..0xFFE6FFFF  → on_instrn_write callback (tensix later)
      Tensix CFG  0xFFEF0000..0xFFEFFFFF  config register file
      Everything else                      catch-all MMIO (reads=0, writes stored)
    """
    def __init__(self, l1, ldm, ldm_size):
        self.l1 = l1               # Memory — shared tile L1
        self.ldm = ldm             # Memory — core-private SRAM
        self.ldm_size = ldm_size
        self.noc = [Memory(), Memory()]  # NOC0, NOC1 register files
        self.cfg = Memory()              # Tensix backend config registers
        self.mmio = Memory()             # catch-all for other MMIO regions
        self.slow_ldm = []               # [(Memory, size), ...] for 5 cross-core LDM slots
        self.semaphores = None           # Semaphores — set by device
        self.on_instrn_write = None      # callback(thread_id, word) — set by tensix later
        self.on_noc_cmd = None           # callback(noc_id, buf_idx) — set by noc later

    def _route(self, addr):
        """Return (Memory, offset) for addr. Instruction FIFO and NOC CMD_CTRL
        are handled specially in write32, not here."""
        if addr <= L1_END:
            return self.l1, addr
        if self.ldm_size and LDM_BASE <= addr < LDM_BASE + self.ldm_size:
            return self.ldm, addr - LDM_BASE
        if self.slow_ldm and LDM_SLOW_BRISC <= addr < LDM_SLOW_BRISC + 5 * LDM_SLOW_STRIDE:
            slot = (addr - LDM_SLOW_BRISC) >> 13
            if slot < len(self.slow_ldm):
                mem, size = self.slow_ldm[slot]
                off = addr - (LDM_SLOW_BRISC + slot * LDM_SLOW_STRIDE)
                if off < size:
                    return mem, off
            return self.mmio, addr
        if NOC0_BASE <= addr < NOC0_BASE + NOC_SIZE:
            return self.noc[0], addr - NOC0_BASE
        if NOC1_BASE <= addr < NOC1_BASE + NOC_SIZE:
            return self.noc[1], addr - NOC1_BASE
        if TENSIX_CFG_BASE <= addr <= TENSIX_CFG_END:
            return self.cfg, addr - TENSIX_CFG_BASE
        return self.mmio, addr

    def read8(self, addr):
        mem, off = self._route(addr); return mem.read8(off)
    def read16(self, addr):
        mem, off = self._route(addr); return mem.read16(off)
    def read32(self, addr):
        if self.semaphores and _SEM_WIN_LO <= addr <= _SEM_WIN_HI:
            return self.semaphores.value[(addr - _SEM_WIN_LO) >> 2]
        mem, off = self._route(addr); return mem.read32(off)

    def write8(self, addr, val):
        mem, off = self._route(addr); mem.write8(off, val)
    def write16(self, addr, val):
        mem, off = self._route(addr); mem.write16(off, val)

    def write32(self, addr, val):
        # PCBuf semaphore window: bit 0 clear = SEMPOST, bit 0 set = SEMGET
        if self.semaphores and _SEM_WIN_LO <= addr <= _SEM_WIN_HI:
            idx = (addr - _SEM_WIN_LO) >> 2
            if val & 1 == 0:
                self.semaphores.post(idx)
            else:
                self.semaphores.get(idx)
            return
        # Instruction FIFO writes → tensix callback
        if INSTRN_BUF_T0 <= addr <= INSTRN_BUF_END:
            thread = (addr - INSTRN_BUF_T0) >> 16  # 0, 1, or 2
            if self.on_instrn_write: self.on_instrn_write(thread, val)
            return
        # NOC CMD_CTRL writes → fire transaction callback
        for noc_id, base in enumerate((NOC0_BASE, NOC1_BASE)):
            if base <= addr < base + NOC_SIZE:
                off = addr - base
                buf_idx = off >> 11  # 0x800 stride → bits [12:11]
                reg_off = off & 0x7FF
                self.noc[noc_id].write32(off, val)
                if reg_off == NIU_CMD_CTRL and val == 1 and self.on_noc_cmd:
                    self.on_noc_cmd(noc_id, buf_idx)
                return
        mem, off = self._route(addr); mem.write32(off, val)
