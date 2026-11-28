// The HCQ2 queue a service core runs. The host writes the (address, bytes) of a command buffer into a ring in the core's
// L1 and bumps WPTR; the core streams the buffer's 64-byte packets through its own run_pkt and retires it in RPTR.
#pragma once
#include "noc.h"

static void run_pkt(const u32 *p);

static void hcq_read(u32 lo, u32 hi, u32 off, u32 size, u32 local) {
  noc_move_paced(0, 0, lo, hi, off, size, local, 0, 0);
  noc_wait(0, 0, 1);
}

// PKT_WAIT: until the u64 at the address is >= the value (== with flag bit 0)
static void hcq_wait(const u32 *p, u32 scratch) {
  u32 stage = scratch + (p[2] & 63u);  // a NoC read keeps its offset in a 64-byte word
  for (;;) {
    hcq_read(p[2], p[3], 0, 8, stage);
    u32 lo = read32(stage), hi = read32(stage + 4);
    if ((p[1] & 1u) ? (lo == p[4] && hi == p[5]) : (hi > p[5] || (hi == p[5] && lo >= p[4]))) return;
    u32 n = POLL_BACKOFF;
    __asm__ volatile("1: addi %0, %0, -1\n bnez %0, 1b" : "+r"(n));
  }
}

// PKT_SIGNAL stores the packet's u64 at the address, PKT_TIMESTAMP the wall clock 8 bytes after it
static void hcq_signal(const u32 *p, u32 scratch) {
  u32 stamp = p[0] == PKT_TIMESTAMP, lo = p[2] + 8u * stamp, hi = p[3] + (lo < p[2]);
  u32 stage = scratch + (lo & 15u);  // a NoC write keeps its offset in a 16-byte word
  write32(stage, stamp ? read32(WALL_CLOCK_L) : p[4]);
  write32(stage + 4, stamp ? read32(WALL_CLOCK_H) : p[5]);
  fence();
  noc_write(0, lo, hi, stage, 8);
}

INLINE NORETURN hcq_run(u32 wptr, u32 rptr, u32 ready, u32 ring, u32 stage) {
  write32(rptr, 0);
  fence();
  write32(ready, 1);
  fence();
  for (u32 retired = 0;;) {
    WAIT_FAST(read32(wptr) != retired);
    u32 seq = ++retired, desc = ring + (seq % CP_DEPTH) * CP_IB_BYTES;
    u32 lo = read32(desc), hi = read32(desc + 4), bytes = read32(desc + 8);
    for (u32 off = 0; off < bytes; off += CP_CMDBUF_CHUNK) {
      u32 chunk = MIN(bytes - off, CP_CMDBUF_CHUNK);
      hcq_read(lo, hi, off, chunk, stage);
      for (u32 at = 0; at < chunk; at += CP_PKT_BYTES) run_pkt((const u32 *)(stage + at));
    }
    fence();
    write32(rptr, seq);
    fence();
  }
}
