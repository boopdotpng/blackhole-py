#include "fw.h"

#ifndef TT_PCIE_MID
#error "prefetch firmware requires TT_PCIE_MID"
#endif

#define ALIGN 64u
#define PAGE_SIZE 4096u
#define HOST_ISSUE_SIZE (4u << 20)
#define CQ_STATE 0x1000u
#define PREFETCH_DOORBELL CQ_STATE
#define PREFETCH_PCIE_BASE (CQ_STATE + 0x08u)
#define PREFETCH_READ_PTR (CQ_STATE + 0x0Cu)
#define PREFETCH_DISPATCH_READ (CQ_STATE + 0x10u)
#define PREFETCH_TRACE_ACTIVE (CQ_STATE + 0x14u)
#define PREFETCH_TRACE_CURSOR (CQ_STATE + 0x18u)
#define PREFETCH_TRACE_END (CQ_STATE + 0x1Cu)
#define PREFETCH_RECORD_SIZE (CQ_STATE + 0x20u)
#define PREFETCH_READ_PUBLISH (CQ_STATE + 0x30u)
#define PREFETCH_DISPATCH_PUBLISH (CQ_STATE + 0x40u)
#define PREFETCH_STAGING 0x20000u
#define DISPATCH_PUBLISHED CQ_STATE
#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_PAGES 320u
#define DISPATCH_RING_END (DISPATCH_RING_BASE + DISPATCH_RING_PAGES * PAGE_SIZE)
#define DISPATCH_SCRATCH DISPATCH_RING_END
#define DISPATCH_READ_PUBLISH (DISPATCH_SCRATCH + 0x60u)
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define DISPATCH_COORD ((3u << 6) | 14u)

#define PACKET_OP 0u
#define PACKET_TARGET_COUNT 2u
#define PACKET_TOTAL_SIZE 4u
#define PACKET_ADDRESS 8u
#define PACKET_DATA_SIZE 12u
#define PACKET_DRAM_COORD 16u
#define PACKET_TRACE_SIZE 16u

enum {
  OP_PAD = 0,
  OP_DRAM_RECORD = 4,
  OP_TRACE = 6,
};

static void publish_dispatch(u32 put) {
  breadcrumb(0x107u, put, mmio_read32(PREFETCH_DISPATCH_READ), 0, 0);
  mmio_write32(PREFETCH_DISPATCH_PUBLISH, put);
  fence();
  noc_write(
    0, PREFETCH_DISPATCH_PUBLISH, DISPATCH_PUBLISHED,
    0, DISPATCH_COORD, 4, 0
  );
}

