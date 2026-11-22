#ifndef ABI_H
#define ABI_H

#define STEP_EPOCH        0x10
#define SUBORDINATE_SYNC  0x14
#define STEP_TOKEN        0x18
#define SERVICE_COORD     0x1C
#define WORKER_X          0x20
#define WORKER_Y          0x24
#define WORKER_ID         0x28
#define NUM_WORKERS       0x2C
#define DRAM_BANKS_L1     0x30
#define GRID_COLS_L1      0x34
#define SYNC_ARRIVED      0x40
#define SYNC_EPOCH        0x50
#define ROLE_PC           0x60
#define STEP_ARGS         0x80
#define STEP_ARGS_SIZE    0x80
#define CODE_BASE         0x100

#define STACK_TOP         0xFFB01FF0
#define TRISC_STACK_TOP   0xFFB00FF0
#define TRISC_GP          0xFFB007F0

#define PACKET            32
#define RING_SIZE         0x10000

#define OP_KICK           0
#define OP_COPY           1
#define OP_WAIT           2
#define OP_STORE          3

#define SVC_NCRISC_SYNC   0x10
#define SVC_COPY_GO       0x20
#define SVC_COPY_DONE     0x30
#define SVC_PIPE_PROD     0x40
#define SVC_PIPE_CONS     0x50

#define SVC_STATE         0x80
#define SVC_WPTR          (SVC_STATE + 0x00)
#define SVC_RPTR          (SVC_STATE + 0x04)
#define SVC_RING_LO       (SVC_STATE + 0x08)
#define SVC_RING_HI       (SVC_STATE + 0x0C)
#define SVC_EPOCH         (SVC_STATE + 0x10)
#define SVC_DONE_COUNT    (SVC_STATE + 0x20)
#define SVC_COPY_DESC     (SVC_STATE + 0x30)
#define SVC_SCRATCH       (SVC_STATE + 0x80)
#define SVC_STATE_SIZE    0x100

#define SVC_BRISC_BASE    0x200
#define SVC_BRISC_SIZE    0x3E00
#define SVC_NCRISC_BASE   0x4000
#define SVC_NCRISC_SIZE   0x4000
#define SVC_ARGS_L1       0x8000
#define SVC_PACKETS       0x9000
#define SVC_PACKETS_MAX   0x1000
#define SVC_DMA_STAGING   0x10000
#define DMA_BATCH         0x20000

_Static_assert((SVC_EPOCH & 63) == (STEP_EPOCH & 63), "SVC_EPOCH and STEP_EPOCH must align mod 64");
_Static_assert((SVC_ARGS_L1 & 63) == (STEP_ARGS & 63), "SVC_ARGS_L1 and STEP_ARGS must align mod 64");
_Static_assert((SVC_SCRATCH & 63) == 0, "SVC_SCRATCH must be 64-aligned");
_Static_assert((SVC_DONE_COUNT & 15) == 0 && (SYNC_ARRIVED & 15) == 0, "NoC atomics need 16-byte alignment");
_Static_assert(SVC_STATE + SVC_STATE_SIZE <= SVC_BRISC_BASE, "service state overlaps BRISC image");
_Static_assert(SVC_PACKETS + 64 + SVC_PACKETS_MAX <= SVC_DMA_STAGING, "packet buffer overlaps DMA staging");

#endif
