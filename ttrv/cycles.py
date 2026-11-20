"""Offline execution of one TTRV launch on the p150 worker grid."""

import gzip
import hashlib
import heapq
import json
from pathlib import Path
import itertools
import operator
import random
from statistics import median
import struct
from collections import Counter, defaultdict
from functools import lru_cache

import fw
from .cycle_argmax import ArgmaxScan, scan_vocab
from .cycle_tensix import Thread, Tile
from . import hw, isa
from .cycle_noc import Network

MASK = (1 << 32) - 1
OPS = {
  "add": operator.add,
  "sub": operator.sub,
  "and": operator.and_,
  "or": operator.or_,
  "xor": operator.xor,
  "mul": operator.mul,
  "sll": lambda a, b: a << (b & 31),
  "srl": lambda a, b: a >> (b & 31),
  "sra": lambda a, b: signed(a) >> (b & 31),
  "sltu": operator.lt,
  "slt": lambda a, b: signed(a) < signed(b),
}
BRANCH = {
  "beq": operator.eq,
  "bne": operator.ne,
  "bltu": operator.lt,
  "bgeu": operator.ge,
  "blt": lambda a, b: signed(a) < signed(b),
  "bge": lambda a, b: signed(a) >= signed(b),
}
WIDTH = {"lb": 1, "lbu": 1, "lh": 2, "lhu": 2, "lw": 4, "sb": 1, "sh": 2, "sw": 4}


def signed(n):
  return n - (1 << 32) if n >> 31 else n


class Memory:
  """Sparse zero-initialized memory, including byte-granular DMA transfers."""

  def __init__(self):
    self.pages = {}

  def read(self, addr, size):
    data = bytearray()
    while size:
      page, offset = divmod(addr, 4096)
      chunk = min(size, 4096 - offset)
      data.extend(self.pages[page][offset : offset + chunk] if page in self.pages else bytes(chunk))
      addr, size = addr + chunk, size - chunk
    return data

  def write(self, addr, data):
    while data:
      page, offset = divmod(addr, 4096)
      chunk = min(len(data), 4096 - offset)
      if page not in self.pages:
        self.pages[page] = bytearray(4096)
      self.pages[page][offset : offset + chunk] = data[:chunk]
      addr, data = addr + chunk, data[chunk:]


@lru_cache(None)
def decode(word):
  ins = isa.rv_decode(word) if word & 3 == 3 else isa.tensix_decode(isa.outline(word))
  if not ins:
    raise ValueError(f"unknown instruction {word:#010x}")
  return ins


@lru_cache(None)
def operands(word):
  op, fields = decode(word)
  return op, fields.get("rd", 0), fields.get("rs1", 0), fields.get("rs2", 0), fields.get("imm", 0), "imm" in fields


DEFAULT_STARTUP = Path(__file__).resolve().parents[1] / "sims/results/2026-11-19-joint-startup-card0.json"


def firmware_fingerprint():
  digest = hashlib.sha256()
  for file in sorted({*fw.HERE.glob("*.h"), *fw.HERE.glob("worker_*.c"), fw.HERE / "noc.c", fw.HERE / "__init__.py"}):
    digest.update(file.name.encode() + b"\0" + file.read_bytes() + b"\0")
  return digest.hexdigest()


@lru_cache(maxsize=1)
def clock_offsets():
  file = Path(__file__).resolve().parents[1] / "sims/results/2026-11-19-noc-calibration-card0.jsonl.gz"
  with gzip.open(file, "rt") as samples:
    clocks = next(r["offsets"] for r in map(json.loads, samples) if r.get("id") == "clockmap")
  return {tuple(map(int, xy.split(","))): round(offset) for xy, offset in clocks.items()}


def startup_profile(profile=None):
  simultaneous = dict.fromkeys(fw.ROLES, 0)
  if profile == "simultaneous":
    return simultaneous, "simultaneous role entry"
  explicit = profile is not None
  path = Path(profile) if explicit else DEFAULT_STARTUP
  if not explicit and not path.exists():
    return simultaneous, "no startup calibration; assuming simultaneous role entry"
  data = json.loads(path.read_text())
  if not isinstance(data, dict):
    raise ValueError("startup profile must be a JSON object")
  if data.get("firmware_sha256") != firmware_fingerprint():
    if explicit:
      raise ValueError(f"startup calibration {path} belongs to different worker firmware")
    return simultaneous, "unmeasured worker firmware; assuming simultaneous role entry"
  offsets = data.get("role_offsets")
  if (
    not isinstance(offsets, dict)
    or offsets.keys() != simultaneous.keys()
    or not all(type(v) is int for v in offsets.values())
  ):
    raise ValueError("startup profile requires integer offsets for all five RISCs")
  return offsets, str(path.name)


