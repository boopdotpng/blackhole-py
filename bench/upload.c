// Weight upload without a DMA core: the first ACTIVE workers pull chunks from pinned host memory over PCIe into L1
// and write them to interleaved DRAM. Worker of rank r takes chunks r, r + ACTIVE, ... Two L1 slots per worker:
// the read of chunk k+1 overlaps the DRAM write of chunk k.
#include "crt0.h"

#define OUT  0x30000
#define BUF  0x100000

void brisc_step(void) {
  volatile u32 *arg = (volatile u32 *)STEP_ARGS;
  u32 src_lo = arg[0], src_hi = arg[1], dst_lo = arg[2], dst_hi = arg[3], size = arg[4], chunk = arg[5];
  u32 active = arg[6], cap = arg[7], host_lo = arg[8], host_hi = arg[9];
  u32 rank = worker_rank_row_major();
  u32 t0 = read32(WALL_CLOCK_L), bytes = 0;
  if (rank < active) {
    u32 at = rank * chunk, step = active * chunk;
    if (at < size) noc_move_paced(0, 0, src_lo, src_hi, at, MIN(size - at, chunk), BUF, 1, cap);
    for (u32 slot = 0; at < size; slot ^= 1) {
      u32 next = at + step, n = MIN(size - at, chunk);
      noc_wait(0, 1 + slot, 1);                              // chunk `at` is in L1
      if (next < size) {
        noc_wait(0, 3 + (slot ^ 1), 0);                      // the other slot's write has left L1
        noc_move_paced(0, 0, src_lo, src_hi, next, MIN(size - next, chunk), BUF + (slot ^ 1) * chunk, 1 + (slot ^ 1), cap);
      }
      noc_move_paced(0, 1, dst_lo, dst_hi, at, n, BUF + slot * chunk, 3 + slot, 0);
      bytes += n;
      at = next;
    }
    noc_wait(0, 3, 1);
    noc_wait(0, 4, 1);
  }
  write32(OUT, read32(WALL_CLOCK_L) - t0);
  write32(OUT + 4, bytes);
  fence();
  u32 off = rank * 64;
  noc_write_host(0, OUT, host_lo + off, host_hi + (host_lo + off < host_lo), 8);
}
