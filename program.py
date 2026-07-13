from dataclasses import dataclass
from enum import IntEnum
from math import prod
from typing import Callable, Literal

from asm import Core, KERNEL_ROLES, KernelBuilder, KernelRole
from cq import MAX_WRITE_SIZE, McastWrite, UnicastWrite
from fw.consts import TensixL1
from pcie import Allocator
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
  name: str
  initial: Buffer

class Dram:
  BANKS = 7
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64

  def __init__(self):
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)

  def buffer(self, name: str, dtype: DType, shape: tuple[int, ...],
             padded_shape: tuple[int, ...], *, layout="row_major"):
    buffer = Buffer(name, 0, "device", dtype, shape, padded_shape, layout)
    if buffer.page_size % self.ALIGNMENT: raise ValueError("DRAM pages must be 64-byte aligned")
    pages_per_bank = (buffer.pages + self.BANKS - 1) // self.BANKS
    addr = self.allocator.alloc(pages_per_bank * buffer.page_size, name=name)
    return Buffer(name, addr, "device", dtype, shape, padded_shape, layout)

@dataclass(frozen=True)
class CBConfig:
  dtype: DType
  pages: int
  addr: int
  flag_addr: int | None = None

  @property
  def page_size(self): return 1024 * self.dtype.itemsize

@dataclass(frozen=True)
class BarrierConfig:
  parties: int
  addr: int
  @property
  def size(self): return self.parties * 4

@dataclass(frozen=True)
class Program:
  kernels: dict[Core, dict[KernelRole, bytes]]
  params: dict[str, Param]
  cbs: tuple[CBConfig, ...]
  barriers: tuple[BarrierConfig, ...] = ()

  def kernel(self, core: Core, role: KernelRole):
    return self.kernels[core][role]

  def param_addr(self, param: Param):
    slot = tuple(self.params).index(param.name)
    return PARAM_BASE + slot * 4

  def bind(self, param: Param, buffer: Buffer | None = None):
    buffer = param.initial if buffer is None else buffer
    addr = int(buffer.addr).to_bytes(4, "little")
    return UnicastWrite(self.cores, self.param_addr(param), (addr,) * len(self.cores))

  def kernel_commands(self):
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
    commands = list(self.kernel_commands())
    if bind_initial_params and self.params:
      table = b"".join(int(x.initial.addr).to_bytes(4, "little") for x in self.params.values())
      commands.append(UnicastWrite(self.cores, PARAM_BASE, (table,) * len(self.cores)))
    resets = [(x.flag_addr, 4) for x in self.cbs if x.flag_addr is not None] + [(x.addr, x.size) for x in self.barriers]
    commands += [UnicastWrite(self.cores, addr, (bytes(size),) * len(self.cores)) for addr, size in resets]
    return tuple(commands)

  @property
  def cores(self):
    return tuple(self.kernels)

KernelFn = Callable[[KernelBuilder], None]

def _rectangles(cores):
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
  def __init__(
    self, cores: tuple[Core, ...] | list[Core], params: tuple[Param, ...] | list[Param] = (), *,
    brisc: KernelFn | None = None, ncrisc: KernelFn | None = None,
    trisc0: KernelFn | None = None, trisc1: KernelFn | None = None, trisc2: KernelFn | None = None,
  ):
    self.cores = tuple(cores)
    self.params = tuple(params)
    if len(self.params) > TensixL1.PARAM_SLOTS: raise ValueError("kernel bundle parameter table is full")
    self._kernels = {"brisc": brisc, "ncrisc": ncrisc, "trisc0": trisc0, "trisc1": trisc1, "trisc2": trisc2}
    self._cbs: list[CBConfig] = []; self._barriers: list[BarrierConfig] = []

  def cb(self, dtype: DType, pages: int, addr: int, *, flag_addr: int | None = None):
    if pages <= 0: raise ValueError("CB pages must be positive")
    cb = CBConfig(dtype, pages, addr, flag_addr)
    if cb.addr < TensixL1.DATA_BUFFER_SPACE_BASE or cb.addr + cb.pages * cb.page_size > TensixL1.SIZE:
      raise ValueError("CB must fit in the L1 data-buffer region")
    self._cbs.append(cb)
    return cb

  def barrier(self, parties: int, addr: int):
    barrier = BarrierConfig(parties, addr)
    self._barriers.append(barrier); return barrier

  def lower(self):
    kernels = {}
    param_slots = {param: slot for slot, param in enumerate(self.params)}
    for core in self.cores:
      kernels[core] = {}
      for role in KERNEL_ROLES:
        builder = KernelBuilder(role, core, param_slots)
        if (fn := self._kernels[role]) is not None:
          with builder.scope(): fn(builder)
        kernels[core][role] = builder.lower()

    return Program(kernels, {param.name: param for param in self.params}, tuple(self._cbs), tuple(self._barriers))
