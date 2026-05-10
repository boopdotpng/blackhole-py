import struct
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field
from asm import Kernel, Segment
from dispatch import DevMsgs, FAST_CQ_NUM_CIRCULAR_BUFFERS, LaunchMsg
from hw import L1_ALIGN, TensixL1, align_up, as_bytes

# rta and crta order
CORE_ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
# f(core_x, core_y) -> list[int]
CoreArgs = Callable[[tuple[int, int]], list[int]]

@dataclass(frozen=True)
class ProgramLayout:
  kernel_text_offsets: dict[str, int]
  launch_msg: LaunchMsg
  launch: bytes
  payload_addr: int
  payload: bytes
  rta: bytes
  crta: bytes
  kernels: dict[str, bytes]
  sem_offset: int
  local_cb_offset: int
  remote_cb_offset: int
  cb_mask: int
  enables: int

  def kernel_addr(self, role: str) -> int:
    return TensixL1.KERNEL_CONFIG_BASE + self.kernel_text_offsets[role]

def _words(xs) -> bytes:
  return b"".join(struct.pack("<I", int(x) & 0xFFFFFFFF) for x in xs)

def _flatten_segments(segments: list[Segment]) -> bytes:
  if not segments:
    return b""
  base = min(seg.addr for seg in segments)
  out = bytearray()
  for seg in sorted(segments, key=lambda s: s.addr):
    start = seg.addr - base
    end = start + len(seg.data)
    if len(out) < end:
      out.extend(b"\0" * (end - len(out)))
    out[start:end] = seg.data
  return bytes(out)

def _kernel_rtas(kernel: Kernel, core_xy: tuple[int, int] | None) -> list[int]:
  rtas: list[int] | CoreArgs = kernel.rtas
  if callable(rtas):
    if core_xy is None:
      raise ValueError("callable kernel RTAs need core_xy")
    return list(rtas(core_xy))
  return list(rtas)

def _role_map(name: str, value, roles) -> dict[str, object]:
  if value is None:
    return {}
  if isinstance(value, dict):
    unknown = sorted(set(value) - set(roles))
    if unknown:
      raise ValueError(f"unknown {name} role(s): {', '.join(unknown)}")
    return dict(value)
  if isinstance(value, (list, tuple)):
    if len(value) != len(roles):
      raise ValueError(f"{name} sequence must have {len(roles)} entries")
    return {role: item for role, item in zip(roles, value) if item is not None}
  raise TypeError(f"{name} must be a dict or {len(roles)}-item sequence")

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

