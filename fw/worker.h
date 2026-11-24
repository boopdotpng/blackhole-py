#pragma once
#include "noc.h"

// Worker L1 header, written by device.run_workers; must match hw/hw.py. 0x0 holds `jal CODE_BASE`.
#define SUBORDINATE_SYNC         0x14        // byte per subordinate RISC: 0x40 while held, 2 once booted
#define GO_FLAG                  0x18
#define LEADER_COORD             0x1C
#define WORKER_X                 0x20
#define WORKER_Y                 0x24
#define WORKER_ID                0x28
#define NUM_WORKERS              0x2C
#define DRAM_BANKS_L1            0x30
#define GRID_COLS_L1             0x34
#define ROLE_PC                  0x60        // boot pc of ncrisc, trisc0..2; 0 = not launched
#define CODE_BASE                0x100

// ROLE is the index in hw.ROLES
#define ROLE_BRISC               0
#define ROLE_NCRISC              1
#define ROLE_TRISC0              2
#define IS_TRISC                 (ROLE >= ROLE_TRISC0)
#define TRISC_ID                 (ROLE - ROLE_TRISC0)

// Boot stubs and epilogues are linked by boot.ld at address 0 and concatenated with the kernel bodies by
// fw.pack_megakernel, so they must be position independent: no data, and the body starts at `_end`.
