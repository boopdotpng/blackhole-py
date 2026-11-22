// Core-to-core sync patterns for the decode megakernel, timed over many generations in one launch.
//   mode 0: barrier_all (crt0.h), for reference
//   mode 1: all-gather. Each core multicasts its slice to every core; receivers poll one tag per sender.
//   mode 3: coordinator gather (unicast to one core, one multicast back); mode 4: all-reduce ending in it
//   mode 2: all-reduce = reduce-scatter (unicast slice j of my partial to core j) + sum + all-gather of the sums.
// Every packet carries its generation in its last word, so data and flag land together and nothing needs resetting.
// Buffers alternate by generation parity: a core cannot start generation g+2 before every core has finished
// reading g, because g+1 needs everyone's g+1 data, which each core only sends after it has consumed g.
// Summation is integer adds on BRISC (a stand-in for the Tensix doing it); its cycles are reported separately.
#include "crt0.h"

#define OUT      0x30000                  // 16 B result record, written to the host
#define STAGE    0x31000                  // gather source slot
#define RS_STAGE 0x32000                  // reduce-scatter source slots, one per destination
#define AG       0x40000                  // gather slots: 2 parities x workers x slot
#define RS       0x80000                  // reduce-scatter slots: 2 parities x workers x slot
#define AG2      0xA0000                  // all-reduce's gather of the sums
#define ACC      0xC0000

static u32 epoch = 0;
static u32 slot_of(u32 bytes) { return (bytes + 4 + 63) & ~63u; }
static u32 coord_of(u32 id) {             // logical id = x * 10 + y -> translated NoC0 coord
  u32 x = id / 10, y = id % 10, tx = x + 1 < 8 ? x + 1 : x + 3;
  return tx | (y + 2) << 6;
}

static u32 ph_collect = 0, ph_mcast = 0;
static u32 errors = 0, mask[4] = {~0u, ~0u, ~0u, ~0u};  // which ids send in the gather
#define SENDS(i) (mask[(i) >> 5] >> ((i) & 31) & 1)

static void fill(u32 at, u32 bytes, u32 id, u32 g) {
  u32 slot = slot_of(bytes);
  for (u32 k = 0; k < bytes / 4; k++) write32(at + 4 * k, id << 20 ^ g << 8 ^ k);
  write32(at + slot - 4, g);
}

// Wait for every sender's slot of generation g, checking the first and last data words.
static void collect(u32 region, u32 bytes, u32 n, u32 id, u32 g) {
  u32 slot = slot_of(bytes), last = bytes / 4 - 1;
  for (u32 s = 0; s < n; s++) {
    if (s == id || !SENDS(s)) continue;
    u32 at = region + s * slot;
    WAIT_FAST(read32(at + slot - 4) == g);
    if (read32(at) != (s << 20 ^ g << 8) || read32(at + 4 * last) != (s << 20 ^ g << 8 ^ last)) errors++;
  }
}

static void all_gather(u32 base, u32 bytes, u32 n, u32 id, u32 g, u32 rect, u32 excl) {
  u32 slot = slot_of(bytes), region = base + (g & 1) * n * slot;
  noc_mcast_flush(0);                     // the previous generation's multicast has left STAGE
  fill(STAGE, bytes, id, g);
  if (SENDS(id)) noc_mcast(0, STAGE, region + id * slot, rect, excl, slot);  // the sender is not in its own multicast
  collect(region, bytes, n, id, g);
}

// Coordinator gather: everyone unicasts its slice to core COORD, which waits for all of them and multicasts the
// assembled vector once. Only one multicast sender, so no concurrent multicasts.
#define COORD 55                          // x = 5, y = 5: central
#define CIN   0x60000                     // coordinator's receive slots: 2 parities x workers x slot
#define CG_CNT 0x30100                    // coordinator's arrival counter (NoC atomics need 16-byte alignment)
#define RS_CNT 0x30110                    // reduce-scatter arrival counter, on every core
static u32 cg_expect = 0, rs_expect = 0;  // monotonic: zeroed with the counters at the start of a launch

// Check one sampled slot per generation; checking all 119 costs ~55 cycles each and would dominate the timing.
static void sample(u32 region, u32 bytes, u32 n, u32 skip, u32 g) {
  u32 slot = slot_of(bytes), s = g % n, last = bytes / 4 - 1, at = region + s * slot;
  if (s == skip || !SENDS(s)) return;
  if (read32(at + slot - 4) != g || read32(at) != (s << 20 ^ g << 8) || read32(at + 4 * last) != (s << 20 ^ g << 8 ^ last))
    errors++;
}

