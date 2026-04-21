import ctypes, struct, time
from ctypes import c_uint8 as u8, c_uint16 as u16, c_uint32 as u32
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal, NamedTuple

from hw import *

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

Rect = tuple[int, int, int, int]  # (x0, x1, y0, y1)
Args = list[int]
RtArgs = Args | Callable[[int, Core, int], Args]
CoreArgs = tuple[Args, Args, Args]  # (writer, reader, compute) per core

FAST_CQ_NUM_CIRCULAR_BUFFERS = 32

class Dtype(Enum):
  Float32 = 0  # internal-only: used for f32_acc dest accumulation, not for host IO
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

@dataclass
class CBConfig:
  index: int
  dtype: Dtype
  tiles: int = 2

@dataclass
class Program:
  cores: int | Literal["all"]
  reader_kernel: str
  compute_kernel: str
  writer_kernel: str
  cbs: list[CBConfig]
  name: str = ""
  reader_args: RtArgs = field(default_factory=list)
  writer_args: RtArgs = field(default_factory=list)
  compute_args: RtArgs = field(default_factory=list)
  semaphores: int = 0
  math_fidelity: MathFidelity = MathFidelity.HiFi2
  approx: bool = False
  dst_accum_mode: bool = False
  dst_full_sync: bool = False
  reader_recv_kernel: str = ""
  writer_recv_kernel: str = ""
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None

def noc_mcast_xy(rect: Rect) -> tuple[int, int]:
  x0, x1, y0, y1 = rect
  return (y1 << 18) | (x1 << 12) | (y0 << 6) | x0, (x1 - x0 + 1) * (y1 - y0 + 1)

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

@dataclass
class Write:
  cores: list[Core]
  addr: int
  data: bytes | list[bytes]

@dataclass
class Launch:
  cores: list[Core]

IRCommand = Write | Launch

def resolve_args(args: RtArgs, core_idx: int, core_xy: Core, num_cores: int) -> Args:
  return args if isinstance(args, list) else args(core_idx, core_xy, num_cores)

def pack_rta(writer_args: Args, reader_args: Args, compute_args: Args, num_sems: int, sem_off: int) -> bytes:
  pack = lambda xs: b"".join(int(x & 0xFFFFFFFF).to_bytes(4, "little") for x in xs)
  rta = pack(writer_args) + pack(reader_args) + pack(compute_args)
  if num_sems > 0:
    if sem_off > len(rta):
      rta = rta.ljust(sem_off, b"\0")
    rta += b"\0" * (num_sems * 16)
  return rta

def build_cb_blob(program: Program) -> tuple[int, bytes]:
  if not program.cbs:
    return 0, b""
  mask = 0
  for cb in program.cbs:
    mask |= 1 << cb.index
  end = mask.bit_length()
  arr = bytearray(end * 16)
  addr = TensixL1.DATA_BUFFER_SPACE_BASE
  shared_addr: dict[int, int] = {}
  for cb in program.cbs:
    page_size = cb.dtype.tile_size
    size = page_size * cb.tiles
    share_with = {16: 24, 24: 16}.get(cb.index)
    if share_with is not None and share_with in shared_addr:
      cb_addr = shared_addr[share_with]
    else:
      cb_addr = addr
      addr += size
    shared_addr[cb.index] = cb_addr
    struct.pack_into("<IIII", arr, cb.index * 16, cb_addr, size, cb.tiles, page_size)
  return mask, bytes(arr)

class Role(NamedTuple):
  cores: list[Core]
  reader: Any  # CompiledKernel | None
  writer: Any  # CompiledKernel | None

