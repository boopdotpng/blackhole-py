/* Unpacker probe helpers (unpack.py, k_unpack*.c): Tensix instruction encodings, config access, MOP setup, bounded
 * flag polling, and the ttrv lowering of `unpack.fmt` / `unpack.move` (ttrv/movement.py) in C.
 *
 * Encodings are the tt-llk / ttrv/isa.py field layouts, unrotated (push with tensix_push, or TTINSN for constants).
 * unpack.py check_encodings() compiles this header for the host and compares every macro with ttrv.isa. */
#ifndef UNPACK_H
#define UNPACK_H
#include "probe.h"

/* ---- Tensix encodings (unrotated words) ---- */
#define TT_OP(op, rest) ((((u32)(op)) << 24) | (u32)(rest))
#define T_UNPACR(blk, am, inc, ctx, adc, ovrd, dv, bc, zw2, auto_, rs, fl, last)                                      \
  TT_OP(0x42, (u32)(blk) << 23 | (u32)(am) << 15 | (u32)(inc) << 13 | (u32)(ctx) << 10 | (u32)(adc) << 8 |             \
                  (u32)(ovrd) << 7 | (u32)(dv) << 6 | (u32)(bc) << 5 | (u32)(zw2) << 4 | (u32)(auto_) << 3 |            \
                  (u32)(rs) << 2 | (u32)(fl) << 1 | (u32)(last))
/* the form every ttrv / llama unpack uses: multi-context (OvrdThreadId) ctx 0, Last */
#define UNPACR(blk, am, dv) T_UNPACR(blk, am, 0, 0, 0, 1, dv, 0, 0, 0, 0, 0, 1)
#define T_UNPACR_NOP(sel, stream, msg, setdv, clrfmt, stallclr, bankclr, clrval, pop)                                  \
  TT_OP(0x43, (u32)(sel) << 23 | (u32)(stream) << 16 | (u32)(msg) << 12 | (u32)(setdv) << 8 | (u32)(clrfmt) << 6 |     \
                  (u32)(stallclr) << 5 | (u32)(bankclr) << 4 | (u32)(clrval) << 2 | (u32)(pop))
#define UNPACR_NOP_NOP(sel) T_UNPACR_NOP(sel, 0, 0, 0, 0, 0, 0, 0, 2)       /* occupy the unpacker one cycle */
#define UNPACR_NOP_DVALID(sel) T_UNPACR_NOP(sel, 0, 0, 1, 0, 0, 0, 0, 1)    /* LLK/llama: give the bank to math */
#define SETADCXX(mask, xend, xstart) TT_OP(0x5e, (u32)(mask) << 21 | (u32)(xend) << 10 | (u32)(xstart))
#define SETADCXY(mask, c1y, c1x, c0y, c0x, bm)                                                                        \
  TT_OP(0x51, (u32)(mask) << 21 | (u32)(c1y) << 15 | (u32)(c1x) << 12 | (u32)(c0y) << 9 | (u32)(c0x) << 6 | (u32)(bm))
#define SETADCZW(mask, c1w, c1z, c0w, c0z, bm)                                                                        \
  TT_OP(0x54, (u32)(mask) << 21 | (u32)(c1w) << 15 | (u32)(c1z) << 12 | (u32)(c0w) << 9 | (u32)(c0z) << 6 | (u32)(bm))
#define SETADC(mask, ch, dim, v) TT_OP(0x50, (u32)(mask) << 21 | (u32)(ch) << 20 | (u32)(dim) << 18 | (u32)(v))
#define STALLWAIT(stall, wait) TT_OP(0xa2, (u32)(stall) << 15 | (u32)(wait))
#define SEMINIT(max, init, sel) TT_OP(0xa3, (u32)(max) << 20 | (u32)(init) << 16 | (u32)(sel) << 2)
#define SEMPOST(sel) TT_OP(0xa4, (u32)(sel) << 2)
#define SEMGET(sel) TT_OP(0xa5, (u32)(sel) << 2)
#define RMWCIB(byte, mask, data, word) TT_OP(0xb3 + (byte), (u32)(mask) << 16 | (u32)(data) << 8 | (u32)(word))
#define WRCFG(gpr, wide, word) TT_OP(0xb0, (u32)(gpr) << 16 | (u32)(wide) << 15 | (u32)(word))
#define MOP1 TT_OP(0x01, 1u << 23)                                          /* template 1, counts from MopCfg */
#define SETRWC(clr, cr, d, b, a, bm)                                                                                  \
  TT_OP(0x37, (u32)(clr) << 22 | (u32)(cr) << 18 | (u32)(d) << 14 | (u32)(b) << 10 | (u32)(a) << 6 | (u32)(bm))
