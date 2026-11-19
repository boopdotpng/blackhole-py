/* TRISC0 unpacker probes (unpack.py). One image per MODE (compile-time), parameters per case.
 *
 * MODE_RAW    back-to-back UNPACR (or UNPACR_NOP) on A, B or both (A,B interleaved), issued by one MOP or pushed one
 *             by one; optional SetDatValid (then T1 must consume, k_unpack_math.c). Per sample: zero ADC Z/W,
 *             t0, issue c ops, drain, t1. Log t1 - t0 per sample, for each count c, reps samples each (rep 0 warmup).
 * MODE_EXTRA  pushed one by one: [config op(s)] + UNPACR, single unpacker. Per-op overhead of what llama emits
 *             between unpacks (SETADC*, RMWCIB, WRCFG, STALLWAITs, RISC base write, UNPACK_SYNC credit round trip).
 * MODE_MOVE   ttrv `unpack.move` lowering (ttrv/movement.py) per block, in the patterns the llama kernels use;
 *             c blocks (tiles) per sample. Also the verification launch (one tile, T1 copies, T2 packs).
 * MODE_LAT    dvalid -> math: T1 arms STALLWAIT(SRC*_VLD)+SETRWC and raises FL_ARMED; T0 waits for it, idles,
 *             logs t0, issues one UNPACR with SetDatValid, drains, logs t1. T1 logs when its drain returns.
 * MODE_FULL   both Src banks full: T0 fills both A banks, raises FL_FILLED, logs t0, issues a third UNPACR (blocks
 *             until T1 releases a bank), drains, logs t1. T1 waits, idles `delay`, logs t_release, releases.
 *
 * Deadlock rule: every UNPACR with SetDatValid here is matched by exactly one release that T1 issues
 * unconditionally (its flag waits are soft), so neither Tensix thread can be left blocked when both kernels run. */
#define MODE_RAW 1
#define MODE_EXTRA 2
#define MODE_MOVE 3
#define MODE_LAT 4
#define MODE_FULL 5
#include "unpack.h"

enum { P_CFG, P_FMT, P_N, P_BASE_A, P_BASE_B, P_COUNTS, P_REPS, P_ZDIM, P_STRIDE_A, P_STRIDE_B, P_DELAY, P_THB };
#define C_SEL(c)      ((c) & 3)
#define C_DVALID(c)   ((c) >> 2 & 1)
#define C_TRANSP(c)   ((c) >> 3 & 1)
#define C_DIRECT(c)   ((c) >> 4 & 1)
#define C_THROT(c)    ((c) >> 5 & 1)
#define C_THMODE(c)   ((c) >> 6 & 3)
#define C_WSTART(c)   ((c) >> 8 & 1)
#define C_WPACK(c)    ((c) >> 9 & 1)
#define C_PAT(c)      ((c) >> 12 & 15)
#define C_EXTRA(c)    ((c) >> 16 & 15)
#define C_STEP(c)     ((c) >> 20 & 1)
enum { SITE_START = 1, SITE_PSTART, SITE_CREDIT, SITE_ARMED, SITE_REL };
enum { PAT_PAIR_FACE = 1, PAT_A_FACE, PAT_B_FACE, PAT_A_TILE, PAT_B_TILE, PAT_BA_TILE };
enum { X_NONE, X_ADCZW, X_ADCXX_ZW, X_RMWCIB4, X_STALL_CFG, X_STALL_DONE, X_RISC_BASE, X_CREDIT, X_WRCFG, X_SETC16,
       X_NOP_WAKE };

INLINE u32 in_fmt(u32 f, u32 i) { return f >> (8 * i) & 15; }
INLINE u32 out_fmt(u32 f, u32 i) { return f >> (8 * i + 4) & 15; }

