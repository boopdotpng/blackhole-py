"""One-card TTRV runtime with resident worker tables."""
import atexit, copy, math, mmap, struct
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import fw
from device import Device as WorkerDevice
from helpers import Tensor
from . import hw
from .expand import TYPES
from .layout import ResidentCapacityError

NUMPY = {"bf16": np.uint16, "fp16": np.float16, "fp32": np.float32, "e4m3": np.uint8, "e5m2": np.uint8, "u8": np.uint8,
         "u32": np.uint32, "i32": np.int32, "u64": np.uint64, "bfp8": np.uint8, "bfp4": np.uint8}
FROM_NUMPY = {np.dtype(np.float32): "fp32", np.dtype(np.float16): "fp16", np.dtype(np.uint32): "u32",
              np.dtype(np.int32): "i32", np.dtype(np.uint64): "u64", np.dtype(np.uint8): "u8"}
SAFETENSORS = {"BF16": "bf16", "F16": "fp16", "F32": "fp32", "F8_E4M3": "e4m3", "F8_E5M2": "e5m2", "U8": "u8",
               "I32": "i32", "U32": "u32"}
ARGS = fw.PARAM_SIZE  # one launch's argument block


class Var:
  """An integer kernel argument bound when a graph is replayed."""
  def __init__(self, name): self.name = name
  def __repr__(self): return f"Var({self.name!r})"


class Event:
  def __init__(self, dev, epoch): self.dev, self.epoch = dev, epoch
  def wait(self, timeout=10.0):
    if self.dev.compute_epoch == self.epoch: self.dev.wait_workers(timeout)
  synchronize = wait


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
      self.addr = dev.host.noc_addr + self.offset
    else:
      self.addr = dev.allocator.alloc(self.nbytes, tiles_per_page * TYPES[dtype][1])

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
    if self.host: return np.ndarray(self.shape, NUMPY[self.dtype], self.device.dev.host.mem, self.offset)
    self.device.synchronize()
    out = np.empty(self.shape, NUMPY[self.dtype])
    if self.nbytes: self.device.dev.allocator.copyout(out, self.addr)
    return out

  def copy_from(self, x):
    """Fill from a numpy array, bytes, or a safetensors Tensor (read through mmap)."""
    if self.host:
      self.numpy().reshape(-1).view(np.uint8)[:] = np.frombuffer(np.ascontiguousarray(x), np.uint8)
      return self
    self.device.synchronize()  # earlier launches may still read this buffer
    copy = self.device.dev.allocator.copyin
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
  """A resident TTRV entry point. Calls append a graph row during capture and run one row in eager mode."""
  def __init__(self, device, program, name="kernel"):
    self.device, self.name, self.phase = device, name, device.phase_name
    with device.installation(): compiled, self.descriptor = device.install(program)
    self.compiled = compiled
    self.params = compiled.manifest["params"]
    self.grid, self.base = compiled.manifest["grid"], compiled.manifest.get("base", 0)

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
      if v.device is not self.device: raise ValueError(f"{name}: buffer belongs to another device")
      if TYPES[v.dtype][1] != TYPES[d["type"]][1] or TYPES[v.dtype][0] != TYPES[d["type"]][0]:
        raise TypeError(f"{name}: expected {d['type']}[], got a {v.dtype} buffer")
      values[name] = v.addr
    self.compiled.bind(block, 0, values)
    return bytes(block), vars

  def __call__(self, _async=False, **args):
    """Queue a launch. _async: the next launch (on other workers, see const CORE_BASE) starts without waiting for
    this one; it and the launches after it must not depend on this one's results except through device flags."""
    if self.device.phase_name != self.phase:
      if self.device._capture is not None: raise ValueError("kernel belongs to a different resident phase")
      self.device.activate(self.phase)
    block, vars = self.bind(args)
    if self.device._capture is not None: return self.device._capture.append((self, block, vars, _async))
    if vars: raise TypeError(f"{list(vars)} can only be bound in a graph")
    return self.device.eager(self, block)


