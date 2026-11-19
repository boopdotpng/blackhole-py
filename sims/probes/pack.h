/* Packer probe helpers (pack.py, k_pack*.c): Tensix instruction encodings, packer configuration in the form the
 * llama kernels emit it, bounded RISC-side polling of Tensix semaphores, and the shared L1 layout of the pack probes.
 *
 * Encodings are unrotated Tensix words (opcode << 24 | fields), as ttrv/isa.py's tensix() builds them; TTINSN pushes a
 * constant one, tensix_push a runtime one. Field layouts are from ttrv/isa.py's TENSIX table (checked by pack.py's
 * self-test against ttrv.isa.tensix). Generic enough to merge with the FPU / unpacker probe headers later. */
#ifndef PACK_H
#define PACK_H
#include "probe.h"

/* ---- encodings ---- */
#define TT_NOP                  (0x02u << 24)
#define TT_DMANOP               (0x60u << 24)
#define TT_SFPNOP               (0x8Fu << 24)
#define TT_MOP(type, lc, zm)    (0x01u << 24 | (u32)(type) << 23 | (u32)(lc) << 16 | (u32)(zm))
#define TT_PACR(am, intf, last) (0x41u << 24 | (u32)(am) << 15 | (u32)(intf) << 8 | (u32)(last))
#define TT_PACR_ZW(am, intf, last) (TT_PACR(am, intf, last) | 1u << 12)  /* ZeroWrite */
#define TT_SETADC(cnt, ch, dim, v) (0x50u << 24 | (u32)(cnt) << 21 | (u32)(ch) << 20 | (u32)(dim) << 18 | (u32)(v))
#define TT_SETADCXX(cnt, xend, xstart) (0x5Eu << 24 | (u32)(cnt) << 21 | (u32)(xend) << 10 | (u32)(xstart))
#define TT_SETADCXY(cnt, c1y, c1x, c0y, c0x, mask) \
  (0x51u << 24 | (u32)(cnt) << 21 | (u32)(c1y) << 15 | (u32)(c1x) << 12 | (u32)(c0y) << 9 | (u32)(c0x) << 6 | (u32)(mask))
#define TT_SETADCZW(cnt, c1w, c1z, c0w, c0z, mask) \
  (0x54u << 24 | (u32)(cnt) << 21 | (u32)(c1w) << 15 | (u32)(c1z) << 12 | (u32)(c0w) << 9 | (u32)(c0z) << 6 | (u32)(mask))
#define TT_STALLWAIT(stall, wait) (0xA2u << 24 | (u32)(stall) << 15 | (u32)(wait))
#define TT_SEMWAIT(stall, sel, cond) (0xA6u << 24 | (u32)(stall) << 15 | (u32)(sel) << 2 | (u32)(cond))
#define TT_SEMPOST(sel)         (0xA4u << 24 | (u32)(sel) << 2)
#define TT_SEMGET(sel)          (0xA5u << 24 | (u32)(sel) << 2)
#define TT_SEMINIT(max, init, sel) (0xA3u << 24 | (u32)(max) << 20 | (u32)(init) << 16 | (u32)(sel) << 2)
#define TT_ZEROACC(mode, b32, czf, am, where) \
  (0x10u << 24 | (u32)(mode) << 19 | (u32)(b32) << 18 | (u32)(czf) << 17 | (u32)(am) << 14 | (u32)(where))
