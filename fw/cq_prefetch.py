from asm import KernelBuilder
from cq import (
  CQ_STATE, DISPATCH_PUBLISHED, DISPATCH_RING_BASE, DISPATCH_RING_END, PAGE_SIZE,
  PREFETCH_CREDITS, PREFETCH_PCIE_BASE, PREFETCH_PCIE_END, PREFETCH_PCIE_READ,
  PREFETCH_QUEUE, PREFETCH_QUEUE_ENTRIES, PREFETCH_STAGING, PacketLayout,
)
from fw.consts import CQConfig
from isa import R
from ttk.noc import NOC_MAX_BURST_SIZE

def build_prefetch(core=CQConfig.PREFETCH_CORE):
  fw = KernelBuilder("brisc", core)
  with fw.scope(): _emit_prefetch(fw, fw.reg(11))
  return fw

def _emit_prefetch(fw, state):
  queue, queue_end, ring, used, size, cursor, src, dst, left, chunk, pages = state
  noc = fw.noc(0).initialize(CQConfig.PREFETCH_COORD)
  fw.write32(PREFETCH_CREDITS, (DISPATCH_RING_END - DISPATCH_RING_BASE) // PAGE_SIZE)
  fw.li(queue, PREFETCH_QUEUE)
  fw.li(queue_end, PREFETCH_QUEUE + PREFETCH_QUEUE_ENTRIES * 4)
  fw.li(ring, DISPATCH_RING_BASE)
  fw.li(used, 0)
  fw.read32(cursor, PREFETCH_PCIE_READ)
  fw.label("prefetch_loop")
  fw.lw(size, queue, 0)
  fw.beq(size, R.ZERO, "prefetch_loop")
  fw.slli(size, size, 4)
  fw.mv(src, cursor); fw.li(dst, PREFETCH_STAGING); fw.mv(left, size)
  fw.label("pcie_read_loop")
  fw.beq(left, R.ZERO, "pcie_read_done")
  fw.li(chunk, NOC_MAX_BURST_SIZE)
  fw.bltu(chunk, left, "pcie_read_size")
  fw.mv(chunk, left)
  fw.label("pcie_read_size")
  with noc.read_batch(count=1) as reads:
    reads.issue(src, CQConfig.PCIE_COORD, dst, chunk, src_mid=CQConfig.PCIE_MID,
                return_coord=CQConfig.PREFETCH_COORD)
  fw.add(src, src, chunk); fw.add(dst, dst, chunk); fw.sub(left, left, chunk)
  fw.j("pcie_read_loop")
  fw.label("pcie_read_done")
  fw.sw(R.ZERO, queue, 0)
  fw.add(cursor, cursor, size)
  fw.read32(src, PREFETCH_PCIE_END)
  fw.bltu(cursor, src, "pcie_no_wrap")
  fw.read32(cursor, PREFETCH_PCIE_BASE)
  fw.label("pcie_no_wrap")
  fw.li(src, PREFETCH_STAGING)
  fw.lw(size, src, PacketLayout.TOTAL_SIZE)
  fw.li(pages, PAGE_SIZE - 1); fw.add(pages, size, pages); fw.srli(pages, pages, 12)
  fw.label("wait_dispatch_credit")
  fw.read32(left, PREFETCH_CREDITS); fw.sub(left, left, used)
  fw.bltu(left, pages, "wait_dispatch_credit")
  fw.add(used, used, pages)
  fw.mv(dst, ring); fw.mv(left, size)
  fw.label("dispatch_copy_loop")
  fw.beq(left, R.ZERO, "dispatch_copy_done")
  fw.li(chunk, NOC_MAX_BURST_SIZE)
  fw.bltu(chunk, left, "dispatch_copy_size")
  fw.mv(chunk, left)
  fw.label("dispatch_copy_size")
  with noc.write_ack_batch(count=1) as writes: writes.issue(src, dst, CQConfig.DISPATCH_COORD, chunk)
  fw.add(src, src, chunk); fw.add(dst, dst, chunk); fw.sub(left, left, chunk)
  fw.j("dispatch_copy_loop")
  fw.label("dispatch_copy_done")
  fw.write32(CQ_STATE + 0x20, used)
  with noc.write_ack_batch(count=1) as writes:
    writes.issue(CQ_STATE + 0x20, DISPATCH_PUBLISHED, CQConfig.DISPATCH_COORD, 4)
  fw.slli(left, pages, 12); fw.add(ring, ring, left)
  fw.li(left, DISPATCH_RING_END); fw.bne(ring, left, "dispatch_no_wrap")
  fw.li(ring, DISPATCH_RING_BASE)
  fw.label("dispatch_no_wrap")
  fw.addi(queue, queue, 4); fw.bne(queue, queue_end, "prefetch_loop")
  fw.li(queue, PREFETCH_QUEUE); fw.j("prefetch_loop")
