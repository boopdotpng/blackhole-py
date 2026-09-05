import pytest

from asm import Asm
from ttk.cb import CBRegistry, CBSyncSlot, Layout


class Allocator:
  def __init__(self, address=0x1000): self.address = address

  def alloc(self, size, alignment=None):
    alignment = 1 if alignment is None else alignment
    address = (self.address + alignment - 1) & -alignment
    self.address = address + size
    return address


DTYPE = object()


def test_allocates_two_aligned_slots_and_ids():
  cbs = CBRegistry(Allocator(0x1003))
  first = cbs.create(DTYPE, 64)
  second = cbs.create(DTYPE, 32, id=7, layout=Layout.ROW_MAJOR)
  assert (first.id, first.address, first.size_bytes) == (0, 0x1010, 128)
  assert (second.id, second.address, second.size_bytes) == (7, 0x1090, 64)
  assert cbs.configs == (first, second)


def test_logical_cb_count_is_not_limited_by_sync_slots():
  cbs = CBRegistry(Allocator())
  cb = cbs.create(DTYPE, 64, id=100)
  assert cb.id == 100


def test_depth_is_configurable_and_slot_alignment_is_fixed():
  cbs = CBRegistry(Allocator())
  one = cbs.create(DTYPE, 64, depth=1)
  three = cbs.create(DTYPE, 64, depth=3)
  assert (one.depth, one.size_bytes) == (1, 64)
  assert (three.depth, three.size_bytes) == (3, 192)
  assert [three.slot_address(item) for item in range(5)] == [
    three.address,
    three.address + 64,
    three.address + 128,
    three.address,
    three.address + 64,
  ]
  with pytest.raises(ValueError, match="positive"):
    cbs.create(DTYPE, 64, depth=0)
  with pytest.raises(ValueError, match="preserve the alignment"):
    cbs.create(DTYPE, 18)


def test_internal_cb_is_named_and_reused():
  cbs = CBRegistry(Allocator())
  spill = cbs.internal("dst_spill", DTYPE, 2048, lifetime=(4, 9))
  assert cbs.internal("dst_spill", DTYPE, 2048, lifetime=(4, 9)) is spill
  assert cbs.internal_cbs == {"dst_spill": spill}
  with pytest.raises(ValueError, match="different properties"):
    cbs.internal("dst_spill", DTYPE, 4096, lifetime=(4, 9))


def test_tail_window_and_ring_wrap_split_into_exact_spans():
  cbs = CBRegistry(Allocator())
  cb = cbs.create(DTYPE, 64, depth=3)
  write = cbs.write(cb, item=2, items=2, valid_bytes=80)
  assert [(span.address, span.bytes) for span in write.static_spans()] == [
    (cb.address + 128, 64),
    (cb.address, 16),
  ]


def test_multicast_requires_symmetric_cb():
  cbs = CBRegistry(Allocator())
  local = cbs.write(cbs.create(DTYPE, 64), 0)
  with pytest.raises(ValueError, match="symmetric"):
    cbs.remote_write(local, ((1, 2), (2, 2)), multicast=True)
  symmetric = cbs.write(cbs.create(DTYPE, 64, symmetric=True), 0)
  remote = cbs.remote_write(symmetric, ((1, 2), (2, 2)), multicast=True)
  assert remote.multicast


def test_producer_and_consumer_protocols_assemble():
  cb = CBRegistry(Allocator()).create(DTYPE, 64, depth=3)
  sync = CBSyncSlot(4)

  producer = Asm("brisc")
  sync.reserve_back(producer, cb)
  sync.get_write_ptr(producer, cb, producer.reg())
  sync.push_back(producer, cb)
  assert producer.assemble()

  consumer = Asm("trisc0")
  sync.wait_front(consumer, cb)
  sync.get_read_ptr(consumer, cb, consumer.reg())
  sync.pop_front(consumer, cb)
  assert consumer.assemble()
