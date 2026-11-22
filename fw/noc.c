#include "noc.h"

static const unsigned short dram_ports[8][3] = {
  {17 | 14 << 6, 17 | 13 << 6, 17 | 12 << 6},
  {17 | 15 << 6, 17 | 16 << 6, 17 | 17 << 6},
  {17 | 18 << 6, 17 | 19 << 6, 17 | 20 << 6},
  {17 | 21 << 6, 17 | 22 << 6, 17 | 23 << 6},
  {18 | 14 << 6, 18 | 13 << 6, 18 | 12 << 6},
  {18 | 17 << 6, 18 | 16 << 6, 18 | 15 << 6},
  {18 | 20 << 6, 18 | 19 << 6, 18 | 18 << 6},
  {18 | 23 << 6, 18 | 22 << 6, 18 | 21 << 6},
};
#ifndef BANKS
#define BANKS 8
#endif
_Static_assert(BANKS == 7 || BANKS == 8, "Blackhole has 8 DRAM banks (7 on p100a)");
#define PCIE_COORD (1u << 24 | 24 << 6 | 19)

#define NIU(niu) (0xFFB20000 + (niu) * 0x10000)
#define CMD_BUF(niu, buf) ((volatile u32 *)(NIU(niu) + (buf) * 0x800))
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, AT_LEN_BE_1, AT_DATA,
       BRCST_EXCLUDE, CMD_CTRL = 16 };
enum { MCAST_BUF, READ_BUF, WRITE_BUF };

#define NODE_ID(niu) (NIU(niu) + 0x148)
#define OUTSTANDING(niu, tid) (NIU(niu) + 0x240 + (tid) * 4)
#define OUTGOING(niu, tid) (NIU(niu) + 0x280 + (tid) * 4)

#define ATOMIC 0x1
#define WRITE 0x2
#define RESP_MARKED 0x10
#define BROADCAST 0x20
#define STATIC_VC(vc) (0x80 | (vc) << 13)
#define AT_INCREMENT (1 << 12 | 31 << 2)

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

u32 noc_coord(u32 niu) { return read32(NODE_ID(niu)) & 0xFFF; }

void noc_init(u32 niu) {
  volatile u32 *r = CMD_BUF(niu, READ_BUF), *w = CMD_BUF(niu, WRITE_BUF);
  u32 self = noc_coord(niu);
  r[RET_MID] = 0; r[RET_COORD] = self; r[CTRL] = RESP_MARKED | STATIC_VC(1);
  w[TARG_MID] = 0; w[TARG_COORD] = self; w[CTRL] = WRITE | RESP_MARKED | STATIC_VC(1);
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

void noc_dram_read_stream(u32 bank_start, u32 addr_start, u32 page, u32 pages, u32 local, u32 local_mask, u32 tid, u32 cap) {
  volatile u32 *c = CMD_BUF(0, READ_BUF);
  u32 out_reg = OUTSTANDING(0, tid);
  u32 bank = bank_start % BANKS, port = bank_start % 3, addr = addr_start, off = 0;
  wait_idle(c);
  c[PACKET_TAG] = tid << 10;
  c[TARG_MID] = 0;
  c[AT_LEN_BE] = page;
  for (u32 i = 0; i < pages; i++) {
    if (cap) while (read32(out_reg) >= cap) {}
    wait_idle(c);
    c[TARG_LO] = addr;
    c[TARG_COORD] = dram_ports[bank][port];
    c[RET_LO] = local + off;
    send(c);
    off = (off + page) & local_mask;
    if (++bank == BANKS) {
      bank = 0;
      addr += page;
      if (++port == 3) port = 0;
    }
  }
}

void noc_wait(u32 niu, u32 tid, u32 acked) {
  wait_idle(CMD_BUF(niu, READ_BUF));
  wait_idle(CMD_BUF(niu, WRITE_BUF));
  wait_zero(OUTGOING(niu, tid));
  if (acked) wait_zero(OUTSTANDING(niu, tid));
}

void noc_read(u32 niu, u32 lo, u32 hi, u32 local, u32 size) {
  noc_move_paced(niu, 0, lo, hi, 0, size, local, 1, 0);
  noc_wait(niu, 1, 1);
}

void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size) {
  noc_move_paced(niu, 1, lo, hi, 0, size, local, 5, 0);
  noc_wait(niu, 5, 1);
}

void noc_mcast(u32 niu, u32 local, u32 remote, u32 rect, u32 exclude, u32 size) {
  volatile u32 *c = CMD_BUF(niu, MCAST_BUF);
  if (niu == 0) rect = rect >> 12 | (rect & 0xFFF) << 12;
  for (u32 done = 0; done < size; done += NOC_MAX_BURST) {
    while (read32(OUTGOING(niu, 1)) > 128) {}
    wait_idle(c);
    c[TARG_LO] = local + done; c[TARG_MID] = 0; c[TARG_COORD] = noc_coord(niu);
    c[RET_LO] = remote + done; c[RET_MID] = 0; c[RET_COORD] = rect;
    c[PACKET_TAG] = 1 << 10;
    c[CTRL] = WRITE | BROADCAST | STATIC_VC(5);
    c[AT_LEN_BE] = MIN(size - done, NOC_MAX_BURST);
    c[AT_LEN_BE_1] = 0; c[AT_DATA] = 0; c[BRCST_EXCLUDE] = exclude;
    send(c);
  }
  wait_idle(c);
}

void noc_mcast_flush(u32 niu) { wait_zero(OUTGOING(niu, 1)); }

void noc_atomic_inc(u32 niu, u32 remote, u32 coord, u32 value) {
  volatile u32 *c = CMD_BUF(niu, MCAST_BUF);
  wait_idle(c);
  c[TARG_LO] = remote; c[TARG_MID] = 0; c[TARG_COORD] = coord;
  c[PACKET_TAG] = 1 << 10;
  c[CTRL] = ATOMIC | STATIC_VC(1);
  c[AT_LEN_BE] = AT_INCREMENT;
  c[AT_LEN_BE_1] = 0; c[AT_DATA] = value; c[BRCST_EXCLUDE] = 0;
  send(c);
  wait_idle(c);
}

void noc_write_host(u32 niu, u32 local, u32 lo, u32 hi, u32 size) {
  volatile u32 *c = CMD_BUF(niu, WRITE_BUF);
  wait_idle(c);
  u32 base = read32(OUTSTANDING(niu, 5));
  c[TARG_LO] = local; c[TARG_MID] = 0; c[TARG_COORD] = noc_coord(niu);
  c[RET_LO] = lo; c[RET_MID] = hi; c[RET_COORD] = PCIE_COORD;
  c[PACKET_TAG] = 5 << 10;
  c[CTRL] = WRITE | RESP_MARKED | STATIC_VC(1);
  c[AT_LEN_BE] = size;
  c[AT_LEN_BE_1] = 0; c[AT_DATA] = 0; c[BRCST_EXCLUDE] = 0;
  send(c);
  wait_idle(c);
  while (read32(OUTSTANDING(niu, 5)) != base) {}
  fence();
}
