"""Probe: BFP8_b / BFP4_b blocks of N values: unpack -> FPU -> FP32 Dst -> pack.

Every case here uses a real exponent section; none uses the forced shared
exponent of test_lowbit_weight_formats.py / test_fp4_probe.py.  An L1 block of
N values is

  [ceil16(N/16) exponent bytes][N mantissa bytes (BFP8) or N/2 bytes (BFP4)]

with no tile header: the unpacker/packer base registers hold (address/16 - 1),
so the hardware header skip lands exactly on ``address``.

Question each test answers (run with -s to see PROBE_BFP records):

  test_unpack_block       Which N / start position / L1 placement unpacks
                          correctly?  SrcA is multiplied by 1.0 (BF16 SrcB) so
                          the FP32 Dst image is SrcA exactly; every Dst row
                          not written must stay zero (SrcA is cleared first).
  test_pack_placement     Can the packer emit a BFP block of 1, 2 or 4 faces,
                          or half a face, at any 16-byte-aligned L1 address,
                          e.g. four 272-byte blocks inside one 1088-byte page?
  test_pack_rounding      FP32 Dst -> BFP must match PACK_MODEL bit for bit
                          (shared exponent, rounding, saturation, zeros).
                          Dst is loaded straight from FP32 L1, so only the
                          packer is tested, for tt-metal's default packer
                          input (BFP8: E8M6), bfp8_pack_precise (FP32), BF16.
  test_compute_roundtrip  End to end: BFP A (x) BF16 B -> FP32 Dst -> BFP, for
                          ELWMUL (4 fidelity phases) and ELWADD.

test_lowbit_weight_formats.py reports that an X end of 1023 with a BFP input
hung card 0.  That did not reproduce on card 1 (neither here nor in the
lowbit configuration itself): one UNPACR over 512 or 1024 values completes
but delivers only the first 256 (16 Src rows), with or without a matching
X_DIMENSION.
"""
import json
import math
import random
import struct
from dataclasses import dataclass

import pytest

from asm import Asm
from firmware.consts import TensixL1, TensixMMIO
from ttko.isa import Tensix as TT
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.fpu.emit import prepare, execute

BFP8, BFP4 = 6, 7
NAMES = {BFP8: 'bfp8_b', BFP4: 'bfp4_b'}
MAG_BITS = {BFP8: 7, BFP4: 3}          # magnitude bits per datum (hidden bit included)
PACK_SOURCE = {'bfp8': BFP8, 'f32': u.F32, 'bf16': u.BF16}
PACK_STRIDE = {BFP8: 1, u.F32: 4, u.BF16: 2}   # LLK set_packer_strides datum size

BASE = TensixL1.DATA_BUFFER_SPACE_BASE  # 64-byte aligned
INPUT_A = BASE                          # BFP operand area (8 KiB)
INPUT_B = BASE + 0x2000                 # BF16 SrcB operand (2 KiB)
OUT_F32 = BASE + 0x3000                 # FP32 Dst image (4 KiB)
OUT_BFP = BASE + 0x4000                 # BFP pack outputs (16 KiB)
SENTINEL = 0xA5


# ---------------------------------------------------------------- reference --

