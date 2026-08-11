from contextlib import ExitStack
from dataclasses import dataclass
from enum import IntEnum
from math import prod
import numpy as np
from asm import Asm
from cq import MAX_WRITE_SIZE, McastWrite, UnicastWrite
from fw import Firmware, KERNEL_ROLES, TensixL1
from isa import R, RV32
from pcie import Allocator, P100_DRAM_ENDPOINTS, P100_WORKER_CORES


class DType(IntEnum):
  F32 = 0
  BF16 = 5
  U32 = 6

  @property
  def itemsize(self): return 2 if self is DType.BF16 else 4

PARAM_BASE = TensixL1.PARAM_BASE
RETURN_KERNEL = {role: RV32().jal(R.ZERO, Firmware.TEXT[role][0] - TensixL1.WORKER_TEXT_BASE[role]).to_bytes(4, "little") for role in KERNEL_ROLES}

@dataclass(frozen=True, eq=False)
class Buffer:
  name: str
  addr: int
  dtype: DType
  shape: tuple[int, ...]
  banks: int
  page_size: int
  dram_endpoints: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = ()

  def __post_init__(self):
    shape = tuple(self.shape)
    if not shape or any(type(dim) is not int or dim <= 0 for dim in shape):
      raise ValueError("buffer shape must contain positive integer dimensions")
    if not isinstance(self.dtype, DType):
      raise TypeError("buffer dtype must be a DType")
    if type(self.banks) is not int or self.banks < 1:
      raise ValueError("buffer requires at least one DRAM bank")
    if type(self.page_size) is not int or not 0 < self.page_size <= 16 * 1024:
      raise ValueError("buffer page size must be in [1, 16 KiB]")
    if len(self.dram_endpoints) != self.banks:
      raise ValueError("buffer DRAM endpoints must match its bank count")
    object.__setattr__(self, "shape", shape)

  @property
  def size(self): return prod(self.shape) * self.dtype.itemsize

  @property
  def page_count(self): return (self.size + self.page_size - 1) // self.page_size

  def from_numpy(self, values) -> bytes:
    if self.dtype is DType.U32:
      return np.asarray(values, dtype="<u4").reshape(self.shape).tobytes()
    values = np.asarray(values, dtype=np.float32).reshape(self.shape)
    if self.dtype is DType.F32: return values.astype("<f4", copy=False).tobytes()
    return (values.view(np.uint32) >> 16).astype("<u2").tobytes()

  def from_safetensor(self, name,
                      path="weights/model.safetensors") -> bytes:
    from st import load

    info, data = load(name, path)
    expected_dtype = {
      DType.BF16: "BF16",
      DType.F32: "F32",
      DType.U32: "U32",
    }[self.dtype]
    if info.dtype != expected_dtype:
      raise ValueError(
        f"safetensor {name!r} has dtype {info.dtype}, "
        f"but buffer {self.name!r} requires {expected_dtype}",
      )
    if info.shape != self.shape:
      raise ValueError(
        f"safetensor {name!r} has shape {info.shape}, "
        f"but buffer {self.name!r} requires {self.shape}",
      )
    if len(data) != prod(self.shape) * self.dtype.itemsize:
      raise ValueError(f"safetensor {name!r} has an invalid byte length")
    return data

  def to_numpy(self, data: bytes):
    if len(data) != self.size:
      raise ValueError(
        f"buffer {self.name!r} requires exactly {self.size} bytes, got {len(data)}",
      )
    if self.dtype is DType.U32:
      return np.frombuffer(data, dtype="<u4").reshape(self.shape).copy()
    if self.dtype is DType.F32: values = np.frombuffer(data, dtype="<f4")
    else:
      values = (
        np.frombuffer(data, dtype="<u2").astype(np.uint32) << 16
      ).view(np.float32)
    return values.reshape(self.shape).copy()

@dataclass(frozen=True, eq=False)
class Const:
  name: str
  value: int | tuple[int, ...]


Param = Buffer | Const


def _param_word(value):
  return value.addr if isinstance(value, Buffer) else value


class Dram:
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64
  BANKS = 7

  def __init__(self, banks=BANKS, cores=P100_WORKER_CORES,
               dram_endpoints=None):
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)
    self.banks = banks
    self.cores = tuple(cores)
    self.dram_endpoints = tuple(
      P100_DRAM_ENDPOINTS[:banks]
      if dram_endpoints is None else dram_endpoints
    )
    if len(self.dram_endpoints) != banks:
      raise ValueError(
        f"DRAM has {banks} banks but {len(self.dram_endpoints)} endpoints",
      )

  def buffer(self, name: str, dtype: DType, shape: tuple[int, ...],
             *, page_size=4096, banks=None) -> Buffer:
    banks = self.banks if banks is None else banks
    if not 0 < banks <= self.banks:
      raise ValueError("buffer bank count must be within the device bank count")
    endpoints = self.dram_endpoints[:banks]
    buffer = Buffer(name, 0, dtype, shape, banks, page_size, endpoints)
    rows_per_bank = (buffer.page_count + banks - 1) // banks
    addr = self.allocator.alloc(rows_per_bank * page_size)
    return Buffer(name, addr, dtype, shape, banks, page_size, endpoints)


