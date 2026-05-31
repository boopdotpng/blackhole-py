from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import KernelBase
from dsl import Reg, a0, a1, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, t5, t6, zero
from ttk.noc import Noc


class CqKernel(KernelBase, Noc):
  pass

L1_ALIGN = 16
KERNEL_CONFIG_BASE = 0x86B0
CQ_SEM_BASE = KERNEL_CONFIG_BASE + L1_ALIGN

NOC_REGS_START_ADDR = 0xFFB20000
NOC_STATUS_BASE = 0xFFB20200
NOC_CMD_BUF_OFFSET_BIT = 11
NOC_INSTANCE_OFFSET_BIT = 16
NOC_TARG_ADDR_LO = NOC_REGS_START_ADDR + 0x00
NOC_TARG_ADDR_MID = NOC_REGS_START_ADDR + 0x04
NOC_TARG_ADDR_COORDINATE = NOC_REGS_START_ADDR + 0x08
NOC_RET_ADDR_LO = NOC_REGS_START_ADDR + 0x0C
NOC_RET_ADDR_MID = NOC_REGS_START_ADDR + 0x10
NOC_RET_ADDR_COORDINATE = NOC_REGS_START_ADDR + 0x14
NOC_CTRL = NOC_REGS_START_ADDR + 0x1C
NOC_AT_LEN_BE = NOC_REGS_START_ADDR + 0x20
NOC_AT_LEN_BE_1 = NOC_REGS_START_ADDR + 0x24
NOC_AT_DATA = NOC_REGS_START_ADDR + 0x28
NOC_CMD_CTRL = NOC_REGS_START_ADDR + 0x40
NOC_STATUS_READY = 0
NOC_CTRL_SEND_REQ = 1
NOC_PCIE_MID = 0x10000000
NOC_COORD_MASK = 0xFFFFFF
NOC_CMD_CPY = 0
NOC_CMD_AT = 1
NOC_CMD_WR = 1 << 1
NOC_CMD_WR_INLINE = 1 << 3
NOC_CMD_RESP_MARKED = 1 << 4
NOC_CMD_BRCST_PACKET = 1 << 5
NOC_CMD_VC_LINKED = 1 << 6
NOC_CMD_VC_STATIC = 1 << 7
NOC_CMD_PATH_RESERVE = 1 << 8
NOC_CMD_STATIC_VC_1 = 1 << 13
NOC_CMD_STATIC_VC_5 = 5 << 13
NOC_CMD_RD_FIELD = NOC_CMD_CPY | NOC_CMD_RESP_MARKED | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_CMD_WR_FIELD = NOC_CMD_CPY | NOC_CMD_WR | NOC_CMD_RESP_MARKED | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_CMD_WR_POSTED_FIELD = NOC_CMD_CPY | NOC_CMD_WR | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_CMD_WR_MCAST_UNLINK_FIELD = (
  NOC_CMD_CPY
  | NOC_CMD_WR
  | NOC_CMD_RESP_MARKED
  | NOC_CMD_VC_STATIC
  | NOC_CMD_STATIC_VC_5
  | NOC_CMD_BRCST_PACKET
  | NOC_CMD_PATH_RESERVE
)
NOC_CMD_WR_MCAST_LINKED_FIELD = NOC_CMD_WR_MCAST_UNLINK_FIELD | NOC_CMD_VC_LINKED
NOC_CMD_INLINE_FIELD = NOC_CMD_WR_FIELD | NOC_CMD_WR_INLINE
NOC_CMD_AT_INC_FIELD = NOC_CMD_AT | NOC_CMD_RESP_MARKED | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_AT_INS_INCR_GET = 0x1
NOC_AT_INS_SHIFT = 12
NOC_AT_WRAP_SHIFT = 2
NOC_AT_INCR_GET = (NOC_AT_INS_INCR_GET << NOC_AT_INS_SHIFT) | (31 << NOC_AT_WRAP_SHIFT)
NOC_MAX_BURST_SIZE = 16 * 1024

NIU_MST_WR_ACK_RECEIVED = 0x04
NIU_MST_ATOMIC_RESP_RECEIVED = 0x00
NIU_MST_RD_RESP_RECEIVED = 0x08
NIU_MST_NONPOSTED_WR_REQ_SENT = 0x28

STREAM_BASE = 0xFFB40000
STREAM_STRIDE = 0x1000
STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX = 10
STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_REG_INDEX = 270
STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX = 297
REMOTE_DEST_BUF_WORDS_FREE_INC = 6

