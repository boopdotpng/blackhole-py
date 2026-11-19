// T2's 128-bit RISC-V vector unit processes one stripe of value channels at a time.
// Keep the 32 independent dot products in registers across all 128 key channels.
#include <riscv_vector.h>
#include "worker.h"
#include "state.h"

KERNEL kernel_main(void) {
  Scratch *s = (Scratch *)SCRATCH_ADDR;
#if PROMPT
  unsigned rows = read32(L1_PARAM_BASE + 4 * ROWS_SLOT);
#else
  unsigned rows = 1;
#endif
  unsigned offset = PROMPT ? (read32(WORKER_ID) % 2) * 64 : 0;
  for (unsigned row = 0; row < rows; row++) {
    unsigned live = read32(PC_BUF_BASE);
    fence();
    size_t vl = __riscv_vsetvl_e32m8(32);
    for (int block = 0; block < (PROMPT ? 2 : 4); block++) {
      vfloat32m8_t sum = __riscv_vfmv_v_f_f32m8(0, vl);
      if (live)
        for (int k = 0; k < 128; k++) {
          vfloat32m8_t old = __riscv_vle32_v_f32m8(s->state[block][k], vl);
          sum = __riscv_vfmacc_vf_f32m8(sum, s->act[1][k], old, vl);
        }
      vfloat32m8_t value = __riscv_vle32_v_f32m8(s->act[2] + offset + 32 * block, vl);
      value = __riscv_vfnmsac_vf_f32m8(value, s->decay, sum, vl);
      vfloat32m8_t delta = __riscv_vfmul_vf_f32m8(value, s->beta, vl);
      vfloat32m8_t context = __riscv_vfmv_v_f_f32m8(0, vl);
      for (int k = 0; k < 128; k++) {
        vfloat32m8_t next = __riscv_vfmul_vf_f32m8(delta, s->act[1][k], vl);
        if (live) {
          vfloat32m8_t old = __riscv_vle32_v_f32m8(s->state[block][k], vl);
          next = __riscv_vfmacc_vf_f32m8(next, s->decay, old, vl);
        }
        __riscv_vse32_v_f32m8(s->state[block][k], next, vl);
        context = __riscv_vfmacc_vf_f32m8(context, s->act[0][k], next, vl);
      }
      __riscv_vse32_v_f32m8(s->context + 32 * block, context, vl);
    }
    fence();
    write32(MAILBOX_TO_BRISC, 1);
  }
  JUMP(FW_TRISC2 + 4);
}
