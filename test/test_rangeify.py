import math, unittest
from compiler import (
  KernelArg, Ops, Tensor, UOp, Variable, dtypes, exec_alu, function, lower_tensor, render_uir, verify,
)
from compiler.uop import smax

# ---- Minimal Layer 1 kernel-graph interpreter for numerical correctness verification ----

def _eval_kernel(sink: UOp, arg_vals: list) -> None:
  """Execute one Layer 1 kernel SINK(body, arg=KernelArg) in Python over flat lists."""
  assert sink.op is Ops.SINK and isinstance(sink.arg, KernelArg)
  body = sink.src[0]
  # collect active ranges per node so we can loop over END / REDUCE
  def eval_uop(u: UOp, env: dict[UOp, object]) -> object:
    if u in env: return env[u]
    op, src = u.op, u.src
    if op is Ops.CONST: return u.arg
    if op is Ops.NOOP: return None
    if op is Ops.PARAM: return arg_vals[u.arg.slot]
    if op is Ops.CAST:
      v = eval_uop(src[0], env)
      return bool(v) if u.dtype is dtypes.bool else float(v) if u.dtype.is_float else int(v)
    if op is Ops.INDEX:
      buf = eval_uop(src[0], env)
      idx = int(eval_uop(src[1], env))
      return (buf, idx)
    if op is Ops.LOAD:
      buf, idx = eval_uop(src[0], env)
      off = int(eval_uop(src[1], env)) if len(src) >= 2 else 0
      if len(src) == 3 and not eval_uop(src[2], env):
        return 0.0 if u.dtype.is_float else False if u.dtype is dtypes.bool else 0
      return buf[idx + off]
    if op is Ops.STORE:
      buf, idx = eval_uop(src[0], env)
      if len(src) == 4:
        off, val, gate = int(eval_uop(src[1], env)), eval_uop(src[2], env), eval_uop(src[3], env)
        if gate: buf[idx + off] = val
      elif len(src) == 3:
        buf[idx + int(eval_uop(src[1], env))] = eval_uop(src[2], env)
      else:
        buf[idx] = eval_uop(src[1], env)
      return None
    if op is Ops.END:
      rngs = src[1:]
      bounds = [int(eval_uop(r.src[0], env)) for r in rngs]
      def rec(k: int) -> None:
        if k == len(rngs):
          eval_uop(src[0], env)
          return
        r = rngs[k]
        for i in range(bounds[k]):
          env[r] = i
          rec(k + 1)
        env.pop(r, None)
      rec(0)
      return None
    if op is Ops.REDUCE:
      red_op = u.arg[0]
      rngs = src[1:]
      bounds = [int(eval_uop(r.src[0], env)) for r in rngs]
      acc = 0.0 if (red_op is Ops.ADD and u.dtype.is_float) else 0 if red_op is Ops.ADD else (-math.inf if u.dtype.is_float else -(1 << 62))
      def rec(k: int) -> None:
        nonlocal acc
        if k == len(rngs):
          v = eval_uop(src[0], env)
          acc = acc + v if red_op is Ops.ADD else max(acc, v)
          return
        r = rngs[k]
        for i in range(bounds[k]):
          env[r] = i
          rec(k + 1)
        env.pop(r, None)
      rec(0)
      return acc
    if op is Ops.WHERE:
      return eval_uop(src[1], env) if eval_uop(src[0], env) else eval_uop(src[2], env)
    if op in (Ops.ADD, Ops.SUB, Ops.MUL, Ops.DIV, Ops.MOD, Ops.MAX, Ops.NEG, Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RECIP,
              Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE, Ops.AND, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR, Ops.MULACC):
      vals = [eval_uop(s, env) for s in src]
      return exec_alu(op, u.dtype, *vals)
    raise AssertionError(f"unsupported Layer 1 op in test interpreter: {op}")

  eval_uop(body, {})

def run_kernel_graph(kg: UOp, inputs: dict[str, list], var_vals: dict[str, int] | None = None) -> list:
  """Execute a lowered kernel graph (including deduplicated @function CALLs) and return the 'out' buffer."""
  var_vals = var_vals or {}
  allocs: dict[UOp, list] = {}

  def get_val(u: UOp, param_env: list | None = None):
    if u.op is Ops.BUFFER: return inputs[u.arg.name]
    if u.op is Ops.PARAM:
      if u.arg.slot >= 0 and param_env is not None: return param_env[u.arg.slot]
      if u.is_variable: return var_vals[u.arg.name]
      raise AssertionError(f"unbound param {u.arg}")
    if u.op is Ops.ALLOC:
      if u not in allocs:
        numel = math.prod(smax(d) for d in u.shape) if u.shape else 1
        allocs[u] = [0.0 if u.dtype.is_float else 0] * numel
      return allocs[u]
    if u.op is Ops.AFTER:
      for dep in u.src[1:]: exec_node(dep, param_env)
      return get_val(u.src[0], param_env)
    raise AssertionError(f"unexpected call arg {u.op}")

  ran: set[tuple[UOp, int]] = set()
  def exec_node(u: UOp, param_env: list | None = None):
    key = (u, id(param_env))
    if key in ran: return
    ran.add(key)
    if u.op is Ops.SINK:
      for s in u.src: exec_node(s, param_env)
    elif u.op is Ops.CALL:
      body = u.src[0]
      args = [get_val(s, param_env) for s in u.src[1:]]
      if isinstance(body.arg, KernelArg):
        _eval_kernel(body, args)
      else:
        exec_node(body, args)
    elif u.op is Ops.AFTER:
      for dep in u.src[1:]: exec_node(dep, param_env)

  exec_node(kg)
  out_buf = next(u for u in kg.toposort() if u.op is Ops.ALLOC and u.arg.name == "out")
  return allocs[out_buf]

