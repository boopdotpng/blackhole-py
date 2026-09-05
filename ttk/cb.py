from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from isa import Reg, is_reg

Value = int | Reg
Coordinate = tuple[Value, Value]

DEFAULT_CB_DEPTH = 2

# The current firmware resets 32 stream-register pairs for use as physical CB
# synchronization slots.  These slots are allocated by lowering and may be
# reused by logical CBs with disjoint lifetimes.  They do not limit how many CB
# objects or payload allocations a program may have.
CB_SYNC_SLOT_COUNT = 32
CB_ACKED_BASE = 0xFFB48020
CB_RECEIVED_BASE = 0xFFB48028
CB_STREAM_REGISTER_STRIDE = 0x1000

class Layout(Enum):
  ROW_MAJOR = "row_major"
  FACE_TILIZED = "face_tilized"
  SCALAR = "scalar"
  BLOCK = "block"


class L1Allocator(Protocol):
  def alloc(self, size: int, alignment: int | None = None) -> int: ...


def _positive_int(value, name):
  if type(value) is not int or value <= 0:
    raise ValueError(f"{name} must be a positive integer")
  return value


def _power_of_two(value, name):
  _positive_int(value, name)
  if value & (value - 1):
    raise ValueError(f"{name} must be a power of two")
  return value


def _value(value, name, *, positive=False):
  if type(value) is int:
    if value < (1 if positive else 0):
      qualifier = "positive" if positive else "non-negative"
      raise ValueError(f"{name} must be {qualifier}")
  elif not is_reg(value):
    raise TypeError(f"{name} must be an integer or RISC register")
  return value


def _coordinate(core, name="core"):
  if not isinstance(core, tuple) or len(core) != 2:
    raise TypeError(f"{name} must be an (x, y) pair")
  for axis, component in zip("xy", core):
    _value(component, f"{name} {axis}")
    if type(component) is int and component >= 1 << 6:
      raise ValueError(f"{name} {axis} must fit in six bits")
  return core


@dataclass(frozen=True, slots=True)
class CB:
  """A statically allocated L1 ring."""

  id: int
  dtype: object
  item_bytes: int
  address: int
  layout: Layout = Layout.FACE_TILIZED
  alignment: int = 16
  symmetric: bool = False
  depth: int = DEFAULT_CB_DEPTH

  def __post_init__(self):
    if type(self.id) is not int or self.id < 0:
      raise ValueError("CB id must be a non-negative logical index")
    if self.dtype is None:
      raise TypeError("CB dtype cannot be None")
    _positive_int(self.item_bytes, "CB item_bytes")
    _power_of_two(self.alignment, "CB alignment")
    if self.item_bytes % self.alignment:
      raise ValueError("CB item_bytes must preserve the alignment of every slot")
    if type(self.address) is not int or self.address < 0:
      raise TypeError("CB address must be a non-negative static L1 address")
    if self.address % self.alignment:
      raise ValueError("CB address does not satisfy its alignment")
    if not isinstance(self.layout, Layout):
      raise TypeError("CB layout must be a Layout")
    if type(self.symmetric) is not bool:
      raise TypeError("CB symmetric must be a bool")
    _positive_int(self.depth, "CB depth")
    if self.depth >= 1 << 16:
      raise ValueError("CB depth must fit below the 16-bit counter modulus")

  @property
  def size_bytes(self): return self.depth * self.item_bytes

  @property
  def limit(self): return self.address + self.size_bytes

  def slot_address(self, item: int):
    if type(item) is not int or item < 0:
      raise ValueError("CB item must be a non-negative integer")
    return self.address + item % self.depth * self.item_bytes

