from __future__ import annotations
import ctypes
import struct
from ctypes import c_uint8 as u8, c_uint16 as u16, c_uint32 as u32
from dataclasses import dataclass, field
from enum import Enum
from asm import KernelBase, Segment, boot_jal
from ttk.addrs import L1_ALIGN, S, align_up, as_bytes
from ttk.cb import CB as CBRegs
from ttk.tensix import Launch, Mailbox, TensixL1, TensixMMIO

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
  Bfp4_b = 7
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
    if self is Dtype.Bfp4_b:
      return (128 * 4) + (16 * 4)
    return 32 * 32 * self.bpe

class MathFidelity(Enum):
  LoFi = 0
  HiFi2 = 2

def mcast_rects(cores: list[Core]) -> list[Rect]:
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

@dataclass(frozen=True)
class McastMmioWrite32:
  rects: list[Rect]
  addr: int
  value: int

@dataclass(frozen=True)
class PollL1Byte:
  core: Core
  addr: int
  value: int
  timeout_s: float

IRCommand = McastWrite | UnicastWrite | Run | McastMmioWrite32 | PollL1Byte

# RTA order matches launch processor slots.
ROLE_INDEX = {"brisc": 0, "ncrisc": 1, "trisc0": 2, "trisc1": 3, "trisc2": 4}

Kernel = KernelBase

def _kernel_entry(kernel: Kernel) -> int:
  segments = kernel.compile()
  return min((seg.addr for seg in segments if seg.data), default=kernel.base)

def lower_firmware_boot(firmware: dict[str, Kernel], all_cores: list[Core], harvested_dram_bank: int | None) -> list[IRCommand]:
  rects = mcast_rects(all_cores)
  go_init = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_INIT)
  entry = {role: _kernel_entry(firmware[role]) for role in ROLE_INDEX}

  commands: list[IRCommand] = [
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL),
  ]
  for role in ROLE_INDEX:
    for segment in firmware[role].compile(): commands.append(McastWrite(rects, segment.addr, segment.data))

  commands.extend([
    McastWrite(rects, 0, boot_jal(entry["brisc"])),
    McastWrite(rects, TensixL1.GO_MSG, go_init),
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, entry["ncrisc"]),
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, entry["trisc0"]),
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, entry["trisc1"]),
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, entry["trisc2"]),
    McastMmioWrite32(rects, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN),
    PollL1Byte(all_cores[0], TensixL1.GO_MSG + 3, DevMsgs.RUN_MSG_DONE, 2.0),
  ])
  return commands

def _args_blob(values) -> bytes:
  return b"".join((int(x) & 0xFFFFFFFF).to_bytes(4, "little") for x in values)

def _build_cb_blob(cbs: list[tuple[int, int, int]]) -> tuple[int, bytes]:
  if not cbs:
    return 0, b""
  mask = 0
  for index, _, _ in cbs:
    mask |= 1 << index
  arr = bytearray(mask.bit_length() * 16)
  addr = TensixL1.DATA_BUFFER_SPACE_BASE
  shared_addr: dict[int, int] = {}
  shared_extent: dict[int, int] = {}
  for index, page_size, tiles in cbs:
    share_with = {16: 24, 24: 16}.get(index)
    if share_with is not None and share_with in shared_addr:
      cb_addr = shared_addr[share_with]
      needed = max(shared_extent[share_with], page_size * tiles)
      addr += needed - shared_extent[share_with]
      shared_extent[share_with] = needed
    else:
      cb_addr = addr
      addr += page_size * tiles
    shared_addr[index] = cb_addr
    shared_extent[index] = page_size * tiles if share_with is None else shared_extent.get(share_with, page_size * tiles)
    struct.pack_into("<IIII", arr, index * 16, cb_addr, page_size * tiles, tiles, page_size)
  return mask, bytes(arr)

def _shared_segment_groups(per_core_segments: dict[Core, list[Segment]]) -> dict[tuple[int, bytes, str], list[Core]]:
  groups: dict[tuple[int, bytes, str], list[Core]] = {}
  for core, segments in per_core_segments.items():
    for seg in segments:
      if seg.label == "rta":
        continue
      groups.setdefault((seg.addr, seg.data, seg.label), []).append(core)
  return groups

