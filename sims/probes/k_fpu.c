/* Generic Tensix timing kernel for the FPU probes (fpu.py). One TRISC role per image.
 *
 *   1. setup program (L1, written by the host): config, Src bank hand-over, Dst fill, MOVD2A/B, MOP/replay load.
 *   2. timed loop: for each of three iteration counts, SAMPLES runs of
 *        t0 = now(); repeat n times { BODY }; tt_fence(); t1 = now()
 *      BODY is a compile-time list of TTINSN words (-DBODY=...), so the timed region is exactly those inline
 *      Tensix words plus the loop's addi/bne. The first sample of each count is the warmup.
 *   3. check program: zero the accumulators, run the body a few times, read Dst back through the RISC window.
 *
 * Program records are four u32 words {op, a, b, c}. Every wait is bounded (WAIT_UNTIL / tt_fence), except pushes
 * into a full Tensix FIFO. Two-thread cases synchronise each sample with a pair of L1 words (P_BARRIER). */
#include "fpu.h"

#ifndef BODY
#define BODY TTINSN(TT_NOP);
#endif

enum { P_PROG, P_NPROG, P_CHECK, P_NCHECK, P_C0, P_C1, P_C2, P_SAMPLES, P_BARRIER, P_ME, P_PEER };
enum { OP_PUSH = 1, OP_CFG, OP_MOPCFG, OP_FENCE, OP_MOPSYNC, OP_DST32, OP_DST16, OP_DSTRAND16, OP_READ32, OP_READ16,
       OP_RUN, OP_STAMP, OP_FLAG, OP_WAITFLAG, OP_DELAY };
enum { SITE_FENCE = 1, SITE_BARRIER = 2, SITE_PROG = 0x100, SITE_CHECK = 0x1000 };
#define CHECK_LOG 256  /* check-program log words start here; timing words before */
#define SETUP_LOG 512  /* setup-program stamps/reads (two-thread latency cases) */

__attribute__((noinline)) static void body_loop(u32 n) {
  #pragma clang loop unroll(disable)
  for (; n; n--) { BODY }
}

static u32 run_prog(u32 at, u32 n, u32 site, u32 log) {
  for (u32 i = 0; i < n; i++, at += 16) {
    u32 op = read32(at), a = read32(at + 4), b = read32(at + 8), c = read32(at + 12);
    switch (op) {
    case OP_PUSH: tensix_push(a); break;
    case OP_CFG: cfg_rmw(a, b, c); break;
    case OP_MOPCFG: write32(MOP_CFG(a), b); break;
    case OP_FENCE: tt_fence(site + i); break;
    case OP_MOPSYNC: mop_sync(); break;
    case OP_DST32:  /* rows a .. a+b-1, all 16 columns, value c (IEEE fp32 bits) */
      for (u32 r = a; r < a + b; r++) for (u32 col = 0; col < 16; col++) dst_write32(r, col, c);
      (void)dst_read32(a + b - 1, 15);
      break;
    case OP_DST16:
      for (u32 r = a; r < a + b; r++) for (u32 col = 0; col < 16; col++) dst_write16(r, col, c);
      (void)dst_read16(a + b - 1, 15);
      break;
    case OP_DSTRAND16: {  /* positive bf16/fp16-ish values from an LCG: c = (seed, or_mask) packed as seed */
      u32 x = c;
      for (u32 r = a; r < a + b; r++) for (u32 col = 0; col < 16; col++) {
        x = x * 1664525u + 1013904223u;
        dst_write16(r, col, (x >> 16 & 0x00FF) | (c >> 16 & 0xFF00));
      }
      (void)dst_read16(a + b - 1, 15);
      break;
    }
    case OP_READ32: log_word(log++, dst_read32(a, b)); break;
    case OP_READ16: log_word(log++, dst_read16(a, b)); break;
    case OP_RUN: body_loop(a); break;
    case OP_STAMP: log_word(log++, now()); break;
    case OP_FLAG: write32(a, b); fence(); break;
    case OP_WAITFLAG: WAIT_L1((int)(read32(a) - b) >= 0, site + i); break;
    case OP_DELAY: spin(a); break;
    default: probe_fail(site + i);
    }
  }
  return log;
}

KERNEL kernel_main(void) {
  u32 bar = PARAM(P_BARRIER), me = PARAM(P_ME), peer = PARAM(P_PEER), samples = PARAM(P_SAMPLES);
  write32(RES_AUX + 4, run_prog(PARAM(P_PROG), PARAM(P_NPROG), SITE_PROG, SETUP_LOG) - SETUP_LOG);
  tt_fence(SITE_FENCE);
  u32 k = 0, seq = 0;
  for (u32 ci = 0; ci < 3; ci++) {
    u32 n = PARAM(P_C0 + ci);
    if (!n) continue;
    for (u32 s = 0; s < samples; s++) {
      if (bar) {
        write32(bar + 4 * me, ++seq);
        fence();
        WAIT_L1((int)(read32(bar + 4 * peer) - seq) >= 0, SITE_BARRIER);
      }
      u32 t0 = now();
      body_loop(n);
      u32 t1 = tt_fence_time(SITE_FENCE);
      log_word(k++, t0);
      log_word(k++, t1);
    }
  }
  write32(RES_AUX, k);
  u32 end = run_prog(PARAM(P_CHECK), PARAM(P_NCHECK), SITE_CHECK, CHECK_LOG);
  write32(RES_COUNT, end - CHECK_LOG);
  tt_fence(SITE_FENCE);
  probe_done();
}
