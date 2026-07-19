from asm import Asm
from cq import DISPATCH_DONE_COUNT
from fw.consts import CQConfig, Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from isa import R, Tensix as TT
from ttk.cb import CB
from ttk.noc import NIU0, NIU_STRIDE, NIU_CONFIG, NIU_CONTROL, ROUTER_CONTROL
from ttk.sync import Sem

_ECC_SCRUBBER = TensixMMIO.CFG_BASE + 0xC


def _reset_tensix(fw):
  fw.zero_words(TensixMMIO.CFG_BASE, 256)
  push = lambda word: fw.write32(TensixMMIO.INSTRN_BUF_BASE, word)
  push(TT.TTZEROACC(3, 0, 0, 0, 0))
  push(TT.TTSFPENCC(3, 0, 0, 10))
  push(TT.TTNOP())
  push(TT.TTSFPLOADI(0, 0, 0xBF80))
  push(TT.TTSFPCONFIG(0, 11, 0))
  fw.write32(_ECC_SCRUBBER, 1 | 2 | (0x100 << 3))
  for sem in (Sem.MATH_PACK, Sem.UNPACK_TO_DEST, Sem.MATH_DONE):
    push(TT.TTSEMINIT(1, 0, 1 << sem))
  return fw


def _enable_clock_gating(fw):
  for noc in range(2):
    for register in (NIU_CONTROL, ROUTER_CONTROL):
      addr = NIU0 + noc * NIU_STRIDE + NIU_CONFIG + register
      fw.update32(addr, set_bits=1)
  return fw


def build_brisc():
  fw = Asm.firmware("brisc")
  fw.configure_csr()
  fw.setup_stack(Firmware.BRISC_STACK_TOP)

  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, Firmware.TEXT["ncrisc"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, Firmware.TEXT["trisc0"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, Firmware.TEXT["trisc1"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, Firmware.TEXT["trisc2"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  _enable_clock_gating(fw)
  fw.zero_words(TensixL1.MEM_ZEROS_BASE, TensixL1.MEM_ZEROS_SIZE // 4)
  fw.invalidate_risc_caches()
  fw.jal(R.RA, "reset_tensix")
  fw.write32(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0)
  fw.invalidate_risc_caches()

  fw.write32(FirmwareControl.SUBORDINATE_SYNC, RunState.ALL_INIT)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(FirmwareControl.GO_SIGNAL, RunState.GO)
  fw.jal(R.RA, "reset_tensix")
  fw.invalidate_risc_caches()
  fw.signal_range(FirmwareControl.SUBORDINATE_SYNC, range(4), RunState.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["brisc"])
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.DONE)
  fw.signal8(FirmwareControl.GO_SIGNAL, RunState.DONE)
  fw.noc_at(1).atomic_inc(DISPATCH_DONE_COUNT, CQConfig.DISPATCH_COORD)
  fw.j("run_loop")

  fw.label("reset_tensix")
  _reset_tensix(fw)
  CB.reset_counters(fw)
  fw.jalr(R.ZERO, R.RA)
  return fw


def build_ncrisc():
  fw = Asm.firmware("ncrisc")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()
  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(FirmwareControl.SUBORDINATE_SYNC, RunState.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["ncrisc"])
  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunState.DONE)
  fw.j("run_loop")
  return fw


def build_trisc(trisc_id):
  role = f"trisc{trisc_id}"
  sync = FirmwareControl.SUBORDINATE_SYNC + trisc_id + 1
  fw = Asm.firmware(role)
  fw.li(R.GP, Firmware.TRISC_GLOBAL_POINTER)
  fw.setup_stack(Firmware.TRISC_STACK_TOP)
  fw.configure_csr()
  fw.jal(R.RA, "init_tensix")
  fw.write32(TensixMMIO.PRNG_SEED_SEED_VAL, 0)
  fw.delay_cycles(600)
  fw.signal8(sync, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(sync, RunState.GO)
  fw.jal(R.RA, "init_tensix")
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE[role])
  fw.signal8(sync, RunState.DONE)
  fw.j("run_loop")

  fw.label("init_tensix")
  fw.zero_words(TensixMMIO.REGFILE_BASE, 64)
  fw.jalr(R.ZERO, R.RA)
  return fw
