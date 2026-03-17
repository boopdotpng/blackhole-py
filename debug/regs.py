# debug/regs.py - Blackhole Tensix debug register addresses, bit fields, opcodes
#
# All addresses from: tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h
# Bit fields from:    tt-exalens/ttexalens/hardware/baby_risc_debug.py
#                     tt-llk/tt_llk_blackhole/common/inc/ckernel_debug.h
#                     tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h

# -- TLB alignment --------------------------------------------------------- #
TLB_2M = 1 << 21  # 2MB TLB window size

def tlb_align(addr: int) -> tuple[int, int]:
  """Align an address to 2MB TLB boundary. Returns (base, offset)."""
  base = addr & ~(TLB_2M - 1)
  return base, addr - base

# -- base ------------------------------------------------------------------ #
DEBUG_REGS_BASE = 0xFFB12000
DEBUG_TLB_BASE, DEBUG_TLB_OFFSET = tlb_align(DEBUG_REGS_BASE)  # (0xFFA00000, 0x112000)

# -- RISC-V debug interface (DR read/write via NOC) ----------------------- #
# four MMIO registers that proxy access to the 14 per-core debug registers
RISC_DBG_CNTL_0   = DEBUG_REGS_BASE | 0x80   # 0xFFB12080 - trigger DR r/w
RISC_DBG_CNTL_1   = DEBUG_REGS_BASE | 0x84   # 0xFFB12084 - write data
RISC_DBG_STATUS_0  = DEBUG_REGS_BASE | 0x88   # 0xFFB12088 - read-valid flag
RISC_DBG_STATUS_1  = DEBUG_REGS_BASE | 0x8C   # 0xFFB1208C - read result

# CNTL_0 bit layout:
#   [31]    pulse      - 0->1 transition triggers the access
#   [19:17] risc_sel   - which RISC core (2 bits effective, see RISC_SEL)
#   [16]    is_write   - 1 = write DR, 0 = read DR
#   [10:0]  dr_addr    - debug register address (0-17)
#
# STATUS_0:
#   [30]    read_valid  - set when read result is ready in STATUS_1
STATUS_0_READ_VALID = 1 << 30

# -- risc_sel encoding (bits 19:17 of CNTL_0) ----------------------------- #
# only 2 hardware bits => values 0-3.  NCRISC (4) has NO debug hw.
RISC_SEL = {
  "brisc":  0,  # 0x00000 in bits [19:17]
  "trisc0": 1,  # 0x20000
  "trisc1": 2,  # 0x40000
  "trisc2": 3,  # 0x60000
}
# convenience: pre-shifted values for CNTL_0
CNTL0_WRITE = {name: 0x80010000 | (rid << 17) for name, rid in RISC_SEL.items()}
CNTL0_READ  = {name: 0x80000000 | (rid << 17) for name, rid in RISC_SEL.items()}

# -- debug register (DR) addresses ---------------------------------------- #
DR_STATUS               = 0   # read-only  status bitmask
DR_COMMAND              = 1   # write      command + control
DR_COMMAND_ARG_0        = 2   # read/write command argument 0 (reg index / addr)
DR_COMMAND_ARG_1        = 3   # read/write command argument 1 (data)
DR_COMMAND_RETURN_VALUE = 4   # read-only  command result
DR_WATCHPOINT_SETTINGS  = 5   # read/write 8x 4-bit watchpoint modes
DR_WATCHPOINT_BASE      = 10  # DR(10)..DR(17) = watchpoint 0..7 addresses

# -- DR status bits (DR_STATUS = DR(0)) ----------------------------------- #
STATUS_HALTED             = 0x1
STATUS_PC_WATCHPOINT_HIT  = 0x2
STATUS_MEM_WATCHPOINT_HIT = 0x4
STATUS_EBREAK_HIT         = 0x8
# bits 8..15: which watchpoint N triggered (1 << (8 + N))

