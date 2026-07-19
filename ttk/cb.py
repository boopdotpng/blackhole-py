from isa import R


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
