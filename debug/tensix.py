"""Tensix instruction injection and register file reads via debug array.

This module provides:
- Low-level instruction injection into Tensix thread FIFOs
- Blackhole Tensix instruction encoders (SETRWC, SETDVALID, etc.)
- SrcB reading via injection + debug array scan chain
"""

from __future__ import annotations

import time

from debug.regs import (
  ARRAY_ID_SRCA, ARRAY_ID_SRCB, ARRAY_ID_DEST,
  DBG_ARRAY_RD_CMD, DBG_ARRAY_RD_DATA, DBG_ARRAY_RD_EN,
  DEBUG_TLB_BASE, DEST_CHUNKS_PER_ROW,
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


STALL_SFPU = 0x40   # tt-exalens uses 0x40 for stall_res in SrcA reads
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


# -- SrcB reading ---------------------------------------------------------- #
#
# SrcB cannot be read through the debug array scan chain without first
# transferring bank ownership to the Matrix Unit via instruction injection.
#
# The scan chain for SrcB is wired through the Matrix Unit's read port.
# When AllowedClient == Unpackers, the scan chain returns zeros.  To get
# real data we must:
#
#   1. SETRWC — reset all Read/Write Counters so row addresses are absolute
#   2. SETDVALID(0b10) — give the Unpacker's current SrcB bank to the
#      Matrix Unit (and flip the Unpacker to the other bank)
#   3. CLEARDVALID(0b10, 0) — give the MU's current bank back to Unpackers
#      (and flip the MU to the other bank)
#   4. SETDVALID(0b10) — give the Unpacker's (now-other) bank to the MU
#   5. SHIFTXB(7, 0, row) — a lightweight Matrix Unit instruction that
#      accesses SrcB[row], latching the row contents into the scan chain.
#      This is a rotate-left-by-one-lane, so it IS destructive to SrcB.
#   6. CLEARDVALID(0b10, 0) — return the bank to Unpackers
#
# Steps 2-4 cycle the bank state machine so that the MU ends up owning a
# bank regardless of the initial ownership state.  Step 5 is the actual
# "touch" that makes the row scannable.
#
# Destructiveness:  SHIFTXB rotates each row left by one lane (column).
# To undo the rotation after reading, call restore_srcb_row() which
# applies 15 more rotations (16 total = identity).
#
# This sequence follows the approach used in tt-exalens debug_tensix.py.

def _srcb_read_instructions(row: int) -> list[int]:
  """Build the instruction sequence to make one SrcB row scannable."""
  return [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),   # reset RWCs
    TT_OP_SETDVALID(0b10),                # give Unpacker's bank to MU
    TT_OP_CLEARDVALID(0b10, 0),           # give MU's bank to Unpackers, MU flips
    TT_OP_SETDVALID(0b10),                # give Unpacker's (other) bank to MU
    TT_OP_SHIFTXB(7, 0, row),            # touch row (destructive rotate)
    TT_OP_CLEARDVALID(0b10, 0),           # release bank
  ]


def _srcb_restore_instructions(row: int) -> list[int]:
  """Build 15 more SHIFTXB rotations to undo a single read's rotation."""
  return [
    TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF),
    TT_OP_SETDVALID(0b10),
    TT_OP_CLEARDVALID(0b10, 0),
    TT_OP_SETDVALID(0b10),
    *[TT_OP_SHIFTXB(7, 0, row) for _ in range(15)],
    TT_OP_CLEARDVALID(0b10, 0),
  ]


def read_srcb_row(win, core: tuple[int, int], injector: TensixInjector, row: int,
                  thread_id: int = 1, bank: int = 0,
                  drain_timeout: float = 2.0) -> list[int]:
  """Read one SrcB row by injecting bank-ownership + SHIFTXB, then scanning.

  Uses batch injection so this works even when the FIFO has pre-existing
  instructions (e.g. from firmware init).  Our instructions queue behind
  them and execute once the stall clears.

  WARNING: SHIFTXB rotates the row left by one lane.  Call
  restore_srcb_row() afterwards if you need to preserve SrcB contents.

  Args:
    win: TLBWindow
    core: target core (x, y)
    injector: TensixInjector for the target core
    row: SrcB row to read (0..63)
    thread_id: Tensix thread to inject into (must be halted; default 1 = math)
    bank: SrcB bank (0 or 1)
    drain_timeout: seconds to wait for FIFO drain (default 2s)
  """
  injector.inject_batch(_srcb_read_instructions(row), thread_id,
                        drain_timeout=drain_timeout)
  return dbg_array_read_row(win, core, row, ARRAY_ID_SRCB, bank=bank)


