/* Cross-card greedy pick after a vocabulary-split LM head. Each card's argmax left (key, global token) in winner;
   exchange them over TT-link, keep the larger key (rank 0 holds the lower tokens, so it wins ties), then write the
   token to the host slot and, during generation, append it to the history, as single-card argmax does.
   One worker. Defines: RANK, ETH, NSLOT, *_SLOT, SCRATCH_ADDR. */
#include "noc.h"
#include "worker.h"
#include "link.h"

#define TIMEOUT_CYCLES (1350u * 1000 * 1000)
#define PARAM(slot) read32(L1_PARAM_BASE + 4 * (slot))

static void dram32(int write, int slot, u32 offset, void *local, u32 bytes) {  /* u32 buffers: 4 KiB pages */
  u32 base = PARAM(slot);
  u32 low = ((base & ~7u) << 3) + ((base & 7) << 12);  /* per-bank address x 8 banks + bank x page */
  u32 high = (1u << 31) | (12u << 24) | (base >> 29);
  noc_move(0, write, low, high, offset, bytes, (u32)local, 1);
  noc_wait(0, 1, 1);
}

typedef struct { u32 mine[4], peer[4], word[4], line[16]; } Scratch;

KERNEL kernel_main(void) {
  noc_init(0);
  Scratch *s = (Scratch *)SCRATCH_ADDR;
  u32 tag = PARAM(STEP_SLOT) * NSLOT + PARAM(SLOT_SLOT), p = tag & 1, pos = PARAM(START_POS_SLOT) + 1;
  dram32(0, WINNER_SLOT, 0, s->mine, 16);
  noc_write(0, LINK_STAGE(p), ETH, (u32)s->mine, 16);
  s->word[0] = tag; s->word[1] = 16; s->word[2] = 1; s->word[3] = 0;
  noc_write(0, LINK_READY, ETH, (u32)s->word, 16);
  u32 t0 = read32(WALL_CLOCK_L), ok = 1;
  for (;;) {
    noc_read(0, LINK_FLAG(p), ETH, (u32)s->word, 16);
    if (s->word[0] == tag) break;
    if (read32(WALL_CLOCK_L) - t0 > TIMEOUT_CYCLES) { ok = 0; break; }
  }
  u32 best;
  if (ok) {
    noc_read(0, LINK_RECV(p), ETH, (u32)s->peer, 16);
    u32 *a = RANK == 0 ? s->mine : s->peer, *b = RANK == 0 ? s->peer : s->mine;
    best = b[0] > a[0] ? b[1] : a[1];
  } else best = 0xFFFFFFFF;   /* the host sees an impossible token */
  s->word[0] = best; s->word[1] = s->word[2] = s->word[3] = 0;
  noc_move(0, 1, PARAM(TOKENS_SLOT), PARAM(TOKENS_SLOT + 1), 16 * pos, 16, (u32)s->word, 1);
  noc_wait(0, 1, 1);
  if (PARAM(WRITE_TOKEN_SLOT) && ok) {
    dram32(0, HISTORY_SLOT, 4 * (pos & ~15u), s->line, 64);
    s->line[pos & 15] = best;
    dram32(1, HISTORY_SLOT, 4 * (pos & ~15u), s->line, 64);
  }
  JUMP(FW_BRISC + 4);
}
