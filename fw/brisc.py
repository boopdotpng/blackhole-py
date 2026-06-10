from __future__ import annotations

import sys
from pathlib import Path
from asm import Kernel, KernelBase
from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero
from ttk import Cb, Noc, Tensix
from ttk.mailbox import BriscMailbox as BM, Dispatch, Firmware
from ttk.noc import NOC, NocCfg
from dsl import TTNOP, TTSEMINIT, TTSFPENCC, TTSFPCONFIG, TTSFPLOADI, TTZEROACC
from ttk.tensix import Launch, Mailbox, RunMsg, RunSync, TensixL1, TensixMMIO, TensixRegs, TensixSem

def signal_subordinate_if_enabled(fw: KernelBase, role: int, value: int, *,
                                  enabled: Reg = t0, mask: Reg = t1):
  skip = fw._new_label("skip_subordinate_signal")
  fw.launch_kernel_enabled(role, enabled=enabled, mask=mask)
  fw.beq(enabled, zero, skip)
  fw.write8(Mailbox.SUBORDINATE_SYNC + role - 1, value)
  fw.label(skip)
  return fw

def write_noc_cmd_reg(fw: KernelBase, noc: Reg, reg: int, value: int | Reg, *,
                      addr: Reg = t0, tmp_val: Reg = t1):
  fw.li(addr, reg + (NocCfg.NCRISC_AT_CMD_BUF << NOC.CMD_BUF_OFFSET_BIT))
  fw.add(addr, addr, noc)
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)

