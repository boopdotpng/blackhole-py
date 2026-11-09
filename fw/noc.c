#include "noc.h"

/* p150: first NoC endpoint of each DRAM bank, and PCIe */
static const u32 dram_coords[] = {17 | 14 << 6, 17 | 15 << 6, 17 | 18 << 6, 17 | 21 << 6,
                                  18 | 14 << 6, 18 | 17 << 6, 18 | 20 << 6, 18 | 23 << 6};
#define BANKS 8
#define PCIE_COORD (1u << 24 | 24 << 6 | 19)

/* Writes: TARG is the local source, RET the remote destination. Reads and atomics: TARG is the remote. */
#define NIU(niu) (0xFFB20000 + (niu) * 0x10000)
#define CMD_BUF(niu, buf) ((volatile u32 *)(NIU(niu) + (buf) * 0x800))
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, AT_LEN_BE_1, AT_DATA,
       BRCST_EXCLUDE, CMD_CTRL = 16 };
enum { MCAST_BUF, READ_BUF, WRITE_BUF };

#define NODE_ID(niu) (NIU(niu) + 0x148)                       /* NOC_ID_LOGICAL */
#define OUTSTANDING(niu, tid) (NIU(niu) + 0x240 + (tid) * 4)  /* reads and write acks in flight */
#define OUTGOING(niu, tid) (NIU(niu) + 0x280 + (tid) * 4)     /* writes not yet sent out of L1 */

#define ATOMIC 0x1
#define WRITE 0x2
#define RESP_MARKED 0x10
#define BROADCAST 0x20
#define STATIC_VC(vc) (0x80 | (vc) << 13)
#define AT_INCREMENT (1 << 12 | 31 << 2)  /* increment, wrapping at bit 31 */

static void wait_zero(u32 counter) {
  while (read32(counter)) {}
  fence();
}

/* without the second fence the busy poll can pass the SEND store */
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

void noc_move(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid) {
  lo += offset;
  hi += lo < offset;
  u32 dram = hi >> 31, page = NOC_MAX_BURST, within = 0, bank = 0, coord = hi;
  if (dram) {
    u32 shift = hi >> 24 & 63, index = lo >> shift | (hi & 0xFFFFFF) << (32 - shift);
    page = 1u << shift;
    within = lo & (page - 1);
    bank = index % BANKS;
    lo = index / BANKS << shift;
    hi = 0;
    coord = dram_coords[bank];
  } else if (hi >> 28) {
    coord = PCIE_COORD;
  } else {
    hi = 0;
  }
  volatile u32 *c = CMD_BUF(niu, write ? WRITE_BUF : READ_BUF);
  wait_idle(c);
  c[PACKET_TAG] = tid << 10;
  for (u32 done = 0; done < size;) {
    u32 chunk = MIN(size - done, page - within);
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
      if (++bank == BANKS) { bank = 0; lo += page; }
      coord = dram_coords[bank];
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
  noc_move(niu, 0, lo, hi, 0, size, local, 1);
  noc_wait(niu, 1, 1);
}

void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size) {
  noc_move(niu, 1, lo, hi, 0, size, local, 5);
  noc_wait(niu, 5, 1);
}

void noc_mcast(u32 niu, u32 local, u32 remote, u32 start, u32 end, u32 size) {
  volatile u32 *c = CMD_BUF(niu, MCAST_BUF);
  u32 rect = niu == 0 ? end | start << 12 : start | end << 12;
  for (u32 done = 0; done < size; done += NOC_MAX_BURST) {
    while (read32(OUTGOING(niu, 1)) > 128) {}
    wait_idle(c);
    c[TARG_LO] = local + done; c[TARG_MID] = 0; c[TARG_COORD] = noc_coord(niu);
    c[RET_LO] = remote + done; c[RET_MID] = 0; c[RET_COORD] = rect;
    c[PACKET_TAG] = 1 << 10;
    c[CTRL] = WRITE | BROADCAST | STATIC_VC(4);
    c[AT_LEN_BE] = MIN(size - done, NOC_MAX_BURST);
    c[AT_LEN_BE_1] = 0; c[AT_DATA] = 0; c[BRCST_EXCLUDE] = 0;
    send(c);
  }
  wait_idle(c);
}

void noc_mcast_flush(u32 niu) { wait_zero(OUTGOING(niu, 1)); }

/* Posted: no response, so nothing to wait for once the command buffer has sent it. */
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
