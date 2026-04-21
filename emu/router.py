class Router:
  __slots__ = ('_ranges', '_hooks32', 'default',
               '_c_lo', '_c_hi', '_c_h', '_c_off')

  def __init__(self, default=None):
    self._ranges: list[tuple[int, int, object, int]] = []
    self._hooks32: dict[int, object] = {}
    self.default = default
    # Hot-path cache — lo>hi means empty
    self._c_lo, self._c_hi = 1, 0
    self._c_h, self._c_off = None, 0

  def register(self, lo: int, hi: int, handler, offset: int = 0):
    self._ranges.append((lo, hi, handler, offset))
    # Invalidate cache — a newly-registered earlier range could shadow it.
    self._c_lo, self._c_hi = 1, 0

  def on_write32(self, addr: int, cb):
    self._hooks32[addr] = cb

  def _find(self, addr: int):
    if self._c_lo <= addr <= self._c_hi:
      return self._c_h, self._c_off
    for lo, hi, h, off in self._ranges:
      if lo <= addr <= hi:
        self._c_lo, self._c_hi, self._c_h, self._c_off = lo, hi, h, off
        return h, off
    return self.default, 0

  def read8(self, addr):
    h, off = self._find(addr); return h.read8(addr - off)
  def read16(self, addr):
    h, off = self._find(addr); return h.read16(addr - off)
  def read32(self, addr):
    h, off = self._find(addr); return h.read32(addr - off)

  def write8(self, addr, val):
    h, off = self._find(addr); h.write8(addr - off, val)
  def write16(self, addr, val):
    h, off = self._find(addr); h.write16(addr - off, val)
  def write32(self, addr, val):
    cb = self._hooks32.get(addr)
    old = self.read32(addr) if cb else None
    h, off = self._find(addr); h.write32(addr - off, val)
    if cb: cb(old, val)
