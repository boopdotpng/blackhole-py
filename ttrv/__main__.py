"""Parse, expand or build a TTRV source file."""

import argparse, json, struct, sys
from pathlib import Path
from . import build
from .parse import Error, parse, show
from .expand import expand, show_program


def main(argv=None):
  ap = argparse.ArgumentParser(prog="ttrv")
  ap.add_argument("cmd", choices=("parse", "expand", "build"))
  ap.add_argument("file", type=Path)
  ap.add_argument("-D", dest="defines", action="append", default=[], metavar="NAME=VALUE")
  ap.add_argument("-o", "--output", type=Path, help="directory for build artifacts (default FILE.build)")
  ap.add_argument("--cycles", action="store_true", help="simulate a single build offline and print per-worker/RISC AICLK estimates as JSON")
  ap.add_argument("--args", type=Path, help="binary launch argument block (e.g. args0.bin)")
  ap.add_argument("--bind", action="append", default=[], metavar="NAME=INT", help="integer or encoded buffer address")
  ap.add_argument("--input", action="append", default=[], metavar="NAME=FILE", help="initial DRAM buffer bytes in host page order")
  ap.add_argument("--l1", action="append", default=[], metavar="X,Y,NAME=FILE", help="initial bytes of named worker L1 storage at physical coordinates")
  ap.add_argument("--startup", metavar="FILE|simultaneous", help="role entry calibration; defaults to matching card-0 firmware")
  ap.add_argument("--samples",type=int, help="sample several refresh and firmware polling phases and report interval medians")
  ap.add_argument("--max-cycles", type=int, help="simulation cycle limit (default 10000000)")
  ap.add_argument("--sample-iterations", type=int, metavar="N",
                  help="simulate long kernels at about N and 2N iterations of their shared trip counts and extrapolate "
                       "(default 32; 0 simulates every iteration)")
  a = ap.parse_args(argv)
  if a.cycles and (a.cmd != "build" or a.output): ap.error("--cycles requires build and writes its report to stdout")
  if (a.args or a.bind or a.input or a.l1 or a.startup or a.samples is not None or a.max_cycles is not None
      or a.sample_iterations is not None) and not a.cycles: ap.error("simulation options require build --cycles")
  if a.args and a.bind: ap.error("choose either --args or --bind")
  try:
    decls = parse(a.file.read_text(), str(a.file))
    if a.cmd == "parse":
      print(show(decls))
      return
    p = expand(decls, dict(d.split("=", 1) for d in a.defines))
    if a.cmd == "expand":
      print(show_program(p))
      return
    kernel = build(p)
    if a.cycles:
      from .cycles import estimate
      bindings = {k: int(v, 0) for k,v in (s.split("=", 1) for s in a.bind)}
      tile_inputs = {}
      for item in a.l1:
        target, filename = item.split("=", 1)
        x, y, name = target.split(",", 2)
        tile_inputs[int(x, 0), int(y, 0), name] = Path(filename).read_bytes()
      print(json.dumps(estimate(kernel, bindings=bindings or None, arguments=a.args.read_bytes() if a.args else None,
                                tile_inputs=tile_inputs, inputs={k:Path(v).read_bytes() for k,v in (s.split("=",1) for s in a.input)},
                                max_cycles=10_000_000 if a.max_cycles is None else a.max_cycles,
                                samples=1 if a.samples is None else a.samples, startup=a.startup,
                                sample_iterations=32 if a.sample_iterations is None else a.sample_iterations or None),
                       indent=2))
      return
    out = a.output or a.file.with_suffix(".build")
    out.mkdir(parents=True, exist_ok=True)
    for role, image in kernel.images.items():
      (out / f"{role}.bin").write_bytes(image)
      (out / f"{role}.lst").write_text(kernel.listing[role] + "\n")
    manifest = kernel.manifest | {"images": {r: f"{r}.bin" for r in kernel.images}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
  except (Error, OSError, ValueError, struct.error) as e:
    print(e, file=sys.stderr)
    return 1


if __name__ == "__main__":
  sys.exit(main())
