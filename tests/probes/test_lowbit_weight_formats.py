"""Probe: which low-bit weight encodings reach MVMUL bit-exactly on Blackhole?

Each case unpacks a weight operand (every code point of the format) into one
source bank and a one-hot selector into the other, runs a single LoFi MVMUL
per 8 output rows and packs FP32 Dst.  With a one-hot selector each output is
exactly 1.0 * weight, so the FP32 result is the value the FPU multiplied.

Cases:
  e4m3        FP8 E4M3 (LF8 + Unp_LF8_4b_exp) -> FP16 Src, FP16 one-hot SrcB
  e5m2        FP8 E5M2 (LF8 without 4b-exp)    -> FP16 Src, FP16 one-hot SrcB
  e4m3_bf16b  FP8 E4M3 SrcA (FP16) x BF16 one-hot SrcB   (mixed implied formats)
  bf16a_e4m3b BF16 identity SrcA x FP8 E4M3 SrcB         (mixed, swapped)
  e4m3_out_bf16  FP8 E4M3 with Out_data_format = BF16 (doc: undefined; hangs)
  bfp8_eNNN   BFP8 (code 6) with a forced shared exponent; all sign-magnitude
              bytes except 0x80.  Covers int8 [-127,127] and E2M1*2 magnitudes.

Run with -s to see per-case PROBE_LOWBIT records.
"""
import json
import math
import os
import struct

import pytest

from asm import Asm
from firmware.consts import TensixL1
from ttko.isa import Tensix as TT
from tests import fp8
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.operation_pocs.fpu.emit import prepare, execute

INPUT_A = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_B = INPUT_A + 4096
OUTPUT = INPUT_B + 4096
BFP8 = 6
CODES = bytes(range(256)) * 4


def bf16_bits(v):
  return struct.unpack('<I', struct.pack('<f', v))[0] >> 16


def e5m2(code):
  sign = -1 if code & 128 else 1
  exp, man = (code >> 2) & 31, code & 3
  if exp == 31:
    return sign * math.inf if man == 0 else math.nan
  return sign * (man * 2.**-16 if exp == 0 else (1 + man / 4) * 2.**(exp - 15))


def bfp8(code, exponent):
  if code == 0x80: return math.nan
  return (-1 if code & 128 else 1) * (code & 127) / 64 * 2.**(exponent - 127)


def configure(k, engine, kind, address, exponent=0):
  target = (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB)[engine]
  fp8_kind = kind in ('e4m3', 'e5m2', 'e4m3_out_bf16')
  u.configure_unpacker(k, engine, address, u.FP8_E4M3 if fp8_kind else u.BF16, target, commit=False)
  if kind == 'e5m2':
    u._rmw_cfg_byte(k, u.CFG_BASE + (71 + engine * 48) * 4, 2, 0x40, 0)
  if kind == 'e4m3_out_bf16':
    k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine), 0x20 | u.BF16)
  if kind == 'bfp8':
    k.write(u._engine_cfg(u.UnpackCfg.TILE_DESCRIPTOR, engine),
            BFP8 | 0x10 | ((u.FACE_ELEMENTS if engine else 0) << 16))
    k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine), 0x20 | BFP8)
    k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine) + 4, 0x103)  # force shared exponent
    k.write(u.ADDR_MISC[engine], exponent | (0x100 if engine == 0 else 0))


def images(kind_a, kind_b, exponent=0, phases=2):
  loader, math_k, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  u.clear_sources(loader)
  configure(loader, 0, kind_a, INPUT_A, exponent)
  configure(loader, 1, kind_b, INPUT_B, exponent)
  observed = loader.reg()
  loader.read(observed, u._engine_cfg(u.UnpackCfg.BASE, 0))
  loader.write(u.UNPACK_CONFIG_SYNC, 0)
  loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  # 16 rows per bank.  Issued last so nothing clears the X end.  (An X end of
  # 1023 with a BFP input hangs the unpacker; 255 is all MVMUL needs.)
  loader.emit(TT.TTSETADCXX(3, 255, 0))
  u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR | u.Wait.SRCB_CLR)
  u.configure_mop(loader, u._mop_loop_words(
    1, 1, start=u._unpacr(0), loop=u._unpacr(1),
    last=u._unpacr(1), outer_last=u._unpacr(1)))
  u.run_mop(loader)
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0 | u.Wait.UNPACK1)
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)

  u.sem_wait(math_k, u.Sem.MATH_PACK, u.SemWait.ON_MAX, u.Stall.SYNC)
  math_k.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  u.stall(math_k, u.Stall.SYNC, u.Wait.MATH)
  u.configure_fp32_dst(math_k, 0)
  u.stall(math_k, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
  # Two 8-row MVMULs: B rows 8s..8s+7 (slot s) @ A rows 0..15 -> Dst rows 8s..8s+7.
  for slot in (0, 1):
    prepare(math_k, 'mvmul', 0, slot, slot, fidelity=1 if phases == 1 else 2, repeats=1)
    if phases == 4:  # phases 0,1,2,3 (addr mod 1 increments, 2 resets fidelity)
      words = tuple(TT.TTMVMUL(0, 0, mod, slot * 8) for mod in (1, 1, 1, 2))
      u.load_replay(math_k, 0, words)
      replay = TT.TTREPLAY(0, len(words), 0, 0)
      u.configure_mop(math_k, u._mop_loop_words(1, 1, loop=replay, last=replay))
    execute(math_k)
  math_k.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  u.publish_dst(math_k)
  count = packer.reg()
  packer.li(count, 256)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=u.F32)
  return {k.role: k.lower() for k in (loader, math_k, packer)}


