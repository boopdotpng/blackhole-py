"""Matmul epilogue: FP32 accumulators -> row-major BF16 rows in DRAM.

After the last K block every output tile holds its FP32 sum in CB16 (packer L1
accumulation, face-major tiles). For each 1xW output subblock:

* TRISC0 unpacks the W tiles straight into FP32 Dst (unpack-to-dest, exact):
  one UNPACR per 256-datum face, Z stepping faces in both L1 and Dst.
* TRISC2 packs them untilized: each PACR reads face-0 row r and face-1 row r
  through two read interfaces in strided Dst mode, so one PACR is one 32-wide
  tile row. Z steps tiles, Y rows, W selects the bottom face pair, and the L1
  destination advances one output row (W*64 bytes) per tile row. The early
  packer conversion rounds FP32 -> BF16 to nearest, ties away from zero (the
  packer's only deterministic rounding; it differs from round-to-nearest-even
  only on exact ties).
* NCRISC writes the subblock's 32 row segments into the row-major output.

Strided Dst reads need Dst address remap + 32-bit swizzle (DEST_ACCESS_CFG),
which changes Dst addressing for every client. TRISC0 enables it only after the
matmul's last pack (and its ZEROACC) is done, and clears it only after the
writer has consumed every page: neither a STALLWAIT on PACK0 nor a TRISC2
tensix_sync proved the packer had stopped reading Dst. Remapped packer Dst
strides count 32-byte units. Probe: tests/probes/test_untilize_epilogue.py;
regression: tests/compute/fpu/test_matmul_epilogue.py.
"""
from ttko.isa import R, Tensix as TT
from ttko.mop import LoopTemplate
from ttko.registers import Cfg, DType, Sem, SemWait, Stall, TensixRegs, ThreadCfg, Wait

OUT_CB = 17
EPILOGUE_SEM = Sem.UNPACK_TO_DEST     # TRISC0 -> TRISC2: "Dst holds the next subblock"
PACK_IDLE_SEM = Sem.MATH_DONE         # TRISC2 -> TRISC0: matmul packs (and their ZEROACCs) are done


def init(fw):
  """TRISC0 prologue: both epilogue semaphores start empty, one slot each."""
  fw.emit(TT.TTSEMINIT(sem_sel=Sem.mask(EPILOGUE_SEM), init_value=0, max_value=1))
  fw.emit(TT.TTSEMINIT(sem_sel=Sem.mask(PACK_IDLE_SEM), init_value=0, max_value=1))

DEST_ACCESS_CFG = TensixRegs.CFG_BASE + 220 * 4
REMAP_SWIZZLE = 3
CFG = TensixRegs.CFG_BASE
F32, BF16 = 0, 5
# Unpacker 0 (section 0) registers, as in tests/movement/unpacker/unpack.py.
UNP_TILE_DESCRIPTOR, UNP_OPTIONS, UNP_DESTINATION, UNP_X_DIMENSION = CFG + 0x100, CFG + 0x120, CFG + 0x150, CFG + 0x158
UNP_ADDRESS_XY0, UNP_ADDRESS_ZW0, UNP_ADDRESS_XY1, UNP_ADDRESS_ZW1 = CFG + 0xB0, CFG + 0xB4, CFG + 0xE0, CFG + 0xE4
UNP_OFFSET, UNP_ADDR_BASE0, UNP_ADDR_BASE1, UNP_ADDR_MISC, UNP_NOP_CLEAR = CFG + 0x170, CFG + 48*4, CFG + 49*4, CFG + 50*4, CFG + 53*4
PACK_ALU_FORMAT, PACK_ADDRESS_XY, PACK_ADDRESS_ZW = CFG + 4, CFG + 0x30, CFG + 0x34
PACK_DESTINATION_READ, PACK_DATA_FORMAT = CFG + 0x48, CFG + 0x118
PACK_ADDRESS_MODIFIER = 37
GPR = 0xFFE00000


def row_bytes(plan):
  return plan.out_subblock_w * 32 * 2


def page_bytes(plan):
  """CB17 page: one subblock's FP32 tiles in CB16, reused for its BF16 rows."""
  return plan.out_subblock_num_tiles * 4096


def check(plan):
  if plan.out_subblock_h != 1:
    raise ValueError('the row-major epilogue packs 1xW subblocks')
  if plan.n_passes != 1:
    raise ValueError('the row-major epilogue needs N_PASSES == 1')


