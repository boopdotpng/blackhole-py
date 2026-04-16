import struct
import pytest
from emu.tensix import TensixCoprocessor
from emu.dsl import decode_tensix
from emu.tensix.rwc import RWCState, AddrModState, ADCState
from emu.tensix.fpu import FPU, _19bit_to_float, _float_to_19bit, _float_to_dest, _dest_to_float
from emu.tensix.sfpu import SFPU, _to_float, _to_bits, POS_INF, NEG_INF, CONST_ONE
from emu.tensix.regfile import SrcRegFile, DestRegFile


# ── helpers ──────────────────────────────────────────────────────────────

def _f2b(f):
  return struct.unpack('I', struct.pack('f', f))[0]

def _b2f(b):
  return struct.unpack('f', struct.pack('I', b & 0xFFFFFFFF))[0]

def _make_coproc():
  return TensixCoprocessor()


# =============================================================================
# RWC Tests
# =============================================================================

class TestRWC:
  def test_initial_state(self):
    rwc = RWCState()
    assert rwc.a == 0 and rwc.b == 0 and rwc.d == 0 and rwc.cr == 0

  def test_setrwc_all(self):
    rwc = RWCState()
    # Set a=3, b=5, d=7, cr=2, bitmask=0x0F (all)
    word = (0x37 << 24) | (0 << 22) | (2 << 18) | (7 << 14) | (5 << 10) | (3 << 6) | 0x0F
    clear = rwc.execute_setrwc(decode_tensix(word))
    assert rwc.a == 3
    assert rwc.b == 5
    assert rwc.d == 7
    assert rwc.cr == 2
    assert clear == 0

  def test_setrwc_selective(self):
    rwc = RWCState()
    rwc.a = 10; rwc.b = 11
    # Only set a (bitmask bit 0)
    word = (0x37 << 24) | (0 << 22) | (0 << 18) | (0 << 14) | (0 << 10) | (5 << 6) | 0x01
    rwc.execute_setrwc(decode_tensix(word))
    assert rwc.a == 5
    assert rwc.b == 11  # unchanged

  def test_setrwc_returns_clear_ab(self):
    rwc = RWCState()
    # clear_ab_vld = 3 (both bits)
    word = (0x37 << 24) | (3 << 22) | (0 << 18) | (0 << 14) | (0 << 10) | (0 << 6) | 0
    clear = rwc.execute_setrwc(decode_tensix(word))
    assert clear == 3

  def test_incrwc(self):
    rwc = RWCState()
    rwc.a = 5; rwc.b = 10; rwc.d = 14; rwc.cr = 6
    # Increment: a+2, b+3, d+4, cr+1
    word = (0x38 << 24) | (1 << 18) | (4 << 14) | (3 << 10) | (2 << 6)
    rwc.execute_incrwc(decode_tensix(word))
    assert rwc.a == 7
    assert rwc.b == 13
    assert rwc.d == (14 + 4) & 0xF  # wraps at 4 bits
    assert rwc.cr == 7

  def test_incrwc_wraps(self):
    rwc = RWCState()
    rwc.a = 15
    word = (0x38 << 24) | (0 << 18) | (0 << 14) | (0 << 10) | (1 << 6)
    rwc.execute_incrwc(decode_tensix(word))
    assert rwc.a == 0  # 15 + 1 wraps to 0


# =============================================================================
# ADC Tests
# =============================================================================

class TestADC:
  def test_setadc(self):
    adc = ADCState()
    # Set Unpacker0, channel 0, dimension X to 42
    word = (0x50 << 24) | (1 << 21) | (0 << 20) | (0 << 18) | 42
    adc.execute_setadc(decode_tensix(word))
    assert adc.unpackers[0].channels[0].x.val == 42

  def test_setadc_multiple_units(self):
    adc = ADCState()
    # Set all units (mask=7), channel 1, dimension Y to 99
    word = (0x50 << 24) | (7 << 21) | (1 << 20) | (1 << 18) | 99
    adc.execute_setadc(decode_tensix(word))
    assert adc.unpackers[0].channels[1].y.val == 99
    assert adc.unpackers[1].channels[1].y.val == 99
    assert adc.packers.channels[1].y.val == 99

  def test_setadcxy(self):
    adc = ADCState()
    # Unpacker0, Ch0_X=3, Ch0_Y=5, bitmask=0x03
    word = (0x51 << 24) | (1 << 21) | (0 << 15) | (0 << 12) | (5 << 9) | (3 << 6) | 0x03
    adc.execute_setadcxy(decode_tensix(word))
    assert adc.unpackers[0].channels[0].x.val == 3
    assert adc.unpackers[0].channels[0].y.val == 5

  def test_incadczw(self):
    adc = ADCState()
    adc.unpackers[0].channels[0].z.val = 10
    adc.unpackers[0].channels[0].w.val = 20
    # Unpacker0, Ch0_Z += 5, Ch0_W += 3
    word = (0x55 << 24) | (1 << 21) | (0 << 15) | (0 << 12) | (3 << 9) | (5 << 6)
    adc.execute_incadczw(decode_tensix(word))
    assert adc.unpackers[0].channels[0].z.val == 15
    assert adc.unpackers[0].channels[0].w.val == 23


