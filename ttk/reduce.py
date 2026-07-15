import struct

from program import DType
from ttk.tensix import MopCfg, nop_word, tt_word


def scalar_reduce_mop():
  clear_src_a = tt_word("TTUNPACR_NOP", 0, 0, 0, 0, 0, 0, 0, 0, 1)
  replay_ab = tt_word("TTREPLAY", 0, 2, 0, 0)
  return MopCfg.slots(
    outer=1, inner=4, fill=nop_word(),
    slot3=clear_src_a, slot4=replay_ab,
    slot5=replay_ab, slot6=replay_ab,
  )


SCALAR_REDUCE_MOP = scalar_reduce_mop()


def scalar_reduce_tile(value: float, dtype: DType) -> bytes:
  if dtype is DType.BF16:
    bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
    datum = struct.pack("<H", bits >> 16)
  elif dtype is DType.F32:
    datum = struct.pack("<f", float(value))
  else:
    raise ValueError(f"unsupported scalar-reduce dtype {dtype}")
  tile = bytearray(1024 * dtype.itemsize)
  row = datum * 16
  face_bytes = 256 * dtype.itemsize
  for face in range(4): tile[face * face_bytes:face * face_bytes + len(row)] = row
  return bytes(tile)
