from __future__ import annotations

import enum, json, os, pickle, socket, struct
from dataclasses import asdict

PORT = 7140
REQ = "<BIIQQQ"   # cmd, dev_id, handle, arg0, arg1, arg2
RESP = "<BQQ"     # status, ret0, ret1


class Cmd(enum.IntEnum):
  LIST, OPEN, CLOSE, ALLOC_TLB, FREE_TLB, CONFIG_TLB, MAP_TLB, MAP_BAR4, MAP_READ, MAP_WRITE, MAP_CLOSE, FLUSH, \
  TELEMETRY_LAYOUT, TELEMETRY_TAG, BOARD_INFO, ARC_READ, ARC_WRITE, ARC_MSG, POWER, RESET_INDEX, RESET_BDF, \
  RUN_IR, DRAM_WRITE, DRAM_READ = range(24)


def remote_addr() -> tuple[str, int]:
  host, sep, port = os.environ.get("REMOTE", "").partition(":")
  if not sep:
    raise RuntimeError("REMOTE must be host:port")
  return host, int(port)


def recvall(sock: socket.socket, n: int) -> bytes:
  data = b""
  while len(data) < n:
    chunk = sock.recv(n - len(data))
    if not chunk: raise RuntimeError("remote PCIe connection closed")
    data += chunk
  return data


def jpack(x) -> bytes: return json.dumps(x, separators=(",", ":")).encode()
def junpack(x: bytes): return json.loads(x.decode())


def layout_fix(layout):
  if layout is not None and "tag_to_offset" in layout:
    layout = dict(layout)
    layout["tag_to_offset"] = {int(k): int(v) for k, v in layout["tag_to_offset"].items()}
  return layout


def board_fix(x):
  from pcie import BoardInfo
  return BoardInfo(
    board=x["board"],
    worker_cores=[tuple(c) for c in x["worker_cores"]],
    program_cores=[tuple(c) for c in x["program_cores"]],
    dram_tiles=[tuple(t) for t in x["dram_tiles"]],
    prefetch_core=tuple(x["prefetch_core"]),
    dispatch_core=tuple(x["dispatch_core"]),
    harvested_dram_bank=x["harvested_dram_bank"],
  )


class RemoteMapping:
  def __init__(self, dev: "RemotePCIDevice", handle: int, size: int):
    self.dev, self.handle, self.size, self.closed, self.u32 = dev, handle, size, False, None

  def __len__(self): return self.size

  def check(self, off: int, size: int):
    if self.closed: raise ValueError("remote mapping is closed")
    if off < 0 or size < 0 or off + size > self.size:
      raise ValueError(f"remote mapping range out of bounds: offset=0x{off:x} size=0x{size:x} mapping_size=0x{self.size:x}")

  def read(self, off: int, size: int) -> bytes:
    self.check(off, size)
    return self.dev.rpc(Cmd.MAP_READ, self.handle, off, size, readout=size)[2]

  def write(self, off: int, data): self.copy_from(off, data)

  def copy_from(self, off: int, src, size: int | None = None) -> int:
    view = memoryview(src)
    size = view.nbytes if size is None else size
    self.check(off, size)
    if size > view.nbytes: raise ValueError(f"source buffer too small: need {size} bytes, have {view.nbytes}")
    if not view.c_contiguous: raise ValueError("source buffer must be C-contiguous")
    self.dev.rpc(Cmd.MAP_WRITE, self.handle, off, size, payload=bytes(view.cast("B")[:size]))
    return size

  def copy_to(self, off: int, dst, size: int | None = None) -> int:
    view = memoryview(dst)
    size = view.nbytes if size is None else size
    self.check(off, size)
    if view.readonly: raise ValueError("destination buffer must be writable")
    if size > view.nbytes: raise ValueError(f"destination buffer too small: need {size} bytes, have {view.nbytes}")
    if not view.c_contiguous: raise ValueError("destination buffer must be C-contiguous")
    view.cast("B")[:size] = self.read(off, size)
    return size

  def view_at(self, off: int = 0, size: int | None = None):
    raise RuntimeError("remote mappings do not expose local memoryviews")

  def flush(self, off: int = 0, size: int | None = None):
    size = self.size - off if size is None else size
    self.check(off, size)
    self.dev.rpc(Cmd.FLUSH, self.handle, off, size)

  def close(self):
    if not self.closed:
      self.closed = True
      self.dev.rpc(Cmd.MAP_CLOSE, self.handle)


