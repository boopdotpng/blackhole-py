"""Tensix instruction injection and register file reads via debug array.

This module provides:
- Low-level instruction injection into Tensix thread FIFOs
- Blackhole Tensix instruction encoders (SETRWC, SETDVALID, etc.)
- Non-destructive SrcA/SrcB/LReg reading via injection + debug array + MMIO restore
"""

from __future__ import annotations

import time

from debug.regs import (
  ARRAY_ID_SRCA, ARRAY_ID_SRCB, ARRAY_ID_DEST,
  DBG_ARRAY_RD_CMD, DBG_ARRAY_RD_DATA, DBG_ARRAY_RD_EN,
  DEBUG_TLB_BASE, DEST_BASE, DEST_CHUNKS_PER_ROW, DEST_ROW_BYTES,
)

# -- Instruction buffer debug registers ------------------------------------ #

INSTRN_BUF_CTRL0  = 0xFFB120A0
INSTRN_BUF_CTRL1  = 0xFFB120A4
INSTRN_BUF_STATUS = 0xFFB120A8

INJECT_POLL_INTERVAL = 0.00001   # 10 µs
INJECT_POLL_TIMEOUT  = 0.5       # 500 ms


# -- Tensix instruction encoders (Blackhole) ------------------------------- #

def _tt_op(opcode: int, params: int) -> int:
  """Encode a 32-bit Tensix instruction."""
  return ((opcode & 0xFF) << 24) | (params & 0x00FFFFFF)


def TT_OP_SETRWC(clear_ab_vld: int, rwc_cr: int, rwc_d: int, rwc_b: int, rwc_a: int, bitmask: int) -> int:
  return _tt_op(0x37, (clear_ab_vld << 22) | (rwc_cr << 18) | (rwc_d << 14) | (rwc_b << 10) | (rwc_a << 6) | bitmask)


def TT_OP_SETDVALID(setvalid: int) -> int:
  return _tt_op(0x57, setvalid)


def TT_OP_CLEARDVALID(cleardvalid: int, reset: int) -> int:
  return _tt_op(0x36, (cleardvalid << 22) | reset)


def TT_OP_SHIFTXB(addr_mode: int, rot_shift: int, shift_row: int) -> int:
  return _tt_op(0x18, (addr_mode << 14) | (rot_shift << 10) | shift_row)


def TT_OP_STALLWAIT(stall_res: int, wait_res: int) -> int:
  return _tt_op(0xA2, (stall_res << 15) | wait_res)


