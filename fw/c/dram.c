#include "fw.h"
#define breadcrumb(stage, a, b, c, d) \
  breadcrumb_at(TT_BREADCRUMB_BASE + TT_FW_RISC * 0x20u, stage, a, b, c, d)

#ifndef TT_FW_RISC
#error "compile dram.c with -DTT_FW_RISC=0 or -DTT_FW_RISC=1"
#elif TT_FW_RISC == 0
#define FIRST_BANK 0u
#define DRAM_STAGING 0x20000u
#define DRAM_READY (CQ_STATE + 8u)
#define COORD_0 (TT_DRAM_0_0_X | (TT_DRAM_0_0_Y << 6))
#define COORD_1 (TT_DRAM_1_0_X | (TT_DRAM_1_0_Y << 6))
#define COORD_2 (TT_DRAM_2_0_X | (TT_DRAM_2_0_Y << 6))
#define COORD_3 (TT_DRAM_3_0_X | (TT_DRAM_3_0_Y << 6))
#define COORD_4 (TT_DRAM_4_0_X | (TT_DRAM_4_0_Y << 6))
#define COORD_5 (TT_DRAM_5_0_X | (TT_DRAM_5_0_Y << 6))
#define COORD_6 (TT_DRAM_6_0_X | (TT_DRAM_6_0_Y << 6))
#if TT_DRAM_BANKS > 7
#define COORD_7 (TT_DRAM_7_0_X | (TT_DRAM_7_0_Y << 6))
#endif
#elif TT_FW_RISC == 1
#define FIRST_BANK 1u
#define DRAM_STAGING 0x30000u
#define DRAM_READY (CQ_STATE + 0x0Cu)
#define COORD_0 (TT_DRAM_0_1_X | (TT_DRAM_0_1_Y << 6))
#define COORD_1 (TT_DRAM_1_1_X | (TT_DRAM_1_1_Y << 6))
#define COORD_2 (TT_DRAM_2_1_X | (TT_DRAM_2_1_Y << 6))
#define COORD_3 (TT_DRAM_3_1_X | (TT_DRAM_3_1_Y << 6))
#define COORD_4 (TT_DRAM_4_1_X | (TT_DRAM_4_1_Y << 6))
#define COORD_5 (TT_DRAM_5_1_X | (TT_DRAM_5_1_Y << 6))
#define COORD_6 (TT_DRAM_6_1_X | (TT_DRAM_6_1_Y << 6))
#if TT_DRAM_BANKS > 7
#define COORD_7 (TT_DRAM_7_1_X | (TT_DRAM_7_1_Y << 6))
#endif
#else
#error "TT_FW_RISC must select BRISC (0) or NCRISC (1)"
#endif

#define ALIGN 64u
#define CQ_STATE 0x1000u
#define DRAM_PUBLISHED CQ_STATE
#define DRAM_NCRISC_READ (CQ_STATE + 4u)
#define DRAM_READ_PUBLISH (CQ_STATE + 0x60u)
#define DRAM_QUEUE_BASE 0x2000u
#define DRAM_QUEUE_ENTRIES 32u
#define DISPATCH_DRAM_READ 0x160090u
#define DISPATCH_SIGNAL 0x160070u
#define DISPATCH_COORD ((3u << 6) | 14u)
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define WALL_CLOCK_LO 0xFFB121F0u
#define BC_BASE (0x300u + TT_FW_RISC * 0x100u)
#define WALL_CLOCK_HI 0xFFB121F8u
#define NCRISC_RESET_PC 0xFFB12238u
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223Cu
#define SOFT_RESET 0xFFB121B0u

#define PACKET_OP 0u
#define PACKET_ADDRESS 8u
#define PACKET_DATA_SIZE 12u
#define COPY_SOURCE_LO 16u
#define COPY_SOURCE_MID 20u
#define COPY_PAGE_COUNT 24u
#define COPY_BANKS 28u
#define COPY_DIRECTION 32u
#define COPY_BANK_START 36u
#define SIGNAL_TARGET_LO 8u
#define SIGNAL_TARGET_MID 12u
#define SIGNAL_VALUE 16u

enum {
  OP_SIGNAL = 5,
  OP_DRAM_COPY = 7,
};

static const u32 coordinates[TT_DRAM_BANKS] = {
  COORD_0, COORD_1, COORD_2, COORD_3,
  COORD_4, COORD_5, COORD_6,
#if TT_DRAM_BANKS > 7
  COORD_7,
#endif
};

