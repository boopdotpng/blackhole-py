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

/* rect = start | end << 12. exclude is the NIU's BRCST_EXCLUDE word, which removes one corner quadrant (0 = none); its
 * anchor is in that NoC's frame, so NoC1 mirrors it. */
void noc_mcast(u32 niu, u32 local, u32 remote, u32 rect, u32 exclude, u32 size);
void noc_mcast_flush(u32 niu);

void noc_atomic_inc(u32 niu, u32 remote, u32 coord, u32 value);
/* size <= NOC_MAX_BURST bytes to host (PCIe) memory, returning once it is acked. Sets every command field it uses. */
void noc_write_host(u32 niu, u32 local, u32 lo, u32 hi, u32 size);

#endif
