from dataclasses import dataclass

import numpy as np
import struct

from ttk.addrs import Dram, align_up
from pcie import NocOrdering, TLBWindow
from program import Dtype

Shape = tuple[int, ...]
TILE_R, TILE_C, FACE_R, FACE_C = 32, 32, 16, 16

def _np_dtype(bpe: int) -> np.dtype: return {2: np.dtype('uint16'), 4: np.dtype('uint32')}[bpe]

def tilize(data: bytes, bpe: int, shape: Shape) -> bytes:
  rows, cols = shape[-2], shape[-1]
  assert rows % TILE_R == 0 and cols % TILE_C == 0
  batch = 1
  for d in shape[:-2]: batch *= d
  dt = _np_dtype(bpe)
  a = np.frombuffer(data, dtype=dt).reshape(batch, rows // TILE_R, TILE_R, cols // TILE_C, TILE_C)
  a = a.transpose(0, 1, 3, 2, 4)                                    # grid: (b, tr, tc, 32, 32)
  a = a.reshape(-1, 2, FACE_R, 2, FACE_C).transpose(0, 1, 3, 2, 4) # face: (n_tiles, 2, 2, 16, 16)
  return a.tobytes()

def untilize(data: bytes, bpe: int, shape: Shape) -> bytes:
  rows, cols = shape[-2], shape[-1]
  assert rows % TILE_R == 0 and cols % TILE_C == 0
  batch = 1
  for d in shape[:-2]: batch *= d
  tr, tc = rows // TILE_R, cols // TILE_C
  dt = _np_dtype(bpe)
  a = np.frombuffer(data, dtype=dt).reshape(-1, 2, 2, FACE_R, FACE_C)
  a = a.transpose(0, 1, 3, 2, 4).reshape(batch, tr, tc, TILE_R, TILE_C)
  a = a.transpose(0, 1, 3, 2, 4).reshape(batch, rows, cols)
  return a.tobytes()

@dataclass
class DramBuffer:
  name: str
  addr: int
  num_tiles: int
  dtype: Dtype
  shape: Shape | None = None

  @property
  def page_size(self) -> int: return self.dtype.tile_size

  @property
  def size(self) -> int: return self.num_tiles * self.page_size

class Allocator:
  def __init__(self, dev, bank_tiles: list):
    self.dev = dev
    self.bank_tiles = bank_tiles[:: Dram.TILES_PER_BANK]
    self.win: TLBWindow | None = None
    self.next = Dram.WRITE_OFFSET

  def _win(self) -> TLBWindow:
    if self.win is None:
      self.win = TLBWindow(self.dev, start=self.bank_tiles[0][1:], size=TLBWindow.SIZE_4G, wc=True)
    return self.win

  def alloc(self, num_tiles: int, dtype: Dtype, name: str = "", shape: Shape | None = None) -> DramBuffer:
    num_banks = len(self.bank_tiles)
    pages_per_bank = (num_tiles + num_banks - 1) // num_banks
    addr = self.next
    self.next = align_up(addr + pages_per_bank * dtype.tile_size, Dram.ALIGNMENT)
    return DramBuffer(name=name, addr=addr, num_tiles=num_tiles, dtype=dtype, shape=shape)

  def barrier(self):
    win = self._win()
    for flag in Dram.BARRIER_FLAGS:
      for _, x, y in self.bank_tiles:
        win.target((x, y))
        win.write(Dram.BARRIER_BASE, struct.pack("<I", flag))
        while struct.unpack("<I", win.read(Dram.BARRIER_BASE, 4))[0] != flag:
          pass

  def write(self, buf: DramBuffer, data: bytes):
    remote_write = getattr(self.dev, "dram_write", None)
    if remote_write is not None:
      remote_write(self.bank_tiles, buf, data)
      return
    assert len(data) <= buf.size
    win = self._win()
    view, ps, nb = memoryview(data), buf.page_size, len(self.bank_tiles)
    n_pages = (len(data) + ps - 1) // ps
    for bi, (_, x, y) in enumerate(self.bank_tiles):
      bank_data = b''.join(bytes(view[p * ps : p * ps + ps]) for p in range(bi, n_pages, nb))
      if not bank_data: continue
      win.target((x, y), mode=NocOrdering.POSTED)
      win.write(buf.addr, bank_data)
    self.barrier()

  def read(self, buf: DramBuffer) -> bytes:
    remote_read = getattr(self.dev, "dram_read", None)
    if remote_read is not None:
      return remote_read(self.bank_tiles, buf)
    win = self._win()
    result, ps, nb = bytearray(buf.size), buf.page_size, len(self.bank_tiles)
    n_pages = (buf.size + ps - 1) // ps
    for bi, (_, x, y) in enumerate(self.bank_tiles):
      bank_pages = list(range(bi, n_pages, nb))
      if not bank_pages: continue
      win.target((x, y), mode=NocOrdering.RELAXED)
      bank_data = win.read(buf.addr, len(bank_pages) * ps)
      for i, p in enumerate(bank_pages):
        n = min(ps, buf.size - p * ps)
        result[p * ps : p * ps + n] = bank_data[i * ps : i * ps + n]
    return bytes(result)

  def close(self):
    if self.win is not None:
      self.win.close()
      self.win = None
