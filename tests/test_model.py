import pytest

from ttk.model import (Dtype, Kernel, Loop, RegClass, OPS, Vec, dst, loop, sfpu, trace)


def _ops(kernel): return [inst.op for inst in kernel.insts()]


def test_lane_sum_shape():
  def fn(): sfpu.lane_sum(sfpu.const(1.0))
  k = trace(fn)
  ops = _ops(k)
  assert ops.count('sfp.shft2') == 7          # 4 + 2 + 1 rotations
  assert ops.count('sfp.add') == 6            # three row adds, three column adds
  assert ops.count('sfp.transp') == 1
  transp = next(i for i in k.insts() if i.op == 'sfp.transp')
  assert len(set(transp.ins)) == 4            # duplicates copied into distinct registers
  assert OPS['sfp.transp'].fixed == (0, 1, 2, 3)
  assert all(o.cls is RegClass.LREG for o in transp.outs)


def test_rsqrt_uses_temporaries_freely():
  def fn(): sfpu.rsqrt(sfpu.const(4.0))
  k = trace(fn)
  regs = {o for i in k.insts() for o in i.outs}
  assert len(regs) > 8                        # more virtual LRegs than physical: allocator's job
  assert 'sfp.mad' in _ops(k) and 'sfp.iadd' in _ops(k)


def test_loop_carried_ssa():
  def fn():
    with dst(blocks=8) as d:
      initial = sfpu.const(0.0)
      def body(index, acc):
        x = sfpu.load(d)
        return sfpu.mad(x, x, acc)
      sfpu.lane_sum(loop(32, body, carry=initial))
  k = trace(fn)
  node = next(i for i in k.body if isinstance(i, Loop))
  mad = next(i for i in k.insts() if i.op == 'sfp.mad')
  assert mad.outs[0] is not mad.ins[2]
  assert mad.ins[2] is node.arguments[0]
  assert node.yields == mad.outs
  assert node.results[0] is not node.yields[0]
  assert 'carrying' in k.dump() and 'loop.yield' in k.dump()


def test_operand_class_checked():
  def fn():
    with dst(blocks=1) as d:
      sfpu.mad(d, d, d)
  with pytest.raises(TypeError): trace(fn)


def test_ops_require_trace():
  with pytest.raises(RuntimeError): sfpu.const(1.0)


def test_python_branch_rejected():
  def fn():
    v = sfpu.const(1.0)
    if v: pass
  with pytest.raises(TypeError): trace(fn)


def test_stream_order_and_resident_reuse():
  from ttk.model import (Dtype, Buffer, cb, l1, srca, unpack)
  source = Buffer('source', Dtype.bf16, 4096)
  def fn():
    resident = l1.read(source, nbytes=256)
    stream = cb.read(source, item_bytes=512, depth=2)
    def consume(index):
      item = stream.next()
      a = srca.alloc(1)
      unpack(item[:256], into=a)
      unpack(item[256:], into=a)
      unpack(resident, into=a)
      a.free()
      item.release()
    loop(8, consume)
    resident.free()
  k = trace(fn)
  declaration = next(i for i in k.insts() if i.op == 'cb.read')
  assert declaration.attrs['count'] == 8
  assert declaration.attrs['depth'] == 2
  region = next(i for i in k.body if isinstance(i, Loop))
  assert region.body[0].op == 'cb.next'
  assert len([i for i in k.insts() if i.op == 'noc.read']) == 1


def test_free_invalidates_views_and_rejects_loop_escape():
  def freed():
    d = dst.alloc(2)
    view = d[1]
    d.free()
    sfpu.load(view)
  with pytest.raises(ValueError, match='use after free'): trace(freed)
  def escaped():
    values = []
    loop(2, lambda i: values.append(sfpu.const(1)))
    values[0] + 1
  with pytest.raises(ValueError, match='escaped'): trace(escaped)
  def enclosing():
    d = dst.alloc(1)
    loop(2, lambda i: d.free())
  with pytest.raises(ValueError, match='enclosing'): trace(enclosing)


