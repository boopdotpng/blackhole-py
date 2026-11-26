#pragma once

#define ROLE_BRISC  0
#define ROLE_NCRISC 1
#define ROLE_TRISC0 2

// ---- Worker L1 header (host-written; 0x0 holds `jal CODE_BASE`) ----
#define L1_SIZE          0x180000
#define SUBORDINATE_SYNC 0x14
#define GO_FLAG          0x18
#define WORKER_X         0x20
#define WORKER_Y         0x24
#define LEADER_COORD     0x1C
#define WORKER_ID        0x28
#define NUM_WORKERS      0x2C     // followed by the DRAM bank count and the Tensix column count
#define ROLE_PC          0x60     // NCRISC, TRISC0..2 entry points; 0 leaves that RISC in reset
#define CODE_BASE        0x100

// ---- DMA core L1 ----

#define PACKET           0x20     // bytes per host-written DMA descriptor
#define DMA_DEPTH        4        // descriptor ring depth
#define DMA_BATCH        0x20000  // bytes per chunk
#define DMA_SLOTS        4        // staging slots per engine
#define DMA_NCRISC_SYNC  0x10     // NCRISC boot handshake (writes 2 when up)
#define DMA_COPY_GO      0x20     // BRISC -> NCRISC: copy sequence number to start
#define DMA_COPY_DONE    0x30     // NCRISC -> BRISC: copy sequence number finished
#define DMA_PIPE_PROD    0x40     // DRAM-source copy: chunks BRISC has staged
#define DMA_PIPE_CONS    0x50     // DRAM-source copy: chunks NCRISC has written out
#define DMA_STATE        0x80     // host-initialised state block, DMA_STATE_SIZE bytes
#define DMA_STATE_SIZE   0x100
#define DMA_WPTR         0x80     // latest submitted sequence
#define DMA_SIGNAL       0x88     // host address of the completion counter
#define DMA_COPY_DESC    0xB0
#define DMA_SCRATCH      0x100
#define DMA_BRISC_BASE   0x200
#define DMA_BRISC_SIZE   0x3E00
#define DMA_NCRISC_BASE  0x4000
#define DMA_NCRISC_SIZE  0x4000
#define DMA_PACKETS      0x9000
#define DMA_STAGING      0x10000  // 2 engines x DMA_SLOTS x DMA_BATCH

#define LOCAL_MEM                0xFFB00000  // each RISC's private data RAM
#define STACK_TOP                0xFFB01FF0
#define TRISC_STACK_TOP          0xFFB00FF0
#define TDMA_CLK_GATE_EN         0xFFB11024
#define SOFT_RESET               0xFFB121B0
#define RESET_BRISC              (1u << 11)
#define RESET_TRISC0             (1u << 12)
#define RESET_NCRISC             (1u << 18)
#define RESET_ALL                0x47800
#define TRISC0_RESET_PC          0xFFB12228
#define TRISC_RESET_PC_OVERRIDE  0xFFB12234
#define NCRISC_RESET_PC          0xFFB12238
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223C
#define DEST_CG_CTRL             0xFFB12240

// ---- Overlay stream registers, reused as CB counters like tt-metal (only the low 16 bits count) ----
#define OVERLAY_STREAMS 0xFFB40000
#define STREAM_STRIDE   0x1000
#define CBS             32
#define CB_STREAM0      8
#define CB_PUSHED       8
#define CB_POPPED       10

// ---- Tensix MMIO windows ----
#define REGFILE                0xFFE00000  // this thread's 64 Tensix GPRs
#define INSTRN_BUF             0xFFE40000  // a store pushes one Tensix instruction
#define PC_BUF                 0xFFE80000
#define COPROCESSOR_DONE_CHECK 0xFFE80004  // load returns once every Tensix instruction from this thread has finished
#define TENSIX_CFG             0xFFEF0000  // Config bank (hw/cfg.py), 4 bytes per word

// Config bank words boot touches (hw/cfg.py has the fields)
#define CFG_STATE_RESET         4                        // MATH.state_reset: any write zeroes words 0..179
#define CFG_GLOBAL_BASE         180                      // first word state_reset keeps
#define CFG_BANK_WORDS          224
#define CFG_ECC_SCRUBBER        (TENSIX_CFG + 3 * 4)
#define CFG_RISCV_IC_INVALIDATE (TENSIX_CFG + 185 * 4)   // GLOBAL.icache_invalidate
#define CFG_RISC_PREFETCH_CTRL  (TENSIX_CFG + 208 * 4)   // GLOBAL.prefetch_*
#define THD_CFG_TTSYNC          56                       // ThreadConfig word reset_thread() keeps
#define THD_CFG_RESET           67                       // ThreadConfig words reset_thread() zeroes

// Tensix instructions boot issues to reset a core (encodings from hw/isa.py)
#define ZEROACC_ALL       0x10180000  // ZEROACC(clear_mode=3)
#define SFPENCC_RESET     0x8A00300A  // SFPENCC(imm12_math=3, instr_mod1=10)
#define NOP               0x02000000  // NOP()
#define SFPLOADI_MINUS1   0x7100BF80  // SFPLOADI(imm16=0xBF80): -1.0 as bf16
#define SFPCONFIG_L11     0x910000B0  // SFPCONFIG(config_dest=LReg.NEG_ONE)
#define SEMINIT_ALL       0xA31003FC  // SEMINIT(max_value=1, sem_sel=0xFF)
#define CLEARDVALID_RESET 0x36000001  // CLEARDVALID(reset=1)
#define SETRWC_ZERO       0x3700000F  // SETRWC(BitMask=15)
#define SETADCXY_ZERO     0x51E0000F  // SETADCXY(CntSetMask=7, BitMask=15)
#define SETADCZW_ZERO     0x54E0000F  // SETADCZW(CntSetMask=7, BitMask=15)

// ---- NoC NIU (two instances: NoC0 for BRISC, NoC1 for NCRISC) ----
#define NOC0_REGS           0xFFB20000
#define NOC_INSTANCE_OFFSET 0x10000
#define CMD_BUF_STRIDE      0x800
#define NOC_MAX_BURST       0x4000
#define NOC_ID_LOGICAL      0x148
#define NOC_OUTSTANDING     0x240  // + 4 * tid: reads and write acks in flight
#define NOC_OUTGOING        0x280  // + 4 * tid: writes not yet sent out of L1
#define CTRL_WRITE          (1u << 1)
#define CTRL_RESP_MARKED    (1u << 4)
#define CTRL_VC_STATIC      (1u << 7)

// ---- Topology, translated NoC coordinates (y << 6 | x) ----
#define PCIE_COORD (1u << 24 | 24 << 6 | 19)  // bit 24 selects host memory
#define DRAM_BANKS 8
// three NoC endpoints per bank (x 17 for banks 0..3, 18 for 4..7), by y; banks 4..7 are reversed
#define DRAM_PORT_COORDS {                                                       \
  {0x391, 0x351, 0x311}, {0x3D1, 0x411, 0x451}, {0x491, 0x4D1, 0x511}, {0x551, 0x591, 0x5D1}, \
  {0x392, 0x352, 0x312}, {0x452, 0x412, 0x3D2}, {0x512, 0x4D2, 0x492}, {0x5D2, 0x592, 0x552}}
