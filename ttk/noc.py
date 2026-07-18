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
  CLEAR_OUTSTANDING = 0x60       # relative to NIU base, not status base
  FIRST_MANAGED_TID = 1
  LAST_MANAGED_TID = 15
  WIDTH_MASK = 0xFF
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
    self._needs_source = False
    self._needs_remote = False
    self._source_waited = False
    self._remote_waited = False
    self._closed = False
    self._nonposted_multicast = None
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

  @staticmethod
  def _packets_for(byte_count):
    if type(byte_count) is not int: return None
    return (byte_count + NiuCommand.MAX_PACKET_BYTES - 1) // NiuCommand.MAX_PACKET_BYTES

  def _track_response(self): self._needs_remote = True

  def _track_multicast(self, packet_bytes, destinations):
    self._nonposted_multicast = (packet_bytes, destinations)
    self._needs_remote = True

  def read(self, source_address, source_coordinate, target_address,
           packet_bytes, *, source_middle_address=0, linked=False):
    self._track_response()
    self.noc._read(self.tid, source_address, source_coordinate, target_address,
                   packet_bytes, source_middle_address=source_middle_address,
                   linked=linked)
    return self

  def write(self, source_address, target_address, target_coordinate,
            packet_bytes, *, target_middle_address=0, posted=True, linked=False):
    self._needs_source = True
    if not posted: self._track_response()
    self.noc._write(self.tid, source_address, target_address, target_coordinate,
                    packet_bytes, target_middle_address=target_middle_address,
                    posted=posted, linked=linked)
    return self

  def multicast_write(self, source_address, target_address, targets,
                      packet_bytes, *, posted=True, linked=False, destinations=1):
    self._needs_source = True
    if not posted: self._track_multicast(packet_bytes, destinations)
    self.noc._multicast_write(
      self.tid, source_address, target_address, targets, packet_bytes,
      posted=posted, linked=linked, destinations=destinations,
    )
    return self

  def inline_write(self, value, target_address, target_coordinate, *,
                   posted=True, linked=False):
    if not posted: self._track_response()
    self.noc._inline_write(self.tid, value, target_address, target_coordinate,
                           posted=posted, linked=linked)
    return self

  def atomic_inc(self, target_address, target_coordinate, value=1, *,
                 return_address=4, posted=False, linked=False):
    if not posted: self._track_response()
    self.noc._atomic_inc(self.tid, target_address, target_coordinate, value,
                         return_address=return_address, posted=posted, linked=linked)
    return self

  def wait_source(self):
    if self._closed: return self
    if self._needs_source and not self._source_waited:
      self.noc._wait_counter(TidCounters.writes_outgoing(self.tid), 0)
    self._source_waited = True
    return self

  def _emit_multicast_terminal(self):
    packet_bytes, destinations = self._nonposted_multicast
    packets = self._packets_for(packet_bytes)
    if packets is not None and type(destinations) is int:
      return (packets * (1 - destinations)) & TidCounters.WIDTH_MASK

    # Runtime form of: ceil(bytes / 16KiB) * (1 - destinations) mod 256.
    k = self.k
    target, packet_count, receiver_delta, tmp = k.reg(4)
    if packets is None:
      k.li(tmp, NiuCommand.MAX_PACKET_BYTES - 1)
      k.add(packet_count, packet_bytes, tmp)
      k.srli(packet_count, packet_count, 14)
    else:
      k.li(packet_count, packets)
    k.li(receiver_delta, 1)
    if isinstance(destinations, R): k.sub(receiver_delta, receiver_delta, destinations)
    else: k.addi(receiver_delta, receiver_delta, -destinations)
    k.mul(target, packet_count, receiver_delta)
    k.andi(target, target, TidCounters.WIDTH_MASK)
    return target

  def wait_remote(self):
    if self._closed: return self
    if self._needs_remote and not self._remote_waited:
      if self._nonposted_multicast is None:
        self.noc._wait_counter(TidCounters.requests_outstanding(self.tid), 0)
      else:
        # One multicast command increments once per generated request packet,
        # while every recipient ACK decrements. The settled value is therefore
        # packets * (1 - destinations), modulo the eight-bit counter width.
        with self.k.scope():
          terminal = self._emit_multicast_terminal()
          self.noc._wait_counter(TidCounters.requests_outstanding(self.tid), terminal)
        # Return the deliberately underflowed bucket to zero before TID reuse.
        self.k.write32(self.noc._niu() + TidCounters.CLEAR_OUTSTANDING, 1 << self.tid)
        self.k.fence()
    self._remote_waited = True
    return self

  def wait(self):
    if self._closed: return self.noc
    self.wait_source()
    self.wait_remote()
    return self.release()

  def release(self):
    if self._closed: return self.noc
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
    self.index, self.k = index, k
    states = getattr(k, "_noc_tid_allocators", None)
    if states is None:
      states = {}
      setattr(k, "_noc_tid_allocators", states)
    self._allocator = states.setdefault(index, _TidAllocator())

  def _niu(self): return NIU0 + self.index * NIU_STRIDE
  def _status(self, register): return self._niu() + TidCounters.STATUS_OFFSET + register

  def transaction(self, tid=None): return Transaction(self, tid)

  def _local_coordinate(self, out):
    self.k.load(out, self._niu() + NIU_CONFIG + LOGICAL_NODE_ID)
    self.k.slli(out, out, 20); self.k.srli(out, out, 20)
    return out

  def _packet_options(self, operation, *, posted=False, linked=False,
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
            packet_bytes, *, source_middle_address=0, linked=False):
    self._wait_issue_safe(TidCounters.requests_outstanding(tid), packet_bytes)
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      self._submit(
        _endpoint(source_address, source_coordinate, source_middle_address),
        _endpoint(target_address, local),
        _packet(tid, self._packet_options("read", linked=linked), packet_bytes),
      )
    return self

  def _write(self, tid, source_address, target_address, target_coordinate,
             packet_bytes, *, target_middle_address=0, posted=True, linked=False):
    self._wait_issue_safe(TidCounters.writes_outgoing(tid), packet_bytes)
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid), packet_bytes)
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      self._submit(
        _endpoint(source_address, local),
        _endpoint(target_address, target_coordinate, target_middle_address),
        _packet(tid, self._packet_options("write", posted=posted, linked=linked), packet_bytes),
      )
    return self

  def _multicast_write(self, tid, source_address, target_address, targets,
                       packet_bytes, *, posted=True, linked=False, destinations=1):
    self._wait_issue_safe(TidCounters.writes_outgoing(tid), packet_bytes)
    # Non-posted multicast deliberately underflows REQS_OUTSTANDING and is
    # therefore isolated by Transaction and completed against its final value.
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      self._submit(
        _endpoint(source_address, local),
        _endpoint(target_address, targets),
        _packet(tid, self._packet_options(
          "write", posted=posted, linked=linked, multicast=True), packet_bytes),
      )
    return self

  def _inline_write(self, tid, value, target_address, target_coordinate, *,
                    posted=True, linked=False):
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid))
    # Inline destinations occupy the hardware source endpoint group.
    return self._submit(
      _endpoint(target_address, target_coordinate), _endpoint(0, 0),
      _packet(tid, self._packet_options(
        "write", posted=posted, linked=linked, inline=True), 0xF, value),
    )

  def _atomic_inc(self, tid, target_address, target_coordinate, value=1, *,
                  return_address=4, posted=False, linked=False):
    if not posted: self._wait_issue_safe(TidCounters.requests_outstanding(tid))
    with self.k.scope():
      local = self._local_coordinate(self.k.reg())
      return self._submit(
        _endpoint(target_address, target_coordinate),
        _endpoint(return_address, local),
        _packet(tid, self._packet_options("atomic", posted=posted, linked=linked),
                (1 << 12) | (31 << 2), value),
      )

  def read(self, source_address, source_coordinate, target_address, packet_bytes, **options):
    return self.transaction().read(
      source_address, source_coordinate, target_address, packet_bytes, **options,
    ).wait()

  def write(self, source_address, target_address, target_coordinate, packet_bytes, **options):
    return self.transaction().write(
      source_address, target_address, target_coordinate, packet_bytes, **options,
    ).wait()

  def multicast_write(self, source_address, target_address, targets, packet_bytes, **options):
    return self.transaction().multicast_write(
      source_address, target_address, targets, packet_bytes, **options,
    ).wait()

  def inline_write(self, value, target_address, target_coordinate, **options):
    return self.transaction().inline_write(
      value, target_address, target_coordinate, **options,
    ).wait()

  def atomic_inc(self, target_address, target_coordinate, value=1, **options):
    return self.transaction().atomic_inc(
      target_address, target_coordinate, value, **options,
    ).wait()
