"""Continuous batching over a model backend: requests share one decode step, one sequence per KV/state slot, and new
prompts prefill in chunks between decode steps so running streams keep advancing.

A backend owns the device graphs and per-slot state. It provides
  slots, capacity, vocab, eos         slot count, positions per slot, logit width, end-of-sequence ids
  prefill(slot, ids, start, end)      process prompt positions start .. end - 1 of ids into slot (start > 0 continues
                                      the slot's state); returns the number of positions it processed (>= 1)
  decode(rows) -> logits [n, vocab]   one token per row: rows are (slot, pos, token)
  reusable(slot, ids, held)           positions of held (the slot's cached tokens) a new prompt ids may keep:
                                      any common prefix for KV-only models, all-or-nothing for recurrent state
  copy_prefix(src, dst, n) -> bool    optional: copy the first n positions of src's state into dst
  prefill_budget                      prompt positions to process between two decode steps while streams are live
"""
import collections, queue, threading, time, traceback

import numpy as np


class Sequence:
  """One request. on_token(seq, token) runs on the engine thread for each generated token and may return True to
  stop (e.g. a stop string). finish_reason is 'stop', 'length', 'cancelled' or 'error' once done is set."""
  def __init__(self, ids, max_new, temperature=0.0, top_p=1.0, top_k=0, min_p=0.0, seed=None, stop_ids=(),
               on_token=None, on_done=None):
    if not ids or max_new < 1: raise ValueError("expected a nonempty prompt and a positive token count")
    self.ids, self.max_new, self.out = list(ids), max_new, []
    self.temperature, self.top_p, self.top_k, self.min_p = temperature, top_p, top_k, min_p
    self.rng = np.random.default_rng(seed)
    self.stop_ids, self.on_token, self.on_done = set(stop_ids), on_token, on_done
    self.slot = self.pos = None
    self.filled = 0              # prompt positions in the slot's state
    self.next_token = self.ids[-1]
    self.done = self.cancelled = False
    self.finish_reason = self.error = None
    self.cached = 0              # prompt positions reused from the slot's previous contents
    self.timings = {"submitted": time.perf_counter()}

  def cancel(self): self.cancelled = True


def sample(seq, x):
  """Draw from softmax(x / temperature) restricted by top-k, top-p and min-p; greedy at temperature 0."""
  if seq.temperature <= 0: return int(np.argmax(x))
  x = x.astype(np.float32) * np.float32(1 / seq.temperature)
  if not (seq.top_k > 0 or seq.top_p < 1 or seq.min_p > 0):  # plain sampling: Gumbel-max over the whole row
    return int(np.argmax(x - np.log(-np.log(seq.rng.random(x.shape, np.float32)))))
  p = np.exp(x - x.max())
  p /= p.sum(dtype=np.float64)
  # Candidates: tokens within 1e-6 of the top probability (the rest hold almost no mass), widened to the whole
  # vocabulary in the rare case the nucleus reaches past them.
  ids = np.flatnonzero(p >= 1e-6 * p.max())
  if seq.top_p < 1 and p[ids].sum() < seq.top_p: ids = np.arange(len(p))
  if seq.top_k and seq.top_k < len(ids): ids = ids[np.argpartition(-p[ids], seq.top_k - 1)[:seq.top_k]]
  ids = ids[np.argsort(-p[ids], kind="stable")]
  probs = p[ids]
  if seq.top_p < 1: probs = probs[:int(np.searchsorted(np.cumsum(probs), seq.top_p)) + 1]
  if seq.min_p > 0: probs = probs[probs >= seq.min_p * probs[0]]
  return int(ids[seq.rng.choice(len(probs), p=probs / probs.sum())])


def common_prefix(a, b):
  n = min(len(a), len(b))
  diff = np.flatnonzero(np.asarray(a[:n]) != np.asarray(b[:n]))
  return int(diff[0]) if len(diff) else n


