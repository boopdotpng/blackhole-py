#include "crt0.h"

#ifdef ROLE_BRISC
#define ROLE 0
#define STEP brisc_step
#elif defined(ROLE_NCRISC)
#define ROLE 1
#define STEP ncrisc_step
#else
#define ROLE (2 + ROLE_TRISC)
#define STEP trisc_step
#endif

typedef struct { u32 base, count, pc[5], words, streams, early_weights; } Kernel;
typedef struct { const Kernel *kernel; const u32 *args; const u32 *patch; u32 join; } Row;
_Static_assert(sizeof(Kernel) == 40 && sizeof(Row) == 16, "host table ABI mismatch");
extern void run_kernel(u32 pc);

void STEP(void) {
#ifdef ROLE_TRISC
  // Table dispatch can switch kernels after every return from Tensix.
  configure_csr(0);
#endif
  const Row *rows = (const Row *)read32(STEP_ARGS);
  u32 count = read32(STEP_ARGS + 4), id = read32(WORKER_ID);
  u32 joined = 0, prior_streams = 0, streams = 0;
#ifdef ROLE_NCRISC
  u32 participated = 0, stamps = read32(STEP_ARGS + 16);
  if (!id && stamps) write32(stamps, read32(WALL_CLOCK_L));
#endif
  // Host installs immutable code before ringing the doorbell. Each RISC
  // invalidates its own instruction cache after waking from idle.
#ifdef ROLE_TRISC
  write32(CFG_RISCV_IC_INVALIDATE, 2u << ROLE_TRISC);
#elif defined(ROLE_BRISC)
  invalidate_icache();
#endif
  fence();
  for (u32 i = 0; i < count; i++) {
    const Row *r = rows + i;
    const Kernel *k = r->kernel;
    // Only the decode projection's BRISC touches the reserved weight stream.
    // It may fill it while the preceding stage drains compute and writeback.
    if (ROLE != 0 || !k->early_weights || (prior_streams & (1u << 31)))
      WAIT_SLOW(read32(ROLE_RELEASE) >= joined);
    if (id - k->base < k->count && k->pc[ROLE]) {
      for (u32 a = 0; a < k->words; a++) write32(L1_PARAM_BASE + 4*a, r->args[a]);
      if (r->patch)
        for (const u32 *p = r->patch; *p; p++)
          write32(L1_PARAM_BASE + 4*((*p & 255) - 1), read32(ARG_VALUES + 4*(*p >> 8)));
      fence();
#ifdef ROLE_TRISC
      write32(CFG_RISCV_IC_INVALIDATE, 2u << ROLE_TRISC);
      fence();
#endif
      run_kernel(k->pc[ROLE]);
#ifdef ROLE_TRISC
      tensix_drain();
#endif
    }
    streams |= k->streams;
#ifdef ROLE_NCRISC
    participated |= id - k->base < k->count;
#endif
    if (!r->join) continue;  // disjoint workers in the same dependency group
    fence();
    write32(ROLE_PROGRESS + ROLE * 4, i + 1);
#ifdef ROLE_NCRISC
    for (u32 role = 0; role < 5; role++)
      WAIT_SLOW(read32(ROLE_PROGRESS + role * 4) >= i + 1);
    for (u32 mask = streams; mask; mask &= mask - 1) {
      u32 cb = __builtin_ctz(mask);
      write32(STREAM_REG(8 + cb, 8), 0);
      write32(STREAM_REG(8 + cb, 10), 0);
    }
    fence();
    if (!id) {
      WAIT_FAST(read32(SYNC_ARRIVED) == r->join - 1);
      write32(SYNC_ARRIVED, 0);
      write32(SYNC_EPOCH, i + 1);
      if (stamps) write32(stamps + 4*(i + 1), read32(WALL_CLOCK_L));
      fence();
      // BRISC lookahead only issues weight reads. NoC0 multicast has its own command buffer.
      noc_mcast(0, SYNC_EPOCH, SYNC_EPOCH, read32(STEP_ARGS + 8), read32(STEP_ARGS + 12), 4);
      noc_mcast_flush(0);
    } else {
      if (participated) noc_atomic_inc(1, SYNC_ARRIVED, read32(LEADER_COORD), 1);
      WAIT_SLOW(read32(SYNC_EPOCH) >= i + 1);
    }
    participated = 0;
    write32(ROLE_RELEASE, i + 1);
#endif
    prior_streams = streams;
    streams = 0;
    joined = i + 1;
  }
}
