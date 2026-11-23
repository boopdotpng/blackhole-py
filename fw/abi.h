#pragma once
// L1 memory layout shared by host (fw/__init__.py), service firmware, and worker crt0.
// NoC copies need src and dst to agree mod 64, hence the alignment asserts at the bottom.

// ---- Worker L1 (0x0 holds a jal to CODE_BASE: the BRISC reset vector) ----
#define STEP_EPOCH        0x10  // host multicasts a new epoch here; a change starts one step
#define SUBORDINATE_SYNC  0x14  // 1 byte per NCRISC/TRISC0-2: boot ready = 2, NCRISC go = 0x80 / done = 0
#define STEP_TOKEN        0x18  // per-step token BRISC hands the TRISCs (seeded from wall clock so stale tokens never match)
#define LEADER_COORD     0x1C  // NoC coord of worker zero, target of the step-done atomic
#define WORKER_X          0x20  // logical worker column, set by crt0
#define WORKER_Y          0x24  // logical worker row, set by crt0
#define WORKER_ID         0x28  // x * 10 + y
#define NUM_WORKERS       0x2C  // written by host in the load header
#define DRAM_BANKS_L1     0x30  // 8, or 7 on p100a
#define GRID_COLS_L1      0x34  // enabled Tensix columns (12 or 14)
#define SYNC_ARRIVED      0x40  // barrier_all arrival counter (on worker 0, NoC-atomic target)
#define SYNC_EPOCH        0x50  // barrier_all release epoch, multicast by worker 0
#define ROLE_PC           0x60  // 4 start PCs: NCRISC, TRISC0, TRISC1, TRISC2 (0 = role not loaded)
#define STEP_ARGS         0x80  // kernel args, multicast by the host before each step
#define STEP_ARGS_SIZE    0x80
#define CODE_BASE         0x100 // kernel images start here

// ---- Per-RISC private local memory ----
#define STACK_TOP         0xFFB01FF0  // BRISC/NCRISC: 8 KiB local mem
#define TRISC_STACK_TOP   0xFFB00FF0  // TRISC: 4 KiB local mem
#define TRISC_GP          0xFFB007F0

// Host writes six-word DMA descriptors into these 32-byte L1 slots.
#define PACKET            32
#define DMA_DEPTH         4

// ---- Service core L1 ----
#define SVC_NCRISC_SYNC   0x10  // NCRISC boot handshake (writes 2 when up)
#define SVC_COPY_GO       0x20  // BRISC -> NCRISC: copy sequence number to start
#define SVC_COPY_DONE     0x30  // NCRISC -> BRISC: copy sequence number finished
#define SVC_PIPE_PROD     0x40  // DRAM-source copy: chunks BRISC has staged
#define SVC_PIPE_CONS     0x50  // DRAM-source copy: chunks NCRISC has written out

#define SVC_STATE         0x80  // block the host initialises and polls
#define SVC_WPTR          SVC_STATE           // latest host-submitted DMA sequence
#define SVC_SIGNAL        (SVC_STATE + 8)     // pinned completion counter address
#define SVC_COPY_DESC     (SVC_STATE + 0x30)
#define SVC_SCRATCH       (SVC_STATE + 0x80)
#define SVC_STATE_SIZE    0x100

#define SVC_BRISC_BASE    0x200     // service BRISC image slot
#define SVC_BRISC_SIZE    0x3E00
#define SVC_NCRISC_BASE   0x4000    // service NCRISC image slot
#define SVC_NCRISC_SIZE   0x4000
#define SVC_PACKETS       0x9000    // host-written DMA descriptors
#define SVC_DMA_STAGING   0x10000   // 2 engines x DMA_SLOTS x DMA_BATCH staging slots for host/DRAM copies
#ifndef DMA_BATCH
#define DMA_BATCH         0x20000
#endif
#ifndef DMA_SLOTS
#define DMA_SLOTS         4         // per engine; reads use tids 8..8+DMA_SLOTS-1, writes the DMA_SLOTS above them
#endif

_Static_assert((SVC_SCRATCH & 63) == 0, "SVC_SCRATCH must be 64-aligned");
_Static_assert(SVC_STATE + SVC_STATE_SIZE <= SVC_BRISC_BASE, "service state overlaps BRISC image");
_Static_assert(SVC_PACKETS + PACKET * DMA_DEPTH <= SVC_DMA_STAGING, "packet buffer overlaps DMA staging");
_Static_assert(DMA_SLOTS >= 2 && 8 + 2 * DMA_SLOTS <= 16, "DMA ring needs 2..4 slots: 2 NoC tids each, from tid 8");
_Static_assert(SVC_DMA_STAGING + 2 * DMA_SLOTS * DMA_BATCH <= 0x180000, "DMA staging exceeds L1");

// Completion counter on worker zero, separate from the in-graph barrier.
#define WORK_READY        0x74
#define WORK_DONE         0x70
#define ROLE_PROGRESS     0x4000
#define ROLE_RELEASE      0x4020
#define ARG_VALUES        0x4100
#define MAX_VARS          512
#define WEIGHT_RING       0x8000
#define DATA_BASE         0x18000
#define PARAM_SIZE        64
#define L1_PARAM_BASE     0xffb00840
#define EAGER_ROW         0x4900
