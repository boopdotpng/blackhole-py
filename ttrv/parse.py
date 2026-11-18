"""Front end, part 1: source text -> syntax tree (spec §2, §5). Knows the syntax, not the instruction set.

  parse(src, file) -> [declaration]          show(node) -> source text (round-trips through parse)

Lexing: statements end at a newline or `;`. Newlines are dropped inside () and [], after `,` (a trailing comma
continues the statement) and after `{`. `//` and `/* */` comments. Integers are decimal/hex/binary with `_`; floats
(`1.0`, `2.5e-3`, `inf`) are kept as Python floats and only make sense where an operand takes one.

Parsing is recursive descent with C precedence climbing (spec §5). Every node carries a Loc; expand.py stamps the
macro invocation chain into Loc.via. A device operation is one generic node, Op(ns, name, args): the parser does not
know operand signatures, so `a`, `l0`, `dst[3]`, `srca_vld|srcb_vld`, bare flags like `wait` are all plain
expressions/Names in Arg(None, None, e); named options are Arg(name, '=' | '+=' | '-=', e). ops.py binds them.

A statement starting `ns.` with ns in NAMESPACES is a device op; `x = ns.op ...` is an op with results, while
`x = core.x` (not a namespace) is a dotted read. Template bodies (mop, sfpmacro; also macro bodies, which may be
expanded into templates) accept `label: statement` lines. Errors are Error(loc, id, msg); ids are stable strings."""
from __future__ import annotations
import math, re
from dataclasses import dataclass

class Error(Exception):
  def __init__(self, loc: Loc | None, id: str, msg: str):
    self.loc, self.id, self.msg = loc, id, msg
    where = f"{loc.file}:{loc.line}:{loc.col}" if loc else "<unknown>"
    super().__init__(f"{where}: error[{id}]: {msg}" + ("".join(f"\n  in expansion at {v.file}:{v.line}:{v.col}" for v in loc.via) if loc else ""))

@dataclass(frozen=True)
class Loc:
  file: str
  line: int
  col: int
  via: tuple = ()   # macro invocation sites, innermost first (expand.py)
  def __str__(self):
    return f"{self.file}:{self.line}:{self.col}" + "".join(f"\n  in expansion at {v.file}:{v.line}:{v.col}" for v in self.via)

# ---- tree ----
# Expressions

@dataclass
class Num:
  value: int | float
  loc: Loc = None
  dtype: str | None = None  # explicit integer cast, retained through folding

@dataclass
class Name:
  id: str
  loc: Loc = None

@dataclass
class Attr:      # dotted read: core.x, grid.size, bf16.tile
  base: str
  attr: str
  loc: Loc = None

@dataclass
class Unary:
  op: str
  x: object
  loc: Loc = None

@dataclass
class Bin:
  op: str
  a: object
  b: object
  loc: Loc = None

@dataclass
class Index:     # p[i], buffer[i], dst[row, col]
  base: object
  idx: list
  loc: Loc = None

@dataclass
class Call:      # f(args): an expression (i32, u32, mulh) or a whole statement / assignment value (fn, split)
  fn: str
  args: list
  loc: Loc = None

@dataclass
class Range:     # a..b, only in for/repeat headers, op operands and subscripts
  lo: object
  hi: object
  loc: Loc = None

# Statements

@dataclass
class Arg:       # device-op operand or declaration option; name None = positional
  name: str | None
  op: str | None  # '=', '+=', '-=' for named, None for positional
  value: object
  loc: Loc = None

@dataclass
class Op:
  ns: str
  name: str
  args: list
  loc: Loc = None

@dataclass
class Assign:    # targets (Name | Index) op value; value is an expression, Call or Op
  targets: list
  op: str
  value: object
  loc: Loc = None

@dataclass
class MacroCall:
  name: str
  args: list
  loc: Loc = None

@dataclass
class If:        # also a file-level declaration whose branches hold declarations
  cond: object
  body: list
  orelse: list
  loc: Loc = None

@dataclass
class While:
  cond: object
  body: list
  loc: Loc = None

