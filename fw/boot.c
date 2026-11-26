#include "noc.h"

#define IS_TRISC                 (ROLE >= ROLE_TRISC0)
#define TRISC_ID                 (ROLE - ROLE_TRISC0)

#define SETC16(reg)              (0xB2000000 | (reg) << 16)
#define STREAM_REG(s, reg)       (OVERLAY_STREAMS + (s) * STREAM_STRIDE + 4 * (reg))

#define SUBORDINATE_HELD         0x40404040u
#define SUBORDINATE_UP           2

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
  TT(CLEARDVALID_RESET);
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
}

#endif
