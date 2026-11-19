"""NoC requests: per-kind command buffers, DRAM page interleaving and p150 endpoints (fw/noc.c)."""

import fw
from . import hw
from .hw import Cmd, CmdBuf
from .parse import Num, Name, Index, Call
from .expand import TYPES
from .ops import bind, required, keyword, number

BUFFERS = {"mcast": CmdBuf.MCAST, "read": CmdBuf.READ, "write": CmdBuf.WRITE, "posted": CmdBuf.WRITE, "inc": CmdBuf.ATOMIC}


def cmd_buf(niu, kind): return niu + BUFFERS[kind] * hw.CMD_BUF_STRIDE


def init_buffers(g, kinds):
  if not kinds:
    return
  if g.role not in hw.NIU:
    g.fail("op.role", "NoC requires a data-movement RISC")
  niu = hw.NIU[g.role]
  for kind in sorted(kinds):
    base = cmd_buf(niu, kind)
    write = kind in ("write", "mcast")
    # The local side of every request is this node: TARG for writes, RET for reads and atomics.
    g.mem("sw", base + (Cmd.TARG_COORD if write else Cmd.RET_COORD), g.mem("lw", niu + hw.NOC_ID_LOGICAL))
    for reg in (Cmd.TARG_MID if write else Cmd.RET_MID, Cmd.AT_LEN_BE_1, Cmd.AT_DATA, Cmd.BRCST_EXCLUDE):
      g.mem("sw", base + reg, 0)
  g.rv("fence")


