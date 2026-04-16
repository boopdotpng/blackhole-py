class SrcBank:
  __slots__ = ('rows', 'allowed_client')

  def __init__(self):
    # 64 rows x 16 cols, stored as 32-bit ints (19-bit values)
    self.rows = [[0] * 16 for _ in range(64)]
    self.allowed_client = "unpackers"  # "unpackers" or "matrix_unit"


class SrcRegFile:
  def __init__(self, name="Src"):
    self.name = name
    self.banks = [SrcBank(), SrcBank()]
    self.fpu_bank = 0       # which bank the Matrix Unit reads from
    self.unpack_bank = 0    # which bank the unpacker writes to

  def flip_to_fpu(self):
    self.banks[self.unpack_bank].allowed_client = "matrix_unit"
    self.unpack_bank ^= 1

  def release_from_fpu(self):
    self.banks[self.fpu_bank].allowed_client = "unpackers"
    self.fpu_bank ^= 1


class DestRegFile:
  ROWS = 1024
  COLS = 16

  def __init__(self):
    self.bits = [[0] * self.COLS for _ in range(self.ROWS)]
    self.valid = [False] * self.ROWS

  def clear_valid(self, row):
    if 0 <= row < self.ROWS: self.valid[row] = False

  def clear_range(self, start, count):
    for r in range(start, min(start + count, self.ROWS)):
      self.valid[r] = False

  def clear_half(self, which):
    base = 512 if which else 0
    for r in range(base, base + 512):
      self.valid[r] = False

  def clear_all(self):
    self.valid = [False] * self.ROWS
