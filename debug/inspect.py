# debug/inspect.py - Higher-level inspection: Dest tiles, LRegs, L1, CFG
#
# These operate on a halted TileDebugger and read Tensix compute state
# that goes beyond the basic RISC-V GPRs.
#
# Reference: tt-exalens/ttexalens/debug_tensix.py
#            tt-llk/tt_llk_blackhole/common/inc/ckernel_debug.h

from __future__ import annotations
import struct, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from hw import TLBWindow, Core

from debug.regs import (
  DEBUG_REGS_BASE, DEBUG_TLB_BASE, tlb_align,
  DBG_ARRAY_RD_EN, DBG_ARRAY_RD_CMD, DBG_ARRAY_RD_DATA,
  ARRAY_SRCA, ARRAY_SRCB, ARRAY_DEST, dbg_array_cmd,
  TENSIX_CREG_READ, TENSIX_CREG_RDDATA,
  CFG_THREAD_0, CFG_THREAD_1, CFG_THREAD_2, CFG_HW_0, CFG_HW_1,
  INSTRN_BUF_CTRL0, INSTRN_BUF_CTRL1, INSTRN_BUF_STATUS,
  DEST_BASE, DEST_SIZE,
  FPU_STICKY_BITS,
  WALL_CLOCK_L, WALL_CLOCK_H,
  TT_SFPLOAD, TT_SFPSTORE, TT_STALLWAIT, TT_SETRWC, TT_MOVDBGA2D,
  STALL_SFPU, WAIT_SFPU, SFPU_FMT_FP32, LREG_COUNT,
  PRIVATE_DATA_NOC_ADDR, PRIVATE_DATA_SIZE,
  L1_SIZE,
)

DEST_TLB_BASE, DEST_TLB_OFFSET = tlb_align(DEST_BASE)


