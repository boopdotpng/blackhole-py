from __future__ import annotations

import ctypes
import struct
from ctypes import c_uint8 as u8, c_uint16 as u16, c_uint32 as u32
from dataclasses import dataclass, field
from enum import Enum
from asm import Kernel, Segment
from l1 import L1_ALIGN, S, TensixL1, align_up, as_bytes

Core = tuple[int, int]
Rect = tuple[int, int, int, int]


class DevMsgs:
  RUN_MSG_INIT = 0x40
  RUN_MSG_GO = 0x80
  RUN_MSG_RESET_READ_PTR_FROM_HOST = 0xE0
  RUN_MSG_DONE = 0x00
  DISPATCH_MODE_DEV = 0
  DISPATCH_MODE_HOST = 1
  ProgrammableCoreType_COUNT = 3
  MaxProcessorsPerCoreType = 5


class _RtaOffset(S):
  _pack_ = 1
  _fields_ = [("rta_offset", u16), ("crta_offset", u16)]


class _KernelConfigMsg(S):
  _pack_ = 1
  _fields_ = [
    ("kernel_config_base", u32 * DevMsgs.ProgrammableCoreType_COUNT),
    ("sem_offset", u16 * DevMsgs.ProgrammableCoreType_COUNT),
    ("local_cb_offset", u16),
    ("remote_cb_offset", u16),
    ("rta_offset", _RtaOffset * DevMsgs.MaxProcessorsPerCoreType),
    ("mode", u8),
    ("pad2", u8),
    ("kernel_text_offset", u32 * DevMsgs.MaxProcessorsPerCoreType),
    ("local_cb_mask", u32),
    ("brisc_noc_id", u8),
    ("brisc_noc_mode", u8),
    ("min_remote_cb_start_index", u8),
    ("exit_erisc_kernel", u8),
    ("host_assigned_id", u32),
    ("enables", u32),
    ("watcher_kernel_ids", u16 * DevMsgs.MaxProcessorsPerCoreType),
    ("ncrisc_kernel_size16", u16),
    ("sub_device_origin_x", u8),
    ("sub_device_origin_y", u8),
    ("pad3", u8 * 1),
    ("preload", u8),
  ]


class LaunchMsg(S):
  _pack_ = 1
  _fields_ = [("kernel_config", _KernelConfigMsg)]


class _GoMsgBits(S):
  _pack_ = 1
  _fields_ = [
    ("dispatch_message_offset", u8),
    ("master_x", u8),
    ("master_y", u8),
    ("signal", u8),
  ]


class GoMsg(ctypes.Union):
  _pack_ = 1
  _fields_ = [("all", u32), ("bits", _GoMsgBits)]


FAST_CQ_NUM_CIRCULAR_BUFFERS = 32


class Dtype(Enum):
  Float32 = 0
  Float16 = 1
  Float16_b = 5
  Int32 = 8
  UInt16 = 9
  Int8 = 14
  UInt32 = 24
  UInt8 = 30

  @property
  def bpe(self) -> int:
    return {0: 4, 1: 2, 5: 2, 8: 4, 9: 2, 14: 1, 24: 4, 30: 1}[self.value]

  @property
  def tile_size(self) -> int:
    return 32 * 32 * self.bpe


class MathFidelity(Enum):
  LoFi = 0
  HiFi2 = 2


def mcast_rects(cores: list[Core]) -> list[Rect]:
  if not cores:
    return []
  remaining = set(cores)
  rects = []
  while remaining:
    x0, y0 = min(remaining, key=lambda c: (c[1], c[0]))
    x1 = x0
    while (x1 + 1, y0) in remaining:
      x1 += 1
    y1 = y0
    while all((x, y1 + 1) in remaining for x in range(x0, x1 + 1)):
      y1 += 1
    for x in range(x0, x1 + 1):
      for y in range(y0, y1 + 1):
        remaining.discard((x, y))
    rects.append((x0, x1, y0, y1))
  return rects


