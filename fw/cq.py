from asm import Asm
from cq import (
  ALIGN, CQ_STATE, DISPATCH_DONE_COUNT, DISPATCH_DRAM_PUT,
  DISPATCH_DRAM_READ, DISPATCH_GO, DISPATCH_PUBLISHED, DISPATCH_READ_PUBLISH,
  DISPATCH_RING_BASE, DISPATCH_RING_END, DISPATCH_RING_PAGES,
  DRAM_PUBLISHED, DRAM_QUEUE_BASE, DRAM_QUEUE_ENTRIES, DRAM_READ_PUBLISH,
  HOST_ISSUE_SIZE,
  PAGE_SIZE, PREFETCH_DISPATCH_READ, PREFETCH_DOORBELL, PREFETCH_PCIE_BASE,
  PREFETCH_READ_PTR, PREFETCH_READ_PUBLISH, PREFETCH_RECORD_SIZE,
  PREFETCH_STAGING, PREFETCH_TRACE_ACTIVE, PREFETCH_TRACE_CURSOR,
  PREFETCH_TRACE_END, Op, PacketLayout,
)
from fw.consts import CQConfig, FirmwareControl, RunState
from isa import R
from ttk.noc import NiuCommand

PREFETCH_DISPATCH_PUBLISH = CQ_STATE + 0x40


def build_prefetch(pcie_mid=CQConfig.PCIE_MID):
  fw = Asm("brisc")
  with fw.scope(): _emit_prefetch(fw, fw.reg(12), pcie_mid)
  return fw


