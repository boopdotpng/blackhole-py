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
TT_INLINE u16 mmio_read16(u32 address) {
  return *(volatile u16 *)address;
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

#define TT_NOC_MAX_PACKET_BYTES (16u * 1024u)

static u32 noc_base(u32 niu) {
  return 0xFFB20000u + niu * 0x10000u;
}

static u32 noc_local_coordinate(u32 niu) {
  return mmio_read32(noc_base(niu) + 0x148u) & 0xFFFu;
}

static void noc_wait_counter(u32 niu, u32 offset, u32 expected) {
  u32 address = noc_base(niu) + 0x200u + offset;
  while (mmio_read32(address) != expected) {}
  fence();
}

static void noc_wait_issue(u32 niu, u32 offset, u32 bytes) {
  u32 address = noc_base(niu) + 0x200u + offset;
  u32 packets = (bytes + TT_NOC_MAX_PACKET_BYTES - 1) /
                TT_NOC_MAX_PACKET_BYTES;
  if (packets >= 128) {
    while (mmio_read32(address) != 0) {}
  } else {
    while (mmio_read32(address) >= 129u) {}
  }
}

static void noc_submit(
  u32 niu,
  u32 source_address, u32 source_middle, u32 source_coordinate,
  u32 target_address, u32 target_middle, u32 target_coordinate,
  u32 tid, u32 options, u32 bytes, u32 immediate
) {
  volatile u32 *command = (volatile u32 *)noc_base(niu);
  while (command[16] != 0) {}
  command[0] = source_address;
  command[1] = source_middle;
  command[2] = source_coordinate;
  command[3] = target_address;
  command[4] = target_middle;
  command[5] = target_coordinate;
  command[6] = tid << 10;
  command[7] = options;
  command[8] = bytes;
  command[9] = 0;
  command[10] = immediate;
  command[11] = 0;
  command[12] = 0;
  command[13] = 0;
  command[14] = 0;
  command[16] = 1;
  while (command[16] != 0) {}
}

static void noc_read_start(
  u32 niu, u32 tid, u32 source_address, u32 source_middle,
  u32 source_coordinate, u32 target_address, u32 bytes
) {
  noc_wait_issue(niu, 0x40u + tid * 4u, bytes);
  noc_submit(
    niu,
    source_address, source_middle, source_coordinate,
    target_address, 0, noc_local_coordinate(niu),
    tid, 0x2090u, bytes, 0
  );
}

static void noc_write_start(
  u32 niu, u32 tid, u32 source_address, u32 target_address,
  u32 target_middle, u32 target_coordinate, u32 bytes, u32 posted
) {
  noc_wait_issue(niu, 0x80u + tid * 4u, bytes);
  if (!posted) noc_wait_issue(niu, 0x40u + tid * 4u, bytes);
  noc_submit(
    niu,
    source_address, 0, noc_local_coordinate(niu),
    target_address, target_middle, target_coordinate,
    tid, posted ? 0x2082u : 0x2092u, bytes, 0
  );
}

static void noc_wait_reads(u32 niu, u32 tid) {
  noc_wait_counter(niu, 0x40u + tid * 4u, 0);
}

static void noc_wait_writes(u32 niu, u32 tid, u32 wait_remote) {
  noc_wait_counter(niu, 0x80u + tid * 4u, 0);
  if (wait_remote) noc_wait_reads(niu, tid);
}

static void noc_read(
  u32 niu, u32 source_address, u32 source_middle,
  u32 source_coordinate, u32 target_address, u32 bytes
) {
  noc_read_start(
    niu, 1, source_address, source_middle, source_coordinate,
    target_address, bytes
  );
  noc_wait_reads(niu, 1);
}

static void noc_write(
  u32 niu, u32 source_address, u32 target_address,
  u32 target_middle, u32 target_coordinate, u32 bytes, u32 posted
) {
  noc_write_start(
    niu, 1, source_address, target_address, target_middle,
    target_coordinate, bytes, posted
  );
  noc_wait_writes(niu, 1, !posted);
}

static void noc_multicast_write(
  u32 niu, u32 source_address, u32 target_address,
  u32 target_start, u32 target_end, u32 bytes
) {
  noc_wait_issue(niu, 0x84u, bytes);
  u32 rectangle = niu == 0
    ? target_end | (target_start << 12)
    : target_start | (target_end << 12);
  noc_submit(
    niu,
    source_address, 0, noc_local_coordinate(niu),
    target_address, 0, rectangle,
    1, 0x80A2u, bytes, 0
  );
  noc_wait_counter(niu, 0x84u, 0);
}

static void noc_atomic_inc(
  u32 niu, u32 target_address, u32 target_coordinate, u32 value
) {
  noc_wait_counter(niu, 0x84u, 0);
  noc_wait_counter(niu, 0x44u, 0);
  noc_wait_issue(niu, 0x44u, 1);
  noc_submit(
    niu,
    target_address, 0, target_coordinate,
    4, 0, noc_local_coordinate(niu),
    1, 0x2091u, 0x107Cu, value
  );
  noc_wait_counter(niu, 0x44u, 0);
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
