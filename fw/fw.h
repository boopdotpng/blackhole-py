#ifndef TT_FW_H
#define TT_FW_H
#include "abi.h"

typedef unsigned char u8;
typedef unsigned int u32;

#define TT_INLINE static inline __attribute__((always_inline))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

/* Control moves between firmware and kernels by fixed addresses: firmware jumps to KERNEL_<RISC>, a kernel ends with
 * JUMP(FW_<RISC>_RETURN). A kernel is a KERNEL function, linked to start its slot. */
typedef void (*jump_t)(void) __attribute__((noreturn));
#define JUMP(address) (((jump_t)(address))())
#define KERNEL __attribute__((section(".entry"), noreturn)) void

TT_INLINE void fence(void) {
  __asm__ volatile("fence" ::: "memory");
}

TT_INLINE u32 mmio_read32(u32 address) {
  return *(volatile u32 *)address;
}
TT_INLINE u8 mmio_read8(u32 address) {
  return *(volatile u8 *)address;
}

TT_INLINE void mmio_write32(u32 address, u32 value) {
  *(volatile u32 *)address = value;
}
TT_INLINE void mmio_write8(u32 address, u8 value) {
  *(volatile u8 *)address = value;
}

TT_INLINE void zero_words(u32 address, u32 count) {
  volatile u32 *words = (volatile u32 *)address;
  if (count) do { *words++ = 0; } while (--count);
}

TT_INLINE void wait_u8(u32 address, u8 expected) {
  while (mmio_read8(address) != expected) fence();
  fence();
}

TT_INLINE void configure_csr(void) {
  u32 value = 2;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(value) : "memory");
  value = 1u << 18;
  fence();
  __asm__ volatile(
#ifdef TT_TRISC_ID
  "csrc 0x7c0, %0"
#else
  "csrs 0x7c0, %0"
#endif
  :: "r"(value) : "memory");
  value = 2;
  __asm__ volatile("csrc 0x7c0, %0" :: "r"(value) : "memory");
  fence();
  fence();
  value = 8;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(value) : "memory");
}

TT_INLINE void push_tensix_word(u32 word) {
  mmio_write32(0xFFE40000u, word);
}

/* ---- NoC. Each RISC drives one NIU. A NIU has command buffers 0x800 apart: [0] targ lo (the source of a write, the
 * remote of a read), [1] targ mid, [2] targ coord, [3..5] ret lo/mid/coord, [6] packet tag (tid << 10), [7] ctrl,
 * [8] length, [10] atomic data, [16] send/busy. Status counters per transaction id: 0x240 + 4 * tid requests
 * outstanding (reads, write acks), 0x280 + 4 * tid writes not yet sent, 8 bits each. ---- */
#define NOC_CMD(niu, buf) ((volatile u32 *)(0xFFB20000u + (niu) * 0x10000u + (buf) * 0x800u))
#define NOC_OUTSTANDING(niu, tid) (0xFFB20240u + (niu) * 0x10000u + (tid) * 4u)  /* reads and write acks in flight */
#define NOC_OUTGOING(niu, tid) (0xFFB20280u + (niu) * 0x10000u + (tid) * 4u)  /* writes not yet sent out of L1 */

static u32 noc_local_coordinate(u32 niu) {
  return mmio_read32(0xFFB20148u + niu * 0x10000u) & 0xFFFu;
}

static void noc_wait_zero(u32 counter) {
  while (mmio_read32(counter)) {}
  fence();
}

/* The counters are 8 bits: keep room for the packets a command of bytes will add. */
static void noc_wait_issue(u32 counter, u32 bytes) {
  u32 limit = (bytes + NOC_MAX_BURST - 1) / NOC_MAX_BURST >= 128 ? 1 : 129;
  while (mmio_read32(counter) >= limit) {}
}

/* One-off commands on buffer 0, every register written. */
static void noc_submit(
  u32 niu,
  u32 source_address, u32 source_middle, u32 source_coordinate,
  u32 target_address, u32 target_middle, u32 target_coordinate,
  u32 tid, u32 options, u32 bytes, u32 immediate
) {
  volatile u32 *command = NOC_CMD(niu, 0);
  while (command[16] != 0) {}
  command[0] = source_address;
  command[1] = source_middle;
  command[2] = source_coordinate;
  command[3] = target_address;
  command[4] = target_middle;
  command[5] = target_coordinate;
  command[6] = tid << 10;
  command[7] = options;
  command[8] = bytes;
  command[9] = 0;
  command[10] = immediate;
  command[11] = 0;
  /* Flush command-register stores before SEND, and SEND before polling.
   * Compiled C can reach the status load before buffered MMIO stores land. */
  fence();
  command[16] = 1;
  fence();
  while (command[16] != 0) {}
}

/* Returns once the command is accepted: wait for NOC_OUTGOING(niu, 1) before reusing the source. */
static void noc_multicast_write(
  u32 niu, u32 source_address, u32 target_address,
  u32 target_start, u32 target_end, u32 bytes
) {
  noc_wait_issue(NOC_OUTGOING(niu, 1), bytes);
  u32 rectangle = niu == 0
    ? target_end | (target_start << 12)
    : target_start | (target_end << 12);
  noc_submit(
    niu,
    source_address, 0, noc_local_coordinate(niu),
    target_address, 0, rectangle,
    1, 0x80A2u, bytes, 0
  );
}