@dataclass
class Program:
  brisc: Kernel
  ncrisc: Kernel
  trisc0: Kernel
  trisc1: Kernel
  trisc2: Kernel
  brisc_recv: Kernel | None = None
  ncrisc_recv: Kernel | None = None
  cbs: list[tuple[int, int, int]] = field(default_factory=list)  # (cb_index, page_size, tiles)
  semaphores: int = 0
  num_cores: int | None = None
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None
  core_order: tuple[Core, ...] | None = None
  brisc_sender_cores: tuple[Core, ...] | None = None
  ncrisc_sender_cores: tuple[Core, ...] | None = None

  def __post_init__(self):
    self.cbs = list(self.cbs)
    if self.num_cores is not None and self.num_cores <= 0:
      raise ValueError("Program.num_cores must be positive")
    if self.num_cores is not None and self.grid is not None:
      raise ValueError("Program cannot set both num_cores and grid")
    if self.num_cores is not None and self.core_order is not None:
      raise ValueError("Program cannot set both num_cores and core_order")

  @property
  def kernel_map(self) -> dict[str, Kernel]:
    return {role: getattr(self, role) for role in ROLE_INDEX}

  def grid_cores(self) -> list[Core]:
    if self.core_order is not None:
      return list(self.core_order)
    if self.grid is None:
      raise ValueError("grid_cores() needs Program.grid")
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
    if self.brisc_sender_cores is not None:
      brisc_sender = core_xy in set(self.brisc_sender_cores)
    else:
      brisc_sender = x == cols[0]
    if self.ncrisc_sender_cores is not None:
      ncrisc_sender = core_xy in set(self.ncrisc_sender_cores)
    else:
      ncrisc_sender = y == rows[0]
    if not brisc_sender:
      kernels["brisc"] = self.brisc_recv or self.brisc
    if not ncrisc_sender:
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
    for role, idx in ROLE_INDEX.items():
      cfg.rta_offset[idx].rta_offset = rta_offsets[role]
      cfg.rta_offset[idx].crta_offset = local_cb_off
      cfg.kernel_text_offset[idx] = kernel_text_offsets[role]
    return launch

  def _layout_core(
    self, *, core_xy: Core | None = None,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
    compiled_cache: dict[int, list[Segment]] | None = None,
  ) -> list[Segment]:
    selected = self.kernels_for_core(core_xy)
    compiled_cache = compiled_cache if compiled_cache is not None else {}
    compiled = {}
    for role, kernel in selected.items():
      key = id(kernel)
      if key not in compiled_cache:
        compiled_cache[key] = kernel.compile()
      compiled[role] = compiled_cache[key]
    if core_xy is None and any(kernel.rtas is not None for kernel in selected.values()):
      raise ValueError("kernel RTAs need core_xy")
    xy = core_xy if core_xy is not None else (0, 0)

    rta_offsets = {}
    rta_blob = b""
    for role in ROLE_INDEX:
      rta_offsets[role] = len(rta_blob)
      kernel = selected[role]
      rta_blob += _args_blob(kernel.rtas(*xy) if kernel.rtas is not None else [])
    rta_total = align_up(len(rta_blob), L1_ALIGN)
    rta = rta_blob.ljust(rta_total, b"\0")

    sem_off = rta_total
    semaphores = b"\0" * (self.semaphores * L1_ALIGN)
    local_cb_off = align_up(sem_off + self.semaphores * L1_ALIGN, L1_ALIGN)

    cb_mask, cb_blob = _build_cb_blob(self.cbs)
    remote_cb_off = local_cb_off + len(cb_blob)
    off = align_up(remote_cb_off, L1_ALIGN)

    enables = 0
    kernel_text_offsets = {role: 0 for role in ROLE_INDEX}
    kernel_segments = []
    for role, idx in ROLE_INDEX.items():
      blobs = compiled[role]
      if not blobs:
        continue
      src_base = min(blob.addr for blob in blobs)
      src_end = max(blob.addr + len(blob.data) for blob in blobs)
      kernel_text_offsets[role] = off
      enables |= 1 << idx
      for blob in blobs:
        addr = TensixL1.KERNEL_CONFIG_BASE + off + blob.addr - src_base
        label = f"{role}.{blob.label or 'kernel'}"
        kernel_segments.append(Segment(addr, blob.data, label=label))
      off = align_up(off + src_end - src_base, L1_ALIGN)

    if TensixL1.KERNEL_CONFIG_BASE + off > TensixL1.DATA_BUFFER_SPACE_BASE:
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
      for cb_index, _page_size, _tiles in self.cbs:
        sync_off = cb_index * CBRegs.SYNC_STRIDE
        segments.append(Segment(CBRegs.SYNC_TILES_RECEIVED_BASE + sync_off, b"\0\0\0\0", label=f"cb{cb_index}.received"))
        segments.append(Segment(CBRegs.SYNC_TILES_ACKED_BASE + sync_off, b"\0\0\0\0", label=f"cb{cb_index}.acked"))
    segments.extend(kernel_segments)
    segments.append(Segment(TensixL1.LAUNCH, as_bytes(launch), label="launch"))

    return segments

  def layout(self, **kw) -> list[Segment]:
    return self._layout_core(**kw)

  def _target_cores(self, cores: list[Core] | None) -> list[Core]:
    if self.core_order is not None:
      return list(self.core_order)
    if self.grid is not None:
      return self.grid_cores()
    if cores is None:
      raise ValueError("Program.lower() needs cores when Program.grid is unset")
    ordered = list(cores)
    if self.num_cores is None:
      return ordered
    if self.num_cores > len(ordered):
      raise ValueError(f"Program requested {self.num_cores} cores, only {len(ordered)} available")
    return ordered[:self.num_cores]

  def lower(
    self, cores: list[Core] | None = None, *,
    dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0,
  ) -> list[IRCommand]:
    target_cores = self._target_cores(cores)
    compiled_cache: dict[int, list[Segment]] = {}
    per_core_segments = {
      core: self._layout_core(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
      for core in target_cores
    }

    commands: list[IRCommand] = []
    if dispatch_mode != DevMsgs.DISPATCH_MODE_DEV:
      reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
      commands.extend([
        McastWrite(mcast_rects(target_cores), TensixL1.GO_MSG, reset_blob),
        McastWrite(mcast_rects(target_cores), TensixL1.GO_MSG_INDEX, b"\0\0\0\0"),
      ])
    else:
      commands.append(McastWrite(mcast_rects(target_cores), Mailbox.LAUNCH_MSG_RD_PTR, struct.pack("<I", host_assigned_id & 7)))

    rta_blobs = [
      next((seg.data for seg in per_core_segments[core] if seg.label == "rta"), b"")
      for core in target_cores
    ]
    if any(rta_blobs):
      commands.append(UnicastWrite(target_cores, TensixL1.KERNEL_CONFIG_BASE, rta_blobs))

    launch_blobs = [
      next(seg.data for seg in per_core_segments[core] if seg.label == "launch")
      for core in target_cores
    ]
    launch_addr = TensixL1.LAUNCH + (host_assigned_id & 7) * Launch.MSG_SIZE
    if all(blob == launch_blobs[0] for blob in launch_blobs):
      commands.append(McastWrite(mcast_rects(target_cores), launch_addr, launch_blobs[0]))
    else:
      commands.append(UnicastWrite(target_cores, launch_addr, launch_blobs))

    for (addr, data, label), segment_cores in _shared_segment_groups(per_core_segments).items():
      if label == "launch":
        continue
      if addr >= 0xFF000000 and len(data) == 4:
        commands.append(McastMmioWrite32(mcast_rects(segment_cores), addr, struct.unpack("<I", data)[0]))
      else:
        commands.append(McastWrite(mcast_rects(segment_cores), addr, data))

    commands.append(Run(target_cores))
    return commands
