# Regenerate config._CFG_DEFINES from cfg_defines.h: python3 tools/gen_config_regs.py [path/to/cfg_defines.h]
import re, sys, pathlib, dataclasses
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import config
header = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else root.parent / "tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h")
lines = header.read_text().split("\n")
thread_end = next(i for i, l in enumerate(lines) if "Registers for ALU" in l)  # THREAD registers come first
defs: dict = {}
for i, l in enumerate(lines):
  if m := re.match(r"#define (\w+)_(ADDR32|SHAMT|MASK) (\w+)", l):
    d = defs.setdefault(m.group(1), {"space": "thread" if i < thread_end else "shared"})
    d[m.group(2)] = int(m.group(3), 0)
names = set()
for cls in config.Config.__subclasses__():
  for f in dataclasses.fields(cls):
    for entry in f.metadata.get("locs", ()):
      names |= {entry} if isinstance(entry, str) else set(entry or ())
missing = sorted(n for n in names - config.MANUAL_REGS.keys() if n not in defs)
assert not missing, f"not in {header.name}: {missing}"
rows = []
for n in sorted(names - config.MANUAL_REGS.keys()):
  d = defs[n]; mask = d["MASK"] >> d["SHAMT"]
  assert mask & (mask + 1) == 0, f"{n} mask is not contiguous"
  rows.append(f'  "{n}": ("{d["space"]}", {d["ADDR32"]}, {d["SHAMT"]}, {mask.bit_length()}),')
src = (root / "config.py").read_text()
start, end = "_CFG_DEFINES = {\n", "}\n# --- end generated ---"
a, b = src.index(start) + len(start), src.index(end)
(root / "config.py").write_text(src[:a] + "\n".join(rows) + "\n" + src[b:])
print(f"{len(rows)} fields from {header}")
