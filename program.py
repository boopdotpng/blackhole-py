from __future__ import annotations

import struct
from dataclasses import dataclass, field
from asm import Kernel
from dispatch import DevMsgs, FAST_CQ_NUM_CIRCULAR_BUFFERS, LaunchMsg
from hw import L1_ALIGN, TensixL1, align_up, as_bytes

@dataclass(frozen=True)
class Segment:
  addr: int
  data: bytes
  label: str = ""

# rta and crta order
CORE_ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")

def _args_blob(values) -> bytes:
  return b"".join((int(x) & 0xFFFFFFFF).to_bytes(4, "little") for x in values)

def _layout_args(args_by_role: dict[str, list[int]], base: int = 0, align_each: bool = False) -> tuple[dict[str, int], bytes]:
  offsets = {}
  blob = b""
  for role in CORE_ROLES:
    offsets[role] = base + len(blob)
    blob += _args_blob(args_by_role[role])
    if align_each:
      blob = blob.ljust(align_up(len(blob), L1_ALIGN), b"\0")
  return offsets, blob

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
class Layout:
  common: list[Segment]
  per_core: dict[tuple[int, int], list[Segment]]

@dataclass
class Program:
  brisc: Kernel
  ncrisc: Kernel
  trisc0: Kernel
  trisc1: Kernel
  trisc2: Kernel
  brisc_recv: Kernel | None = None
  ncrisc_recv: Kernel | None = None
  cbs: list[object] = field(default_factory=list)
  semaphores: int = 0
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None

  def __post_init__(self):
    self.cbs = list(self.cbs)

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

  def _layout_core(
    self, *, core_xy: tuple[int, int] | None = None,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> list[Segment]:
    selected = self.kernels_for_core(core_xy)
    kernels = {role: kernel.compile() for role, kernel in selected.items()}
    if core_xy is None and any(kernel.rtas is not None for kernel in selected.values()):
      raise ValueError("kernel RTAs need core_xy")
    xy = core_xy if core_xy is not None else (0, 0)
    rtas = {role: list(kernel.rtas(*xy)) if kernel.rtas is not None else [] for role, kernel in selected.items()}
    crtas = {role: list(kernel.crtas) for role, kernel in selected.items()}
    rta_offsets, rta_blob = _layout_args(rtas)
    rta_total = align_up(len(rta_blob), L1_ALIGN)
    crta_offsets, crta = _layout_args(crtas, base=rta_total, align_each=True)
    crta_total = rta_total + len(crta)
    sem_off = crta_total
    rta = rta_blob.ljust(rta_total, b"\0")
    semaphores = b"\0" * (self.semaphores * L1_ALIGN)

    local_cb_off = align_up(sem_off + self.semaphores * L1_ALIGN, L1_ALIGN)
    cb_mask, cb_blob = _build_cb_blob(self.cbs)
    remote_cb_off = local_cb_off + len(cb_blob)
    off = align_up(remote_cb_off, L1_ALIGN)

    kernel_text_offsets = {role: 0 for role in CORE_ROLES}
    kernel_bases = {}
    enables = 0
    for idx, role in enumerate(CORE_ROLES):
      if not kernels[role]:
        continue
      seg_base = min(seg.addr for seg in kernels[role])
      seg_end = max(seg.addr + len(seg.data) for seg in kernels[role])
      kernel_text_offsets[role] = off
      kernel_bases[role] = (off, seg_base)
      off = align_up(off + seg_end - seg_base, L1_ALIGN)
      enables |= 1 << idx

    if TensixL1.KERNEL_CONFIG_BASE + off > TensixL1.DATA_BUFFER_SPACE_BASE:
      raise ValueError("program config and kernel text overlap data buffer space")

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

    segments = []
    if rta:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE, rta, label="rta"))
    if crta:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + rta_total, crta, label="crta"))
    if semaphores:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + sem_off, semaphores, label="semaphores"))
    if cb_blob:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + local_cb_off, cb_blob, label="cb_config"))
    for role in CORE_ROLES:
      if role not in kernel_bases:
        continue
      kernel_base, seg_base = kernel_bases[role]
      for seg in kernels[role]:
        label = f"{role}.{seg.label or 'kernel'}"
        segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + kernel_base + seg.addr - seg_base, seg.data, label=label))
    segments.append(Segment(TensixL1.LAUNCH, as_bytes(launch), label="launch"))

    return segments

  def layout(self, **kw) -> list[Segment]:
    return self._layout_core(**kw)

  def layouts(self, cores: list[tuple[int, int]] | None = None, **kw) -> Layout:
    if cores is None:
      cores = self.active_cores()
    per_core_segments = {core: self._layout_core(core_xy=core, **kw) for core in cores}
    common: list[Segment] = []
    per_core: dict[tuple[int, int], list[Segment]] = {core: [] for core in cores}
    common_keys = set.intersection(
      *({(seg.addr, seg.data, seg.label) for seg in segments if seg.label != "rta"} for segments in per_core_segments.values())
    ) if per_core_segments else set()

    seen_common = set()
    for core in cores:
      for seg in per_core_segments[core]:
        key = (seg.addr, seg.data, seg.label)
        if key in common_keys:
          if key not in seen_common:
            common.append(seg)
            seen_common.add(key)
        else:
          per_core[core].append(seg)

    return Layout(common, per_core)
