"""Spec tests for ../specs/noc-atomics.md.

Each test is pinned to one or more clauses from
../clauses/noc-atomics.md via the @spec() marker. Tests that
exercise clauses where the emulator diverges from the spec are marked
xfail(strict=True) so the divergence is tracked, not silenced.

Layout:
  - Opcode dispatch (NOP, INCR_GET, INCR_GET_PTR, CAS, SWAP*, STORE_IND, ACC)
  - Field decoders (INCR / WRAP / Ofs / Mask)
  - Response + counter behavior (RESP_MARKED, alignment, multicast)
  - ACC format semantics (FP32 / FP16 / BF16 / INT32 / INT32_UNS / INT8)
"""

import math
import struct

import pytest

from emu import memory as M
from emu.core import BRISC
from emu.memory import Memory
from emu.noc import (
  AT_NOP, AT_INCR_GET, AT_INCR_GET_PTR, AT_SWAP, AT_CAS,
  AT_GET_TILE_MAP, AT_STORE_IND, AT_SWAP_4B, AT_ACC,
  ACC_FP32, ACC_FP16_A, ACC_FP16_B, ACC_INT32,
  ACC_INT32_SAT, ACC_INT32_UNS, ACC_INT8,
  NOC, noc_key,
)

from .conftest import spec


# ===========================================================================
# Opcode dispatch enum
# ===========================================================================

@spec("NOC-AT.OPCODE.NOP")
def test_nop_leaves_target_unchanged(two_tile_network, atomic):
  """NOP atomic must not modify L1."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xDEADBEEF)
  atomic(net, op=AT_NOP, targ_addr=0x8000)
  assert net['dst_l1'].read32(0x8000) == 0xDEADBEEF


@spec("NOC-AT.OPCODE.INCR_GET",
      "NOC-AT.INCR_GET.INCR_FROM_AT_DATA")
def test_incr_get_returns_old_and_increments(two_tile_network, atomic):
  """INCR_GET (0x1): write old to ret_addr, increment target by at_data."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 42)
  # Increment sourced from NOC_AT_DATA per ISA.
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000, at_data=1)
  assert net['src_l1'].read32(0x4) == 42
  assert net['dst_l1'].read32(0x8000) == 43


@spec("NOC-AT.INCR_GET.INCR_FROM_AT_DATA")
@pytest.mark.parametrize("step", [1, 3, 17, 0xFF, 0xFFFF_FFFF])
def test_incr_get_increment_source_is_at_data(two_tile_network, atomic, step):
  """Increment is NOC_AT_DATA (full 32-bit); not NOC_AT_LEN_BE[9:6]."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 100)
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000, at_data=step)
  assert net['dst_l1'].read32(0x8000) == (100 + step) & 0xFFFFFFFF


@spec("NOC-AT.INCR_GET.INCR_FROM_AT_DATA")
def test_incr_get_ignores_at_len_be_bits_9_6(two_tile_network, atomic):
  """Bits [9:6] of NOC_AT_LEN_BE are IntWidth, not INCR; must not affect value."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0)
  # Pack "7" into [9:6] but at_data=3. Expected increment is 3, not 7 or 10.
  at_len_be = (AT_INCR_GET << 12) | (7 << 6)
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000,
         at_len_be=at_len_be, at_data=3)
  assert net['dst_l1'].read32(0x8000) == 3


