from __future__ import annotations

import os
import struct
import time

from ttk.addrs import Core, L1_ALIGN, PCIE_ALIGN, align_up, noc_xy
from ttk.tensix import TensixL1
from pcie import LibCAnonMap, PCIDevice, TLBWindow
from program import IRCommand, McastWrite, Run, UnicastWrite

Rect = tuple[int, int, int, int]
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

# CQ L1 address map. These addresses are consumed by fw/cq.py.
_CQ_L1 = 0x196C0
CQ_PREFETCH_Q_RD_PTR = _CQ_L1 + 0x00
CQ_PREFETCH_Q_PCIE_RD = _CQ_L1 + 0x04
CQ_COMPLETION_WR_PTR = _CQ_L1 + 0x10
CQ_COMPLETION_RD_PTR = _CQ_L1 + 0x20
CQ_COMPLETION_Q0_EVENT = _CQ_L1 + 0x30
CQ_COMPLETION_Q1_EVENT = _CQ_L1 + 0x40
CQ_DISPATCH_SYNC_SEM = _CQ_L1 + 0x50
CQ_PREFETCH_Q_BASE = _CQ_L1 + 0x180
CQ_PREFETCH_Q_ENTRIES = 1534
CQ_PREFETCH_Q_ENTRY_SZ = 2
CQ_PREFETCH_Q_SIZE = CQ_PREFETCH_Q_ENTRIES * CQ_PREFETCH_Q_ENTRY_SZ
CQ_DISPATCH_CB_PAGES = (512 * 1024) >> 12

_PCIE_NOC_BASE = 1 << 60

# Host sysmem layout.
_HOST_ISSUE_BASE = 4 * PCIE_ALIGN
_HOST_ISSUE_SIZE = align_up(64 << 20, PCIE_ALIGN)
_HOST_COMPLETION_BASE = _HOST_ISSUE_BASE + _HOST_ISSUE_SIZE
_HOST_COMPLETION_SIZE = align_up(32 << 20, PCIE_ALIGN)
_HOST_TIMESTAMP_BASE = _HOST_COMPLETION_BASE + _HOST_COMPLETION_SIZE
_HOST_TIMESTAMP_STRIDE = 16
HOST_TIMESTAMP_SLOTS = 4096
_HOST_TIMESTAMP_SIZE = align_up(HOST_TIMESTAMP_SLOTS * _HOST_TIMESTAMP_STRIDE, PCIE_ALIGN)
_HOST_CQ_WR_OFF = 2 * PCIE_ALIGN
_HOST_CQ_RD_OFF = 3 * PCIE_ALIGN
_HOST_SYS_END_BASE = _HOST_TIMESTAMP_BASE + _HOST_TIMESTAMP_SIZE

# Prefetch/dispatch command IDs.
_RELAY_INLINE = 5
_WRITE_LINEAR_HOST = 3
_WRITE_PACKED = 5
_WRITE_PACKED_LARGE = 6
_WAIT = 7
_GO_SIGNAL = 14
_SET_GO_NOC_DATA = 17
_TIMESTAMP = 18

CQ_CMD_SIZE = 16
DONE_STREAM = 48

def _debug_enabled() -> bool:
  return os.environ.get("TT_CQ_DEBUG", "") not in ("", "0", "false", "False")

def _debug_hex_enabled() -> bool:
  return os.environ.get("TT_CQ_DEBUG_HEX", "") not in ("", "0", "false", "False")

def _hex_preview(data: bytes, limit: int = 64) -> str:
  if _debug_hex_enabled():
    return data.hex()
  suffix = "" if len(data) <= limit else f"...(+{len(data) - limit}B)"
  return data[:limit].hex() + suffix

def _describe_ir(cmd: IRCommand) -> str:
  match cmd:
    case UnicastWrite(cores=cores, addr=addr, data=data):
      size = len(data[0]) if data else 0
      uniform = all(blob == data[0] for blob in data[1:]) if data else True
      return f"UnicastWrite cores={len(cores)} addr=0x{addr:x} size={size} uniform={uniform} first={cores[0] if cores else None} last={cores[-1] if cores else None}"
    case McastWrite(rects=rects, addr=addr, data=data):
      return f"McastWrite rects={rects} addr=0x{addr:x} size={len(data)}"
    case Run(cores=cores):
      return f"Run cores={len(cores)} first={cores[0] if cores else None} last={cores[-1] if cores else None}"
    case _:
      return type(cmd).__name__

