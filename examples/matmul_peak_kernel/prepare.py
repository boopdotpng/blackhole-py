"""Prepare each row-major BF16 block once per K block, then reuse packed panels.

One non-tileize UNPACR per L1 row (eight per tile) feeds Dst, and a
Dst-remapped pack writes 32x16 column panels at four PACRs per tile.
tt-metal's one-UNPACR Blackhole tilize was measured slower here: it leaves the
row halves interleaved in Src, and de-interleaving them costs 32 PACRs per
tile (tests/probes/test_bf16_tilize.py).
"""
from dataclasses import replace
from ttko.isa import R, Tensix as TT
from ttko.registers import Cfg, DType, Sem, SemWait, Stall, TensixRegs, ThreadCfg, Wait, TriscLocalMem as TLM
from ttko.pack import BlockedPack


def barrier(fw, phase):
  from . import kernel as k
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, (Wait.UNPACK0 | Wait.UNPACK1, Wait.MATH | Wait.SFPU, Wait.PACK0 | Wait.THCON)[fw.thread_id] | Wait.CFGEXU | Wait.TRISC_CFG | Wait.THCON))
  fw.tensix_sync(fw.thread_id)
  fw.slli(R.T4, R.S6, 3)
  fw.addi(R.T4, R.T4, phase)
  fw.write32(k.PASS_BASE + 96 + fw.thread_id * 4, R.T4)
  fw.fence()
  for thread in range(3):
    loop = fw._new_label('prepare_barrier')
    fw.label(loop)
    fw.fence()
    fw.read32(R.T1, k.PASS_BASE + 96 + thread * 4)
    fw.bltu(R.T1, R.T4, loop)
  fw.fence()


def block(fw, plan):
  from . import kernel as k
  from ttko.mop import LoopTemplate
  if k.INPUT_DTYPE != DType.BF16: return
  role = fw.thread_id
  k.emit_profile_accum_start(fw, k.PROFILE_BASE + 0x180 + role*4)
  barrier(fw, 1)
  if role == 2: k.emit_profile_accum_start(fw, k.PROFILE_BASE + 0x190)
  if role == 0:
    fw.unpack.input_format(DType.BF16, engines=(0,))
    fw.write32(Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx, 32 | 32 << 16)
    fw.write32(Cfg.UNP0_ADDR_CTRL_ZW_REG_1, 256)
    fw.emit(TT.TTSETADCXY(1, 0, 0, 0, 0, 11))
  elif role == 1:
    fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 8)
    fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 16)
    fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
    fw.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    fw.write32(fw.data['dest_offset_id'], 0)
    fw.write32(TensixRegs.CFG_BASE + 220*4, 3)
  else:
    k.emit_pack_reconfig_l1_acc(fw, False)
    advance = TT.TTINCADCZW(4, 0, 0, 1, 0)
    BlockedPack(fw).init(dtype=DType.BF16, out_cb=2, mop_cfg=LoopTemplate(
      outer=1, inner=1, loop=TT.TTREPLAY(0,16), alternate=advance,
      last=advance, outer_last=advance, end0=TT.TTREPLAY(16,4)))
    loaded = fw._new_label('prepare_pack_replay_loaded')
    fw.bne(R.S6, R.ZERO, loaded)
    fw.emit(TT.TTREPLAY(0,16,0,1))
    for row in range(16):
      fw.emit(TT.TTPACR(DstAccessMode=1, AddrMode=2 if row==15 else 1 if row==7 else 0, Last=int(row==15)))
    fw.emit(TT.TTREPLAY(16,4,0,1))
    fw.emit(TT.TTADDDMAREG(0,12,12,14))
    fw.emit(TT.TTSTALLWAIT(Stall.CFG,Wait.THCON))
    fw.emit(TT.TTWRCFG(12,0,Cfg.THCON_SEC0_REG1_L1_Dest_addr.addr32))
    fw.emit(TT.TTNOP())
    for slot, last in ((20, TT.TTPACR(AddrMode=2)), (24, TT.TTPACR(AddrMode=1, Last=1))):
      fw.emit(TT.TTREPLAY(slot,4,0,1))
      for _ in range(3): fw.emit(TT.TTPACR())
      fw.emit(last)
    fw.label(loaded)
    fw.write32(0xffe00000+14*4,128)
    fw.write32(TensixRegs.CFG_BASE + 12*4, 2048 << 16)
    fw.write32(TensixRegs.CFG_BASE + 13*4, 32 | 64 << 16)
    fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC0, 1 | 4 << 6)
    fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC1, 1 << 5 | 1 << 12 | 4 << 6)
    fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC2, 1 << 5 | 1 << 13 | 1 << 11)
    fw.push_tensix(TT.TTRMWCIB3(Mask=0x20, Data=0, CfgRegAddr=Cfg.ALU.addr32))
  barrier(fw, 2)
  if role == 1: fw.emit(TT.TTZEROACC(3, 0, 0, 1, 0))
  barrier(fw, 3)
  if role == 2:
    k.emit_profile_accum_end(fw, k.PROFILE_COUNTER_BASE + 0x40, k.PROFILE_BASE + 0x190)
    k.emit_profile_accum_start(fw, k.PROFILE_BASE + 0x190)
  if role == 2:
    fw.write32(0xffe00000+13*4, 512)
    fw.write32(0xffe00000+15*4, 0)
  for cb, rows, width in ((0, plan.per_core_m, plan.in0_block_w),
                           (1, plan.in0_block_w, plan.per_core_n)):
    if role == 0:
      fw.cb_wait_front(fw.data['cb_interface'], cb, rows*width)
      fw.cb_read_ptr(fw.data['cb_interface'], cb, out=R.S0)
      if width % 2: fw.addi(R.S0, R.S0, 4)
      fw.write32(int(Cfg.THCON_SEC0_REG0_TileDescriptor)+4,
                 k.input_row_pitch(width)//64 | 16 << 16)
    if role == 2:
      fw.cb_reserve_back(fw.data['cb_interface'], cb+2, rows*width)
      fw.cb_write_ptr(fw.data['cb_interface'], cb+2, out=R.T1)
      fw.addi(R.T1, R.T1, -1)
      fw.write32(0xffe00000+12*4, R.T1)
      fw.write32(Cfg.THCON_SEC0_REG1_L1_Dest_addr, R.T1)
    fw.li(R.S9, 0)
    row_loop = fw._new_label('prepare_rows')
    fw.label(row_loop)
    for column in range(0, width, 4):
      group = min(4, width-column)
      if role == 0:
        fw.tensix_sync(0)
        fw.emit(TT.TTSETADCXX(1, group*32-1, 0))
        fw.li(R.T0, width*k.input_page_bytes(width)//16)
        fw.mul(R.T1, R.S9, R.T0)
        fw.add(R.T1, R.T1, R.S0)
        fw.addi(R.T1, R.T1, column*4-1)
        fw.write32(Cfg.THCON_SEC0_REG3_Base_address, R.T1)
        fw.write32(Cfg.THCON_SEC0_REG3_Base_cntx1_address, R.T1)
        fw.emit(TT.TTSTALLWAIT(Stall.UNPACK, Wait.TRISC_CFG))
        fw.emit(TT.TTSETADCXY(1, 0, 0, 0, 0, 11))
        fw.emit(TT.TTSETADCZW(1, 0, 0, 0, 0, 15))
        for _ in range(4): fw.emit(TT.TTREPLAY(12,8))
      elif role == 1:
        fw.emit(TT.TTSEMWAIT(k.STALL_MATH_PACK_ROOM, Sem.mask(Sem.MATH_PACK), SemWait.STALL_ON_MAX))
        fw.read32(R.T1, fw.data['dest_offset_id'])
        fw.slli(R.T1, R.T1, 9)
        fw.li(R.T2, TT.TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0))
        fw.add(R.T1, R.T1, R.T2)
        fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
        fw.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
        for _ in range(4): fw.emit(TT.TTREPLAY(0,9))
        k.emit_math_subblock_commit(fw)
      else:
        fw.emit(TT.TTSEMWAIT(k.STALL_MATH_PACK_DATA, Sem.mask(Sem.MATH_PACK), SemWait.STALL_ON_ZERO))
        fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.PACK0 | Wait.THCON))
        for reg in (Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
                    Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, Cfg.DEST_TARGET_REG_CFG_PACK_SEC3):
          fw.emit(TT.TTWRCFG(15, 0, reg.addr32))
        fw.emit(TT.TTSETADC(4, 0, 3, 0))
        fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.THCON))
        fw.emit(TT.TTMOP(1, 0, group << 10))
        fw.emit(TT.TTSTALLWAIT(Stall.THCON, Wait.PACK0))
        fw.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
        fw.emit(TT.TTSEMGET(Sem.mask(Sem.MATH_PACK)))
        fw.emit(TT.TTSUBDMAREG(0, 15, 15, 13))
    if role == 0: fw.tensix_sync(0)
    fw.addi(R.S9, R.S9, 1)
    fw.li(R.T0, rows)
    fw.bltu(R.S9, R.T0, row_loop)
    if role == 2:
      fw.tensix_sync(2)
      fw.cb_push_back(fw.data['cb_interface'], cb+2, rows*width, tensix_received=True)
  _restore(fw, plan)


