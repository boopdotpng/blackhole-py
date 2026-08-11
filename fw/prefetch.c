#include "fw.h"

#define PACKET_SIZE 64u
#define HOST_ISSUE_SLOTS 16384u
#define CQ_STATE 0x1000u
#define PREFETCH_DOORBELL CQ_STATE
#define PREFETCH_PCIE_BASE (CQ_STATE + 0x08u)
#define PREFETCH_READ_PTR (CQ_STATE + 0x0Cu)
#define PREFETCH_DISPATCH_READ (CQ_STATE + 0x10u)
#define PREFETCH_INDIRECT_ACTIVE (CQ_STATE + 0x14u)
#define PREFETCH_INDIRECT_LO (CQ_STATE + 0x18u)
#define PREFETCH_INDIRECT_MID (CQ_STATE + 0x1Cu)
#define PREFETCH_INDIRECT_INDEX (CQ_STATE + 0x20u)
#define PREFETCH_INDIRECT_COUNT (CQ_STATE + 0x24u)
#define PREFETCH_READ_PUBLISH (CQ_STATE + 0x30u)
#define PREFETCH_DISPATCH_PUBLISH (CQ_STATE + 0x40u)
#define PREFETCH_STAGING 0x20000u

#define DISPATCH_PUBLISHED CQ_STATE
#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_SLOTS 1024u
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define DISPATCH_COORD TT_DISPATCH_COORD

#define PACKET_OP 0u
#define PACKET_INDIRECT_LO 8u
#define PACKET_INDIRECT_MID 12u
#define PACKET_INDIRECT_COUNT 16u

enum {
  OP_INDIRECT = 5,
};

static void read_doorbell(u32 *low, u32 *high) {
  u32 before, after;
  do {
    before = mmio_read32(PREFETCH_DOORBELL + 4u);
    *low = mmio_read32(PREFETCH_DOORBELL);
    after = mmio_read32(PREFETCH_DOORBELL + 4u);
  } while (before != after);
  *high = after;
}

static void publish_host_read(u32 low, u32 high) {
  mmio_write32(PREFETCH_READ_PUBLISH, low);
  mmio_write32(PREFETCH_READ_PUBLISH + 4u, high);
  fence();
  noc_write(
    0, PREFETCH_READ_PUBLISH, mmio_read32(PREFETCH_READ_PTR),
    TT_PCIE_MID, PCIE_COORD, 8, 0
  );
}

static void forward_packet(u32 *put) {
  while (*put - mmio_read32(PREFETCH_DISPATCH_READ) >=
         DISPATCH_RING_SLOTS) fence();
  u32 destination = DISPATCH_RING_BASE +
                    (*put & (DISPATCH_RING_SLOTS - 1u)) * PACKET_SIZE;
  noc_write(
    0, PREFETCH_STAGING, destination,
    0, DISPATCH_COORD, PACKET_SIZE, 0
  );
  (*put)++;
  mmio_write32(PREFETCH_DISPATCH_PUBLISH, *put);
  fence();
  noc_write(
    0, PREFETCH_DISPATCH_PUBLISH, DISPATCH_PUBLISHED,
    0, DISPATCH_COORD, 4, 0
  );
}

void firmware_boot(void) {
  u32 put = 0;
  u32 read_lo = 0;
  u32 read_hi = 0;
  mmio_write32(PREFETCH_DISPATCH_READ, 0);
  mmio_write32(PREFETCH_INDIRECT_ACTIVE, 0);

  for (;;) {
    u32 source_lo;
    u32 source_mid;
    u32 indirect = mmio_read32(PREFETCH_INDIRECT_ACTIVE);

    if (indirect != 0) {
      u32 index = mmio_read32(PREFETCH_INDIRECT_INDEX);
      source_lo = mmio_read32(PREFETCH_INDIRECT_LO) + index * PACKET_SIZE;
      source_mid = mmio_read32(PREFETCH_INDIRECT_MID);
    } else {
      u32 doorbell_lo, doorbell_hi;
      read_doorbell(&doorbell_lo, &doorbell_hi);
      if (doorbell_lo == read_lo && doorbell_hi == read_hi) {
        fence();
        continue;
      }
      source_lo = mmio_read32(PREFETCH_PCIE_BASE) +
                  (read_lo & (HOST_ISSUE_SLOTS - 1u)) * PACKET_SIZE;
      source_mid = TT_PCIE_MID;
    }

    noc_read(
      0, source_lo, source_mid, PCIE_COORD,
      PREFETCH_STAGING, PACKET_SIZE
    );

    switch (mmio_read32(PREFETCH_STAGING + PACKET_OP)) {
      case OP_INDIRECT:
        if (indirect != 0) for (;;) {}
        mmio_write32(
          PREFETCH_INDIRECT_LO,
          mmio_read32(PREFETCH_STAGING + PACKET_INDIRECT_LO)
        );
        mmio_write32(
          PREFETCH_INDIRECT_MID,
          mmio_read32(PREFETCH_STAGING + PACKET_INDIRECT_MID)
        );
        mmio_write32(PREFETCH_INDIRECT_INDEX, 0);
        mmio_write32(
          PREFETCH_INDIRECT_COUNT,
          mmio_read32(PREFETCH_STAGING + PACKET_INDIRECT_COUNT)
        );
        mmio_write32(PREFETCH_INDIRECT_ACTIVE, 1);
        {
          u32 previous = read_lo;
          read_lo++;
          read_hi += read_lo < previous;
        }
        publish_host_read(read_lo, read_hi);
        break;

      default:
        forward_packet(&put);
        if (indirect != 0) {
          u32 index = mmio_read32(PREFETCH_INDIRECT_INDEX) + 1u;
          mmio_write32(PREFETCH_INDIRECT_INDEX, index);
          if (index == mmio_read32(PREFETCH_INDIRECT_COUNT)) {
            mmio_write32(PREFETCH_INDIRECT_ACTIVE, 0);
          }
        } else {
          u32 previous = read_lo;
          read_lo++;
          read_hi += read_lo < previous;
          publish_host_read(read_lo, read_hi);
        }
        break;
    }
  }
}
