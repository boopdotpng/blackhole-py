/* TRISC1 consumer for the unpacker probes (unpack.py, k_unpack.c). One image per MATH (compile-time).
 *
 * MATH_CONSUME  `events` bank hand-offs, each consumed by `kind`:
 *                 release  STALLWAIT(MATH, SRC*_VLD) + SETRWC clear_ab_vld   (fastest possible consumer)
 *                 mova2d   llama qkv/gate/argmax/attention copy: rows/8 x MOVA2D (8 rows, ADDR_MOD 2) + SETRWC release a
 *                 movb2d   verification only: rows/4 x MOVB2D (4 rows) + SETRWC release b
 *                 elwmul   llama dot products: 2 x ELWMUL, the second clears both banks
 *                 mvmul    attention: `mv` x MVMUL, the last clears both banks
 *               every instruction is pushed up front: the Tensix waits on dvalid, the RISC only on a full FIFO.
 *               publish (verification): STALLWAIT(SYNC, MATH|SFPU) + SEMPOST(MATH_PACK) after the last event.
 * MATH_LAT      per rep: push STALLWAIT(MATH, SRC*_VLD) + SETRWC release, raise FL_ARMED = r + 1, drain, log now().
 * MATH_FULL     per rep: wait (soft) for FL_FILLED = r + 1, idle `delay`, log now(), release three banks (the first
 *               unblocks T0's third UNPACR), drain, raise FL_REL = r + 1.
 * Releases are issued whether or not a flag wait timed out, so T0's Tensix thread is never left blocked. */
#define MATH_CONSUME 1
#define MATH_LAT 2
#define MATH_FULL 3
#include "unpack.h"

enum { P_KIND, P_MASK, P_EVENTS, P_ROWS, P_MV, P_FP32, P_PUBLISH, P_RESET_DST, P_REPS, P_DELAY };
enum { K_RELEASE, K_MOVA2D, K_MOVB2D, K_ELWMUL, K_MVMUL };
enum { SITE_FILLED = 1 };

__attribute__((unused)) INLINE u32 vld(u32 mask) { return (mask & 1 ? C_SRCA_VLD : 0) | (mask & 2 ? C_SRCB_VLD : 0); }

#if MATH == MATH_CONSUME
KERNEL kernel_main(void) {
  u32 kind = PARAM(P_KIND), mask = PARAM(P_MASK), events = PARAM(P_EVENTS), rows = PARAM(P_ROWS);
  u32 mv = PARAM(P_MV), rst = PARAM(P_RESET_DST) ? 0xF : 0x3;
  if (kind == K_MOVA2D || kind == K_MOVB2D) {
    u32 b = kind == K_MOVB2D;
    tensix_push(SETC16(1, 0));                     /* Dst offset 0 */
    tensix_push(STALLWAIT(B_CFG, C_MATH | C_SFPU));
    tensix_push(RMWCIB(3, 0x20, PARAM(P_FP32) ? 0x20 : 0, 1));  /* ALU_ACC_CTRL_Fp32_enabled */
    tensix_push(SETC16(12 + 2, b ? 4 << 8 : 8));   /* ADDR_MOD 2: SrcA += 8 (SrcB += 4) */
    tensix_push(SETC16(28 + 2, b ? 4 : 8));        /* Dst += 8 (4) */
    tensix_push(SETC16(47 + 2, 0));
  }
  tensix_push(SETRWC(0, 0, 0, 0, 0, 0xF));
  u32 wait = STALLWAIT(B_MATH, vld(mask));
  u32 a2d = MOVA2D(0, 0, 2, 2, 0), b2d = MOVB2D(0, 0, 2, 4, 0);
  u32 end_a = SETRWC(1, 0, 0, 0, 0, rst), end_b = rst == 0xF ? SETRWC(2, 0, 0, 0, 0, 0xF) : SETRWC(2, 2, 0, 0, 0, 2);
  u32 t0 = now();
  for (u32 e = 0; e < events; e++) {
    switch (kind) {
    case K_RELEASE: tensix_push(wait); tensix_push(SETRWC(mask, 0, 0, 0, 0, 0)); break;
    case K_MOVA2D: tensix_push(wait); for (u32 q = 0; q < rows / 8; q++) tensix_push(a2d); tensix_push(end_a); break;
    case K_MOVB2D: tensix_push(wait); for (u32 q = 0; q < rows / 4; q++) tensix_push(b2d); tensix_push(end_b); break;
    case K_ELWMUL: tensix_push(ELWMUL(0, 0, 0, 0, 0)); tensix_push(ELWMUL(3, 0, 0, 0, 0)); break;
    case K_MVMUL: for (u32 q = 1; q < mv; q++) tensix_push(MVMUL(0, 0, 0, 0)); tensix_push(MVMUL(3, 0, 0, 0)); break;
    default: break;
    }
  }
  if (PARAM(P_PUBLISH)) {
    tensix_push(STALLWAIT(B_SYNC, C_MATH | C_SFPU));
    tensix_push(SEMPOST(1u << SEM_MATH_PACK));
  }
  tensix_drain();
  log_word(0, t0);
  log_word(1, now());
  write32(RES_COUNT, 2);
  probe_done();
}
#endif

#if MATH == MATH_LAT
KERNEL kernel_main(void) {
  u32 mask = PARAM(P_MASK), reps = PARAM(P_REPS);
  tensix_push(SETRWC(0, 0, 0, 0, 0, 0xF));
  tensix_drain();
  for (u32 r = 0; r < reps; r++) {
    tensix_push(STALLWAIT(B_MATH, vld(mask)));
    tensix_push(SETRWC(mask, 0, 0, 0, 0, 0));
    fence();
    write32(FL_ARMED, r + 1);
    tensix_drain();
    log_word(r, now());
  }
  write32(RES_COUNT, reps);
  probe_done();
}
#endif

#if MATH == MATH_FULL
KERNEL kernel_main(void) {
  u32 reps = PARAM(P_REPS), delay = PARAM(P_DELAY);
  u32 wait = STALLWAIT(B_MATH, C_SRCA_VLD), rel = SETRWC(1, 0, 0, 0, 0, 0);
  tensix_push(SETRWC(0, 0, 0, 0, 0, 0xF));
  tensix_drain();
  for (u32 r = 0; r < reps; r++) {
    wait_ge(FL_FILLED, r + 1, SITE_FILLED, 1);
    spin(delay);
    u32 t = now();
    tensix_push(wait); tensix_push(rel);
    tensix_push(wait); tensix_push(rel);
    tensix_push(wait); tensix_push(rel);
    tensix_drain();
    log_word(r, t);
    write32(FL_REL, r + 1);
  }
  write32(RES_COUNT, reps);
  probe_done();
}
#endif
