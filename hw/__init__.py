# Blackhole addresses, L1 layouts, NoC registers and topology. This is the only place these numbers are defined:
# fw/__init__.py renders every int constant here into fw/hw.h for the C firmware. Config fields are in hw.cfg,
# instruction encodings in hw.isa.
# Names follow tt-metal (blackhole tensix.h, cfg_defines.h, noc_parameters.h, tensix_types.h) and tt-llk.

from enum import IntEnum
from . import cfg, isa, sfpu_lat

ADDR_MODS = len(cfg.ADDR_MOD)

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
DRAM_BANK_SIZE, DRAM_PAGE_MAX = 0xFF000000, 4096
ARC = (8, 0)
AICLK_MHZ = 1350
WORKER_ROWS = 10  # Tensix rows per column; firmware numbers workers column-major, x * WORKER_ROWS + y
TELEMETRY_DATA, TELEMETRY_PTR, TAG_ENABLED_TENSIX_COL = 0x80030430, 0x80030434, 34
NOC_NODE_ID = 0xFFB20044  # physical NoC0 coords; NOC_ID_LOGICAL (0xFFB20148) is translated

def coord(x: int, y: int) -> int: return y << 6 | x

def jal(offset: int) -> int:
  return (offset >> 20 & 1) << 31 | (offset >> 1 & 0x3FF) << 21 | (offset >> 11 & 1) << 20 | (offset >> 12 & 0xFF) << 12 | 0x6F

# Worker L1 header, written by Device.run; 0x0 holds `jal CODE_BASE`
SUBORDINATE_SYNC = 0x14
GO_FLAG          = 0x18
LEADER_COORD     = 0x1C
WORKER_X         = 0x20
WORKER_Y         = 0x24
WORKER_ID        = 0x28
NUM_WORKERS      = 0x2C
DRAM_BANKS_L1    = 0x30
GRID_COLS_L1     = 0x34
ROLE_PC          = 0x60
CODE_BASE        = 0x100

# DMA service core L1 layout (fw/service.c on the core, Device.dma_copy on the host)
PACKET, DMA_DEPTH = 32, 4       # host-written DMA descriptors: bytes each, ring depth
DMA_BATCH, DMA_SLOTS = 0x20000, 4  # bytes per chunk; staging slots per engine (reads use tids 8.., writes the DMA_SLOTS above)
SVC_NCRISC_SYNC  = 0x10         # NCRISC boot handshake (writes 2 when up)
SVC_COPY_GO      = 0x20         # BRISC -> NCRISC: copy sequence number to start
SVC_COPY_DONE    = 0x30         # NCRISC -> BRISC: copy sequence number finished
SVC_PIPE_PROD    = 0x40         # DRAM-source copy: chunks BRISC has staged
SVC_PIPE_CONS    = 0x50         # DRAM-source copy: chunks NCRISC has written out
SVC_STATE        = 0x80         # host-initialised block
SVC_STATE_SIZE   = 0x100
SVC_WPTR         = SVC_STATE          # latest host-submitted DMA sequence
SVC_SIGNAL       = SVC_STATE + 8      # host address of the completion counter
SVC_COPY_DESC    = SVC_STATE + 0x30
SVC_SCRATCH      = SVC_STATE + 0x80
SVC_BRISC_BASE,  SVC_BRISC_SIZE  = 0x200, 0x3E00
SVC_NCRISC_BASE, SVC_NCRISC_SIZE = 0x4000, 0x4000
SVC_PACKETS      = 0x9000
SVC_DMA_STAGING  = 0x10000      # 2 engines x DMA_SLOTS x DMA_BATCH

STACK_TOP                = 0xFFB01FF0
TRISC_STACK_TOP          = 0xFFB00FF0
TDMA_CLK_GATE_EN         = 0xFFB11024
SOFT_RESET               = 0xFFB121B0
RESET_BRISC              = 1 << 11
RESET_TRISC0             = 1 << 12
RESET_NCRISC             = 1 << 18
RESET_ALL                = 0x47800
WALL_CLOCK_L             = 0xFFB121F0
TRISC0_RESET_PC          = 0xFFB12228
TRISC_RESET_PC_OVERRIDE  = 0xFFB12234
NCRISC_RESET_PC          = 0xFFB12238
NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
DEST_CG_CTRL             = 0xFFB12240

CFG_ECC_SCRUBBER         = 0xFFEF0000 + 3 * 4
CFG_RISCV_IC_INVALIDATE  = 0xFFEF0000 + 185 * 4
CFG_RISC_PREFETCH_CTRL   = 0xFFEF0000 + 208 * 4
CFG_BANK_WORDS           = 224
CFG_GLOBAL_BASE          = 180
CFG_STATE_RESET          = 4

