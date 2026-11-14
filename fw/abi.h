/* The contract between the host and the firmware. fw/__init__.py mirrors what the host needs. */
#ifndef ABI_H
#define ABI_H

/* ---- L1, every Tensix core ---- */
#define GO_SIGNAL         0x10     /* u32. byte 0: 0x80 = launch, cleared when every RISC returns. bits 8-19: dispatch's NoC coordinate,
                                    * bit 20: which execution slot to run (GO_SLOT) */
#define GO_SLOT_BIT       20
#define SUBORDINATE_SYNC  0x14     /* u8 each for ncrisc, trisc0-2. 2 = booted, 0x80 = go, 0 = returned */

/* Resident firmware, one image per RISC. FW_x + 0 boots, FW_x + 4 is where a kernel jumps when it is done. */
#define FW_BRISC          0x20
#define FW_BRISC_SIZE     0x360
#define FW_NCRISC         0x380
#define FW_NCRISC_SIZE    0x100
#define FW_TRISC0         0x480
#define FW_TRISC0_SIZE    0x100
#define FW_TRISC1         0x580
#define FW_TRISC1_SIZE    0x100
#define FW_TRISC2         0x680
#define FW_TRISC2_SIZE    0x100

/* Two execution slots, double buffered: while one launch runs from slot b, dispatch installs the next one into slot b ^ 1.
 * Slot 1 is slot 0 moved up by SLOT_STRIDE, LAUNCH mask included, and starts where slot 0 ends; the GO word says which
 * one to run. Kernels must therefore be position-independent and return through an absolute jump (see fw.ret).
 * L1_PARAM_BASE is shared, below both slots: it is only written when the launch that reads it is released. LAUNCH is an
 * active-role bitmask. Worker L1: firmware, params, slot 0, slot 1, then DATA_BASE.. for kernels. */
#define L1_PARAM_BASE     0x780
#define PARAM_SIZE        0x40     /* 16 words: DRAM addresses of the kernel's inputs and outputs, everything else is compiled in */
#define LAUNCH            0x7C0
#define CODE_BRISC        0x800
#define CODE_NCRISC       0x2800
#define CODE_TRISC0       0x4800
#define CODE_TRISC1       0x6000
#define CODE_TRISC2       0x7800
#define CODE_TRISC_SIZE   0x1800   /* each TRISC slot; fused attention (RoPE, split KV, merge) needs more than 4 KiB */
#define CODE_END          0x9000
#define SLOT_STRIDE       (CODE_END - LAUNCH)  /* 0x8840: slot 1 = [LAUNCH, CODE_END) + SLOT_STRIDE = [0x9000, 0x11840) */
#define SLOT_OFFSET(go)   ((go) >> GO_SLOT_BIT & 1 ? SLOT_STRIDE : 0)
#define DATA_BASE         (CODE_END + SLOT_STRIDE)  /* 0x11840: everything from here up is free for kernels */

/* Stacks live in each RISC's private local memory, not L1 */
#define STACK_TOP         0xFFB01FF0
#define TRISC_STACK_TOP   0xFFB00FF0
#define TRISC_GP          0xFFB007F0

/* ---- Service cores: CQ (dispatch on BRISC) and DMA (two copy engines) ---- */
/* Each queue is a ring of 32-byte packets {op, a, b, c} (u64 each) in host memory. The host submits compute work as a
 * CALL to a command buffer of the same packets. Programs and args must not change between submit and retire:
 * dispatch reads them ahead. */
#define PACKET            32
#define RING_SIZE         0x10000

#define OP_EXEC           0  /* a = dispatcher-local descriptor address, b = dynamic args, c = optional pair of 16-byte profile slots */
#define OP_COPY           1  /* a = dst, b = src, c = bytes */
#define OP_WAIT           2  /* until *a >= b, or *a == b if c */
#define OP_STORE          3  /* *a = b */
#define OP_TIMESTAMP      4  /* *a = wall clock */
#define OP_CALL           5  /* run c bytes of packets at a (DRAM or host), b_lo times (0 = 1), advancing by b_hi bytes.
                             * Each buffer finishes before the next starts. CQ only, not nested. */

/* Addresses in packets are 64-bit: bit 63 set = DRAM, bits 56-61 log2(page), banks interleaved by page.
 * Otherwise bits 32-43 are a NoC coordinate (bits 60+ set = PCIe/host) and 0-31 the address there. */

#define STATE             DATA_BASE
#define WPTR              (STATE + 0x00)  /* host -> fw: bytes pushed. The doorbell */
#define RPTR              (STATE + 0x04)  /* fw -> host: bytes retired */
#define RING_LO           (STATE + 0x08)  /* NoC address of this queue's ring in host memory */
#define RING_HI           (STATE + 0x0C)
#define GO_WORD           (STATE + 0x10)  /* CQ: the word multicast to GO_SIGNAL */
#define DMA_DONE          (STATE + 0x24)  /* DMA: packets finished, one word per engine */
#define DONE_COUNT        (STATE + 0x30)  /* CQ: each worker core increments this when its kernels return */
#define SCRATCH           (STATE + 0x40)  /* 0x80 per RISC, staging for 8-byte signal reads and writes */
#define STATE_SIZE        0x140
_Static_assert(STATE + STATE_SIZE <= 0x12000, "service-core state must end below GRAPH_L1");

/* CQ descriptor: 8 u32 header words {cores, go_rects, args_bytes, payload_bytes,
 * payload_lo, payload_hi, transfers, reserved}, followed by GO rectangles, then transfers.
 * Each transfer is {payload_offset, worker_address, bytes, rect_count}, followed by its rectangles.
 * Rectangle = start | end << 12. Descriptors are immutable until all referencing work retires. */
#define DESCRIPTOR_L1     0x40000
#define DESCRIPTOR_END    0x80000
#define CQ_PACKETS        0x10000  /* ring packets fetched by dispatch */
#define CQ_PACKETS_MAX    0x1000
#define GRAPH_L1          0x12000  /* two GRAPH_CHUNK buffers for OP_CALL */
#define GRAPH_CHUNK       0x1000
#define PARAMS_L1         0x14000  /* two PARAM_SIZE dynamic-argument buffers */
#define STAMP_L1          0x15000  /* deferred TIMESTAMPs (dispatch and DMA): STAMP_SLOTS x 64 bytes per NIU */
#define STAMP_SLOTS       32
#define STAGE_L1          0x18000  /* two packed program payload buffers, prefetched from DRAM */
#define STAGE_SIZE        0x10000

/* DMA core, per engine: two staging buffers, then the fetched packets */
#define DMA_BATCH         0x20000
#define DMA_PACKETS_MAX   0x800
#define DMA_STAGING       0x20000
#define DMA_STAGING_STRIDE 0x48000

#endif
