/* Resident worker firmware, from blackhole-py firmware/{brisc,ncrisc,trisc}.c. BRISC releases the other four, then on
 * every GO resets Tensix and starts all five at their fixed KERNEL_* slots (TT_KERNEL). Each kernel jumps back to its FW_*_RETURN;
 * when all have, BRISC tells dispatch. TT_WORKER_INDEX: 0 brisc, 1 ncrisc, 2-4 trisc0-2. */
#include "fw.h"

#if TT_WORKER_INDEX == 0
static void enable_clock_gating(void) {
  for (u32 noc = 0; noc < 2; noc++) {
    u32 config = 0xFFB20100u + noc * 0x10000u;
    mmio_write32(config, mmio_read32(config) | 1u);
    mmio_write32(config + 4, mmio_read32(config + 4) | 1u);
  }
}

static void reset_cb_counters(void) {
  for (u32 index = 0; index < 32; index++) {
    u32 base = 0xFFB48020u + index * 0x1000u;
    mmio_write32(base, 0);
    mmio_write32(base + 8, 0);
  }
}

static void reset_tensix(void) {
  zero_words(0xFFEF0000u, 186);
  zero_words(0xFFEF02ECu, 69);
  push_tensix_word(0x10180000u);
  push_tensix_word(0x8A00300Au);
  push_tensix_word(0x02000000u);
  push_tensix_word(0x7100BF80u);
  push_tensix_word(0x910000B0u);
  mmio_write32(0xFFEF000Cu, 0x803u);
  push_tensix_word(0xA3100004u);
  push_tensix_word(0xA3100008u);
  push_tensix_word(0xA3100010u);
  push_tensix_word(0xA3100200u);
  reset_cb_counters();
  mmio_write32(MMIO_CFG_BASE + 208 * 4, 0x11f);
}

static void notify_dispatch(void) {
  noc_atomic_inc(1, DISPATCH_DONE_COUNT, DISPATCH_COORD, 1);
}

static __attribute__((noreturn)) void launch_worker(void) {
  wait_u8(GO_SIGNAL, 0x80u);
  reset_tensix();
  mmio_write32(0xFFEF02E4u, 0x1Fu);
  /* The Tensix reset, CB counter resets,
   * and the cache invalidate must all be visible before the subordinate
   * release; the release stores must land before this core enters its own
   * kernel.  The baby RISC store path can otherwise let the L1 release
   * bytes overtake the configuration/invalidation stores, and a
   * subordinate can fetch a stale kernel or observe clobbered
   * CB credits. */
  fence();
  for (u32 index = 0; index < 4; index++) {
    mmio_write8(SUBORDINATE_SYNC + index, 0x80u);
  }
  fence();
  JUMP(TT_KERNEL);
}

__attribute__((noreturn)) void firmware_boot(void) {
  configure_csr();
  mmio_write32(0xFFB12238u, FW_NCRISC);
  mmio_write32(0xFFB12228u, FW_TRISC0);
  mmio_write32(0xFFB1222Cu, FW_TRISC1);
  mmio_write32(0xFFB12230u, FW_TRISC2);
  mmio_write32(0xFFB12234u, 7);
  mmio_write32(0xFFB1223Cu, 1);
  mmio_write32(0xFFB12240u, 0);
  mmio_write32(0xFFB11024u, 0x3Fu);
  enable_clock_gating();
  zero_words(L1_MEM_ZEROS_BASE, L1_MEM_ZEROS_SIZE / 4);
  mmio_write32(0xFFEF02E4u, 0x1Fu);
  reset_tensix();
  mmio_write32(0x60u, 0);
  mmio_write32(0xFFEF02E4u, 0x1Fu);
  fence();
  /* The sync-word init must be visible before the subordinates are
   * released from soft reset; a delayed L1 store could otherwise land
   * after their BOOT_READY bytes and hide them from the wait below. */
  mmio_write32(SUBORDINATE_SYNC, 0x40404040u);
  fence();
  mmio_write32(0xFFB121B0u, 0);
  for (u32 index = 0; index < 4; index++) {
    wait_u8(SUBORDINATE_SYNC + index, 2);
  }
  launch_worker();
}

__attribute__((noreturn)) void firmware_resume_after_kernel(void) {
  for (u32 index = 0; index < 4; index++) {
    wait_u8(SUBORDINATE_SYNC + index, 0);
  }
  mmio_write8(GO_SIGNAL, 0);
  fence();
  notify_dispatch();
  launch_worker();
}

#elif TT_WORKER_INDEX == 1
#define SYNC SUBORDINATE_SYNC

static __attribute__((noreturn)) void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
  JUMP(TT_KERNEL);
}

__attribute__((noreturn)) void firmware_boot(void) {
  configure_csr();
  mmio_write8(SYNC, 2);
  fence();
  launch_worker();
}

__attribute__((noreturn)) void firmware_resume_after_kernel(void) {
  mmio_write8(SYNC, 0);
  fence();
  launch_worker();
}

#else
#define SYNC (SUBORDINATE_SYNC + 1 + TT_TRISC_ID)

TT_INLINE void initialize_tensix(void) {
  zero_words(0xFFE00000u, 64);
}

static void delay_600_cycles(void) {
  u32 remaining = 600;
  __asm__ volatile(
    "1: addi %0, %0, -1\n"
    "bnez %0, 1b\n"
    : "+r"(remaining)
  );
}

static __attribute__((noreturn)) void launch_worker(void) {
  wait_u8(SYNC, 0x80u);
  initialize_tensix();
  JUMP(TT_KERNEL);
}

__attribute__((noreturn)) void firmware_boot(void) {
  configure_csr();
  /* The register file is initialized immediately before every kernel launch. */
  mmio_write32(0xFFEF02E8u, 0);
  delay_600_cycles();
  mmio_write8(SYNC, 2);
  fence();
  launch_worker();
}

__attribute__((noreturn)) void firmware_resume_after_kernel(void) {
  mmio_write8(SYNC, 0);
  fence();
  launch_worker();
}

#endif

/* FW_X + 0 boots, FW_X + 4 is where kernels return to. Both reset the stack (and gp on TRISC), which a kernel may have
 * left anywhere. */
#define STR_(x) #x
#define STR(x) STR_(x)
#ifdef TT_FW_GLOBAL_POINTER
#define SET_SP_GP "li sp, " STR(TT_FW_STACK_TOP) "\n li gp, " STR(TT_FW_GLOBAL_POINTER) "\n"
#else
#define SET_SP_GP "li sp, " STR(TT_FW_STACK_TOP) "\n"
#endif
__asm__(".section .entry, \"ax\", @progbits\n"
        "j 1f\n"
        SET_SP_GP "j firmware_resume_after_kernel\n"
        "1: " SET_SP_GP "j firmware_boot\n");
