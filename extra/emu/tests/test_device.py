from emu import memory as M
from emu import dsl
from emu.memory import LDM_SCRATCH, LDM_BASE
from emu.tests._helpers import mini_device


def test_device_tiles_have_shared_resources():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  cores = tile.cores
  for core in cores[1:]:
    assert core.l1 is cores[0].l1
    # Each core has its own Router but they all share the tile's mmio
    # fallback, so unmapped accesses from any core land in the same place.
    assert core.mem is not cores[0].mem
    assert core.mem.default is cores[0].mem.default is tile.mmio
  # But they have different LDM
  assert cores[0].ldm is not cores[1].ldm

def test_device_tiles_share_l1():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  tile.brisc.mem.write32(0x1000, 0xDEAD)
  assert tile.ncrisc.mem.read32(0x1000) == 0xDEAD

def test_device_noc_to_dram():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]

  # Write data to tile's L1
  tile.l1.write32(0x5000, 0x12345678)

  # Get DRAM bank 1's NOC coordinates from bank_xy
  bank_id = 1
  # bank 1 should be in bank_xy (P100A with bank 0 harvested)
  bx, by0 = dev.bank_xy[bank_id]
  port = 1  # use port 1

  # Program NOC write to DRAM bank
  regs = tile.noc0.regs
  regs.write32(M.NIU_TARG_ADDR_LO, 0x5000)
  regs.write32(M.NIU_TARG_ADDR_MID, 0)
  regs.write32(M.NIU_RET_ADDR_LO, 0x100)  # DRAM offset
  regs.write32(M.NIU_RET_ADDR_MID, 0)
  regs.write32(M.NIU_RET_ADDR_HI, ((by0 + port) << 6) | bx)
  regs.write32(M.NIU_AT_LEN_BE, 4)
  regs.write32(M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_RESP_MARKED)
  tile.brisc.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  # Read back from DRAM bank
  # Find which index in dram_banks corresponds to bank_id
  active_banks = sorted(dev.bank_xy.keys())
  bank_idx = active_banks.index(bank_id)
  assert dev.dram_banks[bank_idx].read32(0x100) == 0x12345678

def test_device_niu_id_logical():
  dev = mini_device()
  for (x, y), tile in dev.tiles.items():
    expected = (y << 6) | x
    assert tile.noc0.regs.read32(M.NIU_ID_LOGICAL) == expected
    assert tile.noc1.regs.read32(M.NIU_ID_LOGICAL) == expected

def test_device_dram_read_write():
  dev = mini_device()
  dev.write_dram(0, 0x100, b"\xAA\xBB\xCC\xDD")
  assert dev.read_dram(0, 0x100, 4) == b"\xAA\xBB\xCC\xDD"

def test_device_l1_read_write():
  dev = mini_device()
  dev.write_l1(1, 2, 0x1000, b"\x01\x02\x03\x04")
  assert dev.read_l1(1, 2, 0x1000, 4) == b"\x01\x02\x03\x04"



# -- LDM scratch area redirection ---------------------------------------------

def test_do_crt1_copies_data_to_ldm():
  dev = mini_device()
  tile = dev.tiles[(1, 2)]
  core = tile.brisc

  # Pre-populate L1 scratch with 2 words of initialized data
  scratch = LDM_SCRATCH['brisc']
  tile.l1.write32(scratch + 0, 0xCAFEBABE)
  tile.l1.write32(scratch + 4, 0x12345678)

  # Dirty LDM to verify BSS zeroing actually clears it
  core.ldm.write32(8, 0xFFFFFFFF)
  core.ldm.write32(12, 0xFFFFFFFF)

  # Assemble a minimal do_crt1:
  #   - Copy 2 words from L1 scratch → LDM (0xFFB00000)
  #   - Zero 2 words of BSS at LDM+8
  #
  # Registers:
  #   a0 = L1 scratch address
  #   a1 = LDM base (0xFFB00000)
  #   a2 = scratch data word
  #   a3 = zero
  code_addr = 0x100
  insns = [
    # Load scratch address into a0
    dsl.LUI(dsl.a0, scratch & 0xFFFFF000),
    dsl.ADDI(dsl.a0, dsl.a0, scratch & 0xFFF),
    # Load LDM base into a1
    dsl.LUI(dsl.a1, 0xFFB00000),
    # Copy word 0: L1[scratch+0] → LDM[0]
    dsl.LW(dsl.a2, dsl.a0, 0),
    dsl.SW(dsl.a1, dsl.a2, 0),
    # Copy word 1: L1[scratch+4] → LDM[4]
    dsl.LW(dsl.a2, dsl.a0, 4),
    dsl.SW(dsl.a1, dsl.a2, 4),
    # Zero BSS: LDM[8] and LDM[12]
    dsl.SW(dsl.a1, dsl.zero, 8),
    dsl.SW(dsl.a1, dsl.zero, 12),
  ]
  for i, insn in enumerate(insns):
    tile.l1.write32(code_addr + i * 4, int(insn))

  core.pc = code_addr
  core.run(n=len(insns) + 1)

  # Verify data was copied to LDM
  assert core.ldm.read32(0) == 0xCAFEBABE
  assert core.ldm.read32(4) == 0x12345678
  # Verify BSS was zeroed
  assert core.ldm.read32(8) == 0
  assert core.ldm.read32(12) == 0
