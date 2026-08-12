#include "cq.h"

#if TT_FW_RISC == 0
#define FIRST_BANK 0u
#define DRAM_STAGING 0x20000u
#else
#define FIRST_BANK 1u
#define DRAM_STAGING 0x30000u
#endif

#define DRAM_COORD(bank) TT_DRAM_##bank

#define PAGE_SIZE 4096u
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

static const u32 dram_coordinates[TT_DRAM_BANKS] = {
  DRAM_COORD(0), DRAM_COORD(1), DRAM_COORD(2), DRAM_COORD(3),
  DRAM_COORD(4), DRAM_COORD(5), DRAM_COORD(6),
#if TT_DRAM_BANKS == 8
  DRAM_COORD(7),
#endif
};

static void copy_pages(void) {
  volatile dma_copy *copy = (volatile dma_copy *)DMA_DESCRIPTOR;
  u32 dram = copy->device_address;
  u32 host_base = copy->host_lo;
  u32 host_mid = copy->host_mid;
  u32 byte_count = copy->byte_count;
  u32 direction = copy->direction;
  u32 banks = TT_DRAM_BANKS;
  u32 page_count = (byte_count + PAGE_SIZE - 1u) / PAGE_SIZE;

  for (u32 bank = FIRST_BANK; bank < banks; bank += 2u) {
    if (bank >= page_count) continue;
    u32 rows = (page_count - bank + banks - 1u) / banks;
    u32 full_rows = rows;
    u32 tail = byte_count % PAGE_SIZE;
    if (tail != 0 && bank == (page_count - 1u) % banks) full_rows--;
    u32 row = 0;
    u32 stride = banks * PAGE_SIZE;
    u32 coordinate = dram_coordinates[bank];

    while (row < full_rows) {
      u32 batch = full_rows - row;
      if (batch > 16u) batch = 16u;
      u32 remote = dram + row * PAGE_SIZE;
      u32 host = host_base + (row * banks + bank) * PAGE_SIZE;

      if (direction != 0) {
        noc_read(
          TT_FW_RISC, remote, 0, coordinate,
          DRAM_STAGING, batch * PAGE_SIZE
        );
        u32 stage = DRAM_STAGING;
        for (u32 remaining = batch; remaining != 0; remaining--) {
          noc_write_start(
            TT_FW_RISC, 1, stage, host, host_mid,
            PCIE_COORD, PAGE_SIZE, 0
          );
          stage += PAGE_SIZE;
          host += stride;
        }
        noc_wait_writes(TT_FW_RISC, 1, 1);
      } else {
        u32 stage = DRAM_STAGING;
        for (u32 remaining = batch; remaining != 0; remaining--) {
          noc_read_start(
            TT_FW_RISC, 1, host, host_mid,
            PCIE_COORD, stage, PAGE_SIZE
          );
          host += stride;
          stage += PAGE_SIZE;
        }
        noc_wait_reads(TT_FW_RISC, 1);
        noc_write(
          TT_FW_RISC, DRAM_STAGING, remote, 0,
          coordinate, batch * PAGE_SIZE, 0
        );
      }
      row += batch;
    }

    if (row != rows) {
      u32 remote = dram + row * PAGE_SIZE;
      u32 host = host_base + (row * banks + bank) * PAGE_SIZE;
      if (direction != 0) {
        noc_read(TT_FW_RISC, remote, 0, coordinate, DRAM_STAGING, tail);
        noc_write(
          TT_FW_RISC, DRAM_STAGING, host, host_mid,
          PCIE_COORD, tail, 0
        );
      } else {
        noc_read(
          TT_FW_RISC, host, host_mid, PCIE_COORD,
          DRAM_STAGING, tail
        );
        noc_write(
          TT_FW_RISC, DRAM_STAGING, remote, 0,
          coordinate, tail, 0
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
    fence();
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