# -- DR command bits (DR_COMMAND = DR(1)) ---------------------------------- #
CMD_HALT            = 0x00000001  # pause a running core
CMD_STEP            = 0x00000002  # single-step (while halted, slow exec mode)
CMD_CONTINUE        = 0x00000004  # resume
CMD_READ_REGISTER   = 0x00000008  # read GPR (index in DR(2), result in DR(4))
CMD_WRITE_REGISTER  = 0x00000010  # write GPR (index in DR(2), value in DR(3))
CMD_READ_MEMORY     = 0x00000020  # read mem (addr in DR(2), result in DR(4))
CMD_WRITE_MEMORY    = 0x00000040  # write mem (addr in DR(2), value in DR(3))
CMD_FLUSH_REGISTERS = 0x00000080  # zero x1..x31
CMD_FLUSH           = 0x00000100  # flush / abort in-flight + write PC
CMD_DEBUG_MODE      = 0x80000000  # must be ORed with all commands
CMD_SLOW_EXEC_MODE  = 0x80000000  # bit 31 in DR(1) also = persistent slow mode

# -- watchpoint modes (4 bits per watchpoint in DR(5)) --------------------- #
WP_DISABLED       = 0
WP_PC_BREAK       = 8   # instruction breakpoint at address
WP_MEM_READ       = 9   # memory watchpoint: read
WP_MEM_WRITE      = 10  # memory watchpoint: write
WP_MEM_READ_WRITE = 11  # memory watchpoint: read or write

# -- GPR indices ----------------------------------------------------------- #
GPR_COUNT = 32
GPR_PC    = 32  # pseudo-index: read/write PC via GPR protocol
GPR_NAMES = [
  "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0",   "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6",   "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8",   "s9", "s10","s11","t3", "t4", "t5", "t6",
]

# -- soft reset register --------------------------------------------------- #
SOFT_RESET_0 = DEBUG_REGS_BASE | 0x1B0  # 0xFFB121B0

SOFT_RESET_BRISC  = 1 << 11
SOFT_RESET_TRISC0 = 1 << 12
SOFT_RESET_TRISC1 = 1 << 13
SOFT_RESET_TRISC2 = 1 << 14
SOFT_RESET_NCRISC = 1 << 18
SOFT_RESET_ALL    = SOFT_RESET_BRISC | SOFT_RESET_TRISC0 | SOFT_RESET_TRISC1 | SOFT_RESET_TRISC2 | SOFT_RESET_NCRISC
# also includes FPU/SrcA/SrcB/Dest/thcon resets from hw.py:
SOFT_RESET_ALL_FULL = 0x47800

SOFT_RESET_BITS = {
  "brisc":  SOFT_RESET_BRISC,
  "trisc0": SOFT_RESET_TRISC0,
  "trisc1": SOFT_RESET_TRISC1,
  "trisc2": SOFT_RESET_TRISC2,
  "ncrisc": SOFT_RESET_NCRISC,
}

# -- wall clock ------------------------------------------------------------ #
WALL_CLOCK_L = DEBUG_REGS_BASE | 0x1F0  # 0xFFB121F0  low 32 bits
WALL_CLOCK_H = DEBUG_REGS_BASE | 0x1F8  # 0xFFB121F8  high 32 bits (snapshot)

# -- debug bus (daisy chain) ----------------------------------------------- #
DBG_BUS_CTRL    = DEBUG_REGS_BASE | 0x54  # 0xFFB12054
DBG_BUS_RD_DATA = DEBUG_REGS_BASE | 0x5C  # 0xFFB1205C

# DBG_BUS_CTRL bit layout:
#   [15:0]  sig_sel     - signal selection
#   [23:16] daisy_sel   - daisy chain tap
#   [27:24] rd_sel      - which 32-bit slice of 128-bit group
#   [28]    reg_ovrd_en
#   [29]    daisy_en    - must be 1 to enable
#   [31:30] reserved
def dbg_bus_cntl(sig_sel: int, daisy_sel: int, rd_sel: int) -> int:
  return (1 << 29) | (rd_sel << 24) | (daisy_sel << 16) | sig_sel

