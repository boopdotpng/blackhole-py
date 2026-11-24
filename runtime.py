from __future__ import annotations
import atexit, copy, math, time
import numpy as np
import fw, hw
from device import Device as RawDevice

# name: (bytes per element, None for block-float; bytes per 1024-element tile)
TYPES = {
  "bf16": (2, 2048), "fp16": (2, 2048), "fp32": (4, 4096),
  "e4m3": (1, 1024), "e5m2": (1, 1024),
  "bfp8": (None, 1088), "bfp4": (None, 576),
  "u8": (1, 1024), "u32": (4, 4096), "i32": (4, 4096), "u64": (8, 8192),
}
NUMPY = {
  "bf16": np.uint16, "fp16": np.float16, "fp32": np.float32,
  "e4m3": np.uint8, "e5m2": np.uint8, "u8": np.uint8,
  "u32": np.uint32, "i32": np.int32, "u64": np.uint64,
  "bfp8": np.uint8, "bfp4": np.uint8,
}
FROM_NUMPY = {
  np.dtype(np.float32): "fp32", np.dtype(np.float16): "fp16",
  np.dtype(np.uint32): "u32", np.dtype(np.int32): "i32",
  np.dtype(np.uint64): "u64", np.dtype(np.uint8): "u8",
}


class Buffer:
  def __init__(self, device: Device, shape, dtype: str, host: bool = False, tiles_per_page: int = 1):
    if dtype not in TYPES: raise ValueError(f"unknown type {dtype!r}")
    self.device, self.shape, self.dtype, self.host = device, tuple(shape), dtype, host
    self.nbytes = int(np.prod(self.shape, dtype=np.int64)) * np.dtype(NUMPY[dtype]).itemsize
    raw = device.raw
    if tiles_per_page < 1 or tiles_per_page * TYPES[dtype][1] > hw.NOC_MAX_BURST or (host and tiles_per_page != 1):
      raise ValueError("invalid tiles_per_page")
    if host:
      self.offset = raw.alloc_host(max(self.nbytes, 64))
      self.addr = raw.host.noc_addr + self.offset
    else:
      self.addr = raw.allocator.alloc(self.nbytes, tiles_per_page * TYPES[dtype][1])

  def page_view(self, byte_offset: int, shape):
    if self.host: raise ValueError("expected a DRAM buffer")
    view = copy.copy(self)
    view.shape = (shape,) if isinstance(shape, int) else tuple(shape)
    view.nbytes = math.prod(view.shape) * np.dtype(NUMPY[self.dtype]).itemsize
    shift = self.addr >> 56 & 63
    page = 1 << shift if shift else ((self.addr >> 48 & 255) + 1) * 64
    if byte_offset < 0 or byte_offset % page or byte_offset + view.nbytes > self.nbytes or any(n < 0 for n in view.shape):
      raise ValueError("invalid DRAM page view")
    view.addr = self.addr + byte_offset
    return view

  def numpy(self) -> np.ndarray:
    # Host buffers return a live view: no copy and no synchronization with the device.
    if self.host: return np.ndarray(self.shape, NUMPY[self.dtype], self.device.raw.host.mem, self.offset)
    out = np.empty(self.shape, NUMPY[self.dtype])
    if self.nbytes: self.device.raw.allocator.copyout(out, self.addr)
    return out

  def copy_from(self, x):
    if self.host:
      self.numpy().reshape(-1).view(np.uint8)[:] = np.frombuffer(np.ascontiguousarray(x), np.uint8)
      return self
    data = memoryview(np.ascontiguousarray(x)).cast("B")
    if len(data) != self.nbytes: raise ValueError(f"{len(data)} bytes into a {self.nbytes}-byte buffer")
    self.device.raw.allocator.copyin(self.addr, data)
    return self

  def __repr__(self): return f"Buffer({self.shape}, {self.dtype}{', host' if self.host else ''})"


class HostStream:
  def __init__(self, device: Device, capacity: int):
    # u32[0] is the written counter, padded to 64 bytes; the payload ring starts at u32[16].
    self.capacity = capacity
    self.buf = device.zeros(16 + capacity, "u32", host=True)
    self.view = self.buf.numpy()
    self.count_addr = self.buf.addr
    self.data_addr = self.buf.addr + 64
    self.read_idx = 0

  @property
  def written(self) -> int: return int(self.view[0])

  def poll(self) -> np.ndarray:
    w = self.written
    if w <= self.read_idx: return np.empty(0, dtype=np.uint32)
    idxs = np.arange(self.read_idx, w, dtype=np.int64) % self.capacity
    self.read_idx = w
    return self.view[16 + idxs].copy()

  def wait(self, target: int, timeout: float = 10.0) -> np.ndarray:
    deadline = time.monotonic() + timeout
    while self.written < target:
      if time.monotonic() > deadline:
        raise TimeoutError(f"HostStream timed out at written={self.written}, waiting for {target}")
    return self.poll()


class Device:
  def __init__(self, index: int = 0):
    self.raw = RawDevice(index)
    atexit.register(self.close)

  @property
  def num_workers(self) -> int: return len(self.raw.workers)

  @property
  def workers(self) -> list[tuple[int, int]]: return self.raw.workers

  def empty(self, shape, dtype: str, host: bool = False, *, tiles_per_page: int = 1) -> Buffer:
    return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host, tiles_per_page)

  def zeros(self, shape, dtype: str, host: bool = False) -> Buffer:
    b = self.empty(shape, dtype, host)
    if host:
      b.numpy().fill(0)
      return b
    chunk = bytes(min(b.nbytes, 16 << 20))
    for off in range(0, b.nbytes, len(chunk) or 1):
      self.raw.allocator.copyin(b.addr + off, memoryview(chunk)[:min(len(chunk), b.nbytes - off)])
    return b

  def array(self, x, dtype: str | None = None) -> Buffer:
    x = np.asarray(x)
    if dtype == "bf16" and x.dtype.kind == "f":
      u = x.astype(np.float32).view(np.uint32).astype(np.uint64)
      x = ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
    dtype = dtype or FROM_NUMPY.get(x.dtype)
    if dtype is None: raise TypeError(f"no runtime type for {x.dtype}; pass dtype=")
    return self.empty(x.shape, dtype).copy_from(x)

  def stream(self, capacity: int = 4096) -> HostStream:
    return HostStream(self, capacity)

  def run(self, images: dict[str, bytes], data: dict[int, bytes] | None = None, cores=None) -> int:
    blob, pcs, code_end = fw.pack_megakernel(images)
    self.raw.run_workers(blob, pcs, data=data, cores=cores)
    return code_end

  def stop(self):
    self.raw.stop_workers()

  def read_l1(self, core: int | tuple[int, int], addr: int, size: int) -> bytes:
    xy = self.raw.workers[core] if isinstance(core, int) else core
    return self.raw.card.read(xy, addr, size)

  def write_l1(self, core: int | tuple[int, int] | None, addr: int, data: bytes):
    if core is None:
      for rect in self.raw.worker_rects: self.raw.card.write(rect, addr, data)
    else:
      xy = self.raw.workers[core] if isinstance(core, int) else core
      self.raw.card.write(xy, addr, data)

  def close(self):
    self.raw.close()
