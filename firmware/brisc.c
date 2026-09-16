#include "fw.h"

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

static void load_param_template(void) {
  u32 template = mmio_read32(GO_SIGNAL & -4u) & 0xffffffu;
  if (!template) return;
  u32 count = mmio_read32(template);
  for (u32 i = 0; i < count; i++) {
    u32 id = mmio_read8(template + L1_PARAM_TEMPLATE_IDS + i);
    u32 value = mmio_read32(id == 0xff ? template + L1_PARAM_TEMPLATE_VALUES + i * 4 : L1_RUNTIME_PARAM_BASE + id * 4);
    mmio_write32(L1_PARAM_BASE + i * 4, value);
  }
  for (u32 i = 0; i < 5; i++) {
    u32 entry = mmio_read32(template + L1_PARAM_TEMPLATE_KERNELS + i * 4);
    if (entry) mmio_write32(L1_WORKER_ENTRY_BASE + i * 4, entry);
  }
}

static __attribute__((noreturn)) void launch_worker(void) {
  wait_u8(GO_SIGNAL, 0x80u);
  load_param_template();
  reset_tensix();
  mmio_write32(0xFFEF02E4u, 0x1Fu);
  /* The Tensix reset, CB counter resets,
   * and the cache invalidate must all be visible before the subordinate
   * release; the release stores must land before this core enters its own
   * kernel.  The baby RISC store path can otherwise let the L1 release
   * bytes overtake the configuration/invalidation stores, and a
   * subordinate can fetch a stale kernel entry word or observe clobbered
   * CB credits. */
  fence();
  for (u32 index = 0; index < 4; index++) {
    mmio_write8(SUBORDINATE_SYNC + index, 0x80u);
  }
  fence();
  run_worker_kernel();
}

__attribute__((noreturn)) void firmware_boot(void) {
  configure_csr();
  mmio_write32(0xFFB12238u, FW_NCRISC + 4);
  mmio_write32(0xFFB12228u, FW_TRISC0 + 4);
  mmio_write32(0xFFB1222Cu, FW_TRISC1 + 4);
  mmio_write32(0xFFB12230u, FW_TRISC2 + 4);
  mmio_write32(0xFFB12234u, 7);
  mmio_write32(0xFFB1223Cu, 1);
  mmio_write32(0xFFB12240u, 0);
  mmio_write32(0xFFB11024u, 0x3Fu);
  enable_clock_gating();
  mmio_write32(L1_WORKER_ENTRY_BASE, WORKER_BRISC);
  mmio_write32(L1_WORKER_ENTRY_BASE + 4, WORKER_NCRISC);
  mmio_write32(L1_WORKER_ENTRY_BASE + 8, WORKER_TRISC0);
  mmio_write32(L1_WORKER_ENTRY_BASE + 12, WORKER_TRISC1);
  mmio_write32(L1_WORKER_ENTRY_BASE + 16, WORKER_TRISC2);
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
