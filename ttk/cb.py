from isa import R


class CB:
  INTERFACE_SIZE = 32
  SYNC_TILES_ACKED_BASE = 0xFFB48020
  SYNC_TILES_RECEIVED_BASE = 0xFFB48028
  SYNC_STRIDE = 0x1000

  @staticmethod
  def setup_local_cbs(kernel):
    with kernel.scope():
      acked, remaining, stride = kernel.reg(3)
      kernel.li(acked, CB.SYNC_TILES_ACKED_BASE)
      kernel.li(remaining, 32); kernel.li(stride, CB.SYNC_STRIDE)
      loop = kernel._new_label("reset_cb_sync")
      kernel.label(loop); kernel.sw(R.ZERO, acked); kernel.sw(R.ZERO, acked, 8)
      kernel.add(acked, acked, stride)
      kernel.addi(remaining, remaining, -1); kernel.bne(remaining, R.ZERO, loop)
    return kernel

  def __init__(self, kernel, config):
    self.k, self.config = kernel, config
    self.interface = kernel.local.alloc(self.INTERFACE_SIZE, name=f"cb{config.index}_interface")
    for offset, value in (
      (0, config.addr), (4, config.addr + config.pages * config.page_size),
      (8, config.page_size), (12, config.pages),
      (16, config.addr), (20, config.addr), (24, 0), (28, 0),
    ): kernel.store(self.interface + offset, value)

  @property
  def index(self): return self.config.index

  @property
  def addr(self): return self.config.addr

  @property
  def dtype(self): return self.config.dtype

  @property
  def page_size(self): return self.config.page_size

  def _sync(self, base): return base + self.index * self.SYNC_STRIDE

  def _advance(self, pointer_offset, count):
    if type(count) is not int or not 0 < count <= self.config.pages:
      raise ValueError("CB page count must be a positive integer within capacity")
    k = self.k
    with k.scope():
      pointer, step, limit, base = k.reg(4)
      k.load(pointer, self.interface + pointer_offset)
      k.li(step, count * self.page_size); k.add(pointer, pointer, step)
      k.load(limit, self.interface + 4)
      no_wrap = k._new_label("cb_no_wrap")
      k.bltu(pointer, limit, no_wrap)
      k.load(base, self.interface); k.sub(limit, limit, base); k.sub(pointer, pointer, limit)
      k.label(no_wrap); k.store(self.interface + pointer_offset, pointer)

  def reserve_back(self, count=1):
    k = self.k
    with k.scope():
      counter, received, acked, used, capacity, need = k.reg(6)
      k.load(counter, self.interface + 24); k.srli(received, counter, 16)
      loop, done = k._new_label("cb_reserve"), k._new_label("cb_reserved")
      k.label(loop)
      k.load(acked, self._sync(self.SYNC_TILES_ACKED_BASE), bytes=2)
      k.sub(used, received, acked); k.slli(used, used, 16); k.srli(used, used, 16)
      k.load(capacity, self.interface + 12)
      k.sub(capacity, capacity, used); k.li(need, count)
      k.bgeu(capacity, need, done); k.fence(); k.j(loop); k.label(done); k.fence()
    return self

  def push_back(self, count=1):
    self._advance(20, count); k = self.k
    with k.scope():
      counter, acked, received, tmp = k.reg(4)
      k.load(counter, self.interface + 24)
      k.slli(acked, counter, 16); k.srli(acked, acked, 16)
      k.srli(received, counter, 16); k.addi(received, received, count)
      k.slli(tmp, received, 16); k.or_(counter, tmp, acked)
      k.store(self.interface + 24, counter)
      k.store(self._sync(self.SYNC_TILES_RECEIVED_BASE), received); k.fence()
    return self

  def wait_front(self, count=1):
    k = self.k
    with k.scope():
      counter, acked, received, available, need = k.reg(5)
      k.load(counter, self.interface + 24)
      k.slli(acked, counter, 16); k.srli(acked, acked, 16); k.li(need, count)
      loop, done = k._new_label("cb_wait"), k._new_label("cb_ready")
      k.label(loop)
      k.load(received, self._sync(self.SYNC_TILES_RECEIVED_BASE), bytes=2)
      k.sub(available, received, acked); k.slli(available, available, 16); k.srli(available, available, 16)
      k.bgeu(available, need, done); k.fence(); k.j(loop); k.label(done); k.fence()
    return self

  def pop_front(self, count=1):
    k = self.k
    with k.scope():
      counter, acked, received, tmp = k.reg(4)
      k.load(counter, self.interface + 24)
      k.slli(acked, counter, 16); k.srli(acked, acked, 16); k.addi(acked, acked, count)
      k.slli(tmp, acked, 16); k.srli(acked, tmp, 16)
      k.srli(received, counter, 16); k.slli(received, received, 16)
      k.or_(counter, received, acked); k.store(self.interface + 24, counter)
      k.store(self._sync(self.SYNC_TILES_ACKED_BASE), acked); k.fence()
    self._advance(16, count)
    return self

  def read_ptr(self, out: R): self.k.load(out, self.interface + 16); return self

  def write_ptr(self, out: R): self.k.load(out, self.interface + 20); return self
