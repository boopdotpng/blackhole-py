/* TRISC2 side of the pack probes (pack.py). Waits for TRISC1's Dst fill (SEM_FILL, polled from the RISC), configures
 * the packer the way the llama kernels do, then times "units" (one pack of `rows` Dst rows: a tile, a face, ...).
 *
 * Unit body: 0 inline PACRs (ttrv pack.move: rows / k PACRs of k rows, the last AddrMode 1 + Last), 1 llama's MOP
 * (faces x 4 PACRs of 4 rows), 2 tiny (one PACR of `tinyx + 1` datums of one row; tiny_last=0: Last on every PACR,
 * 1: only on the last of a sample). Flags add the per-tile instructions the kernels emit around the body (pack.py F).
 *
 * mode 0 throughput: per sample, per count c: t0, issue c units, t1, STALLWAIT(packer) + drain, t2. log t1-t0, t2-t0.
 * mode 1 visibility: one unit per sample; log t0 (before issue), t1 (issued), t2 (packer idle + drained), t3 (the
 *        RISC sees the last 16 B of the output change). vis bit 0: drain before polling; bit 1: BRISC NoC reader.
 * mode 2/3 handoff: n units, each behind SEMWAIT(MATH_PACK) (flag F_SEMWAIT) or a RISC poll (F_SEMPOLL) and ending
 *        in STALLWAIT + drain; log now() after each. TRISC1 posts (k_pack_math.c).
 * aux[0] first timed now(), aux[1] last, aux[2] traffic start seen (PK_TRAFFIC_UP), aux[3] unpack start seen. */
#include "pack.h"

enum { P_FMT, P_BODY, P_ROWS, P_K, P_FLAGS, P_COUNTS, P_SAMPLES, P_DSTT, P_OUT, P_STRIDE, P_MODE, P_N, P_VIS, P_SEMMAX,
       P_WAITUP, P_TINYX };
enum { BODY_INLINE, BODY_MOP, BODY_TINY };
enum { F_SETW = 1, F_ADDR_WRCFG = 2, F_ADDR_ADC = 4, F_PRE = 8, F_POST = 16, F_CB = 32, F_ZEROACC = 64, F_SELFSEM = 128,
       F_L1ACC = 256, F_EDGE = 512, F_RECFG = 1024, F_PRE_TTRV = 2048, F_SEMWAIT = 4096, F_SEMPOLL = 8192 };
enum { SITE_FILL = 1, SITE_TRAFFIC, SITE_UNPACK, SITE_VIS_SEEN, SITE_VIS_DONE, SITE_SEM };
#define SENT 0xFFFFFFFFu  /* no in-scope output pattern contains it (PACK.md) */

typedef struct { u32 fmt, body, rows, k, flags, dstt, out, stride, tinyx, mid, last; } ctx_t;

static void configure(const ctx_t *c) {
  const packfmt *f = &FORMATS[c->fmt];
  u32 faces = c->rows >= 16 ? c->rows / 16 : 1, sz = f->insize, acc = !!(c->flags & F_L1ACC);
  cfg_write(CW_EXP_SIZE, (f->bfp ? faces : f->e4m3 ? 0 : 4) << 16);
  cfg_write(CW_L1_DEST, ((c->out >> 4) - 1) | 0x80000000u);
  cfg_write(CW_PACK_FMT, 1 | acc << 2 | (u32)f->out << 4 | (u32)f->in << 8);
  cfg_write(CW_PACK_MISC, (u32)f->e4m3 << 23 | acc << 19);
  cfg_write(CW_PCK_DEST_RD, f->read32 | (u32)f->round10 << 3);
  cfg_write(CW_PCK0_XY0, (16 * sz) << 16);
  cfg_write(CW_PCK0_ZW0, 256 * sz | (1024 * sz) << 16);
  cfg_write(CW_PCK0_XY1, 0);
  cfg_write(CW_PCK0_ZW1, c->flags & F_ADDR_ADC ? c->stride << 16 : 0);
  cfg_write(CW_PACK_COUNTERS, 0x1000);
  if (c->flags & F_EDGE) {  /* llama qkv / gate / lm / o's second pack config, verbatim */
    cfg_write(CW_EDGE0, 0x20000); cfg_write(CW_EDGE1, 1); cfg_write(CW_ROWSET0, 0); cfg_write(CW_ROWSET1, 1);
  } else {
    cfg_write(CW_EDGE0, 0xFFFF); cfg_write(CW_EDGE1, 0); cfg_write(CW_ROWSET0, 0); cfg_write(CW_ROWSET1, 0);
  }
  cfg_write(CW_PACK_DST_OFS, 0);
  cfg_commit(CW_PACK_DST_OFS);
  TTINSN(SETC16(THD_ADDR_MOD_PACK + 0, 0x104));   /* Y += 4 (Dst and L1 side) */
  TTINSN(SETC16(THD_ADDR_MOD_PACK + 1, 0x2820));  /* tile end: Y, Z cleared */
  TTINSN(SETC16(THD_ADDR_MOD_PACK + 2, 0x1120));  /* face end: Y cleared, Z += 1 */
  tensix_push(SETC16(THD_ADDR_MOD_PACK + 3, c->body == BODY_TINY ? 0 : (c->k | c->k << 6)));  /* inline: Y += k */
  TTINSN(TT_SETADCXY(4, 0, 0, 0, 0, 0xB));
  TTINSN(TT_SETADCZW(4, 0, 0, 0, 0, 0xF));
  tensix_push(TT_SETADCXX(4, c->body == BODY_TINY ? c->tinyx : 15, 0));
  if (c->body == BODY_MOP) mop_pack_faces(faces);
  tensix_drain();
}

