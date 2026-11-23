import json, math, struct
from dataclasses import dataclass
from pathlib import Path

NUMPY = {"F64": "f8", "F32": "f4", "F16": "f2", "I64": "i8", "I32": "i4", "U32": "u4", "I8": "i1", "U8": "u1"}

@dataclass(frozen=True)
class Tensor:
  name: str
  dtype: str
  shape: tuple[int, ...]
  path: Path
  offset: int
  nbytes: int
  packed_format: str | None = None

  @property
  def logical_shape(self):
    """HF weight shape [output, input] for transposed, face-packed projection tiles."""
    return (32 * self.shape[1], 32 * self.shape[0]) if self.packed_format else self.shape

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
  metadata = header.pop("__metadata__", {})
  packed = json.loads(metadata.get("blackhole.formats", "{}"))
  if packed and (metadata.get("blackhole.layout") != "kn_tiles_32x32_v1" or not packed.keys() <= header.keys()):
    raise ValueError(f"{path}: invalid packed weight metadata")
  tensors = {}
  for name, h in header.items():
    start, end = h["data_offsets"]
    shape = tuple(h["shape"])
    fmt = packed.get(name)
    if name in packed and (fmt not in ("bfp4_b", "bfp8_b") or h["dtype"] != "U8" or len(shape) != 3
                           or shape[2] != (576 if fmt == "bfp4_b" else 1088) or end - start != math.prod(shape)):
      raise ValueError(f"{path}: invalid packed tensor {name}")
    tensors[name] = Tensor(name, h["dtype"], shape, path, 8 + n + start, end - start, fmt)
  return tensors

def rope(cfg, head_dim, length):
  """cos and sin [length, head_dim] in float32 as HF has them, sin negated in each first half."""
  import numpy as np
  inv = 1 / cfg["rope_theta"] ** (np.arange(0, head_dim, 2, dtype=np.float32) / head_dim)
  angle = np.tile(np.arange(length, dtype=np.float32)[:, None] * inv.astype(np.float32), 2)
  return np.cos(angle), np.sin(angle) * np.repeat(np.float32([-1, 1]), head_dim // 2)
