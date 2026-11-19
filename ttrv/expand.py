"""Front end, part 2: compile-time evaluation and front-end checks (spec §3-§5). Ends the front end.

  expand(decls, defines={}) -> Program

What it does, in order:
  1. File-level declarations: resolve constant `if`s (spliced, no scope), fold `const` and `type` (with -D overrides), `grid`,
     types (T[n] counts become ints), declaration options. One namespace for file-level names; reserved words,
     types, builtins and hardware semaphore names cannot be declared.
  2. shared { }: each assignment is checked uniform (constants, grid.size, core.*, earlier shared names, builtins).
  3. Templates (mop/replay/sfpmacro): constants, repeat and macros expanded; the result must be device ops only,
     every mop/sfpmacro line labeled, no replay line labeled.
  4. Functions: constants folded, constant `if` keeps the taken branch, `repeat` emits one copy per index, macros
     are substituted hygienically. Then the entry functions get the shared assignments they read prepended.
  5. Checks on the flat functions: names exist and are in scope (except bare words in device-op operands, which
     ops.py decides), no local shadows a file-level name, for variables are read-only, break/continue inside a loop
     and never out of a macro expansion, `loop { }` has a syntactic exit, return counts agree, calls are whole
     statements with the right arity/result count, the call graph is acyclic.

The flat tree uses the parse.py nodes. Expansions leave Block nodes (a scope: resolved if, one repeat copy, one
macro expansion with Block.macro set); codegen treats Block as a nested scope. Macro-local names are renamed
`name~k`; every node from a macro body has the invocation chain in loc.via.

Constant folding uses mathematical integers and requires every intermediate to fit 32 bits as u32 or i32
(-2^31 .. 2^32-1). `/` and `%` truncate toward zero (RV32M), shift counts must be 0..31. `~c` of a non-negative
constant is its u32 complement (`~31` = 0xFFFFFFE0), since u32 is the default type; codegen does the type-exact
check where the operand type is known. Float constants support arithmetic and sqrt."""
from __future__ import annotations
import math
import operator
from dataclasses import dataclass, field, replace
from ttrv.parse import (Alias, SfpRegion, Error, Num, Name, Attr, Unary, Bin, Index, Call, Range, Arg, Op, Assign, MacroCall, If, While,
                        For, Loop, Repeat, Break, Continue, Fence, Return, Label, Block, Grid, Const, Param, TypeDecl, Storage,
                        Sem, Macro, Fn, Template, Shared, KEYWORDS, NAMESPACES, DECLS, show, show_expr)

# name: (bytes per element or None for BFP, T.tile)
TYPES = {"bf16": (2, 2048), "fp16": (2, 2048), "fp32": (4, 4096), "e4m3": (1, 1024), "e5m2": (1, 1024),
         "bfp8": (None, 1088), "bfp4": (None, 576), "u8": (1, 1024), "u32": (4, 4096), "i32": (4, 4096),
         "u64": (8, 8192)}
SEMS = ("fpu_sfpu", "math_pack", "unpack_to_dest", "unpack_operand_sync", "pack_done", "unpack_sync",
        "unpack_math_done", "math_done")
ENTRIES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
EXPR_BUILTINS = {"i32": 1, "u32": 1, "mulh": 2}     # name: arity; one result, usable inside expressions
STMT_BUILTINS = {"split": (1, 2)}                  # name: (arity, results); whole statements only, like fn calls
ENDPOINTS = {"remote": 3, "rect": 5}               # NoC endpoint constructors, device operands only (spec §7)
CORE_ATTRS = ("x", "y", "id")
RESERVED = KEYWORDS | NAMESPACES | DECLS | set(TYPES) | set(EXPR_BUILTINS) | set(STMT_BUILTINS) | set(ENDPOINTS) | set(SEMS) | {"core", "inf"}
MAX_STMTS = 200_000

