/* FW_x + 0 boots, FW_x + 4 is where kernels return to. Both reset sp (and gp on TRISC), which a kernel may clobber. */
#ifndef WORKER_H
#define WORKER_H
#include "hw.h"

/* Idle waits. Firmware only, so probe and user kernels (which include hw.h, not this) are not rebuilt when they change. */
/* Poll of an L1 word, back to back; the fence flushes the L0 data cache so each poll reads L1. Only where nothing else
 * on the core is using L1 (boot, BRISC waiting for GO after every RISC has returned): polling L1 while other RISCs,
 * the unpackers, packers or NoC work takes a large share of L1 bandwidth from them (sims/probes, run.py --quiet).
 * Idle TRISCs therefore wait without touching L1 (a blocking PCBuf read; BRISC blocks on their mailboxes). NCRISC has
 * neither, so NCRISC and BRISC waiting for it use WAIT_SLOW: an L1 poll every NCRISC_BACKOFF register-only iterations. */
#define WAIT_FAST(cond) do { while (!(cond)) fence(); fence(); } while (0)
#ifndef NCRISC_BACKOFF
#define NCRISC_BACKOFF 64
#endif
#define WAIT_SLOW(cond) do {                                                \
    while (!(cond)) {                                                       \
      fence();                                                              \
      u32 n_ = NCRISC_BACKOFF;                                              \
      __asm__ volatile("1: addi %0, %0, -1\n bnez %0, 1b" : "+r"(n_));      \
    }                                                                       \
    fence();                                                                \
  } while (0)

/* PCBufs (BabyRISCV/PCBufs.md): a FIFO from BRISC to each TRISC; a TRISC read of PC_BUF_BASE blocks until BRISC pushes.
 * (A BRISC read of PCBUF(i) is documented to block until TRISC i is idle in that read, but it returned before a launched
 * TRISC's kernel had finished, so "done" goes through the mailboxes instead.) */
#define PC_BUF_BASE  0xFFE80000
#define PCBUF(i)     (PC_BUF_BASE + (i) * 0x10000)
/* Mailboxes (BabyRISCV/Mailboxes.md): 4-deep FIFOs between BRISC and the TRISCs; a read of an empty one blocks. */
#define MAILBOX_TO_BRISC   0xFFEC0000                     /* TRISC: write = this TRISC -> BRISC */
#define MAILBOX_FROM(i)    (0xFFEC1000 + (i) * 0x1000)    /* BRISC: read = TRISC i -> BRISC */
/* Not used for NCRISC: the PIC software IRQ registers (PIC.md, read returns the value and clears it) as single-slot
 * queues. Polling one back to back slowed the other RISC's NIU register accesses ~5%, and with a backoff between polls
 * a BRISC write of the launch token was lost (NCRISC never saw it; the core hung). */

#define STR_(x) #x
#define STR(x) STR_(x)

#define FIRMWARE_ENTRY(setup)                       \
  __asm__(".section .entry, \"ax\", @progbits\n"    \
          "j 1f\n"                                  \
          setup "j firmware_resume\n"               \
          "1: " setup "j firmware_boot\n");

#define SET_SP(stack) "li sp, " STR(stack) "\n"
#define SET_GP(gp) "li gp, " STR(gp) "\n"

#endif
