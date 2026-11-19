"""A CUDA-style runtime for TTRV kernels: device buffers, kernel launches, captured graphs.

  d = Device(0)                                # open card 0; it closes at exit
  x = d.array(np.ones(1024, np.float32))       # DRAM buffer, filled from the host
  y = d.empty(1024, "fp32")
  scale = d.kernel("scale.ttrv", N=1024)       # compile with N defined, install
  scale(x=x, y=y, k=2)                         # queued; returns at once
  y.numpy()                                    # waits for the device, copies back

  k = Var("k")
  with d.graph() as g:                         # launches are recorded, not run
    scale(x=x, y=y, k=k)
  g(k=3).wait()                                # replay with k bound to 3
"""

import atexit, mmap
from pathlib import Path
import numpy as np
import fw
from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, BlackholeGraph, dram
from helpers import Tensor
from .expand import TYPES

NUMPY = {"bf16": np.uint16, "fp16": np.float16, "fp32": np.float32, "e4m3": np.uint8, "e5m2": np.uint8, "u8": np.uint8,
         "u32": np.uint32, "i32": np.int32, "u64": np.uint64, "bfp8": np.uint8, "bfp4": np.uint8}
FROM_NUMPY = {np.dtype(np.float32): "fp32", np.dtype(np.float16): "fp16", np.dtype(np.uint32): "u32",
              np.dtype(np.int32): "i32", np.dtype(np.uint64): "u64", np.dtype(np.uint8): "u8"}
SAFETENSORS = {"BF16": "bf16", "F16": "fp16", "F32": "fp32", "F8_E4M3": "e4m3", "F8_E5M2": "e5m2", "U8": "u8",
               "I32": "i32", "U32": "u32"}
ARGS = fw.PARAM_SIZE  # one launch's argument block
RING = 256            # argument blocks for launches outside a graph, reused once their launch is done


class Var:
  """An integer kernel argument bound when a graph is replayed."""
  def __init__(self, name): self.name = name
  def __repr__(self): return f"Var({self.name!r})"


class Event:
  """Marks the work queued before it; wait() returns once the device has done that work."""
  def __init__(self, dev, value): self.dev, self.value = dev, value
  def wait(self, timeout=10.0): self.dev.timeline_signal.wait(self.value, timeout)
  @property
  def done(self): return self.dev.timeline_signal.value >= self.value


