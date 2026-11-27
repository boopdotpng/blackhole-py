import functools, itertools, math
from collections import defaultdict
from typing import Any
from .dtype import DType, Invalid, can_lossless_cast, dtypes, least_upper_dtype
from .ops import exec_alu
from .uop import BottomUpGate, GroupOp, Ops, PatternMatcher, UOp, UPat, graph_rewrite, identity_element

def _ceildiv(a: int, b: int) -> int: return -((-a) // b)
def _partition(xs, pred):
  a, b = [], []
  for x in xs: (a if pred(x) else b).append(x)
  return a, b
def _dedup(xs): return list(dict.fromkeys(xs))
def _all_same(xs): return len(xs) <= 1 or all(x == xs[0] for x in xs[1:])
def _is_num(c: UOp, v: Any) -> bool: return c.is_const and not c.is_invalid and type(c.val) is not bool and c.val == v
def _fits(x: UOp, v: Any) -> bool: return not (x.dtype.is_int and x.dtype.is_signed and x.dtype is not dtypes.weakint) or x.dtype.min <= v <= x.dtype.max
def _no_overflow(u: UOp) -> bool: return _fits(u, u.vmin) and _fits(u, u.vmax)

# ---- div and mod symbolic (ported from tinygrad/uop/divandmod.py) ----

@functools.cache
def fold_divmod_general(d: UOp) -> UOp | None:
  x, y = d.src
  if x.is_invalid or y.is_invalid: return None
  if y.vmin == y.vmax == 0: raise ZeroDivisionError(f"{'Division' if d.op is Ops.DIV else 'Mod'} by zero trying to rewrite {x.alu(d.op, y)}")
  if d.op is Ops.MOD and (xdiv := x // y).vmin == xdiv.vmax: return x - xdiv.vmin * y

  x_peeled, const = x.pop_const()
  if not isinstance(const, int) or isinstance(const, bool): return None
  uops_no_const = list(x_peeled.split_uop(Ops.ADD))

  # Constant denominator rules (y is scalar const > 0)
  if y.op is Ops.CONST and isinstance(y.arg, int) and not isinstance(y.arg, bool) and (c := y.arg) > 0:
    # nested_div: (x % (k*c)) // c -> (x // c) % k
    if d.op is Ops.DIV and x.op is Ops.MOD and (k := x.src[1].divides(c)) is not None and k.vmin > 0:
      return (x.src[0] // y) % k

    # remove_nested_mod in sum: (a % 4 + b) % 2 -> (a + b) % 2
    if d.op is Ops.MOD:
      new_xs = [u.src[0] if u.op is Ops.MOD and u.src[1].divides(c) is not None else u for u in uops_no_const]
      if new_xs != uops_no_const: return (UOp.usum(*new_xs) + const) % y

    # exact division: (q*c + k) // c -> q + k // c
    if d.op is Ops.DIV and (q := x_peeled.divides(c)) is not None: return q + const // c

    decomp = [(u.divides(f := u.const_factor()), f) for u in uops_no_const]
    if all(t is not None for t, _ in decomp):
      terms, factors = zip(*decomp)
      # fold_divmod_congruence: fold if congruent to an expression whose range stays in one [k*c, (k+1)*c) bucket
      ties = [i for i, (f, v) in enumerate(zip(factors, terms)) if (f % c) * 2 == c and v.vmin != v.vmax]
      rem_choices = [(r, r - c) if len(terms) == 1 or ties == [i] else (min(r, r - c, key=abs),) for i, r in enumerate(f % c for f in factors)]
      for rems in itertools.product(*rem_choices):
        ends = [sorted((r * v.vmin, r * v.vmax)) for r, v in zip(rems, terms)]
        lo, hi = sum(e[0] for e in ends) + const % c, sum(e[1] for e in ends) + const % c
        if lo // c == hi // c:
          if d.op is Ops.MOD:
            parts = [r * v for r, v in zip(rems, terms) if r != 0]
            k = const % c - (lo // c) * c
            return (UOp.usum(*parts) + k) if parts else x.const_like(k)
          parts = [((f - r) // c) * v for f, r, v in zip(factors, rems, terms) if (f - r) // c != 0]
          k = const // c + lo // c
          return (UOp.usum(*parts) + k) if parts else x.const_like(k)

      # nest_by_factor: x // c -> (x // f) // (c // f), x % c -> ((x // f) % (c // f)) * f + x % f
      results = []
      for div in {abs(f) for f in (*factors, math.gcd(*factors, c)) if 1 < abs(f) < c and c % f == 0}:
        if (newxs := fold_divmod_general(x // div)) is not None:
          if d.op is Ops.DIV:
            results.append((len(newxs.backward_slice), newxs // (c // div)))
          elif x.vmin >= 0 and newxs.vmin >= 0:
            b_parts = [(f % div) * t for f, t in zip(factors, terms) if f % div]
            if const % div: b_parts.append(x.const_like(const % div))
            b = UOp.usum(*b_parts) if b_parts else x.const_like(0)
            if 0 <= b.vmin and b.vmax < div:
              r_expr = (newxs % (c // div)) * div + b
              results.append((len(r_expr.backward_slice), r_expr))
      if results: return min(results, key=lambda r: r[0])[1]

  # Variable denominator / fallback rules
  all_uops = list(x.split_uop(Ops.ADD))
  gcd = UOp.gcd(*all_uops, y).simplify()
  if not (gcd.op is Ops.CONST and gcd.arg == 1):
    if (nx := x.divide_exact(gcd)) is not None and (ny := y.divide_exact(gcd)) is not None:
      ret = nx.alu(d.op, ny)
      return ret * gcd if d.op is Ops.MOD else ret

  if y.vmin < 0 or x.vmin < 0: return None
  quo, rem = [], []
  for u in all_uops:
    if (q := u.divide_exact(y)) is not None: quo.append(q)
    elif y.op is Ops.CONST and isinstance(y.arg, int) and (cf := u.const_factor()) % y.arg != cf and (uq := u.divides(cf)) is not None:
      rem.append(uq * (cf % y.arg))
      quo.append(uq * (cf // y.arg) if d.op is Ops.DIV else u.const_like(0))
    else: rem.append(u)

  if not quo: return None
  new_x = UOp.usum(*rem) if rem else x.const_like(0)
  if new_x.vmin < 0: return None
  return new_x % y if d.op is Ops.MOD else new_x // y + UOp.usum(*quo)

div_and_mod_symbolic = PatternMatcher([
  # (x // c + a) // d -> (x + a * c) // (c * d) for c > 0, d > 0
  ((UPat.var("x", dtypes.weakint) // UPat.cvar("c") + UPat.cvar("a")) // UPat.cvar("d"),
   lambda x, c, a, d: (x + a.arg * c.arg) // (c.arg * d.arg) if c.vmin > 0 and d.vmin > 0 else None),
  # (x + c) // d -> (x + c%d) // d + c//d ; (x + c) % d -> (x + c%d) % d
  (UPat((Ops.DIV, Ops.MOD), src=(UPat.var("x", dtypes.weakint) + UPat.cvar("c"), UPat.cvar("d")), name="n"),
   lambda n, x, c, d: None if d.arg == 0 or c.arg % d.arg == c.arg else
     (x + c.arg % d.arg) // d + c.arg // d.arg if n.op is Ops.DIV else (x + c.arg % d.arg) % d),
  # general div/mod folding on weakint
  (UPat((Ops.DIV, Ops.MOD), dtype=dtypes.weakint, name="d"), fold_divmod_general),
])

# ---- Invalid propagation ----

invalid_pat = UPat(Ops.CONST, arg=Invalid, name="i")
invalid_gate = UPat.var("cond").where(UPat.var("x"), invalid_pat)

def lift_reduce_gate(red: UOp, cond: UOp, x: UOp, i: UOp) -> UOp | None:
  op, horizontal = red.arg
  if horizontal != 0: return None
  closed = {rr for r in red.src[1:] for rr in r.ranges}
  keep, lift = _partition(cond.split_uop(Ops.AND), lambda c: any(rr in c.ranges for rr in closed))
  inner = UOp.uand(*keep).where(x, x.const_like(identity_element(op, red.dtype))) if keep else x
  ret = red.replace(src=(inner, *red.src[1:]))
  return UOp.uand(*lift).where(ret, i) if lift else ret

pm_data_invalid = PatternMatcher([
  (UPat(GroupOp.Unary | {Ops.CAST, Ops.BITCAST}, src=(invalid_pat,)), lambda i: i),
  (UPat(GroupOp.Unary | {Ops.CAST, Ops.BITCAST}, src=(invalid_gate,), name="op"),
   lambda cond, x, op, i: cond.where(op.replace(src=(x,)), i)),
  (UPat(GroupOp.Binary, src=(invalid_gate, UPat.var("y")), name="alu"),
   lambda cond, x, y, alu, i: cond.where(x.alu(alu.op, y), i)),
  (UPat(GroupOp.Binary, src=(UPat.var("y"), invalid_gate), name="alu"),
   lambda cond, x, y, alu, i: cond.where(y.alu(alu.op, x), i)),
  (UPat(GroupOp.Binary - GroupOp.Comparison, src=[invalid_pat, UPat()]), lambda i: i),
  (invalid_gate.reduce(allow_any_len=True, name="red"), lift_reduce_gate),
  (invalid_pat.where(UPat(), UPat()), lambda i: i),
  (invalid_gate.where(UPat.var("a"), UPat.var("b")), lambda cond, x, i, a, b: cond.where(x.where(a, b), i)),
  (UPat.var("cond").where(invalid_pat, UPat.var("val")),
   lambda cond, i, val: cond.logical_not().where(val, i) if not val.is_invalid else i),
  (UPat.var("a").where(invalid_gate, UPat.var("c")),
   lambda cond, i, x, a, c: (a.logical_not() | cond).where(a.where(x, c), i) if not c.is_invalid else None),
  (UPat.var("a").where(UPat.var("b"), invalid_gate),
   lambda cond, i, x, a, b: (a | cond).where(a.where(b, x), i) if not b.is_invalid else None),
  # fold gated LOAD/STORE on Invalid index
  (UPat(Ops.STORE, src=(UPat(Ops.INDEX, src=(UPat(), invalid_pat), allow_any_len=True).or_casted(), UPat()), name="x"),
   lambda i, x: UOp.noop().after(*x.src)),
  (UPat(Ops.LOAD, src=(UPat(Ops.INDEX, src=(UPat(), invalid_pat), allow_any_len=True).or_casted(),), allow_any_len=True, name="x"),
   lambda x, i: x.const_like(0)),
])

pm_remove_invalid = PatternMatcher([
  (invalid_gate.named("w"), lambda cond, x, i, w: w.replace(src=(cond, x, w.const_like(0)))),
  (UPat(Ops.STACK, name="s"), lambda s: s.replace(src=tuple(UOp.const(0, s.dtype) if x.is_invalid else x for x in s.src))
   if any(x.is_invalid for x in s.src) else None),
])

# ---- uncast redundant typed constants inside broadcastable ops ----

def _uncast_const(u: UOp) -> UOp | None:
  src = tuple(s.src[0] if s.op is Ops.CAST and s.dtype not in dtypes.weaks and s.src[0].op is Ops.CONST
              and s.src[0].dtype in dtypes.weaks else s for s in u.src)
  if src == u.src: return None
  # ensure operand promotion and result dtype are unchanged
  if u.op is Ops.WHERE:
    if src[0] is not u.src[0]: return None
    new_promo = least_upper_dtype(src[1].dtype, src[2].dtype)
    old_promo = least_upper_dtype(u.src[1].dtype, u.src[2].dtype)
    if new_promo != old_promo: return None
  else:
    if u.op in (Ops.SHL, Ops.SHR):
      if src[0].dtype != u.src[0].dtype: return None
    else:
      if least_upper_dtype(*(s.dtype for s in src)) != least_upper_dtype(*(s.dtype for s in u.src)): return None
  cand = UOp(u.op, src, u.arg)
  return cand if cand.dtype == u.dtype else None

pm_uncast_const = PatternMatcher([(UPat(GroupOp.Broadcastable, name="u"), _uncast_const)])

# ---- phase 1: constant folding & simple identities ----

def _fold_const_alu(u: UOp) -> UOp | None:
  if not all(s.is_const and not s.is_invalid for s in u.src): return None
  if (v := exec_alu(u.op, u.dtype, *(s.val for s in u.src))) is None: return None
  return u.const_like(v)

def _const_like_op(val: Any, c: UOp) -> UOp:
  return UOp.const(val, None if c.dtype in dtypes.weaks else c.dtype)

def _fold_mul_consts(u: UOp, x: UOp, c1: UOp, c2: UOp) -> UOp | None:
  if not (c1.is_const and c2.is_const) or c1.is_invalid or c2.is_invalid: return None
  prod = c1.val * c2.val
  if u.dtype.is_float and (not math.isfinite(prod) or prod == 0): return None
  if not _fits(x, prod): return None
  return x * _const_like_op(prod, c2 if c1.dtype in dtypes.weaks else c1)

def _fold_add_consts(u: UOp, x: UOp, c1: UOp, c2: UOp) -> UOp | None:
  if u.dtype.is_float or not (c1.is_const and c2.is_const) or c1.is_invalid or c2.is_invalid: return None
  s = c1.val + c2.val
  if not _fits(x, s): return None
  return x + _const_like_op(s, c2 if c1.dtype in dtypes.weaks else c1)

def _fold_div_const(u: UOp, x: UOp, c: UOp) -> UOp | None:
  if not (u.dtype.is_float and c.is_const and not c.is_invalid and c.val != 0 and type(c.val) is not bool): return None
  inv = 1.0 / float(c.val)
  if not math.isfinite(inv): return None
  return x * _const_like_op(inv, c)

def _fold_where(w: UOp, c: UOp, a: UOp, b: UOp) -> UOp | None:
  if a is b: return a
  if c.is_const and not c.is_invalid:
    ret = a if c.val else b
    if ret.op is Ops.CONST and not ret.is_invalid and ret.dtype in dtypes.weaks and w.dtype not in dtypes.weaks:
      return ret.cast(w.dtype)
    return ret
  if a.is_const and b.is_const and not a.is_invalid and not b.is_invalid and a.dtype is dtypes.bool and b.dtype is dtypes.bool:
    if a.val is True and b.val is False: return c
    if a.val is False and b.val is True: return c.logical_not()
  return None

def _quotient_base(q: UOp, base: UOp, div: int) -> UOp | None:
  (q, s), (num, a) = q.pop_const(), base.pop_const()
  if q.op is not Ops.DIV or q.src[1].op is not Ops.CONST: return None
  if div > 0 and num.op is Ops.DIV and num.src[1].op is Ops.CONST and q.src[1].arg == (c := num.src[1].arg) * div:
    num, a, D = num.src[0], a * c, c * div
  elif q.src[1].arg == div:
    D = div
  else:
    return None
  (x, xa), (p, pa) = num.pop_const(), q.src[0].pop_const()
  if p is not x or (t := xa + a - pa) % D: return None
  return base - k * div if (k := t // D - s) else base

def fold_add_divmod_recombine(x: UOp) -> UOp | None:
  terms = list(x.split_uop(Ops.ADD))
  scaled = [t.pop_const(Ops.MUL) for t in terms]
  for i, (mod, mul) in enumerate(scaled):
    if mod.op is not Ops.MOD or mod.src[1].op is not Ops.CONST or not isinstance(mod.src[1].arg, int): continue
    base, div = mod.src[0], mod.src[1].arg
    for j, (q, scale) in enumerate(scaled):
      if i == j or scale != div * mul: continue
      if (b := _quotient_base(q, base, div)) is None:
        if q.op is not Ops.MOD or q.src[1].op is not Ops.CONST or not isinstance(q.src[1].arg, int) or (d := q.src[1].arg) <= 0: continue
        if (b := _quotient_base(q.src[0], base, div)) is None: continue
        b = b % (div * d)
      rest = [t for k, t in enumerate(terms) if k not in (i, j)]
      return UOp.usum(b * mul, *rest)
  return None

symbolic_simple = pm_data_invalid + PatternMatcher([
  # constant folding
  (UPat(GroupOp.ALU, name="u"), _fold_const_alu),
  (UPat(Ops.CAST, src=(UPat(Ops.CAST, src=(UPat.cvar("c"),), name="mid"),), name="u"),
   lambda u, mid, c: UOp.const(c.arg, u.dtype) if can_lossless_cast(mid.dtype, u.dtype) or mid.dtype in dtypes.weaks else None),
  (UPat((Ops.CAST, Ops.BITCAST), src=(UPat.var("x"),), name="u"), lambda u, x: x if u.dtype == x.dtype else None),
  (UPat(Ops.CAST, src=(UPat(Ops.CAST, src=(UPat.var("x"),), name="mid"),), name="u"),
   lambda u, mid, x: x if u.dtype == x.dtype and can_lossless_cast(x.dtype, mid.dtype) else None),
  (UPat(Ops.BITCAST, src=(UPat(Ops.BITCAST, src=(UPat.var("x"),)),), name="u"), lambda u, x: x.bitcast(u.dtype)),
  (UPat(Ops.CAST, dtype=dtypes.bool, src=(UPat.var("x"),)), lambda x: x.ne(0) if x.dtype is not dtypes.bool else None),

  # normalize SUB / NEG on weakint to additive/multiplicative form so all index rules match uniformly
  (UPat(Ops.SUB, dtype=dtypes.weakint, src=(UPat.var("a"), UPat.var("b"))),
   lambda a, b: (a + (-b.arg)) if b.op is Ops.CONST and not b.is_invalid else a + (b * -1)),
  (UPat(Ops.NEG, dtype=dtypes.weakint, src=(UPat.var("x"),)), lambda x: x * -1),

  # identities (float x * 0 is not folded because of NaN/Inf)
  (UPat((Ops.ADD, Ops.SUB, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR), src=(UPat.var("x"), UPat.var("c"))), lambda x, c: x if _is_num(c, 0) else None),
  (UPat((Ops.ADD, Ops.OR, Ops.XOR), src=(UPat.var("c"), UPat.var("x"))), lambda x, c: x if _is_num(c, 0) else None),
  (UPat(Ops.SUB, src=(UPat.var("c"), UPat.var("x"))), lambda c, x: -x if _is_num(c, 0) else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c")]), lambda x, c: x if _is_num(c, 1) else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c")], name="u"),
   lambda u, x, c: (-x if _is_num(c, -1) and u.dtype.is_signed and u.dtype is not dtypes.weakint else
                    (u.const_like(0) if _is_num(c, 0) and not u.dtype.is_float else None))),
  (UPat(Ops.AND, src=[UPat.var("x"), UPat.var("c")], name="u"), lambda u, x, c: u.const_like(0) if _is_num(c, 0) else None),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.var("c")), name="u"),
   lambda u, x, c: x if _is_num(c, 1) else (x * -1 if _is_num(c, -1) and u.dtype is dtypes.weakint else
                                            (-x if _is_num(c, -1) and u.dtype.is_int and u.dtype.is_signed else _fold_div_const(u, x, c)))),
  (UPat(Ops.DIV, src=(UPat.var("c"), UPat.var("x")), name="u"), lambda u, c, x: x.recip() if u.dtype.is_float and _is_num(c, 1) else None),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.var("x")), name="u"), lambda u, x: u.const_like(1) if not u.dtype.is_float else None),

  # self-folding & signs
  (UPat(GroupOp.Idempotent, src=(UPat.var("x"), UPat.var("x"))), lambda x: x),
  (UPat((Ops.SUB, Ops.XOR, Ops.MOD), src=(UPat.var("x"), UPat.var("x")), name="u"),
   lambda u, x: u.const_like(0) if not u.dtype.is_float else None),
  (UPat(Ops.CMPLT, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(False)),
  (UPat(Ops.CMPEQ, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(True) if not x.dtype.is_float else None),
  (UPat(Ops.CMPNE, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(False) if not x.dtype.is_float else None),
  (UPat(Ops.NEG, src=(UPat(Ops.NEG, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.XOR, src=[UPat(Ops.XOR, src=[UPat.var("x"), UPat.var("y")]), UPat.var("y")]), lambda x, y: x),
  (UPat(Ops.MOD, src=(UPat(Ops.MOD, src=(UPat(), UPat.var("y")), name="base"), UPat.var("y"))), lambda base, y: base),
  (UPat(Ops.ADD, src=[UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),))], name="u"),
   lambda u, a, b: a - b if u.dtype is not dtypes.weakint else None),
  (UPat(Ops.SUB, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)))), lambda a, b: a + b),
  (UPat(Ops.MUL, src=(UPat(Ops.NEG, src=(UPat.var("x"),)), UPat(Ops.NEG, src=(UPat.var("y"),)))), lambda x, y: x * y),
  (UPat(Ops.MUL, src=[UPat(Ops.NEG, src=(UPat.var("x"),)), UPat.var("c")]),
   lambda x, c: x * _const_like_op(-c.val, c) if c.is_const and not c.is_invalid and type(c.val) is not bool else None),

  # variations of (x % c) + (x // c) * c = x
  (UPat(Ops.ADD, dtype=dtypes.weakint, name="x"), fold_add_divmod_recombine),

  # two-stage constant folding
  (UPat(Ops.MUL, src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c1")]), UPat.var("c2")], name="u"), _fold_mul_consts),
  (UPat(Ops.ADD, src=[UPat(Ops.ADD, src=[UPat.var("x"), UPat.var("c1")]), UPat.var("c2")], name="u"), _fold_add_consts),

  # bool & control
  (UPat(Ops.MUL, dtype=dtypes.bool, src=(UPat.var("x"), UPat.var("y"))), lambda x, y: x & y),
  (UPat((Ops.ADD, Ops.MAX), dtype=dtypes.bool, src=(UPat.var("x"), UPat.var("y"))), lambda x, y: x | y),
  (UPat(Ops.AND, dtype=dtypes.bool, src=[UPat.var("x"), UPat.cvar("c")]), lambda x, c: x if c.arg else c),
  (UPat(Ops.OR, dtype=dtypes.bool, src=[UPat.var("x"), UPat.cvar("c")]), lambda x, c: c if c.arg else x),
  (UPat(Ops.CMPEQ, src=[UPat.var("x", dtype=dtypes.bool), UPat.cvar("c")]), lambda x, c: x if c.arg is True else x.logical_not()),
  (UPat(Ops.CMPNE, src=[UPat.var("x", dtype=dtypes.bool), UPat.cvar("c")]), lambda x, c: x.logical_not() if c.arg is True else x),
  (UPat.var("x", dtype=dtypes.bool).cast(dtypes.wints).eq(UPat.cvar("c")),
   lambda x, c: x.logical_not() if c.arg == 0 else x if c.arg == 1 else UOp.const(False)),
  (UPat(Ops.WHERE, src=(UPat.var("c"), UPat.var("a"), UPat.var("b")), name="w"), _fold_where),
  (UPat(Ops.IF, src=(UPat.var("c"), UPat.var("body")), allow_any_len=True, name="u"),
   lambda u, c, body: (body if c.val else (u.src[2] if len(u.src) == 3 else None)) if c.is_const and not c.is_invalid else None),
])

# ---- phase 2: index symbolic + div/mod ----

def lt_folding(x: UOp, c: int) -> UOp | None:
  if isinstance(c, bool): return None
  p, np = _partition([u.pop_const(Ops.MUL) for u in x.split_uop(Ops.ADD)], lambda uf: uf[1] == 1)
  if np and (d := math.gcd(*[int(f) for _, f in np])) > 1 and \
     (t := _ceildiv(c - sum(u.vmin for u, _ in p), d)) == _ceildiv(c - sum(u.vmax for u, _ in p), d):
    return UOp.usum(*(u * (f // d) for u, f in np)) < t
  return None

def canonicalize_simplex(x: UOp) -> UOp | None:
  changed, ret = False, []
  for u in x.split_uop(Ops.ADD):
    if u.op is Ops.MUL and u.src[1].op is Ops.CONST and isinstance(u.src[1].arg, int) and u.src[1].arg > 0:
      changed = True
      u = u.src[0]
    if not (u.op in GroupOp.Irreducible and u.vmin >= 0): return None
    ret.append(u)
  return UOp.usum(*ret) if changed else None

def fold_where_closure(cond: UOp, t: UOp, f: UOp) -> UOp | None:
  if any(u.op_in_backward_slice_with_self(Ops.INDEX) for u in (cond, t, f)): return None
  nt, nf = t.substitute({cond: UOp.const(True)}), f.substitute({cond: UOp.const(False)})
  return None if nt is t and nf is f else cond.where(nt, nf)

commutative = PatternMatcher([
  # canonicalize commutative ops on weakint (constants drift to the right since CONST has smallest op.value or tuplize order)
  (UPat(GroupOp.Commutative, dtype=dtypes.weakint, name="x"),
   lambda x: x.replace(src=x.src[::-1]) if x.src[1].tuplize < x.src[0].tuplize else None),
])

def _is_zero_const(u: UOp) -> bool: return u.is_const and not u.is_invalid and type(u.val) is not bool and u.val == 0
_zero = UPat.cvar().or_casted()

symbolic = symbolic_simple + commutative + PatternMatcher([
  # boolean algebra
  ((UPat.var("x", dtype=dtypes.bool).logical_not() | UPat.var("y")) & UPat.var("x"), lambda x, y: y & x),
  (UPat.var("x", dtype=dtypes.bool) | UPat.var("x", dtype=dtypes.bool).logical_not(), lambda x: UOp.const(True)),
  (UPat.var("x", dtype=dtypes.bool) & UPat.var("x", dtype=dtypes.bool).logical_not(), lambda x: UOp.const(False)),

  # combine terms
  (UPat.var("x", dtypes.wints) * UPat.cvar("c0") + UPat.var("x") * UPat.cvar("c1"),
   lambda x, c0, c1: x * (c0 + c1) if _fits(x, c0.vmin + c1.vmin) else None),
  ((UPat.var("y") + UPat.var("x", dtypes.wints) * UPat.cvar("c0")) + UPat.var("x") * UPat.cvar("c1"),
   lambda x, y, c0, c1: y + m if _fits(x, c0.vmin + c1.vmin) and _no_overflow(m := x * (c0 + c1)) else None),
  (UPat.var("x", dtypes.wints) + UPat.var("x") * UPat.cvar("c"),
   lambda x, c: x * (c + 1) if _fits(x, c.vmin + 1) else None),
  ((UPat.var("y") + UPat.var("x", dtypes.wints)) + UPat.var("x") * UPat.cvar("c"),
   lambda x, y, c: y + m if _fits(x, c.vmin + 1) and _no_overflow(m := x * (c + 1)) else None),
  ((UPat.var("y") + UPat.var("x", dtypes.wints) * UPat.cvar("c")) + UPat.var("x"),
   lambda x, y, c: y + m if _fits(x, c.vmin + 1) and _no_overflow(m := x * (c + 1)) else None),
  (UPat.var("x", dtypes.wints) + UPat.var("x"), lambda x: x * 2 if _fits(x, 2 * x.vmin) and _fits(x, 2 * x.vmax) else None),
  (((UPat.var("y") + UPat.var("x", dtypes.wints)) + UPat.var("x")).named("a"),
   lambda a, y, x: y + x * 2 if _fits(a, 2 * x.vmin) and _fits(a, 2 * x.vmax) else None),
  # distribute const over weakint add: c * (x + k) -> c*x + c*k
  (UPat.cvar("y") * (UPat.var("x", dtype=dtypes.weakint) + UPat.cvar("c")), lambda x, y, c: (y * x) + (y * c)),

  # where folding
  (UPat.var("cond", dtype=dtypes.bool).logical_not().where(UPat.var("t"), UPat.var("f")),
   lambda cond, t, f: cond.where(f, t) if not f.is_invalid else None),
  (UPat.var("cond").where(UPat.var("t"), UPat.var("f")), fold_where_closure),
  (UPat.var("gate").where(UPat.var("x"), UPat.cvar("z")).ne(UPat.cvar("z2")),
   lambda gate, x, z, z2: gate & x.ne(0) if _is_zero_const(z) and _is_zero_const(z2) else None),
  (UPat.var("a").where(UPat.var("b").where(UPat.var("c"), UPat.var("d")), UPat.var("d")), lambda a, b, c, d: (a & b).where(c, d)),
  (UPat.var("a").where(UPat.var("b").where(UPat.var("c"), UPat.var("d")), UPat.var("c")), lambda a, b, c, d: (a & b.logical_not()).where(d, c)),
  (UPat.var("a").where(UPat.var("c"), UPat.var("b").where(UPat.var("c"), UPat.var("d"))), lambda a, b, c, d: (a | b).where(c, d)),
  (UPat(GroupOp.Binary, name="alu", src=(UPat.var("c").where(UPat.var("t"), UPat.var("f")), UPat.var("c").where(UPat.var("tt"), UPat.var("ff")))),
   lambda alu, c, t, tt, f, ff: c.where(t.alu(alu.op, tt), f.alu(alu.op, ff)) if (t.op is Ops.CONST and tt.op is Ops.CONST) or (f.op is Ops.CONST and ff.op is Ops.CONST) else None),
  (UPat.var("c").where(UPat.var("t"), UPat.cvar("z1")) + UPat.var("c").where(UPat.cvar("z2"), UPat.var("f")),
   lambda c, t, f, z1, z2: c.where(t, f) if _is_zero_const(z1) and _is_zero_const(z2) else None),

  # vmin == vmax -> CONST
  (UPat({Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE, Ops.DIV, Ops.MOD, Ops.PARAM, Ops.SPECIAL}, name="x"),
   lambda x: x.const_like(x.vmin) if x.dtype is not dtypes.void and x.vmin == x.vmax else None),
  (UPat(Ops.RANGE, src=(UPat.cvar().or_casted(),), name="x"), lambda x: x.const_like(x.vmin) if x.vmin == x.vmax else None),

  # max folding
  ((UPat.cvar("a") < UPat.var("b")).where(UPat.var("b"), UPat.cvar("c")), lambda a, b, c: b.maximum(a) if a.arg == c.arg else None),
  ((UPat.var("a") < UPat.cvar("b")).where(UPat.cvar("c"), UPat.var("y")),
   lambda a, b, c, y: y.maximum(c) if (y is a and b.arg == c.arg) or (a.dtype.is_int and a.dtype.is_signed and y is a + (c.arg - b.arg)) else None),
  (UPat.var("x").maximum(UPat.var("y"), name="m"),
   lambda m, x, y: (x.cast(m.dtype) if x.dtype != m.dtype else x) if x.vmin >= y.vmax else None),

  # nested div: (x // c1) // c2 -> x // (c1 * c2)
  ((UPat.var("x") // UPat.cvar("c1")) // UPat.cvar("c2"),
   lambda x, c1, c2: x // (c1.arg * c2.arg) if c2.vmin > 0 and x.dtype.min <= c1.vmin * c2.vmin <= x.dtype.max else None),

  # lt folding
  ((UPat.cvar("c0") + UPat.var("x", dtype=dtypes.swints)) < UPat.cvar("c1"),
   lambda x, c0, c1: x < (c1.arg - c0.arg) if _fits(x, c1.vmin - c0.vmin) else None),
  ((UPat.var("x", dtype=dtypes.weakint) // UPat.cvar("d")) < UPat.cvar("c"),
   lambda x, d, c: (x < c.arg * d.arg) if d.arg > 0 else None),
  (UPat.var("x", dtype=dtypes.weakint) < UPat.cvar("c"), lambda x, c: lt_folding(x, c.arg)),
  ((UPat.var("x", dtype=dtypes.swints) * -1) < (UPat.var("y") * -1), lambda x, y: y < x),
  ((UPat.var("x", dtype=dtypes.swints) * -1) < UPat.cvar("c"), lambda x, c: (-c.arg) < x if _fits(x, -c.vmin) else None),
  ((UPat.var("x", dtype=dtypes.weakint) < 1).logical_not(),
   lambda x: (newx < 1).logical_not() if (newx := canonicalize_simplex(x)) is not None else None),

  # move add/mul consts to end
  ((UPat.var("x", dtypes.wints) + UPat.cvar("c1")) + UPat.var("y"),
   lambda x, c1, y: m + c1 if y.op is not Ops.CONST and _no_overflow(m := x + y) else None),
  ((UPat.var("x") * UPat.cvar("c1")) * UPat.var("y"),
   lambda x, c1, y: m * c1 if y.op is not Ops.CONST and (x.dtype in dtypes.wints or c1.arg == -1) and _no_overflow(m := x * y) else None),

  # range mod/div its own upper bound
  (UPat(Ops.RANGE, src=(UPat.var("end"),), name="r") % UPat.var("end"), lambda r, end: r),
  (UPat(Ops.RANGE, src=(UPat.var("end"),), name="r") // UPat.var("end"), lambda r, end: r.const_like(0)),

  # cast folding
  (UPat.var("x").cast(name="a").cast(name="b"), lambda x, a, b: x.cast(b.dtype) if can_lossless_cast(x.dtype, a.dtype) else None),
  (UPat.var("x", dtypes.wints).cast(dtypes.wints, name="a").cast(name="b"),
   lambda x, a, b: x.cast(b.dtype) if not x.overflows(a.dtype) else None),
  ((UPat.var("x", dtype=dtypes.weakint) + UPat.cvar("c")).cast(dtypes.sints, name="cast"),
   lambda x, c, cast: x.cast(cast.dtype) + cast.const_like(c.arg)),

  # AFTER/END cleanup
  (UPat((Ops.AFTER, Ops.END), src=(UPat.var("s"),)), lambda s: s),
]) + div_and_mod_symbolic + pm_uncast_const

# ---- valid simplification (ported from tinygrad/uop/symbolic.py) ----

def parse_valid(v: UOp) -> tuple[UOp, bool, int] | None:
  # returns (expr, is_upper, bound): is_upper=True => expr <= bound, is_upper=False => expr >= bound
  neg = False
  lt = v
  if v.op is Ops.XOR and len(v.src) == 2 and any(s.op is Ops.CONST and s.arg is True for s in v.src):
    neg = True
    lt = v.src[0] if (v.src[1].op is Ops.CONST and v.src[1].arg is True) else v.src[1]
  elif v.op is Ops.CMPEQ and len(v.src) == 2 and any(s.op is Ops.CONST and s.arg is False for s in v.src):
    neg = True
    lt = v.src[0] if (v.src[1].op is Ops.CONST and v.src[1].arg is False) else v.src[1]
  if lt.op is not Ops.CMPLT or not lt.src[0].dtype.is_int: return None
  if (a := lt.src[0]).op is Ops.CONST and not a.is_invalid: return lt.src[1], neg, int(a.arg) + (0 if neg else 1)
  return a, not neg, int(lt.src[1].vmin) if neg else int(lt.src[1].vmax) - 1

def _sub_keep_ranges(uop: UOp, mapping: dict[UOp, UOp]) -> UOp:
  # substitute expressions without descending into unrelated RANGEs (like tinygrad's pm_keep_range)
  def gate(ctx: dict[UOp, UOp], u: UOp):
    if u in ctx: return ctx[u]
    if u.op is Ops.RANGE: raise BottomUpGate
    return None
  return graph_rewrite(uop, PatternMatcher([(UPat.var("u"), gate)]), ctx=mapping, bottom_up=True)

def uop_given_valid(valid: UOp, uop: UOp, try_simplex: bool = True) -> UOp:
  bounds: defaultdict[UOp, list[int | None]] = defaultdict(lambda: [None, None])
  for stmt in valid.split_uop(Ops.AND):
    if (res := parse_valid(stmt)) is None: continue
    expr, is_upper, c = res
    bounds[expr][int(is_upper)] = c

  all_candidates: list[tuple[UOp, UOp]] = []
  for i, (expr, v) in enumerate(bounds.items()):
    v0 = expr.vmin if v[0] is None else max(expr.vmin, v[0])
    v1 = expr.vmax if v[1] is None else min(expr.vmax, v[1])
    if v0 > v1: continue
    all_candidates.append((expr, UOp.variable(f"_fake{i}", v0, v1, expr.dtype)))

    if try_simplex and expr.op is Ops.ADD and v0 == 1 and all(u.op in GroupOp.Irreducible and u.op is not Ops.CONST for u in expr.split_uop(Ops.ADD)):
      candidate = [(xi, UOp.variable(f"_fake{i}", 1, xi.vmax, xi.dtype)) for xi in expr.split_uop(Ops.ADD) if xi.vmax >= 1]
      bs = set(uop.backward_slice) | {uop}
      if not candidate or any(x not in bs for x, _ in candidate): continue
      newuops = [_sub_keep_ranges(uop, {x: nx}).simplify().substitute({nx: x}).simplify() for x, nx in candidate]
      if _all_same(newuops): uop = newuops[0]
      elif uop.op is Ops.STACK and len(uop.src) == 2:
        if _all_same([nu.src[0] for nu in newuops]): uop = uop.replace(src=(newuops[0].src[0], uop.src[1]))
        if _all_same([nu.src[1] for nu in newuops]): uop = uop.replace(src=(uop.src[0], newuops[0].src[1]))

  if all_candidates:
    sub_dict = dict(all_candidates)
    if (s_uop := _sub_keep_ranges(uop, sub_dict)) is not uop:
      uop = s_uop.simplify().substitute({nx: x for x, nx in sub_dict.items()}).simplify()
  return uop

def _valid_priority(v: UOp, valids: list[UOp]) -> tuple[int, int]:
  if (res := parse_valid(v)) is None: return (0, 0)
  return (sum(-1 for other in valids if res[0] is other or res[0] in other.backward_slice), res[2] if res[1] else -res[2])

def simplify_valid(valid: UOp) -> UOp | None:
  if valid.op_in_backward_slice_with_self(Ops.INDEX): return None
  ret: list[UOp] = []
  valids = list(valid.split_uop(Ops.AND))
  valids = sorted(valids, key=lambda v: _valid_priority(v, valids))
  for stmt in _dedup(valids):
    if ret: stmt = uop_given_valid(UOp.uand(*ret), stmt)
    ret.append(stmt)
  return UOp.uand(*ret) if ret != valids else None

def gated_given_valid(cond: UOp, x: UOp, i: UOp) -> UOp | None:
  if x.dtype is not dtypes.weakint or x.op_in_backward_slice_with_self(Ops.INDEX): return None
  nx = uop_given_valid(cond, x, try_simplex=False)
  return None if nx is x else cond.where(nx, i)

pm_simplify_valid = PatternMatcher([
  (UPat(Ops.AND, dtype=dtypes.bool, name="valid"), simplify_valid),
  (invalid_gate, gated_given_valid),
])

def drop_and_clauses(cond: UOp, x: UOp, i: UOp) -> UOp | None:
  keep, drop = _partition(cond.split_uop(Ops.AND), lambda c: any(r in x.ranges for r in c.ranges))
  return UOp.uand(*keep).where(x, i) if drop else None

pm_drop_and_clauses = PatternMatcher([(invalid_gate, drop_and_clauses)])

# ---- phase 3: full kernel symbolic (sym) ----

def reduce_mul_chain(r: UOp) -> UOp | None:
  if r.arg[1] != 0 or r.arg[0] not in (Ops.ADD, Ops.MAX): return None
  if r.arg[0] is Ops.MAX and r.dtype.is_int and not r.dtype.is_signed: return None
  inside, outside = [], []
  closed = set(r.src[1:])
  for m in r.src[0].split_uop(Ops.MUL):
    if m not in closed and not (m.ranges & closed) and (r.arg[0] is not Ops.MAX or m.vmin >= 0):
      outside.append(m)
    else:
      inside.append(m)
  if not outside: return None
  inner = UOp.uprod(*inside) if inside else r.src[0].const_like(1)
  return r.replace(src=(inner, *r.src[1:])) * UOp.uprod(*outside)

def where_on_load(cond: UOp, buf: UOp, idx: UOp, or_cast: UOp) -> UOp | None:
  where_clauses, load_valid = list(cond.split_uop(Ops.AND)), idx.get_valid()
  in_load = set(load_valid.split_uop(Ops.AND))
  idx_index = {u for u in idx.backward_slice if u.op is Ops.INDEX} | ({idx} if idx.op is Ops.INDEX else set())
  def can_move(c: UOp) -> bool:
    return c.op is not Ops.CONST and c.ranges <= idx.ranges and \
      all(u in idx_index for u in c.backward_slice if u.op is Ops.INDEX) and (c.op is not Ops.INDEX or c in idx_index)
  moved, keep = _partition([c for c in where_clauses if c not in in_load], can_move)
  if len(keep) == len(where_clauses): return None
  new_idx = buf.index(idx.get_idx().valid(UOp.uand(load_valid, *moved)))
  ret = new_idx.cast(or_cast.dtype) if or_cast.op is Ops.CAST else new_idx
  return UOp.uand(*keep).where(ret, ret.const_like(0)) if keep else ret

pm_move_where_on_load = PatternMatcher([
  (UPat.var("cond").where(UPat.var("buf").index(UPat.var("idx")).or_casted("or_cast"), _zero.named("z")),
   lambda cond, buf, idx, or_cast, z: where_on_load(cond, buf, idx, or_cast) if _is_zero_const(z) else None),
  (UPat.var("cond").where(_zero.named("z"), UPat.var("buf").index(UPat.var("idx")).or_casted("or_cast")),
   lambda cond, buf, idx, or_cast, z: where_on_load(cond.logical_not(), buf, idx, or_cast) if _is_zero_const(z) else None),
])

sym = symbolic + pm_simplify_valid + PatternMatcher([
  # gated store of Invalid -> NOOP
  (UPat(Ops.STORE, src=(UPat(), invalid_pat), name="x"), lambda i, x: UOp.noop().after(*x.src)),
  (UPat(Ops.STORE, src=(UPat(Ops.INDEX, name="index"), UPat.var("cond").where(UPat.var("val"), invalid_pat))),
   lambda index, cond, val, i: index.src[0].index(index.src[1].valid(cond)).store(val)),
  # move loop-invariant muls outside reduce
  (UPat(Ops.REDUCE, src=(UPat(Ops.MUL),), allow_any_len=True, name="r"), reduce_mul_chain),
  # (x + y) * c -> x*c + y*c for weakint
  ((UPat.var("x", dtype=dtypes.weakint) + UPat.var("y")).named("a") * UPat.cvar("c"),
   lambda a, x, y, c: x * c + y * c if all(_fits(a, v * c.vmin) for v in (x.vmin, x.vmax, y.vmin, y.vmax)) else None),
])
