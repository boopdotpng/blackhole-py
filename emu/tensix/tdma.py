# =============================================================================
# TDMA-RISC register block (0xFFB11000..0xFFB11FFF).  MMIO front-end for the
# Mover DMA engine: any RISC-V core writes staging registers and a command
# word here instead of issuing an XMOV Tensix instruction.
#
# Implements the command processor from emu/specs/xmov-and-tdma-mover.md §3:
#
#   0x00 XMOV_SRC_ADDR       CmdParams[0]  (source, 16B units)
#   0x04 XMOV_DST_ADDR       CmdParams[1]  (destination, 16B units)
#   0x08 XMOV_SIZE           CmdParams[2]  (size, 16B units)
#   0x0C XMOV_DIRECTION      CmdParams[3]  (xmov_direction_t)
#   0x10 COMMAND_ADDR        Trigger — non-compact or compact command
#   0x14 STATUS              Always 0x08 (FIFO_EMPTY) in sync emulation
#   0x24 CLK_GATE_EN         No-op (firmware writes 0x3F during device_setup)
#   0x28 CLK_GATE_HYST       No-op
#   0x2C XMOV_L1_BASE_ADDR   MovCmdBase (compact-command base, 16B units)
#   0x30 FIFO_PACKED_TILE_SIZE(0)      Peek packer-0 FIFO tile size (no pop)
#   0x34 FIFO_PACKED_TILE_ZEROMASK(0)  Pop packer-0 FIFO, return zero-mask
#
# Register-block bus protocol: offsets are relative to TDMA_BASE because the
# Router registers us with offset=TDMA_BASE.
#
# Packer sideband 0x18 / 0x1C (PACKED_SIZE / ACC_PACKED_SIZE) and 0x38
# (FIFO_PACKED_TILE_STATUS) still read 0 — tt-metal's tdma_xmov.c does not
# exercise them, and none of the current kernels depend on the accumulator.
# =============================================================================

# Register offsets within the block.
_XMOV_SRC_ADDR   = 0x00
_XMOV_DST_ADDR   = 0x04
_XMOV_SIZE       = 0x08
_XMOV_DIRECTION  = 0x0C
_COMMAND_ADDR    = 0x10
_STATUS          = 0x14
_CLK_GATE_EN     = 0x24
_CLK_GATE_HYST   = 0x28
_XMOV_L1_BASE    = 0x2C

# STATUS bits — we always report "idle, queue empty" because transfers
# complete synchronously on write to COMMAND_ADDR.
_STATUS_IDLE = 0x08

# Command opcodes recognised by the command processor.
_CMD_MOVER = 0x40
_CMD_NOP   = 0x89


class TDMA:
  def __init__(self, mover, packer=None):
    self.mover = mover
    # Packer is optional — only needed to service the FIFO_PACKED_TILE_*
    # sideband registers at 0x30 / 0x34.  Lets tests skip wiring a full packer
    # when they only exercise the XMOV MMIO path.
    self.packer = packer
    # CmdParams[0..3]: src, dst, size, direction (all in 16B units except dir).
    self.cmd_params = [0, 0, 0, 0]
    # MovCmdBase for compact commands (16B units).
    self.l1_base = 0

  # ---- bus handler protocol --------------------------------------------------
  # The Router calls these with address relative to TDMA_BASE.  TDMA registers
  # are 32-bit; byte/half-word access is not used by real firmware but we
  # provide trivial aliases so accidental narrow access does not crash.

  def read32(self, addr):
    match addr:
      case 0x14:            return _STATUS_IDLE    # STATUS
      case 0x2C:            return self.l1_base    # XMOV_L1_BASE_ADDR
      case 0x30:
        # FIFO_PACKED_TILE_SIZE(0) — peek packer-0's completed-tile FIFO.
        # Reads do not pop; pop happens on the 0x34 read.
        return self.packer.peek_packed_tile_size(0) if self.packer else 0
      case 0x34:
        # FIFO_PACKED_TILE_ZEROMASK(0) — pop one entry, return its zero-mask.
        return self.packer.pop_packed_tile_zeromask(0) if self.packer else 0
      case _:               return 0

  def write32(self, addr, val):
    val &= 0xFFFFFFFF
    match addr:
      case 0x00: self.cmd_params[0] = val                 # XMOV_SRC_ADDR
      case 0x04: self.cmd_params[1] = val                 # XMOV_DST_ADDR
      case 0x08: self.cmd_params[2] = val                 # XMOV_SIZE
      case 0x0C: self.cmd_params[3] = val                 # XMOV_DIRECTION
      case 0x10: self._execute_command(val)               # COMMAND_ADDR
      case 0x24 | 0x28:      pass                         # clock-gate: no-op
      case 0x2C: self.l1_base = val                       # XMOV_L1_BASE_ADDR
      case _:                pass                         # status / packer sideband / unused

  def read8(self, addr):   return (self.read32(addr & ~3) >> (8 * (addr & 3))) & 0xFF
  def read16(self, addr):  return (self.read32(addr & ~3) >> (8 * (addr & 3))) & 0xFFFF
  def write8(self, addr, val):  pass
  def write16(self, addr, val): pass

  # ---- command decode --------------------------------------------------------

  def _execute_command(self, word):
    if word & (1 << 31):
      # Compact command: all parameters packed in the 32-bit write.
      opcode    = word & 0xFF
      if opcode != _CMD_MOVER: return          # compact-NOP or unknown
      src_off   = (word >> 8)  & 0xFF
      dst_16b   = (word >> 16) & 0xFF
      size_16b  = (word >> 24) & 0x3F
      direction = (word >> 30) & 0x1           # 0 = L1→CFG, 1 = L1→L1
      # Compact dir encoding: 0=L1→CFG (XMOV_L1_TO_L0=1), 1=L1→L1 (=3).
      direction = 3 if direction else 1
      src_byte  = (self.l1_base + src_off) << 4
      dst_byte  = dst_16b << 4
      size_byte = size_16b << 4
      self.mover.transfer(dst_byte, src_byte, size_byte, direction)
      return

    # Non-compact: low byte is the command opcode; mover_number is in [15:8]
    # but we have only one functional Mover, so it is ignored.
    opcode = word & 0xFF
    if opcode == _CMD_MOVER:
      src  = self.cmd_params[0] << 4
      dst  = self.cmd_params[1] << 4
      size = self.cmd_params[2] << 4
      direction = self.cmd_params[3]
      self.mover.transfer(dst, src, size, direction)
    # _CMD_NOP (0x89), mover wait/flush (0x46), L1 write (0x66): not exercised
    # by any test; treat as no-ops.
