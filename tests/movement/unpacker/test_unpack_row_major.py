"""Native FP8/BF16 tilization into complete SrcA/SrcB column panels."""
import numpy as np
import pytest

from asm import Asm
from examples.matmul_peak_kernel import kernel as peak
from tests import fp8
from tests.movement.unpacker import unpack as u
from tests.movement.unpacker.test_unpack import INPUT_A
from ttko.isa import Tensix as TT

OUTPUT_A = INPUT_A + 0x10000


@pytest.mark.parametrize('dtype', ('fp8', 'bf16'))
@pytest.mark.parametrize('bank', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('width,column', ((32, 0), (64, 16), (96, 32), (320, 128), (576, 256)))
def test_row_major_panels(bh, monkeypatch, bank, width, column, dtype):
  # The matmul handoff publishes all 64 source rows at once. Observe that bank
  # without the usual copy helper's per-face dvalid releases.
  def copy_bank(k, bank, release):
    move = TT.TTMOVA2D(0, 0, 2, 2, 0) if bank == u.UnpackTarget.SRCA else TT.TTMOVB2D(0, 0, 2, 4, 0)
    u.configure_mop(k, u._mop_loop_words(
      1, 8 if bank == u.UnpackTarget.SRCA else 16, loop=move, last=move,
      outer_last=move, end0=TT.TTSETRWC(release, 0, 0, 0, 0, 3)))
  monkeypatch.setattr(u, '_configure_copy_mop', copy_bank)
  raw = b''.join(fp8.normal_tile(i) for i in range(width // 32))
  values = np.frombuffer(fp8.as_f32(raw), '<f4').reshape(32, width)
  itemsize = 1 if dtype == 'fp8' else 2
  fmt = u.FP8_E4M3 if dtype == 'fp8' else u.BF16
  if dtype == 'bf16':
    codes = np.arange(width*32, dtype=np.uint16) + 0x3000
    raw = codes.tobytes()
    values = (codes.astype(np.uint32) << 16).view(np.float32).reshape(32, width)
  expected = np.concatenate((values[:, column:column+16].flatten(),
                             values[:, column+16:column+32].flatten()))
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  engine = int(bank)
  cfg = lambda reg: u._engine_cfg(reg, engine)
  u.clear_sources(loader)
  u.configure_unpacker(loader, engine, INPUT_A + column * itemsize, fmt, bank)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR), (0x10 | fmt) | 16 << 16)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR) + 4, (1 if dtype == "fp8" else width // 16) | 1 << 16)
  loader.write(cfg(u.UnpackCfg.X_DIMENSION), 16 | 16 << 16)
  loader.write(cfg(u.UnpackCfg.ADDRESS_ZW1), 512 if dtype == "fp8" else 32)
  loader.write(cfg(u.UnpackCfg.OPTIONS), (0x20 | fmt) | (1 << 9 | (width // 16) << 16 if dtype == "fp8" else 0))
  loader.emit(TT.TTSETADCXX(engine + 1, 511 if dtype == "fp8" else 15, 0))
  loader.emit(TT.TTSETADCXY(engine + 1, 0, 0, 0, 0, 10))
  u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR if engine == 0 else u.Wait.SRCB_CLR)
  monkeypatch.setattr(peak, 'INPUT_DTYPE', peak.DType.FP8 if dtype == 'fp8' else peak.DType.BF16)
  if dtype == 'bf16':
    loader.emit(TT.TTREPLAY(engine*8, 8, 0, 1))
    for _ in range(8): loader.emit(TT.TTUNPACR(engine,0x11,0,0,0,1,0,0,0,0,0,0,1))
  for word in peak.row_major_unpack_ops(engine): loader.emit(word)
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0 if engine == 0 else u.Wait.UNPACK1)
  if engine == 0: loader.emit(u._srcb_dvalid())
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)
  u.emit_copy_src_to_dst(math, bank, 0, release=3 if engine == 0 else 2, input_format=fmt)
  u.publish_dst(math)
  u.emit_pack_dst(packer, 0, OUTPUT_A, u.F32, source_format=u.FP16 if dtype == "fp8" else u.F32, dst_fp32=dtype == "bf16")
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: raw, OUTPUT_A: bytes(4096)})
  actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT_A, 4096), '<f4')
  np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize('bank', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('width,column', ((32, 0), (96, 32), (544, 256)))
def test_bf16_whole_tile_tileize(bh, monkeypatch, bank, width, column):
  """tt-llk's Blackhole BF16 tilize: one UNPACR, x_dim covering the whole tile,
  row pitch in the tileize shift field. Blackhole tileize reads 32 16-bit datums
  per L1 row, so Src row 2r+h holds tile row r, columns 16h..16h+15: the two
  halves interleave. tt-llk's packer de-interleaves them afterwards."""
  def copy_bank(k, bank, release):
    move = TT.TTMOVA2D(0, 0, 2, 2, 0) if bank == u.UnpackTarget.SRCA else TT.TTMOVB2D(0, 0, 2, 4, 0)
    u.configure_mop(k, u._mop_loop_words(
      1, 8 if bank == u.UnpackTarget.SRCA else 16, loop=move, last=move,
      outer_last=move, end0=TT.TTSETRWC(release, 0, 0, 0, 0, 3)))
  monkeypatch.setattr(u, '_configure_copy_mop', copy_bank)
  codes = (np.arange(width*32, dtype=np.uint32) % 0x3000 + 0x3000).astype(np.uint16)
  values = (codes.astype(np.uint32) << 16).view(np.float32).reshape(32, width)
  tile = values[:, column:column+32]
  expected = tile.flatten()   # row r's two halves land in Src rows 2r and 2r+1
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  engine = int(bank)
  cfg = lambda reg: u._engine_cfg(reg, engine)
  u.clear_sources(loader)
  u.configure_unpacker(loader, engine, INPUT_A + column * 2, u.BF16, bank)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR), (0x10 | u.BF16) | 1024 << 16)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR) + 4, 1 | 1 << 16)
  loader.write(cfg(u.UnpackCfg.X_DIMENSION), 1024 | 1024 << 16)
  loader.write(cfg(u.UnpackCfg.OPTIONS), (0x20 | u.BF16) | 1 << 9 | (width * 2 // 16) << 16)
  # SETADCXY with Ch1_X in its mask zeroes the x-end, so set the x-end last.
  loader.emit(TT.TTSETADCXY(engine + 1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCZW(engine + 1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCXX(engine + 1, 1023, 0))
  u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR if engine == 0 else u.Wait.SRCB_CLR)
  loader.emit(TT.TTUNPACR(engine, 0x1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1))
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0 if engine == 0 else u.Wait.UNPACK1)
  if engine == 0: loader.emit(u._srcb_dvalid())
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)
  u.emit_copy_src_to_dst(math, bank, 0, release=3 if engine == 0 else 2, input_format=u.BF16)
  u.publish_dst(math)
  u.emit_pack_dst(packer, 0, OUTPUT_A, u.F32, source_format=u.F32, dst_fp32=True)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: codes.tobytes(), OUTPUT_A: bytes(4096)})
  actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT_A, 4096), '<f4')
  if not np.array_equal(actual, expected):
    rows = actual.reshape(64, 16)
    lookup = {float(v): (r, c) for (r, c), v in np.ndenumerate(values)}
    layout = [[lookup.get(float(x), '?') for x in row[::15]] for row in rows]
    raw_rows = (actual.view(np.uint32) >> 16).reshape(64, 16)
    raise AssertionError('Src rows (first,last datum):\n' + '\n'.join(f'{i}: {l} {[hex(x) for x in raw_rows[i][:4]]}' for i, l in enumerate(layout[:20])) + f'\ninput row0 {[hex(x) for x in codes[:4]]} row1 {[hex(x) for x in codes[width:width+4]]}')
