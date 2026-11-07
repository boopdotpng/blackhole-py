/* The COPY queue on DMA_CORE. BRISC and NCRISC each fetch every packet. A COPY is cut into DMA_BATCH byte batches
 * and engine k % 2 moves batch k. WAIT, STORE and TIMESTAMP run on BRISC only. Both engines finish a packet before
 * either starts the next, so a STORE covers both engines' writes. */
#include "fw.h"

#define HALF(h) (DMA_STAGING + TT_FW_RISC * DMA_STAGING_STRIDE + (h) * DMA_BATCH)
#define PACKETS HALF(2)

/* COPY [op, dst, src, size]. src and dst are 64-byte aligned. A batch is read into one staging half (tid 1 + half)
 * while the previous one is written out of the other (tid 3 + half). */
static void copy(volatile u32 *p) {
  u32 size = p[6], batch = TT_FW_RISC * DMA_BATCH;
  if (batch >= size) return;
  noc_move(0, p[4], p[5], batch, MIN(size - batch, DMA_BATCH), HALF(0), 1);
  for (u32 half = 0;; half ^= 1) {
    u32 next = batch + 2 * DMA_BATCH;
    noc_wait(1 + half, 1);
    if (next < size) {
      noc_wait(3 + (half ^ 1), 0);
      noc_move(0, p[4], p[5], next, MIN(size - next, DMA_BATCH), HALF(half ^ 1), 1 + (half ^ 1));
    }
    noc_move(1, p[2], p[3], batch, MIN(size - batch, DMA_BATCH), HALF(half), 3 + half);
    if (next >= size) break;
    batch = next;
  }
  noc_wait(3, 1);
  noc_wait(4, 1);
}

KERNEL kernel_main(void) {
  noc_init();
  for (u32 read = 0, done = 0;;) {
    u32 packets = PACKETS + (read & 63);  /* a NoC read lands at the ring offset mod 64 */
    u32 bytes = fetch(read, packets, DMA_PACKETS_MAX);
    for (u32 offset = 0; offset < bytes; offset += PACKET) {
      volatile u32 *p = (volatile u32 *)(packets + offset);
      if (p[0] == OP_COPY) copy(p);
      else if (TT_FW_RISC == 0) common_op(p);
      done++;
      mmio_write32(DMA_DONE + TT_FW_RISC * 4, done);
      fence();
      while ((int)(mmio_read32(DMA_DONE + (TT_FW_RISC ^ 1) * 4) - done) < 0) fence();
      if (TT_FW_RISC == 0) mmio_write32(RPTR, read + offset + PACKET);
    }
    read += bytes;
  }
}
