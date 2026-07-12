from enum import IntEnum

from ttk.tensix import Cfg, MopCfg, Tensix, TensixStall, TensixState, TensixWait, ThreadCfg


class UnpackFormat(IntEnum):
  F32, F16 = 0, 1
  BF16, BFP4 = 5, 7
  INT32, UINT16, INT8, UINT32, UINT8 = 8, 9, 14, 24, 30


UNPACK_SRC_A_MOP = MopCfg.unpack_src_a_tile()


class Unpack:
  def __init__(self, kernel, *, state: TensixState | None = None): self.k, self.tensix = kernel, Tensix(kernel, 0, state)

  @staticmethod
  def _cb(cb): return int(cb.addr), int(cb.dtype), int(cb.page_size)

  def init(self, source_cb, *, mop_cfg=UNPACK_SRC_A_MOP):
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
    t.write_cfg(Cfg.UNP0_ADDR_CTRL_ZW_REG_1, 0x200); t.write_cfg(Cfg.UNP1_ADDR_CTRL_ZW_REG_1, 0x200)
    t.rmw_cfg_byte(Cfg.ALU_ACC_CTRL, 0, 3, 1)
    t.issue(self.k.tensix_word("TTSETADCXX", 1, 255, 0)); t.issue(self.k.tensix_word("TTSETADCXX", 2, 255, 0))
    t.write_cfg(Cfg.THCON_SEC0_REG5_Dest_cntx01, 0x00400040); t.write_cfg(Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx01, 0x01000100)
    t.write_cfg(Cfg.UNP0, 0x100); t.set_thread_cfg(ThreadCfg.SRCA_SET, 4)
    for half in (72, 74): t.issue(self.k.tensix_word("TTSETDMAREG", 0, tile_bytes >> 4, 0, half))
    t.configure_mop(mop_cfg); t.sync(); t.wait_unpack_config_idle()
    t.write_cfg(Cfg.THCON_SEC0_REG3_Base_address, (addr >> 4) - 1); t.write_cfg(Cfg.THCON_SEC0_REG7_Offset_address, 0)
    t.commit_unpack_config(Cfg.THCON_SEC0_REG3_Base_address)
    self.mop_cfg = mop_cfg; return self

  def to_src_a(self):
    t = self.tensix
    t.issue(self.k.tensix_word("TTSETADCXX", 1, 255, 0)); t.issue(self.k.tensix_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG); t.run_mop(mop_type=1); return self

  def wait(self): self.tensix.stall(TensixStall.UNPACK, TensixWait.UNPACK0); self.tensix.sync(); return self