/* setup common to every mode: fmt, geometry, base, x range, optional throttle override; then drain */
static void setup(u32 cfg, u32 fmt, u32 x, u32 z) {
  for (u32 i = 0; i < 2; i++) {
    if (!(C_SEL(cfg) >> i & 1)) continue;
    u32 in = in_fmt(fmt, i);
    unpack_fmt(i, in, out_fmt(fmt, i), i ? 0 : C_TRANSP(cfg), in == F_LF8);
    unpack_geom(i, x, z);
    unpack_base(i, i ? PARAM(P_BASE_B) : PARAM(P_BASE_A));
    if (C_THROT(cfg)) unpack_throttle(i, i ? PARAM(P_THB) : C_THMODE(cfg));  /* B's mode in P_THB */
    tensix_push(SETADCXX(1u << i, x - 1, 0));
  }
  tensix_push(SETC16(5, 4));  /* SRCA_SET_SetOvrdWithAddr = 1, as ttrv's unpack.fmt a */
  tensix_push(SETADCZW(3, 0, 0, 0, 0, 15));
  tensix_drain();
}

__attribute__((unused)) INLINE void wait_generators(u32 cfg) {
  if (C_WSTART(cfg)) wait_ge(FL_START, 1, SITE_START, 0);
  if (C_WPACK(cfg)) wait_ge(FL_PSTART, 1, SITE_PSTART, 0);
}
__attribute__((unused)) INLINE NORETURN finish(u32 n) {
  write32(FL_DONE, 1);
  fence();  /* L0 data cache: FL_END / FL_PEND are written by other RISCs */
  write32(RES_AUX + 0, read32(FL_END));   /* nonzero: a generator stopped before the measurement ended */
  write32(RES_AUX + 4, read32(FL_PEND));
  write32(RES_COUNT, n);
  probe_done();
}

#if MODE == MODE_RAW || MODE == MODE_EXTRA
KERNEL kernel_main(void) {
  u32 cfg = PARAM(P_CFG), fmt = PARAM(P_FMT), n = PARAM(P_N), counts = PARAM(P_COUNTS), reps = PARAM(P_REPS);
  u32 sel = C_SEL(cfg), dv = C_DVALID(cfg), am = C_STEP(cfg) ? 1 : 0;
  u32 x = FMT_BFP(in_fmt(fmt, sel == 2 ? 1 : 0)) && n > 256 ? 256 : n;
  setup(cfg, fmt, x, PARAM(P_ZDIM));
  u32 op = C_PAT(cfg);  /* raw: 0 UNPACR, 1 UNPACR_NOP (mode 2) */
  u32 ua = op ? UNPACR_NOP_NOP(0) : UNPACR(0, am, dv), ub = op ? UNPACR_NOP_NOP(1) : UNPACR(1, am, dv);
  u32 first = sel == 2 ? ub : ua;
#if MODE == MODE_EXTRA
  u32 i = sel == 2 ? 1 : 0, extra = C_EXTRA(cfg), sec = 64 + 48 * i, bw = base_word(i), basev = read32(CFG(bw));
  u32 rmw[8], nrmw = field_words(rmw, sec + 1, 16, 16, PARAM(P_ZDIM));
  nrmw += field_words(rmw + nrmw, sec, 16, 16, x);
  write32(REGFILE + 4 * 4, basev);  /* GPR 4 = base, for WRCFG */
  u32 xx = SETADCXX(1u << i, x - 1, 0), zw = SETADCZW(1u << i, 0, 0, 0, 0, 15);
  u32 sclr = STALLWAIT(B_UNPACK, C_TRISC_CFG | (i ? C_SRCB_CLR : C_SRCA_CLR)), sdone = STALLWAIT(B_SYNC, i ? C_UNPACK1 : C_UNPACK0);
  u32 wr = WRCFG(4, 0, bw), wake = UNPACR_NOP_NOP(i);
#endif
  wait_generators(cfg);
  u32 nlog = 0;
  for (u32 k = 0; k < 3; k++) {
    u32 c = counts >> (8 * k) & 255;
    if (!c) break;
#if MODE == MODE_RAW
    if (!C_DIRECT(cfg)) {
      if (sel == 3) mop_cfg(c, 1, ua, TT_NOP, TT_NOP, ub, TT_NOP, ub, ub);
      else mop_cfg(1, c, TT_NOP, TT_NOP, TT_NOP, first, TT_NOP, first, first);
    }
#endif
    for (u32 r = 0; r < reps; r++) {
      tensix_push(SETADCZW(3, 0, 0, 0, 0, 15));
      tensix_drain();
      u32 t0 = now();
#if MODE == MODE_RAW
      if (!C_DIRECT(cfg)) tensix_push(MOP1);
      else if (sel == 3) for (u32 j = 0; j < c; j++) { tensix_push(ua); tensix_push(ub); }
      else for (u32 j = 0; j < c; j++) tensix_push(first);
#else
      for (u32 j = 0; j < c; j++) {
        switch (extra) {
        case X_ADCZW: tensix_push(zw); break;
        case X_ADCXX_ZW: tensix_push(xx); tensix_push(zw); break;
        case X_RMWCIB4: for (u32 q = 0; q < nrmw; q++) tensix_push(rmw[q]); break;
        case X_STALL_CFG: tensix_push(sclr); break;
        case X_RISC_BASE: { write32(CFG(bw), basev); u32 v = read32(CFG(bw)); __asm__ volatile("andi %0, %0, 0" : "+r"(v)); } break;
        case X_CREDIT: sem_wait_zero(SEM_UNPACK_SYNC, SITE_CREDIT); write32(SEM(SEM_UNPACK_SYNC), 0); break;
        case X_WRCFG: tensix_push(wr); break;
        case X_SETC16: tensix_push(SETC16(41, 0)); break;
        case X_NOP_WAKE: tensix_push(wake); break;
        default: break;
        }
        tensix_push(first);
        if (extra == X_STALL_DONE) tensix_push(sdone);
        if (extra == X_CREDIT) { tensix_push(sdone); tensix_push(SEMGET(1u << SEM_UNPACK_SYNC)); }
      }
#endif
      tensix_drain();
      u32 t1 = now();
      log_word(nlog++, t1 - t0);
    }
  }
  finish(nlog);
}
#endif