def _describe_payload(payload: bytes) -> str:
  if not payload:
    return "empty"
  cmd = payload[0]
  if cmd == _WRITE_PACKED and len(payload) >= CQ_CMD_SIZE:
    _, flags, count, _reserved, size, addr = struct.unpack_from("<BBHHHI", payload)
    nocs_off = CQ_CMD_SIZE
    data_off = align_up(nocs_off + count * 4, L1_ALIGN)
    return (
      f"WRITE_PACKED flags=0x{flags:02x} count={count} size={size} addr=0x{addr:x} "
      f"payload={len(payload)} data_off={data_off} head={_hex_preview(payload)}"
    )
  if cmd == _WRITE_PACKED_LARGE and len(payload) >= CQ_CMD_SIZE:
    _, flags, count, align, _reserved = struct.unpack_from("<BBHHH", payload)
    sub_off = CQ_CMD_SIZE
    data_off = align_up(sub_off + count * 12, L1_ALIGN)
    subs = []
    for i in range(min(count, 8)):
      xy, addr, length_m1, ndests, sub_flags = struct.unpack_from("<IIHBB", payload, sub_off + i * 12)
      subs.append(f"(xy=0x{xy:x} addr=0x{addr:x} len={length_m1 + 1} ndests={ndests} flags=0x{sub_flags:02x})")
    more = "" if count <= 8 else f" ... +{count - 8} subcmds"
    return (
      f"WRITE_PACKED_LARGE flags=0x{flags:02x} subcmds={count} align={align} "
      f"payload={len(payload)} data_off={data_off} subs=[{' '.join(subs)}{more}] head={_hex_preview(payload)}"
    )
  if cmd == _WAIT and len(payload) >= CQ_CMD_SIZE:
    _, flags, stream, _reserved, count = struct.unpack_from("<BBHII", payload)
    return f"WAIT flags=0x{flags:02x} stream={stream} count={count} payload={len(payload)} head={_hex_preview(payload)}"
  if cmd == _GO_SIGNAL and len(payload) >= CQ_CMD_SIZE:
    _, go_word, multicast, num_unicast, noc_idx, count, stream = struct.unpack_from("<BIBBBII", payload)
    return f"GO_SIGNAL go=0x{go_word:x} multicast=0x{multicast:02x} unicast={num_unicast} noc_idx={noc_idx} stream={stream} count={count} payload={len(payload)} head={_hex_preview(payload)}"
  if cmd == _SET_GO_NOC_DATA and len(payload) >= CQ_CMD_SIZE:
    _, _flags, _reserved, count = struct.unpack_from("<BBHI", payload)
    return f"SET_GO_NOC_DATA count={count} payload={len(payload)} head={_hex_preview(payload)}"
  if cmd == _WRITE_LINEAR_HOST and len(payload) >= CQ_CMD_SIZE:
    _, flags, _reserved, _addr, size = struct.unpack_from("<BBHIQ", payload)
    return f"WRITE_LINEAR_HOST flags=0x{flags:02x} size={size} payload={len(payload)} head={_hex_preview(payload)}"
  if cmd == _TIMESTAMP and len(payload) >= CQ_CMD_SIZE:
    _, _reserved0, _reserved1, noc_xy_addr, addr = struct.unpack_from("<BxHII", payload)
    return f"TIMESTAMP noc_xy=0x{noc_xy_addr:x} addr=0x{addr:x} payload={len(payload)} head={_hex_preview(payload)}"
  return f"cmd={cmd} payload={len(payload)} head={_hex_preview(payload)}"

def _host_sysmem_size() -> int:
  return align_up(_HOST_SYS_END_BASE, PAGE_SIZE)

def _noc_mcast_xy(rect: Rect) -> tuple[int, int]:
  x0, x1, y0, y1 = rect
  return (y1 << 18) | (x1 << 12) | (y0 << 6) | x0, (x1 - x0 + 1) * (y1 - y0 + 1)

def _hdr(fmt: str, values: tuple) -> bytes:
  return struct.pack(fmt, *values).ljust(CQ_CMD_SIZE, b"\0")

