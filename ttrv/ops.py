"""Every device operation: its operand signature and its lowering. One table, name -> (signature, function).

The binder turns positional and named args into a dict with per-op defaults, checks which fields must be constant,
and hands it to the lowering function, which emits items through codegen. Three kinds:

  A. Tensix word: all fields constant -> one inline word (isa.inline). A runtime field -> build the word in RV
     registers (constant part | value << shift) and sw it to the instruction buffer. math.*, sfp.*, sem.*,
     tensix.stall, mop.run, replay.run.
  B. Recipe: a short RV sequence. cb.*, noc.* (incl. the per-page DRAM loop), tensix.wait, split, sem.read, the
     unpack/pack address and context setup, .fmt/.cfg.
  C. Template install: mop.load (MOP config writes), replay.load (REPLAY record + body words).

Hardware rules lowering must follow (measured on p150a, see boop-docs/kernel-dev/known-issues.md):

unpack.ctx <a|b> reset -- the unpacker context counter reset. A lone SETC16 of CfgContextCntReset is silently lost
unless an unpacker instruction issues within a few cycles of it, so always emit exactly:
  SETC16 UNPACK_MISC_CFG (41), offsets | reset bit   (bit 4 = unpacker A, bit 12 = unpacker B)
  UNPACR_NOP <unpacker>, mode 2                      (delay mode, no side effects; mode 1 would clear a Src bank)
  SETC16 UNPACK_MISC_CFG (41), offsets               (clear the bit; this word also holds both CfgContextOffsets)
Nothing may be scheduled between these three.

unpack.ctx <a|b> count=N -- counter wrap, any N in 1-8 (b: 1-2). Always lower to the non_log2 fields:
  THCON_SEC[n]_REG2_Context_count_non_log2_en = 1, THCON_SEC[n]_REG2_Context_count_non_log2 = N - 1
  (word 73 / 121, bits 12 and 11:9). Counter then cycles 0..N-1; Context_count (log2) is ignored while _en = 1.

Context the unpacker reads: (CfgContextOffset + (AutoIncContextID ? counter : CfgContextId)) mod 8. The counter
steps on every UNPACR with AutoIncContextID, not per tile. The offset is not stored in the counter.

SETC16 CfgContextCntInc does nothing on hardware: increment with UNPACR CfgContextCntInc=1 or AutoIncContextID.
Unpacker B context >= 2 (offset + id mod 8, or counter with count > 2) hangs the card: reject it."""
