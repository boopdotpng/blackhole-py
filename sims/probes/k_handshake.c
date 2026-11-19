/* Ping-pong between two RISCs of one tile (handshake.py). The initiator bumps word A, the responder waits for it and
 * bumps word B, the initiator waits for B: one round trip. After WARM round trips, SAMPLES timed samples of N round
 * trips each; the initiator logs (t0, t1) per sample.
 *
 * mode 0: L1 words (store + fence; poll with a fence per retry: L0 data cache is not coherent)
 * mode 1: overlay stream registers (CB pushed counters, as ttrv's CBs; MMIO, low 16 bits)
 * mode 2: Tensix semaphores through PC_BUF (TRISCs only): post = store 0, wait value != 0, then get = store 1
 * params: mode, initiator(1/0), A addr, B addr, N, SAMPLES, WARM */
#include "probe.h"

#define SEM_ACCESS(i) (0xFFE80020u + 4u * (i))

INLINE void post(u32 mode, u32 addr, u32 v) {
  if (mode == 0) { write32(addr, v); fence(); }
  else if (mode == 1) write32(addr, v);
  else write32(addr, 0);
}

INLINE void wait_for(u32 mode, u32 addr, u32 v, u32 site) {
  if (mode == 0) WAIT_L1(read32(addr) == v, site);
  else if (mode == 1) WAIT_UNTIL((read32(addr) & 0xFFFF) == (v & 0xFFFF), site);
  else { WAIT_UNTIL(read32(addr) != 0, site); write32(addr, 1); WAIT_UNTIL(read32(addr) == 0, site); }
}

KERNEL kernel_main(void) {
  u32 mode = PARAM(0), init = PARAM(1), a = PARAM(2), b = PARAM(3), n = PARAM(4), samples = PARAM(5), warm = PARAM(6);
  u32 seq = 0, k = 0;
  for (u32 s = 0; s <= samples; s++) {
    u32 rounds = s ? n : warm;
    u32 t0 = now();
    for (u32 i = 0; i < rounds; i++) {
      seq++;
      if (init) { post(mode, a, seq); wait_for(mode, b, seq, 2); }
      else { wait_for(mode, a, seq, 1); post(mode, b, seq); }
    }
    u32 t1 = now();
    if (s) { log_word(k++, t0); log_word(k++, t1); }
  }
  write32(RES_COUNT, k);
  probe_done();
}
