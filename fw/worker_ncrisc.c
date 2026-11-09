#include "worker.h"

FIRMWARE_ENTRY(SET_SP(STACK_TOP))

static NORETURN launch(void) {
  wait8(SUBORDINATE_SYNC, 0x80);
  u32 slot = SLOT_OFFSET(read32(GO_SIGNAL));  /* stays put until every RISC has returned */
  if (read32(LAUNCH + slot) & 2) JUMP(CODE_NCRISC + slot);
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