PREFETCH_Q_RD_PTR = 0x196C0
PREFETCH_Q_PCIE_RD = 0x196C4
PREFETCH_Q_BASE = 0x19840
PREFETCH_Q_SIZE = 0xBFC
PREFETCH_Q_END = PREFETCH_Q_BASE + PREFETCH_Q_SIZE
PREFETCH_Q_ENTRY_SIZE = 4
HOST_ISSUE_BASE = 0x40000100
DISPATCH_CB_BASE = 0x1A000
DISPATCH_CB_PAGES = 128
DISPATCH_CB_PAGE = 4096
DISPATCH_CB_END = DISPATCH_CB_BASE + DISPATCH_CB_PAGES * DISPATCH_CB_PAGE
CMDDAT_Q_BASE = DISPATCH_CB_END
CMDDAT_Q_SIZE = 64 * 1024
HOST_ISSUE_SIZE = 64 * 1024 * 1024
DISPATCH_S_CB_BASE = 0x9A000
DISPATCH_S_CB_PAGE = 256
DISPATCH_S_CB_END = DISPATCH_S_CB_BASE + 32 * 1024
# Current blackhole-py-old default target is p100:
# prefetch=(14, 2), dispatch=(14, 3).
PREFETCH_NOC_XY = (2 << 6) | 14
DISPATCH_NOC_XY = (3 << 6) | 14
PCIE_NOC_XY = (1 << 24) | (24 << 6) | 19

CQ_PREFETCH_CMD_RELAY_INLINE = 5
CQ_PREFETCH_CMD_RELAY_INLINE_NOFLUSH = 6
CQ_PREFETCH_CMD_EXEC_BUF_END = 8
CQ_PREFETCH_CMD_STALL = 9
CQ_PREFETCH_CMD_TERMINATE = 11
CQ_DISPATCH_CMD_WRITE_LINEAR_H_HOST = 3
CQ_DISPATCH_CMD_WRITE_PACKED = 5
CQ_DISPATCH_CMD_WRITE_PACKED_LARGE = 6
CQ_DISPATCH_CMD_WAIT = 7
CQ_DISPATCH_CMD_TERMINATE = 13
CQ_DISPATCH_CMD_SEND_GO_SIGNAL = 14
CQ_DISPATCH_SET_GO_SIGNAL_NOC_DATA = 17
CQ_DISPATCH_CMD_TIMESTAMP = 18
CQ_WAIT_BARRIER = 0x01
CQ_WAIT_WAIT_STREAM = 0x08
CQ_WAIT_CLEAR_STREAM = 0x10
CQ_PACKED_NO_STRIDE = 0x02
CQ_PACKED_LARGE_UNLINK = 0x01
GO_NO_MULTICAST = 0xFF

COMPLETION_WR_PTR = 0x196D0
COMPLETION_RD_PTR = 0x196E0
COMPLETION_BASE = 0x44000100
COMPLETION_SIZE = 32 * 1024 * 1024
HOST_COMPLETION_WR_PTR_OFF = 0x40000000 + 128
RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0
RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8

GO_SIGNAL_NOC_DATA = 0xB0000
CQ_DEBUG = 0x19000
DISPATCH_RELEASE_PENDING = CQ_DEBUG + 0x80
DISPATCH_PAGE_CURSOR = CQ_DEBUG + 0x84
DISPATCH_RELEASE_VALUE = CQ_DEBUG + 0x90
PREFETCH_PCIE_BASE = CQ_DEBUG + 0xA0
PREFETCH_PCIE_END = CQ_DEBUG + 0xA4
GO_SIGNAL_VALUE = CQ_DEBUG + 0x100

def round_up_reg(fw: CqKernel, reg: Reg, align: int, *, tmp: Reg = t0):
  fw.li(tmp, align - 1)
  fw.add(reg, reg, tmp)
  fw.li(tmp, ~(align - 1))
  fw.and_(reg, reg, tmp)
  return fw

