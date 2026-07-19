from contextlib import ExitStack
from dataclasses import dataclass
from enum import IntEnum
from math import prod
from typing import Literal

from asm import Asm
from cq import Command, MAX_WRITE_SIZE, McastWrite, UnicastWrite
from fw.consts import Core, KERNEL_ROLES, KernelRole, TensixL1
from isa import R, RV32
from pcie import Allocator
from ttk.common import PARAM_BASE

RETURN_KERNEL = RV32().jalr(R.ZERO, R.RA).to_bytes(4, "little")

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
  dram_coords: tuple[tuple[int, ...], tuple[int, ...]] | None = None

  @property
  def size(self): return prod(self.padded_shape) * self.dtype.itemsize

  @property
  def page_size(self): return 1024 * self.dtype.itemsize

  @property
  def pages(self):
    elements = prod(self.padded_shape)
    if elements % 1024: raise ValueError("buffer padding must contain a whole number of 1024-element pages")
    return elements // 1024

  def from_numpy(self, values) -> bytes:
    import numpy as np
    values = np.asarray(values, dtype=np.float32)
    if values.shape != self.shape: raise ValueError(f"expected array shape {self.shape}, got {values.shape}")
    if len(self.shape) != len(self.padded_shape) or any(x > y for x, y in zip(self.shape, self.padded_shape)):
      raise ValueError("logical shape must fit within padded shape")
    padded = np.zeros(self.padded_shape, dtype=np.float32)
    padded[tuple(slice(0, size) for size in self.shape)] = values
    if self.dtype is DType.F32: return padded.astype("<f4", copy=False).tobytes()
    if self.dtype is DType.BF16: return (padded.view(np.uint32) >> 16).astype("<u2").tobytes()
    raise ValueError(f"unsupported NumPy conversion dtype {self.dtype}")

  def to_numpy(self, data: bytes):
    import numpy as np
    if len(data) != self.size: raise ValueError(f"buffer data requires exactly {self.size} bytes")
    if self.dtype is DType.F32: values = np.frombuffer(data, dtype="<f4")
    elif self.dtype is DType.BF16:
      values = (np.frombuffer(data, dtype="<u2").astype(np.uint32) << 16).view(np.float32)
    else: raise ValueError(f"unsupported NumPy conversion dtype {self.dtype}")
    values = values.reshape(self.padded_shape)
    return values[tuple(slice(0, size) for size in self.shape)].copy()

class Dram:
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64

  def __init__(self, harvested_dram_bank: int = 0, coords=None):
    if coords is None:
      from pcie import p100_dram_endpoint_coordinates
      coords = tuple(
        p100_dram_endpoint_coordinates(harvested_dram_bank, noc) for noc in range(2)
      )
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)
    self.coords = tuple(tuple(noc) for noc in coords)
    self.banks = len(self.coords[0])

  def buffer(self, name: str, dtype: DType, shape: tuple[int, ...],
             padded_shape: tuple[int, ...]):
    buffer = Buffer(name, 0, "device", dtype, shape, padded_shape, self.coords)
    if buffer.page_size % self.ALIGNMENT: raise ValueError("DRAM pages must be 64-byte aligned")
    pages_per_bank = (buffer.pages + self.banks - 1) // self.banks
    addr = self.allocator.alloc(pages_per_bank * buffer.page_size, name=name)
    return Buffer(name, addr, "device", dtype, shape, padded_shape, self.coords)

@dataclass(frozen=True)
class CBConfig:
  index: int
  dtype: DType
  depth: int
  addr: int

  @property
  def page_size(self): return 1024 * self.dtype.itemsize

  @property
  def size(self): return self.depth * self.page_size

  @property
  def limit(self): return self.addr + self.size

