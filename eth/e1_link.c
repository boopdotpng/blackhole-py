/* ERISC1 command loop for TT-link experiments. ERISC0 keeps the vendor base firmware; we use TX queue 2 only,
   which the base firmware sets up in TT-link mode and never issues transfers on. Nothing here changes queue,
   MAC or PCS configuration.
   Mailbox at BOX (u32 words):
     [0] magic  [1] heartbeat  [2] req (host bumps)  [3] done (E1 copies req when finished)
     [4] op  [5] src (local L1)  [6] dst (remote L1)  [7] len bytes / reg value / first seq  [8] repeat
     [9] cycles taken (E1 wall clock)
   OP_PING / OP_PONG measure the round trip: both sides count 16-byte packets into PING on the other card. PING sends
   seq then waits for the echo; PONG waits for seq then echoes it. src is a 16-byte local scratch word. */
#include "hw.h"

#define BOX    0x30000
#define MAGIC  0xE1A11E4C

#define TXQ(q, off)  (0xFFB90000 + (q) * 0x1000 + (off))
#define TXQ_CMD 0x4
#define TXQ_STATUS 0x8
#define TXQ_SRC 0x14
#define TXQ_SIZE 0x18
#define TXQ_DST 0x1C
#define TXQ_REG_DATA 0x44
#define CMD_DATA (1 << 1)
#define CMD_REG  (1 << 2)
#define Q 2

#define WALL_LO 0xFFB121F0

enum { OP_SEND = 1, OP_REG = 2, OP_PING = 3, OP_PONG = 4 };
#define PING 0x30100  /* the peer's packets land here */

INLINE void txq_wait(void) {  /* BH-55: touch CMD before polling STATUS.cmd_ongoing (bit 16) */
  do { (void)read32(TXQ(Q, TXQ_CMD)); } while (read32(TXQ(Q, TXQ_STATUS)) >> 16 & 1);
}

INLINE void send(u32 src, u32 dst, u32 len) {
  txq_wait();
  write32(TXQ(Q, TXQ_SRC), src);
  write32(TXQ(Q, TXQ_DST), dst);
  write32(TXQ(Q, TXQ_SIZE), len);
  write32(TXQ(Q, TXQ_CMD), CMD_DATA);
}

INLINE void reg(u32 dst, u32 v) {
  txq_wait();
  write32(TXQ(Q, TXQ_DST), dst);
  write32(TXQ(Q, TXQ_REG_DATA), v);
  write32(TXQ(Q, TXQ_CMD), CMD_REG);
}

__attribute__((noreturn)) static void main_loop(void) {
  volatile u32 *b = (volatile u32 *)BOX;
  u32 done = b[2];
  b[3] = done;
  b[0] = MAGIC;
  for (u32 hb = 0;; hb++) {
    b[1] = hb;
    fence();
    u32 req = b[2];
    if (req == done) continue;
    u32 op = b[4], src = b[5], dst = b[6], len = b[7], n = b[8] ? b[8] : 1;
    u32 t0 = read32(WALL_LO);
    for (u32 i = 0; i < n; i++) {
      u32 seq = len + 1 + i;
      if (op == OP_SEND) send(src, dst, len);
      else if (op == OP_REG) reg(dst, len);
      else if (op == OP_PING || op == OP_PONG) {
        if (op == OP_PONG) do { fence(); } while (read32(PING) != seq);
        txq_wait();
        write32(src, seq);
        fence();
        send(src, PING, 16);
        if (op == OP_PING) do { fence(); } while (read32(PING) != seq);
      }
    }
    txq_wait();
    b[9] = read32(WALL_LO) - t0;
    b[3] = done = req;
  }
}

__attribute__((section(".entry"), naked, noreturn)) void _start(void) {
  __asm__ volatile("li sp, %0\n j %1" :: "i"(BOX - 16), "i"(main_loop));
}
