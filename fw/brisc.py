from __future__ import annotations

import sys
from pathlib import Path
from asm import Kernel
from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero
from ttk.addrs import (
  BriscMailbox as BM, CircularBuffer as CB, Dispatch, Firmware, Launch,
  Mailbox, NocCfg, P100BankTable, RunMsg, RunSync, Tensix, TensixInsn,
  TensixL1, TensixMMIO, TensixSem,
)
from ttk.hw.noc import NOC

def set_subordinate_reset_pcs(fw: Kernel, text_base: dict[str, int] = Firmware.TEXT_BASE):
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, text_base["ncrisc"])
  fw.breadcrumb(0xB015C101)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, text_base["trisc0"])
  fw.breadcrumb(0xB015C102)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, text_base["trisc1"])
  fw.breadcrumb(0xB015C103)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, text_base["trisc2"])
  fw.breadcrumb(0xB015C104)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
  fw.breadcrumb(0xB015C105)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
  fw.breadcrumb(0xB015C106)
  return fw

def enable_noc_clock_gating(fw: Kernel, *, addr: Reg = t0, value: Reg = t1):
  for noc in range(2):
    for reg in (NocCfg.NIU_CFG_0, NocCfg.ROUTER_CFG_0):
      cfg = NOC.CFG_BASE + reg * 4 + (noc << NOC.INSTANCE_OFFSET_BIT)
      fw.li(addr, cfg)
      fw.lw(value, addr, 0)
      fw.ori(value, value, 1)
      fw.sw(value, addr, 0)
  return fw

def device_setup(fw: Kernel):
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.breadcrumb(0xB015C201)
  fw.write32(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  fw.breadcrumb(0xB015C202)
  enable_noc_clock_gating(fw)
  fw.breadcrumb(0xB015C203)
  # invalidate_all_risc_icaches
  fw.write32(Tensix.RISCV_IC_INVALIDATE_INVALIDATE_ALL, Tensix.RISCV_IC_ALL_MASK)
  fw.breadcrumb(0xB015C204)
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.ZEROACC | (3 << 19))
  fw.breadcrumb(0xB015C205)
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SFPENCC | (3 << 12) | 10)
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.NOP)
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SFPLOADI | 0xBF80)
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SFPCONFIG | (11 << 4))
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SEMINIT | (1 << (TensixSem.MATH_PACK + 2)) | (0 << 16) | (1 << 20))
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SEMINIT | (1 << (TensixSem.UNPACK_TO_DEST + 2)) | (0 << 16) | (1 << 20))
  fw.tensix_push_word(Tensix.INSTRN_BUF_BASE, TensixInsn.SEMINIT | (1 << (TensixSem.MATH_DONE + 2)) | (0 << 16) | (1 << 20))
  fw.breadcrumb(0xB015C206)
  return fw

def wait_go(fw: Kernel, *, ptr: Reg = t0, signal: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_go")
  check_reset_host = fw._new_label("check_reset_host")
  check_replay = fw._new_label("check_replay")
  reset_ptr = fw._new_label("reset_launch_ptr")
  reset_ptr_notify = fw._new_label("reset_launch_ptr_notify")
  done = fw._new_label("go_seen")
  fw.li(ptr, Mailbox.GO_SIGNAL)
  fw.label(loop)
  fw.lbu(signal, ptr, 0)
  fw.li(expected, RunMsg.GO)
  fw.beq(signal, expected, done)
  fw.li(expected, RunMsg.RESET_READ_PTR)
  fw.beq(signal, expected, reset_ptr_notify)
  fw.label(check_reset_host)
  fw.li(expected, RunMsg.RESET_READ_PTR_FROM_HOST)
  fw.beq(signal, expected, reset_ptr)
  fw.label(check_replay)
  fw.li(expected, RunMsg.REPLAY_TRACE)
  fw.beq(signal, expected, reset_ptr_notify)
  fw.fence()
  fw.j(loop)
  fw.label(reset_ptr_notify)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=ptr, tmp_val=expected)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE, tmp_addr=ptr, tmp_val=expected)
  notify_dispatch_core_done(fw)
  fw.li(ptr, Mailbox.GO_SIGNAL)
  fw.fence()
  fw.j(loop)
  fw.label(reset_ptr)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=ptr, tmp_val=expected)
  fw.li(ptr, Mailbox.GO_SIGNAL)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()
  return fw

