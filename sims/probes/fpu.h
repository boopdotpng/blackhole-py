/* Generic Tensix helpers for the FPU probes (sims/probes/fpu.py, k_fpu.c). TRISC roles only.
 *
 * Nothing here blocks without a bound except a Tensix push into a full FIFO (a RISC store stalls until the
 * coprocessor accepts it; that only happens if the Tensix thread itself is wedged).
 *
 * Bounded completion (tt_fence): push STALLWAIT(B1 SYNC, C1|C2|C4|C11) then SEMPOST(sem), and poll the semaphore
 * from the RISC with WAIT_UNTIL. The semaphore is taken back with a RISC-side SEMGET (store of 1 to SemaphoreAccess).
 * tensix_drain (PC_BUF_SYNC load) would wait forever on a wedged thread; this gives up and reports the site.
 * Semaphore per role: trisc0 4, trisc1 6, trisc2 3 (llama kernels use 1, 2, 5, 7; reset_tensix SEMINITs all 8 to
 * max 1, value 0 before every launch). */
#ifndef FPU_H
#define FPU_H
#include "probe.h"

/* ---- Tensix words (unrotated). Field layouts from ttrv/isa.py (tt-llk ckernel_ops.h) ---- */
#define TT_OP(op)              ((u32)(op) << 24)
#define TT_NOP                 TT_OP(0x02)
#define TT_STALLWAIT(stall, wait) (TT_OP(0xa2) | (u32)(stall) << 15 | (u32)(wait))
#define TT_SEMPOST(mask)       (TT_OP(0xa4) | (u32)(mask) << 2)
#define TT_SETC16(reg, v)      (TT_OP(0xb2) | (u32)(reg) << 16 | (u32)(v))

/* STALLWAIT block bits (Blackhole) */
#define STALL_SYNC  (1u << 1)
#define STALL_MATH  (1u << 6)
#define STALL_CFG   (1u << 7)
#define STALL_SFPU  (1u << 8)
/* STALLWAIT condition bits (Blackhole numbering) */
#define WAIT_UNPACK0 (1u << 1)
#define WAIT_UNPACK1 (1u << 2)
#define WAIT_PACK    (1u << 3)
#define WAIT_MATH    (1u << 4)
#define WAIT_SRCA_VLD (1u << 7)
#define WAIT_SRCB_VLD (1u << 8)
#define WAIT_SFPU    (1u << 11)
#define WAIT_IDLE    (WAIT_UNPACK0 | WAIT_UNPACK1 | WAIT_MATH | WAIT_SFPU)

/* ---- MMIO ---- */
#define SEM_ACCESS(i)   (0xFFE80020u + 4u * (i))  /* PC_BUF SemaphoreAccess[i]: load = value, store 1 = get, 0 = post */
#define PC_BUF_MOP_SYNC 0xFFE80008u               /* MOPExpanderDoneCheck */
#define MOP_CFG(i)      (0xFFB80000u + 4u * (i))  /* this thread's MOP template words, write-only */
#define DST_RISC        0xFFBD8000u               /* Dst as seen by RISCV T0/T1/T2 (Dst.md "RISCV access") */
#define CFG_WORD(i)     (TENSIX_CFG + 4u * (i))

#ifndef TT_SEM
#define TT_SEM 6
#endif

/* Wait (bounded) until every instruction this thread pushed so far has left the unpackers, FPU and SFPU. */
INLINE void tt_fence(u32 site) {
  tensix_push(TT_STALLWAIT(STALL_SYNC, WAIT_IDLE));
  tensix_push(TT_SEMPOST(1u << TT_SEM));
  WAIT_UNTIL(read32(SEM_ACCESS(TT_SEM)) != 0, site);
  write32(SEM_ACCESS(TT_SEM), 1);
  WAIT_UNTIL(read32(SEM_ACCESS(TT_SEM)) == 0, site);
}

/* tt_fence, returning the wall clock read as soon as the semaphore post is seen (the end time of a timed region). */
INLINE u32 tt_fence_time(u32 site) {
  tensix_push(TT_STALLWAIT(STALL_SYNC, WAIT_IDLE));
  tensix_push(TT_SEMPOST(1u << TT_SEM));
  WAIT_UNTIL(read32(SEM_ACCESS(TT_SEM)) != 0, site);
  u32 t = now();
  write32(SEM_ACCESS(TT_SEM), 1);
  WAIT_UNTIL(read32(SEM_ACCESS(TT_SEM)) == 0, site);
  return t;
}

/* After a fence the expander is idle, so this load returns at once; it orders MOP_CFG writes after it. */
INLINE void mop_sync(void) {
  write32(PC_BUF_MOP_SYNC, 0);
  u32 v = read32(PC_BUF_MOP_SYNC);
  __asm__ volatile("andi %0, %0, 0" : "+r"(v));
}

/* RISC config write with read-back (the read orders it before later pushes). Only with the thread fenced. */
INLINE void cfg_rmw(u32 word, u32 mask, u32 value) {
  u32 v = read32(CFG_WORD(word));
  write32(CFG_WORD(word), (v & ~mask) | (value & mask));
  (void)read32(CFG_WORD(word));
}

/* Dst through the RISC window. 32-bit view needs RISC_DEST_ACCESS_CTRL_SEC<thread>.fmt = 0 (fp32), 16-bit view
 * fmt 2 (fp16) or 3 (bf16); 16-bit accesses must be sh/lhu on T0/T1. Row is a Dst32b or Dst16b row. */
INLINE void dst_write32(u32 row, u32 col, u32 v) { write32(DST_RISC + 4u * (row * 16u + col), v); }
INLINE u32 dst_read32(u32 row, u32 col) { return read32(DST_RISC + 4u * (row * 16u + col)); }
INLINE void dst_write16(u32 row, u32 col, u32 v) { *(volatile unsigned short *)(DST_RISC + 2u * (row * 16u + col)) = (unsigned short)v; }
INLINE u32 dst_read16(u32 row, u32 col) { return *(volatile unsigned short *)(DST_RISC + 2u * (row * 16u + col)); }

INLINE void spin(u32 cycles) {
  u32 until = now() + cycles;
  while ((int)(now() - until) < 0) {}
}

#endif
