/* Instruction-cache cost (icache.py; port of the old test_icache.py build()). Any role; one launch = one sample.
 *
 *     li n, passes ; li x, 0 ; PROF_REC(start)
 *   1: N x BODY_INSN ; addi n,n,-1 ; bnez n,1b
 *     fence (addi)  |  PROF_DRAIN (Tensix bodies)
 *     PROF_REC(stop) ; fence          (one asm statement, instruction for instruction the old kernel: sfpu.h)
 * KIND 0: addi x, x, 1     KIND 1: SFPNOP (.ttinsn)     KIND 2: TTNOP (.ttinsn). N: body length (define).
 * Params: [0] passes. Time stamps at PROF0/PROF1 (LOG + 0xFC0/0xFC4). RES_AUX: cfg0, prefetch control (not on NCRISC), see sfpu.h. */
#include "sfpu.h"

#if KIND == 0
#define END "fence\n"
#else
#define END PROF_DRAIN(ROT_STALL_SYNC_SFPU)
#endif

#if KIND == 0
#define BODY_INSN "addi %1, %1, 1\n"
#elif KIND == 1
#define BODY_INSN ".word 0x3c000002\n"  /* SFPNOP 0x8F000000, rotated */
#elif KIND == 2
#define BODY_INSN ".word 0x08000000\n"  /* NOP 0x02000000, rotated */
#else
#error "KIND must be 0, 1 or 2"
#endif

KERNEL kernel_main(void) {
  record_config();
  u32 n = PARAM(0), x = 0;
  __asm__ volatile("li %1, 0\n"
                   PROF_REC(PROF0)
                   "1:\n"
                   ".rept " XSTR(N) "\n" BODY_INSN ".endr\n"
                   "addi %0, %0, -1\n"
                   "bnez %0, 1b\n"
                   END
                   PROF_REC(PROF1)
                   "fence\n" : "+r"(n), "=&r"(x) :: "t5", "t6", "memory");
  probe_done();
}
