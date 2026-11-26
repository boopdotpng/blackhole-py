"""UIR: the text form of a UOp graph, one line per UOp: `%id = op src src key=value  # dtype shape` (ported from tinygrad).

  %0 = buffer 2048 name=x dtype=bf16  # bf16 (2048,)
  %1 = cast %0 dtype=fp32  # fp32 (2048,)
  %2 = mul %1 %1  # fp32 (2048,)
  %3 = reduce %2 op=add n=1  # fp32

srcs are %ids or inline literals: a CONST (1, 2.5, -inf, true) or an all-CONST STACK ([1 2]) has no line. args are key=value
after the srcs: a literal, a bare word, a 'string', a [list], a %id, or a `python object`. dtype and shape are derived, so they
are a comment. parse_uir(render_uir(x)) is x, since UOps are hash-consed, when every python object's repr evaluates back to it.
parse_uir also reads hand-written UIR: %names, nested (op ...), [stacks] of expressions and {scoped blocks}.
"""
import re, math, ast, importlib
from collections import deque
from enum import Enum
from dataclasses import fields, is_dataclass
from typing import Any, Callable
from . import dtype as dtype_mod, uop as uop_mod
from .dtype import DType, dtypes
from .uop import BufferArg, CallInfo, KernelArg, NativeInfo, Ops, ParamArg, RangeArg, UOp, _fmt_sint

# ***** render *****

_ansi = {"red": 31, "green": 32, "yellow": 33, "blue": 34, "magenta": 35, "cyan": 36, "gray": 90}
_colors = {Ops.REDUCE: "red", Ops.BARRIER: "red",
           Ops.INDEX: "green", Ops.STACK: "green", **{x: "green" for x in uop_mod.GroupOp.Movement},
           Ops.STAGE: "yellow", **{x: "yellow" for x in uop_mod.GroupOp.ALU},
           Ops.BUFFER: "blue", Ops.ALLOC: "blue", Ops.LOAD: "blue", Ops.STORE: "blue", Ops.SPECIAL: "blue",
           Ops.RANGE: "magenta", Ops.IF: "magenta", Ops.NATIVE: "magenta", Ops.CAST: "magenta", Ops.BITCAST: "magenta",
           Ops.CALL: "cyan", Ops.PARAM: "cyan", Ops.LINEAR: "cyan",
           Ops.AFTER: "gray", Ops.END: "gray", Ops.BACKEDGE: "gray", Ops.CONST: "gray",
           Ops.SOURCE: "gray", Ops.BINARY: "gray", Ops.PROGRAM: "gray"}

def _colored(s: str, color: str | None) -> str:
  return s if color is None else f"\x1b[{_ansi[color]}m{s}\x1b[0m"

def ansistrip(s: str) -> str: return re.sub("\x1b\\[(K|.*?m)", "", s)

# keys whose value is written by its name: dtype=fp32 op=add
_named_keys = {"dtype", "op"}
_keywords = {"true", "false", "inf", "nan"}
# ops whose arg is one value with a name, ops whose arg is a dataclass written as key=value per field, ops whose arg is a tuple
_arg_key = {Ops.SPECIAL: "name", Ops.CAST: "dtype", Ops.BITCAST: "dtype"}
_struct_args: dict[Ops, type] = {Ops.BUFFER: BufferArg, Ops.ALLOC: BufferArg, Ops.PARAM: ParamArg, Ops.RANGE: RangeArg,
                                 Ops.CALL: CallInfo, Ops.NATIVE: NativeInfo}
_tuple_keys = {Ops.REDUCE: ("op", "n")}

def _inline(u: UOp) -> bool:
  return u.op is Ops.CONST or (u.op is Ops.STACK and len(u.src) > 0 and all(s.op is Ops.CONST for s in u.src))

def _const_str(x: UOp) -> str:
  v = x.arg
  return str(v).lower() if isinstance(v, bool) or (isinstance(v, float) and not math.isfinite(v)) else repr(v)

def _val(v: Any, named: bool, ref: Callable[[UOp], str | None]) -> str:
  """literals and one-word strings are bare, tuples are [a b], a UOp with a line is its %id, any other python object is `module:repr`"""
  if named and isinstance(v, (Enum, DType)): return v.name.lower() if isinstance(v, Ops) else v.name
  if isinstance(v, bool): return str(v).lower()
  if type(v) is int: return repr(v)
  if type(v) is float: return str(v).lower() if not math.isfinite(v) else repr(v)
  if isinstance(v, tuple): return "[" + " ".join(_val(x, named, ref) for x in v) + "]"
  if isinstance(v, UOp) and (r := ref(v)) is not None: return r
  if isinstance(v, str): return v if re.fullmatch(r"[A-Za-z_][\w:.,+\-]*", v) and v not in _keywords else repr(v)
  mod = "" if type(v).__module__ in ("builtins", dtype_mod.__name__, uop_mod.__name__) else type(v).__module__ + ":"
  r = f"{type(v).__name__}.{v.name}" if isinstance(v, Enum) else repr(v)
  return "`" + (mod + r).replace("\n", " ").replace("`", "\\x60") + "`"