@dataclass
class For:
  var: str
  lo: object
  hi: object
  body: list
  loc: Loc = None

@dataclass
class Loop:      # count None = until break/return
  count: object
  body: list
  loc: Loc = None

@dataclass
class Repeat:    # compile time; `repeat n` is var None, lo 0, hi n
  var: str | None
  lo: object
  hi: object
  body: list
  loc: Loc = None

@dataclass
class Break:
  loc: Loc = None

@dataclass
class Continue:
  loc: Loc = None

@dataclass
class Fence:
  loc: Loc = None

@dataclass
class Return:
  values: list
  loc: Loc = None

@dataclass
class Label:     # template line
  label: str
  stmt: object
  loc: Loc = None

@dataclass
class Block:     # made by expand.py: a resolved if, one repeat copy, one macro expansion (macro = its name)
  body: list
  macro: str | None = None
  loc: Loc = None

# Declarations

@dataclass
class Type:      # T, T[n], T*, T[] (buffer parameter). count is an expression after parse, an int after expand
  name: str
  count: object = None
  ptr: bool = False
  loc: Loc = None
  buf: bool = False

@dataclass
class Grid:
  n: object
  loc: Loc = None

@dataclass
class Const:
  name: str
  value: object
  loc: Loc = None

@dataclass
class Param:      # param x: T[] (buffer) or param n: u32 in lo..hi (integer value)
  name: str
  type: Type
  opts: list
  loc: Loc = None
  range: object = None   # (lo, hi) expressions for an integer parameter

@dataclass
class TypeDecl:   # type NAME = T
  name: str
  type: Type
  loc: Loc = None

@dataclass
class Storage:   # l1 / cb
  kind: str
  name: str
  type: Type
  opts: list
  loc: Loc = None

@dataclass
class Sem:
  name: str
  hw: str
  opts: list
  loc: Loc = None

@dataclass
class Macro:
  name: str
  params: list
  body: list
  loc: Loc = None

@dataclass
class Fn:
  name: str
  params: list    # [(name, Type)]
  body: list
  nret: int = 0   # filled in by expand
  loc: Loc = None

@dataclass
class Template:  # mop / replay / sfpmacro
  kind: str
  name: str
  opts: list
  body: list
  loc: Loc = None

@dataclass
class Shared:
  body: list
  loc: Loc = None

KEYWORDS = {"if", "else", "while", "for", "loop", "repeat", "break", "continue", "return", "fence"}
NAMESPACES = {"noc", "cb", "tensix", "sem", "unpack", "pack", "math", "sfp", "mop", "replay", "sfpmacro"}
DECLS = {"grid", "const", "type", "param", "l1", "cb", "sem", "macro", "fn", "mop", "replay", "sfpmacro", "shared"}
BINARY = {"||": 1, "&&": 2, "|": 3, "^": 4, "&": 5, "==": 6, "!=": 6, "<": 7, "<=": 7, ">": 7, ">=": 7,
          "<<": 8, ">>": 8, "+": 9, "-": 9, "*": 10, "/": 10, "%": 10}
UNARY_PREC = 11
ASSIGN_OPS = {"=", "+=", "-=", "*=", "&=", "|=", "^=", "<<=", ">>="}
OPTION_OPS = {"=", "+=", "-="}

# ---- lexer ----

@dataclass
class Tok:
  kind: str       # int float name op nl eof
  value: object
  loc: Loc

_TOKEN = re.compile(r"""
   (?P<ws>[ \t\r]+) | (?P<nl>\n|;) | (?P<lc>//[^\n]*) | (?P<bc>/\*.*?\*/) | (?P<badc>/\*)
 | (?P<float>\d[\d_]*\.\d[\d_]*(?:[eE][+-]?\d+)?|\d[\d_]*[eE][+-]?\d+)
 | (?P<int>0[xX][0-9a-fA-F_]+|0[bB][01_]+|\d[\d_]*)
 | (?P<name>[A-Za-z_]\w*)
 | (?P<op><<=|>>=|\.\.|<<|>>|<=|>=|==|!=|&&|\|\||[-+*&|^]=|[-+*/%&|^~!<>=()\[\]{},:.])
""", re.X | re.S)

