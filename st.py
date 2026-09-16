"""Small dependency-free safetensors reader.

The format is:
  u64 little-endian JSON header length
  JSON header (space padded)
  packed tensor bytes

Tensor data offsets in the JSON are relative to the end of the header.
"""

from dataclasses import dataclass
import json
from math import prod
from pathlib import Path
import struct


_ITEM_SIZES = {
  "BOOL": 1,
  "F8_E4M3": 1,
  "F8_E5M2": 1,
  "I8": 1,
  "U8": 1,
  "I16": 2,
  "U16": 2,
  "BF16": 2,
  "F16": 2,
  "I32": 4,
  "U32": 4,
  "F32": 4,
  "F64": 8,
  "I64": 8,
  "U64": 8,
}


@dataclass(frozen=True)
class TensorInfo:
  name: str
  dtype: str
  shape: tuple[int, ...]
  start: int
  end: int

  @property
  def nbytes(self): return self.end - self.start


class Safetensor:
  def __init__(self, path="weights/llama3-1b/model.safetensors"):
    self.path = Path(path)
    self.shards = None
    if self.path.is_dir():
      index = self.path / "model.safetensors.index.json"
      if not index.exists():
        self.__init__(self.path / "model.safetensors")
        return
      record = json.loads(index.read_text())
      weight_map = record["weight_map"]
      readers = {}
      self.shards, self.tensors = {}, {}
      self.metadata = record.get("metadata", {})
      for name, filename in weight_map.items():
        shard = (self.path / filename).resolve()
        if shard.parent != self.path.resolve():
          raise ValueError(f"invalid shard filename: {filename!r}")
        if filename not in readers:
          readers[filename] = Safetensor(shard)
        reader = readers[filename]
        self.shards[name] = reader
        self.tensors[name] = reader.info(name)
      return
    file_size = self.path.stat().st_size
    with self.path.open("rb") as file:
      prefix = file.read(8)
      if len(prefix) != 8:
        raise ValueError(f"{self.path} is too short to be a safetensors file")
      header_size = struct.unpack("<Q", prefix)[0]
      if header_size < 2 or 8 + header_size > file_size:
        raise ValueError(f"{self.path} has an invalid header size {header_size}")
      try:
        header = json.loads(file.read(header_size))
      except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{self.path} has an invalid JSON header") from error

    if not isinstance(header, dict):
      raise ValueError(f"{self.path} safetensors header is not an object")
    self.metadata = header.pop("__metadata__", {})
    self.data_start = 8 + header_size
    data_size = file_size - self.data_start
    tensors = {}
    ranges = []
    for name, record in header.items():
      if not isinstance(name, str) or not isinstance(record, dict):
        raise ValueError(f"{self.path} has an invalid tensor record")
      try:
        dtype = record["dtype"]
        shape = tuple(record["shape"])
        start, end = record["data_offsets"]
      except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{self.path} has an invalid record for {name!r}") from error
      if dtype not in _ITEM_SIZES:
        raise ValueError(f"{self.path} tensor {name!r} has unknown dtype {dtype!r}")
      if (
        any(type(dim) is not int or dim < 0 for dim in shape) or
        type(start) is not int or type(end) is not int or
        not 0 <= start <= end <= data_size
      ):
        raise ValueError(f"{self.path} tensor {name!r} has invalid shape or offsets")
      expected = prod(shape) * _ITEM_SIZES[dtype]
      if end - start != expected:
        raise ValueError(
          f"{self.path} tensor {name!r} has {end-start} bytes, expected {expected}",
        )
      info = TensorInfo(name, dtype, shape, start, end)
      tensors[name] = info
      ranges.append((start, end, name))

    previous_end = 0
    for start, end, name in sorted(ranges):
      if start < previous_end:
        raise ValueError(f"{self.path} tensor {name!r} overlaps another tensor")
      previous_end = end
    self.tensors = tensors

  def info(self, name):
    try: return self.tensors[name]
    except KeyError as error:
      raise KeyError(f"tensor {name!r} is not in {self.path}") from error

  def load(self, name):
    if self.shards is not None:
      self.info(name)
      return self.shards[name].load(name)
    info = self.info(name)
    with self.path.open("rb") as file:
      file.seek(self.data_start + info.start)
      data = file.read(info.nbytes)
    if len(data) != info.nbytes:
      raise ValueError(f"{self.path} ended while reading tensor {name!r}")
    return info, data

  def readinto(self, name, target, offset=0):
    """Read a bounded tensor range directly into a writable staging buffer."""
    if self.shards is not None:
      self.info(name)
      return self.shards[name].readinto(name, target, offset)
    info = self.info(name)
    view = memoryview(target).cast("B")
    if offset < 0 or offset + len(view) > info.nbytes:
      raise ValueError(f"read exceeds tensor {name!r}")
    with self.path.open("rb", buffering=0) as file:
      file.seek(self.data_start + info.start + offset)
      done = 0
      while done < len(view):
        count = file.readinto(view[done:])
        if not count:
          raise ValueError(f"{self.path} ended while reading tensor {name!r}")
        done += count
    return done


def load(name, path="weights/llama3-1b/model.safetensors"):
  return Safetensor(path).load(name)


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("name")
  parser.add_argument("--path", default="weights/llama3-1b/model.safetensors")
  args = parser.parse_args()
  info, data = load(args.name, args.path)
  print(f"{info.name}: {info.dtype}{list(info.shape)}, {len(data)} bytes")
