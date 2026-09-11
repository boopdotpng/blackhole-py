"""Independent finite E4M3FN reference values (bias 7; maximum 448)."""
import math
from struct import pack


def decode(code):
  sign = -1 if code & 128 else 1
  exponent, mantissa = (code >> 3) & 15, code & 7
  if exponent == 15 and mantissa == 7:
    return math.nan
  return sign * (mantissa * 2**-9 if exponent == 0 else (1 + mantissa / 8) * 2**(exponent - 7))


def encode(values):
  """Finite, saturating nearest conversion; ties select an even mantissa."""
  levels = tuple(decode(code) for code in range(127))
  result = []
  for value in values:
    if not math.isfinite(value):
      raise ValueError('finite FP8 test inputs required')
    code = min(range(127), key=lambda c: (abs(levels[c] - abs(value)), c & 1))
    result.append(code | (128 if math.copysign(1, value) < 0 else 0))
  return bytes(result)


def normal_tile(seed=0):
  # Every finite normal code, both signs, shuffled across face boundaries.
  codes = tuple(range(8, 127)) + tuple(range(136, 255))
  return bytes(codes[(i * 37 + seed) % len(codes)] for i in range(1024))


def as_f32(payload):
  return pack(f'<{len(payload)}f', *(decode(code) for code in payload))
