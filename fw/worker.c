// Resident 5-RISC worker firmware (booted once per Device; never SOFT_RESET between kernels).
// Reset sequence and BRISC <-> NCRISC/TRISC0..2 step handoff adapted from blackhole-py-archive/fw/crt0.h + hw.h.
#include "noc.h"

#define IS_TRISC           (ROLE >= ROLE_TRISC0)
#define TRISC_ID           (ROLE - ROLE_TRISC0)
#define SETC16(reg)        (0xB2000000u | (reg) << 16)
#define STREAM_REG(s, reg) (OVERLAY_STREAMS + (s) * STREAM_STRIDE + 4 * (reg))

#define SUBORDINATE_HELD   0x40404040u
#define SUBORDINATE_UP     2u

extern void run_kernel(u32 pc, u32 tp_val, u32 t0_val);

#if ROLE == ROLE_BRISC
#define SECOND NOC_REGS(0)
#elif ROLE == ROLE_NCRISC
#define SECOND NOC_REGS(1)
#elif ROLE == ROLE_TRISC0
#define SECOND TENSIX_CFG
#else
#define SECOND PC_BUF
#endif

#if IS_TRISC
#define STACK TRISC_STACK_TOP
#else
#define STACK STACK_TOP
#endif

__asm__(".section .entry, \"ax\", @progbits\n"
        SET_SP(STACK)
        "j worker_main\n");

#if !IS_TRISC
static void noc_init_worker(u32 niu) {
  u32 self = read32(NODE_ID(niu)) & 0xFFF;
  for (u32 buf = MCAST_BUF; buf <= ATOMIC_BUF; buf++) {
    volatile u32 *c = CMD_BUF(niu, buf);
    u32 is_write = buf == MCAST_BUF || buf == WRITE_BUF;
    c[is_write ? TARG_COORD : RET_COORD] = self;
    c[is_write ? TARG_MID : RET_MID] = 0;
    c[AT_LEN_BE_1] = 0;
    c[AT_DATA] = 0;
    c[BRCST_EXCLUDE] = 0;
  }
  fence();
  for (u32 tid = 0; tid < 16; tid++) write32(NOC_BASELINE + 4 * tid, read32(OUTSTANDING(niu, tid)));
}

static void noc_drain_all(u32 niu) {
  WAIT_SLOW(CMD_BUF(niu, READ_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, WRITE_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, MCAST_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, ATOMIC_BUF)[CMD_CTRL] == 0);
  for (u32 tid = 0; tid < 16; tid++) {
    WAIT_SLOW(read32(OUTGOING(niu, tid)) == 0);
    WAIT_SLOW(read32(OUTSTANDING(niu, tid)) == read32(NOC_BASELINE + 4 * tid));
  }
}
#endif

#if ROLE == ROLE_BRISC

