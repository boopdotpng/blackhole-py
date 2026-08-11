#!/usr/bin/env python3
import os, sys, token, tokenize

TOKENS = {token.OP, token.NAME, token.NUMBER, token.STRING}

def tabulate(rows, headers, floatfmt=".1f"):
  rows = [tuple(format(value, floatfmt) if isinstance(value, float) else str(value)
                for value in row) for row in rows]
  headers = tuple(map(str, headers))
  widths = [max(len(header), *(len(row[i]) for row in rows))
            for i, header in enumerate(headers)]

  def format_row(row):
    return "  ".join(value.ljust(width) if i == 0 else value.rjust(width)
                     for i, (value, width) in enumerate(zip(row, widths)))

  return "\n".join([format_row(headers),
                    format_row(tuple("-" * width for width in widths)),
                    *(format_row(row) for row in rows)])

def stats(root):
  for path, dirs, files in os.walk(root):
    dirs[:] = [name for name in dirs if name not in (".git", ".venv", "venv", "__pycache__")]
    for name in files:
      if not name.endswith((".py", ".c")) or name == "sz.py": continue
      filename = os.path.join(path, name)
      if name.endswith(".c"):
        with open(filename) as f: lines = sum(1 for line in f if line.strip())
        if lines: yield os.path.relpath(filename, root), lines, 1.0
        continue
      with tokenize.open(filename) as f:
        tokens = [t for t in tokenize.generate_tokens(f.readline) if t.type in TOKENS]
      lines = len({line for t in tokens for line in range(t.start[0], t.end[0] + 1)})
      if lines: yield os.path.relpath(filename, root), lines, len(tokens) / lines

if __name__ == "__main__":
  rows = sorted(stats(sys.argv[1] if len(sys.argv) > 1 else "."), key=lambda row: (-row[1], row[0]))
  total = sum(row[1] for row in rows)
  density = sum(lines * density for _, lines, density in rows) / total
  print(tabulate([*rows, ("Total", total, density)],
                 headers=("Name", "Lines", "Tokens/Line"), floatfmt=".1f"))
