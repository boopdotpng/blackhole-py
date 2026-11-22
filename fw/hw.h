#ifndef HW_H
#define HW_H
#include "abi.h"

typedef unsigned char u8;
typedef unsigned int u32;

#define INLINE static inline __attribute__((always_inline))
#define NORETURN __attribute__((noreturn)) void
#define MIN(a, b) ((a) < (b) ? (a) : (b))

INLINE void fence(void) { __asm__ volatile("fence" ::: "memory"); }
INLINE u32 read32(u32 a) { return *(volatile u32 *)a; }
INLINE u8 read8(u32 a) { return *(volatile u8 *)a; }
INLINE void write32(u32 a, u32 v) { *(volatile u32 *)a = v; }
INLINE void write8(u32 a, u8 v) { *(volatile u8 *)a = v; }

#define WAIT_FAST(cond) do { while (!(cond)) fence(); fence(); } while (0)
#ifndef POLL_BACKOFF
#define POLL_BACKOFF 64
#endif
#define WAIT_SLOW(cond) do { \
    while (!(cond)) { \
      fence(); \
      u32 n_ = POLL_BACKOFF; \
      __asm__ volatile("1: addi %0, %0, -1\n bnez %0, 1b" : "+r"(n_)); \
    } \
    fence(); \
  } while (0)

#define TDMA_CLK_GATE_EN         0xFFB11024
#define SOFT_RESET               0xFFB121B0
#define RESET_BRISC              (1u << 11)
#define RESET_TRISC0             (1u << 12)
#define RESET_NCRISC             (1u << 18)
#define RESET_ALL                0x47800u
#define WALL_CLOCK_L             0xFFB121F0
#define WALL_CLOCK_H             0xFFB121F8
#define TRISC0_RESET_PC          0xFFB12228
#define TRISC_RESET_PC_OVERRIDE  0xFFB12234
#define NCRISC_RESET_PC          0xFFB12238
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223C
#define DEST_CG_CTRL             0xFFB12240

#define PC_BUF_BASE              0xFFE80000
#define PCBUF(i)                 (PC_BUF_BASE + (i) * 0x10000)
#define PC_BUF_SYNC              0xFFE80004
#define MAILBOX_TO_BRISC         0xFFEC0000
#define MAILBOX_FROM(i)          (0xFFEC1000 + (i) * 0x1000)

#define REGFILE                  0xFFE00000
#define INSTRN_BUF               0xFFE40000
#define TENSIX_CFG               0xFFEF0000
#define CFG_ECC_SCRUBBER         (TENSIX_CFG + 3 * 4)
#define CFG_RISCV_IC_INVALIDATE  (TENSIX_CFG + 185 * 4)
#define CFG_RISC_PREFETCH_CTRL   (TENSIX_CFG + 208 * 4)
#define CFG_BANK_WORDS           224
#define CFG_GLOBAL_BASE          180
#define CFG_STATE_RESET          4

#define STREAM_REG(stream, reg)  (0xFFB40000 + (stream) * 0x1000 + (reg) * 4)

INLINE void reset_cb_counters(void) {
  for (u32 cb = 0; cb < 32; cb++) {
    write32(STREAM_REG(8 + cb, 8), 0);
    write32(STREAM_REG(8 + cb, 10), 0);
  }
}

INLINE void tensix_push(u32 instruction) { write32(INSTRN_BUF, instruction); }
INLINE void tensix_drain(void) {
  write32(PC_BUF_SYNC, 0);
  u32 v = read32(PC_BUF_SYNC);
  __asm__ volatile("andi %0, %0, 0" : "+r"(v));
}

#define TTINSN(w) __asm__ volatile(".word %0" :: "i"((((u32)(w)) << 2) | (((u32)(w)) >> 30)) : "memory")

#define ZEROACC_ALL       0x10180000
#define SFPENCC_RESET     0x8A00300A
#define NOP               0x02000000
#define SFPLOADI_MINUS1   0x7100BF80
#define SFPCONFIG_L11     0x910000B0
#define SEMINIT_ALL       0xA31003FC
#define CLEARDVALID_RESET 0x36000001

INLINE void enable_clock_gating(void) {
  write32(DEST_CG_CTRL, 0);
  write32(TDMA_CLK_GATE_EN, 0x3F);
  for (u32 niu = 0; niu < 2; niu++) {
    u32 cfg = 0xFFB20100 + niu * 0x10000;
    write32(cfg, read32(cfg) | 1);
    write32(cfg + 4, read32(cfg + 4) | 1);
  }
}

INLINE void reset_tensix(void) {
  write32(TENSIX_CFG + CFG_STATE_RESET * 4, 0);
  write32(TENSIX_CFG + (CFG_BANK_WORDS + CFG_STATE_RESET) * 4, 0);
  for (u32 i = CFG_GLOBAL_BASE; i < 185; i++) write32(TENSIX_CFG + i * 4, 0);
  for (u32 i = 187; i < CFG_BANK_WORDS; i++) write32(TENSIX_CFG + i * 4, 0);
  TTINSN(ZEROACC_ALL);
  TTINSN(CLEARDVALID_RESET);
  TTINSN(SFPENCC_RESET);
  TTINSN(NOP);
  TTINSN(SFPLOADI_MINUS1);
  TTINSN(SFPCONFIG_L11);
  write32(CFG_ECC_SCRUBBER, 0x803);
  TTINSN(SEMINIT_ALL);
  reset_cb_counters();
  write32(CFG_RISC_PREFETCH_CTRL, 0x11F);
}

#define SETC16(i, v)   (0xB2000000 | (i) << 16 | (v))
#define THD_CFG_TTSYNC 56
#define THD_CFG_RESET  67
#define SETRWC_ZERO    0x3700000F
#define SETADCXY_ZERO  0x51E0000F
#define SETADCZW_ZERO  0x54E0000F

INLINE void reset_thread(void) {
  #pragma clang loop unroll(disable)
  for (u32 i = 0; i < THD_CFG_RESET; i++) {
    if (i < 64) write32(REGFILE + 4 * i, 0);
    if (i != THD_CFG_TTSYNC) tensix_push(SETC16(i, 0));
  }
  TTINSN(SETRWC_ZERO);
  TTINSN(SETADCXY_ZERO);
  TTINSN(SETADCZW_ZERO);
}

#define CFG0_SET(v) __asm__ volatile("csrs 0x7c0, %0" :: "r"(v) : "memory")
#define CFG0_CLEAR(v) __asm__ volatile("csrc 0x7c0, %0" :: "r"(v) : "memory")
INLINE void configure_csr(int trisc) {
  CFG0_SET(2u);
  fence();
  if (trisc) CFG0_CLEAR(1u << 18);
  else CFG0_SET(1u << 18);
  CFG0_CLEAR(2u);
  fence();
  CFG0_CLEAR(8u);
}

INLINE void invalidate_icache(void) {
  write32(CFG_RISCV_IC_INVALIDATE, 0x1F);
  fence();
}

#define STR_(x) #x
#define STR(x) STR_(x)
#define SET_SP(stack) "li sp, " STR(stack) "\n"
#define SET_GP(gp) "li gp, " STR(gp) "\n"

#endif