def TT_OP_SFPLOAD(lreg: int, fmt: int, addr_mode: int, dest_addr: int) -> int:
  return _tt_op(0x70, (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr)


def TT_OP_SFPSTORE(lreg: int, fmt: int, addr_mode: int, dest_addr: int) -> int:
  return _tt_op(0x72, (lreg << 20) | (fmt << 16) | (addr_mode << 13) | dest_addr)


def TT_OP_MOVDBGA2D(dest_32b_lo: int, src: int, addr_mode: int, instr_mod: int, dst: int) -> int:
  return _tt_op(0x09, (dest_32b_lo << 23) | (src << 17) | (addr_mode << 14) | (instr_mod << 12) | dst)


def TT_OP_MOVDBGB2D(dest_32b_lo: int, src: int, addr_mode: int, movb2d_instr_mod: int, dst: int) -> int:
  return _tt_op(0x0C, (dest_32b_lo << 23) | (src << 17) | (addr_mode << 14) | (movb2d_instr_mod << 11) | dst)


STALL_SFPU = 0x40
WAIT_SFPU  = 0x4000


# -- Instruction injection ------------------------------------------------- #

class TensixInjector:
  """Injects Tensix instructions into a thread's FIFO via the debug interface."""

  def __init__(self, win, core: tuple[int, int]):
    self.win = win
    self.core = core

  def _target(self):
    from hw import NocOrdering
    self.win.target(self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  def _off(self, addr: int) -> int:
    return addr - DEBUG_TLB_BASE

  def _read_status(self) -> int:
    return self.win.read32(self._off(INSTRN_BUF_STATUS))

  def _poll_status_bit(self, bit: int, description: str):
    deadline = time.monotonic() + INJECT_POLL_TIMEOUT
    while True:
      if self._read_status() & (1 << bit):
        return
      if time.monotonic() > deadline:
        raise TimeoutError(f"timeout waiting for {description} on {self.core}")
      time.sleep(INJECT_POLL_INTERVAL)

  def inject(self, instruction: int, thread_id: int):
    """Inject a single 32-bit Tensix instruction into the given thread's FIFO.

    The instruction goes directly to the Tensix thread, bypassing Baby RISC.
    The relevant Baby RISC should be halted before injecting.

    Args:
      instruction: 32-bit Tensix instruction word
      thread_id: 0=trisc0/unpack, 1=trisc1/math, 2=trisc2/pack
    """
    if not 0 <= thread_id <= 2:
      raise ValueError(f"thread_id must be 0-2, got {thread_id}")

    self._target()

    # 1. Wait for FIFO ready
    self._poll_status_bit(thread_id, f"FIFO ready for thread {thread_id}")

    # 2. Claim the FIFO
    self.win.write32(self._off(INSTRN_BUF_CTRL0), 1 << thread_id)

    # 3. Wait for buffer ready
    self._poll_status_bit(thread_id, f"buffer ready for thread {thread_id}")

    # 4. Write the instruction
    self.win.write32(self._off(INSTRN_BUF_CTRL1), instruction & 0xFFFFFFFF)

    # 5. Push: set push bit + keep claim
    push_bit = 1 << (4 + thread_id)
    claim_bit = 1 << thread_id
    self.win.write32(self._off(INSTRN_BUF_CTRL0), push_bit | claim_bit)

    # 6. Wait for drain
    self._poll_status_bit(4 + thread_id, f"instruction drain for thread {thread_id}")

    # 7. Release FIFO
    self.win.write32(self._off(INSTRN_BUF_CTRL0), 0)

  def inject_batch(self, instructions: list[int], thread_id: int,
                   drain_timeout: float = 2.0):
    """Push multiple Tensix instructions and wait for all to drain.

    Unlike inject(), this does NOT require the FIFO to be empty first.
    Instructions are queued behind any existing FIFO contents.  After all
    pushes, we wait for the entire FIFO to drain (with a longer timeout).

    This is the right path when the FIFO has stalled instructions from
    firmware init — they will eventually clear once the other threads
    (trisc0/trisc2) reach the right synchronization point.
    """
    if not 0 <= thread_id <= 2:
      raise ValueError(f"thread_id must be 0-2, got {thread_id}")

    self._target()
    claim_bit = 1 << thread_id
    push_bit = 1 << (4 + thread_id)

    # Wait for not-full, then claim
    self._poll_status_bit(thread_id, f"FIFO not-full for thread {thread_id}")
    self.win.write32(self._off(INSTRN_BUF_CTRL0), claim_bit)

    for insn in instructions:
      # Wait for not-full before each push
      self._poll_status_bit(thread_id, f"FIFO not-full for thread {thread_id}")
      # Write instruction
      self.win.write32(self._off(INSTRN_BUF_CTRL1), insn & 0xFFFFFFFF)
      # Push (0→1 edge on push bit)
      self.win.write32(self._off(INSTRN_BUF_CTRL0), push_bit | claim_bit)
      # Reset push bit for next edge (keep claim)
      self.win.write32(self._off(INSTRN_BUF_CTRL0), claim_bit)

    # Release FIFO ownership so pipeline can drain normally
    self.win.write32(self._off(INSTRN_BUF_CTRL0), 0)

    # Wait for the entire FIFO to drain (all pre-existing + our instructions)
    deadline = time.monotonic() + drain_timeout
    empty_bit = 4 + thread_id
    while True:
      if self._read_status() & (1 << empty_bit):
        return
      if time.monotonic() > deadline:
        raise TimeoutError(
          f"timeout ({drain_timeout}s) waiting for thread {thread_id} FIFO to drain on {self.core}. "
          f"Pre-existing instructions may be permanently stalled at the Wait Gate."
        )
      time.sleep(INJECT_POLL_INTERVAL)


# -- Debug array reads ----------------------------------------------------- #

def dbg_array_read_row(win, core: tuple[int, int], row: int, array_id: int, bank: int = 0) -> list[int]:
  """Read one register file row (8 x 32-bit chunks) via the debug array."""
  from hw import NocOrdering
  win.target(core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
  off = lambda a: a - DEBUG_TLB_BASE
  win.write32(off(DBG_ARRAY_RD_EN), 1)
  chunks = []
  for chunk in range(DEST_CHUNKS_PER_ROW):
    cmd = (bank << 19) | (array_id << 16) | (chunk << 12) | (row & 0xFFF)
    win.write32(off(DBG_ARRAY_RD_CMD), cmd)
    data = win.read32(off(DBG_ARRAY_RD_DATA))
    chunks.append(data)
  win.write32(off(DBG_ARRAY_RD_EN), 0)
  return chunks


def is_thread_fifo_empty(win, core: tuple[int, int], thread_id: int) -> bool:
  """Check if a Tensix thread's instruction FIFO is empty."""
  from hw import NocOrdering
  win.target(core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
  status = win.read32(INSTRN_BUF_STATUS - DEBUG_TLB_BASE)
  return bool(status & (1 << (4 + thread_id)))


# -- MMIO Dest read/write -------------------------------------------------- #
#
# DEST_BASE (0xFFBD8000) is within the debug TLB window (0xFFB00000..0xFFD00000).
# We can read/write Dest rows directly via the TLB mmap without DR halt.
# This is the key to non-destructive register reads: save Dest via MMIO,
# inject instructions that clobber Dest, read the result, then write it back.

def dest_read_row_mmio(win, core: tuple[int, int], row: int) -> list[int]:
  """Read one Dest row (8 x 32-bit words) via direct MMIO to DEST_BASE."""
  from hw import NocOrdering
  win.target(core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
  base_off = DEST_BASE - DEBUG_TLB_BASE
  row_off = base_off + row * DEST_ROW_BYTES
  return [win.read32(row_off + i * 4) for i in range(DEST_CHUNKS_PER_ROW)]


def dest_write_row_mmio(win, core: tuple[int, int], row: int, chunks: list[int]):
  """Write one Dest row (8 x 32-bit words) via direct MMIO to DEST_BASE.

  This writes through the TLB window to the memory-mapped Dest register file.
  The core should be in a kernel pause loop (not actively writing to Dest).
  """
  from hw import NocOrdering
  win.target(core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
  base_off = DEST_BASE - DEBUG_TLB_BASE
  row_off = base_off + row * DEST_ROW_BYTES
  for i, word in enumerate(chunks):
    win.write32(row_off + i * 4, word & 0xFFFFFFFF)


# -- Bank ownership helpers ------------------------------------------------ #
#
# SrcA and SrcB each have 2 banks.  At any time one bank is owned by the
# Unpackers (for writing) and one by the Matrix Unit (for reading).
#
# SETDVALID(mask) gives the Unpacker's bank to the MU (flips ownership).
#   bit 0 = SrcA, bit 1 = SrcB
# CLEARDVALID(mask, reset) gives the MU's bank back to Unpackers.
#
# The 3-flip dance (SET, CLEAR, SET) ensures the MU ends up owning a bank
# regardless of the initial ownership state.

SRCA_BANK_BIT = 0b01
SRCB_BANK_BIT = 0b10


def _bank_acquire_instructions(bank_bit: int) -> list[int]:
  """3-flip dance to ensure MU owns a bank of SrcA (bit 0) or SrcB (bit 1)."""
  return [
    TT_OP_SETDVALID(bank_bit),       # give Unpacker's bank to MU
    TT_OP_CLEARDVALID(bank_bit, 0),  # give MU's bank back, MU flips
    TT_OP_SETDVALID(bank_bit),       # give Unpacker's (other) bank to MU
  ]


def _bank_release_instructions(bank_bit: int) -> list[int]:
  """Release bank back to Unpackers."""
  return [TT_OP_CLEARDVALID(bank_bit, 0)]


# -- SrcA reading ---------------------------------------------------------- #
#
# SrcA cannot be read through the debug array scan chain directly (array_id=0
# returns nothing useful).  Instead we:
#
#   1. Save Dest[0] via debug array read (pure read, no side effects)
#   2. Acquire SrcA bank for MU via SETDVALID/CLEARDVALID dance
#   3. Reset RWCs so MOVDBGA2D addressing is absolute
#   4. MOVDBGA2D copies SrcA[row] -> Dest[0]
#   5. Read Dest[0] via debug array -> this IS the SrcA data
#   6. Release SrcA bank back to Unpackers
#   7. Restore Dest[0] via MMIO write
#
# Non-destructiveness:
#   - MOVDBGA2D only reads from SrcA (SrcA is never modified)
#   - Dest is saved/restored via debug array read + MMIO write
#   - No LRegs are touched
#   - Bank ownership is returned to original state
#   - RWCs are reset (caller may need to account for this)
#
# MOVDBGA2D src field is 6 bits in the encoding but only the low 4 bits
# select the row within a face (0..15).  The face is determined by the
# SrcA read counter (RWC_A).  We reset RWCs and use row & 0xF.

def read_srca_row(win, core: tuple[int, int], injector: TensixInjector,
                  row: int, thread_id: int = 2, dest_scratch_row: int = 0) -> list[int]:
  """Read one SrcA row non-destructively.

  Injects MOVDBGA2D to copy SrcA[row] into Dest, reads via debug array,
  then restores Dest via MMIO write.  SrcA itself is never modified.

  MOVDBGA2D is a debug-path instruction that bypasses normal bank ownership
  checks.  No SETDVALID/CLEARDVALID dance is needed (unlike SrcB via SHIFTXB).
  tt-exalens uses thread 2 (pack) for this injection.

  Args:
    win: TLBWindow
    core: target core (x, y)
    injector: TensixInjector for the target core
    row: SrcA row to read (0..63)
    thread_id: Tensix thread to inject into (default 2 = pack, matching tt-exalens)
    dest_scratch_row: which Dest row to use as scratch (default 0)

  Returns:
    list of 8 x 32-bit chunks (256 bits) from the SrcA row
  """
  # 1. Save the Dest row we're about to clobber
  saved_dest = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)

  # 2. Inject: reset RWCs, copy SrcA -> Dest via debug move
  #    No bank dance needed — MOVDBGA2D is a debug path that bypasses ownership.
  insns = [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),    # reset all RWCs
    TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, dest_scratch_row),
  ]
  injector.inject_batch(insns, thread_id)

  # 3. Read the scratch Dest row — this is our SrcA data
  srca_data = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)

  # 4. Restore the original Dest row via MMIO write
  dest_write_row_mmio(win, core, dest_scratch_row, saved_dest)

  return srca_data


def read_srca_rows(win, core: tuple[int, int], injector: TensixInjector,
                   num_rows: int = 64, thread_id: int = 1,
                   dest_scratch_row: int = 0) -> list[list[int]]:
  """Read multiple SrcA rows non-destructively."""
  rows = []
  for r in range(num_rows):
    rows.append(read_srca_row(win, core, injector, r, thread_id, dest_scratch_row))
  return rows


# -- SrcB reading ---------------------------------------------------------- #
#
# SrcB has two read strategies:
#
# Strategy A (scan chain + SHIFTXB):
#   The debug array scan chain for SrcB (array_id=1) IS wired, but only
#   returns data when the MU owns the bank.  SHIFTXB is a lightweight MU
#   instruction that "touches" a row, latching it into the scan chain.
#   Downside: SHIFTXB rotates the row left by one lane (destructive).
#   Needs 15 more rotations to undo (16 = identity).
#
# Strategy B (MOVDBGB2D, same pattern as SrcA):
#   MOVDBGB2D copies SrcB -> Dest, then read Dest via debug array.
#   Non-destructive to SrcB.  Only clobbers Dest (restored via MMIO).
#
# We implement Strategy B as the default since it's non-destructive.
# Strategy A is kept as _read_srcb_row_shiftxb for comparison.

def read_srcb_row(win, core: tuple[int, int], injector: TensixInjector,
                  row: int, thread_id: int = 1,
                  dest_scratch_row: int = 0) -> list[int]:
  """Read one SrcB row non-destructively via MOVDBGB2D.

  Same approach as SrcA: copy to Dest, read, restore Dest via MMIO.
  """
  saved_dest = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)

  insns = [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),
    *_bank_acquire_instructions(SRCB_BANK_BIT),
    TT_OP_MOVDBGB2D(0, row & 0xF, 0, 0, dest_scratch_row),
    *_bank_release_instructions(SRCB_BANK_BIT),
  ]
  injector.inject_batch(insns, thread_id)

  srcb_data = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)
  dest_write_row_mmio(win, core, dest_scratch_row, saved_dest)
  return srcb_data


