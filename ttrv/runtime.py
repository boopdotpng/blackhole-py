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

  start, end = d.event(), d.event()            # device wall-clock timing, torch.cuda.Event style
  start.record(); scale(x=x, y=y, k=2); end.record()
  end.synchronize(); start.elapsed_time(end)   # ms

  with d.profile() as prof:                    # every launch inside gets hardware counters, eager or graph replay
    g(k=3)
  print(prof)                                  # one row per kernel name; prof.launches has every launch

PROFILE=1 in the environment profiles the whole run and prints the table when the device closes; PROFILE=2 also prints
each launch as its counters arrive.
"""

import atexit, copy, math, mmap, os, sys
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import fw
from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, BlackholeGraph, dram
from helpers import Tensor
from . import hw
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
  """Marks the work queued before it; wait() returns once the device has done that work. Events from Device.event()
  also take the device's wall clock when record()ed, for elapsed_time() (torch.cuda.Event)."""
  def __init__(self, dev, value=None, stamp=None): self.dev, self.value, self.stamp = dev, value, stamp
  def wait(self, timeout=10.0):
    if self.value is None: raise RuntimeError("event was never recorded")
    self.dev.timeline_signal.wait(self.value, timeout)
  synchronize = wait
  @property
  def done(self): return self.value is not None and self.dev.timeline_signal.value >= self.value
  def query(self) -> bool: return self.done

  def record(self):
    """Queue a wall-clock stamp after all work queued so far (the previous launch has finished; the next has not started)."""
    if self.stamp is None: raise RuntimeError("only events from Device.event() can be recorded")
    dev = self.dev
    self.value = dev.next_timeline()
    BlackholeComputeQueue().timestamp(dev.sysmem.noc_addr + self.stamp).signal(dev.timeline_signal, self.value).submit(dev)
    return self

  @property
  def ticks(self) -> int:
    self.wait()
    return int(np.frombuffer(self.dev.sysmem.mem, np.uint64, 1, self.stamp + 8)[0])

  def elapsed_time(self, end: "Event") -> float:
    """Milliseconds of device wall clock from this event to end; waits for both."""
    return (end.ticks - self.ticks) / (fw.AICLK_MHZ * 1e3)