def build_payload(
  program: Program, reader, writer, compute: tuple | None,
  rta_sizes: tuple[int, int, int], dispatch_mode: int,
  sem_off: int | None = None,
) -> tuple[int, bytes, bytes]:
  rta_offsets = [0, rta_sizes[0], rta_sizes[0] + rta_sizes[1]]
  rta_total = align_up(rta_offsets[2] + rta_sizes[2], L1_ALIGN)
  if sem_off is None:
    sem_off = rta_total
  local_cb_off = align_up(sem_off + program.semaphores * 16, L1_ALIGN)
  cb_mask, cb_blob = build_cb_blob(program)
  kernel_off = align_up(local_cb_off + len(cb_blob), L1_ALIGN)
  proc = []
  if writer is not None:
    proc.append(("brisc", writer, 0))
  if reader is not None:
    proc.append(("ncrisc", reader, 1))
  if compute is not None:
    for i, kernel in enumerate(compute):
      proc.append((f"trisc{i}", kernel, i + 2))
  enables = 0
  kernel_text_off = [0] * 5
  off = kernel_off
  for _, kernel, idx in proc:
    kernel_text_off[idx] = off
    off = align_up(off + len(kernel.xip), L1_ALIGN)
    enables |= 1 << idx
  shared = bytearray(off - local_cb_off)
  shared[0:len(cb_blob)] = cb_blob
  for _, kernel, idx in proc:
    dst = kernel_text_off[idx] - local_cb_off
    shared[dst:dst + len(kernel.xip)] = kernel.xip
  shared_addr = TensixL1.KERNEL_CONFIG_BASE + local_cb_off

  launch = LaunchMsg()
  cfg = launch.kernel_config
  for i in range(3):
    cfg.kernel_config_base[i] = TensixL1.KERNEL_CONFIG_BASE
    cfg.sem_offset[i] = sem_off
  cfg.local_cb_offset = local_cb_off
  cfg.remote_cb_offset = local_cb_off + len(cb_blob)
  cfg.local_cb_mask = cb_mask
  cfg.min_remote_cb_start_index = FAST_CQ_NUM_CIRCULAR_BUFFERS
  cfg.enables = enables
  cfg.brisc_noc_id = 1
  cfg.brisc_noc_mode = 0
  cfg.mode = dispatch_mode
  cfg.rta_offset[0].rta_offset, cfg.rta_offset[0].crta_offset = rta_offsets[0], local_cb_off
  cfg.rta_offset[1].rta_offset, cfg.rta_offset[1].crta_offset = rta_offsets[1], local_cb_off
  for i in (2, 3, 4):
    cfg.rta_offset[i].rta_offset, cfg.rta_offset[i].crta_offset = rta_offsets[2], local_cb_off
  for i, value in enumerate(kernel_text_off):
    cfg.kernel_text_offset[i] = value
  return shared_addr, bytes(shared), as_bytes(launch)

def build_ir(
  program: Program, roles: list[Role], compute: tuple | None,
  all_cores: list[Core], per_core_args: list[CoreArgs],
  dispatch_mode: int,
) -> list[IRCommand]:
  max_w = max((len(a[0]) for a in per_core_args), default=0) * 4
  max_r = max((len(a[1]) for a in per_core_args), default=0) * 4
  max_c = max((len(a[2]) for a in per_core_args), default=0) * 4
  rta_sizes = (max_w, max_r, max_c)
  sem_off = align_up(max_w + max_r + max_c, L1_ALIGN)
  rta_blobs = [pack_rta(w, r, c, program.semaphores, sem_off) for w, r, c in per_core_args]
  reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)

  commands: list[IRCommand] = [
    Write(all_cores, TensixL1.GO_MSG, reset_blob),
    Write(all_cores, TensixL1.GO_MSG_INDEX, b"\0\0\0\0"),
  ]

  # RTAs: broadcast if uniform across cores, per-core unicast otherwise
  if rta_blobs and all(b == rta_blobs[0] for b in rta_blobs):
    commands.append(Write(all_cores, TensixL1.KERNEL_CONFIG_BASE, rta_blobs[0]))
  elif rta_blobs:
    commands.append(Write(all_cores, TensixL1.KERNEL_CONFIG_BASE, rta_blobs))

  # Per-role: launch message + shared payload (CB config + kernel text)
  for role_cores, reader, writer in roles:
    shared_addr, shared_blob, launch_blob = build_payload(
      program, reader, writer, compute, rta_sizes, dispatch_mode,
      sem_off=sem_off,
    )
    commands.append(Write(role_cores, TensixL1.LAUNCH, launch_blob))
    commands.append(Write(role_cores, shared_addr, shared_blob))

  commands.append(Launch(all_cores))
  return commands