def _emit_prefetch(fw, state, pcie_mid):
  (
    ring, put, size, cursor, src, dst, left, chunk, pages, remaining,
    read_lo, read_hi,
  ) = state
  noc = fw.noc
  fw.li(ring, DISPATCH_RING_BASE)
  fw.li(put, 0)
  fw.li(read_lo, 0)
  fw.li(read_hi, 0)
  fw.write(PREFETCH_DISPATCH_READ, 0)
  fw.write(PREFETCH_TRACE_ACTIVE, 0)

  fw.label("prefetch_loop")
  fw.read(src, PREFETCH_TRACE_ACTIVE)
  fw.bne(src, R.ZERO, "trace_header")

  # The host publishes an eight-byte monotonic put pointer after writing all
  # record bytes. Read high/low/high so a carry cannot look like a huge put.
  fw.label("read_doorbell")
  fw.read(remaining, PREFETCH_DOORBELL + 4)
  fw.read(src, PREFETCH_DOORBELL)
  fw.read(dst, PREFETCH_DOORBELL + 4)
  fw.bne(remaining, dst, "read_doorbell")
  fw.bne(dst, read_hi, "host_header")
  fw.bne(src, read_lo, "host_header")
  fw.fence(); fw.j("prefetch_loop")

  fw.label("host_header")
  fw.read(cursor, PREFETCH_PCIE_BASE)
  fw.li(dst, HOST_ISSUE_SIZE - 1)
  fw.and_(dst, read_lo, dst)
  fw.add(cursor, cursor, dst)
  fw.j("read_header")

  fw.label("trace_header")
  fw.read(cursor, PREFETCH_TRACE_CURSOR)

  # Every source record starts with one aligned header. PAD consumes host-ring
  # space without entering the dispatch ring; TRACE switches to its immutable
  # host record stream while leaving the issue read pointer parked.
  fw.label("read_header")
  noc.read(
    cursor, CQConfig.PCIE_COORD, PREFETCH_STAGING, ALIGN,
    source_middle_address=pcie_mid,
  )
  fw.read(src, PREFETCH_STAGING + PacketLayout.OP, bytes=1)
  fw.read(dst, PREFETCH_TRACE_ACTIVE)
  fw.bne(dst, R.ZERO, "normal_record")
  fw.li(dst, int(Op.PAD)); fw.beq(src, dst, "issue_pad")
  fw.li(dst, int(Op.TRACE)); fw.bne(src, dst, "normal_record")
  fw.read(cursor, PREFETCH_STAGING + PacketLayout.TRACE_SOURCE_LO)
  fw.read(size, PREFETCH_STAGING + PacketLayout.TRACE_SIZE)
  fw.write(PREFETCH_TRACE_CURSOR, cursor)
  fw.add(dst, cursor, size)
  fw.write(PREFETCH_TRACE_END, dst)
  fw.write(PREFETCH_TRACE_ACTIVE, 1)
  fw.j("trace_header")

  fw.label("issue_pad")
  fw.read(size, PREFETCH_STAGING + PacketLayout.TOTAL_SIZE)
  fw.j("advance_issue")

  fw.label("normal_record")
  fw.read(size, PREFETCH_STAGING + PacketLayout.TOTAL_SIZE)
  fw.write(PREFETCH_RECORD_SIZE, size)
  fw.mv(src, cursor); fw.li(dst, PREFETCH_STAGING); fw.mv(left, size)
  fw.label("pcie_read_loop")
  fw.beq(left, R.ZERO, "pcie_read_done")
  fw.li(chunk, NiuCommand.MAX_PACKET_BYTES)
  fw.bltu(chunk, left, "pcie_read_size")
  fw.mv(chunk, left)
  fw.label("pcie_read_size")
  noc.read(
    src, CQConfig.PCIE_COORD, dst, chunk,
    source_middle_address=pcie_mid,
  )
  fw.add(src, src, chunk); fw.add(dst, dst, chunk); fw.sub(left, left, chunk)
  fw.j("pcie_read_loop")
  fw.label("pcie_read_done")

  fw.li(src, PREFETCH_STAGING)
  # DRAM_RECORD is a compact indirection used by the resident program cache.
  # Replace the descriptor in staging with the immutable lowered CQ record.
  fw.lbu(dst, src, PacketLayout.OP)
  fw.li(left, int(Op.DRAM_RECORD))
  fw.bne(dst, left, "record_ready")
  fw.lw(left, src, PacketLayout.ADDRESS)
  fw.lw(chunk, src, PacketLayout.DATA_SIZE)
  fw.lw(dst, src, PacketLayout.DRAM_COORD)
  noc.read(left, dst, PREFETCH_STAGING, chunk)
  fw.li(src, PREFETCH_STAGING)
  fw.label("record_ready")
  fw.lw(size, src, PacketLayout.TOTAL_SIZE)
  fw.li(pages, PAGE_SIZE - 1); fw.add(pages, size, pages); fw.srli(pages, pages, 12)

  # The dispatch ring uses the same monotonic put/read model as the host ring.
  # Insert one dispatch-local PAD when an expanded record would straddle it.
  fw.li(remaining, DISPATCH_RING_END)
  fw.sub(remaining, remaining, ring)
  fw.srli(remaining, remaining, 12)
  fw.bgeu(remaining, pages, "wait_dispatch_space")
  fw.label("wait_wrap_space")
  fw.read(left, PREFETCH_DISPATCH_READ)
  fw.sub(left, put, left)
  fw.li(chunk, DISPATCH_RING_PAGES); fw.sub(chunk, chunk, left)
  fw.bgeu(chunk, remaining, "wrap_space_ready")
  fw.fence(); fw.j("wait_wrap_space")
  fw.label("wrap_space_ready")
  fw.add(put, put, remaining)
  fw.write(CQ_STATE + 0x60 + PacketLayout.OP, int(Op.PAD), bytes=1)
  fw.write(CQ_STATE + 0x60 + PacketLayout.TARGET_COUNT, 0, bytes=2)
  fw.slli(left, remaining, 12)
  fw.write(CQ_STATE + 0x60 + PacketLayout.TOTAL_SIZE, left)
  fw.write(CQ_STATE + 0x60 + PacketLayout.ADDRESS, 0)
  fw.write(CQ_STATE + 0x60 + PacketLayout.DATA_SIZE, 0)
  noc.write(
    CQ_STATE + 0x60, ring, CQConfig.DISPATCH_COORD,
    PacketLayout.HEADER.size, posted=False,
  )
  fw.write(PREFETCH_DISPATCH_PUBLISH, put)
  fw.fence()
  noc.write(
    PREFETCH_DISPATCH_PUBLISH, DISPATCH_PUBLISHED,
    CQConfig.DISPATCH_COORD, 4, posted=False,
  )
  fw.li(ring, DISPATCH_RING_BASE)

  fw.label("wait_dispatch_space")
  fw.read(left, PREFETCH_DISPATCH_READ)
  fw.sub(left, put, left)
  fw.li(chunk, DISPATCH_RING_PAGES); fw.sub(chunk, chunk, left)
  fw.bgeu(chunk, pages, "dispatch_space_ready")
  fw.fence(); fw.j("wait_dispatch_space")
  fw.label("dispatch_space_ready")
  fw.add(put, put, pages)
  fw.mv(dst, ring); fw.mv(left, size)
  fw.label("dispatch_copy_loop")
  fw.beq(left, R.ZERO, "dispatch_copy_done")
  fw.li(chunk, NiuCommand.MAX_PACKET_BYTES)
  fw.bltu(chunk, left, "dispatch_copy_size")
  fw.mv(chunk, left)
  fw.label("dispatch_copy_size")
  noc.write(src, dst, CQConfig.DISPATCH_COORD, chunk, posted=False)
  fw.add(src, src, chunk); fw.add(dst, dst, chunk); fw.sub(left, left, chunk)
  fw.j("dispatch_copy_loop")
  fw.label("dispatch_copy_done")
  fw.write(PREFETCH_DISPATCH_PUBLISH, put)
  fw.fence()
  noc.write(
    PREFETCH_DISPATCH_PUBLISH, DISPATCH_PUBLISHED,
    CQConfig.DISPATCH_COORD, 4, posted=False,
  )
  fw.slli(left, pages, 12); fw.add(ring, ring, left)
  fw.li(left, DISPATCH_RING_END); fw.bne(ring, left, "dispatch_no_wrap")
  fw.li(ring, DISPATCH_RING_BASE)
  fw.label("dispatch_no_wrap")

  # Advance either the trace cursor or the host issue read pointer only after
  # dispatch owns the record, so host backpressure can safely reclaim bytes.
  fw.read(size, PREFETCH_RECORD_SIZE)
  fw.read(src, PREFETCH_TRACE_ACTIVE)
  fw.beq(src, R.ZERO, "advance_issue")
  fw.read(cursor, PREFETCH_TRACE_CURSOR)
  fw.add(cursor, cursor, size)
  fw.write(PREFETCH_TRACE_CURSOR, cursor)
  fw.read(dst, PREFETCH_TRACE_END)
  fw.bltu(cursor, dst, "trace_header")
  fw.write(PREFETCH_TRACE_ACTIVE, 0)
  fw.li(size, ALIGN)  # Consume the TRACE descriptor in the issue ring.

  fw.label("advance_issue")
  fw.mv(chunk, read_lo)
  fw.add(read_lo, read_lo, size)
  fw.sltu(left, read_lo, chunk)
  fw.add(read_hi, read_hi, left)
  fw.write(PREFETCH_READ_PUBLISH, read_lo)
  fw.write(PREFETCH_READ_PUBLISH + 4, read_hi)
  fw.fence()
  fw.read(dst, PREFETCH_READ_PTR)
  noc.write(
    PREFETCH_READ_PUBLISH, dst, CQConfig.PCIE_COORD, 8,
    target_middle_address=pcie_mid, posted=False,
  )
  fw.j("prefetch_loop")


