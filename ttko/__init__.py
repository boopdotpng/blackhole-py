from enum import IntEnum


class DType(IntEnum):
  F32 = 0
  F16 = 1
  FP8 = 26  # E4M3: Lf8 encoding (10) plus software format flag.
  BF16 = 5
  U32 = 6

  @property
  def itemsize(self): return 1 if self.is_fp8 else 2 if self in (DType.BF16, DType.F16) else 4

  @property
  def tile_size(self): return 1024 * self.itemsize

  @property
  def hw_format(self): return int(self) & 15

  @property
  def register_format(self): return DType.F16 if self.is_fp8 else self

  @property
  def is_fp8(self): return self is DType.FP8


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