def build_prefetch() -> CqKernel:
  fw = CqKernel()
  fw.setup_stack(0xFFB01FF0)
  fw.write32(CQ_DEBUG, 0xC1010001)
  fw.write32(CQ_SEM_BASE, DISPATCH_CB_PAGES)
  fw.li(s0, PREFETCH_Q_BASE)     # queue read pointer
  fw.read32(s1, PREFETCH_Q_PCIE_RD)  # host PCIE read pointer
  fw.write32(PREFETCH_PCIE_BASE, s1, tmp_addr=t0, tmp_val=t1)
  fw.li(t0, HOST_ISSUE_SIZE)
  fw.add(t0, s1, t0)
  fw.write32(PREFETCH_PCIE_END, t0, tmp_addr=t1, tmp_val=t2)
  fw.li(s2, DISPATCH_CB_BASE)    # dispatch CB write pointer
  fw.li(s8, 0)                    # local page-credit adjustment
  fw.read32(s4, NOC_STATUS_BASE + NIU_MST_RD_RESP_RECEIVED)
  fw.read32(s5, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED)
  fw.read32(s7, NOC_STATUS_BASE + NIU_MST_ATOMIC_RESP_RECEIVED)

  fw.label("prefetch_loop")
  fw.write32(CQ_DEBUG, 0xC1010002)
  fw.lw(t0, s0, 0)
  fw.beq(t0, zero, "prefetch_loop")
  fw.li(t1, 0x7FFF)
  fw.and_(t0, t0, t1)
  fw.beq(t0, zero, "prefetch_loop")
  fw.slli(t0, t0, 4)             # byte count
  fw.li(t1, CMDDAT_Q_BASE)
  fw.write32(CQ_DEBUG + 4, t0, tmp_addr=t2, tmp_val=t3)
  fw.mv(s9, s1)                  # host read cursor
  fw.mv(s10, t1)                 # local cmddat write cursor
  fw.mv(s11, t0)                 # bytes remaining
  fw.label("prefetch_read_loop")
  fw.beq(s11, zero, "prefetch_read_done")
  fw.li(t4, NOC_MAX_BURST_SIZE)
  fw.bltu(t4, s11, "prefetch_read_full_burst")
  fw.mv(t5, s11)
  fw.j("prefetch_read_issue")
  fw.label("prefetch_read_full_burst")
  fw.mv(t5, t4)
  fw.label("prefetch_read_issue")
  fw.noc_read(0, 1, s9, NOC_PCIE_MID, PCIE_NOC_XY, s10, t5, ret_coord=PREFETCH_NOC_XY, a=t2, v=t3)
  fw.addi(s4, s4, 1)
  fw.add(s9, s9, t5)
  fw.add(s10, s10, t5)
  fw.sub(s11, s11, t5)
  fw.j("prefetch_read_loop")
  fw.label("prefetch_read_done")
  fw.li(t2, NOC_STATUS_BASE + NIU_MST_RD_RESP_RECEIVED)
  fw.label("prefetch_read_barrier")
  fw.lw(t3, t2, 0)
  fw.bltu(t3, s4, "prefetch_read_barrier")
  fw.write32(CQ_DEBUG, 0xC1010003, tmp_addr=t2, tmp_val=t3)
  fw.sw(zero, s0, 0)
  fw.write32(PREFETCH_Q_RD_PTR, s0, tmp_addr=t2, tmp_val=t3)
  fw.add(s1, s1, t0)
  fw.read32(t2, PREFETCH_PCIE_END, tmp_addr=t3)
  fw.bltu(s1, t2, "prefetch_no_pcie_wrap")
  fw.read32(s1, PREFETCH_PCIE_BASE, tmp_addr=t3)
  fw.label("prefetch_no_pcie_wrap")
  fw.write32(PREFETCH_Q_PCIE_RD, s1, tmp_addr=t2, tmp_val=t3)
  fw.addi(s0, s0, PREFETCH_Q_ENTRY_SIZE)
  fw.li(t2, PREFETCH_Q_END)
  fw.bne(s0, t2, "prefetch_no_q_wrap")
  fw.li(s0, PREFETCH_Q_BASE)
  fw.label("prefetch_no_q_wrap")

  fw.li(t1, CMDDAT_Q_BASE)
  fw.lbu(t2, t1, 0)
  fw.write32(CQ_DEBUG + 8, t2, tmp_addr=t3, tmp_val=t4)
  fw.li(t3, CQ_PREFETCH_CMD_RELAY_INLINE)
  fw.beq(t2, t3, "prefetch_relay_inline")
  fw.li(t3, CQ_PREFETCH_CMD_RELAY_INLINE_NOFLUSH)
  fw.beq(t2, t3, "prefetch_relay_inline")
  fw.li(t3, CQ_PREFETCH_CMD_EXEC_BUF_END)
  fw.beq(t2, t3, "prefetch_relay_inline")
  fw.li(t3, CQ_PREFETCH_CMD_STALL)
  fw.beq(t2, t3, "prefetch_loop")
  fw.li(t3, CQ_PREFETCH_CMD_TERMINATE)
  fw.beq(t2, t3, "prefetch_done")
  fw.j("prefetch_bad_cmd")
  fw.label("prefetch_relay_inline")
  fw.lw(t0, t1, 4)               # payload length
  fw.mv(s6, t0)
  fw.addi(t1, t1, 16)            # payload source
  fw.li(t2, DISPATCH_CB_PAGE - 1)
  fw.add(t2, t0, t2)
  fw.srli(t2, t2, 12)            # pages
  fw.mv(s3, t2)
  fw.write32(CQ_DEBUG + 12, s3, tmp_addr=t2, tmp_val=t3)
  # acquire_local_pages
  fw.li(t3, CQ_SEM_BASE)
  sem_wait = fw._new_label("sem_wait")
  fw.label(sem_wait)
  fw.lw(t0, t3, 0)
  fw.add(t0, t0, s8)
  fw.bltu(t0, s3, sem_wait)
  fw.sub(s8, s8, s3)
  fw.write32(CQ_DEBUG, 0xC1010004, tmp_addr=t2, tmp_val=t3)
  fw.write32(CQ_DEBUG + 16, s2, tmp_addr=t2, tmp_val=t3)
  fw.write32(CQ_DEBUG, 0xC1010005, tmp_addr=t2, tmp_val=t3)
  fw.mv(s9, t1)                  # local cmddat read cursor
  fw.mv(s10, s2)                 # dispatch cb write cursor
  fw.mv(s11, s6)                 # bytes remaining
  fw.label("prefetch_write_loop")
  fw.beq(s11, zero, "prefetch_write_done")
  fw.li(t4, NOC_MAX_BURST_SIZE)
  fw.bltu(t4, s11, "prefetch_write_full_burst")
  fw.mv(t0, s11)
  fw.j("prefetch_write_size_ready")
  fw.label("prefetch_write_full_burst")
  fw.mv(t0, t4)
  fw.label("prefetch_write_size_ready")
  fw.li(t4, DISPATCH_CB_END)
  fw.sub(t4, t4, s10)
  fw.bltu(t4, t0, "prefetch_write_trim_to_end")
  fw.j("prefetch_write_issue")
  fw.label("prefetch_write_trim_to_end")
  fw.mv(t0, t4)
  fw.label("prefetch_write_issue")
  fw.noc_write(0, 0, s9, s10, 0, DISPATCH_NOC_XY, t0, a=t2, v=t3)
  fw.addi(s5, s5, 1)
  fw.noc_wait_write_acks(0, s5, addr=t2, val=t3)
  fw.add(s9, s9, t0)
  fw.add(s10, s10, t0)
  fw.sub(s11, s11, t0)
  fw.li(t4, DISPATCH_CB_END)
  fw.bne(s10, t4, "prefetch_write_no_wrap")
  fw.li(s10, DISPATCH_CB_BASE)
  fw.label("prefetch_write_no_wrap")
  fw.j("prefetch_write_loop")
  fw.label("prefetch_write_done")
  fw.write32(CQ_DEBUG, 0xC1010006, tmp_addr=t2, tmp_val=t3)
  fw.mv(t0, s3)
  fw.slli(t0, t0, 12)
  fw.add(s2, s2, t0)
  fw.li(t1, DISPATCH_CB_END)
  fw.bltu(s2, t1, "prefetch_no_cb_wrap")
  fw.li(t4, DISPATCH_CB_END - DISPATCH_CB_BASE)
  fw.sub(s2, s2, t4)
  fw.label("prefetch_no_cb_wrap")
  fw.li(t1, CQ_SEM_BASE)
  fw.write32(CQ_DEBUG, 0xC1010007, tmp_addr=t2, tmp_val=t3)
  fw.noc_atomic_inc(0, 3, t1, DISPATCH_NOC_XY, s3, PREFETCH_NOC_XY, a=t2, v=t3)
  fw.addi(s7, s7, 1)
  fw.noc_wait_atomic_responses(0, s7, addr=t2, val=t3)
  fw.write32(CQ_DEBUG, 0xC1010008, tmp_addr=t2, tmp_val=t3)
  fw.j("prefetch_loop")
  fw.label("prefetch_bad_cmd")
  fw.write32(CQ_DEBUG, 0xC10100EE, tmp_addr=t2, tmp_val=t3)
  fw.j("prefetch_bad_cmd")
  fw.label("prefetch_done")
  fw.write32(CQ_DEBUG, 0xC10100FF, tmp_addr=t2, tmp_val=t3)
  fw.j("prefetch_done")
  return fw

