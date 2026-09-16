#include "fw.h"

#if TT_FW_RISC == 0
#define STAGING DRAM_BRISC_STAGING
#define READY DRAM_BRISC_READY
#else
#define STAGING DRAM_NCRISC_STAGING
#define READY DRAM_NCRISC_READY
#endif

static u32 coordinate(u32 bank) {
  return mmio_read32(BOOT_COORDS + TT_FW_RISC * 32 + bank * 4);
}

/* Each engine owns alternating contiguous host blocks. Read the next block
 * while scattering this one; separate transaction IDs keep read completion
 * independent of the preceding DRAM writes. */
static void upload_pages(u32 dram, u32 size, u32 host, u32 middle, u32 count, u32 banks) {
  const u32 capacity = DRAM_UPLOAD_BATCH_SIZE;
  const u32 staging = STAGING;
  u32 limit = capacity / size;
  u32 first = TT_FW_RISC * limit;
  if (first >= count) return;
  u32 batch = count - first;
  if (batch > limit) batch = limit;
  u32 slot = 0;
  noc_read_start(TT_FW_RISC, 1, host + first * size, middle, PCIE_COORD, staging, batch * size);
  for (;;) {
    noc_wait_reads(TT_FW_RISC, 1);
    noc_wait_writes(TT_FW_RISC, 2, 1);
    u32 next = first + 2 * limit;
    u32 following = next < count ? count - next : 0;
    if (following > limit) following = limit;
    if (following) {
      noc_read_start(TT_FW_RISC, 1, host + next * size, middle, PCIE_COORD,
                     staging + (slot ^ 1) * capacity, following * size);
    }
    u32 bank = first % banks, remote = dram + (first / banks) * size;
    u32 local = staging + slot * capacity;
    /* Keep invariant scatter registers programmed across the batch. Only
     * source, destination offset and bank coordinate change for each page. */
    volatile u32 *command = (volatile u32 *)noc_base(TT_FW_RISC);
    while (command[16]) {}
    command[1] = 0;
    command[2] = noc_local_coordinate(TT_FW_RISC);
    command[4] = 0;
    command[6] = 2 << 10;
    command[7] = 0x2092;
    command[8] = size;
    command[9] = 0;
    command[10] = 0;
    command[11] = 0;
    for (u32 i = 0; i < batch; i++) {
      noc_wait_issue(TT_FW_RISC, 0x88, size);
      noc_wait_issue(TT_FW_RISC, 0x48, size);
      while (command[16]) {}
      command[0] = local;
      command[3] = remote;
      command[5] = coordinate(bank);
      fence();
      command[16] = 1;
      fence();
      local += size;
      if (++bank == banks) { bank = 0; remote += size; }
    }
    /* SEND must be accepted before completion counters can be trusted. */
    while (command[16]) {}
    if (!following) break;
    first = next;
    batch = following;
    slot ^= 1;
  }
  noc_wait_writes(TT_FW_RISC, 2, 1);
}

/* Downloads gather contiguous DRAM rows, then scatter to strided host pages. */
static void copy_pages(u32 dram, u32 size, u32 host_base, u32 middle, u32 count, u32 banks, u32 direction) {
  if (!direction) { upload_pages(dram, size, host_base, middle, count, banks); return; }
  for (u32 bank = TT_FW_RISC; bank < banks; bank += 2) {
    if (bank >= count) continue;
    u32 rows = (count - bank + banks - 1) / banks;
    u32 limit = 65536 / size, stride = banks * size;
    for (u32 row = 0; row < rows;) {
      u32 batch = rows - row;
      if (batch > limit) batch = limit;
      u32 remote = dram + row * size;
      u32 host = host_base + (row * banks + bank) * size;
      u32 coord = coordinate(bank);
      noc_read(TT_FW_RISC, remote, 0, coord, STAGING, batch * size);
      for (u32 i = 0; i < batch; i++) {
        noc_write_start(TT_FW_RISC, 1, STAGING + i * size, host, middle, PCIE_COORD, size, 0);
        host += stride;
      }
      noc_wait_writes(TT_FW_RISC, 1, 1);
      row += batch;
    }
  }
}

typedef struct { u32 lo, middle, coord; } endpoint;

static endpoint resolve(u32 slot, u32 offset, u32 *chunk) {
  u32 lo = mmio_read32(slot), hi = mmio_read32(slot + 4);
  u32 previous = lo;
  lo += offset;
  hi += lo < previous;
  if (hi >> 31) {
    u32 within = lo & (DMA_PAGE_SIZE - 1);
    if (*chunk > DMA_PAGE_SIZE - within) *chunk = DMA_PAGE_SIZE - within;
    u32 page = (lo >> 11) | (hi << 21), banks = mmio_read32(BOOT_BANKS);
    return (endpoint){(page / banks) * DMA_PAGE_SIZE + within, 0, coordinate(page % banks)};
  }
  return hi >> 28 ? (endpoint){lo, hi, PCIE_COORD} : (endpoint){lo, 0, hi};
}