def restore_srcb_row(injector: TensixInjector, row: int, thread_id: int = 1,
                     drain_timeout: float = 2.0):
  """Undo the SHIFTXB rotation by applying 15 more left-rotations.

  SHIFTXB rotates a row left by one lane.  Doing this 16 times total is
  the identity (16 columns per row), so 15 more rotations restore the
  original data.
  """
  injector.inject_batch(_srcb_restore_instructions(row), thread_id,
                        drain_timeout=drain_timeout)


def read_srcb_row_direct(win, core: tuple[int, int], row: int, bank: int = 0) -> list[int]:
  """Read one SrcB row via direct debug array access (no injection).

  This returns zeros unless the Matrix Unit already owns the bank (rare).
  Kept for diagnostic comparison against the injection-based path.
  """
  return dbg_array_read_row(win, core, row, ARRAY_ID_SRCB, bank=bank)


def read_srcb_rows(win, core: tuple[int, int], injector: TensixInjector,
                   num_rows: int = 64, thread_id: int = 1, bank: int = 0,
                   restore: bool = False) -> list[list[int]]:
  """Read multiple SrcB rows via injection + debug array.

  Args:
    restore: if True, apply 15 extra SHIFTXB rotations per row to undo
             the destructive rotation.  Slow but preserves SrcB contents.
  """
  rows = []
  for r in range(num_rows):
    rows.append(read_srcb_row(win, core, injector, r, thread_id, bank))
    if restore:
      restore_srcb_row(injector, r, thread_id)
  return rows


# -- SrcA reading ---------------------------------------------------------- #
#
# SrcA cannot be read through the debug array directly (array_id=0 returns
# nothing useful).  Instead, we inject instructions to copy SrcA rows into
# Dest via MOVDBGA2D, then read Dest via the debug array.
#
# This is the exact sequence proven working in tt-exalens on Blackhole.
# tt-exalens uses thread_id=2 (pack thread) for this injection.
#
# IMPORTANT: The target thread's FIFO must be EMPTY for injection to work.
# Use a PAUSE spin-wait in the kernel to guarantee this.
#
# Limitations:
#   - MOVDBGA2D has a 4-bit src field: only row & 0xF (rows 0-15 per face)
#   - You get the last 2 faces written (hardware limitation, no bank select)
#   - Clobbers Dest rows 0 and 2 (best-effort restore via LReg3)

def read_srca_row(win, core: tuple[int, int], injector: TensixInjector,
                  row: int, thread_id: int = 2) -> list[int]:
  """Read one SrcA row by injecting MOVDBGA2D into Dest, then reading Dest.

  Args:
    win: TLBWindow
    core: target core (x, y)
    injector: TensixInjector for the target core
    row: SrcA row to read (0..63)
    thread_id: Tensix thread to inject into (default 2 = pack, matching tt-exalens)

  Returns:
    list of 8 x 32-bit chunks (256 bits) from the SrcA row
  """
  # Phase 1: save LReg3 from Dest, then copy SrcA row into Dest row 0
  injector.inject(TT_OP_SFPLOAD(3, 0, 0, 0), thread_id)   # save dest row 0 -> LReg3
  injector.inject(TT_OP_SFPLOAD(3, 0, 0, 2), thread_id)   # save dest row 2 -> LReg3
  injector.inject(TT_OP_STALLWAIT(STALL_SFPU, WAIT_SFPU), thread_id)
  injector.inject(TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, 0), thread_id)  # SrcA row -> Dest row 0

  # Phase 2: read Dest row 0 via debug array
  chunks = dbg_array_read_row(win, core, 0, ARRAY_ID_DEST, bank=0)

  # Phase 3: restore LReg3 back to Dest and reset counters periodically
  injector.inject(TT_OP_SFPSTORE(3, 0, 0, 0), thread_id)  # restore dest row 0
  injector.inject(TT_OP_SFPSTORE(3, 0, 0, 2), thread_id)  # restore dest row 2
  if row % 16 == 15:
    injector.inject(TT_OP_SETRWC(3, 0, 0, 0, 0, 0xF), thread_id)  # reset RWCs every face

  return chunks


def read_srca_rows(win, core: tuple[int, int], injector: TensixInjector,
                   num_rows: int = 64, thread_id: int = 2) -> list[list[int]]:
  """Read multiple SrcA rows via injection + debug array."""
  rows = []
  for r in range(num_rows):
    rows.append(read_srca_row(win, core, injector, r, thread_id))
  return rows
