#include "fw.h"

#define PACKET_SIZE 64u
#define CQ_STATE 0x1000u
#define PREFETCH_DISPATCH_READ (CQ_STATE + 0x10u)
#define DISPATCH_PUBLISHED CQ_STATE
#define DISPATCH_RING_BASE 0x20000u
#define DISPATCH_RING_SLOTS 1024u
#define DISPATCH_RING_END (DISPATCH_RING_BASE + DISPATCH_RING_SLOTS * PACKET_SIZE)
#define DISPATCH_READ_PUBLISH DISPATCH_RING_END
#define DISPATCH_DONE_COUNT (DISPATCH_RING_END + 0x10u)
#define DISPATCH_GO (DISPATCH_RING_END + 0x20u)
#define DISPATCH_SIGNAL (DISPATCH_RING_END + 0x40u)
#define DISPATCH_ARGS (DISPATCH_RING_END + 0x80u)
#define DISPATCH_TARGETS (DISPATCH_RING_END + 0x100u)
#define DISPATCH_DATA (DISPATCH_RING_END + 0x1000u)

#define PREFETCH_COORD TT_PREFETCH_COORD
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define GO_SIGNAL 0x0373u
#define PARAM_BASE 0x3FD0u

#define PACKET_OP 0u
#define PACKET_TARGET_COUNT 4u
#define PACKET_ADDRESS 8u
#define PACKET_BYTE_COUNT 12u
#define PACKET_SOURCE_LO 16u
#define PACKET_SOURCE_MID 20u
#define PACKET_TARGETS_LO 24u
#define PACKET_TARGETS_MID 28u
#define PACKET_RUN_ARGS_LO 8u
#define PACKET_RUN_ARGS_MID 12u
#define PACKET_RUN_ARGS_SIZE 16u
#define PACKET_RUN_EXPECTED 20u
#define PACKET_RUN_TARGETS_LO 24u
#define PACKET_RUN_TARGETS_MID 28u
#define PACKET_RUN_ENTRY_POINTS 32u
#define WORKER_ENTRY_BASE 0x17FFE0u
#define PACKET_SIGNAL_TARGET_LO 8u
#define PACKET_SIGNAL_TARGET_MID 12u
#define PACKET_SIGNAL_VALUE 16u

enum {
  OP_UNICAST_WRITE = 1,
  OP_MCAST_WRITE = 2,
  OP_RUN = 3,
  OP_SIGNAL = 4,
};

static void fetch_host(
  u32 source_lo, u32 source_mid, u32 destination, u32 bytes
) {
  noc_read(
    0, source_lo, source_mid, PCIE_COORD,
    destination, bytes
  );
}

static void execute_unicast(u32 packet) {
  u32 count = mmio_read32(packet + PACKET_TARGET_COUNT);
  u32 address = mmio_read32(packet + PACKET_ADDRESS);
  u32 bytes = mmio_read32(packet + PACKET_BYTE_COUNT);
  u32 source = mmio_read32(packet + PACKET_SOURCE_LO);
  u32 source_mid = mmio_read32(packet + PACKET_SOURCE_MID);
  fetch_host(
    mmio_read32(packet + PACKET_TARGETS_LO),
    mmio_read32(packet + PACKET_TARGETS_MID),
    DISPATCH_TARGETS, count * 4u
  );
  for (u32 index = 0; index < count; index++) {
    fetch_host(source, source_mid, DISPATCH_DATA, bytes);
    noc_write(
      0, DISPATCH_DATA, address, 0,
      mmio_read32(DISPATCH_TARGETS + index * 4u), bytes, 0
    );
    source += bytes;
  }
}

