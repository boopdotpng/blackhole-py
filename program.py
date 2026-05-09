import struct
from dataclasses import dataclass, field
from typing import Any
from asm import Kernel
from dispatch import DevMsgs, FAST_CQ_NUM_CIRCULAR_BUFFERS, LaunchMsg
from hw import L1_ALIGN, TensixL1, align_up, as_bytes

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
ROLE_INDEX = {name: idx for idx, name in enumerate(ROLES)}

def _words(xs) -> bytes:
  return b"".join(struct.pack("<I", int(x) & 0xFFFFFFFF) for x in xs)

def _kernel_bytes(kernel) -> bytes:
  if kernel is None:
    return b""
  if isinstance(kernel, Kernel):
    loads = kernel.pt_loads()
    if len(loads) == 1:
      return loads[0]["data"]
    executable = [seg for seg in loads if "X" in seg.get("perms", "")]
    if len(executable) == 1:
      return executable[0]["data"]
    raise ValueError("kernel has multiple load segments; pass the flat text bytes")
  if hasattr(kernel, "xip"):
    return bytes(kernel.xip)
  return bytes(kernel)

def _kernel_rtas(kernel, core_idx: int, core_xy: tuple[int, int] | None, num_cores: int) -> list[int]:
  rtas = getattr(kernel, "rtas", [])
  if callable(rtas):
    if core_xy is None:
      raise ValueError("callable kernel RTAs need core_xy")
    return list(rtas(core_idx, core_xy, num_cores))
  return list(rtas)

def _cb_fields(cb) -> tuple[int, int, int]:
  if hasattr(cb, "index"):
    page_size = cb.dtype.tile_size if hasattr(cb, "dtype") else cb.page_size
    return cb.index, page_size, cb.tiles
  return cb

def _build_cb_blob(cbs) -> tuple[int, bytes]:
  if not cbs:
    return 0, b""
  fields = [_cb_fields(cb) for cb in cbs]
  mask = 0
  for index, _, _ in fields:
    mask |= 1 << index
  arr = bytearray(mask.bit_length() * 16)
  addr = TensixL1.DATA_BUFFER_SPACE_BASE
  shared_addr: dict[int, int] = {}
  for index, page_size, tiles in fields:
    share_with = {16: 24, 24: 16}.get(index)
    if share_with is not None and share_with in shared_addr:
      cb_addr = shared_addr[share_with]
    else:
      cb_addr = addr
      addr += page_size * tiles
    shared_addr[index] = cb_addr
    struct.pack_into("<IIII", arr, index * 16, cb_addr, page_size * tiles, tiles, page_size)
  return mask, bytes(arr)

@dataclass(frozen=True)
class EncodedProgram:
  kernel_text_offsets: dict[str, int]
  launch_msg: LaunchMsg
  launch: bytes
  payload_addr: int
  payload: bytes
  rta: bytes
  kernels: dict[str, bytes]
  sem_offset: int
  local_cb_offset: int
  remote_cb_offset: int
  cb_mask: int
  enables: int

  def kernel_addr(self, role: str) -> int:
    return TensixL1.KERNEL_CONFIG_BASE + self.kernel_text_offsets[role]

  def writes(self) -> list[tuple[int, bytes]]:
    out = []
    if self.rta:
      out.append((TensixL1.KERNEL_CONFIG_BASE, self.rta))
    out.append((self.payload_addr, self.payload))
    out.append((TensixL1.LAUNCH, self.launch))
    return out

