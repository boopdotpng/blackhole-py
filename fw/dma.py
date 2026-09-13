from fw.abi import BOOT_BANKS, BOOT_COORDS
from asm import Asm
from fw.abi import (
  CQ_STATE, DISPATCH_DRAM_READ, DISPATCH_SIGNAL, DRAM_BRISC_READY,
  DRAM_BRISC_STAGING, DRAM_NCRISC_READ, DRAM_NCRISC_READY,
  DRAM_NCRISC_STAGING, DRAM_PUBLISHED,
  DRAM_QUEUE_BASE, DRAM_READ_PUBLISH,
  DRAM_QUEUE_ENTRIES, Op, PacketLayout,
)
from fw.consts import CQConfig, TensixMMIO
from isa import R

DRAM_BRISC_COORD_TABLE = CQ_STATE + 0x20
DRAM_NCRISC_COORD_TABLE = CQ_STATE + 0x40


def build_dram_brisc():
  fw = Asm("brisc")
  with fw.scope():
    _emit_engine(fw, fw.reg(12), 0, DRAM_BRISC_STAGING)
  return fw


def build_dram_ncrisc():
  fw = Asm("ncrisc")
  with fw.scope():
    _emit_engine(fw, fw.reg(12), 1, DRAM_NCRISC_STAGING)
  return fw


