#!/usr/bin/env python3
import os, sys, token, tokenize

TOKEN_WHITELIST = {token.OP, token.NAME, token.NUMBER, token.STRING}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__"}
SKIP_FILES = {"sz.py"}

def is_docstring(tok):
  return tok.type == token.STRING and tok.string.startswith(('"""', "'''")) and tok.line.lstrip().startswith(('"""', "'''"))

def gen_stats(base_path="."):
  stats = []
  for path, dirs, files in os.walk(base_path):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    for name in files:
      if not name.endswith(".py") or name in SKIP_FILES: continue
      filepath = os.path.join(path, name)
      with tokenize.open(filepath) as f:
        tokens = [tok for tok in tokenize.generate_tokens(f.readline) if tok.type in TOKEN_WHITELIST and not is_docstring(tok)]
      lines = {line for tok in tokens for line in range(tok.start[0], tok.end[0] + 1)}
      if lines:
        relpath = os.path.relpath(filepath, base_path).replace("\\", "/")
        stats.append((relpath, len(lines), len(tokens) / len(lines)))
  return stats

def gen_diff(old, new):
  old, new = {row[0]: row[1:] for row in old}, {row[0]: row[1:] for row in new}
  diff = []
  for name in old.keys() | new.keys():
    old_lines, old_density = old.get(name, (0, 0))
    lines, density = new.get(name, (0, 0))
    if lines != old_lines or density != old_density:
      diff.append((name, lines, lines - old_lines, density, density - old_density))
  return diff

def render(headers, rows, formats):
  table = [[fmt(value) for fmt, value in zip(formats, row)] for row in [headers, *rows]]
  widths = [max(len(row[i]) for row in table) for i in range(len(headers))]
  def line(row): return "  ".join(value.ljust(widths[i]) if i == 0 else value.rjust(widths[i]) for i, value in enumerate(row))
  return "\n".join([line(table[0]), line(["-" * width for width in widths]), *(line(row) for row in table[1:])])

def text(value): return str(value)
def integer(value): return str(value) if isinstance(value, str) else f"{value:d}"
def signed_integer(value): return str(value) if isinstance(value, str) else f"{value:+d}"
def decimal(value): return str(value) if isinstance(value, str) else f"{value:.1f}"
def signed_decimal(value): return str(value) if isinstance(value, str) else f"{value:+.1f}"

def firmware_stats():
  from functools import partial
  from fw.brisc import build_brisc
  from fw.consts import Firmware
  from fw.ncrisc import build_ncrisc
  from fw.trisc import build_trisc
  builds = {
    "brisc": build_brisc, "ncrisc": build_ncrisc,
    **{f"trisc{i}": partial(build_trisc, i) for i in range(3)},
  }
  rows = []
  for role, build in builds.items():
    size = len(build().lower())
    limit = Firmware.TEXT_SIZE[role]
    rows.append((role, size, limit, limit - size, 100 * size / limit))
  return rows

if __name__ == "__main__":
  if sys.argv[1:] == ["--firmware"]:
    print(render(("Role", "Bytes", "Limit", "Free", "Used %"), firmware_stats(),
                 (text, integer, integer, integer, decimal)))
  elif len(sys.argv) == 3:
    rows = sorted(gen_diff(gen_stats(sys.argv[1]), gen_stats(sys.argv[2])), key=lambda row: (-row[1], row[0]))
    if rows:
      print("### Changes")
      print("```")
      print(render(("Name", "Lines", "Diff", "Tokens/Line", "Diff"), rows,
                   (text, integer, signed_integer, decimal, signed_decimal)))
      print(f"\ntotal line changes: {sum(row[2] for row in rows):+d}")
      print("```")
  else:
    base_path = sys.argv[1] if len(sys.argv) == 2 else "."
    rows = sorted(gen_stats(base_path), key=lambda row: (-row[1], row[0]))
    if rows:
      total_lines = sum(row[1] for row in rows)
      total_density = sum(lines * density for _, lines, density in rows) / total_lines
      print(render(("Name", "Lines", "Tokens/Line"), [*rows, ("Total", total_lines, total_density)], (text, integer, decimal)))
      max_lines = int(os.getenv("MAX_LINE_COUNT", "10000"))
      assert total_lines <= max_lines, f"OVER {max_lines} LINES"
