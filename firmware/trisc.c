#include "fw.h"

#ifndef TT_TRISC_ID
#error "compile trisc.c with -DTT_TRISC_ID=0, 1, or 2"
#elif TT_TRISC_ID == 0
#define SYNC 0x0069u
#elif TT_TRISC_ID == 1
#define SYNC 0x006Au
#elif TT_TRISC_ID == 2
#define SYNC 0x006Bu
#else
#error "TT_TRISC_ID must select TRISC 0, 1, or 2"
#endif

TT_INLINE void initialize_tensix(void) {
  zero_words(0xFFE00000u, 64);
}

static void delay_600_cycles(void) {
  u32 remaining = 600;
  __asm__ volatile(
    "1: addi %0, %0, -1\n"
    "bnez %0, 1b\n"
    : "+r"(remaining)
  );
}

static __attribute__((noreturn)) void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
  initialize_tensix();
  run_worker_kernel();
}

__attribute__((noreturn)) void firmware_boot(void) {
  configure_csr();
  /* The register file is initialized immediately before every kernel launch. */
  mmio_write32(0xFFEF02E8u, 0);
  delay_600_cycles();
  mmio_write8(SYNC, 2);
  fence();
  launch_worker();
}

__attribute__((noreturn)) void firmware_resume_after_kernel(void) {
  mmio_write8(SYNC, 0);
  fence();
  launch_worker();
}