def lex(src: str, file: str = "<input>") -> list[Tok]:
  out, pos, line, bol, depth = [], 0, 1, 0, 0
  while pos < len(src):
    m = _TOKEN.match(src, pos)
    loc = Loc(file, line, pos - bol + 1)
    if m is None: raise Error(loc, "lex.char", f"unexpected character {src[pos]!r}")
    kind, text = m.lastgroup, m.group()
    if kind == "badc": raise Error(loc, "lex.comment", "unterminated /* comment")
    if kind in ("float", "int") and m.end() < len(src) and (src[m.end()].isalnum() or src[m.end()] == "_"):
      raise Error(loc, "lex.number", f"malformed number starting {text!r}")
    if kind == "nl":
      prev = out[-1] if out else None
      if depth == 0 and prev and prev.kind != "nl" and not (prev.kind == "op" and prev.value in (",", "{")):
        out.append(Tok("nl", text, loc))
    elif kind == "int": out.append(Tok("int", int(text.replace("_", ""), 0), loc))
    elif kind == "float": out.append(Tok("float", float(text.replace("_", "")), loc))
    elif kind == "name": out.append(Tok("name", text, loc))
    elif kind == "op":
      depth += text in "([" and len(text) == 1
      depth -= text in ")]" and len(text) == 1 and depth > 0
      out.append(Tok("op", text, loc))
    nls = text.count("\n")
    if nls: line, bol = line + nls, m.start() + text.rindex("\n") + 1
    pos = m.end()
  out.append(Tok("eof", None, Loc(file, line, pos - bol + 1)))
  return out

# ---- parser ----