static void coord_gather(u32 base, u32 bytes, u32 n, u32 id, u32 g, u32 rect, u32 excl) {
  u32 slot = slot_of(bytes), in = CIN + (g & 1) * n * slot, out = base + (g & 1) * n * slot;
  if (id == COORD) {
    noc_mcast_flush(0);                   // the multicast two generations ago has left this parity's slots
    fill(in + id * slot, bytes, id, g);
    u32 t0 = read32(WALL_CLOCK_L);
    cg_expect += n - 1;
    WAIT_FAST((int)(read32(CG_CNT) - cg_expect) >= 0);
    sample(in, bytes, n, id, g);
    u32 t1 = read32(WALL_CLOCK_L);
    noc_mcast(0, in, out, rect, excl, n * slot);
    noc_mcast_flush(0);
    ph_collect += t1 - t0; ph_mcast += read32(WALL_CLOCK_L) - t1;
    return;
  }
  noc_wait(0, 6, 0);                      // last generation's unicast has left STAGE
  fill(STAGE, bytes, id, g);
  noc_move_paced(0, 1, in + id * slot, coord_of(COORD), 0, slot, STAGE, 6, 0);
  noc_atomic_inc(0, CG_CNT, coord_of(COORD), 1);  // same NIU and VC as the write, so it lands after it
  u32 t0 = read32(WALL_CLOCK_L), lastslot = out + (n - 1 == COORD ? n - 2 : n - 1) * slot;
  WAIT_FAST(read32(lastslot + slot - 4) == g);  // one multicast lands in order: its last slot lands last
  sample(out, bytes, n, COORD, g);
  ph_collect += read32(WALL_CLOCK_L) - t0;
}

static u32 all_reduce(u32 bytes, u32 n, u32 id, u32 g, u32 rect, u32 excl, u32 coordinated) {
  u32 slot = slot_of(bytes), region = RS + (g & 1) * n * slot;
  noc_wait(0, 5, 0);                      // last generation's unicasts have left RS_STAGE
  for (u32 j = 0; j < n; j++) {
    if (j == id) continue;
    u32 src = RS_STAGE + j * slot;
    fill(src, bytes, id, g);
    noc_move_paced(0, 1, region + id * slot, coord_of(j), 0, slot, src, 5, 0);
    noc_atomic_inc(0, RS_CNT, coord_of(j), 1);
  }
  rs_expect += n - 1;
  WAIT_FAST((int)(read32(RS_CNT) - rs_expect) >= 0);
  sample(region, bytes, n, id, g);
  u32 t = read32(WALL_CLOCK_L);
  for (u32 k = 0; k < bytes / 4; k++) {
    u32 sum = 0;
    for (u32 s = 0; s < n; s++) sum += s == id ? 0 : read32(region + s * slot + 4 * k);
    write32(ACC + 4 * k, sum);
  }
  u32 summing = read32(WALL_CLOCK_L) - t;
  if (coordinated) coord_gather(AG2, bytes, n, id, g, rect, excl);
  else all_gather(AG2, bytes, n, id, g, rect, excl);
  return summing;
}

void brisc_step(void) {
  volatile u32 *arg = (volatile u32 *)STEP_ARGS;
  u32 mode = arg[0], iters = arg[1], bytes = arg[2], rect = arg[3], excl = arg[4], coord0 = arg[5];
  u32 host_lo = arg[6], host_hi = arg[7], first_gen = arg[8];
  if (arg[9] | arg[10] | arg[11] | arg[12]) for (u32 i = 0; i < 4; i++) mask[i] = arg[9 + i];
  u32 id = read32(WORKER_ID), n = read32(NUM_WORKERS), summing = 0;
  errors = 0;
  write32(CG_CNT, 0); write32(RS_CNT, 0); cg_expect = rs_expect = 0; ph_collect = ph_mcast = 0;
  fence();
  barrier_all(coord0, rect, excl, n, &epoch);
  u32 t0 = read32(WALL_CLOCK_L);
  for (u32 i = 0; i < iters; i++) {
    u32 g = first_gen + i;
    if (mode == 0) barrier_all(coord0, rect, excl, n, &epoch);
    else if (mode == 1) all_gather(AG, bytes, n, id, g, rect, excl);
    else if (mode == 2) summing += all_reduce(bytes, n, id, g, rect, excl, 0);
    else if (mode == 3) coord_gather(AG, bytes, n, id, g, rect, excl);
    else summing += all_reduce(bytes, n, id, g, rect, excl, 1);
  }
  u32 t1 = read32(WALL_CLOCK_L);
  noc_mcast_flush(0);
  noc_wait(0, 5, 1);
  noc_wait(0, 6, 1);
  barrier_all(coord0, rect, excl, n, &epoch);  // nobody leaves while others still poll its buffers
  write32(OUT, t1 - t0);
  write32(OUT + 4, summing);
  write32(OUT + 8, errors);
  write32(OUT + 12, ph_collect);
  write32(OUT + 16, ph_mcast);
  fence();
  u32 off = id * 64;
  noc_write_host(0, OUT, host_lo + off, host_hi + (host_lo + off < host_lo), 20);
}
