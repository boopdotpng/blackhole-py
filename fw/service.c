#include "noc.h"

#define NIU SVC_ENGINE
#define DMA_CAP 32
#define STAGING(slot) (SVC_DMA_STAGING + (slot) * DMA_BATCH)
#define RD_TID(s) (8 + (s))
#define WR_TID(s) (8 + DMA_SLOTS + (s))

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j _svc_boot\n");

// Engine e moves chunks e, e+2, ... through a ring of DMA_SLOTS staging slots, keeping DMA_SLOTS-1 reads in flight:
// one read and one write at a time can't cover the PCIe round trip.
static void dma_copy_parallel(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  u32 stride = 2 * DMA_BATCH, first = SVC_ENGINE * DMA_BATCH, base = SVC_ENGINE * DMA_SLOTS;
  if (first >= size) return;
  u32 chunks = (size - first + stride - 1) / stride;
  #define AT(i) (first + (i) * stride)
  #define READ(i) noc_move_paced(NIU, 0, src_lo, src_hi, AT(i), MIN(size - AT(i), DMA_BATCH), \
                                 STAGING(base + (i) % DMA_SLOTS), RD_TID((i) % DMA_SLOTS), DMA_CAP)
  for (u32 i = 0; i < DMA_SLOTS - 1 && i < chunks; i++) READ(i);
  for (u32 i = 0; i < chunks; i++) {
    u32 ahead = i + DMA_SLOTS - 1;
    if (ahead < chunks) {
      if (i) noc_wait(NIU, WR_TID((i - 1) % DMA_SLOTS), 0);  // chunk i-1 has left the slot chunk `ahead` reuses
      READ(ahead);
    }
    u32 s = i % DMA_SLOTS;
    noc_wait(NIU, RD_TID(s), 1);
    noc_move_paced(NIU, 1, dst_lo, dst_hi, AT(i), MIN(size - AT(i), DMA_BATCH), STAGING(base + s), WR_TID(s), DMA_CAP);
  }
  for (u32 s = 0; s < DMA_SLOTS; s++) noc_wait(NIU, WR_TID(s), 1);
  #undef READ
  #undef AT
}

static void dma_copy_dram_src(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  u32 chunks = (size + DMA_BATCH - 1) / DMA_BATCH;
#if SVC_ENGINE == 0
  (void)dst_lo; (void)dst_hi;
  for (u32 i = 0; i < chunks; i++) {
    WAIT_SLOW(i - read32(SVC_PIPE_CONS) < 4);
    u32 at = i * DMA_BATCH, n = MIN(size - at, DMA_BATCH);
    noc_move_paced(0, 0, src_lo, src_hi, at, n, STAGING(i & 3), 1, DMA_CAP);
    noc_wait(0, 1, 1);
    write32(SVC_PIPE_PROD, i + 1);
    fence();
  }
#else
  (void)src_lo; (void)src_hi;
  for (u32 i = 0; i < chunks; i++) {
    WAIT_SLOW(read32(SVC_PIPE_PROD) > i);
    u32 at = i * DMA_BATCH, n = MIN(size - at, DMA_BATCH);
    noc_move_paced(1, 1, dst_lo, dst_hi, at, n, STAGING(i & 3), 3, DMA_CAP);
    noc_wait(1, 3, 0);
    write32(SVC_PIPE_CONS, i + 1);
    fence();
  }
  noc_wait(1, 3, 1);
#endif
}

static void dma_copy(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  if (!size) return;
  if (src_hi >> 31) dma_copy_dram_src(dst_lo, dst_hi, src_lo, src_hi, size);
  else dma_copy_parallel(dst_lo, dst_hi, src_lo, src_hi, size);
}

#if SVC_ENGINE == 1

NORETURN _svc_boot(void) {
  configure_csr(0);
  noc_init(1);
  write32(SVC_NCRISC_SYNC, 2);
  fence();
  for (u32 seq = 0;;) {
    u32 go;
    WAIT_SLOW((go = read32(SVC_COPY_GO)) != seq);
    seq = go;
    dma_copy(read32(SVC_COPY_DESC + 0), read32(SVC_COPY_DESC + 4),
             read32(SVC_COPY_DESC + 8), read32(SVC_COPY_DESC + 12),
             read32(SVC_COPY_DESC + 16));
    fence();
    write32(SVC_COPY_DONE, seq);
  }
}

#else

NORETURN _svc_boot(void) {
  configure_csr(0);
  invalidate_icache();
  enable_clock_gating();
  noc_init(0);
  write32(SVC_NCRISC_SYNC, 0);
  write32(SVC_COPY_GO, 0);
  write32(SVC_COPY_DONE, 0);

  write32(NCRISC_RESET_PC, SVC_NCRISC_BASE);
  write32(NCRISC_RESET_PC_OVERRIDE, 1);
  fence();
  write32(SOFT_RESET, RESET_ALL & ~(RESET_BRISC | RESET_NCRISC));
  WAIT_FAST(read32(SVC_NCRISC_SYNC) == 2);
  for (u32 retired = 0;;) {
    WAIT_FAST(read32(SVC_WPTR) != retired);
    u32 seq = ++retired, p = SVC_PACKETS + (seq % DMA_DEPTH) * PACKET;
    write32(SVC_PIPE_PROD, 0);
    write32(SVC_PIPE_CONS, 0);
    for (u32 i = 0; i < 5; i++) write32(SVC_COPY_DESC + 4*i, read32(p + 4*i));
    fence();
    write32(SVC_COPY_GO, seq);
    dma_copy(read32(p), read32(p+4), read32(p+8), read32(p+12), read32(p+16));
    WAIT_SLOW(read32(SVC_COPY_DONE) == seq);
    write32(SVC_SCRATCH, seq);
    write32(SVC_SCRATCH + 4, read32(p + 20));
    fence();
    noc_write(0, read32(SVC_SIGNAL), read32(SVC_SIGNAL + 4), SVC_SCRATCH, 8);
  }
}

#endif
