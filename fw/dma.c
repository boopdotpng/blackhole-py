#include "queue.h"

#define NIU DMA_ENGINE
#define STAGING(i) (DMA_STAGING + DMA_ENGINE * DMA_STAGING_STRIDE + (i) * DMA_BATCH)
#define PACKETS STAGING(2)

/* tids 1, 2: reads into staging 0, 1. tids 3, 4: writes out of them */
static void copy(packet *p) {
  u32 size = p->c, at = DMA_ENGINE * DMA_BATCH;
  if (at >= size) return;
  noc_move(NIU, 0, p->b_lo, p->b_hi, at, MIN(size - at, DMA_BATCH), STAGING(0), 1);
  for (u32 buf = 0;; buf ^= 1) {
    u32 next = at + 2 * DMA_BATCH;
    noc_wait(NIU, 1 + buf, 1);
    if (next < size) {
      noc_wait(NIU, 3 + (buf ^ 1), 0);
      noc_move(NIU, 0, p->b_lo, p->b_hi, next, MIN(size - next, DMA_BATCH), STAGING(buf ^ 1), 1 + (buf ^ 1));
    }
    noc_move(NIU, 1, p->a_lo, p->a_hi, at, MIN(size - at, DMA_BATCH), STAGING(buf), 3 + buf);
    if (next >= size) break;
    at = next;
  }
  noc_wait(NIU, 3, 1);
  noc_wait(NIU, 4, 1);
}

KERNEL kernel_main(void) {
  noc_init(NIU);
  queue_init(NIU);
  for (u32 read = 0, done = 0;;) {
    u32 packets = PACKETS + (read & 63);
    u32 bytes = queue_fetch(NIU, read, packets, DMA_PACKETS_MAX);
    if (!bytes && DMA_ENGINE == 0) queue_idle(NIU);
    for (u32 offset = 0; offset < bytes; offset += PACKET) {
      packet *p = (packet *)(packets + offset);
      if (p->op == OP_COPY) copy(p);
      else if (DMA_ENGINE == 0) queue_signal_op(NIU, p);
      write32(DMA_DONE + DMA_ENGINE * 4, ++done);
      fence();
      while ((int)(read32(DMA_DONE + (DMA_ENGINE ^ 1) * 4) - done) < 0) fence();
      if (DMA_ENGINE == 0) write32(RPTR, read + offset + PACKET);
    }
    read += bytes;
  }
}