class Registers(dict):
  """A tile's MMIO register values. Writes wake RISCs sleeping in a poll loop on that tile."""

  def __init__(self, sim, xy):
    super().__init__()
    self.sim, self.xy = sim, xy

  def __setitem__(self, key, value):
    super().__setitem__(key, value)
    if self.sim.sleepers[self.xy]:
      self.sim.poke(self.xy, lambda core: key in core.watch_mmio)


class Simulation:
  def __init__(self):
    self.time = 0
    self.refresh_phase = 0
    self.cache_phase = 0
    self.events = []
    self.serial = itertools.count()
    self.memories = {}
    self.network = Network(self)
    self.shared = {}
    self.tiles = {}
    self.sleepers = defaultdict(list)

  def memory(self, key):
    mem = self.memories.get(key)
    if mem is None:
      mem = self.memories[key] = Memory()
    return mem

  def registers(self, xy):
    regs = self.shared.get(xy)
    if regs is None:
      regs = self.shared[xy] = Registers(self, xy)
    return regs

  def tile(self, xy):
    t = self.tiles.get(xy)
    if t is None:
      t = self.tiles[xy] = Tile()
      # Pollers read semaphores only; Src valid and other Tensix state changes do not concern them.
      t.on_change = lambda: self.sleepers[xy] and self.poke(xy, lambda core: core.watch_tile and core.sem_seen != t.sem)
    return t

  def poke(self, xy, affected):
    """Shared state on tile xy changed: each RISC spinning on that state re-polls at its next load slot."""
    sleepers = self.sleepers[xy]
    woken = [core for core in sleepers if affected(core)]
    if woken:
      self.sleepers[xy] = [core for core in sleepers if core.sleep is not None and core not in woken]
      for core in woken:
        core.wake()

  def after(self, delay, callback):
    heapq.heappush(self.events, (self.time + delay, next(self.serial), callback))

  def at(self, time, callback):
    heapq.heappush(self.events, (time, next(self.serial), callback))