def test_physical_positions_cover_block_and_preserve_masked_destination():
  assert sfpu.lane_element(0, 0) == 0
  assert sfpu.lane_element(0, 8) == 16
  assert sfpu.lane_element(1, 0) == 1
  assert sfpu.lane_element(2, 0) == 64
  assert sorted(sfpu.lane_element(p, l) for p in range(4) for l in range(32)) == list(range(128))
  def fn():
    d = dst.alloc(1)
    old = sfpu.const(7)
    sfpu.predicate(0x55555555)
    old = sfpu.load(d[0], position=1, previous=old)
    sfpu.predicate()
    sfpu.store(old, d[0], position=1)
    d.free()
  k = trace(fn)
  load = next(i for i in k.insts() if i.op == 'sfp.load')
  assert load.ins[1] is not load.outs[0]
  assert load.attrs['inactive'] == 'previous'
  assert load.attrs['predicate'] == 0x55555555


def test_compositions_expand_and_preserve_predicate():
  from ttk.model import (exp, reciprocal, swiglu)
  def fn():
    sfpu.predicate(15)
    x = sfpu.const(0.5)
    exp(x)
    reciprocal(x)
    swiglu(x, x)
    sfpu.predicate()
  k = trace(fn)
  assert _ops(k).count('sfp.arecip') == 2
  assert all(i.attrs['predicate'] == 15 for i in k.insts() if i.op != 'sfp.predicate')
  assert not any(i.op in ('exp', 'reciprocal', 'swiglu') for i in k.insts())


def test_rmsnorm_sketch_traces_physical_indexing():
  from ttk.model import (Dtype, Buffer, LaneView)
  from ttk.sketches.rmsnorm_embedding import rmsnorm_embedding, N
  k = trace(rmsnorm_embedding, Buffer('emb', Dtype.bf16, N*2*16),
            *(Buffer(name, Dtype.bf16, N*2) for name in ('gamma', 'residual', 'normalized')))
  loads = [i for i in k.insts() if i.op == 'sfp.load']
  assert {i.attrs['position'] for i in loads} == set(range(4))
  assert all(isinstance(i.ins[0], LaneView) for i in loads)
  assert _ops(k).count('noc.write') == 2


def test_loop_index_cannot_escape_and_trace_ownership():
  def escaped():
    indices = []
    loop(2, lambda i: indices.append(i))
    indices[0] + 1
  with pytest.raises(ValueError, match='escaped'): trace(escaped)
  values = []
  trace(lambda: values.append(sfpu.const(1)))
  with pytest.raises(ValueError, match='another trace'): trace(lambda: values[0] + 1)


def test_exp_recipe_numerics_on_cpu():
  import math
  import struct
  from ttk.model import (exp)
  def fp32(x): return struct.unpack('<f', struct.pack('<f', x))[0]
  for value in (-10, -1, 0, 1, 10):
    outputs = []
    k = trace(lambda: outputs.append(exp(sfpu.const(value))))
    registers = {}
    for inst in k.insts():
      if inst.op == 'sfp.const':
        result = struct.unpack('<f', struct.pack('<I', inst.attrs['bits']))[0]
      elif inst.op == 'sfp.mul':
        result = registers[inst.ins[0]] * registers[inst.ins[1]]
      elif inst.op == 'sfp.mad':
        result = registers[inst.ins[0]] * registers[inst.ins[1]] + registers[inst.ins[2]]
      else: raise AssertionError(inst.op)
      registers[inst.outs[0]] = fp32(result)
    assert registers[outputs[0].reg] == pytest.approx(math.exp(value), rel=5e-5)


def test_effects_separate_allocation_reads_writes_and_accumulation():
  from ttk.model import (l1, srca, srcb, unpack, pack, fpu, Access)
  def fn():
    data = l1.alloc(256)
    a, b, d = srca.alloc(1), srcb.alloc(1), dst.alloc(2)
    unpack(data, into=a)
    unpack(data, into=b)
    fpu.op('mul', a, b, into=d[1])
    fpu.op('mul', a, b, into=d[1], accumulate=True)
    pack(d[1], into=data)
    d.free()
  k = trace(fn)
  allocation = k.insts()[0]
  assert allocation.allocates and not allocation.writes
  transfer = next(i for i in k.insts() if i.op == 'unpack')
  assert transfer.reads == (Access(transfer.ins[0]),)
  assert transfer.writes == (Access(transfer.ins[1]),)
  overwrite, accumulate = [i for i in k.insts() if i.op == 'fpu.mul']
  assert len(overwrite.reads) == 2
  assert len(accumulate.reads) == 3
  assert overwrite.writes[0].target.offset == 1
  release = k.insts()[-1]
  assert release.releases and not release.reads and not release.writes
  assert 'reads=' in k.dump(effects=True)