static void noc_atomic_inc(
  u32 niu, u32 target_address, u32 target_coordinate, u32 value
) {
  noc_wait_zero(NOC_OUTGOING(niu, 1));
  noc_wait_zero(NOC_OUTSTANDING(niu, 1));
  noc_submit(
    niu,
    target_address, 0, target_coordinate,
    4, 0, noc_local_coordinate(niu),
    1, 0x2091u, 0x107Cu, value
  );
  noc_wait_zero(NOC_OUTSTANDING(niu, 1));
}

#ifdef TT_FW_RISC
/* ---- service loops ---- */
#define NIU TT_FW_RISC
#define READ_BUF 1
#define WRITE_BUF 2

/* Buffers 1 (reads) and 2 (writes, non-posted) keep what never changes, so a command programs only its addresses,
 * tag and length, and SEND does not wait to be accepted. */
static void noc_init(void) {
  volatile u32 *r = NOC_CMD(NIU, READ_BUF), *w = NOC_CMD(NIU, WRITE_BUF);
  u32 self = noc_local_coordinate(NIU);
  r[4] = 0; r[5] = self; r[7] = 0x2090u; r[9] = 0; r[10] = 0; r[11] = 0;
  w[1] = 0; w[2] = self; w[7] = 0x2092u; w[9] = 0; w[10] = 0; w[11] = 0;
}

static const u32 dram_coords[] = DRAM_COORDS;

/* Move bytes [offset, offset + size) of the remote side lo:hi to or from local L1 on transaction id tid. Local and
 * remote must agree mod 64. The remote is a 64-bit device address:
 *   bit 63 set     interleaved DRAM, log2 of the page size in bits 56..61 (cq.dram): page p of the buffer lives in
 *                  bank p % BANKS at (p / BANKS) << shift, one command per page
 *   hi 0x1xxxxxxx  PCIe sysmem, one command per NOC_MAX_BURST
 *   otherwise      L1 address lo on the core whose NoC coordinate is hi, one command per NOC_MAX_BURST
 * The DRAM bank and row are found once; after that each page steps to the next bank, and past the last to the next row. */
static void noc_move(u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid) {
  lo += offset;
  hi += lo < offset;
  u32 dram = hi >> 31, page = NOC_MAX_BURST, within = 0, bank = 0, coord = hi;
  if (dram) {
    u32 shift = hi >> 24 & 63, index = lo >> shift | (hi & 0xFFFFFFu) << (32 - shift);
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
  volatile u32 *c = NOC_CMD(NIU, write ? WRITE_BUF : READ_BUF);
  while (c[16]) {}
  c[6] = tid << 10;
  for (u32 done = 0; done < size;) {
    u32 chunk = MIN(size - done, page - within);
    while (c[16]) {}
    if (write) { c[0] = local + done; c[3] = lo + within; c[4] = hi; c[5] = coord; }
    else { c[0] = lo + within; c[1] = hi; c[2] = coord; c[3] = local + done; }
    c[8] = chunk;
    fence();
    c[16] = 1;
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

/* Wait until tid's commands are accepted and its writes have left L1, and with acked, its reads have landed and its
 * writes are acknowledged. */
static void noc_wait(u32 tid, u32 acked) {
  while (NOC_CMD(NIU, READ_BUF)[16] || NOC_CMD(NIU, WRITE_BUF)[16]) {}
  noc_wait_zero(NOC_OUTGOING(NIU, tid));
  if (acked) noc_wait_zero(NOC_OUTSTANDING(NIU, tid));
}

static void read_any(u32 lo, u32 hi, u32 target, u32 size) {
  noc_move(0, lo, hi, 0, size, target, 1);
  noc_wait(1, 1);
}

/* Copy the pushed ring bytes [read, WPTR), at most max and never past the ring end, into target. */
static u32 fetch(u32 read, u32 target, u32 max) {
  u32 offset = read & (RING_SIZE - 1), pushed = mmio_read32(WPTR) - read, bytes = MIN(pushed, MIN(RING_SIZE - offset, max));
  if (bytes) read_any(mmio_read32(RING_LO) + offset, mmio_read32(RING_HI), target, bytes);
  fence();
  return bytes;
}

/* Signals are 8 bytes, not 64-byte aligned: the L1 side sits at the same offset within its 64 bytes. */
static u32 scratch(u32 lo) {
  return SCRATCH + NIU * 0x80u + (lo & 63);
}

static void store64(u32 lo, u32 hi, u32 value_lo, u32 value_hi) {
  u32 source = scratch(lo);
  mmio_write32(source, value_lo);
  mmio_write32(source + 4, value_hi);
  fence();
  noc_move(1, lo, hi, 0, 8, source, 5);
  noc_wait(5, 1);
}

/* The ops every queue has. A packet is [op, a, b, c] as u64s: p[0] op, p[2..3] a, p[4..5] b, p[6..7] c. */
static void common_op(volatile u32 *p) {
  u32 op = p[0];
  if (op == OP_WAIT) {  /* until *a >= b, or *a == b when c */
    u32 source = scratch(p[2]);
    for (;;) {
      read_any(p[2], p[3], source, 8);
      u32 lo = mmio_read32(source), hi = mmio_read32(source + 4);
      if (p[6] ? hi == p[5] && lo == p[4] : hi > p[5] || (hi == p[5] && lo >= p[4])) break;
    }
  } else if (op == OP_STORE) {  /* *a = b */
    store64(p[2], p[3], p[4], p[5]);
  } else if (op == OP_TIMESTAMP) {  /* *a = wall clock */
    u32 lo, hi;
    do {
      hi = mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_H);
      lo = mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_L);
    } while (hi != mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_H));
    store64(p[2], p[3], lo, hi);
  } else {
    for (;;) {}
  }
}
#endif

#endif
