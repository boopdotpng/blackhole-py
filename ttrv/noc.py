"""Per-kind NoC command buffers and p150 logical DRAM coordinates (fw/noc.c)."""

import fw
from . import hw
from .parse import Num, Name, Index, Call
from .expand import TYPES
from .ops import bind, required, keyword, number

BUFFERS = {"mcast": 0, "read": 1, "write": 2, "posted": 2, "inc": 3}


def init_buffers(g, kinds):
  if not kinds:
    return
  if g.role not in hw.NOC:
    g.fail("op.role", "NoC requires a data-movement RISC")
  niu = hw.NOC[g.role]
  for kind in sorted(kinds):
    base = niu + (BUFFERS[kind] << 11)
    write = kind in ("write", "mcast")
    with g.temps():
      g.mem("sw", base + (8 if write else 20), g.mem("lw", niu + 0x148))
      for off in ((4 if write else 16), 36, 40, 44):
        g.mem("sw", base + off, 0)
  g.rv("fence")


def noc(g, s):
  niu = hw.NOC[g.role]

  def poll(off, limit=0):
    with g.temps():
      loop = object()
      g.mark(loop)
      r = g.mem("lw", niu + off)
      if limit:
        g.branch("bgeu", r, g.li(limit), loop)
      else:
        g.branch("bne", r, 0, loop)

  def handle(e):
    k = keyword(e)
    if k not in g.env or not g.env[k][1].startswith("tid:"):
      g.fail("noc.handle", k)
    _, kind, tid = g.env[k][1].split(":")
    return kind, int(tid)

  def wait(kind, tid, sent):
    if not sent or kind in ("posted", "mcast"):
      g.event("set", f"transaction {tid}")
    poll((BUFFERS[kind] << 11) + 64)
    if kind in ("write", "posted", "mcast"):
      poll(0x280 + 4 * tid)
    if kind not in ("posted", "mcast") and not sent:
      poll(0x240 + 4 * tid)
    g.rv("fence")

  if s.name == "wait":
    sent = bool(s.args and s.args[-1].value == Name("sent", s.args[-1].value.loc))
    args = s.args[:-1] if sent else s.args
    if not args:
      g.fail("noc.wait", "expected handles")
    for a in args:
      kind, tid = handle(a.value)
      if sent and kind in ("read", "inc"):
        g.fail("noc.wait", "read has no sent completion")
      wait(kind, tid, sent)
    return []
  if s.name == "status":
    d = bind(s, "handle counter")
    _, tid = handle(required(d, "handle", s))
    counter = keyword(required(d, "counter", s))
    if counter not in ("outstanding", "outgoing"):
      g.fail("noc.counter", counter)
    return [(g.mem("lw", niu + (0x240 if counter == "outstanding" else 0x280) + 4 * tid), "u32")]
  if s.name not in ("read", "write", "inc", "mcast"):
    g.fail("noc.op", s.name)
  atomic = s.name == "inc"
  multicast = s.name == "mcast"
  write = s.name in ("write", "mcast")
  d = bind(
    s,
    "dst" if atomic else "dst src",
    "by ret tid" if atomic else "n tid port",
    "wait include_sender" if multicast else "wait posted" if write else "wait",
  )
  kind = "posted" if "posted" in d else s.name
  cmd = niu + (BUFFERS[kind] << 11)
  if "tid" in d:
    previous, tid = handle(d["tid"])
    if kind != previous:
      g.fail("noc.kind", "incompatible transaction ID")
  else:
    g.tid += 1
    tid = g.tid
    if tid >= 16:
      g.fail("noc.tids", "no free transaction IDs")
  fact = f"transaction {tid}"
  g.initial.add(fact)
  g.completions.add(fact)
  g.event("clear", fact)
  local = g.alloc()
  offset = g.alloc()
  left = g.alloc()
  remote = required(d, "dst" if write or atomic else "src", s)
  local_expr = required(d, "ret" if atomic else "src" if write else "dst", s)
  with g.temps():
    r, t = g.expr(local_expr)
    if not t.endswith("*"):
      g.fail("noc.local", "L1 pointer required")
    g.mov(local, r)
    if atomic:
      g.check_pointer(local_expr, 16, 16)
      g.li(4, left)
      if t != "u32*":
        g.fail("noc.atomic", "expected a u32 response slot")
    else:
      count = required(d, "n", s)
      size = TYPES[t[:-1]][0]
      if isinstance(count, Num) and (
        count.value <= 0 or not isinstance(remote, Index) and size and count.value * size > 16384
      ):
        g.fail("noc.length", "invalid transfer length")
      if isinstance(count, Num) and size:
        g.check_pointer(local_expr, length=count.value * size)
      g.mov(left, g.scale(g.condition(count), t[:-1]))

  def worker(x, y):
    xx = g.condition(x)
    yy = g.condition(y)
    skip = g.imm("sltiu", xx, 7)
    xx = g.calc("sub", g.imm("addi", xx, 3), g.imm("slli", skip, 1))
    return g.calc("or", xx, g.imm("slli", g.imm("addi", yy, 2), 6))

  if atomic and not (isinstance(remote, Call) and remote.fn == "remote"):
    g.fail("noc.atomic", "expected remote u32 pointer")
  if multicast and not (isinstance(remote, Call) and remote.fn == "rect"):
    g.fail("noc.mcast", "expected rectangle")
  host = None
  if isinstance(remote, Index) and isinstance(remote.base, Name) and len(remote.idx) == 1:
    host = g.m["params"].get(remote.base.id)
    if not host or host["kind"] != "host":
      host = None
  if isinstance(remote, Index) and isinstance(remote.base, Name) and len(remote.idx) == 1 and host is None:
    param = g.m["params"].get(remote.base.id)
    if param and param["kind"] == "host":
      g.fail("noc.endpoint", "internal: host endpoint")
    if not param or param["kind"] != "dram" or TYPES[param["type"]][0] != TYPES[t[:-1]][0]:
      g.fail("noc.endpoint", "incompatible DRAM endpoint")
    known = g.check_pointer(local_expr)
    if (
      not write
      and known is not None
      and isinstance(remote.idx[0], Num)
      and (known - remote.idx[0].value * TYPES[t[:-1]][0]) % 64
    ):
      g.fail("noc.align", "DRAM and L1 read offsets must match modulo 64")
    page = param["page"]
    base = g.mem("lw", fw.L1_PARAM_BASE + 4 * param["slot"])
    # Divide the element index before converting to bytes: a u32 index can address
    # more than 4 GiB. Carry page and intra-page cursors separately across requests.
    element_size = TYPES[param["type"]][0]
    if element_size is None:
      g.fail("type.size", "BFP elements cannot be indexed")
    page_index = g.alloc()
    with g.temps():
      index = g.condition(remote.idx[0])
      elements = g.li(page // element_size)
      g.rv("divu", page_index, index, elements)
      g.mov(offset, g.scale(g.calc("remu", index, elements), param["type"]))
    ports = ((14, 13, 12), (15, 16, 17), (18, 19, 20), (21, 22, 23), (14, 13, 12), (17, 16, 15), (20, 19, 18), (23, 22, 21))
    def table(port):  # packed y offsets from row 12, one nibble per bank
      return sum((ys[int(g.role == "ncrisc") if port is None else (port + bank) % 3] - 12) << (4 * bank)
                 for bank, ys in enumerate(ports))
    port_reg = None
    if "port" in d and not isinstance(d["port"], Num):
      # A runtime port (spec §7): evaluated once per request statement, selected per page below.
      port_reg = g.alloc()
      with g.temps():
        g.mov(port_reg, g.condition(d["port"]))
      y_tables = [table(p) for p in range(3)]
    else:
      y_table = table(number(d["port"], 0, 2) if "port" in d else None)
    dram = True
  else:
    if "port" in d:
      g.fail("noc.port", "port requires DRAM")
    dram = False
    middle = 0
    if isinstance(remote, Call) and remote.fn == "remote" and len(remote.args) == 3:
      x, y, p = remote.args
      with g.temps():
        ptr, typ = g.expr(p)
        if not typ.endswith("*") or atomic and typ != "u32*":
          g.fail("noc.endpoint", "invalid remote pointer")
        g.mov(offset, ptr)
      coord = worker(x, y)
    elif multicast:
      if len(remote.args) != 5:
        g.fail("noc.mcast", "expected rect(x0, y0, x1, y1, pointer)")
      x0, y0, x1, y1, p = remote.args
      with g.temps():
        ptr, typ = g.expr(p)
        if not typ.endswith("*"):
          g.fail("noc.endpoint", "expected remote pointer")
        g.mov(offset, ptr)
      coord = g.alloc()
      with g.temps():
        g.mov(coord, worker(x0, y0))
      with g.temps():
        end = worker(x1, y1)
        high, low = (coord, end) if g.role == "brisc" else (end, coord)
        g.rv("or", coord, low, g.imm("slli", high, 12))
    elif host is not None:
      if TYPES[host["type"]][0] != TYPES[t[:-1]][0]:
        g.fail("noc.endpoint", "incompatible host endpoint")
      a = fw.L1_PARAM_BASE + 4 * host["slot"]
      middle = g.alloc()
      with g.temps():
        byte = g.scale(g.condition(remote.idx[0]), host["type"])
        g.rv("add", offset, g.mem("lw", a), byte)
        carry = g.calc("sltu", offset, byte)
        g.rv("add", middle, g.mem("lw", a + 4), carry)
      coord = g.li((1 << 24) | (24 << 6) | 19)
    else:
      g.fail("noc.endpoint", "expected DRAM, host or remote endpoint")
  loop, end = object(), object()
  g.mark(loop)
  g.branch("beq", left, 0, end)
  length = g.alloc()
  with g.temps():
    poll((BUFFERS[kind] << 11) + 64)
    if kind not in ("posted", "mcast"):
      poll(0x240 + tid * 4, 128)
    if write:
      poll(0x280 + tid * 4, 128)
    if dram:
      size = g.li(page)
      idx = g.alloc()
      within = offset
      # Low bits of the aligned binding carry the first bank.
      tmp = g.imm("andi", base, 7)
      g.rv("add", idx, page_index, tmp)
      g.rv("andi", tmp, base, imm=-8)
      address = g.calc("add", tmp, g.calc("mul", g.imm("srli", idx, 3), size))
      address = g.calc("add", address, within)
      bank = g.imm("andi", idx, 7)
      # Packed y offsets from row 12, indexed by the bank's nibble.
      with g.temps():
        if port_reg is None:
          y = g.li(y_table)
        else:
          y, picked = g.li(y_tables[0]), object()
          g.branch("beq", port_reg, 0, picked)
          g.li(y_tables[1], y)
          g.branch("beq", port_reg, g.li(1), picked)
          g.li(y_tables[2], y)
          g.mark(picked)
        x = g.imm("slli", bank, 2)
        g.rv("srl", y, y, x)
        g.rv("andi", y, y, imm=15)
        g.rv("addi", y, y, imm=12)
        g.rv("slli", y, y, imm=6)
        g.rv("srli", x, bank, imm=2)
        g.rv("addi", x, x, imm=17)
        g.rv("or", x, x, y)
        g.mem("sw", cmd + (20 if write else 8), x)
      middle = 0
      g.rv("sub", length, size, within)
      ready = object()
      g.branch("bltu", length, left, ready)
      g.mov(length, left)
      g.mark(ready)
    else:
      address = offset
      g.mov(length, left)
      g.mem("sw", cmd + (20 if write else 8), coord)
    for off, r in (
      (0, local if write else address),
      (12, address if write else local),
      (16 if write else 4, middle),
      (32, g.li(0x107C) if atomic else length),
    ):
      g.mem("sw", cmd + off, r)
    if atomic:
      g.mem("sw", cmd + 40, g.condition(d.get("by", Num(1))))
    ctrl = (0x8080 | 32 | (int("include_sender" in d) << 17)) if multicast else 0x2080
    ctrl |= 2 if write else 1 if atomic else 0
    if kind not in ("posted", "mcast"):
      ctrl |= 16
    g.mem("sw", cmd + 24, g.li(tid << 10))
    g.mem("sw", cmd + 28, g.li(ctrl))
    g.rv("fence")
    g.mem("sw", cmd + 64, g.li(1))
    g.rv("fence")
  if dram:
    g.rv("addi", page_index, page_index, imm=1)
    g.mov(offset, 0)
    g.rv("add", local, local, length)
    g.rv("sub", left, left, length)
    g.jump(loop)
  g.mark(end)
  if "wait" in d:
    wait(kind, tid, False)
  return [(0, f"tid:{kind}:{tid}")]