#if MODE == MODE_MOVE
/* One ttrv `unpack.move` (movement.py), with the RMWCIB words precomputed: credit wait, block geometry fields,
 * base write + readback, credit post, SETADCXX, SETADCZW, STALLWAIT(UNPACK, TRISC_CFG|SRC*_CLR), the UNPACR(s)
 * (BFP: one per face, AddrMode 0x11, dvalid on the last), STALLWAIT(SYNC, UNPACK*), SEMGET(UNPACK_SYNC). */
typedef struct { u32 w[8], nw, bw, pre[3], faces, am, post[2]; } Move;

static void move_init(Move *m, u32 i, u32 bfp, u32 x, u32 faces, u32 dv) {
  u32 sec = 64 + 48 * i;
  m->nw = field_words(m->w, sec + 1, 16, 16, faces);
  m->nw += field_words(m->w + m->nw, sec, 16, 16, x);
  if (!i) {
    m->nw += field_words(m->w + m->nw, sec + 20, 0, 16, 64);
    m->nw += field_words(m->w + m->nw, sec + 22, 0, 16, x);
  }
  m->bw = base_word(i);
  m->pre[0] = SETADCXX(1u << i, x - 1, 0);
  m->pre[1] = SETADCZW(1u << i, 0, 0, 0, 0, 15);
  m->pre[2] = STALLWAIT(B_UNPACK, C_TRISC_CFG | (i ? C_SRCB_CLR : C_SRCA_CLR));
  m->faces = faces;
  m->am = UNPACR(i, bfp ? 0x11 : 0, 0);
  m->post[0] = UNPACR(i, bfp ? 0x11 : 0, dv);  /* the last UNPACR of the block carries SetDatValid */
  m->post[1] = STALLWAIT(B_SYNC, i ? C_UNPACK1 : C_UNPACK0);
}

INLINE void move(const Move *m, u32 addr) {
  sem_wait_zero(SEM_UNPACK_SYNC, SITE_CREDIT);
  for (u32 q = 0; q < m->nw; q++) tensix_push(m->w[q]);
  write32(CFG(m->bw), (addr >> 4) - 1);
  u32 v = read32(CFG(m->bw));
  __asm__ volatile("andi %0, %0, 0" : "+r"(v));
  write32(SEM(SEM_UNPACK_SYNC), 0);
  tensix_push(m->pre[0]); tensix_push(m->pre[1]); tensix_push(m->pre[2]);
  for (u32 j = 1; j < m->faces; j++) tensix_push(m->am);
  tensix_push(m->post[0]); tensix_push(m->post[1]);
  tensix_push(SEMGET(1u << SEM_UNPACK_SYNC));
}

