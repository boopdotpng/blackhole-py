/* Streams of NoC reads or writes from one RISC, issued the way the llama kernels issue them (traffic.py).
 *
 * Up to 4 streams, each on its own (NoC, command buffer, transaction id), issued round-robin `count` times each.
 * Per command: wait for the buffer to be ready, optionally (cap != 0) wait until fewer than `cap` requests of this
 * tid are outstanding (and, for writes, fewer than `cap` not yet sent), point the command at the next page, fire.
 * The loop is kept lean (bank coordinates precomputed, addresses advanced by addition) so the RISC issues about as
 * fast as the command buffer accepts: these probes measure the NoC and DRAM, not ttrv's issue code. DRAM streams walk pages interleaved over the 8 banks through the core's port, as llama does; tile streams
 * hit one fixed remote address. Control words match the kernels: VC static 1, reads 0x2090, writes 0x2092 (0x2082
 * when posted).
 *
 * aux[0] start time, aux[1+s] when stream s finished (outstanding 0, or outgoing 0 for posted writes),
 * aux[5+s] stream s's first issue. Optional log: every fire time, in issue order. */
#include "probe.h"

enum { P_CFG, P_COUNT, P_START, P_CAP, P_S0 };  /* stream s: words P_S0 + 3s .. +2 */
enum { SITE_START = 1, SITE_READY, SITE_CAP, SITE_DONE };
#define MAXS 4
/* stream word 0 */
#define S_NOC(w)    ((w) & 1)
#define S_BUF(w)    ((w) >> 1 & 3)
#define S_WRITE(w)  ((w) >> 3 & 1)
#define S_DRAM(w)   ((w) >> 4 & 1)
#define S_PORT(w)   ((w) >> 5 & 3)
#define S_POSTED(w) ((w) >> 7 & 1)
#define S_TID(w)    ((w) >> 8 & 15)
#define S_FIXED(w)  ((w) >> 12 & 1)     /* DRAM stream pinned to one endpoint: translated coordinate in bits 16-27 */
#define S_COORD(w)  ((w) >> 16 & 0xFFF)
/* stream word 1: size in bits 0-15; for fixed streams bits 16-31 = stride in 256-byte units (0 = size). A fixed stream
 * advances its address every command and wraps inside an 8 MiB window: base + (offset & 0x7FFFFF). */
#define WINDOW_MASK 0x7FFFFF
/* stream word 1: bytes per command; word 2: DRAM bank offset of page 0, or tile coordinate (remote address PAYLOAD) */

KERNEL kernel_main(void) {
  u32 cfg = PARAM(P_CFG), ns = cfg & 7, log_issue = cfg >> 8 & 1, count = PARAM(P_COUNT), cap = PARAM(P_CAP);
  u32 cmd[MAXS], w[MAXS], size[MAXS], base[MAXS], outst[MAXS], outg[MAXS], first[MAXS], addr[MAXS], coords[MAXS][8];
  u32 stride[MAXS], off[MAXS];
  for (u32 s = 0; s < ns; s++) {
    u32 x = PARAM(P_S0 + 3 * s);
    u32 w1 = PARAM(P_S0 + 3 * s + 1);
    w[s] = x; size[s] = w1 & 0xFFFF; base[s] = PARAM(P_S0 + 3 * s + 2);
    stride[s] = (w1 >> 16) ? (w1 >> 16) * 256 : size[s]; off[s] = 0;
    cmd[s] = CMDBUF(S_NOC(x), S_BUF(x));
    outst[s] = NIU(S_NOC(x)) + 0x240 + 4 * S_TID(x);
    outg[s] = NIU(S_NOC(x)) + 0x280 + 4 * S_TID(x);
    u32 local = PAYLOAD + s * 0x10000;
    u32 ctrl = CTRL_VC_STATIC | CTRL_STATIC_VC(1) | (S_WRITE(x) && !S_POSTED(x) ? CTRL_RESP_MARKED : 0);
    u32 rc = S_DRAM(x) ? (S_FIXED(x) ? S_COORD(x) : dram_coord(0, S_PORT(x))) : base[s], ra = S_DRAM(x) ? base[s] : PAYLOAD;
    WAIT_CMD_READY(cmd[s], SITE_READY);
    if (S_WRITE(x)) cmd_write(cmd[s], S_NOC(x), local, rc, ra, size[s], ctrl);
    else cmd_read(cmd[s], S_NOC(x), rc, ra, local, size[s], ctrl);
    write32(cmd[s] + C_PACKET_TAG, TAG_TID(S_TID(x)));
    for (u32 b = 0; b < 8; b++) coords[s][b] = S_FIXED(x) ? S_COORD(x) : dram_coord(b, S_PORT(x));
    addr[s] = base[s];
  }
  u32 start = PARAM(P_START);
  if (start) {
    if ((int)(start - now()) > (1 << 28)) probe_fail(SITE_START);
    while ((int)(now() - start) < 0) {}
  }
  write32(RES_AUX, now());

  u32 n = 0;
  for (u32 i = 0; i < count; i++) {
    for (u32 s = 0; s < ns; s++) {
      u32 x = w[s], c = cmd[s];
      WAIT_CMD_READY(c, SITE_READY);
      if (cap) {
        WAIT_UNTIL(read32(outst[s]) < cap, SITE_CAP);
        if (S_WRITE(x)) WAIT_UNTIL(read32(outg[s]) < cap, SITE_CAP);
      }
      u32 bank = i & 7;
      if (S_DRAM(x)) {
        if (S_WRITE(x)) { write32(c + C_RET_LO, addr[s]); write32(c + C_RET_COORD, coords[s][bank]); }
        else { write32(c + C_TARG_LO, addr[s]); write32(c + C_TARG_COORD, coords[s][bank]); }
      }
      u32 t = fire(c);
      if (S_FIXED(x)) { off[s] += stride[s]; addr[s] = base[s] + (off[s] & WINDOW_MASK); }
      else if (bank == 7) addr[s] += size[s];
      if (i == 0) first[s] = t;
      if (log_issue) log_word(n++, t);
    }
  }

  u32 pending = (1u << ns) - 1, left = BUDGET;
  while (pending) {
    for (u32 s = 0; s < ns; s++) {
      if (!(pending >> s & 1)) continue;
      u32 busy = S_WRITE(w[s]) && S_POSTED(w[s]) ? read32(outg[s]) : read32(outst[s]);
      if (!busy) { write32(RES_AUX + 4 * (1 + s), now()); pending &= ~(1u << s); }
    }
    if (!--left) probe_fail(SITE_DONE);
  }
  for (u32 s = 0; s < ns; s++) write32(RES_AUX + 4 * (5 + s), first[s]);
  write32(RES_COUNT, n);
  probe_done();
}
