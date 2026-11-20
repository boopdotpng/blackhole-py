"""Numerical result of the BF16 SFPU index-capture scan in examples/llama3/argmax.ttrv.

All role instructions and pack/unpack events still execute in the timing model. Only the 64 numerical
words handed from the packer to scalar code are supplied here. Changing any of the three Tensix programs
disables this shortcut. These signatures identify instructions, and contain no measured cycle counts.
"""

import hashlib
import struct


# SHA256 of the concatenated unpack, math and pack images. The compiled math role
# includes the literal vocab size and split. The pack/unpack images fix the CB layout.
VOCAB_BY_IMAGE = {
  "301d4e1e35b50abdec9cf9830d99acf4bb951ea3b60f0e3dd35757c1f151587e": 128256,
  "70e3e01d888740329bc416217eb11c330d0075185bebdd3524f68ba0936a82b4": 166912,
  "b22a92eaba62e9c6654dfa6e76a8683ee83adb15292609a800d8cc838854d905": 248320,
}


def scan_vocab(kernel):
  if not {"page", "candidates"} <= kernel.manifest["storage"].keys() or kernel.manifest["grid"] != 88:
    return None
  roles = ("trisc0", "trisc1", "trisc2")
  if not all(r in kernel.images for r in roles):
    return None
  return VOCAB_BY_IMAGE.get(hashlib.sha256(b"".join(kernel.images[r] for r in roles)).hexdigest())


def candidates(data, lead, count):
  # Dst datum i maps to lane (i // 2) % 32. Each lane visits its indices
  # in ascending order, keeping the first index on equal sortable keys.
  best = [(0, 0)] * 32
  for i, (bf16,) in enumerate(struct.iter_unpack("<H", data[2 * lead : 2 * (lead + count)]), start=lead):
    # The hardware scan maps both signed zeros and BF16 subnormals to positive zero.
    bits = bf16 << 16 if bf16 & 0x7F80 else 0
    key = (bits ^ (0xFFFFFFFF if bits >> 31 else 0x80000000)) >> 1
    lane = (i // 2) % 32
    if key > best[lane][0]:
      best[lane] = (key, i)
  return b"".join(struct.pack("<II", *pair) for pair in best)


class ArgmaxScan:
  def __init__(self, mem, storage, worker, vocab):
    self.mem = mem
    self.page, self.out = storage["page"]["address"], storage["candidates"]["address"]
    first, end = worker * vocab // 88, (worker + 1) * vocab // 88
    self.lead, self.count = first % 32, end - first
    self.result = None

  def unpack(self):
    if self.result is None:
      self.result = candidates(self.mem.read(self.page, 2 * (self.lead + self.count)), self.lead, self.count)

  def pack(self):
    if self.result is None:
      raise ValueError("argmax pack preceded its unpack")
    self.mem.write(self.out, self.result)
