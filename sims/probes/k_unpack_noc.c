/* BRISC/NCRISC NoC traffic against the unpacking tile's L1 (unpack.py contention cases).
 *
 * mode 0 (self):   on the unpacking tile itself, NoC writes from local [src, src+size) to its own coordinate at dst.
 *                  The transaction reads and writes this tile's L1 without leaving it. Stops at FL_DONE or `max`.
 * mode 1 (wr_in):  on another tile: writes size bytes from its local src into target:dst (incoming L1 writes).
 * mode 2 (rd_out): on another tile: reads size bytes from target:dst into its local src (outgoing L1 reads).
 * Remote modes cannot see FL_DONE (it is in the target's L1), so they run exactly `max` commands; the host sizes
 * `max` to outlast the measurement, and they post FL_END to the target when they stop so T0 can tell.
 * The generator posts FL_START (locally, or by an inline write to the target) after its first command.
 * Writes are posted (no acks), as llama's bulk writes; one command buffer, re-armed only via CMD_CTRL. */
#include "unpack.h"

enum { P_MODE, P_NOC, P_SIZE, P_TARGET, P_DST, P_MAX, P_SRC, P_BUF };
enum { SITE_READY = 1, SITE_SIGNAL, SITE_DRAIN };
#define CTRL_BULK (CTRL_VC_STATIC | CTRL_STATIC_VC(1))

KERNEL kernel_main(void) {
  u32 mode = PARAM(P_MODE), noc = PARAM(P_NOC), size = PARAM(P_SIZE), max = PARAM(P_MAX), src = PARAM(P_SRC);
  u32 c = CMDBUF(noc, PARAM(P_BUF)), target = mode ? PARAM(P_TARGET) : my_coord(noc), dst = PARAM(P_DST);
  WAIT_CMD_READY(c, SITE_READY);
  if (mode == 2) cmd_read(c, noc, target, dst, src, size, CTRL_BULK);
  else cmd_write(c, noc, src, target, dst, size, CTRL_BULK);
  u32 sent = NIU_STATUS(noc, mode == 2 ? CNT_RD_RESP : CNT_P_WR_SENT), base = read32(sent), n = 0;
  u32 t0 = now();
  for (; n < max; n++) {
    WAIT_CMD_READY(c, SITE_READY);
    fire(c);
    if (n == 0) {
      if (mode) {
        WAIT_CMD_READY(c, SITE_READY);
        signal_word(noc, PARAM(P_BUF) ^ 1, target, FL_START, 1, SITE_SIGNAL);
      } else write32(FL_START, 1);
    }
    if (!mode && (fence(), read32(FL_DONE))) { n++; break; }  /* fence: L0 data cache */
  }
  u32 t1 = now();
  WAIT_CMD_READY(c, SITE_DRAIN);
  WAIT_UNTIL(read32(sent) - base >= n, SITE_DRAIN);
  if (mode) signal_word(noc, PARAM(P_BUF) ^ 1, target, FL_END, 1, SITE_SIGNAL);
  else write32(FL_END, 1);
  log_word(0, t0);
  log_word(1, t1);
  log_word(2, n);
  log_word(3, now());
  write32(RES_COUNT, 4);
  probe_done();
}