KERNEL kernel_main(void) {
  u32 cfg = PARAM(P_CFG), fmt = PARAM(P_FMT), n = PARAM(P_N), counts = PARAM(P_COUNTS), reps = PARAM(P_REPS);
  u32 pat = C_PAT(cfg), dv = C_DVALID(cfg), ba = PARAM(P_BASE_A), bb = PARAM(P_BASE_B);
  u32 sa = PARAM(P_STRIDE_A), sb = PARAM(P_STRIDE_B);
  u32 bfa = FMT_BFP(in_fmt(fmt, 0)), bfb = FMT_BFP(in_fmt(fmt, 1));
  u32 xa = bfa && n > 256 ? 256 : n, xb = bfb && n > 256 ? 256 : n;
  setup(cfg, fmt, xa, 1);
  if (C_SEL(cfg) & 2) unpack_geom(1, xb, 1);
  Move ma, mb;
  move_init(&ma, 0, bfa, xa, n / xa, dv);
  move_init(&mb, 1, bfb, xb, n / xb, dv);
  /* face patterns: block f of tile t at base + t * stride + f * face_bytes (stride = tile bytes / 4 per face) */
  u32 fa = sa / 4, fb = sb / 4;
  wait_generators(cfg);
  u32 nlog = 0;
  for (u32 k = 0; k < 3; k++) {
    u32 c = counts >> (8 * k) & 255;
    if (!c) break;
    for (u32 r = 0; r < reps; r++) {
      tensix_drain();
      u32 t0 = now();
      for (u32 t = 0; t < c; t++) {
        u32 a = ba + t * sa, b = bb + t * sb;
        switch (pat) {
        case PAT_PAIR_FACE: for (u32 f = 0; f < 4; f++) { move(&ma, a + f * fa); move(&mb, b + f * fb); } break;
        case PAT_A_FACE: for (u32 f = 0; f < 4; f++) move(&ma, a + f * fa); break;
        case PAT_B_FACE: for (u32 f = 0; f < 4; f++) move(&mb, b + f * fb); break;
        case PAT_A_TILE: move(&ma, a); break;
        case PAT_B_TILE: move(&mb, b); break;
        case PAT_BA_TILE: move(&mb, b); move(&ma, a); break;
        default: break;
        }
      }
      tensix_drain();
      u32 t1 = now();
      log_word(nlog++, t1 - t0);
    }
  }
  finish(nlog);
}
#endif

#if MODE == MODE_LAT || MODE == MODE_FULL
KERNEL kernel_main(void) {
  u32 cfg = PARAM(P_CFG), fmt = PARAM(P_FMT), n = PARAM(P_N), reps = PARAM(P_REPS), delay = PARAM(P_DELAY);
  (void)delay;  /* MODE_FULL: the delay is on T1 */
  u32 i = C_SEL(cfg) == 2 ? 1 : 0;
  setup(cfg, fmt, n, 1);
  u32 u = UNPACR(i, 0, 1);
  for (u32 r = 0; r < reps; r++) {
#if MODE == MODE_LAT
    wait_ge(FL_ARMED, r + 1, SITE_ARMED, 1);  /* soft: T1 consumes this bank whether or not we saw the flag */
    spin(delay);
    u32 t0 = now();
    tensix_push(u);
    tensix_drain();
    u32 t1 = now();
#else
    tensix_push(u); tensix_push(u);
    tensix_drain();
    write32(FL_FILLED, r + 1);
    u32 t0 = now();
    tensix_push(u);       /* waits in the unpacker until T1 releases a bank */
    tensix_drain();
    u32 t1 = now();
    wait_ge(FL_REL, r + 1, SITE_REL, 1);
#endif
    log_word(2 * r, t0);
    log_word(2 * r + 1, t1);
  }
  write32(RES_COUNT, 2 * reps);
  probe_done();
}
#endif