def test_symbolic_gather_and_lane_addresses_are_dependencies():
  from ttk.model import (Dtype, Buffer, BufferRange, LaneView, MemorySpace, noc, kernel)
  table = Buffer('table', Dtype.bf16, 4096)
  def fn():
    token = kernel.param("token_id")
    noc.read(table, offset=token * 256, nbytes=256, resident=True)
    d = dst.alloc(2)
    def body(block):
      for lane in sfpu.lanes(d[block]): sfpu.load(lane)
    loop(2, body)
  k = trace(fn)
  gather = next(i for i in k.insts() if i.op == 'noc.read')
  external = next(a.target for a in gather.reads if isinstance(a.target, BufferRange))
  assert external.buffer.space is MemorySpace.DRAM
  assert any(a.target is external.offset for a in gather.reads)
  loads = [i for i in k.insts() if i.op == 'sfp.load']
  assert len(loads) == 4
  for inst in loads:
    lane = next(a.target for a in inst.reads if isinstance(a.target, LaneView))
    assert any(a.target is lane.block.offset for a in inst.reads)


def test_masked_updates_define_fresh_ssa_values():
  def fn():
    d = dst.alloc(1)
    old = sfpu.const(7)
    sfpu.predicate(15)
    loaded = sfpu.load(d[0], previous=old)
    result = sfpu.mad(1, 2, 3, previous=loaded)
    sfpu.store(result, d[0])
    sfpu.predicate()
  k = trace(fn)
  load = next(i for i in k.insts() if i.op == 'sfp.load')
  old = load.ins[1]
  assert load.outs[0] is not old
  assert any(a.target is old for a in load.reads)
  assert not load.writes[0].partial
  mad = next(i for i in k.insts() if i.op == 'sfp.mad')
  assert mad.ins[-1] is load.outs[0] and mad.outs[0] is not load.outs[0]
  store = next(i for i in k.insts() if i.op == 'sfp.store')
  assert store.writes[0].partial and store.writes[0].mask == 15


def test_lanes_reject_ranges_and_use_after_free():
  def wide(): sfpu.lanes(dst.alloc(2)[:])
  with pytest.raises(ValueError, match='one Dst block'): trace(wide)
  def freed():
    d = dst.alloc(1)
    lane = sfpu.lanes(d[0])[0]
    d.free()
    sfpu.load(lane)
  with pytest.raises(ValueError, match='use after free'): trace(freed)


def test_stream_effects_keep_external_source_cursor_and_explicit_release():
  from ttk.model import (Dtype, Buffer, cb, StreamRange)
  def fn():
    stream = cb.read(Buffer('weights', Dtype.bf16, 4096), item_bytes=512, depth=2)
    def consume(index):
      item = stream.next()
      item.release()
    loop(8, consume)
  k = trace(fn)
  acquire = next(i for i in k.insts() if i.op == 'cb.next')
  source = next(a.target for a in acquire.reads if isinstance(a.target, StreamRange))
  assert source.extent == 512 and source.stride == 512
  release = next(i for i in k.insts() if i.op == 'cb.release')
  assert release.releases == acquire.outs
  assert release.writes[0].target == ('cb.credits', source.cursor)


def test_runtime_parameter_and_dram_read_are_distinct():
  from ttk.model import Dtype, Buffer, noc, kernel
  outputs = []
  def fn():
    outputs.extend((kernel.param('token_id'), noc.read(Buffer('data', Dtype.u32, 16), nbytes=4)))
  k = trace(fn)
  scalar, data = outputs
  assert scalar.cls is RegClass.GPR and scalar.extent == 1
  assert data.cls is RegClass.L1 and data.extent == 4
  assert k.params[0].name == 'token_id' and k.params[0].value is scalar
  assert 'noc.read_scalar' not in _ops(k)