def read_srcb_rows(win, core: tuple[int, int], injector: TensixInjector,
                   num_rows: int = 64, thread_id: int = 1,
                   dest_scratch_row: int = 0) -> list[list[int]]:
  """Read multiple SrcB rows non-destructively."""
  rows = []
  for r in range(num_rows):
    rows.append(read_srcb_row(win, core, injector, r, thread_id, dest_scratch_row))
  return rows


# -- SrcB reading via scan chain (Strategy A, destructive) ----------------- #
#
# Kept for comparison / fallback if MOVDBGB2D doesn't work.

def _srcb_shiftxb_read_instructions(row: int) -> list[int]:
  """Build instruction sequence to make one SrcB row scannable via SHIFTXB."""
  return [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),
    *_bank_acquire_instructions(SRCB_BANK_BIT),
    TT_OP_SHIFTXB(7, 0, row),            # touch row (destructive: rotates left by 1)
    *_bank_release_instructions(SRCB_BANK_BIT),
  ]


def _srcb_shiftxb_restore_instructions(row: int) -> list[int]:
  """Build 15 more SHIFTXB rotations to undo a single read's rotation."""
  return [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),
    *_bank_acquire_instructions(SRCB_BANK_BIT),
    *[TT_OP_SHIFTXB(7, 0, row) for _ in range(15)],
    *_bank_release_instructions(SRCB_BANK_BIT),
  ]