@dataclass
class Program:
  brisc: Kernel
  ncrisc: Kernel
  trisc0: Kernel
  trisc1: Kernel
  trisc2: Kernel
  _: KW_ONLY
  brisc_recv: Kernel | None = None
  ncrisc_recv: Kernel | None = None
  cbs: list[object] = field(default_factory=list)
  semaphores: int = 0
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None

  def __post_init__(self):
    self.cbs = list(self.cbs)

  @classmethod
  def decode(
    cls,
    brisc: Kernel | None = None,
    ncrisc: Kernel | None = None,
    trisc0: Kernel | None = None,
    trisc1: Kernel | None = None,
    trisc2: Kernel | None = None,
    bin_file=None,
    rtas=None,
    crtas=None,
    **kw,
  ):
    kernels = {
      "brisc": brisc,
      "ncrisc": ncrisc,
      "trisc0": trisc0,
      "trisc1": trisc1,
      "trisc2": trisc2,
      "brisc_recv": kw.pop("brisc_recv", None),
      "ncrisc_recv": kw.pop("ncrisc_recv", None),
    }
    kernel_fields = (*CORE_ROLES, "brisc_recv", "ncrisc_recv")
    for role, path in _role_map("bin_file", bin_file, kernel_fields).items():
      if kernels[role] is not None:
        raise ValueError(f"cannot pass both {role} and bin_file[{role!r}]")
      kernels[role] = Kernel.decode(bin_file=path, kind=role if role in CORE_ROLES else role.removesuffix("_recv"))
    for role, values in _role_map("rtas", rtas, kernel_fields).items():
      if kernels[role] is None:
        raise ValueError(f"cannot set RTAs for missing {role} kernel")
      kernels[role].rtas = values
    for role, values in _role_map("crtas", crtas, kernel_fields).items():
      if kernels[role] is None:
        raise ValueError(f"cannot set CRTAs for missing {role} kernel")
      kernels[role].crtas = list(values)
    return cls(
      kernels["brisc"], kernels["ncrisc"], kernels["trisc0"], kernels["trisc1"], kernels["trisc2"],
      brisc_recv=kernels["brisc_recv"], ncrisc_recv=kernels["ncrisc_recv"], **kw,
    )

  @classmethod
  def encode(
    cls,
    brisc: Kernel | None = None,
    ncrisc: Kernel | None = None,
    trisc0: Kernel | None = None,
    trisc1: Kernel | None = None,
    trisc2: Kernel | None = None,
    bin_file=None,
    rtas=None,
    crtas=None,
    **kw,
  ):
    return cls.decode(brisc, ncrisc, trisc0, trisc1, trisc2, bin_file=bin_file, rtas=rtas, crtas=crtas, **kw).layout()

  @property
  def kernel_map(self) -> dict[str, Kernel]:
    return {role: getattr(self, role) for role in CORE_ROLES}

  def active_cores(self) -> list[tuple[int, int]]:
    if self.grid is None:
      raise ValueError("active_cores() needs Program.grid")
    rows, cols = self.grid
    return [(x, y) for y in rows for x in cols]

  def kernels_for_core(self, core_xy: tuple[int, int] | None = None) -> dict[str, Kernel]:
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

  def layout_for_core(
    self, *, core_xy: tuple[int, int] | None = None,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> ProgramLayout:
    selected = self.kernels_for_core(core_xy)
    kernels = {role: _flatten_segments(kernel.compile()) for role, kernel in selected.items()}
    rtas = {role: _kernel_rtas(kernel, core_xy) for role, kernel in selected.items()}
    crtas = {role: list(kernel.crtas) for role, kernel in selected.items()}
    rta_offsets = {}
    rta = b""
    for role in CORE_ROLES:
      rta_offsets[role] = len(rta)
      rta += _words(rtas[role])
    rta_total = align_up(len(rta), L1_ALIGN)
    crta_offsets = {}
    crta = b""
    for role in CORE_ROLES:
      crta_offsets[role] = rta_total + len(crta)
      crta += _words(crtas[role])
      crta = crta.ljust(align_up(len(crta), L1_ALIGN), b"\0")
    crta_total = rta_total + len(crta)
    sem_off = crta_total
    rta = rta.ljust(rta_total, b"\0") + crta
    if self.semaphores:
      rta += b"\0" * (self.semaphores * L1_ALIGN)

    local_cb_off = align_up(sem_off + self.semaphores * L1_ALIGN, L1_ALIGN)
    cb_mask, cb_blob = _build_cb_blob(self.cbs)
    remote_cb_off = local_cb_off + len(cb_blob)
    off = align_up(remote_cb_off, L1_ALIGN)

    kernel_text_offsets = {role: 0 for role in CORE_ROLES}
    enables = 0
    for idx, role in enumerate(CORE_ROLES):
      if not kernels[role]:
        continue
      kernel_text_offsets[role] = off
      off = align_up(off + len(kernels[role]), L1_ALIGN)
      enables |= 1 << idx

    if TensixL1.KERNEL_CONFIG_BASE + off > TensixL1.DATA_BUFFER_SPACE_BASE:
      raise ValueError("program config and kernel text overlap data buffer space")

    payload = bytearray(off - local_cb_off)
    payload[:len(cb_blob)] = cb_blob
    for role in CORE_ROLES:
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
    for idx, role in enumerate(CORE_ROLES):
      cfg.rta_offset[idx].rta_offset = rta_offsets[role]
      cfg.rta_offset[idx].crta_offset = crta_offsets[role] if crtas[role] else 0
      cfg.kernel_text_offset[idx] = kernel_text_offsets[role]
    cfg.host_assigned_id = host_assigned_id

    return ProgramLayout(
      kernel_text_offsets=kernel_text_offsets,
      launch_msg=launch,
      launch=as_bytes(launch),
      payload_addr=TensixL1.KERNEL_CONFIG_BASE + local_cb_off,
      payload=bytes(payload),
      rta=rta,
      crta=crta,
      kernels=kernels,
      sem_offset=sem_off,
      local_cb_offset=local_cb_off,
      remote_cb_offset=remote_cb_off,
      cb_mask=cb_mask,
      enables=enables,
    )

  def layout(self, **kw) -> ProgramLayout:
    return self.layout_for_core(**kw)

  def layouts(self, cores: list[tuple[int, int]] | None = None, **kw) -> dict[tuple[int, int], ProgramLayout]:
    if cores is None:
      cores = self.active_cores()
    return {core: self.layout_for_core(core_xy=core, **kw) for core in cores}
