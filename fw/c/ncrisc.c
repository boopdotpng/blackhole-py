#include "fw.h"

#define SYNC 0x0068u

static void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
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
