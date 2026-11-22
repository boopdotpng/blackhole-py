#pragma once
#include "noc.h"

#ifdef ROLE_BRISC
void brisc_step(void);
__attribute__((weak)) void brisc_init(void) {}

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j _crt0_brisc\n");

INLINE u32 worker_rank_row_major(void) { return read32(WORKER_Y) * read32(GRID_COLS_L1) + read32(WORKER_X); }

INLINE u32 dram_stagger_offset(u32 rank) { return (2u * rank + 1u) * 256u; }

INLINE void barrier_all(u32 coord0, u32 rect, u32 exclude, u32 n_workers, u32 *ep) {
  u32 next = ++(*ep);
  fence();
  if (read32(WORKER_ID) == 0) {
    while (read32(SYNC_ARRIVED) != n_workers - 1) fence();
    write32(SYNC_ARRIVED, 0);
    write32(SYNC_EPOCH, next);
    fence();
    noc_mcast(0, SYNC_EPOCH, SYNC_EPOCH, rect, exclude, 4);
    noc_mcast_flush(0);
  } else {
    noc_atomic_inc(1, SYNC_ARRIVED, coord0, 1);
    WAIT_FAST(read32(SYNC_EPOCH) == next);
  }
}

NORETURN _crt0_brisc(void) {
  configure_csr(0);
  invalidate_icache();
  u32 node = read32(0xFFB20148), x = node & 63, y = ((node >> 6) & 63) - 2;
  x -= 1 + 2 * (x >= 10);
  write32(WORKER_X, x); write32(WORKER_Y, y); write32(WORKER_ID, x * 10 + y);
  enable_clock_gating();
  reset_tensix();
  noc_init(0);

  u32 expect = 0x40404040, reset = RESET_ALL & ~RESET_BRISC, en_nc = read32(ROLE_PC) != 0, en_tr = 0;
  write32(SUBORDINATE_SYNC, expect);
  write32(STEP_TOKEN, read32(WALL_CLOCK_L) | 1);
  if (en_nc) {
    write32(NCRISC_RESET_PC, read32(ROLE_PC));
    write32(NCRISC_RESET_PC_OVERRIDE, 1);
    reset &= ~RESET_NCRISC;
    expect ^= 0x42u;
  }
  for (u32 i = 0; i < 3; i++) {
    u32 pc = read32(ROLE_PC + 4 + 4 * i);
    if (!pc) continue;
    write32(TRISC0_RESET_PC + 4 * i, pc);
    en_tr |= 1u << i;
    reset &= ~(RESET_TRISC0 << i);
    expect ^= 0x42u << 8 * (i + 1);
  }
  if (en_tr) write32(TRISC_RESET_PC_OVERRIDE, en_tr);
  fence();
  write32(SOFT_RESET, reset);
  WAIT_FAST(read32(SUBORDINATE_SYNC) == expect);
  brisc_init();
  for (u32 last_epoch = 0;;) {
    u32 ep;
    WAIT_FAST((ep = read32(STEP_EPOCH)) != last_epoch);
    last_epoch = ep;
    u32 tok = read32(STEP_TOKEN) + 1;
    write32(STEP_TOKEN, tok);
    fence();
    if (en_nc) write8(SUBORDINATE_SYNC, 0x80);
    for (u32 i = 0; i < 3; i++) if (en_tr >> i & 1) write32(PCBUF(i), tok);
    fence();
    brisc_step();
    if (en_nc) WAIT_SLOW(read8(SUBORDINATE_SYNC) == 0);
    for (u32 i = 0; i < 3; i++)
      if (en_tr >> i & 1)
        while (read32(MAILBOX_FROM(i)) != tok) {}
    fence();
    reset_cb_counters();
    noc_atomic_inc(1, SVC_DONE_COUNT, read32(SERVICE_COORD), 1);
  }
}
#endif

#ifdef ROLE_NCRISC
void ncrisc_step(void);
__attribute__((weak)) void ncrisc_init(void) {}

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j _crt0_ncrisc\n");

NORETURN _crt0_ncrisc(void) {
  configure_csr(0);
  noc_init(1);
  ncrisc_init();
  write8(SUBORDINATE_SYNC, 2);
  fence();
  for (;;) {
    WAIT_SLOW(read8(SUBORDINATE_SYNC) == 0x80);
    ncrisc_step();
    fence();
    write8(SUBORDINATE_SYNC, 0);
  }
}
#endif

#ifdef ROLE_TRISC
void trisc_step(void);
__attribute__((weak)) void trisc_init(void) {}

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(TRISC_STACK_TOP)
        SET_GP(TRISC_GP)
        "j _crt0_trisc\n");

NORETURN _crt0_trisc(void) {
  configure_csr(1);
  write32(CFG_RISCV_IC_INVALIDATE, 2u << ROLE_TRISC);
  fence();
  reset_thread();
  trisc_init();
  write8(SUBORDINATE_SYNC + 1 + ROLE_TRISC, 2);
  fence();
  for (;;) {
    u32 tok;
    do {
      tok = read32(PC_BUF_BASE);
      fence();
    } while (tok != read32(STEP_TOKEN));
    trisc_step();
    tensix_drain();
    fence();
    write32(MAILBOX_TO_BRISC, tok);
  }
}
#endif
