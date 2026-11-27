import struct
import unittest

from compiler import BlackholeRenderer, DType, Ops, RVOps, RV32Renderer, UOp, X, X0, dtypes, linearize, rv_label, split_roles, to_program
from test.test_isa import run_rv32


class TestBackendControl(unittest.TestCase):
  def test_physical_buffer_sizes_in_lifetime_plan(self):
    from compiler.memory import _plan_lifetimes
    a, b, c = [UOp.alloc((1,), dtypes.fp32, name=name) for name in ("a", "b", "c")]
    sizes = {a: 1024, b: 256, c: 1024}
    plan = _plan_lifetimes({a: 0, b: 1, c: 2}, {a: 1, b: 2, c: 3}, 256, sizes)
    for left, right in ((a, b), (b, c)):
      self.assertTrue(plan.offsets[left] + sizes[left] <= plan.offsets[right] or
                      plan.offsets[right] + sizes[right] <= plan.offsets[left])
    self.assertEqual(plan.offsets[a], plan.offsets[c])
    self.assertEqual(plan.peak_bytes, 1280)

  def test_sibling_loops_execute_once(self):
    a, b = UOp.range(3, 0, "a"), UOp.range(5, 1, "b")
    root = UOp.sink(X[10].index(a).store(a + 10).end(a), X[11].index(b).store(b + 20).end(b))
    stack = []
    for u in linearize(root):
      if u.op is Ops.RANGE:
        self.assertEqual(stack, [])
        stack.append(u)
      elif u.op is Ops.END: self.assertIs(stack.pop(), u.src[1])
    code = to_program(root, RV32Renderer(wgpr=X[12:28])).src[3].arg
    _, mem = run_rv32(code, {10: 256, 11: 512})
    self.assertEqual(struct.unpack_from("<3I", mem, 256), (10, 11, 12))
    self.assertEqual(struct.unpack_from("<5I", mem, 512), (20, 21, 22, 23, 24))

  def test_role_projection_slices_addresses_and_bounds(self):
    bound = UOp.special(140, "worker_id") + 1
    r = UOp.range(bound, 0)
    address = r * 512
    read = UOp.ins(RVOps.SW, (X0, address, UOp.const(0)), dtypes.void, role="brisc")
    consume = UOp.ins(RVOps.FENCE, (read,), dtypes.void, role="trisc0")
    end = consume.end(r)
    joint = [*bound.toposort(), r, address, read, consume, end]
    cores = {c.arg: c.src for c in split_roles(joint).src}
    self.assertIn(address, cores["brisc"])
    self.assertNotIn(address, cores["trisc0"])
    self.assertNotIn(read, cores["trisc0"])
    for role in ("brisc", "trisc0"):
      self.assertIn(bound, cores[role])
      self.assertIn(r, cores[role])
      self.assertIn(end, cores[role])
    self.assertEqual(cores["trisc1"], ())

  def test_worker_id_load(self):
    root = UOp.sink(X[10].index(0).store(UOp.special(140, "worker_id") + 3))
    code = to_program(root, RV32Renderer(wgpr=X[12:28])).src[3].arg
    mem = bytearray(4096)
    struct.pack_into("<I", mem, 0x28, 137)
    run_rv32(code, {10: 512}, mem)
    self.assertEqual(struct.unpack_from("<I", mem, 512)[0], 140)

  def test_repeated_instruction_in_separate_role_loops(self):
    a, b = UOp.range(3, 0), UOp.range(5, 1)
    effect = UOp.ins(RVOps.FENCE, (), dtypes.void, role="trisc1")
    first, second = effect.end(a), effect.end(b)
    core = split_roles([a, effect, first, b, effect, second]).src[3]
    self.assertEqual(core.src, (a, effect, first, b, effect, second))

  def test_signed_small_loads(self):
    for dt, packed in ((DType("i8", 8, is_signed=True), b"\x80"), (DType("i16", 16, is_signed=True), b"\x00\x80")):
      # Use typed physical pointers to select the load width; the cast is
      # representation-only after a sign-extending load.
      from compiler.isa.rv32 import _load_op
      load = UOp.ins(_load_op(dt), (X[10], UOp.const(0)), dtypes.i32, X[12])
      stream = [load, UOp.ins(RVOps.SW, (X[11], load, UOp.const(0)), dtypes.void),
                UOp.ins(RVOps.RET, (), dtypes.void)]
      mem = bytearray(4096)
      mem[256:256 + len(packed)] = packed
      run_rv32(RV32Renderer().assemble(stream), {10: 256, 11: 512}, mem)
      self.assertEqual(struct.unpack_from("<i", mem, 512)[0], -(1 << (dt.bits - 1)))

  def test_long_conditional_branch(self):
    key = UOp(Ops.NOOP, arg="far")
    branch = UOp.ins(RVOps.BEQ, (key, X[10], X0), dtypes.void)
    padding = UOp.ins(RVOps.ADDI, (X[11], UOp.const(1)), dtypes.u32, X[11])
    stream = [branch, *([padding] * 1100), rv_label(key), UOp.ins(RVOps.RET, (), dtypes.void)]
    for ren in (RV32Renderer(), BlackholeRenderer()):
      code = ren.assemble(stream)
      self.assertEqual(run_rv32(code, {10: 0})[0][11], 0)
      self.assertEqual(run_rv32(code, {10: 1})[0][11], 1100)

  def test_runtime_argument_words(self):
    from compiler.isa.rv32 import rv_arg
    lo, hi = rv_arg(15), rv_arg(15, high=True)
    root = UOp.sink(X[10].index(0).store(lo), X[10].index(1).store(hi))
    code = to_program(root, RV32Renderer(wgpr=X[12:28])).src[3].arg
    mem = bytearray(4096)
    struct.pack_into("<Q", mem, 0xF8, 0x8C000001DEADBEEF)
    run_rv32(code, {10: 512}, mem)
    self.assertEqual(struct.unpack_from("<Q", mem, 512)[0], 0x8C000001DEADBEEF)
    with self.assertRaises(ValueError): rv_arg(16)


if __name__ == "__main__": unittest.main()


def test_scalar_expression_first_used_on_skipped_path():
  from compiler.blackhole.scalar import select_scalar
  done = UOp.const(987)
  expr = X[11] * 7 + 3
  def store(offset): return UOp.ins(RVOps.SW, (X0, expr, UOp.const(offset)), dtypes.void)
  stream = [UOp.ins(RVOps.BEQ, (done, X[10], X0), dtypes.void), store(256), rv_label(done),
            store(260), UOp.ins(RVOps.RET, (), dtypes.void)]
  _, code = BlackholeRenderer().compile_core(select_scalar(stream))
  for flag in (0, 1):
    _, mem = run_rv32(code, {10: flag, 11: 13})
    assert struct.unpack_from("<II", mem, 256) == (94 * flag, 94)
