#include "cq.h"
#include "noc.h"

#define DISPATCH_PUBLISHED 0x1000u
#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_SLOTS 1024u
#define DISPATCH_READ_PUBLISH (DISPATCH_RING_BASE + DISPATCH_RING_SLOTS * CQ_PACKET_SIZE)
#define DISPATCH_DONE_COUNT (DISPATCH_READ_PUBLISH + 0x10u)
#define DISPATCH_GO (DISPATCH_READ_PUBLISH + 0x20u)
#define DISPATCH_SIGNAL (DISPATCH_READ_PUBLISH + 0x40u)
#define DISPATCH_ARGS (DISPATCH_READ_PUBLISH + 0x80u)
#define DISPATCH_TARGETS (DISPATCH_READ_PUBLISH + 0x100u)
#define DISPATCH_DATA (DISPATCH_READ_PUBLISH + 0x1000u)

#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define GO_SIGNAL 0x0373u
#define PARAM_BASE 0x3FD0u

#define WORKER_ENTRY_BASE 0x17FFE0u

static void fetch_host(
  u32 source_lo, u32 source_mid, u32 destination, u32 bytes
) {
  noc_read(
    0, source_lo, source_mid, PCIE_COORD,
    destination, bytes
  );
}

static void fetch_targets(u32 source_lo, u32 source_mid, u32 count) {
  if (count != 0) {
    fetch_host(source_lo, source_mid, DISPATCH_TARGETS,
               count * sizeof(cq_target_region));
  }
}

static void write_targets(u32 source, u32 address, u32 bytes, u32 count) {
  if (count != 0) {
    volatile cq_target_region *regions =
      (volatile cq_target_region *)DISPATCH_TARGETS;
    for (u32 index = 0; index < count; index++) {
      if (regions[index].start == regions[index].end) {
        noc_write(0, source, address, 0, regions[index].start, bytes, 0);
      } else {
        noc_multicast_write(
          0, source, address, regions[index].start, regions[index].end, bytes
        );
      }
    }
    return;
  }
  noc_multicast_write(
    0, source, address, 1u | (2u << 6), 13u | (4u << 6), bytes
  );
  noc_multicast_write(
    0, source, address, 1u | (5u << 6), 14u | (11u << 6), bytes
  );
}

static void execute_write(volatile cq_packet *packet) {
  u32 target_count = packet->target_count;
  u32 bytes = packet->payload.write.byte_count;
  fetch_targets(packet->payload.write.targets_lo,
                packet->payload.write.targets_mid, target_count);
  fetch_host(
    packet->payload.write.source_lo, packet->payload.write.source_mid,
    DISPATCH_DATA, bytes
  );
  write_targets(
    DISPATCH_DATA, packet->payload.write.address, bytes, target_count
  );
}

static void execute_exec(volatile cq_packet *packet) {
  u32 target_count = packet->target_count;
  u32 args_size = packet->payload.exec.args_size;
  fetch_targets(packet->payload.exec.targets_lo,
                packet->payload.exec.targets_mid, target_count);
  if (args_size != 0) {
    fetch_host(
      packet->payload.exec.args_lo, packet->payload.exec.args_mid,
      DISPATCH_ARGS, args_size
    );
  }

  mmio_write32(DISPATCH_DONE_COUNT, 0);
  mmio_write32(DISPATCH_GO, 0x80000000u);
  fence();
  if (args_size != 0) {
    write_targets(DISPATCH_ARGS, PARAM_BASE, args_size, target_count);
  }
  write_targets(
    (u32)&packet->payload.exec.entry_points,
    WORKER_ENTRY_BASE, 5u * 4u, target_count
  );
  write_targets(DISPATCH_GO, GO_SIGNAL & -4u, 4u, target_count);
  fence();
  while (mmio_read32(DISPATCH_DONE_COUNT) != packet->payload.exec.expected) fence();
  fence();
}

static void execute_signal(volatile cq_packet *packet) {
  mmio_write32(DISPATCH_SIGNAL, packet->payload.signal.value[0]);
  mmio_write32(DISPATCH_SIGNAL + 4u, packet->payload.signal.value[1]);
  fence();
  noc_write(
    0, DISPATCH_SIGNAL,
    packet->payload.signal.target_lo, packet->payload.signal.target_mid,
    PCIE_COORD, 8, 0
  );
}

void firmware_boot(void) {
  u32 read = 0;
  for (;;) {
    while (mmio_read32(DISPATCH_PUBLISHED) == read) fence();
    volatile cq_packet *packet = (volatile cq_packet *)(
      DISPATCH_RING_BASE +
      (read & (DISPATCH_RING_SLOTS - 1u)) * CQ_PACKET_SIZE
    );
    switch (packet->op) {
      case CQ_OP_WRITE: execute_write(packet); break;
      case CQ_OP_EXEC: execute_exec(packet); break;
      case CQ_OP_SIGNAL: execute_signal(packet); break;
      default: for (;;) {}
    }
    read++;
    mmio_write32(DISPATCH_READ_PUBLISH, read);
    fence();
    noc_write(
      0, DISPATCH_READ_PUBLISH, 0x1010u, // Prefetch dispatch-read mailbox.
      0, TT_PREFETCH_COORD, 4, 0
    );
  }
}
