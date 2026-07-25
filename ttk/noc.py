from asm import Cond
from fw.consts import TensixL1
from isa import R
from pcie import P100_DRAM_ENDPOINTS
from ttk.cb import CB

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
      k.write(cls.address(niu, index * 4), value)

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

  @staticmethod
  def _packets_for(byte_count):
    if type(byte_count) is not int: return None
    return (byte_count + NiuCommand.MAX_PACKET_BYTES - 1) // NiuCommand.MAX_PACKET_BYTES

  def read(self, source_address, source_coordinate, target_address,
           packet_bytes, source_middle_address=0):
    self._remote_pending = True
    self.noc._read(self.tid, source_address, source_coordinate, target_address, packet_bytes,
                   source_middle_address=source_middle_address)
    return self

  def write(self, source_address, target_address, target_coordinate,
            packet_bytes, target_middle_address=0, posted=True):
    self._source_pending = True
    if not posted: self._remote_pending = True
    self.noc._write(self.tid, source_address, target_address, target_coordinate, packet_bytes,
                    target_middle_address=target_middle_address, posted=posted)
    return self

  def _multicast_write(self, source_address, target_address, target_start,
                       target_end, packet_bytes):
    self._source_pending = True
    self.noc._multicast_write(self.tid, source_address, target_address, target_start,
                              target_end, packet_bytes)
    return self

  def multicast_write(self, source_address, target_address, target_start,
                      target_end, packet_bytes):
    return self._multicast_write(
      source_address, target_address, target_start, target_end, packet_bytes,
    )

  def inline_write(self, value, target_address, target_coordinate,
                   posted=True):
    if not posted: self._remote_pending = True
    self.noc._inline_write(self.tid, value, target_address, target_coordinate, posted=posted)
    return self

  def atomic_inc(self, target_address, target_coordinate, value=1,
                 return_address=4, posted=False):
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
    self.noc._allocator.release(self.tid)
    self._closed = True
    return self.noc