class Buffer:
  """shape elements of a TTRV type. DRAM buffers interleave over 8 banks in pages of one or more tiles; host
  buffers live in pinned host memory that kernels can write."""
  def __init__(self, device, shape, dtype, host=False, tiles_per_page=1):
    if dtype not in TYPES: raise ValueError(f"unknown type {dtype!r}")
    self.device, self.shape, self.dtype, self.host = device, tuple(shape), dtype, host
    self.nbytes = int(np.prod(self.shape, dtype=np.int64)) * np.dtype(NUMPY[dtype]).itemsize
    dev = device.dev
    if tiles_per_page < 1 or tiles_per_page * TYPES[dtype][1] > hw.NOC_MAX_BURST or (host and tiles_per_page != 1):
      raise ValueError("invalid tiles_per_page")
    if host:
      self.offset = dev.alloc_host(self.nbytes)
      self.addr = dev.sysmem.noc_addr + self.offset
    else:
      self.addr = dev.allocator._alloc(self.nbytes, tiles_per_page * TYPES[dtype][1])

  def page_view(self, byte_offset, shape):
    """Alias an aligned region of this DRAM allocation, preserving its bank interleave."""
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
  take device Buffers, host params host Buffers, integer params ints (or Vars inside a graph). name labels it in
  profiles."""
  def __init__(self, device, compiled, name="kernel"):
    self.device, self.compiled, self.name = device, compiled, name
    self.program = compiled.install(device.dev)
    self.params = compiled.manifest["params"]
    self.grid = compiled.manifest["grid"]

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
    self.device._launch(self.program, block, self)


class Graph:
  """Launches captured by Device.graph(), replayed with one CALL. Each replay binds its Vars with STOREs queued ahead
  of the CALL (the argument blocks are only written in queue order), so replays can be queued back to back."""
  def __init__(self, device, launches):
    dev = device.dev
    self.device, self.vars, self.kernels, self.profiled = device, {}, [k for k, _, _ in launches], None
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
    prof = self.device._profiler
    if prof is None:
      value, _ = self.graph.submit(before=q)
      return Event(self.device.dev, value)
    return prof.replay(self, q)


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
    self.dev, self._capture, self._profiler, self._env_profiler = BlackholeDevice(f"BLACKHOLE:{index}"), None, None, None
    atexit.register(self.close)
    at = self.dev.alloc_host(ARGS * RING)
    self._ring, self._ring_at, self._ring_used = at, 0, [0] * RING
    self._profile_slots = None  # eager launches' counter blocks, allocated by the first profile
    if (level := int(os.environ.get("PROFILE", "0") or 0)) > 0:
      self._env_profiler = Profiler(self, verbose=level >= 2).__enter__()

  def empty(self, shape, dtype, host=False, *, tiles_per_page=1) -> Buffer:
    return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host, tiles_per_page)

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
    if isinstance(x, Tensor):
      storage_type = x.packed_format.removesuffix("_b") if x.packed_format else SAFETENSORS[x.dtype]
      return self.empty(x.shape, dtype or storage_type).copy_from(x)
    x = np.asarray(x)
    if dtype == "bf16" and x.dtype.kind == "f":  # round to nearest even
      u = x.astype(np.float32).view(np.uint32).astype(np.uint64)
      x = ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
    dtype = dtype or FROM_NUMPY.get(x.dtype)
    if dtype is None: raise TypeError(f"no TTRV type for {x.dtype}; pass dtype=")
    return self.empty(x.shape, dtype).copy_from(x)

  def kernel(self, source, name=None, **defines) -> Kernel:
    """Compile and install a kernel from a .ttrv path (or source text), with constants overridden by defines. name
    labels it in profiles; it defaults to the file's stem."""
    from . import build
    path = Path(source) if not isinstance(source, Path) and "\n" not in source else source
    text, file = (path.read_text(), str(path)) if isinstance(path, Path) else (source, "<string>")
    return Kernel(self, build(text, defines, file), name or (path.stem if isinstance(path, Path) else "kernel"))

  def graph(self): return _Capture(self)

  def event(self) -> Event:
    """A timing event: record() it after some work, then elapsed_time() between two of them (ms)."""
    return Event(self.dev, stamp=self.dev.alloc_host(16, 16))

  def profile(self) -> "Profiler":
    """Context manager: every launch inside, eager or graph replay, collects per-core hardware counters."""
    return Profiler(self)

  def synchronize(self, timeout=10.0): self.dev.synchronize(timeout)

  def close(self):  # stops the cores and unpins host memory; safe to call twice
    if self._env_profiler is not None and self.dev.iface is not None:
      prof, self._env_profiler = self._env_profiler, None
      try: prof.__exit__(None, None, None)
      finally: print(prof, flush=True)
    self.dev.close()

  def _launch(self, program, block, kernel=None):
    i = self._ring_at
    self._ring_at = (i + 1) % RING
    self.dev.timeline_signal.wait(self._ring_used[i])  # the launch that last used this block has read it
    self.dev.sysmem.mem[self._ring + ARGS * i:self._ring + ARGS * (i + 1)] = block
    if self._profiler is not None and kernel is not None:
      self._ring_used[i] = self._profiler.launch(kernel, self.dev.sysmem.noc_addr + self._ring + ARGS * i)
      return
    value = self.dev.next_timeline()
    BlackholeComputeQueue().exec(program, self.dev.sysmem.noc_addr + self._ring + ARGS * i) \
      .signal(self.dev.timeline_signal, value).submit(self.dev)
    self._ring_used[i] = value


