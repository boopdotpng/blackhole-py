/* L1 pressure from a RISC (traffic.py l1 cases): `count` word loads (mode 0) or stores (mode 1), 4 per iteration,
 * over a 4 KiB buffer, as fast as the core issues them. aux = {count, t_end, t_start}. */
#include "probe.h"

#define BUF 0x150000

KERNEL kernel_main(void) {
  u32 mode = PARAM(0), count = PARAM(1), t0 = now(), acc = 0;
  volatile u32 *p = (volatile u32 *)BUF;
  if (mode == 0) {
    for (u32 i = 0; i < count; i += 4) acc += p[i & 1023] + p[(i + 1) & 1023] + p[(i + 2) & 1023] + p[(i + 3) & 1023];
  } else {
    for (u32 i = 0; i < count; i += 4) { p[i & 1023] = i; p[(i + 1) & 1023] = i; p[(i + 2) & 1023] = i; p[(i + 3) & 1023] = i; }
  }
  u32 t1 = now();
  write32(RES_AUX, count);
  write32(RES_AUX + 4, t1);
  write32(RES_AUX + 8, t0);
  write32(RES_AUX + 12, acc);
  probe_done();
}