def signal_subordinate_if_enabled(fw: Kernel, role: int, value: int, *,
                                  enabled: Reg = t0, mask: Reg = t1):
  skip = fw._new_label("skip_subordinate_signal")
  fw.launch_kernel_enabled(role, enabled=enabled, mask=mask)
  fw.beq(enabled, zero, skip)
  fw.write8(Mailbox.SUBORDINATE_SYNC + role - 1, value)
  fw.label(skip)
  return fw

def init_risc_noc_coords(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1, tmp: Reg = t2):
  for noc in range(2):
    fw.read32(noc_id, fw.noc_cmd_addr(noc, 0, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4), tmp_addr=tmp)
    fw.andi(coord, noc_id, NocCfg.NODE_ID_MASK)
    fw.write8(BM.MY_X + noc, coord, tmp_addr=tmp)
    fw.srli(coord, noc_id, NocCfg.ADDR_NODE_ID_BITS)
    fw.andi(coord, coord, NocCfg.NODE_ID_MASK)
    fw.write8(BM.MY_Y + noc, coord, tmp_addr=tmp)
  return fw

def init_brisc_mailbox_globals(fw: Kernel, *, value: Reg = t0, tmp: Reg = t1):
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=tmp, tmp_val=value)
  fw.write8(BM.NOC_INDEX, 0, tmp_addr=tmp, tmp_val=value)
  fw.write8(BM.BRISC_NOC_MODE, 0, tmp_addr=tmp, tmp_val=value)
  fw.li(tmp, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(value, tmp, 0)
  fw.write8(BM.MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.li(tmp, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(value, tmp, 0)
  fw.write8(BM.MY_LOGICAL_Y, value, tmp_addr=tmp)
  fw.write32(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0, tmp_addr=tmp, tmp_val=value)
  return fw

def init_brisc_kernel_config(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                             off: Reg = t2, addr: Reg = t3, tmp: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)

  for i in range(3):
    fw.lhu(off, launch, Launch.SEM_OFFSET + 2 * i)
    fw.add(addr, config_base, off)
    fw.write32(BM.SEM_L1_BASE + 4 * i, addr, tmp_addr=tmp)

  fw.lhu(off, launch, Launch.RTA_OFFSET)
  fw.add(addr, config_base, off)
  fw.write32(BM.RTA_L1_BASE_PTR, addr, tmp_addr=tmp)

  fw.lhu(off, launch, Launch.RTA_OFFSET + 2)
  fw.add(addr, config_base, off)
  fw.write32(BM.CRTA_L1_BASE_PTR, addr, tmp_addr=tmp)
  return fw

def init_brisc_launch_globals(fw: Kernel, *, launch: Reg = t0, value: Reg = t1,
                              tmp: Reg = t2, origin: Reg = t3):
  keep = fw._new_label("keep_launch_noc")
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.lbu(value, launch, Launch.BRISC_NOC_ID)
  fw.bne(value, zero, keep)
  fw.lw(value, launch, Launch.ENABLES)
  fw.andi(value, value, 1 << 1)
  fw.beq(value, zero, keep)
  fw.li(value, 1)
  fw.label(keep)
  fw.sb(value, launch, Launch.BRISC_NOC_ID)
  fw.write8(BM.NOC_INDEX, value, tmp_addr=tmp)
  fw.lbu(value, launch, Launch.BRISC_NOC_MODE)
  fw.write8(BM.BRISC_NOC_MODE, value, tmp_addr=tmp)
  fw.li(tmp, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(value, tmp, 0)
  fw.write8(BM.MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  fw.write8(BM.MY_RELATIVE_X, value, tmp_addr=tmp)
  fw.li(tmp, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(value, tmp, 0)
  fw.write8(BM.MY_LOGICAL_Y, value, tmp_addr=tmp)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  fw.write8(BM.MY_RELATIVE_Y, value, tmp_addr=tmp)
  return fw

def init_noc_local_state(fw: Kernel, *, launch: Reg = t0, noc_id: Reg = t1,
                         noc_shift: Reg = t2, status: Reg = t3,
                         dest: Reg = t4, value: Reg = t5):
  fw.current_launch_ptr(launch=launch, tmp=value)
  fw.lbu(noc_id, launch, Launch.BRISC_NOC_ID)
  fw.slli(noc_shift, noc_id, 16)
  fw.noc_snapshot_status_counters(noc_id, noc_shift, [
    (NocCfg.NIU_MST_RD_RESP_RECEIVED_WORD, BM.NOC_READS_NUM_ISSUED),
    (NocCfg.NIU_MST_NONPOSTED_WR_REQ_SENT_WORD, BM.NOC_NONPOSTED_WRITES_NUM_ISSUED),
    (NocCfg.NIU_MST_WR_ACK_RECEIVED_WORD, BM.NOC_NONPOSTED_WRITES_ACKED),
    (NocCfg.NIU_MST_ATOMIC_RESP_RECEIVED_WORD, BM.NOC_NONPOSTED_ATOMICS_ACKED),
    (NocCfg.NIU_MST_POSTED_WR_REQ_SENT_WORD, BM.NOC_POSTED_WRITES_NUM_ISSUED),
  ], status=status, dest=dest, value=value)
  return fw

def wait_noc_cmd_buf_ready(fw: Kernel, noc: Reg, *, addr: Reg = t0, value: Reg = t1):
  fw.li(addr, NOC.CMD_CTRL + (NocCfg.NCRISC_AT_CMD_BUF << NOC.CMD_BUF_OFFSET_BIT))
  fw.add(addr, addr, noc)
  loop = fw._new_label("wait_noc_cmd_buf")
  fw.label(loop)
  fw.lw(value, addr, 0)
  fw.bne(value, zero, loop)
  return fw

def write_noc_cmd_reg(fw: Kernel, noc: Reg, reg: int, value: int | Reg, *,
                      addr: Reg = t0, tmp_val: Reg = t1):
  fw.li(addr, reg + (NocCfg.NCRISC_AT_CMD_BUF << NOC.CMD_BUF_OFFSET_BIT))
  fw.add(addr, addr, noc)
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)

def notify_dispatch_core_done(fw: Kernel, *, launch: Reg = t0, mode: Reg = t1,
                              go_index: Reg = t2, go_addr: Reg = t3,
                              dispatch_addr: Reg = t4, coord: Reg = t5,
                              noc_shift: Reg = t6):
  skip = fw._new_label("skip_dispatch_notify")
  fw.current_launch_ptr(launch=launch, tmp=mode)
  fw.lbu(mode, launch, Launch.MODE)
  fw.li(coord, Dispatch.MODE_DEV)
  fw.bne(mode, coord, skip)

  fw.li(go_addr, Mailbox.GO_MESSAGES)

  fw.lbu(dispatch_addr, go_addr, 0)
  fw.slli(dispatch_addr, dispatch_addr, 12)
  fw.li(coord, Dispatch.MESSAGE_ADDR)
  fw.add(dispatch_addr, dispatch_addr, coord)

  fw.lbu(coord, go_addr, 2)
  fw.slli(coord, coord, 6)
  fw.lbu(mode, go_addr, 1)
  fw.or_(coord, coord, mode)

  fw.li(noc_shift, 0)
  fw.lbu(noc_shift, launch, Launch.BRISC_NOC_ID)
  fw.slli(noc_shift, noc_shift, NOC.INSTANCE_OFFSET_BIT)
  wait_noc_cmd_buf_ready(fw, noc_shift, addr=go_addr, value=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC.AT_DATA, Dispatch.DONE_WORD, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC.CTRL, NocCfg.INLINE_WRITE_POSTED_FIELD, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC.TARG_ADDR_LO, dispatch_addr, addr=go_addr)
  # C++ firmware writes (dispatch_addr >> 32) & NOC_PCIE_MASK here. For the
  # local dispatch stream register address used by this path, those mid bits
  # are zero; setting the low nibble to 0xF targets the wrong NOC address.
  write_noc_cmd_reg(fw, noc_shift, NOC.TARG_ADDR_MID, 0, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC.TARG_ADDR_COORDINATE, coord, addr=go_addr)
  write_noc_cmd_reg(fw, noc_shift, NOC.AT_LEN_BE, 0xF, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=go_addr, tmp_val=mode)

  fw.sw(zero, launch, Launch.ENABLES)
  fw.sb(zero, launch, Launch.PRELOAD)

  fw.label(skip)
  return fw

def noc_init(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1,
             tmp_addr: Reg = t2, tmp_val: Reg = t3):
  for noc in range(2):
    fw.read32(noc_id, fw.noc_cmd_addr(noc, 0, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4), tmp_addr=tmp_addr)
    fw.andi(coord, noc_id, NocCfg.NODE_ID_MASK)
    fw.srli(noc_id, noc_id, NocCfg.ADDR_NODE_ID_BITS)
    fw.andi(noc_id, noc_id, NocCfg.NODE_ID_MASK)
    fw.slli(noc_id, noc_id, NocCfg.ADDR_NODE_ID_BITS)
    fw.or_(coord, coord, noc_id)

    fw.noc_init_cmd_bufs(
      noc,
      coord,
      atomic_ret_addr=NocCfg.MEM_NOC_ATOMIC_RET_VAL_ADDR,
      read_ctrl=NocCfg.RD_CMD_FIELD,
      wr_buf=NocCfg.NCRISC_WR_CMD_BUF,
      rd_buf=NocCfg.NCRISC_RD_CMD_BUF,
      wr_reg_buf=NocCfg.NCRISC_WR_REG_CMD_BUF,
      at_buf=NocCfg.NCRISC_AT_CMD_BUF,
      tmp_addr=tmp_addr,
      tmp_val=tmp_val,
    )
  return fw

def setup_local_cbs(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4,
                    size: Reg = t5, fifo: Reg = t6):
  fw.current_launch_ptr(launch=launch, tmp=size)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, Launch.LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, BM.CB_INTERFACE)
  fw.lw(mask, launch, Launch.LOCAL_CB_MASK)
  fw.li(launch, CB.SYNC_TILES_ACKED_BASE)
  fw.li(config_base, CB.SYNC_TILES_RECEIVED_BASE)

  loop = fw._new_label("setup_cb")
  skip = fw._new_label("skip_cb")
  done = fw._new_label("done_cb")
  fw.label(loop)
  fw.beq(mask, zero, done)
  fw.andi(size, mask, 1)
  fw.beq(size, zero, skip)
  fw.lw(size, cb_config, 4)
  fw.lw(fifo, cb_config, 0)
  fw.sw(size, cb_if, 0)
  fw.add(size, fifo, size)
  fw.sw(size, cb_if, 4)
  fw.lw(size, cb_config, 12)
  fw.sw(size, cb_if, 8)
  fw.lw(size, cb_config, 8)
  fw.sw(size, cb_if, 12)
  fw.sw(fifo, cb_if, 16)
  fw.sw(fifo, cb_if, 20)
  fw.sw(zero, cb_if, 24)
  fw.sw(zero, cb_if, 28)
  fw.sw(zero, launch, 0)
  fw.sw(zero, config_base, 0)
  fw.label(skip)
  fw.addi(cb_config, cb_config, CB.LOCAL_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, CB.LOCAL_INTERFACE_SIZE)
  fw.li(size, CB.SYNC_STRIDE)
  fw.add(launch, launch, size)
  fw.add(config_base, config_base, size)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw

def build(*, text_base: dict[str, int] = Firmware.TEXT_BASE) -> Kernel:
  fw = Kernel(base_addr=Firmware.TEXT_BASE["brisc"])
  fw.segment(Firmware.LOCAL_DATA_BASE["brisc"], b"\x68".ljust(Firmware.LOCAL_DATA_SIZE["brisc"], b"\0"), label="local_data")
  fw.configure_csr()
  fw.breadcrumb(0xB015C001)
  fw.setup_stack(Firmware.BRISC_STACK_TOP)
  fw.breadcrumb(0xB015C100)
  set_subordinate_reset_pcs(fw, text_base)
  device_setup(fw)
  fw.breadcrumb(0xB015C002)
  init_risc_noc_coords(fw)
  # init_bank_tables
  fw.copy_words(
    BM.DRAM_BANK_TO_NOC_XY,
    TensixL1.MEM_BANK_TO_NOC_SCRATCH,
    P100BankTable.DRAM_BANK_TO_NOC_SIZE + P100BankTable.L1_BANK_TO_NOC_SIZE +
    P100BankTable.BANK_TO_DRAM_OFFSET_SIZE + P100BankTable.BANK_TO_L1_OFFSET_SIZE,
  )
  init_brisc_mailbox_globals(fw)
  noc_init(fw)
  init_noc_local_state(fw)
  fw.breadcrumb(0xB015C005)
  # invalidate_all_risc_icaches
  fw.write32(Tensix.RISCV_IC_INVALIDATE_INVALIDATE_ALL, Tensix.RISCV_IC_ALL_MASK)
  fw.breadcrumb(0xB015C006)
  # init_subordinate_sync
  fw.write32(Mailbox.SUBORDINATE_SYNC, RunSync.ALL_INIT)
  fw.breadcrumb(0xB015C007)
  # deassert_all_riscs
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in (1, 2, 3, 4):
    fw.wait8(Mailbox.SUBORDINATE_SYNC + role - 1, RunSync.DONE)
  fw.breadcrumb(0xB015C008)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE)
  # Ask TRISC0 to clear CB sync registers before launching kernels.
  fw.write8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.INIT_SYNC_REGISTERS)
  fw.breadcrumb(0xB015C009)

  fw.label("run_loop")
  wait_go(fw)
  fw.breadcrumb(0xB015C010)
  fw.wait8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.DONE)
  fw.breadcrumb(0xB015C011)
  init_brisc_kernel_config(fw)
  init_brisc_launch_globals(fw)
  noc_init(fw)
  init_noc_local_state(fw)
  # invalidate_all_risc_icaches
  fw.write32(Tensix.RISCV_IC_INVALIDATE_INVALIDATE_ALL, Tensix.RISCV_IC_ALL_MASK)
  signal_subordinate_if_enabled(fw, 1, RunSync.LOAD)
  for role in (2, 3, 4):
    signal_subordinate_if_enabled(fw, role, RunSync.GO)
  setup_local_cbs(fw)
  signal_subordinate_if_enabled(fw, 1, RunSync.GO)
  fw.run_launch_kernel(0)
  for role in (1, 2, 3, 4):
    fw.wait8(Mailbox.SUBORDINATE_SYNC + role - 1, RunSync.DONE)
  fw.breadcrumb(0xB015C020)
  # Ask TRISC0 to clear CB sync registers before accepting the next launch.
  fw.write8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.INIT_SYNC_REGISTERS)
  fw.breadcrumb(0xB015C021)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE)
  notify_dispatch_core_done(fw)
  fw.read32(t0, Mailbox.LAUNCH_MSG_RD_PTR, tmp_addr=t1)
  fw.addi(t0, t0, 1)
  fw.andi(t0, t0, 7)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, t0, tmp_addr=t1)
  fw.j("run_loop")
  return fw
