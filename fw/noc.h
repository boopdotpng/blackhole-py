#pragma once
#include "hw.h"

#define NOC_MAX_BURST 0x4000

u32 noc_coord(u32 niu);
void noc_init(u32 niu);

void noc_move_paced(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap);
void noc_wait(u32 niu, u32 tid, u32 acked);
void noc_read(u32 niu, u32 lo, u32 hi, u32 local, u32 size);
void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size);

void noc_dram_read_stream(u32 bank_start, u32 addr_start, u32 page, u32 pages, u32 local, u32 local_mask, u32 tid, u32 cap);

void noc_mcast(u32 niu, u32 local, u32 remote, u32 rect, u32 exclude, u32 size);
void noc_mcast_flush(u32 niu);

void noc_atomic_inc(u32 niu, u32 remote, u32 coord, u32 value);
void noc_write_host(u32 niu, u32 local, u32 lo, u32 hi, u32 size);