def ceil16(n): return -(-n // 16) * 16
def exp_bytes(n): return ceil16(-(-n // 16))
def mant_bytes(fmt, n): return n if fmt == BFP8 else n // 2
def block_bytes(fmt, n): return exp_bytes(n) + mant_bytes(fmt, n)
def f32_bits(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def from_bits(b): return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]
def bf16_bits(x): return f32_bits(x) >> 16


def codes_of(fmt, data, n):
  if fmt == BFP8: return list(data[:n])
  return [(data[i // 2] >> (4 * (i & 1))) & 15 for i in range(n)]


def pack_codes(fmt, codes):
  if fmt == BFP8: return bytes(codes)
  return bytes(codes[i] | codes[i + 1] << 4 for i in range(0, len(codes), 2))


def value(fmt, code, exponent):
  b = MAG_BITS[fmt]
  return (-1. if code >> b & 1 else 1.) * (code & ((1 << b) - 1)) * 2. ** (exponent - 127 - (b - 1))


def decode(fmt, block, n):
  e = exp_bytes(n)
  return [value(fmt, c, block[i // 16]) for i, c in enumerate(codes_of(fmt, block[e:], n))]


def random_block(fmt, n, rng, exps=(110, 140)):
  """Canonical block: every group has one datum with the hidden bit set, no
  zero magnitudes (so no -0 codes); repacking it must reproduce the bytes."""
  b = MAG_BITS[fmt]
  exponents, codes = [], []
  for _ in range(n // 16):
    exponents.append(rng.randrange(*exps))
    group = [rng.randrange(1, 1 << b) | rng.randrange(2) << b for _ in range(16)]
    k = rng.randrange(16)
    group[k] = (group[k] & 1 << b) | rng.randrange(1 << (b - 1), 1 << b)
    codes += group
  return bytes(exponents).ljust(exp_bytes(n), b'\0') + pack_codes(fmt, codes)


def bf16_payload(values):
  return struct.pack(f'<{len(values)}H', *(bf16_bits(v) for v in values))


# Packer model, fitted on card 1 (3 seeds x 64 stress groups, every group
# exact for all six format/source pairs):
#   1. Each FP32 datum is pre-rounded according to the packer In_data_format:
#      bfp8 (tt-metal default, "E8M6"): 6 fraction bits, round half away;
#      bf16: 7 fraction bits, round half away (ties come from FPU results);
#      f32 (tt-metal bfp8_pack_precise): no pre-rounding.  Denormals -> 0.
#      A pre-round carry bumps that datum's exponent (E8M6 of 1.99*2^127
#      becomes exponent 255).
#   2. Shared exponent = max datum exponent of the 16-value group (0 if the
#      group is all zero); significands are shifted to it and rounded
#      half away from zero to 7 magnitude bits, saturating at 127.
#   3. BFP4_b keeps the top 3 of those 7 magnitude bits: truncation.
#   Sign of a zero magnitude is dropped (-0.0 packs as code 0).

def _round_shift(v, shift, mode):
  if shift <= 0: return v << -shift
  q, r = v >> shift, v & ((1 << shift) - 1)
  half = 1 << (shift - 1)
  if mode == 'trunc': return q
  if mode == 'half_away': return q + (r >= half)
  return q + (r > half or (r == half and q & 1))  # rne


def _pre(bits, steps):
  sign, exp, frac = bits >> 31, bits >> 23 & 255, bits & 0x7FFFFF
  if exp == 0: return sign, 0, 0                   # FP32 denormals flush
  sig = frac | 1 << 23
  for keep, mode in steps:
    s = _round_shift(sig, 23 - keep, mode)
    if s >> (keep + 1): s, exp = s >> 1, exp + 1
    sig = s << (23 - keep)
  return sign, exp, sig


def encode(fmt, bits, pre=(), align='half_away', reduce='trunc'):
  exps, codes = [], []
  for g in range(0, len(bits), 16):
    items = [_pre(x, pre) for x in bits[g:g + 16]]
    shared = max((e for _, e, s in items if s), default=0)
    mags = [min(_round_shift(s, 17 + shared - e, align), 127) if s else 0 for _, e, s in items]
    if fmt == BFP4: mags = [min(_round_shift(m, 4, reduce), 7) for m in mags]
    exps.append(shared)
    codes += [(sg << MAG_BITS[fmt] if m else 0) | m for (sg, _, _), m in zip(items, mags)]
  return bytes(exps).ljust(exp_bytes(len(bits)), b'\0') + pack_codes(fmt, codes)


PACK_MODEL = {'bfp8': ((6, 'half_away'),), 'f32': (), 'bf16': ((7, 'half_away'),)}


def model_block(fmt, source, dst_bits):
  return encode(fmt, dst_bits, PACK_MODEL[source])


MODES = ('trunc', 'rne', 'half_away')
HYPOTHESES = {
  f'pre={"+".join(f"{k}{m}" for k, m in pre) or "none"},align={al},bfp4={rd}': (pre, al, rd)
  for pre in ((),) + tuple(((k, m),) for k in (7, 6) for m in MODES)
  for al in MODES for rd in MODES
}


def matching_hypotheses(fmt, dst_bits, block):
  """Diagnostics only: which alternative models reproduce ``block``."""
  n = len(dst_bits)
  got = decode(fmt, block, n)
  return [name for name, (pre, al, rd) in HYPOTHESES.items()
          if (fmt == BFP4 or rd == 'trunc') and decode(fmt, encode(fmt, dst_bits, pre, al, rd), n) == got]


def explain(fmt, block, n, image):
  """For each non-zero 16-value Dst chunk: which source datum it starts at and
  which exponent byte(s) explain it.  Used only for failure diagnostics."""
  codes = codes_of(fmt, block[exp_bytes(n):], n)
  exps = block[:exp_bytes(n)]
  b = MAG_BITS[fmt]
  out = []
  for chunk in range(len(image) // 16):
    vals = image[chunk * 16:(chunk + 1) * 16]
    if not any(vals): continue
    found = None
    for s in range(n - 15):
      cs = codes[s:s + 16]
      nz = next((i for i, v in enumerate(vals) if v), None)
      if nz is None or not cs[nz] & ((1 << b) - 1): continue
      e = math.log2(abs(vals[nz]) / (cs[nz] & ((1 << b) - 1))) + 127 + (b - 1)
      if e != int(e): continue
      if all(value(fmt, c, int(e)) == v for c, v in zip(cs, vals)):
        found = (s, int(e), [i for i, x in enumerate(exps) if x == int(e)][:4])
        break
    out.append((chunk, found))
  return out


def record(tag, **fields):
  print('PROBE_BFP ' + json.dumps(dict(case=tag, **fields), default=str))


# ------------------------------------------------------------------ kernels --

def configure_bfp_unpacker(k, fmt, address, *, x_dim, faces):
  """Unpacker 0 -> SrcA from a BFP block whose exponent section the hardware
  sizes from x_dim * 1 * faces.  On Blackhole unpacker 0 takes X from the
  per-context X_DIMENSION register (configure_unpacker leaves the descriptor
  X at zero), so both are written."""
  u.configure_unpacker(k, 0, address, u.BF16, u.UnpackTarget.SRCA, commit=False)
  descriptor = u._engine_cfg(u.UnpackCfg.TILE_DESCRIPTOR, 0)
  k.write(descriptor, fmt | 0x10 | x_dim << 16)
  k.write(descriptor + 4, 1 | faces << 16)
  k.write(u._engine_cfg(u.UnpackCfg.OPTIONS, 0), 0x20 | fmt)
  k.write(u._engine_cfg(u.UnpackCfg.X_DIMENSION, 0), x_dim | x_dim << 16)


def emit_loader(k, fmt, address, *, x_dim=256, faces=4, issue=4, x_start=0,
                x_end=255, z_start=0, y_start=0):
  u.clear_sources(k)
  configure_bfp_unpacker(k, fmt, address, x_dim=x_dim, faces=faces)
  u.configure_unpacker(k, 1, INPUT_B, u.BF16, u.UnpackTarget.SRCB, commit=False)
  observed = k.reg()
  k.read(observed, u._engine_cfg(u.UnpackCfg.BASE, 0))
  k.write(u.UNPACK_CONFIG_SYNC, 0)
  k.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  if z_start: k.emit(TT.TTSETADC(1, 0, 2, z_start))
  if y_start: k.emit(TT.TTSETADC(1, 0, 1, y_start))
  # X ranges last: SETADCXY/ZW would otherwise clear them.
  k.emit(TT.TTSETADCXX(1, x_end, x_start))
  k.emit(TT.TTSETADCXX(2, 255, 0))
  u.stall(k, u.Stall.UNPACK, u.Wait.SRCA_CLR | u.Wait.SRCB_CLR)
  # Each UNPACR with SetDatValid is its own Src bank handoff (rows 0.. of the
  # next bank); with two banks the third UNPACR waits for math to release
  # one.  So A and B are issued in pairs and math consumes them one by one.
  a, b = u._unpacr(0), u._unpacr(1)
  u.configure_mop(k, u._mop_loop_words(issue, 1, start=a, loop=b, last=b, outer_last=b))
  u.run_mop(k)
  u.stall(k, u.Stall.UNPACK, u.Wait.UNPACK0 | u.Wait.UNPACK1)
  u.sem_get(k, u.Sem.UNPACK_SYNC)
  u.pc_sync(k)


def emit_math(k, op, issue=4, slots=2):
  """For each of ``issue`` Src bank pairs: ``slots`` 8-row SrcA (op) SrcB
  operations into consecutive FP32 Dst rows, then release both banks."""
  u.sem_wait(k, u.Sem.MATH_PACK, u.SemWait.ON_MAX, u.Stall.SYNC)
  k.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  u.stall(k, u.Stall.SYNC, u.Wait.MATH)
  u.configure_fp32_dst(k, 0)
  for bank in range(issue):
    u.stall(k, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
    for slot in range(slots):
      dst = bank * slots + slot
      if op == 'mul':
        prepare(k, 'elwmul', slot, slot, dst, fidelity=2, repeats=1)
        words = tuple(TT.TTELWMUL(0, 0, 0, mod, dst * 8) for mod in (1, 1, 1, 2))
        u.load_replay(k, 0, words)
        replay = TT.TTREPLAY(0, len(words), 0, 0)
        u.configure_mop(k, u._mop_loop_words(1, 1, loop=replay, last=replay))
      else:
        prepare(k, 'elwadd', slot, slot, dst, repeats=1)
      execute(k)
    k.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))   # clear SrcA/SrcB valid: hand banks back
  u.publish_dst(k)


@dataclass(frozen=True)
class Pack:
  address: int
  fmt: int
  source: str = 'bfp8'   # packer In_data_format: 'bfp8' (tt-metal default), 'f32', 'bf16'
  faces: int = 4
  first_face: int = 0
  rows: int = 16         # rows per face; 8 = half a face

  @property
  def values(self): return self.faces * self.rows * 16

  @property
  def size(self): return block_bytes(self.fmt, self.values)


def emit_bfp_pack(k, p: Pack):
  source = PACK_SOURCE[p.source]
  xs = PACK_STRIDE[source]
  u.configure_packer(k, u.F32)           # FP32 Dst read path, then override
  u._rmw_cfg_byte(k, u.PackCfg.ALU_FORMAT, 3, 0x1E, source << 1)
  for register, word in (
    (u.PackCfg.SECTION_SIZES, p.faces << 16),          # Exp_section_size, 16 B units
    (u.PackCfg.DATA_FORMAT, 1 | p.fmt << 4 | source << 8),
    (u.PackCfg.ADDRESS_XY, 16 * xs << 16),
    (u.PackCfg.ADDRESS_ZW, 256 * xs | 1024 * xs << 16),
  ):
    k.write(int(register), word)
  k.write(TensixMMIO.REGFILE_BASE + 16 * 4, ceil16(p.size) >> 4)
  k.write(TensixMMIO.REGFILE_BASE + 52 * 4, p.faces << 16)
  u.configure_mop(k, u._mop_loop_words(
    p.faces, p.rows // 4, loop=TT.TTPACR(),
    last=TT.TTPACR(0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1),
    outer_last=TT.TTPACR(0, 0, 0, 2)))
  u.pc_sync(k)
  u._set_pack_destination(k, 0, p.address)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
  if p.first_face: k.emit(TT.TTSETADC(4, 0, 2, p.first_face))
  k.write(u.PackCfg.DESTINATION_OFFSET, 0)
  u.stall(k, u.Stall.CFG, u.Wait.PACK0)
  u.run_mop(k)
  u.stall(k, u.Stall.SYNC, u.Wait.PACK0)
  u.pc_sync(k)


def emit_packer(k, packs):
  u.emit_pack_dst(k, 0, OUT_F32, u.F32)  # FP32 Dst image first (control)
  for p in packs: emit_bfp_pack(k, p)
  u.finish_pack(k)


def compute_images(fmt, address, op='mul', packs=(), **loader):
  loader_k, math_k, packer_k = (Asm(r) for r in ('trisc0', 'trisc1', 'trisc2'))
  emit_loader(loader_k, fmt, address, **loader)
  rows = -(-(loader.get('x_end', 255) + 1 - loader.get('x_start', 0)) // 16)
  emit_math(math_k, op, issue=loader.get('issue', 4), slots=max(2, -(-rows // 8)))
  emit_packer(packer_k, packs)
  return {k.role: k.lower() for k in (loader_k, math_k, packer_k)}


def direct_images(packs):
  """FP32 L1 (INPUT_A, 4 KiB) -> FP32 Dst tile 0 -> packs."""
  loader_k, math_k, packer_k = (Asm(r) for r in ('trisc0', 'trisc1', 'trisc2'))
  count = loader_k.reg()
  loader_k.li(count, 4096)
  u.emit_unpack_to_dst(loader_k, INPUT_A, count, 0, 0)
  u.emit_direct_dst_math_handshake(math_k, 0)
  emit_packer(packer_k, packs)
  return {k.role: k.lower() for k in (loader_k, math_k, packer_k)}


def launch(bh, images, inputs, out_bfp_bytes=0x4000):
  l1 = dict(inputs)
  l1[OUT_F32] = bytes([SENTINEL]) * 4096
  l1[OUT_BFP] = bytes([SENTINEL]) * out_bfp_bytes
  bh.launch(images, l1=l1)
  image = struct.unpack('<1024f', bh.read_l1(bh.core, OUT_F32, 4096))
  return image, bh.read_l1(bh.core, OUT_BFP, out_bfp_bytes)


PACKS_PER_LAUNCH = 3  # each BFP pack reconfigures the packer; TRISC2 text is 4 KiB


def run_packs(bh, make_images, packs, inputs):
  """Launch ``make_images(chunk)`` for chunks of packs.  The Dst contents are
  regenerated identically by every launch; returns the FP32 Dst image of the
  first launch and, per pack, the output region of the launch that wrote it."""
  packs, regions, image = tuple(packs), {}, None
  for i in range(0, max(len(packs), 1), PACKS_PER_LAUNCH):
    chunk = packs[i:i + PACKS_PER_LAUNCH]
    img, out = launch(bh, make_images(chunk), inputs)
    if image is None: image = img
    assert img == image, 'FP32 Dst image differs between launches'
    regions.update({p: out for p in chunk})
  return image, regions


# ---------------------------------------------------------- unpack probes --

@dataclass(frozen=True)
class UnpackCase:
  n: int                      # values in the L1 block (descriptor size)
  issue: int = 0              # UNPACRs issued (default n/256)
  slot: int = 0               # block index inside a packed page of equal blocks
  x_start: int = 0
  x_end: int = 255
  z_start: int = 0
  x_dim: int = 256
  x_start_bytes: int = 0      # overrides x_start: mantissa byte offset
  misaligned: bool = False    # expected to corrupt data (strict xfail)
  cap: int = 0                # values that actually arrive (0: all)
  note: str = ''

  def for_format(self, fmt):
    if not self.x_start_bytes: return self
    import dataclasses
    return dataclasses.replace(self, x_start=self.x_start_bytes * (1 if fmt == BFP8 else 2))

  @property
  def faces(self): return max(1, self.n // self.x_dim)


UNPACK_CASES = {
  'n1024': UnpackCase(1024, note='full block, 4 UNPACRs'),
  'n512': UnpackCase(512, note='descriptor Z=2: 32 exponent bytes'),
  'n256': UnpackCase(256, note='descriptor Z=1: 16 exponent bytes'),
  'n256_slot2': UnpackCase(256, slot=2, note='third block of a page of four 256-value blocks'),
  'n256_slot3': UnpackCase(256, slot=3, note='fourth block (offset 816 B for BFP8, 432 B for BFP4)'),
  'n512_slot1': UnpackCase(512, slot=1, note='second block of a page of two 512-value blocks'),
  'face2_of_1024': UnpackCase(1024, issue=1, z_start=2, note='Z counter starts at face 2'),
  'faces23_of_1024': UnpackCase(1024, issue=2, z_start=2, note='faces 2..3 only'),
  'n128': UnpackCase(128, x_dim=128, x_end=127, note='sub-face block: 16 B exponent section, 8 rows'),
  'x0_127_of_256': UnpackCase(256, x_end=127, note='first half of a 256-value block'),
  'x128_255_of_256': UnpackCase(256, x_start=128, note='second half of a 256-value block'),
  # X start in mantissa *bytes*: BFP8 X=16/BFP4 X=32 is one 16-byte L1 word.
  'x_start_16B': UnpackCase(256, x_start_bytes=16, note='mantissa read starts on a 16 B word'),
  'x_start_48B': UnpackCase(256, x_start_bytes=48, note='mantissa read starts on a 16 B word'),
  'x_start_8B': UnpackCase(256, x_start_bytes=8, misaligned=True,
                           note='mantissa read starts mid 16 B word'),
  'x_start_24B': UnpackCase(256, x_start_bytes=24, misaligned=True,
                            note='mantissa read starts mid 16 B word'),
  # One UNPACR spanning more than a face: completes when X_DIMENSION covers
  # the X range, but only the first 256 values (16 Src rows) arrive.
  'x_end_1023_xdim1024': UnpackCase(1024, issue=1, x_dim=1024, x_end=1023, cap=256,
                                    note='one UNPACR for 1024 values, consistent X_DIMENSION'),
  'x_end_511_xdim512': UnpackCase(512, issue=1, x_dim=512, x_end=511, cap=256,
                                  note='one UNPACR for 512 values, consistent X_DIMENSION'),
  # X end beyond the 256-wide X_DIMENSION: also completes (card 1).
  'x_end_1023_xdim256': UnpackCase(1024, issue=1, x_end=1023, cap=256,
                                   note='X end 1023 with X_DIMENSION 256'),
}


def page_of_blocks(fmt, n, count, rng):
  blocks = [random_block(fmt, n, rng, exps=(100 + 8 * i, 108 + 8 * i)) for i in range(count)]
  return blocks, b''.join(blocks)


def expected_unpack(fmt, block, case):
  """Spec model: FirstDatum = (Z*Y + y)*X + x; exponent pointer = FirstDatum/16."""
  vals = decode(fmt, block, case.n)
  out = []
  for issue in range(case.issue or case.faces):
    first = (case.z_start + issue) * case.x_dim + case.x_start
    out += vals[first:first + case.x_end + 1 - case.x_start]
  return out[:case.cap] if case.cap else out


@pytest.mark.parametrize('fmt', (BFP8, BFP4), ids=NAMES.values())
@pytest.mark.parametrize('name', UNPACK_CASES)
def test_unpack_block(bh, request, fmt, name):
  case = UNPACK_CASES[name].for_format(fmt)
  if case.misaligned:
    # Observed on card 1: X starts whose mantissa byte offset is not a
    # multiple of 16 corrupt fixed 8-value chunks (BFP8 X=8: Dst 120..127,
    # 184..191, 240..247; X=24: 120..127, 184..191; BFP4 X=16: half the face).
    # Strict: an XPASS means this rule is wrong.
    request.node.add_marker(pytest.mark.xfail(
      reason='BFP mantissa reads must start on a 16-byte L1 word', strict=True))
  rng = random.Random(sum(map(ord, name)) * 16 + fmt)
  # Neighbouring blocks share the page and have disjoint exponent ranges, so
  # a read of the wrong block or wrong exponents cannot pass by accident.
  per_page = {256: 4, 512: 2}.get(case.n, 1)
  blocks, page = page_of_blocks(fmt, case.n, max(per_page, case.slot + 1), rng)
  block = blocks[case.slot]
  offset = case.slot * block_bytes(fmt, case.n)
  issue = case.issue or case.faces
  # Round trip only where the whole block was unpacked to rows 0.. and is a
  # whole number of faces (the BFP pack path is face-granular).
  repack = (issue * (case.x_end + 1) == case.n and case.x_start == 0 and not case.cap and
            case.z_start == 0 and case.n % 256 == 0)
  packs = (Pack(OUT_BFP, fmt, faces=case.n // 256),) if repack else ()
  images = compute_images(fmt, INPUT_A + offset, packs=packs, x_dim=case.x_dim,
                          faces=case.faces, issue=issue, x_start=case.x_start,
                          x_end=case.x_end, z_start=case.z_start)
  image, out = launch(bh, images, {INPUT_A: page, INPUT_B: bf16_payload([1.] * 1024)})
  expected = expected_unpack(fmt, block, case)
  width = len(expected)
  found_at = next((o for o in range(1024 - width + 1) if list(image[o:o + width]) == expected), None)
  at = 0 if found_at is None else found_at
  rest_zero = not any(image[:at]) and not any(image[at + width:])
  fields = dict(fmt=NAMES[fmt], note=case.note, x_start=case.x_start, block_offset=offset, block_offset_mod64=(INPUT_A + offset) % 64,
                block_bytes=block_bytes(fmt, case.n), values=width,
                found_at_dst_element=found_at, rest_zero=rest_zero)
  if found_at is None or not rest_zero:
    fields['nonzero_rows'] = [r for r in range(64) if any(image[r * 16:(r + 1) * 16])]
    fields['explain'] = {i: [e for e in explain(fmt, blk, case.n, image) if e[1]][:12]
                         for i, blk in enumerate(blocks)}
  if repack:
    fields['repack_exact'] = out[:len(block)] == block
    fields['repack_overrun_clean'] = out[len(block):len(block) + 64] == bytes([SENTINEL]) * 64
  record(f'unpack_{name}', **fields)
  assert found_at is not None and rest_zero
  if repack:
    assert fields['repack_exact'] and fields['repack_overrun_clean']


# ------------------------------------------------------------ pack probes --

def representable_dst(fmt, rng):
  """FP32 Dst contents that are exact in ``fmt`` and canonical, so a correct
  pack is bit-exact whatever the rounding mode."""
  block = random_block(fmt, 1024, rng, exps=(112, 140))
  return block, decode(fmt, block, 1024)


def face_block(fmt, block, first, faces, rows=16):
  """Reference block for ``faces`` faces (``rows`` rows each) starting at face ``first``."""
  vals, n = [], 1024
  codes = codes_of(fmt, block[exp_bytes(n):], n)
  exps, out = block[:exp_bytes(n)], []
  for f in range(first, first + faces):
    idx = range(f * 256, f * 256 + rows * 16)
    vals += [codes[i] for i in idx]
    out += [exps[i // 16] for i in idx[::16]]
  return bytes(out).ljust(exp_bytes(len(vals)), b'\0') + pack_codes(fmt, vals)


def placement_packs(fmt):
  page = OUT_BFP
  b256 = block_bytes(fmt, 256)
  packs = {
    'full_at_+16': Pack(page + 16, fmt),
    **{f'face{f}_slot{f}': Pack(page + 0x1000 + f * b256, fmt, faces=1, first_face=f) for f in range(4)},
    'faces23_as_512': Pack(page + 0x1800, fmt, faces=2, first_face=2),
    'half_face0_128': Pack(page + 0x1C00, fmt, faces=1, rows=8),
    'half_face1_128_at_+48': Pack(page + 0x1E00 + 48, fmt, faces=1, first_face=1, rows=8),
  }
  return packs


@pytest.mark.parametrize('fmt', (BFP8, BFP4), ids=NAMES.values())
def test_pack_placement(bh, fmt):
  rng = random.Random(1000 + fmt)
  block, vals = representable_dst(fmt, rng)
  packs = placement_packs(fmt)
  image, regions = run_packs(bh, direct_images, packs.values(), {INPUT_A: struct.pack('<1024f', *vals)})
  assert list(image) == vals, 'FP32 Dst control image is wrong'
  results, failed = {}, []
  for name, p in packs.items():
    out = regions[p]
    want = face_block(fmt, block, p.first_face, p.faces, p.rows)
    at = p.address - OUT_BFP
    got = out[at:at + len(want)]
    exps_used = -(-p.values // 16)
    ok_exps = got[:exps_used] == want[:exps_used]
    ok_mant = got[exp_bytes(p.values):] == want[exp_bytes(p.values):]
    res = dict(address_mod64=p.address % 64, bytes=len(want), exps_ok=ok_exps, mantissas_ok=ok_mant,
               exp_pad=got[exps_used:exp_bytes(p.values)].hex())
    if not (ok_exps and ok_mant):
      res['got_exps'] = got[:exp_bytes(p.values)].hex()
      res['want_exps'] = want[:exp_bytes(p.values)].hex()
      res['first_bad_byte'] = next((i for i, (x, y) in enumerate(zip(got, want)) if x != y), None)
    results[name] = res
    if not (ok_exps and ok_mant): failed.append(name)
  # Every byte of a launch's output region outside that launch's packs must
  # still hold the sentinel: no stray or oversized writes.
  stray = {}
  for out in {id(o): o for o in regions.values()}.values():
    covered = set()
    for p in (p for p in packs.values() if regions[p] is out):
      covered.update(range(p.address - OUT_BFP, p.address - OUT_BFP + p.size))
    bad = [i for i, x in enumerate(out) if i not in covered and x != SENTINEL]
    if bad: stray[hex(OUT_BFP + bad[0])] = len(bad)
  record('pack_placement', fmt=NAMES[fmt], results=results, stray_writes=stray)
  assert failed == [] and stray == {}


def rounding_dst(rng):
  """64 groups of FP32 values stressing shared-exponent choice and rounding."""
  bits = []
  for g in range(64):
    top = rng.randrange(118, 136)
    if g < 28:      # random full-precision mantissas, exponents spread 0..11 below top
      grp = [rng.randrange(2) << 31 | (top - rng.randrange(12)) << 23 | rng.getrandbits(23) for _ in range(16)]
    elif g < 36:    # exact ties for BFP8 (g<32) / BFP4 (g>=32): (m + 1/2) quanta
      b = 7 if g < 32 else 3
      grp = [top << 23] + [f32_bits((m + .5) * 2. ** (top - 127 - (b - 1)))
                           for m in rng.sample(range(1 << (b - 1)), min(15, 1 << (b - 1)))]
      grp += [f32_bits(2. ** (top - 127))] * (16 - len(grp))
    elif g < 40:    # carry out of the top bit: 1.11111.. x 2^top
      grp = [top << 23 | 0x7FFFFF - rng.randrange(1 << 14)] + \
            [rng.randrange(2) << 31 | (top - rng.randrange(3)) << 23 | rng.getrandbits(23) for _ in range(15)]
    elif g < 44:    # BF16-exact values (pre-rounding to BF16 is a no-op)
      grp = [rng.randrange(2) << 31 | (top - rng.randrange(8)) << 23 | rng.getrandbits(7) << 16 for _ in range(16)]
    elif g == 44: grp = [0] * 16
    elif g == 45: grp = [0x80000000] * 8 + [0] * 8                     # -0.0 / +0.0
    elif g == 46: grp = [0x80000000] * 15 + [top << 23]                # -0.0 next to a normal
    elif g == 47: grp = [top << 23] + [(top - 30) << 23 | 0x400000] * 15  # underflow to 0
    elif g == 48: grp = [top << 23] + [0x00012345] * 15                # FP32 denormals
    elif g == 49: grp = [1 << 23 | 0x123456] * 16                       # smallest normal exponent
    elif g == 50: grp = [254 << 23 | 0x7F0000] * 16                     # near FP32 max
    else:           # negatives with the largest magnitude negative
      grp = [1 << 31 | (top - rng.randrange(6)) << 23 | rng.getrandbits(23) for _ in range(16)]
    rng.shuffle(grp)
    bits += grp
  return bits


def rounding_packs():
  packs, at = {}, OUT_BFP
  for fmt in (BFP8, BFP4):
    for source in PACK_SOURCE:
      packs[(fmt, source)] = Pack(at, fmt, source=source)
      at += ceil16(block_bytes(fmt, 1024)) + 64
  return packs


@pytest.mark.parametrize('seed', (7, 8))
def test_pack_rounding(bh, seed):
  bits = rounding_dst(random.Random(seed))
  packs = rounding_packs()
  image, regions = run_packs(bh, direct_images, packs.values(), {INPUT_A: struct.pack('<1024I', *bits)})
  dst = [f32_bits(x) for x in image]
  assert dst == bits, 'direct FP32 L1 -> Dst must be bit-exact'
  bad = []
  for (fmt, source), p in packs.items():
    out = regions[p]
    at = p.address - OUT_BFP
    block = out[at:at + p.size]
    want = model_block(fmt, source, dst)
    wrong = [g for g in range(64) if decode(fmt, block[:64] + block[64:], 1024)[g * 16:g * 16 + 16] !=
             decode(fmt, want, 1024)[g * 16:g * 16 + 16]]
    fields = dict(fmt=NAMES[fmt], source=source, bit_exact=block == want, wrong_groups=wrong,
                  zero_group_exp=block[44], neg_zero_codes=codes_of(fmt, block[64:], 1024)[45 * 16:46 * 16],
                  near_max_exp=block[50], near_max_code=codes_of(fmt, block[64:], 1024)[50 * 16],
                  overrun_clean=out[at + p.size:at + p.size + 64] == bytes([SENTINEL]) * 64)
    if block != want:
      fields['matching_alternatives'] = matching_hypotheses(fmt, dst, block)
    record('pack_rounding', seed=seed, **fields)
    if block != want or not fields['overrun_clean']: bad.append((NAMES[fmt], source))
  assert bad == []


# ------------------------------------------------------- end-to-end probe --

@pytest.mark.parametrize('op', ('mul', 'add'))
@pytest.mark.parametrize('fmt', (BFP8, BFP4), ids=NAMES.values())
def test_compute_roundtrip(bh, fmt, op):
  rng = random.Random(31 * fmt + len(op))
  block = random_block(fmt, 1024, rng, exps=(120, 134))
  a = decode(fmt, block, 1024)
  b = [from_bits(bf16_bits(rng.choice((-1, 1)) * rng.uniform(1, 2) * 2. ** rng.randrange(-4, 5)) << 16)
       for _ in range(1024)]
  packs = {source: Pack(OUT_BFP + i * 0x500, fmt, source=source) for i, source in enumerate(PACK_SOURCE)}
  images = compute_images(fmt, INPUT_A, op=op, packs=tuple(packs.values()))
  image, out = launch(bh, images, {INPUT_A: block, INPUT_B: bf16_payload(b)})
  exact = [x * y if op == 'mul' else x + y for x, y in zip(a, b)]
  ref32 = [from_bits(f32_bits(v)) for v in exact]     # FP32 RNE of the exact result
  dst_bits = [f32_bits(x) for x in image]
  mism = [(i, a[i], b[i], ref32[i], image[i]) for i in range(1024) if image[i] != ref32[i]]
  rel = max((abs(image[i] - exact[i]) / abs(exact[i]) for i in range(1024) if exact[i]), default=0)
  packed = {}
  for source, p in packs.items():
    blk = out[p.address - OUT_BFP:p.address - OUT_BFP + p.size]
    got = decode(fmt, blk, 1024)
    over = [i for i, (x, y) in enumerate(zip(image, got))
            if abs(x - y) > 2. ** (blk[i // 16] - 127 - (MAG_BITS[fmt] - 1))]
    packed[source] = dict(bit_exact_vs_model=blk == model_block(fmt, source, dst_bits),
                          beyond_one_quantum=len(over))
    if blk != model_block(fmt, source, dst_bits):
      packed[source]['matching_alternatives'] = matching_hypotheses(fmt, dst_bits, blk)
  record(f'compute_{op}', fmt=NAMES[fmt], dst_mismatch_vs_fp32_rne=len(mism), first=mism[:8],
         max_rel_err_vs_exact=rel, packed=packed)
  if op == 'mul': assert mism == [], 'BFP x BF16 with 4 fidelity phases should be exact in FP32 Dst'
  # Observed: ELWADD is not FP32-exact; results carry ~10-11 fraction bits.
  assert rel < 2. ** -10
  assert all(v['bit_exact_vs_model'] and v['beyond_one_quantum'] == 0 for v in packed.values())