@dataclass(frozen=True)
class McastWrite:
  rects: list[Rect]
  addr: int
  data: bytes


@dataclass(frozen=True)
class UnicastWrite:
  cores: list[Core]
  addr: int
  data: list[bytes]


@dataclass(frozen=True)
class Run:
  cores: list[Core]


IRCommand = McastWrite | UnicastWrite | Run

# RTA order matches launch processor slots.
CORE_ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
ROLE_INDEX = {role: i for i, role in enumerate(CORE_ROLES)}

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

def _kernel_text_layout(compiled: dict[str, list], start: int) -> tuple[dict[str, tuple[int, int]], int, int]:
  bases = {}
  enables = 0
  off = start
  for role in CORE_ROLES:
    blobs = compiled[role]
    if not blobs:
      continue
    src_base = min(blob.addr for blob in blobs)
    src_end = max(blob.addr + len(blob.data) for blob in blobs)
    bases[role] = (off, src_base)
    off = align_up(off + src_end - src_base, L1_ALIGN)
    enables |= 1 << ROLE_INDEX[role]
  return bases, off, enables

def _common_segments(per_core_segments: dict[Core, list[Segment]]) -> tuple[list[Segment], dict[Core, list[Segment]]]:
  per_core = {core: [] for core in per_core_segments}
  if not per_core_segments:
    return [], per_core

  common_keys = set.intersection(*(
    {(seg.addr, seg.data, seg.label) for seg in segments if seg.label != "rta"}
    for segments in per_core_segments.values()
  ))

  common = []
  seen = set()
  for core, segments in per_core_segments.items():
    for seg in segments:
      key = (seg.addr, seg.data, seg.label)
      if key in common_keys:
        if key not in seen:
          common.append(seg)
          seen.add(key)
      else:
        per_core[core].append(seg)
  return common, per_core