class Parser:
  def __init__(self, toks): self.toks, self.i = toks, 0
  def peek(self, k=0): return self.toks[min(self.i + k, len(self.toks) - 1)]
  def next(self):
    t = self.toks[self.i]
    self.i += t.kind != "eof"
    return t
  def at(self, v, k=0):
    t = self.peek(k)
    return t.kind == "op" and t.value == v
  def at_word(self, w, k=0):
    t = self.peek(k)
    return t.kind == "name" and t.value == w
  def at_end(self): return self.peek().kind in ("nl", "eof") or self.at("}")
  def fail(self, msg, tok=None, id="parse.syntax"):
    tok = tok or self.peek()
    got = {"nl": "end of statement", "eof": "end of file"}.get(tok.kind, repr(tok.value))
    raise Error(tok.loc, id, f"{msg}, got {got}")
  def expect(self, v):
    if not self.at(v): self.fail(f"expected {v!r}")
    return self.next()
  def name(self, what="a name"):
    if self.peek().kind != "name": self.fail(f"expected {what}")
    return self.next().value
  def skip_nl(self):
    while self.peek().kind == "nl": self.next()
  def end_stmt(self):
    if self.at("}") or self.peek().kind == "eof": return
    if self.peek().kind != "nl": self.fail("expected end of statement (newline or ';')")
    self.skip_nl()

  def block(self, item):
    open_ = self.expect("{")
    self.skip_nl()
    body = []
    while not self.at("}"):
      if self.peek().kind == "eof": raise Error(open_.loc, "parse.unclosed", "unclosed '{'")
      body.append(item())
      self.end_stmt()
    self.next()
    return body

  # -- declarations --

  def decl(self):
    t = self.peek()
    if t.kind != "name" or t.value not in DECLS | {"if"}: self.fail("expected a declaration")
    w, loc = self.next().value, t.loc
    if w == "if": return self.if_(self.decl, loc)
    if w == "grid": return Grid(self.expr(), loc)
    if w == "shared": return Shared(self.block(self.stmt), loc)
    name = self.name(f"a name after {w!r}")
    if w == "const":
      self.expect("=")
      return Const(name, self.expr(), loc)
    if w == "type":
      self.expect("=")
      return TypeDecl(name, self.type(), loc)
    if w in ("param", "l1", "cb"):
      self.expect(":")
      ty = self.type()
      rng = None
      if w == "param" and self.peek().kind == "name" and self.peek().value == "in":
        self.next()
        rng = self.range()
      opts = self.opts()
      return Param(name, ty, opts, loc, rng) if w == "param" else Storage(w, name, ty, opts, loc)
    if w == "sem":
      self.expect("=")
      return Sem(name, self.name("a hardware semaphore name"), self.opts(), loc)
    if w == "macro":
      return Macro(name, self.paren_list(lambda: self.name("a macro parameter")), self.block(lambda: self.stmt(True)), loc)
    if w == "fn":
      return Fn(name, self.paren_list(self.fn_param), self.block(self.stmt), loc=loc)
    return Template(w, name, self.opts(), self.block(lambda: self.stmt(w != "replay")), loc)

  def paren_list(self, item):
    self.expect("(")
    out = []
    while not self.at(")"):
      out.append(item())
      if not self.at(")"): self.expect(",")
    self.next()
    return out

  def fn_param(self):
    loc, name = self.peek().loc, self.name("a parameter name")
    if self.at(":"):
      self.next()
      return name, self.type()
    return name, Type("u32", loc=loc)

  def type(self):
    loc, name = self.peek().loc, self.name("a type")
    count, ptr, buf = None, False, False
    if self.at("["):
      self.next()
      if self.at("]"): buf = True
      else: count = self.expr()
      self.expect("]")
    if self.at("*"):
      self.next()
      ptr = True
    return Type(name, count, ptr, loc, buf)

  def opts(self):
    if not self.at(","): return []
    self.next()
    return self.args()

  # -- statements --

  def stmt(self, labels=False):
    t = self.peek()
    if t.kind != "name": self.fail("expected a statement")
    w, loc = t.value, t.loc
    if labels and self.at(":", 1):
      self.next(); self.next()
      return Label(w, self.stmt(False), loc)
    if w in KEYWORDS:
      self.next()
      if w == "if": return self.if_(lambda: self.stmt(labels), loc)
      if w == "while":
        return While(self.expr(), self.block(lambda: self.stmt(labels)), loc)
      if w == "for":
        var = self.name("a loop variable")
        if not self.at_word("in"): self.fail("expected 'in'")
        self.next()
        lo, hi = self.range()
        return For(var, lo, hi, self.block(lambda: self.stmt(labels)), loc)
      if w == "loop":
        count = None if self.at("{") else self.expr()
        return Loop(count, self.block(lambda: self.stmt(labels)), loc)
      if w == "repeat":
        if self.peek().kind == "name" and self.at_word("in", 1):
          var = self.next().value
          self.next()
          lo, hi = self.range()
        else: var, lo, hi = None, Num(0, loc), self.expr()
        return Repeat(var, lo, hi, self.block(lambda: self.stmt(labels)), loc)
      if w == "break": return Break(loc)
      if w == "continue": return Continue(loc)
      if w == "fence": return Fence(loc)
      if w == "return": return Return([] if self.at_end() else self.expr_list(), loc)
      self.fail("unexpected 'else'", t)
    if w in NAMESPACES and self.at(".", 1): return self.op()
    if self.at("!", 1) and self.at("(", 2):
      self.next(); self.next()
      return MacroCall(w, self.paren_list(self.expr), loc)
    targets = self.expr_list()
    if self.peek().kind == "op" and self.peek().value in ASSIGN_OPS:
      op = self.next().value
      for e in targets:
        if not isinstance(e, (Name, Index)): raise Error(e.loc, "parse.target", "can only assign to a name or p[i]")
      value = self.op() if self.at_op() else self.expr()
      if len(targets) > 1 and (op != "=" or not isinstance(value, (Call, Op))):
        raise Error(loc, "parse.multi", "several targets need `=` and a call or device operation on the right")
      return Assign(targets, op, value, loc)
    if len(targets) == 1 and isinstance(targets[0], Call): return targets[0]
    self.fail("expected an assignment, call, device operation or keyword", t)

  def if_(self, item, loc):
    cond, body, orelse = self.expr(), self.block(item), []
    save = self.i
    self.skip_nl()
    if self.at_word("else"):
      eloc = self.next().loc
      if self.at_word("if"):
        self.next()
        orelse = [self.if_(item, eloc)]
      else: orelse = self.block(item)
    else: self.i = save
    return If(cond, body, orelse, loc)

  def at_op(self): return self.peek().kind == "name" and self.peek().value in NAMESPACES and self.at(".", 1)

  def op(self):
    loc, ns = self.peek().loc, self.next().value
    self.expect(".")
    name = self.name("an operation name")
    return Op(ns, name, [] if self.at_end() else self.args(), loc)

  def args(self):
    out = [self.arg()]
    while self.at(","):
      self.next()
      out.append(self.arg())
    return out

  def arg(self):
    t = self.peek()
    if t.kind == "name" and self.peek(1).kind == "op" and self.peek(1).value in OPTION_OPS:
      self.next()
      return Arg(t.value, self.next().value, self.expr_or_range(), t.loc)
    return Arg(None, None, self.expr_or_range(), t.loc)

  # -- expressions --

  def expr_list(self):
    out = [self.expr()]
    while self.at(","):
      self.next()
      out.append(self.expr())
    return out

  def range(self):
    lo = self.expr()
    self.expect("..")
    return lo, self.expr()

  def expr_or_range(self):
    e = self.expr()
    if not self.at(".."): return e
    self.next()
    return Range(e, self.expr(), e.loc)

  def expr(self, minp=1):
    lhs = self.unary()
    while (t := self.peek()).kind == "op" and BINARY.get(t.value, 0) >= minp:
      self.next()
      lhs = Bin(t.value, lhs, self.expr(BINARY[t.value] + 1), t.loc)
    return lhs

  def unary(self):
    t = self.peek()
    if t.kind == "op" and t.value in ("-", "~", "!"):
      self.next()
      return Unary(t.value, self.unary(), t.loc)
    e = self.primary()
    while self.at("["):
      self.next()
      idx = [self.expr_or_range()]
      while self.at(","):
        self.next()
        idx.append(self.expr_or_range())
      self.expect("]")
      e = Index(e, idx, e.loc)
    return e

  def primary(self):
    t = self.next()
    if t.kind in ("int", "float"): return Num(t.value, t.loc)
    if t.kind == "name":
      if t.value in KEYWORDS: self.fail(f"unexpected keyword {t.value!r}", t)
      if t.value == "inf": return Num(math.inf, t.loc)
      if self.at("("): return Call(t.value, self.paren_list(self.expr), t.loc)
      if self.at("."):
        self.next()
        return Attr(t.value, self.name("an attribute"), t.loc)
      return Name(t.value, t.loc)
    if t.kind == "op" and t.value == "(":
      e = self.expr()
      self.expect(")")
      return e
    self.fail("expected an expression", t)

