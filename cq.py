from __future__ import annotations

import os
import struct
import time

from ttk.addrs import Core, L1_ALIGN, PCIE_ALIGN, align_up, noc_xy
from ttk.tensix import TensixL1
from pcie import Mapping, PCIDevice, TLBWindow
from program import IRCommand, McastMmioWrite32, McastWrite, Run, UnicastWrite

Rect = tuple[int, int, int, int]
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

# CQ L1 address map. These addresses are the single source of truth for the CQ
# ABI: fw/cq.py imports this module and aliases the names below so the host
# encoder and the on-device prefetch/dispatch firmware can never drift apart.
CQ_L1 = 0x196C0
_CQ_L1 = CQ_L1  # backwards-compatible private alias for this module's body
CQ_PREFETCH_Q_RD_PTR = _CQ_L1 + 0x00
CQ_PREFETCH_Q_PCIE_RD = _CQ_L1 + 0x04
CQ_COMPLETION_WR_PTR = _CQ_L1 + 0x10
CQ_COMPLETION_RD_PTR = _CQ_L1 + 0x20
CQ_COMPLETION_Q0_EVENT = _CQ_L1 + 0x30
CQ_COMPLETION_Q1_EVENT = _CQ_L1 + 0x40
CQ_DISPATCH_SYNC_SEM = _CQ_L1 + 0x50
CQ_COMPLETION_BASE_PTR = _CQ_L1 + 0xD0
CQ_COMPLETION_END_PTR = _CQ_L1 + 0xD4
CQ_COMPLETION_HOST_WR_OFF = _CQ_L1 + 0xD8
CQ_PREFETCH_Q_BASE = _CQ_L1 + 0x180
CQ_PREFETCH_Q_SIZE = 0xBFC
CQ_PREFETCH_Q_ENTRY_SZ = 4
CQ_PREFETCH_Q_ENTRIES = CQ_PREFETCH_Q_SIZE // CQ_PREFETCH_Q_ENTRY_SZ
CQ_DISPATCH_CB_PAGES = (1280 * 1024) >> 12

_PCIE_NOC_BASE = 1 << 60

# Host sysmem layout.
_HOST_ISSUE_BASE = 4 * PCIE_ALIGN
_HOST_ISSUE_SIZE = align_up(int(os.environ.get("CQ_ISSUE_MB", "64")) << 20, PCIE_ALIGN)
_HOST_COMPLETION_BASE = _HOST_ISSUE_BASE + _HOST_ISSUE_SIZE
_HOST_COMPLETION_SIZE = align_up(32 << 20, PCIE_ALIGN)
_HOST_CQ_WR_OFF = 2 * PCIE_ALIGN
_HOST_CQ_RD_OFF = 3 * PCIE_ALIGN
_HOST_SYS_END_BASE = _HOST_COMPLETION_BASE + _HOST_COMPLETION_SIZE

# Prefetch/dispatch command IDs. Public names are the shared CQ ABI consumed by
# fw/cq.py; the leading-underscore aliases keep this module's encoder body terse.
CMD_RELAY_INLINE = 5
CMD_WRITE_LINEAR_HOST = 3
CMD_WRITE_PACKED = 5
CMD_WRITE_PACKED_LARGE = 6
CMD_WAIT = 7
CMD_GO_SIGNAL = 14
CMD_SET_GO_NOC_DATA = 17
CMD_TIMESTAMP = 18
_RELAY_INLINE = CMD_RELAY_INLINE
_WRITE_LINEAR_HOST = CMD_WRITE_LINEAR_HOST
_WRITE_PACKED = CMD_WRITE_PACKED
_WRITE_PACKED_LARGE = CMD_WRITE_PACKED_LARGE
_WAIT = CMD_WAIT
_GO_SIGNAL = CMD_GO_SIGNAL
_SET_GO_NOC_DATA = CMD_SET_GO_NOC_DATA
_TIMESTAMP = CMD_TIMESTAMP

