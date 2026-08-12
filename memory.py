from dataclasses import dataclass

from pcie import Allocator


@dataclass(frozen=True, eq=False)
class Buffer:
  name: str
  addr: int
  size: int


class Dram:
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64
  PAGE_SIZE = 4096

  def __init__(self, banks):
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)
    self.banks = banks

  def buffer(self, name: str, size: int) -> Buffer:
    pages = (size + self.PAGE_SIZE - 1) // self.PAGE_SIZE
    rows_per_bank = (pages + self.banks - 1) // self.banks
    addr = self.allocator.alloc(rows_per_bank * self.PAGE_SIZE)
    return Buffer(name, addr, size)
