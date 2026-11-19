/* Probe kernel library: plain C (clang, rv32im, no SFPI) on blackhole-py's resident worker firmware.
 *
 * A probe is one BRISC kernel, launched directly by sims/probes/tile.py (no CQ). It reads its arguments from the
 * launch parameter words, logs u32 records to LOG, and must end with probe_done(). Every wait that depends on the NoC
 * goes through WAIT_UNTIL, which gives up after BUDGET polls: the kernel then records which wait (a small site
 * number) in RES_SITE, sets RES_STATUS = ST_TIMEOUT and returns to the firmware, so the tile is free again.
 * Pure clock spins end on their own and are not bounded.
 *
 * Command buffers are programmed completely before each use: the firmware's done-atomic leaves NoC1 buffer 0 with
 * an atomic CTRL and transaction id 1. */
#ifndef PROBE_H
#define PROBE_H
#include "hw.h"

/* ---- L1 layout, mirrored in tile.py. RES/LOG/PARAM_AT/RETURN_ADDR are per role, passed by tile.build ---- */
#ifndef PARAM_AT
#define PARAM_AT    L1_PARAM_BASE    /* brisc: shared launch words; ncrisc: its own 16 words (tile.py) */
#endif
#define PARAM(i)    read32(PARAM_AT + 4 * (i))  /* 16 launch words */
#ifndef RES
#define RES         0x20000
#endif
#ifndef LOG
#define LOG         0x21000         /* up to RES + 0x10000 */
#endif
#define RES_STATUS  (RES + 0x0)
#define RES_SITE    (RES + 0x4)
#define RES_COUNT   (RES + 0x8)     /* u32 records written to LOG */
#define RES_AUX     (RES + 0x10)    /* 60 kernel-defined words, to RES + 0x100 */
#define FLAG        0x40000         /* word a receiver polls */
#define FLAG2       0x40040
#define READY_WORD  0x40100         /* receiver -> sender handshake */
#define PAYLOAD     0x100000        /* NoC source / destination, up to 0x180000 */

#define ST_DONE     0xD0E0D0E0u
#define ST_TIMEOUT  0x7E000000u
#define BUDGET      (1u << 22)      /* polls per wait: >= ~5 cycles each, so >= ~15 ms at 1.35 GHz */

#ifndef RETURN_ADDR
#define RETURN_ADDR (FW_BRISC + 4)
#endif

INLINE u32 now(void) { return read32(WALL_CLOCK_L); }

__attribute__((noinline, noreturn)) static void probe_fail(u32 site) {
  write32(RES_SITE, site);
  write32(RES_STATUS, ST_TIMEOUT);
  fence();
  JUMP(RETURN_ADDR);
}

INLINE NORETURN probe_done(void) {
  write32(RES_STATUS, ST_DONE);
  fence();
  JUMP(RETURN_ADDR);
}

/* WAIT_UNTIL is for MMIO (NIU counters, command buffers, Tensix semaphores): no fence, as the kernels poll them. */
#define WAIT_UNTIL(cond, site) do {                                   \
    u32 left_ = BUDGET;                                               \
    while (!(cond)) if (__builtin_expect(!--left_, 0)) probe_fail(site); \
  } while (0)
/* WAIT_L1 is for words in L1 written by the NoC, the host or another RISC. The firmware runs with the L0 data cache on
 * and L0 is not coherent: the fence on every retry flushes it so the poll sees a new value at once, not after a random
 * periodic flush, and the fence after the loop makes later reads of other such words fresh too. */
#define WAIT_L1(cond, site) do {                                      \
    u32 left_ = BUDGET;                                               \
    while (!(cond)) { fence(); if (__builtin_expect(!--left_, 0)) probe_fail(site); } \
    fence();                                                          \
  } while (0)

/* ---- NIU ---- */
#define NIU(noc)          (0xFFB20000u + (noc) * 0x10000u)
#define CMDBUF(noc, buf)  (NIU(noc) + (buf) * 0x800u)
#define NIU_STATUS(noc, i) (NIU(noc) + 0x200u + 4u * (i))
#define NIU_NODE_ID(noc)  (NIU(noc) + 0x148u)  /* NOC_ID_LOGICAL: same frame the host and GO word use */

/* command buffer registers (byte offsets) */
#define C_TARG_LO 0x00
#define C_TARG_MID 0x04
#define C_TARG_COORD 0x08
#define C_RET_LO 0x0C
#define C_RET_MID 0x10
#define C_RET_COORD 0x14
#define C_PACKET_TAG 0x18
#define C_CTRL 0x1C
#define C_AT_LEN_BE 0x20
#define C_AT_LEN_BE_1 0x24
#define C_AT_DATA 0x28
#define C_BRCST_EXCLUDE 0x2C
#define C_CMD_CTRL 0x40

/* CTRL bits */
#define CTRL_ATOMIC       (1u << 0)
#define CTRL_WRITE        (1u << 1)
#define CTRL_WR_INLINE    (1u << 3)
#define CTRL_RESP_MARKED  (1u << 4)  /* reads always; writes: non-posted (acked) */
#define CTRL_BRCST        (1u << 5)
#define CTRL_VC_STATIC    (1u << 7)
#define CTRL_PATH_RESERVE (1u << 8)
#define CTRL_STATIC_VC(v) ((u32)(v) << 13)
#define CTRL_ARB_PRIO(p)  ((u32)(p) << 27)
#define TAG_TID(t)        ((u32)(t) << 10)
#define AT_INCREMENT      (1u << 12 | 31u << 2)  /* atomic increment, wrapping at bit 31 */

