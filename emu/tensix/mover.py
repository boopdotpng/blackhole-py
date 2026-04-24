# =============================================================================
# Mover — the Tensix DMA engine shared by the XMOV instruction (issued from
# the Tensix thread pipeline) and the TDMA-RISC register block (MMIO-driven
# from any RISC-V core). Implements the four-direction functional model:
#
#   dir=0 (L0→L1): memset(0) into L1
#   dir=1 (L1→L0): memcpy from L1 to CFG space (or NCRISC IRAM — discarded
#                  on Blackhole, which has no NCRISC IRAM)
#   dir=2 (L0→L0): memset(0) into CFG space
#   dir=3 (L1→L1): memcpy within L1
#
# All addresses and sizes are byte quantities; callers (XMOV dispatch /
# TDMA handler) are responsible for converting 16B units to bytes.  The real
# hardware runs asynchronously and drives the C9 wait condition; in the
# functional emulator transfers complete synchronously and C9 is always
# reported clear by frontend.py's WaitGate.
# =============================================================================

# Address ranges used by the dst-is-"L0" direction modes.
TENSIX_CFG_BASE    = 0xFFEF0000
NCRISC_IRAM_LO     = 0x40000
NCRISC_IRAM_HI     = 0x4FFFF


class Mover:
  def __init__(self, l1, cfg, ncrisc_iram=None):
    # l1, cfg, ncrisc_iram are byte-addressed Memory-like objects with
    # read8/write8.  On Blackhole there is no NCRISC IRAM; leave as None
    # and transfers targeting that range are discarded (per spec).
    self.l1 = l1
    self.cfg = cfg
    self.iram = ncrisc_iram

  def transfer(self, dst, src, count, direction):
    """Execute one Mover transfer.  dst/src/count are in bytes."""
    if (dst | src | count) & 0xF:
      # All XMOV transfers must be 16B-aligned.  Real hardware likely
      # misbehaves on unaligned access; the emulator refuses to simulate
      # something undefined.
      raise ValueError(
        f"XMOV 16B alignment: dst=0x{dst:x} src=0x{src:x} count=0x{count:x}")
    if direction in (1, 2):
      # L0-as-destination: resolve to CFG or NCRISC IRAM.
      if dst <= 0xFFFF:
        # Spec quotes dst += TENSIX_CFG_BASE, which names the absolute bus
        # address.  The emulator's cfg Memory stores at *relative* offsets
        # (device.py registers it with offset=TENSIX_CFG_BASE so the Router
        # strips the base on routed accesses), so we write the relative dst
        # directly and it becomes observable at both the absolute bus
        # address and the stored offset.
        self._do(self.cfg, dst, src, count, direction)
      elif NCRISC_IRAM_LO <= dst <= NCRISC_IRAM_HI:
        if self.iram is not None:
          self._do(self.iram, dst - NCRISC_IRAM_LO, src, count, direction)
        # else: no NCRISC IRAM on Blackhole — writes discarded.
      # Any other dst: unmapped, writes discarded (spec).
      return
    # L1 destination (dir 0 or 3).
    self._do(self.l1, dst, src, count, direction)

  def _do(self, dst_mem, dst, src, count, direction):
    if direction in (1, 3):                    # memcpy from L1
      for i in range(count):
        dst_mem.write8(dst + i, self.l1.read8(src + i))
    else:                                      # memset(0)
      for i in range(count):
        dst_mem.write8(dst + i, 0)
