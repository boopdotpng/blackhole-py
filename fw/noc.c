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

void noc_init(u32 niu) {
  volatile u32 *r = CMD_BUF(niu, READ_BUF), *w = CMD_BUF(niu, WRITE_BUF);
  u32 self = noc_coord(niu);
  r[RET_MID] = 0; r[RET_COORD] = self; r[CTRL] = CTRL_RESP_MARKED | STATIC_VC(1);
  w[TARG_MID] = 0; w[TARG_COORD] = self; w[CTRL] = CTRL_WRITE | CTRL_RESP_MARKED | STATIC_VC(1);
  r[AT_LEN_BE_1] = w[AT_LEN_BE_1] = 0;
  r[AT_DATA] = w[AT_DATA] = 0;
  r[BRCST_EXCLUDE] = w[BRCST_EXCLUDE] = 0;
}

void noc_move_paced(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap) {
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
    if (cap) while (read32(out_reg) >= cap) {}
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