def test_named_blocks_and_srca_pair_alignment():
  from ttk.model import (srca, srcb, fpu, l1)
  def fn(offset):
    a, b, d = srca.alloc(4), srcb.alloc(1), dst.alloc(1)
    fpu.op('mvmul', a.blocks(offset=offset, count=2), b, into=d)
  k = trace(lambda: fn(2))
  read = next(i for i in k.insts() if i.op == 'fpu.mvmul').reads[0]
  assert read.alignment == 2 and read.target.reg.alignment == 2
  with pytest.raises(ValueError, match='even block'): trace(lambda: fn(1))
  with pytest.raises(TypeError, match='L1 offsets are bytes'):
    trace(lambda: l1.alloc(512).blocks(count=1))


def test_parameters_are_hoisted_deduplicated_and_visible_after_loops():
  from ttk.model import kernel, Dtype
  values = []
  def fn():
    def body(index):
      value = kernel.param('token_id', dtype=Dtype.u32)
      values.append(value)
      value + 1
    loop(2, body)
    values.append(kernel.param('token_id'))
    loop(values[0], lambda i: None)
  k = trace(fn)
  assert values[0] is values[1]
  assert len(k.params) == 1
  assert k.body[0].op == 'kernel.param'
  assert _ops(k).count('kernel.param') == 1
  assert k.body[-1].count is values[0]
  assert k.body[0].reads[0].target is k.params[0]


def test_parameter_validation_and_symbolic_control_flow():
  from ttk.model import kernel, Dtype
  def conflict():
    kernel.param('n')
    kernel.param('n', dtype=Dtype.i32)
  with pytest.raises(TypeError, match='conflicting'): trace(conflict)
  with pytest.raises(ValueError, match='nonempty'): trace(lambda: kernel.param(''))
  with pytest.raises(TypeError, match='i32/u32'): trace(lambda: kernel.param('x', dtype=Dtype.f32))
  with pytest.raises(ValueError, match='invocation lifetime'): trace(lambda: kernel.param('n').free())
  with pytest.raises(TypeError, match='symbolic'): trace(lambda: bool(kernel.param('n')))
  with pytest.raises(TypeError): trace(lambda: range(kernel.param('n')))
  with pytest.raises(RuntimeError): kernel.param('outside')


def test_parameter_declarations_are_per_kernel():
  from ttk.model import kernel
  first = trace(lambda: kernel.param('n'))
  second = trace(lambda: kernel.param('n'))
  assert first.params[0].value is not second.params[0].value
  with pytest.raises(ValueError, match='another trace'):
    trace(lambda: first.params[0].value + 1)


@pytest.mark.parametrize('count, expected', [(0, 2.0), (1, 8.0), (3, 80.0)])
def test_ssa_loop_recurrence_on_cpu(count, expected):
  """Execute the value/loop subset independently, including nested loop results."""
  captured = []
  def fn():
    def outer_body(index, acc):
      def inner_body(inner_index, inner_acc):
        return inner_acc + acc
      return loop(2, inner_body, carry=acc) + 2
    captured.append(loop(count, outer_body, carry=sfpu.const(2)).reg)
  k = trace(fn)
  values = {}
  def execute(items):
    for item in items:
      if isinstance(item, Loop):
        carried = [values[v] for v in item.initial]
        for index in range(item.count):
          values[item.index] = index
          values.update(zip(item.arguments, carried))
          execute(item.body)
          carried = [values[v] for v in item.yields]
        values.update(zip(item.results, carried))
      elif item.op == 'sfp.const': values[item.outs[0]] = item.ins[0]
      elif item.op == 'sfp.add': values[item.outs[0]] = sum(values[v] for v in item.ins)
      elif item.op != 'loop.yield': raise AssertionError(item.op)
  execute(k.body)
  # One outer iteration computes 3*acc + 2.
  reference = 2.0
  for _ in range(count): reference = 3 * reference + 2
  assert values[captured[0]] == reference == expected


def test_gpr_loop_carry_and_result_addressing():
  from ttk.model import kernel, Buffer, Dtype, noc
  def fn():
    start = kernel.param('offset')
    offset = loop(2, lambda i, address: address + 256, carry=start)
    noc.read(Buffer('input', Dtype.bf16, 4096), offset=offset, nbytes=256)
  k = trace(fn)
  node = next(i for i in k.body if isinstance(i, Loop))
  assert node.results[0].dtype is Dtype.u32
  assert any(a.target is node.results[0] for a in k.body[-1].reads)


