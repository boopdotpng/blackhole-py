"""Raw per-core worker images and their command-queue launch records.

No tensor layouts, graph lowering, or hardware access belong here.
"""

from struct import Struct

from cq import MAX_WRITE_SIZE, McastWrite, Run, UnicastWrite, rectangles
from fw.consts import Firmware, KERNEL_ROLES, TensixL1
from isa import R, RV32

PARAM_STRUCT = Struct(f"<{TensixL1.PARAM_SLOTS}I")
RETURN_KERNEL = {
  role: RV32().jal(R.ZERO, Firmware.TEXT[role][0] - TensixL1.WORKER_TEXT_BASE[role]).to_bytes(4, "little")
  for role in KERNEL_ROLES
}

def _writes(cores, address, data):
  cores, rects = tuple(cores), rectangles(cores)
  for offset in range(0, len(data), MAX_WRITE_SIZE):
    chunk = data[offset:offset + MAX_WRITE_SIZE]
    yield (UnicastWrite(cores, address + offset, (chunk,)) if len(cores) == 1
           else McastWrite(rects, address + offset, chunk))


class Program:
  def __init__(self, core_images):
    self.images = {}
    for core, images in core_images.items():
      unknown = set(images) - set(KERNEL_ROLES)
      if unknown: raise ValueError(f"unknown worker roles: {sorted(unknown)}")
      self.images[core] = {**RETURN_KERNEL, **{role: bytes(image) for role, image in images.items()}}
    if not self.images: raise ValueError("a program requires at least one worker tile")
    self.cores = tuple(self.images)

  def commands(self, *, params=None, l1=None):
    core_images, cores = self.images, self.cores
    commands = []
    for role in KERNEL_ROLES:
      groups = {}
      for core, images in core_images.items():
        image = bytes(images[role])
        if not image or len(image) % 4:
          raise ValueError(f"{role} image must contain complete instructions")
        if len(image) > TensixL1.WORKER_TEXT_SIZE[role]:
          raise ValueError(f"{role} image exceeds its worker text partition")
        groups.setdefault(image, []).append(core)
      for image, image_cores in groups.items():
        commands.extend(_writes(image_cores, TensixL1.WORKER_TEXT_BASE[role], image))

    params = {} if params is None else dict(params)
    unknown_param_cores = set(params) - set(cores)
    if unknown_param_cores:
      raise ValueError("parameters were supplied for a tile outside the launch")
    tables = []
    for core in cores:
      words = tuple(params.get(core, ()))
      if len(words) > TensixL1.PARAM_SLOTS:
        raise ValueError("raw parameter table has more than 12 words")
      if any(type(word) is not int or not 0 <= word < 1 << 32 for word in words):
        raise ValueError("raw parameters must be u32 integers")
      tables.append(PARAM_STRUCT.pack(*(words + (0,) * (TensixL1.PARAM_SLOTS - len(words)))))
    commands.append(UnicastWrite(cores, TensixL1.PARAM_BASE, tuple(tables)))

    for address, data in ({} if l1 is None else dict(l1)).items():
      data = bytes(data)
      if not data:
        raise ValueError("raw L1 initialization cannot be empty")
      if not 0 <= address or address + len(data) > TensixL1.SIZE:
        raise ValueError("raw L1 initialization is outside worker L1")
      commands.extend(_writes(cores, address, data))

    commands.append(Run(cores))
    return tuple(commands)
