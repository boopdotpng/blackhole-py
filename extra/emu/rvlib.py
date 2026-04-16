# rvlib.py — Standard library for RVIR firmware and kernels
import struct
from .dsl import *
from . import memory as M

# =============================================================================
# Constants — run protocol
# =============================================================================

RUN_SYNC_MSG_DONE   = 0x00
RUN_SYNC_MSG_GO     = 0x80
RUN_SYNC_MSG_LOAD   = 0x01
RUN_SYNC_MSG_INIT   = 0x40
RUN_SYNC_MSG_INIT_SYNC_REGISTERS = 0x03
RUN_SYNC_MSG_ALL_INIT = 0x40404040

RUN_MSG_DONE = 0x00
RUN_MSG_GO   = 0x80

# =============================================================================
# Constants — L1 layout
# =============================================================================

MAILBOX_BASE      = M.MAILBOX_BASE           # 0x60
SUBORDINATE_SYNC  = M.SUBORDINATE_SYNC       # 0x68  [ncrisc, t0, t1, t2]
LAUNCH_MSG_RD_PTR = M.LAUNCH_MSG_RD_PTR      # 0x6C
LAUNCH_MSG_RING   = M.LAUNCH_MSG_RING        # 0x70
GO_MESSAGES       = M.GO_MESSAGES            # 0x370
GO_SIGNAL         = GO_MESSAGES + 3          # 0x373  (byte: go_msg[0].signal)
GO_MESSAGE_INDEX  = M.GO_MESSAGE_INDEX       # 0x3A0
ZEROS_BASE        = M.ZEROS_BASE            # 0x3240
CORE_INFO_X       = 0x9A0                    # core_info.absolute_logical_x
CORE_INFO_Y       = 0x9A1                    # core_info.absolute_logical_y

# =============================================================================
# Constants — hardware MMIO
# =============================================================================

INSTRN_BUF_T0    = M.INSTRN_BUF_T0           # 0xFFE40000
PCBUF_BASE       = M.PCBUF_T0                # 0xFFE80000
PCBUF_DONE       = PCBUF_BASE + M.PCBUF_COPROC_DONE  # 0xFFE80004
REGFILE_BASE     = M.GPR_BASE                # 0xFFE00000
TENSIX_CFG_BASE  = M.TENSIX_CFG_BASE         # 0xFFEF0000

NOC0_BASE        = M.NOC0_BASE               # 0xFFB20000
NOC1_BASE        = M.NOC1_BASE               # 0xFFB30000
NOC0_ID          = NOC0_BASE + M.NIU_ID_LOGICAL   # 0xFFB20148
NOC1_ID          = NOC1_BASE + M.NIU_ID_LOGICAL   # 0xFFB30148
NOC0_CFG0        = NOC0_BASE + M.NIU_CFG_0        # 0xFFB20100
NOC1_CFG0        = NOC1_BASE + M.NIU_CFG_0        # 0xFFB30100

DEST_CG_CTRL     = M.DEST_CG_CTRL            # 0xFFB12240
TDMA_CLK_GATE_EN = M.TDMA_CLK_GATE_EN        # 0xFFB11024
SOFT_RESET_0     = M.SOFT_RESET_0            # 0xFFB121B0
TRISC_PC_OVR     = M.TRISC_RESET_PC_OVR      # 0xFFB12234
NCRISC_PC_OVR    = M.NCRISC_RESET_PC_OVR     # 0xFFB1223C
LDM_BASE         = M.LDM_BASE                # 0xFFB00000

IC_INVALIDATE    = TENSIX_CFG_BASE + 185 * 4  # 0xFFEF02E4
IC_ALL_MASK      = 0x1F

PRNG_SEED        = TENSIX_CFG_BASE + 0x2E8   # 0xFFEF02E8

CSR_CUSTOM       = 0x7C0

# =============================================================================
# Constants — subordinate sync byte addresses
# =============================================================================

NCRISC_RUN = SUBORDINATE_SYNC + 0  # 0x68
TRISC0_RUN = SUBORDINATE_SYNC + 1  # 0x69
TRISC1_RUN = SUBORDINATE_SYNC + 2  # 0x6A
TRISC2_RUN = SUBORDINATE_SYNC + 3  # 0x6B

# =============================================================================
# Constants — stream / circular buffer
# =============================================================================

