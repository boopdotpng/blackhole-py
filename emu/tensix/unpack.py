# =============================================================================
# T0 (unpack) pipeline backend — placeholder.
#
# The real unpacker pulls tile data from L1, applies the configured data
# format conversion, and writes rows into SrcA/SrcB, flipping the unpack
# bank over to the FPU when done. None of that data path is emulated yet;
# this file only carries the bank-ownership side effects of UNPACR/UNPACR_NOP
# so the WaitGate's SrcA/SrcB valid conditions (C5–C8) sequence correctly.
#
# When the real unpacker lands it belongs here: L1 reads, format conversion,
# row stride / face iteration driven by the ADC unpacker channels, and the
# strip-mining that fills 16×16 faces into the 64×16 Src banks.
# =============================================================================


def _clear_src_bank(srcregfile):
  bank = srcregfile.banks[srcregfile.unpack_bank]
  for r in range(64):
    for c in range(16):
      bank.rows[r][c] = 0


class Unpacker:
  def __init__(self, srca, srcb):
    self.srca = srca
    self.srcb = srcb

  def handle_unpacr(self, d):
    # Real unpacker would read L1 + write Src rows here; we only mirror the
    # bank flip so SrcA/SrcB ownership transitions are observable.
    if d.SetDatValid:
      (self.srca if d.Unpack_block_selection == 0 else self.srcb).flip_to_fpu()

  def handle_unpacr_nop(self, d):
    if d.Set_Dvalid & 1:
      (self.srca if d.Unpacker_Select == 0 else self.srcb).flip_to_fpu()
    clr = d.Src_ClrVal_Ctrl
    if clr & 1: _clear_src_bank(self.srca)
    if clr & 2: _clear_src_bank(self.srcb)
