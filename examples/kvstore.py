"""Tiered prefix store for examples/engine.py: slot states (KV caches up to a length, plus any recurrent state) saved to
host RAM, spilled to SSD, and restored into a slot when a new prompt starts with the saved tokens.

A slot's state is saved when the engine hands the slot to a sequence that keeps less of it than it holds (eviction),
and every slot is saved when the server stops (Engine.flush). Entries are least-recently-used in each tier: RAM
entries past the RAM budget move to SSD files (written by a background thread), SSD entries past the SSD budget are
deleted. The SSD tier is persistent: entries live under ssd_dir/<fingerprint>/ as prefix-<n>.bin (the state) and
prefix-<n>.tokens (int64 token ids), and are found again by a later server for the same model and state layout (the
backend's fingerprint), so a new session sharing a long system prompt starts from it.

Backends opt in with
  fingerprint                         a string naming the checkpoint and the state layout save() produces
  save(slot, n) -> uint8 array        the slot's state for positions 0 .. n - 1
  load(slot, data, n, m)              restore the first m of the n positions data holds
and their reusable(slot, ids, held) decides how much of an entry a prompt may use (any prefix for KV-only models,
all or nothing with recurrent state).
"""
import collections, hashlib, itertools, os, threading, time
from pathlib import Path

import numpy as np


def read_file(path, chunk=32 << 20, threads=8):
  """A whole file as a uint8 array: parallel O_DIRECT reads (no page cache) into page-aligned memory, several
  gigabytes a second on NVMe where a buffered single-thread read manages a fraction of that."""
  import concurrent.futures, mmap
  n = os.path.getsize(path)
  buf = mmap.mmap(-1, max(n + -n % mmap.PAGESIZE, mmap.PAGESIZE))
  view = memoryview(buf)
  try: fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
  except OSError: fd = os.open(path, os.O_RDONLY)
  def part(off):
    end = min(off + chunk, len(view))
    got = os.preadv(fd, [view[off:end]], off)
    if got < min(end, n) - off: raise OSError(f"{path}: short read at {off}")
  try:
    with concurrent.futures.ThreadPoolExecutor(threads) as pool: list(pool.map(part, range(0, n, chunk)))
  finally: os.close(fd)
  return np.frombuffer(buf, np.uint8, n)


class RunCopier:
  """Moves lists of (DRAM address, bytes) runs between the card and one host array through a pinned bounce buffer:
  DMAs into one half while the other half is copied out, so many small runs cost about as much as one large copy.
  Runs must be multiples of 64 bytes at 64-byte aligned addresses (the NoC can't shift bytes)."""
  def __init__(self, dev, size=256 << 20):
    self.dev, self.half = dev.dev, size // 2
    self.host = self.dev.pinned(size)

  def _batches(self, runs):
    batch, used = [], 0
    for addr, size in runs:
      while size:
        n = min(size, self.half - used)
        batch.append((addr, n, used))
        addr, size, used = addr + n, size - n, used + n
        if used == self.half:
          yield batch
          batch, used = [], 0
    if batch: yield batch

  def gather(self, runs):
    """The runs' bytes, concatenated, as a new uint8 array."""
    dev, alloc = self.dev, self.dev.allocator
    out = np.empty(sum(size for _, size in runs), np.uint8)
    base, at, pending = out.ctypes.data, 0, None
    def drain(item):
      value, half, start, n = item
      dev.timeline_signal.wait(value, 60)
      alloc._memcpy(base + start, self.host.addr + half * self.half, n)
    for i, batch in enumerate(self._batches(runs)):
      half = i % 2
      for addr, n, off in batch: value = dev.dma_copy(self.host.noc_addr + half * self.half + off, addr, n)
      n = sum(b[1] for b in batch)
      if pending: drain(pending)
      pending = value, half, at, n
      at += n
    if pending: drain(pending)
    return out

  def scatter(self, runs, data):
    """Write data's bytes over the runs, in order (the inverse of gather)."""
    dev, alloc = self.dev, self.dev.allocator
    base, at, last = data.ctypes.data, 0, [0, 0]
    for i, batch in enumerate(self._batches(runs)):
      half = i % 2
      dev.timeline_signal.wait(last[half], 60)   # this half's previous DMAs have read it
      n = sum(b[1] for b in batch)
      alloc._memcpy(self.host.addr + half * self.half, base + at, n)
      for addr, size, off in batch: last[half] = dev.dma_copy(addr, self.host.noc_addr + half * self.half + off, size)
      at += n
    dev.timeline_signal.wait(max(last), 60)


class Entry:
  def __init__(self, key, tokens, data, nbytes=None):
    self.key, self.tokens, self.data = key, tokens, data
    self.nbytes = data.nbytes if data is not None else nbytes
    self.path = None       # SSD file once written


