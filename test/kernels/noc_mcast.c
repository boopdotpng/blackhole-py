// Isolate the resident multicast ABI from compiler scheduling and Tensix.
#include "common.h"
#define MCAST ((void (*)(u32,u32,u32,u32,u32,u32,u32))FN_NOC_MCAST)
#define INC ((void (*)(u32,u32,u32,u32))FN_NOC_INC)
#define WAIT ((void (*)(u32,u32,u32))FN_NOC_WAIT)
#define CTRL(axis) (MCAST_CTRL_BASE + (axis) * 0x100)
#define DATA(axis, slot) (0x20000 + (axis) * 0x10000 + (slot) * 0x8000)
#define RESULT 0x50000

__asm__(".section .entry, \"ax\", @progbits\n call body\n j _end\n");

static __attribute__((unused)) u32 pattern(u32 axis, u32 seq, u32 line, u32 i) {
  return (axis << 30) ^ (seq * 0x12345) ^ (line * 0x432100) ^ i;
}

#if ROLE < ROLE_TRISC0
static void produce(u32 axis, u32 seq, u32 wx, u32 wy) {
  u32 len = axis ? GROWS : GCOLS, me = axis ? wy : wx;
  if (me != seq % len) return;
  u32 base = CTRL(axis), slot = seq & 1, at = slot * 16;
  if (seq >= 2) {
    u32 need = read32(base + 0x60 + at) + len;
    WAIT_FAST(read32(base + 0x40 + at) >= need);
    write32(base + 0x60 + at, need);
  }
  u32 data = DATA(axis, slot), line = axis ? wx : wy;
  for (u32 i = 0; i < BYTES / 4; i++) write32(data + i * 4, pattern(axis, seq, line, i));
  write32(base + 0x20 + at, seq + 1);
  fence();
  u32 rect = axis ? wx | (wx << 12) | ((GROWS - 1) << 18) : (wy << 6) | ((GCOLS - 1) << 12) | (wy << 18);
  MCAST(axis, data, data, rect, BYTES, axis + 2, 1);
  MCAST(axis, base + 0x20 + at, base + at, rect, 4, axis + 2, 1);
  WAIT(axis, axis + 2, 0);
}
#endif

void body(void) {
  u32 wx = read32(WORKER_X), wy = read32(WORKER_Y);
#if ROLE == ROLE_TRISC0
  u32 errors = 0;
#endif
  for (u32 seq = 0; seq < ITERATIONS; seq++) {
#if ROLE == ROLE_BRISC
    if (AXES & 1) produce(0, seq, wx, wy);
#elif ROLE == ROLE_NCRISC
    if (AXES & 2) produce(1, seq, wx, wy);
    // Forward before waiting for consumption, then credit the *next* sender
    // of this ring slot. Even the current sender returns a credit.
    for (u32 axis = 0; axis < 2; axis++) if (AXES & (1 << axis)) {
      u32 base = CTRL(axis), len = axis ? GROWS : GCOLS;
      WAIT_FAST(read32(base + 0x90) > seq);
      if (seq + 2 < ITERATIONS) {
        u32 target = axis ? wx | (((seq + 2) % len) << 6) : ((seq + 2) % len) | (wy << 6);
        INC(1, base + 0x40 + (seq & 1) * 16, target, 4);
        WAIT(1, 4, 0);
      }
    }
#else
    for (u32 axis = 0; axis < 2; axis++) if (AXES & (1 << axis)) {
      u32 base = CTRL(axis), slot = seq & 1, data = DATA(axis, slot), line = axis ? wx : wy;
      WAIT_FAST(read32(base + slot * 16) > seq);
      for (u32 i = 0; i < BYTES / 4; i++) errors += read32(data + 4 * i) != pattern(axis, seq, line, i);
      fence();
      write32(base + 0x90, seq + 1);
      fence();
    }
  #endif
  }
#if ROLE == ROLE_TRISC0
  write32(RESULT, errors);
  write32(RESULT + 4, ITERATIONS);
#endif
}