@dataclass(frozen=True, slots=True)
class CBSyncSlot:
  """One physical received/acked register pair assigned during lowering."""

  index: int

  def __post_init__(self):
    if type(self.index) is not int or not 0 <= self.index < CB_SYNC_SLOT_COUNT:
      raise ValueError(
        f"CB sync slot must be in range 0..{CB_SYNC_SLOT_COUNT - 1}",
      )

  def _counter(self, base): return base + self.index * CB_STREAM_REGISTER_STRIDE

  @property
  def acked_address(self): return self._counter(CB_ACKED_BASE)

  @property
  def received_address(self): return self._counter(CB_RECEIVED_BASE)

  @staticmethod
  def _increment_counter(kernel, address):
    value = kernel.reg()
    kernel.read(value, address, bytes=2)
    kernel.addi(value, value, 1)
    # Keep the software value identical to the architected 16-bit counter.
    kernel.slli(value, value, 16)
    kernel.srli(value, value, 16)
    kernel.fence()
    kernel.write(address, value)
    return kernel.fence()

  def reserve_back(self, kernel, cb: CB):
    """Wait until the producer owns one free slot."""
    received, acked, used, depth = kernel.reg(4)
    kernel.read(received, self.received_address, bytes=2)
    kernel.li(depth, cb.depth)
    loop = kernel._new_label("cb_reserve")
    done = kernel._new_label("cb_reserved")
    kernel.label(loop)
    kernel.read(acked, self.acked_address, bytes=2)
    kernel.sub(used, received, acked)
    kernel.slli(used, used, 16)
    kernel.srli(used, used, 16)
    kernel.bltu(used, depth, done)
    kernel.fence()
    kernel.j(loop)
    kernel.label(done)
    kernel.fence()
    return cb

  def push_back(self, kernel, cb: CB):
    """Publish one completely filled slot to the consumer."""
    self._increment_counter(kernel, self.received_address)
    return cb

  def wait_front(self, kernel, cb: CB):
    """Wait until the consumer owns one filled slot."""
    acked, received = kernel.reg(2)
    kernel.read(acked, self.acked_address, bytes=2)
    loop = kernel._new_label("cb_wait")
    done = kernel._new_label("cb_ready")
    kernel.label(loop)
    kernel.read(received, self.received_address, bytes=2)
    kernel.bne(received, acked, done)
    kernel.fence()
    kernel.j(loop)
    kernel.label(done)
    kernel.fence()
    return cb

  def pop_front(self, kernel, cb: CB):
    """Release one completely consumed slot to the producer."""
    self._increment_counter(kernel, self.acked_address)
    return cb

  @staticmethod
  def _pointer(kernel, cb: CB, counter_address: int, out: Reg):
    counter, slot = kernel.reg(2)
    kernel.read(counter, counter_address, bytes=2)
    if cb.depth & (cb.depth - 1) == 0:
      mask = cb.depth - 1
      if mask < 1 << 11:
        kernel.andi(slot, counter, mask)
      else:
        kernel.li(slot, mask)
        kernel.and_(slot, counter, slot)
    else:
      kernel.li(slot, cb.depth)
      kernel.remu(slot, counter, slot)
    kernel.li(out, cb.address)
    if cb.item_bytes & (cb.item_bytes - 1) == 0:
      kernel.slli(slot, slot, cb.item_bytes.bit_length() - 1)
    else:
      stride = kernel.reg()
      kernel.li(stride, cb.item_bytes)
      kernel.mul(slot, slot, stride)
    kernel.add(out, out, slot)
    return cb

  def get_write_ptr(self, kernel, cb: CB, out: Reg):
    return self._pointer(kernel, cb, self.received_address, out)

  def get_read_ptr(self, kernel, cb: CB, out: Reg):
    return self._pointer(kernel, cb, self.acked_address, out)


@dataclass(frozen=True, slots=True)
class CBSpan:
  address: int
  bytes: int


@dataclass(frozen=True, slots=True)
class _CBWindow:
  cb: CB
  item: Value
  items: Value = 1
  valid_bytes: Value | None = None

  def __post_init__(self):
    if not isinstance(self.cb, CB):
      raise TypeError("CB window requires a CB")
    _value(self.item, "CB window item")
    _value(self.items, "CB window items", positive=True)
    if type(self.items) is int and self.items > self.cb.depth:
      raise ValueError("CB window cannot exceed the ring depth")
    if self.valid_bytes is not None:
      _value(self.valid_bytes, "CB window valid_bytes", positive=True)
      if type(self.valid_bytes) is int and type(self.items) is int:
        if self.valid_bytes > self.items * self.cb.item_bytes:
          raise ValueError("CB window valid_bytes exceeds its slot capacity")

  @property
  def capacity_bytes(self):
    return self.items * self.cb.item_bytes if type(self.items) is int else None

  @property
  def payload_bytes(self):
    return self.capacity_bytes if self.valid_bytes is None else self.valid_bytes

  def static_spans(self):
    """Return contiguous L1 spans, splitting a statically known ring wrap."""
    if not all(type(value) is int for value in (self.item, self.items, self.payload_bytes)):
      raise TypeError("CB spans require static item, items, and byte count")
    remaining = self.payload_bytes
    item = self.item
    spans = []
    for _ in range(self.items):
      size = min(remaining, self.cb.item_bytes)
      if size:
        spans.append(CBSpan(self.cb.slot_address(item), size))
        remaining -= size
      item += 1
    return tuple(spans)


@dataclass(frozen=True, slots=True)
class CBRead(_CBWindow):
  pass


@dataclass(frozen=True, slots=True)
class CBWrite(_CBWindow):
  pass


@dataclass(frozen=True, slots=True)
class RemoteCBRead:
  local: CBRead
  core: Coordinate

  def __post_init__(self):
    if not isinstance(self.local, CBRead):
      raise TypeError("remote CB source must be a CBRead")
    _coordinate(self.core)


