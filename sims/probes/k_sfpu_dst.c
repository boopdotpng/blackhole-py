/* FPU -> SFPU through Dst (sfpu.py: the old test_sfpu_dst.py images()). Three TRISCs, one GO:
 *   trisc0 (PART 0)  unpack A (SrcA) and B (SrcB), 1024 BF16 each (1/64), then L1 READY = 1
 *   trisc1 (PART 1)  wait READY (bounded), FP32 Dst, MOVA2D-define tiles 0 and 2, LREGs = 0, then either
 *                      VALUE: COMPUTE once (ELWMUL; gap; SFPLOAD), or
 *                      LOOP:  PROF_REC; 1: BODY; addi; bnez 1b; PROF_DRAIN(SYNC, MATH|SFPU); PROF_REC
 *                    then SFPSTORE L0 to Dst rows 128.. (tile 2) and publish to the packer
 *   trisc2 (PART 2)  pack 64 rows of Dst tile 2 to OUTPUT + 8192 as F32
 * L1 (as the old run): A 0x40000, B 0x40800, READY 0x41000, OUTPUT 0x42000 (host initialises them every launch).
 * Params (trisc1): [0] loop iterations. LOOP time stamps at PROF0/PROF1 (trisc1 LOG + 0xFC0/0xFC4). */
#include "sfpu.h"

#define A_ADDR  0x40000
#define B_ADDR  0x40800
#define READY   0x41000
#define OUTPUT  0x42000

enum { SITE_CFG_A = 1, SITE_CFG_B, SITE_READY, SITE_MATH_PACK };

#if PART == 0
/* unpack.py configure_unpacker(engine, address, BF16, SrcA/SrcB, commit=False): the per-engine config words */
INLINE void configure_unpacker_bf16(u32 e, u32 address, u32 site) {
  u32 sec = e * 0xC0, ab = e * 8;          /* THCON section stride; the address counters are interleaved */
  WAIT_UNTIL(!(read32(UNPACK_CONFIG_SYNC) & 0xFE), site);
  TTINSN(0xB2000000);                      /* SETC16(0, 0) */
  write32(CFG(0x100 + sec), 0x15 | (e ? 256u << 16 : 0)); write32(CFG(0x104 + sec), 0x40001);
  write32(CFG(0x108 + sec), 0); write32(CFG(0x10C + sec), 0);
  write32(CFG(0x120 + sec), 0x25); write32(CFG(0x124 + sec), 0x3); write32(CFG(0x128 + sec), 0); write32(CFG(0x12C + sec), 0);
  if (e) TTINSN(0xB5400077); else TTINSN(0xB5400047);  /* RMWCIB2 cfg 71 + 48 e: mask 0x40 data 0 */
  write32(CFG(0xB0 + ab), 0); write32(CFG(0xB4 + ab), 0); write32(CFG(0xE0 + ab), 0x200002); write32(CFG(0xE4 + ab), 0x200);
  write32(CFG(e ? 0xF0 : 0xC0), 0); write32(CFG(e ? 0xF4 : 0xC4), 0);   /* ADDR_BASE0/1 */
  write32(CFG(e ? 0xF8 : 0xC8), e ? 0 : 0x100); write32(CFG(e ? 0xFC : 0xD4), 0);  /* ADDR_MISC, NOP_CLEAR */
  write32(CFG(0x150 + sec), e ? 0 : 0x400040); write32(CFG(0x158 + sec), 0x1000100);
  write32(CFG(0x170 + sec), 0); write32(CFG(0x174 + sec), 0);
  write32(CFG(0x130 + sec), (address >> 4) - 1); write32(CFG(0x134 + sec), (address >> 4) - 1);
  TTINSN(0xB2290000);                      /* SETC16(UNPACK_MISC_CONFIG, 0) */
  if (!e) TTINSN(0xB2050004);              /* SETC16(SRCA_SET, 4) */
}
#endif

