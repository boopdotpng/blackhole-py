/* RISC L1 access under L1 traffic from other agents (riscsync.py l1lat cases).
 *
 * mode 0: dependent load chase over a ring of 16 words 4 KiB apart (every load misses the 4-line L0 data cache),
 *         `count` loads per sample.
 * mode 1: instruction fetch: a 1024-instruction straight-line loop body (past the ~128-instruction I-cache knee),
 *         `count` passes per sample.
 * Spins `delay` cycles first so the companions are streaming, runs SAMPLES samples, then raises the companions' stop
 * words (each given as a param, 0 = none). params: mode, count, ring base, delay, stop0, stop1. log: (t0, t1) pairs. */
#include "probe.h"

#define SAMPLES 6

__attribute__((noinline)) static void straight(u32 n) {
  __asm__ volatile("1:\n .rept 1023\n addi zero, zero, 0\n .endr\n addi %0, %0, -1\n bnez %0, 1b\n" : "+r"(n));
}

KERNEL kernel_main(void) {
  u32 mode = PARAM(0), count = PARAM(1), ring = PARAM(2), delay = PARAM(3), k = 0;
  for (u32 i = 0; i < 16; i++) write32(ring + 4096 * i, ring + 4096 * ((i + 1) % 16));
  fence();
  u32 until = now() + delay;
  while ((int)(now() - until) < 0) {}
  for (u32 s = 0; s < SAMPLES; s++) {
    u32 t0 = now();
    if (mode == 0) {
      u32 p = ring, n = count;
      __asm__ volatile("1: lw %0, 0(%0)\n addi %1, %1, -1\n bnez %1, 1b\n" : "+r"(p), "+r"(n));
      write32(RES_AUX + 8, p);
    } else straight(count);
    u32 t1 = now();
    log_word(k++, t0);
    log_word(k++, t1);
  }
  for (u32 i = 4; i < 6; i++) if (PARAM(i)) write32(PARAM(i), 1);
  fence();
  write32(RES_COUNT, k);
  probe_done();
}