# =============================================================================
# AddrMod Tests
# =============================================================================

class TestAddrMod:
  def test_apply_increment(self):
    rwc = RWCState()
    rwc.a = 3; rwc.b = 5; rwc.d = 7
    ams = AddrModState()
    ams.descriptors[0].srca_incr = 2
    ams.descriptors[0].srcb_incr = 1
    ams.descriptors[0].dest_incr = 3
    ams.apply(0, rwc)
    assert rwc.a == 5
    assert rwc.b == 6
    assert rwc.d == 10

  def test_apply_clear(self):
    rwc = RWCState()
    rwc.a = 10; rwc.b = 10
    ams = AddrModState()
    ams.descriptors[1].srca_clr = True
    ams.descriptors[1].srcb_incr = 5
    ams.apply(1, rwc)
    assert rwc.a == 0  # cleared
    assert rwc.b == 15  # incremented


# =============================================================================
# FPU Tests
# =============================================================================

class TestFPU:
  def _make(self):
    srca = SrcRegFile("SrcA")
    srcb = SrcRegFile("SrcB")
    dest = DestRegFile()
    return FPU(srca, srcb, dest), srca, srcb, dest

  def test_zeroacc_all(self):
    fpu, _, _, dest = self._make()
    # Mark some rows as valid
    for r in range(100):
      dest.valid[r] = True
    # ZEROACC CLR_ALL (clear_mode=3)
    word = (0x10 << 24) | (3 << 19)
    fpu.zeroacc(decode_tensix(word))
    assert not any(dest.valid)

  def test_zeroacc_specific(self):
    fpu, _, _, dest = self._make()
    dest.valid[42] = True
    word = (0x10 << 24) | (0 << 19) | 42
    fpu.zeroacc(decode_tensix(word))
    assert not dest.valid[42]

  def test_zeroacc_16_rows(self):
    fpu, _, _, dest = self._make()
    for r in range(100):
      dest.valid[r] = True
    word = (0x10 << 24) | (1 << 19) | 10
    fpu.zeroacc(decode_tensix(word))
    for r in range(10, 26):
      assert not dest.valid[r]
    assert dest.valid[9]
    assert dest.valid[26]

  def test_zerosrc_srca(self):
    fpu, srca, _, _ = self._make()
    bank = srca.banks[srca.fpu_bank]
    bank.rows[0][0] = 0xDEAD
    # ZEROSRC: src_mask=1 (SrcA only), write_mode=0 (zero)
    word = (0x11 << 24) | 1
    fpu.zerosrc(decode_tensix(word))
    assert bank.rows[0][0] == 0

  def test_zerosrc_neg_inf(self):
    fpu, srca, _, _ = self._make()
    bank = srca.banks[srca.fpu_bank]
    # ZEROSRC: src_mask=1, write_mode=1 (-inf)
    word = (0x11 << 24) | (1 << 3) | 1
    fpu.zerosrc(decode_tensix(word))
    val = _19bit_to_float(bank.rows[0][0])
    assert val == float('-inf')

  def test_elwadd_simple(self):
    fpu, srca, srcb, dest = self._make()
    rwc = RWCState()

    # Pre-load SrcA and SrcB with known values
    srca_bank = srca.banks[srca.fpu_bank]
    srcb_bank = srcb.banks[srcb.fpu_bank]
    for col in range(16):
      srca_bank.rows[0][col] = _float_to_19bit(float(col))
      srcb_bank.rows[0][col] = _float_to_19bit(float(col * 10))

    # ELWADD: dest_accum_en=0
    word = (0x28 << 24) | (0 << 21) | 0
    fpu.elwadd(decode_tensix(word), rwc)

    # Check: dest[0][col] should be col + col*10 = col*11
    for col in range(16):
      expected = float(col * 11)
      actual = _dest_to_float(dest.bits[0][col])
      assert abs(actual - expected) < 0.01, f"col {col}: {actual} != {expected}"
      assert dest.valid[0]

  def test_elwadd_accumulate(self):
    fpu, srca, srcb, dest = self._make()
    rwc = RWCState()

    # Pre-load Dest with 100.0
    dest.bits[0][0] = _float_to_dest(100.0)
    dest.valid[0] = True

    srca_bank = srca.banks[srca.fpu_bank]
    srcb_bank = srcb.banks[srcb.fpu_bank]
    srca_bank.rows[0][0] = _float_to_19bit(1.0)
    srcb_bank.rows[0][0] = _float_to_19bit(2.0)

    # ELWADD with dest_accum_en=1
    word = (0x28 << 24) | (1 << 21) | 0
    fpu.elwadd(decode_tensix(word), rwc)

    actual = _dest_to_float(dest.bits[0][0])
    assert abs(actual - 103.0) < 0.01

  def test_mvmul_identity(self):
    fpu, srca, srcb, dest = self._make()
    rwc = RWCState()

    srca_bank = srca.banks[srca.fpu_bank]
    srcb_bank = srcb.banks[srcb.fpu_bank]

    # SrcA = identity-like (diagonal 1.0 in first 8 cols)
    for r in range(16):
      for c in range(16):
        srca_bank.rows[r][c] = _float_to_19bit(1.0 if r == c else 0.0)

    # SrcB = row of 1.0 through 8.0
    for r in range(8):
      for c in range(16):
        srcb_bank.rows[r][c] = _float_to_19bit(float(r + 1))

    # MVMUL
    word = (0x26 << 24) | 0
    fpu.mvmul(decode_tensix(word), rwc)

    # With identity SrcA, Dest should equal SrcB
    for r in range(8):
      for c in range(16):
        expected = float(r + 1)  # SrcB value
        actual = _dest_to_float(dest.bits[r][c])
        assert abs(actual - expected) < 0.1, f"[{r}][{c}]: {actual} != {expected}"

  def test_mvmul_accumulates(self):
    fpu, srca, srcb, dest = self._make()
    rwc = RWCState()

    srca_bank = srca.banks[srca.fpu_bank]
    srcb_bank = srcb.banks[srcb.fpu_bank]

    # Simple setup: SrcA identity, SrcB all 1.0
    for r in range(16):
      srca_bank.rows[r][r] = _float_to_19bit(1.0)
    for r in range(8):
      for c in range(16):
        srcb_bank.rows[r][c] = _float_to_19bit(1.0)

    word = (0x26 << 24) | 0
    fpu.mvmul(decode_tensix(word), rwc)
    fpu.mvmul(decode_tensix(word), rwc)  # second accumulation

    # After two passes, each Dest element should be 2.0
    actual = _dest_to_float(dest.bits[0][0])
    assert abs(actual - 2.0) < 0.1

  def test_gmpool(self):
    fpu, srca, _, dest = self._make()
    rwc = RWCState()

    srca_bank = srca.banks[srca.fpu_bank]
    # SrcA row 0 = [1.0, -5.0, 3.0, ...]
    srca_bank.rows[0][0] = _float_to_19bit(1.0)
    srca_bank.rows[0][1] = _float_to_19bit(-5.0)
    srca_bank.rows[0][2] = _float_to_19bit(3.0)

    word = (0x33 << 24) | 0
    fpu.gmpool(decode_tensix(word), rwc)

    # First pass: Dest gets SrcA values
    assert abs(_dest_to_float(dest.bits[0][0]) - 1.0) < 0.01

    # Load bigger values into SrcA
    srca_bank.rows[0][0] = _float_to_19bit(5.0)
    srca_bank.rows[0][1] = _float_to_19bit(-2.0)

    fpu.gmpool(decode_tensix(word), rwc)

    # Second pass: max(old, new)
    assert abs(_dest_to_float(dest.bits[0][0]) - 5.0) < 0.01
    assert abs(_dest_to_float(dest.bits[0][1]) - (-2.0)) < 0.01  # max(-5, -2) = -2

  def test_movb2d(self):
    fpu, _, srcb, dest = self._make()
    rwc = RWCState()

    srcb_bank = srcb.banks[srcb.fpu_bank]
    srcb_bank.rows[0][0] = _float_to_19bit(42.0)
    srcb_bank.rows[0][1] = _float_to_19bit(99.0)

    # MOVB2D: src=0, dst=0, instr_mod=0 (1 row)
    word = (0x13 << 24) | (0 << 17) | (0 << 11) | 0
    fpu.movb2d(decode_tensix(word), rwc)

    assert abs(_dest_to_float(dest.bits[0][0]) - 42.0) < 0.1
    assert abs(_dest_to_float(dest.bits[0][1]) - 99.0) < 0.1

  def test_movd2a(self):
    fpu, srca, _, dest = self._make()
    rwc = RWCState()

    dest.bits[0][0] = _float_to_dest(77.0)
    dest.valid[0] = True

    # MOVD2A: src=0, dst=0, instr_mod=0 (1 row)
    word = (0x08 << 24) | (0 << 17) | (0 << 12) | 0
    fpu.movd2a(decode_tensix(word), rwc)

    srca_bank = srca.banks[srca.fpu_bank]
    actual = _19bit_to_float(srca_bank.rows[0][0])
    assert abs(actual - 77.0) < 1.0  # some precision loss in 19-bit

  def test_movd2b(self):
    fpu, _, srcb, dest = self._make()
    rwc = RWCState()

    dest.bits[0][0] = _float_to_dest(55.0)
    dest.valid[0] = True

    word = (0x0A << 24) | (0 << 17) | (0 << 12) | 0
    fpu.movd2b(decode_tensix(word), rwc)

    srcb_bank = srcb.banks[srcb.fpu_bank]
    actual = _19bit_to_float(srcb_bank.rows[0][0])
    assert abs(actual - 55.0) < 1.0

  def test_cleardvalid_srca(self):
    fpu, srca, _, _ = self._make()
    srca.flip_to_fpu()  # bank 0 now owned by matrix unit
    assert srca.banks[0].allowed_client == "matrix_unit"

    # CLEARDVALID: bit 0 = release SrcA
    word = (0x36 << 24) | (1 << 22)
    fpu.cleardvalid(decode_tensix(word))

    # After release, the old fpu_bank should be back with unpackers
    assert srca.banks[0].allowed_client == "unpackers"

  def test_trnspsrcb(self):
    fpu, _, srcb, _ = self._make()
    bank = srcb.banks[srcb.fpu_bank]

    # Set rows 16-31 to a pattern: bank[16+r][c] = r*16 + c
    for r in range(16):
      for c in range(16):
        bank.rows[16 + r][c] = r * 16 + c

    word = (0x16 << 24)
    fpu.trnspsrcb(decode_tensix(word))

    # After transpose: bank[16+r][c] should be c*16 + r
    for r in range(16):
      for c in range(16):
        assert bank.rows[16 + r][c] == c * 16 + r


