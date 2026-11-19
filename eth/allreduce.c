/* Cross-card all-reduce of a bf16 vector, one BRISC per slice: output = bf16((p0 + p1) + residual), summed in FP32
   in card order so both cards produce the same bits. A worker stages its partial slice in the Ethernet tile, waits
   for the peer's slice of the same tag, then adds.
   Defines: GRID, DIM, RANK (0/1), ETH (NoC0 coordinate), NSLOT, *_SLOT parameter slots, SCRATCH_ADDR. */
#include "noc.h"
#include "worker.h"
#include "link.h"

typedef unsigned short bf16;
#define SLICE (DIM / GRID)
#define TIMEOUT_CYCLES (1350u * 1000 * 1000)   /* ~1 s at AICLK */

static void dram(int write, int slot, u32 elem, void *local, u32 bytes) {
  u32 base = read32(L1_PARAM_BASE + 4 * slot);
  u32 low = ((base & ~7u) << 3) + ((base & 7) << 11);   /* per-bank address + first bank, 2 KiB pages */
  u32 high = (1u << 31) | (11u << 24) | (base >> 29);
  noc_move(0, write, low, high, 2 * elem, bytes, (u32)local, 1);
  noc_wait(0, 1, 1);
}
static void eth_read(u32 remote, void *local, u32 bytes) { noc_read(0, remote, ETH, (u32)local, bytes); }
static void eth_write(u32 remote, void *local, u32 bytes) { noc_write(0, remote, ETH, (u32)local, bytes); }

static float load(bf16 x) { union { u32 u; float f; } v = {.u = (u32)x << 16}; return v.f; }
static bf16 store(float f) {
  union { float f; u32 u; } v = {.f = f};
  if ((v.u & 0x7F800000) == 0x7F800000) return v.u >> 16 | ((v.u & 0xFFFF) ? 0x40 : 0);  /* inf / quiet NaN */
  return (v.u + 0x7FFF + (v.u >> 16 & 1)) >> 16;
}

typedef struct {
  bf16 mine[SLICE], peer[SLICE], residual[SLICE], out[SLICE];
  u32 word[4];
} Scratch;

KERNEL kernel_main(void) {
  noc_init(0);
  Scratch *s = (Scratch *)SCRATCH_ADDR;
  u32 w = read32(WORKER_ID), first = w * SLICE;
  u32 tag = read32(L1_PARAM_BASE + 4 * STEP_SLOT) * NSLOT + read32(L1_PARAM_BASE + 4 * SLOT_SLOT);
  u32 p = tag & 1;

  dram(0, PARTIAL_SLOT, first, s->mine, sizeof s->mine);
  eth_write(LINK_STAGE(p) + 2 * first, s->mine, sizeof s->mine);   /* noc_write waits for the ack ... */
  s->word[0] = tag; s->word[1] = 2 * DIM; s->word[2] = GRID; s->word[3] = 0;
  eth_write(LINK_READY + 16 * w, s->word, 16);                     /* ... so E1 never sees ready before data */
  dram(0, RESIDUAL_SLOT, first, s->residual, sizeof s->residual);

  u32 t0 = read32(WALL_CLOCK_L), ok = 1;
  for (;;) {
    eth_read(LINK_FLAG(p), s->word, 16);
    if (s->word[0] == tag) break;
    if (read32(WALL_CLOCK_L) - t0 > TIMEOUT_CYCLES) { ok = 0; break; }
  }
  if (ok) eth_read(LINK_RECV(p) + 2 * first, s->peer, sizeof s->peer);
  for (u32 i = 0; i < SLICE; i++) {
    float a = load(s->mine[i]), b = ok ? load(s->peer[i]) : __builtin_nanf("");
    float sum = RANK == 0 ? a + b : b + a;
    s->out[i] = store(sum + load(s->residual[i]));
  }
  dram(1, OUTPUT_SLOT, first, s->out, sizeof s->out);
  JUMP(FW_BRISC + 4);
}
