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
import os
from pathlib import Path
import struct


_ITEM_SIZES = {
  "BOOL": 1,
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
  def __init__(self, path="weights/model.safetensors"):
    self.path = Path(path)
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
    info = self.info(name)
    with self.path.open("rb") as file:
      file.seek(self.data_start + info.start)
      data = file.read(info.nbytes)
    if len(data) != info.nbytes:
      raise ValueError(f"{self.path} ended while reading tensor {name!r}")
    return info, data

  def readinto(self, name, destination):
    info = self.info(name)
    view = memoryview(destination).cast("B")
    if view.nbytes != info.nbytes:
      raise ValueError(
        f"tensor {name!r} has {info.nbytes} bytes, destination has {view.nbytes}",
      )
    offset = self.data_start + info.start
    with self.path.open("rb", buffering=0) as file:
      while view:
        count = os.preadv(file.fileno(), (view,), offset)
        if count == 0:
          raise ValueError(f"{self.path} ended while reading tensor {name!r}")
        view = view[count:]
        offset += count
    return info


def load(name, path="weights/model.safetensors"):
  return Safetensor(path).load(name)


def readinto(name, destination, path="weights/model.safetensors"):
  return Safetensor(path).readinto(name, destination)


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("name")
  parser.add_argument("--path", default="weights/model.safetensors")
  args = parser.parse_args()
  info, data = load(args.name, args.path)
  print(f"{info.name}: {info.dtype}{list(info.shape)}, {len(data)} bytes")
