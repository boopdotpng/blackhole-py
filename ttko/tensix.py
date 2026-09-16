from ttko.mop import LoopTemplate
from ttko.isa import R, Tensix as TT
from ttko.registers import TensixRegs, ThreadCfg
class TensixOps:
  def tt_raw(self, inst) -> int:
    return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF

  def push_tensix(self, word: int | object, *, tmp_addr: R = R.T0, tmp_val: R = R.T1):
    # Push a Tensix instruction to the instruction buffer at runtime via MMIO.
    # Takes a raw Tensix word; needed when the word is built at runtime. For a
    # word known at build time, prefer emit() which embeds it inline (rotated).
    return self.write32(TensixRegs.INSTRN_BUF_BASE, self.tt_raw(word), tmp_addr=tmp_addr, tmp_val=tmp_val)

  def setc16(self, reg: int, value: int):
    # Set a thread-cfg register (ThreadCfg.*). SETC16 is the ONLY way to write
    # this write-only, per-thread config space (no MMIO address, no read-back).
    # Build-time emit; for a runtime write use push_tensix(TTSETC16(reg, value)).
    return self.emit(TT.TTSETC16(int(reg), value))

  def mop_sync(self, trisc_id: int = 0, *, tmp: R = R.T0):
    self.write32(TensixRegs.PC_BUF_MOP_SYNC, 0, tmp_addr=R.T0, tmp_val=R.T1)
    self.read32(tmp, TensixRegs.PC_BUF_MOP_SYNC, tmp_addr=R.T1)
    return self.and_(R.ZERO, R.ZERO, tmp)

  def write_mop_cfg(self, cfg: LoopTemplate | list[int] | tuple[int, ...], trisc_id: int = 0, *, ptr: R = R.T0, tmp: R = R.T1):
    words = cfg.words() if isinstance(cfg, LoopTemplate) else list(cfg)
    self.mop_sync(trisc_id, tmp=tmp)
    self.li(ptr, TensixRegs.MOP_CFG)
    for i, word in enumerate(words):
      self.li(tmp, word)
      self.sw(tmp, ptr, i * 4)
    return self

  def tensix_sync(self, trisc_id: int = 0, *, tmp: R = R.T0):
    self.write32(TensixRegs.PC_BUF_SYNC, 0, tmp_addr=R.T0, tmp_val=R.T1)
    self.read32(tmp, TensixRegs.PC_BUF_SYNC, tmp_addr=R.T1)
    return self.and_(R.ZERO, R.ZERO, tmp)

  def write_repeated_bytes(self, addr: int, value: int, count_words: int, *, ptr: R = R.T0, tmp: R = R.T1):
    byte = value & 0xFF
    self.li(ptr, addr)
    self.li(tmp, byte | (byte << 8) | (byte << 16) | (byte << 24))
    for i in range(count_words):
      self.sw(tmp, ptr, i * 4)
    return self

  def wait_mmio_low_byte_zero(self, addr: int, *, ptr: R = R.T0, tmp: R = R.T1):
    done = self._new_label("wait_mmio_zero_done")
    loop = self._new_label("wait_mmio_zero")
    self.li(ptr, addr)
    self.label(loop)
    self.lw(tmp, ptr, 0)
    self.andi(tmp, tmp, 0xFF)
    self.beq(tmp, R.ZERO, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self

  def math_direct_mova2d_init(self):
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC3_Src, 0)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC3, 0)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC3_Bias, 0)
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 1)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 1)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, 8)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 8)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
    self.setc16(ThreadCfg.CLR_DVALID_Src, 0)
    return self.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