class TileInspector:
  """Read Tensix compute state from a Tensix tile via TLBWindow.

  The TLBWindow is shared with TileDebugger and will be re-targeted
  as needed. Most operations require the relevant RISC cores to be halted.
  """

  TILE_ROWS = 32 * 32   # 1024 rows per tile (in 16-bit mode)
  TILE_COLS = 16
  DEST_TILES = 8

  def __init__(self, tlb: TLBWindow, core: Core):
    self.tlb = tlb
    self.core = core

  def _target(self, base_addr: int):
    """Target TLB at a 2MB-aligned window containing base_addr."""
    from hw import NocOrdering
    aligned_base, _ = tlb_align(base_addr)
    self._current_tlb_base = aligned_base
    self.tlb.target(self.core, addr=aligned_base, mode=NocOrdering.STRICT)

  def _off(self, addr: int) -> int:
    """Convert absolute address to offset within current TLB window."""
    return addr - self._current_tlb_base

  # -- L1 memory ----------------------------------------------------------- #

  def read_l1(self, addr: int, size: int = 4) -> bytes:
    """Read bytes from L1 (address 0x0 .. 0x17FFFF). No halt required."""
    if addr < 0 or addr + size > L1_SIZE:
      raise ValueError(f"L1 address 0x{addr:x}+{size} out of range (max 0x{L1_SIZE:x})")
    self._target(addr & ~0x1FFFFF)  # align to 2MB TLB window
    base = addr & ~0x1FFFFF
    result = bytearray()
    # read in 4-byte chunks
    off = addr - base
    remaining = size
    while remaining > 0:
      chunk = min(remaining, 4)
      val = self.tlb.read32(off)
      result.extend(val.to_bytes(4, "little")[:chunk])
      off += 4
      remaining -= chunk
    return bytes(result)

  def read_l1_u32(self, addr: int) -> int:
    """Read a single u32 from L1."""
    return int.from_bytes(self.read_l1(addr, 4), "little")

  def write_l1(self, addr: int, data: bytes):
    """Write bytes to L1."""
    if addr < 0 or addr + len(data) > L1_SIZE:
      raise ValueError(f"L1 address 0x{addr:x}+{len(data)} out of range")
    self._target(addr & ~0x1FFFFF)
    base = addr & ~0x1FFFFF
    off = addr - base
    # write in 4-byte aligned chunks
    i = 0
    while i < len(data):
      chunk = min(len(data) - i, 4)
      if chunk == 4:
        val = int.from_bytes(data[i:i+4], "little")
      else:
        # partial word: read-modify-write
        existing = self.tlb.read32(off).to_bytes(4, "little")
        word = bytearray(existing)
        word[:chunk] = data[i:i+chunk]
        val = int.from_bytes(word, "little")
      self.tlb.write32(off, val)
      off += 4
      i += chunk

  def dump_l1(self, addr: int, count: int = 64) -> str:
    """Hex dump of L1 memory, 16 bytes per line."""
    data = self.read_l1(addr, count)
    lines = []
    for i in range(0, len(data), 16):
      row = data[i:i+16]
      hexpart = " ".join(f"{b:02x}" for b in row)
      ascpart = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
      lines.append(f"  0x{addr+i:06x}: {hexpart:<48s} {ascpart}")
    return "\n".join(lines)

  # -- direct dest register access (Blackhole only) ------------------------ #

  def read_dest_raw(self, num_tiles: int = 8) -> bytes:
    """Read dest register file directly at 0xFFBD8000.

    Returns raw bytes: num_tiles * 1024 * 4 bytes.
    Default format is FP32 (32 bits per datum, 1024 datums per tile,
    where each tile = 32 rows x 16 cols in the 32-bit view).

    TRISC1 (math) should be halted to get a consistent snapshot.
    """
    size = num_tiles * 1024 * 4
    if size > DEST_SIZE:
      size = DEST_SIZE
    self._target(DEST_BASE)
    result = bytearray(size)
    for i in range(0, size, 4):
      val = self.tlb.read32(i)
      struct.pack_into("<I", result, i, val)
    return bytes(result)

  def read_dest_tile(self, tile: int = 0) -> list[list[float]]:
    """Read one dest tile as 32x32 grid of FP32 values.

    Returns list of 32 rows, each with 32 float values.
    Note: Tensix tiles are stored as 4 faces of 16x16, but the
    direct dest access gives them linearly.
    """
    if tile < 0 or tile >= self.DEST_TILES:
      raise ValueError(f"tile must be 0..{self.DEST_TILES - 1}")
    raw = self.read_dest_raw(num_tiles=tile + 1)
    tile_offset = tile * 1024 * 4
    tile_data = raw[tile_offset:tile_offset + 1024 * 4]
    floats = struct.unpack(f"<{1024}f", tile_data)
    return [list(floats[r*32:(r+1)*32]) for r in range(32)]

  def dump_dest_summary(self, tile: int = 0) -> str:
    """Print a compact summary of a dest tile."""
    grid = self.read_dest_tile(tile)
    lines = [f"  Dest tile {tile} (32x32 FP32):"]
    for r in range(min(4, len(grid))):  # first 4 rows
      vals = " ".join(f"{v:8.4f}" for v in grid[r][:8])  # first 8 cols
      lines.append(f"    row {r:2d}: {vals} ...")
    lines.append(f"    ... ({len(grid)} rows total)")
    return "\n".join(lines)

  # -- debug array reads (SrcA, SrcB, Dest via array interface) ------------ #
  #
  # Register file layout:
  #   SrcA / SrcB: 2 banks x 64 rows x 16 cols x 19 bits (double-buffered)
  #     - bank 0 / bank 1: one is owned by unpackers, one by matrix unit
  #     - each row = 8 x 32-bit chunks via debug array interface
  #   Dest: 1024 rows x 16 cols x 16 bits (or 512 x 16 x 32 bits in FP32)
  #     - single buffer, shared between math (writer) and pack (reader)
  #     - also directly accessible at 0xFFBD8000 on Blackhole
  #
  # SrcB: readable directly via debug array (array_id=1, bank_id=0|1)
  # SrcA: NOT directly readable. Must inject MOVDBGA2D to copy a row
  #        to dest, then read dest via debug array.

  REGFILE_ROWS = 64
  REGFILE_CHUNKS_PER_ROW = 8  # 8 x 32-bit words per row

  def _dbg_array_read_row(self, array_id: int, row: int, bank: int = 0) -> list[int]:
    """Read one row (8 x 32-bit chunks) from a register array.

    array_id: 0=SrcA, 1=SrcB, 2=Dest
    bank: 0 or 1 (for double-buffered SrcA/SrcB)
    """
    self._target(DEBUG_REGS_BASE)
    self.tlb.write32(self._off(DBG_ARRAY_RD_EN), 1)
    chunks = []
    for i in range(self.REGFILE_CHUNKS_PER_ROW):
      cmd = dbg_array_cmd(array_id, row, i, bank)
      self.tlb.write32(self._off(DBG_ARRAY_RD_CMD), cmd)
      time.sleep(0.00002)  # ~20us settle time
      val = self.tlb.read32(self._off(DBG_ARRAY_RD_DATA))
      chunks.append(val)
    self.tlb.write32(self._off(DBG_ARRAY_RD_EN), 0)
    return chunks

  def read_dest_array(self, row: int) -> list[int]:
    """Read one dest row via the debug array interface (8 x 32-bit words)."""
    return self._dbg_array_read_row(ARRAY_DEST, row)

  # -- SrcB ---------------------------------------------------------------- #

  def read_srcb_row(self, row: int, bank: int = 0) -> list[int]:
    """Read one SrcB row (8 x 32-bit chunks). Direct debug array read."""
    return self._dbg_array_read_row(ARRAY_SRCB, row, bank)

  def read_srcb(self, bank: int = 0, num_rows: int = 64) -> list[list[int]]:
    """Read SrcB register file (one bank).

    Returns list of rows, each row = 8 x 32-bit words.
    bank: 0 or 1 (the two double-buffer banks).
    """
    return [self.read_srcb_row(r, bank) for r in range(min(num_rows, self.REGFILE_ROWS))]

  def dump_srcb(self, bank: int = 0, num_rows: int = 4) -> str:
    """Compact dump of SrcB register file."""
    lines = [f"  SrcB bank {bank} ({self.REGFILE_ROWS} rows x 8 chunks):"]
    for r in range(min(num_rows, self.REGFILE_ROWS)):
      chunks = self.read_srcb_row(r, bank)
      vals = " ".join(f"{v:08x}" for v in chunks[:4])
      lines.append(f"    row {r:2d}: {vals} ...")
    if num_rows < self.REGFILE_ROWS:
      lines.append(f"    ... ({self.REGFILE_ROWS} rows total)")
    return "\n".join(lines)

  # -- SrcA (requires instruction injection) ------------------------------- #

  def read_srca_row(self, row: int, bank: int = 0) -> list[int]:
    """Read one SrcA row by injecting MOVDBGA2D to copy it to dest.

    TRISC1 (math) must be halted. Temporarily clobbers dest row 0.

    Protocol (from tt-exalens debug_tensix.py):
      1. Save dest rows that will be clobbered
      2. Inject SFPLOAD to save LReg3 state (it gets used internally)
      3. Inject MOVDBGA2D(src=row, ...) to copy SrcA debug row -> dest
      4. Read dest via debug array (array_id=DEST, row=0)
      5. Inject SFPSTORE to restore LReg3
      6. Restore dest
    """
    MATH_THREAD = 1
    saved = self._save_dest_rows(0, 128)  # save 2 dest rows (32 floats)

    self._target(DEBUG_REGS_BASE)
    self._inject_start(MATH_THREAD)
    # save LReg3 to dest rows 0,2 first (SFPLOAD reads from dest into LReg)
    self._inject_push(TT_SFPLOAD(3, 0, 0, 0), MATH_THREAD)
    self._inject_push(TT_SFPLOAD(3, 0, 0, 2), MATH_THREAD)
    self._inject_push(TT_STALLWAIT(STALL_SFPU, WAIT_SFPU), MATH_THREAD)
    # MOVDBGA2D: copy SrcA debug row to dest for readout
    # src field encodes the row within the 16-row group: row & 0xF
    # the bank/group selection is implicit from the last-used state
    self._inject_push(TT_MOVDBGA2D(0, row & 0xF, 0, 0, 0), MATH_THREAD)
    self._inject_push(TT_STALLWAIT(STALL_SFPU, WAIT_SFPU), MATH_THREAD)
    self._inject_end(MATH_THREAD)
    time.sleep(0.0001)

    # read the dest row via debug array (the MOVDBGA2D wrote it there)
    # we read from array_id=DEST (2), row=0
    chunks = self._dbg_array_read_row(ARRAY_DEST, 0)

    # restore: inject SFPSTORE to put LReg3 back to dest rows 0,2
    self._target(DEBUG_REGS_BASE)
    self._inject_start(MATH_THREAD)
    self._inject_push(TT_SFPSTORE(3, 0, 0, 0), MATH_THREAD)
    self._inject_push(TT_SFPSTORE(3, 0, 0, 2), MATH_THREAD)
    self._inject_push(TT_STALLWAIT(STALL_SFPU, WAIT_SFPU), MATH_THREAD)
    # reset read/write counters every 16 rows
    if (row + 1) % 16 == 0:
      self._inject_push(TT_SETRWC(3, 0, 0, 0, 0, 0xF), MATH_THREAD)
    self._inject_end(MATH_THREAD)
    time.sleep(0.0001)

    # restore the original dest content
    self._restore_dest_rows(0, saved)
    return chunks

  def read_srca(self, bank: int = 0, num_rows: int = 64) -> list[list[int]]:
    """Read SrcA register file (one bank) via instruction injection.

    TRISC1 (math) must be halted. Slow (~20ms for 64 rows).
    bank parameter is currently not selectable via MOVDBGA2D (reads
    the last-used bank); included for API symmetry.
    """
    return [self.read_srca_row(r, bank) for r in range(min(num_rows, self.REGFILE_ROWS))]

  def dump_srca(self, bank: int = 0, num_rows: int = 4) -> str:
    """Compact dump of SrcA register file."""
    lines = [f"  SrcA (last-used bank, {self.REGFILE_ROWS} rows x 8 chunks):"]
    for r in range(min(num_rows, self.REGFILE_ROWS)):
      chunks = self.read_srca_row(r, bank)
      vals = " ".join(f"{v:08x}" for v in chunks[:4])
      lines.append(f"    row {r:2d}: {vals} ...")
    if num_rows < self.REGFILE_ROWS:
      lines.append(f"    ... ({self.REGFILE_ROWS} rows total)")
    return "\n".join(lines)

  # -- CFG register reads -------------------------------------------------- #

  def read_cfg(self, index: int) -> int:
    """Read a Tensix CFG register by index.

    index = cfg_id * HW_CFG_SIZE + register_offset
    Uses the debug path (TENSIX_CREG_READ/RDDATA), accessible from NOC.
    """
    self._target(DEBUG_REGS_BASE)
    self.tlb.write32(self._off(TENSIX_CREG_READ), index)
    time.sleep(0.00002)  # few cycles to latch
    return self.tlb.read32(self._off(TENSIX_CREG_RDDATA))

  def read_fpu_sticky_bits(self) -> int:
    """Read FPU sticky bits (NaN/Inf/etc flags)."""
    self._target(DEBUG_REGS_BASE)
    return self.tlb.read32(self._off(FPU_STICKY_BITS))

  # -- instruction injection ----------------------------------------------- #

  def _inject_start(self, thread_id: int):
    """Claim a thread's instruction FIFO for injection."""
    self._target(DEBUG_REGS_BASE)
    deadline = time.monotonic() + 0.5
    while True:
      status = self.tlb.read32(self._off(INSTRN_BUF_STATUS))
      if status & (1 << thread_id):
        break
      if time.monotonic() > deadline:
        raise TimeoutError(f"instruction buffer not ready for thread {thread_id}")
      time.sleep(0.0001)
    self.tlb.write32(self._off(INSTRN_BUF_CTRL0), 1 << thread_id)

  def _inject_push(self, insn: int, thread_id: int):
    """Push one instruction into the thread's FIFO."""
    deadline = time.monotonic() + 0.5
    while True:
      status = self.tlb.read32(self._off(INSTRN_BUF_STATUS))
      if status & (1 << thread_id):
        break
      if time.monotonic() > deadline:
        raise TimeoutError(f"instruction push timeout for thread {thread_id}")
      time.sleep(0.0001)
    self.tlb.write32(self._off(INSTRN_BUF_CTRL1), insn)
    self.tlb.write32(self._off(INSTRN_BUF_CTRL0), (1 << (4 + thread_id)) | (1 << thread_id))
    deadline = time.monotonic() + 0.5
    while True:
      status = self.tlb.read32(self._off(INSTRN_BUF_STATUS))
      if status & (1 << (4 + thread_id)):
        break
      if time.monotonic() > deadline:
        raise TimeoutError(f"instruction drain timeout for thread {thread_id}")
      time.sleep(0.0001)

  def _inject_end(self, thread_id: int):
    """Release the thread's instruction FIFO."""
    self.tlb.write32(self._off(INSTRN_BUF_CTRL0), 0)

  def inject_instruction(self, insn: int, thread_id: int):
    """Inject a single Tensix instruction into a thread FIFO.

    thread_id: 0 = unpack (TRISC0), 1 = math (TRISC1), 2 = pack (TRISC2)
    The relevant TRISC must be halted.
    """
    self._inject_start(thread_id)
    self._inject_push(insn, thread_id)
    self._inject_end(thread_id)

  # -- LReg (SFPU register) reads ----------------------------------------- #

  # readable LReg indices:
  #   0-7:   mutable (general purpose)
  #   8:     read-only constant 0.8373 (skip, known value)
  #   9:     read-only constant 0.0    (skip)
  #   10:    read-only constant 1.0    (skip)
  #   11-14: programmable constants (writable via SFPCONFIG, readable via SFPSTORE)
  #   15:    read-only, lane i = i*2   (skip, known pattern)
  #   16:    writable by SFPLOADMACRO only
  LREG_READABLE = [*range(8), 11, 12, 13, 14, 16]
  LREG_CONSTANTS = {
    8:  ("const", 0.8373),
    9:  ("const", 0.0),
    10: ("const", 1.0),
    15: ("const", "lane_id * 2"),
  }

  def read_lregs(self, indices: list[int] | None = None) -> dict[int, list[float]]:
    """Read SFPU LRegs by injecting SFPSTORE to Dest.

    TRISC1 (math) must be halted. Stores all requested LRegs to
    consecutive dest rows in one batch, reads them all, then restores.

    indices: which LRegs to read (default: all readable = 0-7, 11-14, 16).
    Returns {lreg_index: [32 x float32 lane values]}.
    """
    if indices is None:
      indices = self.LREG_READABLE
    MATH_THREAD = 1
    to_read = [i for i in indices if i not in self.LREG_CONSTANTS]
    if not to_read:
      return {}

    # each SFPSTORE writes 32 lanes x 4 bytes = 128 bytes to dest
    total_bytes = len(to_read) * 128
    saved = self._save_dest_rows(0, total_bytes)

    # inject all SFPSTOREs in one batch, each to a different dest offset
    self._target(DEBUG_REGS_BASE)
    self._inject_start(MATH_THREAD)
    for slot, lreg_idx in enumerate(to_read):
      # addr_mode=4 means use absolute dest_reg_addr (slot * 2 for FP32 row pairs)
      self._inject_push(TT_SFPSTORE(lreg_idx, SFPU_FMT_FP32, 0, slot * 2), MATH_THREAD)
    self._inject_push(TT_STALLWAIT(STALL_SFPU, WAIT_SFPU), MATH_THREAD)
    self._inject_end(MATH_THREAD)
    time.sleep(0.0002)

    # read all lanes at once from dest
    result = {}
    self._target(DEST_BASE)
    for slot, lreg_idx in enumerate(to_read):
      base_off = slot * 128
      lanes = []
      for lane in range(32):
        raw = self.tlb.read32(base_off + lane * 4)
        lanes.append(struct.unpack("<f", struct.pack("<I", raw))[0])
      result[lreg_idx] = lanes

    self._restore_dest_rows(0, saved)
    return result

  def read_lreg(self, index: int) -> list[float]:
    """Read a single LReg. Returns 32 float32 lane values."""
    result = self.read_lregs([index])
    if index not in result:
      raise ValueError(f"LReg {index} is a known constant, not readable via injection")
    return result[index]

  def _save_dest_rows(self, offset: int, size: int) -> bytes:
    """Save dest bytes starting at offset (relative to DEST_BASE)."""
    self._target(DEST_BASE)
    data = bytearray(size)
    for i in range(0, size, 4):
      struct.pack_into("<I", data, i, self.tlb.read32(offset + i))
    return bytes(data)

  def _restore_dest_rows(self, offset: int, data: bytes):
    """Restore dest bytes."""
    self._target(DEST_BASE)
    for i in range(0, len(data), 4):
      val = struct.unpack_from("<I", data, i)[0]
      self.tlb.write32(offset + i, val)

  def dump_lregs(self) -> str:
    """Read and format all LRegs as a string."""
    lregs = self.read_lregs()
    lines = ["  SFPU LRegs (32 lanes each):"]
    for idx in range(17):
      if idx in lregs:
        vals = lregs[idx]
        preview = " ".join(f"{v:8.4f}" for v in vals[:8])
        lines.append(f"    LR{idx:<2d}: {preview} ...")
      elif idx in self.LREG_CONSTANTS:
        kind, val = self.LREG_CONSTANTS[idx]
        lines.append(f"    LR{idx:<2d}: ({kind} {val})")
    return "\n".join(lines)

  # -- private data memory ------------------------------------------------- #

  def read_private_data(self, risc: str, offset: int = 0, size: int | None = None) -> bytes:
    """Read a RISC core's private data memory via its NOC address.

    Does not require halt (NOC read, not debug memory read).
    """
    if risc not in PRIVATE_DATA_NOC_ADDR:
      raise ValueError(f"unknown risc: {risc}")
    noc_addr = PRIVATE_DATA_NOC_ADDR[risc]
    max_size = PRIVATE_DATA_SIZE[risc]
    if size is None:
      size = max_size
    if offset + size > max_size:
      raise ValueError(f"{risc} private data: offset {offset} + size {size} > {max_size}")
    self._target(noc_addr + offset)
    result = bytearray(size)
    for i in range(0, size, 4):
      chunk = min(size - i, 4)
      val = self.tlb.read32(i)
      result[i:i+chunk] = val.to_bytes(4, "little")[:chunk]
    return bytes(result)
