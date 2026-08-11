#include "fw.h"

#define ALIGN 64u
#define PAGE_SIZE 4096u
#define CQ_STATE 0x1000u
#define PREFETCH_DISPATCH_READ (CQ_STATE + 0x10u)
#define DISPATCH_PUBLISHED CQ_STATE
#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_PAGES 320u
#define DISPATCH_RING_END (DISPATCH_RING_BASE + DISPATCH_RING_PAGES * PAGE_SIZE)
#define DISPATCH_SCRATCH DISPATCH_RING_END
#define DISPATCH_GO (DISPATCH_SCRATCH + 0x40u)
#define DISPATCH_DONE_COUNT (DISPATCH_SCRATCH + 0x50u)
#define DISPATCH_READ_PUBLISH (DISPATCH_SCRATCH + 0x60u)
#define DISPATCH_DRAM_PUT (DISPATCH_SCRATCH + 0x80u)
#define DISPATCH_DRAM_READ (DISPATCH_SCRATCH + 0x90u)
#define DRAM_PUBLISHED CQ_STATE
#define DRAM_READ_PUBLISH (CQ_STATE + 0x60u)
#define DRAM_QUEUE_BASE 0x2000u
#define DRAM_QUEUE_ENTRIES 32u
#define PREFETCH_COORD ((2u << 6) | 14u)
#define DRAM_COORD ((4u << 6) | 14u)
#define GO_SIGNAL 0x0373u

#define PACKET_OP 0u
#define PACKET_TARGET_COUNT 2u
#define PACKET_TOTAL_SIZE 4u
#define PACKET_ADDRESS 8u
#define PACKET_DATA_SIZE 12u
#define PACKET_WRITE_TARGETS 16u
#define PACKET_RUN_TEMPLATE 16u
#define PACKET_RUN_TARGETS 24u

enum {
  OP_PAD = 0,
  OP_UNICAST_WRITE = 1,
  OP_MCAST_WRITE = 2,
  OP_RUN = 3,
  OP_SIGNAL = 5,
  OP_DRAM_COPY = 7,
};

static void wait_dram_idle(void) {
  for (;;) {
    u32 put = mmio_read32(DISPATCH_DRAM_PUT);
    breadcrumb(0x203u, put, mmio_read32(DISPATCH_DRAM_READ), 0, 0);
    fence();
    noc_read(
      0, DRAM_READ_PUBLISH, 0, DRAM_COORD,
      DISPATCH_DRAM_READ, 4
    );
    fence();
    if (put == mmio_read32(DISPATCH_DRAM_READ)) return;
  }
}

static void enqueue_dram(u32 record) {
  u32 put;
  for (;;) {
    put = mmio_read32(DISPATCH_DRAM_PUT);
    u32 read = mmio_read32(DISPATCH_DRAM_READ);
    breadcrumb(0x204u, record, put, read, 0);
    if (put - read < DRAM_QUEUE_ENTRIES) break;
    fence();
    noc_read(
      0, DRAM_READ_PUBLISH, 0, DRAM_COORD,
      DISPATCH_DRAM_READ, 4
    );
    fence();
  }
  u32 slot = DRAM_QUEUE_BASE +
             (put & (DRAM_QUEUE_ENTRIES - 1)) * ALIGN;
  noc_write(0, record, slot, 0, DRAM_COORD, ALIGN, 0);
  put++;
  mmio_write32(DISPATCH_DRAM_PUT, put);
  fence();
  noc_write(
    0, DISPATCH_DRAM_PUT, DRAM_PUBLISHED,
    0, DRAM_COORD, 4, 0
  );
}