static void copy_bytes(u32 slot) {
  u32 size = mmio_read32(slot + 32);
  if (!size) return;
  /* Full stripes between aligned sysmem and DRAM retain the batched path. */
  u32 lo = mmio_read32(slot + 16), hi = mmio_read32(slot + 20);
  u32 host = mmio_read32(slot + 24), middle = mmio_read32(slot + 28);
  u32 direction = 1;
  if (!(hi >> 31)) {
    u32 temp = lo; lo = host; host = temp;
    temp = hi; hi = middle; middle = temp;
    direction = 0;
  }
  u32 banks = mmio_read32(BOOT_BANKS), page = (lo >> 11) | (hi << 21);
  if ((hi >> 31) && (middle >> 28) == 1 && !(size & 2047) && !(lo & 2047) && !(host & 63) && !(page % banks)) {
    copy_pages((page / banks) * DMA_PAGE_SIZE, DMA_PAGE_SIZE, host, middle, size / DMA_PAGE_SIZE, banks, direction);
    return;
  }
  /* Both engines derive identical page-bounded chunks and alternate ownership. */
  for (u32 offset = 0, index = 0; offset < size; index++) {
    u32 chunk = size - offset;
    if (chunk > DMA_PAGE_SIZE) chunk = DMA_PAGE_SIZE;
    endpoint src = resolve(slot + 16, offset, &chunk);
    endpoint dst = resolve(slot + 24, offset, &chunk);
    if ((index & 1) == TT_FW_RISC) {
      u32 source = STAGING + (src.lo & 63);
      noc_read(TT_FW_RISC, src.lo, src.middle, src.coord, source, chunk);
      if ((src.lo & 63) != (dst.lo & 63)) {
        u32 aligned = STAGING + 4096 + (dst.lo & 63);
        for (u32 i = 0; i < chunk; i++) mmio_write8(aligned + i, mmio_read8(source + i));
        source = aligned;
        fence();
      }
      noc_write(TT_FW_RISC, source, dst.lo, dst.middle, dst.coord, chunk, 0);
    }
    offset += chunk;
  }
}

static void publish_signal(u32 slot, u32 op) {
  u32 lo, hi;
  if (op == OP_SIGNAL) {
    lo = mmio_read32(slot + PACKET_SIGNAL_VALUE);
    hi = mmio_read32(slot + PACKET_SIGNAL_VALUE + 4);
  } else {
    do {
      hi = mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_H);
      lo = mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_L);
    } while (hi != mmio_read32(MMIO_RISCV_DEBUG_REG_WALL_CLOCK_H));
  }
  u32 target = mmio_read32(slot + PACKET_SIGNAL_TARGET_LO);
  /* NoC byte lanes must agree, including timeline timestamps at signal + 8. */
  u32 source = STAGING + (target & 63);
  mmio_write32(source, lo);
  mmio_write32(source + 4, hi);
  fence();
  noc_write(0, source, target,
            mmio_read32(slot + PACKET_SIGNAL_TARGET_MID), PCIE_COORD, 8, 0);
}

void firmware_boot(void) {
  u32 read = 0;
  if (TT_FW_RISC) {
    mmio_write32(DRAM_NCRISC_READ, 0);
    /* BRISC clears the previous boot's queue state before either engine polls it. */
    while (mmio_read32(DRAM_BRISC_READY) != 1) fence();
  } else {
    mmio_write32(DRAM_PUBLISHED, 0);
    mmio_write32(DRAM_READ_PUBLISH, 0);
  }
  fence();
  mmio_write32(READY, 1);
  fence();
  for (;;) {
    while (mmio_read32(DRAM_PUBLISHED) == read) fence();
    fence();
    u32 slot = DRAM_QUEUE_BASE + (read & (DRAM_QUEUE_ENTRIES - 1)) * ALIGN;
    u32 op = mmio_read8(slot + PACKET_OP);
    if (op == OP_DRAM_COPY) {
      copy_pages(mmio_read32(slot + PACKET_ADDRESS), mmio_read32(slot + PACKET_DATA_SIZE),
                 mmio_read32(slot + PACKET_COPY_SOURCE_LO), mmio_read32(slot + PACKET_COPY_SOURCE_MID),
                 mmio_read32(slot + PACKET_COPY_TILE_COUNT), mmio_read32(slot + PACKET_COPY_BANKS),
                 mmio_read32(slot + PACKET_COPY_DIRECTION));
    } else if (op == OP_DMA) {
      copy_bytes(slot);
    } else if (op != OP_SIGNAL && op != OP_TIMESTAMP) {
      for (;;) {}
    }
    read++;
    if (TT_FW_RISC) {
      mmio_write32(DRAM_NCRISC_READ, read);
      fence();
      /* Uploads own blocks; downloads own banks. Both engines must finish
       * before a later descriptor can read or overwrite the same tensor. */
      while ((int)(mmio_read32(DRAM_READ_PUBLISH) - read) < 0) fence();
    } else {
      while ((int)(mmio_read32(DRAM_NCRISC_READ) - read) < 0) fence();
      fence();
      if (op == OP_SIGNAL || op == OP_TIMESTAMP) publish_signal(slot, op);
      mmio_write32(DRAM_READ_PUBLISH, read);
      fence();
      noc_write(0, DRAM_READ_PUBLISH, DISPATCH_DRAM_READ, 0, DISPATCH_COORD, 4, 0);
    }
  }
}
