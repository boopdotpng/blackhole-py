#include "worker.h"

FIRMWARE_ENTRY(SET_SP(TRISC_STACK_TOP) SET_GP(TRISC_GP))

#define SYNC (SUBORDINATE_SYNC + 1 + TRISC)
#define FW (FW_TRISC0 + TRISC * (FW_TRISC1 - FW_TRISC0))

static NORETURN launch(void) {
  for (;;) {  /* blocks in the PCBuf read: no L1 traffic while idle */
    u32 token = read32(PC_BUF_BASE);
    fence();
    if (token == read32(LAUNCH_TOKEN)) break;
  }
  /* BRISC's I-cache invalidate at launch does not reach a TRISC blocked in the PCBuf read: without this, a kernel
   * installed in the slot of an earlier one ran the earlier one's cached instructions. */
  write32(CFG_RISCV_IC_INVALIDATE, 2 << TRISC);
  fence();
  u32 slot = SLOT_OFFSET(read32(GO_SIGNAL));  /* stays put until every RISC has returned */
  if (read32(LAUNCH + slot) & (4 << TRISC)) JUMP(CODE_TRISC0 + TRISC * CODE_TRISC_SIZE + slot);
  JUMP(FW + 4);
}

NORETURN firmware_boot(void) {
  configure_csr(1);
  reset_thread();
  write8(SYNC, 2);
  fence();
  launch();
}

NORETURN firmware_resume(void) {
  tensix_drain();  /* kernels return with Tensix work queued: finish it before reporting done */
  fence();
  write32(MAILBOX_TO_BRISC, read32(LAUNCH_TOKEN));  /* done with this launch */
  launch();
}