def one_hot_b(fmt):
  """B rows 0..15: row r has 1.0 at column r, so Dst row r = 1.0 * A row r."""
  one, zero = (0x38, 0x00) if fmt == 'fp8' else (0x3F80, 0)
  vals = [one if (i < 256 and i // 16 == i % 16) else zero for i in range(1024)]
  return bytes(vals) if fmt == 'fp8' else struct.pack('<1024H', *vals)


def identity_a_bf16():
  return struct.pack('<1024H', *(0x3F80 if (i < 256 and i // 16 == i % 16) else 0 for i in range(1024)))


def bf16_of_e4m3():
  vals = [fp8.decode(c) for c in range(256)]
  return struct.pack('<1024H', *(bf16_bits(0. if math.isnan(v) else v) for v in vals * 4))


def e4m3_subnormal(code): return (code & 0x7F) in range(1, 8)
def e5m2_subnormal(code): return (code & 0x7F) in range(1, 4)
def none(code): return False


# name: (kind_a, kind_b, payload_a, payload_b, decoder, observed scale, codes that read as 0)
CASES = {
  'bf16_control': ('bf16', 'bf16', bf16_of_e4m3(), one_hot_b('bf16'), fp8.decode, 1., none),
  'e4m3': ('e4m3', 'e4m3', CODES, one_hot_b('fp8'), fp8.decode, 1., e4m3_subnormal),
  'e5m2': ('e5m2', 'e4m3', CODES, one_hot_b('fp8'), e5m2, 1., e5m2_subnormal),
  # Mixed implied formats: FP16 SrcA x BF16 SrcB and the reverse.  Observed to
  # be exact up to a power-of-two factor 2^(+-112) = 2^(127-15).
  'e4m3_bf16b': ('e4m3', 'bf16', CODES, one_hot_b('bf16'), fp8.decode, 2.**112, e4m3_subnormal),
  'bf16a_e4m3b': ('bf16', 'e4m3', identity_a_bf16(), CODES, fp8.decode, 2.**-112, e4m3_subnormal),
}


def run(bh, kind_a, kind_b, payload_a, payload_b, exponent=0, phases=2):
  bh.launch(images(kind_a, kind_b, exponent, phases), l1={
    INPUT_A: payload_a, INPUT_B: payload_b, OUTPUT: b'\xa5' * 1088})
  assert bh.read_l1(bh.core, OUTPUT + 1024, 64) == b'\xa5' * 64
  return struct.unpack('<256f', bh.read_l1(bh.core, OUTPUT, 1024))


def classify(actual, expected):
  """Bit-exact compare; NaN/Inf reference codes are reported separately."""
  bad, special = [], []
  for code, (x, y) in enumerate(zip(actual, expected)):
    if not math.isfinite(y):
      special.append((hex(code), x))
    elif struct.pack('<f', x) != struct.pack('<f', y) and not (x == 0 and y == 0):
      bad.append((hex(code), y, x))
  return bad, special


@pytest.mark.parametrize('name', CASES)
def test_fp8_into_mvmul(bh, name):
  kind_a, kind_b, pa, pb, decode, scale, zeroed = CASES[name]
  actual = run(bh, kind_a, kind_b, pa, pb)
  bad, special = classify(actual, [decode(c) * scale for c in range(256)])
  print('PROBE_LOWBIT ' + json.dumps(dict(case=name, mismatches=len(bad), first=bad[:40],
                                          special=special), default=str))
  assert {int(c, 16) for c, *_ in bad} == {c for c in range(256) if zeroed(c)}
  assert all(x == 0 for *_, x in bad)


@pytest.mark.skipif(os.environ.get('PROBE_ALLOW_HANG') != '1',
                    reason='hangs the unpacker on card 0 (CQ timeout; needs a card reset)')
def test_e4m3_out_format_bf16(bh):
  """Doc: FP8 input requires Out_data_format == FP8 (else UndefinedBehavior).
  Observed 2026-10-02 on card 0: the launch never completes (CQ timeout), so
  there is no direct E4M3 -> BF16 unpack.  Set PROBE_ALLOW_HANG=1 to retry."""
  actual = run(bh, 'e4m3_out_bf16', 'bf16', CODES, one_hot_b('bf16'))
  bad, special = classify(actual, [fp8.decode(c) for c in range(256)])
  print('PROBE_LOWBIT ' + json.dumps(dict(case='e4m3_out_bf16', mismatches=len(bad), first=bad[:40],
                                          special=special), default=str))
  ratios = sorted({y / x if x else None for _, x, y in bad if x} - {None})
  print('PROBE_LOWBIT e4m3_out_bf16 ratios', ratios[:8])


@pytest.mark.parametrize('exponent', (133, 12, 250))
def test_bfp8_sign_magnitude_into_mvmul(bh, exponent):
  """BFP8 + forced exponent E: byte s|m -> (-1)^s * m/64 * 2^(E-127).  With
  E = e8m0 + 5 and m = 2*|q| this is exactly MXFP4 (E2M1 x E8M0); with
  E = 133 it is sign-magnitude int8.  Two fidelity phases cover 7 bits of SrcA."""
  payload = bytes(0 if c == 0x80 else c for c in CODES)  # 0x80 is -2^128/-inf
  actual = run(bh, 'bfp8', 'bf16', payload, one_hot_b('bf16'), exponent)
  bad, _ = classify(actual, [0. if c == 0x80 else bfp8(c, exponent) for c in range(256)])
  print('PROBE_LOWBIT ' + json.dumps(dict(case=f'bfp8_e{exponent}', mismatches=len(bad),
                                          first=bad[:40]), default=str))
  assert bad == []


ROW_EXPONENTS = (-120, -100, -80, -60, -40, -20, -10, -4, 0, 2, 4, 6, 8, 12, 16, 20)


def test_e4m3_weights_times_bf16_activations(bh):
  """SrcA = E4M3 weights unpacked to FP16, SrcB = BF16 activations (full
  8-bit significands, exponents 2^-120..2^22), all four fidelity phases.
  Compare bitwise against the same product with A pre-widened to BF16 (the
  native BF16 x BF16 path).  Expect mixed == 2^112 * native wherever the
  scaled result fits FP32 (real |products and partial sums| < 2^16)."""
  import random
  rng = random.Random(7)
  a_codes = [rng.choice(range(0x28, 0x50)) | rng.choice((0, 0x80)) for _ in range(256)]
  a = [fp8.decode(c) for c in a_codes]           # |a| in [2^-2, 2^3)
  b_bits = []
  for r in range(16):
    for _ in range(16):
      e = ROW_EXPONENTS[r] + rng.randrange(3)
      b_bits.append(rng.choice((0, 0x8000)) | (e + 127) << 7 | rng.randrange(128))
  b = [struct.unpack('<f', struct.pack('<I', x << 16))[0] for x in b_bits]
  pb = struct.pack('<1024H', *b_bits, *([0] * 768))
  mixed = run(bh, 'e4m3', 'bf16', bytes(a_codes) * 4, pb, phases=4)
  native = run(bh, 'bf16', 'bf16', struct.pack('<1024H', *(bf16_bits(x) for x in a * 4)), pb, phases=4)
  rows = []
  for r in range(16):
    peak = max(abs(b[r * 16 + k] * a[k * 16 + c]) for k in range(16) for c in range(16))
    fits = peak < 2.**15
    m, n = mixed[r * 16:(r + 1) * 16], native[r * 16:(r + 1) * 16]
    same = all(struct.pack('<f', x * 2.**-112) == struct.pack('<f', y) for x, y in zip(m, n))
    rows.append(dict(row=r, exp=ROW_EXPONENTS[r], peak_product=peak, fits=fits,
                     identical=same, mixed0=m[0], native0=n[0]))
  print('PROBE_LOWBIT ' + json.dumps(dict(case='e4m3_x_bf16_act', rows=rows), default=str))
  assert all(row['identical'] for row in rows if row['fits'])
  assert not any(row['identical'] for row in rows if row['peak_product'] >= 2.**16)
