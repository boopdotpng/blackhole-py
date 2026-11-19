/* TRISC2 packer for the unpacker probes (unpack.py). One image per PACK (compile-time).
 *
 * PACK_VERIFY  waits (RISC-side, bounded) for T1's MATH_PACK post, packs Dst tile 0 (64 rows of 32-bit Dst, or 64
 *              rows of 16-bit Dst) to L1, releases MATH_PACK. Configuration is blackhole-py-old
 *              tests/movement/unpacker/unpack.py configure_packer + emit_pack_dst, which passed on hardware.
 * PACK_LOOP    L1 write contention: the same configuration (fp32 Dst -> bf16), then packs Dst tile 0 to PACK_OUT
 *              two tiles per drain until T0 raises FL_DONE or `max` tiles; FL_PSTART after the first pair, FL_PEND
 *              at the end. Dst holds whatever it holds: only the L1 traffic matters.
 * Neither mode issues a Tensix-side wait on another thread. */
#define PACK_VERIFY 1
#define PACK_LOOP 2
#include "unpack.h"

enum { P_OUT, P_SRC, P_DST32, P_ADDR, P_W70, P_MAX };
enum { SITE_MATH = 1 };

static void configure(u32 out, u32 src, u32 dst32, u32 w70) {
  u32 lf8 = out == F_LF8, size = src == F_FP32 ? 4 : 2;
  tensix_push(RMWCIB(2, 0x80, lf8 ? 0x80 : 0, 71));  /* Pac_LF8_4b_exp (bit 23; bit 22 is the unpacker's) */
  tensix_push(SETC16(0, 0));
  tensix_push(RMWCIB(3, 0x1E, src << 1, 1));         /* pack source format */
  tensix_push(RMWCIB(0, 0x07, 0, 1));                /* no stochastic rounding */
  tensix_push(RMWCIB(0, 0xFC, 0, 2));                /* no ReLU */
  tensix_push(RMWCIB(1, 0xFF, 0, 2));
  tensix_push(RMWCIB(2, 0x3F, 0, 2));
  tensix_drain();
  cfg_write(68, lf8 ? 0 : 0x40000);                   /* SECTION_SIZES */
  cfg_write(70, 1 | out << 4 | (lf8 ? F_FP16 : src) << 8 | w70);  /* DATA_FORMAT; w70 keeps the unpack throttle bit */
  cfg_write(18, dst32 | (lf8 && dst32 ? 8 : 0));      /* DESTINATION_READ */
  cfg_write(12, (16 * size) << 16);                   /* Dst read strides */
  cfg_write(13, 256 * size | (1024 * size) << 16);
  cfg_write(28, 0x1000);
  cfg_write(24, 0xFFFF);
  cfg_write(25, 0);
  cfg_write(20, 0);
  cfg_write(21, 0);
  cfg_write(180, 0);                                  /* DESTINATION_OFFSET */
  u32 tile_bytes = out == F_FP32 ? 4096 : lf8 ? 1024 : 2048;
  write32(REGFILE + 16 * 4, tile_bytes >> 4);
  write32(REGFILE + 52 * 4, 0x40000);
  tensix_push(SETC16(37, 0x0104));
  tensix_push(SETC16(38, 0x2820));
  tensix_push(SETC16(39, 0x1120));
  tensix_push(SETADCXY(4, 0, 0, 0, 0, 0xB));
  tensix_push(SETADCZW(4, 0, 0, 0, 0, 0xF));
  u32 pacr = T_PACR(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
  mop_cfg(4, 4, TT_NOP, TT_NOP, TT_NOP, pacr, TT_NOP, T_PACR(0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1),
          T_PACR(0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0));
  tensix_drain();
}

INLINE void set_dest(u32 addr) { cfg_write(69, ((addr >> 4) - 1) | 0x80000000u); }
INLINE void pack_tile(void) {
  tensix_push(SETADC(4, 0, 3, 0));               /* W = Dst tile 0 */
  tensix_push(SETADCXX(4, 15, 0));
  tensix_push(SETADCZW(4, 0, 0, 0, 0, 5));
  tensix_push(STALLWAIT(B_CFG, C_PACK0));
  tensix_push(MOP1);
}

#if PACK == PACK_VERIFY
KERNEL kernel_main(void) {
  configure(PARAM(P_OUT), PARAM(P_SRC), PARAM(P_DST32), PARAM(P_W70));
  set_dest(PARAM(P_ADDR));
  WAIT_UNTIL(read32(SEM(SEM_MATH_PACK)) != 0, SITE_MATH);
  pack_tile();
  tensix_push(STALLWAIT(B_SYNC, C_PACK0));
  tensix_drain();
  write32(SEM(SEM_MATH_PACK), 1);  /* get */
  probe_done();
}
#endif

#if PACK == PACK_LOOP
KERNEL kernel_main(void) {
  configure(F_BF16, F_BF16, 1, PARAM(P_W70));
  set_dest(PACK_OUT);
  u32 max = PARAM(P_MAX), n = 0;
  u32 t0 = now();
  while (n < max) {
    pack_tile();
    pack_tile();
    tensix_drain();
    n += 2;
    if (n == 2) write32(FL_PSTART, 1);
    fence();  /* L0 data cache: re-read L1 */
    if (read32(FL_DONE)) break;
  }
  write32(FL_PEND, 1);
  log_word(0, t0);
  log_word(1, now());
  log_word(2, n);
  write32(RES_COUNT, 3);
  probe_done();
}
#endif