class Graph:
  """A table of resident entry points, immutable argument blocks and replay-variable slots."""
  def __init__(self, device, launches):
    self.device, self.vars, self.stamps = device, {}, 0
    self.phase = device.phase_name
    with device.installation(): self.pack(launches)

  def pack(self, launches):
    device, rows, occupied = self.device, [], set()
    for i, (k, block, bindings, asynchronous) in enumerate(launches):
      active = set(range(k.base, k.base + k.grid))
      if active & occupied: raise ValueError("overlapping worker ranges in an asynchronous group")
      occupied |= active
      join = not asynchronous or i + 1 == len(launches)
      participants = len(occupied | {0}) if join else 0
      if join: occupied.clear()
      patch = []
      for v, offsets in bindings.items():
        index = self.vars.setdefault(v.name, len(self.vars))
        if index >= fw.MAX_VARS: raise ValueError("too many table variables")
        patch.extend(index << 8 | (1 + off // 4) for off in offsets)
      args = device.intern(block[:k.compiled.args_size])
      changes = device.intern(struct.pack(f"<{len(patch)+1}I", *patch, 0)) if patch else 0
      rows.append(struct.pack("<4I", k.descriptor, args, changes, participants))
    self.addr, self.count = device.intern(b"".join(rows)), len(rows)

  def enable_timing(self):
    self.device.activate(self.phase)
    size = 4 * (self.count + 1)
    if not self.stamps: self.stamps = self.device.local(size)
    def milliseconds():
      if self.device.phase_name != self.phase: raise RuntimeError("read timings before leaving the graph phase")
      self.device.synchronize()
      raw = self.device.dev
      ticks = np.frombuffer(raw.card.read(raw.workers[0], self.stamps, size), "<u4")
      return np.diff(ticks).astype(float) / (fw.AICLK_MHZ * 1000)
    return milliseconds

  def __call__(self, **values):
    if values.keys() != self.vars.keys(): raise TypeError(f"expected {sorted(self.vars)}, got {sorted(values)}")
    self.device.activate(self.phase)
    slots = [0] * (max(self.vars.values(), default=-1) + 1)
    for name, index in self.vars.items(): slots[index] = values[name]
    return self.device.replay(self.addr, self.count, self.stamps, slots)


class _Capture:
  def __init__(self, device): self.device, self.launches, self.graph = device, [], None
  def __enter__(self):
    if self.device._capture is not None: raise RuntimeError("graphs do not nest")
    self.device._capture = self.launches
    return self
  def __exit__(self, *exc):
    self.device._capture = None
    if exc[0] is None: self.graph = Graph(self.device, self.launches)
  def split(self, index):
    """Take two independently replayable views at a completed join in the installed table."""
    if self.graph is None or not 0 < index < len(self.launches) or self.launches[index - 1][3]:
      raise ValueError("split must follow a completed dependency group")
    def view(begin, end):
      part = _Capture(self.device)
      part.launches = self.launches[begin:end]
      graph = part.graph = copy.copy(self.graph)
      graph.addr += 16 * begin
      graph.count, graph.stamps = end - begin, 0
      graph.vars = {v.name: self.graph.vars[v.name] for _, _, bindings, _ in part.launches for v in bindings}
      return part
    return view(0, index), view(index, len(self.launches))

  def __call__(self, **values) -> Event: return self.graph(**values)


class Device:
  """One card, open until close() or process exit."""
  def __init__(self, index=0):
    self.dev, self._capture = WorkerDevice(index), None
    try:
      if self.dev.dram_banks != 8: raise ValueError("TTRV model kernels require eight DRAM banks")
      image, pcs, _ = fw.build_worker(["table.c", "call.S"], fw.ROLES, self.dev.dram_banks, fw.ROLE_PROGRESS - fw.CODE_BASE)
      self.dev.load(image, pcs)
      self.top, self.scratch_base = fw.DATA_BASE, hw.L1_SIZE
      self.blobs, self.kernels, self.local_blocks = {}, {}, {}
      self.phase_name, self.phases = "decode", {}
      self.images = {}
      self.step_args = self.dev.alloc_host(64)
    except BaseException:
      self.dev.close()
      raise
    atexit.register(self.close)

  def activate(self, name):
    """Replace worker code, graph and temporary L1. Cross-phase model state must reside in DRAM or sysmem."""
    if name == self.phase_name: return
    if self._capture is not None: raise RuntimeError("cannot switch phases during graph capture")
    self.dev.synchronize(120)
    self.phases[self.phase_name] = self.top, self.scratch_base, self.blobs, self.kernels, self.local_blocks
    top, scratch, blobs, kernels, local = self.phases.get(name, (fw.DATA_BASE, hw.L1_SIZE, {}, {}, {}))
    image = self.images.get(name)
    if image is None or len(image) != top - fw.DATA_BASE:
      image = self.images[name] = bytearray(top - fw.DATA_BASE)
      for blob, at in blobs.items():
        offset = at - fw.DATA_BASE
        image[offset:offset + len(blob)] = blob
    if image:
      for target in self.dev.worker_rects: self.dev.card.write(target, fw.DATA_BASE, image)
    self.top, self.scratch_base, self.blobs, self.kernels, self.local_blocks = top, scratch, blobs, kernels, local
    self.phase_name = name

  @contextmanager
  def phase(self, name):
    previous = self.phase_name
    self.activate(name)
    try: yield
    finally: self.activate(previous)

  @contextmanager
  def installation(self):
    """Plan a complete install before touching L1. A failed specialization can be retried at a smaller shape."""
    top, scratch = self.top, self.scratch_base
    self.pending = {}
    try:
      yield
      if self.top > self.scratch_base: raise ResidentCapacityError("worker scratch overlaps resident data")
      if self.top > top:
        payload = bytearray(self.top - top)  # also zero-initializes new keep allocations
        for blob, at in self.pending.items(): payload[at-top:at-top+len(blob)] = blob
        self.dev.synchronize(120)
        for target in self.dev.worker_rects: self.dev.card.write(target, top, payload)
      self.blobs.update(self.pending)
    except BaseException:
      self.top, self.scratch_base = top, scratch
      raise
    finally: self.pending = None

  def intern(self, blob):
    if not blob: return 0
    if blob in self.blobs: return self.blobs[blob]
    if blob not in self.pending:
      self.pending[blob] = self.reserve(len(blob), 4)
    return self.pending[blob]

  def reserve(self, nbytes, align):
    at = (self.top + align - 1) & -align
    if at + nbytes > self.scratch_base: raise ResidentCapacityError("worker L1 exhausted")
    self.top = at + nbytes
    return at

  def local(self, nbytes, align=64):
    """Reserve the same persistent activation range on every worker. Bind it to a TTRV l1 declaration with at=."""
    if nbytes <= 0 or align < 64 or align & (align-1): raise ValueError("invalid worker L1 allocation")
    at = self.reserve(nbytes, align)
    self.local_blocks[at] = nbytes
    return at

  def install(self, program):
    from . import compile_program, layout
    m = layout(program)
    if m["base"] < 0 or m["grid"] < 1 or m["base"] + m["grid"] > len(self.dev.workers):
      raise ValueError("kernel grid exceeds worker grid")
    storage = m["storage"]
    kept = {name: self.reserve(v["size"], v["align"]) for name, v in storage.items() if v.get("keep")}
    for v in storage.values():
      if v.get("external") and self.local_blocks.get(v["address"], 0) < v["size"]:
        raise ValueError("external L1 declaration exceeds its device allocation")
    # Slide the entire scratch layout up by a common alignment multiple. This preserves pointer
    # relationships inside kernels and gives all installed variants the same high end of L1.
    align = max((v["align"] for v in storage.values()), default=64)
    shift = (hw.L1_SIZE - m["scratch_end"]) & -align
    scratch = fw.DATA_BASE + shift
    self.scratch_base = min(self.scratch_base, scratch)
    if self.top > self.scratch_base: raise ResidentCapacityError("resident storage overlaps worker scratch")
    compiled = compile_program(program, scratch_base=scratch, kept=kept)
    m = compiled.manifest
    streams = sum(1 << v["cb"] for v in m["storage"].values() if "cb" in v)
    pcs = [self.intern(compiled.images.get(role, b"")) for role in fw.ROLES]
    early = compiled.program.consts.get("EARLY_WEIGHTS", 0)
    if early and (m["storage"].get("matrices", {}).get("cb") != 31 or m["storage"]["matrices"].get("producer") != "brisc"):
      raise ValueError("BRISC lookahead requires a BRISC-produced weight ring on CB31")
    return compiled, self.intern(struct.pack("<10I", m["base"], m["grid"], *pcs, compiled.args_size // 4, streams, early))

  def eager(self, kernel, block):
    self.dev.synchronize()
    params = fw.EAGER_ROW + 16
    row = struct.pack("<4I", kernel.descriptor, params, 0, kernel.grid + (kernel.base != 0))
    for target in self.dev.worker_rects: self.dev.card.write(target, fw.EAGER_ROW, row + block)
    return self.replay(fw.EAGER_ROW, 1, 0, [])

  def replay(self, addr, count, stamps, values):
    raw = self.dev
    raw.synchronize(120)
    rect, exclude = raw.cover(raw.workers)
    header = struct.pack("<5I", addr, count, rect, exclude, stamps)
    for target in raw.worker_rects:
      raw.card.write(target, fw.ROLE_PROGRESS, bytes(36))
      raw.card.write32(target, fw.SYNC_EPOCH, 0)
      if values:
        raw.card.write(target, fw.ARG_VALUES, struct.pack(f"<{len(values)}I", *(int(v) & 0xffffffff for v in values)))
    at = self.step_args
    raw.host.mem[at:at + len(header)] = header
    return Event(raw, raw.launch(raw.host.noc_addr + at, len(header)))


  def empty(self, shape, dtype, host=False, *, tiles_per_page=1) -> Buffer:
    return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host, tiles_per_page)

  def zeros(self, shape, dtype, host=False) -> Buffer:
    b = self.empty(shape, dtype, host)
    if host:
      b.numpy().fill(0)
      return b
    chunk = bytes(min(b.nbytes, 16 << 20))
    for off in range(0, b.nbytes, len(chunk) or 1):
      self.dev.allocator.copyin(b.addr + off, memoryview(chunk)[:min(len(chunk), b.nbytes - off)])
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
    from . import expand, parse
    path = Path(source) if not isinstance(source, Path) and "\n" not in source else source
    text, file = (path.read_text(), str(path)) if isinstance(path, Path) else (source, "<string>")
    key = file, text, tuple(sorted(defines.items())), name
    if key not in self.kernels:
      self.kernels[key] = Kernel(self, expand(parse(text, file), defines), name or (path.stem if isinstance(path, Path) else "kernel"))
    return self.kernels[key]

  def graph(self): return _Capture(self)

  def synchronize(self, timeout=10.0): self.dev.synchronize(timeout)
  def close(self): self.dev.close()