RECORD = np.dtype([(f, "<u4") for f in fw.PROFILE_FIELDS] + [("_", "<u4", (fw.PROFILE_RECORD_SIZE // 4 - len(fw.PROFILE_FIELDS),))])
EAGER_SLOTS = 16  # eager launches whose counters can be in flight at once


@dataclass
class Launch:
  """One profiled launch. start_ns and end_ns are the dispatcher's wall clock when it began the EXEC (before code
  install) and when the last core reported done. cores holds one counter record per worker (fw.PROFILE_FIELDS), in
  AICLK cycles and 64-byte NoC flits."""
  name: str
  grid: int
  start_ns: float
  end_ns: float
  cores: np.recarray

  @property
  def us(self): return (self.end_ns - self.start_ns) / 1e3

  def __str__(self):
    c, cyc = self.cores, max(int(self.cores.cycles.sum()), 1)
    busy = " ".join(f"{f} {100 * int(c[f].sum()) / cyc:4.1f}%" for f in ("fpu", "sfpu", "unpack", "pack", "math_stall"))
    t = max(self.end_ns - self.start_ns, 1)
    return (f"{self.name:<14} {self.us:9.1f} us  {self.grid:3d} cores  {busy}  "
            f"rd {64 * int(c.noc_read.sum()) / t:7.1f} GB/s  wr {64 * int(c.noc_write.sum()) / t:7.1f} GB/s")


def _ns(ticks): return int(ticks) * 1e3 / fw.AICLK_MHZ


class Profiler:
  """Collects a counter record from every core of every launch while active (Device.profile()). Eager launches use a
  small ring of blocks; a graph gets a second copy of its command buffer with a block per launch, and each replay's
  records are read before the next replay of that graph is queued, so only one replay of it is in flight."""
  def __init__(self, device, verbose=False):
    self.device, self.verbose, self.launches, self.parent = device, verbose, [], None
    self.pending = []  # (timeline value that retires it, [(name, grid, block offset)])

  def __enter__(self):  # nests: an inner profile's launches also go to the outer one (PROFILE=1)
    self.parent, self.device._profiler = self.device._profiler, self
    return self

  def __exit__(self, *exc):
    self.device._profiler = self.parent
    try:
      self.device.synchronize()
      self._harvest(len(self.pending))
    finally:
      self.pending.clear()

  # --- queueing
  def _block(self, grid): return round_up64(fw.PROFILE_HEADER + fw.PROFILE_RECORD_SIZE * grid)

  def launch(self, kernel, args) -> int:
    d, dev = self.device, self.device.dev
    if d._profile_slots is None:
      size = self._block(len(dev.workers))
      d._profile_slots = [[dev.alloc_host(size, 64), 0] for _ in range(EAGER_SLOTS)]
      d._profile_slot_at = 0
    slot = d._profile_slots[d._profile_slot_at]
    d._profile_slot_at = (d._profile_slot_at + 1) % EAGER_SLOTS
    self._release(slot[1])
    at = slot[0]
    self._clear(at, self._block(kernel.grid))
    value = dev.next_timeline()
    BlackholeComputeQueue().exec(kernel.program, args, profile=dev.sysmem.noc_addr + at, counters=True) \
      .signal(dev.timeline_signal, value).submit(dev)
    slot[1] = value
    self.pending.append((value, [(kernel.name, kernel.grid, at)]))
    return value

  def replay(self, graph, before) -> Event:
    dev = self.device.dev
    if graph.profiled is None:
      blocks, at = [], dev.alloc_host(sum(self._block(k.grid) for k in graph.kernels), 64)
      q = BlackholeComputeQueue()
      for i, k in enumerate(graph.kernels):
        blocks.append((k.name, k.grid, at))
        q.exec(k.program, graph.base + ARGS * i, profile=dev.sysmem.noc_addr + at, counters=True)
        at += self._block(k.grid)
      graph.profiled = [BlackholeGraph(dev, q), blocks, 0, blocks[0][2], at - blocks[0][2]]
    copy, blocks, last, start, size = graph.profiled
    self._release(last)
    self._clear(start, size)
    value, _ = copy.submit(before=before)
    graph.profiled[2] = value
    self.pending.append((value, blocks))
    return Event(dev, value)

  def _clear(self, at, size): self.device.dev.sysmem.mem[at:at + size] = bytes(size)

  def _release(self, value):
    """Wait for timeline value (the last launch to use a block about to be reused) and read every launch up to it."""
    self.device.dev.timeline_signal.wait(value)
    self._harvest(sum(v <= value for v, _ in self.pending))

  def _harvest(self, n):
    mem = self.device.dev.sysmem.mem
    for _, blocks in self.pending[:n]:
      for name, grid, at in blocks:
        start, end = np.frombuffer(mem, np.uint64, 4, at)[[1, 3]]
        cores = np.frombuffer(mem, RECORD, grid, at + fw.PROFILE_HEADER).copy().view(np.recarray)
        if not (cores.id >> 31).all() or ((cores.id & 0x7FFFFFFF) != np.arange(grid)).any():
          missing = np.flatnonzero(~(cores.id >> 31).astype(bool) | ((cores.id & 0x7FFFFFFF) != np.arange(grid)))
          raise RuntimeError(f"{name}: no counter record from cores {missing.tolist()[:8]}")
        launch = Launch(name, grid, _ns(start), _ns(end), cores)
        p = self
        while p is not None: p.launches.append(launch); p = p.parent
        if self.verbose: print(launch, file=sys.stderr, flush=True)
    del self.pending[:n]

  # --- report
  def table(self):
    rows = {}
    for l in self.launches: rows.setdefault(l.name, []).append(l)
    out = [f"{'kernel':<14} {'calls':>6} {'total ms':>9} {'mean us':>8} {'cores':>5} {'fpu%':>5} {'sfpu%':>5} "
           f"{'unpack%':>7} {'pack%':>5} {'stall%':>6} {'rd GB/s':>8} {'wr GB/s':>8}"]
    for name, ls in sorted(rows.items(), key=lambda kv: -sum(l.end_ns - l.start_ns for l in kv[1])):
      t = sum(l.end_ns - l.start_ns for l in ls)
      c = np.concatenate([l.cores for l in ls]).view(np.recarray)
      cyc = max(int(c.cycles.sum()), 1)
      pct = [100 * int(c[f].sum()) / cyc for f in ("fpu", "sfpu", "unpack", "pack", "math_stall")]
      out.append(f"{name:<14} {len(ls):>6} {t / 1e6:>9.2f} {t / 1e3 / len(ls):>8.1f} {max(l.grid for l in ls):>5} "
                 f"{pct[0]:>5.1f} {pct[1]:>5.1f} {pct[2]:>7.1f} {pct[3]:>5.1f} {pct[4]:>6.1f} "
                 f"{64 * int(c.noc_read.sum()) / max(t, 1):>8.1f} {64 * int(c.noc_write.sum()) / max(t, 1):>8.1f}")
    return "\n".join(out)

  def __str__(self): return self.table()


def round_up64(n): return (n + 63) & -64
