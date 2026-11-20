"""Timing of the three asynchronous Tensix instruction streams (sims/probes/{FPU,SFPU,PACK,UNPACK}.md)."""

from collections import Counter, defaultdict, deque
from functools import lru_cache
from math import ceil

from sims.hw import SFPU_OPS, sfpu_cost
from . import cfg, hw, isa

NOP = isa.NOP()
FPU = set("MVMUL ELWMUL ELWADD ELWSUB GMPOOL GAPOOL MOVA2D MOVB2D MOVD2A MOVD2B MOVB2A ZEROACC ZEROSRC".split())


@lru_cache(None)
def instruction(word):
  decoded = isa.tensix_decode(word)
  if not decoded:
    raise ValueError(f"unknown backend instruction {word:#010x}")
  return decoded


def expand_mop(word, cfg, high):
  outer, inner, start, end0, end1, loop0, loop1, last, last_inner = cfg
  if not word & (1 << 23):
    mask = high << 16 | (word & 65535)
    for i in range(1 + ((word >> 16) & 127)):
      if mask >> i & 1:
        yield cfg[7]
        if inner & 1:
          yield cfg[8]
      else:
        yield cfg[3]
        if inner & 2:
          yield from cfg[4:7]
        if inner & 1:
          yield cfg[2]
    return
  outer = ((word >> 10) & 1023) or (outer & 1023)
  inner = (word & 1023) or (inner & 1023)
  loops = (loop0,) if loop1 == NOP else (loop0, loop1)
  for j in range(outer):
    if start != NOP:
      yield start
    for i in range(inner * len(loops)):
      if i + 1 == inner * len(loops):
        yield last if j + 1 == outer else last_inner
      else:
        yield loops[i % len(loops)]
    if end0 != NOP:
      yield end0
      if end1 != NOP:
        yield end1


class Tile:
  def __init__(self):
    self.cfg = defaultdict(int)
    self.sem = [0] * 8
    self.maximum = [1] * 8
    self.valid = [0, 0]
    self.publishing = [0, 0]
    self.ready = Counter()
    self.waiters = []
    self.argmax = None
    self.on_change = None

  def changed(self):
    waiters, self.waiters = self.waiters, []
    for wake in waiters:
      wake()
    if self.on_change:
      self.on_change()