def test_callback_carry_scope_and_storage_rejection():
  def escaped():
    values = []
    def body(index, acc):
      result = acc + 1
      values.append(result)
      return result
    loop(2, body, carry=sfpu.const(0))
    values[0] + 1
  with pytest.raises(ValueError, match='escaped'): trace(escaped)
  with pytest.raises(TypeError, match='not storage'):
    trace(lambda: loop(2, lambda i, value: value, carry=dst.alloc(1)))


def test_verifier_rejects_duplicate_definitions_and_non_dominating_reads():
  def fn():
    a = sfpu.const(1)
    a + 2
  k = trace(fn)
  k.body.append(k.body[0])
  with pytest.raises(ValueError, match='more than once'): k.verify()
  k = trace(fn)
  k.body[0], k.body[-1] = k.body[-1], k.body[0]
  with pytest.raises(ValueError, match='dominate'): k.verify()


def test_old_sfpu_into_syntax_is_rejected():
  def fn():
    old = sfpu.const(1)
    sfpu.mad(old, old, old, into=old)
  with pytest.raises(TypeError, match='into'): trace(fn)


def test_bits_constant_dump_is_hexadecimal():
  k = trace(lambda: sfpu.const_bits(0x5f1110a0))
  assert 'sfp.const_bits(0x5f1110a0)' in k.dump()
  assert 'const(0.0)' not in k.dump()


def test_multiple_loop_carried_values_have_independent_edges():
  from ttk.model import kernel
  def fn():
    initial = sfpu.const(0)
    index = kernel.param('start')
    value, offset = loop(3, lambda i, value, offset: (value + 1, offset + 2), carry=(initial, index))
    sfpu.lane_sum(value)
    offset + 4
  k = trace(fn)
  node = next(i for i in k.body if isinstance(i, Loop))
  assert len(node.initial) == len(node.arguments) == len(node.yields) == len(node.results) == 2
  assert [v.cls for v in node.results] == [RegClass.LREG, RegClass.GPR]
  assert len(set((*node.initial, *node.arguments, *node.yields, *node.results))) == 8


def test_predicated_ssa_mad_preserves_old_value_on_cpu():
  captured = []
  def fn():
    old = sfpu.const(7)
    a, b, c = sfpu.const(2), sfpu.const(3), sfpu.const(2)
    sfpu.predicate(0x55555555)
    result = sfpu.mad(a, b, c, previous=old)
    sfpu.predicate()
    captured.extend((old.reg, result.reg))
  k = trace(fn)
  values = {}
  for inst in k.insts():
    if inst.op == 'sfp.const': values[inst.outs[0]] = [inst.ins[0]] * 32
    elif inst.op == 'sfp.mad':
      a, b, c, previous = (values[v] for v in inst.ins)
      values[inst.outs[0]] = [a[i]*b[i]+c[i] if inst.attrs['predicate'] & (1 << i) else previous[i]
                             for i in range(32)]
  assert captured[0] is not captured[1]
  assert values[captured[0]] == [7] * 32
  assert values[captured[1]] == [8 if i % 2 == 0 else 7 for i in range(32)]


def test_callback_loops_trace_once_and_support_tuple_carry():
  from ttk.model import kernel
  calls = []
  def fn():
    def body(index, value, address):
      calls.append('body')
      return value + 1, address + 256
    value, address = loop(100, body, carry=(sfpu.const(0), kernel.param('address')))
    def consume(index):
      calls.append('consume')
      address + index
    assert loop(100, consume) is None
    sfpu.lane_sum(value)
  k = trace(fn)
  assert calls == ['body', 'consume']
  loops = [i for i in k.body if isinstance(i, Loop)]
  assert len(loops[0].results) == 2
  assert not loops[1].initial and not loops[1].results


def test_callback_return_contracts():
  with pytest.raises(TypeError, match='without carry'):
    trace(lambda: loop(2, lambda i: sfpu.const(1)))
  with pytest.raises(TypeError, match='tuple return'):
    trace(lambda: loop(2, lambda i, x: x, carry=(sfpu.const(0),)))
  with pytest.raises(TypeError, match='scalar return'):
    trace(lambda: loop(2, lambda i, x: (x,), carry=sfpu.const(0)))
  with pytest.raises(ValueError, match='arity'):
    trace(lambda: loop(2, lambda i, x: (), carry=(sfpu.const(0),)))
  with pytest.raises(TypeError, match='type mismatch'):
    trace(lambda: loop(2, lambda i, x: i, carry=sfpu.const(0)))


