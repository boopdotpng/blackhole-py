from __future__ import annotations
from ttko.asm import Cond
from fw.consts import TensixL1
from ttko.isa import R
from ttko.cb import CB
from ttko.registers import TensixL1, BriscMailbox as BM

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
    values = (*source, *target, *packet)
    inputs = tuple(value for value in values if isinstance(value, R))
    with k.scope():
      base = k.reg(exclude=inputs)
      k.li(base, cls.address(niu, 0))
      for index, value in enumerate(values):
        if isinstance(value, R):
          k.sw(value, base, index * 4)
        elif value == 0:
          k.sw(R.ZERO, base, index * 4)
        else:
          with k.scope():
            immediate = k.reg(exclude=(base, *inputs))
            k.li(immediate, value)
            k.sw(immediate, base, index * 4)

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
    k, buffer = self.k, param
    endpoints = buffer.dram_endpoints
    if len(endpoints) != buffer.banks:
      raise ValueError(
        f"buffer uses {buffer.banks} DRAM banks but has "
        f"{len(endpoints)} endpoints",
      )
    base = k.reg()
    k.read(base, TensixL1.PARAM_BASE + k.param_slots[param] * 4)
    address, coordinate, bank, banks, scale, rotation = k.reg(
      6, exclude=(tile, base),
    )
    # Program binding moves the base to this core's shard and stores the
    # shard's first DRAM bank in the aligned address's low bits.
    k.andi(rotation, base, 7); k.andi(base, base, -8)
    if isinstance(tile, R): k.add(address, tile, rotation)
    else: k.li(address, tile); k.add(address, address, rotation)
    k.li(banks, len(endpoints))
    k.remu(bank, address, banks); k.divu(address, address, banks)
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


L1_ALIGN = 16
class NOC:
  REGS_START_ADDR = NIU0
  STATUS_BASE = NIU0 + TidCounters.STATUS_OFFSET
  CMD_BUF_OFFSET_BIT = 11
  INSTANCE_OFFSET_BIT = 16
  CFG_BASE = REGS_START_ADDR + 0x100

  TARG_ADDR_LO = REGS_START_ADDR + 0x00
  TARG_ADDR_MID = REGS_START_ADDR + 0x04
  TARG_ADDR_COORDINATE = REGS_START_ADDR + 0x08
  RET_ADDR_LO = REGS_START_ADDR + 0x0C
  RET_ADDR_MID = REGS_START_ADDR + 0x10
  RET_ADDR_COORDINATE = REGS_START_ADDR + 0x14
  CTRL = REGS_START_ADDR + 0x1C
  AT_LEN_BE = REGS_START_ADDR + 0x20
  AT_LEN_BE_1 = REGS_START_ADDR + 0x24
  AT_DATA = REGS_START_ADDR + 0x28
  CMD_CTRL = REGS_START_ADDR + 0x40

  CTRL_SEND_REQ = 1
  PCIE_MID = 0x10000000
  COORD_MASK = 0xFFFFFF

  CMD_CPY = 0
  CMD_AT = 1
  CMD_WR = 1 << 1
  CMD_WR_INLINE = 1 << 3
  CMD_RESP_MARKED = 1 << 4
  CMD_BRCST_PACKET = 1 << 5
  CMD_VC_LINKED = 1 << 6
  CMD_VC_STATIC = 1 << 7
  CMD_PATH_RESERVE = 1 << 8
  CMD_STATIC_VC_1 = 1 << 13
  CMD_STATIC_VC_5 = 5 << 13

  CMD_RD_FIELD = CMD_CPY | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_FIELD = CMD_CPY | CMD_WR | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_POSTED_FIELD = CMD_CPY | CMD_WR | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_MCAST_UNLINK_FIELD = (
    CMD_CPY | CMD_WR | CMD_RESP_MARKED | CMD_VC_STATIC |
    CMD_STATIC_VC_5 | CMD_BRCST_PACKET | CMD_PATH_RESERVE
  )
  CMD_WR_MCAST_LINKED_FIELD = CMD_WR_MCAST_UNLINK_FIELD | CMD_VC_LINKED
  CMD_INLINE_FIELD = CMD_WR_FIELD | CMD_WR_INLINE
  CMD_AT_INC_FIELD = CMD_AT | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1

  AT_INS_INCR_GET = 0x1
  AT_INS_SHIFT = 12
  AT_WRAP_SHIFT = 2
  AT_INCR_GET = (AT_INS_INCR_GET << AT_INS_SHIFT) | (31 << AT_WRAP_SHIFT)

  MAX_BURST_SIZE = NiuCommand.MAX_PACKET_BYTES

  NIU_MST_ATOMIC_RESP_RECEIVED = 0x00
  NIU_MST_WR_ACK_RECEIVED = 0x04
  NIU_MST_RD_RESP_RECEIVED = 0x08
  NIU_MST_NONPOSTED_WR_REQ_SENT = 0x28
  NIU_MST_POSTED_WR_REQ_SENT = 0x2C