STREAM_BASE           = M.STREAM_BASE         # 0xFFB40000
STREAM_STRIDE         = M.STREAM_STRIDE       # 0x1000
STREAM_TILES_ACKED    = M.STREAM_TILES_ACKED  # 0x020
STREAM_TILES_RECEIVED = M.STREAM_TILES_RECEIVED  # 0x028
NUM_CBS = 32  # firmware init_sync_registers zeroes streams 8..39

# =============================================================================
# Constants — launch_msg_t layout (matches dispatch.py _KernelConfigMsg)
# =============================================================================

LM_CONFIG_BASE     =  0   # kernel_config_base[TENSIX]      u32
LM_SEM_OFFSET      = 12   # sem_offset[0..2]                u16×3
LM_LOCAL_CB_OFF    = 18   # local_cb_offset                 u16
LM_REMOTE_CB_OFF   = 20   # remote_cb_offset                u16
LM_RTA_OFFSETS     = 22   # rta_offset[0..4] (u16,u16) each
LM_MODE            = 42   # dispatch mode                   u8
LM_TEXT_BRISC      = 44   # kernel_text_offset[DM0]         u32
LM_TEXT_NCRISC     = 48   # kernel_text_offset[DM1]         u32
LM_TEXT_TRISC0     = 52   # kernel_text_offset[MATH0]       u32
LM_TEXT_TRISC1     = 56   # kernel_text_offset[MATH0+1]     u32
LM_TEXT_TRISC2     = 60   # kernel_text_offset[MATH0+2]     u32
LM_LOCAL_CB_MASK   = 64   # local_cb_mask                   u32
LM_ENABLES         = 76   # enables bitmask                 u32
LM_SIZE            = 96   # total launch_msg_t size

EN_BRISC     = 1 << 0
EN_NCRISC    = 1 << 1
EN_TRISC0    = 1 << 2
EN_TRISC_ALL = (1 << 2) | (1 << 3) | (1 << 4)

# =============================================================================
# Constants — stack / GP / LDM scratch
# =============================================================================

GP         = 0xFFB007F0
BRISC_SP   = 0xFFB01FF0   # 8 KiB LDM
NCRISC_SP  = 0xFFB01FF0
TRISC_SP   = 0xFFB00FF0   # 4 KiB LDM

BRISC_SCRATCH  = M.BRISC_LDM_SCRATCH    # 0x086B0
NCRISC_SCRATCH = M.NCRISC_LDM_SCRATCH   # 0x0A6B0
TRISC0_SCRATCH = M.TRISC0_LDM_SCRATCH   # 0x0C6B0
TRISC1_SCRATCH = M.TRISC1_LDM_SCRATCH   # 0x0D6B0
TRISC2_SCRATCH = M.TRISC2_LDM_SCRATCH   # 0x0E6B0


# =============================================================================
# Boot / CRT helpers
# =============================================================================

def emit_start(k, sp_top):
    k.label("_start")
    k.li(gp, GP)
    k.li(sp, sp_top)
    k.call("main")
    k.label("exit")
    k.j("exit")


def emit_configure_csr(k):
    k.li(t1, 2)
    k.emit(CSRRS(zero, t1, CSR_CUSTOM))
    k.li(t1, 1 << 18)
    k.emit(FENCE())
    k.emit(CSRRS(zero, t1, CSR_CUSTOM))
    k.li(t1, 2)
    k.emit(CSRRC(zero, t1, CSR_CUSTOM))
    k.emit(FENCE())
    k.emit(FENCE())
    k.li(t1, 8)
    k.emit(CSRRS(zero, t1, CSR_CUSTOM))


