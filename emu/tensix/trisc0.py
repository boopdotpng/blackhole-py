from ..dsl import decode_tensix


class TRISC0Decoder:
  def __init__(self, coproc):
    self.coproc = coproc

  def dispatch(self, word, thread):
    d = decode_tensix(word)
    match d.name:
      case 'UNPACR':     self._unpacr(d)
      case 'UNPACR_NOP': self._unpacr_nop(d)
      case _:            return False
    return True

  def _unpacr(self, d):
    # Bank flip: hand ownership from Unpackers to Matrix Unit
    if d.SetDatValid:
      (self.coproc.srca if d.Unpack_block_selection == 0 else self.coproc.srcb).flip_to_fpu()

  def _unpacr_nop(self, d):
    if d.Set_Dvalid & 1:  # bank flip
      (self.coproc.srca if d.Unpacker_Select == 0 else self.coproc.srcb).flip_to_fpu()
    clr = d.Src_ClrVal_Ctrl
    if clr & 1: self._clear_bank(self.coproc.srca)  # SrcA
    if clr & 2: self._clear_bank(self.coproc.srcb)  # SrcB

  @staticmethod
  def _clear_bank(srcregfile):
    bank = srcregfile.banks[srcregfile.unpack_bank]
    for r in range(64):
      for c in range(16):
        bank.rows[r][c] = 0