static void copy_pages(u32 slot) {
  u32 dram = mmio_read32(slot + PACKET_ADDRESS);
  u32 page_size = mmio_read32(slot + PACKET_DATA_SIZE);
  u32 source = mmio_read32(slot + COPY_SOURCE_LO);
  u32 middle = mmio_read32(slot + COPY_SOURCE_MID);
  u32 page_count = mmio_read32(slot + COPY_PAGE_COUNT);
  u32 banks = mmio_read32(slot + COPY_BANKS);
  u32 direction = mmio_read32(slot + COPY_DIRECTION);
  u32 bank_start = mmio_read32(slot + COPY_BANK_START);
  breadcrumb(BC_BASE + 3, page_size, page_count, banks,
             direction | (bank_start << 8));

  u32 bank = FIRST_BANK;
  if (bank < bank_start) {
    bank = bank_start;
    if ((bank & 1u) != FIRST_BANK) bank++;
  }
  for (; bank - bank_start < banks; bank += 2) {
    u32 local_bank = bank - bank_start;
    if (local_bank >= page_count) continue;
    u32 rows = (page_count - local_bank + banks - 1) / banks;
    u32 row = 0;
    u32 limit = (64u * 1024u) / page_size;
    u32 stride = banks * page_size;
    breadcrumb(BC_BASE + 4, bank, local_bank, rows, coordinates[bank]);
    while (row < rows) {
      u32 batch = rows - row;
      if (batch > limit) batch = limit;
      u32 remote = dram + row * page_size;
      u32 host = source + (row * banks + local_bank) * page_size;

      breadcrumb(BC_BASE + 5 + (direction == 0), row, batch, remote, host);
      if (direction != 0) {
        u32 bytes = batch * page_size;
        noc_read(
          TT_FW_RISC, remote, 0, coordinates[bank],
          DRAM_STAGING, bytes
        );
        u32 stage = DRAM_STAGING;
        for (u32 remaining = batch; remaining != 0; remaining--) {
          noc_write_start(
            TT_FW_RISC, 1, stage, host, middle,
            PCIE_COORD, page_size, 0
          );
          stage += page_size;
          host += stride;
        }
        noc_wait_writes(TT_FW_RISC, 1, 1);
      } else {
        u32 stage = DRAM_STAGING;
        for (u32 remaining = batch; remaining != 0; remaining--) {
          noc_read_start(
            TT_FW_RISC, 1, host, middle,
            PCIE_COORD, stage, page_size
          );
          host += stride;
          stage += page_size;
        }
        noc_wait_reads(TT_FW_RISC, 1);
        noc_write(
          TT_FW_RISC, DRAM_STAGING, remote, 0,
          coordinates[bank], batch * page_size, 0
        );
      }
      row += batch;
    }
  }
}

static void publish_signal(u32 slot) {
  u32 target = mmio_read32(slot + SIGNAL_TARGET_LO);
  u32 middle = mmio_read32(slot + SIGNAL_TARGET_MID);
  mmio_write32(DISPATCH_SIGNAL, mmio_read32(slot + SIGNAL_VALUE));
  mmio_write32(DISPATCH_SIGNAL + 4, mmio_read32(slot + SIGNAL_VALUE + 4));
  mmio_write32(DISPATCH_SIGNAL + 8, mmio_read32(WALL_CLOCK_LO));
  mmio_write32(DISPATCH_SIGNAL + 12, mmio_read32(WALL_CLOCK_HI));
  fence();
  breadcrumb(BC_BASE + 9, target, middle,
             mmio_read32(slot + SIGNAL_VALUE), 0);
  noc_write(
    0, DISPATCH_SIGNAL, target, middle,
    PCIE_COORD, 16, 0
  );
}

void firmware_boot(void) {
  u32 read = 0;
  if (TT_FW_RISC == 0) {
    mmio_write32(DRAM_PUBLISHED, 0);
    mmio_write32(DRAM_READ_PUBLISH, 0);
    mmio_write32(NCRISC_RESET_PC, 0xA000u);
    mmio_write32(NCRISC_RESET_PC_OVERRIDE, 1);
    mmio_write32(SOFT_RESET, 0);
  } else {
    mmio_write32(DRAM_NCRISC_READ, 0);
  }
  mmio_write32(DRAM_READY, 1);
  fence();
  breadcrumb(BC_BASE, read, TT_DRAM_BANKS, FIRST_BANK, DRAM_STAGING);

  for (;;) {
    breadcrumb(
      BC_BASE + 1, read, mmio_read32(DRAM_PUBLISHED),
      mmio_read32(DRAM_NCRISC_READ), mmio_read32(DRAM_READ_PUBLISH)
    );
    while (mmio_read32(DRAM_PUBLISHED) == read) fence();
    u32 slot = DRAM_QUEUE_BASE +
               (read & (DRAM_QUEUE_ENTRIES - 1)) * ALIGN;
    u8 op = mmio_read8(slot + PACKET_OP);
    breadcrumb(BC_BASE + 2, op, slot, read, mmio_read32(DRAM_PUBLISHED));
    if (op == OP_DRAM_COPY) {
      copy_pages(slot);
    } else if (op != OP_SIGNAL) {
      breadcrumb(BC_BASE + 0xFFu, op, slot, read, 0);
      for (;;) {}
    }

    u32 next = read + 1;
    if (TT_FW_RISC == 1) {
      read = next;
      mmio_write32(DRAM_NCRISC_READ, read);
      fence();
      continue;
    }

    breadcrumb(
      BC_BASE + 7, next, mmio_read32(DRAM_NCRISC_READ), op, slot
    );
    while (mmio_read32(DRAM_NCRISC_READ) < next) fence();
    if (op == OP_SIGNAL) publish_signal(slot);
    read = next;
    breadcrumb(BC_BASE + 8, next, op, slot, 0);
    mmio_write32(DRAM_READ_PUBLISH, read);
    fence();
    noc_write(
      0, DRAM_READ_PUBLISH, DISPATCH_DRAM_READ,
      0, DISPATCH_COORD, 4, 0
    );
  }
}