# PC signals: daisy_sel=7, rd_sel=1, sig_sel varies, mask=0x3FFFFFFF
PC_SIGNALS = {
  "brisc":  {"sig_sel": 2 * 5 + 1,  "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc0": {"sig_sel": 2 * 6 + 1,  "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc1": {"sig_sel": 2 * 7 + 1,  "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc2": {"sig_sel": 2 * 8 + 1,  "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "ncrisc": {"sig_sel": 2 * 12 + 1, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
}

# -- register file debug array --------------------------------------------- #
DBG_ARRAY_RD_EN   = DEBUG_REGS_BASE | 0x60  # 0xFFB12060
DBG_ARRAY_RD_CMD  = DEBUG_REGS_BASE | 0x64  # 0xFFB12064
DBG_ARRAY_RD_DATA = DEBUG_REGS_BASE | 0x6C  # 0xFFB1206C

# DBG_ARRAY_RD_CMD bit layout:
#   [11:0]  row_addr    - row index within the array
#   [15:12] row_32b_sel - which 32-bit chunk (0..7 for 8 chunks per row)
#   [18:16] array_id    - 0=SrcA, 1=SrcB, 2=Dest
#   [19]    bank_id     - which bank (for double-buffered SrcA/SrcB)
ARRAY_SRCA = 0
ARRAY_SRCB = 1
ARRAY_DEST = 2

def dbg_array_cmd(array_id: int, row_addr: int, chunk: int, bank: int = 0) -> int:
  return (bank << 19) | (array_id << 16) | (chunk << 12) | row_addr

# -- CFG register read ----------------------------------------------------- #
TENSIX_CREG_READ   = DEBUG_REGS_BASE | 0x58  # 0xFFB12058  write index here
TENSIX_CREG_RDDATA = DEBUG_REGS_BASE | 0x78  # 0xFFB12078  read result here

# CFG register IDs (for the index written to TENSIX_CREG_READ)
CFG_THREAD_0 = 0  # TRISC0 / unpack thread config
CFG_THREAD_1 = 1  # TRISC1 / math thread config
CFG_THREAD_2 = 2  # TRISC2 / pack thread config
CFG_HW_0     = 3  # hardware config state 0
CFG_HW_1     = 4  # hardware config state 1

# -- instruction injection ------------------------------------------------- #
INSTRN_BUF_CTRL0  = DEBUG_REGS_BASE | 0xA0  # 0xFFB120A0
INSTRN_BUF_CTRL1  = DEBUG_REGS_BASE | 0xA4  # 0xFFB120A4
INSTRN_BUF_STATUS = DEBUG_REGS_BASE | 0xA8  # 0xFFB120A8

# protocol: see inspect.py for full inject_instruction() implementation
# CTRL0: write (1 << thread_id) to claim, then (1<<(4+tid)) | (1<<tid) to push
# CTRL1: write the 32-bit instruction word
# STATUS: poll bit [thread_id] for ready, bit [4+thread_id] for drained

# -- direct dest access (Blackhole only) ----------------------------------- #
DEST_BASE = 0xFFBD8000  # 32KB = 8 tiles x 1024 rows x 4 bytes
DEST_SIZE = 32768        # in bytes

# dest format control: CFG register at ADDR32=3, per-section fields
# SEC0 = TRISC0, SEC1 = TRISC1, SEC2 = TRISC2
# fmt field: 0=FP32, 1=FP16, 2=BF16, 3=Int32, 4=Int16, 5=Int8
DEST_ACCESS_CTRL_ADDR32 = 3
DEST_FMT_FP32  = 0
DEST_FMT_FP16  = 1
DEST_FMT_BF16  = 2
DEST_FMT_INT32 = 3
DEST_FMT_INT16 = 4
DEST_FMT_INT8  = 5

# -- FPU sticky bits -------------------------------------------------------- #
FPU_STICKY_BITS = DEBUG_REGS_BASE | 0xB4  # 0xFFB120B4

# -- reset PC override registers ------------------------------------------- #
TRISC0_RESET_PC          = DEBUG_REGS_BASE | 0x228  # 0xFFB12228
TRISC1_RESET_PC          = DEBUG_REGS_BASE | 0x22C  # 0xFFB1222C
TRISC2_RESET_PC          = DEBUG_REGS_BASE | 0x230  # 0xFFB12230
TRISC_RESET_PC_OVERRIDE  = DEBUG_REGS_BASE | 0x234  # 0xFFB12234
NCRISC_RESET_PC          = DEBUG_REGS_BASE | 0x238  # 0xFFB12238
NCRISC_RESET_PC_OVERRIDE = DEBUG_REGS_BASE | 0x23C  # 0xFFB1223C

# -- per-RISC private data memory NOC addresses ----------------------------- #
# all cores see 0xFFB00000 as their own local RAM, but each maps to a
# different NOC address so the host can read it via TLB
PRIVATE_DATA_NOC_ADDR = {
  "brisc":  0xFFB14000,  # 8 KB
  "trisc0": 0xFFB18000,  # 4 KB
  "trisc1": 0xFFB1A000,  # 4 KB
  "trisc2": 0xFFB1C000,  # 4 KB
  "ncrisc": 0xFFB16000,  # 8 KB
}
PRIVATE_DATA_SIZE = {
  "brisc": 8192, "ncrisc": 8192,
  "trisc0": 4096, "trisc1": 4096, "trisc2": 4096,
}

# -- default reset PC (where each RISC starts executing) -------------------- #
DEFAULT_RESET_PC = {
  "brisc":  0x00000,
  "trisc0": 0x06000,
  "trisc1": 0x0A000,
  "trisc2": 0x0E000,
  "ncrisc": 0x12000,
}

# -- Tensix instruction encodings (for injection) -------------------------- #
# TT_OP(opcode, params) = (opcode << 24) | params
# all instructions stored little-endian on device

def tt_op(opcode: int, params: int) -> int:
  return (opcode << 24) | (params & 0x00FFFFFF)

def TT_SFPLOAD(lreg: int, fmt: int = 0, addr_mode: int = 0, dest_addr: int = 0) -> int:
  return tt_op(0x70, (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr)

def TT_SFPSTORE(lreg: int, fmt: int = 0, addr_mode: int = 0, dest_addr: int = 0) -> int:
  return tt_op(0x72, (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr)

def TT_STALLWAIT(stall_res: int, wait_res: int) -> int:
  return tt_op(0xA2, (stall_res << 15) | wait_res)

def TT_SETRWC(clear_ab: int, cr: int, d: int, b: int, a: int, mask: int) -> int:
  return tt_op(0x37, (clear_ab << 22) | (cr << 18) | (d << 14) | (b << 10) | (a << 6) | mask)

def TT_MOVDBGA2D(dest_32b_lo: int, src: int, addr_mode: int = 0, instr_mod: int = 0, dst: int = 0) -> int:
  return tt_op(0x09, (dest_32b_lo << 23) | (src << 17) | (addr_mode << 14) | (instr_mod << 12) | dst)

# stall/wait constants
STALL_SFPU  = 0x100  # stall SFPU
WAIT_SFPU   = 0x4000 # wait for SFPU complete
STALL_MATH  = 0x40
STALL_PACK  = 0x4

# SFPLOAD/SFPSTORE format modes (instr_mod0 / fmt field)
SFPU_FMT_DEFAULT       = 0
SFPU_FMT_FP16A         = 1
SFPU_FMT_FP16B         = 2
SFPU_FMT_FP32          = 3
SFPU_FMT_INT32         = 4
SFPU_FMT_INT8          = 5
SFPU_FMT_LO16          = 6
SFPU_FMT_HI16          = 7
SFPU_FMT_INT32_2S_COMP = 12
SFPU_FMT_INT8_2S_COMP  = 13

# LReg indices
LREG_COUNT     = 8   # mutable: LReg0..LReg7
LREG_CONST_0_8 = 8   # read-only 0.8373
LREG_CONST_0   = 9   # read-only 0.0
LREG_CONST_1   = 10  # read-only 1.0
# LReg 11-14: programmable constants (writable only via SFPCONFIG)
# LReg 15: read-only, lane i = i*2
# LReg 16: writable only by SFPLOADMACRO

# -- L1 layout (from blackhole-py hw.py) ----------------------------------- #
L1_SIZE       = 0x180000  # 1.5 MB
L1_GO_MSG     = 0x000370
L1_LAUNCH_MSG = 0x000070
L1_MAILBOX    = 0x000060