#define MOVA2D(lo, src, am, mod, dst) TT_OP(0x12, (u32)(lo) << 23 | (u32)(src) << 17 | (u32)(am) << 14 | (u32)(mod) << 12 | (u32)(dst))
#define MOVB2D(lo, src, am, mod, dst) TT_OP(0x13, (u32)(lo) << 23 | (u32)(src) << 17 | (u32)(am) << 14 | (u32)(mod) << 11 | (u32)(dst))
#define ELWMUL(clr, acc, mod19, am, dst) TT_OP(0x27, (u32)(clr) << 22 | (u32)(acc) << 21 | (u32)(mod19) << 19 | (u32)(am) << 14 | (u32)(dst))
#define MVMUL(clr, mod19, am, dst) TT_OP(0x26, (u32)(clr) << 22 | (u32)(mod19) << 19 | (u32)(am) << 14 | (u32)(dst))
#define T_PACR(ctx, pad, dam, am, adc, zw, intf, ovrd, cat, cc, fl, last)                                              \
  TT_OP(0x41, (u32)(ctx) << 21 | (u32)(pad) << 18 | (u32)(dam) << 17 | (u32)(am) << 15 | (u32)(adc) << 13 |             \
                  (u32)(zw) << 12 | (u32)(intf) << 8 | (u32)(ovrd) << 7 | (u32)(cat) << 4 | (u32)(cc) << 2 | (u32)(fl) << 1 | \
                  (u32)(last))
#define TT_NOP 0x02000000u

/* STALLWAIT block (B) and condition (C) bits */
enum { B_TDMA = 1, B_SYNC = 2, B_PACK = 4, B_UNPACK = 8, B_XMOV = 16, B_THCON = 32, B_MATH = 64, B_CFG = 128, B_SFPU = 256 };
enum { C_THCON = 1, C_UNPACK0 = 2, C_UNPACK1 = 4, C_PACK0 = 8, C_MATH = 16, C_SRCA_CLR = 32, C_SRCB_CLR = 64,
       C_SRCA_VLD = 128, C_SRCB_VLD = 256, C_XMOV = 512, C_TRISC_CFG = 1024, C_SFPU = 2048 };

/* format codes (ttrv/ops.py FMT) */
enum { F_FP32 = 0, F_FP16 = 1, F_BF16 = 5, F_BFP8 = 6, F_BFP4 = 7, F_LF8 = 10 };
#define FMT_BYTE_DATUM(f) ((f) == F_BFP8 || (f) == F_BFP4 || (f) == F_LF8)  /* Src stride datum size 1 (movement.py) */
#define FMT_BFP(f) ((f) == F_BFP8 || (f) == F_BFP4)

/* ---- addresses ---- */
#define CFG(w)            (TENSIX_CFG + 4 * (w))
#define SEM(i)            (0xFFE80020u + 4 * (i))  /* RISC view of Tensix semaphore i: lw value, sw 0 post, sw 1 get */
#define SEM_UNPACK_SYNC   5                         /* ttrv UNPACK_CREDIT */
#define SEM_MATH_PACK     1
#define PC_BUF_MOP_SYNC   0xFFE80008u
#define MOP_CFG           0xFFB80000u
#define DST_RISC          0xFFBD8000u

