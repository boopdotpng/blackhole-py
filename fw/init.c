/* Run once on every worker at startup, as an ordinary BRISC kernel. */
#include "hw.h"

KERNEL kernel_main(void) {
  write32(DEST_CG_CTRL, 0);
  write32(TDMA_CLK_GATE_EN, 0x3F);
  for (u32 niu = 0; niu < 2; niu++) {  /* NIU_CFG_0 and ROUTER_CFG_0 bit 0: clock gating */
    u32 cfg = 0xFFB20100 + niu * 0x10000;
    write32(cfg, read32(cfg) | 1);
    write32(cfg + 4, read32(cfg + 4) | 1);
  }
  JUMP(FW_BRISC + 4);
}
