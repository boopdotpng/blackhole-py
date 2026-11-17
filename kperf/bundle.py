"""kperf bundle files (kperf/bundles/<name>.kperf).

A bundle is one gzip stream of:  b"KPRF" | u32 header length | header JSON | pad to 4 | arrays
The header is everything the viewer needs except the folded samples, plus `streams` and `arrays`. The samples are
three columns (bin, label, count) of one entry per (core, lane, bin, label), sorted by core, lane, bin, then count
descending; streams[i] = [core, lane, start, end] names the rows of one (core, lane). Core "typical" is the sum over
all cores, precomputed so the viewer never aggregates. arrays = {name: [dtype, byte offset, length]}, offsets from the
start of the array section. The server sends the file as is with Content-Encoding: gzip, so the browser inflates it
and maps the columns as typed arrays without parsing.

  python -m kperf.bundle convert kperf/bundles/*.json   # old JSON bundles -> .kperf next to them
"""
import gzip, json, struct, sys
from pathlib import Path
import numpy as np

MAGIC = b"KPRF"
DTYPES = {"u1": np.uint8, "u2": np.uint16, "u4": np.uint32}

def _small(a):
  a = np.asarray(a)
  hi = int(a.max()) if a.size else 0
  assert a.size == 0 or int(a.min()) >= 0
  for name, dt in DTYPES.items():
    if hi <= np.iinfo(dt).max: return name, a.astype(dt)
  raise ValueError(f"value {hi} does not fit u4")

def columns(cells):
  """cells: {(core, lane): {bin: Counter(label -> n)}} -> (streams, {bin, label, count}) with a 'typical' stream per lane."""
  typical = {}
  for (ck, lane), bins in cells.items():
    T = typical.setdefault(("typical", lane), {})
    for b, c in bins.items():
      tc = T.setdefault(b, {})
      for li, n in c.items(): tc[li] = tc.get(li, 0) + n
  streams, B, L, N = [], [], [], []
  for (ck, lane), bins in [*cells.items(), *typical.items()]:
    start = len(B)
    for b in sorted(bins):
      for li, n in sorted(bins[b].items(), key=lambda kv: (-kv[1], kv[0])): B.append(b); L.append(li); N.append(n)
    streams.append([ck, lane, start, len(B)])
  return streams, dict(bin=np.array(B, np.int64), label=np.array(L, np.int64), count=np.array(N, np.int64))

def lane_kinds(b, lane):
  """lane -> {kind: samples} over all cores, from the typical stream."""
  kinds, out = np.array([l["kind"] for l in b["labels"]] or [0]), {}
  a = b["arrays"]
  for ck, ln, s, e in b["streams"]:
    if ck == "typical" and ln == lane:
      for k, n in zip(kinds[a["label"][s:e]].tolist(), a["count"][s:e].tolist()): out[k] = out.get(k, 0) + n
  return out

def write(path, b):
  """b: header dict with 'streams' and 'arrays' ({name: int array}); arrays are stored in the smallest dtype that fits."""
  arrays = {k: _small(v) for k, v in b["arrays"].items()}
  order = sorted(arrays, key=lambda k: -arrays[k][1].itemsize)  # widest first keeps every column aligned
  meta, off, blobs = {}, 0, []
  for k in order:
    dt, a = arrays[k]
    meta[k] = [dt, off, int(a.size)]
    blobs.append(a.astype(a.dtype.newbyteorder("<")).tobytes()); off += len(blobs[-1])
    pad = -off % 4; blobs.append(bytes(pad)); off += pad
  head = json.dumps({**b, "arrays": meta}, separators=(",", ":")).encode()
  head += b" " * (-(8 + len(head)) % 4)
  tmp = Path(path).with_suffix(".tmp")
  with open(tmp, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", compresslevel=6, mtime=0) as z:
    z.write(MAGIC + struct.pack("<I", len(head)) + head)
    for x in blobs: z.write(x)
  tmp.replace(path)

def read_header(path) -> dict:
  with gzip.open(path, "rb") as z:
    magic, n = z.read(4), struct.unpack("<I", z.read(4))[0]
    if magic != MAGIC: raise ValueError(f"{path}: not a kperf bundle")
    return json.loads(z.read(n))

def read(path) -> dict:
  raw = gzip.decompress(Path(path).read_bytes())
  if raw[:4] != MAGIC: raise ValueError(f"{path}: not a kperf bundle")
  n = struct.unpack_from("<I", raw, 4)[0]
  b = json.loads(raw[8:8 + n])
  base = 8 + n
  b["arrays"] = {k: np.frombuffer(raw, DTYPES[dt], cnt, base + off).astype(np.int64) for k, (dt, off, cnt) in b["arrays"].items()}
  return b

def from_json(j):
  """an old JSON bundle (nested bins) -> a header dict for write()."""
  cells = {(ck, lane): {int(k): dict(pairs) for k, pairs in bins.items()} for ck, lanes in j.pop("bins").items() for lane, bins in lanes.items()}
  j["streams"], j["arrays"] = columns(cells)
  j.pop("findings", None)
  return j

if __name__ == "__main__":
  if len(sys.argv) < 3 or sys.argv[1] != "convert": sys.exit(__doc__)
  for p in map(Path, sys.argv[2:]):
    out = p.with_suffix(".kperf")
    write(out, from_json(json.loads(p.read_text())))
    print(f"{p} ({p.stat().st_size / 1e6:.1f} MB) -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
