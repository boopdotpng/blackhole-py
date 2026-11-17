"""Blackhole facts the compiler needs: MMIO addresses, the config field map (name -> space, word, shift, width,
owning engine; generated, see docs/ttrv_cfg.md), the state firmware leaves at launch (spec §12), and the base
register table (spec §5).

A RISC's address space (from fw/abi.h, fw/hw.h, fw/noc.c):
  0x00000000-0x0017FFFF  L1, 1.5 MiB, shared by the core's five RISCs, the Tensix engines and the NoC
  0xFFB00000             this RISC's private local memory: 8 KiB on BRISC/NCRISC, 4 KiB on TRISCs. Firmware keeps its
                         stack at the top (0xFFB01FF0 / 0xFFB00FF0) and TRISC gp data at 0xFFB007F0
  0xFFB1xxxx             tile control: soft reset, wall clock, reset PCs
  0xFFB20000 + niu<<16   NoC interface (niu 0 = BRISC's NoC0, 1 = NCRISC's NoC1). Command buffer n at +n*0x800,
                         node id at +0x148, per-transaction counters at +0x240 / +0x280
  0xFFB40000 + s<<12     stream registers
  0xFFE00000             this TRISC's Tensix GPRs
  0xFFE40000             instruction buffer: a store pushes one Tensix instruction (runtime-built words only)
  0xFFE80004             PC_BUF_SYNC: a load returns once this thread's Tensix work is done (tensix.wait)
  0xFFEF0000             Tensix config, shared by the three TRISCs

Base registers (x3, x4, x5), each at block + 0x800 so it reaches the block's first 4 KiB:
  all RISCs  x3 = 0xFFB00800  private RAM: CB cursors (all of a TRISC's 4 KiB)
  BRISC      x4 = 0xFFB20800  NoC0: command buffers 0-1, node id, transaction counters
  NCRISC     x4 = 0xFFB30800  NoC1: same
  TRISC0     x4 = 0xFFEF0800  config: per-tile unpack base address stores (every config word the language uses)
             x5 = 0xFFE80800  PC buffer: tensix.wait, unpack config sync
  TRISC1/2   x4 = 0xFFE80800  PC buffer: tensix.wait, MOP sync
No base: the instruction buffer (rare runtime words) and the CB stream counters (4 KiB apart, one per CB). Without a
base a constant address costs one lui; its low 12 bits go in the access's offset. Revisit the table against listings."""
