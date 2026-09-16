#include "fw.h"

#define PUBLISH (CQ_STATE + 0x40u)
#define WRAP_HEADER (CQ_STATE + 0x60u)

static void wait_space(u32 put, u32 pages) {
  while (DISPATCH_RING_PAGES - (put - mmio_read32(PREFETCH_DISPATCH_READ)) < pages) fence();
}

static void publish(u32 put) {
  mmio_write32(PUBLISH, put);
  fence();
  noc_write(0, PUBLISH, DISPATCH_PUBLISHED, 0, DISPATCH_COORD, 4, 0);
}

void firmware_boot(void) {
  u32 ring = DISPATCH_RING_BASE, put = 0, read_lo = 0, read_hi = 0;
  u32 trace_cursor = 0, trace_end = 0, in_trace = 0;
  u32 middle = mmio_read32(BOOT_PCIE_MID);
  mmio_write32(PREFETCH_DISPATCH_READ, 0);
  for (;;) {
    u32 cursor;
    if (in_trace) {
      cursor = trace_cursor;
    } else {
      u32 hi, lo;
      do {
        fence();
        do {
          hi = mmio_read32(PREFETCH_DOORBELL + 4);
          lo = mmio_read32(PREFETCH_DOORBELL);
        } while (hi != mmio_read32(PREFETCH_DOORBELL + 4));
      } while (lo == read_lo && hi == read_hi);
      cursor = mmio_read32(PREFETCH_PCIE_BASE) + (read_lo & (HOST_ISSUE_SIZE - 1));
    }
    noc_read(0, cursor, middle, PCIE_COORD, PREFETCH_STAGING, ALIGN);
    u32 op = mmio_read8(PREFETCH_STAGING + PACKET_OP);
    u32 consumed = mmio_read32(PREFETCH_STAGING + PACKET_TOTAL_SIZE);
    if (!in_trace && op == OP_TRACE) {
      trace_cursor = mmio_read32(PREFETCH_STAGING + PACKET_TRACE_SOURCE_LO);
      trace_end = trace_cursor + mmio_read32(PREFETCH_STAGING + PACKET_TRACE_SIZE);
      in_trace = 1;
      continue;
    }
    if (!in_trace && op == OP_PAD) goto advance_issue;
    for (u32 offset = 0; offset < consumed;) {
      u32 chunk = consumed - offset;
      if (chunk > TT_NOC_MAX_PACKET_BYTES) chunk = TT_NOC_MAX_PACKET_BYTES;
      noc_read(0, cursor + offset, middle, PCIE_COORD, PREFETCH_STAGING + offset, chunk);
      offset += chunk;
    }
    if (op == OP_DRAM_RECORD) {
      u32 source = mmio_read32(PREFETCH_STAGING + PACKET_ADDRESS);
      u32 bytes = mmio_read32(PREFETCH_STAGING + PACKET_DATA_SIZE);
      u32 coord = mmio_read32(PREFETCH_STAGING + PACKET_DRAM_COORD);
      noc_read(0, source, 0, coord, PREFETCH_STAGING, bytes);
    }
    u32 size = mmio_read32(PREFETCH_STAGING + PACKET_TOTAL_SIZE);
    u32 pages = (size + PAGE_SIZE - 1) / PAGE_SIZE;
    u32 remaining = (DISPATCH_RING_END - ring) / PAGE_SIZE;
    if (remaining < pages) {
      wait_space(put, remaining);
      mmio_write32(WRAP_HEADER, OP_PAD);
      mmio_write32(WRAP_HEADER + PACKET_TOTAL_SIZE, remaining * PAGE_SIZE);
      mmio_write32(WRAP_HEADER + PACKET_ADDRESS, 0);
      mmio_write32(WRAP_HEADER + PACKET_DATA_SIZE, 0);
      fence();
      noc_write(0, WRAP_HEADER, ring, 0, DISPATCH_COORD, 16, 0);
      put += remaining;
      publish(put);
      ring = DISPATCH_RING_BASE;
    }
    wait_space(put, pages);
    for (u32 offset = 0; offset < size;) {
      u32 chunk = size - offset;
      if (chunk > TT_NOC_MAX_PACKET_BYTES) chunk = TT_NOC_MAX_PACKET_BYTES;
      noc_write(0, PREFETCH_STAGING + offset, ring + offset, 0, DISPATCH_COORD, chunk, 0);
      offset += chunk;
    }
    put += pages;
    publish(put);
    ring += pages * PAGE_SIZE;
    if (ring == DISPATCH_RING_END) ring = DISPATCH_RING_BASE;
    if (in_trace) {
      trace_cursor += consumed;
      if (trace_cursor < trace_end) continue;
      in_trace = 0;
      consumed = ALIGN;
    }
advance_issue:
    {
      u32 previous = read_lo;
      read_lo += consumed;
      read_hi += read_lo < previous;
      mmio_write32(PREFETCH_READ_PUBLISH, read_lo);
      mmio_write32(PREFETCH_READ_PUBLISH + 4, read_hi);
      fence();
      noc_write(0, PREFETCH_READ_PUBLISH, mmio_read32(PREFETCH_READ_PTR), middle, PCIE_COORD, 8, 0);
    }
  }
}
