#include "fw.h"
#include "cq.h"

#ifndef TT_PCIE_MID
#error "prefetch firmware requires TT_PCIE_MID"
#endif

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
  breadcrumb(0x100u, ring, put, read_lo, read_hi);

  for (;;) {
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
    u32 cursor = mmio_read32(PREFETCH_PCIE_BASE) +
                 (read_lo & (HOST_ISSUE_SIZE - 1));
    breadcrumb(0x102u, cursor, put, read_lo, read_hi);
    noc_read(0, cursor, TT_PCIE_MID, PCIE_COORD, PREFETCH_STAGING, ALIGN);
    u8 op = mmio_read8(PREFETCH_STAGING + PACKET_OP);
    u32 size = mmio_read32(PREFETCH_STAGING + PACKET_TOTAL_SIZE);
    if (op == OP_PAD) goto advance_issue;
    breadcrumb(0x103u, op, size, cursor, 0);
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
    u32 read_destination = mmio_read32(PREFETCH_READ_PTR);
    noc_write(
      0, PREFETCH_READ_PUBLISH, read_destination,
      TT_PCIE_MID, PCIE_COORD, 8, 0
    );
  }
}