# Tensix instructions fw/boot.c issues to reset a core
ZEROACC_ALL              = isa.ZEROACC(clear_mode=3)
SFPENCC_RESET            = isa.SFPENCC(imm12_math=3, instr_mod1=10)
NOP                      = isa.NOP()
SFPLOADI_MINUS1          = isa.SFPLOADI(imm16=0xBF80)  # -1.0 as bf16
SFPCONFIG_L11            = isa.SFPCONFIG(config_dest=isa.LReg.NEG_ONE)
SEMINIT_ALL              = isa.SEMINIT(max_value=1, sem_sel=0xFF)
CLEARDVALID_RESET        = isa.CLEARDVALID(reset=1)
SETRWC_ZERO              = isa.SETRWC(BitMask=15)
SETADCXY_ZERO            = isa.SETADCXY(CntSetMask=7, BitMask=15)
SETADCZW_ZERO            = isa.SETADCZW(CntSetMask=7, BitMask=15)
THD_CFG_TTSYNC           = 56
THD_CFG_RESET            = 67

L1_SIZE = 0x180000
assert SVC_SCRATCH % 64 == 0 and SVC_STATE + SVC_STATE_SIZE <= SVC_BRISC_BASE, "service state overlaps the BRISC image"
assert SVC_BRISC_BASE + SVC_BRISC_SIZE <= SVC_NCRISC_BASE and SVC_NCRISC_BASE + SVC_NCRISC_SIZE <= SVC_PACKETS
assert SVC_PACKETS + PACKET * DMA_DEPTH <= SVC_DMA_STAGING, "packet buffer overlaps DMA staging"
assert 2 <= DMA_SLOTS and 8 + 2 * DMA_SLOTS <= 16, "DMA ring needs 2..4 slots: 2 NoC tids each, from tid 8"
assert SVC_DMA_STAGING + 2 * DMA_SLOTS * DMA_BATCH <= L1_SIZE, "DMA staging exceeds L1"
LOCAL_MEM = 0xFFB00000            # each RISC's private data RAM
NOC0_REGS = 0xFFB20000
NOC_INSTANCE_OFFSET = 0x10000
OVERLAY_STREAMS = 0xFFB40000
STREAM_STRIDE = 0x1000
MOP_CFG = 0xFFB80000
REGFILE = 0xFFE00000              # this thread's 64 Tensix GPRs
INSTRN_BUF = 0xFFE40000           # a store pushes one Tensix instruction
PC_BUF = 0xFFE80000
TENSIX_CFG = 0xFFEF0000


# TRISC-only MMIO at PC_BUF. Write (to order earlier stores), then load, and consume the result in an ALU op before
# any other PC_BUF load: hardware bug, otherwise the next load can return garbage or hang.

COPROCESSOR_DONE_CHECK = PC_BUF + 4   # load returns once every Tensix instruction from this thread has finished
MOP_EXPANDER_DONE_CHECK = PC_BUF + 8  # load returns once the MOP expander is idle (safe to rewrite MOP_CFG)
SEMAPHORE_ACCESS = PC_BUF + 32
SEM_POST, SEM_GET = 0, 1              # store to SemaphoreAccess[i]: even = SEMPOST (+1), odd = SEMGET (-1)


class Sem(IntEnum):
  FPU_SFPU = 0
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  UNPACK_OPERAND_SYNC = 3
  PACK_DONE = 4
  UNPACK_SYNC = 5       # TTRV unpack credit; SEMINIT'd every launch
  UNPACK_MATH_DONE = 6
  MATH_DONE = 7


def semaphore(i): return SEMAPHORE_ACCESS + 4 * i


MOP_CFG_WORDS = 9  # outer, inner, start, end0, end1, loop0, loop1, last_inner, last

# Reserved Tensix GPRs. SETDMAREG addresses 16-bit halves: 2g, 2g+1 = GPR g.
GPR_PACK_L1_ADDRESS = 12
GPR_UNPACK_BASE = (13, 14)

# Overlay stream registers reused as CB counters, like tt-metal. Only the low 16 bits count.

CBS = 32
CB_STREAM0 = 8
CB_PUSHED, CB_POPPED = 8, 10


def stream_reg(stream, reg): return OVERLAY_STREAMS + stream * STREAM_STRIDE + 4 * reg
def cb_pushed(cb): return stream_reg(CB_STREAM0 + cb, CB_PUSHED)
def cb_popped(cb): return stream_reg(CB_STREAM0 + cb, CB_POPPED)


NIU = {"brisc": NOC0_REGS, "ncrisc": NOC0_REGS + NOC_INSTANCE_OFFSET}
CMD_BUF_STRIDE = 0x800
NOC_MAX_BURST = 0x4000
NOC_TIDS = 16