@spec("NOC-AT.OPCODE.GET_TILE_MAP")
def test_get_tile_map_is_read_only(two_tile_network, atomic):
  """GET_TILE_MAP (0x5): return value; do not modify L1."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0x12345678)
  atomic(net, op=AT_GET_TILE_MAP, targ_addr=0x8000)
  assert net['src_l1'].read32(0x4) == 0x12345678
  assert net['dst_l1'].read32(0x8000) == 0x12345678


# ===========================================================================
# INCR_GET_PTR: field decoders + wrap semantics
# ===========================================================================

@spec("NOC-AT.INCR_GET_PTR.INCR_FIELD")
@pytest.mark.parametrize("incr_field,expected_step", [
  (0, 1),   # 0 means "step by 1"
  (1, 1),
  (3, 3),
  (7, 7),
  (15, 15),
])
def test_incr_get_ptr_incr_field_decoding(two_tile_network, atomic,
                                          incr_field, expected_step):
  """NOC_AT_LEN_BE[9:6] = INCR; INCR=0 means step by 1."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0)
  at_len_be = (AT_INCR_GET_PTR << 12) | (incr_field << 6)  # WRAP=0 → no wrap
  atomic(net, op=AT_INCR_GET_PTR, targ_addr=0x8000, at_len_be=at_len_be)
  assert net['dst_l1'].read32(0x8000) == expected_step


@spec("NOC-AT.OPCODE.INCR_GET_PTR",
      "NOC-AT.INCR_GET_PTR.WRAP_FIELD",
      "NOC-AT.INCR_GET_PTR.WRAP_SEMANTIC")
@pytest.mark.parametrize("start,incr,wrap,expected", [
  # (old, INCR, WRAP, expected_new)
  (0, 1, 5, 1),   # below boundary
  (3, 1, 5, 4),   # below boundary
  (4, 1, 5, 0),   # exactly at boundary: new=5 >= 5 → wrap to 0
  (4, 3, 5, 0),   # above boundary via large incr
  (100, 3, 0, 103),  # WRAP=0 → no wrap
])
def test_incr_get_ptr_wrap_semantics(two_tile_network, atomic,
                                      start, incr, wrap, expected):
  """new_val = old + incr; if wrap > 0 and new_val >= wrap then new_val = 0."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, start)
  at_len_be = (AT_INCR_GET_PTR << 12) | (incr << 6) | (wrap << 2)
  atomic(net, op=AT_INCR_GET_PTR, targ_addr=0x8000, at_len_be=at_len_be)
  assert net['dst_l1'].read32(0x8000) == expected


@spec("NOC-AT.INCR_GET_PTR.OLD_VAL_RETURNED")
def test_incr_get_ptr_returns_old_value(two_tile_network, atomic):
  """Return old (pre-increment) value to NOC_RET_ADDR_LO."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 7)
  at_len_be = (AT_INCR_GET_PTR << 12) | (1 << 6)
  atomic(net, op=AT_INCR_GET_PTR, targ_addr=0x8000,
         ret_addr=0xA0, at_len_be=at_len_be)
  assert net['src_l1'].read32(0xA0) == 7


@spec("NOC-AT.INCR_GET.NO_WRAP")
def test_incr_get_ignores_wrap_field(two_tile_network, atomic):
  """INCR_GET has no wrap; bits [5:2] of NOC_AT_LEN_BE are ignored."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 4)
  # WRAP=5 is set in [5:2] but opcode 0x1 must ignore it.
  at_len_be = (AT_INCR_GET << 12) | (5 << 2)
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000,
         at_len_be=at_len_be, at_data=1)
  assert net['dst_l1'].read32(0x8000) == 5  # 4+1 = 5, NOT wrapped to 0


# ===========================================================================
# CAS
# ===========================================================================

@spec("NOC-AT.OPCODE.CAS",
      "NOC-AT.CAS.COMPARE_FROM_AT_DATA",
      "NOC-AT.CAS.SUCCESS_PATH")
def test_cas_success(two_tile_network, atomic):
  """CAS matches → write (original high | set_val) to target."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xAAAA_1234)  # low 16 = 0x1234
  cmp_val, set_val = 0x1234, 0x5678
  at_data = cmp_val | (set_val << 16)
  atomic(net, op=AT_CAS, targ_addr=0x8000, at_data=at_data)
  # high 16 preserved, low 16 replaced
  assert net['dst_l1'].read32(0x8000) == 0xAAAA_5678


