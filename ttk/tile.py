"""Host-side conversion between row-major 32x32 tiles and four 16x16 faces."""


def tilize(tile: bytes, itemsize: int) -> bytes:
  if type(itemsize) is not int or itemsize <= 0:
    raise ValueError("tile item size must be positive")
  if len(tile) != 32 * 32 * itemsize:
    raise ValueError("tilize expects exactly one 32x32 tile")
  output = bytearray(len(tile))
  write = 0
  row_bytes = 32 * itemsize
  face_row_bytes = 16 * itemsize
  for face_row in range(2):
    for face_column in range(2):
      for row in range(16):
        read = (face_row * 16 + row) * row_bytes + face_column * face_row_bytes
        output[write:write + face_row_bytes] = tile[read:read + face_row_bytes]
        write += face_row_bytes
  return bytes(output)


def untilize(tile: bytes, itemsize: int) -> bytes:
  if type(itemsize) is not int or itemsize <= 0:
    raise ValueError("tile item size must be positive")
  if len(tile) != 32 * 32 * itemsize:
    raise ValueError("untilize expects exactly one 32x32 tile")
  output = bytearray(len(tile))
  read = 0
  row_bytes = 32 * itemsize
  face_row_bytes = 16 * itemsize
  for face_row in range(2):
    for face_column in range(2):
      for row in range(16):
        write = (face_row * 16 + row) * row_bytes + face_column * face_row_bytes
        output[write:write + face_row_bytes] = tile[read:read + face_row_bytes]
        read += face_row_bytes
  return bytes(output)