class CmdBuf(IntEnum):
  MCAST = 0
  READ = 1
  WRITE = 2
  ATOMIC = 3


class Cmd(IntEnum):
  # Writes: TARG local, RET remote. Reads and atomics: TARG remote.
  TARG_LO = 0x00
  TARG_MID = 0x04
  TARG_COORD = 0x08
  RET_LO = 0x0C
  RET_MID = 0x10
  RET_COORD = 0x14
  PACKET_TAG = 0x18
  CTRL = 0x1C
  AT_LEN_BE = 0x20        # length in bytes, or the atomic instruction
  AT_LEN_BE_1 = 0x24
  AT_DATA = 0x28
  BRCST_EXCLUDE = 0x2C
  CMD_CTRL = 0x40         # write 1 to send; reads nonzero while the buffer is busy


CTRL_ATOMIC = 1 << 0
CTRL_WRITE = 1 << 1
CTRL_RESP_MARKED = 1 << 4
CTRL_BRCST_PACKET = 1 << 5
CTRL_VC_STATIC = 1 << 7
CTRL_BRCST_SRC_INCLUDE = 1 << 17


def ctrl_static_vc(vc): return CTRL_VC_STATIC | vc << 13


def packet_tag(tid): return tid << 10


AT_INCR_GET = 1
def at_instruction(ins, wrap=31, index=0): return ins << 12 | wrap << 2 | index


NOC_ID_LOGICAL = 0x148
NOC_OUTSTANDING, NOC_OUTGOING = 0x240, 0x280
def outstanding(tid): return NOC_OUTSTANDING + 4 * tid    # reads and write acks in flight
def outgoing(tid): return NOC_OUTGOING + 4 * tid          # writes not yet sent out of L1


# p150 topology, translated NoC coordinates

WORKER_COLUMNS = (*range(1, 8), *range(10, 17))
WORKER_ROW0 = 2
WORKER_X_GAP = 7


def worker_coord(x, y): return coord(WORKER_COLUMNS[x], WORKER_ROW0 + y)


DRAM_BANKS = 8
DRAM_X0 = 17
DRAM_Y0 = 12
# three NoC endpoints per bank, by y; banks 4..7 are reversed
DRAM_PORTS = ((14, 13, 12), (15, 16, 17), (18, 19, 20), (21, 22, 23), (14, 13, 12), (17, 16, 15), (20, 19, 18), (23, 22, 21))


def dram_coord(bank, port): return coord(DRAM_X0 + bank // 4, DRAM_PORTS[bank][port])


PCIE_COORD = 1 << 24 | coord(19, 24)   # bit 24 selects host memory

# E4M3 is LF8 plus the Unp/Pac_LF8_4b_exp flag.
class DataFormat(IntEnum):
  FLOAT32 = 0
  FLOAT16 = 1
  BFP8 = 2
  BFP4 = 3
  TF32 = 4
  FLOAT16_B = 5
  BFP8_B = 6
  BFP4_B = 7
  INT32 = 8
  UINT16 = 9
  LF8 = 10
  BFP2 = 11
  INT8 = 14
  BFP2_B = 15


FORMAT = {
  "fp32": DataFormat.FLOAT32, "bf16": DataFormat.FLOAT16_B, "bfp8": DataFormat.BFP8_B,
  "e4m3": DataFormat.LF8, "e5m2": DataFormat.LF8,
}

CORE = {"x": WORKER_X, "y": WORKER_Y, "id": WORKER_ID}

# TTRV ABI. LOCAL_MEM: [0, 512) CB cursors, [512, 2048) spill frame, [2048, ...) firmware.
# Base registers point at the middle of a 4 KiB block so signed 12-bit offsets reach all of it.

CB_CURSORS = LOCAL_MEM
CB_CURSOR_STRIDE = 16
CB_CONSUMER, CB_PRODUCER = 0, 8   # cursor offsets: +0 pointer, +4 count
SPILL_FRAME = LOCAL_MEM + 512
SPILL_SLOTS = 384
FIRMWARE_LOCAL = LOCAL_MEM + 2048


def cb_cursor(cb, producer): return CB_CURSORS + CB_CURSOR_STRIDE * cb + (CB_PRODUCER if producer else CB_CONSUMER)


LOCAL_BASE_REG = 3


def bases(role):
  second = NIU.get(role, TENSIX_CFG if role == "trisc0" else PC_BUF)
  return {LOCAL_BASE_REG: LOCAL_MEM + 2048, 4: second + 2048} | ({5: PC_BUF + 2048} if role == "trisc0" else {})