def test_dst_affine_offsets_fold_without_gpr_arithmetic():
  from ttk.model import AffineIndex
  def fn():
    d = dst.alloc(32)
    gamma = d.blocks(offset=16, count=16)
    def body(block):
      sfpu.load(gamma[block])
      sfpu.load(d[block + 16])
      sfpu.load(d[16 + block + 2 - 2])
    loop(16, body)
  k = trace(fn)
  assert 'gpr.add' not in _ops(k)
  loads = [i for i in k.insts() if i.op == 'sfp.load']
  offsets = [i.ins[0].block.offset for i in loads]
  assert all(isinstance(v, AffineIndex) and v.constant == 16 for v in offsets)
  assert all(v.index is offsets[0].index for v in offsets)
  assert all(any(a.target is offsets[0].index for a in i.reads) for i in loads)
  assert '+ 16:+1]' in k.dump()


@pytest.mark.parametrize('kind', ['scaled', 'parameter', 'two_indices', 'escaped'])
def test_dst_rejects_non_counter_indices(kind):
  from ttk.model import kernel
  def fn():
    d = dst.alloc(32)
    captured = []
    def body(block):
      if kind == 'scaled': sfpu.load(d[block * 2])
      elif kind == 'parameter': sfpu.load(d[kernel.param('offset')])
      elif kind == 'two_indices':
        loop(2, lambda inner: sfpu.load(d[block + inner]))
      else: captured.append(block + 1)
    loop(2, body)
    if kind == 'escaped': sfpu.load(d[captured[0]])
  with pytest.raises(ValueError, match='induction|escaped'): trace(fn)


def test_affine_index_materializes_for_noc_but_not_dst():
  from ttk.model import noc, Buffer, Dtype
  def fn():
    d = dst.alloc(4)
    source = Buffer('input', Dtype.bf16, 4096)
    def body(index):
      offset = index + 1
      sfpu.load(d[offset])
      noc.read(source, offset=offset * 256, nbytes=256)
    loop(2, body)
  k = trace(fn)
  assert _ops(k).count('gpr.add') == 1
  assert _ops(k).count('gpr.mul') == 1
  assert '+ 1:+1]' in k.dump()


def test_dump_suppresses_default_inactive_annotation_only():
  def fn():
    d = dst.alloc(1)
    old = sfpu.const(7)
    value = sfpu.load(d)
    sfpu.predicate(15)
    value = sfpu.load(d, previous=old)
    sfpu.store(value, d)
    sfpu.predicate()
  k = trace(fn)
  assert "inactive='undefined'" not in k.dump()
  assert "inactive='previous'" in k.dump()
  assert "inactive='preserve'" in k.dump()
  assert any(i.attrs.get('inactive') == 'undefined' for i in k.insts())


def test_loop_requires_callback():
  with pytest.raises(TypeError, match='body'): loop(2)
  with pytest.raises(TypeError, match='callable'): loop(2, None)


def test_compact_dump_hides_defaults_but_keeps_active_masks_and_sizes():
  from ttk.model import Buffer, Dtype, noc
  def fn():
    data = noc.read(Buffer('input', Dtype.bf16, 256))
    d = dst.alloc(1)
    x = sfpu.const(2)
    sfpu.const_bits(0x5f1110a0)
    sfpu.load(d)
    sfpu.predicate(0)
    sfpu.mul(x, x)
    sfpu.predicate()
    data.free()
  k = trace(fn)
  compact, verbose = k.dump(), k.dump(effects=True)
  for noise in ('predicate=None', 'position=', 'bits=', 'Buffer(', 'completion=', '<Dtype.'):
    assert noise not in compact
  assert 'source=@input' in compact
  assert 'dst.alloc(blocks=1, dtype=f32)' in compact
  assert 'predicate=0x00000000' in compact
  assert 'sfp.predicate(all)' in compact
  assert 'sfp.const_bits(0x5f1110a0)' in compact
  assert 'predicate=None' in verbose and "completion='before_use'" in verbose
  assert 'Buffer(' in verbose and 'reads=' in verbose
