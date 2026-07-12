from contextlib import AbstractContextManager, contextmanager

from asm import Cond
from isa import R

NOC_REGS_START_ADDR = 0xFFB20000
NOC_CFG_BASE = NOC_REGS_START_ADDR + 0x100
NOC_STATUS_BASE = 0xFFB20200
NOC_CMD_BUF_OFFSET_BIT = 11
NOC_INSTANCE_OFFSET_BIT = 16

NOC_TARG_ADDR_LO = 0x00
NOC_TARG_ADDR_MID = 0x04
NOC_TARG_ADDR_COORDINATE = 0x08
NOC_RET_ADDR_LO = 0x0C
NOC_RET_ADDR_MID = 0x10
NOC_RET_ADDR_COORDINATE = 0x14
NOC_PACKET_TAG = 0x18
NOC_CTRL = 0x1C
NOC_AT_LEN_BE = 0x20
NOC_AT_LEN_BE_1 = 0x24
NOC_AT_DATA = 0x28
NOC_BRCST_EXCLUDE = 0x2C
NOC_CMD_CTRL = 0x40
NOC_MAX_BURST_SIZE = 16 * 1024

NOC_ID_LOGICAL = 0x12

NIU_MST_ATOMIC_RESP_RECEIVED = 0x00
NIU_MST_WR_ACK_RECEIVED = 0x04
NIU_MST_RD_RESP_RECEIVED = 0x08
NIU_MST_POSTED_WR_REQ_SENT = 0x2C


class NocCfg:
  """NoC configuration values shared by resident firmware and kernels."""
  NIU_CFG_0 = 0
  ROUTER_CFG_0 = 1
  NODE_ID_MASK = 0x3F
  ADDR_NODE_ID_BITS = 6
  MEM_NOC_ATOMIC_RET_VAL_ADDR = 0x04
  NCRISC_WR_CMD_BUF = 0
  NCRISC_RD_CMD_BUF = 1
  NCRISC_WR_REG_CMD_BUF = 2
  NCRISC_AT_CMD_BUF = 3
  RD_CMD_FIELD = (1 << 4) | (1 << 7) | (1 << 13)

NOC_CTRL_SEND_REQ = 1
NOC_CMD_AT = 1
NOC_CMD_WR = 1 << 1
NOC_CMD_RESP_MARKED = 1 << 4
NOC_CMD_BRCST_PACKET = 1 << 5
NOC_CMD_VC_LINKED = 1 << 6
NOC_CMD_VC_STATIC = 1 << 7
NOC_CMD_PATH_RESERVE = 1 << 8
NOC_CMD_STATIC_VC_1 = 1 << 13
NOC_CMD_STATIC_VC_5 = 5 << 13
NOC_CMD_BRCST_XY = 1 << 16

NOC_CMD_RD_FIELD = NOC_CMD_RESP_MARKED | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_CMD_WR_FIELD = NOC_CMD_WR | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_CMD_WR_MCAST_FIELD = (NOC_CMD_WR | NOC_CMD_VC_STATIC |
                          NOC_CMD_STATIC_VC_5 | NOC_CMD_BRCST_PACKET | NOC_CMD_PATH_RESERVE)
NOC_CMD_AT_INC_FIELD = NOC_CMD_AT | NOC_CMD_RESP_MARKED | NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1
NOC_AT_INCR_GET = 1 << 12 | 31 << 2

Value = int | R
_WRITE_BUFFER, _READ_BUFFER, _ATOMIC_BUFFER = 0, 1, 3

class _CounterTicket:
  def __init__(self, noc, start: R, status: int, buffer: int):
    self.noc, self.asm, self.start, self.status, self.buffer = noc, noc.asm, start, status, buffer

  def wait(self, count: Value):
    if type(count) is int and not 0 <= count < 1 << 31: raise ValueError("batch count must satisfy 0 <= count < 2^31")
    with self.asm.scope():
      addr, current, delta = self.asm.reg(3)
      expected = count if isinstance(count, R) else self.asm.reg()
      if not isinstance(count, R): self.asm.li(expected, count)
      self.asm.li(addr, self.noc._base(self.buffer))
      with self.asm.loop():
        self.asm.lw(current, addr, NOC_CMD_CTRL)
        self.asm.break_(Cond(current, "==", 0))
      self.asm.li(addr, NOC_STATUS_BASE + (self.noc.index << NOC_INSTANCE_OFFSET_BIT) + self.status)
      with self.asm.loop():
        self.asm.lw(current, addr)
        self.asm.sub(delta, current, self.start)
        self.asm.break_(Cond(delta, ">=u", expected))
    self.asm.fence()
    return self.noc