_RISC_NAMES = ["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]

def _resolve_stuck_pcs(win, x, y, dev):
  """Read PCs for the stuck core and resolve them against RVIR kernel disassembly."""
  try:
    import os
    if os.environ.get("RVIR") != "1":
      return ""
    # read kernel_config_base[0] and kernel_text_offset[0..4] from the launch msg in L1
    launch_off = TensixL1.LAUNCH
    kcb = int.from_bytes(win.mm[launch_off:launch_off+4], "little")
    kto = [int.from_bytes(win.mm[launch_off+44+i*4:launch_off+44+i*4+4], "little") for i in range(5)]

    # read PCs for this core via a separate MMIO-addressed window
    mmio_base, _ = align_down(TensixMMIO.DBG_BUS_CNTL, TLBWindow.SIZE_2M)
    cntl_off = TensixMMIO.DBG_BUS_CNTL - mmio_base
    data_off = TensixMMIO.DBG_BUS_RD_DATA - mmio_base
    with TLBWindow(dev, start=(x, y), addr=mmio_base) as dbg:
      pcs = {r: read_risc_pc(dbg, cntl_off, data_off, r) for r in _RISC_NAMES}

    from examples.add1 import _build_rvir_kernels
    tiles = int(os.environ.get("TILES", "4"))
    reader, writer, (t0, t1, t2) = _build_rvir_kernels(tiles)
    # writer_kernel=reader (brisc), reader_kernel=writer (ncrisc)
    kern_progs = {"brisc": reader, "ncrisc": writer, "trisc0": t0, "trisc1": t1, "trisc2": t2}
    kern_disasms = {}
    for name, prog in kern_progs.items():
      prog.assemble()
      kern_disasms[name] = prog.disasm()

    lines = ["\n  --- PC resolution (RVIR add1 kernels) ---"]
    for idx, risc in enumerate(_RISC_NAMES):
      pc = pcs[risc]
      lma = kcb + kto[idx]
      disasm = kern_disasms.get(risc, "")
      if not disasm or kto[idx] == 0:
        lines.append(f"  {risc}: PC=0x{pc:08x} (no kernel)")
        continue
      # check if PC is in firmware or kernel
      if pc < lma:
        lines.append(f"  {risc}: PC=0x{pc:08x} (in firmware, before kernel @ 0x{lma:x})")
        continue
      offset = pc - lma
      # find function + context in disasm
      dlines = disasm.split("\n")
      # build index: list of (addr, line_idx) for instruction lines
      insn_addrs = []
      for i, dl in enumerate(dlines):
        stripped = dl.strip()
        if ":" in stripped and not stripped.startswith("<") and not stripped.endswith(">:"):
          try:
            addr = int(stripped.split(":")[0], 16)
            insn_addrs.append((addr, i))
          except ValueError:
            pass
      # find closest instruction
      fn_name, fn_addr = "???", 0
      for i, dl in enumerate(dlines):
        if "<" in dl and ">:" in dl:
          try:
            parts = dl.strip().split()
            a = int(parts[0], 16)
            n = dl.split("<")[1].split(">")[0]
            if a <= offset:
              fn_name, fn_addr = n, a
          except (ValueError, IndexError):
            pass
      fn_off = offset - fn_addr
      # find the instruction line index closest to our offset
      best_idx = None
      for addr, lidx in insn_addrs:
        if addr == offset:
          best_idx = lidx
          break
        if addr <= offset:
          best_idx = lidx
      # show context: 3 lines above and below
      ctx = ""
      if best_idx is not None:
        start = max(0, best_idx - 3)
        end = min(len(dlines), best_idx + 4)
        for j in range(start, end):
          marker = " >>>" if j == best_idx else "    "
          ctx += f"\n      {marker} {dlines[j].rstrip()}"
      lines.append(f"  {risc}: PC=0x{pc:08x} -> {fn_name}+0x{fn_off:x}{ctx}")
    return "\n".join(lines)
  except Exception as e:
    return f"\n  (PC resolution failed: {e})"

def slow_dispatch(win, commands: list[IRCommand], dev=None, all_cores=None):
  for cmd in commands:
    match cmd:
      case Write(cores=cores, addr=addr, data=data) if isinstance(data, list):
        for core, d in zip(cores, data):
          win.target(core)
          win.write(addr, d)
      case Write(cores=cores, addr=addr, data=data):
        for x0, x1, y0, y1 in mcast_rects(cores):
          win.target((x0, y0), (x1, y1))
          win.write(addr, data)
      case Launch(cores=cores):
        go = GoMsg()
        go.bits.signal = DevMsgs.RUN_MSG_GO
        go_blob = struct.pack("<I", go.all)
        for x0, x1, y0, y1 in mcast_rects(cores):
          win.target((x0, y0), (x1, y1))
          win.mm[TensixL1.GO_MSG:TensixL1.GO_MSG + 4] = go_blob
        for x, y in cores:
          win.target((x, y))
          deadline = time.perf_counter() + 10.0
          host_sync_initial = None
          host_sync_last = None
          host_sync_first_change = None
          host_sync_change_count = 0
          while win.mm[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
            sync_sample = int.from_bytes(win.mm[0x68:0x6C], "little")
            if host_sync_initial is None:
              host_sync_initial = sync_sample
              host_sync_last = sync_sample
            elif sync_sample != host_sync_last:
              host_sync_change_count += 1
              if host_sync_first_change is None:
                host_sync_first_change = sync_sample
              host_sync_last = sync_sample
            if time.perf_counter() > deadline:
              sentinel = int.from_bytes(win.mm[0x240:0x244], "little")
              go_val = int.from_bytes(win.mm[TensixL1.GO_MSG:TensixL1.GO_MSG+4], "little")
              sync_val = int.from_bytes(win.mm[0x68:0x6C], "little")
              t0 = int.from_bytes(win.mm[0x244:0x248], "little")
              t1 = int.from_bytes(win.mm[0x248:0x24C], "little")
              t2 = int.from_bytes(win.mm[0x24C:0x250], "little")
              msg = f"timeout core ({x},{y}) brisc=0x{sentinel:x} go=0x{go_val:08x} sync=0x{sync_val:08x} t0=0x{t0:x} t1=0x{t1:x} t2=0x{t2:x}"
              # Read BRISC kernel debug sentinels from L1
              brisc_tiles_recv = int.from_bytes(win.mm[0x250:0x254], "little")
              brisc_done = int.from_bytes(win.mm[0x254:0x258], "little")
              brisc_tile_idx = int.from_bytes(win.mm[0x258:0x25C], "little")
              ncrisc_stage = int.from_bytes(win.mm[0x25C:0x260], "little")
              ncrisc_aux = int.from_bytes(win.mm[0x260:0x264], "little")
              trisc0_stage = int.from_bytes(win.mm[0x268:0x26C], "little")
              trisc0_aux = int.from_bytes(win.mm[0x26C:0x270], "little")
              trisc1_stage = int.from_bytes(win.mm[0x270:0x274], "little")
              trisc1_aux = int.from_bytes(win.mm[0x274:0x278], "little")
              trisc2_stage = int.from_bytes(win.mm[0x278:0x27C], "little")
              trisc2_aux = int.from_bytes(win.mm[0x27C:0x280], "little")
              brisc_wait_stage = int.from_bytes(win.mm[0x1E80:0x1E84], "little")
              brisc_wait_initial = int.from_bytes(win.mm[0x1E84:0x1E88], "little")
              brisc_wait_last = int.from_bytes(win.mm[0x1E88:0x1E8C], "little")
              brisc_wait_first_change = int.from_bytes(win.mm[0x1E8C:0x1E90], "little")
              brisc_wait_reads = int.from_bytes(win.mm[0x1E90:0x1E94], "little")
              trisc0_done_sync = int.from_bytes(win.mm[0x800:0x804], "little")
              trisc1_done_sync = int.from_bytes(win.mm[0x804:0x808], "little")
              trisc2_done_sync = int.from_bytes(win.mm[0x808:0x80C], "little")
              trisc0_done_byte = int.from_bytes(win.mm[0xF80:0xF84], "little")
              trisc1_done_byte = int.from_bytes(win.mm[0xF84:0xF88], "little")
              trisc2_done_byte = int.from_bytes(win.mm[0xF88:0xF8C], "little")
              msg += f"\n  BRISC kernel: tiles_recv_readback={brisc_tiles_recv} done=0x{brisc_done:x} tile_idx={brisc_tile_idx}"
              msg += f"\n  NCRISC fw: stage=0x{ncrisc_stage:x} aux=0x{ncrisc_aux:x}"
              msg += f"\n  TRISC0 fw: stage=0x{trisc0_stage:x} aux=0x{trisc0_aux:x}"
              msg += f"\n  TRISC1 fw: stage=0x{trisc1_stage:x} aux=0x{trisc1_aux:x}"
              msg += f"\n  TRISC2 fw: stage=0x{trisc2_stage:x} aux=0x{trisc2_aux:x}"
              msg += f"\n  Host sync trace: initial=0x{(host_sync_initial or 0):08x} last=0x{(host_sync_last or 0):08x} first_change=0x{(host_sync_first_change or 0):08x} changes={host_sync_change_count}"
              msg += f"\n  BRISC wait-sync: stage=0x{brisc_wait_stage:x} initial=0x{brisc_wait_initial:08x} last=0x{brisc_wait_last:08x} first_change=0x{brisc_wait_first_change:08x} reads={brisc_wait_reads}"
              msg += f"\n  TRISC done-sync snapshots: t0=0x{trisc0_done_sync:08x} t1=0x{trisc1_done_sync:08x} t2=0x{trisc2_done_sync:08x}"
              msg += f"\n  TRISC done-byte readbacks: t0=0x{trisc0_done_byte:08x} t1=0x{trisc1_done_byte:08x} t2=0x{trisc2_done_byte:08x}"
              if dev is not None and all_cores is not None:
                msg += f"\n  --- RISC-V PCs (all cores) ---\n{dump_core_pcs(dev, all_cores)}"
              msg += _resolve_stuck_pcs(win, x, y, dev)
              raise TimeoutError(msg)
