from asm import Cond
from isa import R

# Every tile has two NIUs. NIU 0 drives NoC 0 and NIU 1 drives NoC 1.
NIU0 = 0xFFB20000
NIU_STRIDE = 0x10000
NIU_CONFIG = 0x100            # config region offset within a NIU window
NIU_CONTROL = 0x00            # within the config region
ROUTER_CONTROL = 0x04
LOGICAL_NODE_ID = 0x48

def _endpoint(address, coordinate, middle=0): return address, middle, coordinate

def _packet(tid, options, packet_bytes, immediate=0, exclusions=0):
  return tid << 10, options, packet_bytes, 0, immediate, exclusions

class NiuCommand:
  MAX_PACKET_BYTES = 16 * 1024
  SEND_REQUEST = 0x40

  @classmethod
  def address(cls, niu, register): return NIU0 + niu * NIU_STRIDE + register

  @classmethod
  def build(cls, k, niu, source, target, packet):
    for index, value in enumerate((*source, *target, *packet)):
      k.write32(cls.address(niu, index * 4), value)

class TidCounters:
  STATUS_OFFSET = 0x200
  REQS_OUTSTANDING_BASE = 0x40
  WRITE_REQS_OUTGOING_BASE = 0x80
  FIRST_MANAGED_TID = 1
  LAST_MANAGED_TID = 15
  ISSUE_SAFE_LIMIT = 129

  @classmethod
  def requests_outstanding(cls, tid): return cls.REQS_OUTSTANDING_BASE + tid * 4

  @classmethod
  def writes_outgoing(cls, tid): return cls.WRITE_REQS_OUTGOING_BASE + tid * 4

class _TidAllocator:
  def __init__(self):
    self.free = set(range(TidCounters.FIRST_MANAGED_TID, TidCounters.LAST_MANAGED_TID + 1))

  def acquire(self, requested=None):
    tid = min(self.free) if requested is None else requested
    self.free.remove(tid)
    return tid

  def release(self, tid): self.free.add(tid)

class Transaction:
  def __init__(self, noc, tid=None):
    self.noc, self.k = noc, noc.k
    self.tid = noc._allocator.acquire(tid)
    self._source_pending = self._remote_pending = self._closed = False
    # A free TID must have no old payload reads or responses. Poll rather than
    # forcibly clearing it: clearing an actually-live bucket would hide traffic.
    noc._wait_counter(TidCounters.writes_outgoing(self.tid), 0)
    noc._wait_counter(TidCounters.requests_outstanding(self.tid), 0)

  def __enter__(self): return self

  def __exit__(self, exc_type, exc, tb):
    if exc_type is None:
      self.wait()
    elif not self._closed:
      # Code generation is being abandoned, so release compile-time ownership.
      self.noc._allocator.release(self.tid)
      self._closed = True

  def _ensure_open(self):
    if self._closed: raise RuntimeError("transaction is already closed")

  @staticmethod
  def _packets_for(byte_count):
    if type(byte_count) is not int: return None
    return (byte_count + NiuCommand.MAX_PACKET_BYTES - 1) // NiuCommand.MAX_PACKET_BYTES

  def read(self, source_address, source_coordinate, target_address,
           packet_bytes, source_middle_address=0):
    self._ensure_open(); self._remote_pending = True
    self.noc._read(self.tid, source_address, source_coordinate, target_address, packet_bytes,
                   source_middle_address=source_middle_address)
    return self

  def write(self, source_address, target_address, target_coordinate,
            packet_bytes, target_middle_address=0, posted=True):
    self._ensure_open(); self._source_pending = True
    if not posted: self._remote_pending = True
    self.noc._write(self.tid, source_address, target_address, target_coordinate, packet_bytes,
                    target_middle_address=target_middle_address, posted=posted)
    return self

  def _multicast_write(self, source_address, target_address, target_start,
                       target_end, packet_bytes, linked):
    self._ensure_open(); self._source_pending = True
    self.noc._multicast_write(self.tid, source_address, target_address, target_start,
                              target_end, packet_bytes, linked=linked)
    return self

  def multicast_write(self, source_address, target_address, target_start,
                      target_end, packet_bytes):
    return self._multicast_write(source_address, target_address, target_start,
                                 target_end, packet_bytes, linked=False)

  def multicast_write_chain(self, requests):
    requests = tuple(tuple(request) for request in requests)
    if not requests: raise ValueError("multicast chain must not be empty")
    if any(len(request) != 5 for request in requests): raise ValueError("chain requests need five values")
    rectangle = requests[0][2:4]
    if any(r[2:4] != rectangle for r in requests[1:]): raise ValueError("chain rectangle changed")
    for index, request in enumerate(requests): self._multicast_write(*request, linked=index + 1 < len(requests))
    return self

  def inline_write(self, value, target_address, target_coordinate,
                   posted=True):
    self._ensure_open()
    if not posted: self._remote_pending = True
    self.noc._inline_write(self.tid, value, target_address, target_coordinate, posted=posted)
    return self

  def atomic_inc(self, target_address, target_coordinate, value=1,
                 return_address=4, posted=False):
    self._ensure_open()
    if not posted: self._remote_pending = True
    self.noc._atomic_inc(self.tid, target_address, target_coordinate, value,
                         return_address=return_address, posted=posted)
    return self

  def wait_source(self):
    if self._closed: return self
    if self._source_pending:
      self.noc._wait_counter(TidCounters.writes_outgoing(self.tid), 0)
      self._source_pending = False
    return self

  def wait_remote(self):
    if self._closed: return self
    if self._remote_pending:
      self.noc._wait_counter(TidCounters.requests_outstanding(self.tid), 0)
      self._remote_pending = False
    return self

  def wait(self):
    if self._closed: return self.noc
    self.wait_source()
    self.wait_remote()
    return self._release()

  def _release(self):
    if self._closed: return self.noc
    if self._source_pending or self._remote_pending: raise RuntimeError("pending traffic")
    self.noc._allocator.release(self.tid)
    self._closed = True
    return self.noc