def notify_dispatch_core_done(fw: KernelBase, *, launch: Reg = t0, mode: Reg = t1,
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
  # wait_noc_cmd_buf_ready
  fw.li(go_addr, NOC.CMD_CTRL + (NocCfg.NCRISC_AT_CMD_BUF << NOC.CMD_BUF_OFFSET_BIT))
  fw.add(go_addr, go_addr, noc_shift)
  wait_noc_cmd_buf = fw._new_label("wait_noc_cmd_buf")
  fw.label(wait_noc_cmd_buf)
  fw.lw(mode, go_addr, 0)
  fw.bne(mode, zero, wait_noc_cmd_buf)
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

def noc_init(fw: KernelBase, *, noc_id: Reg = t0, coord: Reg = t1,
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

def init_noc_local_state(fw: KernelBase, *, launch: Reg = t0, noc_id: Reg = t1,
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

def rmw_tensix_cfg(fw: KernelBase, addr32: int, mask: int, value: int, *,
                   shift: int = 0, addr: Reg = t0, old: Reg = t1, tmp: Reg = t2):
  fw.li(addr, TensixRegs.CFG_BASE + addr32 * 4)
  fw.lw(old, addr, 0)
  fw.li(tmp, ~mask & 0xFFFFFFFF)
  fw.and_(old, old, tmp)
  fw.li(tmp, (value << shift) & mask)
  fw.or_(old, old, tmp)
  fw.sw(old, addr, 0)
  return fw

TENSIX_CFG_RESET_WORDS = 256  # named CFG regs end at +0x378; zero 0x400 bytes

def tensix_hw_reset(fw: KernelBase):
  """Return Tensix to cold-boot state. Run at boot AND before every launch so
  no kernel inherits CFG/DEST/semaphore state from a differing predecessor
  (programs are only correct relative to reset state, never to leftovers)."""
  # CFG space resets to zero at cold boot; differing programs leave plan-
  # specific descriptors behind. Kernels program what they use from zero.
  fw.zero_words(TensixRegs.CFG_BASE, TENSIX_CFG_RESET_WORDS)
  buf = TensixRegs.INSTRN_BUF_BASE
  fw.push_tensix_word(buf, TTZEROACC(clear_mode=3).raw_word())
  fw.push_tensix_word(buf, TTSFPENCC(imm12_math=3, instr_mod1=10).raw_word())
  fw.push_tensix_word(buf, TTNOP().raw_word())
  fw.push_tensix_word(buf, TTSFPLOADI(imm16=0xBF80).raw_word())
  fw.push_tensix_word(buf, TTSFPCONFIG(config_dest=11).raw_word())
  rmw_tensix_cfg(fw, TensixRegs.ECC_SCRUBBER_ADDR32, TensixRegs.ECC_SCRUBBER_ENABLE_MASK, 1)
  rmw_tensix_cfg(fw, TensixRegs.ECC_SCRUBBER_ADDR32, TensixRegs.ECC_SCRUBBER_SCRUB_ON_ERROR_MASK, 1, shift=1)
  rmw_tensix_cfg(
    fw, TensixRegs.ECC_SCRUBBER_ADDR32, TensixRegs.ECC_SCRUBBER_DELAY_MASK, 0x100,
    shift=TensixRegs.ECC_SCRUBBER_DELAY_SHAMT,
  )
  for sem in (TensixSem.MATH_PACK, TensixSem.UNPACK_TO_DEST, TensixSem.MATH_DONE):
    fw.push_tensix_word(buf, TTSEMINIT(sem_sel=TensixSem.mask(sem), init_value=0, max_value=1).raw_word())
  return fw

def build(*, text_base: dict[str, int] = Firmware.TEXT_BASE) -> KernelBase:
  fw = Kernel(Tensix, Noc, Cb, base_addr=Firmware.TEXT_BASE["brisc"])
  fw.segment(Firmware.LOCAL_DATA_BASE["brisc"], b"\x68".ljust(Firmware.LOCAL_DATA_SIZE["brisc"], b"\0"), label="local_data")
  fw.configure_csr()
  fw.setup_stack(Firmware.BRISC_STACK_TOP)

  # set_subordinate_reset_pcs
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, text_base["ncrisc"])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, text_base["trisc0"])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, text_base["trisc1"])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, text_base["trisc2"])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)

  # device_setup
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  # enable_noc_clock_gating
  for noc in range(2):
    for reg in (NocCfg.NIU_CFG_0, NocCfg.ROUTER_CFG_0):
      cfg = NOC.CFG_BASE + reg * 4 + (noc << NOC.INSTANCE_OFFSET_BIT)
      fw.li(t0, cfg)
      fw.lw(t1, t0, 0)
      fw.ori(t1, t1, 1)
      fw.sw(t1, t0, 0)
  fw.zero_words(TensixL1.MEM_ZEROS_BASE, TensixL1.MEM_ZEROS_SIZE // 4)
  # invalidate_all_risc_icaches
  fw.write32(TensixRegs.RISCV_IC_INVALIDATE_INVALIDATE_ALL, TensixRegs.RISCV_IC_ALL_MASK)
  tensix_hw_reset(fw)

  # init_risc_noc_coords
  fw.init_risc_noc_coords(BM.MY_X, BM.MY_Y)

  # init_bank_tables
  fw.init_bank_tables(BM.DRAM_BANK_TO_NOC_XY)

  # init_brisc_mailbox_globals
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=t1, tmp_val=t0)
  fw.write8(BM.NOC_INDEX, 0, tmp_addr=t1, tmp_val=t0)
  fw.write8(BM.BRISC_NOC_MODE, 0, tmp_addr=t1, tmp_val=t0)
  fw.li(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(t0, t1, 0)
  fw.write8(BM.MY_LOGICAL_X, t0, tmp_addr=t1)
  fw.li(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(t0, t1, 0)
  fw.write8(BM.MY_LOGICAL_Y, t0, tmp_addr=t1)
  fw.write32(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0, tmp_addr=t1, tmp_val=t0)

  noc_init(fw)
  init_noc_local_state(fw)
  # invalidate_all_risc_icaches
  fw.write32(TensixRegs.RISCV_IC_INVALIDATE_INVALIDATE_ALL, TensixRegs.RISCV_IC_ALL_MASK)
  # init_subordinate_sync
  fw.write32(Mailbox.SUBORDINATE_SYNC, RunSync.ALL_INIT)
  # deassert_all_riscs
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in (1, 2, 3, 4):
    fw.wait8(Mailbox.SUBORDINATE_SYNC + role - 1, RunSync.DONE)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE)
  # Ask TRISC0 to clear CB sync registers before launching kernels.
  fw.write8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.INIT_SYNC_REGISTERS)
  fw.wait8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.DONE)

  fw.label("run_loop")

  # wait_go
  wait_go_loop = fw._new_label("wait_go")
  check_reset_host = fw._new_label("check_reset_host")
  check_replay = fw._new_label("check_replay")
  reset_ptr = fw._new_label("reset_launch_ptr")
  reset_ptr_notify = fw._new_label("reset_launch_ptr_notify")
  go_seen = fw._new_label("go_seen")
  fw.li(t0, Mailbox.GO_SIGNAL)
  fw.label(wait_go_loop)
  fw.lbu(t1, t0, 0)
  fw.li(t2, RunMsg.GO)
  fw.beq(t1, t2, go_seen)
  fw.li(t2, RunMsg.RESET_READ_PTR)
  fw.beq(t1, t2, reset_ptr_notify)
  fw.label(check_reset_host)
  fw.li(t2, RunMsg.RESET_READ_PTR_FROM_HOST)
  fw.beq(t1, t2, reset_ptr)
  fw.label(check_replay)
  fw.li(t2, RunMsg.REPLAY_TRACE)
  fw.beq(t1, t2, reset_ptr_notify)
  fw.fence()
  fw.j(wait_go_loop)
  fw.label(reset_ptr_notify)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=t0, tmp_val=t2)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE, tmp_addr=t0, tmp_val=t2)
  notify_dispatch_core_done(fw)
  fw.li(t0, Mailbox.GO_SIGNAL)
  fw.fence()
  fw.j(wait_go_loop)
  fw.label(reset_ptr)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, 0, tmp_addr=t0, tmp_val=t2)
  fw.li(t0, Mailbox.GO_SIGNAL)
  fw.fence()
  fw.j(wait_go_loop)
  fw.label(go_seen)
  fw.fence()

  # Per-launch Tensix reset: kernels must start from cold-boot state, not the
  # previous program's CFG/DEST/semaphore residue (back-to-back differing CB
  # layouts corrupted outputs deterministically before this).
  tensix_hw_reset(fw)

  # Match tt-metal: let NCRISC start loading its launch state before BRISC does
  # the rest of per-launch firmware setup.
  signal_subordinate_if_enabled(fw, 1, RunSync.LOAD)

  # init_brisc_kernel_config
  fw.current_launch_ptr(launch=t0, tmp=t4)
  fw.lw(t1, t0, Launch.KERNEL_CONFIG_BASE)
  for i in range(3):
    fw.lhu(t2, t0, Launch.SEM_OFFSET + 2 * i)
    fw.add(t3, t1, t2)
    fw.write32(BM.SEM_L1_BASE + 4 * i, t3, tmp_addr=t4)
  fw.lhu(t2, t0, Launch.RTA_OFFSET)
  fw.add(t3, t1, t2)
  fw.write32(BM.RTA_L1_BASE_PTR, t3, tmp_addr=t4)
  fw.lhu(t2, t0, Launch.RTA_OFFSET + 2)
  fw.add(t3, t1, t2)
  fw.write32(BM.CRTA_L1_BASE_PTR, t3, tmp_addr=t4)

  # init_brisc_launch_globals
  keep_launch_noc = fw._new_label("keep_launch_noc")
  fw.current_launch_ptr(launch=t0, tmp=t2)
  fw.lbu(t1, t0, Launch.BRISC_NOC_ID)
  fw.bne(t1, zero, keep_launch_noc)
  fw.lw(t1, t0, Launch.ENABLES)
  fw.andi(t1, t1, 1 << 1)
  fw.beq(t1, zero, keep_launch_noc)
  fw.li(t1, 1)
  fw.label(keep_launch_noc)
  fw.sb(t1, t0, Launch.BRISC_NOC_ID)
  fw.write8(BM.NOC_INDEX, t1, tmp_addr=t2)
  fw.lbu(t1, t0, Launch.BRISC_NOC_MODE)
  fw.write8(BM.BRISC_NOC_MODE, t1, tmp_addr=t2)
  fw.li(t2, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(t1, t2, 0)
  fw.write8(BM.MY_LOGICAL_X, t1, tmp_addr=t2)
  fw.lbu(t3, t0, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(t1, t1, t3)
  fw.write8(BM.MY_RELATIVE_X, t1, tmp_addr=t2)
  fw.li(t2, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(t1, t2, 0)
  fw.write8(BM.MY_LOGICAL_Y, t1, tmp_addr=t2)
  fw.lbu(t3, t0, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(t1, t1, t3)
  fw.write8(BM.MY_RELATIVE_Y, t1, tmp_addr=t2)

  noc_init(fw)
  init_noc_local_state(fw)
  # invalidate_all_risc_icaches
  fw.write32(TensixRegs.RISCV_IC_INVALIDATE_INVALIDATE_ALL, TensixRegs.RISCV_IC_ALL_MASK)

  # Match tt-metal run_triscs(): TRISC0 owns CB sync-register init and BRISC
  # waits here before sending GO to the TRISC trio.
  fw.wait8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.DONE)
  for role in (2, 3, 4):
    signal_subordinate_if_enabled(fw, role, RunSync.GO)

  # setup_local_cbs
  fw.setup_local_cbs(BM.CB_INTERFACE)

  signal_subordinate_if_enabled(fw, 1, RunSync.GO)
  fw.run_launch_kernel(0)
  for role in (1, 2, 3, 4):
    fw.wait8(Mailbox.SUBORDINATE_SYNC + role - 1, RunSync.DONE)
  # Ask TRISC0 to clear CB sync registers before accepting the next launch.
  fw.write8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.INIT_SYNC_REGISTERS)
  fw.wait8(Mailbox.SUBORDINATE_SYNC + 1, RunSync.DONE)
  fw.write8(Mailbox.GO_SIGNAL, RunMsg.DONE)
  notify_dispatch_core_done(fw)
  fw.read32(t0, Mailbox.LAUNCH_MSG_RD_PTR, tmp_addr=t1)
  fw.addi(t0, t0, 1)
  fw.andi(t0, t0, 7)
  fw.write32(Mailbox.LAUNCH_MSG_RD_PTR, t0, tmp_addr=t1)
  fw.j("run_loop")
  return fw
