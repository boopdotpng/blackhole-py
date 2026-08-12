#include "cq.h"
#include "noc.h"

#define HOST_ISSUE_SLOTS 16384u
#define PREFETCH_DOORBELL 0x1000u
#define PREFETCH_PCIE_BASE 0x1008u
#define PREFETCH_READ_PTR 0x100Cu
#define PREFETCH_DISPATCH_READ 0x1010u
#define PREFETCH_READ_PUBLISH 0x1030u
#define PREFETCH_DISPATCH_PUBLISH 0x1040u
#define PREFETCH_STAGING 0x20000u

#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_SLOTS 1024u
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)

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
                    (*put & (DISPATCH_RING_SLOTS - 1u)) * CQ_PACKET_SIZE;
  noc_write(
    0, PREFETCH_STAGING, destination,
    0, TT_DISPATCH_COORD, CQ_PACKET_SIZE, 0
  );
  (*put)++;
  mmio_write32(PREFETCH_DISPATCH_PUBLISH, *put);
  fence();
  noc_write(
    0, PREFETCH_DISPATCH_PUBLISH, 0x1000u, // Dispatch published-count mailbox.
    0, TT_DISPATCH_COORD, 4, 0
  );
}

void firmware_boot(void) {
  u32 put = 0;
  u32 read_lo = 0;
  u32 read_hi = 0;
  u32 indirect_lo = 0;
  u32 indirect_mid = 0;
  u32 indirect_index = 0;
  u32 indirect_count = 0;
  mmio_write32(PREFETCH_DISPATCH_READ, 0);

  for (;;) {
    u32 source_lo;
    u32 source_mid;
    u32 indirect = indirect_index != indirect_count;

    if (indirect != 0) {
      source_lo = indirect_lo + indirect_index * CQ_PACKET_SIZE;
      source_mid = indirect_mid;
    } else {
      u32 doorbell_lo, doorbell_hi;
      read_doorbell(&doorbell_lo, &doorbell_hi);
      if (doorbell_lo == read_lo && doorbell_hi == read_hi) {
        fence();
        continue;
      }
      source_lo = mmio_read32(PREFETCH_PCIE_BASE) +
                  (read_lo & (HOST_ISSUE_SLOTS - 1u)) * CQ_PACKET_SIZE;
      source_mid = TT_PCIE_MID;
    }

    noc_read(
      0, source_lo, source_mid, PCIE_COORD,
      PREFETCH_STAGING, CQ_PACKET_SIZE
    );

    volatile cq_packet *packet = (volatile cq_packet *)PREFETCH_STAGING;
    switch (packet->op) {
      case CQ_OP_INDIRECT:
        if (indirect != 0) for (;;) {}
        indirect_lo = packet->payload.indirect.source_lo;
        indirect_mid = packet->payload.indirect.source_mid;
        indirect_index = 0;
        indirect_count = packet->payload.indirect.count;
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
          indirect_index++;
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
