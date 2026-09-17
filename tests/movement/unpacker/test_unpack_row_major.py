"""Native FP8 tilization into complete SrcA/SrcB column panels."""
import numpy as np
import pytest

from asm import Asm
from examples.matmul_peak_kernel.kernel import row_major_unpack_ops
from tests import fp8
from tests.movement.unpacker import unpack as u
from tests.movement.unpacker.test_unpack import INPUT_A
from ttko.isa import Tensix as TT

OUTPUT_A = INPUT_A + 0x10000


@pytest.mark.parametrize('bank', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('width,column', ((32, 0), (64, 16), (96, 32), (320, 128), (576, 256)))
def test_fp8_row_major_panels(bh, monkeypatch, bank, width, column):
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
  expected = np.concatenate((values[:, column:column+16].flatten(),
                             values[:, column+16:column+32].flatten()))
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  engine = int(bank)
  cfg = lambda reg: u._engine_cfg(reg, engine)
  u.clear_sources(loader)
  u.configure_unpacker(loader, engine, INPUT_A + column, u.FP8_E4M3, bank)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR), 0x1a | 16 << 16)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR) + 4, 1 | 1 << 16)
  loader.write(cfg(u.UnpackCfg.X_DIMENSION), 16 | 16 << 16)
  loader.write(cfg(u.UnpackCfg.ADDRESS_ZW1), 512)
  loader.write(cfg(u.UnpackCfg.OPTIONS), 0x2a | 1 << 9 | (width // 16) << 16)
  loader.emit(TT.TTSETADCXX(engine + 1, 511, 0))
  loader.emit(TT.TTSETADCXY(engine + 1, 0, 0, 0, 0, 10))
  u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR if engine == 0 else u.Wait.SRCB_CLR)
  for word in row_major_unpack_ops(engine): loader.emit(word)
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0 if engine == 0 else u.Wait.UNPACK1)
  if engine == 0: loader.emit(u._srcb_dvalid())
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)
  u.emit_copy_src_to_dst(math, bank, 0, release=3 if engine == 0 else 2, input_format=u.FP8_E4M3)
  u.publish_dst(math)
  u.emit_pack_dst(packer, 0, OUTPUT_A, u.F32, source_format=u.FP16, dst_fp32=False)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: raw, OUTPUT_A: bytes(4096)})
  actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT_A, 4096), '<f4')
  np.testing.assert_array_equal(actual, expected)