/* L1 layout shared by every k_unpack*.c kernel and unpack.py (all below 0x180000) */
#define U_FLAGS   0x48000u   /* 16 words of cross-RISC flags, cleared by the host each launch */
#define FL_START  (U_FLAGS + 0x00)  /* traffic generator -> T0: traffic is running */
#define FL_DONE   (U_FLAGS + 0x04)  /* T0 -> generators: measurement finished, stop */
#define FL_END    (U_FLAGS + 0x08)  /* generator -> T0: traffic stopped (budget ran out) */
#define FL_ARMED  (U_FLAGS + 0x0C)  /* T1 -> T0 (latency): rep r armed */
#define FL_FILLED (U_FLAGS + 0x10)  /* T0 -> T1 (full stall): both banks full in rep r */
#define FL_REL    (U_FLAGS + 0x14)  /* T1 -> T0 (full stall): rep r released */
#define FL_PSTART (U_FLAGS + 0x18)  /* packer -> T0: pack loop running */
#define FL_PEND   (U_FLAGS + 0x1C)  /* packer -> T0: pack loop stopped */
#define SRC_A     0x80000u   /* unpack sources: [0x80000, 0x100000) */
#define SRC_B     0x100000u  /* [0x100000, 0x160000) */
#define PACK_OUT  0x160000u  /* packer output: [0x160000, 0x170000) */
#define NOC_BUF   0x170000u  /* NoC traffic buffers: [0x170000, 0x180000) */

/* ---- small helpers ---- */
INLINE void cfg_write(u32 w, u32 v) { write32(CFG(w), v); }
INLINE void cfg_field(u32 w, u32 shift, u32 width, u32 v) {  /* RISC read-modify-write, setup only */
  u32 m = (width >= 32 ? 0xFFFFFFFFu : ((1u << width) - 1)) << shift;
  write32(CFG(w), (read32(CFG(w)) & ~m) | ((v << shift) & m));
}
/* ttrv field(): one RMWCIB per byte the mask touches (movement.py), so the Tensix stream matches the kernels */
INLINE u32 field_words(u32 *out, u32 w, u32 shift, u32 width, u32 v) {
  u32 m = (width >= 32 ? 0xFFFFFFFFu : ((1u << width) - 1)) << shift, n = 0;
  for (u32 i = 0; i < 4; i++) {
    u32 b = m >> (8 * i) & 255;
    if (b) out[n++] = RMWCIB(i, b, ((v << shift) >> (8 * i)) & b, w);
  }
  return n;
}
INLINE void field_push(u32 w, u32 shift, u32 width, u32 v) {
  u32 ws[4], n = field_words(ws, w, shift, width, v);
  for (u32 i = 0; i < n; i++) tensix_push(ws[i]);
}

INLINE void sync_load(u32 a) {  /* PC_BUF_SYNC style: store, load, consume */
  write32(a, 0);
  u32 v = read32(a);
  __asm__ volatile("andi %0, %0, 0" : "+r"(v));
}
INLINE void mop_sync(void) { sync_load(PC_BUF_MOP_SYNC); }
/* 9 MopCfg words: outer, inner, start, end0, end1, loop, loop1, loop0last, loop1last. Drains the expander first. */
INLINE void mop_cfg(u32 outer, u32 inner, u32 start, u32 end0, u32 end1, u32 loop, u32 loop1, u32 last0, u32 last1) {
  mop_sync();
  write32(MOP_CFG + 0, outer); write32(MOP_CFG + 4, inner); write32(MOP_CFG + 8, start);
  write32(MOP_CFG + 12, end0); write32(MOP_CFG + 16, end1); write32(MOP_CFG + 20, loop);
  write32(MOP_CFG + 24, loop1); write32(MOP_CFG + 28, last0); write32(MOP_CFG + 32, last1);
}

INLINE void spin(u32 cycles) { u32 t = now(); while (now() - t < cycles) {} }

/* Bounded flag waits. `soft`: on timeout record the site and carry on (used where the caller must still release
 * Tensix resources the other thread is blocked on); returns 0 on timeout. */