def verify_all_kernels(kg: UOp) -> list[UOp]:
  kernels = [u for u in kg.toposort(enter_calls=True) if u.op is Ops.SINK and isinstance(u.arg, KernelArg)]
  for k in kernels: verify(k)
  return kernels


class TestSymbolicAndDivMod(unittest.TestCase):
  def test_arange_mod_congruence_and_bounds(self):
    N = 128256
    i, r = UOp.range(N, 0), UOp.range(N, 1)
    self.assertIs(((i * (2 * N) + r) % (2 * N - 1)).simplify(), (i + r).simplify())
    self.assertIs(((i * (2 * N) + r) < (2 * N * N - N)).simplify(), UOp.const(True))
    self.assertIs(((i + r) < (2 * N - 1)).simplify(), UOp.const(True))
    self.assertIs((i % N).simplify(), i)
    self.assertIs((i // N).simplify(), UOp.const(0))

  def test_divmod_recombine(self):
    r = UOp.range(32, 0)
    self.assertIs(((r // 4) * 4 + (r % 4)).simplify(), r)
    self.assertIs((((r + 3) // 4) * 4 + ((r + 3) % 4)).simplify(), (r + 3).simplify())

  def test_nested_div_and_lt_folding(self):
    r = UOp.range(64, 0)
    self.assertIs(((r // 4) // 2).simplify(), (r // 8).simplify())
    self.assertIs(((r * 4 + 1) < 20).simplify(), (r < 5).simplify())


class TestRangeifyAndCollapse(unittest.TestCase):
  def test_arange_collapses_completely(self):
    for args, expected in [
      ((8,), list(range(8))),
      ((2, 10, 2), [2, 4, 6, 8]),
      ((10, 0, -1), list(range(10, 0, -1))),
      ((0.0, 4.0, 0.5), [i * 0.5 for i in range(8)]),
    ]:
      kg = lower_tensor(Tensor.arange(*args))
      ks = verify_all_kernels(kg)
      self.assertEqual(len(ks), 1)
      # zero REDUCE ops left!
      self.assertEqual([u for u in ks[0].toposort() if u.op is Ops.REDUCE], [])
      got = run_kernel_graph(kg, {})
      self.assertEqual(got, expected)

  def test_embedding_lowers_to_single_gather(self):
    vocab, dim = 16, 4
    w = Tensor.buffer("w", (vocab, dim), dtypes.bf16)
    tok = Tensor.buffer("tok", (1, 1), dtypes.i32)
    hot = tok.unsqueeze(-1).eq(Tensor.arange(vocab)).unsqueeze(-1)

    for expr in [hot.where(w, 0.0).sum(-2), hot.where(w, 0.0).sum(-2, dtype=w.dtype)]:
      kg = lower_tensor(expr)
      ks = verify_all_kernels(kg)
      self.assertEqual(len(ks), 1)
      # no REDUCE left — collapsed to a single gated gather!
      self.assertEqual([u for u in ks[0].toposort() if u.op is Ops.REDUCE], [])
      # only a single loop over dim=4 (renumbered to axis=0)
      rngs = [u for u in ks[0].toposort() if u.op is Ops.RANGE]
      self.assertEqual(len(rngs), 1)
      self.assertEqual(rngs[0].arg.axis, 0)
      self.assertEqual(rngs[0].src[0].arg, dim)

      w_data = [float(i * 10 + j) for i in range(vocab) for j in range(dim)]
      # in-bounds lookup
      self.assertEqual(run_kernel_graph(kg, {"w": w_data, "tok": [7]}), [70.0, 71.0, 72.0, 73.0])
      # out-of-bounds lookup is safely gated to 0.0
      self.assertEqual(run_kernel_graph(kg, {"w": w_data, "tok": [-1]}), [0.0, 0.0, 0.0, 0.0])
      self.assertEqual(run_kernel_graph(kg, {"w": w_data, "tok": [vocab]}), [0.0, 0.0, 0.0, 0.0])

  def test_argmax_collapses_arange_and_breaks_ties_first(self):
    x = Tensor.buffer("x", (6,), dtypes.fp32)
    kg = lower_tensor(x.argmax())
    ks = verify_all_kernels(kg)
    # should only have 2 1D max reduces (no 6x6 arange add reduce)
    adds = [u for k in ks for u in k.toposort() if u.op is Ops.REDUCE and u.arg[0] is Ops.ADD]
    self.assertEqual(adds, [])
    self.assertEqual(run_kernel_graph(kg, {"x": [1.0, 5.0, 3.0, 5.0, 2.0, 0.0]}), [1])
    self.assertEqual(run_kernel_graph(kg, {"x": [9.0, 1.0, 2.0, 3.0, 4.0, 5.0]}), [0])
    self.assertEqual(run_kernel_graph(kg, {"x": [0.0, 1.0, 2.0, 3.0, 4.0, 8.0]}), [5])

  def test_matmul_rmsnorm_softmax_swiglu(self):
    a = Tensor.buffer("a", (2, 4), dtypes.fp32)
    b = Tensor.buffer("b", (4, 3), dtypes.fp32)
    out = (a @ b).silu().softmax(-1)
    kg = lower_tensor(out)
    verify_all_kernels(kg)

    a_data = [1.0, -2.0, 3.0, 0.5, -1.0, 2.0, 0.0, 1.5]
    b_data = [0.2, -0.1, 0.3, 0.4, 0.5, -0.2, -0.3, 0.1, 0.2, 0.6, -0.4, 0.1]
    got = run_kernel_graph(kg, {"a": a_data, "b": b_data})

    # Python reference
    ref = []
    for i in range(2):
      row = []
      for j in range(3):
        v = sum(a_data[i * 4 + k] * b_data[k * 3 + j] for k in range(4))
        row.append(v / (1.0 + math.exp(-v)))
      m = max(row)
      ex = [math.exp(v - m) for v in row]
      s = sum(ex)
      ref.extend(v / s for v in ex)
    for g, r in zip(got, ref): self.assertAlmostEqual(g, r, places=5)

  def test_kv_cache_symbolic_start_pos_and_function_dedup(self):
    cache = Tensor.buffer("cache", (1, 8, 4), dtypes.fp32)
    new_k = Tensor.buffer("k", (1, 1, 4), dtypes.fp32)
    q = Tensor.buffer("q", (1, 1, 4), dtypes.fp32)
    sp = Variable("start_pos", 1, 7)

    @function(allow_implicit=True)
    def step(q: Tensor, new_k: Tensor, sp: UOp) -> Tensor:
      st = cache[:, sp:sp + 1, :].uop.store(new_k.uop)
      kv = Tensor.from_uop(cache.uop.after(st))
      k_all = kv[:, :sp + 1, :]  # (1, sp+1, 4)
      return (q * k_all).sum(-1).sum(-1)  # scalar sum of dot products over 0..sp

    kg = lower_tensor(step(q, new_k, sp))
    verify_all_kernels(kg)

    # evaluate at two different runtime values of start_pos using the exact same lowered graph!
    for pos in (1, 4):
      c_buf = [float(t * 10 + d) for t in range(8) for d in range(4)]
      k_buf = [1.0, 2.0, 3.0, 4.0]
      q_buf = [1.0, 1.0, 1.0, 1.0]
      got = run_kernel_graph(kg, {"cache": c_buf, "k": k_buf, "q": q_buf}, {"start_pos": pos})
      # cache[0, pos, :] should have been updated in-place to k_buf
      self.assertEqual(c_buf[pos * 4:(pos + 1) * 4], k_buf)
      expected = sum(c_buf[t * 4 + d] * q_buf[d] for t in range(pos + 1) for d in range(4))
      self.assertAlmostEqual(got[0], expected, places=5)

  def test_nanbeige_decode_and_prefill_lowering(self):
    import examples.nanbeige as nb
    m = nb.Model()
    # decode with symbolic start_pos
    sp = Variable("start_pos", 1, nb.max_seq_len - 1)
    kg_dec = lower_tensor(m(Tensor.buffer("tok", (1, 1), dtypes.i32), start_pos=sp))
    ks_dec = verify_all_kernels(kg_dec)
    self.assertLessEqual(len(ks_dec), 20)
    # verify no vocab-sized (166912 x 166912) arange cumsum or vocab-axis embedding sum survives
    for k in ks_dec:
      reduces = [u for u in k.toposort() if u.op is Ops.REDUCE]
      # any ADD reduce over 166912 would mean an uncollapsed arange or uncollapsed embedding
      for r in reduces:
        if r.arg[0] is Ops.ADD:
          for rng in r.src[1:]:
            self.assertNotEqual(rng.src[0].arg if rng.src[0].op is Ops.CONST else None, nb.vocab_size)

    # prefill
    kg_pre = lower_tensor(m(Tensor([[128000, 15339, 11, 1268, 527, 499]], dtype=dtypes.i32), start_pos=0))
    verify_all_kernels(kg_pre)


if __name__ == "__main__":
  unittest.main()
