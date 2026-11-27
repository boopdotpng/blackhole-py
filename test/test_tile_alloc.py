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
  allocated, addresses = allocate_cb_stream(stream, sizes)
  verify_tile_stream(allocated)
  assert len(addresses) < 32
  assert any(u.is_ins and isinstance(u.ins_op, CbOp) and u.ins_op.kind == 'wait' and u.ins_op.role == 'brisc' for u in allocated)