def trisc0(fw, plan):
  """Unpack each subblock's FP32 tiles into Dst tiles 0..W-1."""
  from . import kernel as k
  check(plan)
  w = plan.out_subblock_w
  nsub = plan.in0_num_subblocks * plan.in1_num_subblocks
  mark = lambda code: k.emit_progress_mark(fw, k.DEBUG_TRISC0, code, block_reg=R.S9, i0_reg=R.S9, i1_reg=R.S9)
  fw.li(R.S9, 0)
  mark(0xE300)
  fw.cb_wait_front(fw.data['cb_interface'], 16, plan.out_block_num_tiles)
  mark(0xE301)
  fw.cb_read_ptr(fw.data['cb_interface'], 16, out=R.S0)          # 16-byte units
  fw.emit(TT.TTSEMWAIT(Stall.UNPACK, Sem.mask(PACK_IDLE_SEM), SemWait.STALL_ON_ZERO))
  fw.emit(TT.TTSEMGET(Sem.mask(PACK_IDLE_SEM)))
  fw.tensix_sync(0)
  mark(0xE302)
  fw.write32(DEST_ACCESS_CFG, REMAP_SWIZZLE)
  for register, value in (
    (UNP_TILE_DESCRIPTOR, (F32 & 0xF) | 0x10), (UNP_TILE_DESCRIPTOR + 4, 1 | 4 << 16),
    (UNP_TILE_DESCRIPTOR + 8, 0), (UNP_TILE_DESCRIPTOR + 12, 0),
    (UNP_OPTIONS, 0x20 | F32), (UNP_OPTIONS + 4, 0x03 | 0x30),
    (UNP_ADDRESS_XY0, 0), (UNP_ADDRESS_ZW0, 0),
    (UNP_ADDRESS_XY1, 4 | 64 << 16), (UNP_ADDRESS_ZW1, 1024),   # Dst: one face = 16 FP32 rows
    (UNP_ADDR_BASE0, 0), (UNP_ADDR_BASE1, 0), (UNP_ADDR_MISC, 0x100), (UNP_NOP_CLEAR, 0),
    (UNP_DESTINATION, 64 | 64 << 16), (UNP_X_DIMENSION, 256 | 256 << 16),
    (UNP_OFFSET, 0), (UNP_OFFSET + 4, 0),
  ):
    fw.write32(register, value)
  fw.push_tensix(TT.TTRMWCIB2(0x40, 0, 71))                       # not FP8
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.setc16(ThreadCfg.SRCA_SET, 0)                                # Src row override off for Dst
  fw.emit(TT.TTSETADCXX(1, 255, 0))
  fw.li(R.S9, 0)
  loop, done = fw._new_label('epi0_sub'), fw._new_label('epi0_done')
  fw.label(loop)
  fw.li(R.T0, nsub)
  fw.bge(R.S9, R.T0, done)
  # Wait (Tensix side) for the packer to release Dst, then drain so the RISC
  # base-address write cannot race the previous subblock's unpacks.
  mark(0xE310)
  fw.emit(TT.TTSEMWAIT(Stall.UNPACK, Sem.mask(EPILOGUE_SEM), SemWait.STALL_ON_MAX))
  fw.tensix_sync(0)
  mark(0xE311)
  fw.li(R.T0, w * 4096 // 16)
  fw.mul(R.T1, R.S9, R.T0)
  fw.add(R.T1, R.T1, R.S0)
  fw.addi(R.T1, R.T1, -1)
  fw.write32(Cfg.THCON_SEC0_REG3_Base_address, R.T1)
  fw.write32(Cfg.THCON_SEC0_REG3_Base_cntx1_address, R.T1)
  fw.emit(TT.TTSTALLWAIT(Stall.UNPACK, Wait.TRISC_CFG))
  # The matmul leaves unpacker Y counters walking K (FP8 batched unpack).
  fw.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 0xB))
  fw.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for _ in range(4 * w):
    fw.emit(TT.TTUNPACR(0, 0x11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1))
    fw.emit(TT.TTSTALLWAIT(Stall.UNPACK, Wait.UNPACK0))
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, Wait.UNPACK0))
  fw.emit(TT.TTSEMPOST(Sem.mask(EPILOGUE_SEM)))
  fw.addi(R.S9, R.S9, 1)
  fw.j(loop)
  fw.label(done)
  # Clear the remap only once the writer has consumed every page. Neither a
  # STALLWAIT on PACK0 nor a TRISC2 tensix_sync proves the packer has stopped
  # reading Dst (measured: clearing then corrupts the last subblock), but the
  # writer only sees a page after it is complete.
  from ttko.cb import CB
  fw.li(R.T1, CB.SYNC_TILES_ACKED_BASE + OUT_CB * CB.SYNC_STRIDE)
  fw.li(R.T2, nsub)
  drained = fw._new_label('epi0_pages_written')
  fw.label(drained)
  fw.lhu(R.T3, R.T1, 0)
  fw.bltu(R.T3, R.T2, drained)
  fw.tensix_sync(0)
  fw.write32(DEST_ACCESS_CFG, 0)
  fw.setc16(ThreadCfg.SRCA_SET, 4)
  fw.cb_pop_front(fw.data['cb_interface'], 16, plan.out_block_num_tiles)
  mark(0xE3FF)


