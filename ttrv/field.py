"""A configuration register field, and a value to write to it.

  cfg.THCON_SEC0_REG2_Out_data_format               Field(space=CONFIG, word=72, shift=0, width=4, name=...)
  cfg.THCON_SEC0_REG2_Out_data_format(fmt)          Set(field, fmt): a pending write, checked to fit

Writes are emitted explicitly (ops.rmw / ops.setc16), never by assignment: config writes are instructions whose order
matters, so they stay visible as calls."""

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
  """{word: value} with every Set placed. Bits of a word that no Set names are zero."""
  out = {}
  for s in sets:
    out[s.field.word] = out.get(s.field.word, 0) | s.bits
  return out
