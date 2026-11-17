"""Whole-program resource assignment, done once before codegen. Deterministic, declaration order, no reuse.

- l1/cb storage from fw.DATA_BASE, 64-byte aligned unless align=; overlap and overflow are errors.
- CB cursors: 8 bytes per CB end in the owning RISC's private RAM (0xFFB00000), below firmware's stack and data.
  Shared counters are stream 8 + cb, registers 8 and 10.
- param slots (one word per DRAM buffer, two per u64 host address, 16 words), CB ids (up to 32), sem aliases to the
  eight hardware semaphores, replay buffer offsets.
- Per RISC: reachable functions, call graph (acyclic), NoC transaction id per request statement.
- Ownership: each CB has one producer RISC and one consumer RISC. Each config field, keyed by (space, word, bits), is
  written by one RISC; a WRCFG word has one writing RISC. CFG_STATE_ID is never written, so every thread stays on
  config bank 0 (masked writes go to the writing thread's bank).
- Out: the map codegen reads, and the manifest (param names -> slots, grid, storage map)."""