class Risc:
  def __init__(self, sim, xy, role, image):
    self.sim, self.xy, self.role, self.image = sim, xy, role, image
    self.tile = sim.memory(xy)
    self.private = Memory()
    self.private_size = 4096 if role.startswith("trisc") else 8192
    self.regs = [0] * 32
    self.ready = [0] * 32
    self.cause = [""] * 32
    self.l0 = {}
    # DisLowCachePeriodicFlush is clear in the measured firmware. Pick a
    # reproducible starting phase for each RISC's roughly 1-in-128 flush.
    self.l0_access = (31 * xy[0] + 17 * xy[1] + 13 * fw.ROLES.index(role) + sim.cache_phase) % 128
    self.fetched = {0}
    self.fetch_line = 0
    self.redirect = False
    self.fetch_ready = None
    self.inline_seen = set()
    self.pc = 0
    self.count = Counter()
    self.predict = {}
    self.mmio = sim.registers(xy)
    self.thread = Thread(sim, sim.tile(xy), role, xy) if role.startswith("trisc") else None
    self.last_store = -100
    self.instructions = 0
    self.noc_stats = Counter()
    self.end = None
    self.poll = None
    self.poll_cycles = Counter()
    self.t = 0
    self.spin = None
    self.sleep = None
    self.stored = False
    self.last_shared = None
    self.watch_mmio, self.watch_tile, self.unwatchable = set(), False, False
    self.sem_seen = None
    self.caps = {}  # pc -> [(name, location)]: shared trip counts to record and scale on first arrival
    self.trip = {}
    self.scale = None

  def memory_op(self, addr, name, value):
    load, size = name.startswith("l"), WIDTH[name]
    if addr % size:
      raise ValueError(f"misaligned {name} at {addr:#x}")
    if addr + size <= hw.L1_SIZE or hw.LOCAL_MEM <= addr <= hw.LOCAL_MEM + self.private_size - size:
      local = addr >= hw.LOCAL_MEM
      mem = self.private if local else self.tile
      if load:
        latency = 2
        if local:
          data = mem.read(addr, size)
        else:
          line, offset = divmod(addr, 16)
          self.l0_access = (self.l0_access + 1) % 128
          if self.l0_access == 0:
            self.l0.clear()
          if line not in self.l0:
            if len(self.l0) == 4:
              self.l0.pop(next(iter(self.l0)))
            self.l0[line] = mem.read(addr - offset, 16)
            latency = 8
          data = self.l0[line][offset : offset + size]
        return (
          int.from_bytes(data, "little", signed=name in ("lb", "lh")),
          latency,
          "private_load" if local else "l1_load",
        )
      if not local:
        self.l0.pop(addr // 16, None)
      mem.write(addr, value.to_bytes(4, "little")[:size])
      return 0, 1, "private_store" if local else "l1_store"
    if load and size == 4 and addr in (0xFFB121F0, 0xFFB121F8):
      if addr == 0xFFB121F0:
        clock = (self.sim.time + clock_offsets()[self.xy]) & ((1 << 64) - 1)
        self.mmio[0xFFB121F8] = clock >> 32
        return clock & MASK, 7, "wall_clock_load"
      return self.mmio.get(addr, 0), 7, "wall_clock_load"
    niu = hw.NOC0_REGS <= addr < hw.NOC0_REGS + 2 * hw.NOC_INSTANCE_OFFSET
    overlay = hw.OVERLAY_STREAMS <= addr < hw.OVERLAY_STREAMS + 64 * hw.STREAM_STRIDE
    if size != 4 and not (overlay and name == "lhu"):
      raise ValueError(f"unmodelled {name} at MMIO {addr:#x}")
    if niu:
      noc, off = divmod(addr - hw.NOC0_REGS, hw.NOC_INSTANCE_OFFSET)
      if load and off == hw.NOC_ID_LOGICAL:
        return hw.coord(*self.xy), 7, "niu_load"
      status = off % hw.CMD_BUF_STRIDE == hw.Cmd.CMD_CTRL or hw.outstanding(0) <= off <= hw.outgoing(15)
      if load:
        if status and self.mmio.get(addr):
          wait = (
            "noc_command_wait"
            if off % hw.CMD_BUF_STRIDE == hw.Cmd.CMD_CTRL
            else "noc_sent_wait"
            if off >= hw.outgoing(0)
            else "noc_response_wait"
          )
          return self.mmio[addr], 7, wait
        return self.mmio.get(addr, 0), 7, "niu_load"
      if off % hw.CMD_BUF_STRIDE == hw.Cmd.CMD_CTRL:
        self.sim.network.send(self, noc, self.mmio, addr - hw.Cmd.CMD_CTRL)
      else:
        self.mmio[addr] = value
      return 0, 1, "niu_store"
    if overlay:
      if load:
        return self.mmio.get(addr, 0) & ((1 << (8 * size)) - 1), 7, "cb_load"
      self.mmio[addr] = value
      return 0, 1, "cb_store"
    thread = self.thread
    if thread and hw.SEMAPHORE_ACCESS <= addr < hw.SEMAPHORE_ACCESS + 32:
      i = (addr - hw.SEMAPHORE_ACCESS) // 4
      if load:
        return thread.tile.sem[i], 3, "semaphore_load"
      thread.tile.sem[i] = max(0, min(15, thread.tile.sem[i] + (-1 if value & 1 else 1)))
      thread.tile.changed()
      return 0, 1, "semaphore_store"
    if thread and hw.MOP_CFG <= addr < hw.MOP_CFG + 36 and not load:
      thread.mop[(addr - hw.MOP_CFG) // 4] = value
      return 0, 1, "mop_config"
    if hw.TENSIX_CFG <= addr < hw.TENSIX_CFG + 4096:
      regs = self.sim.tile(self.xy).cfg
      reg = (addr - hw.TENSIX_CFG) // 4
      if load:
        return regs[reg], 4, "config_load"
      regs[reg] = value
      return 0, 1, "config_store"
    if thread and hw.REGFILE <= addr < hw.REGFILE + 256:
      reg = (addr - hw.REGFILE) // 4
      if load:
        return thread.gpr[reg], 4, "gpr_load"
      thread.gpr[reg] = value
      return 0, 1, "gpr_store"
    if thread and addr == hw.INSTRN_BUF and not load:
      thread.push(value)
      return 0, 1, "tensix_push"
    if addr in (hw.COPROCESSOR_DONE_CHECK, hw.MOP_EXPANDER_DONE_CHECK):
      return 0, 3 if load else 1, "tensix_sync"
    raise ValueError(f"unmodelled MMIO {name} at {addr:#x}")

  def at(self, time):
    """Continue execution at absolute cycle `time` (not before the current global time)."""
    self.t = time
    self.sim.at(max(time, self.sim.time), self.run)

  def retry(self, group, delay=1):
    self.count[group] += delay
    self.instructions -= 1
    self.at(self.sim.time + delay)

  def wait_thread(self, group, event):
    begin = self.sim.time
    self.instructions -= 1

    def resume():
      self.count[group] += self.sim.time - begin
      self.at(self.sim.time)

    setattr(self.thread, event, resume)

  def apply_caps(self, pc):
    """Record each shared trip count when the prelude leaves it at pc, and scale it for a sampled run."""
    for name, (kind, where) in self.caps.pop(pc):
      if kind == "x":
        value = self.regs[where]
      else:
        value = int.from_bytes(self.private.read(where, 4), "little")
      self.trip[name] = value
      if self.scale is not None and value:
        value = max(1, round(value * self.scale))
        if kind == "x":
          self.regs[where] = value
        else:
          self.private.write(where, value.to_bytes(4, "little"))

  def wake(self):
    """Shared state changed while spinning: resume at the first iteration whose poll load can see it."""
    head, period, offset, counts, polls, instructions = self.sleep
    self.sleep = None
    k = max(0, -((head + offset - self.sim.time) // period))
    if k:
      for group, n in counts.items():
        self.count[group] += k * n
      for group, n in polls.items():
        self.poll_cycles[group] += k * n
      self.instructions += k * instructions
    if self.spin:
      self.spin = self.spin[0], head + k * period, dict(self.count), dict(self.poll_cycles), self.instructions
    self.at(head + k * period)

  def run(self):
    """Execute until the next access to state another agent can see, a spin, or the return.

    Instructions that only touch registers and private memory run ahead of the global clock. An instruction
    that reads or writes L1, MMIO or the Tensix FIFO waits for the global clock to reach its issue cycle.
    A loop iteration that stores nothing and leaves every register unchanged is a poll: the RISC sleeps
    until its tile's shared state changes and is charged the skipped iterations.
    """
    sim, image, regs, ready, count = self.sim, self.image, self.regs, self.ready, self.count
    t = self.t
    private_lo, private_hi = hw.LOCAL_MEM, hw.LOCAL_MEM + self.private_size
    while True:
      pc = self.pc
      if pc % 4 or not 0 <= pc // 4 < len(image):
        raise ValueError("PC outside image")
      if self.caps and pc in self.caps:
        self.apply_caps(pc)
      # Eight lines can be prefetched while the integer pipe is stalled. Use thirds
      # of a cycle for the measured 16-byte refill interval (5 or 4+2/3 cycles).
      line = pc // 16
      if line not in self.fetched:
        if self.fetch_ready is None:
          self.fetch_ready = 3 * t
        self.fetched.add(line)
        period = 15 if self.role == "ncrisc" else 14
        delta = line - self.fetch_line
        if self.redirect and (delta < 0 or delta >= 4):
          # A new distant target can be requested directly. The cold-jump sweep
          # plateaus at about 15 cycles per jump, independent of skipped bytes.
          self.fetch_ready = 3 * t + 42
        elif 1 <= delta <= 8:
          self.fetch_ready = max(self.fetch_ready + delta * period, 3 * t - 7 * period)
        else:
          self.fetch_ready = 3 * t + period
        self.fetch_line = line
        delay = (self.fetch_ready + 2) // 3 - t
        if delay > 0:
          count["instruction_fetch"] += delay
          t += delay
      elif self.fetch_ready is None:
        self.fetch_ready = 3 * t
      word = image[pc // 4]
      op, rd, a, b, imm, immediate = operands(word)
      dep = a if ready[a] >= ready[b] else b
      if ready[dep] > t:
        count[self.cause[dep]] += ready[dep] - t
        t = ready[dep]
      x, y = regs[a], regs[b]
      inline = word & 3 != 3
      if inline:
        # A push needs the global clock only when the FIFO might be full; the thread starts each
        # instruction no earlier than the cycle the RISC pushed it.
        shared = self.thread is None or len(self.thread.fifo) > 24
      elif op in WIDTH:
        addr = (x + imm) & MASK
        shared = not private_lo <= addr <= private_hi - WIDTH[op]
      else:
        shared = False
      if shared and t != sim.time:
        if t > sim.time:
          self.at(t)
          return
        t = sim.time
      self.instructions += 1
      now = t
      nextpc = pc + 4
      value, cost, latency, group = 0, 1, 1, "alu"
      if inline:
        if not self.thread:
          raise ValueError("inline Tensix instruction on data movement RISC")
        if len(self.thread.fifo) > 28:
          return self.wait_thread("tensix_fifo_wait", "on_space")
        # Prefetch fusion delivers up to four adjacent inline words in one RISC cycle.
        n = 0
        limit = 4 if pc in self.inline_seen else 1
        while n < limit and pc // 4 + n < len(image):
          raw = image[pc // 4 + n]
          if raw & 3 == 3 or (n and pc + 4 * n not in self.inline_seen):
            break
          self.inline_seen.add(pc + 4 * n)
          self.thread.push(isa.outline(raw), now)
          n += 1
        nextpc = pc + 4 * n
        self.instructions += n - 1
        self.stored = True
        group = "tensix_push"
      elif op in WIDTH:
        if self.thread and addr == hw.INSTRN_BUF and len(self.thread.fifo) > 28:
          return self.wait_thread("tensix_fifo_wait", "on_space")
        if self.thread and addr in (hw.COPROCESSOR_DONE_CHECK, hw.MOP_EXPANDER_DONE_CHECK) and op == "lw":
          if self.thread.active:
            return self.wait_thread("tensix_drain", "on_drain")
          for cond in self.thread.conditions:
            if cond[1]["stall_res"] & isa.Stall.SYNC and (waiting := self.thread.condition(cond)):
              return self.retry(*waiting)
          remaining = self.thread.done - now
          if addr == hw.COPROCESSOR_DONE_CHECK and remaining > 0:
            return self.retry("tensix_drain", remaining)
        value, latency, group = self.memory_op(addr, op, y)
        if op.startswith("s"):
          self.last_store = now
          self.stored = True
        else:
          if shared:
            self.last_shared = now
            if group == "semaphore_load":
              self.watch_tile = True
            elif group == "l1_load" or group in ("config_load", "gpr_load", "wall_clock_load"):
              # L0-cached L1 reads, Tensix config and the clock change without a wake-up.
              self.unwatchable = True
            else:
              self.watch_mmio.add(addr)
          if group in ("cb_load", "semaphore_load") or group.startswith("noc_"):
            self.poll = pc, now, group
      elif op in BRANCH:
        taken = BRANCH[op](x, y)
        if taken:
          nextpc = pc + imm
        if taken != self.predict.get(pc, False):
          cost += 4
        self.predict[pc] = taken
        if taken and self.poll and nextpc == self.poll[0]:
          _, begin, kind = self.poll
          self.poll_cycles[kind] += now + cost - begin
        group = "branch"
        if taken and self.poll and nextpc == self.poll[0] and self.poll[2].startswith("noc_"):
          group = self.poll[2]
      elif op in ("jal", "jalr"):
        value = fw.CODE[self.role] + pc + 4
        nextpc = pc + imm if op == "jal" else ((x + imm) & ~1) - fw.CODE[self.role]
        group = "branch"
        if op == "jalr" and x + imm == fw.RETURN[self.role]:
          self.end = now + 1
      elif op == "lui":
        value = imm << 12
      elif op == "auipc":
        value = fw.CODE[self.role] + pc + (imm << 12)
      elif op in ("divu", "remu", "div", "rem"):
        if op in ("div", "rem"):
          x, y = signed(x), signed(y)
        q = (abs(x) // abs(y)) * (-1 if (x < 0) != (y < 0) else 1) if y else -1
        value = q if op.startswith("div") else x - q * y
        cost = (
          2 if y in (0, 1) or (x == -(1 << 31) and y == -1) else min(33, 2 + 4 * max(1, (abs(x).bit_length() + 3) // 4))
        )
        group = "divide"
      elif op in ("mulh", "mulhu", "mulhsu"):
        lhs = x if op == "mulhu" else signed(x)
        rhs = signed(y) if op == "mulh" else y
        value, latency, group = (lhs * rhs) >> 32, 2, "multiply"
      elif op in ("sh1add", "sh2add", "sh3add"):
        value = y + (x << int(op[2]))
      elif op == "fence":
        self.l0.clear()
        cost, group = max(4, self.last_store + 9 - now), "fence"
      else:
        base = op.replace("sltiu", "sltu") if op == "sltiu" else op.removesuffix("i") if immediate else op
        if base not in OPS:
          raise ValueError(f"unmodelled RV instruction {op}")
        value = OPS[base](x, (imm & MASK) if immediate else y)
        if op == "mul":
          latency, group = 2, "multiply"
      count[group] += cost
      if rd:
        regs[rd], ready[rd], self.cause[rd] = value & MASK, now + latency, group
      self.redirect = nextpc != pc + 4 and (op in BRANCH or op in ("jal", "jalr"))
      self.pc = nextpc
      t = now + cost
      if self.end is not None:
        return
      if nextpc <= pc and self.redirect and op != "jalr":
        # Back edge: compare this iteration with the previous one at the same head.
        key = nextpc, tuple(regs)
        spin = self.spin
        if spin and not self.stored and not self.unwatchable and spin[0] == key and self.last_shared is not None:
          _, head0, counts0, polls0, instructions0 = spin
          self.sleep = (
            t,
            t - head0,
            self.last_shared - head0,
            {g: n - counts0.get(g, 0) for g, n in count.items() if n != counts0.get(g, 0)},
            {g: n - polls0.get(g, 0) for g, n in self.poll_cycles.items() if n != polls0.get(g, 0)},
            self.instructions - instructions0,
          )
          if self.watch_tile:
            self.sem_seen = list(self.thread.tile.sem)
          sim.sleepers[self.xy].append(self)
          self.stored, self.last_shared = False, None
          return
        self.spin = key, t, dict(count), dict(self.poll_cycles), self.instructions
        self.stored, self.last_shared, self.unwatchable = False, None, False
        self.watch_mmio.clear()
        self.watch_tile = False


def _simulate(
  kernel,
  *,
  bindings=None,
  arguments=None,
  max_cycles=10_000_000,
  dram=None,
  inputs=None,
  tile_inputs=None,
  startup=None,
  trial=0,
  trials=1,
  scale=None,
):
  """bindings contains runtime-format addresses and integer values. dram maps physical bank to {offset: bytes}.

  scale multiplies every shared trip count (kernel.timing) as the prelude computes it, for a sampled run."""
  sim = Simulation()
  sim.network.rng.seed(trial)
  rng = random.Random(trial)
  if trial:
    sim.refresh_phase = rng.random() * 2497.5
    sim.cache_phase = (79 * trial) % 128
  if max_cycles < 1:
    raise ValueError("max_cycles must be positive")
  if arguments is None:
    bindings = bindings or {}
    missing = kernel.manifest["params"].keys() - bindings.keys()
    if missing:
      raise ValueError(f"missing launch bindings {sorted(missing)}")
    arguments = kernel.arguments(bindings)
  elif bindings is not None or not kernel.args_size <= len(arguments) <= fw.PARAM_SIZE:
    raise ValueError("invalid argument block or both arguments and bindings supplied")
  for name, data in (inputs or {}).items():
    param = kernel.manifest["params"].get(name)
    if not param or param["kind"] != "dram":
      raise ValueError(f"{name}: expected DRAM parameter for input data")
    page = param["page"]
    (encoded,) = struct.unpack_from("<I", arguments, 4 * param["slot"])
    bank = encoded & 7
    offset = encoded - bank
    for pos in range(0, len(data), page):
      sim.memory(("dram", bank)).write(offset, data[pos : pos + page])
      bank = (bank + 1) % 8
      if not bank:
        offset += page
  for bank, segments in (dram or {}).items():
    for offset, data in segments.items():
      sim.memory(("dram", bank)).write(offset, data)
  for (x, y, name), data in (tile_inputs or {}).items():
    storage = kernel.manifest["storage"].get(name)
    if not storage or len(data) > storage["size"]:
      raise ValueError(f"unknown or oversized L1 input {name} on tile ({x},{y})")
    if (
      x not in hw.WORKER_COLUMNS
      or not 2 <= y < 12
      or 10 * hw.WORKER_COLUMNS.index(x) + y - 2 >= kernel.manifest["grid"]
    ):
      raise ValueError(f"L1 input tile ({x},{y}) is outside the launch grid")
    sim.memory((x, y)).write(storage["address"], data)
  images = {r: tuple(x[0] for x in struct.iter_unpack("<I", img)) for r, img in kernel.images.items()}
  roles = []
  grid = kernel.manifest["grid"]
  if not 1 <= grid <= 138:
    raise ValueError(f"invalid p150 worker count {grid}")
  # Card 0 role_cycles.py, unprofiled resident firmware. Relative to BRISC entry.
  # GO is a NoC0 multicast; each intervening router adds nine cycles.
  if not images:
    raise ValueError("kernel has no active RISC images")
  entry, startup_source = startup_profile(startup)
  phases = None
  if trials > 1 and entry["ncrisc"] and "ncrisc" in images:
    data = json.loads(Path(startup or DEFAULT_STARTUP).read_text())
    measured = data.get("ncrisc_phases")
    if measured:
      if not all(
        isinstance(row, list) and len(row) == data.get("grid") and all(type(n) is int for n in row) for row in measured
      ):
        raise ValueError("invalid measured NCRISC phase vectors")
      if grid <= data["grid"]:
        phases = measured[(2 * trial + 1) * len(measured) // (2 * trials)]
  # Dispatcher at (16,10). The NoC0 y ring wraps before reaching row 2.
  hop_counts = [(hw.WORKER_COLUMNS[i // 10] - 16) % 17 + ((2 + i % 10) - 10) % 12 for i in range(grid)]
  vocab = scan_vocab(kernel)
  for i in range(grid):
    xy = hw.WORKER_COLUMNS[i // 10], 2 + i % 10
    tile = sim.memory(xy)
    if vocab is not None:
      sim.tile(xy).argmax = ArgmaxScan(tile, kernel.manifest["storage"], i, vocab)
    tile.write(fw.WORKER_X, struct.pack("<III", i // 10, i % 10, i))
    tile.write(fw.L1_PARAM_BASE, arguments)
    for role, image in images.items():
      risc = Risc(sim, xy, role, image)
      risc.caps = trip_marks(kernel, role)
      risc.scale = scale
      roles.append(risc)
      risc.start = entry[role] + 9 * hop_counts[i]
      if phases is not None and role == "ncrisc":
        risc.start += phases[i] - entry[role]
      elif trial and role == "ncrisc" and startup_source != "simultaneous role entry" and entry["ncrisc"] > 0:
        # WAIT_SLOW polls after 64 two-instruction iterations. Sample its phase.
        risc.start += rng.randrange(-64, 65)
  origin = min(r.start for r in roles)
  for r in roles:
    r.start -= origin
    r.at(r.start)
  while sim.events:
    sim.time, _, callback = heapq.heappop(sim.events)
    if sim.time > max_cycles:
      raise ValueError(f"exceeded {max_cycles} cycles (blocked or increase --max-cycles)")
    try:
      callback()
    except ValueError as exc:
      core = getattr(callback, "__self__", None)
      if isinstance(core, Thread):
        raise ValueError(f"{core.xy} {core.role} backend at cycle {sim.time}: {exc}") from exc
      if isinstance(core, Risc):
        raise ValueError(f"{core.xy} {core.role} +{core.pc:#x}: {exc}") from exc
      raise
  blocked = [(r.xy, r.role, r.pc) for r in roles if r.end is None]
  if blocked:
    raise ValueError(f"kernel blocked without a runnable event: {blocked[:5]}")
  tiles = {}
  for r in roles:
    tile = tiles.setdefault(r.xy, dict(x=r.xy[0], y=r.xy[1], cores={}))
    tile["cores"][r.role] = dict(
      start=r.start,
      finish=r.end,
      cycles=r.end - r.start,
      instructions=r.instructions,
      breakdown=dict(r.count),
      poll_cycles=dict(r.poll_cycles),
    )
    row = tile["cores"][r.role]
    if r.trip:
      tile.setdefault("trip_counts", {}).update(r.trip)
    if r.noc_stats:
      row["noc"] = dict(r.noc_stats)
    if r.thread:
      row["backend"] = dict(r.thread.count)
      row["unit_busy"] = dict(r.thread.unit_cycles)
      row["backend_finish"] = max(r.end, r.thread.done)
  for tile in tiles.values():
    cores = tile["cores"]
    tile["inactive"] = [r for r in fw.ROLES if r not in cores]
    tile["start"] = min(row["start"] for row in cores.values())
    tile["finish"] = max(row["finish"] for row in cores.values())
    tile["cycles"] = tile["finish"] - tile["start"]
    tile["backend_finish"] = max(row.get("backend_finish", row["finish"]) for row in cores.values())
  return dict(
    model="experimental p150",
    startup=startup_source,
    role_entry_offsets=entry,
    memory="zero-initialized except supplied data",
    tensor_values="BF16 argmax candidate values" if vocab is not None else "timing only",
    unit="AICLK",
    interval="kernel entry through firmware return instruction",
    cycles=max(r.end for r in roles),
    backend_finish=max(t["backend_finish"] for t in tiles.values()),
    tiles=list(tiles.values()),
  )


def trip_marks(kernel, role):
  """pc -> [(name, location)] for each shared value that bounds a runtime loop in this role's image."""
  meta = getattr(kernel, "timing", None)
  if not meta:
    return {}
  marks = defaultdict(list)
  for name, m in meta["shared"].get(role, {}).items():
    if name in meta["trip_counts"]:
      marks[m["pc"]].append((name, tuple(m["loc"])))
  return dict(marks)


def trip_counts(kernel, arguments):
  """Each worker's shared trip counts, from running only the shared preludes (no other agent is simulated)."""
  meta = getattr(kernel, "timing", None)
  if not meta or not meta["trip_counts"]:
    return None
  images = {r: tuple(x[0] for x in struct.iter_unpack("<I", img)) for r, img in kernel.images.items()}
  wanted = set(meta["trip_counts"])
  out = []
  for i in range(kernel.manifest["grid"]):
    sim = Simulation()
    xy = hw.WORKER_COLUMNS[i // 10], 2 + i % 10
    tile = sim.memory(xy)
    tile.write(fw.WORKER_X, struct.pack("<III", i // 10, i % 10, i))
    tile.write(fw.L1_PARAM_BASE, arguments)
    found = {}
    for role, image in images.items():
      marks = trip_marks(kernel, role)
      if not {n for m in marks.values() for n, _ in m} - found.keys():
        continue
      core = Risc(sim, xy, role, image)
      core.caps = marks
      core.at(0)
      while sim.events and core.caps and core.end is None and sim.time < 100_000:
        sim.time, _, callback = heapq.heappop(sim.events)
        callback()
      found.update(core.trip)
      if wanted <= found.keys():
        break
    if not wanted <= found.keys():
      return None
    out.append(found)
  return out


def _extrapolate(a, b, xa, xb):
  """Value at x = 1 of the line through (xa, a) and (xb, b), applied to every number in matching structures."""
  if isinstance(a, dict):
    return {k: _extrapolate(a.get(k, 0), b.get(k, 0), xa, xb) for k in a.keys() | b.keys()}
  if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
    if xb == xa:
      return b
    return round(a + (1 - xa) * (b - a) / (xb - xa))
  return b


def _run_parallel(kernel, launches):
  """_simulate each launch, in forked worker processes when the platform allows it."""
  import multiprocessing as mp
  import os

  if len(launches) < 2 or (os.cpu_count() or 1) < 2 or "fork" not in mp.get_all_start_methods():
    return [_simulate(kernel, **launch) for launch in launches]
  with mp.get_context("fork").Pool(len(launches)) as pool:
    return pool.starmap(_simulate_star, [(kernel, launch) for launch in launches])


def _simulate_star(kernel, launch):
  return _simulate(kernel, **launch)


def _sampled(kernel, sample_iterations, **launch):
  """Two short runs with every shared trip count scaled down, extrapolated linearly to the real counts.

  Each tile's report is the line through its two sampled reports, evaluated at its own full trip counts. A kernel
  whose iterations cost the same, apart from fill and drain, is linear in its trip count, so this charges
  prologue, epilogue, fill and drain once and the steady-state iteration cost per remaining iteration."""
  arguments = launch.get("arguments")
  if arguments is None:
    arguments = kernel.arguments(launch.get("bindings") or {})
  counts = trip_counts(kernel, arguments)
  if not counts:
    return None
  largest = max((v for c in counts for v in c.values()), default=0)
  # A count that wrapped below zero belongs to a worker that skips the loop; scaling it is meaningless.
  if largest < 4 * sample_iterations or largest >= 1 << 20:
    return None
  scales = sample_iterations / largest, 2 * sample_iterations / largest
  runs = _run_parallel(kernel, [dict(launch, scale=f) for f in scales])

  def coordinate(full, f):
    total = sum(full.values())
    return sum(max(1, round(v * f)) if v else 0 for v in full.values()) / total if total else 1

  tiles = []
  for i, (ta, tb) in enumerate(zip(runs[0]["tiles"], runs[1]["tiles"])):
    xa, xb = coordinate(counts[i], scales[0]), coordinate(counts[i], scales[1])
    tile = dict(tb)
    cores = {}
    for role in tb["cores"]:
      row = _extrapolate(ta["cores"][role], tb["cores"][role], xa, xb)
      row["start"] = tb["cores"][role]["start"]
      bd = row["breakdown"] = {k: v for k, v in row["breakdown"].items() if v}
      row["cycles"] = max(1, row["cycles"])
      if bd:
        # Rounding each category separately can leave the sum a few cycles off the total.
        bd[max(bd, key=bd.get)] += row["cycles"] - sum(bd.values())
      row["finish"] = row["start"] + row["cycles"]
      if "backend_finish" in row:
        row["backend_finish"] = max(row["finish"], row["backend_finish"])
      cores[role] = row
    tile["cores"] = cores
    tile["trip_counts"] = counts[i]
    tile["start"] = min(r["start"] for r in cores.values())
    tile["finish"] = max(r["finish"] for r in cores.values())
    tile["cycles"] = tile["finish"] - tile["start"]
    tile["backend_finish"] = max(r.get("backend_finish", r["finish"]) for r in cores.values())
    tiles.append(tile)
  report = dict(runs[1])
  report["tiles"] = tiles
  report["cycles"] = max(t["finish"] for t in tiles)
  report["backend_finish"] = max(t["backend_finish"] for t in tiles)
  report["sampling"] = dict(
    method="two runs with scaled shared trip counts, extrapolated linearly per tile and RISC",
    trip_counts=sorted(kernel.timing["trip_counts"]),
    scales=[round(f, 6) for f in scales],
    largest_trip_count=largest,
  )
  return report


def estimate(kernel, *, samples=1, sample_iterations=32, **launch):
  """Run the launch offline. Multiple trials vary the unknown refresh and NCRISC polling phases.

  When the kernel's shared trip counts are large, the launch is simulated twice at about sample_iterations and
  2 * sample_iterations iterations and extrapolated (_sampled). sample_iterations=None simulates every iteration."""
  if samples < 1:
    raise ValueError("samples must be positive")
  if sample_iterations and samples == 1:
    report = _sampled(kernel, sample_iterations, **launch)
    if report is not None:
      return report
  runs = [_simulate(kernel, trial=i, trials=samples, **launch) for i in range(samples)]
  if samples == 1:
    return runs[0]

  def intervals(run):
    yield run
    for tile in run["tiles"]:
      yield tile
      yield from tile["cores"].values()

  vectors = [list(intervals(run)) for run in runs]
  medians = [median(row["cycles"] for row in group) for group in zip(*vectors)]
  # Keep one coherent timeline. Each interval also carries its own median and sampled range.
  index = min(
    range(samples), key=lambda i: sum(abs(row["cycles"] - m) / max(1, m) for row, m in zip(vectors[i], medians))
  )
  for group, m in zip(zip(*vectors), medians):
    values = [r["cycles"] for r in group]
    group[index]["sampled_cycles"] = dict(min=min(values), median=m, max=max(values))
  runs[index]["samples"] = samples
  return runs[index]