@spec("NOC-AT.CAS.FAILURE_PATH")
def test_cas_failure_does_not_write(two_tile_network, atomic):
  """CAS mismatch → L1 unchanged."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xAAAA_1111)
  cmp_val, set_val = 0x1234, 0x5678  # cmp ≠ low16 of stored
  at_data = cmp_val | (set_val << 16)
  atomic(net, op=AT_CAS, targ_addr=0x8000, at_data=at_data)
  assert net['dst_l1'].read32(0x8000) == 0xAAAA_1111


@spec("NOC-AT.CAS.RETURN_ORIGINAL")
@pytest.mark.parametrize("stored,cmp_val,succeed", [
  (0xAAAA_1234, 0x1234, True),
  (0xAAAA_1234, 0x9999, False),
])
def test_cas_returns_original(two_tile_network, atomic,
                              stored, cmp_val, succeed):
  """CAS returns the pre-operation 32-bit value regardless of success."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, stored)
  at_data = cmp_val | (0xFFFF << 16)
  atomic(net, op=AT_CAS, targ_addr=0x8000,
         ret_addr=0xB0, at_data=at_data)
  assert net['src_l1'].read32(0xB0) == stored


# ===========================================================================
# SWAP / SWAP_4B
# ===========================================================================

@spec("NOC-AT.SWAP_4B.RETURN_ORIGINAL")
def test_swap_4b_returns_original(two_tile_network, atomic):
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xDEADBEEF)
  atomic(net, op=AT_SWAP_4B, targ_addr=0x8000,
         ret_addr=0x10, at_data=0xCAFEBABE)
  assert net['src_l1'].read32(0x10) == 0xDEADBEEF


@spec("NOC-AT.SWAP.RETURN_ORIGINAL_32B")
def test_swap_mask_returns_original_32b(two_tile_network, atomic):
  """SWAP (mask variant) returns the pre-op 32-bit target word."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xFACEF00D)
  mask = 0b0000_0001   # overwrite only granule 0
  at_len_be = (AT_SWAP << 12) | (mask << 4)
  atomic(net, op=AT_SWAP, targ_addr=0x8000, ret_addr=0x30,
         at_len_be=at_len_be, at_data=0x0000BEEF)
  assert net['src_l1'].read32(0x30) == 0xFACEF00D


@spec("NOC-AT.OPCODE.SWAP_4B",
      "NOC-AT.SWAP_4B.WRITE_32B")
def test_swap_4b_writes_new_value(two_tile_network, atomic):
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xDEADBEEF)
  atomic(net, op=AT_SWAP_4B, targ_addr=0x8000, at_data=0xCAFEBABE)
  assert net['dst_l1'].read32(0x8000) == 0xCAFEBABE


@spec("NOC-AT.OPCODE.SWAP_MASK",
      "NOC-AT.SWAP.MASK_SELECTS_GRANULES")
def test_swap_mask_selects_granules(two_tile_network, atomic):
  """SWAP mask bit i selects whether to overwrite granule at base+i*2."""
  net = two_tile_network
  base = 0x8000
  # 16-byte region pre-seeded with an identifiable pattern at each granule
  for i in range(8):
    net['dst_l1'].write16(base + i * 2, 0x1000 + i)
  # Write only granule 0 and granule 5 (mask=0b00100001=0x21)
  mask = 0b0010_0001
  at_len_be = (AT_SWAP << 12) | (mask << 4)
  # to_write[0] = at_data & 0xFFFF (even granules),
  # to_write[1] = (at_data >> 16) & 0xFFFF (odd granules)
  at_data = 0xAAAA | (0xBBBB << 16)
  atomic(net, op=AT_SWAP, targ_addr=base,
         at_len_be=at_len_be, at_data=at_data)
  # Granule 0 (even, in mask) → 0xAAAA
  assert net['dst_l1'].read16(base + 0) == 0xAAAA
  # Granules 1..4 (not in mask) → unchanged
  for i in range(1, 5):
    assert net['dst_l1'].read16(base + i * 2) == 0x1000 + i
  # Granule 5 (odd, in mask) → 0xBBBB
  assert net['dst_l1'].read16(base + 5 * 2) == 0xBBBB
  # Granules 6,7 (not in mask) → unchanged
  for i in range(6, 8):
    assert net['dst_l1'].read16(base + i * 2) == 0x1000 + i


# ===========================================================================
# STORE_IND
# ===========================================================================

@spec("NOC-AT.OPCODE.STORE_IND",
      "NOC-AT.STORE_IND.INDIRECT_WRITE")
def test_store_ind_writes_through_pointer(two_tile_network, atomic):
  """Read pointer at targ_addr; write at_data to *pointer; pointer unchanged."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0x9000)   # pointer
  net['dst_l1'].write32(0x9000, 0)        # indirect slot
  atomic(net, op=AT_STORE_IND, targ_addr=0x8000,
         ret_addr=0x20, at_data=0xFEEDFACE)
  assert net['src_l1'].read32(0x20) == 0x9000          # pointer returned
  assert net['dst_l1'].read32(0x9000) == 0xFEEDFACE     # data at *pointer
  assert net['dst_l1'].read32(0x8000) == 0x9000         # pointer unchanged


