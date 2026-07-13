from asm import KernelBuilder
from isa import R
from fw.consts import Firmware, FirmwareControl, RunSync, TensixL1
from ttk.tensix import Tensix, TensixRegs

def build(trisc_id: int):
  if trisc_id not in (0, 1, 2):
    raise ValueError("TRISC id must be 0, 1, or 2")
  role = f"trisc{trisc_id}"
  sync = FirmwareControl.SUBORDINATE_SYNC + trisc_id + 1
  fw = KernelBuilder.standalone(role)
  fw.li(R.GP, Firmware.TRISC_GLOBAL_POINTER)
  fw.setup_stack(Firmware.TRISC_STACK_TOP)
  fw.configure_csr()
  fw.jal(R.RA, "init_tensix")
  fw.write32(TensixRegs.PRNG_SEED_SEED_VAL, 0)
  fw.delay_cycles(600)

  fw.signal8(sync, RunSync.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(sync, RunSync.GO)
  fw.jal(R.RA, "init_tensix")
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE[role])
  fw.signal8(sync, RunSync.DONE)
  fw.j("run_loop")

  fw.label("init_tensix")
  Tensix.init(fw)
  fw.jalr(R.ZERO, R.RA)
  return fw

def build_trisc0(): return build(0)
def build_trisc1(): return build(1)
def build_trisc2(): return build(2)
