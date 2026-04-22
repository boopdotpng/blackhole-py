# =============================================================================
# T2 (pack) pipeline backend — placeholder.
#
# The real packer reads Dest rows, applies the configured format conversion
# (FP32 -> BF16/FP16/INT8/…), optional ReLU and edge-mask gating, and writes
# the result to L1 driven by the ADC packer channel. None of that is
# emulated today — PACR is a no-op — but the class exists so instruction
# dispatch has a clear home to grow into.
# =============================================================================


class Packer:
  def __init__(self, dest):
    self.dest = dest

  def handle_pacr(self, d):
    # No-op. Real implementation: iterate Dest rows selected by the packer's
    # ADC channel, format-convert to L1 addresses, honour edge mask / ReLU.
    pass
