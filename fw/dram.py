from asm import KernelBuilder
from fw.consts import CQConfig, Firmware, TensixL1
from isa import R
from program import Program

ARGS_BASE = TensixL1.PARAM_BASE
ARGS_WORDS = 6
SCRATCH = TensixL1.DATA_BUFFER_SPACE_BASE

def _kernel(write: bool, core, dram_coords):
  fw = KernelBuilder("ncrisc", core)
  with fw.scope():
    x_addr, y_addr = Firmware.NOC_COORDINATE_BASE["ncrisc"]
    base, sysmem, mid, tile, tiles, size, bank, address, coord, seven, local, tmp = fw.reg(12)
    for reg, offset in zip((base, sysmem, mid, tile, tiles, size), range(0, ARGS_WORDS * 4, 4)):
      fw.load(reg, ARGS_BASE + offset)

    fw.load(local, x_addr + 1, bytes=1)
    fw.load(tmp, y_addr + 1, bytes=1)
    fw.slli(tmp, tmp, 6); fw.or_(local, local, tmp)
    noc = fw.noc(1).initialize(local)
    fw.li(seven, 7)

    fw.label("dram_loop")
    fw.beq(tiles, R.ZERO, "dram_done")
    fw.remu(bank, tile, seven)
    fw.divu(address, tile, seven)
    fw.mul(address, address, size); fw.add(address, address, base)
    fw.switch(bank, {index: f"dram_bank_{index}" for index in range(7)}, "dram_bad_bank")
    for index, bank_coord in enumerate(dram_coords):
      fw.label(f"dram_bank_{index}")
      fw.li(coord, bank_coord)
      fw.j("dram_bank_selected")
    fw.label("dram_bad_bank"); fw.j("dram_bad_bank")
    fw.label("dram_bank_selected")

    if write:
      with noc.read_batch(count=1) as reads:
        reads.issue(sysmem, CQConfig.PCIE_COORD, SCRATCH, size,
                    src_mid=mid, return_coord=local)
      with noc.write_ack_batch(count=1) as writes:
        writes.issue(SCRATCH, address, coord, size)
    else:
      with noc.read_batch(count=1) as reads:
        reads.issue(address, coord, SCRATCH, size, return_coord=local)
      with noc.write_ack_batch(count=1) as writes:
        writes.issue(SCRATCH, sysmem, CQConfig.PCIE_COORD, size, dst_mid=mid)

    fw.add(sysmem, sysmem, size)
    fw.addi(tile, tile, 1); fw.addi(tiles, tiles, -1)
    fw.j("dram_loop")
    fw.label("dram_done")
  return fw.lower()

def _program(cores, dram_coords, *, write):
  cores = tuple(cores)
  image = _kernel(write, cores[0], tuple(dram_coords))
  return Program({core: {"ncrisc": image} for core in cores}, {}, ())

def dram_write(cores, dram_coords):
  return _program(cores, dram_coords, write=True)

def dram_read(cores, dram_coords):
  return _program(cores, dram_coords, write=False)
