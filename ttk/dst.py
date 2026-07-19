from dataclasses import dataclass


@dataclass(frozen=True)
class DstTile:
  index: int
  fp32: bool = False
  owner: int = 0

  def __post_init__(self):
    capacity = 8 if self.fp32 else 16
    if type(self.index) is not int or not 0 <= self.index < capacity:
      raise ValueError(f"Dst tile index must be in range 0..{capacity - 1}")

  @property
  def row_base(self): return self.index * 64


class Dst:
  def __init__(self, fp32=False):
    self.fp32, self._owner = bool(fp32), id(self)

  @property
  def capacity(self): return 8 if self.fp32 else 16

  def tile(self, index=0): return DstTile(index, self.fp32, self._owner)

  def check(self, tile):
    if not isinstance(tile, DstTile) or tile.owner != self._owner or tile.fp32 != self.fp32:
      raise ValueError("Dst tile belongs to another Program or Dst mode")
    return tile
