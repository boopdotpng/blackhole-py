#include "worker.h"
#include "noc.h"

FIRMWARE_ENTRY(SET_SP(STACK_TOP))

static __attribute__((noinline)) void reset(void) { reset_tensix(); }  /* boot and resume share one copy */

static const unsigned short banks[] = {PERF_INSTRN, PERF_UNPACK, PERF_FPU, PERF_PACK};
#define RECORD(i) (PROFILE_RECORD + 4 * (i))

/* Profiled launches only, before the other RISCs are released: the NoC counts so far, then every bank cleared and
 * counting. */
static __attribute__((noinline)) void profile_start(void) {
  write32(RECORD(PROFILE_NOC_READ), NIU_READ_FLITS(0) + NIU_READ_FLITS(1));
  write32(RECORD(PROFILE_NOC_WRITE), NIU_WRITE_FLITS(0) + NIU_WRITE_FLITS(1));
  for (u32 i = 0; i < 4; i++) {
    u32 r = PERF_BASE + banks[i];
    write32(r, 0xFFFFFFFF);  /* reference period: never reached */
    write32(r + 4, 0);       /* mode 0, continuous */
    write32(r + 8, 0);
    write32(r + 8, PERF_START);
  }
}

/* Each bank's output offset from PERF_BASE + PERF_OUT_INSTRN, in banks[] order */
static const unsigned char outs[] = {0, PERF_OUT_UNPACK - PERF_OUT_INSTRN, PERF_OUT_FPU - PERF_OUT_INSTRN,
                                     PERF_OUT_PACK - PERF_OUT_INSTRN};
/* Record word PROFILE_EVENTS + i: banks[] index << 12 | select (tt-llk blackhole.h), in abi.h's order */
#define EV(bank, select) ((bank) << 12 | (select))
static const unsigned short events[PROFILE_WORDS - PROFILE_EVENTS] = {
  EV(2, 0), EV(2, 1),                          /* FPU, SFPU */
  EV(1, 7), EV(1, 8), EV(3, 18),               /* UNPACK0_BUSY_THREAD0, UNPACK1_BUSY_THREAD0, PACKER_BUSY */
  EV(0, 24), EV(0, 25), EV(0, 26),             /* THREAD_STALLS_0-2 */
  EV(0, 29), EV(0, 30),                        /* WAITING_FOR_SRCA_VALID, WAITING_FOR_SRCB_VALID */
  EV(0, 35), EV(0, 44), EV(0, 53),             /* WAITING_FOR_NONZERO_SEM_0-2 */
  EV(0, 36), EV(0, 45), EV(0, 54),             /* WAITING_FOR_NONFULL_SEM_0-2 */
  EV(0, 256), EV(0, 264), EV(0, 272)};         /* THREAD_INSTRUCTIONS_0-2 */

/* After every RISC has returned and before done is signalled: stop, read, send the record and wait for its ack, so it
 * is in host memory before dispatch can retire the launch. */
static __attribute__((noinline)) void profile_finish(void) {
  for (u32 i = 0; i < 4; i++) {
    u32 r = PERF_BASE + banks[i] + 8;
    write32(r, 0);
    write32(r, PERF_STOP);
  }
  write32(RECORD(PROFILE_CYCLES), read32(PERF_BASE + PERF_OUT_INSTRN));  /* reference cycles, whatever the select */
  for (u32 i = 0; i < PROFILE_WORDS - PROFILE_EVENTS; i++) {
    u32 e = events[i], mode = PERF_BASE + banks[e >> 12] + 4, select = (e & 0x1FF) << 8;
    write32(mode, select);
    while (read32(mode) != select) {}  /* the new select has taken effect */
    write32(RECORD(PROFILE_EVENTS + i), read32(PERF_BASE + PERF_OUT_INSTRN + outs[e >> 12] + 4));
  }
  write32(RECORD(PROFILE_NOC_READ), NIU_READ_FLITS(0) + NIU_READ_FLITS(1) - read32(RECORD(PROFILE_NOC_READ)));
  write32(RECORD(PROFILE_NOC_WRITE), NIU_WRITE_FLITS(0) + NIU_WRITE_FLITS(1) - read32(RECORD(PROFILE_NOC_WRITE)));
  u32 id = read32(WORKER_ID);
  write32(RECORD(PROFILE_ID), 1u << 31 | id);
  fence();
  u32 lo = read32(PROFILE_ADDR), hi = read32(PROFILE_ADDR + 4), offset = id * PROFILE_RECORD_SIZE;
  lo += offset;
  hi += lo < offset;
  noc_write_host(1, PROFILE_RECORD, lo, hi, PROFILE_RECORD_SIZE);
}

static NORETURN launch(void) {
  WAIT_FAST(read8(GO_SIGNAL) == 0x80);  /* every RISC of this core has returned: nothing to contend with */
  u32 slot = SLOT_OFFSET(read32(GO_SIGNAL));
  invalidate_icache();  /* every RISC: the slot may hold lines from the launch before last */
  u32 token = read32(LAUNCH_TOKEN) + 1;
  write32(LAUNCH_TOKEN, token);
  fence();
  if (read32(GO_SIGNAL) >> GO_PROFILE_BIT & 1) profile_start();
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
  u32 go = read32(GO_SIGNAL), dispatch = go >> 8 & 0xFFF;
  if (go >> GO_PROFILE_BIT & 1) profile_finish();
  write8(GO_SIGNAL, 0);
  fence();
  noc_atomic_inc(1, DONE_COUNT, dispatch, 1);
  reset();  /* off the critical path: overlaps the dispatcher collecting done counts and sending the next GO.
                    * Safe because every TRISC drained its Tensix thread before returning. */
  launch();
}