def _restore(fw, plan):
  from . import kernel as k
  role = fw.thread_id
  barrier(fw, 4)
  if role == 2:
    k.emit_profile_accum_end(fw, k.PROFILE_COUNTER_BASE + 0x44, k.PROFILE_BASE + 0x190)
    k.emit_profile_accum_start(fw, k.PROFILE_BASE + 0x190)
  if role == 0:
    fw.cb_pop_front(fw.data['cb_interface'], 0, plan.in0_block_num_tiles)
    fw.cb_pop_front(fw.data['cb_interface'], 1, plan.in1_block_num_tiles)
    fw.unpack.input_format(DType.BF16)
    for engine in (0, 1):
      fw.write32(int(Cfg.THCON_SEC0_REG0_TileDescriptor) + engine * 0xc0 + 0x58, 256 | 256 << 16)
      fw.write32(int(Cfg.UNP0_ADDR_CTRL_ZW_REG_1) + engine * 8, 512)
      fw.emit(TT.TTSETADCXX(engine + 1, 1023, 0))
    fw.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 11))
  elif role == 1:
    fw.write32(fw.data['dest_offset_id'], 0)
    fw.write32(TensixRegs.CFG_BASE + 220*4, 0)
    k.matmul_math_addrmod_init(fw)
  else:
    fw.pack.init(dtype=k.OUTPUT_DTYPE, out_cb=16, mop_cfg=k.matmul_pack_mop_cfg())
    fw.write32(0xffe00000+14*4,k.TILE_BYTES//16)
    fw.push_tensix(TT.TTRMWCIB3(Mask=0x20, Data=0x20, CfgRegAddr=Cfg.ALU.addr32))  # FP32 Dst
  barrier(fw, 5)
  if role == 1: fw.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  barrier(fw, 6)
  if role == 2: k.emit_profile_accum_end(fw, k.PROFILE_COUNTER_BASE + 0x48, k.PROFILE_BASE + 0x190)
  k.emit_profile_accum_end(fw, k.PROFILE_COUNTER_BASE + 0x34 + role*4, k.PROFILE_BASE + 0x180 + role*4)
