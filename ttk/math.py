from ttk.sfpu import Sfpu
from ttk.tensix import Cfg, MopCfg, Tensix, TensixSem, TensixStall, TensixState, TensixWait, ThreadCfg, tt_word

MATH_COPY_SRC_A_MOP = MopCfg.copy_src_a_to_dst()

class Math:
  pipe = 1

  def __init__(self, kernel, *, state: TensixState | None = None):
    self.tensix = Tensix(kernel, self.pipe, state); self.sfpu = Sfpu(self.tensix)
    self.mop_cfg = None

  def _set_dst_mode(self, fp32=False, int8=False):
    self.tensix.rmw_cfg_byte(Cfg.ALU, 3, 0xE0, (0x60 if fp32 else 0) | (0x80 if int8 else 0)); return self

  def set_fp32_dest(self, enabled):
    self.tensix.stall(TensixStall.CFG, TensixWait.MATH | TensixWait.SFPU)
    return self._set_dst_mode(fp32=enabled)

  def _configure_copy_addressing(self):
    t = self.tensix
    for reg, value in ((ThreadCfg.ADDR_MOD_AB_SEC3, 0), (ThreadCfg.ADDR_MOD_DST_SEC3, 0),
      (ThreadCfg.ADDR_MOD_BIAS_SEC3, 0), (ThreadCfg.ADDR_MOD_AB_SEC0, 1),
      (ThreadCfg.ADDR_MOD_DST_SEC0, 1), (ThreadCfg.ADDR_MOD_BIAS_SEC0, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC2, 8), (ThreadCfg.ADDR_MOD_DST_SEC2, 8),
      (ThreadCfg.ADDR_MOD_BIAS_SEC2, 0), (ThreadCfg.CLR_DVALID, 0)): t.set_thread_cfg(reg, value)
    t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF))

  def initialize(self, *, fp32_dest=False, int8_math=False, mop_cfg=MATH_COPY_SRC_A_MOP):
    t = self.tensix; t.set_thread_cfg(ThreadCfg.CFG_STATE_ID, 0); self._set_dst_mode(fp32_dest, int8_math)
    for reg, value in ((ThreadCfg.DISABLE_IMPLIED_SRCA_FMT, 0), (ThreadCfg.DISABLE_IMPLIED_SRCB_FMT, 0),
      (ThreadCfg.DEST_TARGET_REG_CFG_MATH, 0), (ThreadCfg.ADDR_MOD_AB_SEC1, 0),
      (ThreadCfg.ADDR_MOD_DST_SEC1, 0), (ThreadCfg.ADDR_MOD_BIAS_SEC1, 0)): t.set_thread_cfg(reg, value)
    t.issue(tt_word("TTZEROACC", 3, 0, 0, 1, 0))
    t.write_cfg(Cfg.DEST_ACCESS_CFG, t.state.cfg(1, Cfg.DEST_ACCESS_CFG) & ~8)
    self._configure_copy_addressing(); self.sfpu.initialize(); t.configure_mop(mop_cfg); t.stall(TensixStall.CFG, TensixWait.MATH)
    self.mop_cfg = mop_cfg; return self

  def copy_src_a_to_dst(self, destination_offset=0):
    self.tensix.set_thread_cfg(ThreadCfg.DEST_TARGET_REG_CFG_MATH, destination_offset)
    if self.mop_cfg != MATH_COPY_SRC_A_MOP: self.tensix.configure_mop(MATH_COPY_SRC_A_MOP); self.mop_cfg = MATH_COPY_SRC_A_MOP
    self.tensix.run_mop(); return self

  def publish_dst(self): self.tensix.semaphore_post(TensixSem.MATH_PACK); return self
