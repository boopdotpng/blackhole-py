// Megakernel boot stub for one RISC (-DROLE=hw.ROLES index), or with -DPARK the epilogue that parks it.
// fw.pack_megakernel lays out each launched role as [stub][kernel body][epilogue]: the stub sets up the core, preloads
// the TTRV base registers and jumps to _end, which is where the body starts.
#include "worker.h"

#define TRISC_STACK_TOP          0xFFB00FF0
#define RESET_TRISC0             (1u << 12)
#define TRISC0_RESET_PC          0xFFB12228
#define TRISC_RESET_PC_OVERRIDE  0xFFB12234

#define LOCAL_MEM                0xFFB00000
#define OVERLAY_STREAMS          0xFFB40000
#define STREAM_STRIDE            0x1000
#define REGFILE                  0xFFE00000  // this thread's 64 Tensix GPRs
#define INSTRN_BUF               0xFFE40000  // a store pushes one Tensix instruction
#define PC_BUF                   0xFFE80000
#define COPROCESSOR_DONE_CHECK   (PC_BUF + 4)

#define CFG_ECC_SCRUBBER         (TENSIX_CFG + 3 * 4)
#define CFG_RISC_PREFETCH_CTRL   (TENSIX_CFG + 208 * 4)
#define CFG_BANK_WORDS           224
#define CFG_GLOBAL_BASE          180
#define CFG_STATE_RESET          4

#define ZEROACC_ALL              0x10180000
#define SFPENCC_RESET            0x8A00300A
#define NOP                      0x02000000
#define SFPLOADI_MINUS1          0x7100BF80
#define SFPCONFIG_L11            0x910000B0
#define SEMINIT_ALL              0xA31003FC
#define CLEARDVALID_RESET        0x36000001
#define SETRWC_ZERO              0x3700000F
#define SETADCXY_ZERO            0x51E0000F
#define SETADCZW_ZERO            0x54E0000F
#define SETC16(reg)              (0xB2000000 | (reg) << 16)
#define THD_CFG_TTSYNC           56
#define THD_CFG_RESET            67

#define CB_STREAM0               8
#define CBS                      32
#define CB_PUSHED                8
#define CB_POPPED                10
#define STREAM_REG(s, reg)       (OVERLAY_STREAMS + (s) * STREAM_STRIDE + 4 * (reg))

#define SUBORDINATE_HELD         0x40404040u
#define SUBORDINATE_UP           2

#ifdef PARK

// Body done: trisc waits for its Tensix instructions to retire (PC_BUF: store, load, consume), then everyone spins.
__asm__(".section .entry, \"ax\", @progbits\n"
#if IS_TRISC
        "li t0, " STR(COPROCESSOR_DONE_CHECK) "\n"
        "sw zero, 0(t0)\n"
        "lw t1, 0(t0)\n"
        "andi t1, t1, 0\n"
#endif
        "fence\n"
        "1: j 1b\n");

#else

// TTRV ABI: gp = local memory, tp = this role's NIU (trisc0: Tensix config, trisc1/2: PC_BUF), trisc0 t0 = PC_BUF.
// Each points at the middle of a 4 KiB block so signed 12-bit offsets reach all of it.
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
// Point every command buffer at this core with no pending atomics or broadcast exclusions; kernels set CTRL.
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

// Release every subordinate with a nonzero ROLE_PC and wait until each has reported in.
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

  // logical NoC coords -> worker grid: x skips column 0 and the 8..9 gap, y starts at row 2
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
  // reset_thread(): zero the GPRs and every ThreadConfig word except THD_CFG_TTSYNC
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
#endif
