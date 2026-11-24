#pragma once
#include "hw.h"  // addresses and layouts; hand-written, host-side copies live in fw/__init__.py and device.py

typedef unsigned char u8;
typedef unsigned int u32;

#define INLINE static inline __attribute__((always_inline))
#define NORETURN __attribute__((noreturn)) void
#define MIN(a, b) ((a) < (b) ? (a) : (b))

INLINE void fence(void) { __asm__ volatile("fence" ::: "memory"); }
INLINE u32 read32(u32 a) { return *(volatile u32 *)a; }
INLINE void write32(u32 a, u32 v) { *(volatile u32 *)a = v; }

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

INLINE void enable_clock_gating(void) {
  write32(DEST_CG_CTRL, 0);
  write32(TDMA_CLK_GATE_EN, 0x3F);
  for (u32 niu = 0; niu < 2; niu++) {
    u32 cfg = NOC0_REGS + 0x100 + niu * NOC_INSTANCE_OFFSET;
    write32(cfg, read32(cfg) | 1);
    write32(cfg + 4, read32(cfg + 4) | 1);
  }
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

// A Tensix instruction inlined into the RISC instruction stream (hw.isa.inline)
#define TT(w) __asm__ volatile(".word %0" :: "i"((u32)(w) << 2 | (u32)(w) >> 30) : "memory")

#define STR_(x) #x
#define STR(x) STR_(x)
#define SET_SP(stack) "li sp, " STR(stack) "\n"
