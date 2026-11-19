# Run a program on ERISC1 of one Ethernet tile, leaving ERISC0 (vendor base firmware) and the link alone.
# Before E1 leaves reset, the KMD is told to put it back in reset when our fd closes, so a crash or kill -9
# can't leave our code running on the card.
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fw
from system import PCIIface, ioctl

ETH_X = [1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10]  # channel -> NoC0 x, y = 1
SOFT_RESET, ERISC0_RESET, ERISC1_RESET = 0xFFB121B0, 1 << 11, 1 << 12
ERISC1_RESET_PC = 0xFFB14008
CODE, CODE_SIZE = 0x20000, 0x8000
HERE = os.path.dirname(os.path.abspath(__file__))

def build(src:str) -> bytes:
  return fw.compile([os.path.join(HERE, src)], (CODE, CODE_SIZE), ["-Os", "-I", fw.HERE.as_posix()])

class E1:
  def __init__(self, dev:PCIIface, ch:int):
    self.dev, self.core = dev, (ETH_X[ch], 1)
    rst = dev.read32(self.core, SOFT_RESET)
    if rst & ERISC0_RESET: raise RuntimeError(f"ch {ch}: ERISC0 is in reset, no base firmware here")
    if not rst & ERISC1_RESET: raise RuntimeError(f"ch {ch}: ERISC1 already out of reset ({rst:#x}); someone else owns it")
    self.held = rst  # the value that parks E1 and leaves E0 running

  def start(self, image:bytes):
    d, c = self.dev, self.core
    d.write(c, CODE, image)
    assert d.read(c, CODE, len(image)) == image, "E1 image readback mismatch"
    d.write32(c, ERISC1_RESET_PC, CODE)
    # SET_NOC_CLEANUP: on fd close the KMD writes `held` to SOFT_RESET, putting E1 back in reset
    ioctl(d.fd, 14, "IIBBBBIQQ", 32, 0, 1, c[0], c[1], 0, 0, SOFT_RESET, self.held)
    d.write32(c, SOFT_RESET, self.held & ~ERISC1_RESET)

  def stop(self):
    self.dev.write32(self.core, SOFT_RESET, self.held)
    ioctl(self.dev.fd, 14, "IIBBBBIQQ", 32, 0, 0, 0, 0, 0, 0, 0, 0)
