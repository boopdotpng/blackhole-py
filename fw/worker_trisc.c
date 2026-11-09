#include "worker.h"

FIRMWARE_ENTRY(SET_SP(TRISC_STACK_TOP) SET_GP(TRISC_GP))

#define SYNC (SUBORDINATE_SYNC + 1 + TRISC)
#define FW (FW_TRISC0 + TRISC * (FW_TRISC1 - FW_TRISC0))

static NORETURN launch(void) {
  wait8(SYNC, 0x80);
  for (u32 i = 0; i < 64; i++) write32(REGFILE + 4 * i, 0);  /* kernels assume zeroed Tensix GPRs */
  if (read32(LAUNCH) & (4 << TRISC)) JUMP(CODE_TRISC0 + TRISC * 0x1000);
  JUMP(FW + 4);
}

NORETURN firmware_boot(void) {
  configure_csr(1);
  write8(SYNC, 2);
  fence();
  launch();
}

NORETURN firmware_resume(void) {
  write8(SYNC, 0);
  fence();
  launch();
}