def _fields_str(a: Any, ref: Callable[[UOp], str | None], first: bool) -> str:
  ret = []
  for i, f in enumerate(fields(a)):
    v = getattr(a, f.name)
    # a default is left out, except the first field if first. compared by repr, since == of a UOp builds a UOp
    if repr(v) == repr(f.default) and not (first and i == 0): continue
    ret.append(f"{f.name}={_val(v, f.name in _named_keys, ref)}")
  return " ".join(ret)

def _render_arg(x: UOp, ref: Callable[[UOp], str | None] = lambda _: None) -> str:
  """the args, written after the srcs"""
  if (a := x.arg) is None or x.op is Ops.CONST: return ""
  if (keys := _tuple_keys.get(x.op)) is not None: return " ".join(f"{k}={_val(v, k in _named_keys, ref)}" for k, v in zip(keys, a))
  if type(a) is _struct_args.get(x.op) or (x.op is Ops.SINK and type(a) is KernelArg):
    # the first field is always written, so a default arg isn't None. a CALL's arg is always a CallInfo
    return _fields_str(a, ref, first=x.op is not Ops.CALL)
  key = _arg_key.get(x.op, "arg")
  return f"{key}={_val(a, key in _named_keys, ref)}"

def _order(root: UOp | list[UOp]) -> list[UOp]:
  if isinstance(root, UOp): return [u for u in root.toposort(enter_calls=True) if not _inline(u)]
  # a list (e.g. a linearized program) keeps its order; srcs it doesn't contain get lines just before their first use
  seen: dict[UOp, None] = {}
  for item in root:
    for u in item.toposort(enter_calls=True):
      if u not in seen and not _inline(u): seen[u] = None
  return list(seen)

def render_uir(root: UOp | list[UOp], color: bool = False, types: bool = True) -> str:
  """one line per UOp: %id = op src src key=value  # dtype shape"""
  nodes = _order(root)
  table = {u: i for i, u in enumerate(nodes)}
  def src_str(u: UOp) -> str:
    if not _inline(u): return f"%{table[u]}"
    return _const_str(u) if u.op is Ops.CONST else "[" + " ".join(src_str(s) for s in u.src) + "]"
  lines = []
  for i, u in enumerate(nodes):
    # a UOp in an arg is its %id if it has an earlier line
    arg = _render_arg(u, lambda v: f"%{table[v]}" if table.get(v, i) < i else None)
    op_str = u.op.name.lower()
    line = " ".join([f"%{i} = {_colored(op_str, _colors.get(u.op)) if color else op_str}", *map(src_str, u.src)] + ([arg] if arg else []))
    if types and (u.dtype is not dtypes.void or u.shape not in (None, ())):
      line += f"  # {u.dtype.name}" + (f" {_fmt_sint(u.shape)}" if u.shape not in (None, ()) else "")
    lines.append(line)
  # an inline root has no line of its own, so it's a literal value
  if isinstance(root, UOp) and _inline(root): lines.append(f"%{len(nodes)} = {src_str(root)}")
  return "\n".join(lines)

# ***** parse *****

# a token is a comment, an assignment '%name =', a key=, a %ref, a bracket, a quoted string, a `python object`, or a bare word
_tokens = re.compile(r"""#[^\n]*|%\w+\s*=|\w+=|%\w+|[\[\](){}]|'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]*`|[^\s\[\](){}#]+""", re.ASCII)
_ops = {o.name.lower(): o for o in Ops}
_named_parse: dict[str, Callable[[str], Any]] = {"dtype": dtypes.from_name, "op": lambda v: _ops[v]}

def _lit(t: str) -> Any:
  """literals: true false 0x2a -3 1.5 1e+20 -inf nan. anything else is a bare word"""
  if t in ("true", "false"): return t == "true"
  if re.fullmatch(r"-?0x[0-9a-fA-F]+", t): return int(t, 16)
  if re.fullmatch(r"-?[0-9]+", t): return int(t)
  if re.fullmatch(r"-?[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?|-?inf|nan", t): return float(t)
  return t

def _eval(expr: str) -> Any:
  """a `python object`: a repr, evaluated with the names in compiler.dtype, compiler.uop and the module before a ':'. NOTE: this is eval"""
  ns = {**vars(dtype_mod), **vars(uop_mod), "inf": math.inf, "nan": math.nan}
  if (m := re.match(r"([\w.]+):(?!=)", expr)):
    ns.update(vars(importlib.import_module(m[1])))
    expr = expr[m.end():]
  return eval(expr, ns)  # pylint: disable=eval-used