def trisc2(fw, plan):
  """Pack each subblock untilized into one CB17 page of 32 BF16 rows."""
  from . import kernel as k
  check(plan)
  w = plan.out_subblock_w
  nsub = plan.in0_num_subblocks * plan.in1_num_subblocks
  mark = lambda code: k.emit_progress_mark(fw, k.DEBUG_TRISC2, code, block_reg=R.S9, i0_reg=R.S9, i1_reg=R.S9)
  fw.li(R.S9, 0)
  mark(0xD300)
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, Wait.PACK0 | Wait.MATH | Wait.THCON))
  fw.tensix_sync(2)
  fw.emit(TT.TTSEMPOST(Sem.mask(PACK_IDLE_SEM)))
  # The last K block packed with L1 accumulation; these packs must overwrite.
  k.emit_pack_reconfig_l1_acc(fw, False)
  # FP32 Dst read, BF16 intermediate (early conversion rounds), BF16 out.
  fw.push_tensix(TT.TTRMWCIB3(Mask=0x1E, Data=BF16 << 1, CfgRegAddr=1))
  fw.write32(PACK_DATA_FORMAT, 1 | BF16 << 4 | BF16 << 8)
  fw.write32(PACK_DESTINATION_READ, 1)
  fw.write32(PACK_ADDRESS_XY, 32 << 16)                            # Y: one FP32 row (remapped units)
  fw.write32(PACK_ADDRESS_ZW, 2048 | 1024 << 16)                   # Z: one tile, W: two faces
  fw.setc16(PACK_ADDRESS_MODIFIER + 0, 1 << 12)                    # z += 1: next tile
  fw.setc16(PACK_ADDRESS_MODIFIER + 1, 1 | 2 << 12)               # y += 1, z = 0: next row
  pacr = lambda mode, last: TT.TTPACR(0, 0, 1, mode, 0, 0, 0b0011, 0, 0, 0, 0, last)
  fw.write_mop_cfg(LoopTemplate(outer=16, inner=w, loop=pacr(0, 0), last=pacr(1, 1),
                                outer_last=pacr(1, 1), end0=TT.TTREPLAY(0, 4)), 2)
  fw.emit(TT.TTREPLAY(0, 4, 0, 1))                                  # advance the L1 row
  fw.emit(TT.TTADDDMAREG(0, 12, 12, 14))
  fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.THCON))
  fw.emit(TT.TTWRCFG(12, 0, Cfg.THCON_SEC0_REG1_L1_Dest_addr.addr32))
  fw.emit(TT.TTNOP())
  fw.write32(GPR + 14 * 4, row_bytes(plan) // 16)
  fw.emit(TT.TTSETADCXX(4, 15, 0))
  for reg in (Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
              Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, Cfg.DEST_TARGET_REG_CFG_PACK_SEC3):
    fw.write32(reg, 0)
  fw.li(R.S9, 0)
  loop, done = fw._new_label('epi2_sub'), fw._new_label('epi2_done')
  fw.label(loop)
  fw.li(R.T0, nsub)
  fw.bge(R.S9, R.T0, done)
  mark(0xD310)
  fw.cb_reserve_back(fw.data['cb_interface'], OUT_CB, 1)
  mark(0xD311)
  fw.cb_write_ptr(fw.data['cb_interface'], OUT_CB, out=R.T1)
  fw.emit(TT.TTSEMWAIT(Stall.TDMA, Sem.mask(EPILOGUE_SEM), SemWait.STALL_ON_ZERO))
  fw.tensix_sync(2)
  mark(0xD312)
  fw.cb_write_ptr(fw.data['cb_interface'], OUT_CB, out=R.T1)
  fw.addi(R.T1, R.T1, -1)
  fw.write32(GPR + 12 * 4, R.T1)
  fw.write32(Cfg.THCON_SEC0_REG1_L1_Dest_addr, R.T1)
  for half in (0, 1):
    fw.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB))
    fw.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    fw.emit(TT.TTSETADC(4, 0, 3, half))
    fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.PACK0 | Wait.THCON))
    fw.emit(TT.TTMOP(1, 0, 0))
  # Release Dst and publish the page only once the packer has fully drained:
  # a STALLWAIT on PACK0 alone can pass while PACRs are still reading Dst.
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, Wait.PACK0))
  fw.tensix_sync(2)
  fw.emit(TT.TTSEMGET(Sem.mask(EPILOGUE_SEM)))
  fw.cb_push_back(fw.data['cb_interface'], OUT_CB, 1)
  fw.addi(R.S9, R.S9, 1)
  fw.j(loop)
  fw.label(done)
  fw.tensix_sync(2)
  fw.tensix_sync(2)
  mark(0xD3FF)