/* One unit with the per-tile instructions selected by flags, in the order the exported llama kernels emit them. */
static __attribute__((noinline)) void unit(const ctx_t *c, u32 u) {
  u32 fl = c->flags;
  if (fl & F_RECFG) configure(c);
  if (fl & F_SELFSEM) TTINSN(TT_SEMPOST(1 << SEM_MATH_PACK));
  if (fl & F_SEMPOLL) WAIT_UNTIL(sem_value(SEM_MATH_PACK) != 0, SITE_SEM);
  if (fl & (F_SELFSEM | F_SEMWAIT)) TTINSN(TT_SEMWAIT(STALL_TDMA, 1 << SEM_MATH_PACK, SEM_ON_ZERO));
  if (fl & F_SETW) tensix_push(TT_SETADC(4, 0, 3, u % c->dstt));
  if (fl & F_ADDR_WRCFG) {
    u32 a = ((c->out + u * c->stride) >> 4) - 1;
    tensix_push(TT_SETDMAREG16(24, a));
    tensix_push(TT_SETDMAREG16(25, 0x8000 | a >> 16));
    TTINSN(TT_STALLWAIT(STALL_CFG, WAIT_THCON | WAIT_PACK0));
    TTINSN(TT_WRCFG(12, 0, CW_L1_DEST));
    tensix_push(TT_SETDMAREG16(25, a >> 16));
    TTINSN(TT_DMANOP);
  }
  if (fl & F_ADDR_ADC) tensix_push(TT_SETADC(4, 1, 3, u));
  if (fl & F_PRE) {
    TTINSN(TT_SETADCXX(4, 15, 0));
    TTINSN(TT_SETADCZW(4, 0, 0, 0, 0, 5));
    cfg_write(CW_PACK_DST_OFS, 0);
    TTINSN(TT_STALLWAIT(STALL_CFG, WAIT_PACK0));
  }
  if (fl & F_PRE_TTRV) {
    TTINSN(TT_SETADCXX(4, 15, 0));
    TTINSN(TT_SETADCXY(4, 0, 0, 0, 0, 11));
    TTINSN(TT_SETADCZW(4, 0, 0, 0, 0, 5));
    TTINSN(TT_STALLWAIT(STALL_CFG, WAIT_PACK0));
  }
  if (c->body == BODY_MOP) TTINSN(TT_MOP(1, 0, 0));
  else {
    u32 n = c->rows / c->k, mid = c->mid;
    for (u32 i = 1; i < n; i++) tensix_push(mid);
    tensix_push(c->last);
  }
  if (fl & F_POST) pack_wait();
  if (fl & F_CB) {
    u32 v = *(volatile unsigned short *)STREAM_REG(9, 8);
    fence();
    write32(STREAM_REG(9, 10), v + u + 1);
  }
  if (fl & F_ZEROACC) TTINSN(TT_ZEROACC(3, 1, 0, 1, 0));
  if (fl & (F_SELFSEM | F_SEMWAIT | F_SEMPOLL)) TTINSN(TT_SEMGET(1 << SEM_MATH_PACK));
  if (fl & F_SEMPOLL) tensix_drain();  /* the next RISC poll must not see this unit's post again */
}

/* units with only ADC moves around the body, without unit()'s call and flag tests (the Tensix, not the RISC, must
 * be the bottleneck: a bf16 tile packs in ~18 cycles) */
static void fast_units(const ctx_t *c, u32 n) {
  u32 setw = c->flags & F_SETW, adc = c->flags & F_ADDR_ADC, w = 0, dstt = c->dstt;
  for (u32 u = 0; u < n; u++) {
    if (setw) { tensix_push(TT_SETADC(4, 0, 3, w)); if (++w == dstt) w = 0; }
    if (adc) tensix_push(TT_SETADC(4, 1, 3, u));
    if (c->body == BODY_MOP) TTINSN(TT_MOP(1, 0, 0));
    else {
      u32 m = c->rows / c->k, mid = c->mid;
      for (u32 i = 1; i < m; i++) tensix_push(mid);
      tensix_push(c->last);
    }
  }
}

