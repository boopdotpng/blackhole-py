from dataclasses import dataclass
from enum import IntEnum
from math import prod
from typing import Callable, Literal

from asm import Core, KERNEL_ROLES, KernelBuilder, KernelRole
from cq import MAX_WRITE_SIZE, McastWrite, UnicastWrite
from fw.consts import TensixL1
from pcie import BumpAllocator
from ttk.common import PARAM_BASE

class DType(IntEnum):
  F32 = 0
  BF16 = 5

  @property
  def itemsize(self): return 4 if self is DType.F32 else 2

@dataclass(frozen=True)
class Buffer:
  name: str
  addr: int
  loc: Literal["host", "device"]
  dtype: DType
  shape: tuple[int, ...]
  padded_shape: tuple[int, ...]
  layout: Literal["row_major", "tile"] = "row_major"

  @property
  def tiles(self): return prod(self.padded_shape) // 1024

  @property
  def tile_size(self): return 1024 * self.dtype.itemsize

  @property
  def page_size(self):
    return self.tile_size if self.layout == "tile" else self.padded_shape[-1] * self.dtype.itemsize

  @property
  def pages(self):
    return self.tiles if self.layout == "tile" else prod(self.padded_shape[:-1])

  @property
  def size(self): return self.pages * self.page_size

@dataclass(frozen=True, eq=False)
class Param:
  """A replaceable, fixed-shape DRAM buffer used by compiled kernels."""

  name: str
  initial: Buffer

  def __post_init__(self):
    if not self.name: raise ValueError("parameter name cannot be empty")
    if self.initial.loc != "device": raise ValueError("parameter buffer must be in DRAM")

  def validate(self, buffer: Buffer):
    """Require a replacement buffer with the captured storage contract."""
    if buffer.loc != "device": raise ValueError("bound parameter buffer must be in DRAM")
    if buffer.dtype != self.initial.dtype: raise ValueError(f"parameter {self.name!r} dtype changed")
    if buffer.shape != self.initial.shape: raise ValueError(f"parameter {self.name!r} shape changed")
    if buffer.padded_shape != self.initial.padded_shape: raise ValueError(f"parameter {self.name!r} layout changed")
    if buffer.layout != self.initial.layout: raise ValueError(f"parameter {self.name!r} memory layout changed")
    return buffer

class DramAllocator:
  BANKS = 7
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64

  def __init__(self):
    self.allocator = BumpAllocator(self.END - self.START, self.START)

  def alloc(self, name: str, dtype: DType, shape: tuple[int, ...],
            padded_shape: tuple[int, ...], *, layout="row_major"):
    if layout not in ("row_major", "tile"): raise ValueError("unknown buffer layout")
    if not shape or len(shape) != len(padded_shape): raise ValueError("shape rank mismatch")
    if any(dim <= 0 for dim in (*shape, *padded_shape)): raise ValueError("buffer dimensions must be positive")
    if any(actual > padded for actual, padded in zip(shape, padded_shape)):
      raise ValueError("padded shape cannot be smaller than shape")
    buffer = Buffer(name, 0, "device", dtype, shape, padded_shape, layout)
    if buffer.page_size % self.ALIGNMENT: raise ValueError("DRAM pages must be 64-byte aligned")
    pages_per_bank = (buffer.pages + self.BANKS - 1) // self.BANKS
    addr = self.allocator.alloc(pages_per_bank * buffer.page_size, self.ALIGNMENT)
    return Buffer(name, addr, "device", dtype, shape, padded_shape, layout)

@dataclass(frozen=True)
class CBConfig:
  dtype: DType
  pages: int
  addr: int

  @property
  def page_size(self): return 1024 * self.dtype.itemsize

  @property
  def size(self): return self.pages * self.page_size

  @property
  def end(self): return self.addr + self.size

