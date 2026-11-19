/* BRISC side of the pack probes (pack.py).
 *
 * mode 0 traffic: a stream of NoC writes (posted) or reads of `size` bytes between this tile's `local` buffer and
 *   `target`:`remote` (target 0xFFFFFFFF = this tile, through its own NIU), back to back, until TRISC2 sets PK_STOP,
 *   `dur` cycles pass (dur != 0: used on a remote tile, which can't see PK_STOP), or `max` commands. PK_TRAFFIC_UP
 *   gets the start time (| 1) so TRISC2 starts timing only inside the stream. aux[0] start, aux[1] end, aux[2] count.
 * mode 1 visibility reader: per sample, wait for PK_VIS_GO == s + 1, then fire `reads` 16 B NoC reads of `visaddr` on
 *   this tile into PK_VIS_SLOTS + 16 i back to back, wait for every response, log the fire times then each slot's
 *   first word, set PK_VIS_DONE = s + 1. The first read that returns the packed value bounds when an outgoing NoC
 *   read sees the pack's data. */
#include "pack.h"

enum { P_MODE, P_NOC, P_OP, P_TARGET, P_LOCAL, P_REMOTE, P_SIZE, P_MAX, P_DUR, P_SAMPLES, P_READS, P_VISADDR };
enum { SITE_SETUP = 1, SITE_READY, SITE_DRAIN, SITE_GO, SITE_RESP };

KERNEL kernel_main(void) {
  u32 noc = PARAM(P_NOC), c = CMDBUF(noc, 0);
  u32 target = PARAM(P_TARGET) == 0xFFFFFFFFu ? my_coord(noc) : PARAM(P_TARGET);
  WAIT_CMD_READY(c, SITE_SETUP);
  if (PARAM(P_MODE) == 0) {
    u32 rd = PARAM(P_OP), size = PARAM(P_SIZE), max = PARAM(P_MAX), dur = PARAM(P_DUR);
    if (rd) cmd_read(c, noc, target, PARAM(P_REMOTE), PARAM(P_LOCAL), size, 0);
    else cmd_write(c, noc, PARAM(P_LOCAL), target, PARAM(P_REMOTE), size, 0);
    u32 cnt = NIU_STATUS(noc, rd ? CNT_RD_RESP : CNT_P_WR_SENT), base = read32(cnt), n = 0;
    u32 t0 = now();
    write32(PK_TRAFFIC_UP, t0 | 1);
    while (n < max) {
      if (dur ? (now() - t0) > dur : (fence(), read32(PK_STOP) != 0)) break;  /* fence: L0 data cache */
      WAIT_CMD_READY(c, SITE_READY);
      fire(c);
      n++;
    }
    u32 t1 = now();
    WAIT_CMD_READY(c, SITE_DRAIN);
    WAIT_UNTIL(read32(cnt) - base >= n, SITE_DRAIN);
    write32(RES_AUX, t0); write32(RES_AUX + 4, t1); write32(RES_AUX + 8, n);
  } else {
    u32 samples = PARAM(P_SAMPLES), reads = PARAM(P_READS), nlog = 0;
    u32 cnt = NIU_STATUS(noc, CNT_RD_RESP);
    cmd_read(c, noc, target, PARAM(P_VISADDR), PK_VIS_SLOTS, 16, 0);
    for (u32 s = 0; s < samples; s++) {
      WAIT_L1(read32(PK_VIS_GO) == s + 1, SITE_GO);
      u32 base = read32(cnt);
      for (u32 i = 0; i < reads; i++) {
        WAIT_CMD_READY(c, SITE_READY);
        write32(c + C_RET_LO, PK_VIS_SLOTS + 16 * i);
        log_word(nlog++, fire(c));
      }
      WAIT_UNTIL(read32(cnt) - base >= reads, SITE_RESP);
      for (u32 i = 0; i < reads; i++) log_word(nlog++, read32(PK_VIS_SLOTS + 16 * i));
      write32(PK_VIS_DONE, s + 1);
    }
    write32(RES_COUNT, nlog);
  }
  probe_done();
}
