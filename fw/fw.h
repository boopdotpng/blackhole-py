#pragma once

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define TT_INLINE static inline __attribute__((always_inline))
#define TT_STRINGIFY_INNER(value) #value
#define TT_STRINGIFY(value) TT_STRINGIFY_INNER(value)

TT_INLINE void fence(void) {
  __asm__ volatile("fence" ::: "memory");
}

TT_INLINE u32 mmio_read32(u32 address) {
  return *(volatile u32 *)address;
}
TT_INLINE u8 mmio_read8(u32 address) {
  return *(volatile u8 *)address;
}

TT_INLINE void mmio_write32(u32 address, u32 value) {
  *(volatile u32 *)address = value;
}
TT_INLINE void mmio_write8(u32 address, u8 value) {
  *(volatile u8 *)address = value;
}

TT_INLINE void zero_words(u32 address, u32 count) {
  volatile u32 *words = (volatile u32 *)address;
  while (count--) *words++ = 0;
}

TT_INLINE void wait_u8(u32 address, u8 expected) {
  while (mmio_read8(address) != expected) fence();
  fence();
}

TT_INLINE void configure_csr(void) {
  u32 value = 2;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(value) : "memory");
  value = 1u << 18;
  fence();
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(value) : "memory");
  value = 2;
  __asm__ volatile("csrc 0x7c0, %0" :: "r"(value) : "memory");
  fence();
  fence();
  value = 8;
  __asm__ volatile("csrs 0x7c0, %0" :: "r"(value) : "memory");
}

TT_INLINE void push_tensix_word(u32 word) {
  mmio_write32(0xFFE40000u, word);
}

#ifdef TT_WORKER_ENTRY_SLOT
TT_INLINE void run_worker_kernel(void) {
  u32 entry = mmio_read32(TT_WORKER_ENTRY_SLOT);
  __asm__ volatile("jr %0" :: "r"(entry) : "memory");
  __builtin_unreachable();
}
#endif

__asm__(
  ".pushsection .entry,\"ax\",@progbits\n"
  ".balign 4\n"
#ifdef TT_FW_RESIDENT
  ".global _firmware_return\n"
  "_firmware_return:\n"
  "j .Ltt_kernel_return\n"
#endif
  ".global _start\n"
  "_start:\n"
  "li sp, " TT_STRINGIFY(TT_FW_STACK_TOP) "\n"
  "j .Ltt_boot\n"
  ".popsection\n"
  ".pushsection .text,\"ax\",@progbits\n"
  ".balign 4\n"
  ".Ltt_boot:\n"
#ifdef TT_FW_INVALIDATE_ON_BOOT
  "li t0, 0xFFEF02E4\n"
  "li t1, 0x1F\n"
  "sw t1, 0(t0)\n"
  "fence\n"
#endif
#ifdef TT_FW_GLOBAL_POINTER
  "li gp, " TT_STRINGIFY(TT_FW_GLOBAL_POINTER) "\n"
#endif
  "call firmware_boot\n"
  "j .Ltt_hang\n"
#ifdef TT_FW_RESIDENT
  ".Ltt_kernel_return:\n"
  "li sp, " TT_STRINGIFY(TT_FW_STACK_TOP) "\n"
#ifdef TT_FW_GLOBAL_POINTER
  "li gp, " TT_STRINGIFY(TT_FW_GLOBAL_POINTER) "\n"
#endif
  "call firmware_resume_after_kernel\n"
#endif
  ".Ltt_hang:\n"
  "j .Ltt_hang\n"
  ".popsection\n"
);