@dataclass(frozen=True)
class Program:
  """Per-core kernel bytes, DRAM buffer parameters, and CB configuration."""

  kernels: dict[Core, dict[KernelRole, bytes]]
  params: tuple[Param, ...]
  cbs: tuple[CBConfig, ...]

  def kernel(self, core: Core, role: KernelRole):
    """Return one core and role's assembled kernel bytes."""
    return self.kernels[core][role]

  def param_addr(self, param: Param):
    """Return the fixed per-core L1 word containing this parameter's DRAM address."""
    try: slot = self.params.index(param)
    except ValueError: raise ValueError(f"parameter {param.name!r} does not belong to this program") from None
    return PARAM_BASE + slot * 4

  def param(self, name: str):
    """Return a declared parameter by name."""
    matches = [param for param in self.params if param.name == name]
    if not matches: raise KeyError(name)
    return matches[0]

  def bind(self, param: Param, buffer: Buffer | None = None):
    """Create the CQ write that binds a DRAM buffer to its fixed parameter word."""
    buffer = param.initial if buffer is None else param.validate(buffer)
    addr = int(buffer.addr).to_bytes(4, "little")
    return UnicastWrite(self.cores, self.param_addr(param), (addr,) * len(self.cores))

  def kernel_commands(self):
    """Return CQ writes that place worker kernels at their fixed L1 addresses."""
    commands = []
    for role in KERNEL_ROLES:
      groups = {}
      for core in self.cores:
        image = self.kernels[core][role]
        if image:
          if len(image) > TensixL1.WORKER_TEXT_SIZE:
            raise ValueError(f"{role} kernel exceeds its fixed text partition")
          groups.setdefault(image, []).append(core)
      for image, cores in groups.items():
        size = len(image)
        for offset in range(0, size, MAX_WRITE_SIZE):
          data = image[offset:offset + MAX_WRITE_SIZE]
          if len(cores) == 1:
            commands.append(UnicastWrite(
              tuple(cores), TensixL1.WORKER_TEXT_BASE[role] + offset, (data,),
            ))
          else:
            rects = _rectangles(cores)
            commands.append(McastWrite(
              rects, TensixL1.WORKER_TEXT_BASE[role] + offset, data,
              tuple(sum(x0 <= x <= x1 and y0 <= y <= y1 for x, y in cores)
                    for (x0, y0), (x1, y1) in rects),
            ))
    return tuple(commands)

  def commands(self, *, bind_initial_params: bool = True):
    """Lower one complete fixed-layout program into CQ write commands."""
    commands = list(self.kernel_commands())
    if bind_initial_params:
      commands.extend(self.bind(param) for param in self.params)
    return tuple(commands)

  @property
  def cores(self):
    """Return cores in their stable lowering order."""
    return tuple(self.kernels)

KernelFn = Callable[[KernelBuilder], None]


def _rectangles(cores):
  """Form rectangles while allowing NoC multicast to cross absent columns."""
  rows = {}
  for x, y in cores: rows.setdefault(y, []).append(x)
  columns = sorted({x for xs in rows.values() for x in xs})
  rank = {x: i for i, x in enumerate(columns)}
  active, rectangles = {}, []
  previous_y = None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      column = rank[x]
      if runs and column == runs[-1][1] + 1: runs[-1] = (runs[-1][0], column)
      else: runs.append((column, column))
    if previous_y is None or y != previous_y + 1:
      rectangles.extend(active.values()); active = {}
    next_active = {}
    for run in runs:
      if run in active:
        start, _ = active[run]; next_active[run] = (start, (columns[run[1]], y))
      else: next_active[run] = ((columns[run[0]], y), (columns[run[1]], y))
    rectangles.extend(rect for run, rect in active.items() if run not in next_active)
    active, previous_y = next_active, y
  rectangles.extend(active.values())
  return tuple(rectangles)

class KernelBundle:
  """Compile five kernel functions for every core with declared parameters."""

  def __init__(
    self, cores: tuple[Core, ...] | list[Core], params: tuple[Param, ...] | list[Param] = (), *,
    brisc: KernelFn | None = None, ncrisc: KernelFn | None = None,
    trisc0: KernelFn | None = None, trisc1: KernelFn | None = None, trisc2: KernelFn | None = None,
  ):
    self.cores = tuple(cores)
    self.params = tuple(params)
    if not self.cores: raise ValueError("kernel bundle requires at least one core")
    if len(set(self.cores)) != len(self.cores): raise ValueError("kernel bundle cores must be unique")
    if len(set(self.params)) != len(self.params): raise ValueError("kernel bundle parameters must be unique")
    if len({param.name for param in self.params}) != len(self.params): raise ValueError("parameter names must be unique")
    if len(self.params) > TensixL1.PARAM_SLOTS: raise ValueError("kernel bundle parameter table is full")
    self._kernels = {"brisc": brisc, "ncrisc": ncrisc, "trisc0": trisc0, "trisc1": trisc1, "trisc2": trisc2}
    self._cbs: list[CBConfig] = []
    self._lowered = False

  def cb(self, dtype: DType, pages: int, addr: int):
    if self._lowered: raise RuntimeError("kernel bundle has already been lowered")
    if pages <= 0: raise ValueError("CB pages must be positive")
    cb = CBConfig(dtype, pages, addr)
    if cb.addr < TensixL1.DATA_BUFFER_SPACE_BASE or cb.end > TensixL1.SIZE:
      raise ValueError("CB must fit in the L1 data-buffer region")
    self._cbs.append(cb)
    return cb

  def lower(self):
    """Assemble every core and role pair with a common parameter-slot layout."""
    if self._lowered: raise RuntimeError("kernel bundle has already been lowered")
    kernels = {}
    param_slots = {param: slot for slot, param in enumerate(self.params)}
    for core in self.cores:
      kernels[core] = {}
      for role in KERNEL_ROLES:
        builder = KernelBuilder(role, core, param_slots)
        if (fn := self._kernels[role]) is not None:
          with builder.scope(): fn(builder)
        kernels[core][role] = builder.lower()

    self._lowered = True
    return Program(kernels, self.params, tuple(self._cbs))