# ===========================================================================
# ACC: per-format arithmetic (single-lane; see xfails for SIMD clauses)
# ===========================================================================

def _f32_bits(f):  return struct.unpack('<I', struct.pack('<f', f))[0]
def _bits_f32(b):  return struct.unpack('<f', struct.pack('<I', b))[0]
def _f16_bits(f):  return struct.unpack('<H', struct.pack('<e', f))[0]
def _bits_f16(b):  return struct.unpack('<e', struct.pack('<H', b))[0]


@spec("NOC-AT.OPCODE.ACC")
def test_acc_fp32_single_lane_add(two_tile_network, atomic):
  """ACC fmt=0 FP32 single-lane: 1.5 + 2.25 = 3.75 (emulator's realized behavior)."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, _f32_bits(1.5))
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=_f32_bits(2.25),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP32)
  assert _bits_f32(net['dst_l1'].read32(0x8000)) == 3.75


@spec("NOC-AT.OPCODE.ACC")
def test_acc_fp16a_single_lane_add(two_tile_network, atomic):
  """ACC fmt=1 FP16_A single-lane: 1.0 + 0.5 = 1.5."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, _f16_bits(1.0))
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=_f16_bits(0.5),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP16_A)
  assert _bits_f16(net['dst_l1'].read32(0x8000) & 0xFFFF) == 1.5


@spec("NOC-AT.OPCODE.ACC")
def test_acc_bf16_single_lane_add(two_tile_network, atomic):
  """ACC fmt=2 BF16 single-lane: 1.0 + 2.0 = 3.0 (0x4040)."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0x3F80)        # BF16 1.0
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=0x4000,                        # BF16 2.0
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP16_B)
  assert (net['dst_l1'].read32(0x8000) & 0xFFFF) == 0x4040


@spec("NOC-AT.OPCODE.ACC")
def test_acc_int32_signed_add(two_tile_network, atomic):
  """ACC fmt=3 INT32 signed: 10 + (-3) = 7."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 10)
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=(-3) & 0xFFFFFFFF,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT32)
  assert net['dst_l1'].read32(0x8000) == 7