void firmware_boot(void) {
  u32 ring = DISPATCH_RING_BASE;
  u32 put = 0;
  u32 read_lo = 0;
  u32 read_hi = 0;
  mmio_write32(PREFETCH_DISPATCH_READ, 0);
  mmio_write32(PREFETCH_TRACE_ACTIVE, 0);
  breadcrumb(0x100u, ring, put, read_lo, read_hi);

  for (;;) {
    u32 cursor;
    if (mmio_read32(PREFETCH_TRACE_ACTIVE) != 0) {
      cursor = mmio_read32(PREFETCH_TRACE_CURSOR);
    } else {
      u32 high_before, low, high_after;
      do {
        high_before = mmio_read32(PREFETCH_DOORBELL + 4);
        low = mmio_read32(PREFETCH_DOORBELL);
        high_after = mmio_read32(PREFETCH_DOORBELL + 4);
      } while (high_before != high_after);
      if (high_after == read_hi && low == read_lo) {
        fence();
        continue;
      }
      cursor = mmio_read32(PREFETCH_PCIE_BASE);
      cursor += read_lo & (HOST_ISSUE_SIZE - 1);
    }

read_header:
    breadcrumb(0x102u, cursor, put, read_lo, read_hi);
    noc_read(
      0, cursor, TT_PCIE_MID, PCIE_COORD,
      PREFETCH_STAGING, ALIGN
    );
    u8 op = mmio_read8(PREFETCH_STAGING + PACKET_OP);
    u32 size;
    if (mmio_read32(PREFETCH_TRACE_ACTIVE) == 0) {
      if (op == OP_PAD) {
        size = mmio_read32(PREFETCH_STAGING + PACKET_TOTAL_SIZE);
        goto advance_issue;
      }
      if (op == OP_TRACE) {
        cursor = mmio_read32(PREFETCH_STAGING + PACKET_ADDRESS);
        size = mmio_read32(PREFETCH_STAGING + PACKET_TRACE_SIZE);
        mmio_write32(PREFETCH_TRACE_CURSOR, cursor);
        mmio_write32(PREFETCH_TRACE_END, cursor + size);
        mmio_write32(PREFETCH_TRACE_ACTIVE, 1);
        goto read_header;
      }
    }

    size = mmio_read32(PREFETCH_STAGING + PACKET_TOTAL_SIZE);
    breadcrumb(0x103u, op, size, cursor, mmio_read32(PREFETCH_TRACE_ACTIVE));
    mmio_write32(PREFETCH_RECORD_SIZE, size);
    u32 source = cursor;
    u32 destination = PREFETCH_STAGING;
    u32 left = size;
    while (left != 0) {
      u32 chunk = left < TT_NOC_MAX_PACKET_BYTES
        ? left : TT_NOC_MAX_PACKET_BYTES;
      noc_read(
        0, source, TT_PCIE_MID, PCIE_COORD,
        destination, chunk
      );
      source += chunk;
      destination += chunk;
      left -= chunk;
    }

    source = PREFETCH_STAGING;
    if (mmio_read8(source + PACKET_OP) == OP_DRAM_RECORD) {
      u32 address = mmio_read32(source + PACKET_ADDRESS);
      u32 bytes = mmio_read32(source + PACKET_DATA_SIZE);
      u32 coordinate = mmio_read32(source + PACKET_DRAM_COORD);
      noc_read(0, address, 0, coordinate, PREFETCH_STAGING, bytes);
      source = PREFETCH_STAGING;
    }
    size = mmio_read32(source + PACKET_TOTAL_SIZE);
    u32 pages = (size + PAGE_SIZE - 1) >> 12;

    u32 remaining = (DISPATCH_RING_END - ring) >> 12;
    breadcrumb(
      0x104u, put, mmio_read32(PREFETCH_DISPATCH_READ),
      pages, remaining
    );
    if (remaining < pages) {
      while (DISPATCH_RING_PAGES -
             (put - mmio_read32(PREFETCH_DISPATCH_READ)) < remaining) {
        fence();
      }
      put += remaining;
      mmio_write8(DISPATCH_READ_PUBLISH + PACKET_OP, OP_PAD);
      *(volatile u16 *)(DISPATCH_READ_PUBLISH + PACKET_TARGET_COUNT) = 0;
      mmio_write32(
        DISPATCH_READ_PUBLISH + PACKET_TOTAL_SIZE,
        remaining << 12
      );
      mmio_write32(DISPATCH_READ_PUBLISH + PACKET_ADDRESS, 0);
      mmio_write32(DISPATCH_READ_PUBLISH + PACKET_DATA_SIZE, 0);
      noc_write(
        0, DISPATCH_READ_PUBLISH, ring, 0, DISPATCH_COORD,
        16, 0
      );
      publish_dispatch(put);
      ring = DISPATCH_RING_BASE;
    }

    while (DISPATCH_RING_PAGES -
           (put - mmio_read32(PREFETCH_DISPATCH_READ)) < pages) {
      fence();
    }
    put += pages;
    breadcrumb(0x105u, put, ring, pages, size);
    destination = ring;
    left = size;
    while (left != 0) {
      u32 chunk = left < TT_NOC_MAX_PACKET_BYTES
        ? left : TT_NOC_MAX_PACKET_BYTES;
      noc_write(
        0, source, destination, 0, DISPATCH_COORD,
        chunk, 0
      );
      source += chunk;
      destination += chunk;
      left -= chunk;
    }
    publish_dispatch(put);
    ring += pages << 12;
    if (ring == DISPATCH_RING_END) ring = DISPATCH_RING_BASE;

    size = mmio_read32(PREFETCH_RECORD_SIZE);
    if (mmio_read32(PREFETCH_TRACE_ACTIVE) != 0) {
      cursor = mmio_read32(PREFETCH_TRACE_CURSOR) + size;
      mmio_write32(PREFETCH_TRACE_CURSOR, cursor);
      if (cursor < mmio_read32(PREFETCH_TRACE_END)) goto read_header;
      mmio_write32(PREFETCH_TRACE_ACTIVE, 0);
      size = ALIGN;
    }

advance_issue:
    breadcrumb(0x106u, size, read_lo, read_hi, cursor);
    {
      u32 previous = read_lo;
      read_lo += size;
      read_hi += read_lo < previous;
    }
    mmio_write32(PREFETCH_READ_PUBLISH, read_lo);
    mmio_write32(PREFETCH_READ_PUBLISH + 4, read_hi);
    fence();
    destination = mmio_read32(PREFETCH_READ_PTR);
    noc_write(
      0, PREFETCH_READ_PUBLISH, destination,
      TT_PCIE_MID, PCIE_COORD, 8, 0
    );
  }
}