class NoC:
  # Deliberately hardcoded request policy.
  unicast_vc = 1
  multicast_vc = 4
  reserve_multicast_path = True
  multicast_along_y = False
  multicast_include_sender = False
  arbitration_priority = 0

  def __init__(self, k, index: int):
    if index not in (0, 1): raise ValueError("NoC index must be 0 or 1")
    self.index, self.k = index, k
    states = getattr(k, "_noc_tid_allocators", None)
    if states is None:
      states = {}
      setattr(k, "_noc_tid_allocators", states)
    self._allocator = states.setdefault(index, _TidAllocator())

  def _niu(self): return NIU0 + self.index * NIU_STRIDE
  def _status(self, register): return self._niu() + TidCounters.STATUS_OFFSET + register

  def transaction(self, tid=None): return Transaction(self, tid)

  @staticmethod
  def coordinate(x, y):
    if any(type(v) is not int or not 0 <= v < 64 for v in (x, y)): raise ValueError("invalid coordinate")
    return x | y << 6

  static_coord = coordinate

  @staticmethod
  def _validate_rectangle(start, end):
    for name, coordinate in (("start", start), ("end", end)):
      if isinstance(coordinate, R): continue
      if type(coordinate) is not int or not 0 <= coordinate < 1 << 12: raise ValueError(f"invalid {name}")
      if coordinate & 0x3F in (8, 9): raise ValueError(f"{name} cannot use columns 8 or 9")
    if type(start) is int and type(end) is int:
      sx, sy, ex, ey = start & 0x3F, start >> 6, end & 0x3F, end >> 6
      if sx > ex or sy > ey: raise ValueError("multicast start must precede end")

  def _rectangle(self, out, start, end):
    self._validate_rectangle(start, end)
    low, high = (end, start) if self.index == 0 else (start, end)
    if type(low) is int and type(high) is int:
      self.k.li(out, low | high << 12)
    else:
      shifted = self.k.reg(exclude=(out, *(x for x in (start, end) if isinstance(x, R))))
      self.k.mv(out, low) if isinstance(low, R) else self.k.li(out, low)
      self.k.mv(shifted, high) if isinstance(high, R) else self.k.li(shifted, high)
      self.k.slli(shifted, shifted, 12); self.k.or_(out, out, shifted)
    return out

  def _local_coordinate(self, out):
    self.k.load(out, self._niu() + NIU_CONFIG + LOGICAL_NODE_ID)
    self.k.slli(out, out, 20); self.k.srli(out, out, 20)
    return out

  def _packet_options(self, operation, posted=False, linked=False,
                      multicast=False, inline=False):
    options = {"read": 0, "atomic": 1, "write": 2}[operation]
    if inline: options |= 1 << 3
    if operation == "read" or not posted: options |= 1 << 4
    if multicast: options |= 1 << 5
    if linked: options |= 1 << 6
    options |= 1 << 7  # static VC
    options |= (self.multicast_vc if multicast else self.unicast_vc) << 13
    if multicast and self.reserve_multicast_path: options |= 1 << 8
    if multicast and self.multicast_along_y: options |= 1 << 16
    if multicast and self.multicast_include_sender: options |= 1 << 17
    options |= self.arbitration_priority << 27
    return options

  def _wait_counter(self, register, expected):
    k = self.k
    with k.scope():
      current = k.reg(exclude=expected if isinstance(expected, R) else ())
      with k.loop():
        k.load(current, self._status(register))
        k.break_(Cond(current, "==", expected))
      k.fence()
    return self

  def _wait_issue_safe(self, register, packet_bytes=None):
    k = self.k
    packets = Transaction._packets_for(packet_bytes) if packet_bytes is not None else 1
    with k.scope():
      current = k.reg()
      with k.loop():
        k.load(current, self._status(register))
        # A large auto-split command increments the counter all at once. Drain
        # the bucket first when that increment can exceed the half-range limit;
        # ordinary one-packet issue can retain up to 128 requests in flight.
        condition = Cond(current, "==", 0) if packets is not None and packets >= 128 else \
                    Cond(current, "<u", TidCounters.ISSUE_SAFE_LIMIT)
        k.break_(condition)
    return self

  def _submit(self, source, target, packet):
    k = self.k
    with k.scope():
      base, busy = k.reg(2)
      k.li(base, NiuCommand.address(self.index, 0))
      with k.loop():
        k.lw(busy, base, NiuCommand.SEND_REQUEST)
        k.break_(Cond(busy, "==", 0))
      NiuCommand.build(k, self.index, source, target, packet)
      k.write32(NiuCommand.address(self.index, NiuCommand.SEND_REQUEST), 1)
      # This readback orders submission and waits for hardware auto-splitting;
      # payload and response completion are tracked separately by the TID.
      with k.loop():
        k.lw(busy, base, NiuCommand.SEND_REQUEST)
        k.break_(Cond(busy, "==", 0))
    return self

  def _read(self, tid, source_address, source_coordinate, target_address,
            packet_bytes, source_middle_address=0):
    self._wait_issue_safe(TidCounters.requests_outstanding(tid), packet_bytes)
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      self._submit(
        _endpoint(source_address, source_coordinate, source_middle_address),
        _endpoint(target_address, local),
        _packet(tid, self._packet_options("read"), packet_bytes),
      )
    return self

  def _write(self, tid, source_address, target_address, target_coordinate,
             packet_bytes, target_middle_address=0, posted=True):
    self._wait_issue_safe(TidCounters.writes_outgoing(tid), packet_bytes)
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid), packet_bytes)
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      self._submit(
        _endpoint(source_address, local),
        _endpoint(target_address, target_coordinate, target_middle_address),
        _packet(tid, self._packet_options("write", posted=posted), packet_bytes),
      )
    return self

  def _multicast_write(self, tid, source_address, target_address, target_start,
                       target_end, packet_bytes, linked=False):
    self._wait_issue_safe(TidCounters.writes_outgoing(tid), packet_bytes)
    with self.k.scope():
      local, targets = self.k.reg(2)
      self._local_coordinate(local); self._rectangle(targets, target_start, target_end)
      self._submit(
        _endpoint(source_address, local),
        _endpoint(target_address, targets),
        _packet(tid, self._packet_options(
          "write", posted=True, linked=linked, multicast=True), packet_bytes),
      )
    return self

  def _inline_write(self, tid, value, target_address, target_coordinate,
                    posted=True):
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid))
    # Inline destinations occupy the hardware source endpoint group.
    return self._submit(
      _endpoint(target_address, target_coordinate), _endpoint(0, 0),
      _packet(tid, self._packet_options(
        "write", posted=posted, inline=True), 0xF, value),
    )

  def _atomic_inc(self, tid, target_address, target_coordinate, value=1,
                  return_address=4, posted=False):
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid))
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      return self._submit(
        _endpoint(target_address, target_coordinate),
        _endpoint(return_address, local),
        _packet(tid, self._packet_options("atomic", posted=posted),
                (1 << 12) | (31 << 2), value),
      )

  def _complete(self, operation, *args, **options):
    with self.transaction() as transaction: getattr(transaction, operation)(*args, **options)
    return self

  def read(self, *args, **options): return self._complete("read", *args, **options)
  def write(self, *args, **options): return self._complete("write", *args, **options)

  def read_into_cb(self, source_address, source_coordinate, cb, source_middle_address=0):
    from ttk.cb import CB
    CB.reserve_back(self.k, cb)
    with self.k.scope():
      target = self.k.reg()
      CB.get_write_ptr(self.k, cb, target)
      self.read(source_address, source_coordinate, target, cb.page_size,
                source_middle_address=source_middle_address)
    CB.push_back(self.k, cb)
    return self

  def write_from_cb(self, cb, target_address, target_coordinate,
                    target_middle_address=0, posted=False):
    from ttk.cb import CB
    CB.wait_front(self.k, cb)
    with self.k.scope():
      source = self.k.reg()
      CB.get_read_ptr(self.k, cb, source)
      self.write(source, target_address, target_coordinate, cb.page_size,
                 target_middle_address=target_middle_address, posted=posted)
    CB.pop_front(self.k, cb)
    return self

  def multicast_write(self, *args): return self._complete("multicast_write", *args)
  def multicast_write_chain(self, requests): return self._complete("multicast_write_chain", requests)
  def inline_write(self, *args, **options): return self._complete("inline_write", *args, **options)
  def atomic_inc(self, *args, **options): return self._complete("atomic_inc", *args, **options)
