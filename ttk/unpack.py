from enum import IntEnum

from ttk.tensix import Cfg, MopCfg, Tensix, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixState, TensixWait, ThreadCfg, nop_word, tt_word

class UnpackFormat(IntEnum):
  F32, F16 = 0, 1
  BF16, BFP4 = 5, 7
  INT32, UINT16, INT8, UINT32, UINT8 = 8, 9, 14, 24, 30

UNPACK_SRC_A_MOP = MopCfg.unpack_src_a_tile()
# ROW broadcast unpacks SrcB once per face row and rewinds its Z counter while
# SrcA advances through both faces.
UNPACK_ROW_BROADCAST_MOP = MopCfg.slots(
  outer=2, inner=2, fill=nop_word(),
  slot1=tt_word("TTSETADCZW", 2, 0, 0, 0, 0, 1),
  slot3=tt_word("TTUNPACR", 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
  slot4=tt_word("TTUNPACR", 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
  slot5=tt_word("TTUNPACR", 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
  slot6=tt_word("TTUNPACR", 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
)

class Unpack:
  def __init__(self, kernel, *, state: TensixState | None = None): self.k, self.tensix = kernel, Tensix(kernel, 0, state)

  @staticmethod
  def _cb(cb): return int(cb.addr), int(cb.dtype), int(cb.page_size)

  def init(self, source_cb, *, fp32_dest=False, mop_cfg=UNPACK_SRC_A_MOP):
    addr, fmt, tile_bytes = self._cb(source_cb)
    if addr & 15 or tile_bytes <= 0 or tile_bytes & 15: raise ValueError("unpack CB must be 16-byte aligned")
    if fmt not in set(UnpackFormat): raise ValueError(f"unsupported unpack format {fmt}")
    out = fmt if fmt in (UnpackFormat.F32, UnpackFormat.F16) else UnpackFormat.BF16
    desc, reg2, t = fmt | (0 if fmt == UnpackFormat.BFP4 else 0x10), 0x20 | out, self.tensix
    t.set_thread_cfg(ThreadCfg.CFG_STATE_ID, 0); t.set_thread_cfg(ThreadCfg.UNPACK_MISC_CFG, 0)
    for reg, value in ((Cfg.THCON_SEC0_REG0_TileDescriptor, desc), (Cfg.THCON_SEC0_REG0_TileDescriptor_1, 0x00040001),
      (Cfg.THCON_SEC1_REG0_TileDescriptor, desc | 0x01000000), (Cfg.THCON_SEC1_REG0_TileDescriptor_1, 0x00040001),
      (Cfg.THCON_SEC0_REG2, reg2), (Cfg.THCON_SEC0_REG2_1, 0x000F000F),
      (Cfg.THCON_SEC1_REG2, reg2), (Cfg.THCON_SEC1_REG2_1, 0x000F000F)): t.write_cfg(reg, value)
    t.issue(self.k.tensix_word("TTZEROSRC", 0, 0, 1, 3))
    t.issue(self.k.tensix_word("TTSETADCXY", 3, 0, 0, 0, 0, 0xB)); t.issue(self.k.tensix_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    # Z advances once per 16x16 face. F32 pages therefore need a 1 KiB
    # stride; the old fixed 512-byte value silently overlapped adjacent faces.
    face_bytes = tile_bytes // 4
    t.write_cfg(Cfg.UNP0_ADDR_CTRL_ZW_REG_1, face_bytes); t.write_cfg(Cfg.UNP1_ADDR_CTRL_ZW_REG_1, face_bytes)
    t.rmw_cfg_byte(Cfg.ALU_ACC_CTRL, 0, 3, 1)
    t.rmw_cfg_byte(Cfg.ALU, 3, 0x60, 0x60 if fp32_dest else 0)
    t.issue(self.k.tensix_word("TTSETADCXX", 1, 255, 0)); t.issue(self.k.tensix_word("TTSETADCXX", 2, 255, 0))
    t.write_cfg(Cfg.THCON_SEC0_REG5_Dest_cntx01, 0x00400040); t.write_cfg(Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx01, 0x01000100)
    t.write_cfg(Cfg.UNP0, 0x100); t.set_thread_cfg(ThreadCfg.SRCA_SET, 4)
    for half in (72, 74): t.issue(self.k.tensix_word("TTSETDMAREG", 0, tile_bytes >> 4, 0, half))
    t.configure_mop(mop_cfg); t.sync()
    t.write_cfg(Cfg.THCON_SEC0_REG7_Offset_address, 0)
    self.mop_cfg = mop_cfg; return self

  def init_row_broadcast(self, source_cb, weight_cb):
    if source_cb.dtype != weight_cb.dtype:
      raise ValueError("ROW-broadcast operands must have the same dtype")
    self.init(source_cb, mop_cfg=UNPACK_ROW_BROADCAST_MOP)
    self.weight_cb = weight_cb
    return self

  def wait_config_idle(self): self.tensix.wait_unpack_config_idle(); return self

  def wait_source_clear(self):
    """Wait until math has consumed SrcA before changing its unpack config."""
    self.tensix.stall(TensixStall.UNPACK, TensixWait.SRCA_CLR)
    return self

  def configure_source(self, source_cb):
    if int(source_cb.dtype) not in set(UnpackFormat): raise ValueError(f"unsupported unpack format {source_cb.dtype}")
    with self.k.scope():
      address = self.k.reg(); source_cb.read_ptr(address)
      self.k.srli(address, address, 4); self.k.addi(address, address, -1)
      self.k.write32(Cfg.THCON_SEC0_REG3_Base_address, address)
    return self

  def configure_row_broadcast(self, source_cb, weight_cb=None):
    weight_cb = self.weight_cb if weight_cb is None else weight_cb
    with self.k.scope():
      source, weight = self.k.reg(2)
      source_cb.read_ptr(source); weight_cb.read_ptr(weight)
      self.k.srli(source, source, 4); self.k.addi(source, source, -1)
      self.k.srli(weight, weight, 4); self.k.addi(weight, weight, -1)
      self.k.write32(Cfg.THCON_SEC0_REG3_Base_address, source)
      self.k.write32(Cfg.THCON_SEC1_REG3_Base_address, weight)
    return self

  def commit_config(self):
    self.tensix.commit_unpack_config(Cfg.THCON_SEC0_REG3_Base_address); return self

  def to_src_a(self):
    t = self.tensix
    t.issue(self.k.tensix_word("TTSETADCXX", 1, 255, 0)); t.issue(self.k.tensix_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG); t.run_mop(mop_type=1); return self

  def row_broadcast(self):
    t = self.tensix
    t.issue(self.k.tensix_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG); t.run_mop(mop_type=1)
    return self

  def wait_both(self):
    self.tensix.stall(TensixStall.UNPACK, TensixWait.UNPACK0 | TensixWait.UNPACK1)
    self.tensix.semaphore_get(TensixSem.UNPACK_SYNC).sync()
    return self

  def wait(self):
    self.tensix.stall(TensixStall.UNPACK, TensixWait.UNPACK0)
    self.tensix.semaphore_get(TensixSem.UNPACK_SYNC).sync()
    return self

  def to_dst(self, source_cb):
    """Unpack one tile directly to FP32 Dst, ordered against Math and Pack."""
    t = self.tensix
    source_cb.wait_front(); self.wait_config_idle()
    t.issue(self.k.tensix_word("TTSETC16", int(ThreadCfg.UNPACK_MISC_CFG), 0))
    self.configure_source(source_cb); self.commit_config()
    self.k.write32(TensixRegs.REGFILE_BASE + 0x12 * 4, 0x00400040)
    t.write_cfg_from_gpr(0x12, Cfg.THCON_SEC0_REG5_Dest_cntx01)
    t.issue(self.k.tensix_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.set_thread_cfg(ThreadCfg.SRCA_SET, 0)
    t.rmw_cfg_byte(Cfg.THCON_SEC0_REG2_1, 0, 0x10, 0x10)
    t.semaphore_wait(TensixSem.MATH_DONE, TensixSemWait.STALL_ON_ZERO, stall=TensixStall.UNPACK)
    t.semaphore_get(TensixSem.MATH_DONE)
    t.semaphore_wait(TensixSem.UNPACK_TO_DEST, TensixSemWait.STALL_ON_MAX, stall=TensixStall.UNPACK)
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG | TensixWait.PACK0)
    direct = tt_word("TTUNPACR", 0, 0x11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1)
    for _ in range(4):
      t.issue(direct); t.stall(TensixStall.UNPACK, TensixWait.UNPACK0)
    t.stall(TensixStall.UNPACK, TensixWait.THCON | TensixWait.UNPACK0)
    t.semaphore_get(TensixSem.UNPACK_SYNC).sync()
    t.rmw_cfg_byte(Cfg.THCON_SEC0_REG2_1, 0, 0x10, 0)
    t.set_thread_cfg(ThreadCfg.SRCA_SET, 4)
    t.semaphore_post(TensixSem.UNPACK_TO_DEST)
    source_cb.pop_front()
    return self

  def finish_to_dst(self):
    """Drain a direct-to-Dst stream before a phase boundary or kernel return."""
    self.tensix.sync()
    return self