def _write_packed(cores: list[Core], addr: int, data: bytes | list[bytes]) -> bytes:
  uniform = isinstance(data, bytes)
  size = len(data) if uniform else len(data[0])
  flags = 0x02 if uniform else 0
  hdr = _hdr("<BBHHHI", (_WRITE_PACKED, flags, len(cores), 0, size, addr))
  targets = b"".join(struct.pack("<I", noc_xy(x, y)) for x, y in cores)
  targets = targets.ljust(align_up(len(targets), L1_ALIGN), b"\0")
  if uniform:
    body = bytes(data).ljust(align_up(size, L1_ALIGN), b"\0")
  else:
    stride = align_up(size, L1_ALIGN)
    body = b"".join(bytes(blob).ljust(stride, b"\0") for blob in data)
  return hdr + targets + body

def _write_packed_large(rects: list[Rect], addr: int, data: bytes) -> list[bytes]:
  padded = bytes(data).ljust(align_up(len(data), L1_ALIGN), b"\0")
  records: list[bytes] = []
  for i in range(0, len(rects), 35):
    batch = rects[i : i + 35]
    hdr = _hdr("<BBHHH", (_WRITE_PACKED_LARGE, 2, len(batch), L1_ALIGN, 0))
    subcmds = b"".join(
      struct.pack("<IIHBB", xy, addr, len(data) - 1, count, 0x01)
      for rect in batch
      for xy, count in [_noc_mcast_xy(rect)]
    )
    subcmds = subcmds.ljust(align_up(len(subcmds), L1_ALIGN), b"\0")
    records.append(hdr + subcmds + padded)
  return records

def _barrier() -> bytes:
  return _hdr("<BBHII", (_WAIT, 0x01, 0, 0, 0))

def _set_go_signal_noc_data(cores: list[Core]) -> bytes:
  hdr = _hdr("<BBHI", (_SET_GO_NOC_DATA, 0, 0, len(cores)))
  body = b"".join(struct.pack("<I", noc_xy(x, y)) for x, y in cores)
  return hdr + body

def _send_go_signal(go_word: int, stream: int, count: int, num_unicast: int) -> bytes:
  return _hdr("<BIBBBII", (_GO_SIGNAL, go_word, 0xFF, num_unicast, 0, count, stream))

def _wait_stream(stream: int, count: int, clear: bool = True) -> bytes:
  flags = 0x08 | (0x10 if clear else 0)
  return _hdr("<BBHII", (_WAIT, flags, stream, 0, count))

def _host_event(event_id: int) -> bytes:
  payload = struct.pack("<I", event_id & 0xFFFFFFFF).ljust(L1_ALIGN, b"\0")
  hdr = _hdr("<BBHIQ", (_WRITE_LINEAR_HOST, 1, 0, 0, CQ_CMD_SIZE + len(payload)))
  return hdr + payload

def _timestamp(noc_xy_addr: int, addr: int) -> bytes:
  return _hdr("<BxHII", (_TIMESTAMP, 0, noc_xy_addr, addr))

def _relay_inline(payload: bytes) -> bytes:
  stride = align_up(CQ_CMD_SIZE + len(payload), PCIE_ALIGN)
  hdr = struct.pack("<BBHII", _RELAY_INLINE, 0, 0, len(payload), stride).ljust(CQ_CMD_SIZE, b"\0")
  return hdr + payload.ljust(stride - CQ_CMD_SIZE, b"\0")

