#ifndef NOC_H
#define NOC_H
#include "hw.h"

#define NOC_MAX_BURST 0x4000

u32 noc_coord(u32 niu);

void noc_init(u32 niu);
void noc_move(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid);
void noc_wait(u32 niu, u32 tid, u32 acked);
void noc_read(u32 niu, u32 lo, u32 hi, u32 local, u32 size);
void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size);

void noc_mcast(u32 niu, u32 local, u32 remote, u32 start, u32 end, u32 size);
void noc_mcast_flush(u32 niu);

void noc_atomic_inc(u32 niu, u32 remote, u32 coord, u32 value);

#endif