class Program:
  def __init__(self, cores, *parameters, images=None):
    self._cores = tuple(cores)
    params = tuple(parameters)
    if len(params) > TensixL1.PARAM_SLOTS:
      raise ValueError("program parameter table is full")
    self.params = {param.name: param for param in params}
    self._param_slots = {param: slot for slot, param in enumerate(params)}
    # Program-scoped scratch and constants consume the non-persistent arena.
    self._l1 = Allocator(
      TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.DATA_BUFFER_SPACE_END, 16,
    )
    self._l1_constants = {}
    self.launch = ()
    self._static = None
    self._kernels = None if images is None else {
      core: dict(images) for core in self._cores
    }

    if images is not None: return
    self.roles = {
      role: Asm(role, param_slots=self._param_slots)
      for role in KERNEL_ROLES
    }
    for role, stream in self.roles.items(): setattr(self, role, stream)
    self._scopes = ExitStack()
    for stream in self.roles.values(): self._scopes.enter_context(stream.scope())

  def l1(self, size: int, alignment=4):
    return self._l1.alloc(size, alignment)

  def l1_constant(self, data: bytes, alignment=16):
    data = bytes(data)
    if not data: raise ValueError("L1 constant cannot be empty")
    key = data, alignment
    if key not in self._l1_constants:
      self._l1_constants[key] = self._l1.alloc(len(data), alignment)
    return self._l1_constants[key]

  @property
  def cores(self): return self._cores

  def lower(self):
    if self._kernels is None:
      self._scopes.close()
      images = {role: stream.lower() for role, stream in self.roles.items()}
      self._kernels = {core: dict(images) for core in self.cores}
    return self._kernels

  def param(self, name):
    return self.params[name]

  def param_addr(self, param):
    return PARAM_BASE + self._param_slots[param] * 4

  def arg_data(self, values=None):
    values = {} if values is None else dict(values)
    resolved = {}
    for key, value in values.items():
      param = self.params[key] if isinstance(key, str) else key
      resolved[param] = value
    words = []
    for param in self.params.values():
      value = resolved.get(param, param if isinstance(param, Buffer) else param.value)
      value = _param_word(value)
      if type(value) is not int or not 0 <= value < 1 << 32:
        raise ValueError(f"parameter {param.name!r} must be a 32-bit integer or Buffer")
      words.append(value)
    return b"".join(word.to_bytes(4, "little") for word in words)

  def static_commands(self):
    if self._static is not None: return self._static
    commands, kernels = [], self.lower()
    for role in KERNEL_ROLES:
      groups = {}
      for core in self.cores:
        image = kernels[core].get(role, RETURN_KERNEL[role])
        if len(image) > TensixL1.WORKER_TEXT_SIZE[role]:
          raise ValueError(f"{role} kernel exceeds its text partition")
        groups.setdefault(image, []).append(core)
      for image, cores in groups.items():
        for offset in range(0, len(image), MAX_WRITE_SIZE):
          data = image[offset:offset + MAX_WRITE_SIZE]
          if len(cores) == 1:
            commands.append(UnicastWrite(
              tuple(cores), TensixL1.WORKER_TEXT_BASE[role] + offset, (data,),
            ))
          else:
            commands.append(McastWrite(
              rectangles(cores), TensixL1.WORKER_TEXT_BASE[role] + offset, data,
            ))
    for (data, _), address in self._l1_constants.items():
      for offset in range(0, len(data), MAX_WRITE_SIZE):
        chunk = data[offset:offset + MAX_WRITE_SIZE]
        if len(self.cores) == 1:
          commands.append(UnicastWrite(
            self.cores, address + offset, (chunk,),
          ))
        else:
          commands.append(McastWrite(
            rectangles(self.cores), address + offset, chunk,
          ))
    self._static = tuple(commands)
    return self._static

  def runtime_commands(self, params=None):
    return self.launch

  def commands(self, params=None):
    return (*self.static_commands(), *self.runtime_commands(params))


def rectangles(cores):
  rows = {}
  for x, y in cores: rows.setdefault(y, []).append(x)
  active, result, previous_y = {}, [], None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      if runs and x == runs[-1][1] + 1: runs[-1] = (runs[-1][0], x)
      else: runs.append((x, x))
    if previous_y is None or y != previous_y + 1:
      result.extend(active.values()); active = {}
    following = {}
    for run in runs:
      if run in active:
        following[run] = (active[run][0], (run[1], y))
      else:
        following[run] = ((run[0], y), (run[1], y))
    result.extend(rect for run, rect in active.items() if run not in following)
    active, previous_y = following, y
  result.extend(active.values())
  return tuple(result)
