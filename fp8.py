"""Finite E4M3 conversion, saturating round-to-nearest-even (no torch dependency)."""
import numpy as np


def decode(bits):
  bits = np.asarray(bits, dtype=np.uint8)
  exp = (bits >> 3) & 15
  mantissa = bits & 7
  magnitude = np.where(exp == 0, mantissa.astype(np.float32) * 2**-9,
                       (1 + mantissa.astype(np.float32) / 8) * np.exp2(exp.astype(np.float32) - 7))
  magnitude = np.where((exp == 15) & (mantissa == 7), np.nan, magnitude)
  return np.copysign(magnitude, np.where(bits & 128, -1., 1.)).astype(np.float32)


_POSITIVE = decode(np.arange(127, dtype=np.uint8))


def encode(values):
  values = np.asarray(values, dtype=np.float32)
  if not np.isfinite(values).all(): raise ValueError('FP8 input must be finite')
  magnitude = np.minimum(np.abs(values), 448.)
  hi = np.searchsorted(_POSITIVE, magnitude).clip(0, 126)
  lo = np.maximum(hi - 1, 0)
  dl, dh = magnitude - _POSITIVE[lo], _POSITIVE[hi] - magnitude
  codes = np.where((dl < dh) | ((dl == dh) & ((lo & 1) == 0)), lo, hi)
  result = codes.astype(np.uint8)
  sign = np.signbit(values).astype(np.uint8)
  sign <<= 7
  np.bitwise_or(result, sign, out=result)
  return result


def encode_hardware(values):
  """E4M3 RNE with subnormals flushed for Blackhole native operands."""
  bits = encode(values)
  bits[(bits & 127) < 8] &= np.uint8(128)
  return bits