void firmware_boot(void) {
  u32 ring = DISPATCH_RING_BASE;
  u32 read = 0;
  mmio_write32(DISPATCH_DRAM_PUT, 0);
  mmio_write32(DISPATCH_DRAM_READ, 0);
  breadcrumb(0x200u, ring, read, 0, 0);

  for (;;) {
    breadcrumb(
      0x201u, ring, read, mmio_read32(DISPATCH_PUBLISHED),
      mmio_read32(DISPATCH_DRAM_READ)
    );
    while (mmio_read32(DISPATCH_PUBLISHED) == read) fence();
    u8 op = mmio_read8(ring + PACKET_OP);
    breadcrumb(
      0x202u, op, ring, read, mmio_read32(DISPATCH_PUBLISHED)
    );

    if (op == OP_DRAM_COPY || op == OP_SIGNAL) {
      enqueue_dram(ring);
      goto command_done;
    }

    wait_dram_idle();
    switch (op) {
      case OP_PAD:
        break;

      case OP_UNICAST_WRITE: {
        u32 target_count = mmio_read16(ring + PACKET_TARGET_COUNT);
        u32 address = mmio_read32(ring + PACKET_ADDRESS);
        u32 bytes = mmio_read32(ring + PACKET_DATA_SIZE);
        u32 targets = ring + PACKET_WRITE_TARGETS;
        u32 data = (targets + target_count * 4 + ALIGN - 1) & -ALIGN;
        u32 stride = (bytes + ALIGN - 1) & -ALIGN;
        breadcrumb(0x205u, target_count, address, bytes, data);
        while (target_count--) {
          u32 coordinate = mmio_read32(targets);
          noc_write(0, data, address, 0, coordinate, bytes, 0);
          targets += 4;
          data += stride;
        }
        break;
      }

      case OP_MCAST_WRITE: {
        u32 target_count = mmio_read16(ring + PACKET_TARGET_COUNT);
        u32 address = mmio_read32(ring + PACKET_ADDRESS);
        u32 bytes = mmio_read32(ring + PACKET_DATA_SIZE);
        u32 targets = ring + PACKET_WRITE_TARGETS;
        u32 data = (targets + target_count * 8 + ALIGN - 1) & -ALIGN;
        breadcrumb(0x206u, target_count, address, bytes, data);
        while (target_count--) {
          u32 start = mmio_read32(targets);
          u32 end = mmio_read32(targets + 4);
          noc_multicast_write(0, data, address, start, end, bytes);
          targets += 8;
        }
        break;
      }

      case OP_RUN: {
        u32 expected = mmio_read32(ring + PACKET_DATA_SIZE);
        mmio_write32(DISPATCH_DONE_COUNT, 0);
        fence();
        u32 targets = ring + PACKET_RUN_TARGETS;
        u32 go = mmio_read32(ring + PACKET_RUN_TEMPLATE) |
                 (0x80u << 24);
        mmio_write32(DISPATCH_GO, go);
        fence();
        u32 target_count = mmio_read16(ring + PACKET_TARGET_COUNT);
        breadcrumb(
          0x208u, expected, mmio_read32(DISPATCH_DONE_COUNT),
          target_count, go
        );
        while (target_count--) {
          u32 start = mmio_read32(targets);
          u32 end = mmio_read32(targets + 4);
          noc_multicast_write(
            0, DISPATCH_GO, GO_SIGNAL & -4u,
            start, end, 4
          );
          targets += 8;
        }
        while (mmio_read32(DISPATCH_DONE_COUNT) != expected) fence();
        fence();
        break;
      }

      default:
        breadcrumb(0x2FFu, op, ring, read, 0);
        for (;;) {}
    }

command_done:
    {
      u32 bytes = mmio_read32(ring + PACKET_TOTAL_SIZE);
      u32 pages = (bytes + PAGE_SIZE - 1) >> 12;
      read += pages;
      breadcrumb(0x209u, op, ring, read, pages);
      mmio_write32(DISPATCH_READ_PUBLISH, read);
      fence();
      noc_write(
        0, DISPATCH_READ_PUBLISH, PREFETCH_DISPATCH_READ,
        0, PREFETCH_COORD, 4, 0
      );
      ring += pages << 12;
      if (ring == DISPATCH_RING_END) ring = DISPATCH_RING_BASE;
    }
  }
}
