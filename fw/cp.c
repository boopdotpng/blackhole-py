// HCQ2-compatible Command Processor (COMPUTE:0 queue, running on core (right, 10)).
// Streams 64-byte packets from host/DRAM indirect command buffers, manages the worker L1
// program cache (bump-allocated with flush-on-full + monotonic cache_epoch), overlaps
// kernargs / program fetch with the running kernel, and executes WAIT/SIGNAL/TIMESTAMP/BARRIER.
#include "noc.h"

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK_TOP)
        "j cp_main\n");

typedef struct {
  u32 key;
  u32 l1_base;
  u32 pc[5];
  u32 cb_mask;
} CacheEntry;

static CacheEntry cache_tbl[CP_CACHE_MAX];
static u32 cache_count, cache_top, cache_epoch;
static u32 active_workers, step_epoch;

static void exec_barrier(void) {
  if (!active_workers) return;
  WAIT_FAST(read32(CP_WORK_DONE) >= active_workers);
  write32(CP_WORK_DONE, 0);
  fence();
  active_workers = 0;
}

static void noc_read_sync(u32 lo, u32 hi, u32 off, u32 size, u32 local) {
  noc_move_paced(0, 0, lo, hi, off, size, local, 0, 0);
  noc_wait(0, 0, 1);
}

static void mcast_all_workers(u32 local, u32 remote, u32 size) {
  u32 n = read32(CP_ALL_NRECTS);
  for (u32 i = 0; i < n; i++) noc_send_rect(0, local, remote, read32(CP_ALL_RECTS + 4 * i), size, 2);
  noc_send_rect_flush(0, 2);
}

static CacheEntry *cache_lookup(u32 key) {
  if (!key) return (CacheEntry *)0;
  for (u32 i = 0; i < cache_count; i++) {
    if (cache_tbl[i].key == key) return &cache_tbl[i];
  }
  return (CacheEntry *)0;
}

static CacheEntry *cache_load(u32 prog_lo, u32 prog_hi, u32 prog_bytes, u32 key) {
  CacheEntry *e = cache_lookup(key);
  if (e) return e;

  u32 code_bytes = prog_bytes > PROG_HDR_BYTES ? prog_bytes - PROG_HDR_BYTES : 0;
  u32 aligned = (code_bytes + 63u) & ~63u;

  // Evict entire cache on wrap (or table full): drain active workers first so no running
  // kernel is overwritten, then reset bump pointer to CODE_CACHE_BASE.
  if (cache_count >= CP_CACHE_MAX || cache_top + aligned > CODE_CACHE_END) {
    exec_barrier();
    cache_count = 0;
    cache_top = CODE_CACHE_BASE;
  }

  // Pull packed program bundle (64B header + code) from DRAM/host into CP_PROG_STAGE.
  // Can overlap with an active kernel running at < cache_top!
  noc_read_sync(prog_lo, prog_hi, 0, prog_bytes, CP_PROG_STAGE);

  u32 base = cache_top;
  if (aligned) mcast_all_workers(CP_PROG_STAGE + PROG_HDR_BYTES, base, aligned);
  cache_top += aligned;
  cache_epoch++;

  e = &cache_tbl[cache_count++];
  e->key = key;
  e->l1_base = base;
  for (u32 r = 0; r < 5; r++) {
    u32 off = read32(CP_PROG_STAGE + 4 * r);
    e->pc[r] = off ? base + (off - PROG_HDR_BYTES) : 0;
  }
  e->cb_mask = read32(CP_PROG_STAGE + 20);
  return e;
}

