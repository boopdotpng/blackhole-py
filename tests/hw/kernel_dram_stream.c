/* DRAM streaming kernel for BRISC (NoC 0) or NCRISC (NoC 1), TT_FW_RISC picks which. params: [bytes, brisc mode,
 * ncrisc mode, log2 page, repeats], mode 0 idle, 1 read DRAM -> L1, 2 write L1 -> DRAM. Each core and RISC streams its
 * own 16 MB of interleaved DRAM, two 64 KB batches in flight. */
#include "fw.h"
#define P(i) mmio_read32(L1_PARAM_BASE + 4 * (i))
#define BATCH (64u << 10)
#define BUF (0x40000u + TT_FW_RISC * 2 * BATCH)

KERNEL kernel_main(void) {
  u32 bytes = P(0), mode = P(1 + TT_FW_RISC), reps = P(4);
  if (mode) {
    noc_init();
    u32 me = noc_local_coordinate(0), slot = ((me & 63) * 16 + (me >> 6)) * 2 + TT_FW_RISC;
    u32 lo = slot << 24, hi = 0x80000000u | P(3) << 24 | slot >> 8;
    for (u32 r = 0; r < reps; r++) {
      for (u32 done = 0, half = 0; done < bytes; done += BATCH, half ^= 1) {
        noc_wait(1 + half, mode == 1);  /* this half's last read has landed, or its last write has left L1 */
        noc_move(mode == 2, lo, hi, done, MIN(BATCH, bytes - done), BUF + half * BATCH, 1 + half);
      }
    }
    noc_wait(1, 1);
    noc_wait(2, 1);
  }
  fence();
  JUMP(TT_FW_RISC ? FW_NCRISC_RETURN : FW_BRISC_RETURN);
}
