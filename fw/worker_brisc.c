#include "worker.h"
#include "noc.h"

FIRMWARE_ENTRY(SET_SP(STACK_TOP))

static __attribute__((noinline)) void reset(void) { reset_tensix(); }  /* boot and resume share one copy */

static NORETURN launch(void) {
  WAIT_FAST(read8(GO_SIGNAL) == 0x80);  /* every RISC of this core has returned: nothing to contend with */
  u32 slot = SLOT_OFFSET(read32(GO_SIGNAL));
  invalidate_icache();  /* every RISC: the slot may hold lines from the launch before last */
  u32 token = read32(LAUNCH_TOKEN) + 1;
  write32(LAUNCH_TOKEN, token);
  fence();
  write8(SUBORDINATE_SYNC, 0x80);                 /* NCRISC */
  for (u32 i = 0; i < 3; i++) write32(PCBUF(i), token);  /* TRISCs */
  fence();
  if (read32(LAUNCH + slot) & 1) JUMP(CODE_BRISC + slot);
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
  write32(LAUNCH_TOKEN, read32(WALL_CLOCK_L) | 1);  /* fresh per boot: a token from before cannot match */
  fence();
  write32(SOFT_RESET, 0);
  WAIT_FAST(read32(SUBORDINATE_SYNC) == 0x02020202);
  reset();
  launch();
}

NORETURN firmware_resume(void) {
  WAIT_SLOW(read8(SUBORDINATE_SYNC) == 0);  /* NCRISC back in firmware */
  u32 token = read32(LAUNCH_TOKEN);
  for (u32 i = 0; i < 3; i++)       /* blocking mailbox reads; a value from an aborted run does not match */
    while (read32(MAILBOX_FROM(i)) != token) {}
  fence();
  u32 dispatch = read32(GO_SIGNAL) >> 8 & 0xFFF;
  write8(GO_SIGNAL, 0);
  fence();
  noc_atomic_inc(1, DONE_COUNT, dispatch, 1);
  reset();  /* off the critical path: overlaps the dispatcher collecting done counts and sending the next GO.
                    * Safe because every TRISC drained its Tensix thread before returning. */
  launch();
}