def build_dispatch() -> CqKernel:
  fw = CqKernel()
  fw.setup_stack(0xFFB01FF0)
  fw.write32(CQ_DEBUG, 0xC1D10001)
  fw.li(s0, DISPATCH_CB_BASE)  # cmd ptr
  fw.read32(s1, COMPLETION_WR_PTR)  # completion wr ptr in 16B units
  fw.li(s2, 0)  # completion toggle
  fw.read32(s6, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED + (1 << NOC_INSTANCE_OFFSET_BIT))
  fw.write32(DISPATCH_RELEASE_PENDING, 0)
  fw.write32(DISPATCH_PAGE_CURSOR, 0)
  fw.write32(DISPATCH_RELEASE_VALUE, DISPATCH_CB_PAGES)

  fw.label("dispatch_loop")
  fw.write32(CQ_DEBUG, 0xC1D10002)
  fw.li(t0, CQ_SEM_BASE)
  fw.label("dispatch_wait_page")
  fw.fence()
  fw.lw(t1, t0, 0)
  fw.write32(CQ_DEBUG + 20, t1, tmp_addr=t2, tmp_val=t3)
  fw.read32(t2, DISPATCH_PAGE_CURSOR, tmp_addr=t3)
  fw.beq(t1, t2, "dispatch_wait_page")
  fw.addi(t2, t2, 1)
  fw.write32(DISPATCH_PAGE_CURSOR, t2, tmp_addr=t3, tmp_val=t4)
  fw.write32(CQ_DEBUG + 24, s0, tmp_addr=t1, tmp_val=t2)
  fw.mv(s9, s0)          # page-aligned start of the current dispatch record
  fw.lbu(t0, s0, 0)
  fw.write32(CQ_DEBUG + 4, t0, tmp_addr=t1, tmp_val=t2)
  fw.li(t1, CQ_DISPATCH_CMD_WRITE_PACKED_LARGE)
  fw.beq(t0, t1, "cmd_packed_large")
  fw.li(t1, CQ_DISPATCH_CMD_WRITE_PACKED)
  fw.beq(t0, t1, "cmd_packed")
  fw.li(t1, CQ_DISPATCH_CMD_WAIT)
  fw.beq(t0, t1, "cmd_wait")
  fw.li(t1, CQ_DISPATCH_SET_GO_SIGNAL_NOC_DATA)
  fw.beq(t0, t1, "cmd_set_go")
  fw.li(t1, CQ_DISPATCH_CMD_SEND_GO_SIGNAL)
  fw.beq(t0, t1, "cmd_go")
  fw.li(t1, CQ_DISPATCH_CMD_WRITE_LINEAR_H_HOST)
  fw.beq(t0, t1, "cmd_host")
  fw.li(t1, CQ_DISPATCH_CMD_TIMESTAMP)
  fw.beq(t0, t1, "cmd_timestamp")
  fw.li(t1, CQ_DISPATCH_CMD_TERMINATE)
  fw.beq(t0, t1, "dispatch_done")
  fw.j("advance_page")

  fw.label("cmd_packed_large")
  fw.write32(CQ_DEBUG, 0xC1D10600)
  fw.lbu(s4, s0, 1)      # global flags
  fw.andi(s4, s4, CQ_PACKED_NO_STRIDE)
  fw.lhu(s3, s0, 2)      # remaining subcmd count
  fw.addi(s5, s0, 16)    # subcmd ptr
  fw.mv(t3, s5)
  fw.li(t4, 12)
  fw.mul(t4, s3, t4)
  fw.add(t3, t3, t4)
  round_up_reg(fw, t3, L1_ALIGN, tmp=t4)  # data ptr
  fw.mv(a0, t3)           # shared data ptr for NO_STRIDE records
  fw.lhu(a1, s5, 8)
  fw.addi(a1, a1, 1)
  fw.add(a1, a1, a0)
  round_up_reg(fw, a1, L1_ALIGN, tmp=t4)  # shared record end ptr
  fw.li(s8, 1)           # must barrier before a fresh multicast path reservation
  fw.label("pl_loop")
  fw.beq(s3, zero, "pl_done")
  fw.write32(CQ_DEBUG, 0xC1D10601)
  fw.lw(t4, s5, 0)       # noc xy
  fw.write32(CQ_DEBUG + 8, t4, tmp_addr=t0, tmp_val=t2)
  fw.lw(t5, s5, 4)       # addr
  fw.write32(CQ_DEBUG + 12, t5, tmp_addr=t0, tmp_val=t2)
  fw.lhu(t1, s5, 8)      # len-1
  fw.addi(t1, t1, 1)
  fw.write32(CQ_DEBUG + 16, t1, tmp_addr=t0, tmp_val=t2)
  fw.lbu(s7, s5, 10)     # num destinations
  fw.lbu(s11, s5, 11)    # flags
  fw.andi(s11, s11, CQ_PACKED_LARGE_UNLINK)
  fw.write32(CQ_DEBUG, 0xC1D10602, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG, 0xC1D10620, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 40, s11, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 44, s8, tmp_addr=t0, tmp_val=t2)
  fw.mv(s10, t1)         # bytes remaining for this subcommand
  fw.label("pl_burst_loop")
  fw.write32(CQ_DEBUG, 0xC1D10621, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 32, s10, tmp_addr=t0, tmp_val=t2)
  fw.beq(s10, zero, "pl_subcmd_done")
  fw.li(t6, NOC_MAX_BURST_SIZE)
  fw.bltu(t6, s10, "pl_full_burst")
  fw.mv(t1, s10)
  # Blackhole can hang when reserving multicast paths back-to-back. Keep the
  # Python dispatcher conservative: each multicast is unlinked, and every
  # multicast after the first waits for prior writes to finish path teardown.
  fw.beq(s8, zero, "pl_single_path_ready")
  fw.noc_write_barrier(1, s6, addr=t0, val=t2)
  fw.label("pl_single_path_ready")
  fw.write32(CQ_DEBUG, 0xC1D10622, tmp_addr=t0, tmp_val=t2)
  fw.noc_write(1, 0, t3, t5, 0, t4, t1, mcast=True, mcast_linked=False, num_dests=s7, a=t0, v=t2)
  fw.j("pl_burst_sent")
  fw.label("pl_full_burst")
  fw.write32(CQ_DEBUG, 0xC1D10624, tmp_addr=t0, tmp_val=t2)
  fw.beq(s8, zero, "pl_full_path_ready")
  fw.noc_write_barrier(1, s6, addr=t0, val=t2)
  fw.label("pl_full_path_ready")
  fw.mv(t1, t6)
  fw.noc_write(1, 0, t3, t5, 0, t4, t1, mcast=True, mcast_linked=False, num_dests=s7, a=t0, v=t2)
  fw.label("pl_burst_sent")
  fw.li(s8, 1)
  fw.add(s6, s6, s7)
  fw.write32(CQ_DEBUG + 36, t1, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 48, s6, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG, 0xC1D10603, tmp_addr=t0, tmp_val=t2)
  fw.noc_wait_cmd_ready(1, 0, addr=t0, val=t2)
  fw.write32(CQ_DEBUG, 0xC1D10604, tmp_addr=t0, tmp_val=t2)
  fw.add(t3, t3, t1)
  fw.add(t5, t5, t1)
  fw.write32(CQ_DEBUG, 0xC1D10625, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 52, t3, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 56, t5, tmp_addr=t0, tmp_val=t2)
  fw.sub(s10, s10, t1)
  fw.write32(CQ_DEBUG, 0xC1D10626, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 32, s10, tmp_addr=t0, tmp_val=t2)
  fw.j("pl_burst_loop")
  fw.label("pl_subcmd_done")
  fw.write32(CQ_DEBUG, 0xC1D10627, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 40, s11, tmp_addr=t0, tmp_val=t2)
  fw.beq(s11, zero, "pl_keep_linked")
  fw.li(s8, 1)
  fw.write32(CQ_DEBUG, 0xC1D10628, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 44, s8, tmp_addr=t0, tmp_val=t2)
  fw.j("pl_round_subcmd")
  fw.label("pl_keep_linked")
  fw.li(s8, 0)
  fw.write32(CQ_DEBUG, 0xC1D10629, tmp_addr=t0, tmp_val=t2)
  fw.write32(CQ_DEBUG + 44, s8, tmp_addr=t0, tmp_val=t2)
  fw.label("pl_round_subcmd")
  fw.write32(CQ_DEBUG, 0xC1D1062A, tmp_addr=t0, tmp_val=t2)
  # CQWritePackedLarge currently emits L1_ALIGN alignment.
  round_up_reg(fw, t3, L1_ALIGN, tmp=t4)
  fw.beq(s4, zero, "pl_data_ptr_ready")
  fw.mv(t3, a0)
  fw.label("pl_data_ptr_ready")
  fw.write32(CQ_DEBUG + 52, t3, tmp_addr=t0, tmp_val=t2)
  fw.addi(s5, s5, 12)
  fw.addi(s3, s3, -1)
  fw.write32(CQ_DEBUG + 60, s3, tmp_addr=t0, tmp_val=t2)
  fw.j("pl_loop")
  fw.label("pl_done")
  fw.beq(s4, zero, "pl_done_ptr_ready")
  fw.mv(t3, a1)
  fw.label("pl_done_ptr_ready")
  fw.mv(s0, t3)
  fw.j("release_and_continue")

  fw.label("cmd_packed")
  fw.lbu(s8, s0, 1)      # flags
  fw.lhu(t1, s0, 2)      # count
  fw.lhu(t2, s0, 6)      # size
  fw.lw(t3, s0, 8)       # dst addr
  fw.addi(t4, s0, 16)    # noc list
  fw.mv(t5, t4)
  fw.slli(t0, t1, 2)
  fw.add(t5, t5, t0)
  round_up_reg(fw, t5, L1_ALIGN, tmp=t0)  # data
  fw.mv(s10, t5)        # first data byte; needed for NO_STRIDE command size
  fw.mv(s11, t2)
  round_up_reg(fw, s11, L1_ALIGN, tmp=t0)
  fw.label("pw_loop")
  fw.beq(t1, zero, "pw_done")
  fw.lw(t0, t4, 0)
  fw.noc_write(1, 0, t5, t3, 0, t0, t2, a=s3, v=s4)
  fw.addi(s6, s6, 1)
  fw.noc_wait_cmd_ready(1, 0, addr=s3, val=s4)
  fw.andi(t0, s8, CQ_PACKED_NO_STRIDE)
  fw.bne(t0, zero, "pw_no_stride")
  fw.add(t5, t5, t2)
  round_up_reg(fw, t5, L1_ALIGN, tmp=t0)
  fw.label("pw_no_stride")
  fw.addi(t4, t4, 4)
  fw.addi(t1, t1, -1)
  fw.j("pw_loop")
  fw.label("pw_done")
  fw.andi(t0, s8, CQ_PACKED_NO_STRIDE)
  fw.beq(t0, zero, "pw_done_ptr_ready")
  fw.mv(t5, s10)
  fw.add(t5, t5, s11)
  fw.label("pw_done_ptr_ready")
  fw.mv(s0, t5)
  fw.j("release_and_continue")

  fw.label("cmd_wait")
  fw.lbu(t0, s0, 1)
  fw.andi(t1, t0, CQ_WAIT_BARRIER)
  fw.beq(t1, zero, "wait_no_barrier")
  fw.noc_write_barrier(1, s6, addr=t2, val=t3)
  fw.label("wait_no_barrier")
  fw.andi(t1, t0, CQ_WAIT_WAIT_STREAM)
  fw.beq(t1, zero, "wait_clear")
  fw.lhu(t2, s0, 2)
  fw.lw(t3, s0, 8)
  fw.write32(CQ_DEBUG, 0xC1D10700, tmp_addr=t4, tmp_val=t5)
  fw.write32(CQ_DEBUG + 40, t2, tmp_addr=t4, tmp_val=t5)
  fw.write32(CQ_DEBUG + 44, t3, tmp_addr=t4, tmp_val=t5)
  fw.slli(t2, t2, 12)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX * 4)
  fw.add(t2, t2, t4)
  fw.label("wait_stream_loop")
  fw.lw(t4, t2, 0)
  fw.write32(CQ_DEBUG + 48, t4, tmp_addr=t5, tmp_val=s3)
  fw.li(t5, (1 << 17) - 1)
  fw.and_(t4, t4, t5)
  fw.sub(t4, t4, t3)
  fw.slli(t4, t4, 15)
  fw.blt(t4, zero, "wait_stream_loop")
  fw.label("wait_stream_done")
  fw.write32(CQ_DEBUG, 0xC1D10701, tmp_addr=t4, tmp_val=t5)
  fw.label("wait_clear")
  fw.andi(t1, t0, CQ_WAIT_CLEAR_STREAM)
  fw.beq(t1, zero, "wait_done")
  fw.lhu(t2, s0, 2)
  fw.slli(t2, t2, 12)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX * 4)
  fw.add(t5, t2, t4)
  fw.lw(t3, t5, 0)
  fw.sub(t3, zero, t3)
  fw.slli(t3, t3, REMOTE_DEST_BUF_WORDS_FREE_INC)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_REG_INDEX * 4)
  fw.add(t5, t2, t4)
  fw.sw(t3, t5, 0)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX * 4)
  fw.add(t5, t2, t4)
  fw.label("wait_clear_drain")
  fw.lw(t3, t5, 0)
  fw.li(t4, (1 << 17) - 1)
  fw.and_(t3, t3, t4)
  fw.bne(t3, zero, "wait_clear_drain")
  fw.label("wait_done")
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("cmd_set_go")
  fw.lw(t0, s0, 4)
  fw.addi(t1, s0, 16)
  fw.li(t2, GO_SIGNAL_NOC_DATA)
  fw.slli(t0, t0, 2)
  fw.copy_words(t2, t1, t0, word=t3)
  fw.mv(s0, t1)
  fw.add(s0, s0, t0)
  round_up_reg(fw, s0, L1_ALIGN, tmp=t0)
  fw.j("release_and_continue")

  fw.label("cmd_go")
  fw.lbu(t0, s0, 1)
  fw.lbu(t3, s0, 2)
  fw.slli(t3, t3, 8)
  fw.or_(t0, t0, t3)
  fw.lbu(t3, s0, 3)
  fw.slli(t3, t3, 16)
  fw.or_(t0, t0, t3)
  fw.lbu(t3, s0, 4)
  fw.slli(t3, t3, 24)
  fw.or_(t0, t0, t3)
  fw.lbu(t1, s0, 6)     # num_unicast
  fw.lw(t2, s0, 8)      # wait_count
  fw.lw(t3, s0, 12)     # wait_stream
  fw.write32(CQ_DEBUG + 32, t0, tmp_addr=t4, tmp_val=t5)
  fw.write32(CQ_DEBUG + 36, t1, tmp_addr=t4, tmp_val=t5)
  fw.slli(t3, t3, 12)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX * 4)
  fw.add(t3, t3, t4)
  fw.label("go_wait_stream_loop")
  fw.lw(t4, t3, 0)
  fw.li(t5, (1 << 17) - 1)
  fw.and_(t4, t4, t5)
  fw.sub(t4, t4, t2)
  fw.slli(t4, t4, 15)
  fw.blt(t4, zero, "go_wait_stream_loop")
  fw.lbu(t2, s0, 7)     # noc data index
  fw.li(t3, GO_SIGNAL_NOC_DATA)
  fw.slli(t2, t2, 2)
  fw.add(t3, t3, t2)
  # Blackhole inline writes can hang. Keep the GO word in stable scratch so
  # dispatch-CB page release cannot race the NOC engine's source read.
  fw.li(t6, GO_SIGNAL_VALUE)
  fw.sw(t0, t6, 0)
  fw.label("go_loop")
  fw.beq(t1, zero, "go_done")
  fw.lw(t2, t3, 0)
  fw.li(t4, 0x370)
  fw.li(s3, 4)
  fw.noc_write(1, 1, t6, t4, 0, t2, s3, posted=False, a=t5, v=s4)
  fw.noc_wait_cmd_ready(1, 1, addr=t5, val=s3)
  fw.addi(t3, t3, 4)
  fw.addi(t1, t1, -1)
  fw.j("go_loop")
  fw.label("go_done")
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("cmd_host")
  fw.write32(CQ_DEBUG, 0xC1D10300, tmp_addr=t1, tmp_val=t2)
  fw.lw(t0, s0, 8)      # length
  fw.write32(CQ_DEBUG + 8, t0, tmp_addr=t1, tmp_val=t2)
  fw.slli(t1, s1, 4)    # completion dst addr
  fw.write32(CQ_DEBUG + 12, t1, tmp_addr=t4, tmp_val=t5)
  fw.write32(CQ_DEBUG, 0xC1D10301, tmp_addr=t4, tmp_val=t5)
  fw.li(t4, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED)
  fw.lw(s6, t4, 0)
  fw.noc_write(1, 0, s0, t1, NOC_PCIE_MID, PCIE_NOC_XY, t0, a=t2, v=t3)
  fw.addi(s6, s6, 1)
  fw.write32(CQ_DEBUG, 0xC1D10302, tmp_addr=t4, tmp_val=t5)
  fw.noc_wait_write_acks(1, s6, addr=t2, val=t3)
  fw.write32(CQ_DEBUG, 0xC1D10303, tmp_addr=t4, tmp_val=t5)
  fw.addi(s1, s1, 256)  # one 4K completion page in 16B units
  fw.li(t2, (COMPLETION_BASE + COMPLETION_SIZE) >> 4)
  fw.bltu(s1, t2, "host_no_wrap")
  fw.li(s1, COMPLETION_BASE >> 4)
  fw.xori(s2, s2, 1)
  fw.label("host_no_wrap")
  fw.mv(t0, s1)
  fw.slli(t1, s2, 31)
  fw.or_(t0, t0, t1)
  fw.write32(COMPLETION_WR_PTR, t0, tmp_addr=t1, tmp_val=t2)
  fw.li(t1, COMPLETION_WR_PTR)
  fw.li(t2, HOST_COMPLETION_WR_PTR_OFF)
  fw.li(t3, 4)
  fw.write32(CQ_DEBUG, 0xC1D10304, tmp_addr=t4, tmp_val=t5)
  fw.li(t4, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED)
  fw.lw(s6, t4, 0)
  fw.noc_write(1, 0, t1, t2, NOC_PCIE_MID, PCIE_NOC_XY, t3, a=t4, v=t5)
  fw.addi(s6, s6, 1)
  fw.write32(CQ_DEBUG, 0xC1D10305, tmp_addr=t4, tmp_val=t5)
  fw.noc_wait_write_acks(1, s6, addr=t4, val=t5)
  fw.write32(CQ_DEBUG, 0xC1D10306, tmp_addr=t4, tmp_val=t5)
  fw.li(t1, 4096)
  fw.add(s0, s0, t1)
  fw.j("release_flush_and_continue")

  fw.label("cmd_timestamp")
  fw.lw(t0, s0, 4)
  fw.lw(t1, s0, 8)
  fw.read32(t2, RISCV_DEBUG_REG_WALL_CLOCK_L, tmp_addr=t3)
  fw.read32(t3, RISCV_DEBUG_REG_WALL_CLOCK_H, tmp_addr=t4)
  fw.sw(t2, s0, 0)
  fw.sw(t3, s0, 4)
  fw.li(t4, 8)
  fw.noc_write(1, 0, s0, t1, NOC_PCIE_MID, t0, t4, a=t5, v=s3)
  fw.addi(s6, s6, 1)
  fw.noc_wait_write_acks(1, s6, addr=t5, val=s3)
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("advance_page")
  fw.li(t0, DISPATCH_CB_PAGE)
  fw.add(s0, s0, t0)
  fw.j("release_and_continue")

  fw.label("release_and_continue")
  fw.li(t6, 8)
  fw.j("release_common")

  fw.label("release_flush_and_continue")
  fw.li(t6, 1)

  fw.label("release_common")
  round_up_reg(fw, s0, DISPATCH_CB_PAGE, tmp=t0)
  fw.mv(t3, s0)
  fw.sub(t3, t3, s9)
  fw.srli(t3, t3, 12)    # pages consumed by this dispatch record
  fw.write32(CQ_DEBUG + 28, t3, tmp_addr=t0, tmp_val=t4)
  fw.addi(t4, t3, -1)
  fw.beq(t4, zero, "dispatch_local_pages_done")
  fw.li(t0, DISPATCH_PAGE_CURSOR)
  fw.lw(t5, t0, 0)
  fw.add(t5, t5, t4)
  fw.sw(t5, t0, 0)
  fw.label("dispatch_local_pages_done")
  fw.li(t0, DISPATCH_CB_END)
  fw.bne(s0, t0, "dispatch_no_wrap")
  fw.li(s0, DISPATCH_CB_BASE)
  fw.label("dispatch_no_wrap")
  fw.li(t0, DISPATCH_RELEASE_PENDING)
  fw.lw(t4, t0, 0)
  fw.add(t4, t4, t3)
  fw.sw(t4, t0, 0)
  fw.bltu(t4, t6, "release_skip_atomic")
  fw.mv(t3, t4)
  fw.sw(zero, t0, 0)
  fw.noc_write_barrier(1, s6, addr=t0, val=t4)
  fw.li(t0, DISPATCH_RELEASE_VALUE)
  fw.lw(t4, t0, 0)
  fw.add(t4, t4, t3)
  fw.sw(t4, t0, 0)
  fw.li(t1, CQ_SEM_BASE)
  fw.li(t3, 4)
  fw.write32(CQ_DEBUG, 0xC1D1F010, tmp_addr=t5, tmp_val=s3)
  fw.noc_write(1, 2, t0, t1, 0, PREFETCH_NOC_XY, t3, a=t5, v=s3)
  fw.write32(CQ_DEBUG, 0xC1D1F011, tmp_addr=t5, tmp_val=s3)
  fw.label("release_skip_atomic")
  fw.j("dispatch_loop")

  fw.label("dispatch_done")
  fw.j("dispatch_done")
  return fw
