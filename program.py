from contextlib import ExitStack
from dataclasses import dataclass
from enum import IntEnum
from math import prod

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
  dtype: DType
  shape: tuple[int, ...]
  padded_shape: tuple[int, ...]
  dram_endpoints: tuple[tuple[Core, Core], ...] | None = None

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
    padded = np.zeros(self.padded_shape, dtype=np.float32)
    padded[tuple(slice(0, size) for size in self.shape)] = values
    if self.dtype is DType.F32: return padded.astype("<f4", copy=False).tobytes()
    return (padded.view(np.uint32) >> 16).astype("<u2").tobytes()

  def to_numpy(self, data: bytes):
    import numpy as np
    if self.dtype is DType.F32: values = np.frombuffer(data, dtype="<f4")
    else: values = (np.frombuffer(data, dtype="<u2").astype(np.uint32) << 16).view(np.float32)
    values = values.reshape(self.padded_shape)
    return values[tuple(slice(0, size) for size in self.shape)].copy()

class Dram:
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64

  def __init__(self, endpoints=None):
    if endpoints is None:
      from pcie import P100_DRAM_ENDPOINTS
      endpoints = P100_DRAM_ENDPOINTS
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)
    self.endpoints = tuple(endpoints)
    self.banks = len(self.endpoints)

  def buffer(self, name: str, dtype: DType, shape: tuple[int, ...],
             padded_shape: tuple[int, ...]):
    buffer = Buffer(name, 0, dtype, shape, padded_shape, self.endpoints)
    pages_per_bank = (buffer.pages + self.banks - 1) // self.banks
    addr = self.allocator.alloc(pages_per_bank * buffer.page_size)
    return Buffer(name, addr, dtype, shape, padded_shape, self.endpoints)

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
  def __init__(self, cores: tuple[Core, ...] | list[Core],
               buffers: tuple[Buffer, ...] | list[Buffer] = (), *, fp32_dst=False):
    self._cores = tuple(cores)
    buffers = tuple(buffers)
    self.params = {buffer.name: buffer for buffer in buffers}
    self._param_slots = {buffer: slot for slot, buffer in enumerate(buffers)}
    self._cbs: list[CBConfig] = []
    self._l1 = Allocator(TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.SIZE, 16)
    self._runtime_args: tuple[tuple[int, ...], ...] | None = None
    self.launch: tuple[Command, ...] = ()
    self._kernels = None

    self.roles = {role: Asm(role, param_slots=self._param_slots) for role in KERNEL_ROLES}
    for role, stream in self.roles.items(): setattr(self, role, stream)
    from ttk.dst import Dst
    from ttk.fpu import Fpu
    from ttk.pack import Pack
    from ttk.sfpu import Sfpu
    from ttk.unpack import Unpack
    self.dst = Dst(fp32_dst)
    self.unpack = Unpack(self.trisc0, self.dst)
    self.fpu = Fpu(self.trisc1, self.dst)
    self.sfpu = Sfpu(self.trisc1, self.dst)
    self.pack = Pack(self.trisc2, self.dst)
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
    program._kernels = kernels
    return program

  def cb(self, dtype: DType, depth: int = 2):
    index = len(self._cbs)
    page_size = 1024 * dtype.itemsize
    addr = self._l1.alloc(depth * page_size)
    cb = CBConfig(index, dtype, depth, addr)
    self._cbs.append(cb)
    return cb

  def l1(self, size: int, alignment=4):
    return self._l1.alloc(size, alignment)

  def set_runtime_args(self, args_by_core):
    if isinstance(args_by_core, dict):
      rows = tuple(tuple(args_by_core[core]) for core in self.cores)
    else:
      rows = tuple(tuple(row) for row in args_by_core)
    width = len(rows[0]) if rows else 0
    if len(self.params) + width > TensixL1.PARAM_SLOTS:
      raise ValueError("program parameter and runtime argument table is full")
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