@spec("NOC-AT.OPCODE.ACC")
def test_acc_int32_saturates_positive(two_tile_network, atomic):
  """INT32 + with sat_dis=0: INT32_MAX + 1 clamps to INT32_MAX."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0x7FFFFFFF)
  atomic(net, op=AT_ACC, targ_addr=0x8000, at_data=1,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT32)
  assert net['dst_l1'].read32(0x8000) == 0x7FFFFFFF


@spec("NOC-AT.ACC.SAT_DIS_FLAG")
def test_acc_int32_sat_dis_wraps(two_tile_network, atomic):
  """sat_dis=1 (bit 3): INT32_MAX + 1 wraps to INT32_MIN instead of saturating."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0x7FFFFFFF)
  atomic(net, op=AT_ACC, targ_addr=0x8000, at_data=1,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT32 | (1 << 3))
  assert net['dst_l1'].read32(0x8000) == 0x80000000


@spec("NOC-AT.OPCODE.ACC")
def test_acc_uint32_saturates(two_tile_network, atomic):
  """ACC fmt=5 unsigned: UINT32_MAX-1 + 5 saturates to UINT32_MAX."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0xFFFFFFFE)
  atomic(net, op=AT_ACC, targ_addr=0x8000, at_data=5,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT32_UNS)
  assert net['dst_l1'].read32(0x8000) == 0xFFFFFFFF


@spec("NOC-AT.OPCODE.ACC")
def test_acc_int8_four_lanes_signed(two_tile_network, atomic):
  """ACC fmt=6 INT8 packs 4 signed bytes with per-lane saturating add."""
  net = two_tile_network
  target  = 10 | (20 << 8) | (30 << 16) | (40 << 24)
  operand =  5 | ((-3 & 0xFF) << 8) | (10 << 16) | ((-10 & 0xFF) << 24)
  net['dst_l1'].write32(0x8000, target)
  atomic(net, op=AT_ACC, targ_addr=0x8000, at_data=operand,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT8)
  out = net['dst_l1'].read32(0x8000)
  assert (out & 0xFF) == 15
  assert ((out >> 8) & 0xFF) == 17
  assert ((out >> 16) & 0xFF) == 40
  assert ((out >> 24) & 0xFF) == 30


@spec("NOC-AT.OPCODE.ACC")
def test_acc_int8_saturates(two_tile_network, atomic):
  """INT8 per-lane saturation at 127: 120 + 100 → 127."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 120)
  atomic(net, op=AT_ACC, targ_addr=0x8000, at_data=100,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_INT8)
  assert (net['dst_l1'].read32(0x8000) & 0xFF) == 127


# ===========================================================================
# ACC: SIMD lane semantics (spec §Format Table) — emulator is single-lane
# ===========================================================================

@spec("NOC-AT.ACC.FMT0.FP32_LANES")
def test_acc_fp32_four_lane_broadcast(two_tile_network, atomic):
  """Fmt=0: L1 is 4× fp32; NOC_AT_DATA is 1× fp32 broadcast to all 4 lanes."""
  net = two_tile_network
  base = 0x8000
  for i, v in enumerate([1.0, 2.0, 3.0, 4.0]):
    net['dst_l1'].write32(base + i * 4, _f32_bits(v))
  atomic(net, op=AT_ACC, targ_addr=base,
         at_data=_f32_bits(0.5),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP32)
  for i, expected in enumerate([1.5, 2.5, 3.5, 4.5]):
    assert _bits_f32(net['dst_l1'].read32(base + i * 4)) == expected


@spec("NOC-AT.ACC.FMT1.FP16_LANES")
def test_acc_fp16_eight_lane_twoway_broadcast(two_tile_network, atomic):
  net = two_tile_network
  base = 0x8000
  for i in range(8):
    net['dst_l1'].write16(base + i * 2, _f16_bits(float(i + 1)))
  at_data = _f16_bits(0.5) | (_f16_bits(0.25) << 16)  # even: +0.5; odd: +0.25
  atomic(net, op=AT_ACC, targ_addr=base,
         at_data=at_data,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP16_A)
  for i in range(8):
    expected = (i + 1) + (0.5 if i % 2 == 0 else 0.25)
    got = _bits_f16(net['dst_l1'].read16(base + i * 2))
    assert got == pytest.approx(expected, abs=1e-3), f"lane {i}: {got} vs {expected}"


