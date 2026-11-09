#include "worker.h"
#include "noc.h"

FIRMWARE_ENTRY(SET_SP(STACK_TOP))

static NORETURN launch(void) {
  wait8(GO_SIGNAL, 0x80);
  reset_tensix();
  invalidate_icache();
  for (u32 i = 0; i < 4; i++) write8(SUBORDINATE_SYNC + i, 0x80);
  fence();
  if (read32(LAUNCH) & 1) JUMP(CODE_BRISC);
  JUMP(FW_BRISC + 4);
}

NORETURN firmware_boot(void) {
  configure_csr(0);
  write32(TRISC0_RESET_PC + 0, FW_TRISC0);
  write32(TRISC0_RESET_PC + 4, FW_TRISC1);
  write32(TRISC0_RESET_PC + 8, FW_TRISC2);
  write32(TRISC_RESET_PC_OVERRIDE, 7);
  write32(NCRISC_RESET_PC, FW_NCRISC);
  write32(NCRISC_RESET_PC_OVERRIDE, 1);
  write32(SUBORDINATE_SYNC, 0x40404040);
  fence();
  write32(SOFT_RESET, 0);
  for (u32 i = 0; i < 4; i++) wait8(SUBORDINATE_SYNC + i, 2);
  launch();
}

NORETURN firmware_resume(void) {
  for (u32 i = 0; i < 4; i++) wait8(SUBORDINATE_SYNC + i, 0);
  u32 dispatch = read32(GO_SIGNAL) >> 8 & 0xFFF;
  write8(GO_SIGNAL, 0);
  fence();
  noc_atomic_inc(1, DONE_COUNT, dispatch, 1);
  launch();
}
