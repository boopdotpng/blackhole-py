#pragma once
#include "hw.h"

#define NOC_MAX_BURST 0x4000
#define PCIE_COORD (1u << 24 | 24 << 6 | 19)

#define NOC_REGS(niu) (0xFFB20000 + (niu) * 0x10000)
#define CMD_BUF(niu, buf) ((volatile u32 *)(NOC_REGS(niu) + (buf) * 0x800))
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, AT_LEN_BE_1, AT_DATA,
       BRCST_EXCLUDE, CMD_CTRL = 16 };
enum { MCAST_BUF, READ_BUF, WRITE_BUF, ATOMIC_BUF };

#define NODE_ID(niu) (NOC_REGS(niu) + 0x148)
#define OUTSTANDING(niu, tid) (NOC_REGS(niu) + 0x240 + (tid) * 4)
#define OUTGOING(niu, tid) (NOC_REGS(niu) + 0x280 + (tid) * 4)

#define WRITE 0x2
#define RESP_MARKED 0x10
#define STATIC_VC(vc) (0x80 | (vc) << 13)

void noc_init(u32 niu);
void noc_move_paced(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap);
void noc_wait(u32 niu, u32 tid, u32 acked);
void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size);