class _CompletionBatch:
  def __init__(self, noc, status: int, buffer: int, count: Value | None = None, owner=None):
    self.noc, self.status, self.buffer, self.count, self.owner = noc, status, buffer, count, owner
    self.ticket, self.issued, self.active = None, 0, False

  def __enter__(self):
    if self.ticket is not None: raise RuntimeError("NoC batch cannot be entered more than once")
    if self.buffer in self.noc._batches: raise RuntimeError("NoC command buffer already has an active batch")
    if self.owner is None and self.buffer in self.noc._streams:
      raise RuntimeError("NoC command buffer is owned by an active stream")
    if self.owner is not None and self.owner._batch is not None:
      raise RuntimeError("NoC stream already has an active batch")
    self.ticket = self.noc._ticket(self.status, self.buffer)
    self.noc._batches[self.buffer] = self
    if self.owner is not None: self.owner._batch = self
    self.active = True
    return self

  def __exit__(self, exc_type, exc, tb):
    if self.owner is not None: self.owner._batch = None
    del self.noc._batches[self.buffer]
    self.active = False
    if exc_type is None: self.ticket.wait(self.issued if self.count is None else self.count)

  def _record(self, count: int = 1):
    if not self.active: raise RuntimeError("NoC batch operation requires an active context")
    self.issued += count

  def _require_active(self):
    if not self.active: raise RuntimeError("NoC batch operation requires an active context")

class _Stream:
  def __init__(self, noc, base: R, scratch: R, send: R):
    self.noc, self.asm, self.base, self.scratch, self.send = noc, noc.asm, base, scratch, send
    self._batch = None

  def _ready(self):
    with self.asm.loop():
      self.asm.lw(self.scratch, self.base, NOC_CMD_CTRL)
      self.asm.break_(Cond(self.scratch, "==", 0))

  def _write(self, register: int, value: Value):
    if not isinstance(value, R): self.asm.li(self.scratch, value); value = self.scratch
    self.asm.sw(value, self.base, register)

  def _send(self): self.asm.sw(self.send, self.base, NOC_CMD_CTRL)

  def _record(self):
    if self._batch is not None: self._batch._record()

class ReadStream(_Stream):

  def issue(self, src: Value, src_coord: Value, dst: Value):
    """Issue one fixed-size read using this stream's invariant setup."""
    self._ready()
    self._write(NOC_TARG_ADDR_LO, src)
    self._write(NOC_TARG_ADDR_COORDINATE, src_coord)
    self._write(NOC_RET_ADDR_LO, dst)
    self._send()
    self._record()

  def batch(self, count: Value | None = None):
    """Wait for this stream's issued reads when the context exits."""
    return _CompletionBatch(self.noc, NIU_MST_RD_RESP_RECEIVED, _READ_BUFFER, count, self)

class WriteStream(_Stream):

  def issue(self, src: Value, dst: Value, dst_coord: Value):
    """Issue one fixed-size write using this stream's invariant setup."""
    self._ready()
    self._write(NOC_TARG_ADDR_LO, src)
    self._write(NOC_RET_ADDR_LO, dst)
    self._write(NOC_RET_ADDR_COORDINATE, dst_coord)
    self._send()
    self._record()

  def batch(self, count: Value | None = None):
    """Wait for this stream's issued writes when the context exits."""
    return _CompletionBatch(self.noc, NIU_MST_POSTED_WR_REQ_SENT, _WRITE_BUFFER, count, self)