class RemotePCIDevice:
  @staticmethod
  def connect() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect(remote_addr())
    return sock

  @staticmethod
  def rpc_on(sock: socket.socket, dev_id: int, cmd: Cmd, handle=0, arg0=0, arg1=0, arg2=0, payload=b"", readout=0):
    sock.sendall(struct.pack(REQ, int(cmd), dev_id, handle, arg0, arg1, arg2) + payload)
    status, r0, r1 = struct.unpack(RESP, recvall(sock, struct.calcsize(RESP)))
    if status: raise RuntimeError(recvall(sock, r0).decode() if r0 else f"remote RPC failed: {cmd.name}")
    return r0, r1, recvall(sock, readout) if readout else b""

  @classmethod
  def list_devices(cls) -> list[str]:
    sock = cls.connect()
    try:
      n, count, _ = cls.rpc_on(sock, 0, Cmd.LIST)
      return recvall(sock, n).decode().splitlines()[:count]
    finally:
      sock.close()

  @classmethod
  def reset_index(cls, index: int = 0):
    sock = cls.connect()
    try: cls.rpc_on(sock, 0, Cmd.RESET_INDEX, arg0=index)
    finally: sock.close()

  @staticmethod
  def reset_bdf(bdf: str):
    sock = RemotePCIDevice.connect()
    try: RemotePCIDevice.rpc_on(sock, 0, Cmd.RESET_BDF, arg0=len(bdf), payload=bdf.encode())
    finally: sock.close()

  def __init__(self, index: int = 0, use_vfio: bool = True):
    self.sock, self._closed = self.connect(), False
    n, self._tlb_4g_count, _ = self.rpc_on(self.sock, 0, Cmd.OPEN, arg0=index, arg1=int(use_vfio))
    info = junpack(recvall(self.sock, n))
    self.dev_id, self.sysfs, self.bdf = info["dev_id"], info["sysfs"], info["bdf"]

  def rpc(self, cmd: Cmd, handle=0, arg0=0, arg1=0, arg2=0, payload=b"", readout=0):
    return self.rpc_on(self.sock, self.dev_id, cmd, handle, arg0, arg1, arg2, payload, readout)

  def telemetry_layout(self):
    n, _, _ = self.rpc(Cmd.TELEMETRY_LAYOUT)
    return layout_fix(junpack(recvall(self.sock, n)))

  def telemetry_tag(self, layout, tag):
    payload = jpack({"layout": layout, "tag": tag})
    val, present, _ = self.rpc(Cmd.TELEMETRY_TAG, arg0=len(payload), payload=payload)
    return val if present else None

  def board_info(self, layout=None, fast_dispatch=False):
    payload = jpack({"layout": layout, "fast_dispatch": fast_dispatch})
    n, _, _ = self.rpc(Cmd.BOARD_INFO, arg0=len(payload), payload=payload)
    return board_fix(junpack(recvall(self.sock, n)))

  def read_arc_apb32(self, off: int) -> int: return self.rpc(Cmd.ARC_READ, arg0=off)[0]
  def write_arc_apb32(self, off: int, val: int): self.rpc(Cmd.ARC_WRITE, arg0=off, arg1=val)
  def arc_msg(self, msg: int, arg0: int = 0, arg1: int = 0, timeout_ms: int = 1000) -> int:
    return self.rpc(Cmd.ARC_MSG, arg0=msg, arg1=arg0, arg2=arg1, payload=struct.pack("<I", timeout_ms))[0]
  def set_power_state(self, busy: bool): self.rpc(Cmd.POWER, arg0=int(busy))

  def run_ir(self, commands):
    payload = pickle.dumps(commands, protocol=5)
    self.rpc(Cmd.RUN_IR, arg0=len(payload), payload=payload)

  def dram_write(self, bank_tiles, buf, data):
    view = memoryview(data)
    if not view.c_contiguous: raise ValueError("source buffer must be C-contiguous")
    payload = pickle.dumps((bank_tiles, buf, bytes(view.cast("B"))), protocol=5)
    self.rpc(Cmd.DRAM_WRITE, arg0=len(payload), payload=payload)

  def dram_read(self, bank_tiles, buf) -> bytes:
    payload = pickle.dumps((bank_tiles, buf), protocol=5)
    n, _, _ = self.rpc(Cmd.DRAM_READ, arg0=len(payload), payload=payload)
    return recvall(self.sock, n)

  def alloc_tlb(self, size: int) -> int: return self.rpc(Cmd.ALLOC_TLB, arg0=size)[0]
  def free_tlb(self, index: int): self.rpc(Cmd.FREE_TLB, arg0=index)

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int, x_end: int, y_end: int,
                    noc: int = 0, mcast: int = 0, ordering: int = 1, linked: int = 0, static_vc: int = 0):
    self.rpc(Cmd.CONFIG_TLB, arg0=index, payload=struct.pack("<QBBBBBBBBB", addr, x_start, y_start, x_end, y_end, noc, mcast, ordering, linked, static_vc))

  def tlb_window(self, index: int, wc: bool = False):
    handle, size, _ = self.rpc(Cmd.MAP_TLB, arg0=index, arg1=int(wc))
    return RemoteMapping(self, handle, size)

  def map_bar4_window(self, window: int, size: int):
    handle, size, _ = self.rpc(Cmd.MAP_BAR4, arg0=window, arg1=size)
    return RemoteMapping(self, handle, size)

  def pin_pages(self, buf, preferred_iatu_region=None): raise RuntimeError("remote DMA/sysmem pinning is not implemented")
  def unpin_pages(self, buf, noc_addr: int): raise RuntimeError("remote DMA/sysmem pinning is not implemented")

  def close(self):
    if self._closed: return
    self._closed = True
    try: self.rpc(Cmd.CLOSE)
    finally: self.sock.close()

  def __enter__(self): return self
  def __exit__(self, exc_type, exc, tb): self.close()

  def __getattr__(self, name: str):
    if name.isupper():
      from pcie import PCIDevice
      if hasattr(PCIDevice, name): return getattr(PCIDevice, name)
    raise AttributeError(name)