class NoC:
  # Deliberately hardcoded request policy.
  unicast_vc = 1
  multicast_vc = 4
  multicast_linked = False
  reserve_multicast_path = False
  multicast_along_y = False
  multicast_include_sender = False
  arbitration_priority = 0

  def __init__(self, k, index: int):
    self.index, self.k, self.local_coordinate = index, k, None
    states = getattr(k, "_noc_tid_allocators", None)
    if states is None:
      states = {}
      setattr(k, "_noc_tid_allocators", states)
    self._allocator = states.setdefault(index, _TidAllocator())

  def _niu(self): return NIU0 + self.index * NIU_STRIDE
  def _status(self, register): return self._niu() + TidCounters.STATUS_OFFSET + register

  def transaction(self, tid=None): return Transaction(self, tid)

  def initialize(self, coordinate):
    self.local_coordinate = coordinate
    return self

  @staticmethod
  def coordinate(x, y): return x | y << 6

  static_coord = coordinate

  @staticmethod
  def _check_multicast_endpoint(coordinate):
    if isinstance(coordinate, R): return
    if type(coordinate) is not int or not 0 <= coordinate < 1 << 12:
      raise ValueError("invalid multicast endpoint")
    if coordinate & 0x3F in (8, 9):
      raise ValueError("multicast start/end cannot use NoC columns 8 or 9")

  def _rectangle(self, out, start, end):
    self._check_multicast_endpoint(start); self._check_multicast_endpoint(end)
    if type(start) is int and type(end) is int:
      sx, sy, ex, ey = start & 0x3F, start >> 6, end & 0x3F, end >> 6
      if sx > ex or sy > ey: raise ValueError("multicast start must precede end")
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
    if self.local_coordinate is not None:
      self.k.mv(out, self.local_coordinate) if isinstance(self.local_coordinate, R) else \
        self.k.li(out, self.local_coordinate)
      return out
    self.k.read(out, self._niu() + NIU_CONFIG + LOGICAL_NODE_ID)
    self.k.slli(out, out, 20); self.k.srli(out, out, 20)
    return out

  def _packet_options(self, operation, posted=False, multicast=False, inline=False):
    options = {"read": 0, "atomic": 1, "write": 2}[operation]
    if inline: options |= 1 << 3
    if operation == "read" or not posted: options |= 1 << 4
    if multicast: options |= 1 << 5
    if multicast and self.multicast_linked: options |= 1 << 6
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
        k.read(current, self._status(register))
        k.break_(Cond(current, "==", expected))
      k.fence()
    return self

  def _wait_issue_safe(self, register, packet_bytes=None):
    k = self.k
    packets = Transaction._packets_for(packet_bytes) if packet_bytes is not None else 1
    with k.scope():
      current = k.reg()
      with k.loop():
        k.read(current, self._status(register))
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
      k.write(NiuCommand.address(self.index, NiuCommand.SEND_REQUEST), 1)
      # Order submission and wait for hardware auto-splitting before the
      # command registers can be reused by the next request.
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
                       target_end, packet_bytes):
    self._wait_issue_safe(TidCounters.writes_outgoing(tid), packet_bytes)
    with self.k.scope():
      local, targets = self.k.reg(2)
      self._local_coordinate(local); self._rectangle(targets, target_start, target_end)
      self._submit(
        _endpoint(source_address, local),
        _endpoint(target_address, targets),
        _packet(tid, self._packet_options("write", posted=True, multicast=True), packet_bytes),
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

  def read(self, *args, **options):
    with self.transaction() as transaction: transaction.read(*args, **options)
    return self

  def write(self, *args, **options):
    with self.transaction() as transaction: transaction.write(*args, **options)
    return self

  def _dram_tile(self, param, tile):
    k, endpoints, buffer = self.k, P100_DRAM_ENDPOINTS, param
    base = k.reg()
    k.read(base, TensixL1.PARAM_BASE + k.param_slots[param] * 4)
    address, coordinate, bank, banks, scale, rotation = k.reg(
      6, exclude=(tile, base),
    )
    # Program binding moves the base to this core's shard and stores the
    # shard's first DRAM bank in the aligned address's low bits.
    k.andi(rotation, base, 7); k.andi(base, base, -8)
    k.li(banks, len(endpoints))
    if param.bank_block_tiles == 1:
      if isinstance(tile, R): k.add(address, tile, rotation)
      else: k.li(address, tile); k.add(address, address, rotation)
      k.remu(bank, address, banks); k.divu(address, address, banks)
    else:
      if not param.global_address:
        raise ValueError(
          "blocked DRAM bank interleave requires global addressing",
        )
      with k.scope():
        group, within, block = k.reg(3, exclude=(tile, base))
        k.li(block, param.bank_block_tiles)
        if isinstance(tile, R):
          k.divu(group, tile, block)
          k.remu(within, tile, block)
        else:
          k.li(group, tile // param.bank_block_tiles)
          k.li(within, tile % param.bank_block_tiles)
        k.remu(bank, group, banks)
        k.divu(address, group, banks)
        k.mul(address, address, block)
        k.add(address, address, within)
    k.li(scale, buffer.tile_size); k.mul(address, address, scale); k.add(address, address, base)
    selected = k._new_label("dram_bank_selected")
    invalid = k._new_label("dram_bank_invalid")
    labels = {index: k._new_label(f"dram_bank_{index}") for index in range(len(endpoints))}
    k.switch(bank, labels, invalid)
    for index, label in labels.items():
      k.label(label); k.li(coordinate, self.coordinate(*endpoints[index][self.index])); k.j(selected)
    k.label(invalid); k.j(invalid); k.label(selected)
    return address, coordinate

  def read_into_cb(self, param, tile, cb, source_middle_address=0):
    CB.reserve_back(self.k, cb)
    with self.k.scope():
      source_address, source_coordinate = self._dram_tile(param, tile)
      target = self.k.reg(exclude=(source_address, source_coordinate))
      CB.get_write_ptr(self.k, cb, target)
      self.read(source_address, source_coordinate, target, cb.tile_size,
                source_middle_address=source_middle_address)
    CB.push_back(self.k, cb)
    return self

  def read_tiles_into_cb(self, param, tiles, cb, source_middle_address=0):
    """Issue a group of tile reads before waiting and publish them together."""
    tiles = tuple(tiles)
    if not tiles: raise ValueError("tile read group cannot be empty")
    if cb.depth % len(tiles):
      raise ValueError("tile read group must evenly divide circular-buffer depth")
    CB.reserve_back(self.k, cb, len(tiles))
    with self.transaction() as transaction:
      for index, tile in enumerate(tiles):
        with self.k.scope():
          source_address, source_coordinate = self._dram_tile(param, tile)
          target = self.k.reg(exclude=(source_address, source_coordinate))
          CB.get_write_ptr(self.k, cb, target)
          if index:
            offset = self.k.reg(exclude=(source_address, source_coordinate, target))
            self.k.li(offset, index * cb.tile_size)
            self.k.add(target, target, offset)
          transaction.read(
            source_address, source_coordinate, target, cb.tile_size,
            source_middle_address=source_middle_address,
          )
    CB.push_back(self.k, cb, len(tiles))
    return self

  def read_tile(self, param, tile, target_address,
                source_middle_address=0):
    """Read one DRAM tile directly into a caller-owned L1 address."""
    with self.k.scope():
      source_address, source_coordinate = self._dram_tile(param, tile)
      self.read(
        source_address, source_coordinate, target_address, param.tile_size,
        source_middle_address=source_middle_address,
      )
    return self

  def read_tiles(self, param, tiles_and_targets, source_middle_address=0):
    """Issue direct-to-L1 tile reads as one transaction."""
    tiles_and_targets = tuple(tiles_and_targets)
    if not tiles_and_targets:
      raise ValueError("direct tile read group cannot be empty")
    with self.transaction() as transaction:
      for tile, target_address in tiles_and_targets:
        with self.k.scope():
          source_address, source_coordinate = self._dram_tile(param, tile)
          transaction.read(
            source_address, source_coordinate, target_address,
            param.tile_size, source_middle_address=source_middle_address,
          )
    return self

  def write_from_cb(self, cb, param, tile, target_middle_address=0, posted=False):
    CB.wait_front(self.k, cb)
    with self.k.scope():
      target_address, target_coordinate = self._dram_tile(param, tile)
      source = self.k.reg(exclude=(target_address, target_coordinate))
      CB.get_read_ptr(self.k, cb, source)
      self.write(source, target_address, target_coordinate, cb.tile_size,
                 target_middle_address=target_middle_address, posted=posted)
    CB.pop_front(self.k, cb)
    return self

  def write_tiles_from_cb(self, cb, param, tiles,
                          target_middle_address=0, posted=False):
    """Issue a group of CB tile writes before one completion wait."""
    tiles = tuple(tiles)
    if not tiles: raise ValueError("tile write group cannot be empty")
    if cb.depth % len(tiles):
      raise ValueError("tile write group must evenly divide circular-buffer depth")
    CB.wait_front(self.k, cb, len(tiles))
    with self.transaction() as transaction:
      for index, tile in enumerate(tiles):
        with self.k.scope():
          target_address, target_coordinate = self._dram_tile(param, tile)
          source = self.k.reg(exclude=(target_address, target_coordinate))
          CB.get_read_ptr(self.k, cb, source)
          if index:
            offset = self.k.reg(exclude=(target_address, target_coordinate, source))
            self.k.li(offset, index * cb.tile_size)
            self.k.add(source, source, offset)
          transaction.write(
            source, target_address, target_coordinate, cb.tile_size,
            target_middle_address=target_middle_address, posted=posted,
          )
    CB.pop_front(self.k, cb, len(tiles))
    return self

  def multicast_write(self, *args):
    with self.transaction() as transaction: transaction.multicast_write(*args)
    return self

  def inline_write(self, *args, **options):
    with self.transaction() as transaction: transaction.inline_write(*args, **options)
    return self

  def atomic_inc(self, *args, **options):
    with self.transaction() as transaction: transaction.atomic_inc(*args, **options)
    return self