# Wait-command flags and packed-write flags (shared with fw/cq.py).
CQ_WAIT_BARRIER = 0x01
CQ_WAIT_WAIT_STREAM = 0x08
CQ_WAIT_CLEAR_STREAM = 0x10
CQ_PACKED_NO_STRIDE = 0x02
CQ_PACKED_LARGE_UNLINK = 0x01
GO_NO_MULTICAST = 0xFF

CQ_CMD_SIZE = 16
DONE_STREAM = 48
CQ_TIMESTAMP_BASE = _CQ_L1 + 0x180  # dispatch-core scratch; prefetch queue uses this only on prefetch core
CQ_TIMESTAMP_STRIDE = 16
CQ_TIMESTAMP_SLOTS = 64

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
  flags = CQ_PACKED_NO_STRIDE if uniform else 0
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
    hdr = _hdr("<BBHHH", (_WRITE_PACKED_LARGE, CQ_PACKED_NO_STRIDE, len(batch), L1_ALIGN, 0))
    subcmds = b"".join(
      struct.pack("<IIHBB", xy, addr, len(data) - 1, count, CQ_PACKED_LARGE_UNLINK)
      for rect in batch
      for xy, count in [_noc_mcast_xy(rect)]
    )
    subcmds = subcmds.ljust(align_up(len(subcmds), L1_ALIGN), b"\0")
    records.append(hdr + subcmds + padded)
  return records

def _barrier() -> bytes:
  return _hdr("<BBHII", (_WAIT, CQ_WAIT_BARRIER, 0, 0, 0))

def _set_go_signal_noc_data(cores: list[Core]) -> bytes:
  hdr = _hdr("<BBHI", (_SET_GO_NOC_DATA, 0, 0, len(cores)))
  body = b"".join(struct.pack("<I", noc_xy(x, y)) for x, y in cores)
  return hdr + body

def _send_go_signal(go_word: int, stream: int, count: int, num_unicast: int) -> bytes:
  return _hdr("<BIBBBII", (_GO_SIGNAL, go_word, GO_NO_MULTICAST, num_unicast, 0, count, stream))

def _wait_stream(stream: int, count: int, clear: bool = True) -> bytes:
  flags = CQ_WAIT_WAIT_STREAM | (CQ_WAIT_CLEAR_STREAM if clear else 0)
  return _hdr("<BBHII", (_WAIT, flags, stream, 0, count))

def _host_event(event_id: int) -> bytes:
  payload = struct.pack("<I", event_id & 0xFFFFFFFF).ljust(L1_ALIGN, b"\0")
  hdr = _hdr("<BBHIQ", (_WRITE_LINEAR_HOST, 1, 0, 0, CQ_CMD_SIZE + len(payload)))
  return hdr + payload

def _timestamp(addr: int) -> bytes:
  return _hdr("<BxxxI", (_TIMESTAMP, addr))

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

  def read_timestamp(self, slot: int) -> int:
    return self.sysmem.read_timestamp(slot)

  def submit_commands(self, payloads: list[bytes]):
    self.extend(payloads)
    event_id = self.sysmem.next_event_id()
    self.append(_host_event(event_id))
    self.sysmem.flush(self)
    self.sysmem.wait_completion(event_id)

  def submit_ir(self, programs: list[list[IRCommand]], go_word: int, names: list[str] | None = None):
    timestamps = [CQ_TIMESTAMP_BASE + i * CQ_TIMESTAMP_STRIDE for i in range(min(2 * len(programs), CQ_TIMESTAMP_SLOTS))]
    self.sysmem.clear_timestamps(len(timestamps))
    payloads = lower_programs(programs, go_word, timestamps=timestamps)
    self.submit_commands(payloads)
    return self.read_timings(len(programs), names=names)

  def read_timings(self, n: int, names: list[str] | None = None):
    timings = []
    freq_mhz = 1350
    names = names or [""] * n
    for i in range(n):
      slot = 2 * i
      if slot + 1 >= CQ_TIMESTAMP_SLOTS:
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