class CommandQueue:
  def __init__(self, dev: PCIDevice, prefetch_core: Core, dispatch_core: Core):
    self.sysmem = CQSysmem(
      dev,
      prefetch_win=TLBWindow(dev, start=prefetch_core),
      dispatch_win=TLBWindow(dev, start=dispatch_core),
    )
    self.stream = bytearray()
    self.sizes_16b: list[int] = []

  def clear(self):
    self.stream.clear()
    self.sizes_16b.clear()

  def append(self, payload: bytes):
    record = _relay_inline(payload)
    self.stream.extend(record)
    self.sizes_16b.append(len(record) >> 4)

  def extend(self, payloads: list[bytes]):
    for payload in payloads:
      self.append(payload)

  @property
  def prefetch_win(self) -> TLBWindow:
    return self.sysmem.prefetch_win

  @property
  def dispatch_win(self) -> TLBWindow:
    return self.sysmem.dispatch_win

  @property
  def completion_base_16b(self) -> int:
    return self.sysmem.completion_base_16b

  def timestamp_noc_addr(self, slot: int) -> tuple[int, int]:
    return self.sysmem.timestamp_noc_addr(slot)

  def read_timestamp(self, slot: int) -> int:
    return self.sysmem.read_timestamp(slot)

  def submit_commands(self, payloads: list[bytes]):
    self.extend(payloads)
    event_id = self.sysmem.next_event_id()
    self.append(_host_event(event_id))
    self.sysmem.flush(self)
    self.sysmem.wait_completion(event_id)

  def submit_ir(self, programs: list[list[IRCommand]], go_word: int, names: list[str] | None = None):
    timestamps = [self.timestamp_noc_addr(i) for i in range(min(2 * len(programs), HOST_TIMESTAMP_SLOTS))]
    payloads = lower_programs(programs, go_word, timestamps=timestamps)
    if _debug_enabled():
      print("CQ DEBUG IR")
      for pi, program in enumerate(programs):
        print(f"  program[{pi}] commands={len(program)}")
        for ci, cmd in enumerate(program):
          print(f"    ir[{ci:02d}] {_describe_ir(cmd)}")
      print("CQ DEBUG payloads")
      for i, payload in enumerate(payloads):
        record_len = align_up(CQ_CMD_SIZE + len(payload), PCIE_ALIGN)
        pages = (len(payload) + 4095) // 4096
        print(f"  payload[{i:02d}] relay_record={record_len}B relay_size16={record_len >> 4} dispatch_pages={pages} {_describe_payload(payload)}")
    self.submit_commands(payloads)
    return self.read_timings(len(programs), names=names)

  def read_timings(self, n: int, names: list[str] | None = None):
    timings = []
    freq_mhz = 1350
    names = names or [""] * n
    for i in range(n):
      slot = 2 * i
      if slot + 1 >= HOST_TIMESTAMP_SLOTS:
        break
      start = self.read_timestamp(slot)
      end = self.read_timestamp(slot + 1)
      cycles = end - start
      timings.append({
        "cycles": cycles,
        "us": cycles / freq_mhz,
        "freq_mhz": freq_mhz,
        "name": names[i] if i < len(names) else "",
      })
    return timings

  def close(self):
    self.sysmem.close()

