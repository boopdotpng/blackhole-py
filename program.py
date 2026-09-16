"""Raw per-core worker images and their command-queue launch records.

No tensor layouts, graph lowering, or hardware access belong here.
"""

from struct import Struct

from cq import MAX_WRITE_SIZE, McastWrite, Run, UnicastWrite, rectangles
from firmware.consts import Firmware, KERNEL_ROLES, TensixL1
from ttko.isa import R, RV32

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
    entries = b''.join(address.to_bytes(4, 'little') for address in TensixL1.WORKER_TEXT_BASE.values())
    commands = list(_writes(cores, TensixL1.WORKER_ENTRY_BASE, entries))
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
        raise ValueError(f"raw parameter table has more than {TensixL1.PARAM_SLOTS} words")
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


class GridProgram:
  """One resident binary and entry table, common params, runtime (ri, ci).

  Physical row/column lists describe placement, including harvested gaps.
  The launcher supplies identity as data; compilation never sees a core rank.
  """
  def __init__(self, sources, *, rows, cols):
    self.rows, self.cols = tuple(rows), tuple(cols)
    if not self.rows or not self.cols or len(set(self.rows)) != len(self.rows) or len(set(self.cols)) != len(self.cols):
      raise ValueError('grid axes must be nonempty and unique')
    if any(type(v) is not int or not 0 <= v < 64 for v in (*self.rows, *self.cols)):
      raise ValueError('grid coordinates must be integers in [0, 63]')
    if set(sources) != set(KERNEL_ROLES):
      raise ValueError('a grid program requires one image per controller')
    self.global_size = (len(self.rows), len(self.cols))
    self.cores = tuple((x, y) for y in self.rows for x in self.cols)
    self.entries = {role: sources[role][0] for role in KERNEL_ROLES}
    pieces = sorted((base, bytes(image)) for base, image in sources.values())
    if any(type(base) is not int or base < TensixL1.KERNEL_CACHE_BASE or base + len(image) > TensixL1.KERNEL_CACHE_END
           for base, image in pieces):
      raise ValueError('grid binary is outside the resident kernel arena')
    self.base = pieces[0][0]
    end = self.base
    binary = bytearray()
    for base, image in pieces:
      if base % 4 or not image or len(image) % 4 or base < end:
        raise ValueError('grid images must be aligned, nonempty, and non-overlapping')
      binary.extend(bytes(base - end)); binary.extend(image)
      end = base + len(image)
    self.binary = bytes(binary)

  def commands(self, *, params=(), l1=None):
    words = tuple(params)
    if len(words) > TensixL1.PARAM_SLOTS or any(type(v) is not int or not 0 <= v < 1 << 32 for v in words):
      raise ValueError('grid parameters must fit the common u32 launch table')
    commands = list(_writes(self.cores, self.base, self.binary))
    entries = b''.join(address.to_bytes(4, 'little') for address in self.entries.values())
    commands.extend(_writes(self.cores, TensixL1.WORKER_ENTRY_BASE, entries))
    commands.extend(_writes(self.cores, TensixL1.PARAM_BASE,
                            PARAM_STRUCT.pack(*(words + (0,) * (TensixL1.PARAM_SLOTS - len(words))))))
    ranks = tuple(Struct('<2I').pack(ri, ci) for ri in range(len(self.rows)) for ci in range(len(self.cols)))
    commands.append(UnicastWrite(self.cores, TensixL1.GRID_RANK_BASE, ranks))
    for address, data in ({} if l1 is None else dict(l1)).items():
      data = bytes(data)
      if not data or address < 0 or address + len(data) > TensixL1.SIZE:
        raise ValueError('invalid grid L1 initialization')
      commands.extend(_writes(self.cores, address, data))
    return (*commands, Run(self.cores))
