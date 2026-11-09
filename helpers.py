import ctypes, ctypes.util, json, mmap, os, struct
from dataclasses import dataclass
from pathlib import Path

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int64]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

PAGE = mmap.PAGESIZE
def round_up(x:int, n:int) -> int: return -(-x // n) * n
def view_at(addr:int, n:int) -> memoryview:  # n bytes of raw memory at addr, as a writable memoryview
  return memoryview((ctypes.c_uint8 * n).from_address(addr)).cast("B")
def mv_address(buf) -> int:
  return ctypes.addressof(ctypes.c_char.from_buffer(memoryview(buf).cast("B")))
def libc_mmap(size:int, fd:int=-1, offset:int=0, flags:int=mmap.MAP_SHARED, prot:int=mmap.PROT_READ | mmap.PROT_WRITE) -> int:
  if fd == -1: flags |= mmap.MAP_ANONYMOUS
  if (addr := libc.mmap(None, size, prot, flags, fd, offset)) in (None, 2**64 - 1):
    raise OSError(ctypes.get_errno(), f"mmap of {size} bytes failed: {os.strerror(ctypes.get_errno())}")
  return addr
def libc_munmap(addr:int, size:int): libc.munmap(addr, size)

@dataclass(frozen=True)
class Tensor:
  name: str
  dtype: str
  shape: tuple[int, ...]
  path: Path
  offset: int
  nbytes: int
  @property
  def end(self) -> int: return self.offset + self.nbytes

def safe_load(path) -> dict[str, Tensor]:
  path = Path(path)
  if path.suffix == ".json":
    files = sorted(set(json.loads(path.read_text())["weight_map"].values()))
    return {k: v for f in files for k, v in safe_load(path.parent / f).items()}
  with open(path, "rb") as f:
    n, = struct.unpack("<Q", f.read(8))
    header = json.loads(f.read(n))
  header.pop("__metadata__", None)
  return {name: Tensor(name, h["dtype"], tuple(h["shape"]), path, 8 + n + h["data_offsets"][0],
                       h["data_offsets"][1] - h["data_offsets"][0]) for name, h in header.items()}
