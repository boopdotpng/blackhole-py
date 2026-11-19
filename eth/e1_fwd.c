/* E1 forwarder. Local workers stage their slices of a partial vector in LINK_STAGE(tag & 1) and publish the tag in
   their ready word {tag, bytes, workers}. Once every worker shows the same new tag, E1 sends the whole stage to the peer's LINK_RECV and then
   a 16-byte packet with the tag to the peer's LINK_FLAG. Queue 2 delivers in order, so the flag lands after the data.
   Only TX queue 2 is used; queue, MAC and PCS configuration are the vendor firmware's and stay untouched. */
#include "hw.h"
#include "link.h"

#define TXQ(off) (0xFFB90000 + 2 * 0x1000 + (off))
#define CMD_DATA (1 << 1)

INLINE void txq_wait(void) {  /* BH-55: touch CMD before polling STATUS.cmd_ongoing (bit 16) */
  do { (void)read32(TXQ(0x4)); } while (read32(TXQ(0x8)) >> 16 & 1);
}

INLINE void send(u32 src, u32 dst, u32 len) {
  txq_wait();
  write32(TXQ(0x14), src);
  write32(TXQ(0x1C), dst);
  write32(TXQ(0x18), len);
  write32(TXQ(0x4), CMD_DATA);
}

__attribute__((noreturn)) static void main_loop(void) {
  volatile u32 *box = (volatile u32 *)LINK_BOX;
  u32 last = box[4];
  box[0] = LINK_MAGIC;
  for (u32 hb = 0;; hb++) {
    box[1] = hb;
    fence();
    u32 tag = read32(LINK_READY);
    if (tag == last) continue;
    u32 bytes = read32(LINK_READY + 4), workers = read32(LINK_READY + 8), w = 1;
    if (bytes > LINK_MAX_BYTES || workers > 64) { box[5] = tag; last = tag; continue; }  /* malformed: never sent */
    while (w < workers && read32(LINK_READY + 16 * w) == tag) w++;
    if (w < workers) continue;
    u32 p = tag & 1;
    send(LINK_STAGE(p), LINK_RECV(p), bytes);
    txq_wait();                       /* the queue may still be reading the previous flag packet */
    write32(LINK_FLAGSRC + 16 * p, tag);
    fence();
    send(LINK_FLAGSRC + 16 * p, LINK_FLAG(p), 16);
    box[4] = last = tag;
  }
}

__attribute__((section(".entry"), naked, noreturn)) void _start(void) {
  __asm__ volatile("li sp, %0\n j %1" :: "i"(LINK_BOX - 16), "i"(main_loop));
}