def read_srcb_row_shiftxb(win, core: tuple[int, int], injector: TensixInjector,
                           row: int, thread_id: int = 1, bank: int = 0,
                           restore: bool = True,
                           drain_timeout: float = 2.0) -> list[int]:
  """Read one SrcB row via SHIFTXB + scan chain (destructive, then restore).

  SHIFTXB rotates the row left by one lane.  If restore=True, 15 more
  rotations are applied to undo (16 total = identity).
  """
  injector.inject_batch(_srcb_shiftxb_read_instructions(row), thread_id,
                        drain_timeout=drain_timeout)
  data = dbg_array_read_row(win, core, row, ARRAY_ID_SRCB, bank=bank)
  if restore:
    injector.inject_batch(_srcb_shiftxb_restore_instructions(row), thread_id,
                          drain_timeout=drain_timeout)
  return data


def read_srcb_row_direct(win, core: tuple[int, int], row: int, bank: int = 0) -> list[int]:
  """Read one SrcB row via direct debug array access (no injection).

  Returns zeros unless the MU already owns the bank.  Diagnostic only.
  """
  return dbg_array_read_row(win, core, row, ARRAY_ID_SRCB, bank=bank)


# -- LReg reading ---------------------------------------------------------- #
#
# SFPU LRegs (lreg0..lreg15) are read by:
#   1. Save Dest[scratch_row] via debug array
#   2. SFPSTORE(lreg, 0, 0, scratch_row) -> writes LReg into Dest
#   3. Read Dest[scratch_row] via debug array -> LReg data
#   4. Restore Dest[scratch_row] via MMIO write
#
# This never modifies the LReg itself (SFPSTORE is a read from LReg).

