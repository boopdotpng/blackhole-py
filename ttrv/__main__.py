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
  a = ap.parse_args(argv)
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