/* tiny PACRs pushed straight from a tight loop (no call per PACR) */
static void tiny(const ctx_t *c, u32 n) {
  u32 w = c->mid, i = 1;
  for (; i + 4 <= n; i += 4) { tensix_push(w); tensix_push(w); tensix_push(w); tensix_push(w); }
  for (; i < n; i++) tensix_push(w);
  tensix_push(c->last);
}

KERNEL kernel_main(void) {
  ctx_t c = {PARAM(P_FMT), PARAM(P_BODY), PARAM(P_ROWS), PARAM(P_K), PARAM(P_FLAGS), PARAM(P_DSTT), PARAM(P_OUT),
             PARAM(P_STRIDE), PARAM(P_TINYX), 0, 0};
  if (!c.k) c.k = 4;
  if (!c.dstt) c.dstt = 1;
  u32 mode = PARAM(P_MODE), samples = PARAM(P_SAMPLES), counts = PARAM(P_COUNTS), waitup = PARAM(P_WAITUP);
  u32 intf = c.k == 4 ? 0 : (1u << c.k) - 1;
  if (c.body == BODY_TINY) {  /* k = 0: Last on every PACR; 1: only on the last of the sample */
    c.last = TT_PACR(3, 1, 1);
    c.mid = PARAM(P_K) ? TT_PACR(3, 1, 0) : c.last;
  } else {
    c.mid = TT_PACR(c.k == 4 ? 0 : 3, intf, 0);
    c.last = TT_PACR(1, intf, 1);
  }

  WAIT_UNTIL(sem_value(SEM_FILL) != 0, SITE_FILL);
  configure(&c);
  if (PARAM(P_SEMMAX) > 1) { tensix_push(TT_SEMINIT(PARAM(P_SEMMAX), 0, 1 << SEM_MATH_PACK)); tensix_drain(); }
  if (waitup & 1) { WAIT_L1(read32(PK_TRAFFIC_UP) != 0, SITE_TRAFFIC); write32(RES_AUX + 8, read32(PK_TRAFFIC_UP)); }
  if (waitup & 2) { WAIT_L1(read32(PK_UNPACK_UP) != 0, SITE_UNPACK); write32(RES_AUX + 12, read32(PK_UNPACK_UP)); }
  write32(PK_READY, 1);
  write32(RES_AUX, now());

  u32 nlog = 0, fast = !(c.flags & ~(u32)(F_SETW | F_ADDR_ADC | F_L1ACC | F_EDGE));
  if (mode == 0) {
    for (u32 s = 0; s < samples; s++)
      for (u32 ki = 0; ki < 4; ki++) {
        u32 n = counts >> (8 * ki) & 0xFF;
        if (!n) continue;
        u32 t0 = now();
        if (c.body == BODY_TINY) tiny(&c, n);
        else if (fast) fast_units(&c, n);
        else for (u32 u = 0; u < n; u++) unit(&c, u);
        u32 t1 = now();
        pack_wait();
        u32 t2 = now();
        log_word(nlog++, t1 - t0);
        log_word(nlog++, t2 - t0);
      }
  } else if (mode == 1) {
    u32 vis = PARAM(P_VIS), lastw = c.out + PARAM(P_STRIDE) - 16;
    for (u32 s = 0; s < samples; s++) {
      write32(lastw, SENT);
      fence();
      WAIT_L1(read32(lastw) == SENT, SITE_VIS_SEEN);
      if (vis & 2) {
        write32(PK_VIS_GO, s + 1);
        u32 until = now() + 400;  /* let the BRISC reader get going */
        while ((int)(now() - until) < 0) {}
      }
      u32 t0 = now(), t1, t2, t3;
      unit(&c, 0);
      t1 = now();
      if (vis & 1) {
        pack_wait();
        t2 = now();
        WAIT_L1(read32(lastw) != SENT, SITE_VIS_SEEN);
        t3 = now();
      } else {
        WAIT_L1(read32(lastw) != SENT, SITE_VIS_SEEN);
        t3 = now();
        pack_wait();
        t2 = now();
      }
      log_word(nlog++, t0); log_word(nlog++, t1); log_word(nlog++, t2); log_word(nlog++, t3);
      if (vis & 2) WAIT_L1(read32(PK_VIS_DONE) == s + 1, SITE_VIS_DONE);
    }
  } else {
    u32 n = PARAM(P_N);
    for (u32 i = 0; i < n; i++) {
      unit(&c, i);
      if (!(c.flags & F_POST)) pack_wait();
      log_word(nlog++, now());
    }
  }
  write32(RES_AUX + 4, now());
  write32(PK_STOP, 1);
  write32(RES_COUNT, nlog);
  probe_done();
}
