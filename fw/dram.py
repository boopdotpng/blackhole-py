from asm import Asm
from fw.consts import CQConfig, TensixL1
from isa import R
from program import Program

ARGS_BASE = TensixL1.PARAM_BASE
ARGS_WORDS = 6
SCRATCH = TensixL1.DATA_BUFFER_SPACE_BASE

def _kernel(write: bool, dram_endpoints):
  fw = Asm("ncrisc")
  with fw.scope():
    base, sysmem, mid, tile, tiles, tile_size, bank, address, coord, banks = fw.reg(10)
    for reg, offset in zip((base, sysmem, mid, tile, tiles, tile_size), range(0, ARGS_WORDS * 4, 4)):
      fw.load(reg, ARGS_BASE + offset)

    noc = fw.noc
    fw.li(banks, len(dram_endpoints))

    fw.label("dram_loop")
    fw.beq(tiles, R.ZERO, "dram_done")
    fw.remu(bank, tile, banks)
    fw.divu(address, tile, banks)
    fw.mul(address, address, tile_size); fw.add(address, address, base)
    fw.switch(bank, {index: f"dram_bank_{index}" for index in range(len(dram_endpoints))}, "dram_bad_bank")
    for index, ((_, _), (x, y)) in enumerate(dram_endpoints):
      fw.label(f"dram_bank_{index}")
      fw.li(coord, x | y << 6)
      fw.j("dram_bank_selected")
    fw.label("dram_bad_bank"); fw.j("dram_bad_bank")
    fw.label("dram_bank_selected")

    if write:
      noc.read(
        sysmem, CQConfig.PCIE_COORD, SCRATCH, tile_size,
        source_middle_address=mid,
      )
      noc.write(SCRATCH, address, coord, tile_size, posted=False)
    else:
      noc.read(address, coord, SCRATCH, tile_size)
      noc.write(
        SCRATCH, sysmem, CQConfig.PCIE_COORD, tile_size,
        target_middle_address=mid, posted=False,
      )

    fw.add(sysmem, sysmem, tile_size)
    fw.addi(tile, tile, 1); fw.addi(tiles, tiles, -1)
    fw.j("dram_loop")
    fw.label("dram_done")
  return fw.lower()

def _program(cores, dram_endpoints, write):
  cores = tuple(cores)
  image = _kernel(write, tuple(dram_endpoints))
  return Program(cores, images={"ncrisc": image})

def dram_write(cores, dram_endpoints):
  return _program(cores, dram_endpoints, write=True)

def dram_read(cores, dram_endpoints):
  return _program(cores, dram_endpoints, write=False)
