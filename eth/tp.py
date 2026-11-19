"""Two-card tensor parallelism over one TT-link channel: E1 forwarders and the worker all-reduce kernel."""
import os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import fw, ttrv
from ttrv.runtime import Kernel
from e1 import E1, build

BOX, READY, FLAG, MAGIC = 0x30000, 0x30400, 0x60000, 0xE1F0A4D1


class Link:
  """E1 forwarders on channel ch of every card in devs (straight-across cabling: card r ch <-> card 1-r ch).
  Each Device's fd carries a KMD cleanup that parks its E1 when the fd closes."""
  def __init__(self, devs, ch=11):
    assert len(devs) == 2
    self.devs, self.ch, self.e1 = devs, ch, [E1(d.dev.iface, ch) for d in devs]
    image = build("e1_fwd.c")
    for d, e in zip(devs, self.e1):
      io = d.dev.iface
      for a, n in ((BOX, 0x1000), (FLAG, 0x100)): io.write(e.core, a, bytes(n))
    for d, e in zip(devs, self.e1): e.start(image)
    t = time.time()
    for d, e in zip(devs, self.e1):
      while d.dev.iface.read32(e.core, BOX) != MAGIC:
        if time.time() - t > 1: raise RuntimeError(f"E1 forwarder on ch {ch} did not start")
    self.coord = self.e1[0].core[0] | self.e1[0].core[1] << 6

  def status(self, r):
    io, c = self.devs[r].dev.iface, self.e1[r].core
    return dict(heartbeat=io.read32(c, BOX + 4), last=io.read32(c, BOX + 16), malformed=io.read32(c, BOX + 20),
                flags=[io.read32(c, FLAG), io.read32(c, FLAG + 16)])

  def close(self):
    for e in self.e1: e.stop()


def allreduce_kernel(dev, link, *, dim, rank, nslot, grid=16):
  """output = bf16((partial_0 + partial_1) + residual) on both cards. Launch with step (replay counter, >= 1)
  and slot (0 <= slot < nslot, a different one for each all-reduce in a replay)."""
  if dim % (grid * 32) or 2 * dim > 0x8000: raise ValueError(f"dim {dim} does not split into {grid} slices of 32")
  slice_ = dim // grid
  scratch = 8 * slice_ + 64
  src = "\n".join([f"grid {grid}", "param partial: bf16[]", "param residual: bf16[]", "param output: bf16[]",
                   "param step: u32", "param slot: u32", f"l1 scratch: u8[{scratch}]", "fn brisc() { }"])
  spec = ttrv.build(src)
  m = spec.manifest
  flags = ["-O2", "-march=rv32imf_zicsr_zba_zbb", f"-I{HERE}", f"-DSCRATCH_ADDR={m['storage']['scratch']['address']}",
           f"-DGRID={grid}", f"-DDIM={dim}", f"-DRANK={rank}", f"-DETH={link.coord}", f"-DNSLOT={nslot}",
           *(f"-D{n.upper()}_SLOT={m['params'][n]['slot']}" for n in ("partial", "residual", "output", "step", "slot"))]
  assert m["storage"]["scratch"]["address"] % 64 == 0
  spec.images = fw.program({"brisc": ([HERE / "allreduce.c", "noc.c"], flags)})
  return Kernel(dev, spec)


def pick_kernel(dev, link, *, rank, nslot):
  """Combine two cards' (key, token) argmax winners; writes tokens[pos + 1] and, if write_token, history[pos + 1]."""
  src = "\n".join(["grid 1", "param winner: u32[]", "param history: u32[]", "param tokens: u32[], host", "param start_pos: u32",
                   "param write_token: u32", "param step: u32", "param slot: u32", "l1 scratch: u8[256]", "fn brisc() { }"])
  spec = ttrv.build(src)
  m = spec.manifest
  flags = ["-O2", "-march=rv32im_zicsr", f"-I{HERE}", f"-DSCRATCH_ADDR={m['storage']['scratch']['address']}",
           f"-DRANK={rank}", f"-DETH={link.coord}", f"-DNSLOT={nslot}",
           *(f"-D{n.upper()}_SLOT={m['params'][n]['slot']}" for n in ("winner", "history", "tokens", "start_pos", "write_token", "step", "slot"))]
  spec.images = fw.program({"brisc": ([HERE / "pick.c", "noc.c"], flags)})
  return Kernel(dev, spec)
