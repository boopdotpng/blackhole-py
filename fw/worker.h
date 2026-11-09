/* FW_x + 0 boots, FW_x + 4 is where kernels return to. Both reset sp (and gp on TRISC), which a kernel may clobber. */
#ifndef WORKER_H
#define WORKER_H
#include "hw.h"

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
