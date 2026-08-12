#pragma once

#include "fw.h"

#define TT_NOC_MAX_PACKET_BYTES (16u * 1024u)

static u32 noc_base(u32 niu) {
  return 0xFFB20000u + niu * 0x10000u;
}

static u32 noc_local_coordinate(u32 niu) {
  return mmio_read32(noc_base(niu) + 0x148u) & 0xFFFu;
}

static void noc_wait_counter(u32 niu, u32 offset, u32 expected) {
  u32 address = noc_base(niu) + 0x200u + offset;
  while (mmio_read32(address) != expected) {}
  fence();
}

static void noc_wait_issue(u32 niu, u32 offset, u32 bytes) {
  u32 address = noc_base(niu) + 0x200u + offset;
  u32 packets = (bytes + TT_NOC_MAX_PACKET_BYTES - 1) /
                TT_NOC_MAX_PACKET_BYTES;
  if (packets >= 128) {
    while (mmio_read32(address) != 0) {}
  } else {
    while (mmio_read32(address) >= 129u) {}
  }
}

static void noc_submit(
  u32 niu,
  u32 source_address, u32 source_middle, u32 source_coordinate,
  u32 target_address, u32 target_middle, u32 target_coordinate,
  u32 tid, u32 options, u32 bytes, u32 immediate
) {
  volatile u32 *command = (volatile u32 *)noc_base(niu);
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
  command[12] = 0;
  command[13] = 0;
  command[14] = 0;
  command[16] = 1;
  while (command[16] != 0) {}
}

static void noc_read_start(
  u32 niu, u32 tid, u32 source_address, u32 source_middle,
  u32 source_coordinate, u32 target_address, u32 bytes
) {
  noc_wait_issue(niu, 0x40u + tid * 4u, bytes);
  noc_submit(
    niu,
    source_address, source_middle, source_coordinate,
    target_address, 0, noc_local_coordinate(niu),
    tid, 0x2090u, bytes, 0
  );
}

static void noc_write_start(
  u32 niu, u32 tid, u32 source_address, u32 target_address,
  u32 target_middle, u32 target_coordinate, u32 bytes, u32 posted
) {
  noc_wait_issue(niu, 0x80u + tid * 4u, bytes);
  if (!posted) noc_wait_issue(niu, 0x40u + tid * 4u, bytes);
  noc_submit(
    niu,
    source_address, 0, noc_local_coordinate(niu),
    target_address, target_middle, target_coordinate,
    tid, posted ? 0x2082u : 0x2092u, bytes, 0
  );
}

static void noc_wait_reads(u32 niu, u32 tid) {
  noc_wait_counter(niu, 0x40u + tid * 4u, 0);
}

static void noc_wait_writes(u32 niu, u32 tid, u32 wait_remote) {
  noc_wait_counter(niu, 0x80u + tid * 4u, 0);
  if (wait_remote) noc_wait_reads(niu, tid);
}

static void noc_read(
  u32 niu, u32 source_address, u32 source_middle,
  u32 source_coordinate, u32 target_address, u32 bytes
) {
  noc_read_start(
    niu, 1, source_address, source_middle, source_coordinate,
    target_address, bytes
  );
  noc_wait_reads(niu, 1);
}

static void noc_write(
  u32 niu, u32 source_address, u32 target_address,
  u32 target_middle, u32 target_coordinate, u32 bytes, u32 posted
) {
  noc_write_start(
    niu, 1, source_address, target_address, target_middle,
    target_coordinate, bytes, posted
  );
  noc_wait_writes(niu, 1, !posted);
}

static void noc_multicast_write(
  u32 niu, u32 source_address, u32 target_address,
  u32 target_start, u32 target_end, u32 bytes
) {
  noc_wait_issue(niu, 0x84u, bytes);
  u32 rectangle = niu == 0
    ? target_end | (target_start << 12)
    : target_start | (target_end << 12);
  noc_submit(
    niu,
    source_address, 0, noc_local_coordinate(niu),
    target_address, 0, rectangle,
    1, 0x80A2u, bytes, 0
  );
  noc_wait_counter(niu, 0x84u, 0);
}

static void noc_atomic_inc(
  u32 niu, u32 target_address, u32 target_coordinate, u32 value
) {
  noc_wait_counter(niu, 0x84u, 0);
  noc_wait_counter(niu, 0x44u, 0);
  noc_wait_issue(niu, 0x44u, 1);
  noc_submit(
    niu,
    target_address, 0, target_coordinate,
    4, 0, noc_local_coordinate(niu),
    1, 0x2091u, 0x107Cu, value
  );
  noc_wait_counter(niu, 0x44u, 0);
}
