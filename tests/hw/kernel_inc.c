/* test kernel for BRISC: OUT = params[0] + 1 */
#include "fw.h"
#define OUT 0x100000u

KERNEL kernel_main(void) {
  mmio_write32(OUT, mmio_read32(L1_PARAM_BASE) + 1);
  fence();
  JUMP(FW_BRISC_RETURN);
}