class Thread:
  def __init__(self, sim, tile, role, xy):
    self.xy = xy
    self.sim, self.tile, self.role = sim, tile, role
    self.fifo = deque()
    self.stream = None
    self.current = None
    self.active = False
    self.mop = [0] * 9
    self.mask = 0
    self.replay = {}
    self.record = None
    self.gpr = defaultdict(int)
    self.cfg = defaultdict(int)
    self.count = Counter()
    self.sfpu = None
    self.last_sfpu = -10
    self.xend = [0, 0]
    self.dst = 0
    self.dst_ready = Counter()
    self.done = 0
    self.conditions = []
    self.unit_cycles = Counter()
    self.busy_until = Counter()
    self.on_space = None
    self.on_drain = None
    self.dst_cr = 0
    self.l0_bits = 0
    self.macros = {}

  def busy(self, unit, until):
    # Performance counters count the union of active pipeline intervals.
    self.unit_cycles[unit] += max(0, until - max(self.sim.time, self.busy_until[unit]))
    self.busy_until[unit] = max(until, self.busy_until[unit])

  def push(self, word, stamp=None):
    """Queue an instruction the RISC issued at cycle stamp (default now). The thread never starts it earlier."""
    stamp = self.sim.time if stamp is None else stamp
    self.fifo.append((stamp, word))
    if not self.active:
      self.active = True
      self.sim.at(max(stamp, self.sim.time), self.step)

  def expand(self, word):
    op, f = instruction(word)
    if op == "MOP_CFG":
      self.mask = word & 0xFFFF
      return
    words = expand_mop(word, self.mop, self.mask) if op == "MOP" else (word,)
    for raw in words:
      if self.record:
        slot, left, execute = self.record
        self.replay[slot] = raw
        self.record = (slot + 1, left - 1, execute) if left > 1 else None
        if execute:
          yield raw
      elif raw >> 24 == 4:
        _, r = instruction(raw)
        slot, length = r["start_idx"], r["len"]
        if r["load_mode"]:
          self.record = slot, length, r["execute_while_loading"]
        else:
          for i in range(slot, slot + length):
            if i not in self.replay:
              raise ValueError(f"uninitialized REPLAY slot {i}")
            yield self.replay[i]
      else:
        yield raw

  def step(self):
    if self.current is None:
      if self.stream is not None:
        self.current = next(self.stream, None)
      if self.current is None:
        if not self.fifo:
          self.active = False
          self.done = max(self.done, self.sim.time)
          if self.on_drain:
            wake, self.on_drain = self.on_drain, None
            wake()
          return
        if self.fifo[0][0] > self.sim.time:
          # The RISC ran ahead of the global clock; this instruction is not in the FIFO yet.
          self.sim.at(self.fifo[0][0], self.step)
          return
        self.stream = self.expand(self.fifo.popleft()[1])
        if self.on_space and len(self.fifo) <= 28:
          wake, self.on_space = self.on_space, None
          wake()
        self.current = next(self.stream, None)
    cycles = 1
    if self.current is not None:
      group, cycles, accepted = self.issue(self.current)
      if not accepted and group in ("semaphore_wait", "unpacker_wait", "src_valid_wait"):
        begin = self.sim.time

        def resume():
          self.count[group] += self.sim.time - begin
          self.sim.after(0, self.step)

        self.tile.waiters.append(resume)
        return
      self.count[group] += cycles
      if accepted:
        self.current = None
    self.sim.after(cycles, self.step)

  def condition(self, entry):
    op, f = entry
    if op == "SEMWAIT":
      for i, v in enumerate(self.tile.sem):
        if f["sem_sel"] & (1 << i):
          if (f["wait_sem_cond"] & 1 and v == 0) or (f["wait_sem_cond"] & 2 and v == self.tile.maximum[i]):
            return "semaphore_wait", 1
    else:
      mask = f["wait_res"]
      for i in (0, 1):
        if mask & (isa.Wait.SRCA_CLR << i) and self.tile.valid[i] >= 2:
          return "unpacker_wait", 1
        if mask & (isa.Wait.SRCA_VLD << i) and not self.tile.valid[i]:
          return "src_valid_wait", 1
      for bit, unit in (
        (isa.Wait.UNPACK0, "unpack0"),
        (isa.Wait.UNPACK1, "unpack1"),
        (isa.Wait.PACK0, "pack"),
        (isa.Wait.MATH, "fpu"),
        (isa.Wait.SFPU, "sfpu"),
      ):
        remaining = self.tile.ready[unit + "_done"] - self.sim.time
        if mask & bit and remaining > 0:
          return unit + "_drain", remaining

  def issue(self, word):
    t, now = self.tile, self.sim.time
    op, f = instruction(word)
    unit = (
      "sfpu"
      if word >> 24 in SFPU_OPS
      else "fpu"
      if op in FPU or op in ("SETRWC", "INCRWC")
      else "unpack"
      if op.startswith("UNPACR")
      else "pack"
      if op == "PACR"
      else "sync"
      if op.startswith("SEM")
      else "cfg"
    )
    bit = {"sfpu": 256, "fpu": 64, "unpack": 8, "pack": 4, "sync": 2, "cfg": 128}[unit]
    pending = []
    for entry in self.conditions:
      waiting = self.condition(entry)
      if waiting and entry[1]["stall_res"] & bit:
        return *waiting, False
      if waiting:
        pending.append(entry)
    self.conditions = pending
    group = unit
    if op in ("SEMWAIT", "STALLWAIT"):
      self.conditions.append((op, f))
      group = "sync"
    elif op.startswith("SEM"):
      for i in range(8):
        if not f["sem_sel"] & (1 << i):
          continue
        if op == "SEMINIT":
          t.sem[i], t.maximum[i] = f["init_value"], f["max_value"]
        elif op == "SEMPOST":
          t.sem[i] = min(15, t.sem[i] + 1)
        elif op == "SEMGET":
          t.sem[i] = max(0, t.sem[i] - 1)
      t.changed()
    elif unit == "sfpu":
      if now - self.last_sfpu > 1:
        self.sfpu = None
      if op == "SFPLOADI" and f["lreg_ind"] == 0:
        imm, mode = f["imm16"], f["instr_mod0"]
        if mode == 8:
          self.l0_bits = (self.l0_bits & 65535) | (imm << 16)
        elif mode == 10:
          self.l0_bits = (self.l0_bits & 0xFFFF0000) | imm
        else:
          self.l0_bits = imm << 16 if mode == 0 else imm
      if op == "SFPCONFIG" and 4 <= f["config_dest"] < 8:
        self.macros[f["config_dest"] - 4] = f["imm16_math"] if f["instr_mod1"] & 1 else self.l0_bits
      stall, _, self.sfpu = sfpu_cost(self.sfpu, word, self.macros)
      self.unit_cycles["sfpu"] += 1
      self.last_sfpu = now + stall
      t.ready["sfpu_done"] = self.last_sfpu + 1
      self.done = max(self.done, self.last_sfpu + 1)
      self.count["sfpu_interlock"] += stall
      self.count["sfpu"] -= stall
      return "sfpu", 1 + stall, True
    elif op.startswith("RMWCIB"):
      shift = 8 * int(op[-1])
      mask = f["Mask"] << shift
      reg = f["CfgRegAddr"]
      t.cfg[reg] = (t.cfg[reg] & ~mask) | ((f["Data"] << shift) & mask)
    elif op == "SETC16":
      self.cfg[f["setc16_reg"]] = f["setc16_value"]
    elif op == "SETDMAREG":
      reg, shift = f["RegIndex16b"] // 2, 16 * (f["RegIndex16b"] % 2)
      self.gpr[reg] = (self.gpr[reg] & ~(65535 << shift)) | (((word >> 8) & 65535) << shift)
    elif op == "WRCFG":
      for i in range(4 if f["wr128b"] else 1):
        t.cfg[f["CfgReg"] + i] = self.gpr[f["GprAddress"] + i]
    elif op == "SETADCXX":
      for i in range(2):
        if f["CntSetMask"] & (1 << i):
          self.xend[i] = f["x_end2"]
    elif unit == "unpack":
      i = f.get("Unpack_block_selection", f.get("Unpacker_Select"))
      group = "unpack" + str(i)
      give = f.get("SetDatValid") or f.get("Set_Dvalid")
      if give and t.valid[i] + t.publishing[i] >= 2:
        return "unpacker_wait", 1, False
      if t.ready[group] > now:
        return group + "_busy_wait", t.ready[group] - now, False
      field = hw.UNPACKER[i].in_data_format
      fmt = (t.cfg[field.word] & field.mask) >> field.shift
      size = {0: 4, 1: 2, 5: 2, 8: 4}.get(fmt, 1)
      duration = max(2, ceil((1 + self.xend[i]) * size / 128)) if op == "UNPACR" else 1
      t.ready[group] = now + duration
      t.ready[group + "_done"] = now + duration + 26
      self.done = max(self.done, t.ready[group + "_done"])
      if op == "UNPACR":
        if t.argmax is not None:
          t.argmax.unpack()
        payload_cycles = ceil((1 + self.xend[i]) * size / 128)
        self.busy(group, now + 15 + payload_cycles)
      if give:
        t.publishing[i] += 1

        def publish():
          t.publishing[i] -= 1
          t.valid[i] += 1
          t.changed()

        self.sim.after(duration + 32, publish)
    elif unit == "pack":
      if t.ready["pack"] > now:
        return "packer_busy_wait", t.ready["pack"] - now, False
      if t.argmax is not None:
        t.argmax.pack()
      field = cfg.THCON_SEC0_REG1_Out_data_format
      duration = 1 if ((t.cfg[field.word] & field.mask) >> field.shift) == hw.DataFormat.LF8 else 2
      self.busy("pack", now + duration + 19)
      t.ready["pack"] = now + duration
      t.ready["pack_done"] = self.busy_until["pack"]
      self.done = max(self.done, now + 28)
    elif unit == "fpu":
      needed = (
        (0,)
        if op == "MOVA2D"
        else (1,)
        if op == "MOVB2D"
        else (0, 1)
        if op in ("MVMUL", "ELWADD", "ELWSUB", "ELWMUL", "GMPOOL", "GAPOOL")
        else ()
      )
      if any(not t.valid[i] for i in needed):
        return "src_valid_wait", 1, False
      block = ((self.dst + f.get("dst", 0)) % 1024) // 8
      accum = op in ("MVMUL", "GAPOOL", "GMPOOL") or f.get("dest_accum_en")
      ready = max(t.ready["fpu"], self.dst_ready[block] if accum else 0)
      if ready > now:
        return "fpu_interlock", ready - now, False
      if op in FPU:
        self.dst_ready[block] = now + 6
        if op != "ZEROACC":
          self.unit_cycles["fpu"] += 1
      t.ready["fpu"] = now + 1
      t.ready["fpu_done"] = now + 5
      self.done = max(self.done, t.ready["fpu_done"])
      for i in range(2):
        if f.get("clear_ab_vld", f.get("clear_dvalid", 0)) & (1 << i):
          t.valid[i] = max(0, t.valid[i] - 1)
          t.changed()
      if "addr_mode" in f:
        slot = hw.ADDR_MOD[f["addr_mode"] % len(hw.ADDR_MOD)]
        inc, clear = slot.incr[2], slot.clear[2]
        base = (
          0
          if self.cfg[clear.word] & clear.mask
          else self.dst_cr
          if self.cfg[slot.cr[2].word] & slot.cr[2].mask
          else self.dst
        )
        self.dst = base + ((self.cfg[inc.word] & inc.mask) >> inc.shift)
        if self.cfg[slot.c_to_cr.word] & slot.c_to_cr.mask:
          self.dst_cr = self.dst
      if op == "SETRWC" and f["BitMask"] & 4:
        self.dst = (self.dst if f["rwc_cr"] & 8 else self.dst_cr if f["rwc_cr"] & 4 else 0) + f["rwc_d"]
        if f["rwc_cr"] & 4:
          self.dst_cr = self.dst
      if op == "INCRWC":
        self.dst += f["rwc_d"]
    elif op not in ("SETADC", "SETADCZW", "SETADCXY", "INCADCXY", "NOP", "DMANOP"):
      raise ValueError(f"unmodelled Tensix instruction {op}")
    return group, 1, True