def _build(name: str, srcs: tuple[UOp, ...], kv: dict[str, Any]) -> UOp:
  """make the UOp for `op srcs key=value`. any op's arg can be a lone arg="""
  if (op := _ops.get(name)) is None: raise ValueError(f"unknown op {name!r}")
  struct = _struct_args.get(op) or (KernelArg if op is Ops.SINK and kv and set(kv) != {"arg"} else None)
  keys = set(_tuple_keys.get(op, ())) or ({f.name for f in fields(struct)} if struct else {_arg_key.get(op, "arg")})
  if set(kv) - keys and set(kv) != {"arg"}: raise ValueError(f"{name} has no {sorted(set(kv) - keys)}, its args are {sorted(keys)}")
  arg: Any = None
  if set(kv) == {"arg"}: arg = kv["arg"]
  elif op in _tuple_keys: arg = tuple(kv[k] for k in _tuple_keys[op])
  elif struct is not None and (kv or op is Ops.CALL): arg = struct(**kv)   # a CALL always has a CallInfo
  elif kv: arg = kv[_arg_key[op]]
  return UOp(op, srcs, arg)

def _const(t: str) -> UOp | None: return None if isinstance(lv := _lit(t), str) else UOp.const(lv)

def parse_uir(text: str) -> UOp:
  """parse UIR text into a UOp graph: render_uir's output, or hand-written UIR.
  a program is `%name = value` assignments and its root is the last one. a value is `op srcs key=value` (only right after
  the `=`), `(op srcs key=value)`, `[values]` for a STACK, `{assignments}` for the last of a scoped block, a %name, or a
  literal. NOTE: a `python object` is eval'd, only parse UIR you trust"""
  toks = deque(t for t in _tokens.findall(ansistrip(text)) if not t.startswith("#"))
  def is_assign(t: str) -> bool: return t[0] == "%" and t[-1] == "="
  def at_end() -> bool: return not toks or toks[0] in (")", "]", "}") or is_assign(toks[0])
  def pop(what: str) -> str:
    if not toks: raise ValueError(f"expected {what}, got end of input")
    return toks.popleft()
  def ref(names: dict[str, UOp | None], t: str) -> UOp:
    if (u := names.get(t)) is None: raise ValueError(f"{t} is not defined")
    return u
  def attr(names: dict[str, UOp | None], k: str) -> Any:
    t = pop(f"a value for {k}=")
    if t in ("(", ")", "]", "{", "}"): raise ValueError(f"expected a value for {k}=, got {t!r}")
    if t[0] in "`'\"" and (len(t) < 2 or t[-1] != t[0]): raise ValueError(f"unterminated {t[0]} in {k}=")
    if t == "[":
      ret = []
      while toks and toks[0] != "]": ret.append(attr(names, k))
      pop("']'")
      return tuple(ret)
    if t[0] == "`": return _eval(t[1:-1])
    if t[0] in "'\"": return ast.literal_eval(t)
    if t[0] == "%": return ref(names, t)
    return _named_parse.get(k, _lit)(t)
  def expr(names: dict[str, UOp | None], name: str, close: str | None) -> UOp:
    srcs: list[UOp] = []
    while not at_end() and not toks[0].endswith("="): srcs.append(value(names))
    kv: dict[str, Any] = {}
    while not at_end():
      k = pop("key=")
      if not k.endswith("="): raise ValueError(f"srcs must come before key=value args in {name}, got {k!r}")
      if k[:-1] in kv: raise ValueError(f"{name} has {k} twice")
      kv[k[:-1]] = attr(names, k[:-1])
    if close is not None and pop(repr(close)) != close: raise ValueError(f"expected {close!r} to end {name}")
    return _build(name, tuple(srcs), kv)
  def value(names: dict[str, UOp | None], bare=False) -> UOp:
    t = pop("a value")
    if t == "{": return scope(dict(names), "}")
    if t == "(": return expr(names, pop("an op"), ")")
    if t == "[":
      srcs = []
      while toks and toks[0] != "]": srcs.append(value(names))
      pop("']'")
      return UOp.stack(*srcs)
    if t[0] == "%": return ref(names, t)
    if (c := _const(t)) is not None: return c
    if bare and re.fullmatch(r"[a-z_0-9]+", t): return expr(names, t, None)   # an assignment's value can be a bare op
    raise ValueError(f"{t!r} is not a %name or a literal" + (f", write ({t} ...)" if t in _ops else ""))
  def scope(names: dict[str, UOp | None], close: str | None) -> UOp:
    root: UOp | None = None
    while toks and toks[0] != "}":
      t = pop("'%name ='")
      if not is_assign(t): raise ValueError(f"expected '%name =', got {t!r}")
      name = t[:-1].rstrip()
      if name in names: raise ValueError(f"{name} is already defined")
      names[name] = None   # defined, so its value can't define it again, but not usable until its value is parsed
      names[name] = root = value(names, bare=True)
    if (toks.popleft() if toks else None) != close: raise ValueError(f"expected {close or 'end of input'!r}")
    if root is None: raise ValueError("expected an assignment")
    return root
  return scope({}, None)
