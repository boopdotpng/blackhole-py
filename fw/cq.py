from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, ra, sp, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, t5, t6, zero


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
NOC_AT_INCR_GET = 0x2
NOC_MAX_BURST_SIZE = 16 * 1024

NIU_MST_WR_ACK_RECEIVED = 0x04
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
HOST_ISSUE_BASE = 0x40000100
CMDDAT_Q_BASE = 0x1A440
DISPATCH_CB_BASE = 0x1A000
DISPATCH_CB_PAGES = 128
DISPATCH_CB_PAGE = 4096
DISPATCH_CB_END = DISPATCH_CB_BASE + DISPATCH_CB_PAGES * DISPATCH_CB_PAGE
DISPATCH_S_CB_BASE = 0x9A000
DISPATCH_S_CB_PAGE = 256
DISPATCH_S_CB_END = DISPATCH_S_CB_BASE + 32 * 1024
# Current blackhole-py-old default target is p100:
# prefetch=(14, 2), dispatch=(14, 3).
PREFETCH_NOC_XY = (2 << 6) | 14
DISPATCH_NOC_XY = (3 << 6) | 14
PCIE_NOC_XY = (1 << 24) | (24 << 6) | 19

CQ_PREFETCH_CMD_RELAY_INLINE = 5
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
HOST_COMPLETION_WR_PTR_OFF = 128
RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0
RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8

GO_SIGNAL_NOC_DATA = 0xB0000
CQ_DEBUG = 0x19000


def write32(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)


