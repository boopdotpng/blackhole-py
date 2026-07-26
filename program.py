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
  # Face-tilize each 1024-element tile on upload. Required for anything the
  # Tensix datapath consumes directly (unpack -> srcA/srcB), because the
  # unpacker's address generator walks 16x16 faces. Set False only for buffers
  # read as raw bytes by BRISC/NCRISC -- e.g. an embedding table gathered by
  # NoC and tilized on device afterwards. Operands that are elementwise-
  # combined must agree: a row-major activation against a tilized weight
  # silently pairs the wrong elements.
  tilized: bool = True

  def __post_init__(self):
    shape, axis, cores = tuple(self.shape), self.axis, tuple(self.cores)
    if not cores: raise ValueError("buffer requires at least one storage core")
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

    items_per_core = max(1, per_core + bool(extra))
    tiles_per_core = items_per_core * tiles_per_item
    object.__setattr__(self, "items", items)
    object.__setattr__(self, "item_elements", item_elements)
    object.__setattr__(self, "items_per_core", items_per_core)
    object.__setattr__(self, "tiles_per_item", tiles_per_item)
    object.__setattr__(self, "tiles_per_core", tiles_per_core)
    object.__setattr__(self, "item_starts", tuple(item_starts))
    object.__setattr__(self, "item_counts", item_counts)
    object.__setattr__(
      self, "tile_starts",
      tuple(index * tiles_per_core for index in range(len(cores))),
    )
    object.__setattr__(self, "tile_counts", (tiles_per_core,) * len(cores))

  @property
  def tiles(self): return self.items * self.tiles_per_item

  @property
  def physical_tiles(self): return len(self.cores) * self.tiles_per_core

  @property
  def tile_size(self): return 1024 * self.dtype.itemsize

  @property
  def size(self): return self.physical_tiles * self.tile_size

  @property
  def storage_shape(self): return len(self.cores), self.tiles_per_core, 32, 32

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

  def tile_data(self, data: bytes, *, inverse=False):
    element = np.dtype(f"V{self.dtype.itemsize}")
    if inverse:
      physical = np.frombuffer(data, dtype=element)
      if self.tilized:
        tiles = physical.reshape(self.physical_tiles, 2, 2, 16, 16)
        tiles = tiles.transpose(0, 1, 3, 2, 4).reshape(self.physical_tiles, 1024)
      else:
        tiles = physical.reshape(self.physical_tiles, 1024)
      blocks = tiles.reshape(len(self.cores), self.items_per_core,
                             self.tiles_per_item * 1024)
      items = np.concatenate([
        block[:count] for block, count in zip(blocks, self.item_counts)
      ])
      if self.axis is None: return items.reshape(-1)[:prod(self.shape)].tobytes()
      items = items[:, :self.item_elements]
      moved_shape = (
        self.shape[self.axis], *self.shape[:self.axis], *self.shape[self.axis + 1:]
      )
      values = items.reshape(moved_shape)
      return np.moveaxis(values, 0, self.axis).tobytes()

    values = np.frombuffer(data, dtype=element).reshape(self.shape)
    # Llama weights use axis-0 rows made of complete tiles. Tilize directly
    # from the safetensor view into final sharded storage, avoiding the two
    # full-size "logical" and "blocks" intermediates below. This matters for
    # multi-gigabyte model startup, while the generic path still handles
    # partial items and arbitrary shard axes.
    if (
      self.axis == 0 and
      self.item_elements == self.tiles_per_item * 1024
    ):
      items = values.reshape(
        self.items, self.tiles_per_item, 2, 16, 2, 16,
      )
      if self.tilized:
        items = items.transpose(0, 1, 2, 4, 3, 5)
      if len(self.cores) == 1 and self.items_per_core == self.items:
        return items.tobytes()
      item_shape = (
        (self.tiles_per_item, 2, 2, 16, 16)
        if self.tilized else (self.tiles_per_item, 2, 16, 2, 16)
      )
      blocks = np.zeros(
        (len(self.cores), self.items_per_core, *item_shape),
        dtype=element,
      )
      for block, start, count in zip(
        blocks, self.item_starts, self.item_counts,
      ):
        block[:count] = items[start:start + count]
      return blocks.tobytes()

    if self.axis is None:
      logical = np.zeros((self.items, 1024), dtype=element)
      logical.reshape(-1)[:values.size] = values.reshape(-1)
    else:
      logical = np.zeros(
        (self.items, self.tiles_per_item * 1024), dtype=element,
      )
      logical[:, :self.item_elements] = np.moveaxis(
        values, self.axis, 0,
      ).reshape(self.items, self.item_elements)

    blocks = np.zeros(
      (len(self.cores), self.items_per_core, self.tiles_per_item * 1024),
      dtype=element,
    )
    for block, start, count in zip(blocks, self.item_starts, self.item_counts):
      block[:count] = logical[start:start + count]
    if not self.tilized: return blocks.tobytes()
    tiles = blocks.reshape(self.physical_tiles, 2, 16, 2, 16)
    return tiles.transpose(0, 1, 3, 2, 4).tobytes()


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
             axis=None, *, global_address=False, cores=None,
             tilized=True) -> Buffer:
    storage_cores = self.cores if cores is None else tuple(cores)
    if not storage_cores: raise ValueError("buffer requires storage cores")
    if len(set(storage_cores)) != len(storage_cores):
      raise ValueError("buffer storage cores must be unique")
    if any(core not in self.cores for core in storage_cores):
      raise ValueError("buffer storage cores must belong to this DRAM device")
    # Globally addressed buffers have one linear tile namespace shared by all
    # worker cores. Use one storage core so sharding introduces no padding.
    storage_cores = (storage_cores[0],) if global_address else storage_cores
    buffer = Buffer(
      name, 0, dtype, shape, axis, storage_cores, self.banks, global_address,
      tilized,
    )
    tiles_per_bank = (buffer.physical_tiles + self.banks - 1) // self.banks
    addr = self.allocator.alloc(tiles_per_bank * buffer.tile_size)
    return Buffer(
      name, addr, dtype, shape, axis, storage_cores, self.banks, global_address,
      tilized,
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