def lower_ir(
  commands: list[IRCommand],
  go_word: int,
  run_timestamps: tuple[int, int] | None = None,
) -> list[bytes]:
  out: list[bytes] = []
  for cmd in commands:
    match cmd:
      case UnicastWrite(cores=cores, addr=addr, data=data):
        _append_unicast_write(out, cores, addr, data)
      case McastWrite(rects=rects, addr=addr, data=data):
        _append_mcast_write(out, rects, addr, data)
        out.append(_barrier())
      case McastMmioWrite32(rects=rects, addr=addr, value=value):
        # MMIO regs are NoC-addressable; same encoding as a 4-byte mcast write.
        _append_mcast_write(out, rects, addr, struct.pack("<I", value & 0xFFFFFFFF))
        out.append(_barrier())
      case Run(cores=cores):
        out.extend([
          _barrier(),
          _set_go_signal_noc_data(cores),
          _wait_stream(DONE_STREAM, 0),
        ])
        if run_timestamps is not None:
          out.append(_timestamp(run_timestamps[0]))
        out.extend([
          _send_go_signal(go_word, DONE_STREAM, 0, len(cores)),
          _wait_stream(DONE_STREAM, len(cores)),
        ])
        if run_timestamps is not None:
          out.append(_timestamp(run_timestamps[1]))
      case _:
        raise TypeError(f"{type(cmd).__name__} is not supported by fast dispatch CQ")
  return out

def lower_programs(
  programs: list[list[IRCommand]],
  go_word: int,
  timestamps: list[int] | None = None,
) -> list[bytes]:
  out: list[bytes] = []
  for i, commands in enumerate(programs):
    ts = 2 * i
    run_timestamps = None
    if timestamps and ts + 1 < len(timestamps):
      run_timestamps = (timestamps[ts], timestamps[ts + 1])
    out.extend(lower_ir(commands, go_word, run_timestamps=run_timestamps))
  return out