# =============================================================================
# SFPU Tests
# =============================================================================

class TestSFPU:
  def _make(self):
    dest = DestRegFile()
    return SFPU(dest), dest

  def test_lreg_constants(self):
    sfpu, _ = self._make()
    assert sfpu.lregs[8][0] == POS_INF
    assert sfpu.lregs[9][0] == NEG_INF
    assert sfpu.lregs[16][0] == CONST_ONE
    assert sfpu.lregs[15][0] == 0      # lane 0 TILEID = 0*2
    assert sfpu.lregs[15][1] == 2      # lane 1 TILEID = 1*2
    assert sfpu.lregs[15][31] == 62    # lane 31 TILEID = 31*2

  def test_lreg_readonly(self):
    sfpu, _ = self._make()
    # Trying to write to LReg[8] (read-only) via sfploadi should be ignored
    word = (0x71 << 24) | (8 << 20) | (4 << 16) | 999
    sfpu.sfploadi(decode_tensix(word))
    assert sfpu.lregs[8][0] == POS_INF  # unchanged

  def test_sfploadi_u16(self):
    sfpu, _ = self._make()
    # Load U16 = 0xBEEF into LReg[0]
    word = (0x71 << 24) | (0 << 20) | (4 << 16) | 0xBEEF
    sfpu.sfploadi(decode_tensix(word))
    for lane in range(32):
      assert sfpu.lregs[0][lane] == 0xBEEF

  def test_sfploadi_bf16(self):
    sfpu, _ = self._make()
    # BF16 for 1.0 = 0x3F80
    word = (0x71 << 24) | (0 << 20) | (0 << 16) | 0x3F80
    sfpu.sfploadi(decode_tensix(word))
    val = _to_float(sfpu.lregs[0][0])
    assert abs(val - 1.0) < 0.001

  def test_sfploadi_hi16(self):
    sfpu, _ = self._make()
    # First load lo16
    sfpu.lregs[1][0] = 0x0000BEEF
    # Then load hi16 = 0xDEAD
    word = (0x71 << 24) | (1 << 20) | (8 << 16) | 0xDEAD
    sfpu.sfploadi(decode_tensix(word))
    assert sfpu.lregs[1][0] == 0xDEADBEEF

  def test_sfpload_sfpstore_roundtrip(self):
    sfpu, dest = self._make()
    rwc = RWCState()

    # Write known values to Dest rows 0 and 1
    for col in range(16):
      dest.bits[0][col] = _f2b(float(col))
      dest.bits[1][col] = _f2b(float(16 + col))
      dest.valid[0] = True
      dest.valid[1] = True

    # SFPLOAD into LReg[2]
    word = (0x70 << 24) | (2 << 20) | 0
    sfpu.sfpload(decode_tensix(word), rwc)

    # Verify lanes match Dest values
    for lane in range(32):
      row = lane // 16
      col = lane % 16
      expected = _f2b(float(row * 16 + col))
      assert sfpu.lregs[2][lane] == expected

    # Modify LReg and store back
    for lane in range(32):
      sfpu.lregs[2][lane] = _f2b(float(lane * 100))

    # SFPSTORE from LReg[2] to Dest row 10
    word = (0x72 << 24) | (2 << 20) | 10
    sfpu.sfpstore(decode_tensix(word), rwc)

    for col in range(16):
      assert dest.bits[10][col] == _f2b(float(col * 100))
      assert dest.bits[11][col] == _f2b(float((16 + col) * 100))

  def test_sfpmad(self):
    sfpu, _ = self._make()
    # LReg[0] = 2.0, LReg[1] = 3.0, LReg[2] = 4.0
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(2.0)
      sfpu.lregs[1][lane] = _f2b(3.0)
      sfpu.lregs[2][lane] = _f2b(4.0)

    # SFPMAD: VD = VA * VB + VC => LReg[3] = LReg[0] * LReg[1] + LReg[2]
    # a=0, b=1, c=2, d=3, mod=0
    word = (0x84 << 24) | (0 << 16) | (1 << 12) | (2 << 8) | (3 << 4) | 0
    sfpu.sfpmad(decode_tensix(word))

    for lane in range(32):
      actual = _b2f(sfpu.lregs[3][lane])
      assert abs(actual - 10.0) < 0.001  # 2*3 + 4 = 10

  def test_sfpmad_negate(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(2.0)
      sfpu.lregs[1][lane] = _f2b(3.0)
      sfpu.lregs[2][lane] = _f2b(4.0)

    # mod=3: negate B and C => VD = VA * (-VB) + (-VC) = 2*(-3) + (-4) = -10
    word = (0x84 << 24) | (0 << 16) | (1 << 12) | (2 << 8) | (3 << 4) | 3
    sfpu.sfpmad(decode_tensix(word))

    for lane in range(32):
      assert abs(_b2f(sfpu.lregs[3][lane]) - (-10.0)) < 0.001

  def test_sfpadd(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[1][lane] = _f2b(7.0)
      sfpu.lregs[2][lane] = _f2b(3.0)

    # SFPADD: VD = VB + VC => LReg[3] = 7 + 3 = 10
    word = (0x85 << 24) | (0 << 16) | (1 << 12) | (2 << 8) | (3 << 4) | 0
    sfpu.sfpadd(decode_tensix(word))

    assert abs(_b2f(sfpu.lregs[3][0]) - 10.0) < 0.001

  def test_sfpmul(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(5.0)
      sfpu.lregs[1][lane] = _f2b(6.0)

    # SFPMUL: VD = VA * VB => LReg[3] = 5 * 6 = 30
    word = (0x86 << 24) | (0 << 16) | (1 << 12) | (0 << 8) | (3 << 4) | 0
    sfpu.sfpmul(decode_tensix(word))

    assert abs(_b2f(sfpu.lregs[3][0]) - 30.0) < 0.001

  def test_sfpiadd(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[2][lane] = 100
      sfpu.lregs[3][lane] = 50

    # SFPIADD: VD = VC + VD, mod=0 (use reg, add, no CC)
    # c=2, d=3
    word = (0x79 << 24) | (0 << 12) | (2 << 8) | (3 << 4) | 0
    sfpu.sfpiadd(decode_tensix(word))

    assert sfpu.lregs[3][0] == 150

  def test_sfpiadd_subtract(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[2][lane] = 100
      sfpu.lregs[3][lane] = 30

    # mod=2: subtract (VC - VD)
    word = (0x79 << 24) | (0 << 12) | (2 << 8) | (3 << 4) | 2
    sfpu.sfpiadd(decode_tensix(word))

    assert sfpu.lregs[3][0] == 70  # 100 - 30

  def test_sfpiadd_immediate(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[2][lane] = 200

    # mod=1: use immediate, add
    # imm12 = 50
    word = (0x79 << 24) | (50 << 12) | (2 << 8) | (3 << 4) | 1
    sfpu.sfpiadd(decode_tensix(word))

    assert sfpu.lregs[3][0] == 250

  def test_sfpand_sfpor_sfpnot_sfpxor(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = 0xFF00FF00
      sfpu.lregs[1][lane] = 0x0F0F0F0F

    # SFPAND: VD &= VC => LReg[0] &= LReg[1]
    word = (0x7E << 24) | (1 << 8) | (0 << 4) | 0
    sfpu.sfpand(decode_tensix(word))
    assert sfpu.lregs[0][0] == 0x0F000F00

    # Reset
    for lane in range(32):
      sfpu.lregs[2][lane] = 0xFF00FF00
      sfpu.lregs[3][lane] = 0x0F0F0F0F

    # SFPOR: VD |= VC
    word = (0x7F << 24) | (3 << 8) | (2 << 4) | 0
    sfpu.sfpor(decode_tensix(word))
    assert sfpu.lregs[2][0] == 0xFF0FFF0F

    # SFPNOT
    for lane in range(32):
      sfpu.lregs[4][lane] = 0xAAAAAAAA
    word = (0x80 << 24) | (4 << 8) | (5 << 4) | 0
    sfpu.sfpnot(decode_tensix(word))
    assert sfpu.lregs[5][0] == 0x55555555

    # SFPXOR
    for lane in range(32):
      sfpu.lregs[6][lane] = 0xFF00FF00
      sfpu.lregs[7][lane] = 0x0F0F0F0F
    word = (0x8D << 24) | (7 << 8) | (6 << 4) | 0
    sfpu.sfpxor(decode_tensix(word))
    assert sfpu.lregs[6][0] == 0xF00FF00F

  def test_sfplz(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = 0x00010000  # 15 leading zeros
    sfpu.lregs[0][1] = 0           # 32 leading zeros
    sfpu.lregs[0][2] = 0x80000000  # 0 leading zeros

    word = (0x81 << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfplz(decode_tensix(word))

    assert sfpu.lregs[1][0] == 15
    assert sfpu.lregs[1][1] == 32
    assert sfpu.lregs[1][2] == 0

  def test_sfpabs(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = _f2b(-42.0)
    sfpu.lregs[0][1] = _f2b(42.0)

    word = (0x7D << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfpabs(decode_tensix(word))

    assert abs(_b2f(sfpu.lregs[1][0]) - 42.0) < 0.001
    assert abs(_b2f(sfpu.lregs[1][1]) - 42.0) < 0.001

  def test_sfpsetcc(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = _f2b(-1.0)  # negative
    sfpu.lregs[0][1] = _f2b(0.0)   # zero
    sfpu.lregs[0][2] = _f2b(5.0)   # positive

    # mod=0: flag = (VC < 0)
    word = (0x7B << 24) | (0 << 8) | (0 << 4) | 0
    sfpu.sfpsetcc(decode_tensix(word))
    assert sfpu.lane_flags[0] is True   # -1 < 0
    assert sfpu.lane_flags[1] is False  # 0 is not < 0
    assert sfpu.lane_flags[2] is False  # 5 is not < 0

  def test_sfpsetcc_zero(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = _f2b(0.0)
    sfpu.lregs[0][1] = _f2b(1.0)

    # mod=3: flag = (VC == 0)
    word = (0x7B << 24) | (0 << 8) | (0 << 4) | 3
    sfpu.sfpsetcc(decode_tensix(word))
    assert sfpu.lane_flags[0] is True   # 0 == 0
    assert sfpu.lane_flags[1] is False  # 1 != 0

  def test_predication(self):
    sfpu, _ = self._make()

    # Enable predication with all lanes True
    word = (0x8A << 24) | 1
    sfpu.sfpencc(decode_tensix(word))
    assert sfpu.use_lane_flags is True
    assert all(sfpu.lane_flags)

    # Disable some lanes
    sfpu.lane_flags[0] = False
    sfpu.lane_flags[1] = False

    # Load U16=999 — should only affect enabled lanes
    for lane in range(32):
      sfpu.lregs[0][lane] = 0
    word = (0x71 << 24) | (0 << 20) | (4 << 16) | 999
    sfpu.sfploadi(decode_tensix(word))

    assert sfpu.lregs[0][0] == 0    # disabled
    assert sfpu.lregs[0][1] == 0    # disabled
    assert sfpu.lregs[0][2] == 999  # enabled

  def test_pushc_compc_popc(self):
    sfpu, _ = self._make()

    # Set specific flags
    sfpu.lane_flags = [True] * 16 + [False] * 16

    # Push
    word = (0x87 << 24)
    sfpu.sfppushc(decode_tensix(word))

    # Complement (else)
    word = (0x8B << 24)
    sfpu.sfpcompc(decode_tensix(word))
    assert sfpu.lane_flags[:16] == [False] * 16
    assert sfpu.lane_flags[16:] == [True] * 16

    # Pop (restore)
    word = (0x88 << 24)
    sfpu.sfppopc(decode_tensix(word))
    assert sfpu.lane_flags[:16] == [True] * 16
    assert sfpu.lane_flags[16:] == [False] * 16

  def test_sfpmov(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(42.0)

    # VD = VC
    word = (0x7C << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfpmov(decode_tensix(word))
    assert abs(_b2f(sfpu.lregs[1][0]) - 42.0) < 0.001

    # VD = -VC
    word = (0x7C << 24) | (0 << 8) | (2 << 4) | 1
    sfpu.sfpmov(decode_tensix(word))
    assert abs(_b2f(sfpu.lregs[2][0]) - (-42.0)) < 0.001

  def test_sfpexexp_raw(self):
    sfpu, _ = self._make()
    # FP32 for 8.0: sign=0, exp=130, mant=0 => 0x41000000
    sfpu.lregs[0][0] = 0x41000000

    word = (0x77 << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfpexexp(decode_tensix(word))
    assert sfpu.lregs[1][0] == 130

  def test_sfpexexp_debiased(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = 0x41000000  # 8.0: exp=130

    word = (0x77 << 24) | (0 << 8) | (1 << 4) | 1
    sfpu.sfpexexp(decode_tensix(word))
    assert sfpu.lregs[1][0] == 3  # 130 - 127 = 3 (2^3 = 8)

  def test_sfparecip(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(4.0)

    word = (0x99 << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfparecip(decode_tensix(word))
    assert abs(_b2f(sfpu.lregs[1][0]) - 0.25) < 0.001

  def test_sfplutfp32(self):
    sfpu, _ = self._make()
    for lane in range(32):
      # Piece 0 (|x| < 1): slope=2.0, intercept=1.0
      sfpu.lregs[0][lane] = _f2b(2.0)
      sfpu.lregs[4][lane] = _f2b(1.0)
      # Input x = 0.5 (piece 0)
      sfpu.lregs[3][lane] = _f2b(0.5)

    word = (0x95 << 24) | (5 << 4) | 0
    sfpu.sfplutfp32(decode_tensix(word))

    # Result = 2.0 * 0.5 + 1.0 = 2.0
    assert abs(_b2f(sfpu.lregs[5][0]) - 2.0) < 0.001

  def test_sfpswap(self):
    sfpu, _ = self._make()
    for lane in range(32):
      sfpu.lregs[0][lane] = _f2b(10.0)
      sfpu.lregs[1][lane] = _f2b(3.0)

    word = (0x92 << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfpswap(decode_tensix(word))

    # VD = min, VC = max
    assert abs(_b2f(sfpu.lregs[1][0]) - 3.0) < 0.001   # min
    assert abs(_b2f(sfpu.lregs[0][0]) - 10.0) < 0.001   # max

  def test_sfpconfig(self):
    sfpu, _ = self._make()
    # Load BF16 1.0 (0x3F80) into LReg[11]
    word = (0x91 << 24) | (0x3F80 << 8) | (11 << 4) | 0
    sfpu.sfpconfig(decode_tensix(word))
    assert abs(_b2f(sfpu.lregs[11][0]) - 1.0) < 0.001

  def test_sfpgt(self):
    sfpu, _ = self._make()
    sfpu.lregs[0][0] = _f2b(5.0)
    sfpu.lregs[1][0] = _f2b(3.0)   # VD=LReg[1] > VC=LReg[0]? 3 > 5? No
    sfpu.lregs[1][1] = _f2b(10.0)  # 10 > 5? Yes

    sfpu.lregs[0][1] = _f2b(5.0)

    word = (0x97 << 24) | (0 << 8) | (1 << 4) | 0
    sfpu.sfpgt(decode_tensix(word))
    assert sfpu.lane_flags[0] is False  # 3 > 5 = False
    assert sfpu.lane_flags[1] is True   # 10 > 5 = True


# =============================================================================
# TRISC1 Decoder Tests — FPU/SFPU dispatch through the full pipeline
# =============================================================================

class TestTRISC1Dispatch:
  def test_zeroacc_through_pipeline(self):
    c = _make_coproc()
    # Mark Dest rows as valid
    for r in range(100):
      c.dest.valid[r] = True

    # Push ZEROACC CLR_ALL through thread 1
    word = (0x10 << 24) | (3 << 19)
    c.push_instruction(1, word)
    c.step()

    assert not any(c.dest.valid)

  def test_sfploadi_through_pipeline(self):
    c = _make_coproc()
    # Push SFPLOADI U16=0xABCD into LReg[0] through thread 1
    word = (0x71 << 24) | (0 << 20) | (4 << 16) | 0xABCD
    c.push_instruction(1, word)
    c.step()

    assert c.sfpu.lregs[0][0] == 0xABCD

  def test_setrwc_through_pipeline(self):
    c = _make_coproc()
    # Push SETRWC: set d=5, bitmask=0x04
    word = (0x37 << 24) | (0 << 22) | (0 << 18) | (5 << 14) | (0 << 10) | (0 << 6) | 0x04
    c.push_instruction(1, word)
    c.step()

    assert c.rwc[1].d == 5

  def test_elwadd_through_pipeline(self):
    c = _make_coproc()

    # Pre-load SrcA and SrcB banks (FPU bank)
    srca_bank = c.srca.banks[c.srca.fpu_bank]
    srcb_bank = c.srcb.banks[c.srcb.fpu_bank]
    srca_bank.rows[0][0] = _float_to_19bit(3.0)
    srcb_bank.rows[0][0] = _float_to_19bit(7.0)

    word = (0x28 << 24) | 0
    c.push_instruction(1, word)
    c.step()

    actual = _dest_to_float(c.dest.bits[0][0])
    assert abs(actual - 10.0) < 0.1

  def test_adc_through_pipeline(self):
    c = _make_coproc()
    # SETADC: Unpacker0, channel 0, dim X = 42
    word = (0x50 << 24) | (1 << 21) | (0 << 20) | (0 << 18) | 42
    c.push_instruction(0, word)
    c.step()

    assert c.adc[0].unpackers[0].channels[0].x.val == 42


# =============================================================================
# TRISC0/TRISC2 Decoder Tests
# =============================================================================

class TestTRISC0Dispatch:
  def test_unpacr_nop_bank_flip(self):
    c = _make_coproc()
    assert c.srca.banks[0].allowed_client == "unpackers"

    # UNPACR_NOP: unpacker_sel=0 (SrcA), set_dvalid=1
    word = (0x43 << 24) | (0 << 23) | (1 << 8)
    c.push_instruction(0, word)
    c.step()

    assert c.srca.banks[0].allowed_client == "matrix_unit"

  def test_unpacr_bank_flip(self):
    c = _make_coproc()
    # UNPACR: block_sel=1 (SrcB), set_dvalid=1
    word = (0x42 << 24) | (1 << 23) | (1 << 6)
    c.push_instruction(0, word)
    c.step()

    assert c.srcb.banks[0].allowed_client == "matrix_unit"


class TestTRISC2Dispatch:
  def test_pacr_accepted(self):
    c = _make_coproc()
    # PACR: basic pack, last=1
    word = (0x41 << 24) | 1
    c.push_instruction(2, word)
    c.step()
    # Should not crash; pack is a structural no-op in functional emu

  def test_pacr_from_any_thread(self):
    c = _make_coproc()
    word = (0x41 << 24) | 1
    c.push_instruction(1, word)  # issued by T1
    c.step()
    # Should not crash