@dataclass
class Program:
  # Program owns the multi-core launch contract: five per-core Kernel images,
  # CB config, launch offsets, and L1 upload layout. Kernel owns its own RTA
  # values because those are part of the per-core kernel ABI. Program decides
  # where those RTAs live and writes the matching firmware launch offsets.
  brisc: Any = None
  ncrisc: Any = None
  trisc0: Any = None
  trisc1: Any = None
  trisc2: Any = None
  brisc_recv: Any = None
  ncrisc_recv: Any = None
  cbs: list[Any] = field(default_factory=list)
  semaphores: int = 0
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None

  @classmethod
  def decode(cls, brisc=None, ncrisc=None, trisc0=None, trisc1=None, trisc2=None, **kw):
    return cls(brisc, ncrisc, trisc0, trisc1, trisc2, **kw)

  @classmethod
  def encode(cls, brisc=None, ncrisc=None, trisc0=None, trisc1=None, trisc2=None, **kw) -> EncodedProgram:
    return cls.decode(brisc, ncrisc, trisc0, trisc1, trisc2, **kw).layout()

  @property
  def kernel_map(self) -> dict[str, Any]:
    return {role: getattr(self, role) for role in ROLES}

  def active_cores(self) -> list[tuple[int, int]]:
    if self.grid is None:
      raise ValueError("active_cores() needs Program.grid")
    rows, cols = self.grid
    return [(x, y) for y in rows for x in cols]

  def kernels_for_core(self, core_xy: tuple[int, int] | None = None) -> dict[str, Any]:
    out = self.kernel_map
    if self.grid is None or core_xy is None:
      return out
    rows, cols = self.grid
    x, y = core_xy
    if x not in cols or y not in rows:
      return out
    if x != cols[0]:
      out["brisc"] = self.brisc_recv if self.brisc_recv is not None else self.brisc
    if y != rows[0]:
      out["ncrisc"] = self.ncrisc_recv if self.ncrisc_recv is not None else self.ncrisc
    return out

  def layout(
    self, *, core_idx=0, core_xy: tuple[int, int] | None = None, num_cores=1,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> EncodedProgram:
    selected = self.kernels_for_core(core_xy)
    kernels = {role: _kernel_bytes(kernel) for role, kernel in selected.items()}
    rtas = {role: _kernel_rtas(kernel, core_idx, core_xy, num_cores) for role, kernel in selected.items()}
    rta_offsets = {}
    rta = b""
    for role in ROLES:
      rta_offsets[role] = len(rta)
      rta += _words(rtas[role])
    rta_total = align_up(len(rta), L1_ALIGN)
    sem_off = rta_total
    if self.semaphores:
      rta = rta.ljust(sem_off, b"\0") + b"\0" * (self.semaphores * L1_ALIGN)

    local_cb_off = align_up(sem_off + self.semaphores * L1_ALIGN, L1_ALIGN)
    cb_mask, cb_blob = _build_cb_blob(self.cbs)
    remote_cb_off = local_cb_off + len(cb_blob)
    off = align_up(remote_cb_off, L1_ALIGN)

    kernel_text_offsets = {role: 0 for role in ROLES}
    enables = 0
    for role in ROLES:
      if not kernels[role]:
        continue
      kernel_text_offsets[role] = off
      off = align_up(off + len(kernels[role]), L1_ALIGN)
      enables |= 1 << ROLE_INDEX[role]

    if TensixL1.KERNEL_CONFIG_BASE + off > TensixL1.DATA_BUFFER_SPACE_BASE:
      raise ValueError("program config and kernel text overlap data buffer space")

    payload = bytearray(off - local_cb_off)
    payload[:len(cb_blob)] = cb_blob
    for role in ROLES:
      if kernels[role]:
        dst = kernel_text_offsets[role] - local_cb_off
        payload[dst:dst + len(kernels[role])] = kernels[role]

    launch = LaunchMsg()
    cfg = launch.kernel_config
    for i in range(DevMsgs.ProgrammableCoreType_COUNT):
      cfg.kernel_config_base[i] = TensixL1.KERNEL_CONFIG_BASE
      cfg.sem_offset[i] = sem_off
    cfg.local_cb_offset = local_cb_off
    cfg.remote_cb_offset = remote_cb_off
    cfg.local_cb_mask = cb_mask
    cfg.min_remote_cb_start_index = FAST_CQ_NUM_CIRCULAR_BUFFERS
    cfg.enables = enables
    cfg.brisc_noc_id = 1
    cfg.brisc_noc_mode = 0
    cfg.mode = dispatch_mode
    for role in ROLES:
      idx = ROLE_INDEX[role]
      cfg.rta_offset[idx].rta_offset = rta_offsets[role]
      cfg.rta_offset[idx].crta_offset = 0
      cfg.kernel_text_offset[idx] = kernel_text_offsets[role]
    cfg.host_assigned_id = host_assigned_id

    return EncodedProgram(
      kernel_text_offsets=kernel_text_offsets,
      launch_msg=launch,
      launch=as_bytes(launch),
      payload_addr=TensixL1.KERNEL_CONFIG_BASE + local_cb_off,
      payload=bytes(payload),
      rta=rta,
      kernels=kernels,
      sem_offset=sem_off,
      local_cb_offset=local_cb_off,
      remote_cb_offset=remote_cb_off,
      cb_mask=cb_mask,
      enables=enables,
    )

  def layouts(self, cores: list[tuple[int, int]] | None = None, **kw) -> dict[tuple[int, int], EncodedProgram]:
    if cores is None:
      cores = self.active_cores()
    return {core: self.layout(core_idx=i, core_xy=core, num_cores=len(cores), **kw) for i, core in enumerate(cores)}
