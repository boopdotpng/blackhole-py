#include "noc.h"

static const unsigned short dram_ports[DRAM_BANKS][3] = DRAM_PORT_COORDS;
#ifndef BANKS
#define BANKS 8
#endif
_Static_assert(BANKS == 7 || BANKS == 8, "Blackhole has 8 DRAM banks (7 on p100a)");

static void wait_zero(u32 counter) {
  while (read32(counter)) {}
  fence();
}

static void send(volatile u32 *c) {
  fence();
  c[CMD_CTRL] = 1;
  fence();
}

static void wait_idle(volatile u32 *c) { while (c[CMD_CTRL]) {} }

static u32 noc_coord(u32 niu) { return read32(NODE_ID(niu)) & 0xFFF; }

static u32 worker_coord(u32 wx, u32 wy) {
  return ((wy + 2) << 6) | (wx + (wx >= 7 ? 3 : 1));
}

// Caller supplies a one-dimensional rectangle containing the sender. Data
// and its readiness flag must use this same ordered VC and command buffer.
void noc_mcast(u32 niu, u32 local, u32 remote, u32 rect_packed, u32 size, u32 tid, u32 include_sender) {
  u32 c0 = worker_coord(rect_packed & 63, (rect_packed >> 6) & 63);
  u32 c1 = worker_coord((rect_packed >> 12) & 63, (rect_packed >> 18) & 63);
  u32 rect = niu ? (c1 << 12) | c0 : (c0 << 12) | c1;
  volatile u32 *c = CMD_BUF(niu, MCAST_BUF);
  for (u32 done = 0; done < size; done += NOC_MAX_BURST) {
    while (read32(OUTGOING(niu, tid)) > 128) {}
    wait_idle(c);
    c[TARG_LO] = local + done; c[TARG_MID] = 0; c[TARG_COORD] = noc_coord(niu);
    c[RET_LO] = remote + done; c[RET_MID] = 0; c[RET_COORD] = rect;
    c[PACKET_TAG] = tid << 10;
    c[CTRL] = CTRL_WRITE | CTRL_BRCST_PACKET | STATIC_VC(4) | (include_sender ? CTRL_BRCST_SRC_INCLUDE : 0);
    c[AT_LEN_BE] = MIN(size - done, NOC_MAX_BURST);
    c[AT_LEN_BE_1] = 0; c[AT_DATA] = 0; c[BRCST_EXCLUDE] = 0;
    send(c);
  }
}

void noc_inc_worker(u32 niu, u32 remote, u32 target_xy_packed, u32 tid) {
  volatile u32 *c = CMD_BUF(niu, ATOMIC_BUF);
  wait_idle(c);
  c[TARG_LO] = remote; c[TARG_MID] = 0;
  c[TARG_COORD] = worker_coord(target_xy_packed & 63, (target_xy_packed >> 6) & 63);
  c[PACKET_TAG] = tid << 10;
  c[CTRL] = 1u | STATIC_VC(1);
  c[AT_LEN_BE] = (1u << 12) | (31u << 2);
  c[AT_LEN_BE_1] = 0; c[AT_DATA] = 1; c[BRCST_EXCLUDE] = 0;
  send(c);
}

void noc_init(u32 niu) {
  volatile u32 *r = CMD_BUF(niu, READ_BUF), *w = CMD_BUF(niu, WRITE_BUF);
  u32 self = noc_coord(niu);
  r[RET_MID] = 0; r[RET_COORD] = self; r[CTRL] = CTRL_RESP_MARKED | STATIC_VC(1);
  w[TARG_MID] = 0; w[TARG_COORD] = self; w[CTRL] = CTRL_WRITE | CTRL_RESP_MARKED | STATIC_VC(1);
  r[AT_LEN_BE_1] = w[AT_LEN_BE_1] = 0;
  r[AT_DATA] = w[AT_DATA] = 0;
  r[BRCST_EXCLUDE] = w[BRCST_EXCLUDE] = 0;
}

void noc_move_paced_base(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap, u32 baseline) {
  lo += offset;
  hi += lo < offset;
  u32 dram = hi >> 31, page = NOC_MAX_BURST, within = 0, bank = 0, port = 0, coord = hi;
  if (dram) {
    u32 shift = hi >> 24 & 63, index;
    if (shift) {
      index = lo >> shift | (hi & 0xFFFFFF) << (32 - shift);
      page = 1u << shift;
      within = lo & (page - 1);
    } else {
      u32 upper = hi & 0xFFFF;
      page = ((hi >> 16 & 255) + 1) * 64;
      u32 rem = lo % page + upper * (0xFFFFFFFFu % page + 1);
      index = lo / page + upper * (0xFFFFFFFFu / page) + rem / page;
      within = rem % page;
    }
    bank = index % BANKS;
    u32 stripe = index / BANKS;
    port = stripe % 3;
    lo = stripe * page;
    hi = 0;
    coord = dram_ports[bank][port];
  } else if (hi >> 28) {
    coord = PCIE_COORD;
  } else {
    hi = 0;
  }
  volatile u32 *c = CMD_BUF(niu, write ? WRITE_BUF : READ_BUF);
  u32 out_reg = OUTSTANDING(niu, tid);
  wait_idle(c);
  c[PACKET_TAG] = tid << 10;
  for (u32 done = 0; done < size;) {
    u32 chunk = MIN(size - done, page - within);
    if (cap) while ((u32)(read32(out_reg) - baseline) >= cap) {}
    wait_idle(c);
    if (write) { c[TARG_LO] = local + done; c[RET_LO] = lo + within; c[RET_MID] = hi; c[RET_COORD] = coord; }
    else { c[TARG_LO] = lo + within; c[TARG_MID] = hi; c[TARG_COORD] = coord; c[RET_LO] = local + done; }
    c[AT_LEN_BE] = chunk;
    send(c);
    done += chunk;
    if (!dram) {
      lo += chunk;
      hi += lo < chunk;
    } else if ((within += chunk) == page) {
      within = 0;
      if (++bank == BANKS) {
        bank = 0;
        lo += page;
        if (++port == 3) port = 0;
      }
      coord = dram_ports[bank][port];
    }
  }
}

void noc_move_paced(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap) {
  noc_move_paced_base(niu, write, lo, hi, offset, size, local, tid, cap, 0);
}

void noc_wait(u32 niu, u32 tid, u32 acked) {
  wait_idle(CMD_BUF(niu, READ_BUF));
  wait_idle(CMD_BUF(niu, WRITE_BUF));
  wait_zero(OUTGOING(niu, tid));
  if (acked) wait_zero(OUTSTANDING(niu, tid));
}

void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size) {
  noc_move_paced(niu, 1, lo, hi, 0, size, local, 5, 0);
  noc_wait(niu, 5, 1);
}

void noc_atomic_inc(u32 niu, u32 remote, u32 coord) {
  volatile u32 *c = CMD_BUF(niu, ATOMIC_BUF);
  wait_idle(c);
  c[TARG_LO] = remote; c[TARG_MID] = 0; c[TARG_COORD] = coord;
  c[PACKET_TAG] = 1 << 10;
  c[CTRL] = 1 | STATIC_VC(1);
  c[AT_LEN_BE] = 1 << 12 | 31 << 2;
  c[AT_LEN_BE_1] = 0; c[AT_DATA] = 1; c[BRCST_EXCLUDE] = 0;
  send(c);
  wait_idle(c);
}
