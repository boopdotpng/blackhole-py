/* Sender-side NoC event timing on one tile's wall clock (events.py).
 *
 * single: `count` times, fire one command, poll an NIU_MST counter until it moves, log (t_fire, t_seen), then idle
 *         `period` cycles so nothing overlaps.
 * stream: fire `count` commands back to back (re-arming only CMD_CTRL), log each fire time, then the time the
 *         counter reaches base + count.
 * t_fire is read after the fence that orders the command setup, right before the CMD_CTRL store. */
#include "probe.h"

enum { P_MODE, P_NOC, P_OP, P_CTRL, P_COUNTER, P_TARGET, P_SIZE, P_COUNT, P_PERIOD, P_BUF, P_REMOTE, P_REMOTE_MID };
enum { MODE_SINGLE, MODE_STREAM };
enum { OP_WRITE, OP_READ };
enum { SITE_SETUP = 1, SITE_READY, SITE_COUNTER, SITE_DRAIN };

KERNEL kernel_main(void) {
  u32 noc = PARAM(P_NOC), c = CMDBUF(noc, PARAM(P_BUF)), cnt = NIU_STATUS(noc, PARAM(P_COUNTER));
  u32 target = PARAM(P_TARGET), size = PARAM(P_SIZE), count = PARAM(P_COUNT), period = PARAM(P_PERIOD);
  WAIT_CMD_READY(c, SITE_SETUP);
  u32 remote = PARAM(P_REMOTE) ? PARAM(P_REMOTE) : PAYLOAD, mid = PARAM(P_REMOTE_MID);  /* DRAM / host targets */
  if (PARAM(P_OP) == OP_WRITE) { cmd_write(c, noc, PAYLOAD, target, remote, size, PARAM(P_CTRL)); write32(c + C_RET_MID, mid); }
  else { cmd_read(c, noc, target, remote, PAYLOAD + 0x10000, size, PARAM(P_CTRL)); write32(c + C_TARG_MID, mid); }

  if (PARAM(P_MODE) == MODE_SINGLE) {
    for (u32 i = 0; i < count; i++) {
      WAIT_CMD_READY(c, SITE_READY);
      u32 base = read32(cnt);
      u32 t0 = fire(c);
      WAIT_UNTIL(read32(cnt) != base, SITE_COUNTER);
      u32 t1 = now();
      log_word(2 * i, t0);
      log_word(2 * i + 1, t1);
      u32 until = t1 + period;
      while ((int)(now() - until) < 0) {}
    }
    write32(RES_COUNT, 2 * count);
  } else {
    u32 base = read32(cnt);
    for (u32 i = 0; i < count; i++) {
      WAIT_CMD_READY(c, SITE_READY);
      log_word(i, fire(c));
    }
    WAIT_UNTIL(read32(cnt) - base >= count, SITE_COUNTER);
    log_word(count, now());
    write32(RES_COUNT, count + 1);
  }
  WAIT_CMD_READY(c, SITE_DRAIN);
  probe_done();
}
