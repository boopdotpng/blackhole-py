from asm import Asm
from cq import (
  CQ_STATE, DISPATCH_DRAM_READ, DISPATCH_SIGNAL, DRAM_BRISC_READY,
  DRAM_BRISC_STAGING, DRAM_NCRISC_READ, DRAM_NCRISC_READY,
  DRAM_NCRISC_STAGING, DRAM_PUBLISHED,
  DRAM_QUEUE_BASE, DRAM_READ_PUBLISH,
  DRAM_QUEUE_ENTRIES, Op, PacketLayout,
)
from fw.consts import CQConfig, TensixMMIO
from isa import R
from pcie import P100_DRAM_ENDPOINTS

DRAM_BRISC_COORD_TABLE = CQ_STATE + 0x20
DRAM_NCRISC_COORD_TABLE = CQ_STATE + 0x40


def build_dram_brisc():
  fw = Asm("brisc")
  with fw.scope(): _emit_engine(fw, fw.reg(12), 0, DRAM_BRISC_STAGING)
  return fw


def build_dram_ncrisc():
  fw = Asm("ncrisc")
  with fw.scope(): _emit_engine(fw, fw.reg(12), 1, DRAM_NCRISC_STAGING)
  return fw


def _emit_engine(fw, state, first_bank, staging):
  (
    read, published, slot, op, dram, source, mid, tile_size, tile_count,
    banks, direction, scratch,
  ) = state
  noc = fw.noc
  endpoints = tuple(pair[0 if first_bank == 0 else 1] for pair in P100_DRAM_ENDPOINTS)
  coord_table = DRAM_NCRISC_COORD_TABLE if first_bank else DRAM_BRISC_COORD_TABLE
  for index, (x, y) in enumerate(endpoints):
    fw.write(coord_table + index * 4, x | y << 6)
  fw.li(read, 0)
  if first_bank:
    fw.write(DRAM_NCRISC_READ, 0)
    fw.write(DRAM_NCRISC_READY, 1)
  else:
    fw.write(DRAM_PUBLISHED, 0)
    fw.write(DRAM_READ_PUBLISH, 0)
    fw.write(DRAM_BRISC_READY, 1)

  fw.fence()
  fw.label("dram_loop")
  fw.read(published, DRAM_PUBLISHED)
  fw.bne(published, read, "dram_ready")
  # FENCE flushes the RISC data cache before polling a NoC-updated mailbox.
  fw.fence(); fw.j("dram_loop")
  fw.label("dram_ready")
  fw.andi(slot, read, DRAM_QUEUE_ENTRIES - 1)
  fw.slli(slot, slot, 6)
  fw.li(scratch, DRAM_QUEUE_BASE); fw.add(slot, slot, scratch)
  fw.lbu(op, slot, PacketLayout.OP)
  fw.li(scratch, int(Op.DRAM_COPY))
  fw.beq(op, scratch, "dram_copy")
  fw.li(scratch, int(Op.SIGNAL))
  fw.beq(op, scratch, "engine_done")
  fw.j("dram_bad_command")

  fw.label("dram_copy")
  fw.lw(dram, slot, PacketLayout.ADDRESS)
  fw.lw(tile_size, slot, PacketLayout.DATA_SIZE)
  fw.lw(source, slot, PacketLayout.COPY_SOURCE_LO)
  fw.lw(mid, slot, PacketLayout.COPY_SOURCE_MID)
  fw.lw(tile_count, slot, PacketLayout.COPY_TILE_COUNT)
  fw.lw(banks, slot, PacketLayout.COPY_BANKS)
  fw.lw(direction, slot, PacketLayout.COPY_DIRECTION)
  with fw.scope():
    bank, row, rows, batch, limit, host, remote, stage, coord, stride = fw.reg(10)
    fw.li(bank, first_bank)
    fw.label("copy_bank_loop")
    fw.bgeu(bank, banks, "engine_done")
    fw.bgeu(bank, tile_count, "copy_next_bank")
    # Number of tiles in this bank: ceil((tile_count - bank) / banks).
    fw.sub(rows, tile_count, bank)
    fw.add(rows, rows, banks); fw.addi(rows, rows, -1)
    fw.divu(rows, rows, banks)
    fw.li(row, 0)
    fw.li(limit, 64 * 1024); fw.divu(limit, limit, tile_size)
    fw.mul(stride, banks, tile_size)
    fw.label("copy_batch_loop")
    fw.bgeu(row, rows, "copy_next_bank")
    fw.sub(batch, rows, row)
    fw.bgeu(limit, batch, "copy_batch_size")
    fw.mv(batch, limit)
    fw.label("copy_batch_size")
    fw.li(stage, coord_table)
    fw.slli(coord, bank, 2); fw.add(coord, coord, stage); fw.lw(coord, coord, 0)
    fw.mul(remote, row, tile_size); fw.add(remote, remote, dram)
    fw.mul(host, row, banks); fw.add(host, host, bank)
    fw.mul(host, host, tile_size); fw.add(host, host, source)
    fw.beq(direction, R.ZERO, "copy_batch_to_dram")

    # DRAM is contiguous within one bank. Read one large batch, then scatter
    # its tiles back into the host's interleaved physical-tile order.
    fw.mul(stage, batch, tile_size)
    noc.read(remote, coord, staging, stage)
    fw.li(stage, staging); fw.mv(scratch, batch)
    with noc.transaction() as transaction:
      fw.label("copy_host_write_loop")
      fw.beq(scratch, R.ZERO, "copy_host_write_done")
      transaction.write(
        stage, host, CQConfig.PCIE_COORD, tile_size,
        target_middle_address=mid, posted=False,
      )
      fw.add(stage, stage, tile_size); fw.add(host, host, stride)
      fw.addi(scratch, scratch, -1); fw.j("copy_host_write_loop")
      fw.label("copy_host_write_done")
    fw.j("copy_batch_done")

    # Gather one bank's strided host tiles with many reads in flight, then
    # issue one contiguous DRAM write for the complete batch.
    fw.label("copy_batch_to_dram")
    fw.li(stage, staging); fw.mv(scratch, batch)
    with noc.transaction() as transaction:
      fw.label("copy_host_read_loop")
      fw.beq(scratch, R.ZERO, "copy_host_read_done")
      transaction.read(
        host, CQConfig.PCIE_COORD, stage, tile_size,
        source_middle_address=mid,
      )
      fw.add(host, host, stride); fw.add(stage, stage, tile_size)
      fw.addi(scratch, scratch, -1); fw.j("copy_host_read_loop")
      fw.label("copy_host_read_done")
    fw.mul(stage, batch, tile_size)
    noc.write(staging, remote, coord, stage, posted=False)

    fw.label("copy_batch_done")
    fw.add(row, row, batch)
    fw.j("copy_batch_loop")
    fw.label("copy_next_bank")
    fw.addi(bank, bank, 2)
    fw.j("copy_bank_loop")

  fw.label("engine_done")
  fw.addi(scratch, read, 1)
  if first_bank:
    fw.mv(read, scratch)
    fw.write(DRAM_NCRISC_READ, read)
    fw.fence()
    fw.j("dram_loop")
  else:
    # Descriptor completion is the barrier between both NoCs. NCRISC may run
    # ahead, but BRISC only reclaims a slot after NCRISC reached this sequence.
    fw.label("wait_ncrisc")
    fw.read(published, DRAM_NCRISC_READ)
    fw.bgeu(published, scratch, "ncrisc_done")
    fw.fence(); fw.j("wait_ncrisc")
    fw.label("ncrisc_done")

    # Signals share the descriptor stream, so they become visible only after
    # every earlier copy completed on both engines.
    fw.li(published, int(Op.SIGNAL))
    fw.bne(op, published, "publish_read")
    fw.lw(dram, slot, PacketLayout.SIGNAL_TARGET_LO)
    fw.lw(mid, slot, PacketLayout.SIGNAL_TARGET_MID)
    fw.lw(source, slot, PacketLayout.SIGNAL_VALUE)
    fw.lw(tile_size, slot, PacketLayout.SIGNAL_VALUE + 4)
    fw.read(tile_count, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    fw.read(banks, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
    fw.write(DISPATCH_SIGNAL, source)
    fw.write(DISPATCH_SIGNAL + 4, tile_size)
    fw.write(DISPATCH_SIGNAL + 8, tile_count)
    fw.write(DISPATCH_SIGNAL + 12, banks)
    fw.fence()
    noc.write(
      DISPATCH_SIGNAL, dram, CQConfig.PCIE_COORD, 16,
      target_middle_address=mid, posted=False,
    )
    fw.label("publish_read")
    fw.mv(read, scratch)
    fw.write(DRAM_READ_PUBLISH, read)
    fw.fence()
    noc.write(
      DRAM_READ_PUBLISH, DISPATCH_DRAM_READ,
      CQConfig.DISPATCH_COORD, 4, posted=False,
    )
    fw.j("dram_loop")

  fw.label("dram_bad_command")
  fw.j("dram_bad_command")
