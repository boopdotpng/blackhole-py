from ttk import DType
from ttk.fpu import Broadcast
from ttk.sfpu import SfpuFormat


class Ops:
  _BF16_ONE = b"\x80\x3f"
  _BF16_ZERO = b"\0\0"
  _BF16_NEG_ONE = b"\x80\xbf"

  def __init__(self, program, unpack, fpu, sfpu, pack):
    self.program = program
    self.unpack = unpack
    self.fpu = fpu
    self.sfpu = sfpu
    self.pack = pack

  def rand_fast(self, *, seed=0, dst_tile=0):
    output_cb = self.program.cb.internal(
      "ops.rand_fast.output", DType.BF16, depth=1,
    )
    builder = self.sfpu.program()
    value = builder.rand_fast()
    builder.store(value, format=SfpuFormat.BF16)
    self.sfpu.seed(seed)
    self.sfpu.map(builder.finish(), tile=dst_tile).publish()
    self.pack.move(output_cb, tile=dst_tile)
    return output_cb

  def _unit_scaler_address(self):
    # GAPOOL consumes four 16-value weight rows per face. Keep one compact
    # four-face scaler in local L1 and never expose it as a user buffer.
    return self.program.l1_constant(self._BF16_ONE * 4 * 16 * 4)

  def _row_scaler_address(self):
    # The row reducer halo-transposes row 0 of each physical scaler face
    # into the MVMUL column. GMPOOL also requires a valid SrcB row of ones.
    face = self._BF16_ONE * 16 + self._BF16_ZERO * (16 * 15)
    return self.program.l1_constant(face * 4)

  def reduce(self, input_cb, output_cb, *, dst_tile=0, maximum=False):
    self.unpack.move_reduce(input_cb, self._unit_scaler_address())
    self.fpu.pool_scalar(dst_tile=dst_tile, maximum=maximum).publish()
    self.pack.move_scalar(output_cb, tile=dst_tile)
    return self

  def accumulate_rows(self, input_cb, *, dst_tile=0, maximum=False):
    self.unpack.move_row_reduce(
      input_cb, self._row_scaler_address(), maximum=maximum,
    )
    reduce = self.fpu.reduce_row_max if maximum else self.fpu.reduce_row_sum
    reduce(dst_tile=dst_tile)
    return self

  def reduce_rows(self, input_cb, output_cb, *, dst_tile=0, maximum=False):
    self.accumulate_rows(
      input_cb, dst_tile=dst_tile, maximum=maximum,
    )
    self.fpu.publish()
    self.pack.move(output_cb, tile=dst_tile)
    return self

  def _negative_tile_address(self):
    return self.program.l1_constant(self._BF16_NEG_ONE * 32 * 32)

  def _negative_scaler_address(self):
    # GMPOOL consumes the leading scaler rows. ELWMUL works in eight-row
    # blocks, so retain -1 in the otherwise-unused second half of each face.
    face = self._BF16_ONE * 8 * 16 + self._BF16_NEG_ONE * 8 * 16
    return self.program.l1_constant(face * 4)

  def store_row_values(self, output_cb, *, dst_tile=0):
    self.fpu.publish()
    self.pack.move(output_cb, tile=dst_tile)
    return self

  def binary_rows(self, input_cb, row_values_cb, output_cb, *,
                  operation, dst_tile=0):
    # row_values_cb stores its 32 values in logical column 0. The unpacker
    # visits only the two physical faces containing that column.
    self.unpack.move_pair_rows(input_cb, row_values_cb)
    self.fpu.binary(operation, dst_tile=dst_tile, broadcast=Broadcast.COLUMN).publish()
    self.pack.move(output_cb, tile=dst_tile)
    return self

  def reduce_min(self, input_cb, output_cb, *, dst_tile=0):
    negated_cb = self.program.cb.internal("ops.reduce_min.negated", input_cb.dtype)
    negative_tile = self._negative_tile_address()

    # Materialize -x in an operation-owned CB so the next unpack can present
    # it to GMPOOL as a fresh SrcA tile.
    self.unpack.move_l1_pair(input_cb, negative_tile)
    self.fpu.binary("mul", dst_tile=dst_tile).publish()
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
