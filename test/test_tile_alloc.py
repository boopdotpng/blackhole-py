import pytest
from compiler.blackhole.alloc import TileAllocator


def test_dst_contiguous_lifetimes_and_spill_reservation():
  alloc = TileAllocator()
  a, b, c = alloc.dst(16), alloc.dst(16), alloc.dst(24)
  assert (a, b, c) == (0, 16, 32)
  with pytest.raises(MemoryError, match='limit 56'): alloc.dst()
  alloc.release_dst(b)
  assert alloc.dst(8) == 16
  assert alloc.dst(8) == 24
  alloc.release_dst(a)
  alloc.release_dst(c)
  with pytest.raises(MemoryError, match='contiguous'): alloc.dst(25)
  with pytest.raises(ValueError): alloc.release_dst(c)


def test_cb_reuse_preserves_static_configuration():
  alloc = TileAllocator()
  first = alloc.cb(4097)
  second = alloc.cb(1)
  assert alloc.cb_addrs == {first: 0x20000, second: 0x22000}
  alloc.release_cb(first)
  assert alloc.cb(256) == first
  assert alloc.cb_addrs[first] == 0x20000
  assert alloc.cb(8193) == 2
  assert alloc.cb_addrs[2] == 0x23000


def test_limits_and_failed_allocation_are_atomic():
  alloc = TileAllocator()
  for _ in range(32): alloc.cb()
  with pytest.raises(MemoryError, match='32'): alloc.cb()
  alloc.release_cb(7)
  assert alloc.cb() == 7
  alloc = TileAllocator()
  alloc.cb(0x160000)
  with pytest.raises(MemoryError, match='L1'): alloc.cb()
  assert len(alloc.cb_addrs) == 1
  alloc.release_cb(0)
  assert alloc.cb() == 0


def test_phase_reuse_orders_producers():
  from compiler import UOp, dtypes, linearize
  from compiler.blackhole.pipeline import instruction, insert_syncs, verify_tile_stream
  from compiler.blackhole.alloc import allocate_cb_stream
  from compiler.blackhole.specs import NocRead, UnpackOp, Space, SfpLoadOp, SfpStoreOp, PackOp, NocWrite, CbOp
  dependency = UOp.noop()
  sizes = {}
  for phase in range(40):
    cb, out = phase * 2, phase * 2 + 1
    sizes[cb] = sizes[out] = 4096
    read = instruction(NocRead(0, cb, 512), UOp.const(0).after(dependency))
    unpack = instruction(UnpackOp(Space.DST, cb), read)
    fp = UOp.range(UOp.const(4).after(dependency), phase, 'fp')
    value = instruction(SfpLoadOp(0), unpack, fp, dtype=dtypes.fp32)
    stored = instruction(SfpStoreOp(0), value + 1, fp).end(fp)
    packed = instruction(PackOp(out), stored)
    dependency = instruction(NocWrite(1, out, 512), packed, UOp.const(0))
  stream = insert_syncs(linearize(UOp.sink(dependency)))
  allocated, addresses, depths, pages = allocate_cb_stream(stream, sizes)
  verify_tile_stream(allocated)
  assert len(addresses) < 32
  assert all(d == 1 for d in depths.values())
  assert any(u.is_ins and isinstance(u.ins_op, CbOp) and u.ins_op.kind == 'wait' and u.ins_op.role == 'brisc' for u in allocated)


def test_streaming_cb_default_depth_and_l1_stepdown():
  from compiler import UOp, dtypes, linearize
  from compiler.blackhole.pipeline import instruction, insert_syncs, verify_tile_stream
  from compiler.blackhole.alloc import allocate_cb_stream
  from compiler.blackhole.specs import NocRead, UnpackOp, Space, SfpLoadOp, SfpStoreOp, PackOp, NocWrite, CbOp

  def build_stream(a_size, w_size, iters=10):
    outer = UOp.range(iters, 0, 'out')
    r0 = instruction(NocRead(0, 0, a_size), outer)
    r1 = instruction(NocRead(1, 1, w_size), outer)
    u0 = instruction(UnpackOp(Space.DST, 0, dst_slot=0), r0)
    u1 = instruction(UnpackOp(Space.DST, 1, dst_slot=1), r1)
    fp = UOp.range(UOp.const(1).after(outer), 1, 'fp')
    v0 = instruction(SfpLoadOp(0), u0, fp, dtype=dtypes.fp32)
    v1 = instruction(SfpLoadOp(1), u1, fp, dtype=dtypes.fp32)
    st = instruction(SfpStoreOp(0), v0 + v1, fp).end(fp)
    pk = instruction(PackOp(2, dst_slot=0), st)
    wr = instruction(NocWrite(2, 2, 512), pk, outer).end(outer)
    return insert_syncs(linearize(UOp.sink(wr)))

  # Normal streaming kernel: all 3 streaming CBs get depth 3 with no fence.
  stream = build_stream(64 * 1024, 64 * 1024, iters=10)
  allocated, addrs, depths, pages = allocate_cb_stream(stream, {0: 64 * 1024, 1: 64 * 1024, 2: 4096})
  verify_tile_stream(allocated)
  assert depths == {0: 3, 1: 3, 2: 3}
  assert addrs[1] - addrs[0] == 3 * 64 * 1024
  assert addrs[2] - addrs[1] == 3 * 64 * 1024
  assert not any(u.is_ins and isinstance(u.ins_op, CbOp) and u.ins_op.kind == 'wait' and u.ins_op.role == 'brisc' for u in allocated)

  # Tight L1 (like down_proj: 344 KiB + 200 KiB + 4 KiB): largest page steps down 3 -> 2.
  stream = build_stream(344 * 1024, 200 * 1024, iters=4)
  allocated, addrs, depths, pages = allocate_cb_stream(stream, {0: 344 * 1024, 1: 200 * 1024, 2: 4096})
  verify_tile_stream(allocated)
  assert depths == {0: 2, 1: 3, 2: 3}
  assert max(addrs[i] + pages[i] * depths[i] for i in addrs) <= 0x180000

  # Single-iteration loop: caps depth at 1 to avoid wasting L1.
  stream = build_stream(64 * 1024, 64 * 1024, iters=1)
  _, _, depths, _ = allocate_cb_stream(stream, {0: 64 * 1024, 1: 64 * 1024, 2: 4096})
  assert depths == {0: 1, 1: 1, 2: 1}


def test_contiguous_group_strips_after():
  from compiler import UOp, dtypes
  from compiler.blackhole.recipes import contiguous_group
  lane = UOp.special(128, "gather_lane")
  dep = UOp.range(4, 0, "outer")
  offset = ((lane // 16) * 16 + (lane % 16)) * 2
  valid = lane // 16 < 8
  _, count, _, _ = contiguous_group((offset.after(dep), valid), 128, 2, 100)
  assert count == 16