class CQSysmem:
  def __init__(self, dev: PCIDevice, prefetch_win: TLBWindow, dispatch_win: TLBWindow):
    self.dev = dev
    self.prefetch_win = prefetch_win
    self.dispatch_win = dispatch_win
    self.size = _host_sysmem_size()
    self.sysmem = Mapping(self.size)
    self.sysmem_addr = self.sysmem.addr
    if self.sysmem_addr % PAGE_SIZE or self.size % PAGE_SIZE:
      raise RuntimeError("CQ sysmem must be page-aligned and page-sized")

    self.noc_addr = dev.pin_pages(self.sysmem, preferred_iatu_region=1)
    if (self.noc_addr & _PCIE_NOC_BASE) != _PCIE_NOC_BASE:
      raise RuntimeError(f"bad CQ sysmem NOC address: 0x{self.noc_addr:x}")
    self.noc_local = self.noc_addr - _PCIE_NOC_BASE
    if self.noc_local > 0xFFFFFFFF:
      raise RuntimeError(f"CQ sysmem NOC offset too large: 0x{self.noc_local:x}")

    self.issue_wr = 0
    self.prefetch_q_wr_idx = 0
    self.dispatch_cb_page_pos = 0
    self.event_id = 0
    self.completion_base_16b = ((self.noc_local + _HOST_COMPLETION_BASE) >> 4) & 0x7FFFFFFF
    self.completion_page_16b = PAGE_SIZE >> 4
    self.completion_end_16b = self.completion_base_16b + (_HOST_COMPLETION_SIZE >> 4)
    self.completion_rd_16b = self.completion_base_16b
    self.completion_rd_toggle = 0

    self.prefetch_win.write(CQ_PREFETCH_Q_RD_PTR, struct.pack("<I", CQ_PREFETCH_Q_BASE + CQ_PREFETCH_Q_SIZE))
    self.prefetch_win.write(CQ_PREFETCH_Q_PCIE_RD, struct.pack("<I", (self.noc_local + _HOST_ISSUE_BASE) & 0xFFFFFFFF))
    self.prefetch_win.write(CQ_PREFETCH_Q_BASE, bytes(CQ_PREFETCH_Q_SIZE))
    self.write_sysmem32(_HOST_CQ_WR_OFF, self.completion_base_16b)
    self.write_sysmem32(_HOST_CQ_RD_OFF, self.completion_base_16b)

  def read_sysmem32(self, off: int) -> int:
    return struct.unpack("<I", self.sysmem.read(off, 4))[0]

  def write_sysmem32(self, off: int, value: int):
    self.sysmem.write(off, struct.pack("<I", value & 0xFFFFFFFF))

  def _wait_prefetch_slot_free(self, idx: int, timeout_s: float = 5.0):
    off = CQ_PREFETCH_Q_BASE + idx * CQ_PREFETCH_Q_ENTRY_SZ
    deadline = time.perf_counter() + timeout_s
    while struct.unpack("<I", self.prefetch_win.read(off, 4))[0] != 0:
      if struct.unpack("<I", self.prefetch_win.read(CQ_PREFETCH_Q_RD_PTR, 4))[0] == 0xFFFFFFFF:
        raise RuntimeError("CQ prefetch core reads back 0xffffffff -- device off bus, needs reset")
      if time.perf_counter() > deadline:
        base = max(0, idx - 4)
        end = min(CQ_PREFETCH_Q_ENTRIES, idx + 5)
        entries = []
        for i in range(base, end):
          entry_off = CQ_PREFETCH_Q_BASE + i * CQ_PREFETCH_Q_ENTRY_SZ
          value = struct.unpack("<I", self.prefetch_win.read(entry_off, 4))[0]
          entries.append(f"{i}:{value}")
        rd_ptr = struct.unpack("<I", self.prefetch_win.read(CQ_PREFETCH_Q_RD_PTR, 4))[0]
        pcie_rd = struct.unpack("<I", self.prefetch_win.read(CQ_PREFETCH_Q_PCIE_RD, 4))[0]
        current = struct.unpack("<I", self.prefetch_win.read(off, 4))[0]
        raise TimeoutError(
          "timeout waiting for CQ prefetch queue slot "
          f"idx={idx} value={current} rd_ptr=0x{rd_ptr:x} "
          f"pcie_rd=0x{pcie_rd:x} nearby=[{', '.join(entries)}]"
        )

  def _issue_write(self, record: bytes):
    # Dispatch FW parses records linearly and only wraps its cursor when it
    # lands exactly on DISPATCH_CB_END, but prefetch splits writes across the
    # wrap. A multi-page record straddling the 128-page ring boundary makes
    # dispatch walk past CB end into stale L1 (spurious writes, then semaphore
    # divergence -> wait_completion wedge). The host knows every record's page
    # count, so pad to the ring boundary instead: an unknown-cmd record costs
    # exactly one page via dispatch's advance_page fallback.
    pages = max(1, (struct.unpack_from("<I", record, 4)[0] + 4095) >> 12)
    if pages > CQ_DISPATCH_CB_PAGES:
      raise ValueError(f"CQ record needs {pages} pages, dispatch CB has {CQ_DISPATCH_CB_PAGES}")

    self.issue_wr = align_up(self.issue_wr, PCIE_ALIGN)
    if self.issue_wr + len(record) > _HOST_ISSUE_SIZE:
      # Prefetch FW wraps its PCIe cursor only when it reaches HOST_ISSUE_SIZE
      # exactly; wrapping early here would desync it. Pad to the end with
      # filler records (16B unknown-cmd payload, stride covers the gap; stride
      # capped well under the 64K cmddat staging buffer).
      while self.issue_wr < _HOST_ISSUE_SIZE:
        stride = min(_HOST_ISSUE_SIZE - self.issue_wr, 32768)
        hdr = struct.pack("<BBHII", _RELAY_INLINE, 0, 0, CQ_CMD_SIZE, stride).ljust(CQ_CMD_SIZE, b"\0")
        self._issue_write(hdr.ljust(stride, b"\0"))
      self.issue_wr = 0
      # Wrap fence: a free slot only proves the prefetcher *started* on the
      # filler before it; its PCIe fetch of the ring tail can still be in
      # flight when the host begins rewriting offset 0 (rare hard-hang race).
      # Wait until every queued slot is consumed -- the prefetcher's PCIe
      # cursor has then provably wrapped past the region we are reusing.
      for i in range(CQ_PREFETCH_Q_ENTRIES):
        self._wait_prefetch_slot_free(i)

    while self.dispatch_cb_page_pos and pages > CQ_DISPATCH_CB_PAGES - self.dispatch_cb_page_pos:
      self._issue_write(_relay_inline(bytes(CQ_CMD_SIZE)))
    self.dispatch_cb_page_pos = (self.dispatch_cb_page_pos + pages) % CQ_DISPATCH_CB_PAGES

    base = _HOST_ISSUE_BASE + self.issue_wr
    self.sysmem.write(base, record)
    flush_base = base & ~(PAGE_SIZE - 1)
    flush_end = align_up(base + len(record), PAGE_SIZE)
    self.sysmem.flush(flush_base, flush_end - flush_base)
    self.issue_wr += len(record)

    idx = self.prefetch_q_wr_idx
    self._wait_prefetch_slot_free(idx)
    off = CQ_PREFETCH_Q_BASE + idx * CQ_PREFETCH_Q_ENTRY_SZ
    self.prefetch_win.write(off, struct.pack("<I", len(record) >> 4))
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

  def read_timestamp(self, slot: int) -> int:
    off = CQ_TIMESTAMP_BASE + slot * CQ_TIMESTAMP_STRIDE
    lo, hi = struct.unpack("<II", self.dispatch_win.read(off, 8))
    return (hi << 32) | lo

  def clear_timestamps(self, slots: int):
    if slots:
      self.dispatch_win.write(CQ_TIMESTAMP_BASE, bytes(slots * CQ_TIMESTAMP_STRIDE))

  def wait_completion(self, event_id: int, timeout_s: float = 10.0):
    deadline = time.perf_counter() + timeout_s
    while True:
      wr_raw = self.read_sysmem32(_HOST_CQ_WR_OFF)
      wr_16b, wr_toggle = wr_raw & 0x7FFFFFFF, (wr_raw >> 31) & 1
      if wr_16b != self.completion_rd_16b or wr_toggle != self.completion_rd_toggle:
        off = (self.completion_rd_16b << 4) - self.noc_local
        # Dispatch can publish the wr pointer before the event payload write
        # is observable (it waits for one ack, which an earlier in-flight
        # write can satisfy). Poll briefly for the expected id.
        got = self.read_sysmem32(off + CQ_CMD_SIZE)
        if got != (event_id & 0xFFFFFFFF):
          # Stale page: a stale wr-ptr read (toggle alias one ring later) or
          # payload still in flight. Do not consume; keep waiting.
          if time.perf_counter() > deadline:
            raise RuntimeError(f"CQ completion event mismatch: got {got}, expected {event_id}")
          time.sleep(0.0002)
          continue
        self.completion_rd_16b += self.completion_page_16b
        if self.completion_rd_16b >= self.completion_end_16b:
          self.completion_rd_16b = self.completion_base_16b
          self.completion_rd_toggle ^= 1
        raw = (self.completion_rd_16b & 0x7FFFFFFF) | (self.completion_rd_toggle << 31)
        self.dispatch_win.write(CQ_COMPLETION_RD_PTR, struct.pack("<I", raw))
        self.write_sysmem32(_HOST_CQ_RD_OFF, raw)
        if got != (event_id & 0xFFFFFFFF):
          raise RuntimeError(f"CQ completion event mismatch: got {got}, expected {event_id}")
        return
      if time.perf_counter() > deadline:
        raise TimeoutError(f"timeout waiting for CQ completion event {event_id} -- reset the device")
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
