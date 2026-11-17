/* Observer: sample remote 32-bit registers (e.g. DRAM-tile NIU counters) over NoC0 into an L1 log, until stopped.
 * Config at CFG: [0] n targets, [1] log base, [2] log end, [3] period (cycles), [4] stop flag (host writes 1),
 * [5] records written (we write), then n x {lo, mid, coord, pad}. Record: {wall_lo, wall_hi, done_lo, value[n]}: wall clock
 * before the first read is issued and (low word) after the last response arrives. Under NoC congestion the reads can take
 * 5x their usual time, so the start stamp alone misdates the values. */
#include "hw.h"
#define NIU0 0xFFB20000
#define CMD ((volatile u32 *)(NIU0 + 1 * 0x800))  /* read command buffer */
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, CMD_CTRL = 16 };
#define RD_RESP_RECEIVED (NIU0 + 0x208)     /* NIU_MST_RD_RESP_RECEIVED: one per completed read */
#define STAGE 0x18000                         /* 16 B per target: NoC reads keep the source's low address bits */

KERNEL kernel_main(void) {
  volatile u32 *cfg = (volatile u32 *)CFG;
  u32 n = cfg[0], log = cfg[1], end = cfg[2], period = cfg[3], rec = 12 + 4 * n, count = 0;
  volatile u32 *tg = cfg + 8;
  u32 self = read32(NIU0 + 0x148) & 0xFFF;
  CMD[RET_MID] = 0; CMD[RET_COORD] = self; CMD[CTRL] = 0x10 | 0x80 | 1 << 13; CMD[PACKET_TAG] = 2 << 10;
  u32 next = read32(WALL_CLOCK_L);
  while (!cfg[4] && log + rec <= end) {
    while ((int)(read32(WALL_CLOCK_L) - next) < 0) {}
    u32 lo = read32(WALL_CLOCK_L), hi = read32(WALL_CLOCK_H);
    next = lo + period;
    u32 r0 = read32(RD_RESP_RECEIVED);
    for (u32 i = 0; i < n; i++) {
      u32 a = tg[4 * i];
      while (CMD[CMD_CTRL]) {}
      CMD[TARG_LO] = a; CMD[TARG_MID] = tg[4 * i + 1]; CMD[TARG_COORD] = tg[4 * i + 2];
      CMD[RET_LO] = STAGE + 16 * i + (a & 15); CMD[AT_LEN_BE] = 4; CMD[PACKET_TAG] = 2 << 10;
      fence(); CMD[CMD_CTRL] = 1; fence();
    }
    while (read32(RD_RESP_RECEIVED) - r0 < n) {}
    fence();
    write32(log, lo); write32(log + 4, hi); write32(log + 8, read32(WALL_CLOCK_L));
    for (u32 i = 0; i < n; i++) write32(log + 12 + 4 * i, read32(STAGE + 16 * i + (tg[4 * i] & 15)));
    log += rec; cfg[5] = ++count;
  }
  cfg[4] = 2;     /* done; never return: we were started directly, not by the dispatcher */
  for (;;) {}
}