def read32(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lw(rd, addr, 0)


def read16(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lhu(rd, addr, 0)


def stream_reg(stream: int | Reg, reg: int, *, out: Reg = t0, tmp: Reg = t1):
  if isinstance(stream, int):
    return STREAM_BASE + stream * STREAM_STRIDE + reg * 4
  # out = STREAM_BASE + stream * STREAM_STRIDE + reg*4
  # STREAM_STRIDE is 1<<12.
  return out


def setup_stack(fw: Kernel):
  return fw.li(sp, 0xFFB01FF0)


def noc_cmd_addr(noc: int, buf: int, reg: int) -> int:
  return reg + (buf << NOC_CMD_BUF_OFFSET_BIT) + (noc << NOC_INSTANCE_OFFSET_BIT)


def wait_cmd_ready(fw: Kernel, noc: int, buf: int, *, addr: Reg = t0, val: Reg = t1):
  fw.li(addr, noc_cmd_addr(noc, buf, NOC_CMD_CTRL))
  loop = fw._new_label("noc_ready")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bne(val, zero, loop)
  return fw


def wait_noc_write_acks(fw: Kernel, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
  fw.li(addr, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED + (noc << NOC_INSTANCE_OFFSET_BIT))
  loop = fw._new_label("wr_ack")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bltu(val, target, loop)
  return fw


def noc_write_reg(fw: Kernel, noc: int, buf: int, reg: int, value: int | Reg, *, addr: Reg = t0, tmp: Reg = t1):
  return write32(fw, noc_cmd_addr(noc, buf, reg), value, tmp_addr=addr, tmp_val=tmp)


def noc_read(fw: Kernel, noc: int, buf: int, src_lo: Reg, src_mid: int | Reg, src_coord: int | Reg,
             dst: Reg, length: Reg, *, a: Reg = t0, v: Reg = t1):
  wait_cmd_ready(fw, noc, buf, addr=a, val=v)
  noc_write_reg(fw, noc, buf, NOC_CTRL, NOC_CMD_RD_FIELD, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_RET_ADDR_LO, dst, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_LO, src_lo, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_MID, src_mid, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_COORDINATE, src_coord, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_AT_LEN_BE, length, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CMD_CTRL, NOC_CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def noc_write(fw: Kernel, noc: int, buf: int, src: Reg, dst_lo: Reg, dst_mid: int | Reg, dst_coord: Reg,
              length: Reg, *, mcast: bool = False, mcast_linked: bool = False,
              num_dests: Reg | None = None, a: Reg = t0, v: Reg = t1):
  wait_cmd_ready(fw, noc, buf, addr=a, val=v)
  if mcast:
    noc_write_reg(
      fw, noc, buf, NOC_CTRL,
      NOC_CMD_WR_MCAST_LINKED_FIELD if mcast_linked else NOC_CMD_WR_MCAST_UNLINK_FIELD,
      addr=a, tmp=v)
  else:
    noc_write_reg(fw, noc, buf, NOC_CTRL, NOC_CMD_WR_FIELD, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_LO, src, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_RET_ADDR_LO, dst_lo, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_RET_ADDR_MID, dst_mid, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_AT_LEN_BE, length, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CMD_CTRL, NOC_CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def noc_inline_write(fw: Kernel, noc: int, buf: int, value: Reg, dst_lo: Reg, dst_mid: int | Reg, dst_coord: Reg,
                     *, a: Reg = t0, v: Reg = t1):
  wait_cmd_ready(fw, noc, buf, addr=a, val=v)
  noc_write_reg(fw, noc, buf, NOC_AT_DATA, value, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CTRL, NOC_CMD_INLINE_FIELD, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_MID, dst_mid, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_AT_LEN_BE, 0xF, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CMD_CTRL, NOC_CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def noc_atomic_inc(fw: Kernel, noc: int, buf: int, dst_lo: Reg, dst_coord: int | Reg, incr: Reg | int,
                   *, a: Reg = t0, v: Reg = t1):
  wait_cmd_ready(fw, noc, buf, addr=a, val=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_MID, 0, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CTRL, NOC_CMD_AT_INC_FIELD, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_AT_LEN_BE, NOC_AT_INCR_GET | (31 << 12), addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_AT_DATA, incr, addr=a, tmp=v)
  noc_write_reg(fw, noc, buf, NOC_CMD_CTRL, NOC_CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def copy_words(fw: Kernel, dst: Reg, src: Reg, byte_count: Reg, *, word: Reg = t0):
  loop = fw._new_label("copy")
  done = fw._new_label("copy_done")
  fw.label(loop)
  fw.beq(byte_count, zero, done)
  fw.lw(word, src, 0)
  fw.sw(word, dst, 0)
  fw.addi(src, src, 4)
  fw.addi(dst, dst, 4)
  fw.addi(byte_count, byte_count, -4)
  fw.j(loop)
  fw.label(done)
  return fw


def acquire_local_pages(fw: Kernel, sem_addr: int, pages: Reg, credit: Reg, *, ptr: Reg = t0, val: Reg = t1):
  fw.li(ptr, sem_addr)
  loop = fw._new_label("sem_wait")
  fw.label(loop)
  fw.lw(val, ptr, 0)
  fw.add(val, val, credit)
  fw.bltu(val, pages, loop)
  fw.sub(credit, credit, pages)
  return fw


def round_up_reg(fw: Kernel, reg: Reg, align: int, *, tmp: Reg = t0):
  fw.li(tmp, align - 1)
  fw.add(reg, reg, tmp)
  fw.li(tmp, ~(align - 1))
  fw.and_(reg, reg, tmp)
  return fw


def build_prefetch() -> Kernel:
  fw = Kernel(kind="brisc")
  setup_stack(fw)
  write32(fw, CQ_DEBUG, 0xC1010001)
  fw.li(s0, PREFETCH_Q_BASE)     # queue read pointer
  read32(fw, s1, PREFETCH_Q_PCIE_RD)  # host PCIE read pointer
  fw.li(s2, DISPATCH_CB_BASE)    # dispatch CB write pointer
  fw.li(s8, 0)                    # local page-credit adjustment
  read32(fw, s4, NOC_STATUS_BASE + NIU_MST_RD_RESP_RECEIVED)
  read32(fw, s5, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED)

  fw.label("prefetch_loop")
  write32(fw, CQ_DEBUG, 0xC1010002)
  fw.lhu(t0, s0, 0)
  fw.beq(t0, zero, "prefetch_loop")
  fw.slli(t0, t0, 4)             # byte count
  fw.li(t1, CMDDAT_Q_BASE)
  write32(fw, CQ_DEBUG + 4, t0, tmp_addr=t2, tmp_val=t3)
  noc_read(fw, 0, 1, s1, NOC_PCIE_MID, PCIE_NOC_XY, t1, t0, a=t2, v=t3)
  fw.addi(s4, s4, 1)
  fw.li(t2, NOC_STATUS_BASE + NIU_MST_RD_RESP_RECEIVED)
  fw.label("prefetch_read_barrier")
  fw.lw(t3, t2, 0)
  fw.bltu(t3, s4, "prefetch_read_barrier")
  fw.sh(zero, s0, 0)
  write32(fw, PREFETCH_Q_RD_PTR, s0, tmp_addr=t2, tmp_val=t3)
  fw.add(s1, s1, t0)
  write32(fw, PREFETCH_Q_PCIE_RD, s1, tmp_addr=t2, tmp_val=t3)
  fw.addi(s0, s0, 2)
  fw.li(t2, PREFETCH_Q_END)
  fw.bne(s0, t2, "prefetch_no_q_wrap")
  fw.li(s0, PREFETCH_Q_BASE)
  fw.label("prefetch_no_q_wrap")

  fw.li(t1, CMDDAT_Q_BASE)
  fw.lbu(t2, t1, 0)
  write32(fw, CQ_DEBUG + 8, t2, tmp_addr=t3, tmp_val=t4)
  fw.li(t3, CQ_PREFETCH_CMD_RELAY_INLINE)
  fw.bne(t2, t3, "prefetch_loop")
  fw.lw(t0, t1, 4)               # payload length
  fw.mv(s6, t0)
  fw.addi(t1, t1, 16)            # payload source
  fw.li(t2, DISPATCH_CB_PAGE - 1)
  fw.add(t2, t0, t2)
  fw.srli(t2, t2, 12)            # pages
  fw.mv(s3, t2)
  acquire_local_pages(fw, CQ_SEM_BASE, s3, s8, ptr=t3, val=t0)
  noc_write(fw, 0, 0, t1, s2, 0, DISPATCH_NOC_XY, s6, a=t2, v=t3)
  fw.addi(s5, s5, 1)
  wait_noc_write_acks(fw, 0, s5, addr=t2, val=t3)
  fw.mv(t0, s3)
  fw.slli(t0, t0, 12)
  fw.add(s2, s2, t0)
  fw.li(t1, DISPATCH_CB_END)
  fw.bne(s2, t1, "prefetch_no_cb_wrap")
  fw.li(s2, DISPATCH_CB_BASE)
  fw.label("prefetch_no_cb_wrap")
  fw.li(t1, CQ_SEM_BASE)
  noc_atomic_inc(fw, 0, 3, t1, DISPATCH_NOC_XY, s3, a=t2, v=t3)
  fw.j("prefetch_loop")
  return fw


def build_dispatch() -> Kernel:
  fw = Kernel(kind="brisc")
  setup_stack(fw)
  write32(fw, CQ_DEBUG, 0xC1D10001)
  fw.li(s0, DISPATCH_CB_BASE)  # cmd ptr
  read32(fw, s1, COMPLETION_WR_PTR)  # completion wr ptr in 16B units
  fw.li(s2, 0)  # completion toggle
  read32(fw, s6, NOC_STATUS_BASE + NIU_MST_WR_ACK_RECEIVED + (1 << NOC_INSTANCE_OFFSET_BIT))

  fw.label("dispatch_loop")
  write32(fw, CQ_DEBUG, 0xC1D10002)
  fw.li(t0, CQ_SEM_BASE)
  fw.label("dispatch_wait_page")
  fw.lw(t1, t0, 0)
  fw.beq(t1, zero, "dispatch_wait_page")
  fw.addi(t1, t1, -1)
  fw.sw(t1, t0, 0)
  fw.lbu(t0, s0, 0)
  write32(fw, CQ_DEBUG + 4, t0, tmp_addr=t1, tmp_val=t2)
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
  write32(fw, CQ_DEBUG, 0xC1D10600)
  fw.lhu(s3, s0, 2)      # remaining subcmd count
  fw.lhu(s4, s0, 4)      # alignment
  fw.addi(s5, s0, 16)    # subcmd ptr
  fw.mv(t3, s5)
  fw.li(t4, 12)
  fw.mul(t4, s3, t4)
  fw.add(t3, t3, t4)
  round_up_reg(fw, t3, L1_ALIGN, tmp=t4)  # data ptr
  fw.label("pl_loop")
  fw.beq(s3, zero, "pl_done")
  write32(fw, CQ_DEBUG, 0xC1D10601)
  fw.lw(t4, s5, 0)       # noc xy
  write32(fw, CQ_DEBUG + 8, t4, tmp_addr=t0, tmp_val=t2)
  fw.lw(t5, s5, 4)       # addr
  write32(fw, CQ_DEBUG + 12, t5, tmp_addr=t0, tmp_val=t2)
  fw.lhu(t1, s5, 8)      # len-1
  fw.addi(t1, t1, 1)
  write32(fw, CQ_DEBUG + 16, t1, tmp_addr=t0, tmp_val=t2)
  fw.lbu(s7, s5, 10)     # num destinations
  write32(fw, CQ_DEBUG, 0xC1D10602)
  noc_write(fw, 1, 0, t3, t5, 0, t4, t1, mcast=True, num_dests=s7, a=t0, v=t2)
  write32(fw, CQ_DEBUG, 0xC1D10603)
  wait_cmd_ready(fw, 1, 0, addr=t0, val=t4)
  write32(fw, CQ_DEBUG, 0xC1D10604)
  fw.add(t3, t3, t1)
  # CQWritePackedLarge currently emits L1_ALIGN alignment.
  round_up_reg(fw, t3, L1_ALIGN, tmp=t4)
  fw.addi(s5, s5, 12)
  fw.addi(s3, s3, -1)
  fw.j("pl_loop")
  fw.label("pl_done")
  fw.mv(s0, t3)
  fw.j("release_and_continue")

  fw.label("cmd_packed")
  fw.lbu(t0, s0, 1)      # flags
  fw.lhu(t1, s0, 2)      # count
  fw.lhu(t2, s0, 6)      # size
  fw.lw(t3, s0, 8)       # dst addr
  fw.addi(t4, s0, 16)    # noc list
  fw.mv(t5, t4)
  fw.slli(t0, t1, 2)
  fw.add(t5, t5, t0)
  round_up_reg(fw, t5, L1_ALIGN, tmp=t0)  # data
  fw.label("pw_loop")
  fw.beq(t1, zero, "pw_done")
  fw.lw(t0, t4, 0)
  noc_write(fw, 1, 0, t5, t3, 0, t0, t2, a=s3, v=s4)
  wait_cmd_ready(fw, 1, 0, addr=s3, val=s4)
  fw.add(t5, t5, t2)
  round_up_reg(fw, t5, L1_ALIGN, tmp=t0)
  fw.addi(t4, t4, 4)
  fw.addi(t1, t1, -1)
  fw.j("pw_loop")
  fw.label("pw_done")
  fw.mv(s0, t5)
  fw.j("release_and_continue")

  fw.label("cmd_wait")
  fw.lbu(t0, s0, 1)
  fw.andi(t1, t0, CQ_WAIT_BARRIER)
  # Per-command cmd-buffer-ready waits above provide the barrier we need for add1.
  fw.andi(t1, t0, CQ_WAIT_WAIT_STREAM)
  fw.beq(t1, zero, "wait_clear")
  fw.lhu(t2, s0, 2)
  fw.lw(t3, s0, 8)
  fw.slli(t2, t2, 12)
  fw.li(t4, STREAM_BASE + STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX * 4)
  fw.add(t2, t2, t4)
  fw.label("wait_stream_loop")
  fw.lw(t4, t2, 0)
  fw.bltu(t4, t3, "wait_stream_loop")
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
  fw.label("wait_done")
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("cmd_set_go")
  fw.lw(t0, s0, 4)
  fw.addi(t1, s0, 16)
  fw.li(t2, GO_SIGNAL_NOC_DATA)
  fw.slli(t0, t0, 2)
  copy_words(fw, t2, t1, t0, word=t3)
  fw.mv(s0, t1)
  fw.add(s0, s0, t0)
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
  fw.lbu(t2, s0, 7)     # noc data index
  fw.li(t3, GO_SIGNAL_NOC_DATA)
  fw.slli(t2, t2, 2)
  fw.add(t3, t3, t2)
  fw.label("go_loop")
  fw.beq(t1, zero, "go_done")
  fw.lw(t2, t3, 0)
  fw.li(t4, 0x370)
  noc_inline_write(fw, 1, 1, t0, t4, 0, t2, a=t5, v=s3)
  wait_cmd_ready(fw, 1, 1, addr=t5, val=s3)
  fw.addi(t3, t3, 4)
  fw.addi(t1, t1, -1)
  fw.j("go_loop")
  fw.label("go_done")
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("cmd_host")
  fw.lw(t0, s0, 8)      # length
  fw.slli(t1, s1, 4)    # completion dst addr
  noc_write(fw, 1, 0, s0, t1, NOC_PCIE_MID, PCIE_NOC_XY, t0, a=t2, v=t3)
  fw.addi(s6, s6, 1)
  wait_noc_write_acks(fw, 1, s6, addr=t2, val=t3)
  fw.addi(s1, s1, 256)  # one 4K completion page in 16B units
  fw.li(t2, (COMPLETION_BASE + COMPLETION_SIZE) >> 4)
  fw.bltu(s1, t2, "host_no_wrap")
  fw.li(s1, COMPLETION_BASE >> 4)
  fw.xori(s2, s2, 1)
  fw.label("host_no_wrap")
  fw.mv(t0, s1)
  fw.slli(t1, s2, 31)
  fw.or_(t0, t0, t1)
  write32(fw, COMPLETION_WR_PTR, t0, tmp_addr=t1, tmp_val=t2)
  fw.li(t1, COMPLETION_WR_PTR)
  fw.li(t2, HOST_COMPLETION_WR_PTR_OFF)
  fw.li(t3, 4)
  noc_write(fw, 1, 0, t1, t2, NOC_PCIE_MID, PCIE_NOC_XY, t3, a=t4, v=t5)
  fw.addi(s6, s6, 1)
  wait_noc_write_acks(fw, 1, s6, addr=t4, val=t5)
  fw.li(t1, 4096)
  fw.add(s0, s0, t1)
  fw.j("release_and_continue")

  fw.label("cmd_timestamp")
  fw.lw(t0, s0, 4)
  fw.lw(t1, s0, 8)
  read32(fw, t2, RISCV_DEBUG_REG_WALL_CLOCK_L, tmp_addr=t3)
  read32(fw, t3, RISCV_DEBUG_REG_WALL_CLOCK_H, tmp_addr=t4)
  fw.sw(t2, s0, 0)
  fw.sw(t3, s0, 4)
  fw.li(t4, 8)
  noc_write(fw, 1, 0, s0, t1, NOC_PCIE_MID, t0, t4, a=t5, v=s3)
  fw.addi(s6, s6, 1)
  wait_noc_write_acks(fw, 1, s6, addr=t5, val=s3)
  fw.addi(s0, s0, 16)
  fw.j("release_and_continue")

  fw.label("advance_page")
  fw.li(t0, DISPATCH_CB_PAGE)
  fw.add(s0, s0, t0)
  fw.j("release_and_continue")

  fw.label("release_and_continue")
  round_up_reg(fw, s0, DISPATCH_CB_PAGE, tmp=t0)
  fw.li(t0, DISPATCH_CB_END)
  fw.bne(s0, t0, "dispatch_no_wrap")
  fw.li(s0, DISPATCH_CB_BASE)
  fw.label("dispatch_no_wrap")
  fw.li(t0, CQ_SEM_BASE)
  noc_atomic_inc(fw, 1, 3, t0, PREFETCH_NOC_XY, 1, a=t1, v=t2)
  fw.j("dispatch_loop")

  fw.label("dispatch_done")
  fw.j("dispatch_done")
  return fw


def build_dispatch_subordinate() -> Kernel:
  fw = Kernel(kind="ncrisc")
  setup_stack(fw)
  # This minimal fast-dispatch path handles go signals on dispatch BRISC.
  fw.label("idle")
  fw.j("idle")
  return fw


def _write_manifest(out: Path, name: str, kernel: Kernel) -> Path:
  segments = kernel.compile()
  manifest = {"kind": kernel.kind, "segments": []}
  for i, seg in enumerate(segments):
    bin_name = f"{name}.seg{i}.bin"
    (out / bin_name).write_bytes(seg.data)
    manifest["segments"].append({
      "label": seg.label or "text",
      "addr": f"0x{seg.addr:x}",
      "bin": bin_name,
      "filesz": len(seg.data),
      "memsz": len(seg.data),
      "flags": 5 if (seg.label or "text").endswith("text") or seg.addr == 0 else 6,
    })
  path = out / f"{name}.json"
  path.write_text(json.dumps(manifest, indent=2) + "\n")
  return path


def write_artifacts(out_dir: Path | str | None = None) -> list[Path]:
  out = Path(__file__).resolve().parent / "build" if out_dir is None else Path(out_dir)
  out.mkdir(parents=True, exist_ok=True)
  return [
    _write_manifest(out, "cq_prefetch_brisc", build_prefetch()),
    _write_manifest(out, "cq_dispatch_brisc", build_dispatch()),
    _write_manifest(out, "cq_dispatch_s_ncrisc", build_dispatch_subordinate()),
  ]


if __name__ == "__main__":
  for path in write_artifacts():
    print(path)