@dataclass
class Program:
  grid: int
  consts: dict = field(default_factory=dict)      # name -> int
  params: dict = field(default_factory=dict)      # name -> Param, declaration order (= slot order); range set for integers
  types: dict = field(default_factory=dict)       # type NAME = T: name -> element type name
  l1: dict = field(default_factory=dict)          # name -> Storage
  cbs: dict = field(default_factory=dict)         # name -> Storage
  sems: dict = field(default_factory=dict)        # alias -> Sem
  templates: dict = field(default_factory=dict)   # name -> Template, body flat: [Label(Op)] or [Op] for replay
  fns: dict = field(default_factory=dict)         # name -> Fn, body flat, nret set, entries with shared prelude
  shared: list = field(default_factory=list)      # expanded shared assignments, source order
  calls: dict = field(default_factory=dict)       # fn -> [callee] in first-call order
  names: dict = field(default_factory=dict)       # every file-level name -> its declaration

def _err(node, id, msg): raise Error(getattr(node, "loc", None), id, msg)

def _fit(v, node):
  if not -(1 << 31) <= v < (1 << 32): _err(node, "const.range", f"constant {v} does not fit 32 bits")
  return v

def _consts_declared(decls):
  for d in decls:
    if isinstance(d, (Const, TypeDecl)): yield d.name
    elif isinstance(d, If): yield from _consts_declared(d.body + d.orelse)

def _walk_stmts(body):
  """Every statement, depth first, including nested bodies."""
  for s in body:
    yield s
    match s:
      case If(): yield from _walk_stmts(s.body); yield from _walk_stmts(s.orelse)
      case While() | For() | Loop() | Repeat() | Block(): yield from _walk_stmts(s.body)
      case Label(): yield from _walk_stmts([s.stmt])

def _walk_expr(e):
  yield e
  match e:
    case Unary(): yield from _walk_expr(e.x)
    case Bin(): yield from _walk_expr(e.a); yield from _walk_expr(e.b)
    case Index():
      yield from _walk_expr(e.base)
      for i in e.idx: yield from _walk_expr(i)
    case Call():
      for a in e.args: yield from _walk_expr(a)
    case Range(): yield from _walk_expr(e.lo); yield from _walk_expr(e.hi)
    case Op():
      for a in e.args: yield from _walk_expr(a.value)

def _stmt_exprs(s):
  """The expressions a statement reads directly (not those of nested bodies). Assign targets included."""
  match s:
    case Assign(): return [*s.targets, s.value]
    case Op() | Call(): return [s]
    case If() | While(): return [s.cond]
    case For(): return [s.lo, s.hi]
    case Loop(): return [] if s.count is None else [s.count]
    case Return(): return s.values
    case Label(): return _stmt_exprs(s.stmt)
  return []

def _assigned_names(body):
  out = set()
  for s in _walk_stmts(body):
    if isinstance(s, Assign): out |= {t.id for t in s.targets if isinstance(t, Name)}
    elif isinstance(s, For): out.add(s.var)
  return out

def _flatten(body):
  for s in body:
    if isinstance(s, Block): yield from _flatten(s.body)
    else: yield s

