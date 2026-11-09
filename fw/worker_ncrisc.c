#include "worker.h"

FIRMWARE_ENTRY(SET_SP(STACK_TOP))

static NORETURN launch(void) {
  wait8(SUBORDINATE_SYNC, 0x80);
  if (read32(LAUNCH) & 2) JUMP(CODE_NCRISC);
  JUMP(FW_NCRISC + 4);
}

NORETURN firmware_boot(void) {
  configure_csr(0);
  write8(SUBORDINATE_SYNC, 2);
  fence();
  launch();
}

NORETURN firmware_resume(void) {
  write8(SUBORDINATE_SYNC, 0);
  fence();
  launch();
}