static void execute_multicast(u32 packet) {
  u32 count = mmio_read32(packet + PACKET_TARGET_COUNT);
  u32 bytes = mmio_read32(packet + PACKET_BYTE_COUNT);
  fetch_host(
    mmio_read32(packet + PACKET_TARGETS_LO),
    mmio_read32(packet + PACKET_TARGETS_MID),
    DISPATCH_TARGETS, count * 8u
  );
  fetch_host(
    mmio_read32(packet + PACKET_SOURCE_LO),
    mmio_read32(packet + PACKET_SOURCE_MID),
    DISPATCH_DATA, bytes
  );
  for (u32 index = 0; index < count; index++) {
    u32 target = DISPATCH_TARGETS + index * 8u;
    noc_multicast_write(
      0, DISPATCH_DATA, mmio_read32(packet + PACKET_ADDRESS),
      mmio_read32(target), mmio_read32(target + 4u), bytes
    );
  }
}

static void execute_run(u32 packet) {
  u32 target_count = mmio_read32(packet + PACKET_TARGET_COUNT);
  u32 args_size = mmio_read32(packet + PACKET_RUN_ARGS_SIZE);
  fetch_host(
    mmio_read32(packet + PACKET_RUN_TARGETS_LO),
    mmio_read32(packet + PACKET_RUN_TARGETS_MID),
    DISPATCH_TARGETS, target_count * 8u
  );
  if (args_size != 0) {
    fetch_host(
      mmio_read32(packet + PACKET_RUN_ARGS_LO),
      mmio_read32(packet + PACKET_RUN_ARGS_MID),
      DISPATCH_ARGS, args_size
    );
  }

  mmio_write32(DISPATCH_DONE_COUNT, 0);
  mmio_write32(DISPATCH_GO, 0x80u);
  fence();
  for (u32 index = 0; index < target_count; index++) {
    u32 target = DISPATCH_TARGETS + index * 8u;
    u32 start = mmio_read32(target);
    u32 end = mmio_read32(target + 4u);
    if (args_size != 0) {
      noc_multicast_write(
        0, DISPATCH_ARGS, PARAM_BASE, start, end, args_size
      );
    }
    for (u32 role = 0; role < 5; role++) {
      u32 entry = mmio_read32(
        packet + PACKET_RUN_ENTRY_POINTS + role * 4u
      );
      mmio_write32(DISPATCH_ARGS + 0x40u, entry);
      fence();
      noc_multicast_write(
        0, DISPATCH_ARGS + 0x40u,
        WORKER_ENTRY_BASE + role * 4u, start, end, 4
      );
    }
    noc_multicast_write(
      0, DISPATCH_GO, GO_SIGNAL & -4u, start, end, 4
    );
  }
  fence();
  while (
    mmio_read32(DISPATCH_DONE_COUNT) !=
    mmio_read32(packet + PACKET_RUN_EXPECTED)
  ) fence();
  fence();
}

static void execute_signal(u32 packet) {
  mmio_write32(
    DISPATCH_SIGNAL,
    mmio_read32(packet + PACKET_SIGNAL_VALUE)
  );
  mmio_write32(
    DISPATCH_SIGNAL + 4u,
    mmio_read32(packet + PACKET_SIGNAL_VALUE + 4u)
  );
  fence();
  noc_write(
    0, DISPATCH_SIGNAL,
    mmio_read32(packet + PACKET_SIGNAL_TARGET_LO),
    mmio_read32(packet + PACKET_SIGNAL_TARGET_MID),
    PCIE_COORD, 8, 0
  );
}

void firmware_boot(void) {
  u32 read = 0;
  for (;;) {
    while (mmio_read32(DISPATCH_PUBLISHED) == read) fence();
    u32 packet = DISPATCH_RING_BASE +
                 (read & (DISPATCH_RING_SLOTS - 1u)) * PACKET_SIZE;
    switch (mmio_read32(packet + PACKET_OP)) {
      case OP_UNICAST_WRITE: execute_unicast(packet); break;
      case OP_MCAST_WRITE: execute_multicast(packet); break;
      case OP_RUN: execute_run(packet); break;
      case OP_SIGNAL: execute_signal(packet); break;
      default: for (;;) {}
    }
    read++;
    mmio_write32(DISPATCH_READ_PUBLISH, read);
    fence();
    noc_write(
      0, DISPATCH_READ_PUBLISH, PREFETCH_DISPATCH_READ,
      0, PREFETCH_COORD, 4, 0
    );
  }
}