class NocCfg:
  NIU_CFG_0 = 0x0
  ROUTER_CFG_0 = 0x1
  ID_LOGICAL = 0x12
  NODE_ID_MASK = 0x3F
  ADDR_NODE_ID_BITS = 6
  ADDR_COORD_SHIFT = 36
  COORDINATE_MASK = 0xFFFFFF
  PCIE_MASK = 0x1000000F
  INLINE_WRITE_POSTED_FIELD = (1 << 7) | (1 << 13) | (1 << 1) | (1 << 3)
  STREAM_REG_SPACE_SIZE = 0x1000
  MEM_NOC_ATOMIC_RET_VAL_ADDR = 0x04
  NCRISC_WR_CMD_BUF = 0
  NCRISC_RD_CMD_BUF = 1
  NCRISC_WR_REG_CMD_BUF = 2
  NCRISC_AT_CMD_BUF = 3
  RD_CMD_FIELD = (1 << 4) | (1 << 7) | (1 << 13)
  NIU_MST_ATOMIC_RESP_RECEIVED_WORD = 0x0
  NIU_MST_WR_ACK_RECEIVED_WORD = 0x1
  NIU_MST_RD_RESP_RECEIVED_WORD = 0x2
  NIU_MST_NONPOSTED_WR_REQ_SENT_WORD = 0xA
  NIU_MST_POSTED_WR_REQ_SENT_WORD = 0xB

