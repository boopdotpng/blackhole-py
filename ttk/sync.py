class Barrier:
  def __init__(self, kernel, config, party): self.k, self.config, self.party = kernel, config, party

  def wait(self):
    self.k.store(self.config.addr + self.party * 4, 1); self.k.fence()
    for party in range(self.config.parties):
      if party != self.party: self.k.wait32(self.config.addr + party * 4, 1)
    return self
