from __future__ import annotations
from dataclasses import dataclass
from ttko.isa import R, Tensix as TT
from ttko import DType
from ttko.registers import DType, TensixRegs


@dataclass(frozen=True)
class CBConfig:
  index: int
  dtype: DType
  depth: int
  addr: int

  @property
  def tile_size(self): return 1024 * self.dtype.itemsize

  @property
  def size(self): return self.depth * self.tile_size

  @property
  def limit(self): return self.addr + self.size


class CBRegistry:
  COUNT = 32

  def __init__(self, l1_allocator):
    self._l1 = l1_allocator
    self._configs = []
    self._internal = {}

  def _allocate(self, dtype, depth):
    if not isinstance(dtype, DType):
      raise TypeError("CB dtype must be a DType")
    if type(depth) is not int or depth < 1:
      raise ValueError("CB depth must be a positive integer")
    if len(self._configs) >= self.COUNT:
      raise ValueError(f"program cannot allocate more than {self.COUNT} CBs")
    tile_size = 1024 * dtype.itemsize
    config = CBConfig(
      len(self._configs), dtype, depth,
      self._l1.alloc(depth * tile_size),
    )
    self._configs.append(config)
    return config

  def __call__(self, dtype, depth=2):
    return self._allocate(dtype, depth)

  def internal(self, name, dtype, depth=1):
    if not isinstance(name, str) or not name:
      raise ValueError("internal CB name must be a non-empty string")
    requested = dtype, depth
    if name in self._internal:
      config = self._internal[name]
      if (config.dtype, config.depth) != requested:
        raise ValueError(
          f"internal CB {name!r} was already allocated as "
          f"{config.dtype.name} depth {config.depth}"
        )
      return config
    config = self._allocate(dtype, depth)
    self._internal[name] = config
    return config

  @property
  def configs(self): return tuple(self._configs)


