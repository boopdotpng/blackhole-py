from contextlib import ExitStack
from dataclasses import dataclass
from math import prod
import numpy as np
from asm import Asm
from cq import MAX_WRITE_SIZE, McastWrite, UnicastWrite
from fw.consts import Firmware, KERNEL_ROLES, TensixL1
from isa import R, RV32
from pcie import Allocator, P100_WORKER_CORES
from ttk import Dst, DType
from ttk.cb import CBRegistry
from ttk.fpu import Fpu
from ttk.ops import Ops
from ttk.pack import Pack
from ttk.sfpu import Sfpu
from ttk.unpack import Unpack

PARAM_BASE = TensixL1.PARAM_BASE
RETURN_KERNEL = {role: RV32().jal(R.ZERO, Firmware.TEXT[role][0] - TensixL1.WORKER_TEXT_BASE[role]).to_bytes(4, "little") for role in KERNEL_ROLES}

@dataclass(frozen=True, eq=False)
class Buffer:
  name: str
  addr: int
  dtype: DType
  shape: tuple[int, ...]
  axis: int | None
  cores: tuple[tuple[int, int], ...]
  banks: int
  global_address: bool = False

  def __post_init__(self):
    shape, axis, cores = tuple(self.shape), self.axis, tuple(self.cores)
    if not cores: raise ValueError("buffer requires at least one storage core")
    elements = prod(shape)
    if elements <= 0: raise ValueError("buffer shape must contain at least one element")
    if axis is not None:
      if axis < 0: axis += len(shape)
      if not 0 <= axis < len(shape): raise ValueError("shard axis is outside the buffer shape")
    object.__setattr__(self, "shape", shape)
    object.__setattr__(self, "axis", axis)

    if axis is None:
      items = (prod(shape) + 1023) // 1024
      item_elements, tiles_per_item = 1024, 1
    else:
      items = shape[axis]
      item_elements = prod((*shape[:axis], *shape[axis + 1:]))
      tiles_per_item = max(1, (item_elements + 1023) // 1024)

    cores = cores[:min(max(1, items), len(cores))]
    object.__setattr__(self, "cores", cores)
    per_core, extra = divmod(items, len(cores))
    item_counts = tuple(per_core + (index < extra) for index in range(len(cores)))
    item_starts, start = [], 0
    for count in item_counts:
      item_starts.append(start)
      start += count

    items_per_core = max(item_counts)
    if axis is None:
      shard_element_starts = tuple(start * 1024 for start in item_starts)
      shard_element_counts = tuple(
        min(count * 1024, elements - start)
        for start, count in zip(shard_element_starts, item_counts)
      )
    else:
      # Axis 0 shards are contiguous in row-major storage. For other axes this
      # identifies the first element; codegen must apply the tensor strides.
      axis_stride = prod(shape[axis + 1:])
      shard_element_starts = tuple(start * axis_stride for start in item_starts)
      shard_element_counts = tuple(count * item_elements for count in item_counts)
    tile_starts = tuple(start // 1024 for start in shard_element_starts)
    shard_offsets = tuple(start % 1024 for start in shard_element_starts)
    tile_counts = tuple(
      (offset + count + 1023) // 1024
      for offset, count in zip(shard_offsets, shard_element_counts)
    )
    object.__setattr__(self, "items", items)
    object.__setattr__(self, "item_elements", item_elements)
    object.__setattr__(self, "items_per_core", items_per_core)
    object.__setattr__(self, "tiles_per_item", tiles_per_item)
    object.__setattr__(self, "tiles_per_core", max(tile_counts))
    object.__setattr__(self, "item_starts", tuple(item_starts))
    object.__setattr__(self, "item_counts", item_counts)
    object.__setattr__(self, "tile_starts", tile_starts)
    object.__setattr__(self, "tile_counts", tile_counts)
    object.__setattr__(self, "shard_offsets", shard_offsets)
    object.__setattr__(self, "shard_element_starts", shard_element_starts)
    object.__setattr__(self, "shard_element_counts", shard_element_counts)

  @property
  def tiles(self): return (prod(self.shape) + 1023) // 1024

  @property
  def physical_tiles(self): return self.tiles

  @property
  def tile_size(self): return 1024 * self.dtype.itemsize

  @property
  def size(self): return prod(self.shape) * self.dtype.itemsize

  @property
  def tail_size(self): return self.size % self.tile_size

  @property
  def allocation_size(self):
    """Largest exact byte span occupied in any one interleaved DRAM bank."""
    full_tiles, tail = divmod(self.size, self.tile_size)
    tail_transfer = (tail + 15) & -16 if tail else 0
    spans = []
    for bank in range(self.banks):
      full_in_bank = (
        (full_tiles - bank + self.banks - 1) // self.banks
        if bank < full_tiles else 0
      )
      span = full_in_bank * self.tile_size
      if tail and bank == full_tiles % self.banks:
        span += tail_transfer
      spans.append(span)
    return max(spans)

  def shard_addr(self, core):
    if self.global_address: return self.addr
    tile = self.tile_starts[self.cores.index(core)]
    rows, bank = divmod(tile, self.banks)
    # Buffer addresses are 64-byte aligned. Use the otherwise-zero low bits
    # to carry this shard's initial bank without adding another kernel param.
    return self.addr + rows * self.tile_size | bank

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
    if self.dtype is DType.U32:
      return np.frombuffer(data, dtype="<u4").reshape(self.shape).copy()
    if self.dtype is DType.F32: values = np.frombuffer(data, dtype="<f4")
    else:
      values = (
        np.frombuffer(data, dtype="<u2").astype(np.uint32) << 16
      ).view(np.float32)
    return values.reshape(self.shape).copy()

  def storage_data(self, data: bytes, *, inverse=False):
    """Validate exact, dense row-major storage bytes.

    The final DRAM page is short rather than zero-padded. Sharding is metadata
    only and never changes or expands the logical byte stream.
    """
    data = bytes(data)
    if len(data) != self.size:
      direction = "readback" if inverse else "upload"
      raise ValueError(
        f"{direction} for {self.name!r} has {len(data)} bytes; "
        f"expected exactly {self.size}",
      )
    return data


@dataclass(frozen=True, eq=False)
class Const:
  name: str
  value: int | tuple[int, ...]


Param = Buffer | Const


def _param_values(param, cores, value=None):
  if value is None: value = param if isinstance(param, Buffer) else param.value
  if isinstance(value, Buffer): return tuple(value.shard_addr(core) for core in cores)
  return tuple(value) if isinstance(value, (tuple, list)) else (value,) * len(cores)


def _param_word(value):
  return value.addr if isinstance(value, Buffer) else value


class Dram:
  START = 0x40
  END = 1 << 32
  ALIGNMENT = 64
  BANKS = 7

  def __init__(self, banks=BANKS, cores=P100_WORKER_CORES):
    self.allocator = Allocator(self.START, self.END, self.ALIGNMENT)
    self.banks = banks
    self.cores = tuple(cores)

  def buffer(self, name: str, dtype: DType, shape: tuple[int, ...],
             axis=None, *, global_address=False, cores=None) -> Buffer:
    storage_cores = self.cores if cores is None else tuple(cores)
    if not storage_cores: raise ValueError("buffer requires storage cores")
    if len(set(storage_cores)) != len(storage_cores):
      raise ValueError("buffer storage cores must be unique")
    if any(core not in self.cores for core in storage_cores):
      raise ValueError("buffer storage cores must belong to this DRAM device")
    # Globally addressed buffers have one linear page namespace shared by all
    # worker cores, so they need only one metadata owner.
    storage_cores = (storage_cores[0],) if global_address else storage_cores
    buffer = Buffer(
      name, 0, dtype, shape, axis, storage_cores, self.banks, global_address,
    )
    addr = self.allocator.alloc(buffer.allocation_size)
    return Buffer(
      name, addr, dtype, shape, axis, storage_cores, self.banks, global_address,
    )


class Program:
  def __init__(self, cores, *parameters, fp32_dst=False, images=None):
    self._cores = tuple(cores)
    params = tuple(parameters)
    if len(params) > TensixL1.PARAM_SLOTS:
      raise ValueError("program parameter table is full")
    self.params = {param.name: param for param in params}
    self._param_slots = {param: slot for slot, param in enumerate(params)}
    # Program-scoped CBs and constants consume the large non-persistent arena.
    self._l1 = Allocator(
      TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.DATA_BUFFER_SPACE_END, 16,
    )
    self.cb = CBRegistry(self._l1)
    self._l1_constants = {}
    self.launch = ()
    self._kernels = None if images is None else {
      core: dict(images) for core in self._cores
    }

    if images is not None: return
    self.roles = {
      role: Asm(role, param_slots=self._param_slots)
      for role in KERNEL_ROLES
    }
    for role, stream in self.roles.items(): setattr(self, role, stream)
    dst = Dst(fp32_dst)
    self.unpack = Unpack(self.trisc0, dst)
    self.fpu = Fpu(self.trisc1, dst)
    self.sfpu = Sfpu(self.trisc1, dst, seed_kernel=self.brisc)
    self.pack = Pack(self.trisc2, dst)
    self.ops = Ops(self, self.unpack, self.fpu, self.sfpu, self.pack)
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
  def cbs(self): return self.cb.configs

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

  def bind(self, param, value=None):
    values = _param_values(param, self.cores, value)
    data = tuple(_param_word(item).to_bytes(4, "little") for item in values)
    return UnicastWrite(self.cores, self.param_addr(param), data)

  def _param_table(self, values=None):
    values = {} if values is None else dict(values)
    resolved = {}
    for key, value in values.items():
      param = self.params[key] if isinstance(key, str) else key
      resolved[param] = value
    columns = [
      _param_values(param, self.cores, resolved.get(param))
      for param in self.params.values()
    ]
    return tuple(
      b"".join(_param_word(column[index]).to_bytes(4, "little") for column in columns)
      for index in range(len(self.cores))
    )

  def static_commands(self):
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
    return tuple(commands)

  def runtime_commands(self, params=None):
    commands = []
    if self.params:
      commands.append(UnicastWrite(
        self.cores, PARAM_BASE, self._param_table(params),
      ))
    return (*commands, *self.launch)

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