def emit_do_crt1(k, scratch_base, data_size, bss_size):
    if data_size > 0:
        k.li(a0, scratch_base)
        k.li(a1, LDM_BASE)
        k.li(a2, data_size // 4)
        with k.countdown(a2, count=None):
            k.lw(t0, a0, 0)
            k.sw(a1, t0, 0)
            k.emit(ADDI(a0, a0, 4))
            k.emit(ADDI(a1, a1, 4))
    if bss_size > 0:
        k.li(a1, LDM_BASE + data_size)
        k.li(a2, bss_size // 4)
        with k.countdown(a2, count=None):
            k.sw(a1, zero, 0)
            k.emit(ADDI(a1, a1, 4))


def pack_firmware(k, text_base, ldm_data=b'', bss_size=0):
    words = k.assemble()
    text_bytes = b''.join(struct.pack('<I', w) for w in words)
    segments = [(text_base, text_bytes)]
    if ldm_data or bss_size > 0:
        segments.append((LDM_BASE, ldm_data + b'\x00' * bss_size))
    return {'segments': segments, 'text_base': text_base}


# =============================================================================
# Core info / NOC
# =============================================================================

def read_core_info(k, x_reg, y_reg, tmp=t0):
    k.li(tmp, CORE_INFO_X)
    k.lbu(x_reg, tmp, 0)
    k.lbu(y_reg, tmp, 1)


def read_noc_ids(k, noc0_reg, noc1_reg, tmp=t0):
    k.li(tmp, NOC0_ID)
    k.lw(noc0_reg, tmp, 0)
    k.li(tmp, NOC1_ID)
    k.lw(noc1_reg, tmp, 0)


def noc_cfg_enable(k, noc_cfg_base, base_reg=t1, tmp=t0):
    k.li(base_reg, noc_cfg_base)
    k.lw(tmp, base_reg, 0)
    k.emit(ORI(tmp, tmp, 1))
    k.sw(base_reg, tmp, 0)
    k.lw(tmp, base_reg, 4)
    k.emit(ORI(tmp, tmp, 1))
    k.sw(base_reg, tmp, 4)


# =============================================================================
# Polling / sync primitives
# =============================================================================

def poll_byte_eq(k, addr, value, tmp0=t0, tmp1=t1):
    with k.while_true() as L:
        k.lbu(tmp0, zero, addr)
        k.li(tmp1, value)
        k.beq(tmp0, tmp1, L.brk)
        k.emit(FENCE())


def poll_byte_neq(k, addr, value, tmp0=t0, tmp1=t1):
    with k.while_true() as L:
        k.lbu(tmp0, zero, addr)
        k.li(tmp1, value)
        k.bne(tmp0, tmp1, L.brk)
        k.emit(FENCE())


def poll_word_zero(k, addr, tmp=t0):
    with k.while_true() as L:
        k.lw(tmp, zero, addr)
        k.beqz(tmp, L.brk)
        k.emit(FENCE())


def signal_done(k, run_addr):
    k.emit(SB(zero, zero, run_addr))


def signal_go(k, run_addr, tmp=t0):
    k.li(tmp, RUN_SYNC_MSG_GO)
    k.emit(SB(zero, tmp, run_addr))


def wait_for_go(k, run_addr, tmp0=t0, tmp1=t1):
    poll_byte_eq(k, run_addr, RUN_SYNC_MSG_GO, tmp0, tmp1)


def wait_subordinates_done(k, tmp=t0):
    poll_word_zero(k, SUBORDINATE_SYNC, tmp)


# =============================================================================
# Instruction cache
# =============================================================================

def invalidate_icache(k, tmp0=t0, tmp1=t1):
    k.li(tmp0, IC_INVALIDATE)
    k.li(tmp1, IC_ALL_MASK)
    k.sw(tmp0, tmp1, 0)


# =============================================================================
# Launch message / kernel dispatch
# =============================================================================

def read_launch_msg(k, ptr_reg, msg_reg, config_reg, tmp=t0):
    k.lw(ptr_reg, zero, LAUNCH_MSG_RD_PTR)
    k.li(tmp, LM_SIZE)
    k.emit(MUL(msg_reg, ptr_reg, tmp))
    k.emit(ADDI(msg_reg, msg_reg, LAUNCH_MSG_RING))
    k.lw(config_reg, msg_reg, LM_CONFIG_BASE)


def call_kernel(k, msg_reg, config_reg, text_field_offset, tmp=t0):
    k.lw(tmp, msg_reg, text_field_offset)
    k.emit(ADD(tmp, tmp, config_reg))
    k.emit(JALR(ra, tmp, 0))


# =============================================================================
# Tensix coprocessor control
# =============================================================================

def tensix_sync(k, tmp0=None, tmp1=t0):
    base = tmp0 if tmp0 is not None else tmp1
    k.li(base, PCBUF_DONE)
    k.sw(base, zero, 0)
    k.lw(tmp1, base, 0)


def zero_regfile(k, addr_reg=a0, count_reg=a1):
    k.li(addr_reg, REGFILE_BASE)
    k.li(count_reg, 64)
    with k.countdown(count_reg, count=None):
        k.sw(addr_reg, zero, 0)
        k.emit(ADDI(addr_reg, addr_reg, 4))


def seed_prng(k, cycles=600, tmp=t0, count_reg=a0):
    k.li(tmp, PRNG_SEED)
    k.sw(tmp, zero, 0)
    k.li(count_reg, cycles // 4)
    with k.countdown(count_reg, count=None):
        k.emit(NOP())


def init_sync_registers(k, addr_reg=a0, end_reg=a1, stride_reg=a2):
    k.li(addr_reg, STREAM_BASE + 8 * STREAM_STRIDE + STREAM_TILES_RECEIVED)
    k.li(end_reg, STREAM_BASE + (8 + NUM_CBS) * STREAM_STRIDE + STREAM_TILES_RECEIVED)
    k.li(stride_reg, STREAM_STRIDE)
    with k.while_true() as L:
        k.sw(addr_reg, zero, 0)
        k.sw(addr_reg, zero, STREAM_TILES_ACKED - STREAM_TILES_RECEIVED)
        k.emit(ADD(addr_reg, addr_reg, stride_reg))
        k.beq(addr_reg, end_reg, L.brk)


def tensix_init(k, buf_reg=t1, tmp=t0):
    k.li(buf_reg, INSTRN_BUF_T0)

    # ZEROACC: clear all dest accumulators
    k.li(tmp, int(TT_ZEROACC(clear_mode=0x1F, use_32_bit_mode=0,
                              clear_zero_flags=0, addr_mode=0, where=0)))
    k.sw(buf_reg, tmp, 0)

    # SFPENCC: enable per-lane condition codes
    k.li(tmp, int(TT_SFPENCC(imm12_math=0, lreg_c=0,
                              lreg_dest=0, instr_mod1=0)))
    k.sw(buf_reg, tmp, 0)

    # SEMINIT: all 8 semaphores, max=15, init=0
    k.li(tmp, int(TT_SEMINIT(max_value=15, init_value=0, sem_sel=0xFF)))
    k.sw(buf_reg, tmp, 0)


# =============================================================================
# Memory utilities
# =============================================================================

def memzero(k, addr, nbytes, addr_reg=a0, count_reg=a1):
    assert nbytes % 4 == 0, "nbytes must be word-aligned"
    k.li(addr_reg, addr)
    k.li(count_reg, nbytes // 4)
    with k.countdown(count_reg, count=None):
        k.sw(addr_reg, zero, 0)
        k.emit(ADDI(addr_reg, addr_reg, 4))


def memcopy(k, src, dst, nbytes, src_reg=a0, dst_reg=a1, count_reg=a2, tmp=t0):
    assert nbytes % 4 == 0, "nbytes must be word-aligned"
    k.li(src_reg, src)
    k.li(dst_reg, dst)
    k.li(count_reg, nbytes // 4)
    with k.countdown(count_reg, count=None):
        k.lw(tmp, src_reg, 0)
        k.sw(dst_reg, tmp, 0)
        k.emit(ADDI(src_reg, src_reg, 4))
        k.emit(ADDI(dst_reg, dst_reg, 4))


# =============================================================================
# Device setup helpers
# =============================================================================

def disable_dest_clock_gating(k, tmp=t0):
    k.li(tmp, DEST_CG_CTRL)
    k.sw(tmp, zero, 0)


def enable_tdma_clock_gating(k, tmp0=t0, tmp1=t1):
    k.li(tmp0, TDMA_CLK_GATE_EN)
    k.li(tmp1, 0x3F)
    k.sw(tmp0, tmp1, 0)


def set_reset_pc_overrides(k, tmp0=t0, tmp1=t1):
    k.li(tmp0, TRISC_PC_OVR)
    k.li(tmp1, 0b111)
    k.sw(tmp0, tmp1, 0)
    k.li(tmp0, NCRISC_PC_OVR)
    k.li(tmp1, 1)
    k.sw(tmp0, tmp1, 0)


def release_subordinates(k, tmp=t0):
    k.li(tmp, SOFT_RESET_0)
    k.sw(tmp, zero, 0)