class Program:
  def __init__(self, cores: tuple[Core, ...] | list[Core], buffers: tuple[Buffer, ...] | list[Buffer] = ()):
    self._cores = tuple(cores)
    if not self._cores: raise ValueError("program requires at least one core")
    if len(set(self._cores)) != len(self._cores): raise ValueError("program cores must be unique")
    buffers = tuple(buffers)
    if len(buffers) > TensixL1.PARAM_SLOTS: raise ValueError("program parameter table is full")
    if len({buffer.name for buffer in buffers}) != len(buffers): raise ValueError("program buffer names must be unique")
    self.params = {buffer.name: buffer for buffer in buffers}
    self._param_slots = {buffer: slot for slot, buffer in enumerate(buffers)}
    self._cbs: list[CBConfig] = []
    self._l1 = Allocator(TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.SIZE, 16)
    self._runtime_args: tuple[tuple[int, ...], ...] | None = None
    self.launch: tuple[Command, ...] = ()
    self._kernels = None

    self.roles = {role: Asm(role, param_slots=self._param_slots) for role in KERNEL_ROLES}
    for role, stream in self.roles.items(): setattr(self, role, stream)
    from ttk.pack import Pack
    from ttk.sfpu import Sfpu
    from ttk.tensix import TensixPipe
    from ttk.unpack import Unpack
    self.unpack, self.fpu, self.pack = Unpack(self.trisc0), TensixPipe(self.trisc1, 1), Pack(self.trisc2)
    self.sfpu = Sfpu(self.fpu)
    self._scopes = ExitStack()
    for stream in self.roles.values(): self._scopes.enter_context(stream.scope())

  @classmethod
  def from_kernels(cls, kernels: dict[Core, dict[KernelRole, bytes]],
                   cbs: tuple[CBConfig, ...] = (), launch: tuple[Command, ...] = ()):
    program = cls.__new__(cls)
    program._cores = tuple(kernels)
    program.params, program._param_slots = {}, {}
    program._runtime_args = None
    program._cbs, program.launch = list(cbs), tuple(launch)
    program._l1 = None
    program._kernels = kernels
    program.roles = {}
    program._scopes = None
    return program

  def cb(self, dtype: DType, depth: int = 2, name: str | None = None):
    if self._kernels is not None: raise RuntimeError("program has already been lowered")
    if depth <= 0: raise ValueError("CB depth must be positive")
    if len(self._cbs) >= 32: raise ValueError("at most 32 circular buffers are supported")
    index = len(self._cbs)
    page_size = 1024 * dtype.itemsize
    addr = self._l1.alloc(depth * page_size, name=name)
    cb = CBConfig(index, dtype, depth, addr)
    self._cbs.append(cb)
    return cb

  def l1(self, size: int, alignment=4, name: str | None = None):
    """Reserve shared worker L1 storage for kernel-side coordination."""
    if self._kernels is not None: raise RuntimeError("program has already been lowered")
    if type(size) is not int or size <= 0: raise ValueError("L1 allocation size must be positive")
    if type(alignment) is not int or alignment <= 0 or alignment & (alignment - 1):
      raise ValueError("L1 alignment must be a positive power of two")
    return self._l1.alloc(size, alignment, name=name)

  def set_runtime_args(self, args_by_core):
    """Set the per-core u32 argument rows loaded with ``Asm.arg(index)``."""
    if isinstance(args_by_core, dict):
      missing = set(self.cores) - set(args_by_core)
      extra = set(args_by_core) - set(self.cores)
      if missing or extra:
        raise ValueError(f"runtime argument cores differ (missing={sorted(missing)}, extra={sorted(extra)})")
      rows = tuple(tuple(args_by_core[core]) for core in self.cores)
    else:
      rows = tuple(tuple(row) for row in args_by_core)
      if len(rows) != len(self.cores):
        raise ValueError("runtime arguments require one row per program core")
    widths = {len(row) for row in rows}
    if len(widths) != 1: raise ValueError("runtime argument rows must have equal length")
    width = widths.pop() if widths else 0
    if len(self.params) + width > TensixL1.PARAM_SLOTS:
      raise ValueError("program parameter and runtime argument table is full")
    if any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF for row in rows for value in row):
      raise ValueError("runtime arguments must be u32 integers")
    self._runtime_args = rows
    return self

  @property
  def cbs(self): return tuple(self._cbs)

  def lower(self):
    if self._kernels is None:
      self._scopes.close()
      images = {role: stream.lower() for role, stream in self.roles.items()}
      self._kernels = {core: dict(images) for core in self._cores}
    return self

  @property
  def kernels(self): self.lower(); return self._kernels

  def kernel(self, core: Core, role: KernelRole):
    image = self.kernels[core].get(role)
    return RETURN_KERNEL if image is None else image

  def param_addr(self, buffer: Buffer):
    if buffer not in self._param_slots: raise KeyError(f"{buffer.name!r} is not a program buffer")
    return PARAM_BASE + self._param_slots[buffer] * 4

  def bind(self, parameter: Buffer, buffer: Buffer | None = None):
    buffer = parameter if buffer is None else buffer
    addr = int(buffer.addr).to_bytes(4, "little")
    return UnicastWrite(self.cores, self.param_addr(parameter), (addr,) * len(self.cores))

  def kernel_commands(self):
    commands = []
    for role in KERNEL_ROLES:
      groups = {}
      for core in self.cores:
        image = self.kernel(core, role)
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
            rects = rectangles(cores)
            commands.append(McastWrite(
              rects, TensixL1.WORKER_TEXT_BASE[role] + offset, data,
            ))
    return tuple(commands)

  def commands(self, bind_initial_params: bool = True):
    commands = list(self.kernel_commands())
    params = (b"".join(int(buffer.addr).to_bytes(4, "little") for buffer in self.params.values())
              if bind_initial_params else b"")
    arg_rows = self._runtime_args
    if arg_rows is not None and arg_rows and arg_rows[0]:
      args = tuple(b"".join(value.to_bytes(4, "little") for value in row) for row in arg_rows)
      if params:
        commands.append(UnicastWrite(self.cores, PARAM_BASE,
                                     tuple(params + row for row in args)))
      else:
        commands.append(UnicastWrite(
          self.cores, PARAM_BASE + len(self.params) * 4, args,
        ))
    elif params:
      commands.append(UnicastWrite(self.cores, PARAM_BASE, (params,) * len(self.cores)))
    commands += self.launch
    return tuple(commands)

  @property
  def cores(self):
    return self._cores

def rectangles(cores):
  rows = {}
  for x, y in cores: rows.setdefault(y, []).append(x)
  active, rectangles = {}, []
  previous_y = None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      if runs and x == runs[-1][1] + 1: runs[-1] = (runs[-1][0], x)
      else: runs.append((x, x))
    if previous_y is None or y != previous_y + 1:
      rectangles.extend(active.values()); active = {}
    next_active = {}
    for run in runs:
      if run in active:
        start, _ = active[run]; next_active[run] = (start, (run[1], y))
      else: next_active[run] = ((run[0], y), (run[1], y))
    rectangles.extend(rect for run, rect in active.items() if run not in next_active)
    active, previous_y = next_active, y
  rectangles.extend(active.values())
  return tuple(rectangles)
