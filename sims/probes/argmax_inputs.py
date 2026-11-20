"""Keep the argmax launch and addresses fixed while changing the BF16 logit values."""

import argparse
from dataclasses import replace
import gzip
import json
from pathlib import Path
from statistics import median

import numpy as np

from role_cycles import Device, Kernel, build, firmware_fingerprint, fw, measure


def compare(path, kernel):
  from ttrv.cycles import estimate

  with gzip.open(path, "rt") as rows:
    for row in map(json.loads, rows):
      if row["firmware"] != firmware_fingerprint():
        raise ValueError("firmware mismatch")
      brisc = [core for core in row["cores"] if core["role"] == "brisc"]
      inputs = {}
      if row["case"] == "random":
        floats = np.random.default_rng(42).standard_normal(128256, dtype=np.float32)
        inputs["logits"] = (floats.view(np.uint32) >> 16).astype("<u2").tobytes()
      elif row["case"].startswith("bits-"):
        inputs["logits"] = np.full(128256, int(row["case"][5:], 16), dtype="<u2").tobytes()
      for label, memory in [("zero-filled DRAM", {}), ("recorded input pattern", inputs)]:
        tiles = estimate(kernel, bindings=row["bindings"], inputs=memory)["tiles"]
        errors = [
          100 * (tile["cores"]["brisc"]["cycles"] / core["measured"] - 1)
          for tile, core in zip(tiles, brisc, strict=True)
        ]
        print(
          f"{row['case']} {label}: BRISC median signed error {median(errors):+.2f}%, "
          f"{sum(abs(e) <= 3 for e in errors)}/{len(errors)} within 3%",
          flush=True,
        )


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--device", type=int, default=0)
  parser.add_argument("--repeats", type=int, default=21)
  parser.add_argument("--edge-values", action="store_true", help="probe signed zero, subnormals, infinities and NaNs")
  mode = parser.add_mutually_exclusive_group(required=True)
  mode.add_argument("--output", type=Path)
  mode.add_argument(
    "--compare", type=Path, help="offline comparison using zero-filled DRAM and the recorded input pattern"
  )
  a = parser.parse_args()
  if a.repeats < 1 or (a.output and a.output.exists()):
    parser.error("supply a positive repeat count and a new output path")
  path = Path(__file__).resolve().parents[2] / "examples/llama3/argmax.ttrv"
  kernel = build(path.read_text(), file=str(path))
  if a.compare:
    return compare(a.compare, kernel)
  dev = Device(a.device)
  try:
    args = dict(
      logits=dev.zeros(128256, "bf16"),
      history=dev.zeros(8192, "u32"),
      tokens=dev.zeros(8, "u32", host=True),
      start_pos=0,
      write_token=0,
    )
    run = Kernel(dev, kernel, "argmax")
    blank = replace(kernel, images={r: fw.ret(r) for r in kernel.images})
    overhead, _ = measure(run, blank, args, a.repeats, ordered=True)
    rng = np.random.default_rng(42)
    values = rng.standard_normal(args["logits"].shape, dtype=np.float32)
    words = (values.view(np.uint32) >> 16).astype(np.uint16)
    cases = [("zero", np.zeros_like(words)), ("random", words), ("zero-repeat", np.zeros_like(words))]
    if a.edge_values:
      for bits in (0x8000, 0x0001, 0x8001, 0xFF80, 0x7F80, 0x7FC0, 0xFFC0):
        cases.append((f"bits-{bits:04x}", np.full_like(words, bits)))
    with gzip.open(a.output, "xt") as out:
      for label, data in cases:
        args["logits"].copy_from(data)
        raw, _ = measure(run, kernel, args, a.repeats, ordered=True)
        winner = int(args["tokens"].numpy()[4])
        expected = int((data.astype(np.uint32) << 16).view(np.float32).argmax())
        rows = [
          dict(x=x, y=y, role=r, measured=median(v) - median(overhead[x, y, r]) + 1, raw=v, blank=overhead[x, y, r])
          for (x, y, r), v in raw.items()
        ]
        print(
          json.dumps(
            dict(
              case=label,
              card=a.device,
              firmware=firmware_fingerprint(),
              winner=winner,
              numpy_winner=expected,
              bindings={k: getattr(v, "addr", v) for k, v in args.items()},
              cores=rows,
              candidates=[
                dev.dev.iface.read(xy, kernel.manifest["storage"]["candidates"]["address"], 256).hex()
                for xy in dev.dev.workers[: run.grid]
              ],
            )
          ),
          file=out,
          flush=True,
        )
        print(label, winner, flush=True)
        if winner != expected and not label.startswith("bits-"):
          raise ValueError(f"{label}: expected token {expected}, got {winner}")
  finally:
    dev.close()


if __name__ == "__main__":
  main()