class Buffer:
  """shape elements of a TTRV type. DRAM buffers interleave over the 8 banks one tile of their type at a time; host
  buffers live in pinned host memory that kernels can write."""
  def __init__(self, device, shape, dtype, host=False):
    if dtype not in TYPES: raise ValueError(f"unknown type {dtype!r}")
    self.device, self.shape, self.dtype, self.host = device, tuple(shape), dtype, host
    self.nbytes = int(np.prod(self.shape, dtype=np.int64)) * np.dtype(NUMPY[dtype]).itemsize
    dev = device.dev
    if host:
      self.offset = dev.alloc_host(self.nbytes)
      self.addr = dev.sysmem.noc_addr + self.offset
    else:
      self.addr = dev.allocator._alloc(self.nbytes, TYPES[dtype][1])

  def numpy(self) -> np.ndarray:
    """A DRAM buffer waits for queued work and returns a copy. A host buffer returns a live view without waiting,
    like pinned memory under CUDA: wait for the event of the work that writes it."""
    if self.host: return np.ndarray(self.shape, NUMPY[self.dtype], self.device.dev.sysmem.mem, self.offset)
    self.device.synchronize()
    out = np.empty(self.shape, NUMPY[self.dtype])
    if self.nbytes: self.device.dev.allocator._copyout(out, self.addr)
    return out

  def copy_from(self, x):
    """Fill from a numpy array, bytes, or a safetensors Tensor (read through mmap)."""
    if self.host:
      self.numpy().reshape(-1).view(np.uint8)[:] = np.frombuffer(np.ascontiguousarray(x), np.uint8)
      return self
    self.device.synchronize()  # earlier launches may still read this buffer
    copy = self.device.dev.allocator._copyin
    if isinstance(x, Tensor):
      if x.nbytes != self.nbytes: raise ValueError(f"{x.name}: {x.nbytes} bytes into a {self.nbytes}-byte buffer")
      with open(x.path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm, memoryview(mm) as view:
        copy(self.addr, view[x.offset:x.offset + x.nbytes])
      return self
    data = memoryview(np.ascontiguousarray(x)).cast("B")
    if len(data) != self.nbytes: raise ValueError(f"{len(data)} bytes into a {self.nbytes}-byte buffer")
    copy(self.addr, data)
    return self

  def __repr__(self): return f"Buffer({self.shape}, {self.dtype}{', host' if self.host else ''})"


class Kernel:
  """A compiled, installed kernel. Calling it queues one launch; arguments bind parameters by name: DRAM params
  take device Buffers, host params host Buffers, integer params ints (or Vars inside a graph)."""
  def __init__(self, device, compiled):
    self.device, self.compiled = device, compiled
    self.program = compiled.install(device.dev)
    self.params = compiled.manifest["params"]

  def bind(self, args):
    """(argument block, {Var: [byte offsets of its 8-byte words]})."""
    if args.keys() != self.params.keys():
      raise TypeError(f"expected arguments {list(self.params)}, got {list(args)}")
    block, values, vars = bytearray(ARGS), {}, {}
    for name, v in args.items():
      d = self.params[name]
      if d["kind"] == "int":
        if isinstance(v, Var): vars.setdefault(v, []).append(4 * d["slot"])
        elif isinstance(v, (int, np.integer)): values[name] = int(v)
        else: raise TypeError(f"{name}: expected an int or Var, got {v!r}")
        continue
      if not isinstance(v, Buffer): raise TypeError(f"{name}: expected a Buffer, got {v!r}")
      if v.host != (d["kind"] == "host"): raise TypeError(f"{name}: expected a {'host' if d['kind'] == 'host' else 'device'} buffer")
      if TYPES[v.dtype][1] != TYPES[d["type"]][1] or TYPES[v.dtype][0] != TYPES[d["type"]][0]:
        raise TypeError(f"{name}: expected {d['type']}[], got a {v.dtype} buffer")
      values[name] = v.addr
    self.compiled.bind(block, 0, values)
    return bytes(block), vars

  def __call__(self, **args):
    block, vars = self.bind(args)
    if self.device._capture is not None: return self.device._capture.append((self, block, vars))
    if vars: raise TypeError(f"{list(vars)} can only be bound in a graph")
    self.device._launch(self.program, block)


class Graph:
  """Launches captured by Device.graph(), replayed with one CALL. Each replay binds its Vars with STOREs queued ahead
  of the CALL (the argument blocks are only written in queue order), so replays can be queued back to back."""
  def __init__(self, device, launches):
    dev = device.dev
    self.device, self.vars = device, {}
    at = dev.alloc_host(ARGS * len(launches))
    self.base, self.words = dev.sysmem.noc_addr + at, np.zeros(ARGS * len(launches) // 4, np.uint32)
    q = BlackholeComputeQueue()
    for i, (kernel, block, vars) in enumerate(launches):
      self.words[ARGS // 4 * i:ARGS // 4 * (i + 1)] = np.frombuffer(block, np.uint32)
      for v, offsets in vars.items(): self.vars.setdefault(v.name, []).extend(ARGS * i + o for o in offsets)
      q.exec(kernel.program, self.base + ARGS * i)
    np.ndarray(self.words.shape, np.uint32, dev.sysmem.mem, at)[:] = self.words
    self.graph = BlackholeGraph(dev, q)

  def __call__(self, **values) -> Event:
    if values.keys() != self.vars.keys(): raise TypeError(f"expected {sorted(self.vars)}, got {sorted(values)}")
    q = BlackholeComputeQueue()
    for name, offsets in self.vars.items():
      for o in offsets:
        if self.words[o // 4] != values[name] & 0xFFFFFFFF:
          self.words[o // 4] = values[name] & 0xFFFFFFFF
          q.store(self.base + o, int(self.words[o // 4]) | int(self.words[o // 4 + 1]) << 32)
    value, _ = self.graph.submit(before=q)
    return Event(self.device.dev, value)


class _Capture:
  def __init__(self, device): self.device, self.launches, self.graph = device, [], None
  def __enter__(self):
    if self.device._capture is not None: raise RuntimeError("graphs do not nest")
    self.device._capture = self.launches
    return self
  def __exit__(self, *exc):
    self.device._capture = None
    if exc[0] is None: self.graph = Graph(self.device, self.launches)
  def __call__(self, **values) -> Event: return self.graph(**values)


class Device:
  """One card, open until close() or process exit."""
  def __init__(self, index=0):
    self.dev, self._capture = BlackholeDevice(f"BLACKHOLE:{index}"), None
    atexit.register(self.close)
    at = self.dev.alloc_host(ARGS * RING)
    self._ring, self._ring_at, self._ring_used = at, 0, [0] * RING

  def empty(self, shape, dtype, host=False) -> Buffer: return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host)

  def zeros(self, shape, dtype, host=False) -> Buffer:
    b = self.empty(shape, dtype, host)
    chunk = bytes(min(b.nbytes, 16 << 20))
    if host: b.numpy().reshape(-1).view(np.uint8)[:] = 0
    for off in range(0, 0 if host else b.nbytes, len(chunk)):
      self.dev.allocator._copyin(b.addr + off, memoryview(chunk)[:min(len(chunk), b.nbytes - off)])
    return b

  def array(self, x, dtype=None) -> Buffer:
    """A DRAM buffer holding x: a numpy array or a safetensors Tensor. dtype names the TTRV type when numpy has none:
    bf16 takes uint16 bits, or floats to round."""
    if isinstance(x, Tensor): return self.empty(x.shape, dtype or SAFETENSORS[x.dtype]).copy_from(x)
    x = np.asarray(x)
    if dtype == "bf16" and x.dtype.kind == "f":  # round to nearest even
      u = x.astype(np.float32).view(np.uint32).astype(np.uint64)
      x = ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
    dtype = dtype or FROM_NUMPY.get(x.dtype)
    if dtype is None: raise TypeError(f"no TTRV type for {x.dtype}; pass dtype=")
    return self.empty(x.shape, dtype).copy_from(x)

  def kernel(self, source, **defines) -> Kernel:
    """Compile and install a kernel from a .ttrv path (or source text), with constants overridden by defines."""
    from . import build
    path = Path(source) if not isinstance(source, Path) and "\n" not in source else source
    text, name = (path.read_text(), str(path)) if isinstance(path, Path) else (source, "<string>")
    return Kernel(self, build(text, defines, name))

  def graph(self): return _Capture(self)

  def synchronize(self, timeout=10.0): self.dev.synchronize(timeout)

  def close(self): self.dev.close()  # stops the cores and unpins host memory; safe to call twice

  def _launch(self, program, block):
    i = self._ring_at
    self._ring_at = (i + 1) % RING
    self.dev.timeline_signal.wait(self._ring_used[i])  # the launch that last used this block has read it
    self.dev.sysmem.mem[self._ring + ARGS * i:self._ring + ARGS * (i + 1)] = block
    value = self.dev.next_timeline()
    BlackholeComputeQueue().exec(program, self.dev.sysmem.noc_addr + self._ring + ARGS * i) \
      .signal(self.dev.timeline_signal, value).submit(self.dev)
    self._ring_used[i] = value
