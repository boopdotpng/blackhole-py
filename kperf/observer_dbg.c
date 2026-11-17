/* Observer: sample debug-bus signals of remote Tensix tiles over NoC0. For each signal: write its select word to every
 * target's RISCV_DEBUG_REG_DBG_BUS_CNTL (non-posted, wait for acks), then read every target's DBG_RD_DATA.
 * Config at CFG: [0] n targets, [1] n signals, [2] log base, [3] log end, [4] stop (host writes 1), [5] sweeps done,
 * [8..8+n) target NoC coords, [40..40+s) select words. Record per sweep: {wall_lo, wall_hi, {t_lo, value[target]}[signal]}
 * where t_lo is the wall clock when that signal's reads were issued. */
#include "hw.h"
#define NIU0 0xFFB20000
#define RD ((volatile u32 *)(NIU0 + 1 * 0x800))
#define WR ((volatile u32 *)(NIU0 + 2 * 0x800))
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, CMD_CTRL = 16 };
#define WR_ACK_RECEIVED (NIU0 + 0x204)
#define RD_RESP_RECEIVED (NIU0 + 0x208)
#define DBG_CNTL 0xFFB12054
#define DBG_DATA 0xFFB1205C
#define STAGE_W 0x18000   /* select word at +4: same low 4 bits as DBG_CNTL */
#define STAGE_R 0x18100   /* 16 B per target, data at +0xC */

static void send(volatile u32 *c) { fence(); c[CMD_CTRL] = 1; fence(); }

KERNEL kernel_main(void) {
  volatile u32 *cfg = (volatile u32 *)CFG;
  u32 n = cfg[0], ns = cfg[1], log = cfg[2], end = cfg[3], rec = 8 + 4 * (n + 1) * ns, count = 0;
  volatile u32 *coord = cfg + 8, *sel = cfg + 40;
  u32 self = read32(NIU0 + 0x148) & 0xFFF;
  RD[RET_MID] = 0; RD[RET_COORD] = self; RD[CTRL] = 0x10 | 0x80 | 1 << 13; RD[TARG_MID] = 0;
  WR[TARG_MID] = 0; WR[TARG_COORD] = self; WR[CTRL] = 0x2 | 0x10 | 0x80 | 1 << 13; WR[RET_MID] = 0;
  while (!cfg[4] && log + rec <= end) {
    write32(log, read32(WALL_CLOCK_L)); write32(log + 4, read32(WALL_CLOCK_H));
    for (u32 s = 0; s < ns; s++) {
      write32(STAGE_W + 4, sel[s]);
      fence();
      u32 w0 = read32(WR_ACK_RECEIVED);
      for (u32 i = 0; i < n; i++) {
        while (WR[CMD_CTRL]) {}
        WR[TARG_LO] = STAGE_W + 4; WR[RET_LO] = DBG_CNTL; WR[RET_COORD] = coord[i]; WR[AT_LEN_BE] = 4; WR[PACKET_TAG] = 3 << 10;
        send(WR);
      }
      while (read32(WR_ACK_RECEIVED) - w0 < n) {}
      u32 ts = read32(WALL_CLOCK_L);
      u32 r0 = read32(RD_RESP_RECEIVED);
      for (u32 i = 0; i < n; i++) {
        while (RD[CMD_CTRL]) {}
        RD[TARG_LO] = DBG_DATA; RD[TARG_COORD] = coord[i]; RD[RET_LO] = STAGE_R + 16 * i + 0xC; RD[AT_LEN_BE] = 4; RD[PACKET_TAG] = 2 << 10;
        send(RD);
      }
      while (read32(RD_RESP_RECEIVED) - r0 < n) {}
      fence();
      u32 at = log + 8 + 4 * s * (n + 1);
      write32(at, ts);
      for (u32 i = 0; i < n; i++) write32(at + 4 + 4 * i, read32(STAGE_R + 16 * i + 0xC));
    }
    log += rec; cfg[5] = ++count;
  }
  cfg[4] = 2;
  for (;;) {}
}
