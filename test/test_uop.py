"""compiler/uop.py: hash-consing, pattern matching and graph_rewrite. python3.14 -m pytest test/test_uop.py -q"""
import gc, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compiler.uop import UOp, UPat, PatternMatcher, Ops, dtypes, graph_rewrite, substitute

def x(n="x"): return UOp(Ops.PARAM, dtypes.fp32, arg=n)

def test_hash_consing():
  assert x() is x() and (x() + 1.0) is (x() + 1.0)
  assert UOp.const(dtypes.fp32, 1) is not UOp.const(dtypes.fp32, 1.0)   # type(arg) separates them
  assert UOp.const(dtypes.fp32, 1.0) is not UOp.const(dtypes.bf16, 1.0)

def test_cache_releases():
  from compiler.uop import UOpMetaClass
  before = len(UOpMetaClass.ucache)
  y = x("tmp") * 3.0
  assert len(UOpMetaClass.ucache) > before
  del y; gc.collect()
  assert len(UOpMetaClass.ucache) == before

def test_upat_commutative_and_names():
  p = UPat(Ops.MUL, src=[UPat.var("a"), UPat.cvar("c")])
  e = 2.0 * x()                       # const first: the list pattern still matches
  (m,) = p.match(e, {})
  assert m["a"] is x() and m["c"].arg == 2.0
  same = UPat(Ops.ADD, src=(UPat.var("a"), UPat.var("a")))
  assert same.match(x() + x(), {}) and not same.match(x() + x("y"), {})

def test_graph_rewrite_folds_to_fixed_point():
  fold = PatternMatcher([
    (UPat(Ops.MUL, src=[UPat.var("a"), UPat.cvar(arg=1.0)]), lambda a: a),
    (UPat(Ops.ADD, src=[UPat.var("a"), UPat.cvar(arg=0.0)]), lambda a: a),
    (UPat(Ops.ADD, src=(UPat.cvar("a"), UPat.cvar("b"))), lambda a, b: UOp.const(a.dtype, a.arg + b.arg)),
  ])
  e = (x() * 1.0 + (UOp.const(dtypes.fp32, -2.0) + 2.0)) * 1.0
  assert graph_rewrite(e, fold) is x()
  assert graph_rewrite(e, fold, bottom_up=True) is x()

def test_shared_nodes_rewrite_once():
  calls = []
  pm = PatternMatcher([(UPat(Ops.PARAM, name="p"), lambda p: None if p.arg.endswith("'") else calls.append(p) or p.replace(arg=p.arg + "'"))])
  shared = x()
  out = graph_rewrite(UOp.sink(shared * 2.0, shared + 1.0), pm)
  assert len(calls) == 1 and all(s.src[0].arg == "x'" for s in out.src)

def test_ctx_and_substitute():
  pm = PatternMatcher([(UPat(Ops.PARAM, name="p"), lambda ctx, p: ctx.setdefault(p.arg, len(ctx)) and None or None)])
  seen = {}
  graph_rewrite(UOp.sink(x("a") + x("b")), pm, ctx=seen)
  assert set(seen) == {"a", "b"}
  assert substitute(x("a") + x("b"), {x("b"): x("c")}) is x("a") + x("c")

if __name__ == "__main__":
  for name, fn in list(globals().items()):
    if name.startswith("test_"): fn(); print("PASS", name)