class PrefixStore:
  def __init__(self, ram_bytes=0, ssd_bytes=0, ssd_dir=None, min_tokens=256):
    """min_tokens: shorter states, or evictions losing fewer positions, are not saved."""
    self.ram_bytes, self.ssd_bytes, self.min_tokens = ram_bytes, ssd_bytes, min_tokens
    self.root = Path(ssd_dir) if ssd_dir and ssd_bytes else None
    self.dir = None        # root/<fingerprint>, set by attach()
    self.ram = collections.OrderedDict()   # key -> Entry with data in memory, least recently used first
    self.ssd = collections.OrderedDict()   # key -> Entry with data on disk
    self.ids = itertools.count()
    self.lock = threading.Lock()
    self.spilling = None
    self.stats = collections.Counter()

  def enabled(self): return self.ram_bytes > 0 or self.root is not None

  def attach(self, fingerprint):
    """Use the SSD entries a previous run left for this fingerprint."""
    if self.root is None: return
    self.dir = self.root / hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
    self.dir.mkdir(parents=True, exist_ok=True)
    (self.dir / "fingerprint.txt").write_text(fingerprint + "\n")
    found = []
    for tokens_path in self.dir.glob("prefix-*.tokens"):
      path = tokens_path.with_suffix(".bin")
      try:
        key = int(tokens_path.stem.removeprefix("prefix-"))
        tokens = np.fromfile(tokens_path, np.int64)
        st = path.stat()
      except (ValueError, OSError):
        continue
      e = Entry(key, tokens, None, st.st_size)
      e.path = path
      found.append((st.st_mtime, e))
    for _, e in sorted(found, key=lambda x: x[0]): self.ssd[e.key] = e
    for leftover in self.dir.glob("prefix-*.bin"):   # a .bin without its .tokens: an interrupted write
      if not leftover.with_suffix(".tokens").exists(): leftover.unlink()
    self.ids = itertools.count(max((e.key for _, e in found), default=-1) + 1)
    self.stats["loaded from ssd"] = len(found)
    self._trim_ssd()

  def entries(self):
    with self.lock: return list(self.ram.values()) + list(self.ssd.values())

  def covers(self, tokens):
    """Whether some entry already holds tokens as its prefix."""
    n = len(tokens)
    return any(len(e.tokens) >= n and np.array_equal(e.tokens[:n], tokens) for e in self.entries())

  def best(self, ids, usable):
    """(entry, positions) of the entry whose state a prompt ids can use the most of; usable(tokens) -> positions."""
    best, most = None, 0
    for e in self.entries():
      m = usable(e.tokens)
      if m > most: best, most = e, m
    return best, most

  def put(self, tokens, data):
    if len(tokens) < self.min_tokens or not self.enabled(): return
    tokens = np.array(tokens, np.int64)
    with self.lock:
      # Entries this one extends hold nothing it doesn't.
      for tier in (self.ram, self.ssd):
        for key, e in list(tier.items()):
          if len(e.tokens) <= len(tokens) and np.array_equal(tokens[:len(e.tokens)], e.tokens):
            self._drop(tier, key)
      e = Entry(next(self.ids), tokens, data)
      self.ram[e.key] = e
      self.stats["saved"] += 1
    self._balance()

  def get(self, e):
    """The entry's data (read back from SSD if spilled); marks it used."""
    with self.lock:
      if e.key in self.ram:
        self.ram.move_to_end(e.key)
        self.stats["ram hits"] += 1
        return e.data
      self.ssd.move_to_end(e.key)
      path = e.path
    data = read_file(path)
    os.utime(path)   # least recently used order survives restarts
    self.stats["ssd hits"] += 1
    return data

  def _drop(self, tier, key):
    e = tier.pop(key)
    if e.path is not None:
      for p in (e.path.with_suffix(".tokens"), e.path):
        try: p.unlink()
        except FileNotFoundError: pass

  def _balance(self, keep_ram=True):
    """Move RAM entries past the budget (all of them unless keep_ram) to SSD in the background, or drop them."""
    with self.lock:
      over = []
      ram = sum(e.nbytes for e in self.ram.values())
      while self.ram and (ram > self.ram_bytes or not keep_ram):
        key, e = self.ram.popitem(last=False)
        ram -= e.nbytes
        if self.dir is not None and e.nbytes <= self.ssd_bytes: over.append(e)
        else: self.stats["dropped"] += 1
    if over:
      if self.spilling is not None: self.spilling.join()
      self.spilling = threading.Thread(target=self._spill, args=(over,), daemon=True)
      self.spilling.start()

  def _spill(self, entries):
    for e in entries:
      path = self.dir / f"prefix-{e.key}.bin"
      with open(path, "wb") as f: e.data.tofile(f)
      e.tokens.tofile(path.with_suffix(".tokens"))   # written last: marks the entry complete
      with self.lock:
        e.path, e.data = path, None
        self.ssd[e.key] = e
        self.stats["spilled"] += 1
      self._trim_ssd()

  def _trim_ssd(self):
    with self.lock:
      disk = sum(x.nbytes for x in self.ssd.values())
      while self.ssd and disk > self.ssd_bytes:
        key, old = next(iter(self.ssd.items()))
        disk -= old.nbytes
        self._drop(self.ssd, key)
        self.stats["dropped"] += 1

  def persist(self):
    """Write every RAM entry to SSD and wait (before the process exits)."""
    if self.dir is None: return
    self._balance(keep_ram=False)
    if self.spilling is not None: self.spilling.join()

  def summary(self):
    with self.lock:
      return {"ram entries": len(self.ram), "ram bytes": sum(e.nbytes for e in self.ram.values()),
              "ssd entries": len(self.ssd), "ssd bytes": sum(e.nbytes for e in self.ssd.values()), **self.stats}