class ReadBatch(_CompletionBatch):

  def issue(self, src: Value, src_coord: Value, dst: Value, size: Value, *,
            src_mid: Value = 0, return_coord: Value | None = None):
    """Issue a read tracked by this completion batch."""
    self._require_active()
    self.noc.read(src, src_coord, dst, size, src_mid=src_mid, return_coord=return_coord)

class WriteBatch(_CompletionBatch):

  def __init__(self, noc, status=NIU_MST_POSTED_WR_REQ_SENT, buffer=_WRITE_BUFFER,
               count=None, owner=None, *, posted=True):
    super().__init__(noc, status, buffer, count, owner)
    self.posted = posted

  def issue(self, src: Value, dst: Value, dst_coord: Value, size: Value, *, dst_mid: Value = 0):
    """Issue a write tracked by this completion batch."""
    self._require_active()
    self.noc.write(src, dst, dst_coord, size, dst_mid=dst_mid, posted=self.posted)

  def multicast(self, src: Value, dst: Value, dst_coord: Value, size: int, *, exclude: Value = 0, along_y=False):
    """Issue multicast packets tracked by this completion batch."""
    self._require_active()
    packets = self.noc.multicast(src, dst, dst_coord, size, exclude=exclude, along_y=along_y)
    return packets

  def multicast_packet(self, src: Value, dst: Value, dst_coord: Value, size: Value, *,
                       exclude: Value = 0, along_y=False):
    """Issue one unlinked runtime-sized multicast packet."""
    self._require_active()
    self.noc._multicast(src, dst, dst_coord, size, linked=False, reserve_path=True,
                        exclude=exclude, along_y=along_y, posted=self.posted)
    self._record()
    return self

class AtomicBatch(_CompletionBatch):

  def issue(self, dst: Value, dst_coord: Value, value: Value = 1, *, return_coord: Value | None = None):
    """Issue an atomic increment tracked by this completion batch."""
    self._require_active()
    self.noc.atomic_inc(dst, dst_coord, value, return_coord=return_coord)