def noc(g, s):
  niu = hw.NIU[g.role]

  def poll(off, limit=0):  # spin while the NIU register at off is nonzero (or >= limit)
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
    poll(cmd_buf(0, kind) + Cmd.CMD_CTRL)
    if kind in ("write", "posted", "mcast"):
      poll(hw.outgoing(tid))
    if kind not in ("posted", "mcast") and not sent:
      poll(hw.outstanding(tid))
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
    return [(g.mem("lw", niu + (hw.outstanding(tid) if counter == "outstanding" else hw.outgoing(tid))), "u32")]
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
  cmd = cmd_buf(niu, kind)
  if "tid" in d:
    previous, tid = handle(d["tid"])
    if kind != previous:
      g.fail("noc.kind", "incompatible transaction ID")
  else:
    g.tid += 1
    tid = g.tid
    if tid >= hw.NOC_TIDS:
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
      count.value <= 0 or not isinstance(remote, Index) and size and count.value * size > hw.NOC_MAX_BURST
    ):
      g.fail("noc.length", "invalid transfer length")
    if isinstance(count, Num) and size:
      g.check_pointer(local_expr, length=count.value * size)
    if size is None:
      # A block-floating DRAM index addresses a packed tile. Transfers contain whole tiles.
      if not (isinstance(remote, Index) or multicast) or not isinstance(count, Num) or count.value <= 0 or count.value % 1024:
        g.fail("noc.length", "BFP transfers require whole 1024-element tiles")
      nbytes = count.value // 1024 * TYPES[t[:-1]][1]
      if multicast and nbytes > hw.NOC_MAX_BURST:
        g.fail("noc.length", "packed multicast exceeds the NoC burst limit")
      g.check_pointer(local_expr, length=nbytes)
      g.li(nbytes, left)
    else:
      g.mov(left, g.scale(g.condition(count), t[:-1]))

  def worker(x, y):  # hw.worker_coord at runtime: column x + lo below the gap, x + hi after it; row y + WORKER_ROW0
    lo = hw.WORKER_COLUMNS[0]
    hi = hw.WORKER_COLUMNS[hw.WORKER_X_GAP] - hw.WORKER_X_GAP
    assert hi - lo == 2  # the shift below
    xx = g.condition(x)
    yy = g.condition(y)
    left = g.imm("sltiu", xx, hw.WORKER_X_GAP)
    xx = g.calc("sub", g.imm("addi", xx, hi), g.imm("slli", left, 1))
    return g.calc("or", xx, g.imm("slli", g.imm("addi", yy, hw.WORKER_ROW0), 6))

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
    if not param or param["kind"] != "dram" or TYPES[param["type"]] != TYPES[t[:-1]]:
      g.fail("noc.endpoint", "incompatible DRAM endpoint")
    known = g.check_pointer(local_expr)
    if (
      not write
      and known is not None and TYPES[t[:-1]][0] is not None
      and isinstance(remote.idx[0], Num)
      and (known - remote.idx[0].value * TYPES[t[:-1]][0]) % 64
    ):
      g.fail("noc.align", "DRAM and L1 read offsets must match modulo 64")
    page = param["page"]
    base = g.mem("lw", fw.L1_PARAM_BASE + 4 * param["slot"])
    # Divide the element index before converting to bytes: a u32 index can address
    # more than 4 GiB. Carry page and intra-page cursors separately across requests.
    element_size = TYPES[param["type"]][0]
    page_index = g.alloc()
    index = g.condition(remote.idx[0])

    def split(per_page):  # page_index, offset = divmod(index, per_page); offset in units, scaled by the caller
      if per_page & (per_page - 1) == 0:
        k = per_page.bit_length() - 1
        g.rv("srli", page_index, index, imm=k)
        mask = per_page - 1
        g.mov(offset, g.imm("andi", index, mask) if mask < 2048 else g.calc("and", index, g.li(mask)))
      else:
        n = g.li(per_page)
        g.rv("divu", page_index, index, n)
        g.mov(offset, g.calc("remu", index, n))
    if element_size is None:
      tile_bytes = TYPES[param["type"]][1]
      if page == tile_bytes:
        g.mov(page_index, index)
        g.mov(offset, 0)
      else:
        split(page // tile_bytes)
        g.rv("mul", offset, offset, g.li(tile_bytes))
    else:
      split(page // element_size)
      g.mov(offset, g.scale(offset, param["type"]))
    def table(port):  # packed y offsets from DRAM_Y0, one nibble per bank; port rotates with the bank
      return sum((ys[int(g.role == "ncrisc") if port is None else (port + bank) % 3] - hw.DRAM_Y0) << (4 * bank)
                 for bank, ys in enumerate(hw.DRAM_PORTS))
    port_reg = None
    if "port" in d and not isinstance(d["port"], Num):
      # A runtime port (spec §7): evaluated once per request statement, selected per page below.
      port_reg = g.alloc()
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
      ptr, typ = g.expr(p)
      if not typ.endswith("*") or atomic and typ != "u32*":
        g.fail("noc.endpoint", "invalid remote pointer")
      g.mov(offset, ptr)
      coord = worker(x, y)
    elif isinstance(remote, Call) and remote.fn == "noc_xy":
      # A physical NoC endpoint (e.g. Ethernet L1), addressed in bytes.
      x, y, addr = remote.args
      coord = g.li(number(x, 0, 63) | number(y, 0, 63) << 6)
      g.mov(offset, g.condition(addr))
    elif multicast:
      if len(remote.args) != 5:
        g.fail("noc.mcast", "expected rect(x0, y0, x1, y1, pointer)")
      x0, y0, x1, y1, p = remote.args
      ptr, typ = g.expr(p)
      if not typ.endswith("*"):
        g.fail("noc.endpoint", "expected remote pointer")
      if typ != t:
        g.fail("noc.endpoint", "multicast source and destination types must match")
      g.mov(offset, ptr)
      coord = g.alloc()
      g.mov(coord, worker(x0, y0))
      end = worker(x1, y1)
      high, low = (coord, end) if g.role == "brisc" else (end, coord)
      g.rv("or", coord, low, g.imm("slli", high, 12))
    elif host is not None:
      if TYPES[host["type"]][0] != TYPES[t[:-1]][0]:
        g.fail("noc.endpoint", "incompatible host endpoint")
      a = fw.L1_PARAM_BASE + 4 * host["slot"]
      middle = g.alloc()
      byte = g.scale(g.condition(remote.idx[0]), host["type"])
      g.rv("add", offset, g.mem("lw", a), byte)
      carry = g.calc("sltu", offset, byte)
      g.rv("add", middle, g.mem("lw", a + 4), carry)
      coord = g.li(hw.PCIE_COORD)
    else:
      g.fail("noc.endpoint", "expected DRAM, host or remote endpoint")
  loop, end = object(), object()
  g.mark(loop)
  g.branch("beq", left, 0, end)
  length = g.alloc()
  poll(cmd_buf(0, kind) + Cmd.CMD_CTRL)
  if kind not in ("posted", "mcast"):
    poll(hw.outstanding(tid), 128)
  if write:
    poll(hw.outgoing(tid), 128)
  if dram:
    size = g.li(page)
    within = offset
    address, bank = g.alloc(), g.alloc()
    # Pages interleave over the banks starting at the buffer's bank (its low 3 bits).
    idx = g.imm("andi", base, hw.DRAM_BANKS - 1)
    g.rv("add", idx, page_index, idx)
    g.rv("andi", bank, idx, imm=hw.DRAM_BANKS - 1)
    g.rv("srli", idx, idx, imm=3)
    g.rv("mul", idx, idx, size)
    g.rv("andi", address, base, imm=-8)
    g.rv("add", address, address, idx)
    g.rv("add", address, address, within)
    # Packed y offsets from row 12, indexed by the bank's nibble.
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
    g.rv("addi", y, y, imm=hw.DRAM_Y0)
    g.rv("slli", y, y, imm=6)
    g.rv("srli", x, bank, imm=2)
    g.rv("addi", x, x, imm=hw.DRAM_X0)
    g.rv("or", x, x, y)
    g.mem("sw", cmd + (Cmd.RET_COORD if write else Cmd.TARG_COORD), x)
    middle = 0
    g.rv("sub", length, size, within)
    ready = object()
    g.branch("bltu", length, left, ready)
    g.mov(length, left)
    g.mark(ready)
  else:
    address = offset
    g.mov(length, left)
    g.mem("sw", cmd + (Cmd.RET_COORD if write else Cmd.TARG_COORD), coord)
  for reg, r in (
    (Cmd.TARG_LO, local if write else address),
    (Cmd.RET_LO, address if write else local),
    (Cmd.RET_MID if write else Cmd.TARG_MID, middle),
    (Cmd.AT_LEN_BE, g.li(hw.at_instruction(hw.AT_INCR_GET)) if atomic else length),
  ):
    g.mem("sw", cmd + reg, r)
  if atomic:
    g.mem("sw", cmd + Cmd.AT_DATA, g.condition(d.get("by", Num(1))))
  if multicast:
    ctrl = hw.ctrl_static_vc(4) | hw.CTRL_BRCST_PACKET | (hw.CTRL_BRCST_SRC_INCLUDE if "include_sender" in d else 0)
  else:
    ctrl = hw.ctrl_static_vc(1)
  ctrl |= hw.CTRL_WRITE if write else hw.CTRL_ATOMIC if atomic else 0
  if kind not in ("posted", "mcast"):
    ctrl |= hw.CTRL_RESP_MARKED
  g.mem("sw", cmd + Cmd.PACKET_TAG, g.li(hw.packet_tag(tid)))
  g.mem("sw", cmd + Cmd.CTRL, g.li(ctrl))
  g.rv("fence")
  g.mem("sw", cmd + Cmd.CMD_CTRL, g.li(1))
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
