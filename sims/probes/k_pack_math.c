/* TRISC1 side of the pack probes (pack.py): fills Dst with a known pattern from the SFPU, then plays the math thread
 * of the math -> pack handoff.
 *
 * Fill: for Dst tile t, row group g (4 rows), column parity p, one SFPLOADI + SFPIADD + SFPSTORE writes
 *   bits = base(t, g, p) + lane_term(lane)   (lane = (row % 4) * 8 + col / 2)
 * pattern 1 (fp32/bf16/bfp8): base = p << 31 | (64 + (16t + g) % 128) << 23, lane_term = lane << 17
 * pattern 2 (bfp4):           same base, lane_term = (lane & 3) << 21
 * pattern 3 (e4m3):           base = p << 31 | (121 + (16t + g) % 11) << 23, lane_term = lane << 20
 * pack.py's reference computes the same values. Every value is exact in its output format (see PACK.md).
 * Then STALLWAIT on the SFPU and SEMPOST(SEM_FILL): TRISC2 polls that semaphore before configuring the packer.
 *
 * Handoff (mode 1 latency, 2 pipeline): wait for TRISC2's PK_READY, then `n` times: poll MATH_PACK below `semmax`
 * (bounded; a timeout is counted in aux[1] but the post still happens, so TRISC2's SEMWAIT always ends), spin
 * `delay` cycles (latency: since the previous post; pipeline: the "math work" after the Dst section came free),
 * log now(), SEMPOST(MATH_PACK). */
#include "pack.h"

enum { P_PATTERN, P_DST16, P_TILES, P_HMODE, P_N, P_DELAY, P_SEMMAX };
enum { SITE_READY = 1 };

static void fill(u32 pattern, u32 dst16, u32 tiles) {
  if (pattern == 1) TTINSN(TT_SFPSHFT(16, 15, 1, 5));        /* L1 = (2 lane) << 16 = lane << 17 */
  else if (pattern == 2) {
    TTINSN(TT_SFPSHFT(29, 15, 1, 5));                          /* L1 = (2 lane) << 29: lane bits 0-1 at 30-31 */
    TTINSN(TT_SFPSHFT(-9, 0, 1, 1));                           /* L1 >>= 9 (logical): (lane & 3) << 21 */
  } else TTINSN(TT_SFPSHFT(19, 15, 1, 5));                     /* L1 = (2 lane) << 19 */
  TTINSN(TT_SFPNOP);
  u32 store = TT_SFPSTORE(0, dst16 ? 2 : 3, 0, 0);             /* BF16 into Dst16b, or FP32 into Dst32b */
  for (u32 t = 0; t < tiles; t++)
    for (u32 g = 0; g < 16; g++)
      for (u32 p = 0; p < 2; p++) {
        u32 e = pattern == 3 ? 121 + (16 * t + g) % 11 : 64 + ((16 * t + g) & 127);
        tensix_push(TT_SFPLOADI(0, 0, p << 15 | e << 7));     /* FLOATB: L0 = imm << 16 */
        TTINSN(TT_SFPIADD(0, 1, 0, 4));                         /* L0 = L1 + L0, flags untouched */
        TTINSN(TT_SFPNOP);
        tensix_push(store | (64 * t + 4 * g + 2 * p));
      }
  TTINSN(TT_STALLWAIT(STALL_SYNC, WAIT_SFPU | WAIT_MATH));
}

KERNEL kernel_main(void) {
  u32 mode = PARAM(P_HMODE), n = PARAM(P_N), delay = PARAM(P_DELAY), semmax = PARAM(P_SEMMAX);
  if (PARAM(P_PATTERN)) fill(PARAM(P_PATTERN), PARAM(P_DST16), PARAM(P_TILES));
  TTINSN(TT_SEMPOST(1 << SEM_FILL));
  tensix_drain();
  u32 late = 0;
  if (mode) {
    WAIT_L1(read32(PK_READY) != 0, SITE_READY);
    u32 last = now();
    for (u32 i = 0; i < n; i++) {
      u32 left = BUDGET;
      while (sem_value(SEM_MATH_PACK) >= semmax && --left) {}
      if (!left) late++;
      if (mode == 1) while ((int)(now() - (last + delay)) < 0) {}
      else { u32 until = now() + delay; while ((int)(now() - until) < 0) {} }
      last = now();
      TTINSN(TT_SEMPOST(1 << SEM_MATH_PACK));
      log_word(i, last);
    }
    write32(RES_COUNT, n);
  }
  write32(RES_AUX + 4, late);
  probe_done();
}
