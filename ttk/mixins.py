from __future__ import annotations

from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, zero
from ttk.abi import LAUNCH, RUNTIME
from ttk.hw.mmio import MMIO
from ttk.hw.noc import NOC


class RvMixin:
  def write32(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    if isinstance(value, int):
      self.li(tmp_val, value)
      value = tmp_val
    return self.sw(value, addr, 0)

  def read32(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    return self.lw(dst, addr, 0)

  def write8(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    if isinstance(value, int):
      self.li(tmp_val, value)
      value = tmp_val
    return self.sb(value, addr, 0)

  def read8(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    return self.lbu(dst, addr, 0)

  def read16(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    return self.lhu(dst, addr, 0)

  def zero_words(self, addr: int, words: int, *, ptr: Reg = t0, count: Reg = t1):
    from asm import cond

    self.li(ptr, addr)
    self.li(count, words)
    with self.loop():
      self.break_(cond(count, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(count, count, -1)
    return self

  def zero_word_range(self, start: int, end: int, *, ptr: Reg = t0, limit: Reg = t1):
    self.li(ptr, start)
    self.li(limit, end)
    loop = self._new_label("zero_words")
    done = self._new_label("zero_words_done")
    self.label(loop)
    self.bgeu(ptr, limit, done)
    self.sw(zero, ptr, 0)
    self.addi(ptr, ptr, 4)
    self.j(loop)
    self.label(done)
    return self

  def copy_words(self, dst: int | Reg, src: int | Reg, byte_count: int | Reg, *,
                 dst_reg: Reg = t0, src_reg: Reg = t1, value: Reg = t2,
                 count: Reg = t3, word: Reg | None = None):
    if word is not None:
      value = word
    if isinstance(dst, int):
      self.li(dst_reg, dst)
      dst = dst_reg
    if isinstance(src, int):
      self.li(src_reg, src)
      src = src_reg
    if isinstance(byte_count, int):
      self.li(count, byte_count // 4)
      byte_count = count
    else:
      self.srli(byte_count, byte_count, 2)
    loop = self._new_label("copy_words")
    done = self._new_label("copy_done")
    self.label(loop)
    self.beq(byte_count, zero, done)
    self.lw(value, src, 0)
    self.sw(value, dst, 0)
    self.addi(src, src, 4)
    self.addi(dst, dst, 4)
    self.addi(byte_count, byte_count, -1)
    self.j(loop)
    self.label(done)
    return self

  def delay_cycles(self, cycles: int, *, count: Reg = t0):
    from asm import cond

    self.li(count, cycles)
    with self.loop():
      self.break_(cond(count, "==", zero))
      self.addi(count, count, -1)
    return self


class FlowMixin:
  def wait8(self, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
    self.li(ptr, addr)
    self.li(expected, value)
    start = self._new_label("wait8")
    done = self._new_label("wait8_done")
    self.label(start)
    self.lbu(actual, ptr, 0)
    self.beq(actual, expected, done)
    self.fence()
    self.j(start)
    self.label(done)
    self.fence()
    return self

  def wait32(self, addr: int, value: int, *, actual: Reg = t0, expected: Reg = t1):
    self.li(expected, value)
    loop = self._new_label("wait32")
    self.label(loop)
    self.read32(actual, addr)
    self.bne(actual, expected, loop)
    return self

  def signal8(self, addr: int, value: int):
    return self.write8(addr, value)

  def invalidate_l1_cache(self):
    return self.fence()

  def setup_stack(self, stack_top: int):
    return self.li(sp, stack_top)

  def current_launch_ptr(self, launch: Reg = t0, tmp: Reg = t1):
    return self.li(launch, LAUNCH.base)

  def configure_csr(self, *, value: Reg = t0):
    self.li(value, 2)
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 2)
    self.csrrc(zero, value, 0x7C0)
    self.fence()
    self.fence()
    self.li(value, 8)
    self.csrrs(zero, value, 0x7C0)
    return self

  def wait_go(self):
    return self.wait8(RUNTIME.go_signal, RUNTIME.run_msg_go)

  def signal_done(self):
    return self.signal8(RUNTIME.go_signal, RUNTIME.run_msg_done)

  def signal_subordinate_go(self, role_index: int):
    return self.signal8(RUNTIME.subordinate_sync + role_index - 1, RUNTIME.run_msg_go)

  def signal_subordinate_done(self, role_index: int):
    return self.signal8(RUNTIME.subordinate_sync + role_index - 1, RUNTIME.run_msg_done)

  def wait_subordinate_go(self, role_index: int):
    return self.wait8(RUNTIME.subordinate_sync + role_index - 1, RUNTIME.run_msg_go)

  def wait_subordinate_done(self, role_index: int):
    return self.wait8(RUNTIME.subordinate_sync + role_index - 1, RUNTIME.run_msg_done)

  def launch_kernel_enabled(self, role_index: int, *, enabled: Reg = t0, mask: Reg = t1):
    self.current_launch_ptr(enabled)
    self.lw(enabled, enabled, LAUNCH.enables)
    self.li(mask, 1 << role_index)
    return self.and_(enabled, enabled, mask)

  def run_launch_kernel(self, role_index: int, *, launch: Reg = t0, config_base: Reg = t1,
                        offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
    skip = self._new_label("skip_kernel")
    self.launch_kernel_enabled(role_index, enabled=enabled, mask=offset)
    self.beq(enabled, zero, skip)
    self.current_launch_ptr(launch)
    self.lw(config_base, launch, LAUNCH.kernel_config_base)
    self.lw(offset, launch, LAUNCH.kernel_text_offset + 4 * role_index)
    self.add(entry, config_base, offset)
    self.jalr(ra, entry, 0)
    self.label(skip)
    return self


class NocMixin:
  def write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write32(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def read_reg(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read32(dst, addr, tmp_addr=tmp_addr)

  def noc_write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write_reg(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def noc_read_reg(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read_reg(dst, addr, tmp_addr=tmp_addr)

  def noc_set_active_instance(self, noc: int):
    self.active_noc = noc
    return self

  def set_subordinate_reset_pcs(self, *, ncrisc: int, trisc0: int, trisc1: int, trisc2: int):
    self.write_reg(MMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, ncrisc)
    self.write_reg(MMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, trisc0)
    self.write_reg(MMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, trisc1)
    self.write_reg(MMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, trisc2)
    self.write_reg(MMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
    self.write_reg(MMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
    return self

  def deassert_all_riscs(self):
    return self.write_reg(MMIO.RISCV_DEBUG_REG_SOFT_RESET_0, MMIO.SOFT_RESET_NONE)

  def noc_cmd_addr(self, noc: int, buf: int, reg: int) -> int:
    return reg + (buf << NOC.CMD_BUF_OFFSET_BIT) + (noc << NOC.INSTANCE_OFFSET_BIT)

  def noc_cmd_reg(self, noc: int, buf: int, reg: int, value: int | Reg, *, addr: Reg = t0, tmp: Reg = t1):
    return self.write32(self.noc_cmd_addr(noc, buf, reg), value, tmp_addr=addr, tmp_val=tmp)

  def noc_wait_cmd_ready(self, noc: int, buf: int, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, self.noc_cmd_addr(noc, buf, NOC.CMD_CTRL))
    loop = self._new_label("noc_ready")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bne(val, zero, loop)
    return self

  def noc_wait_write_acks(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("wr_ack")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self

  def noc_write_barrier(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.noc_wait_write_acks(noc, target, addr=addr, val=val)
    return self.fence()

  def noc_read(self, noc: int, buf: int, src_lo: Reg, src_mid: int | Reg, src_coord: int | Reg,
               dst: Reg, length: Reg, *, ret_coord: int | Reg = 0, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_RD_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, src_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, src_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_write(self, noc: int, buf: int, src: Reg, dst_lo: Reg, dst_mid: int | Reg, dst_coord: Reg,
                length: Reg, *, mcast: bool = False, mcast_linked: bool = False,
                num_dests: Reg | None = None, posted: bool = False, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    if mcast:
      ctrl = NOC.CMD_WR_MCAST_LINKED_FIELD if mcast_linked else NOC.CMD_WR_MCAST_UNLINK_FIELD
    else:
      ctrl = NOC.CMD_WR_POSTED_FIELD if posted else NOC.CMD_WR_FIELD
    self.noc_cmd_reg(noc, buf, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_inline_write(self, noc: int, buf: int, value: Reg, dst_lo: Reg,
                       dst_mid: int | Reg, dst_coord: Reg, *, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_DATA, value, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_INLINE_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, 0xF, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_wait_atomic_responses(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_ATOMIC_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("atomic_resp")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self

  def noc_atomic_inc(self, noc: int, buf: int, dst_lo: Reg, dst_coord: int | Reg,
                     incr: Reg | int, ret_coord: int, *, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, 4, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_AT_INC_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, NOC.AT_INCR_GET, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_DATA, incr, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self


class TensixMixin:
  def tensix_push_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0):
    self.li(tmp, word)
    return self.write32(instrn_buf, tmp)

  def push_tensix_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0):
    return self.tensix_push_word(instrn_buf, word, tmp=tmp)

  def tensix_set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.write32(cfg_base + offset_words * 4, value)

  def set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.tensix_set_cfg_reg(cfg_base, offset_words, value)

  def tensix_reset_cfg_state_id(self, addr: int):
    return self.write32(addr, 0)

  def reset_cfg_state_id(self, addr: int):
    return self.tensix_reset_cfg_state_id(addr)


class CbMixin:
  def clear_cb_sync_registers(self, tiles_received_base: int, tiles_acked_base: int, count: int = 64,
                              *, ptr: Reg = t0, remaining: Reg = t1):
    from asm import cond

    self.li(ptr, tiles_received_base)
    self.li(remaining, count)
    with self.loop():
      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)

    self.li(ptr, tiles_acked_base)
    self.li(remaining, count)
    with self.loop():
      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)
    return self
