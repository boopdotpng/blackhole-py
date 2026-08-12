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
#define DISPATCH_MASKS (DISPATCH_TARGETS + 0x800u)
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
#define PACKET_EXEC_ARGS_LO 8u
#define PACKET_EXEC_ARGS_MID 12u
#define PACKET_EXEC_ARGS_SIZE 16u
#define PACKET_EXEC_EXPECTED 20u
#define PACKET_EXEC_TARGETS_LO 24u
#define PACKET_EXEC_TARGETS_MID 28u
#define PACKET_EXEC_ENTRY_POINTS 32u
#define WORKER_ENTRY_BASE 0x17FFE0u
#define PACKET_SIGNAL_TARGET_LO 8u
#define PACKET_SIGNAL_TARGET_MID 12u
#define PACKET_SIGNAL_VALUE 16u

enum {
  OP_WRITE = 1,
  OP_EXEC = 2,
  OP_SIGNAL = 3,
};

static void fetch_host(
  u32 source_lo, u32 source_mid, u32 destination, u32 bytes
) {
  noc_read(
    0, source_lo, source_mid, PCIE_COORD,
    destination, bytes
  );
}

static void fetch_targets(u32 packet, u32 count) {
  fetch_host(
    mmio_read32(packet + PACKET_TARGETS_LO),
    mmio_read32(packet + PACKET_TARGETS_MID),
    DISPATCH_TARGETS, count * 4u
  );
}

static u32 mask_address(u32 x, u32 y) {
  return DISPATCH_MASKS + (y * 2u + (x >> 5)) * 4u;
}

static u32 target_present(u32 x, u32 y) {
  return mmio_read32(mask_address(x, y)) & (1u << (x & 31u));
}

static void write_targets(
  u32 source, u32 address, u32 bytes, u32 count
) {
  zero_words(DISPATCH_MASKS, 128u);
  for (u32 index = 0; index < count; index++) {
    u32 coordinate = mmio_read32(DISPATCH_TARGETS + index * 4u);
    u32 x = coordinate & 63u;
    u32 y = (coordinate >> 6) & 63u;
    u32 mask = mask_address(x, y);
    mmio_write32(mask, mmio_read32(mask) | (1u << (x & 31u)));
  }

  u32 remaining = count;
  while (remaining != 0) {
    u32 start_x = 0;
    u32 start_y = 0;
    u32 found = 0;
    for (u32 y = 0; y < 64u && found == 0; y++) {
      for (u32 x = 0; x < 64u; x++) {
        if (target_present(x, y)) {
          start_x = x;
          start_y = y;
          found = 1;
          break;
        }
      }
    }
    if (found == 0) for (;;) {}

    u32 end_x = start_x;
    while (end_x + 1u < 64u && target_present(end_x + 1u, start_y)) {
      end_x++;
    }
    u32 end_y = start_y;
    while (end_y + 1u < 64u) {
      u32 complete = 1;
      for (u32 x = start_x; x <= end_x; x++) {
        if (!target_present(x, end_y + 1u)) {
          complete = 0;
          break;
        }
      }
      if (complete == 0) break;
      end_y++;
    }

    u32 target_count = (end_x - start_x + 1u) *
                       (end_y - start_y + 1u);
    u32 start = start_x | (start_y << 6);
    if (target_count == 1u) {
      noc_write(0, source, address, 0, start, bytes, 0);
    } else {
      u32 end = end_x | (end_y << 6);
      noc_multicast_write(0, source, address, start, end, bytes);
    }
    for (u32 y = start_y; y <= end_y; y++) {
      for (u32 x = start_x; x <= end_x; x++) {
        u32 mask = mask_address(x, y);
        mmio_write32(
          mask, mmio_read32(mask) & ~(1u << (x & 31u))
        );
      }
    }
    remaining -= target_count;
  }
}

static void execute_write(u32 packet) {
  u32 count = mmio_read32(packet + PACKET_TARGET_COUNT);
  u32 bytes = mmio_read32(packet + PACKET_BYTE_COUNT);
  fetch_targets(packet, count);
  fetch_host(
    mmio_read32(packet + PACKET_SOURCE_LO),
    mmio_read32(packet + PACKET_SOURCE_MID),
    DISPATCH_DATA, bytes
  );
  write_targets(
    DISPATCH_DATA, mmio_read32(packet + PACKET_ADDRESS), bytes, count
  );
}

static void execute_exec(u32 packet) {
  u32 target_count = mmio_read32(packet + PACKET_TARGET_COUNT);
  u32 args_size = mmio_read32(packet + PACKET_EXEC_ARGS_SIZE);
  fetch_targets(packet, target_count);
  if (args_size != 0) {
    fetch_host(
      mmio_read32(packet + PACKET_EXEC_ARGS_LO),
      mmio_read32(packet + PACKET_EXEC_ARGS_MID),
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
    packet + PACKET_EXEC_ENTRY_POINTS,
    WORKER_ENTRY_BASE, 5u * 4u, target_count
  );
  write_targets(DISPATCH_GO, GO_SIGNAL & -4u, 4u, target_count);
  fence();
  while (
    mmio_read32(DISPATCH_DONE_COUNT) !=
    mmio_read32(packet + PACKET_EXEC_EXPECTED)
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
      case OP_WRITE: execute_write(packet); break;
      case OP_EXEC: execute_exec(packet); break;
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