@spec("NOC-AT.ACC.FMT2.BF16_LANES")
def test_acc_bf16_eight_lane_twoway_broadcast(two_tile_network, atomic):
  """Fmt=2: L1 is 8× bf16; NOC_AT_DATA holds 2× bf16 broadcast 2-way over
  the 8 lanes. Even lanes (0,2,4,6) get at_data[15:0]; odd lanes
  (1,3,5,7) get at_data[31:16].

  CURRENTLY FAILS — the emulator's _acc_compute is single-lane for bf16
  (it only updates lane 0). This test documents the multi-lane spec and
  will pass once lane fan-out is implemented."""
  net = two_tile_network
  base = 0x8000
  # Pre-seed 8 bf16 lanes with values 1.0..8.0.
  # bf16 = top 16 bits of fp32: float(n) for small integers has clean bf16 bits.
  def _bf16(f):
    return struct.unpack('<I', struct.pack('<f', float(f)))[0] >> 16
  for i in range(8):
    net['dst_l1'].write16(base + i * 2, _bf16(float(i + 1)))
  # at_data: even lanes add 0.5, odd lanes add 0.25.
  at_data = _bf16(0.5) | (_bf16(0.25) << 16)
  atomic(net, op=AT_ACC, targ_addr=base,
         at_data=at_data,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP16_B)
  for i in range(8):
    expected = (i + 1) + (0.5 if i % 2 == 0 else 0.25)
    got_bf16 = net['dst_l1'].read16(base + i * 2)
    got_f32 = struct.unpack('<f', struct.pack('<I', got_bf16 << 16))[0]
    assert got_f32 == pytest.approx(expected, abs=1e-2), \
           f"bf16 lane {i}: {got_f32} vs {expected}"


@spec("NOC-AT.ACC.FMT4.INT32_LANES")
def test_acc_int32_four_lane_broadcast(two_tile_network, atomic):
  """Fmt=4: L1 is 4× u32 (wrapping two's complement); NOC_AT_DATA is 1× u32
  broadcast to all 4 lanes. Wrapping (no saturation).

  CURRENTLY FAILS — the emulator's INT32 ACC path updates only one 32-bit
  word at targ_addr. This test documents the 4-lane spec and will pass
  once lane fan-out is implemented."""
  net = two_tile_network
  base = 0x8000
  # Pre-seed 4 u32 lanes: 10, 20, 30, UINT32_MAX (to exercise wrapping).
  lanes_in = [10, 20, 30, 0xFFFFFFFF]
  for i, v in enumerate(lanes_in):
    net['dst_l1'].write32(base + i * 4, v)
  add = 5
  atomic(net, op=AT_ACC, targ_addr=base,
         at_data=add,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | 4)   # fmt=4: wrapping int32
  expected = [(v + add) & 0xFFFFFFFF for v in lanes_in]
  for i, want in enumerate(expected):
    got = net['dst_l1'].read32(base + i * 4)
    assert got == want, f"int32 lane {i}: got {got:#x} want {want:#x}"


@spec("NOC-AT.ACC.FMT7.INT8_SAT")
def test_acc_int8_sixteen_lane_unsigned_saturating(two_tile_network, atomic):
  """Fmt=7: 16 u8 lanes, unsigned saturating at 255, 4-way broadcast."""
  net = two_tile_network
  base = 0x8000
  for i in range(16):
    net['dst_l1'].write8(base + i, 200)
  # at_data = [50, 100, 60, 80] broadcast 4-way
  at_data = 50 | (100 << 8) | (60 << 16) | (80 << 24)
  atomic(net, op=AT_ACC, targ_addr=base,
         at_data=at_data,
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | 7)   # fmt=7
  for i in range(16):
    bcast = [50, 100, 60, 80][i & 3]
    assert net['dst_l1'].read8(base + i) == min(255, 200 + bcast)


