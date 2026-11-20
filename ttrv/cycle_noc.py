"""Event-driven Blackhole NoC. Times are AICLK cycles (sims/noc_findings.md)."""

from collections import defaultdict, deque
from functools import lru_cache
from math import ceil
from random import Random
from . import hw

# Calibrated constants (sims/noc_findings.md). Kept in one place so probes can refit them.
P = dict(
  bank_rate=47.4,  # DRAM bank data rate, bytes per cycle
  credits=8,  # concurrent reads one endpoint accepts per NoC
  credit_base=116,  # cycles a read holds its endpoint credit, plus size / credit_rate
  credit_rate=26,
  buffer=512,  # bytes a router input holds; a longer packet keeps upstream links until its tail fits
  random_rr=True,
  read_merge=False,  # order queued reads at a bank by nested round robin along their request routes  # a router output whose last winner is idle restarts round robin at a random input
)

# tt-umd blackhole_140_arch.yaml, in translated endpoint order (routes.py).
DRAM_ROWS = (0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6)


def endpoint(word):
  x, y = word & 63, (word >> 6) & 63
  if word == hw.PCIE_COORD:
    return (2, 0), ("host", 0)
  if x in (17, 18) and 12 <= y < 24:
    return ((0, 9)[x - 17], DRAM_ROWS[y - 12]), ("dram", (x - 17) * 4 + (y - 12) // 3)
  if x in hw.WORKER_COLUMNS and 2 <= y < 12:
    return (x, y), (x, y)
  raise ValueError(f"unmodelled NoC endpoint {word:#x}")


@lru_cache(None)
def route(noc, src, dst):
  pos = list(src)
  links = []
  for axis in (1, 0) if noc else (0, 1):
    while pos[axis] != dst[axis]:
      links.append((noc, *pos, axis))
      pos[axis] = (pos[axis] + (-1 if noc else 1)) % (17, 12)[axis]
  return tuple(links)


class Port:
  """Round robin among input ports with packets waiting for this output."""

  def __init__(self, sim, rng=None):
    self.sim = sim
    self.rng = rng
    self.inputs = {}
    self.order = deque()
    self.busy = False
    self.previous = None

  def enqueue(self, sender, duration, start):
    def grant(release):
      start()
      self.sim.after(duration, release)

    self.request(sender, grant)

  def request(self, sender, grant):
    if sender not in self.inputs:
      self.inputs[sender] = deque()
      self.order.append(sender)
    self.inputs[sender].append(grant)
    if not self.busy:
      self.busy = True
      self.sim.after(0, self.serve)

  def serve(self):
    self.busy = bool(self.order)
    if not self.busy:
      return
    if len(self.order) > 1 and self.previous not in self.order and self.rng and P["random_rr"]:
      self.order.rotate(self.rng.randrange(len(self.order)))
    if len(self.order) > 1 and self.order[0] == self.previous:
      self.order.rotate(-1)
    sender = self.order.popleft()
    self.previous = sender
    grant = self.inputs[sender].popleft()
    if self.inputs[sender]:
      self.order.append(sender)
    else:
      del self.inputs[sender]
    grant(self.serve)


class Merge:
  """Arbitrate queued DRAM packets at successive input ports back from the endpoint."""

  def __init__(self):
    self.branches = {}
    self.turns = deque()
    self.packets = deque()

  def put(self, path, packet):
    if not path:
      self.packets.append(packet)
      return
    key = path[0]
    if key not in self.branches:
      self.branches[key] = Merge()
      self.turns.append(key)
    self.branches[key].put(path[1:], packet)

  def get(self):
    if self.packets:
      return self.packets.popleft()
    key = self.turns.popleft()
    branch = self.branches[key]
    packet = branch.get()
    if branch.turns or branch.packets:
      self.turns.append(key)
    else:
      del self.branches[key]
    return packet


class Bank:
  def __init__(self, sim):
    self.sim = sim
    self.queue = Merge()
    self.busy = False

  def enqueue(self, path, duration, start):
    self.queue.put(path, (duration, start))
    if not self.busy:
      self.serve()

  def serve(self):
    self.busy = bool(self.queue.turns)
    if self.busy:
      duration, start = self.queue.get()
      start()
      self.sim.after(duration, self.serve)


class Network:
  def __init__(self, sim):
    self.sim = sim
    self.rng = Random(0)
    self.links = defaultdict(lambda: Port(sim, self.rng))
    self.banks = defaultdict(lambda: Bank(sim))
    self.injectors = defaultdict(lambda: Port(sim))
    self.read_credits = defaultdict(lambda: [0] * P["credits"])

  def packet(self, noc, src, dst, size, delivered, injected=None, *, response=False):
    links = route(noc, src, dst)
    duration = max(1, ceil(size / 63))
    # A long packet keeps a router output until its tail can leave. Queuing
    # every entire packet at the next router erases the nested round-robin shares.
    # Break channel dependencies at turns and at the torus dateline.
    # Keep at most a few flits at each intermediate input. Once the head
    # advances far enough the buffered tail no longer occupies the sender.
    held = deque()
    release_injector = None

    def sent():
      release_injector()
      if injected:
        injected()

    def credit(i, drain=False):
      while held:
        j, started, release = held[0]
        if not drain and P["buffer"] * (i - j) < size:
          break
        held.popleft()
        self.sim.after(max(0, started + duration - self.sim.time), release)

    def hop(i, dateline=False):
      if i == len(links):
        # Endpoint ejection arbitrates among local, X and Y input ports too.
        def accepted():
          credit(i, True)
          if not links:
            self.sim.after(duration, sent)
          self.sim.after(duration, delivered)

        self.links[noc, dst, "eject"].enqueue((links[-1] if links else src, response, dateline), duration, accepted)
        return
      link = links[i]
      sender = links[i - 1] if i else src
      axis = link[-1]
      turning = i > 0 and links[i - 1][-1] != axis
      crossing = link[1 + axis] == ((16, 11)[axis] if noc else 0)
      if i and (turning or crossing):
        credit(i, True)

      def grant(release_link):
        # The first hop must accept the tail before the NIU can mark the
        # payload sent or inject the next packet from the same port.
        def release():
          release_link()
          if i == 0:
            sent()

        credit(i)
        if size <= P["buffer"]:
          self.sim.after(duration, release)
        else:
          held.append((i, self.sim.time, release))
        self.sim.after(9, lambda: hop(i + 1, crossing or (dateline and not turning)))

      self.links[link].request((sender, response, dateline), grant)

    def inject(release):
      nonlocal release_injector
      release_injector = release
      hop(0)

    self.injectors[noc, src].request(src, inject)

  def multicast(self, core, noc, rect, ctrl, addr, payload, injected):
    endpoints = (rect >> 12, rect & 0xFFF)
    (x0, y0), _ = endpoint(endpoints[noc])
    (x1, y1), _ = endpoint(endpoints[1 - noc])
    if not (x0 <= x1 and y0 <= y1):
      raise ValueError("invalid multicast rectangle")
    targets = {(x, y) for x in hw.WORKER_COLUMNS if x0 <= x <= x1 for y in range(y0, y1 + 1)}
    if not ctrl & hw.CTRL_BRCST_SRC_INCLUDE:
      targets.discard(core.xy)
    tree = {}
    for dst in sorted(targets):
      node = tree
      for link in route(noc, core.xy, dst):
        node = node.setdefault(link, {})
      node[None] = dst
    duration = max(1, ceil(len(payload) / 63))

    def visit(node, sender):
      for link, child in node.items():
        if link is None:
          self.sim.after(duration, lambda dst=child: self.sim.memory(dst).write(addr, payload))
        else:

          def onward(child=child, link=link):
            self.sim.after(9, lambda: visit(child, link))

          self.links[link].enqueue(sender, duration, onward)

    def inject():
      self.sim.after(duration, injected)
      visit(tree, core.xy)

    self.injectors[noc, core.xy].enqueue(core.xy, duration, inject)

  def send(self, core, noc, regs, base):
    cmd = hw.Cmd

    def get(reg):
      return regs.get(base + reg, 0)

    ctrl = get(cmd.CTRL)
    multicast = bool(ctrl & hw.CTRL_BRCST_PACKET)
    write, atomic = bool(ctrl & hw.CTRL_WRITE), bool(ctrl & hw.CTRL_ATOMIC)
    size = 4 if atomic else get(cmd.AT_LEN_BE)
    if not 0 < size <= hw.NOC_MAX_BURST:
      raise ValueError(f"invalid packet length {size}")
    coord = get(cmd.RET_COORD if write else cmd.TARG_COORD)
    local_addr = get(cmd.TARG_LO if write else cmd.RET_LO)
    remote_addr = get(cmd.RET_LO if write else cmd.TARG_LO)
    remote_addr |= get(cmd.RET_MID if write else cmd.TARG_MID) << 32
    tid = get(cmd.PACKET_TAG) >> 10 & 15
    niu = hw.NOC0_REGS + noc * hw.NOC_INSTANCE_OFFSET
    out, sent = niu + hw.outstanding(tid), niu + hw.outgoing(tid)
    busy = base + cmd.CMD_CTRL
    regs[busy] = 1
    # cmd_accept.py samples the status with one lw after 0..24 intervening
    # instructions. The load sees idle at distance five, or immediately after a fence.
    self.sim.after(5, lambda: regs.__setitem__(busy, 0))
    marked = bool(ctrl & hw.CTRL_RESP_MARKED)
    if marked:
      regs[out] = regs.get(out, 0) + 1
    if write:
      regs[sent] = regs.get(sent, 0) + 1
    payload = core.tile.read(local_addr, size) if write else None

    def sent_one():
      regs[sent] -= 1

    if multicast:
      if not write or marked or get(cmd.BRCST_EXCLUDE):
        raise ValueError("unmodelled multicast command")
      core.noc_stats["multicast_requests"] += 1
      core.noc_stats["multicast_bytes"] += size
      self.sim.after(31, lambda: self.multicast(core, noc, coord, ctrl, remote_addr, payload, sent_one))
      return
    remote, key = endpoint(coord)
    dram = key[0] == "dram"
    target = self.sim.memory(key)
    operand = get(cmd.AT_DATA)
    issue = self.sim.time
    injected_at = serviced_at = issue
    kind = "atomic" if atomic else "write" if write else "read"
    core.noc_stats[kind + "_last_issue"] = issue
    core.noc_stats[kind + "_requests"] += 1
    core.noc_stats[kind + "_bytes"] += size
    core.noc_stats[kind + "_data_hops"] += len(route(noc, core.xy, remote) if write else route(noc, remote, core.xy))

    def ack():
      core.noc_stats[kind + "_last_completion"] = self.sim.time
      core.noc_stats[kind + "_return_network_cycles_sum"] += self.sim.time - serviced_at
      core.noc_stats[kind + "_completion_cycles_sum"] += self.sim.time - issue
      if marked:
        regs[out] -= 1

    def service():
      nonlocal serviced_at
      serviced_at = self.sim.time
      if write:
        target.write(remote_addr, payload)
        if marked:
          self.packet(noc, remote, core.xy, 1, ack, response=True)
        else:
          ack()  # posted writes complete here for attribution, without a return packet
      else:
        data = target.read(remote_addr, size)
        if atomic:
          target.write(remote_addr, ((int.from_bytes(data, "little") + operand) & 0xFFFFFFFF).to_bytes(4, "little"))

        def receive():
          core.tile.write(local_addr, data)
          ack()

        self.packet(noc, remote, core.xy, size, receive, response=True)

    def arrived():
      core.noc_stats[kind + "_request_network_cycles_sum"] += self.sim.time - injected_at
      # Measured 64-byte read/ack RTTs are 429/319 for DRAM, 49+9*hops for L1.
      delay = 16 + (12 if atomic else 0) if marked else 0
      if key[0] == "host":
        # Gen5 x16, card 0: host-{read,write} in sims/probes/traffic.py.
        rtt = (359 if write else 829) + round(size * (0.021 if write else 0.028))
        delay = max(0, rtt - 29 * 9 - 31 - ceil(size / 63) - 12)
      if dram:
        # Interpolate the unqueued RTT sweep, removing route, wire and probe polling costs.
        sizes = (64, 256, 1024, 2048, 4096, 16384)
        latencies = (319, 329, 339, 359, 389, 609) if write else (429, 439, 459, 479, 529, 789)
        rtt = latencies[0]
        for a, b, ta, tb in zip(sizes, sizes[1:], latencies, latencies[1:]):
          if size > a:
            rtt = round(ta + (tb - ta) * (min(size, b) - a) / (b - a))
        delay = max(0, rtt - 31 - 29 * 9 - 1 - ceil(size / 63) - 12)
      if dram and not write:
        phase = (self.sim.time - self.sim.refresh_phase - (0, 942, 2267, 659, 485, 291, 694, 87)[key[1]]) % 2497.5
        if phase < 150 and not self.banks[key].busy:
          delay += ceil(150 - phase)
      core.noc_stats[kind + "_endpoint_service_cycles_sum"] += delay
      if dram:
        # Requests the bank cannot take yet wait in the routers, and each router lets its waiting inputs through in
        # turn. Ordering the bank queue by the request's route reproduces that nested round robin.
        merged = write or P["read_merge"]
        path = ((remote, noc), *(reversed(route(noc, core.xy, remote))), core.xy) if merged else ((remote, noc),)
        transfer = ceil(size / P["bank_rate"])

        def enqueue():
          queued = self.sim.time

          def selected():
            core.noc_stats[kind + "_bank_queue_cycles_sum"] += self.sim.time - queued
            self.sim.after(delay, service)

          # Short acknowledged writes pipeline. On card 0, 96 NCRISCs each
          # writing 64 bytes have entry-to-return durations within five cycles.
          self.banks[key].enqueue(path, transfer, selected)

        if write:
          enqueue()
        else:
          # The fixed-address burst probe resolves eight concurrent reads per endpoint.
          # Successive groups take 118 cycles at 64 B and 136 cycles at 512 B.
          credits = self.read_credits[noc, remote]
          slot = credits.index(min(credits))
          start = max(self.sim.time, credits[slot])
          credits[slot] = start + P["credit_base"] + ceil(size / P["credit_rate"])
          core.noc_stats[kind + "_credit_wait_cycles_sum"] += start - self.sim.time
          self.sim.after(start - self.sim.time, enqueue)
      else:
        self.sim.after(delay, service)

    def inject():
      nonlocal injected_at
      injected_at = self.sim.time
      core.noc_stats[kind + "_issue_cycles_sum"] += injected_at - issue
      self.packet(noc, core.xy, remote, size if write else 1, arrived, sent_one if write else None)

    self.sim.after(31 + (self.rng.randrange(-4, 5) if dram else 0), inject)
