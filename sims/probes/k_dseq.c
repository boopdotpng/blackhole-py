/* One DRAM read at a time over an address pattern (traffic.py dseq): command i reads bank banks[i % nb] (port
 * `port`) at base + ((i / nb) * stride & 0x1FFFF) (stays inside the 128 KiB the dinit cases wrote), waits for its response, logs (t_fire, latency), idles `period` cycles. */
#include "probe.h"

enum { P_COUNT, P_SIZE, P_PERIOD, P_NB, P_BANKS, P_PORT, P_BASE, P_STRIDE };
enum { SITE_READY = 1, SITE_RESP };

KERNEL kernel_main(void) {
  u32 count = PARAM(P_COUNT), size = PARAM(P_SIZE), period = PARAM(P_PERIOD), nb = PARAM(P_NB), banks = PARAM(P_BANKS);
  u32 port = PARAM(P_PORT), base = PARAM(P_BASE), stride = PARAM(P_STRIDE);
  u32 c = CMDBUF(0, 0), cnt = NIU_STATUS(0, CNT_RD_RESP), coords[8];
  for (u32 j = 0; j < nb; j++) coords[j] = dram_coord(banks >> (4 * j) & 7, port);
  WAIT_CMD_READY(c, SITE_READY);
  cmd_read(c, 0, coords[0], base, PAYLOAD, size, CTRL_VC_STATIC | CTRL_STATIC_VC(1));
  u32 j = 0, off = 0;
  for (u32 i = 0; i < count; i++) {
    WAIT_CMD_READY(c, SITE_READY);
    write32(c + C_TARG_LO, base + (off & 0x1FFFF));
    write32(c + C_TARG_COORD, coords[j]);
    u32 b0 = read32(cnt);
    u32 t0 = fire(c);
    WAIT_UNTIL(read32(cnt) != b0, SITE_RESP);
    u32 t1 = now();
    log_word(2 * i, t0);
    log_word(2 * i + 1, t1 - t0);
    if (++j == nb) { j = 0; off += stride; }
    u32 until = t1 + period;
    while ((int)(now() - until) < 0) {}
  }
  write32(RES_COUNT, 2 * count);
  probe_done();
}
