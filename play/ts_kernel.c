/* Each RISC appends N events (128-bit mode) to the tile's hardware timestamp stream, then times K more stamps. */
#include "hw.h"
#define TS 0xFFB121FC
KERNEL kernel_main(void) {
  for (u32 i = 0; i < N; i++) write32(TS, (ROLE << 24) | (i << 3));  /* low 3 bits 0: 128-bit event */
  /* cost: K back-to-back stamps, bracketed by wall clock reads; result to L1 RESULT + 16*ROLE */
  u32 t0 = read32(WALL_CLOCK_L);
  for (u32 i = 0; i < K; i++) write32(TS, (ROLE << 24) | (0xFFF << 3));
  u32 t1 = read32(WALL_CLOCK_L);
  for (u32 i = 0; i < K; i++) __asm__ volatile("nop");
  u32 t2 = read32(WALL_CLOCK_L);
  write32(RESULT + 16 * ROLE, t1 - t0);
  write32(RESULT + 16 * ROLE + 4, t2 - t1);
  JUMP(RET);
}
