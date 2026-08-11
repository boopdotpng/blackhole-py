#include "fw.h"

#define SYNC 0x0068u

static void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
  u32 launch_delay = 10000;
  __asm__ volatile(
    "1: addi %0, %0, -1\n"
    "bnez %0, 1b\n"
    : "+r"(launch_delay)
    :
    : "memory"
  );
  run_worker_kernel();
}

void firmware_boot(void) {
  configure_csr();
  mmio_write8(SYNC, 2);
  fence();
  launch_worker();
}

void firmware_resume_after_kernel(void) {
  mmio_write8(SYNC, 0);
  fence();
  launch_worker();
}
