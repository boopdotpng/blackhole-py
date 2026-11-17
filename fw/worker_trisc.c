#include "worker.h"

FIRMWARE_ENTRY(SET_SP(TRISC_STACK_TOP) SET_GP(TRISC_GP))

#define SYNC (SUBORDINATE_SYNC + 1 + TRISC)
#define FW (FW_TRISC0 + TRISC * (FW_TRISC1 - FW_TRISC0))

static NORETURN launch(void) {
  wait8(SYNC, 0x80);
  reset_thread();
  u32 slot = SLOT_OFFSET(read32(GO_SIGNAL));  /* stays put until every RISC has returned */
  if (read32(LAUNCH + slot) & (4 << TRISC)) JUMP(CODE_TRISC0 + TRISC * CODE_TRISC_SIZE + slot);
  JUMP(FW + 4);
}

NORETURN firmware_boot(void) {
  configure_csr(1);
  write8(SYNC, 2);
  fence();
  launch();
}

NORETURN firmware_resume(void) {
  tensix_drain();  /* kernels return with Tensix work queued; BRISC resets the Tensix as soon as every RISC is back */
  write8(SYNC, 0);
  fence();
  launch();
}
