#include "fw.h"

#if TT_TRISC_ID == 0
#define SYNC 0x0069u
#elif TT_TRISC_ID == 1
#define SYNC 0x006Au
#else
#define SYNC 0x006Bu
#endif

static void initialize_tensix(void) {
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

static void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
  initialize_tensix();
  run_worker_kernel();
}

void firmware_boot(void) {
  configure_csr();
  initialize_tensix();
  mmio_write32(0xFFEF02E8u, 0);
  delay_600_cycles();
  mmio_write8(SYNC, 2);
  fence();
  launch_worker();
}

void firmware_resume_after_kernel(void) {
  mmio_write8(SYNC, 0);
  fence();
  launch_worker();
}