#define TT_WRCFG(gpr, w128, cfg) (0xB0u << 24 | (u32)(gpr) << 16 | (u32)(w128) << 15 | (u32)(cfg))
#define TT_SETDMAREG16(idx, v)  (0x45u << 24 | ((u32)(v) & 0xFFFF) << 8 | (u32)(idx))  /* 16-bit immediate to GPR half idx */
#define TT_RMWCIB(byte, mask, data, cfg) ((0xB3u + (byte)) << 24 | (u32)(mask) << 16 | (u32)(data) << 8 | (u32)(cfg))
#define TT_REPLAY(start, len, ewl, load) (0x04u << 24 | (u32)(start) << 14 | (u32)(len) << 4 | (u32)(ewl) << 1 | (u32)(load))
#define TT_SFPLOADI(lreg, mod, imm) (0x71u << 24 | (u32)(lreg) << 20 | (u32)(mod) << 16 | ((u32)(imm) & 0xFFFF))
#define TT_SFPSTORE(lreg, mod, am, addr) (0x72u << 24 | (u32)(lreg) << 20 | (u32)(mod) << 16 | (u32)(am) << 13 | (u32)(addr))
#define TT_SFPSHFT(imm12, vc, vd, mod1) (0x7Au << 24 | ((u32)(imm12) & 0xFFF) << 12 | (u32)(vc) << 8 | (u32)(vd) << 4 | (u32)(mod1))
#define TT_SFPIADD(imm12, vc, vd, mod1) (0x79u << 24 | ((u32)(imm12) & 0xFFF) << 12 | (u32)(vc) << 8 | (u32)(vd) << 4 | (u32)(mod1))
#define TT_UNPACR(sel, am, ovrd, dvalid, last) \
  (0x42u << 24 | (u32)(sel) << 23 | (u32)(am) << 15 | (u32)(ovrd) << 7 | (u32)(dvalid) << 6 | (u32)(last))

/* STALLWAIT / SEMWAIT fields (ttrv/isa.py Stall, Wait, SemWait) */
#define STALL_TDMA   0x001u
#define STALL_SYNC   0x002u
#define STALL_PACK   0x004u
#define STALL_UNPACK 0x008u
#define STALL_MATH   0x040u
#define STALL_CFG    0x080u
#define STALL_SFPU   0x100u
#define WAIT_THCON   0x001u
#define WAIT_UNPACK0 0x002u
#define WAIT_PACK0   0x008u
#define WAIT_MATH    0x010u
#define WAIT_SRCA_CLR 0x020u
#define WAIT_TRISC_CFG 0x400u
#define WAIT_SFPU    0x800u
#define SEM_ON_ZERO  1u
#define SEM_ON_MAX   2u

/* Semaphores: firmware SEMINITs all eight to (max 1, value 0) every launch. 1 = MATH_PACK (llama), 3 = fill done (the
 * pack probes' own), 5 = UNPACK_SYNC (left alone). */
#define SEM_MATH_PACK 1
#define SEM_FILL      3
#define SEM_REG(i)    (0xFFE80020u + 4u * (i))  /* RISC view: value of semaphore i */
INLINE u32 sem_value(u32 i) { return read32(SEM_REG(i)) & 0xF; }

/* ---- packer configuration words (docs/ttrv_cfg.md, ttrv_pack_unpack.md), bank 0 ---- */
#define CFG(w)            (TENSIX_CFG + 4u * (w))
#define CW_PCK_DEST_RD    18   /* bit 0 Read_32b_data, bit 3 Round_10b_mant */
#define CW_PCK0_XY0       12   /* Dst Ystride << 16 */
#define CW_PCK0_ZW0       13   /* Dst Zstride | Wstride << 16 */
#define CW_PCK0_XY1       14   /* L1 Ystride << 16 */
#define CW_PCK0_ZW1       15   /* L1 Zstride | Wstride << 16 (bytes, 16 B aligned) */
#define CW_ROWSET0        20
#define CW_ROWSET1        21
#define CW_EDGE0          24   /* PCK_EDGE_OFFSET_SEC0_mask | mode << 16 | row-set select */
#define CW_EDGE1          25
#define CW_PACK_COUNTERS  28   /* pack_reads_per_xy_plane = 16: 0x1000 */
#define CW_EXP_SIZE       68   /* Exp_section_size << 16 */
#define CW_L1_DEST        69   /* (addr >> 4) - 1, bit 31 as llama writes it */
#define CW_PACK_FMT       70   /* 1 uncompressed | 4 Disable_pack_zero_flags | out << 4 | in << 8 */
#define CW_PACK_MISC      71   /* bit 19 Pack_L1_Acc, bit 23 Pac_LF8_4b_exp (e4m3) */
#define CW_PACK_DST_OFS   180  /* DEST_TARGET_REG_CFG_PACK_SEC0_Offset */
#define THD_ADDR_MOD_PACK 37   /* SETC16 37..40: ADDR_MOD_PACK_SEC0..3 */

