from asm import Asm
from fw.consts import CQConfig, TensixL1
from isa import R
from program import Program

ARGS_BASE = TensixL1.PARAM_BASE
ARGS_WORDS = 6
SCRATCH = TensixL1.DATA_BUFFER_SPACE_BASE

def _kernel(write: bool, core, dram_coords):
  fw = Asm("ncrisc", core)
  with fw.scope():
    base, sysmem, mid, tile, tiles, size, bank, address, coord, banks = fw.reg(10)
    for reg, offset in zip((base, sysmem, mid, tile, tiles, size), range(0, ARGS_WORDS * 4, 4)):
      fw.load(reg, ARGS_BASE + offset)

    noc = fw.noc(1)
    fw.li(banks, len(dram_coords))

    fw.label("dram_loop")
    fw.beq(tiles, R.ZERO, "dram_done")
    fw.remu(bank, tile, banks)
    fw.divu(address, tile, banks)
    fw.mul(address, address, size); fw.add(address, address, base)
    fw.switch(bank, {index: f"dram_bank_{index}" for index in range(len(dram_coords))}, "dram_bad_bank")
    for index, bank_coord in enumerate(dram_coords):
      fw.label(f"dram_bank_{index}")
      fw.li(coord, bank_coord)
      fw.j("dram_bank_selected")
    fw.label("dram_bad_bank"); fw.j("dram_bad_bank")
    fw.label("dram_bank_selected")

    if write:
      noc.read(
        sysmem, CQConfig.PCIE_COORD, SCRATCH, size,
        source_middle_address=mid,
      )
      noc.write(SCRATCH, address, coord, size, posted=False)
    else:
      noc.read(address, coord, SCRATCH, size)
      noc.write(
        SCRATCH, sysmem, CQConfig.PCIE_COORD, size,
        target_middle_address=mid, posted=False,
      )

    fw.add(sysmem, sysmem, size)
    fw.addi(tile, tile, 1); fw.addi(tiles, tiles, -1)
    fw.j("dram_loop")
    fw.label("dram_done")
  return fw.lower()

def _program(cores, dram_coords, *, write):
  cores = tuple(cores)
  image = _kernel(write, cores[0], tuple(dram_coords))
  return Program.from_kernels({core: {"ncrisc": image} for core in cores})

def dram_write(cores, dram_coords):
  return _program(cores, dram_coords, write=True)

def dram_read(cores, dram_coords):
  return _program(cores, dram_coords, write=False)