def build_dispatch(pcie_mid=CQConfig.PCIE_MID):
  fw = Asm("brisc")
  with fw.scope(): _emit_dispatch(fw, fw.reg(12), pcie_mid)
  return fw


def _emit_dispatch(fw, state, pcie_mid):
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = state
  noc = fw.noc
  fw.li(s0, DISPATCH_RING_BASE)
  fw.li(s1, 0)
  fw.write(DISPATCH_DRAM_PUT, 0)
  fw.write(DISPATCH_DRAM_READ, 0)

  fw.label("dispatch_loop")
  fw.label("wait_published")
  fw.read(s2, DISPATCH_PUBLISHED)
  fw.bne(s2, s1, "published")
  fw.fence(); fw.j("wait_published")
  fw.label("published")
  fw.lbu(s3, s0, PacketLayout.OP)
  fw.li(s4, int(Op.DRAM_COPY)); fw.beq(s3, s4, "dram_enqueue")
  fw.li(s4, int(Op.SIGNAL)); fw.beq(s3, s4, "dram_enqueue")

  # Preserve queue ordering: ordinary dispatch work can begin only after all
  # earlier asynchronous DRAM descriptors have completed on both copy RISCs.
  fw.label("wait_dram_idle")
  fw.read(s4, DISPATCH_DRAM_PUT)
  fw.fence()
  noc.read(
    DRAM_READ_PUBLISH, CQConfig.DRAM_COORD,
    DISPATCH_DRAM_READ, 4,
  )
  fw.fence()
  fw.read(s5, DISPATCH_DRAM_READ)
  fw.beq(s4, s5, "dram_idle")
  fw.j("wait_dram_idle")
  fw.label("dram_idle")
  fw.switch(s3, {
    int(Op.PAD): "command_done",
    int(Op.UNICAST_WRITE): "unicast",
    int(Op.MCAST_WRITE): "multicast",
    int(Op.RUN): "run",
  }, "bad_command")

  # Copy each asynchronous descriptor into the dedicated DRAM core's local
  # ring before returning dispatch-ring credit.
  fw.label("dram_enqueue")
  fw.label("wait_dram_queue_space")
  fw.read(s4, DISPATCH_DRAM_PUT)
  fw.read(s5, DISPATCH_DRAM_READ)
  fw.sub(s6, s4, s5)
  fw.li(s7, DRAM_QUEUE_ENTRIES)
  fw.bltu(s6, s7, "dram_queue_ready")
  fw.fence()
  noc.read(
    DRAM_READ_PUBLISH, CQConfig.DRAM_COORD,
    DISPATCH_DRAM_READ, 4,
  )
  fw.fence(); fw.j("wait_dram_queue_space")
  fw.label("dram_queue_ready")
  fw.andi(s5, s4, DRAM_QUEUE_ENTRIES - 1)
  fw.slli(s5, s5, 6)
  fw.li(s6, DRAM_QUEUE_BASE); fw.add(s5, s5, s6)
  noc.write(s0, s5, CQConfig.DRAM_COORD, ALIGN, posted=False)
  fw.addi(s4, s4, 1)
  fw.write(DISPATCH_DRAM_PUT, s4)
  fw.fence()
  noc.write(
    DISPATCH_DRAM_PUT, DRAM_PUBLISHED, CQConfig.DRAM_COORD, 4,
    posted=False,
  )
  fw.j("command_done")

  fw.label("unicast")
  fw.lhu(s3, s0, PacketLayout.TARGET_COUNT)
  fw.lw(s4, s0, PacketLayout.ADDRESS)
  fw.lw(s5, s0, PacketLayout.DATA_SIZE)
  fw.addi(s6, s0, PacketLayout.WRITE_TARGETS)
  fw.slli(s7, s3, 2); fw.add(s7, s7, s6)
  fw.align_up(s7, ALIGN)
  fw.mv(s8, s5); fw.align_up(s8, ALIGN)
  fw.mv(s9, s3)
  fw.label("unicast_loop")
  fw.beq(s9, R.ZERO, "unicast_done")
  fw.lw(s10, s6, 0)
  noc.write(s7, s4, s10, s5, posted=False)
  fw.addi(s6, s6, 4); fw.add(s7, s7, s8)
  fw.addi(s9, s9, -1); fw.j("unicast_loop")
  fw.label("unicast_done")
  fw.j("command_done")

  fw.label("multicast")
  fw.lhu(s3, s0, PacketLayout.TARGET_COUNT)
  fw.lw(s4, s0, PacketLayout.ADDRESS)
  fw.lw(s5, s0, PacketLayout.DATA_SIZE)
  fw.addi(s6, s0, PacketLayout.WRITE_TARGETS)
  fw.li(s7, 8); fw.mul(s7, s3, s7); fw.add(s7, s7, s6)
  fw.align_up(s7, ALIGN)
  fw.label("multicast_loop")
  fw.beq(s3, R.ZERO, "multicast_done")
  fw.lw(s8, s6, 0); fw.lw(s9, s6, 4)
  noc.multicast_write(s7, s4, s8, s9, s5)
  fw.addi(s6, s6, 8); fw.addi(s3, s3, -1)
  fw.j("multicast_loop")
  fw.label("multicast_done")
  fw.j("command_done")

  fw.label("run")
  fw.lw(s3, s0, PacketLayout.DATA_SIZE)  # Number of workers expected to finish.
  fw.write(DISPATCH_DONE_COUNT, 0)
  fw.fence()
  fw.addi(s6, s0, PacketLayout.RUN_TARGETS)
  fw.lw(s8, s0, PacketLayout.RUN_TEMPLATE)
  fw.li(s9, int(RunState.GO) << 24)
  fw.or_(s8, s8, s9)
  fw.write(DISPATCH_GO, s8)
  fw.fence()
  fw.lhu(s7, s0, PacketLayout.TARGET_COUNT)
  fw.label("go_loop")
  fw.beq(s7, R.ZERO, "go_done")
  fw.lw(s8, s6, 0); fw.lw(s9, s6, 4)
  noc.multicast_write(
    DISPATCH_GO, FirmwareControl.GO_SIGNAL & -4, s8, s9, 4,
  )
  fw.addi(s6, s6, 8); fw.addi(s7, s7, -1); fw.j("go_loop")
  fw.label("go_done")
  fw.label("wait_workers")
  fw.read(s8, DISPATCH_DONE_COUNT)
  fw.beq(s8, s3, "workers_done")
  fw.fence(); fw.j("wait_workers")
  fw.label("workers_done")
  fw.fence()
  fw.j("command_done")

  fw.label("command_done")
  fw.lw(s3, s0, PacketLayout.TOTAL_SIZE)
  fw.li(s4, PAGE_SIZE - 1); fw.add(s3, s3, s4); fw.srli(s3, s3, 12)
  fw.add(s1, s1, s3)
  fw.write(DISPATCH_READ_PUBLISH, s1)
  fw.fence()
  noc.write(
    DISPATCH_READ_PUBLISH, PREFETCH_DISPATCH_READ,
    CQConfig.PREFETCH_COORD, 4, posted=False,
  )
  fw.slli(s4, s3, 12); fw.add(s0, s0, s4)
  fw.li(s4, DISPATCH_RING_END); fw.bne(s0, s4, "dispatch_loop")
  fw.li(s0, DISPATCH_RING_BASE); fw.j("dispatch_loop")
  fw.label("bad_command"); fw.j("bad_command")
  return fw
