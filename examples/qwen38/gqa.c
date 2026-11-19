// BRISC gathers one block of cached keys and values. TRISC2 owns the online softmax for this query.
#include <riscv_vector.h>
#include "worker.h"
#include "head_math.h"
#include "gqa.h"

static inline vfloat32m4_t expand_bf16(const bf16 *p, size_t vl) {
  vuint16m2_t bits = __riscv_vle16_v_u16m2(p, vl);
  return __riscv_vreinterpret_v_u32m4_f32m4(__riscv_vsll_vx_u32m4(__riscv_vzext_vf2_u32m4(bits, vl), 16, vl));
}

KERNEL kernel_main(void) {
  Scratch *s = (Scratch *)SCRATCH_ADDR;
  u32 base = read32(L1_PARAM_BASE + 4 * POS_SLOT), rows = read32(L1_PARAM_BASE + 4 * ROWS_SLOT);
  size_t vl = __riscv_vsetvl_e32m4(16);
  for (u32 row = read32(WORKER_ID) / 24; row < rows; row += GRID / 24) {
    u32 pos = base + row;
    float maximum = 0, total = 0;
    for (u32 first = 0; first <= pos; first += KEY_BLOCK) {
      u32 count = read32(PC_BUF_BASE);
      fence();
      if (!first) {
        for (int i = 0; i < 256; i += 16) {
          __riscv_vse32_v_f32m4(s->query + i, expand_bf16(s->q + i, vl), vl);
          __riscv_vse32_v_f32m4(s->accum + i, __riscv_vfmv_v_f_f32m4(0, vl), vl);
        }
      }
      for (u32 j = 0; j < count; j++) {
        // BF16 products are exact in FP32. Sum in key-channel order to match the scalar decoder.
        vfloat32m1_t sum = __riscv_vfmv_v_f_f32m1(0, 1);
        for (int i = 0; i < 256; i += 16) {
          vfloat32m4_t q = __riscv_vle32_v_f32m4(s->query + i, vl);
          vfloat32m4_t products = __riscv_vfmul_vv_f32m4(q, expand_bf16(s->keys[j] + i, vl), vl);
          sum = __riscv_vfredosum_vs_f32m4_f32m1(products, sum, vl);
        }
        float score = __riscv_vfmv_f_s_f32m1_f32(sum) * 0.0625f;
        float next = (first || j) && maximum > score ? maximum : score;
        float prev = first || j ? exponential(maximum - next) : 0, w = exponential(score - next);
        for (int i = 0; i < 256; i += 16) {
          vfloat32m4_t acc = __riscv_vfmul_vf_f32m4(expand_bf16(s->values[j] + i, vl), w, vl);
          acc = __riscv_vfmacc_vf_f32m4(acc, prev, __riscv_vle32_v_f32m4(s->accum + i, vl), vl);
          __riscv_vse32_v_f32m4(s->accum + i, acc, vl);
        }
        total = total * prev + w;
        maximum = next;
      }
      s->total = total;
      fence();
      write32(MAILBOX_TO_BRISC, 1);
    }
  }
  JUMP(FW_TRISC2 + 4);
}