static void run_pkt(const u32 *p) {
  u32 op = p[0], flags = p[1];
  if (op == PKT_NOP) return;

  if (op == PKT_EXEC_BARRIER || op == PKT_MEM_BARRIER) {
    exec_barrier();
    return;
  }

  if (op == PKT_WAIT) {
    u32 alo = p[2], ahi = p[3], tlo = p[4], thi = p[5];
    u32 stage = CP_SCRATCH + (alo & 63u);
    for (;;) {
      noc_read_sync(alo, ahi, 0, 8, stage);
      u32 vlo = read32(stage), vhi = read32(stage + 4);
      int ok = (flags & 1u) ? (vlo == tlo && vhi == thi) : (vhi > thi || (vhi == thi && vlo >= tlo));
      if (ok) break;
      u32 n_ = POLL_BACKOFF;
      __asm__ volatile("1: addi %0, %0, -1\n bnez %0, 1b" : "+r"(n_));
    }
    return;
  }

  if (op == PKT_SIGNAL) {
    exec_barrier();
    u32 alo = p[2], ahi = p[3], vlo = p[4], vhi = p[5];
    u32 stage = CP_SCRATCH + (alo & 15u);
    write32(stage, vlo);
    write32(stage + 4, vhi);
    fence();
    noc_write(0, alo, ahi, stage, 8);
    return;
  }

  if (op == PKT_TIMESTAMP) {
    exec_barrier();
    u32 alo = p[2] + 8u, ahi = p[3] + (alo < p[2]);
    u32 tlo = read32(WALL_CLOCK_L), thi = read32(WALL_CLOCK_H);
    u32 stage = CP_SCRATCH + (alo & 15u);
    write32(stage, tlo);
    write32(stage + 4, thi);
    fence();
    noc_write(0, alo, ahi, stage, 8);
    return;
  }

  if (op == PKT_EXEC) {
    u32 prog_lo = p[2], prog_hi = p[3], prog_bytes = p[4], prog_key = p[5];
    u32 args_lo = p[6], args_hi = p[7], nworkers = p[8];
    u32 nrects = p[9] & 0xFFu, args_bytes = p[9] >> 8;

    // Overlap program cache fill and kernargs read with the currently executing kernel.
    CacheEntry *e = cache_load(prog_lo, prog_hi, prog_bytes, prog_key);
    if (args_bytes && (args_lo || args_hi)) {
      noc_read_sync(args_lo, args_hi, 0, args_bytes, CP_DISPATCH_BUF);
    } else {
      for (u32 i = 0; i < 32; i++) write32(CP_DISPATCH_BUF + 4 * i, 0);
    }

    // Wait for prior kernel before writing live worker dispatch mailboxes.
    exec_barrier();

    u32 ep = ++step_epoch;
    u32 hdr = CP_DISPATCH_BUF + 0x80;
    for (u32 r = 0; r < 5; r++) write32(hdr + 4 * r, e->pc[r]);
    write32(hdr + 20, nworkers);
    write32(hdr + 24, e->cb_mask);
    write32(hdr + 28, flags);
    write32(hdr + 32, cache_epoch);
    write32(hdr + 60, ep);
    fence();

    // Send [0x80..0x13B] then STEP_EPOCH (0x13C) on the same ordered static VC.
    for (u32 i = 0; i < nrects; i++) {
      u32 rect = p[10 + i];
      noc_send_rect(0, CP_DISPATCH_BUF, ARG_BASE, rect, DISPATCH_BYTES - 4, 2);
      noc_send_rect(0, CP_DISPATCH_BUF + DISPATCH_BYTES - 4, STEP_EPOCH, rect, 4, 2);
    }
    noc_send_rect_flush(0, 2);
    active_workers = nworkers;
    return;
  }
}

NORETURN cp_main(void) {
  configure_csr(0);
  invalidate_icache();
  enable_clock_gating();
  noc_init(0);

  write32(CP_WORK_DONE, 0);
  write32(CP_RPTR, 0);
  cache_count = 0;
  cache_top = CODE_CACHE_BASE;
  cache_epoch = 0;
  active_workers = 0;
  step_epoch = 0;
  fence();
  write32(CP_READY, 1);
  fence();

  for (u32 retired = 0;;) {
    WAIT_FAST(read32(CP_WPTR) != retired);
    u32 seq = ++retired;
    u32 desc = CP_RING + (seq % CP_DEPTH) * CP_IB_BYTES;
    u32 ib_lo = read32(desc + 0), ib_hi = read32(desc + 4), ib_bytes = read32(desc + 8);

    for (u32 off = 0; off < ib_bytes; off += CP_CMDBUF_CHUNK) {
      u32 chunk = MIN(ib_bytes - off, CP_CMDBUF_CHUNK);
      noc_read_sync(ib_lo, ib_hi, off, chunk, CP_CMDBUF_STAGE);
      for (u32 at = 0; at < chunk; at += CP_PKT_BYTES) {
        run_pkt((const u32 *)(CP_CMDBUF_STAGE + at));
      }
    }
    fence();
    write32(CP_RPTR, seq);
    fence();
  }
}
