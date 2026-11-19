"""Virtual-register RV32IM code. Operands are (register, scalar or pointer type)."""

import struct
import fw
from . import hw, isa
from .parse import (
  Name,
  Num,
  Attr,
  Bin,
  Unary,
  Index,
  Call,
  Op,
  Assign,
  Block,
  If,
  For,
  Loop,
  While,
  Break,
  Continue,
  Return,
  Fence,
  Error,
)
from .expand import TYPES
from .emit import Emitter
from .regalloc import Instruction, allocate


def pow2(v):
  """log2 of a positive power-of-two integer constant, else None."""
  if isinstance(v, bool) or not isinstance(v, int) or v <= 0 or v & (v - 1):
    return None
  return v.bit_length() - 1


class Generator(Emitter):
  def __init__(self, p, m, role):
    super().__init__(role)
    self.p, self.m, self.base = p, m, hw.bases(role)
    self.functions, self.owners, self.addrmods, self.replays = {}, {}, {}, {}
    self.events, self.initial, self.completions, self.ends = {}, set(), set(), {}
    self.next_register, self.allocations = 32, []
    self.app_unpack_sem = None
    self.unpack_credit = False
    self.predicate_depth = 0
    self.tid = 0
    from .sfpmacro import prepare

    prepare(self)
    if self.sfprograms:
      self.initial.update(["SFPU schedule complete", *(f"SFPU cycle {i}" for i in range(1, 8))])

  def event(self, op, *facts):
    self.events[len(self.items)] = [(op, frozenset(facts), self.loc)]
    self.items.append((None, self.loc))

  def fail(self, id, msg):
    raise Error(self.loc, id, msg)

  def alloc(self, name="temporary"):
    r = self.next_register
    self.next_register += 1
    if name != "temporary": self.allocations.append((len(self.items), r, name))
    return r

  def rv(self, op, rd=0, a=0, b=0, imm=0):
    self.items.append((Instruction(op, rd, a, b, imm), self.loc))

  def li(self, n, rd=None):
    if rd is None:
      if n == 0:
        return 0
      rd = self.alloc()
    lo = (n + 2048) % 4096 - 2048
    if (n - lo) & 0xFFFFFFFF:
      self.rv("lui", rd, imm=((n - lo) >> 12) & 0xFFFFF)
      if lo:
        self.rv("addi", rd, rd, imm=lo)
    else:
      self.rv("addi", rd, imm=lo)
    return rd

  def calc(self, op, a, b):
    r = self.alloc()
    self.rv(op, r, a, b)
    return r

  def imm(self, op, a, n):
    r = self.alloc()
    self.rv(op, r, a, imm=n)
    return r

  def mem(self, op, addr, r=None):
    for base, value in {0: 0, **self.base}.items():
      if -2048 <= addr - value < 2048:
        break
    else:
      off = (addr + 2048) % 4096 - 2048
      base = self.li(addr - off)
      value = addr - off
    if r is None:
      r = self.alloc()
      self.rv(op, r, base, imm=addr - value)
    else:
      self.rv(op, 0, base, r, imm=addr - value)
    return r

  def tt(self, op, *args, **kw):
    try:
      self.word(isa.inline(isa.tensix(op, *args, **kw)))
    except ValueError as e:
      self.fail("arg.range", str(e))

  def ttsync(self, check):
    """Wait on a ManualTTSync check register: store (orders earlier stores), load, then consume the load with an ALU
    instruction so no other PC_BUF load starts before it returns (hardware bug, ManualTTSync.md)."""
    self.mem("sw", check, 0)
    self.imm("andi", self.mem("lw", check), 0)

  def drain(self):
    """Block until every Tensix instruction this thread has issued has finished."""
    self.ttsync(hw.COPROCESSOR_DONE_CHECK)

  def zext16(self, r):
    return self.imm("srli", self.imm("slli", r, 16), 16)

  def mov(self, d, s):
    if d != s:
      self.rv("addi", d, s)

  def expr(self, e, want=None):
    match e:
      case Num(n):
        if want in ("bf16", "fp32", "fp16"):
          bits = int.from_bytes(struct.pack("<e" if want == "fp16" else "<f", n), "little")
          if want == "bf16": bits = (bits + 0x7fff + ((bits >> 16) & 1)) >> 16
          return self.li(bits), want
        if type(n) != int:
          self.fail("type.literal", "integer expected")
        t = e.dtype or want or "u32"
        if t not in ("i32", "u32") or not (-(1 << 31) <= n < 1 << 31 if t == "i32" else 0 <= n < 1 << 32):
          self.fail("type.range", f"{n} does not fit {t}")
        return self.li(n), t
      case Name(k):
        if k in self.env:
          if self.env[k][1].startswith("tid:"):
            self.fail("noc.handle", "transaction handles are only valid in NoC operations")
          return self.env[k]
        if k in self.m["storage"]:
          item = self.m["storage"][k]
          return self.li(item["address"]), item["type"] + "*"
        if (param := self.m["params"].get(k)) and param["kind"] == "int":
          return self.mem("lw", fw.L1_PARAM_BASE + 4 * param["slot"]), param["type"]
        self.fail("type.value", f"{k} is not a scalar or local pointer")
      case Attr("core", k):
        return self.mem("lw", hw.CORE[k]), "u32"
      case Call(fn, [a]) if fn in ("i32", "u32"):
        if isinstance(a, Num) and type(a.value) is int:
          return self.li(a.value), fn
        r, t = self.expr(a)
        if t not in ("i32", "u32") and not (fn == "u32" and t.endswith("*")):
          self.fail("type.cast", t)
        return r, fn
      case Call("bits_u32", [value]):
        r, t = self.expr(value)
        if t not in ("bf16", "fp16", "fp32", "e4m3", "e5m2"):
          self.fail("type.bits", "expected a floating-point storage value")
        return r, "u32"
      case Call("tileptr", [base, index]):
        p, t = self.expr(base)
        i, it = self.expr(index)
        if not t.endswith("*") or it not in ("i32", "u32"):
          self.fail("type.tileptr", "expected a local pointer and an integer tile index")
        return self.calc("add", p, self.calc("mul", i, self.li(TYPES[t[:-1]][1]))), t
      case Call("mulh", [a, b]):
        x, t = self.expr(a)
        y, u = self.expr(b, t)
        if t != u or t not in ("i32", "u32"):
          self.fail("type.mulh", "integer operands must agree")
        return self.calc("mulh" if t == "i32" else "mulhu", x, y), t
      case Unary(op, a):
        x, t = self.expr(a, want)
        if t not in ("i32", "u32"):
          self.fail("type.unary", t)
        if op == "!":
          return self.imm("sltiu", x, 1), "u32"
        return (self.calc("sub", 0, x) if op == "-" else self.imm("xori", x, -1)), t
      case Index():
        ptr, t = self.index(e)
        r = self.alloc()
        self.rv(self.width(t, False), r, ptr)
        return r, "u32" if t == "u8" else t
      case Bin(op, a, b):
        if op in ("&&", "||"):
          end = object()
          r = self.alloc()
          for i, part in enumerate((a, b)):
            x, t = self.expr(part)
            if t not in ("i32", "u32"):
              self.fail("type.condition", t)
            self.rv("sltu", r, 0, x)
            if i == 0:
              self.branch("beq" if op == "&&" else "bne", r, 0, end)
          self.mark(end)
          return r, "u32"
        if op == "*" and isinstance(a, Num) and not isinstance(b, Num):
          a, b = b, a
        if op in ("*", "/", "%") and isinstance(b, Num) and pow2(b.value) is not None and not isinstance(a, Num):
          # A power-of-two constant: shift or mask instead of mul/divu/remu (divu and remu take up to 33 cycles).
          x, t = self.expr(a, want)
          k = pow2(b.value)
          if op == "*" and t in ("u32", "i32"):
            return (self.imm("slli", x, k) if k else x), t
          if t == "u32" and op == "/":
            return (self.imm("srli", x, k) if k else x), t
          if t == "u32" and op == "%":
            mask = b.value - 1
            return (self.imm("andi", x, mask) if mask < 2048 else self.calc("and", x, self.li(mask))), t
          y, u = self.expr(b, t if not t.endswith("*") else None)
          return self.binary(op, x, t, y, u)
        if isinstance(a, Num) and not isinstance(b, Num):
          y, u = self.expr(b)
          x, t = self.expr(a, u)
        else:
          x, t = self.expr(a, want)
          y, u = self.expr(b, t if not t.endswith("*") else None)
        return self.binary(op, x, t, y, u)
    self.fail("expr.invalid", str(e))

  def binary(self, op, x, t, y, u):
    if t.endswith("*") and op in ("+", "-") and u in ("u32", "i32"):
      return self.calc("add" if op == "+" else "sub", x, self.scale(y, t[:-1])), t
    if t != u or t not in ("u32", "i32"):
      self.fail("type.binary", f"{t} {op} {u}")
    suffix = "u" if t == "u32" else ""
    if op in ("==", "!="):
      v = self.calc("xor", x, y)
      return (self.imm("sltiu", v, 1) if op == "==" else self.calc("sltu", 0, v)), "u32"
    if op in ("<", ">", "<=", ">="):
      if op in (">", "<="):
        x, y = y, x
      v = self.calc("slt" + suffix, x, y)
      return (self.imm("xori", v, 1) if "=" in op else v), "u32"
    op = {
      "+": "add",
      "-": "sub",
      "*": "mul",
      "/": "div" + suffix,
      "%": "rem" + suffix,
      "&": "and",
      "|": "or",
      "^": "xor",
      "<<": "sll",
      ">>": "srl" if suffix else "sra",
    }[op]
    return self.calc(op, x, y), t

  def scale(self, r, t):
    size = TYPES[t][0]
    if size is None:
      self.fail("type.size", f"{t} elements cannot be indexed")
    return self.imm("slli", r, size.bit_length() - 1) if size > 1 else r

  def width(self, t, store):
    size = TYPES[t][0]
    if size not in (1, 2, 4):
      self.fail("type.width", f"unsupported scalar load/store of {t}")
    return ({1: "sb", 2: "sh", 4: "sw"} if store else {1: "lbu", 2: "lhu", 4: "lw"})[size]

  def storage_pointer(self, e):
    """Resolve a constant pointer as (storage record, byte displacement)."""
    if isinstance(e, Name) and e.id in self.m["storage"]:
      return self.m["storage"][e.id], 0
    if isinstance(e, Call) and e.fn == "tileptr" and isinstance(e.args[1], Num):
      resolved = self.storage_pointer(e.args[0])
      if resolved:
        item, off = resolved
        return item, off + e.args[1].value * TYPES[item["type"]][1]
    if isinstance(e, Bin) and e.op in ("+", "-") and isinstance(e.b, Num):
      resolved = self.storage_pointer(e.a)
      if resolved:
        item, off = resolved
        size = TYPES[item["type"]][0]
        if size:
          return item, off + (size * e.b.value if e.op == "+" else -size * e.b.value)

  def check_pointer(self, e, align=1, length=0):
    resolved = self.storage_pointer(e)
    if resolved:
      item, off = resolved
      if not 0 <= off <= item["size"] - length:
        self.fail("pointer.bounds", "transfer extends beyond declared storage")
      if (item["address"] + off) % align:
        self.fail("pointer.align", f"address requires {align}-byte alignment")
      return item["address"] + off

  def index(self, e):
    if len(e.idx) != 1:
      self.fail("index.rank", "expected one element index")
    i = e.idx[0]
    if isinstance(i, Num) and isinstance(e.base, Name) and e.base.id in self.m["storage"]:
      s = self.m["storage"][e.base.id]
      if not 0 <= i.value < s["count"] * s.get("pages", 1):
        self.fail("index.bounds", str(i.value))
    r, t = self.expr(Bin("+", e.base, i))
    if not t.endswith("*"):
      self.fail("index.type", "expected L1 pointer")
    return r, t[:-1]

  def assign(self, target, val):
    r, t = val
    if isinstance(target, Index):
      a, u = self.index(target)
      if u != t and not (u == "u8" and t == "u32"):
        self.fail("type.store", f"{t} into {u}")
      self.rv(self.width(u, True), 0, a, r)
    else:
      if target.id not in self.env:
        self.env[target.id] = (0 if t.startswith("tid:") else self.alloc(target.id), t)
      d, u = self.env[target.id]
      if t != u:
        self.fail("type.assign", f"{target.id} holds {u}, got {t}")
      self.mov(d, r)

  def values(self, e):
    if isinstance(e, Op):
      from .ops import lower

      return lower(self, e)
    if isinstance(e, Call) and e.fn == "split":
      n, t = self.expr(e.args[0])
      if t != "u32":
        self.fail("split.type", "split expects u32")
      if isinstance(e.args[0], Num) and e.args[0].value * self.p.grid >= 1 << 32:
        self.fail("split.range", "split product overflows")
      core = self.mem("lw", hw.CORE["id"])
      grid = self.li(self.p.grid)
      first = self.calc("divu", self.calc("mul", core, n), grid)
      end = self.calc("divu", self.calc("mul", self.imm("addi", core, 1), n), grid)
      return [(first, "u32"), (self.calc("sub", end, first), "u32")]
    if isinstance(e, Call) and e.fn in self.functions:
      args, returns, link = self.functions[e.fn]
      for expr, (dest, t) in zip(e.args, args):
        r, u = self.expr(expr, t)
        if u != t: self.fail("call.type", f"expected {t}, got {u}")
        self.mov(dest, r)
      self.jump(e.fn, link)
      values = []
      for source, t in returns:
        dest = self.alloc()
        self.mov(dest, source)
        values.append((dest, t))
      return values
    return [self.expr(e)]

  def block(self, body):
    old = self.env.copy()
    for s in body:
      self.loc = s.loc
      self.stmt(s)
    self.env = old

  def stmt(self, s):
    match s:
      case Fence():
        self.rv("fence")
      case Block():
        self.block(s.body)
      case Assign(targets, op, e):
        if op != "=" and isinstance(targets[0], Index):
          addr, element = self.index(targets[0])
          current = self.alloc()
          self.rv(self.width(element, False), current, addr)
          t = "u32" if element == "u8" else element
          r, u = self.expr(e, t)
          result, _ = self.binary(op[:-1], current, t, r, u)
          self.rv(self.width(element, True), 0, addr, result)
          return
        if op != "=":
          e = Bin(op[:-1], targets[0], e)
        if len(targets) == 1 and isinstance(targets[0], Name) and targets[0].id in self.env and isinstance(e, Num):
          vals = [self.expr(e, self.env[targets[0].id][1])]
        elif len(targets) == 1 and isinstance(targets[0], Index) and isinstance(e, Num):
          # A literal in a store takes the element type.
          addr, t = self.index(targets[0])
          store = self.width(t, True)
          if t == "u8":
            if type(e.value) != int or not 0 <= e.value <= 255:
              self.fail("type.range", "byte literal outside 0..255")
            t = "u32"
          r, u = self.expr(e, t)
          if u != t:
            self.fail("type.store", f"cannot store {u} as {t}")
          self.rv(store, 0, addr, r)
          return
        else:
          vals = self.values(e)
        if len(vals) != len(targets):
          self.fail("assign.count", "wrong result count")
        for target, v in zip(targets, vals):
          self.assign(target, v)
      case Op() | Call():
        values = self.values(s)
        if (
          values
          and values[0][1].startswith("tid:")
          and not any(a.name == "tid" or a.value == Name("wait", a.value.loc) for a in s.args)
        ):
          self.fail("noc.handle", "request requires a handle, tid= or wait")
      case Return(vals):
        evaluated = [self.expr(v) for v in vals]
        if self.return_types is None:
          self.return_types = [t for _, t in evaluated]
        if self.return_types != [t for _, t in evaluated]:
          self.fail("return.type", "return types disagree")
        for d, (r, t) in zip(self.results, evaluated):
          self.mov(d, r)
        if vals:
          self.event("set", "return values of " + self.fn_name)
        self.jump(self.exit)
      case If(c, body, other):
        alt, end = object(), object()
        self.branch("beq", self.condition(c), 0, alt)
        self.block(body)
        self.jump(end)
        self.mark(alt)
        self.block(other)
        self.mark(end)
      case Break():
        self.jump(self.loops[-1][0])
      case Continue():
        self.jump(self.loops[-1][1])
      case For() | While() | Loop():
        start, step, end = object(), object(), object()
        old = self.env.copy()
        count = isinstance(s, For) or isinstance(s, Loop) and s.count is not None
        if count:
          i, limit = self.alloc(), self.alloc()
          self.mov(i, self.condition(s.lo) if isinstance(s, For) else 0)
          self.mov(limit, self.condition(s.hi if isinstance(s, For) else s.count))
          if isinstance(s, For):
            self.env[s.var] = i, "u32"
        self.mark(start)
        if count:
          self.branch("bgeu", i, limit, end)
        elif isinstance(s, While):
          self.branch("beq", self.condition(s.cond), 0, end)
        self.loops.append((end, step))
        self.block(s.body)
        self.loops.pop()
        self.mark(step)
        if count:
          self.rv("addi", i, i, imm=1)
        self.jump(start)
        self.mark(end)
        self.env = old

  def condition(self, e):
    r, t = self.expr(e)
    if t not in ("i32", "u32"):
      self.fail("type.condition", t)
    return r

  def generate(self):
    # Emit callees first to establish their parameter and result registers.
    order = []

    def visit(k):
      if k not in order:
        for f in self.p.calls[k]:
          visit(f)
        order.append(k)

    visit(self.role)
    from .expand import _walk_stmts
    from .ops import cb_resource

    cursors = {}
    noc_kinds = set()
    for name in order:
      for stmt in _walk_stmts(self.p.fns[name].body):
        op = stmt.value if isinstance(stmt, Assign) else stmt
        if isinstance(op, Op) and op.ns == "noc" and op.name in ("read", "write", "inc", "mcast"):
          noc_kinds.add(op.name)
        if isinstance(op, Op) and (op.ns, op.name) == ("math", "addrmod"):
          from .ops import keyword, number

          label = next((keyword(a.value) for a in op.args if a.name is None), None)
          slot = next((number(a.value, 0, 7) for a in op.args if a.name == "slot"), None)
          if label and slot is not None:
            self.addrmods[label] = slot
        if isinstance(op, Op) and op.ns == "cb" and op.name in ("push", "pop", "wait", "reserve"):
          self.loc = op.loc
          _, item, _, cursor = cb_resource(self, op)
          cursors[cursor] = item["address"]
    if len(order) > 1:
      self.jump(self.role)
    for name in order:
      self.fn_name = name
      fn = self.p.fns[name]
      self.mark(name)
      self.loc = fn.loc
      self.env = {}
      self.loops = []
      self.exit = object()
      link = 0 if name == self.role else self.alloc("link")
      if fn.nret:
        self.event("clear", "return values of " + name)
      if not link:
        for r, n in self.base.items():
          self.li(n, r)
        from .noc import init_buffers

        init_buffers(self, noc_kinds)
        for cursor, address in sorted(cursors.items()):
          self.mem("sw", cursor, self.li(address))
          self.mem("sw", cursor + 4, 0)
      for k, t in fn.params:
        self.env[k] = self.alloc(k), t.name + ("*" if t.ptr else "")
      args = list(self.env.values())
      self.results = [self.alloc("result") for _ in range(fn.nret)]
      self.return_types = None
      self.block(fn.body)
      self.mark(self.exit)
      if fn.nret:
        self.event("require", "return values of " + name)
      if name == self.role and self.sfprograms:
        self.event("require", "SFPU schedule complete")
      self.ends[name] = len(self.items)
      if link:
        self.rv("jalr", 0, link)
      else:
        self.word(int.from_bytes(fw.ret(self.role), "little"))
      self.functions[name] = args, list(zip(self.results, self.return_types or [])), link
    from .state import verify

    verify(self)
    allocate(self)
    return self.finish()