void kernel_noc_wait(u32 niu, u32 tid, u32 acked);
void kernel_noc_read(u32 niu, u32 lo, u32 hi, u32 off, u32 size, u32 local, u32 tid) {
  if (((lo + off) ^ local) & 63) {
    for (u32 done = 0; done < size;) {
      u32 chunk = MIN(size - done, NOC_READ_STAGE - 64);
      u32 stage = NOC_READ_SCRATCH + niu * NOC_READ_STAGE + ((lo + off + done) & 63);
      noc_move_paced(niu, 0, lo, hi, off + done, chunk, stage, tid, 0);
      kernel_noc_wait(niu, tid, 1);
      u32 i = 0;
      if (!((stage | (local + done)) & 3)) {
        for (; i + 4 <= chunk; i += 4) write32(local + done + i, read32(stage + i));
      }
      for (; i < chunk; i++) *(volatile u8 *)(local + done + i) = *(volatile u8 *)(stage + i);
      done += chunk;
    }
    fence();
  } else {
    u32 workers = read32(NUM_WORKERS), cap = workers >= 88 ? 2 : workers >= 42 ? 8 : 0;
    noc_move_paced_base(niu, 0, lo, hi, off, size, local, tid, cap, read32(NOC_BASELINE + 4 * tid));
  }
}
void kernel_noc_write(u32 niu, u32 lo, u32 hi, u32 off, u32 size, u32 local, u32 tid) {
  if (((lo + off) ^ local) & 15) {
    for (u32 done = 0; done < size;) {
      u32 chunk = MIN(size - done, NOC_READ_STAGE - 16);
      u32 stage = NOC_READ_SCRATCH + niu * NOC_READ_STAGE + ((lo + off + done) & 15);
      for (u32 i = 0; i < chunk; i++) *(volatile u8 *)(stage + i) = *(volatile u8 *)(local + done + i);
      fence();
      noc_move_paced(niu, 1, lo, hi, off + done, chunk, stage, tid, 0);
      kernel_noc_wait(niu, tid, 1);
      done += chunk;
    }
  } else noc_move_paced(niu, 1, lo, hi, off, size, local, tid, 0);
}
void kernel_noc_wait(u32 niu, u32 tid, u32 acked) {
  WAIT_SLOW(CMD_BUF(niu, READ_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, WRITE_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, MCAST_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(CMD_BUF(niu, ATOMIC_BUF)[CMD_CTRL] == 0);
  WAIT_SLOW(read32(OUTGOING(niu, tid)) == 0);
  if (acked) WAIT_SLOW(read32(OUTSTANDING(niu, tid)) == read32(NOC_BASELINE + 4 * tid));
}
void kernel_noc_mcast(u32 niu, u32 local, u32 remote, u32 rect, u32 size, u32 tid, u32 include_sender) {
  noc_mcast(niu, local, remote, rect, size, tid, include_sender);
}
void kernel_noc_inc(u32 niu, u32 remote, u32 target, u32 tid) {
  noc_inc_worker(niu, remote, target, tid);
}

static void install_jump(u32 at, u32 target) {
  u32 off = target - at;
  write32(at, 0x6F | (off & 0x100000) << 11 | (off & 0x7FE) << 20 |
               (off & 0x800) << 9 | (off & 0xFF000));
}

// One-time Tensix boot reset (adapted from blackhole-py-archive/fw/hw.h, without CLEARDVALID(reset=1)).
static void reset_tensix_boot(void) {
  write32(TENSIX_CFG + CFG_STATE_RESET * 4, 0);
  write32(TENSIX_CFG + (CFG_BANK_WORDS + CFG_STATE_RESET) * 4, 0);
  for (u32 i = CFG_GLOBAL_BASE; i < 185; i++) write32(TENSIX_CFG + 4 * i, 0);
  for (u32 i = 187; i < CFG_BANK_WORDS; i++) write32(TENSIX_CFG + 4 * i, 0);
  TT(ZEROACC_ALL);
  TT(SFPENCC_RESET);
  TT(NOP);
  TT(SFPLOADI_MINUS1);
  TT(SFPCONFIG_L11);
  write32(CFG_ECC_SCRUBBER, 0x803);
  TT(SEMINIT_ALL);
  for (u32 s = CB_STREAM0; s < CB_STREAM0 + CBS; s++) {
    write32(STREAM_REG(s, CB_PUSHED), 0);
    write32(STREAM_REG(s, CB_POPPED), 0);
  }
  write32(CFG_RISC_PREFETCH_CTRL, 0x11F);
}

// Fast per-dispatch Tensix reset: hardware config-bank clear + 6 Tensix words (no global/ECC loop).
static void reset_tensix_step(void) {
  write32(TENSIX_CFG + CFG_STATE_RESET * 4, 0);
  write32(TENSIX_CFG + (CFG_BANK_WORDS + CFG_STATE_RESET) * 4, 0);
  TT(ZEROACC_ALL);
  TT(SFPENCC_RESET);
  TT(NOP);
  TT(SFPLOADI_MINUS1);
  TT(SFPCONFIG_L11);
  TT(SEMINIT_ALL);
}

static void boot_subordinates(void) {
  u32 reset = RESET_ALL & ~RESET_BRISC, expect = SUBORDINATE_HELD, trisc_override = 0, pc;
  write32(SUBORDINATE_SYNC, SUBORDINATE_HELD);
  write32(STEP_TOKEN, read32(WALL_CLOCK_L) | 1);
  write32(TENSIX_READY, 0);
  if ((pc = read32(ROLE_PC))) {
    write32(NCRISC_RESET_PC, pc);
    write32(NCRISC_RESET_PC_OVERRIDE, 1);
    reset &= ~RESET_NCRISC;
    expect ^= 0x40u ^ SUBORDINATE_UP;
  }
  for (u32 i = 0; i < 3; i++) {
    if (!(pc = read32(ROLE_PC + 4 + 4 * i))) continue;
    write32(TRISC0_RESET_PC + 4 * i, pc);
    trisc_override |= 1u << i;
    reset &= ~(RESET_TRISC0 << i);
    expect ^= (0x40u ^ SUBORDINATE_UP) << 8 * (i + 1);
  }
  if (trisc_override) write32(TRISC_RESET_PC_OVERRIDE, trisc_override);
  fence();
  write32(SOFT_RESET, reset);
  WAIT_FAST(read32(SUBORDINATE_SYNC) == expect);
}

NORETURN worker_main(void) {
  configure_csr(0);
  invalidate_icache();

  u32 node = read32(NODE_ID(0)), x = node & 63, y = (node >> 6 & 63) - 2;
  x -= x >= 10 ? 3 : 1;
  write32(WORKER_X, x);
  write32(WORKER_Y, y);
  write32(WORKER_ID, x * 10 + y);

  enable_clock_gating();
  noc_init_worker(0);
  noc_init(0);
  install_jump(FN_NOC_READ, (u32)kernel_noc_read);
  install_jump(FN_NOC_WRITE, (u32)kernel_noc_write);
  install_jump(FN_NOC_WAIT, (u32)kernel_noc_wait);
  install_jump(FN_NOC_MCAST, (u32)kernel_noc_mcast);
  install_jump(FN_NOC_INC, (u32)kernel_noc_inc);

  write32(STEP_EPOCH, 0);
  boot_subordinates();
  reset_tensix_boot();
  for (u32 at = MCAST_CTRL_BASE; at < MCAST_CTRL_BASE + 0x400; at += 4) write32(at, 0);
  fence();
  write32(WORK_READY, 1);
  fence();

  u32 last_epoch = 0, last_cache_epoch = 0;
  for (;;) {
    u32 ep;
    WAIT_FAST((ep = read32(STEP_EPOCH)) != last_epoch);
    last_epoch = ep;

    u32 pc_brisc  = read32(KERNEL_PC + 0);
    u32 pc_ncrisc = read32(KERNEL_PC + 4);
    u32 pc_t0     = read32(KERNEL_PC + 8);
    u32 pc_t1     = read32(KERNEL_PC + 12);
    u32 pc_t2     = read32(KERNEL_PC + 16);
    u32 any_trisc = (pc_t0 | pc_t1 | pc_t2) != 0;

    write32(NUM_WORKERS, read32(DISP_NUM_WORKERS));

    if (read32(DISP_FLAGS) & FLAG_CLEAR_MCAST) {
      for (u32 at = MCAST_CTRL_BASE; at < MCAST_CTRL_BASE + 0x400; at += 4) write32(at, 0);
    }

    u32 cb_mask = read32(DISP_CB_MASK);
    for (u32 m = cb_mask; m; m &= m - 1) {
      u32 cb = (u32)__builtin_ctz(m);
      write32(STREAM_REG(CB_STREAM0 + cb, CB_PUSHED), 0);
      write32(STREAM_REG(CB_STREAM0 + cb, CB_POPPED), 0);
    }

    if (any_trisc) reset_tensix_step();

    u32 ce = read32(DISP_CACHE_EPOCH);
    if (ce != last_cache_epoch) {
      write32(CFG_RISCV_IC_INVALIDATE, 0x11u);  // BRISC (bit 0) + NCRISC (bit 4)
      fence();
      last_cache_epoch = ce;
    }

    for (u32 tid = 0; tid < 16; tid++) write32(NOC_BASELINE + 4 * tid, read32(OUTSTANDING(0, tid)));

    u32 tok = read32(STEP_TOKEN) + 1;
    write32(STEP_TOKEN, tok);
    fence();
    if (pc_ncrisc) write8(SUBORDINATE_SYNC, 0x80);
    if (any_trisc) {
      for (u32 i = 0; i < 3; i++) write32(PCBUF(i), tok);
    }
    fence();

    if (pc_brisc) run_kernel(pc_brisc, SECOND + 2048, 0);

    noc_drain_all(0);
    if (pc_ncrisc) WAIT_SLOW(read8(SUBORDINATE_SYNC) == 0);
    if (any_trisc) {
      for (u32 i = 0; i < 3; i++) {
        while (read32(MAILBOX_FROM(i)) != tok) {}
      }
    }
    fence();
    noc_atomic_inc(0, CP_WORK_DONE, read32(LEADER_COORD));
  }
}

#elif ROLE == ROLE_NCRISC

NORETURN worker_main(void) {
  configure_csr(0);
  noc_init_worker(1);
  noc_init(1);
  write8(SUBORDINATE_SYNC, SUBORDINATE_UP);
  fence();
  for (;;) {
    WAIT_SLOW(read8(SUBORDINATE_SYNC) == 0x80);
    for (u32 tid = 0; tid < 16; tid++) write32(NOC_BASELINE + 4 * tid, read32(OUTSTANDING(1, tid)));
    u32 pc = read32(KERNEL_PC + 4);
    if (pc) run_kernel(pc, SECOND + 2048, 0);
    noc_drain_all(1);
    fence();
    write8(SUBORDINATE_SYNC, 0);
    fence();
  }
}

#else

static void reset_thread(void) {
  #pragma clang loop unroll(disable)
  for (u32 i = 0; i < THD_CFG_RESET; i++) {
    if (i < 64) write32(REGFILE + 4 * i, 0);
    if (i != THD_CFG_TTSYNC) write32(INSTRN_BUF, SETC16(i));
  }
  TT(SETRWC_ZERO);
  TT(SETADCXY_ZERO);
  TT(SETADCZW_ZERO);
}

NORETURN worker_main(void) {
  configure_csr(1);
  write32(CFG_RISCV_IC_INVALIDATE, 2u << TRISC_ID);
  fence();
  reset_thread();
  tensix_drain();
  write8(SUBORDINATE_SYNC + 1 + TRISC_ID, SUBORDINATE_UP);
  fence();

  u32 last_cache_epoch = 0;
  for (;;) {
    u32 tok;
    do {
      tok = read32(PC_BUF);
      fence();
    } while (tok != read32(STEP_TOKEN));

    u32 ce = read32(DISP_CACHE_EPOCH);
    if (ce != last_cache_epoch) {
      write32(CFG_RISCV_IC_INVALIDATE, 2u << TRISC_ID);
      fence();
      last_cache_epoch = ce;
    }

#if ROLE == ROLE_TRISC0
    // Drain BRISC's shared Tensix reset instructions before TRISC1/2 begin.
    tensix_drain();
    write32(TENSIX_READY, tok);
    fence();
#else
    WAIT_FAST(read32(TENSIX_READY) == tok);
#endif

    u32 pc = read32(KERNEL_PC + 8 + 4 * TRISC_ID);
    if (pc) {
      run_kernel(pc, SECOND + 2048, ROLE == ROLE_TRISC0 ? PC_BUF + 2048 : 0);
      tensix_drain();
      reset_thread();
      tensix_drain();
    }
    fence();
    write32(MAILBOX_TO_BRISC, tok);
  }
}

#endif