def read_lreg(win, core: tuple[int, int], injector: TensixInjector,
              lreg: int, thread_id: int = 2,
              dest_scratch_row: int = 0) -> list[int]:
  """Read one SFPU LReg non-destructively.

  Args:
    lreg: LReg index (0..15)
    thread_id: thread to inject into (default 2 = pack, has SFPU access)
    dest_scratch_row: Dest row to use as scratch

  Returns:
    list of 8 x 32-bit chunks (256 bits)
  """
  if not 0 <= lreg <= 15:
    raise ValueError(f"lreg must be 0..15, got {lreg}")

  saved_dest = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)

  insns = [
    TT_OP_SFPSTORE(lreg, 0, 0, dest_scratch_row),
    TT_OP_STALLWAIT(STALL_SFPU, WAIT_SFPU),  # wait for SFPSTORE to complete
  ]
  injector.inject_batch(insns, thread_id)

  lreg_data = dbg_array_read_row(win, core, dest_scratch_row, ARRAY_ID_DEST, bank=0)
  dest_write_row_mmio(win, core, dest_scratch_row, saved_dest)
  return lreg_data


def read_lregs(win, core: tuple[int, int], injector: TensixInjector,
               num_lregs: int = 16, thread_id: int = 2,
               dest_scratch_row: int = 0) -> list[list[int]]:
  """Read multiple SFPU LRegs non-destructively."""
  return [read_lreg(win, core, injector, i, thread_id, dest_scratch_row)
          for i in range(num_lregs)]
