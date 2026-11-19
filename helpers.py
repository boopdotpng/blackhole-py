import ctypes, ctypes.util, json, math, mmap, os, struct
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
def libc_mmap(size:int, fd:int=-1, offset:int=0, flags:int=mmap.MAP_SHARED, prot:int=mmap.PROT_READ | mmap.PROT_WRITE) -> int:
  if fd == -1: flags |= mmap.MAP_ANONYMOUS
  if (addr := libc.mmap(None, size, prot, flags, fd, offset)) in (None, 2**64 - 1):
    raise OSError(ctypes.get_errno(), f"mmap of {size} bytes failed: {os.strerror(ctypes.get_errno())}")
  return addr
def libc_munmap(addr:int, size:int): libc.munmap(addr, size)

NUMPY = {"F64": "f8", "F32": "f4", "F16": "f2", "I64": "i8", "I32": "i4", "U32": "u4", "I8": "i1", "U8": "u1"}

@dataclass(frozen=True)
class Tensor:
  name: str
  dtype: str
  shape: tuple[int, ...]
  path: Path
  offset: int
  nbytes: int
  def numpy(self):  # a read-only memmap; types numpy lacks (BF16, F8) come back as raw unsigned integers
    import numpy as np
    raw = f"u{self.nbytes // max(1, math.prod(self.shape))}"
    return np.memmap(self.path, NUMPY.get(self.dtype, raw), "r", self.offset, self.shape)

def safe_load(path) -> dict[str, Tensor]:
  """A .safetensors file, a sharded checkpoint's index .json, or a directory holding either."""
  path = Path(path)
  if path.is_dir(): path = next(f for f in (path / "model.safetensors.index.json", path / "model.safetensors") if f.exists())
  if path.suffix == ".json":
    files = sorted(set(json.loads(path.read_text())["weight_map"].values()))
    return {k: v for f in files for k, v in safe_load(path.parent / f).items()}
  with open(path, "rb") as f:
    n, = struct.unpack("<Q", f.read(8))
    header = json.loads(f.read(n))
  header.pop("__metadata__", None)
  return {name: Tensor(name, h["dtype"], tuple(h["shape"]), path, 8 + n + h["data_offsets"][0],
                       h["data_offsets"][1] - h["data_offsets"][0]) for name, h in header.items()}

def tokenizer(path):
  """A Hugging Face byte-level BPE tokenizer.json as a tiktoken Encoding."""
  import tiktoken
  tok = json.loads((path / "tokenizer.json").read_text())
  bs = [*range(33, 127), *range(161, 173), *range(174, 256)]  # GPT-2 byte-level BPE writes bytes as these characters
  byte = {chr(b): b for b in bs} | {chr(256 + i): b for i, b in enumerate(b for b in range(256) if b not in bs)}
  return tiktoken.Encoding("llama3", pat_str=tok["pre_tokenizer"]["pretokenizers"][0]["pattern"]["Regex"],
                           mergeable_ranks={bytes(byte[c] for c in k): v for k, v in tok["model"]["vocab"].items()},
                           special_tokens={t["content"]: t["id"] for t in tok["added_tokens"]})
