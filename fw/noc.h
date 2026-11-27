#pragma once
#include "common.h"

#define NOC_REGS(niu) (NOC0_REGS + (niu) * NOC_INSTANCE_OFFSET)
#define CMD_BUF(niu, buf) ((volatile u32 *)(NOC_REGS(niu) + (buf) * CMD_BUF_STRIDE))
// command buffer registers as word indexes (hw.Cmd has them as byte offsets)
enum { TARG_LO, TARG_MID, TARG_COORD, RET_LO, RET_MID, RET_COORD, PACKET_TAG, CTRL, AT_LEN_BE, AT_LEN_BE_1, AT_DATA,
       BRCST_EXCLUDE, CMD_CTRL = 16 };
enum { MCAST_BUF, READ_BUF, WRITE_BUF, ATOMIC_BUF };

#define NODE_ID(niu) (NOC_REGS(niu) + NOC_ID_LOGICAL)
#define OUTSTANDING(niu, tid) (NOC_REGS(niu) + NOC_OUTSTANDING + (tid) * 4)
#define OUTGOING(niu, tid) (NOC_REGS(niu) + NOC_OUTGOING + (tid) * 4)
#define STATIC_VC(vc) (CTRL_VC_STATIC | (vc) << 13)

void noc_init(u32 niu);
void noc_move_paced(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap);
void noc_move_paced_base(u32 niu, u32 write, u32 lo, u32 hi, u32 offset, u32 size, u32 local, u32 tid, u32 cap, u32 baseline);
void noc_wait(u32 niu, u32 tid, u32 acked);
void noc_write(u32 niu, u32 lo, u32 hi, u32 local, u32 size);
void noc_atomic_inc(u32 niu, u32 remote, u32 coord);
void noc_mcast(u32 niu, u32 local, u32 remote, u32 rect_packed, u32 size, u32 tid, u32 include_sender);
void noc_inc_worker(u32 niu, u32 remote, u32 target_xy_packed, u32 tid);
