from contextlib import ExitStack
from dataclasses import dataclass

from asm import Asm
from fw import KERNEL_ROLES, TensixL1
from pcie import Allocator


def _u32(value, name):
  if type(value) is not int or not 0 <= value < 1 << 32:
    raise ValueError(f"{name} must fit in 32 bits")
  return value


@dataclass(frozen=True)
class KernargLayout:
  buffers: int = 0
  vals: int = 0

  def __post_init__(self):
    if type(self.buffers) is not int or self.buffers < 0:
      raise ValueError("kernarg buffer count must be a non-negative integer")
    if type(self.vals) is not int or self.vals < 0:
      raise ValueError("kernarg value count must be a non-negative integer")
    if self.size > TensixL1.PARAM_SIZE:
      raise ValueError("kernargs exceed the worker parameter table")

  @property
  def size(self): return (self.buffers + self.vals) * 4

  def addr(self, slot):
    if type(slot) is not int or not 0 <= slot < self.buffers + self.vals:
      raise IndexError("kernarg slot is out of range")
    return TensixL1.PARAM_BASE + slot * 4

  def buffer_addr(self, slot):
    if type(slot) is not int or not 0 <= slot < self.buffers:
      raise IndexError("kernarg buffer slot is out of range")
    return self.addr(slot)

  def val_addr(self, slot):
    if type(slot) is not int or not 0 <= slot < self.vals:
      raise IndexError("kernarg value slot is out of range")
    return self.addr(self.buffers + slot)

  def pack(self, bufs=(), vals=()):
    bufs, vals = tuple(bufs), tuple(vals)
    if len(bufs) != self.buffers:
      raise ValueError(f"program requires {self.buffers} buffers, got {len(bufs)}")
    if len(vals) != self.vals:
      raise ValueError(f"program requires {self.vals} values, got {len(vals)}")
    addresses = tuple(_u32(buf.addr, f"buffer {i} address") for i, buf in enumerate(bufs))
    words = addresses + tuple(_u32(val, f"value {i}") for i, val in enumerate(vals))
    return b"".join(word.to_bytes(4, "little") for word in words)


@dataclass(eq=False)
class Program:
  cores: tuple
  images: dict
  kernargs: KernargLayout = KernargLayout()
  l1_data: tuple[tuple[int, bytes], ...] = ()


class Kernel:
  def __init__(self, cores):
    self.cores = tuple(cores)
    self.roles = {role: Asm(role) for role in KERNEL_ROLES}
    for role, stream in self.roles.items(): setattr(self, role, stream)
    self._scopes = ExitStack()
    for stream in self.roles.values(): self._scopes.enter_context(stream.scope())
    self._l1 = Allocator(
      TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.DATA_BUFFER_SPACE_END, 16,
    )
    self._constants = {}
    self._built = False

  def l1(self, size: int, alignment=4): return self._l1.alloc(size, alignment)

  def constant(self, data: bytes, alignment=16):
    data = bytes(data)
    if not data: raise ValueError("L1 constant cannot be empty")
    key = data, alignment
    if key not in self._constants:
      self._constants[key] = self._l1.alloc(len(data), alignment)
    return self._constants[key]

  def build(self, kernargs=KernargLayout()):
    if self._built: raise RuntimeError("kernel has already been built")
    if not isinstance(kernargs, KernargLayout):
      raise TypeError("kernargs must be a KernargLayout")
    self._scopes.close()
    images = {role: stream.lower() for role, stream in self.roles.items()}
    self._built = True
    return Program(
      self.cores,
      {core: dict(images) for core in self.cores},
      kernargs,
      tuple((address, data) for (data, _), address in self._constants.items()),
    )
