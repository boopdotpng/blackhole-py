/* Quiet filler (tile.py Card.quiet): runs on every role a probe does not use, instead of the firmware's idle loop,
 * which polls an L1 byte (read + fence) back to back and so contends with the measured core's L1 traffic.
 * Spins in registers and looks at its stop word (RES + 0x80, set by the host once every measured role has reported
 * a status) only once per CHUNK iterations, so it adds one L1 read per ~10k cycles. Gives up after ~2^30 iterations.
 * aux = {t_start, t_stop, polls}. */
#include "probe.h"
#define STOP  (RES + 0x80)
#define CHUNK 4096u

KERNEL kernel_main(void) {
  u32 t0 = now(), polls = 0;
  for (;;) {
    u32 n = CHUNK;
    __asm__ volatile("1: addi %0, %0, -1\n bnez %0, 1b" : "+r"(n));
    fence();  /* L0 data cache: re-read the stop word from L1 */
    polls++;
    if (read32(STOP)) break;
    if (polls >> 18) probe_fail(1);
  }
  write32(RES_AUX, t0); write32(RES_AUX + 4, now()); write32(RES_AUX + 8, polls);
  probe_done();
}
