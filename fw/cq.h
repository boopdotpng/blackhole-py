#pragma once

#include "fw.h"

#define CQ_PACKET_SIZE 64u

enum {
  CQ_OP_WRITE = 1,
  CQ_OP_EXEC = 2,
  CQ_OP_SIGNAL = 3,
  CQ_OP_INDIRECT = 4,
};

typedef struct {
  u16 start;
  u16 end;
} cq_target_region;

typedef struct {
  u32 address;
  u32 byte_count;
  u32 source_lo;
  u32 source_mid;
  u32 targets_lo;
  u32 targets_mid;
} cq_write;

typedef struct {
  u32 args_lo;
  u32 args_mid;
  u32 args_size;
  u32 expected;
  u32 targets_lo;
  u32 targets_mid;
  u32 entry_points[5];
} cq_exec;

typedef struct {
  u32 target_lo;
  u32 target_mid;
  u32 value[2];
} cq_signal;

typedef struct {
  u32 source_lo;
  u32 source_mid;
  u32 count;
} cq_indirect;

typedef struct {
  u32 op;
  u32 target_count;
  union {
    cq_write write;
    cq_exec exec;
    cq_signal signal;
    cq_indirect indirect;
    u32 words[14];
  } payload;
} cq_packet;

typedef struct {
  u32 device_address;
  u32 host_lo;
  u32 host_mid;
  u32 byte_count;
  u32 direction;
  u32 reserved[11];
} dma_copy;

_Static_assert(sizeof(cq_target_region) == 4, "invalid target region ABI");
_Static_assert(sizeof(cq_packet) == CQ_PACKET_SIZE, "invalid CQ packet ABI");
_Static_assert(sizeof(dma_copy) == CQ_PACKET_SIZE, "invalid DMA packet ABI");