def parse(src: str, file: str = "<input>") -> list:
  p = Parser(lex(src, file))
  p.skip_nl()
  out = []
  while p.peek().kind != "eof":
    out.append(p.decl())
    p.end_stmt()
  return out

# ---- printer ----

def show_expr(e, p=0) -> str:
  match e:
    case Num(value=v):
      if isinstance(v, float): return ("-inf" if v < 0 else "inf") if math.isinf(v) else repr(v)
      return str(v) if -4096 < v < 4096 else hex(v) if v >= 0 else f"-{hex(-v)}"
    case Name(id=n): return n
    case Attr(): return f"{e.base}.{e.attr}"
    case Unary():
      s = e.op + show_expr(e.x, UNARY_PREC)
      return f"({s})" if p > UNARY_PREC else s
    case Bin():
      q = BINARY[e.op]
      s = f"{show_expr(e.a, q)} {e.op} {show_expr(e.b, q + 1)}"
      return f"({s})" if q < p else s
    case Index(): return f"{show_expr(e.base, UNARY_PREC + 1)}[{', '.join(show_expr(i) for i in e.idx)}]"
    case Call(): return f"{e.fn}({', '.join(show_expr(a) for a in e.args)})"
    case Range(): return f"{show_expr(e.lo, 1)}..{show_expr(e.hi, 1)}"
    case Op(): return show_op(e)
  raise TypeError(f"not an expression: {e!r}")