@dataclass
class Layout:
  common: list[Segment]
  per_core: dict[Core, list[Segment]]

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

  def active_cores(self) -> list[Core]:
    if self.grid is None:
      raise ValueError("active_cores() needs Program.grid")
    rows, cols = self.grid
    return [(x, y) for y in rows for x in cols]

  def kernels_for_core(self, core_xy: Core | None = None) -> dict[str, Kernel]:
    kernels = self.kernel_map
    if self.grid is None or core_xy is None:
      return kernels
    rows, cols = self.grid
    x, y = core_xy
    if x not in cols or y not in rows:
      return kernels
    if x != cols[0]:
      kernels["brisc"] = self.brisc_recv or self.brisc
    if y != rows[0]:
      kernels["ncrisc"] = self.ncrisc_recv or self.ncrisc
    return kernels

  def _build_launch(
    self, *,
    sem_off: int,
    local_cb_off: int,
    remote_cb_off: int,
    cb_mask: int,
    rta_offsets: dict[str, int],
    kernel_text_offsets: dict[str, int],
    enables: int,
    dispatch_mode: int,
    host_assigned_id: int,
  ) -> LaunchMsg:
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
    cfg.host_assigned_id = host_assigned_id
    for role in CORE_ROLES:
      idx = ROLE_INDEX[role]
      cfg.rta_offset[idx].rta_offset = rta_offsets[role]
      cfg.kernel_text_offset[idx] = kernel_text_offsets[role]
    return launch

  def _layout_core(
    self, *, core_xy: Core | None = None,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> list[Segment]:
    selected = self.kernels_for_core(core_xy)
    compiled = {role: kernel.compile() for role, kernel in selected.items()}
    if core_xy is None and any(kernel.rtas is not None for kernel in selected.values()):
      raise ValueError("kernel RTAs need core_xy")
    xy = core_xy if core_xy is not None else (0, 0)
    rtas = {role: list(kernel.rtas(*xy)) if kernel.rtas is not None else [] for role, kernel in selected.items()}

    rta_offsets, rta_blob = _layout_args(rtas)
    rta_total = align_up(len(rta_blob), L1_ALIGN)
    rta = rta_blob.ljust(rta_total, b"\0")

    sem_off = rta_total
    semaphores = b"\0" * (self.semaphores * L1_ALIGN)

    local_cb_off = align_up(sem_off + self.semaphores * L1_ALIGN, L1_ALIGN)
    cb_mask, cb_blob = _build_cb_blob(self.cbs)
    remote_cb_off = local_cb_off + len(cb_blob)

    kernel_start = align_up(remote_cb_off, L1_ALIGN)
    kernel_bases, end_off, enables = _kernel_text_layout(compiled, kernel_start)
    kernel_text_offsets = {role: kernel_bases.get(role, (0, 0))[0] for role in CORE_ROLES}

    if TensixL1.KERNEL_CONFIG_BASE + end_off > TensixL1.DATA_BUFFER_SPACE_BASE:
      raise ValueError("program config and kernel text overlap data buffer space")

    launch = self._build_launch(
      sem_off=sem_off,
      local_cb_off=local_cb_off,
      remote_cb_off=remote_cb_off,
      cb_mask=cb_mask,
      rta_offsets=rta_offsets,
      kernel_text_offsets=kernel_text_offsets,
      enables=enables,
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )

    segments = []
    if rta:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE, rta, label="rta"))
    if semaphores:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + sem_off, semaphores, label="semaphores"))
    if cb_blob:
      segments.append(Segment(TensixL1.KERNEL_CONFIG_BASE + local_cb_off, cb_blob, label="cb_config"))
    for role, (kernel_base, src_base) in kernel_bases.items():
      for blob in compiled[role]:
        label = f"{role}.{blob.label or 'kernel'}"
        addr = TensixL1.KERNEL_CONFIG_BASE + kernel_base + blob.addr - src_base
        segments.append(Segment(addr, blob.data, label=label))
    segments.append(Segment(TensixL1.LAUNCH, as_bytes(launch), label="launch"))

    return segments

  def layout(self, **kw) -> list[Segment]:
    return self._layout_core(**kw)

  def layouts(self, cores: list[Core] | None = None, **kw) -> Layout:
    if cores is None:
      cores = self.active_cores()
    per_core_segments = {core: self._layout_core(core_xy=core, **kw) for core in cores}
    common, per_core = _common_segments(per_core_segments)
    return Layout(common, per_core)

  def _target_cores(self, cores: list[Core] | None) -> list[Core]:
    if self.grid is not None:
      return self.active_cores()
    if cores is None:
      raise ValueError("Program.lower() needs cores when Program.grid is unset")
    return list(cores)

  def lower(
    self, cores: list[Core] | None = None, *,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> list[IRCommand]:
    target_cores = self._target_cores(cores)
    per_core_segments = {
      core: self._layout_core(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
      for core in target_cores
    }

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands: list[IRCommand] = [
      McastWrite(mcast_rects(target_cores), TensixL1.GO_MSG, reset_blob),
      McastWrite(mcast_rects(target_cores), TensixL1.GO_MSG_INDEX, b"\0\0\0\0"),
    ]

    rta_blobs = []
    for core in target_cores:
      rta = next((seg.data for seg in per_core_segments[core] if seg.label == "rta"), b"")
      rta_blobs.append(rta)
    if any(rta_blobs):
      rta_size = max(len(blob) for blob in rta_blobs)
      rta_blobs = [blob.ljust(rta_size, b"\0") for blob in rta_blobs]
      commands.append(UnicastWrite(target_cores, TensixL1.KERNEL_CONFIG_BASE, rta_blobs))

    shared_by_segment: dict[tuple[int, bytes, str], list[Core]] = {}
    for core, segments in per_core_segments.items():
      for seg in segments:
        if seg.label == "rta":
          continue
        shared_by_segment.setdefault((seg.addr, seg.data, seg.label), []).append(core)

    for (addr, data, _), segment_cores in shared_by_segment.items():
      commands.append(McastWrite(mcast_rects(segment_cores), addr, data))

    commands.append(Run(target_cores))
    return commands