def _append_unicast_write(out: list[bytes], cores: list[Core], addr: int, data: list[bytes]):
  if not data:
    return
  size = len(data[0])
  if any(len(blob) != size for blob in data):
    raise ValueError("per-core CQ writes require uniform payload sizes")
  max_payload = 4096 - 2 * CQ_CMD_SIZE - align_up(len(cores) * 4, L1_ALIGN)
  max_chunk = max(L1_ALIGN, (max_payload // len(cores)) & ~(L1_ALIGN - 1))
  for off in range(0, size, max_chunk):
    out.append(_write_packed(cores, addr + off, [blob[off : off + max_chunk] for blob in data]))

def _append_mcast_write(out: list[bytes], rects: list[Rect], addr: int, data: bytes):
  # Keep records comfortably below the prefetch scratch queue size.
  max_rects = min(len(rects), 35) or 1
  max_chunk = max(L1_ALIGN, ((48 * 1024) // max_rects) & ~(L1_ALIGN - 1))
  for off in range(0, len(data), max_chunk):
    out.extend(_write_packed_large(rects, addr + off, data[off : off + max_chunk]))

def lower_ir(commands: list[IRCommand], go_word: int) -> list[bytes]:
  out: list[bytes] = []
  for cmd in commands:
    match cmd:
      case UnicastWrite(cores=cores, addr=addr, data=data):
        _append_unicast_write(out, cores, addr, data)
      case McastWrite(rects=rects, addr=addr, data=data):
        _append_mcast_write(out, rects, addr, data)
        out.append(_barrier())
      case Run(cores=cores):
        out.extend([
          _barrier(),
          _set_go_signal_noc_data(cores),
          _wait_stream(DONE_STREAM, 0),
          _send_go_signal(go_word, DONE_STREAM, 0, len(cores)),
          _wait_stream(DONE_STREAM, len(cores)),
        ])
      case _:
        raise TypeError(f"{type(cmd).__name__} is not supported by fast dispatch CQ")
  return out

def lower_programs(
  programs: list[list[IRCommand]],
  go_word: int,
  timestamps: list[tuple[int, int]] | None = None,
) -> list[bytes]:
  out: list[bytes] = []
  for i, commands in enumerate(programs):
    ts = 2 * i
    if timestamps and ts + 1 < len(timestamps):
      out.append(_timestamp(*timestamps[ts]))
    out.extend(lower_ir(commands, go_word))
    if timestamps and ts + 1 < len(timestamps):
      out.append(_timestamp(*timestamps[ts + 1]))
  return out

class CQSysmem:
  def __init__(self, dev: PCIDevice, prefetch_win: TLBWindow, dispatch_win: TLBWindow):
    self.dev = dev
    self.prefetch_win = prefetch_win
    self.dispatch_win = dispatch_win
    self.size = _host_sysmem_size()
    self.sysmem = LibCAnonMap(self.size)
    self.sysmem_addr = self.sysmem.addr
    if self.sysmem_addr % PAGE_SIZE or self.size % PAGE_SIZE:
      raise RuntimeError("CQ sysmem must be page-aligned and page-sized")

    self.noc_addr = dev.pin_pages(self.sysmem)
    if (self.noc_addr & _PCIE_NOC_BASE) != _PCIE_NOC_BASE:
      raise RuntimeError(f"bad CQ sysmem NOC address: 0x{self.noc_addr:x}")
    self.noc_local = self.noc_addr - _PCIE_NOC_BASE
    if self.noc_local > 0xFFFFFFFF:
      raise RuntimeError(f"CQ sysmem NOC offset too large: 0x{self.noc_local:x}")

    self.issue_wr = 0
    self.prefetch_q_wr_idx = 0
    self.event_id = 0
    self.completion_base_16b = ((self.noc_local + _HOST_COMPLETION_BASE) >> 4) & 0x7FFFFFFF
    self.completion_page_16b = PAGE_SIZE >> 4
    self.completion_end_16b = self.completion_base_16b + (_HOST_COMPLETION_SIZE >> 4)
    self.completion_rd_16b = self.completion_base_16b
    self.completion_rd_toggle = 0

    self.prefetch_win.write32(CQ_PREFETCH_Q_RD_PTR, CQ_PREFETCH_Q_BASE + CQ_PREFETCH_Q_SIZE)
    self.prefetch_win.write32(CQ_PREFETCH_Q_PCIE_RD, (self.noc_local + _HOST_ISSUE_BASE) & 0xFFFFFFFF)
    self.prefetch_win.mm[CQ_PREFETCH_Q_BASE : CQ_PREFETCH_Q_BASE + CQ_PREFETCH_Q_SIZE] = bytes(CQ_PREFETCH_Q_SIZE)
    self.write_sysmem32(_HOST_CQ_WR_OFF, self.completion_base_16b)
    self.write_sysmem32(_HOST_CQ_RD_OFF, self.completion_base_16b)

  def read_sysmem32(self, off: int) -> int:
    return struct.unpack("<I", self.sysmem[off : off + 4])[0]

  def write_sysmem32(self, off: int, value: int):
    self.sysmem[off : off + 4] = struct.pack("<I", value & 0xFFFFFFFF)

  def _wait_prefetch_slot_free(self, idx: int, timeout_s: float = 1.0):
    off = CQ_PREFETCH_Q_BASE + idx * CQ_PREFETCH_Q_ENTRY_SZ
    deadline = time.perf_counter() + timeout_s
    while struct.unpack("<H", self.prefetch_win.mm[off : off + 2])[0] != 0:
      if time.perf_counter() > deadline:
        base = max(0, idx - 4)
        end = min(CQ_PREFETCH_Q_ENTRIES, idx + 5)
        entries = []
        for i in range(base, end):
          entry_off = CQ_PREFETCH_Q_BASE + i * CQ_PREFETCH_Q_ENTRY_SZ
          value = struct.unpack("<H", self.prefetch_win.mm[entry_off : entry_off + 2])[0]
          entries.append(f"{i}:{value}")
        rd_ptr = self.prefetch_win.read32(CQ_PREFETCH_Q_RD_PTR)
        pcie_rd = self.prefetch_win.read32(CQ_PREFETCH_Q_PCIE_RD)
        current = struct.unpack("<H", self.prefetch_win.mm[off : off + 2])[0]
        raise TimeoutError(
          "timeout waiting for CQ prefetch queue slot "
          f"idx={idx} value={current} rd_ptr=0x{rd_ptr:x} "
          f"pcie_rd=0x{pcie_rd:x} nearby=[{', '.join(entries)}]"
        )

  def _issue_write(self, record: bytes):
    self.issue_wr = align_up(self.issue_wr, PCIE_ALIGN)
    if self.issue_wr + len(record) > _HOST_ISSUE_SIZE:
      self.issue_wr = 0

    base = _HOST_ISSUE_BASE + self.issue_wr
    self.sysmem[base : base + len(record)] = record
    flush_base = base & ~(PAGE_SIZE - 1)
    flush_end = align_up(base + len(record), PAGE_SIZE)
    self.sysmem.flush(flush_base, flush_end - flush_base)
    self.issue_wr += len(record)

    idx = self.prefetch_q_wr_idx
    self._wait_prefetch_slot_free(idx)
    off = CQ_PREFETCH_Q_BASE + idx * CQ_PREFETCH_Q_ENTRY_SZ
    self.prefetch_win.mm[off : off + 2] = struct.pack("<H", len(record) >> 4)
    self.prefetch_q_wr_idx = (idx + 1) % CQ_PREFETCH_Q_ENTRIES

  def flush(self, queue: CommandQueue):
    offset = 0
    for size_16b in queue.sizes_16b:
      size = size_16b << 4
      self._issue_write(queue.stream[offset : offset + size])
      offset += size
    queue.clear()

  def next_event_id(self) -> int:
    self.event_id += 1
    return self.event_id

  def timestamp_noc_addr(self, slot: int) -> tuple[int, int]:
    off = _HOST_TIMESTAMP_BASE + slot * _HOST_TIMESTAMP_STRIDE
    pcie_noc_xy = (1 << 24) | ((24 << 6) | 19)
    return pcie_noc_xy, self.noc_local + off

  def read_timestamp(self, slot: int) -> int:
    off = _HOST_TIMESTAMP_BASE + slot * _HOST_TIMESTAMP_STRIDE
    lo = self.read_sysmem32(off)
    hi = self.read_sysmem32(off + 4)
    return (hi << 32) | lo

  def wait_completion(self, event_id: int, timeout_s: float = 10.0):
    deadline = time.perf_counter() + timeout_s
    while True:
      wr_raw = self.read_sysmem32(_HOST_CQ_WR_OFF)
      wr_16b, wr_toggle = wr_raw & 0x7FFFFFFF, (wr_raw >> 31) & 1
      if wr_16b != self.completion_rd_16b or wr_toggle != self.completion_rd_toggle:
        off = (self.completion_rd_16b << 4) - self.noc_local
        got = self.read_sysmem32(off + CQ_CMD_SIZE)
        self.completion_rd_16b += self.completion_page_16b
        if self.completion_rd_16b >= self.completion_end_16b:
          self.completion_rd_16b = self.completion_base_16b
          self.completion_rd_toggle ^= 1
        raw = (self.completion_rd_16b & 0x7FFFFFFF) | (self.completion_rd_toggle << 31)
        self.dispatch_win.write32(CQ_COMPLETION_RD_PTR, raw)
        self.write_sysmem32(_HOST_CQ_RD_OFF, raw)
        if got != (event_id & 0xFFFFFFFF):
          raise RuntimeError(f"CQ completion event mismatch: got {got}, expected {event_id}")
        return
      if time.perf_counter() > deadline:
        raise TimeoutError(f"timeout waiting for CQ completion event {event_id} -- try tt-smi -r")
      time.sleep(0.0002)

  def close(self):
    try:
      self.prefetch_win.close()
    finally:
      try:
        self.dispatch_win.close()
      finally:
        self.dev.unpin_pages(self.sysmem, self.noc_addr)
        self.sysmem.close()
