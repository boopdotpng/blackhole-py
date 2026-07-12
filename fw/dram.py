"""Small worker kernels that copy between staged sysmem and interleaved DRAM."""

from asm import KERNEL_ROLES, KernelBuilder
from cq import MAX_WRITE_SIZE
from fw.consts import CQ, NcriscLocalState, TensixL1
from isa import R
from program import Program

ARGS_BASE = TensixL1.PARAM_BASE
ARGS_WORDS = 6
SCRATCH = TensixL1.DATA_BUFFER_SPACE_BASE


def _kernel(write: bool, core, dram_coords):
  if len(dram_coords) != 7: raise ValueError("DRAM transfer needs seven bank coordinates")
  fw = KernelBuilder("ncrisc", core)
  with fw.scope():
    base, sysmem, mid, tile, tiles, size, bank, address, coord, seven, local, tmp = fw.reg(12)
    for reg, offset in zip((base, sysmem, mid, tile, tiles, size), range(0, ARGS_WORDS * 4, 4)):
      fw.load(reg, ARGS_BASE + offset)

    # Resident NCRISC records both hardware NoC coordinates at boot. NoC 1 is
    # the transfer path used by the original fill/drain kernels.
    fw.load(local, NcriscLocalState.MY_X + 1, bytes=1)
    fw.load(tmp, NcriscLocalState.MY_Y + 1, bytes=1)
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
      with fw.scope():
        with noc.read_batch(count=1) as reads:
          reads.issue(sysmem, CQ.PCIE_COORD, SCRATCH, size,
                      src_mid=mid, return_coord=local)
      with fw.scope():
        with noc.write_ack_batch(count=1) as writes:
          writes.issue(SCRATCH, address, coord, size)
    else:
      with fw.scope():
        with noc.read_batch(count=1) as reads:
          reads.issue(address, coord, SCRATCH, size, return_coord=local)
      with fw.scope():
        with noc.write_ack_batch(count=1) as writes:
          writes.issue(SCRATCH, sysmem, CQ.PCIE_COORD, size, dst_mid=mid)

    fw.add(sysmem, sysmem, size)
    fw.addi(tile, tile, 1); fw.addi(tiles, tiles, -1)
    fw.j("dram_loop")
    fw.label("dram_done")
  return fw.lower()


def _program(cores, dram_coords, *, write):
  cores = tuple(cores)
  if not cores: raise ValueError("DRAM transfer needs at least one worker core")
  if MAX_WRITE_SIZE < 16 * 1024: raise RuntimeError("CQ cannot upload the DRAM kernel")
  images = {role: KernelBuilder(role, cores[0]).lower() for role in KERNEL_ROLES}
  images["ncrisc"] = _kernel(write, cores[0], tuple(dram_coords))
  return Program({core: dict(images) for core in cores}, (), ())


def dram_write(cores, dram_coords):
  """Build the sysmem-to-DRAM worker program."""
  return _program(cores, dram_coords, write=True)


def dram_read(cores, dram_coords):
  """Build the DRAM-to-sysmem worker program."""
  return _program(cores, dram_coords, write=False)