class CB:
  SYNC_TILES_ACKED_BASE = 0xFFB48020
  SYNC_TILES_RECEIVED_BASE = 0xFFB48028
  SYNC_STRIDE = 0x1000

  @staticmethod
  def reset_counters(kernel):
    with kernel.scope():
      acked, remaining, stride = kernel.reg(3)
      kernel.li(acked, CB.SYNC_TILES_ACKED_BASE)
      kernel.li(remaining, 32); kernel.li(stride, CB.SYNC_STRIDE)
      loop = kernel._new_label("reset_cb_sync")
      kernel.label(loop); kernel.sw(R.ZERO, acked); kernel.sw(R.ZERO, acked, 8)
      kernel.add(acked, acked, stride)
      kernel.addi(remaining, remaining, -1); kernel.bne(remaining, R.ZERO, loop)
    return kernel

  @staticmethod
  def _state(kernel, config, producer):
    states = getattr(kernel, "_cb_states", None)
    if states is None:
      states = kernel._cb_states = {}
    key = config.index, producer
    if key not in states:
      state = kernel.local.alloc(8)
      kernel.initialize_local(state, config.addr)
      kernel.initialize_local(state + 4, 0)
      states[key] = state
    return states[key]

  @staticmethod
  def _sync(config, base): return base + config.index * CB.SYNC_STRIDE

  @staticmethod
  def _advance(kernel, config, state, count):
    with kernel.scope():
      pointer, step, limit, size = kernel.reg(4)
      kernel.read(pointer, state)
      kernel.li(step, count * config.tile_size); kernel.add(pointer, pointer, step)
      kernel.li(limit, config.limit)
      no_wrap = kernel._new_label("cb_no_wrap")
      kernel.bltu(pointer, limit, no_wrap)
      kernel.li(size, config.size); kernel.sub(pointer, pointer, size)
      kernel.label(no_wrap); kernel.write(state, pointer)

  @staticmethod
  def reserve_back(kernel, config, count=1):
    state = CB._state(kernel, config, producer=True)
    with kernel.scope():
      received, acked, used, free, need = kernel.reg(5)
      kernel.read(received, state + 4)
      loop, done = kernel._new_label("cb_reserve"), kernel._new_label("cb_reserved")
      kernel.label(loop)
      kernel.read(acked, CB._sync(config, CB.SYNC_TILES_ACKED_BASE), bytes=2)
      kernel.sub(used, received, acked); kernel.slli(used, used, 16); kernel.srli(used, used, 16)
      kernel.li(free, config.depth); kernel.sub(free, free, used); kernel.li(need, count)
      kernel.bgeu(free, need, done); kernel.fence(); kernel.j(loop); kernel.label(done); kernel.fence()
    return config

  @staticmethod
  def push_back(kernel, config, count=1):
    state = CB._state(kernel, config, producer=True)
    CB._advance(kernel, config, state, count)
    with kernel.scope():
      received = kernel.reg()
      kernel.read(received, state + 4); kernel.addi(received, received, count)
      kernel.slli(received, received, 16); kernel.srli(received, received, 16)
      kernel.write(state + 4, received)
      kernel.write(CB._sync(config, CB.SYNC_TILES_RECEIVED_BASE), received); kernel.fence()
    return config

  @staticmethod
  def wait_front(kernel, config, count=1):
    state = CB._state(kernel, config, producer=False)
    with kernel.scope():
      acked, received, available, need = kernel.reg(4)
      kernel.read(acked, state + 4); kernel.li(need, count)
      loop, done = kernel._new_label("cb_wait"), kernel._new_label("cb_ready")
      kernel.label(loop)
      kernel.read(received, CB._sync(config, CB.SYNC_TILES_RECEIVED_BASE), bytes=2)
      kernel.sub(available, received, acked)
      kernel.slli(available, available, 16); kernel.srli(available, available, 16)
      kernel.bgeu(available, need, done); kernel.fence(); kernel.j(loop); kernel.label(done); kernel.fence()
    return config

  @staticmethod
  def pop_front(kernel, config, count=1):
    state = CB._state(kernel, config, producer=False)
    with kernel.scope():
      acked = kernel.reg()
      kernel.read(acked, state + 4); kernel.addi(acked, acked, count)
      kernel.slli(acked, acked, 16); kernel.srli(acked, acked, 16)
      kernel.write(state + 4, acked)
      kernel.write(CB._sync(config, CB.SYNC_TILES_ACKED_BASE), acked); kernel.fence()
    CB._advance(kernel, config, state, count)
    return config

  @staticmethod
  def get_write_ptr(kernel, config, out: R):
    kernel.read(out, CB._state(kernel, config, producer=True))
    return config

  @staticmethod
  def get_read_ptr(kernel, config, out: R):
    kernel.read(out, CB._state(kernel, config, producer=False))
    return config


