#pragma once

typedef unsigned char u8;
typedef unsigned int u32;

// DMA service core L1 layout, also read by fw/__init__.py
#define STACK_TOP                0xFFB01FF0
#define PACKET                   32
#define DMA_DEPTH                4

#define SVC_NCRISC_SYNC          0x10        // NCRISC boot handshake (writes 2 when up)
#define SVC_COPY_GO              0x20        // BRISC -> NCRISC: copy sequence number to start
#define SVC_COPY_DONE            0x30        // NCRISC -> BRISC: copy sequence number finished
#define SVC_PIPE_PROD            0x40        // DRAM-source copy: chunks BRISC has staged
#define SVC_PIPE_CONS            0x50        // DRAM-source copy: chunks NCRISC has written out

#define SVC_STATE                0x80        // host-initialised block
#define SVC_WPTR                 SVC_STATE           // latest host-submitted DMA sequence
#define SVC_SIGNAL               (SVC_STATE + 8)     // host address of the completion counter
#define SVC_COPY_DESC            (SVC_STATE + 0x30)
#define SVC_SCRATCH              (SVC_STATE + 0x80)
#define SVC_STATE_SIZE           0x100

#define SVC_BRISC_BASE           0x200
#define SVC_BRISC_SIZE           0x3E00
#define SVC_NCRISC_BASE          0x4000
#define SVC_NCRISC_SIZE          0x4000
#define SVC_PACKETS              0x9000      // host-written DMA descriptors
#define SVC_DMA_STAGING          0x10000     // 2 engines x DMA_SLOTS x DMA_BATCH
#ifndef DMA_BATCH
#define DMA_BATCH                0x20000
#endif
#ifndef DMA_SLOTS
#define DMA_SLOTS                4           // per engine; reads use tids 8.., writes the DMA_SLOTS above
#endif

_Static_assert((SVC_SCRATCH & 63) == 0, "SVC_SCRATCH must be 64-aligned");
_Static_assert(SVC_STATE + SVC_STATE_SIZE <= SVC_BRISC_BASE, "service state overlaps BRISC image");
_Static_assert(SVC_PACKETS + PACKET * DMA_DEPTH <= SVC_DMA_STAGING, "packet buffer overlaps DMA staging");
_Static_assert(DMA_SLOTS >= 2 && 8 + 2 * DMA_SLOTS <= 16, "DMA ring needs 2..4 slots: 2 NoC tids each, from tid 8");
_Static_assert(SVC_DMA_STAGING + 2 * DMA_SLOTS * DMA_BATCH <= 0x180000, "DMA staging exceeds L1");

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

#define TDMA_CLK_GATE_EN         0xFFB11024
#define SOFT_RESET               0xFFB121B0
#define RESET_BRISC              (1u << 11)
#define RESET_NCRISC             (1u << 18)
#define RESET_ALL                0x47800u
#define NCRISC_RESET_PC          0xFFB12238
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223C
#define DEST_CG_CTRL             0xFFB12240

#define TENSIX_CFG               0xFFEF0000
#define CFG_RISCV_IC_INVALIDATE  (TENSIX_CFG + 185 * 4)

INLINE void enable_clock_gating(void) {
  write32(DEST_CG_CTRL, 0);
  write32(TDMA_CLK_GATE_EN, 0x3F);
  for (u32 niu = 0; niu < 2; niu++) {
    u32 cfg = 0xFFB20100 + niu * 0x10000;
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