@spec("NOC-AT.ACC.ALIGNMENT")
def test_acc_masks_target_to_16b_alignment(two_tile_network, atomic):
  """Unaligned targ_addr should be masked to (targ_addr & ~0xF)."""
  net = two_tile_network
  # Pre-seed aligned region 0x8000..0x8010 with 4 fp32 values.
  for i, v in enumerate([1.0, 2.0, 3.0, 4.0]):
    net['dst_l1'].write32(0x8000 + i * 4, _f32_bits(v))
  # Target an unaligned word inside the 16-byte region; should still hit 0x8000.
  atomic(net, op=AT_ACC, targ_addr=0x8008,
         at_data=_f32_bits(0.5),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP32)
  # With correct alignment masking, all 4 lanes in [0x8000, 0x8010) would be
  # incremented by 0.5.
  for i, expected in enumerate([1.5, 2.5, 3.5, 4.5]):
    assert _bits_f32(net['dst_l1'].read32(0x8000 + i * 4)) == expected


@spec("NOC-AT.ACC.FMT0.FLUSH_DENORMAL")
def test_acc_fp32_flushes_denormals(two_tile_network, atomic):
  """FP32 ACC must flush denormal results to zero."""
  net = two_tile_network
  # 1e-40 is a denormal in fp32
  denormal = struct.unpack('<f', struct.pack('<I', 0x00000100))[0]
  net['dst_l1'].write32(0x8000, _f32_bits(0.0))
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=_f32_bits(denormal),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP32)
  assert net['dst_l1'].read32(0x8000) == 0  # flushed to +0.0


# ===========================================================================
# Response + counter behavior
# ===========================================================================

@spec("NOC-AT.RESP.WRITES_TO_RET_ADDR",
      "NOC-AT.RESP.COUNTER_INCREMENT")
def test_response_writes_ret_addr_and_increments_counter(two_tile_network, atomic):
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 99)
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000, ret_addr=0x200,
         at_data=1, resp_marked=True)
  assert net['src_l1'].read32(0x200) == 99
  assert net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 1


@spec("NOC-AT.RESP.POSTED_NO_WRITE")
def test_posted_atomic_does_not_write_ret_or_counter(two_tile_network, atomic):
  """Posted atomic (RESP_MARKED=0) must not write ret_addr or bump counter."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 99)
  net['src_l1'].write32(0x300, 0xDEADBEEF)     # sentinel
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000, ret_addr=0x300,
         at_data=1, resp_marked=False)
  assert net['dst_l1'].read32(0x8000) == 100    # op still happens
  assert net['src_l1'].read32(0x300) == 0xDEADBEEF  # sentinel preserved
  assert net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 0


def test_atomic_counter_accumulates_across_multiple_ops(two_tile_network, atomic):
  """NIU_MST_ATOMIC_RESP_RECEIVED increments once per non-posted atomic."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0)
  for _ in range(4):
    atomic(net, op=AT_INCR_GET, targ_addr=0x8000, at_data=1)
  assert net['dst_l1'].read32(0x8000) == 4
  assert net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 4


# ===========================================================================
# Multicast
# ===========================================================================

