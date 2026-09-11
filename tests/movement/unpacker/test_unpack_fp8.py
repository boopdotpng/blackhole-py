"""FP8 E4M3 input expansion, using an independent FP32 observation."""
import pytest
from asm import Asm
from tests import fp8
from tests.movement.unpacker import unpack as u
from tests.movement.unpacker.test_unpack import INPUT_A, INPUT_B, OUTPUT_A, OUTPUT_B


@pytest.mark.parametrize('output_format', (u.F32, u.FP8_E4M3), ids=('fp32-out', 'fp8-out'))
@pytest.mark.parametrize('bank', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('seed', (
  0, 91, pytest.param(-1, id='subnormals', marks=pytest.mark.xfail(
    strict=True, raises=AssertionError,
    reason='Blackhole E4M3 unpack does not preserve standard subnormals',
  )),
))
def test_fp8_source_bank(bh, bank, seed, output_format):
  source = bytes(range(16)) * 64 if seed == -1 else fp8.normal_tile(seed)
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  u.clear_sources(loader)
  u.emit_unpack_to_src(loader, INPUT_A, bank, input_format=u.FP8_E4M3)
  u.emit_copy_src_to_dst(math, bank, 0, input_format=u.FP8_E4M3)
  u.publish_dst(math)
  u.emit_pack_dst(packer, 0, OUTPUT_A, output_format, source_format=u.FP16, dst_fp32=False)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: source, OUTPUT_A: b'\xa5' * (4096 + 64)})
  expected = fp8.as_f32(source) if output_format == u.F32 else source
  assert bh.read_l1(bh.core, OUTPUT_A, len(expected)) == expected
  assert bh.read_l1(bh.core, OUTPUT_A + len(expected), 4160 - len(expected)) == b'\xa5' * (4160 - len(expected))


def test_fp8_parallel_source_banks(bh):
  a, b = fp8.normal_tile(3), fp8.normal_tile(91)
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  u.clear_sources(loader)
  u.emit_unpack_pair(loader, INPUT_A, INPUT_B, input_format=u.FP8_E4M3)
  u.emit_copy_src_to_dst(math, u.UnpackTarget.SRCA, 0, release=1, input_format=u.FP8_E4M3)
  u.emit_copy_src_to_dst(math, u.UnpackTarget.SRCB, 1, release=2, wait_for_dst=False, input_format=u.FP8_E4M3)
  u.publish_dst(math)
  u.emit_pack_dst(packer, 0, OUTPUT_A, u.F32, source_format=u.FP16, dst_fp32=False)
  u.emit_pack_dst(packer, 1, OUTPUT_B, u.F32, configure=False, wait_for_dst=False)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: a, INPUT_B: b, OUTPUT_A: bytes(8192)})
  assert bh.read_l1(bh.core, OUTPUT_A, 4096) == fp8.as_f32(a)
  assert bh.read_l1(bh.core, OUTPUT_B, 4096) == fp8.as_f32(b)


def test_fp8_reference_known_encodings():
  assert fp8.decode(0x38) == 1.0
  assert fp8.decode(0xB8) == -1.0
  assert fp8.decode(0x01) == 2**-9
  assert fp8.decode(0x08) == 2**-6
  assert fp8.decode(0x7E) == 448.0
  assert fp8.encode([0., 1., -1., 448., 1.0625, 1.1875]) == bytes((0, 0x38, 0xB8, 0x7E, 0x38, 0x3A))
