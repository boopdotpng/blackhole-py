class TileBuffer:
  def __init__(self, kernel, config): self.k, self.config = kernel, config

  @property
  def addr(self): return self.config.addr

  @property
  def dtype(self): return self.config.dtype

  @property
  def page_size(self): return self.config.page_size

  def publish(self): self.k.fence(); self.k.store(self.config.flag_addr, 1); self.k.fence(); return self
  def wait(self): self.k.wait32(self.config.flag_addr, 1); return self
