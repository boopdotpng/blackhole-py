#ifndef HW_H
#define HW_H
#include "abi.h"

typedef unsigned char u8;
typedef unsigned int u32;

#define INLINE static inline __attribute__((always_inline))
#define NORETURN __attribute__((noreturn)) void
#define MIN(a, b) ((a) < (b) ? (a) : (b))

#define KERNEL __attribute__((section(".entry"))) NORETURN
#define JUMP(address) (((__attribute__((noreturn)) void (*)(void))(address))())

INLINE void fence(void) { __asm__ volatile("fence" ::: "memory"); }
INLINE u32 read32(u32 a) { return *(volatile u32 *)a; }
INLINE u8 read8(u32 a) { return *(volatile u8 *)a; }
INLINE void write32(u32 a, u32 v) { *(volatile u32 *)a = v; }
INLINE void write8(u32 a, u8 v) { *(volatile u8 *)a = v; }

INLINE void wait8(u32 a, u8 v) {
  while (read8(a) != v) fence();
  fence();
}

#define TDMA_CLK_GATE_EN         0xFFB11024  /* clock gating per TDMA block, 0x3F = all */
#define SOFT_RESET               0xFFB121B0  /* bit set = held in reset: 11 BRISC, 12-14 TRISC0-2, 18 NCRISC */
#define WALL_CLOCK_L             0xFFB121F0  /* reading this latches the high word into WALL_CLOCK_H */
#define WALL_CLOCK_H             0xFFB121F8
#define TRISC0_RESET_PC          0xFFB12228  /* +4 per TRISC: where it starts when released from reset */
#define TRISC_RESET_PC_OVERRIDE  0xFFB12234  /* bit n: TRISCn uses its RESET_PC rather than the hardwired one */
#define NCRISC_RESET_PC          0xFFB12238
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223C
#define DEST_CG_CTRL             0xFFB12240  /* Dst clock gating control, tt-metal writes 0 */

#define REGFILE      0xFFE00000  /* this TRISC's 64 Tensix GPRs, u32 each */
#define INSTRN_BUF   0xFFE40000  /* a store here pushes one instruction to this RISC's Tensix thread */
#define TENSIX_CFG   0xFFEF0000  /* shared config registers, u32 each */
#define CFG_ECC_SCRUBBER        (TENSIX_CFG + 3 * 4)
#define CFG_RISCV_IC_INVALIDATE (TENSIX_CFG + 185 * 4)  /* bit per RISC: brisc, trisc0-2, ncrisc. Self-clearing */
#define CFG_PRNG_SEED           (TENSIX_CFG + 186 * 4)
#define CFG_RISC_PREFETCH_CTRL  (TENSIX_CFG + 208 * 4)
#define CFG_BANK_WORDS 224
#define CFG_GLOBAL_BASE 180
#define CFG_STATE_RESET 4

/* Overlay stream registers. Kernels use streams 8-39 as circular-buffer counters (regs 8 received, 10 acked). */
#define STREAM_REG(stream, reg) (0xFFB40000 + (stream) * 0x1000 + (reg) * 4)


INLINE void reset_cb_counters(void) {  /* every launch starts with empty CBs */
  for (u32 cb = 0; cb < 32; cb++) {
    write32(STREAM_REG(8 + cb, 8), 0);
    write32(STREAM_REG(8 + cb, 10), 0);
  }
}

INLINE void tensix_push(u32 instruction) { write32(INSTRN_BUF, instruction); }

#define ZEROACC_ALL     0x10180000  /* clear all of Dst */
#define SFPENCC_RESET   0x8A00300A  /* enable every SFPU lane, clear condition codes */
#define NOP             0x02000000
#define SFPLOADI_MINUS1 0x7100BF80  /* LREG0 = -1.0 (bf16 0xBF80) */
#define SFPCONFIG_L11   0x910000B0  /* LREG11 (constant) = LREG0 */
#define SEMINIT(sem)    (0xA3100000 | 1 << ((sem) + 2))  /* semaphore sem: max 1, value 0 */

/* Every launch starts from the same Tensix state: config zeroed (except the self-clearing icache invalidate and the
 * PRNG seed), Dst cleared, SFPU and semaphores reinitialised, CBs empty. BRISC runs this before releasing the others. */
INLINE void reset_tensix(void) {
  /* Any write to STATE_RESET_EN clears the bank's words [0, 180) in hardware.
   * Reset both banks, then clear the shared globals without touching icache invalidate or PRNG seed.
   * Blackhole cfg_defines.h: STATE_RESET_EN_ADDR32=4, CFG_STATE_SIZE=56 (128-bit units), globals at 180. */
  write32(TENSIX_CFG + CFG_STATE_RESET * 4, 0);
  write32(TENSIX_CFG + (CFG_BANK_WORDS + CFG_STATE_RESET) * 4, 0);
  for (u32 i = CFG_GLOBAL_BASE; i < 185; i++) write32(TENSIX_CFG + i * 4, 0);
  for (u32 i = 187; i < CFG_BANK_WORDS; i++) write32(TENSIX_CFG + i * 4, 0);
  tensix_push(ZEROACC_ALL);
  tensix_push(SFPENCC_RESET);
  tensix_push(NOP);
  tensix_push(SFPLOADI_MINUS1);
  tensix_push(SFPCONFIG_L11);
  write32(CFG_ECC_SCRUBBER, 0x803);  /* enable, scrub on error, delay 256 */
  tensix_push(SEMINIT(0));
  tensix_push(SEMINIT(1));
  tensix_push(SEMINIT(2));
  tensix_push(SEMINIT(7));
  reset_cb_counters();
  write32(CFG_RISC_PREFETCH_CTRL, 0x11F);  /* instruction prefetch on for all five RISCs, 8 requests */
}

/* Custom CSR 0x7c0, set once per RISC at boot as tt-metal does on Blackhole: bit 18 set on BRISC/NCRISC, clear on TRISCs. */
INLINE void configure_csr(int trisc) {
  u32 v = 2;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(v) : "memory");
  v = 1u << 18;
  fence();
  if (trisc) __asm__ volatile("csrc 0x7c0, %0" :: "r"(v) : "memory");
  else __asm__ volatile("csrs 0x7c0, %0" :: "r"(v) : "memory");
  v = 2;
  __asm__ volatile("csrc 0x7c0, %0" :: "r"(v) : "memory");
  fence();
  v = 8;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(v) : "memory");
}

INLINE void invalidate_icache(void) {
  write32(CFG_RISCV_IC_INVALIDATE, 0x1F);
  fence();
}

#endif
