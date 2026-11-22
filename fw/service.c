#include "noc.h"

#define NIU SVC_ENGINE
#define DMA_CAP 32
#define STAGING(slot) (SVC_DMA_STAGING + (slot) * DMA_BATCH)

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j _svc_boot\n");

static void dma_copy_parallel(u32 dst_lo, u32 dst_hi, u32 src_lo, u32 src_hi, u32 size) {
  u32 at = SVC_ENGINE * DMA_BATCH;
  if (at >= size) return;
  u32 base = SVC_ENGINE * 2;
  noc_move_paced(NIU, 0, src_lo, src_hi, at, MIN(size - at, DMA_BATCH), STAGING(base), 1, DMA_CAP);
  for (u32 buf = 0;; buf ^= 1) {
    u32 next = at + 2 * DMA_BATCH;
    noc_wait(NIU, 1 + buf, 1);
    if (next < size) {
      noc_wait(NIU, 3 + (buf ^ 1), 0);
      noc_move_paced(NIU, 0, src_lo, src_hi, next, MIN(size - next, DMA_BATCH), STAGING(base + (buf ^ 1)), 1 + (buf ^ 1), DMA_CAP);
    }
    noc_move_paced(NIU, 1, dst_lo, dst_hi, at, MIN(size - at, DMA_BATCH), STAGING(base + buf), 3 + buf, DMA_CAP);
    if (next >= size) break;
    at = next;
  }
  noc_wait(NIU, 3, 1);
  noc_wait(NIU, 4, 1);
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

typedef struct {
  u32 op, op_arg;
  u32 a_lo, a_hi;
  u32 b_lo, b_hi;
  u32 c_lo, c_hi;
} packet;

static u32 scratch(u32 lo) { return SVC_SCRATCH + (lo & 63); }

static void run_packet(packet *p, u32 *copy_seq) {
  if (p->op == OP_KICK) {
    u32 rect = p->a_lo, exclude = p->a_hi;
    u32 workers = p->c_lo & 0xFFFF, args_bytes = p->c_lo >> 16;
    if (args_bytes) {
      noc_read(0, p->b_lo, p->b_hi, SVC_ARGS_L1, args_bytes);
      noc_mcast(0, SVC_ARGS_L1, STEP_ARGS, rect, exclude, args_bytes);
    }
    write32(SVC_DONE_COUNT, 0);
    noc_mcast_flush(0);
    u32 ep = read32(SVC_EPOCH) + 1;
    if (!ep) ep = 1;
    write32(SVC_EPOCH, ep);
    fence();
    noc_mcast(0, SVC_EPOCH, STEP_EPOCH, rect, exclude, 4);
    noc_mcast_flush(0);
    while (read32(SVC_DONE_COUNT) != workers) fence();
  } else if (p->op == OP_COPY) {
    u32 seq = ++(*copy_seq);
    write32(SVC_PIPE_PROD, 0);
    write32(SVC_PIPE_CONS, 0);
    write32(SVC_COPY_DESC + 0, p->a_lo);
    write32(SVC_COPY_DESC + 4, p->a_hi);
    write32(SVC_COPY_DESC + 8, p->b_lo);
    write32(SVC_COPY_DESC + 12, p->b_hi);
    write32(SVC_COPY_DESC + 16, p->c_lo);
    fence();
    write32(SVC_COPY_GO, seq);
    dma_copy(p->a_lo, p->a_hi, p->b_lo, p->b_hi, p->c_lo);
    WAIT_SLOW(read32(SVC_COPY_DONE) == seq);
  } else if (p->op == OP_WAIT) {
    u32 s = scratch(p->a_lo);
    for (;;) {
      noc_read(0, p->a_lo, p->a_hi, s, 8);
      u32 lo = read32(s), hi = read32(s + 4);
      if (p->c_lo ? hi == p->b_hi && lo == p->b_lo : hi > p->b_hi || (hi == p->b_hi && lo >= p->b_lo)) return;
    }
  } else if (p->op == OP_STORE) {
    u32 s = scratch(p->a_lo);
    write32(s, p->b_lo);
    write32(s + 4, p->b_hi);
    fence();
    noc_write(0, p->a_lo, p->a_hi, s, 8);
  } else {
    for (;;) {}
  }
}

NORETURN _svc_boot(void) {
  configure_csr(0);
  invalidate_icache();
  enable_clock_gating();
  noc_init(0);
  write32(SVC_NCRISC_SYNC, 0);
  write32(SVC_COPY_GO, 0);
  write32(SVC_COPY_DONE, 0);
  write32(SVC_EPOCH, 0);
  write32(NCRISC_RESET_PC, SVC_NCRISC_BASE);
  write32(NCRISC_RESET_PC_OVERRIDE, 1);
  fence();
  write32(SOFT_RESET, RESET_ALL & ~(RESET_BRISC | RESET_NCRISC));
  WAIT_FAST(read32(SVC_NCRISC_SYNC) == 2);
  u32 copy_seq = 0;
  for (u32 read = 0;;) {
    u32 offset = read & (RING_SIZE - 1), pushed = read32(SVC_WPTR) - read;
    u32 bytes = MIN(pushed, MIN(RING_SIZE - offset, SVC_PACKETS_MAX));
    if (!bytes) { fence(); continue; }
    u32 buf = SVC_PACKETS + (read & 63);
    u32 lo = read32(SVC_RING_LO) + offset;
    noc_read(0, lo, read32(SVC_RING_HI) + (lo < offset), buf, bytes);
    fence();
    for (u32 off = 0; off < bytes; off += PACKET) {
      run_packet((packet *)(buf + off), &copy_seq);
      write32(SVC_RPTR, read + off + PACKET);
    }
    read += bytes;
  }
}

#endif
