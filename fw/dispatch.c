#include "queue.h"

#define STAGE(b) (STAGE_L1 + (b) * STAGE_SIZE)
#define PARAMS(b) (PARAMS_L1 + (b) * PARAM_SIZE)
#define TID(b) (3 + (b))

#define START(r) ((r) & 0xFFF)
#define END(r) ((r) >> 12)

static u32 buf, go;
static packet *installed;  /* the EXEC whose code is already in worker slot buf, or 0 */

/* Code and arguments are immutable until the graph retires, so this can overlap the preceding kernel. */
static void fetch(packet *p, u32 b) {
  const u32 *d = (const u32 *)p->a_lo;
  noc_move(0, 0, d[4], d[5], 0, d[3], STAGE(b), TID(b));
  if (d[2]) noc_move(0, 0, p->b_lo, p->b_hi, 0, d[2], PARAMS(b), TID(b));
}

/* Multicast p's code and LAUNCH masks into worker slot b. Slot b's previous launch has returned and the one running now
 * is in the other slot, so this can overlap it too. Everything goes out on NoC0, so the flush before the GO covers it. */
static void install(packet *p, u32 b) {
  const u32 *d = (const u32 *)p->a_lo, *transfer = d + 8 + d[1];
  noc_wait(0, TID(b), 1);
  for (u32 j = 0; j < d[6]; j++) {
    for (u32 i = 0; i < transfer[3]; i++) {
      u32 r = transfer[4 + i];
      noc_mcast(0, STAGE(b) + transfer[0], transfer[1] + b * SLOT_STRIDE, START(r), END(r), transfer[2]);
    }
    transfer += 4 + transfer[3];
  }
}

static void profile(packet *p, u32 offset) {
  if (!(p->c | p->c_hi)) return;
  u32 lo = p->c + offset;
  queue_timestamp(0, lo, p->c_hi + (lo < p->c));
}

static void exec(packet *p, packet *next) {
  profile(p, 8);
  u32 b = buf;
  if (installed != p) {
    fetch(p, b);
    install(p, b);
  }
  const u32 *d = (const u32 *)p->a_lo, *rects = d + 8;
  write32(DONE_COUNT, 0);
  /* Params have one fixed home, which the previous launch may have been reading until it returned */
  if (d[2]) for (u32 i = 0; i < d[1]; i++) noc_mcast(0, PARAMS(b), L1_PARAM_BASE, START(rects[i]), END(rects[i]), d[2]);
  noc_mcast_flush(0);
  write32(GO_WORD, go | b << GO_SLOT_BIT);
  for (u32 i = 0; i < d[1]; i++) noc_mcast(0, GO_WORD, GO_SIGNAL, START(rects[i]), END(rects[i]), 4);
  noc_mcast_flush(0);
  queue_flush(0, 0);
  buf ^= 1;
  installed = 0;
  if (next && next->op == OP_EXEC) {
    fetch(next, buf);
    install(installed = next, buf);
  }
  while (read32(DONE_COUNT) != d[0]) fence();
  profile(p, 24);
}

/* Only EXEC needs lookahead. Each EXEC scans its following STOREs/TIMESTAMPs once;
 * WAIT and CALL stop prefetch because they may gate what the next EXEC reads. */
static void run(packet *p, packet *end) {
  if (p->op != OP_EXEC) { queue_signal_op(0, p); return; }
  packet *next = p + 1;
  while (next < end && (next->op == OP_STORE || next->op == OP_TIMESTAMP)) next++;
  exec(p, next < end && next->op == OP_EXEC ? next : 0);
}

static void call_buffer(u32 lo, u32 hi, u32 size) {
  if (size) noc_move(0, 0, lo, hi, 0, MIN(size, GRAPH_CHUNK), GRAPH_L1, 2);
  for (u32 at = 0, b = 0; at < size; at += GRAPH_CHUNK, b ^= 1) {
    noc_wait(0, 2, 1);
    u32 next = at + GRAPH_CHUNK, chunk = GRAPH_L1 + b * GRAPH_CHUNK, n = MIN(size - at, GRAPH_CHUNK);
    if (next < size) noc_move(0, 0, lo, hi, next, MIN(size - next, GRAPH_CHUNK), GRAPH_L1 + (b ^ 1) * GRAPH_CHUNK, 2);
    packet *end = (packet *)(chunk + n);
    for (packet *q = (packet *)chunk; q < end; q++) run(q, end);
  }
}

static void call(packet *p) {
  u32 lo = p->a_lo, hi = p->a_hi, size = p->c, count = p->b_lo ? p->b_lo : 1, stride = p->b_hi;
  for (u32 i = 0; i < count; i++) {
    call_buffer(lo, hi, size);
    lo += stride;
    hi += lo < stride;
  }
}

KERNEL kernel_main(void) {
  noc_init(0);
  queue_init(0);
  buf = 0;
  installed = 0;
  go = 0x80 | noc_coord(0) << 8;
  for (u32 read = 0;;) {
    u32 packets = CQ_PACKETS + (read & 63);
    u32 bytes = queue_fetch(0, read, packets, CQ_PACKETS_MAX);
    if (!bytes) queue_idle(0);
    packet *end = (packet *)(packets + bytes);
    for (u32 offset = 0; offset < bytes; offset += PACKET) {
      packet *p = (packet *)(packets + offset);
      if (p->op == OP_CALL) call(p);
      else run(p, end);
      write32(RPTR, read + offset + PACKET);
    }
    read += bytes;
  }
}