class NoC:

  def __init__(self, asm, index: int):
    if type(index) is not int or index not in (0, 1): raise ValueError("NoC index must be 0 or 1")
    if getattr(asm, "role", None) not in ("brisc", "ncrisc"):
      raise ValueError("NoC requires a BRISC or NCRISC kernel builder")
    self.asm, self.index = asm, index
    self.local_coord, self.atomic_return = None, 4
    self._streams, self._batches = set(), {}

  @staticmethod
  def static_coord(x: int, y: int):
    """Pack Python X and Y coordinates into a unicast NoC coordinate."""
    if type(x) is not int or type(y) is not int: raise TypeError("static coordinates require Python integers")
    return x | y << 6

  def _base(self, buffer: int):
    return NOC_REGS_START_ADDR + (self.index << NOC_INSTANCE_OFFSET_BIT) + (buffer << NOC_CMD_BUF_OFFSET_BIT)

  def _cfg_addr(self, register: int):
    return NOC_CFG_BASE + (self.index << NOC_INSTANCE_OFFSET_BIT) + register * 4

  def _stores(self, base: R, value: R, registers: dict[int, Value]):
    for reg, val in registers.items():
      if isinstance(val, R): self.asm.sw(val, base, reg)
    literals = {}
    for reg, val in registers.items():
      if type(val) is int: literals.setdefault(val, []).append(reg)
    last = None
    for val, registers in literals.items():
      self.asm.li(value, val)
      for reg in registers: self.asm.sw(value, base, reg)
      last = val
    return last

  def _issue(self, buffer: int, registers: dict[int, Value]):
    if buffer in self._streams: raise RuntimeError("NoC command buffer is owned by an active stream")
    with self.asm.scope():
      base, value = self.asm.reg(2)
      self.asm.li(base, self._base(buffer))
      with self.asm.loop():
        self.asm.lw(value, base, NOC_CMD_CTRL)
        self.asm.break_(Cond(value, "==", 0))
      if self._stores(base, value, registers) != NOC_CTRL_SEND_REQ: self.asm.li(value, NOC_CTRL_SEND_REQ)
      self.asm.sw(value, base, NOC_CMD_CTRL)
    if batch := self._batches.get(buffer): batch._record()
    return self

  @contextmanager
  def _stream(self, buffer: int, registers: dict[int, Value], cls):
    if buffer in self._streams: raise RuntimeError("NoC command buffer already has an active stream")
    if buffer in self._batches: raise RuntimeError("NoC command buffer is owned by an active batch")
    self._streams.add(buffer)
    try:
      with self.asm.scope():
        base, scratch, send = self.asm.reg(3)
        self.asm.li(base, self._base(buffer))
        with self.asm.loop():
          self.asm.lw(scratch, base, NOC_CMD_CTRL)
          self.asm.break_(Cond(scratch, "==", 0))
        self._stores(base, scratch, registers)
        self.asm.li(send, NOC_CTRL_SEND_REQ)
        yield cls(self, base, scratch, send)
    finally: self._streams.remove(buffer)

  def initialize(self, local_coord: Value, atomic_return: Value = 4):
    """Record the initiating coordinate and local atomic-return address."""
    self.local_coord, self.atomic_return = local_coord, atomic_return
    return self

  def init_firmware_command_buffers(self, coord: Value, *,
                                    atomic_return: Value = NocCfg.MEM_NOC_ATOMIC_RET_VAL_ADDR,
                                    read_ctrl: int = NocCfg.RD_CMD_FIELD,
                                    write_buffer: int = NocCfg.NCRISC_WR_CMD_BUF,
                                    read_buffer: int = NocCfg.NCRISC_RD_CMD_BUF,
                                    write_reg_buffer: int = NocCfg.NCRISC_WR_REG_CMD_BUF,
                                    atomic_buffer: int = NocCfg.NCRISC_AT_CMD_BUF):
    """Seed the command-buffer fields used by resident BRISC/NCRISC code.

    This is initialization, not a data transfer: it writes invariant NoC
    fields once so later firmware operations only fill in addresses/lengths.
    The launch/dispatch policy remains in ``fw/brisc.py``.
    """
    self.initialize(coord, atomic_return)
    for buf, registers in (
      (write_buffer, {NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: coord}),
      (write_reg_buffer, {NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: coord}),
      (atomic_buffer, {NOC_RET_ADDR_LO: atomic_return, NOC_RET_ADDR_MID: 0,
                       NOC_RET_ADDR_COORDINATE: coord}),
      (read_buffer, {NOC_CTRL: read_ctrl, NOC_RET_ADDR_MID: 0,
                     NOC_RET_ADDR_COORDINATE: coord}),
    ):
      for register, value in registers.items():
        self.asm.write32(self._base(buf) + register, value)
    return self

  def store_risc_coordinates(self, x_addr: int, y_addr: int):
    """Read this NoC's hardware ID and store its X/Y coordinates."""
    with self.asm.scope():
      id_reg, coord = self.asm.reg(2)
      self.asm.read32(id_reg, self._cfg_addr(NOC_ID_LOGICAL))
      self.asm.andi(coord, id_reg, NocCfg.NODE_ID_MASK)
      self.asm.write8(x_addr + self.index, coord)
      self.asm.srli(id_reg, id_reg, NocCfg.ADDR_NODE_ID_BITS)
      self.asm.andi(id_reg, id_reg, NocCfg.NODE_ID_MASK)
      self.asm.write8(y_addr + self.index, id_reg)
    return self

  def init_resident(self):
    """Initialize one resident BRISC's fixed NoC command-buffer state.

    Logical coordinates come from hardware because one firmware image is
    multicast to every worker.  This deliberately does not update the saved
    X/Y bytes: the old firmware stored those once at boot but reinitialized
    command buffers before every launch.
    """
    with self.asm.scope():
      id_reg, coord = self.asm.reg(2)
      self.asm.read32(id_reg, self._cfg_addr(NOC_ID_LOGICAL))
      self.asm.andi(coord, id_reg, NocCfg.NODE_ID_MASK)
      self.asm.srli(id_reg, id_reg, NocCfg.ADDR_NODE_ID_BITS)
      self.asm.andi(id_reg, id_reg, NocCfg.NODE_ID_MASK)
      self.asm.slli(id_reg, id_reg, NocCfg.ADDR_NODE_ID_BITS)
      self.asm.or_(coord, coord, id_reg)
      self.init_firmware_command_buffers(coord)
    return self

  def _local(self, coord: Value | None):
    coord = self.local_coord if coord is None else coord
    if coord is None: raise RuntimeError("NoC.initialize() requires the local coordinate")
    return coord

  @staticmethod
  def _size(size: int):
    if isinstance(size, R): return size
    if type(size) is not int or not 0 < size <= NOC_MAX_BURST_SIZE:
      raise ValueError(f"NoC transfer must be between 1 and {NOC_MAX_BURST_SIZE} bytes")
    return size

  def read(self, src: Value, src_coord: Value, dst: Value, size: Value, *,
           src_mid: Value = 0, return_coord: Value | None = None):
    """Issue a remote read into local L1 without waiting for completion."""
    self._size(size)
    registers = {NOC_CTRL: NOC_CMD_RD_FIELD,
                 NOC_RET_ADDR_LO: dst, NOC_RET_ADDR_MID: 0, NOC_RET_ADDR_COORDINATE: self._local(return_coord),
                 NOC_TARG_ADDR_LO: src, NOC_TARG_ADDR_MID: src_mid, NOC_TARG_ADDR_COORDINATE: src_coord,
                 NOC_AT_LEN_BE: size, NOC_AT_LEN_BE_1: 0}
    return self._issue(_READ_BUFFER, registers)

  def read_stream(self, size: int, *, return_coord: Value | None = None) -> AbstractContextManager[ReadStream]:
    """Create a context that reuses fixed read command fields."""
    self._size(size)
    return self._stream(_READ_BUFFER, {NOC_CTRL: NOC_CMD_RD_FIELD, NOC_PACKET_TAG: 0,
      NOC_TARG_ADDR_MID: 0, NOC_RET_ADDR_MID: 0, NOC_RET_ADDR_COORDINATE: self._local(return_coord),
      NOC_AT_LEN_BE: size, NOC_AT_LEN_BE_1: 0}, ReadStream)

  def read_batch(self, count: Value | None = None) -> AbstractContextManager[ReadBatch]:
    """Create a read batch that waits for completion on context exit."""
    return ReadBatch(self, NIU_MST_RD_RESP_RECEIVED, _READ_BUFFER, count)

  def write(self, src: Value, dst: Value, dst_coord: Value, size: Value, *,
            dst_mid: Value = 0, posted=True):
    """Issue a posted local-L1-to-remote write without waiting."""
    self._size(size)
    ctrl = NOC_CMD_WR_FIELD if posted else NOC_CMD_WR_FIELD | NOC_CMD_RESP_MARKED
    return self._issue(_WRITE_BUFFER, {NOC_CTRL: ctrl, NOC_PACKET_TAG: 0,
      NOC_TARG_ADDR_LO: src, NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: self._local(None),
      NOC_RET_ADDR_LO: dst, NOC_RET_ADDR_MID: dst_mid,
      NOC_RET_ADDR_COORDINATE: dst_coord, NOC_AT_LEN_BE: size, NOC_AT_LEN_BE_1: 0})

  def write_stream(self, size: int) -> AbstractContextManager[WriteStream]:
    """Create a context that reuses fixed write command fields."""
    self._size(size)
    return self._stream(_WRITE_BUFFER, {NOC_CTRL: NOC_CMD_WR_FIELD, NOC_PACKET_TAG: 0,
      NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: self._local(None), NOC_RET_ADDR_MID: 0,
      NOC_AT_LEN_BE: size, NOC_AT_LEN_BE_1: 0}, WriteStream)

  def write_batch(self, count: Value | None = None) -> AbstractContextManager[WriteBatch]:
    """Create a write batch that waits for issue completion on exit."""
    return WriteBatch(self, NIU_MST_POSTED_WR_REQ_SENT, _WRITE_BUFFER, count)

  def write_ack_batch(self, count: Value | None = None) -> AbstractContextManager[WriteBatch]:
    """Create a nonposted write batch that waits for destination acknowledgements."""
    return WriteBatch(self, NIU_MST_WR_ACK_RECEIVED, _WRITE_BUFFER, count, posted=False)

  def _multicast(self, src: Value, dst: Value, dst_coord: Value, size: Value, *, linked: bool,
                 reserve_path: bool, exclude: Value, along_y: bool, dst_mid: Value = 0,
                 posted=True):
    ctrl = NOC_CMD_WR_MCAST_FIELD | (NOC_CMD_VC_LINKED if linked else 0) | (NOC_CMD_BRCST_XY if along_y else 0)
    if not posted: ctrl |= NOC_CMD_RESP_MARKED
    if not reserve_path: ctrl &= ~NOC_CMD_PATH_RESERVE
    return self._issue(_WRITE_BUFFER, {NOC_CTRL: ctrl, NOC_PACKET_TAG: 0,
      NOC_TARG_ADDR_LO: src, NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: self._local(None),
      NOC_RET_ADDR_LO: dst, NOC_RET_ADDR_MID: dst_mid, NOC_RET_ADDR_COORDINATE: dst_coord,
      NOC_BRCST_EXCLUDE: exclude, NOC_AT_LEN_BE: size, NOC_AT_LEN_BE_1: 0})

  def multicast(self, src: Value, dst: Value, dst_coord: Value, size: int, *, exclude: Value = 0, along_y=False):
    """Issue a possibly chunked multicast write and return its packet count."""
    if type(size) is not int or size <= 0: raise ValueError("multicast size must be a positive Python integer")
    chunks = (size + NOC_MAX_BURST_SIZE - 1) // NOC_MAX_BURST_SIZE
    with self.asm.scope():
      src_at, dst_at = src, dst
      moving = []
      if isinstance(src, R): self.asm.mv(src_at := self.asm.reg(), src); moving.append(src_at)
      if isinstance(dst, R): self.asm.mv(dst_at := self.asm.reg(), dst); moving.append(dst_at)
      step = self.asm.reg() if moving and chunks > 1 else None
      if step is not None: self.asm.li(step, NOC_MAX_BURST_SIZE)
      for i in range(chunks):
        chunk = min(NOC_MAX_BURST_SIZE, size - i * NOC_MAX_BURST_SIZE)
        self._multicast(src_at, dst_at, dst_coord, chunk, linked=i + 1 < chunks,
                        reserve_path=i == 0, exclude=exclude, along_y=along_y)
        if i + 1 < chunks:
          if isinstance(src_at, R): self.asm.add(src_at, src_at, step)
          else: src_at += chunk
          if isinstance(dst_at, R): self.asm.add(dst_at, dst_at, step)
          else: dst_at += chunk
    return chunks

  def atomic_inc(self, dst: Value, dst_coord: Value, value: Value = 1, *, return_coord: Value | None = None):
    """Issue a remote atomic increment that returns the previous value."""
    registers = {NOC_TARG_ADDR_LO: dst, NOC_TARG_ADDR_MID: 0, NOC_TARG_ADDR_COORDINATE: dst_coord,
                 NOC_RET_ADDR_LO: self.atomic_return, NOC_RET_ADDR_MID: 0,
                 NOC_RET_ADDR_COORDINATE: self._local(return_coord), NOC_PACKET_TAG: 0,
                 NOC_CTRL: NOC_CMD_AT_INC_FIELD, NOC_AT_LEN_BE: NOC_AT_INCR_GET,
                 NOC_AT_LEN_BE_1: 0, NOC_AT_DATA: value}
    return self._issue(_ATOMIC_BUFFER, registers)

  def atomic_batch(self, count: Value | None = None) -> AbstractContextManager[AtomicBatch]:
    """Create an atomic batch that waits for responses on context exit."""
    return AtomicBatch(self, NIU_MST_ATOMIC_RESP_RECEIVED, _ATOMIC_BUFFER, count)

  def _ticket(self, status: int, buffer: int):
    start = self.asm.reg()
    self.asm.load(start, NOC_STATUS_BASE + (self.index << NOC_INSTANCE_OFFSET_BIT) + status)
    self.asm.fence()
    return _CounterTicket(self, start, status, buffer)
