from ttk.sfpu import Sfpu
from ttk.mop import LoopTemplate
from ttk.tensix import Cfg, Tensix, TensixSem, TensixSemWait, TensixStall, TensixState, TensixWait, ThreadCfg, tt_word

_MATH_MOVE = tt_word("TTMOVA2D", 0, 0, 2, 2, 0)
MATH_COPY_SRC_A_MOP = LoopTemplate(
  outer=4, inner=2, loop=_MATH_MOVE,
  end0=tt_word("TTSETRWC", 3, 0, 0, 0, 0, 3),
  last=_MATH_MOVE, outer_last=_MATH_MOVE,
)
MATH_ROW_BROADCAST_MUL_HIFI2_MOP = LoopTemplate(
  outer=2, inner=2,
  loop=tt_word("TTELWMUL", 0, 0, 2, 0, 0),
  last=tt_word("TTELWMUL", 3, 0, 2, 3, 0),
  outer_last=tt_word("TTELWMUL", 0, 0, 2, 2, 0),
)

class Math:
  pipe = 1

  def __init__(self, kernel, *, state: TensixState | None = None):
    self.tensix = Tensix(kernel, self.pipe, state); self.sfpu = Sfpu(self.tensix)
    self.mop_cfg = None; self.fp32_dest = False

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
    t = self.tensix; self.fp32_dest = fp32_dest
    t.set_thread_cfg(ThreadCfg.CFG_STATE_ID, 0); self._set_dst_mode(fp32_dest, int8_math)
    for reg, value in ((ThreadCfg.DISABLE_IMPLIED_SRCA_FMT, 0), (ThreadCfg.DISABLE_IMPLIED_SRCB_FMT, 0),
      (ThreadCfg.DEST_TARGET_REG_CFG_MATH, 0), (ThreadCfg.ADDR_MOD_AB_SEC1, 0),
      (ThreadCfg.ADDR_MOD_DST_SEC1, 0), (ThreadCfg.ADDR_MOD_BIAS_SEC1, 0)): t.set_thread_cfg(reg, value)
    t.issue(tt_word("TTZEROACC", 3, int(fp32_dest), 0, 1, 0))
    t.write_cfg(Cfg.DEST_ACCESS_CFG, t.state.cfg(1, Cfg.DEST_ACCESS_CFG) & ~8)
    self._configure_copy_addressing(); self.sfpu.initialize(); t.configure_mop(mop_cfg); t.stall(TensixStall.CFG, TensixWait.MATH)
    self.mop_cfg = mop_cfg; return self

  def initialize_scalar_reduce(self, *, fp32_dest=False):
    self.initialize(fp32_dest=fp32_dest)
    t = self.tensix
    for reg, value in (
      (ThreadCfg.ADDR_MOD_AB_SEC0, 0), (ThreadCfg.ADDR_MOD_DST_SEC0, 0x8000),
      (ThreadCfg.ADDR_MOD_BIAS_SEC0, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC1, 0), (ThreadCfg.ADDR_MOD_DST_SEC1, 0x2000),
      (ThreadCfg.ADDR_MOD_BIAS_SEC1, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC2, 0x0800), (ThreadCfg.ADDR_MOD_DST_SEC2, 8),
      (ThreadCfg.ADDR_MOD_BIAS_SEC2, 0), (ThreadCfg.CLR_DVALID, 0),
    ): t.set_thread_cfg(reg, value)
    t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF))
    return self

  def clear_dst(self):
    self.tensix.issue(tt_word("TTZEROACC", 3, int(self.fp32_dest), 0, 0, 0)); return self

  def scalar_reduce(self, destination_offset=0):
    t = self.tensix
    t.issue(tt_word("TTSETC16", int(ThreadCfg.DEST_TARGET_REG_CFG_MATH), destination_offset))
    for face in range(4):
      for _ in range(3): t.issue(tt_word("TTGAPOOL", 0, 1, 1, 0, 4))
      t.issue(tt_word("TTGAPOOL", 3 if face != 3 else 0, 1, 0, 0, 4))
    t.issue(tt_word("TTSETRWC", 0, 4, 0, 0, 0, 3))
    t.issue(tt_word("TTMOVD2B", 0, 16, 0, 0, 4))
    t.issue(tt_word("TTGATESRCRST", 1, 1))
    t.issue(tt_word("TTTRNSPSRCB"))
    t.issue(tt_word("TTGATESRCRST", 1, 1))
    for offset in (0, 4, 8, 12): t.issue(tt_word("TTMOVB2A", offset, 0, 2, 16 + offset))
    t.issue(tt_word("TTGATESRCRST", 1, 1))
    t.issue(tt_word("TTZEROACC", 0, 0, 0, 0, 4))
    for _ in range(3): t.issue(tt_word("TTGAPOOL", 0, 1, 1, 0, 0))
    t.issue(tt_word("TTGAPOOL", 3, 1, 0, 0, 0))
    return self

  def copy_src_a_to_dst(self, destination_offset=0):
    self.set_destination_offset(destination_offset)
    if self.mop_cfg != MATH_COPY_SRC_A_MOP: self.tensix.configure_mop(MATH_COPY_SRC_A_MOP); self.mop_cfg = MATH_COPY_SRC_A_MOP
    self.tensix.stall(TensixStall.MATH, TensixWait.SRCA_VLD)
    self.tensix.run_mop(); return self

  def set_destination_offset(self, offset):
    if type(offset) is not int or not 0 <= offset < 1 << 12:
      raise ValueError("math destination offset must fit in 12 bits")
    self.tensix.set_thread_cfg(ThreadCfg.DEST_TARGET_REG_CFG_MATH, offset)
    return self

  def configure_row_broadcast_mul_hifi2(self):
    t = self.tensix
    t.configure_mop(MATH_ROW_BROADCAST_MUL_HIFI2_MOP); self.mop_cfg = MATH_ROW_BROADCAST_MUL_HIFI2_MOP
    for reg, value in (
      (ThreadCfg.ADDR_MOD_AB_SEC0, 0x0008), (ThreadCfg.ADDR_MOD_DST_SEC0, 0x0008),
      (ThreadCfg.ADDR_MOD_BIAS_SEC0, 0), (ThreadCfg.ADDR_MOD_AB_SEC2, 0x8080),
      (ThreadCfg.ADDR_MOD_DST_SEC2, 0x2400), (ThreadCfg.ADDR_MOD_BIAS_SEC2, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC3, 0x8080), (ThreadCfg.ADDR_MOD_DST_SEC3, 0x9008),
      (ThreadCfg.ADDR_MOD_BIAS_SEC3, 0),
    ): t.set_thread_cfg(reg, value)
    return self

  def row_broadcast_mul_hifi2(self):
    t = self.tensix; self.set_destination_offset(0)
    t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF))
    t.issue(tt_word("TTZEROACC", 3, 0, 0, 1, 0))
    t.stall(TensixStall.MATH, TensixWait.SRCA_VLD | TensixWait.SRCB_VLD)
    for _ in range(4): t.run_mop()
    t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 0xF))
    t.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    return self

  def acquire_dst(self):
    self.tensix.semaphore_wait(
      TensixSem.MATH_PACK, TensixSemWait.STALL_ON_MAX,
      stall=TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU,
    )
    return self

  def publish_dst(self):
    self.tensix.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    self.tensix.semaphore_post(TensixSem.MATH_PACK)
    return self

  def wait_for_direct_unpack(self):
    """Request and acquire a tile produced by TRISC0's direct-to-Dst path."""
    self.tensix.semaphore_wait(
      TensixSem.MATH_DONE, TensixSemWait.STALL_ON_MAX, stall=TensixStall.SYNC,
    )
    self.tensix.semaphore_post(TensixSem.MATH_DONE)
    self.tensix.semaphore_wait(
      TensixSem.UNPACK_TO_DEST, TensixSemWait.STALL_ON_ZERO, stall=TensixStall.SYNC,
    )
    self.tensix.semaphore_get(TensixSem.UNPACK_TO_DEST)
    self.tensix.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    return self
