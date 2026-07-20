from asm import Asm, scoped
from cq import DISPATCH_DONE_COUNT
from fw.consts import CQConfig, Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from isa import R, Tensix as TT
from ttk.cb import CB
from ttk.noc import NIU0, NIU_STRIDE, NIU_CONFIG, NIU_CONTROL, ROUTER_CONTROL
from ttk.sync import Sem

def _firmware(role): fw = Asm.firmware(role); fw.j("worker_done"); return fw
def _run_worker(fw, role): fw.j(TensixL1.WORKER_TEXT_BASE[role]); return fw.label("worker_done")

def _reset_tensix(fw):
  fw.zero_words(TensixMMIO.CFG_BASE, 256)
  fw.emit(TT.TTZEROACC(3, 0, 0, 0, 0))
  fw.emit(TT.TTSFPENCC(3, 0, 0, 10))
  fw.emit(TT.TTNOP())
  fw.emit(TT.TTSFPLOADI(0, 0, 0xBF80))
  fw.emit(TT.TTSFPCONFIG(0, 11, 0))
  fw.write(TensixMMIO.ECC_SCRUBBER, 1 | 2 | (0x100 << 3))
  for sem in (
    Sem.FPU_SFPU, Sem.MATH_PACK, Sem.UNPACK_TO_DEST, Sem.MATH_DONE,
  ):
    fw.emit(TT.TTSEMINIT(1, 0, 1 << sem))
  return fw

@scoped
def _enable_clock_gating(fw):
  value = fw.reg()
  for noc in range(2):
    for register in (NIU_CONTROL, ROUTER_CONTROL):
      addr = NIU0 + noc * NIU_STRIDE + NIU_CONFIG + register
      fw.read(value, addr); fw.ori(value, value, 1); fw.write(addr, value)
  return fw

@scoped
def _delay_cycles(fw, cycles):
  counter = fw.reg()
  fw.li(counter, cycles)
  loop = fw._new_label("delay")
  fw.label(loop)
  fw.addi(counter, counter, -1)
  fw.bne(counter, R.ZERO, loop)
  return fw


def build_brisc():
  fw = _firmware("brisc")
  fw.configure_csr()
  fw.setup_stack(Firmware.BRISC_STACK_TOP)

  fw.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, Firmware.TEXT["ncrisc"][0] + 4)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, Firmware.TEXT["trisc0"][0] + 4)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, Firmware.TEXT["trisc1"][0] + 4)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, Firmware.TEXT["trisc2"][0] + 4)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  _enable_clock_gating(fw)
  fw.zero_words(TensixL1.MEM_ZEROS_BASE, TensixL1.MEM_ZEROS_SIZE // 4)
  fw.invalidate_risc_caches()
  fw.jal(R.RA, "reset_tensix")
  fw.write(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0)
  fw.invalidate_risc_caches()

  fw.write(FirmwareControl.SUBORDINATE_SYNC, RunState.ALL_INIT)
  fw.write(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in range(1, 5):
    fw.wait(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait(FirmwareControl.GO_SIGNAL, RunState.GO)
  fw.jal(R.RA, "reset_tensix")
  fw.invalidate_risc_caches()
  for role in range(4):
    fw.write(FirmwareControl.SUBORDINATE_SYNC + role, RunState.GO, bytes=1)
  _run_worker(fw, "brisc")
  for role in range(1, 5):
    fw.wait(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.DONE)
  fw.write(FirmwareControl.GO_SIGNAL, RunState.DONE, bytes=1)
  fw.noc_at(1).atomic_inc(DISPATCH_DONE_COUNT, CQConfig.DISPATCH_COORD)
  fw.j("run_loop")

  fw.label("reset_tensix")
  _reset_tensix(fw)
  CB.reset_counters(fw)
  fw.jalr(R.ZERO, R.RA)
  return fw


def build_ncrisc():
  fw = _firmware("ncrisc")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()
  fw.write(FirmwareControl.SUBORDINATE_SYNC, RunState.BOOT_READY, bytes=1)

  fw.label("run_loop")
  fw.wait(FirmwareControl.SUBORDINATE_SYNC, RunState.GO)
  _run_worker(fw, "ncrisc")
  fw.write(FirmwareControl.SUBORDINATE_SYNC, RunState.DONE, bytes=1)
  fw.j("run_loop")
  return fw


def build_trisc(trisc_id):
  role = f"trisc{trisc_id}"
  sync = FirmwareControl.SUBORDINATE_SYNC + trisc_id + 1
  fw = _firmware(role)
  fw.li(R.GP, Firmware.TRISC_GLOBAL_POINTER)
  fw.setup_stack(Firmware.TRISC_STACK_TOP)
  fw.configure_csr()
  fw.jal(R.RA, "init_tensix")
  fw.write(TensixMMIO.PRNG_SEED_SEED_VAL, 0)
  _delay_cycles(fw, 600)
  fw.write(sync, RunState.BOOT_READY, bytes=1)

  fw.label("run_loop")
  fw.wait(sync, RunState.GO)
  fw.jal(R.RA, "init_tensix")
  _run_worker(fw, role)
  fw.write(sync, RunState.DONE, bytes=1)
  fw.j("run_loop")

  fw.label("init_tensix")
  fw.zero_words(TensixMMIO.REGFILE_BASE, 64)
  fw.jalr(R.ZERO, R.RA)
  return fw
