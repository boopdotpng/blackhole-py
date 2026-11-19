/* RISC-V core timing (riscv.py): one fixed asm body in a counted loop, timed on the wall clock, all in one launch.
 *
 * riscv.py passes the asm as string defines (each a C string literal of newline-terminated lines):
 *   RV_INIT    once per launch, before any sample (e.g. write a pointer chain into L1 or local RAM)
 *   RV_SETUP   before every sample, untimed (initial register values)
 *   RV_BODY    the measured loop body
 *   RV_FINISH  after the loop, timed (default: store a1 to the sink, so the last result must exist)
 *   RV_TAIL    after the timed region, never falls through (subroutines for the call cases)
 * plus CFG0_SET / CFG0_CLEAR (cfg0 bits changed for the whole launch, restored before returning), RESTORE_ADDR (an
 * MMIO word saved before and written back after), COUNT0 (iterations of the first point; then x2, x4) and RV_PAIR
 * (no loop: the timed region is just RV_BODY between two clock reads).
 *
 * Timed region, exactly (verified with llvm-objdump in riscv.py --disasm):
 *     fence ; lw t1, 0(t0) ; 90: BODY ; addi a0,a0,-1 ; bnez a0,90b ; FINISH ; fence ; lw t2, 0(t0)
 * t0 = WALL_CLOCK_L, a0 = iterations, s11 = sink address. Bodies own a1-a7, t3-t6, s1-s10, ra and f0-f7; labels
 * 1-89 are free for bodies and tails (90 and 99 are the harness's).
 *
 * LOG: [0] points [1] samples [2] cfg0 at entry [3] cfg0 while measuring [4] pmacfg0 [5] pmacfg1 [6] misa [7] mstatus,
 *      then per point, per sample: t_start, t_end, a1 after FINISH. Sample 0 of every point is the warmup.
 * Nothing here waits on another agent: the only loads that can stall (PC_BUF sync, semaphores) return once this
 * thread's Tensix work is done, and the kernel never pushes work that cannot finish. */
#include "probe.h"

#ifndef RV_INIT
#define RV_INIT ""
#endif
#ifndef RV_SETUP
#define RV_SETUP ""
#endif
#ifndef RV_BODY
#define RV_BODY ""
#endif
#ifndef RV_FINISH
#define RV_FINISH "sw a1, 0(s11)\n"
#endif
#ifndef RV_TAIL
#define RV_TAIL ""
#endif
#ifndef CFG0_SET
#define CFG0_SET 0
#endif
#ifndef CFG0_CLEAR
#define CFG0_CLEAR 0
#endif
#ifndef COUNT0
#define COUNT0 64
#endif
#define POINTS 3
#define SAMPLES 8
#define HEADER 8
#define SINK_ADDR (RES + 0x10)  /* RES_AUX */

#define STR_(x) #x
#define STR(x) STR_(x)
/* F, Zba, Zbb and Zaamo are implemented on every core (tt-isa-documentation InstructionSet.md); fw builds rv32im_zicsr */
#define ARCH ".option push\n.option arch, +f, +zba, +zbb, +zaamo\n"
#define CLOBBERS "ra", "t0", "t3", "t4", "t5", "t6", "a2", "a3", "a4", "a5", "a6", "a7", \
                 "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "memory"

#define CSR_READ(csr) ({ u32 v_; __asm__ volatile("csrr %0, " STR(csr) : "=r"(v_)); v_; })

static __attribute__((noinline)) void sample(u32 count, u32 at) {
  register u32 n __asm__("a0") = count;
  register u32 t_start __asm__("t1"), t_end __asm__("t2"), x __asm__("a1");
  __asm__ volatile(ARCH
                   "li t0, 0xFFB121F0\n"
                   "li s11, " STR(SINK_ADDR) "\n"
                   RV_SETUP
                   "fence\n"
                   "lw t1, 0(t0)\n"
#ifdef RV_PAIR
                   RV_BODY
#else
                   "90:\n"
                   RV_BODY
                   "addi a0, a0, -1\n"
                   "bnez a0, 90b\n"
                   RV_FINISH
                   "fence\n"
#endif
                   "lw t2, 0(t0)\n"
                   "j 99f\n"
                   RV_TAIL
                   "99:\n"
                   ".option pop\n"
                   : "+r"(n), "=&r"(t_start), "=&r"(t_end), "=&r"(x)
                   :
                   : CLOBBERS);
  log_word(at, t_start);
  log_word(at + 1, t_end);
  log_word(at + 2, x);
}

static __attribute__((noinline)) void init(void) {
  __asm__ volatile(ARCH RV_INIT "fence\n.option pop\n" ::: "a1", CLOBBERS);
}

KERNEL kernel_main(void) {
  u32 cfg0 = CSR_READ(0x7c0);
  log_word(0, POINTS);
  log_word(1, SAMPLES);
  log_word(2, cfg0);
  log_word(4, CSR_READ(0x7c1));
  log_word(5, CSR_READ(0x7c2));
  log_word(6, CSR_READ(0x301));
  log_word(7, CSR_READ(0x300));
#ifdef RESTORE_ADDR
  u32 saved = read32(RESTORE_ADDR);
#endif
  fence();
  if (CFG0_SET) __asm__ volatile("csrs 0x7c0, %0" :: "r"(CFG0_SET) : "memory");
  if (CFG0_CLEAR) __asm__ volatile("csrc 0x7c0, %0" :: "r"(CFG0_CLEAR) : "memory");
  fence();
  log_word(3, CSR_READ(0x7c0));
  init();
  u32 at = HEADER;
#pragma clang loop unroll(disable)
  for (u32 p = 0; p < POINTS; p++) {
#pragma clang loop unroll(disable)
    for (u32 s = 0; s < SAMPLES; s++, at += 3) sample((u32)COUNT0 << p, at);
  }
  fence();
  __asm__ volatile("csrw 0x7c0, %0" :: "r"(cfg0) : "memory");
  fence();
#ifdef RESTORE_ADDR
  write32(RESTORE_ADDR, saved);
  fence();
#endif
  write32(RES_COUNT, at);
  probe_done();
}
