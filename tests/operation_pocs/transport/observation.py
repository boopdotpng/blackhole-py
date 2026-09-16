"""Fixture-only full-bank observation after tested Dst guards are captured."""
from ttko.isa import Tensix as TT
from tests.movement.unpacker import unpack as u


def copy_source(k, bank, tile):
  u.configure_fp32_dst(k, 0)
  for register in (12, 28, 47): u._set_thread_cfg(k, register, 0)
  k.emit(TT.TTSETRWC(0,0,0,0,0,0xF))
  u.stall(k,u.Stall.MATH,u.Wait.SRCA_VLD if bank == u.UnpackTarget.SRCA else u.Wait.SRCB_VLD)
  step=8 if bank == u.UnpackTarget.SRCA else 4
  for row in range(0,64,step):
    k.emit(TT.TTMOVA2D(0,row,0,2,tile*64+row) if bank == u.UnpackTarget.SRCA else TT.TTMOVB2D(0,row,0,4,tile*64+row))
  u.stall(k,u.Stall.SYNC,u.Wait.MATH)
  u.pc_sync(k)
