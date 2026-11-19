/* SFPU loop timing on one TRISC (sfpu.py: hazards, matrix and loadmacro timing). One launch = one sample.
 *
 * Port of the old build()/slope() kernels (test_sfpu_hazards.py, test_sfpu_matrix.py, test_sfpu_loadmacro.py):
 *     [cfg0 &= ~clear]  SETUP  drain  fence  li n  PROF_REC(start)
 *   1: BODY  addi n,n,-1  bnez n,1b          (BODY: 16 units of the case's words)
 *     TAIL_WORDS  PROF_DRAIN  PROF_REC(stop)  fence  [cfg0 restored]
 * The timed region (PROF_REC to PROF_REC) is one asm statement, instruction for instruction the old one (sfpu.h).
 *
 * Params: [0] iterations [1] cfg0 bits to clear (old TIMING_CLEAR_CFG0_BITS) [2] 1 = write [3] to the prefetch
 * control first (0 reproduces the old prefetch-off runs; the firmware restores 0x11F after the launch).
 * Time stamps at PROF0/PROF1 (LOG + 0xFC0/0xFC4). RES_AUX: see sfpu.h (cfg0 at entry, cfg0 while timing, prefetch control while timing). */
#include "sfpu.h"

enum { P_COUNT, P_CFG0_CLEAR, P_PREFETCH_WRITE, P_PREFETCH_VALUE };

#ifndef SETUP
#define SETUP
#endif
#ifdef TAIL_WORDS
#define TAIL ".word " XSTR(TAIL_WORDS) "\n"
#else
#define TAIL
#endif

KERNEL kernel_main(void) {
  record_config();
  if (PARAM(P_PREFETCH_WRITE)) {
    write32(CFG_RISC_PREFETCH_CTRL, PARAM(P_PREFETCH_VALUE));
    fence();
  }
  u32 clear = PARAM(P_CFG0_CLEAR), saved = 0;
  if (clear) __asm__ volatile("csrrc %0, 0x7c0, %1" : "=r"(saved) : "r"(clear) : "memory");
  write32(RES_AUX + 4 * AUX_CFG0_TIMED, read_cfg0());
  write32(RES_AUX + 4 * AUX_PREFETCH, read32(CFG_RISC_PREFETCH_CTRL));
  SETUP
  D
  fence();
  u32 n = PARAM(P_COUNT);
  __asm__ volatile(PROF_REC(PROF0)
                   "1:\n"
                   ".word " XSTR(BODY) "\n"
                   "addi %0, %0, -1\n"
                   "bnez %0, 1b\n"
                   TAIL
                   PROF_DRAIN(ROT_STALL_SYNC_SFPU)
                   PROF_REC(PROF1)
                   "fence\n" : "+r"(n) :: "t5", "t6", "memory");
  if (clear) __asm__ volatile("csrs 0x7c0, %0" :: "r"(saved) : "memory");
  probe_done();
}
