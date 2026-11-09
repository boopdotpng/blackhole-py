#include "queue.h"

#define STAGE(b) (STAGE_L1 + (b) * STAGE_SIZE)
#define PARAMS(b) (PARAMS_L1 + (b) * PARAM_SIZE)
#define TID(b) (3 + (b))

static u32 buf;
static packet *loaded;

static void load(packet *p, u32 b) {
  const u32 *d = (const u32 *)p->a_lo;
  noc_move(0, 0, d[4], d[5], 0, d[3], STAGE(b), TID(b));
  if (d[2]) noc_move(0, 0, p->b_lo, p->b_hi, 0, d[2], PARAMS(b), TID(b));
}

static void profile(packet *p, u32 offset) {
  if (!(p->c | p->c_hi)) return;
  u32 lo = p->c + offset;
  queue_timestamp(0, lo, p->c_hi + (lo < p->c));
}

static void exec(packet *p, packet *next) {
  profile(p, 8);
  u32 b = buf;
  if (loaded != p) load(p, b);
  noc_wait(0, TID(b), 1);
  const u32 *d = (const u32 *)p->a_lo, *rects = d + 8, *transfer = rects + d[1];
  write32(DONE_COUNT, 0);
  for (u32 j = 0; j < d[6]; j++) {
    for (u32 i = 0; i < transfer[3]; i++) {
      u32 r = transfer[4 + i];
      noc_mcast(0, STAGE(b) + transfer[0], transfer[1], r & 0xFFF, r >> 12, transfer[2]);
    }
    transfer += 4 + transfer[3];
  }
  if (d[2]) for (u32 i = 0; i < d[1]; i++)
    noc_mcast(0, PARAMS(b), L1_PARAM_BASE, rects[i] & 0xFFF, rects[i] >> 12, d[2]);
  noc_mcast_flush(0);
  for (u32 i = 0; i < d[1]; i++) noc_mcast(0, GO_WORD, GO_SIGNAL, rects[i] & 0xFFF, rects[i] >> 12, 4);
  noc_mcast_flush(0);
  queue_flush(0, 0);
  buf ^= 1;
  loaded = 0;
  if (next && next->op == OP_EXEC) load(loaded = next, buf);
  while (read32(DONE_COUNT) != d[0]) fence();
  profile(p, 24);
}

/* The next EXEC after p, looking past STOREs and TIMESTAMPs so they don't stop its load from overlapping p's run.
 * Anything else (WAIT, CALL) may gate what the EXEC reads, so the search stops there. *stop = where it stopped: every
 * packet before it has the same answer, so callers rescan only on reaching it. */
static packet *next_exec(packet *p, packet *end, packet **stop) {
  for (p++; p < end; p++) {
    if (p->op == OP_EXEC) break;
    if (p->op != OP_STORE && p->op != OP_TIMESTAMP) break;
  }
  *stop = p;
  return p < end && p->op == OP_EXEC ? p : 0;
}

static void run(packet *p, packet *next) {
  if (p->op == OP_EXEC) exec(p, next);
  else queue_signal_op(0, p);
}

static void call(packet *p) {
  u32 lo = p->a_lo, hi = p->a_hi, size = p->c;
  if (size) noc_move(0, 0, lo, hi, 0, MIN(size, GRAPH_CHUNK), GRAPH_L1, 2);
  for (u32 at = 0, b = 0; at < size; at += GRAPH_CHUNK, b ^= 1) {
    noc_wait(0, 2, 1);
    u32 next = at + GRAPH_CHUNK, chunk = GRAPH_L1 + b * GRAPH_CHUNK, n = MIN(size - at, GRAPH_CHUNK);
    if (next < size) noc_move(0, 0, lo, hi, next, MIN(size - next, GRAPH_CHUNK), GRAPH_L1 + (b ^ 1) * GRAPH_CHUNK, 2);
    packet *end = (packet *)(chunk + n), *stop = 0, *ahead = 0;
    for (packet *q = (packet *)chunk; q < end; q++) {
      if (q >= stop) ahead = next_exec(q, end, &stop);
      run(q, ahead);
    }
  }
}

KERNEL kernel_main(void) {
  noc_init(0);
  queue_init(0);
  buf = 0;
  loaded = 0;
  write32(GO_WORD, 0x80 | noc_coord(0) << 8);
  for (u32 read = 0;;) {
    u32 packets = CQ_PACKETS + (read & 63);
    u32 bytes = queue_fetch(0, read, packets, CQ_PACKETS_MAX);
    if (!bytes) queue_idle(0);
    packet *end = (packet *)(packets + bytes), *stop = 0, *ahead = 0;
    for (u32 offset = 0; offset < bytes; offset += PACKET) {
      packet *p = (packet *)(packets + offset);
      if (p >= stop) ahead = next_exec(p, end, &stop);
      if (p->op == OP_CALL) call(p);
      else run(p, ahead);
      write32(RPTR, read + offset + PACKET);
    }
    read += bytes;
  }
}
