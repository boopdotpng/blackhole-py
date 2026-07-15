from ttk.tensix import Cfg, MopCfg, Tensix, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixState, TensixWait, ThreadCfg

PACK_MOP = MopCfg.pack_tile()

class Pack:
  def __init__(self, kernel, *, state: TensixState | None = None): self.k, self.tensix = kernel, Tensix(kernel, 2, state)

  @staticmethod
  def _cb(cb): return int(cb.addr), int(cb.dtype), int(cb.page_size)

  @staticmethod
  def _strides(fmt):
    size = 4 if fmt & 3 == 0 else 2 if fmt & 3 == 1 else 1
    return 16 * size << 16, 256 * size | 1024 * size << 16

  def init(self, output_cb, *, fp32_dest=False, mop_cfg=PACK_MOP):
    addr, dst, page_size = self._cb(output_cb); src, t = (0 if fp32_dest else dst), self.tensix
    if addr & 15 or page_size & 15: raise ValueError("pack CB must be 16-byte aligned")
    t.set_thread_cfg(ThreadCfg.CFG_STATE_ID, 0)
    t.rmw_cfg_byte(Cfg.ALU, 3, 0x1E, 0 if fp32_dest else dst << 1)
    xy, zw = self._strides(src)
    for reg, value in ((Cfg.THCON_SEC0_REG1, 0x00040000), (Cfg.THCON_SEC0_REG1_1, 1 | dst << 4 | src << 8),
      (Cfg.PCK_DEST_RD_CTRL, int(fp32_dest)), (Cfg.PCK0_ADDR_CTRL_XY_REG_0, xy), (Cfg.PCK0_ADDR_CTRL_ZW_REG_0, zw),
      (Cfg.PACK_COUNTERS_SEC0, 0x1000), (Cfg.PACK_COUNTERS_SEC1, 0x1000),
      (Cfg.PACK_COUNTERS_SEC2, 0x1000), (Cfg.PACK_COUNTERS_SEC3, 0x1000),
      (Cfg.PCK_EDGE, 0xFFFF), (Cfg.TILE_ROW_SET_MAPPING_0, 0)): t.write_cfg(reg, value)
    for index in range(4): self.k.write32(TensixRegs.REGFILE_BASE + (8 + index) * 4, 512)
    self.k.write32(TensixRegs.REGFILE_BASE + 16 * 4, page_size >> 4); self.k.write32(TensixRegs.REGFILE_BASE + 52 * 4, 0x40000)
    for section, value in enumerate((0x0104, 0x2820, 0x1120)): t.set_thread_cfg(ThreadCfg.ADDR_MOD_PACK_SEC0 + section, value)
    t.issue(self.k.tensix_word("TTSETADCXY", 4, 0, 0, 0, 0, 0xB)); t.issue(self.k.tensix_word("TTSETADCZW", 4, 0, 0, 0, 0, 0xF))
    t.configure_mop(mop_cfg); t.sync(); self.output_cb = output_cb; return self

  def _program_destination(self):
    t = self.tensix
    with self.k.scope():
      transformed, high, high_valid = self.k.reg(3)
      self.output_cb.write_ptr(transformed)
      self.k.srli(transformed, transformed, 4); self.k.addi(transformed, transformed, -1)
      t.issue(self.k.tensix_word("TTSETADC", 4, 0, 3, 0)); t.set_dma_reg16_from_reg(24, transformed)
      self.k.srli(high, transformed, 16); self.k.li(high_valid, 0x8000); self.k.or_(high_valid, high_valid, high)
      t.set_dma_reg16_from_reg(25, high_valid); t.stall(TensixStall.CFG, TensixWait.THCON | TensixWait.PACK0)
      t.write_cfg_from_gpr(12, Cfg.THCON_SEC0_REG1_L1_Dest_addr)
      t.set_dma_reg16_from_reg(25, high); t.dma_nop()

  def acquire_dst(self):
    self.tensix.semaphore_wait(TensixSem.MATH_PACK, TensixSemWait.STALL_ON_ZERO, stall=TensixStall.TDMA); return self

  def release_dst(self): self.tensix.semaphore_get(TensixSem.MATH_PACK); return self

  def to_cb(self, *, synchronize=True):
    t = self.tensix; self._program_destination()
    t.issue(self.k.tensix_word("TTSETADCXX", 4, 15, 0)); t.issue(self.k.tensix_word("TTSETADCZW", 4, 0, 0, 0, 0, 0xF))
    for reg in (Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
                Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, Cfg.DEST_TARGET_REG_CFG_PACK_SEC3): t.write_cfg(reg, 0)
    t.stall(TensixStall.CFG, TensixWait.PACK0); t.run_mop(mop_type=1)
    t.stall(TensixStall.SYNC, TensixWait.PACK0)
    if synchronize: t.sync()
    return self
