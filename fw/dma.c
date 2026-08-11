#include "fw.h"

#if TT_FW_RISC == 0
#define FIRST_BANK 0u
#define DRAM_STAGING 0x20000u
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
#else
#define FIRST_BANK 1u
#define DRAM_STAGING 0x30000u
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
#endif

#define CQ_STATE 0x1000u
#define DMA_SUBMIT CQ_STATE
#define DMA_COMPLETE (CQ_STATE + 4u)
#define DMA_BRISC_DONE (CQ_STATE + 8u)
#define DMA_NCRISC_DONE (CQ_STATE + 0x0Cu)
#define DMA_BRISC_READY (CQ_STATE + 0x10u)
#define DMA_NCRISC_READY (CQ_STATE + 0x14u)
#define DMA_DESCRIPTOR (CQ_STATE + 0x40u)
#define PCIE_COORD ((1u << 24) | (24u << 6) | 19u)
#define NCRISC_RESET_PC 0xFFB12238u
#define NCRISC_RESET_PC_OVERRIDE 0xFFB1223Cu
#define SOFT_RESET 0xFFB121B0u

#define COPY_DEVICE_ADDRESS 0u
#define COPY_HOST_LO 4u
#define COPY_HOST_MID 8u
#define COPY_BYTE_COUNT 12u
#define COPY_PAGE_SIZE 16u
#define COPY_BANKS 20u
#define COPY_DIRECTION 24u
#define COPY_BANK_START 28u

static const u32 coordinates[TT_DRAM_BANKS] = {
  COORD_0, COORD_1, COORD_2, COORD_3,
  COORD_4, COORD_5, COORD_6,
#if TT_DRAM_BANKS > 7
  COORD_7,
#endif
};

static void copy_pages(void) {
  u32 dram = mmio_read32(DMA_DESCRIPTOR + COPY_DEVICE_ADDRESS);
  u32 source = mmio_read32(DMA_DESCRIPTOR + COPY_HOST_LO);
  u32 middle = mmio_read32(DMA_DESCRIPTOR + COPY_HOST_MID);
  u32 byte_count = mmio_read32(DMA_DESCRIPTOR + COPY_BYTE_COUNT);
  u32 page_size = mmio_read32(DMA_DESCRIPTOR + COPY_PAGE_SIZE);
  u32 banks = mmio_read32(DMA_DESCRIPTOR + COPY_BANKS);
  u32 direction = mmio_read32(DMA_DESCRIPTOR + COPY_DIRECTION);
  u32 bank_start = mmio_read32(DMA_DESCRIPTOR + COPY_BANK_START);
  u32 page_count = (byte_count + page_size - 1u) / page_size;

  u32 bank = FIRST_BANK;
  if (bank < bank_start) {
    bank = bank_start;
    if ((bank & 1u) != FIRST_BANK) bank++;
  }
  for (; bank - bank_start < banks; bank += 2) {
    u32 local_bank = bank - bank_start;
    if (local_bank >= page_count) continue;
    u32 rows = (page_count - local_bank + banks - 1) / banks;
    u32 full_rows = rows;
    u32 tail = byte_count % page_size;
    if (tail != 0 && local_bank == (page_count - 1u) % banks) full_rows--;
    u32 row = 0;
    u32 limit = (64u * 1024u) / page_size;
    u32 stride = banks * page_size;
    while (row < full_rows) {
      u32 batch = full_rows - row;
      if (batch > limit) batch = limit;
      u32 remote = dram + row * page_size;
      u32 host = source + (row * banks + local_bank) * page_size;

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

    if (row != rows) {
      u32 remote = dram + row * page_size;
      u32 host = source + (row * banks + local_bank) * page_size;
      if (direction != 0) {
        noc_read(
          TT_FW_RISC, remote, 0, coordinates[bank],
          DRAM_STAGING, tail
        );
        noc_write(
          TT_FW_RISC, DRAM_STAGING, host, middle,
          PCIE_COORD, tail, 0
        );
      } else {
        noc_read(
          TT_FW_RISC, host, middle, PCIE_COORD,
          DRAM_STAGING, tail
        );
        noc_write(
          TT_FW_RISC, DRAM_STAGING, remote, 0,
          coordinates[bank], tail, 0
        );
      }
    }
  }
}

void firmware_boot(void) {
  u32 read = 0;
  if (TT_FW_RISC == 0) {
    mmio_write32(DMA_SUBMIT, 0);
    mmio_write32(DMA_COMPLETE, 0);
    mmio_write32(DMA_BRISC_DONE, 0);
    mmio_write32(DMA_NCRISC_DONE, 0);
    mmio_write32(NCRISC_RESET_PC, 0xA000u);
    mmio_write32(NCRISC_RESET_PC_OVERRIDE, 1);
    mmio_write32(SOFT_RESET, 0);
  }
  mmio_write32(
    TT_FW_RISC == 0 ? DMA_BRISC_READY : DMA_NCRISC_READY, 1
  );
  fence();

  for (;;) {
    while (mmio_read32(DMA_SUBMIT) == read) fence();
    u32 next = mmio_read32(DMA_SUBMIT);
    copy_pages();
    fence();
    if (TT_FW_RISC == 1) {
      read = next;
      mmio_write32(DMA_NCRISC_DONE, read);
      fence();
      continue;
    }

    mmio_write32(DMA_BRISC_DONE, next);
    fence();
    while (mmio_read32(DMA_NCRISC_DONE) < next) fence();
    read = next;
    mmio_write32(DMA_COMPLETE, read);
    fence();
  }
}
