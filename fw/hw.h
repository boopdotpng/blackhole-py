#pragma once

#define ROLE_BRISC  0
#define ROLE_NCRISC 1
#define ROLE_TRISC0 2
#define ROLE_TRISC1 3
#define ROLE_TRISC2 4

// ---- Worker L1 layout (0x0 holds `jal WORKER_BRISC_BASE`) ----
#define L1_SIZE          0x180000
#define SUBORDINATE_SYNC 0x14     // 1 byte per NCRISC/TRISC0..2: 2=up, NCRISC 0x80=go / 0=done
#define STEP_TOKEN       0x18     // BRISC -> TRISC0..2 per-dispatch token
#define LEADER_COORD     0x1C     // CP NoC0 coord (target of worker completion atomic inc)
#define WORKER_X         0x20     // logical worker column, set by worker boot
#define WORKER_Y         0x24     // logical worker row, set by worker boot
#define WORKER_ID        0x28     // x * 10 + y
#define NUM_WORKERS      0x2C     // active worker count (followed by dram_banks, grid_cols)
#define DRAM_BANKS_L1    0x30
#define GRID_COLS_L1     0x34
#define FN_NOC_INC       0x38     // jal x0 trampolines to resident RV32 ABI functions
#define WORK_DONE        0x40     // completion arrival counter (on CP core)
#define HOST_SIGNAL_ADDR 0x48     // legacy unused on workers
#define LAUNCH_SEQUENCE  0x50
#define TENSIX_READY     0x58     // TRISC0 -> TRISC1/2: BRISC Tensix reset drained for token
#define WORK_READY       0x5C     // worker BRISC sets 1 once resident boot completes
#define ROLE_PC          0x60     // resident NCRISC, TRISC0..2 boot entry PCs
#define FN_NOC_READ      0x70
#define FN_NOC_WRITE     0x74
#define FN_NOC_WAIT      0x78
#define FN_NOC_MCAST     0x7C

// Contiguous 192-byte dispatch mailbox (64B-aligned, multicast by CP before each launch):
//   [0x080..0x0FF] ARG_BASE (16 x u64 kernel args)
//   [0x100..0x113] KERNEL_PC[5] (brisc, ncrisc, trisc0, trisc1, trisc2; 0 = role inactive)
//   [0x114]        DISP_NUM_WORKERS
//   [0x118]        DISP_CB_MASK (bitmask of CBs 0..31 to zero)
//   [0x11C]        DISP_FLAGS (bit 0 = FLAG_CLEAR_MCAST)
//   [0x120]        DISP_CACHE_EPOCH (monotonic; workers invalidate icache on change)
//   [0x13C]        STEP_EPOCH (written last on same VC; change wakes worker BRISC)
#define ARG_BASE         0x80
#define DISPATCH_HDR     0x100
#define KERNEL_PC        0x100
#define DISP_NUM_WORKERS 0x114
#define DISP_CB_MASK     0x118
#define DISP_FLAGS       0x11C
#define DISP_CACHE_EPOCH 0x120
#define STEP_EPOCH       0x13C
#define GATHER_INDEX     0x140    // private BRISC indirect-read result, after dispatch mailbox
#define DISPATCH_BYTES   0xC0     // 0x80..0x13F (192 bytes)
#define FLAG_CLEAR_MCAST 1u

// Resident worker firmware occupies [0x200..0x4000); L1 kernel cache occupies [0x4000..0x1EC00).
#define WORKER_FW_BASE   0x200
#define WORKER_FW_END    0x4000
#define CODE_CACHE_BASE  0x4000
#define CODE_CACHE_END   0x1EC00
#define CODE_BASE        0x4000   // alias for compatibility
#define MCAST_CTRL_BASE  0x1EC00  // 1 KiB, cleared before each multicast launch
#define NOC_READ_SCRATCH 0x1F000  // two private 2 KiB stages for unaligned resident transfers
#define NOC_READ_STAGE   0x800

// ---- Command Processor (CP) core L1 (COMPUTE:0 queue, core (right, 10)) ----
#define CP_WORK_DONE     0x40     // atomic-inc target for worker completions
#define CP_STATE         0x80     // host-initialized state block (0x80..0x17F)
#define CP_STATE_SIZE    0x100
#define CP_WPTR          0x80     // host doorbell: latest submitted IB sequence
#define CP_RPTR          0x84     // CP retired IB sequence
#define CP_ALL_NRECTS    0x88     // number of physical NoC0 rects covering all workers (1..4)
#define CP_ALL_RECTS     0x8C     // up to 4 packed rects: (c0 << 12) | c1
#define CP_READY         0xA0     // CP writes 1 once booted
#define CP_BRISC_BASE    0x200
#define CP_BRISC_SIZE    0x3E00
#define CP_SCRATCH       0x4000   // 256 B, 64B-aligned (signal read/write, timestamps)
#define CP_DISPATCH_BUF  0x4100   // 256 B, 64B-aligned (staged 192B dispatch mailbox)
#define CP_RING          0x5000   // CP_DEPTH x CP_IB_BYTES indirect buffer ring
#define CP_DEPTH         64
#define CP_IB_BYTES      32
#define CP_CMDBUF_STAGE  0x8000   // 16 KiB = 256 x 64B HCQ2 packets
#define CP_CMDBUF_CHUNK  0x4000
#define CP_PROG_STAGE    0x10000  // 128 KiB staging for program binary cache fills
#define CP_PKT_BYTES     64       // fixed 64-byte HCQ2 packet size
#define CP_CACHE_MAX     64       // max resident programs tracked in L1 cache

