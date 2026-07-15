from dataclasses import dataclass

from cq import UnicastWrite


@dataclass(frozen=True)
class RiscBarrier:
  """A reusable phase barrier for independently running worker RISCs."""

  addr: int
  participants: int

  def __post_init__(self):
    if type(self.addr) is not int or self.addr < 0 or self.addr & 3:
      raise ValueError("barrier address must be a nonnegative aligned integer")
    if type(self.participants) is not int or self.participants <= 0:
      raise ValueError("barrier participants must be positive")

  def reset(self, cores, phases: int = 1):
    """Return a launch command that clears every phase before the RISCs run."""
    if type(phases) is not int or phases <= 0: raise ValueError("barrier phases must be positive")
    cores = tuple(cores)
    zeros = bytes(phases * self.participants * 4)
    return UnicastWrite(cores, self.addr, (zeros,) * len(cores))

  def arrive(self, kernel, index: int, phase: int):
    if not 0 <= index < self.participants: raise ValueError("barrier participant index is out of range")
    if type(phase) is not int or phase <= 0: raise ValueError("barrier phase must be positive")
    phase_addr = self.addr + (phase - 1) * self.participants * 4
    kernel.write32(phase_addr + index * 4, phase); kernel.fence()
    for peer in range(self.participants): kernel.wait32(phase_addr + peer * 4, phase)
    return kernel
