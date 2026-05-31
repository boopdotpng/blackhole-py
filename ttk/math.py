from __future__ import annotations

from dsl import (
  TTRMWCIB0, TTRMWCIB3, TTSEMINIT, TTSETC16, TTSETRWC, TTSFPCONFIG, TTSFPLOADI,
  TTSTALLWAIT, TTZEROACC,
)
from program import Dtype
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import (
  Cfg, TensixRegs, TensixSem, TensixStall, TensixWait, ThreadCfg,
)

_TILE_NUM_FACES = 4


class Math:
  """Math-thread (TRISC1) configuration helpers, bound to a kernel builder.

  Tier-2 intent over Tier-1 ops, same shape as ``Unpack``/``Pack``. ``dtype``
  drives the src/dst format writes; the addr-mode and SFPU setup are the generic
  FPU/SFPU init that every math kernel shares. The op-specific compute body
  (e.g. the add1 SFP loop) stays in the kernel, not here."""

  def __init__(self, kernel):
    self.k = kernel

  def _local_state(self, k, dtype: Dtype):
    # Make initial context writes visible, publish operand formats, then wait
    # until the unpack side reports its context is idle.
    k.tensix_sync(1)
    k.write_repeated_bytes(TLM.TRISC1_UNPACK_TILE_NUM_FACES, _TILE_NUM_FACES, 8)
    k.write32(TLM.TRISC1_UNPACK_DST_FORMAT, dtype.value)
    k.write32(TLM.TRISC1_UNPACK_SRC_FORMAT, dtype.value)
    k.setc16(ThreadCfg.ADDR_MOD_AB_SEC1_Src, 0)
    k.setc16(ThreadCfg.ADDR_MOD_DST_SEC1, 0)
    k.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC1_Bias, 0)
    k.emit(TTZEROACC(3, 0, 0, 1, 0))
    k.wait_mmio_low_byte_zero(TensixRegs.PC_UNPACK_SYNC)

  def _sfpu_init(self, k):
    k.emit(TTSFPLOADI(0, 0, 10))
    k.emit(TTSFPLOADI(0, 0, 8))
    k.emit(TTSFPCONFIG(0, 15, 1))
    k.setc16(ThreadCfg.ADDR_MOD_AB_SEC7_Src, 0)
    k.setc16(ThreadCfg.ADDR_MOD_DST_SEC7, 0)
    k.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC7_Bias, 0)
    k.emit(TTSETRWC(0, 0, 0, 0, 0, 15))

  def init(self, *, dtype: Dtype = Dtype.Float16_b, mop_cfg):
    """Configure the math thread: operand formats, mova2d addr modes, the math
    MOP template, the MATH_PACK semaphore, dest-access config and SFPU setup.
    Mirrors the TRISC1 init block of add1 exactly."""
    k = self.k

    self._local_state(k, dtype)
    k.math_direct_mova2d_init()
    k.write_mop_cfg(mop_cfg, 1)
    k.tensix_sync(1)

    k.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
    k.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=1))
    k.push_tensix(TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0))
    k.push_tensix(TTRMWCIB0(Mask=0x08, Data=0x08, CfgRegAddr=Cfg.DEST_ACCESS_CFG.addr32))
    k.write32(k.data["dest_offset_id"], 0)
    k.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH))
    k.push_tensix(TTRMWCIB3(Mask=0x80, Data=0x00, CfgRegAddr=Cfg.ALU.addr32))

    k.math_direct_mova2d_init()
    k.write_mop_cfg(mop_cfg, 1)
    self._sfpu_init(k)
    return k
