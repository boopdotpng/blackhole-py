from cq import (
  ALIGN, DISPATCH_COMPLETION_BASE, DISPATCH_COMPLETION_END,
  DISPATCH_COMPLETION_HOST_PTR, DISPATCH_COMPLETION_PUBLISH, DISPATCH_COMPLETION_WRITE,
  DISPATCH_CREDIT_RETURN, DISPATCH_DONE_COUNT, DISPATCH_GO, DISPATCH_PUBLISHED,
  DISPATCH_RING_BASE, DISPATCH_RING_END, DISPATCH_SCRATCH,
  PAGE_SIZE, PREFETCH_CREDITS, Op, PacketLayout, Timestamp,
)
from fw.consts import CQ, FirmwareControl, RunMsg, TensixMMIO
from isa import R
from asm import KernelBuilder

def build_dispatch(core=CQ.DISPATCH_CORE):
  fw = KernelBuilder("brisc", core)
  with fw.scope(): _emit_dispatch(fw, fw.reg(12))
  return fw

def _emit_dispatch(fw, state):
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = state
  noc = fw.noc(1).initialize(CQ.DISPATCH_COORD)
  fw.li(s0, DISPATCH_RING_BASE)
  fw.li(s1, 0)
  fw.write32(DISPATCH_CREDIT_RETURN, (DISPATCH_RING_END - DISPATCH_RING_BASE) // PAGE_SIZE)

  fw.label("dispatch_loop")
  fw.label("wait_published")
  fw.read32(s2, DISPATCH_PUBLISHED)
  fw.bne(s2, s1, "published")
  fw.fence(); fw.j("wait_published")
  fw.label("published")
  fw.lbu(s3, s0, PacketLayout.OP)
  fw.switch(s3, {
    int(Op.PAD): "command_done",
    int(Op.UNICAST_WRITE): "unicast",
    int(Op.MCAST_WRITE): "multicast",
    int(Op.RUN): "run",
    int(Op.FENCE): "fence",
  }, "bad_command")

  fw.label("unicast")
  fw.lhu(s3, s0, PacketLayout.TARGET_COUNT)
  fw.lw(s4, s0, PacketLayout.ADDRESS)
  fw.lw(s5, s0, PacketLayout.DATA_SIZE)
  fw.addi(s6, s0, PacketLayout.WRITE_TARGETS)
  fw.slli(s7, s3, 2); fw.add(s7, s7, s6)
  fw.align_up(s7, ALIGN, scratch=s8)
  fw.mv(s8, s5); fw.align_up(s8, ALIGN, scratch=s9)
  fw.mv(s9, s3)
  with fw.scope():
    with noc.write_ack_batch(count=s3) as writes:
      fw.label("unicast_loop")
      fw.beq(s9, R.ZERO, "unicast_done")
      fw.lw(s10, s6, 0)
      writes.issue(s7, s4, s10, s5)
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
  fw.align_up(s7, ALIGN, scratch=s8)
  fw.label("multicast_loop")
  fw.beq(s3, R.ZERO, "multicast_done")
  fw.lw(s8, s6, 0); fw.lw(s9, s6, 4)

  with fw.scope():
    with noc.write_ack_batch(count=s9) as writes:
      writes.multicast_packet(s7, s4, s8, s5)
  fw.addi(s6, s6, 8); fw.addi(s3, s3, -1)
  fw.j("multicast_loop")
  fw.label("multicast_done")
  fw.j("command_done")

  fw.label("fence")
  fw.read32(s8, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.read32(s9, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.write32(DISPATCH_SCRATCH + Timestamp.START, s8)
  fw.write32(DISPATCH_SCRATCH + Timestamp.START + 4, s9)
  fw.write32(DISPATCH_SCRATCH + Timestamp.END, s8)
  fw.write32(DISPATCH_SCRATCH + Timestamp.END + 4, s9)
  fw.lw(s8, s0, PacketLayout.RUN_EVENT)
  fw.write32(DISPATCH_SCRATCH + Timestamp.EVENT, s8)
  _publish_completion(fw, noc)
  fw.j("command_done")

  fw.label("run")
  fw.read32(s8, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.read32(s9, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.write32(DISPATCH_SCRATCH + Timestamp.START, s8)
  fw.write32(DISPATCH_SCRATCH + Timestamp.START + 4, s9)
  fw.lhu(s3, s0, PacketLayout.TARGET_COUNT)
  fw.write32(DISPATCH_DONE_COUNT, 0)
  fw.fence()
  fw.addi(s6, s0, PacketLayout.RUN_TARGETS)
  fw.write32(DISPATCH_GO, int(RunMsg.GO) << 24)
  fw.mv(s7, s3)
  with fw.scope():
    with noc.write_ack_batch(count=s3) as writes:
      fw.label("go_loop")
      fw.beq(s7, R.ZERO, "go_done")
      fw.lw(s8, s6, 0)
      writes.issue(DISPATCH_GO, FirmwareControl.GO_SIGNAL & -4, s8, 4)
      fw.addi(s6, s6, 4); fw.addi(s7, s7, -1); fw.j("go_loop")
      fw.label("go_done")
  fw.label("wait_workers")
  fw.read32(s8, DISPATCH_DONE_COUNT)
  fw.bne(s8, s3, "wait_workers")
  fw.fence()
  fw.read32(s8, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.read32(s9, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.write32(DISPATCH_SCRATCH + Timestamp.END, s8)
  fw.write32(DISPATCH_SCRATCH + Timestamp.END + 4, s9)
  fw.lw(s8, s0, PacketLayout.RUN_EVENT)
  fw.write32(DISPATCH_SCRATCH + Timestamp.EVENT, s8)
  _publish_completion(fw, noc)
  fw.j("command_done")

  fw.label("command_done")
  fw.lw(s3, s0, PacketLayout.TOTAL_SIZE)
  fw.li(s4, PAGE_SIZE - 1); fw.add(s3, s3, s4); fw.srli(s3, s3, 12)
  fw.read32(s4, DISPATCH_CREDIT_RETURN); fw.add(s4, s4, s3)
  fw.write32(DISPATCH_CREDIT_RETURN, s4)

  noc.write(DISPATCH_CREDIT_RETURN, PREFETCH_CREDITS, CQ.PREFETCH_COORD, 4)
  fw.add(s1, s1, s3)
  fw.slli(s4, s3, 12); fw.add(s0, s0, s4)
  fw.li(s4, DISPATCH_RING_END); fw.bne(s0, s4, "dispatch_loop")
  fw.li(s0, DISPATCH_RING_BASE); fw.j("dispatch_loop")
  fw.label("bad_command"); fw.j("bad_command")
  return fw

def _publish_completion(fw, noc):
  with fw.scope(): return _emit_completion(fw, noc, fw.reg(4))

def _emit_completion(fw, noc, state):
  s10, s11, s3, s4 = state
  no_wrap = fw._new_label("completion_no_wrap")
  fw.read32(s10, DISPATCH_COMPLETION_WRITE)
  fw.li(s11, 0x7FFFFFFF); fw.and_(s11, s10, s11); fw.slli(s11, s11, 4)
  with fw.scope():
    with noc.write_ack_batch(count=1) as writes:
      writes.issue(DISPATCH_SCRATCH, s11, CQ.PCIE_COORD, Timestamp.STRUCT.size, dst_mid=CQ.PCIE_MID)
  fw.addi(s11, s10, PAGE_SIZE // 16)
  fw.read32(s3, DISPATCH_COMPLETION_END)
  fw.li(s4, 0x7FFFFFFF); fw.and_(s4, s11, s4)
  fw.bltu(s4, s3, no_wrap)
  fw.read32(s11, DISPATCH_COMPLETION_BASE)
  fw.li(s4, 0x80000000); fw.xor(s11, s11, s4)
  fw.label(no_wrap)
  fw.write32(DISPATCH_COMPLETION_WRITE, s11)
  fw.write32(DISPATCH_COMPLETION_PUBLISH, s11)
  fw.read32(s3, DISPATCH_COMPLETION_HOST_PTR)
  with fw.scope():
    with noc.write_ack_batch(count=1) as writes:
      writes.issue(DISPATCH_COMPLETION_PUBLISH, s3, CQ.PCIE_COORD, 4, dst_mid=CQ.PCIE_MID)
