// Appended after each RISC's kernel body: drain outstanding work, then spin forever.
#include "noc.h"

__asm__(".section .entry, \"ax\", @progbits\n"
#if ROLE >= ROLE_TRISC0
        "li t0, " STR(COPROCESSOR_DONE_CHECK) "\n"
        "sw zero, 0(t0)\n"
        "lw t1, 0(t0)\n"
        "andi t1, t1, 0\n"
#endif
        "fence\n"
        "j park\n");

NORETURN park(void) {
#if ROLE < ROLE_TRISC0
  WAIT_SLOW(CMD_BUF(ROLE, READ_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(ROLE, WRITE_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(ROLE, MCAST_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(ROLE, ATOMIC_BUF)[CMD_CTRL] == 0);
  for (u32 tid = 0; tid < 16; tid++) {
    WAIT_SLOW(read32(OUTGOING(ROLE, tid)) == 0);
    WAIT_SLOW(read32(OUTSTANDING(ROLE, tid)) == read32(NOC_BASELINE + 4 * tid));
  }
#endif
#if ROLE != ROLE_BRISC
  *(volatile u8 *)(SUBORDINATE_SYNC + ROLE - ROLE_NCRISC) = 0;
  fence();
#else
  for (u32 i = 0; i < 4; i++)
    if (read32(ROLE_PC + 4 * i)) WAIT_SLOW(*(volatile u8 *)(SUBORDINATE_SYNC + i) == 0);
  // Every worker arrives only after its subordinate engines and NoC drain.
  noc_atomic_inc(0, WORK_DONE, read32(LEADER_COORD));
  if ((read32(NODE_ID(0)) & 0xFFF) == read32(LEADER_COORD)) {
    WAIT_SLOW(read32(WORK_DONE) == read32(NUM_WORKERS));
    if (read32(HOST_SIGNAL_ADDR) || read32(HOST_SIGNAL_ADDR + 4)) {
      noc_init(0);
      noc_write(0, read32(HOST_SIGNAL_ADDR), read32(HOST_SIGNAL_ADDR + 4), LAUNCH_SEQUENCE, 8);
    }
  }
#endif
  for (;;) __asm__ volatile("j .");
}
