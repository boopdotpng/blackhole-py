/* First code on ERISC1 (E1) of an Ethernet tile. It touches only its own L1 block at STATUS: no Ethernet, no
   NoC, and no registers except its stack. ERISC0 keeps running the vendor base firmware.
   STATUS[0] magic, [1] loop counter, [2] host writes a value, [3] E1 echoes it back + 1. */
#include "hw.h"

#define STATUS 0x30000
#define MAGIC  0xE1A1C0DE

__attribute__((noreturn)) static void main_loop(void) {
  volatile u32 *s = (volatile u32 *)STATUS;
  s[0] = MAGIC;
  for (u32 n = 1;; n++) {
    s[1] = n;
    s[3] = s[2] + 1;
  }
}

/* Reset lands here with no stack; give it one in L1 just below STATUS. */
__attribute__((section(".entry"), naked, noreturn)) void _start(void) {
  __asm__ volatile("li sp, %0\n j %1" :: "i"(STATUS - 16), "i"(main_loop));
}
