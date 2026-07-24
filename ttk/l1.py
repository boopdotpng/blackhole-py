"""Scalar access to tiles that live in L1.

A 32x32 tile is stored as four 16x16 faces in TL, TR, BL, BR order, so the
logical (row, column) of an element is not where it physically sits.  These
helpers emit the index math once, letting a kernel address a run of tiles as
if it were a flat row-major array of `tile_count * 1024` elements.
"""

from isa import R
from ttk import DType

TILE_SIDE = 32
FACE_SIDE = 16
TILE_ELEMENTS = TILE_SIDE * TILE_SIDE


def _shift(dtype):
  if dtype.itemsize == 2: return 1
  if dtype.itemsize == 4: return 2
  raise ValueError(f"L1 element access needs a 2 or 4 byte dtype, got {dtype}")


def element_address(kernel, base, index, address, dtype=DType.U32, exclude=()):
  """address = L1 address of logical element `index` in the tiles at `base`."""
  shift = _shift(dtype)
  with kernel.scope():
    if isinstance(exclude, R): exclude = (exclude,)
    within, row, column, scratch = kernel.reg(
      4, exclude=(index, address, *exclude),
    )
    kernel.andi(within, index, TILE_ELEMENTS - 1)
    kernel.sub(address, index, within)      # elements in the preceding tiles
    kernel.srli(row, within, 5)
    kernel.andi(column, within, TILE_SIDE - 1)

    kernel.srli(scratch, row, 4)
    kernel.slli(scratch, scratch, 9)        # bottom faces start 512 elements in
    kernel.add(address, address, scratch)
    kernel.srli(scratch, column, 4)
    kernel.slli(scratch, scratch, 8)        # right faces start 256 elements in
    kernel.add(address, address, scratch)
    kernel.andi(scratch, row, FACE_SIDE - 1)
    kernel.slli(scratch, scratch, 4)
    kernel.add(address, address, scratch)
    kernel.andi(scratch, column, FACE_SIDE - 1)
    kernel.add(address, address, scratch)

    kernel.slli(address, address, shift)    # elements -> bytes
    if isinstance(base, R): kernel.add(address, address, base)
    else:
      kernel.li(scratch, base)
      kernel.add(address, address, scratch)
  return address


def load(kernel, base, index, output, dtype=DType.U32):
  """output = tiles_at_base[index], indexing elements in row-major order."""
  with kernel.scope():
    address = kernel.reg(exclude=(index, output))
    element_address(kernel, base, index, address, dtype, exclude=(output,))
    kernel.read(output, address, bytes=dtype.itemsize)
  return kernel


def store(kernel, base, index, value, dtype=DType.U32):
  """tiles_at_base[index] = value, indexing elements in row-major order."""
  with kernel.scope():
    address = kernel.reg(exclude=(index, value))
    element_address(kernel, base, index, address, dtype, exclude=(value,))
    kernel.write(address, value, bytes=dtype.itemsize)
  return kernel


def copy_words(kernel, source_base, target_base, words, *, source_offset=None):
  """Copy `words` 32-bit words between two L1 regions, one word per iteration."""
  with kernel.scope():
    source, target, remaining, value = kernel.reg(4)
    if isinstance(source_base, R): kernel.mv(source, source_base)
    else: kernel.li(source, source_base)
    if isinstance(source_offset, R): kernel.add(source, source, source_offset)
    elif source_offset: kernel.addi(source, source, source_offset)
    if isinstance(target_base, R): kernel.mv(target, target_base)
    else: kernel.li(target, target_base)
    kernel.li(remaining, words)
    loop, done = kernel._new_label("l1_copy"), kernel._new_label("l1_copy_done")
    kernel.label(loop)
    kernel.beq(remaining, R.ZERO, done)
    kernel.lw(value, source)
    kernel.sw(value, target)
    kernel.addi(source, source, 4)
    kernel.addi(target, target, 4)
    kernel.addi(remaining, remaining, -1)
    kernel.j(loop)
    kernel.label(done)
  return kernel
