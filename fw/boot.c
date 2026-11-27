#include "noc.h"

#define IS_TRISC                 (ROLE >= ROLE_TRISC0)
#define TRISC_ID                 (ROLE - ROLE_TRISC0)

#define SETC16(reg)              (0xB2000000 | (reg) << 16)
#define STREAM_REG(s, reg)       (OVERLAY_STREAMS + (s) * STREAM_STRIDE + 4 * (reg))

#define SUBORDINATE_HELD         0x40404040u
#define SUBORDINATE_UP           2

#if ROLE == ROLE_BRISC

// RV32 ABI: a0=NIU, a1/a2=flat pointer lo/hi, a3=byte offset,
// a4=bytes, a5=local L1 address, a6=transaction id. Callers preserve
// live caller-saved registers and ra across these normal C functions.
void kernel_noc_wait(u32 niu, u32 tid, u32 acked);
void kernel_noc_read(u32 niu, u32 lo, u32 hi, u32 off, u32 size, u32 local, u32 tid) {
  // Blackhole DRAM reads require source and destination congruent modulo 64.
  // Packed 16x16 faces are 144/272 bytes, so their source alignment changes
  // from face to face. Keep the fast asynchronous path for congruent reads.
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
    // Bound simultaneous DRAM responses as the number of readers grows.
    // Counters can retain a baseline across worker resets; pace relative to
    // the same baseline used by kernel_noc_wait.
    u32 workers = read32(NUM_WORKERS), cap = workers >= 88 ? 2 : workers >= 42 ? 8 : 0;
    noc_move_paced_base(niu, 0, lo, hi, off, size, local, tid, cap, read32(NOC_BASELINE + 4 * tid));
  }
}
void kernel_noc_write(u32 niu, u32 lo, u32 hi, u32 off, u32 size, u32 local, u32 tid) {
  // NoC writes require source/destination congruence within a 16-byte word.
  // Indexed stores can target a different column than their staging slot.
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
        "call boot\n"
        "li gp, " STR(LOCAL_MEM + 2048) "\n"
        "li tp, " STR(SECOND + 2048) "\n"
#if ROLE == ROLE_TRISC0
        "li t0, " STR(PC_BUF + 2048) "\n"
#endif
        "j _end\n");

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
#endif

#if ROLE != ROLE_BRISC
static void signal_up_and_wait_go(void) {
  *(volatile u8 *)(SUBORDINATE_SYNC + ROLE - ROLE_NCRISC) = SUBORDINATE_UP;
  fence();
  WAIT_FAST(read32(GO_FLAG));
}
#endif

#if ROLE == ROLE_BRISC

static void reset_tensix(void) {
  write32(TENSIX_CFG + CFG_STATE_RESET * 4, 0);
  write32(TENSIX_CFG + (CFG_BANK_WORDS + CFG_STATE_RESET) * 4, 0);
  // the global config words, minus 185 (CFG_RISCV_IC_INVALIDATE) and 186
  for (u32 i = CFG_GLOBAL_BASE; i < 185; i++) write32(TENSIX_CFG + 4 * i, 0);
  for (u32 i = 187; i < CFG_BANK_WORDS; i++) write32(TENSIX_CFG + 4 * i, 0);
  TT(ZEROACC_ALL);
  // Do not reset Src bank ownership with CLEARDVALID(reset=1): Blackhole
  // documents that mode as unsafe and prone to nondeterministic hangs.
  // The host resets SrcA/SrcB ownership with SOFT_RESET while RISCs are held.
  TT(SFPENCC_RESET);
  TT(NOP);
  TT(SFPLOADI_MINUS1);
  TT(SFPCONFIG_L11);
  write32(CFG_ECC_SCRUBBER, 0x803);
  TT(SEMINIT_ALL);
}

static void boot_subordinates(void) {
  u32 reset = RESET_ALL & ~RESET_BRISC, expect = SUBORDINATE_HELD, trisc_override = 0, pc;
  write32(GO_FLAG, 0);
  write32(SUBORDINATE_SYNC, SUBORDINATE_HELD);
  if ((pc = read32(ROLE_PC))) {
    write32(NCRISC_RESET_PC, pc);
    write32(NCRISC_RESET_PC_OVERRIDE, 1);
    reset &= ~RESET_NCRISC;
    expect ^= 0x40 ^ SUBORDINATE_UP;
  }
  for (u32 i = 0; i < 3; i++) {
    if (!(pc = read32(ROLE_PC + 4 + 4 * i))) continue;
    write32(TRISC0_RESET_PC + 4 * i, pc);
    trisc_override |= 1u << i;
    reset &= ~(RESET_TRISC0 << i);
    expect ^= (0x40u ^ SUBORDINATE_UP) << 8 * (i + 1);
  }
  if (trisc_override) write32(TRISC_RESET_PC_OVERRIDE, trisc_override);
  if (expect == SUBORDINATE_HELD) return;
  fence();
  write32(SOFT_RESET, reset);
  WAIT_FAST(read32(SUBORDINATE_SYNC) == expect);
}

void boot(void) {
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
  for (u32 at = MCAST_CTRL_BASE; at < MCAST_CTRL_BASE + 0x400; at += 4) write32(at, 0);
  boot_subordinates();
  reset_tensix();
  for (u32 s = CB_STREAM0; s < CB_STREAM0 + CBS; s++) {
    write32(STREAM_REG(s, CB_PUSHED), 0);
    write32(STREAM_REG(s, CB_POPPED), 0);
  }
  write32(CFG_RISC_PREFETCH_CTRL, 0x11F);
  fence();
  write32(GO_FLAG, 1);
  fence();
}

#elif ROLE == ROLE_NCRISC

void boot(void) {
  configure_csr(0);
  noc_init_worker(1);
  noc_init(1);
  signal_up_and_wait_go();
}

#else

void boot(void) {
  configure_csr(1);
  write32(CFG_RISCV_IC_INVALIDATE, 2u << TRISC_ID);
  fence();
  for (u32 i = 0; i < THD_CFG_RESET; i++) {
    if (i < 64) write32(REGFILE + 4 * i, 0);
    if (i != THD_CFG_TTSYNC) write32(INSTRN_BUF, SETC16(i));
  }
  TT(SETRWC_ZERO);
  TT(SETADCXY_ZERO);
  TT(SETADCZW_ZERO);
  signal_up_and_wait_go();
#if ROLE == ROLE_TRISC0
  // BRISC's shared initialization is queued on Tensix thread 0. GO only
  // orders its submission; other threads must not consume stale semaphore
  // credits or SFPU state from the previous kernel before it finishes.
  write32(COPROCESSOR_DONE_CHECK, 0);
  u32 done = read32(COPROCESSOR_DONE_CHECK);
  __asm__ volatile("andi %0, %0, 0" : "+r"(done) :: "memory");
  write32(TENSIX_READY, 1);
  fence();
#else
  if (read32(ROLE_PC + 4)) WAIT_FAST(read32(TENSIX_READY));
#endif
}

#endif
