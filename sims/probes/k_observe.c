/* Watch one 32-bit register (e.g. this tile's NIU read-response counter) and log (t, value) at every change, or
 * every `period` cycles when period != 0, until `max` records or `duration` cycles. Runs on NCRISC beside a BRISC
 * traffic kernel (traffic.py dchain, arb.py). Ends on its own: the loop is bounded by the clock.
 * Optional `start` (param 4): wait for that wall-clock time first (refused if more than 2^28 cycles away).
 * aux = {records, t_start}. */
#include "probe.h"

KERNEL kernel_main(void) {
  u32 start = PARAM(4);
  if (start) {
    if ((int)(start - now()) > (1 << 28)) probe_fail(1);
    while ((int)(now() - start) < 0) {}
  }
  u32 addr = PARAM(0), max = PARAM(1), duration = PARAM(2), period = PARAM(3), t0 = now(), last = read32(addr), n = 0;
  log_word(0, t0); log_word(1, last); n = 1;
  u32 next = t0 + period;
  while (n < max) {
    u32 v = read32(addr), t = now();
    if (period ? (int)(t - next) >= 0 : v != last) {
      log_word(2 * n, t); log_word(2 * n + 1, v); n++; last = v; next += period;
    }
    if (t - t0 > duration) break;
  }
  write32(RES_AUX, n);
  write32(RES_AUX + 4, t0);
  probe_done();
}