// Minimal HCQ2 packet opcodes (64 bytes each, 16 x u32)
#define PKT_NOP          0
#define PKT_EXEC         1
#define PKT_EXEC_BARRIER 2
#define PKT_WAIT         3
#define PKT_SIGNAL       4
#define PKT_TIMESTAMP    5
#define PKT_MEM_BARRIER  6
#define PKT_COPY         7        // DMA core: dst, src, bytes

// Program bundle header (first 64 bytes at prog_addr in DRAM/host)
#define PROG_HDR_BYTES   64

// ---- DMA core L1 (COPY:0 queue, core (right, 11)) ----
#define DMA_BATCH        0x20000  // bytes per chunk
#define DMA_SLOTS        4        // staging slots per engine
#define DMA_NCRISC_SYNC  0x10     // NCRISC boot handshake (writes 2 when up)
#define DMA_COPY_GO      0x20     // BRISC -> NCRISC: copy sequence number to start
#define DMA_COPY_DONE    0x30     // NCRISC -> BRISC: copy sequence number finished
#define DMA_PIPE_PROD    0x40     // DRAM-source copy: chunks BRISC has staged
#define DMA_PIPE_CONS    0x50     // DRAM-source copy: chunks NCRISC has written out
#define DMA_WPTR         0x80     // host doorbell, DMA_RPTR and DMA_READY: as the CP's
#define DMA_RPTR         0x84
#define DMA_READY        0xA0
#define DMA_COPY_DESC    0xB0     // the copy BRISC shares with NCRISC: dst, src, bytes
#define DMA_SCRATCH      0x100    // 128 B (signal read/write, timestamps)
#define DMA_BRISC_BASE   0x200
#define DMA_BRISC_SIZE   0x3E00
#define DMA_NCRISC_BASE  0x4000
#define DMA_NCRISC_SIZE  0x4000
#define DMA_RING         0x9000   // CP_DEPTH x CP_IB_BYTES indirect buffer ring
#define DMA_CMDBUF_STAGE 0xA000   // CP_CMDBUF_CHUNK bytes of packets
#define DMA_STAGING      0x10000  // 2 engines x DMA_SLOTS x DMA_BATCH

#define LOCAL_MEM                0xFFB00000  // each RISC's private data RAM
#define NOC_BASELINE             (LOCAL_MEM + 0x100) // private pre-kernel transaction counters
#define CB_RING_OFF              (LOCAL_MEM + 0x600) // 32 x u32 per-RISC CB ring byte offsets (-512(gp)..-388(gp))
#define RETURN_VEC               (LOCAL_MEM + 0x7F0) // -16(gp): return PC; -12(gp): saved sp
#define STACK_TOP                0xFFB01FF0
#define TRISC_STACK_TOP          0xFFB00FF0
#define TDMA_CLK_GATE_EN         0xFFB11024
#define SOFT_RESET               0xFFB121B0
#define RESET_BRISC              (1u << 11)
#define RESET_TRISC0             (1u << 12)
#define RESET_NCRISC             (1u << 18)
#define RESET_ALL                0x47800
#define WALL_CLOCK_L             0xFFB121F0
#define WALL_CLOCK_H             0xFFB121F8
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
#define PCBUF(i)               (0xFFE80000 + (i) * 0x10000)
#define COPROCESSOR_DONE_CHECK 0xFFE80004  // load returns once every Tensix instruction from this thread has finished
#define MAILBOX_TO_BRISC       0xFFEC0000
#define MAILBOX_FROM(i)        (0xFFEC1000 + (i) * 0x1000)
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
#define CTRL_BRCST_PACKET   (1u << 5)
#define CTRL_BRCST_SRC_INCLUDE (1u << 17)
#define CTRL_RESP_MARKED    (1u << 4)
#define CTRL_VC_STATIC      (1u << 7)

// ---- Topology, translated NoC coordinates (y << 6 | x) ----
#define PCIE_COORD (1u << 24 | 24 << 6 | 19)  // bit 24 selects host memory
#define DRAM_BANKS 8
// three NoC endpoints per bank (x 17 for banks 0..3, 18 for 4..7), by y; banks 4..7 are reversed
#define DRAM_PORT_COORDS {                                                       \
  {0x391, 0x351, 0x311}, {0x3D1, 0x411, 0x451}, {0x491, 0x4D1, 0x511}, {0x551, 0x591, 0x5D1}, \
  {0x392, 0x352, 0x312}, {0x452, 0x412, 0x3D2}, {0x512, 0x4D2, 0x492}, {0x5D2, 0x592, 0x552}}
