class Ops:
  """Cross-engine tile operations."""

  _BF16_ONE = b"\x80\x3f"
  _BF16_NEG_ONE = b"\x80\xbf"

  def __init__(self, program, unpack, fpu, pack):
    self.program = program
    self.unpack = unpack
    self.fpu = fpu
    self.pack = pack
    self._unit_scaler = None
    self._negative_tile = None
    self._negative_scaler = None

  def _unit_scaler_address(self):
    if self._unit_scaler is None:
      # GAPOOL consumes four 16-value weight rows per face. Keep one compact
      # four-face scaler in local L1 and never expose it as a user buffer.
      self._unit_scaler = self.program.l1_constant(self._BF16_ONE * 4 * 16 * 4)
    return self._unit_scaler

  def _reduce_scalar(self, input_cb, output_cb, *, dst_tile, maximum):
    self.unpack.move_reduce(input_cb, self._unit_scaler_address())
    self.fpu.pool_scalar(dst_tile=dst_tile, maximum=maximum).publish()
    self.pack.move_scalar(output_cb, tile=dst_tile)
    return self

  def _negative_tile_address(self):
    if self._negative_tile is None:
      self._negative_tile = self.program.l1_constant(
        self._BF16_NEG_ONE * 32 * 32,
      )
    return self._negative_tile

  def _negative_scaler_address(self):
    if self._negative_scaler is None:
      # GMPOOL consumes the leading scaler rows. ELWMUL works in eight-row
      # blocks, so retain -1 in the otherwise-unused second half of each face.
      face = self._BF16_ONE * 8 * 16 + self._BF16_NEG_ONE * 8 * 16
      self._negative_scaler = self.program.l1_constant(face * 4)
    return self._negative_scaler

  def _negated_tile_cb(self, dtype):
    return self.program.cb.internal(
      "ops.reduce_min.negated", dtype, depth=1,
    )

  def reduce_sum(self, input_cb, output_cb, *, dst_tile=0):
    return self._reduce_scalar(
      input_cb, output_cb, dst_tile=dst_tile, maximum=False,
    )

  def reduce_max(self, input_cb, output_cb, *, dst_tile=0):
    return self._reduce_scalar(
      input_cb, output_cb, dst_tile=dst_tile, maximum=True,
    )

  def reduce_min(self, input_cb, output_cb, *, dst_tile=0):
    """Reduce a BF16 tile as -max(-x), leaving the scalar at Dst[0, 0]."""
    negated_cb = self._negated_tile_cb(input_cb.dtype)
    negative_tile = self._negative_tile_address()

    # Materialize -x in an operation-owned CB so the next unpack can present
    # it to GMPOOL as a fresh SrcA tile.
    self.unpack.move_l1_pair(input_cb, negative_tile)
    self.fpu.mul(dst_tile=dst_tile).publish()
    self.pack.move(negated_cb, tile=dst_tile)

    # Pool max(-x), then use the retained -1 rows for the final FPU multiply.
    self.unpack.move_reduce(
      negated_cb, self._negative_scaler_address(), scaler_rows=16,
    )
    self.fpu.pool_scalar(
      dst_tile=dst_tile, maximum=True, negate=True,
    ).publish()
    self.pack.move_scalar(output_cb, tile=dst_tile)
    return self