def show_arg(a: Arg) -> str: return show_expr(a.value) if a.name is None else f"{a.name}{a.op}{show_expr(a.value)}"
def show_args(args, lead=" ") -> str: return lead + ", ".join(map(show_arg, args)) if args else ""
def show_op(o: Op) -> str: return f"{o.ns}.{o.name}{show_args(o.args)}"
def show_type(t: Type) -> str:
  count = "[]" if t.buf else "" if t.count is None else f"[{t.count if isinstance(t.count, int) else show_expr(t.count)}]"
  return f"{t.name}{count}{'*' if t.ptr else ''}"

def show(node, ind: int = 0) -> str:
  """Source text for a declaration, statement or list of them. Block (expand.py) prints as a bare { } with a comment."""
  if isinstance(node, list): return "\n".join(show(n, ind) for n in node)
  pad = "  " * ind
  def blk(body): return "{\n" + "".join(show(s, ind + 1) + "\n" for s in body) + pad + "}"
  match node:
    case Assign(): return f"{pad}{', '.join(show_expr(t) for t in node.targets)} {node.op} {show_expr(node.value)}"
    case Op(): return pad + show_op(node)
    case Call(): return pad + show_expr(node)
    case MacroCall(): return f"{pad}{node.name}!({', '.join(show_expr(a) for a in node.args)})"
    case If():
      s = f"{pad}if {show_expr(node.cond)} {blk(node.body)}"
      if len(node.orelse) == 1 and isinstance(node.orelse[0], If): return s + " else " + show(node.orelse[0], ind).lstrip()
      return s + (f" else {blk(node.orelse)}" if node.orelse else "")
    case While(): return f"{pad}while {show_expr(node.cond)} {blk(node.body)}"
    case For(): return f"{pad}for {node.var} in {show_expr(node.lo, 1)}..{show_expr(node.hi, 1)} {blk(node.body)}"
    case Loop(): return f"{pad}loop {'' if node.count is None else show_expr(node.count) + ' '}{blk(node.body)}"
    case Repeat():
      head = show_expr(node.hi) if node.var is None else f"{node.var} in {show_expr(node.lo, 1)}..{show_expr(node.hi, 1)}"
      return f"{pad}repeat {head} {blk(node.body)}"
    case Break(): return pad + "break"
    case Continue(): return pad + "continue"
    case Fence(): return pad + "fence"
    case Return(): return pad + "return" + (" " + ", ".join(show_expr(v) for v in node.values) if node.values else "")
    case Label(): return f"{pad}{node.label}: {show(node.stmt).lstrip()}"
    case Block(): return pad + (f"// {node.macro}!\n{pad}" if node.macro else "") + blk(node.body)
    case Grid(): return f"{pad}grid {show_expr(node.n) if not isinstance(node.n, int) else node.n}"
    case Const(): return f"{pad}const {node.name} = {show_expr(node.value)}"
    case Param():
      rng = "" if node.range is None else f" in {show_expr(node.range[0], 1)}..{show_expr(node.range[1], 1)}"
      return f"{pad}param {node.name}: {show_type(node.type)}{rng}{show_args(node.opts, ', ')}"
    case TypeDecl(): return f"{pad}type {node.name} = {show_type(node.type)}"
    case Storage(): return f"{pad}{node.kind} {node.name}: {show_type(node.type)}{show_args(node.opts, ', ')}"
    case Sem(): return f"{pad}sem {node.name} = {node.hw}{show_args(node.opts, ', ')}"
    case Macro(): return f"{pad}macro {node.name}({', '.join(node.params)}) {blk(node.body)}"
    case Fn():
      ps = ", ".join(n if t.name == "u32" and not t.ptr and t.count is None else f"{n}: {show_type(t)}" for n, t in node.params)
      return f"{pad}fn {node.name}({ps}) {blk(node.body)}"
    case Template(): return f"{pad}{node.kind} {node.name}{show_args(node.opts, ', ')} {blk(node.body)}"
    case Shared(): return f"{pad}shared {blk(node.body)}"
  raise TypeError(f"cannot show {node!r}")
