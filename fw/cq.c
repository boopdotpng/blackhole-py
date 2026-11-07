/* The COMPUTE queue on CQ_CORE. NCRISC prefetches the sysmem ring into an L1 copy at the same offsets, BRISC
 * dispatches from that copy. They share L1, so FETCHED is a plain store. The host never pushes more than RING_SIZE
 * past RPTR, so prefetch can never overwrite a packet dispatch has not retired. */
#include "fw.h"

#if TT_FW_RISC == 1

KERNEL kernel_main(void) {
  noc_init();
  for (u32 read = 0;;) {
    read += fetch(read, L1_RING + (read & (RING_SIZE - 1)), RING_SIZE);
    mmio_write32(FETCHED, read);
  }
}

#else

static const u32 slots[5] = {KERNEL_BRISC, KERNEL_NCRISC, KERNEL_TRISC0, KERNEL_TRISC1, KERNEL_TRISC2};

static void mcast(u32 source, u32 target, u32 start, u32 end, u32 size) {
  for (u32 offset = 0; offset < size; offset += NOC_MAX_BURST) {
    noc_multicast_write(0, source + offset, target + offset, start, end, MIN(size - offset, NOC_MAX_BURST));
  }
}

/* EXEC [op | prog_size << 32, prog, args, args_size]. prog is the five kernels back to back, args is
 * [rect count, core count, 5 kernel sizes, rects...] padded to ARGS_HEADER, then the params. A rect is start | end << 12.
 * Every kernel goes to its fixed slot on every core, then GO, then wait for every core to finish. */
static void exec(volatile u32 *p) {
  noc_move(0, p[4], p[5], 0, p[6], ARGS_L1, 1);
  noc_move(0, p[2], p[3], 0, p[1], PROG_L1, 1);
  noc_wait(1, 1);
  const u32 *h = (const u32 *)ARGS_L1, *sizes = h + ARGS_SIZES, *rects = h + ARGS_RECTS;
  u32 count = h[0], cores = h[1], params = p[6] - ARGS_HEADER;
  mmio_write32(DISPATCH_DONE_COUNT, 0);
  mmio_write32(GO_WORD, 0x80u);
  fence();
  for (u32 i = 0; i < count; i++) {
    u32 start = rects[i] & 0xFFFu, end = rects[i] >> 12;
    for (u32 r = 0, at = PROG_L1; r < 5; at += sizes[r], r++) mcast(at, slots[r], start, end, sizes[r]);
    mcast(ARGS_L1 + ARGS_HEADER, L1_PARAM_BASE, start, end, params);
  }
  noc_wait_zero(NOC_OUTGOING(0, 1));  /* every kernel and param byte is out before any GO */
  for (u32 i = 0; i < count; i++) noc_multicast_write(0, GO_WORD, GO_SIGNAL, rects[i] & 0xFFFu, rects[i] >> 12, 4);
  noc_wait_zero(NOC_OUTGOING(0, 1));
  while (mmio_read32(DISPATCH_DONE_COUNT) != cores) fence();
  fence();
}

KERNEL kernel_main(void) {
  noc_init();
  for (u32 read = 0;; read += PACKET) {
    while (mmio_read32(FETCHED) == read) fence();
    fence();
    volatile u32 *p = (volatile u32 *)(L1_RING + (read & (RING_SIZE - 1)));
    if (p[0] == OP_EXEC) exec(p);
    else common_op(p);
    mmio_write32(RPTR, read + PACKET);
  }
}

#endif
