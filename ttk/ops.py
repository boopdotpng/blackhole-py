from ttk.fpu import Broadcast


class Ops:
  """Cross-engine tile operations."""

  _BF16_ONE = b"\x80\x3f"
  _BF16_ZERO = b"\0\0"
  _BF16_NEG_ONE = b"\x80\xbf"

  def __init__(self, program, unpack, fpu, pack):
    self.program = program
    self.unpack = unpack
    self.fpu = fpu
    self.pack = pack
    self._unit_scaler = None
    self._row_scaler = None
    self._negative_tile = None
    self._negative_scaler = None

  def _unit_scaler_address(self):
    if self._unit_scaler is None:
      # GAPOOL consumes four 16-value weight rows per face. Keep one compact
      # four-face scaler in local L1 and never expose it as a user buffer.
      self._unit_scaler = self.program.l1_constant(self._BF16_ONE * 4 * 16 * 4)
    return self._unit_scaler

  def _row_scaler_address(self):
    if self._row_scaler is None:
      # The row reducer halo-transposes row 0 of each physical scaler face
      # into the MVMUL column. GMPOOL also requires a valid SrcB row of ones.
      face = self._BF16_ONE * 16 + self._BF16_ZERO * (16 * 15)
      self._row_scaler = self.program.l1_constant(face * 4)
    return self._row_scaler

  def _reduce_scalar(self, input_cb, output_cb, *, dst_tile, maximum):
    self.unpack.move_reduce(input_cb, self._unit_scaler_address())
    self.fpu.pool_scalar(dst_tile=dst_tile, maximum=maximum).publish()
    self.pack.move_scalar(output_cb, tile=dst_tile)
    return self

  def _accumulate_rows(self, input_cb, *, dst_tile, maximum):
    self.unpack.move_row_reduce(
      input_cb, self._row_scaler_address(), maximum=maximum,
    )
    reduce = self.fpu.reduce_row_max if maximum else self.fpu.reduce_row_sum
    reduce(dst_tile=dst_tile)
    return self

  def _reduce_row(self, input_cb, output_cb, *, dst_tile, maximum):
    self._accumulate_rows(
      input_cb, dst_tile=dst_tile, maximum=maximum,
    )
    self.fpu.publish()
    self.pack.move(output_cb, tile=dst_tile)
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

  def row_sum(self, input_cb, output_cb, *, dst_tile=0):
    """Reduce one tile's rows; output column 0 holds the 32 sums."""
    return self._reduce_row(
      input_cb, output_cb, dst_tile=dst_tile, maximum=False,
    )

  def row_max(self, input_cb, output_cb, *, dst_tile=0):
    """Reduce one tile's rows; output column 0 holds the 32 maxima."""
    return self._reduce_row(
      input_cb, output_cb, dst_tile=dst_tile, maximum=True,
    )

  def accumulate_row_sum(self, input_cb, *, dst_tile=0):
    """Accumulate one tile's 32 logical row sums into a live Dst tile."""
    return self._accumulate_rows(
      input_cb, dst_tile=dst_tile, maximum=False,
    )

  def accumulate_row_max(self, input_cb, *, dst_tile=0):
    """Accumulate one tile's 32 logical row maxima into a live Dst tile."""
    return self._accumulate_rows(
      input_cb, dst_tile=dst_tile, maximum=True,
    )

  def store_row_values(self, output_cb, *, dst_tile=0):
    """Publish and pack live row values; only column 0 is specified."""
    self.fpu.publish()
    self.pack.move(output_cb, tile=dst_tile)
    return self

  def _binary_rows(self, input_cb, row_values_cb, output_cb, *,
                   dst_tile, operation):
    # row_values_cb stores its 32 values in logical column 0. The unpacker
    # visits only the two physical faces containing that column.
    self.unpack.move_pair_rows(input_cb, row_values_cb)
    getattr(self.fpu, operation)(
      dst_tile=dst_tile, broadcast=Broadcast.COLUMN,
    ).publish()
    self.pack.move(output_cb, tile=dst_tile)
    return self

  def add_rows(self, input_cb, row_values_cb, output_cb, *, dst_tile=0):
    return self._binary_rows(
      input_cb, row_values_cb, output_cb,
      dst_tile=dst_tile, operation="add",
    )

  def sub_rows(self, input_cb, row_values_cb, output_cb, *, dst_tile=0):
    return self._binary_rows(
      input_cb, row_values_cb, output_cb,
      dst_tile=dst_tile, operation="sub",
    )

  def mul_rows(self, input_cb, row_values_cb, output_cb, *, dst_tile=0):
    return self._binary_rows(
      input_cb, row_values_cb, output_cb,
      dst_tile=dst_tile, operation="mul",
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