KERNEL kernel_main(void) {
  record_config();
#if PART == 0
  configure_unpacker_bf16(0, A_ADDR, SITE_CFG_A);
  configure_unpacker_bf16(1, B_ADDR, SITE_CFG_B);
  (void)read32(CFG(0x130));
  write32(UNPACK_CONFIG_SYNC, 0);
  TTINSN(0x5E23FC00); TTINSN(0x5E43FC00); TTINSN(0x5460000F);  /* SETADCXX(1,255) SETADCXX(2,255) SETADCZW(3) */
  TTINSN(0x5E6FFC00);                      /* SETADCXX(3, 1023, 0) */
  configure_mop(1, 1, 0x420080C1, W_NOP, W_NOP, 0x428080C1, W_NOP, 0x428080C1, 0x428080C1);  /* UNPACR A, B */
  TTINSN(W_MOP);
  TTINSN(0xA2010006);                      /* STALLWAIT(SYNC, UNPACK0 | UNPACK1): this thread's own unpacks */
  TTINSN(0xA5000080);                      /* SEMGET(UNPACK_SYNC) */
  tensix_drain();
  write32(READY, 1);
  fence();
#elif PART == 1
  WAIT_L1(read32(READY) == 1, SITE_READY);
  fence();
  TTINSN(0xB2000000); TTINSN(0xB2010000); TTINSN(0xA2400810); TTINSN(0xB6202001);  /* configure_fp32_dst(0) */
  TTINSN(0xB20B0000); TTINSN(0xB20C0000); TTINSN(0xB21C0000); TTINSN(0xB22F0000);  /* SETC16 11, 12, 28, 47 = 0 */
  TTINSN(0x3700000F);                      /* SETRWC(0, 0, 0, 0, 0, 15) */
  TTINSN(0x101C4000);                      /* ZEROACC(3, 1, 0, 1, 0) */
  /* STALLWAIT(MATH, SRCA_VLD | SRCB_VLD): both banks were filled before READY was written, so this holds now */
  TTINSN(0xA2200180);
  T(0x48008000, 0x48008020, 0x48008040, 0x48008060, 0x48008080, 0x480080a0, 0x480080c0, 0x480080e0,
    0x48008200, 0x48008220, 0x48008240, 0x48008260, 0x48008280, 0x480082a0, 0x480082c0, 0x480082e0)
                                           /* MOVA2D(0, 0, 0, 2, row): rows 0..56 and 128..184 step 8 (rotated) */
  TTINSN(0xA2800010);                      /* STALLWAIT(SFPU, MATH) */
  SETUP                                    /* SFPENCC; LREG0-7 = 0.0 (sfpu.py) */
  TTINSN(W_STALL_SYNC_MATH_SFPU);
  tensix_drain();
#ifdef LOOP
  u32 n = PARAM(0);
  __asm__ volatile(PROF_REC(PROF0)
                   "1:\n"
                   ".word " XSTR(BODY) "\n"
                   "addi %0, %0, -1\n"
                   "bnez %0, 1b\n"
                   PROF_DRAIN(ROT_STALL_SYNC_MATH_SFPU)
                   PROF_REC(PROF1)
                   "fence\n" : "+r"(n) :: "t5", "t6", "memory");
#else
  COMPUTE                                  /* ELWMUL; gap; SFPLOAD (one block) */
#endif
  TTINSN(W_STALL_SYNC_MATH_SFPU);
  T(0xc80c0201, 0xc80c0209, 0xc80c0211, 0xc80c0219)  /* SFPSTORE(0, 3, 0, 128 + 2 pos), rotated */
  sfpu_drain();
  TTINSN(0x37C0000F);                      /* SETRWC(3, ...): release both Src banks */
  publish_dst();
#elif PART == 2
  sem_wait_nonzero(SEM_MATH_PACK, SITE_MATH_PACK);  /* old: SEMWAIT(TDMA, MATH_PACK, ON_ZERO) */
  configure_packer_f32();
  pack_row_addressing();
  configure_mop(1, 64, W_NOP, W_NOP, W_NOP, 0x41000100, W_NOP, 0x41008101, W_NOP);
  tensix_drain();
  TTINSN(0x50840000); TTINSN(0x50880000); TTINSN(0x508C0002);  /* _set_dst_position(2, 0) */
  write32(CFG(0x114), (((OUTPUT + 2 * 4096) >> 4) - 1) | 0x80000000);  /* L1_DESTINATION */
  write32(CFG(0x2D0), 0);                  /* DESTINATION_OFFSET */
  TTINSN(0x5E803C00);                      /* SETADCXX(4, 15, 0) */
  TTINSN(W_MOP);
  TTINSN(0xA2010008);                      /* STALLWAIT(SYNC, PACK0) */
  tensix_drain();
  TTINSN(0xA5000008);                      /* SEMGET(MATH_PACK) */
#else
#error "PART must be 0, 1 or 2"
#endif
  tensix_drain();
  probe_done();
}
