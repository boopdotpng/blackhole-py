from ..dsl import decode_tensix


class TRISC2Decoder:
  def __init__(self, coproc):
    self.coproc = coproc

  def dispatch(self, word, thread):
    d = decode_tensix(word)
    match d.name:
      case 'PACR': self._pacr(d)
      case _:      return False
    return True

  def _pacr(self, d):
    # Functional emulation: the pack operation would read from Dest and
    # write to L1. We don't model the packer output path — a complete
    # implementation would compute Dest read address from ADC + packer
    # state, read 16x16 from Dest, convert to target format
    # (BFP8/BF16/FP16/etc.), apply edge mask/ReLU/exponent threshold,
    # assemble BFP shared exponents if needed, write 16-byte aligned
    # blocks to L1, and RMW-accumulate if Pack_L1_Acc is set.
    pass