class Expander:
  def __init__(self, defines):
    self.defines = dict(defines)
    self.p = Program(grid=None)
    self.macros = {}
    self.sites = ()            # macro invocation locs, innermost first
    self.macro_stack = []
    self.template = None       # kind while expanding a template body
    self.count = 0
    self.fresh = 0

  def run(self, decls):
    known = set(_consts_declared(decls))
    for k in self.defines:
      if k not in known: raise Error(None, "define.unknown", f"-D {k}: no const or type of that name")
    raw_fns, raw_templates, shared = [], [], []
    self.decls(decls, raw_fns, raw_templates, shared)
    if self.p.grid is None: raise Error(None, "grid.missing", "missing `grid N` declaration")
    if len(shared) > 1: _err(shared[1], "shared.dup", "at most one shared { } block")
    if shared: self.shared(shared[0])
    for t in raw_templates: self.p.templates[t.name] = self.template_(t)
    for f in raw_fns: self.p.fns[f.name] = self.fn(f)
    for f in self.p.fns.values(): f.nret = self.nret(f)
    for f in self.p.fns.values(): self.check_fn(f)
    self.check_calls()
    return self.p

  # ---- declarations ----

  def declare(self, name, d):
    if name in RESERVED: _err(d, "name.reserved", f"{name!r} is reserved")
    if name in self.p.names: _err(d, "name.dup", f"{name!r} already declared at {self.p.names[name].loc}")
    self.p.names[name] = d

  def decls(self, decls, fns, templates, shared):
    for d in decls:
      match d:
        case If(): self.decls(d.body if self.const_int(d.cond, "a file-level if condition") else d.orelse, fns, templates, shared)
        case Grid():
          if self.p.grid is not None: _err(d, "grid.dup", "grid declared twice")
          self.p.grid = self.const_int(d.n, "grid")
          if self.p.grid < 1: _err(d, "grid.range", "grid must be at least 1")
        case Const():
          self.declare(d.name, d)
          value = self.expr(d.value, {})
          if not isinstance(value, Num): _err(d, "const.required", f"expected constant {d.name}")
          v = value.value
          if d.name in self.defines:
            override = self.defines[d.name]
            if isinstance(v, float): v = float(override)
            else: v = _fit(int(override, 0) if isinstance(override, str) else int(override), d)
          self.p.consts[d.name] = v
        case TypeDecl():
          self.declare(d.name, d)
          if d.type.count is not None or d.type.ptr or d.type.buf: _err(d.type, "type.decl", "type NAME = T names an element type")
          t = replace(d.type, name=self.defines[d.name]) if d.name in self.defines else d.type
          self.p.types[d.name] = self.type(t).name
        case Param():
          self.declare(d.name, d)
          t = self.type(d.type)
          if t.count is not None or t.ptr: _err(d.type, "param.type", "a parameter is a buffer `T[]` or an integer `u32 in lo..hi`")
          if t.buf:
            if d.range is not None: _err(d, "param.range", "a buffer parameter has no range")
            self.p.params[d.name] = replace(d, type=t, opts=self.opts(d.opts))
          else:
            if t.name not in ("u32", "i32"): _err(d.type, "param.type", f"`param {d.name}: {t.name}` is not allowed: a buffer is `{t.name}[]`, an integer is u32 or i32")
            if d.range is None: _err(d, "param.range", f"integer parameter {d.name} needs a range: `{t.name} in lo..hi`")
            lo, hi = (self.const_int(e, "a parameter bound") for e in d.range)
            if not lo < hi: _err(d, "param.range", "empty parameter range")
            if t.name == "u32" and not (0 <= lo and hi - 1 < 1 << 32) or t.name == "i32" and not (-(1 << 31) <= lo and hi - 1 < 1 << 31):
              _err(d, "param.range", f"range does not fit {t.name}")
            if d.opts: _err(d, "param.opts", "an integer parameter takes no options")
            self.p.params[d.name] = replace(d, type=t, opts=[], range=(lo, hi))
        case Storage():
          self.declare(d.name, d)
          if d.type.count is None or d.type.ptr: _err(d.type, "storage.type", f"{d.kind} storage is declared T[n]")
          (self.p.l1 if d.kind == "l1" else self.p.cbs)[d.name] = replace(d, type=self.type(d.type), opts=self.opts(d.opts))
        case Sem():
          self.declare(d.name, d)
          if d.hw not in SEMS: _err(d, "sem.hw", f"unknown hardware semaphore {d.hw!r}; one of {', '.join(SEMS)}")
          if (other := next((s for s in self.p.sems.values() if s.hw == d.hw), None)):
            _err(d, "sem.alias", f"{d.hw} already aliased as {other.name!r}")
          self.p.sems[d.name] = replace(d, opts=self.opts(d.opts))
        case Macro():
          self.declare(d.name, d)
          if len(set(d.params)) != len(d.params): _err(d, "macro.params", "duplicate macro parameter")
          self.macros[d.name] = d
        case Fn(): self.declare(d.name, d); fns.append(d)
        case Template(): self.declare(d.name, d); templates.append(d)
        case Shared(): shared.append(d)
        case _: _err(d, "decl.unknown", "not a declaration")

  def type(self, t):
    if t.name in self.p.types: t = replace(t, name=self.p.types[t.name])
    if t.name not in TYPES: _err(t, "type.unknown", f"unknown type {t.name!r}")
    if t.count is None: return t
    n = self.const_int(t.count, "an element count")
    if n < 1: _err(t, "type.count", "element count must be positive")
    if TYPES[t.name][0] is None and n % 16: _err(t, "type.bfp", f"{t.name}[n] needs n a multiple of 16")
    return replace(t, count=n)

  def opts(self, args):
    return self.args(args, {})

  def const_int(self, e, what):
    v = self.expr(e, {})
    if not isinstance(v, Num) or isinstance(v.value, float): _err(e, "const.required", f"{what} must be a constant integer, got `{show_expr(v)}`")
    return v.value

  # ---- expressions ----

  def at(self, loc): return replace(loc, via=self.sites) if self.sites and loc is not None else loc

  def expr(self, e, env):
    loc = self.at(e.loc)
    match e:
      case Num(): return replace(e,loc=loc)
      case Name():
        if e.id in env:
          v = env[e.id]
          return replace(v, loc=loc) if isinstance(v, (Num, Name)) else v
        if e.id in self.p.consts: return Num(self.p.consts[e.id], loc)
        if e.id in self.p.types: return Name(self.p.types[e.id], loc)
        return Name(e.id, loc)
      case Attr():
        if e.base == "grid" and e.attr == "size":
          if self.p.grid is None: _err(e, "grid.order", "grid.size used before `grid`")
          return Num(self.p.grid, loc)
        if e.base == "core" and e.attr in CORE_ATTRS: return Attr(e.base, e.attr, loc)
        if e.base == "dst" and e.attr in ("tile", "face"): return Num(64 if e.attr == "tile" else 16, loc)
        base = self.p.types.get(e.base, e.base)
        if base in TYPES and e.attr in ("size", "tile"):
          size, tile = TYPES[base]
          if e.attr == "size" and size is None: _err(e, "type.size", f"{e.base}.size: BFP has no per-element size")
          return Num(size if e.attr == "size" else tile, loc)
        _err(e, "attr.unknown", f"unknown attribute {e.base}.{e.attr}")
      case Unary(): return self.fold(Unary(e.op, self.expr(e.x, env), loc))
      case Bin(): return self.fold(Bin(e.op, self.expr(e.a, env), self.expr(e.b, env), loc))
      case Index(): return Index(self.expr(e.base, env), [self.expr(i, env) for i in e.idx], loc)
      case Call(): return self.fold(Call(e.fn, [self.expr(a, env) for a in e.args], loc))
      case Range(): return Range(self.expr(e.lo, env), self.expr(e.hi, env), loc)
    _err(e, "expr.bad", f"not an expression: {type(e).__name__}")

  def fold(self, e):
    match e:
      case Call(fn="sqrt", args=[Num(value=v)]):
        if v < 0: _err(e, "const.sqrt", "negative square root")
        return Num(math.sqrt(v), e.loc)
      case Unary(x=Num(value=float() as v)):
        if e.op != "-": _err(e, "const.float", f"{e.op} on a float literal")
        return Num(-v, e.loc)
      case Unary(x=Num(value=v)):
        r = {"-": -v, "!": int(v == 0), "~": (~v) & 0xFFFFFFFF if v >= 0 else ~v}[e.op]
        return Num(_fit(r, e), e.loc, "u32" if e.op=="!" else e.x.dtype)
      case Bin(a=Num(value=a), b=Num(value=b)):
        if isinstance(a, float) or isinstance(b, float):
          ops = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}
          if e.op not in ops: _err(e, "const.float", f"invalid floating-point operator {e.op}")
          if e.op == "/" and b == 0: _err(e, "const.div0", "constant division by zero")
          return Num(ops[e.op](a, b), e.loc)
        op = e.op
        if e.a.dtype and e.b.dtype and e.a.dtype!=e.b.dtype: _err(e,"type.binary","mixed signed and unsigned operands")
        dtype=e.a.dtype or e.b.dtype
        if op in ("/", "%"):
          if b == 0: _err(e, "const.div0", "constant division by zero")
          q = abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1)
          r = q if op == "/" else a - b * q
        elif op in ("<<", ">>"):
          if not 0 <= b < 32: _err(e, "const.shift", f"constant shift count {b} outside 0..31")
          r = a << b if op == "<<" else a >> b
        else:
          r = {"+": a + b, "-": a - b, "*": a * b, "&": a & b, "|": a | b, "^": a ^ b, "==": a == b, "!=": a != b,
               "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b, "&&": bool(a and b), "||": bool(a or b)}[op]
        return Num(_fit(int(r), e), e.loc,"u32" if op in ("<","<=",">",">=","==","!=","&&","||") else dtype)
      case Call(fn="u32" | "i32", args=[Num(value=int() as v)]):
        v &= 0xFFFFFFFF
        return Num(v - (1 << 32) if e.fn == "i32" and v >> 31 else v, e.loc, e.fn)
    return e

  def args(self, args, env):
    seen, out = set(), []
    for a in args:
      if a.name is not None:
        if a.name in seen: _err(a, "arg.dup", f"option {a.name!r} given twice")
        seen.add(a.name)
      out.append(Arg(a.name, a.op, self.expr(a.value, env), self.at(a.loc)))
    return out

  # ---- statements ----

  def block(self, body, env, splice=False):
    out = []
    if not splice: env = env.copy()
    for s in body:
      if isinstance(s, Alias): env[s.name] = self.expr(s.value, env)
      else: out += self.stmt(s, env)
    return out

  def target(self, t, env):
    if isinstance(t, Index): return self.expr(t, env)
    name = self.local(t.id, env, t)
    return Name(name, self.at(t.loc))

  def local(self, name, env, node):
    if name in env:
      v = env[name]
      if isinstance(v, Name): return v.id
      _err(node, "assign.const", f"cannot assign {name!r}: it is a repeat index or macro argument bound to `{show_expr(v)}`")
    if name in self.p.consts: _err(node, "assign.const", f"cannot assign const {name!r}")
    return name

  def runtime(self, s, what):
    if self.template: _err(s, "template.control", f"{what} in a {self.template} body: templates hold device instructions only")

  def stmt(self, s, env):
    self.count += 1
    if self.count > MAX_STMTS: _err(s, "expand.size", f"expansion exceeds {MAX_STMTS} statements")
    loc = self.at(s.loc)
    match s:
      case Assign():
        value = self.op(s.value, env) if isinstance(s.value, Op) else self.expr(s.value, env)
        return [Assign([self.target(t, env) for t in s.targets], s.op, value, loc)]
      case SfpRegion():
        def marker(name, args=()):
          return Op("sfp", name, [Arg(None, None, e, loc) for e in args], loc)
        operand = self.expr(s.operand, env)
        body = self.block(s.body, env)
        otherwise = [marker("otherwise"), *self.block(s.orelse, env)] if s.orelse else []
        return [marker("begin_" + s.kind, [operand]), *body, *otherwise, marker("end_" + s.kind)]
      case Op(): return [self.op(s, env)]
      case Call(): return [self.expr(s, env)]
      case MacroCall(): return [self.macro(s, env)]
      case If():
        cond = self.expr(s.cond, env)
        if isinstance(cond, Num):
          # A compile-time if splices its taken branch in place, like C's #if: no scope (spec §3).
          return self.block(s.body if cond.value else s.orelse, env, splice=True)
        self.runtime(s, "a runtime if")
        return [If(cond, self.block(s.body, env), self.block(s.orelse, env), loc)]
      case While():
        self.runtime(s, "while")
        return [While(self.expr(s.cond, env), self.block(s.body, env), loc)]
      case For():
        self.runtime(s, "for")
        return [For(self.local(s.var, env, s), self.expr(s.lo, env), self.expr(s.hi, env), self.block(s.body, env), loc)]
      case Loop():
        self.runtime(s, "loop")
        return [Loop(None if s.count is None else self.expr(s.count, env), self.block(s.body, env), loc)]
      case Repeat():
        lo, hi = self.const_int_env(s.lo, env, "a repeat bound"), self.const_int_env(s.hi, env, "a repeat count")
        if s.var is not None and (s.var in self.p.names or s.var in RESERVED): _err(s, "repeat.var", f"repeat index {s.var!r} shadows a file-level or reserved name")
        out = []
        for k in range(lo, hi):
          inner = env if s.var is None else env | {s.var: Num(k)}
          out.append(Block(self.block(s.body, inner), None, loc))
        return out
      case Break() | Continue() | Fence(): return [type(s)(loc)]
      case Return():
        if self.macro_stack: _err(s, "macro.return", "return inside a macro")
        self.runtime(s, "return")
        return [Return([self.expr(v, env) for v in s.values], loc)]
      case Label():
        if not self.template: _err(s, "label.outside", f"label {s.label!r} outside a mop/sfpmacro body")
        inner = list(_flatten(self.stmt(s.stmt, env)))
        if len(inner) != 1: _err(s, "label.many", f"label {s.label!r} must name exactly one instruction, got {len(inner)}")
        return [Label(s.label, inner[0], loc)]
    _err(s, "stmt.bad", f"unexpected {type(s).__name__} here")

  def const_int_env(self, e, env, what):
    v = self.expr(e, env)
    if not isinstance(v, Num) or isinstance(v.value, float): _err(e, "const.required", f"{what} must be a constant integer, got `{show_expr(v)}`")
    return v.value

  def op(self, o, env): return Op(o.ns, o.name, self.args(o.args, env), self.at(o.loc))

  def macro(self, s, env):
    m = self.macros.get(s.name)
    if m is None: _err(s, "macro.unknown", f"unknown macro {s.name!r}")
    if len(s.args) != len(m.params): _err(s, "macro.arity", f"{s.name}! takes {len(m.params)} arguments, got {len(s.args)}")
    if s.name in self.macro_stack: _err(s, "macro.recursive", f"recursive macro {' -> '.join(self.macro_stack + [s.name])}")
    args = [self.expr(a, env) for a in s.args]
    self.fresh += 1
    inner = dict(zip(m.params, args))
    for n in sorted(_assigned_names(m.body) - set(m.params)):
      if n in self.p.names: _err(m, "assign.global", f"macro {m.name} assigns file-level name {n!r}")
      inner[n] = Name(f"{n}~{self.fresh}")
    loc = self.at(s.loc)
    self.macro_stack.append(s.name)
    saved, self.sites = self.sites, (s.loc,) + self.sites
    try: body = self.block(m.body, inner)
    finally: self.sites, _ = saved, self.macro_stack.pop()
    return Block(body, s.name, loc)

  # ---- shared, templates, functions ----

  def shared(self, sh):
    for s in sh.body:
      if not isinstance(s, Assign) or s.op != "=" or not all(isinstance(t, Name) for t in s.targets):
        _err(s, "shared.stmt", "shared { } holds only `name = expr` / `a, b = builtin(...)` assignments")
      [a] = self.stmt(s, {})
      v = a.value
      if isinstance(v, Call) and v.fn in STMT_BUILTINS:
        nargs, nres = STMT_BUILTINS[v.fn]
        if len(v.args) != nargs or len(a.targets) != nres: _err(s, "call.arity", f"{v.fn} takes {nargs} argument(s) and gives {nres} result(s)")
        args = v.args
      elif len(a.targets) != 1: _err(s, "shared.stmt", "several targets need a builtin call")
      else: args = [v]
      for e in args:
        for x in _walk_expr(e):
          match x:
            case Num() | Attr() | Unary() | Bin(): pass
            case Name() if isinstance(self.p.names.get(x.id), Assign): pass
            case Name() if (d := self.p.params.get(x.id)) is not None and d.range is not None: pass
            case Name(): _err(x, "shared.uniform", f"shared values may read only constants, integer parameters, grid.size, core.* and earlier shared names, not {x.id!r}")
            case Call() if x.fn in EXPR_BUILTINS: self.check_builtin(x)
            case _: _err(x, "shared.uniform", f"`{show_expr(x)}` is not allowed in shared (no element access, device ops or fn calls)")
      for t in a.targets: self.declare(t.id, a)
      self.p.shared.append(a)

  def template_(self, t):
    self.template = t.kind
    try: body = list(_flatten(self.block(t.body, {})))
    finally: self.template = None
    for s in body:
      op = s.stmt if isinstance(s, Label) else s
      if not isinstance(op, Op): _err(s, "template.stmt", f"{t.kind} bodies hold device instructions only")
      if isinstance(op, Op) and op.ns in ("mop", "replay") and t.kind == "replay": _err(s, "template.nest", "a replay cannot run a mop or replay")
      if (t.kind == "replay") == isinstance(s, Label):
        _err(s, "template.label", "replay lines are unlabeled" if t.kind == "replay" else f"every {t.kind} line needs a label")
    labels = [s.label for s in body if isinstance(s, Label)]
    opts = self.opts(t.opts)
    if t.kind == "mop":
      if any(a.name is None and isinstance(a.value, Name) and a.value.id == "mask" for a in opts):
        labels = [label for label in labels if label != "a"]  # mask MOP A can occupy four slots
      if len(set(labels)) != len(labels): _err(t, "template.label", "duplicate mop label")
    return replace(t, opts=opts, body=body)

  def fn(self, f):
    if f.name in ENTRIES and f.params: _err(f, "fn.entry", f"entry function {f.name} takes no parameters")
    params = []
    for n, ty in f.params:
      if n in RESERVED or n in self.p.names: _err(ty, "name.shadow", f"parameter {n!r} shadows a file-level or reserved name")
      ty = self.type(ty)
      if ty.count is not None: _err(ty, "fn.param", "parameters are scalars or pointers (T*)")
      if not ty.ptr and TYPES[ty.name][0] is None: _err(ty, "fn.param", "BFP values cannot be passed")
      if ty.ptr and ty.name == "u64": _err(ty, "fn.param", "no u64 pointers")
      params.append((n, ty))
    if len({n for n, _ in params}) != len(params): _err(f, "fn.param", "duplicate parameter")
    body = self.block(f.body, {})
    reads = {}
    for s in _walk_stmts(body):
      for e in _stmt_exprs(s):
        for x in _walk_expr(e):
          if isinstance(x, Name) and isinstance(self.p.names.get(x.id), Assign): reads.setdefault(x.id, x)
    if reads and f.name not in ENTRIES:
      n, x = next(iter(reads.items()))
      _err(x, "shared.entry", f"shared name {n!r} read in {f.name}; shared values are visible in entry functions only, pass it as an argument")
    need = set(reads)
    for a in reversed(self.p.shared):
      if any(t.id in need for t in a.targets):
        need |= {x.id for e in [a.value] for x in _walk_expr(e) if isinstance(x, Name)}
    prelude = [a for a in self.p.shared if any(t.id in need for t in a.targets)]
    return replace(f, params=params, body=prelude + body)

  # ---- checks ----

  def nret(self, f):
    rets = [s for s in _walk_stmts(f.body) if isinstance(s, Return)]
    counts = {len(r.values) for r in rets}
    if len(counts) > 1: _err(rets[-1], "return.count", f"{f.name}: returns disagree in value count ({sorted(counts)})")
    n = counts.pop() if counts else 0
    if n and f.name in ENTRIES: _err(f, "fn.entry", f"entry function {f.name} returns no values")
    return n

  def check_builtin(self, c):
    if len(c.args) != EXPR_BUILTINS[c.fn]: _err(c, "call.arity", f"{c.fn} takes {EXPR_BUILTINS[c.fn]} argument(s)")

  def check_fn(self, f):
    scopes = [{n: "param" for n, _ in f.params}]
    calls = self.p.calls.setdefault(f.name, [])
    def find(n): return next((s[n] for s in reversed(scopes) if n in s), None)
    def read(e, operand=False):
      for x in _walk_expr(e):
        match x:
          case Name() if find(x.id) is None and x.id not in self.p.names and not operand:
            _err(x, "name.unknown", f"unknown name {x.id!r}")
          case Call() if x.fn in EXPR_BUILTINS: self.check_builtin(x)
          case Call() if x.fn in ENDPOINTS and operand:
            if len(x.args) != ENDPOINTS[x.fn]: _err(x, "call.arity", f"{x.fn} takes {ENDPOINTS[x.fn]} arguments")
          case Call(): _err(x, "call.expr", f"call to {x.fn} must be a statement of its own (`x = {x.fn}(...)`)")
          case Range() if not operand: _err(x, "range.where", "a range a..b only appears in for/repeat and device operands")
    def define(t):
      if t.id in self.p.names or t.id in RESERVED: _err(t, "name.shadow", f"{t.id!r} is a file-level or reserved name; locals cannot shadow it")
      kind = find(t.id)
      if kind == "for": _err(t, "assign.for", f"for variable {t.id!r} is read-only")
      if kind is None: scopes[-1][t.id] = "var"
    def call(c, ntargets):
      for a in c.args: read(a)
      if c.fn in STMT_BUILTINS:
        nargs, nres = STMT_BUILTINS[c.fn]
      elif c.fn in EXPR_BUILTINS:
        self.check_builtin(c)
        return
      elif c.fn in self.p.fns:
        if c.fn in ENTRIES: _err(c, "call.entry", f"cannot call entry function {c.fn}")
        g = self.p.fns[c.fn]
        nargs, nres = len(g.params), g.nret
        if c.fn not in calls: calls.append(c.fn)
      else: _err(c, "call.unknown", f"unknown function {c.fn!r}")
      if len(c.args) != nargs: _err(c, "call.arity", f"{c.fn} takes {nargs} argument(s), got {len(c.args)}")
      if ntargets and ntargets != nres: _err(c, "call.results", f"{c.fn} gives {nres} result(s), assigned to {ntargets}")
    def nested(body, loops, var=None):
      scopes.append({} if var is None else {var: "for"})
      stmts(body, loops)
      scopes.pop()
    def stmts(body, loops):
      for s in body:
        match s:
          case Assign():
            if isinstance(s.value, Op): read(s.value, operand=True)
            elif isinstance(s.value, Call) and s.value.fn not in EXPR_BUILTINS: call(s.value, len(s.targets))
            else: read(s.value)
            for t in s.targets:
              if any(s is a for a in self.p.shared): continue   # shared prelude: names live for the whole entry
              if isinstance(t, Index): read(t)
              elif s.op != "=":
                if find(t.id) is None: _err(t, "name.unknown", f"{s.op} on {t.id!r} before it is assigned")
                define(t)
              else: define(t)
          case Op(): read(s, operand=True)
          case Call(): call(s, 0)
          case If():
            read(s.cond)
            nested(s.body, loops); nested(s.orelse, loops)
          case While(): read(s.cond); nested(s.body, loops + 1)
          case For():
            read(s.lo); read(s.hi)
            if s.var in self.p.names or s.var in RESERVED: _err(s, "name.shadow", f"for variable {s.var!r} shadows a file-level or reserved name")
            nested(s.body, loops + 1, s.var)
          case Loop():
            if s.count is not None: read(s.count)
            elif not self.exits(s.body): _err(s, "loop.exit", "`loop { }` needs a break or return in its body")
            nested(s.body, loops + 1)
          case Block(): nested(s.body, 0 if s.macro else loops)
          case Break() | Continue():
            if not loops: _err(s, "loop.outside", f"{type(s).__name__.lower()} outside a loop" + (" (macro bodies cannot break out of their expansion)" if s.loc.via else ""))
          case Return():
            for v in s.values: read(v)
            if len(s.values) != f.nret: _err(s, "return.count", f"{f.name} returns {f.nret} value(s)")
          case Fence(): pass
          case _: _err(s, "stmt.bad", f"unexpected {type(s).__name__} in a function")
    stmts(f.body, 0)

  def exits(self, body, depth=0):
    for s in body:
      match s:
        case Break() if depth == 0: return True
        case Return(): return True
        case If() if self.exits(s.body, depth) or self.exits(s.orelse, depth): return True
        case Block() if not s.macro and self.exits(s.body, depth): return True
        case While() | For() | Loop() if self.exits(s.body, depth + 1): return True
    return False

  def check_calls(self):
    state = {}
    def visit(f, path):
      if state.get(f) == 1: raise Error(self.p.fns[f].loc, "call.cycle", f"call cycle: {' -> '.join(path + [f])}")
      if state.get(f) == 2: return
      state[f] = 1
      for g in self.p.calls.get(f, []): visit(g, path + [f])
      state[f] = 2
    for f in self.p.fns: visit(f, [])

def expand(decls: list, defines: dict | None = None) -> Program:
  return Expander(defines or {}).run(decls)

def show_program(p: Program) -> str:
  """The flat program as source text."""
  out = [f"grid {p.grid}"]
  out += [f"const {k} = {v}" for k, v in p.consts.items()]
  for d in (*p.params.values(), *p.l1.values(), *p.cbs.values(), *p.sems.values()): out.append(show(d))
  if p.shared: out.append(show(Shared(p.shared)))
  for t in p.templates.values(): out.append(show(t))
  for f in p.fns.values(): out.append(show(f))
  return "\n".join(out)
