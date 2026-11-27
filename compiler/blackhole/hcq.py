"""Minimal HCQ2-compatible compute command queue for Blackhole's Command Processor (CP)."""
import struct
import fw


def pack_phys_rect(target) -> int:
  """Pack a physical core `(x, y)` or rectangle `((x0, y0), (x1, y1))` for NoC0 CP dispatch."""
  if isinstance(target[0], int):
    c = (target[1] << 6) | target[0]
    return (c << 12) | c
  (x0, y0), (x1, y1) = target
  c0 = (y0 << 6) | x0
  c1 = (y1 << 6) | x1
  return (c0 << 12) | c1


class CommandBuffer:
  """Pre-encoded HCQ2 command buffer + contiguous kernargs living in pinned host memory."""
  def __init__(self, device, cmd_off: int, cmd_bytes: int, args_off: int = 0, args_bytes: int = 0,
               signal_pkt_off: int | None = None):
    self.device = device
    self.cmd_off, self.cmd_bytes = cmd_off, cmd_bytes
    self.cmd_addr = device.host.noc_addr + cmd_off
    self.args_off, self.args_bytes = args_off, args_bytes
    self.args_addr = device.host.noc_addr + args_off if args_bytes else 0
    self.signal_pkt_off = signal_pkt_off
    self.last_seq = 0

  def wait_previous(self, timeout: float = 10.0):
    """HCQ2 fence: wait only for the previous run of this command buffer before patching."""
    if self.last_seq:
      self.device.kernel_signal.wait(self.last_seq, timeout)

  def patch_arg_u64(self, rel_byte_off: int, value: int):
    struct.pack_into("<Q", self.device.host.mem, self.args_off + rel_byte_off, value & 0xFFFFFFFFFFFFFFFF)

  def patch_arg_u32(self, rel_byte_off: int, value: int):
    struct.pack_into("<Q", self.device.host.mem, self.args_off + rel_byte_off, value & 0xFFFFFFFF)

  def submit(self, *, signal_timeline: bool = True) -> int:
    """Ring CP_WPTR once for the entire command buffer; returns the new timeline sequence."""
    seq = self.device.kernel_sequence
    if signal_timeline and self.signal_pkt_off is not None:
      seq += 1
      struct.pack_into("<Q", self.device.host.mem, self.cmd_off + self.signal_pkt_off + 16, seq)
      self.device.kernel_sequence = seq
      self.last_seq = seq
    self.device.submit_cp(self.cmd_addr, self.cmd_bytes)
    return seq


class ComputeQueue:
  """Minimal HCQ2 HWQueue builder emitting 64-byte packets for fw/cp.c."""
  def __init__(self):
    self.pkts = bytearray()
    self.args = bytearray()
    self.arg_patches: list[tuple[int, int]] = []  # (pkt_byte_off, rel_args_off)
    self.last_signal_off: int | None = None

  def _emit(self, *words: int) -> int:
    off = len(self.pkts)
    if len(words) > 16: raise ValueError("HCQ2 packet exceeds 16 words (64 bytes)")
    self.pkts += struct.pack("<16I", *words, *(0,) * (16 - len(words)))
    return off

  def nop(self):
    self._emit(fw.PKT_NOP)
    return self

  def exec_barrier(self):
    self._emit(fw.PKT_EXEC_BARRIER)
    return self

  def memory_barrier(self):
    self._emit(fw.PKT_MEM_BARRIER)
    return self

  def wait(self, signal_addr: int, value: int, *, eq: bool = False):
    self._emit(fw.PKT_WAIT, int(eq), signal_addr & 0xFFFFFFFF, signal_addr >> 32,
               value & 0xFFFFFFFF, value >> 32)
    return self

  def signal(self, signal_addr: int, value: int):
    self.last_signal_off = self._emit(fw.PKT_SIGNAL, 0, signal_addr & 0xFFFFFFFF, signal_addr >> 32,
                                      value & 0xFFFFFFFF, value >> 32)
    return self

  def timestamp(self, signal_addr: int):
    self._emit(fw.PKT_TIMESTAMP, 0, signal_addr & 0xFFFFFFFF, signal_addr >> 32)
    return self

  def alloc_args(self, initial: bytes = b"") -> int:
    """Reserve a 64B-aligned 128-byte kernargs block inside this queue's contiguous args buffer."""
    if len(initial) > 128: raise ValueError(f"kernargs ({len(initial)} B) exceeds 128-byte ABI limit")
    rel = len(self.args)
    block = bytearray(128)
    block[:len(initial)] = initial
    self.args += block
    return rel

  def exec(self, prog_addr: int, prog_bytes: int, prog_key: int, rects: list[int], nworkers: int,
           args_rel: int | None = None, *, flags: int = fw.FLAG_CLEAR_MCAST, args_bytes: int = 128):
    if not 1 <= len(rects) <= 6: raise ValueError(f"PKT_EXEC supports 1..6 rects, got {len(rects)}")
    off = self._emit(
      fw.PKT_EXEC, flags,
      prog_addr & 0xFFFFFFFF, prog_addr >> 32,
      prog_bytes, prog_key & 0xFFFFFFFF,
      0, 0,  # args_addr patched in build()
      nworkers, ((args_bytes if args_rel is not None else 0) << 8) | len(rects),
      *rects,
    )
    if args_rel is not None: self.arg_patches.append((off, args_rel))
    return self

  def build(self, device) -> CommandBuffer:
    """Materialize packets + kernargs into pinned host memory, link-patching args addresses."""
    if not self.pkts: self.nop()
    args_off = device.alloc_host(len(self.args), align=64) if self.args else 0
    if self.args:
      device.host.mem[args_off:args_off + len(self.args)] = self.args
    args_base = device.host.noc_addr + args_off if self.args else 0
    for pkt_off, rel in self.arg_patches:
      addr = args_base + rel
      struct.pack_into("<Q", self.pkts, pkt_off + 24, addr)
    cmd_off = device.alloc_host(len(self.pkts), align=64)
    device.host.mem[cmd_off:cmd_off + len(self.pkts)] = self.pkts
    return CommandBuffer(device, cmd_off, len(self.pkts), args_off, len(self.args), self.last_signal_off)