class Engine:
  def __init__(self, backend, store=None):
    """store: an examples/kvstore.py PrefixStore that evicted slot states go to and prompts restore from."""
    self.backend = b = backend
    self.store = store if store is not None and store.enabled() and hasattr(b, "save") else None
    if self.store is not None: self.store.attach(b.fingerprint)
    self.lock = threading.Lock()   # held by the engine thread while it works on the device
    self.slots, self.cap = b.slots, b.capacity
    self.owner = [None] * self.slots                       # the sequence holding each slot
    self.held = [np.zeros(0, np.int64) for _ in range(self.slots)]  # tokens each slot's state holds, in order
    self.used = [0.0] * self.slots
    self.waiting = collections.deque()
    self.inbox = queue.Queue()
    self.steps = self.decoded = 0
    self.stats = collections.Counter()
    self.times = collections.Counter()   # seconds spent in prefill, decode (device and readback) and sampling

  # ---- admission
  def _reuse(self, s, ids): return self.backend.reusable(s, ids, self.held[s]) if len(self.held[s]) else 0

  def _place(self, seq):
    """Bind seq to a free slot, keeping as much of an earlier sequence's state as its prompt allows."""
    free = [s for s in range(self.slots) if self.owner[s] is None]
    if not free: return False
    ids = np.asarray(seq.ids[:-1], np.int64)  # the last prompt token is the first decode step's input
    if len(ids) + seq.max_new > self.cap:
      seq.max_new = self.cap - len(ids)
      if seq.max_new < 1: raise ValueError(f"the prompt needs {len(ids) + 1} of {self.cap} positions")
    slot = max(free, key=lambda s: (self._reuse(s, ids), -self.used[s]))
    keep = self._reuse(slot, ids)
    copier = getattr(self.backend, "copy_prefix", None)
    src = max(range(self.slots), key=lambda s: self._reuse(s, ids))
    better = self._reuse(src, ids) if copier is not None and src != slot else 0
    entry, stored = (None, 0)
    if self.store is not None:
      entry, stored = self.store.best(ids, lambda tokens: self.backend.reusable(None, ids, tokens))
    gain = 32 if copier is not None else 1   # restoring part of a KV cache pays off past a block
    # The rest of the slot's state is about to be overwritten: save it unless little would be lost.
    if self.store is not None and len(self.held[slot]) - keep >= self.store.min_tokens: self._evict(slot)
    if better >= keep + 32 and better >= stored and copier(src, slot, better):  # another slot, possibly live
      keep = better
      self.stats["prefix copies"] += 1
    elif stored >= keep + gain:
      t0 = time.perf_counter()
      self.backend.load(slot, self.store.get(entry), len(entry.tokens), stored)
      self.times["restore"] += time.perf_counter() - t0
      keep = stored
      self.stats["restored tokens"] += stored
    seq.slot, seq.filled, seq.cached = slot, keep, keep
    self.held[slot] = ids[:keep].copy()
    self.owner[slot] = seq
    self.stats["cached tokens"] += keep
    seq.timings["admitted"] = time.perf_counter()
    return True

  def _evict(self, slot):
    """Save the slot's state to the store before it is overwritten, unless the store already holds it."""
    held = self.held[slot]
    if self.store is None or len(held) < self.store.min_tokens or self.store.covers(held): return
    t0 = time.perf_counter()
    self.store.put(held, self.backend.save(slot, len(held)))
    self.times["save"] += time.perf_counter() - t0

  def _prefill(self, seq, budget):
    """Advance seq's prompt by up to budget positions. Returns the positions processed."""
    ids = np.asarray(seq.ids, np.int64)
    end = min(len(ids) - 1, seq.filled + budget)
    if end <= seq.filled: return 0
    t0 = time.perf_counter()
    done = self.backend.prefill(seq.slot, ids, seq.filled, end)
    self.times["prefill"] += time.perf_counter() - t0
    self.held[seq.slot] = ids[:seq.filled + done].copy()
    seq.filled += done
    self.stats["prompt tokens"] += done
    return done

  def _ready(self, seq): return seq.filled >= len(seq.ids) - 1

  # ---- decoding
  def step(self):
    """One decode step for every slot whose prompt is in; samples, appends and finishes them."""
    live = [s for s in self.owner if s is not None and self._ready(s)]
    if not live: return
    for seq in live:
      if seq.pos is None:
        seq.pos = len(seq.ids) - 1
        seq.timings["prefilled"] = time.perf_counter()
    t0 = time.perf_counter()
    logits = self.backend.decode([(seq.slot, seq.pos, seq.next_token) for seq in live])
    now = time.perf_counter()
    self.times["decode"] += now - t0
    for row, seq in enumerate(live):
      slot = seq.slot
      self.held[slot] = np.append(self.held[slot][:seq.pos], seq.next_token)
      self.used[slot] = now
      seq.pos += 1
      if seq.cancelled: self._finish(seq, "cancelled"); continue
      token = sample(seq, logits[row])
      self.decoded += 1
      if "first token" not in seq.timings: seq.timings["first token"] = now
      if token in self.backend.eos or token in seq.stop_ids: self._finish(seq, "stop"); continue
      seq.out.append(token)
      seq.next_token = token
      stop = seq.on_token(seq, token) if seq.on_token else False
      if stop: self._finish(seq, "stop")
      elif len(seq.out) >= seq.max_new or seq.pos + 1 >= self.cap: self._finish(seq, "length")
    self.steps += 1
    self.times["sample"] += time.perf_counter() - now

  def _finish(self, seq, reason, error=None):
    seq.done, seq.finish_reason, seq.error = True, reason, error
    seq.timings["done"] = time.perf_counter()
    if seq.slot is not None and self.owner[seq.slot] is seq: self.owner[seq.slot] = None
    if seq.on_done: seq.on_done(seq)

  # ---- driving
  def submit(self, seq): self.inbox.put(seq)

  def busy(self): return bool(self.waiting) or any(s is not None for s in self.owner) or not self.inbox.empty()

  def pump(self, block=False):
    """Admit what fits, prefill one budget of prompt positions, then take one decode step. Returns False when idle."""
    try:
      while True: self.waiting.append(self.inbox.get(block=block and not self.busy()))
    except queue.Empty: pass
    while self.waiting:
      seq = self.waiting[0]
      if seq.cancelled:
        self.waiting.popleft()
        self._finish(seq, "cancelled")
        continue
      try:
        if not self._place(seq): break
      except Exception as e:
        traceback.print_exc()
        self._finish(seq, "error", e)
      self.waiting.popleft()
    decoding = any(s is not None and self._ready(s) for s in self.owner)
    # With streams live, process at most one budget of prompt positions per step; else prefill without limit.
    budget = self.backend.prefill_budget if decoding else self.cap
    for seq in sorted((s for s in self.owner if s is not None and not self._ready(s)), key=lambda s: s.timings["admitted"]):
      if seq.cancelled: self._finish(seq, "cancelled"); continue
      try:
        while budget > 0 and not self._ready(seq):
          budget -= self._prefill(seq, budget)
      except Exception as e:
        traceback.print_exc()
        self.held[seq.slot] = np.zeros(0, np.int64)
        self._finish(seq, "error", e)
      if budget <= 0: break
    if not any(s is not None for s in self.owner): return bool(self.waiting)
    self.step()
    return True

  def flush(self):
    """Save every slot's state to the store and write the store's RAM tier to SSD (before shutting down)."""
    if self.store is None: return
    with self.lock:
      for slot in range(self.slots): self._evict(slot)
      self.store.persist()

  def run(self, sequences=()):
    """Run until every submitted sequence is done."""
    for s in sequences: self.submit(s)
    while self.pump() or self.busy(): pass

  def serve(self):
    """The engine thread: pump forever, sleeping on the inbox when idle. A failed step ends the live sequences."""
    while True:
      try:
        self._wait()
        with self.lock: self.pump()
      except Exception as e:
        traceback.print_exc()
        for seq in [s for s in self.owner if s is not None]:
          self.held[seq.slot] = np.zeros(0, np.int64)
          self._finish(seq, "error", e)

  def _wait(self):
    """Block until there is work."""
    if not self.busy(): self.waiting.append(self.inbox.get())

  def start(self):
    t = threading.Thread(target=self.serve, name="engine", daemon=True)
    t.start()
    return t
