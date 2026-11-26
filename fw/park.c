// Appended after each RISC's kernel body: drain outstanding work, then spin forever.
#include "common.h"

__asm__(".section .entry, \"ax\", @progbits\n"
#if ROLE >= ROLE_TRISC0
        "li t0, " STR(COPROCESSOR_DONE_CHECK) "\n"
        "sw zero, 0(t0)\n"
        "lw t1, 0(t0)\n"
        "andi t1, t1, 0\n"
#endif
        "fence\n"
        "1: j 1b\n");