def _emit_engine(fw, state, first_bank, staging):
  (
    read, published, slot, op, dram, source, mid, tile_size, tile_count,
    banks, direction, scratch,
  ) = state
  noc = fw.noc
  coord_table = BOOT_COORDS + first_bank * 32
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
  fw.li(scratch, int(Op.TIMESTAMP)); fw.beq(op, scratch, "engine_done")
  fw.li(scratch, int(Op.DMA)); fw.beq(op, scratch, "dma")
  fw.j("dram_bad_command")

  fw.label("dram_copy")
  fw.lw(dram, slot, PacketLayout.ADDRESS)
  fw.lw(tile_size, slot, PacketLayout.DATA_SIZE)
  fw.lw(source, slot, PacketLayout.COPY_SOURCE_LO)
  fw.lw(mid, slot, PacketLayout.COPY_SOURCE_MID)
  fw.lw(tile_count, slot, PacketLayout.COPY_TILE_COUNT)
  fw.lw(banks, slot, PacketLayout.COPY_BANKS)
  fw.lw(direction, slot, PacketLayout.COPY_DIRECTION)
  fw.label("copy_ready")
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

  # Byte-addressed DMA: high bit marks a logical 2 KiB-striped DRAM address;
  # other addresses are NoC PCIe addresses, or L1 coordinates in high bits.
  # Both engines derive the same chunks and execute alternate chunks.
  fw.label("dma")
  # Full stripes use the original gather/scatter engine: up to 64 KiB per
  # bank, multiple host requests in flight, one contiguous DRAM transaction.
  with fw.scope():
    lo, hi, other, page, count = fw.reg(5)
    fw.lw(tile_count, slot, 32); fw.andi(scratch, tile_count, 2047)
    fw.bne(scratch, R.ZERO, "dma_bytes")
    fw.beq(tile_count, R.ZERO, "engine_done")
    fw.lw(lo, slot, 16); fw.lw(hi, slot, 20)
    fw.lw(source, slot, 24); fw.lw(mid, slot, 28)
    fw.li(direction, 1); fw.srli(scratch, hi, 31)
    fw.bne(scratch, R.ZERO, "dma_fast_dram")
    fw.mv(other, lo); fw.mv(lo, source); fw.mv(source, other)
    fw.mv(other, hi); fw.mv(hi, mid); fw.mv(mid, other)
    fw.li(direction, 0); fw.srli(scratch, hi, 31)
    fw.beq(scratch, R.ZERO, "dma_bytes")
    fw.label("dma_fast_dram")
    fw.srli(scratch, mid, 28); fw.li(other, 1)
    fw.bne(scratch, other, "dma_bytes")
    fw.andi(scratch, lo, 2047); fw.bne(scratch, R.ZERO, "dma_bytes")
    fw.andi(scratch, source, 63); fw.bne(scratch, R.ZERO, "dma_bytes")
    fw.srli(page, lo, 11); fw.slli(scratch, hi, 21); fw.or_(page, page, scratch)
    fw.read(banks, BOOT_BANKS); fw.remu(scratch, page, banks)
    fw.bne(scratch, R.ZERO, "dma_bytes")
    fw.divu(dram, page, banks); fw.slli(dram, dram, 11)
    fw.srli(tile_count, tile_count, 11); fw.li(tile_size, 2048)
    fw.j("copy_ready")
  fw.label("dma_bytes")
  fw.lw(tile_count, slot, 32)
  fw.li(tile_size, 0); fw.li(direction, 0)
  fw.label("dma_loop")
  fw.beq(tile_size, tile_count, "engine_done")
  fw.sub(banks, tile_count, tile_size)
  fw.li(scratch, 2048); fw.bgeu(scratch, banks, "dma_size")
  fw.mv(banks, scratch)
  fw.label("dma_size")
  with fw.scope():
    slo, smid, scoord, dlo, dmid, dcoord, page, offset, count, temp = fw.reg(10)
    for name, lo, midreg, coord, addr in (("src", slo, smid, scoord, 16), ("dst", dlo, dmid, dcoord, 24)):
      fw.lw(lo, slot, addr); fw.lw(midreg, slot, addr + 4)
      fw.mv(temp, lo); fw.add(lo, lo, tile_size)
      fw.sltu(temp, lo, temp); fw.add(midreg, midreg, temp)
      fw.srli(temp, midreg, 31); fw.beq(temp, R.ZERO, "dma_" + name + "_linear")
      fw.andi(offset, lo, 2047)
      fw.li(temp, 2048); fw.sub(temp, temp, offset)
      fw.bgeu(temp, banks, "dma_" + name + "_chunk")
      fw.mv(banks, temp)
      fw.label("dma_" + name + "_chunk")
      fw.srli(page, lo, 11); fw.slli(temp, midreg, 21); fw.or_(page, page, temp)
      fw.read(count, BOOT_BANKS)
      fw.remu(coord, page, count); fw.divu(page, page, count)
      fw.slli(lo, page, 11); fw.add(lo, lo, offset)
      fw.slli(coord, coord, 2); fw.li(temp, coord_table)
      fw.add(coord, coord, temp); fw.lw(coord, coord, 0)
      fw.li(midreg, 0); fw.j("dma_" + name + "_ready")
      fw.label("dma_" + name + "_linear")
      # PCIe's high bit 28 identifies sysmem. L1 uses a packed x/y coordinate.
      fw.srli(temp, midreg, 28); fw.bne(temp, R.ZERO, "dma_" + name + "_host")
      fw.mv(coord, midreg); fw.li(midreg, 0); fw.j("dma_" + name + "_ready")
      fw.label("dma_" + name + "_host")
      fw.li(coord, CQConfig.PCIE_COORD)
      fw.label("dma_" + name + "_ready")
    fw.andi(temp, direction, 1); fw.li(count, first_bank)
    fw.bne(temp, count, "dma_skip")
    # NoC endpoints must agree on their low six address bits. Realign only
    # when the user view has different source/destination byte alignment.
    fw.andi(source, slo, 63); fw.li(dram, staging); fw.add(source, source, dram)
    noc.read(slo, scoord, source, banks, source_middle_address=smid)
    fw.andi(temp, slo, 63); fw.andi(count, dlo, 63)
    fw.beq(temp, count, "dma_aligned")
    fw.li(mid, staging + 4096); fw.add(mid, mid, count)
    fw.mv(dram, source); fw.mv(offset, mid); fw.mv(count, banks)
    fw.label("dma_realign")
    fw.lbu(temp, dram, 0); fw.sb(temp, offset, 0)
    fw.addi(dram, dram, 1); fw.addi(offset, offset, 1); fw.addi(count, count, -1)
    fw.bne(count, R.ZERO, "dma_realign")
    fw.mv(source, mid); fw.fence()
    fw.label("dma_aligned")
    noc.write(source, dlo, dcoord, banks, target_middle_address=dmid, posted=False)
  fw.label("dma_skip")
  fw.add(tile_size, tile_size, banks); fw.addi(direction, direction, 1)
  fw.j("dma_loop")

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
    fw.beq(op, published, "signal")
    fw.li(published, int(Op.TIMESTAMP)); fw.bne(op, published, "publish_read")
    fw.label("signal")
    fw.lw(dram, slot, PacketLayout.SIGNAL_TARGET_LO)
    fw.lw(mid, slot, PacketLayout.SIGNAL_TARGET_MID)
    fw.lw(source, slot, PacketLayout.SIGNAL_VALUE)
    fw.lw(tile_size, slot, PacketLayout.SIGNAL_VALUE + 4)
    fw.li(published, int(Op.SIGNAL)); fw.beq(op, published, "signal_value")
    fw.label("clock_read")
    fw.read(tile_size, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
    fw.read(source, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    fw.read(published, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
    fw.bne(tile_size, published, "clock_read")
    fw.label("signal_value")
    fw.write(DISPATCH_SIGNAL, source); fw.write(DISPATCH_SIGNAL + 4, tile_size)
    fw.fence()
    noc.write(DISPATCH_SIGNAL, dram, CQConfig.PCIE_COORD, 8, target_middle_address=mid, posted=False)
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
