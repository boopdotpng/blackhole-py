// The DMA core (COPY:0 queue): BRISC runs the HCQ2 queue and splits every copy with NCRISC, one NoC each.
#if DMA_ENGINE == 0
#include "hcq.h"
#else
#include "noc.h"
#endif

#define NIU DMA_ENGINE
#define DMA_CAP 32
#define STAGING(slot) (DMA_STAGING + (slot) * DMA_BATCH)
#define RD_TID(s) (8 + (s))
#define WR_TID(s) (8 + DMA_SLOTS + (s))

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j _dma_boot\n");

static void dma_copy_parallel(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  u32 stride = 2 * DMA_BATCH, first = DMA_ENGINE * DMA_BATCH, base = DMA_ENGINE * DMA_SLOTS;
  if (first >= size) return;
  u32 chunks = (size - first + stride - 1) / stride;
  #define AT(i) (first + (i) * stride)
  #define READ(i) noc_move_paced(NIU, 0, src_lo, src_hi, AT(i), MIN(size - AT(i), DMA_BATCH), \
                                 STAGING(base + (i) % DMA_SLOTS), RD_TID((i) % DMA_SLOTS), DMA_CAP)
  for (u32 i = 0; i < DMA_SLOTS - 1 && i < chunks; i++) READ(i);
  for (u32 i = 0; i < chunks; i++) {
    u32 ahead = i + DMA_SLOTS - 1;
    if (ahead < chunks) {
      if (i) noc_wait(NIU, WR_TID((i - 1) % DMA_SLOTS), 0);
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
#if DMA_ENGINE == 0
  (void)dst_lo; (void)dst_hi;
  for (u32 i = 0; i < chunks; i++) {
    WAIT_SLOW(i - read32(DMA_PIPE_CONS) < 4);
    u32 at = i * DMA_BATCH, n = MIN(size - at, DMA_BATCH);
    noc_move_paced(0, 0, src_lo, src_hi, at, n, STAGING(i & 3), 1, DMA_CAP);
    noc_wait(0, 1, 1);
    write32(DMA_PIPE_PROD, i + 1);
    fence();
  }
#else
  (void)src_lo; (void)src_hi;
  for (u32 i = 0; i < chunks; i++) {
    WAIT_SLOW(read32(DMA_PIPE_PROD) > i);
    u32 at = i * DMA_BATCH, n = MIN(size - at, DMA_BATCH);
    noc_move_paced(1, 1, dst_lo, dst_hi, at, n, STAGING(i & 3), 3, DMA_CAP);
    noc_wait(1, 3, 0);
    write32(DMA_PIPE_CONS, i + 1);
    fence();
  }
  noc_wait(1, 3, 1);
#endif
}

// An end that is not 64-byte aligned: a NoC read keeps its offset in a 64-byte word and a write in a 16-byte word,
// so BRISC alone reads each chunk at the source's offset and moves it over when the destination's differs.
static void dma_copy_bytes(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
#if DMA_ENGINE == 0
  for (u32 at = 0; at < size;) {
    u32 n = MIN(size - at, DMA_BATCH - 64), rd = STAGING(0) + ((src_lo + at) & 63), wr = STAGING(1) + ((dst_lo + at) & 15);
    noc_move_paced(0, 0, src_lo, src_hi, at, n, rd, 1, DMA_CAP);
    noc_wait(0, 1, 1);
    if (!((rd ^ wr) & 15)) wr = rd;
    else if ((rd | wr) & 3) for (u32 i = 0; i < n; i++) write8(wr + i, read8(rd + i));
    else for (u32 i = 0; i < n; i += 4) write32(wr + i, read32(rd + i));
    fence();
    noc_move_paced(0, 1, dst_lo, dst_hi, at, n, wr, 3, DMA_CAP);
    noc_wait(0, 3, 1);
    at += n;
  }
#else
  (void)dst_lo; (void)dst_hi; (void)src_lo; (void)src_hi; (void)size;
#endif
}

static void dma_copy(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  if (!size) return;
  if ((dst_lo | src_lo) & 63) dma_copy_bytes(dst_lo, dst_hi, src_lo, src_hi, size);
  else if (src_hi >> 31) dma_copy_dram_src(dst_lo, dst_hi, src_lo, src_hi, size);
  else dma_copy_parallel(dst_lo, dst_hi, src_lo, src_hi, size);
}

#if DMA_ENGINE == 1

NORETURN _dma_boot(void) {
  configure_csr(0);
  noc_init(1);
  write32(DMA_NCRISC_SYNC, 2);
  fence();
  for (u32 seq = 0;;) {
    u32 go;
    WAIT_SLOW((go = read32(DMA_COPY_GO)) != seq);
    seq = go;
    dma_copy(read32(DMA_COPY_DESC + 0), read32(DMA_COPY_DESC + 4),
             read32(DMA_COPY_DESC + 8), read32(DMA_COPY_DESC + 12),
             read32(DMA_COPY_DESC + 16));
    fence();
    write32(DMA_COPY_DONE, seq);
  }
}

#else

// d is {dst, src, bytes}: publish it to NCRISC under a new sequence number and copy BRISC's share
static void dma_run(u32 seq, const u32 *d) {
  write32(DMA_PIPE_PROD, 0);
  write32(DMA_PIPE_CONS, 0);
  for (u32 i = 0; i < 5; i++) write32(DMA_COPY_DESC + 4*i, d[i]);
  fence();
  write32(DMA_COPY_GO, seq);
  dma_copy(d[0], d[1], d[2], d[3], d[4]);
  WAIT_SLOW(read32(DMA_COPY_DONE) == seq);
}

static void run_pkt(const u32 *p) {
  static u32 copies;
  if (p[0] == PKT_WAIT) hcq_wait(p, DMA_SCRATCH);
  else if (p[0] == PKT_SIGNAL || p[0] == PKT_TIMESTAMP) hcq_signal(p, DMA_SCRATCH);
  else if (p[0] == PKT_COPY) dma_run(++copies, p + 2);
}

NORETURN _dma_boot(void) {
  configure_csr(0);
  invalidate_icache();
  enable_clock_gating();
  noc_init(0);
  write32(DMA_NCRISC_SYNC, 0);
  write32(DMA_COPY_GO, 0);
  write32(DMA_COPY_DONE, 0);

  write32(NCRISC_RESET_PC, DMA_NCRISC_BASE);
  write32(NCRISC_RESET_PC_OVERRIDE, 1);
  fence();
  write32(SOFT_RESET, RESET_ALL & ~(RESET_BRISC | RESET_NCRISC));
  WAIT_FAST(read32(DMA_NCRISC_SYNC) == 2);
  hcq_run(DMA_WPTR, DMA_RPTR, DMA_READY, DMA_RING, DMA_CMDBUF_STAGE);
}

#endif
