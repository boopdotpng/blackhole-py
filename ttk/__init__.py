from enum import IntEnum


class DType(IntEnum):
  F32 = 0
  BF16 = 5

  @property
  def itemsize(self): return 4 if self is DType.F32 else 2