INLINE u32 wait_ge(u32 addr, u32 v, u32 site, u32 soft) {
  u32 left = BUDGET;
  while ((int)(read32(addr) - v) < 0) {
    fence();  /* L0 data cache: re-read L1 */
    if (!--left) {
      if (!soft) probe_fail(site);
      write32(RES_SITE, site);
      return 0;
    }
  }
  return 1;
}
/* Tensix semaphore poll (a load from SEM(i) must be consumed before the next one: the branch does that) */
INLINE void sem_wait_zero(u32 i, u32 site) { WAIT_UNTIL(read32(SEM(i)) == 0, site); }

/* ---- ttrv `unpack.fmt` (movement.py unpack(), name == "fmt"), unpacker i ----
 * sec = 64 + 48 i. in/out are format codes; transpose (Haloize) only on A. Words only the unpackers use are written
 * by RISC read-modify-write; words other threads also modify (1: ALU formats, 70/71/119: pack words holding unpacker
 * bits) go through RMWCIB as ttrv does, so a concurrent RMWCIB from T1/T2 is not lost. Drain before the first
 * UNPACR. */
INLINE void unpack_fmt(u32 i, u32 in, u32 out, u32 transpose, u32 lf8_e4m3) {
  u32 sec = 64 + 48 * i, size = FMT_BYTE_DATUM(out) ? 1 : 2;
  cfg_field(sec + 9, 8, 1, 0);                  /* no forced shared exponent */
  cfg_field(sec, 0, 4, in);                     /* descriptor InDataFormat */
  cfg_field(sec + 1, 0, 16, 1);                 /* YDim */
  cfg_field(sec + 8, 0, 4, out);                /* Out_data_format */
  cfg_field(sec + 8, 4, 2, 2);                  /* Throttle_mode (ignored unless the override bit is set) */
  cfg_field(sec + 8, 8, 1, transpose);          /* Haloize_mode */
  cfg_field(sec + 9, 0, 4, 15);                 /* Disable_zero_compress ctx 0-3 */
  cfg_field(sec + 9, 16, 4, 15);                /* ctx 4-7 */
  field_push(sec + 7, 22, 1, lf8_e4m3);         /* Unp_LF8_4b_exp (sits in pack words 71 / 119) */
  cfg_field(56 + 2 * i, 16, 16, 16 * size);     /* UNPn_ADDR_CTRL_XY_REG_1 Ystride */
  cfg_field(57 + 2 * i, 0, 16, 256 * size);     /* Zstride */
  field_push(1, 17 + 4 * i, 4, out);            /* ALU_FORMAT_SPEC SrcA / SrcB */
  cfg_field(sec + 8, 14, 1, 1);                 /* Ovrd_data_format */
  for (u32 ctx = 0; ctx < (i ? 2u : 8u); ctx++) cfg_field(sec + 28 + ctx % 4, 16 + 8 * (ctx / 4), 8, in | out << 4);
  if (!i) cfg_field(50, 8, 1, 1);               /* UNP0_ADD_DEST_ADDR_CNTR */
}

/* Throttle override: word 70 bit 3 (one bit for both unpackers) + REG2 Throttle_mode 0 x1, 1 x2, 2 x4 */
INLINE void unpack_throttle(u32 i, u32 mode) {
  field_push(70, 3, 1, 1);
  cfg_field(64 + 48 * i + 8, 4, 2, mode);
}

/* Per-block geometry that ttrv's move writes each time (movement.py name == "move"), here at setup:
 * descriptor XDim = x, ZDim = z, and for A ctx 0: Dest_cntx0 = 64 (Src row 0), Tile_x_dim_cntx0 = x. */
INLINE void unpack_geom(u32 i, u32 x, u32 z) {
  u32 sec = 64 + 48 * i;
  cfg_field(sec + 1, 16, 16, z);
  cfg_field(sec, 16, 16, x);
  if (!i) { cfg_field(sec + 20, 0, 16, 64); cfg_field(sec + 22, 0, 16, x); }
}
INLINE u32 base_word(u32 i) { return 64 + 48 * i + 12; }  /* REG3_Base_address, ctx 0 */
INLINE void unpack_base(u32 i, u32 addr) { cfg_write(base_word(i), (addr >> 4) - 1); }

#endif