class CircularBufferOps:
  def _load_count(self, count: int | R, out: R):
    if (isinstance(count, int) and not isinstance(count, R)):
      return self.li(out, count)
    return self.mv(out, count)

  def cb_iface(self, interface_base: int, cb_index: int, *, out: R = R.T6):
    return self.li(out, interface_base + cb_index * 32)

  def cb_counter_low(self, out: R, counter_reg: R):
    self.slli(out, counter_reg, 16)
    return self.srli(out, out, 16)

  def cb_counter_high(self, out: R, counter_reg: R):
    return self.srli(out, counter_reg, 16)

  def cb_reserve_back(self, interface_base: int, cb_index: int, count: int | R = 1):
    iface, received, acked, free_pages, num_pages, need = R.T6, R.T5, R.T4, R.T3, R.T2, R.T1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(received, iface, 24)
    self.cb_counter_high(received, received)
    loop = self._new_label("cb_reserve")
    done = self._new_label("cb_reserve_done")
    self.label(loop)
    self.li(acked, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
    self.lhu(acked, acked, 0)
    self.sub(free_pages, received, acked)
    self.lw(num_pages, iface, 12)
    self.sub(free_pages, num_pages, free_pages)
    self._load_count(count, need)
    self.bge(free_pages, need, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_push_back(self, interface_base: int, cb_index: int, count: int | R = 1, *, tensix_received: bool = False):
    iface, ptr, tmp, counter, acked, received = R.T6, R.T5, R.T4, R.T3, R.T2, R.T1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(ptr, iface, 20)
    self.lw(tmp, iface, 8)
    if (isinstance(count, int) and not isinstance(count, R)) and count == 1:
      self.add(ptr, ptr, tmp)
    else:
      self._load_count(count, counter)
      self.mul(tmp, tmp, counter)
      self.add(ptr, ptr, tmp)
    self.lw(tmp, iface, 4)
    no_wrap = self._new_label("cb_push_no_wrap")
    self.bltu(ptr, tmp, no_wrap)
    self.lw(tmp, iface, 0)
    self.sub(ptr, ptr, tmp)
    self.label(no_wrap)
    self.sw(ptr, iface, 20)

    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self.cb_counter_high(received, counter)
    if (isinstance(count, int) and not isinstance(count, R)) and count == 1:
      self.addi(received, received, 1)
    else:
      self._load_count(count, tmp)
      self.add(received, received, tmp)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    self.srli(received, received, 16)
    self.li(tmp, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
    self.sw(received, tmp, 0)
    if tensix_received:
      self.slli(tmp, received, 8)
      self.li(ptr, int(TT.TTSETDMAREG(0, 0, 0, 48)))
      self.add(tmp, tmp, ptr)
      self.write32(TensixRegs.INSTRN_BUF_BASE, tmp, tmp_addr=ptr, tmp_val=R.T0)
      self.emit(TT.TTSTALLWAIT(32, 8))
      self.push_tensix(
        TT.TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
      )
    return self.fence()

  def cb_wait_front(self, interface_base: int, cb_index: int, count: int | R = 1):
    iface, counter, acked, received, available, need = R.T6, R.T5, R.T4, R.T3, R.T2, R.T1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self._load_count(count, need)
    loop = self._new_label("cb_wait_front")
    done = self._new_label("cb_wait_front_done")
    self.label(loop)
    self.li(received, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
    self.lhu(received, received, 0)
    self.sub(available, received, acked)
    self._load_count(count, need)
    self.bgeu(available, need, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_pop_front(self, interface_base: int, cb_index: int, count: int | R = 1, *, tensix_ack: bool = False):
    iface, ptr, tmp, counter, acked, received = R.T6, R.T5, R.T4, R.T3, R.T2, R.T1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self.cb_counter_high(received, counter)
    if (isinstance(count, int) and not isinstance(count, R)) and count == 1:
      self.addi(acked, acked, 1)
    else:
      self._load_count(count, tmp)
      self.add(acked, acked, tmp)
    self.cb_counter_low(acked, acked)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    self.li(tmp, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
    self.sw(acked, tmp, 0)
    if tensix_ack:
      self.slli(tmp, acked, 8)
      self.li(ptr, int(TT.TTSETDMAREG(0, 0, 0, 8)))
      self.add(tmp, tmp, ptr)
      self.write32(TensixRegs.INSTRN_BUF_BASE, tmp, tmp_addr=ptr, tmp_val=R.T0)
      self.emit(TT.TTSTALLWAIT(32, 6))
      self.push_tensix(
        TT.TTSTOREREG(4, ((CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
      )

    self.lw(ptr, iface, 16)
    self.lw(tmp, iface, 8)
    if (isinstance(count, int) and not isinstance(count, R)) and count == 1:
      self.add(ptr, ptr, tmp)
    else:
      self._load_count(count, counter)
      self.mul(tmp, tmp, counter)
      self.add(ptr, ptr, tmp)
    self.lw(tmp, iface, 4)
    no_wrap = self._new_label("cb_pop_no_wrap")
    self.bltu(ptr, tmp, no_wrap)
    self.lw(tmp, iface, 0)
    self.sub(ptr, ptr, tmp)
    self.label(no_wrap)
    self.sw(ptr, iface, 16)
    return self.fence()

  def cb_write_ptr(self, interface_base: int, cb_index: int, *, out: R = R.T5, shift_to_bytes: bool = False):
    self.cb_iface(interface_base, cb_index, out=R.T6)
    self.lw(out, R.T6, 20)
    if shift_to_bytes:
      self.slli(out, out, 4)
    return self

  def cb_read_ptr(self, interface_base: int, cb_index: int, *, out: R = R.T5, shift_to_bytes: bool = False):
    self.cb_iface(interface_base, cb_index, out=R.T6)
    self.lw(out, R.T6, 16)
    if shift_to_bytes:
      self.slli(out, out, 4)
    return self