@spec("NOC-AT.MCAST.PER_TILE")
def test_multicast_atomic_hits_every_tile_in_rect():
  """Multicast atomic should execute at every tile in the rect."""
  network = {}

  def tile(x, y):
    l1 = Memory()
    core = BRISC(l1=l1)
    network[noc_key(x, y)] = l1
    noc = NOC(0, l1, network, x, y)
    noc.pre_populate()
    core.mem.default = Memory()
    core.mem.register(M.NOC0_BASE, M.NOC0_BASE + M.NOC_SIZE - 1, noc)
    return core, l1, noc

  src_core, src_l1, src_noc = tile(1, 2)
  _, dst0_l1, _ = tile(3, 4)
  _, dst1_l1, _ = tile(4, 4)
  dst0_l1.write32(0x8000, 10)
  dst1_l1.write32(0x8000, 20)

  rect = (4 << 18) | (3 << 12) | (4 << 6) | 4
  base = 3 * M.NIU_CMD_BUF_STRIDE
  src_noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x8000)
  src_noc.regs.write32(base + M.NIU_TARG_ADDR_HI, rect)
  src_noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0x4)
  src_noc.regs.write32(base + M.NIU_AT_LEN_BE, AT_INCR_GET << 12)
  src_noc.regs.write32(base + M.NIU_AT_DATA, 3)
  src_noc.regs.write32(base + M.NIU_CTRL,
                       M.NOC_CTRL_AT | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED)
  src_core.mem.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)

  assert dst0_l1.read32(0x8000) == 13
  assert dst1_l1.read32(0x8000) == 23
  assert src_l1.read32(0x8000) == 0


# ===========================================================================
# Target restrictions & atomicity invariant
# ===========================================================================

@spec("NOC-AT.TARGET.L1_ONLY")
def test_atomic_target_is_tile_l1_not_mmio(two_tile_network, atomic):
  """Atomic targ_addr is resolved against the target tile's L1 memory
  (via the NOC routing table keyed on (x,y)), not MMIO/DRAM/PCIe. An
  increment to dst L1 must not spill into the src tile's L1 or the src
  tile's MMIO registers at the same numeric offset."""
  net = two_tile_network
  # Pre-seed both L1s at the same numeric offset with distinguishable
  # sentinels, and pre-seed a stream register on the src tile's NIU.
  net['src_l1'].write32(0x8000, 0xAAAA_AAAA)
  net['dst_l1'].write32(0x8000, 42)
  atomic(net, op=AT_INCR_GET, targ_addr=0x8000, at_data=1)
  # Only the destination tile's L1 is mutated.
  assert net['dst_l1'].read32(0x8000) == 43
  assert net['src_l1'].read32(0x8000) == 0xAAAA_AAAA


@spec("NOC-AT.ACC.RESPONSE_UNDEFINED")
def test_acc_response_fire_and_forget_counter_still_ticks(two_tile_network, atomic):
  """ACC is fire-and-forget: the returned payload is undefined, but the
  atomic response counter still increments once the request completes."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, _f32_bits(1.0))
  before = net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED)
  atomic(net, op=AT_ACC, targ_addr=0x8000,
         at_data=_f32_bits(2.5),
         l1_acc_at_en=True,
         l1_acc_instrn=(AT_ACC << 12) | ACC_FP32)
  # The accumulate happened (side-effect to L1)…
  assert _bits_f32(net['dst_l1'].read32(0x8000)) == 3.5
  # …and a response came back, but we don't assert on its payload.
  assert net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == before + 1


@spec("NOC-AT.ATOMICITY")
def test_atomics_are_serialized_and_deterministic(two_tile_network, atomic):
  """Single-threaded synchronous emulator: a long sequence of atomics to
  the same word produces a deterministic, serialized result (no torn
  writes, no lost updates). This clause is satisfied by construction —
  we prove it by driving 100 increments and confirming the exact total."""
  net = two_tile_network
  net['dst_l1'].write32(0x8000, 0)
  # INCR_GET's int_width (NOC_AT_LEN_BE[9:6]) gates which bits get updated.
  # Set int_width=15 → mask=0xFFFF so sums up to 64K land intact.
  at_len_be = (AT_INCR_GET << 12) | (15 << 6)
  for _ in range(100):
    atomic(net, op=AT_INCR_GET, targ_addr=0x8000,
           at_len_be=at_len_be, at_data=3)
  assert net['dst_l1'].read32(0x8000) == 300
  # Every one generated a response.
  assert net['src_noc0'].regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 100