class NocOps:
  def noc_coord(self, out: R, x: int | R, y: int | R, *, tmp: R = R.T0):
    if (isinstance(x, int) and not isinstance(x, R)) and (isinstance(y, int) and not isinstance(y, R)):
      return self.li(out, noc_xy(x, y))
    if (isinstance(y, int) and not isinstance(y, R)):
      self.li(out, y)
    else:
      self.mv(out, y)
    self.slli(out, out, 6)
    if (isinstance(x, int) and not isinstance(x, R)):
      self.li(tmp, x)
      return self.or_(out, out, tmp)
    return self.or_(out, out, x)

  def noc_mcast_coord(self, out: R, x_start: int | R, y_start: int | R,
                      x_end: int | R, y_end: int | R, *, tmp: R = R.T0,
                      reverse: bool = False):
    if reverse:
      x_start, x_end = x_end, x_start
      y_start, y_end = y_end, y_start
    self.noc_coord(out, x_end, y_end, tmp=tmp)
    if (isinstance(x_start, int) and not isinstance(x_start, R)) and (isinstance(y_start, int) and not isinstance(y_start, R)):
      self.li(tmp, noc_xy(x_start, y_start))
    else:
      self.noc_coord(tmp, x_start, y_start)
    self.slli(tmp, tmp, 12)
    return self.or_(out, out, tmp)

  def sem_addr(self, sem_l1_base: int, sem_id: int | R, *, out: R = R.T6, tmp: R = R.T0):
    if (isinstance(sem_id, int) and not isinstance(sem_id, R)):
      self.read32(out, sem_l1_base, tmp_addr=tmp)
      return self.addi(out, out, sem_id * L1_ALIGN)
    off = tmp
    if int(off) == int(sem_id):
      off = R.T5 if int(sem_id) != int(R.T5) and int(out) != int(R.T5) else R.T4
    self.slli(off, sem_id, 4)
    self.read32(out, sem_l1_base, tmp_addr=out)
    return self.add(out, out, off)

  def noc_semaphore_set(self, sem_addr: R, value: int | R, *, tmp: R = R.T0):
    if (isinstance(value, int) and not isinstance(value, R)):
      self.li(tmp, value)
      value = tmp
    self.sw(value, sem_addr, 0)
    return self.fence()

  def noc_semaphore_wait(self, sem_addr: R, value: int | R, *, actual: R = R.T0, expected: R = R.T1):
    if (isinstance(value, int) and not isinstance(value, R)):
      self.li(expected, value)
      value = expected
    loop = self._new_label("noc_sem_wait")
    done = self._new_label("noc_sem_done")
    self.label(loop)
    self.fence()
    self.lw(actual, sem_addr, 0)
    self.beq(actual, value, done)
    self.j(loop)
    self.label(done)
    return self.fence()

  def local_noc0_coord(self, out: R = R.A5, *, x_addr: int = BM.MY_X, y_addr: int = BM.MY_Y):
    self.read8(R.T0, x_addr, tmp_addr=R.T2)
    self.read8(R.T1, y_addr, tmp_addr=R.T2)
    self.slli(R.T1, R.T1, 6)
    return self.or_(out, R.T0, R.T1)

  def dram_tile_addr_from(self, table_base: int, noc_table_offset: int | R = 0, *, tile_bytes=2048):
    self.mv(R.T0, R.A1)
    self.remu(R.A1, R.T0, R.A2)
    self.divu(R.T0, R.T0, R.A2)
    self.slli(R.T0, R.T0, tile_bytes.bit_length() - 1)
    self.add(R.A0, R.A0, R.T0)
    if (isinstance(noc_table_offset, int) and not isinstance(noc_table_offset, R)):
      self.addi(R.T1, R.A1, noc_table_offset)
    else:
      self.add(R.T1, R.A1, noc_table_offset)
    self.slli(R.T1, R.T1, 1)
    self.li(R.T2, table_base)
    self.add(R.T2, R.T2, R.T1)
    return self.lhu(R.A2, R.T2, 0)


  def noc_cmd_addr(self, noc: int, buf: int, reg: int) -> int:
    return reg + (buf << NOC.CMD_BUF_OFFSET_BIT) + (noc << NOC.INSTANCE_OFFSET_BIT)

  def noc_cmd_reg(self, noc: int, buf: int, reg: int, value: int | R, *, addr: R = R.T0, tmp: R = R.T1):
    return self.write32(self.noc_cmd_addr(noc, buf, reg), value, tmp_addr=addr, tmp_val=tmp)


  def noc_wait_cmd_ready(self, noc: int, buf: int, *, addr: R = R.T0, val: R = R.T1):
    self.li(addr, self.noc_cmd_addr(noc, buf, NOC.CMD_CTRL))
    loop = self._new_label("noc_ready")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bne(val, R.ZERO, loop)
    return self


  def noc_reads_flushed(self, noc: int, target: R, *, addr: R = R.T0, val: R = R.T1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("rd_flush")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self.fence()

  def noc_nonposted_writes_flushed(self, noc: int, target: R, *, addr: R = R.T0, val: R = R.T1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("np_wr_flush")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self.fence()

  def noc_read(self, noc: int, buf: int, src_lo: R, src_mid: int | R, src_coord: int | R,
               dst: R, length: R, *, ret_coord: int | R = 0, a: R = R.T0, v: R = R.T1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_RD_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, src_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, src_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_write(self, noc: int, buf: int, src: R, dst_lo: R, dst_mid: int | R, dst_coord: R,
                length: R, *, mcast: bool = False, mcast_linked: bool = False,
                num_dests: R | None = None, posted: bool = False, a: R = R.T0, v: R = R.T1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    if mcast:
      ctrl = NOC.CMD_WR_MCAST_LINKED_FIELD if mcast_linked else NOC.CMD_WR_MCAST_UNLINK_FIELD
    else:
      ctrl = NOC.CMD_WR_POSTED_FIELD if posted else NOC.CMD_WR_FIELD
    self.noc_cmd_reg(noc, buf, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self


  def noc_atomic_inc(self, noc: int, buf: int, dst_lo: R, dst_coord: int | R,
                     incr: R | int, ret_coord: int | R, *, a: R = R.T0, v: R = R.T1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, 4, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_AT_INC_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, NOC.AT_INCR_GET, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_DATA, incr, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_semaphore_inc(self, noc: int, buf: int, sem_addr: R, sem_coord: int | R,
                        incr: int | R = 1, *, ret_coord: int | R = 0, a: R = R.T0, v: R = R.T1):
    return self.noc_atomic_inc(noc, buf, sem_addr, sem_coord, incr, ret_coord, a=a, v=v)

  def noc_semaphore_set_multicast(self, noc: int, buf: int, sem_addr: R, sem_coord: R,
                                  value: int | R, num_dests: int | R, *,
                                  a: R = R.T0, v: R = R.T1):
    if not (isinstance(value, int) and not isinstance(value, R)):
      self.sw(value, sem_addr, 0)
    else:
      self.li(v, value)
      self.sw(v, sem_addr, 0)
    length = R.T5 if int(v) == int(R.T2) else R.T2
    self.li(length, L1_ALIGN)
    self.noc_write(noc, buf, sem_addr, sem_addr, 0, sem_coord, length, mcast=True, a=a, v=v)
    return self