/* NIU_MST status counters (index for NIU_STATUS) */
enum { CNT_ATOMIC_RESP = 0x0, CNT_WR_ACK = 0x1, CNT_RD_RESP = 0x2, CNT_RD_DATA_WORD = 0x3, CNT_CMD_ACCEPTED = 0x4,
       CNT_RD_REQ_SENT = 0x5, CNT_NP_ATOMIC_SENT = 0x6, CNT_P_ATOMIC_SENT = 0x7, CNT_NP_WR_WORD_SENT = 0x8,
       CNT_P_WR_WORD_SENT = 0x9, CNT_NP_WR_SENT = 0xA, CNT_P_WR_SENT = 0xB };

INLINE u32 my_coord(u32 noc) { return read32(NIU_NODE_ID(noc)) & 0xFFF; }
INLINE u32 coord(u32 x, u32 y) { return x | y << 6; }

#define WAIT_CMD_READY(c, site) WAIT_UNTIL(!read32((c) + C_CMD_CTRL), site)

/* Send what is programmed in `c`. Returns the wall clock read just before the CMD_CTRL store. The fences match
 * fw/noc.c: without the trailing one a following ready-poll can pass the store. */
INLINE u32 fire(u32 c) {
  fence();
  u32 t = now();
  write32(c + C_CMD_CTRL, 1);
  fence();
  return t;
}

INLINE void cmd_common(u32 c, u32 tid, u32 len, u32 ctrl) {
  write32(c + C_PACKET_TAG, TAG_TID(tid));
  write32(c + C_CTRL, ctrl);
  write32(c + C_AT_LEN_BE, len);
  write32(c + C_AT_LEN_BE_1, 0);
  write32(c + C_AT_DATA, 0);
  write32(c + C_BRCST_EXCLUDE, 0);
}

/* local [src, src+size) -> `dst_coord`:dst. ctrl_extra adds RESP_MARKED (non-posted), VC bits, ... */
INLINE void cmd_write(u32 c, u32 noc, u32 src, u32 dst_coord, u32 dst, u32 size, u32 ctrl_extra) {
  write32(c + C_TARG_LO, src); write32(c + C_TARG_MID, 0); write32(c + C_TARG_COORD, my_coord(noc));
  write32(c + C_RET_LO, dst); write32(c + C_RET_MID, 0); write32(c + C_RET_COORD, dst_coord);
  cmd_common(c, 0, size, CTRL_WRITE | ctrl_extra);
}

/* `src_coord`:src -> local [dst, dst+size) */
INLINE void cmd_read(u32 c, u32 noc, u32 src_coord, u32 src, u32 dst, u32 size, u32 ctrl_extra) {
  write32(c + C_TARG_LO, src); write32(c + C_TARG_MID, 0); write32(c + C_TARG_COORD, src_coord);
  write32(c + C_RET_LO, dst); write32(c + C_RET_MID, 0); write32(c + C_RET_COORD, my_coord(noc));
  cmd_common(c, 0, size, CTRL_RESP_MARKED | ctrl_extra);
}

/* 4-byte inline write of AT_DATA (set with cmd_inline_value) to `dst_coord`:dst */
INLINE void cmd_inline(u32 c, u32 dst_coord, u32 dst, u32 ctrl_extra) {
  write32(c + C_TARG_LO, dst); write32(c + C_TARG_MID, 0); write32(c + C_TARG_COORD, dst_coord);
  cmd_common(c, 0, 0xF, CTRL_WRITE | CTRL_WR_INLINE | ctrl_extra);
}
INLINE void cmd_inline_value(u32 c, u32 v) { write32(c + C_AT_DATA, v); }

/* Posted 4-byte inline write, then wait until the buffer has sent it. Uses buffer `buf` of `noc`. */
INLINE void signal_word(u32 noc, u32 buf, u32 dst_coord, u32 dst, u32 value, u32 site) {
  u32 c = CMDBUF(noc, buf);
  WAIT_CMD_READY(c, site);
  cmd_inline(c, dst_coord, dst, 0);
  cmd_inline_value(c, value);
  fire(c);
  WAIT_CMD_READY(c, site);
}

INLINE void log_word(u32 i, u32 v) { write32(LOG + 4 * i, v); }

/* ---- DRAM (p150, fw/noc.c and ttrv/noc.py) ----
 * 8 banks, pages interleaved: page i lives in bank i % 8 at bank offset (i / 8) * page. Each bank has three NoC
 * endpoints (ports) in columns x = 17 (banks 0-3) and 18 (banks 4-7). Llama picks the port per core:
 * endpoint = DRAM_PORT_Y[bank][(port + bank) % 3]. */
static const unsigned char DRAM_PORT_Y[8][3] = {{14, 13, 12}, {15, 16, 17}, {18, 19, 20}, {21, 22, 23},
                                                {14, 13, 12}, {17, 16, 15}, {20, 19, 18}, {23, 22, 21}};
INLINE u32 dram_coord(u32 bank, u32 port) { return coord(17 + (bank >> 2), DRAM_PORT_Y[bank][(port + bank) % 3]); }

#endif