def writer(fw, plan):
  """NCRISC: write each CB17 page's 32 rows into the row-major output.

  Output row pitch is a whole number of 2048-byte pages (columns padded to a
  multiple of 1024), and every row segment is W*64 bytes at a W*64-aligned
  column, so a segment never crosses a DRAM page.
  """
  from . import kernel as k
  from ttko.registers import NcriscMailbox as NM
  check(plan)
  w = plan.out_subblock_w
  pitch_pages = output_columns(plan) * 2 // 2048
  k.emit_output_write_state_setup(fw, length=row_bytes(plan))
  fw.arg(R.S0, 18)    # C base
  fw.arg(R.T0, 19)    # first output tile index (row-major tile grid, nt per row)
  fw.arg(R.S11, 29)   # DRAM bank count (S11 is the arg pointer: read it last)
  fw.mul(R.S8, R.S8, R.S11)       # S8: output NoC's offset into the bank table
  fw.li(R.T1, plan.nt)
  fw.divu(R.S1, R.T0, R.T1)       # tile row
  fw.remu(R.S2, R.T0, R.T1)       # tile column
  fw.slli(R.S1, R.S1, 5)          # S1: first global row of this core
  fw.slli(R.S2, R.S2, 6)          # S2: first column byte of this core
  fw.li(R.S4, 0)                  # i0
  i0_loop, i0_done = fw._new_label('wr_i0'), fw._new_label('wr_i0_done')
  fw.label(i0_loop)
  fw.li(R.T0, plan.in0_num_subblocks)
  fw.bge(R.S4, R.T0, i0_done)
  fw.li(R.S5, 0)                  # i1
  i1_loop, i1_done = fw._new_label('wr_i1'), fw._new_label('wr_i1_done')
  fw.label(i1_loop)
  fw.li(R.T0, plan.in1_num_subblocks)
  fw.bge(R.S5, R.T0, i1_done)
  k.emit_progress_mark(fw, k.DEBUG_NCRISC_OUTPUT, 0xB310, block_reg=R.S4, i0_reg=R.S4, i1_reg=R.S5)
  fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB, 1)
  k.emit_progress_mark(fw, k.DEBUG_NCRISC_OUTPUT, 0xB311, block_reg=R.S4, i0_reg=R.S4, i1_reg=R.S5)
  fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=R.S6)   # NCRISC CB pointers are bytes
  fw.slli(R.S7, R.S4, 5)
  fw.add(R.S7, R.S7, R.S1)        # S7: global row of this subblock's row 0
  fw.li(R.T0, row_bytes(plan))
  fw.mul(R.S3, R.S5, R.T0)
  fw.add(R.S3, R.S3, R.S2)        # S3: column byte of this subblock
  fw.li(R.S10, 32)
  row_loop = fw._new_label('wr_row')
  fw.label(row_loop)
  fw.li(R.T0, pitch_pages)
  fw.mul(R.A1, R.S7, R.T0)
  fw.srli(R.T0, R.S3, 11)
  fw.add(R.A1, R.A1, R.T0)        # page index
  fw.mv(R.A0, R.S0)
  fw.mv(R.A2, R.S11)
  fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, R.S8, tile_bytes=2048)
  fw.andi(R.T0, R.S3, 2047)
  fw.add(R.A0, R.A0, R.T0)
  k.emit_output_write_stateful(fw, R.S6, R.A0, R.A2)
  fw.addi(R.S6, R.S6, row_bytes(plan))
  fw.addi(R.S7, R.S7, 1)
  fw.addi(R.S10, R.S10, -1)
  fw.bne(R.S10, R.ZERO, row_loop)
  fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB, 1)
  fw.addi(R.S5, R.S5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(R.S4, R.S4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)


def output_columns(plan):
  """Row-major output row length in elements: padded to whole DRAM pages."""
  return -(-plan.nt * 32 // 1024) * 1024