/* Formats in scope (pack.py FORMATS): (in, out) pairs the llama kernels and their ttrv ports use, plus bfp8/bfp4. */
enum { FMT_F32_F32, FMT_F32_BF16, FMT_BF16_BF16_D16, FMT_F16_E4M3, FMT_F32_BFP8, FMT_F32_BFP4, FMT_COUNT };
typedef struct { u8 in, out, read32, round10, e4m3, insize, bfp, dst16; } packfmt;
static const packfmt FORMATS[FMT_COUNT] = {
  [FMT_F32_F32] = {0, 0, 1, 0, 0, 4, 0, 0},
  [FMT_F32_BF16] = {0, 5, 1, 0, 0, 4, 0, 0},
  [FMT_BF16_BF16_D16] = {5, 5, 0, 0, 0, 2, 0, 1},  /* 16-bit Dst, as llama down/o */
  [FMT_F16_E4M3] = {1, 10, 1, 1, 1, 2, 0, 0},      /* fp32 Dst read as fp16 (Round_10b), out lf8 E4M3 */
  [FMT_F32_BFP8] = {0, 6, 1, 0, 0, 4, 1, 0},
  [FMT_F32_BFP4] = {0, 7, 1, 0, 0, 4, 1, 0},
};

INLINE void cfg_write(u32 w, u32 v) { write32(CFG(w), v); }
/* RISC config writes, then a read back so they have landed before the Tensix uses them (setup only). */
INLINE void cfg_commit(u32 w) { u32 v = read32(CFG(w)); __asm__ volatile("andi %0, %0, 0" : "+r"(v)); }

/* ---- L1 layout shared by the pack probe kernels (mirrored in pack.py) ---- */
#define PK_FLAGS        0x40200u
#define PK_TRAFFIC_UP   (PK_FLAGS + 0x00)  /* BRISC traffic started: its start time */
#define PK_STOP         (PK_FLAGS + 0x10)  /* TRISC2 -> traffic / unpack: stop */
#define PK_UNPACK_UP    (PK_FLAGS + 0x20)  /* TRISC0 unpack stream started */
#define PK_VIS_GO       (PK_FLAGS + 0x30)  /* TRISC2 -> BRISC: sample s + 1 starting */
#define PK_VIS_DONE     (PK_FLAGS + 0x40)  /* BRISC -> TRISC2: sample s + 1 reads done */
#define PK_READY        (PK_FLAGS + 0x50)  /* TRISC2 -> TRISC1: semaphores initialised */
#define PK_OUT          0x80000u           /* pack output (bank 5 if banks are contiguous 96 KiB ranges) */
#define PK_VIS_SLOTS    0xC0000u           /* BRISC NoC-read landing slots, 16 B each */

/* ---- MOP template 1 (llama's: outer x inner PACRs, face end AddrMode 2, tile end AddrMode 1 + Last) ---- */
#define MOP_CFG_BASE 0xFFB80000u
#define PC_BUF_MOP_SYNC 0xFFE80008u
INLINE void mop_drain(void) {
  write32(PC_BUF_MOP_SYNC, 0);
  u32 v = read32(PC_BUF_MOP_SYNC);
  __asm__ volatile("andi %0, %0, 0" : "+r"(v));
}
INLINE void mop_config(u32 outer, u32 inner, u32 start, u32 end0, u32 end1, u32 loop, u32 loop1, u32 last0,
                       u32 last1) {
  mop_drain();
  u32 w[9] = {outer, inner, start, end0, end1, loop, loop1, last0, last1};
  for (u32 i = 0; i < 9; i++) write32(MOP_CFG_BASE + 4 * i, w[i]);
}
/* Tile (or face run) of `faces` x 4 PACRs of four rows, exactly as llama's exported kernels program it. */
INLINE void mop_pack_faces(u32 faces) {
  mop_config(faces, 4, TT_NOP, TT_NOP, TT_NOP, TT_PACR(0, 0, 0), TT_NOP, TT_PACR(1, 0, 1), TT_PACR(2, 0, 0));
}

/* Wait until the packer is idle, then until this thread's Tensix instructions are done (llama's per-tile end). */
INLINE void pack_wait(void) {
  TTINSN(TT_STALLWAIT(STALL_SYNC, WAIT_PACK0));
  tensix_drain();
}

#endif
