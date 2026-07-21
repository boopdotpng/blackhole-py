from enum import IntEnum


class DType(IntEnum):
  F32 = 0
  BF16 = 5

  @property
  def itemsize(self): return 4 if self is DType.F32 else 2


class Dst:
  def __init__(self, fp32=False):
    self.fp32 = bool(fp32)

  @property
  def capacity(self): return 8 if self.fp32 else 16

  def require_fp32(self):
    self.fp32 = True
    return self

  def check(self, tile):
    if type(tile) is not int or not 0 <= tile < self.capacity:
      raise ValueError(f"Dst tile must be in range 0..{self.capacity - 1}")
    return tile

  def row_base(self, tile): return self.check(tile) * 64