@dataclass(frozen=True, slots=True)
class RemoteCBWrite:
  local: CBWrite
  cores: tuple[Coordinate, ...]
  multicast: bool = False

  def __post_init__(self):
    if not isinstance(self.local, CBWrite):
      raise TypeError("remote CB destination must be a CBWrite")
    if not isinstance(self.cores, tuple) or not self.cores:
      raise ValueError("remote CB destination requires at least one core")
    for index, core in enumerate(self.cores):
      _coordinate(core, f"core {index}")
    if len(set(self.cores)) != len(self.cores):
      raise ValueError("remote CB destination cores must be unique")
    if type(self.multicast) is not bool:
      raise TypeError("multicast must be a bool")
    if self.multicast and not self.local.cb.symmetric:
      raise ValueError("multicast requires a symmetric CB")


@dataclass(frozen=True, slots=True)
class _InternalCB:
  cb: CB
  lifetime: object


class CBRegistry:
  """Allocate public and lowering-created internal CBs from program L1."""

  def __init__(self, l1_allocator: L1Allocator):
    if not hasattr(l1_allocator, "alloc"):
      raise TypeError("CBRegistry requires an L1 allocator")
    self._l1 = l1_allocator
    self._cbs: dict[int, CB] = {}
    self._internal: dict[str, _InternalCB] = {}

  def _id(self, requested):
    if requested is not None:
      if type(requested) is not int or requested < 0:
        raise ValueError("CB id must be a non-negative logical index")
      if requested in self._cbs:
        raise ValueError(f"CB {requested} is already allocated")
      return requested
    candidate = 0
    while candidate in self._cbs: candidate += 1
    return candidate

  def create(self, dtype, item_bytes, depth=DEFAULT_CB_DEPTH, *, id=None,
             address=None, alignment=16, layout=Layout.FACE_TILIZED,
             symmetric=False):
    _positive_int(item_bytes, "CB item_bytes")
    _power_of_two(alignment, "CB alignment")
    if item_bytes % alignment:
      raise ValueError("CB item_bytes must preserve the alignment of every slot")
    _positive_int(depth, "CB depth")
    if depth >= 1 << 16:
      raise ValueError("CB depth must fit below the 16-bit counter modulus")
    cb_id = self._id(id)
    if address is None:
      address = self._l1.alloc(depth * item_bytes, alignment)
    cb = CB(cb_id, dtype, item_bytes, address, layout, alignment,
            symmetric, depth)
    self._cbs[cb_id] = cb
    return cb

  __call__ = create

  def internal(self, name, dtype, item_bytes, depth=DEFAULT_CB_DEPTH, *, id=None,
               address=None, alignment=16, layout=Layout.FACE_TILIZED,
               symmetric=False, lifetime=None):
    if not isinstance(name, str) or not name:
      raise ValueError("internal CB name must be a non-empty string")
    existing = self._internal.get(name)
    if existing is not None:
      cb = existing.cb
      requested = (dtype, item_bytes, depth, alignment, layout, symmetric, lifetime)
      actual = (cb.dtype, cb.item_bytes, cb.depth, cb.alignment, cb.layout,
                cb.symmetric, existing.lifetime)
      if requested != actual or (id is not None and id != cb.id) or (
        address is not None and address != cb.address
      ):
        raise ValueError(f"internal CB {name!r} was requested with different properties")
      return cb
    cb = self.create(dtype, item_bytes, depth, id=id, address=address,
                     alignment=alignment, layout=layout, symmetric=symmetric)
    self._internal[name] = _InternalCB(cb, lifetime)
    return cb

  def bind(self, id, address, dtype, item_bytes, depth=DEFAULT_CB_DEPTH, *,
           alignment=16, layout=Layout.FACE_TILIZED, symmetric=False):
    return self.create(dtype, item_bytes, depth, id=id, address=address,
                       alignment=alignment, layout=layout,
                       symmetric=symmetric)

  @staticmethod
  def read(cb, item, items=1, *, valid_bytes=None):
    return CBRead(cb, item, items, valid_bytes)

  @staticmethod
  def write(cb, item, items=1, *, valid_bytes=None):
    return CBWrite(cb, item, items, valid_bytes)

  @staticmethod
  def remote_read(source, core):
    return RemoteCBRead(source, core)

  @staticmethod
  def remote_write(destination, cores, *, multicast=False):
    return RemoteCBWrite(destination, tuple(cores), multicast)

  @property
  def configs(self): return tuple(self._cbs[index] for index in sorted(self._cbs))

  @property
  def internal_cbs(self):
    return {name: entry.cb for name, entry in self._internal.items()}
