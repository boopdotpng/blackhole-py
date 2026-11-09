#include "queue.h"

u32 queue_fetch(u32 niu, u32 read, u32 local, u32 max) {
  u32 offset = read & (RING_SIZE - 1), pushed = read32(WPTR) - read;
  u32 bytes = MIN(pushed, MIN(RING_SIZE - offset, max));
  if (bytes) noc_read(niu, read32(RING_LO) + offset, read32(RING_HI), local, bytes);
  fence();
  return bytes;
}

/* NoC transfers need source and destination at the same offset mod 64, so stage at the target's offset. */
static u32 scratch(u32 niu, u32 lo) { return SCRATCH + niu * 0x80 + (lo & 63); }

static void store64(u32 niu, u32 lo, u32 hi, u32 value_lo, u32 value_hi) {
  u32 s = scratch(niu, lo);
  write32(s, value_lo);
  write32(s + 4, value_hi);
  fence();
  noc_write(niu, lo, hi, s, 8);
}

/* TIMESTAMP only reads the clock into a slot; the NoC writes go out later, in queue_flush: dispatch flushes while
 * the cores run an EXEC, and any queue flushes when it goes idle. STORE and WAIT flush and wait for the acks first,
 * so every timestamp lands before a later signal the host can observe. */
#define TID_STAMP 6
#define STAMP(niu, i) (STAMP_L1 + ((niu) * STAMP_SLOTS + (i)) * 64)

static u32 stamp_lo[2][STAMP_SLOTS], stamp_hi[2][STAMP_SLOTS], stamps[2], unacked[2];  /* unacked: sent since the last acked flush */

void queue_init(u32 niu) { stamps[niu] = unacked[niu] = 0; }

void queue_flush(u32 niu, u32 acked) {
  if (!stamps[niu] && !(acked && unacked[niu])) return;
  unacked[niu] = !acked;
  fence();
  for (u32 i = 0; i < stamps[niu]; i++)
    noc_move(niu, 1, stamp_lo[niu][i], stamp_hi[niu][i], 0, 8, STAMP(niu, i) + (stamp_lo[niu][i] & 63), TID_STAMP);
  stamps[niu] = 0;
  noc_wait(niu, TID_STAMP, acked);  /* sent out of the slots, so they can be reused */
}

void queue_idle(u32 niu) {
  if (stamps[niu]) queue_flush(niu, 0);
}

void queue_timestamp(u32 niu, u32 lo, u32 hi) {
  if (stamps[niu] == STAMP_SLOTS) queue_flush(niu, 0);
  u32 n = stamps[niu]++, s = STAMP(niu, n) + (lo & 63);
  write32(s, read32(WALL_CLOCK_L));  /* reading the low word latches the high one */
  write32(s + 4, read32(WALL_CLOCK_H));
  stamp_lo[niu][n] = lo;
  stamp_hi[niu][n] = hi;
}

void queue_signal_op(u32 niu, packet *p) {
  if (p->op == OP_TIMESTAMP) {
    queue_timestamp(niu, p->a_lo, p->a_hi);
    return;
  }
  queue_flush(niu, 1);
  if (p->op == OP_WAIT) {
    u32 s = scratch(niu, p->a_lo);
    for (;;) {
      noc_read(niu, p->a_lo, p->a_hi, s, 8);
      u32 lo = read32(s), hi = read32(s + 4);
      if (p->c ? hi == p->b_hi && lo == p->b_lo : hi > p->b_hi || (hi == p->b_hi && lo >= p->b_lo)) return;
    }
  } else if (p->op == OP_STORE) {
    store64(niu, p->a_lo, p->a_hi, p->b_lo, p->b_hi);
  } else {
    for (;;) {}
  }
}
