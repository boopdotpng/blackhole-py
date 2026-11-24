from enum import Enum
from typing import NamedTuple


class Space(Enum):
  THREAD = "ThreadConfig"  # per Tensix thread, written whole-word with SETC16
  CONFIG = "Config"        # shared, written with RMWCIB (masked byte), WRCFG, or MMIO at TENSIX_CFG


class Field(NamedTuple):
  space: Space
  word: int
  shift: int
  width: int
  name: str

  @property
  def mask(self): return ((1 << self.width) - 1) << self.shift

  def __call__(self, value) -> "Set":
    value = int(value)
    if not 0 <= value < 1 << self.width:
      raise ValueError(f"{self.name}: {value} does not fit {self.width} bits")
    if self.width > 32:
      raise ValueError(f"{self.name} spans several words; write its parts")
    return Set(self, value)


class Set(NamedTuple):
  field: Field
  value: int

  @property
  def bits(self): return self.value << self.field.shift


def words(sets) -> dict[int, int]:
  out = {}
  for s in sets:
    out[s.field.word] = out.get(s.field.word, 0) | s.bits
  return out
