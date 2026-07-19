#!/usr/bin/env python3
import os, sys, token, tokenize
from tabulate import tabulate

TOKENS = {token.OP, token.NAME, token.NUMBER, token.STRING}

def stats(root):
  for path, dirs, files in os.walk(root):
    dirs[:] = [name for name in dirs if name not in (".git", ".venv", "venv", "__pycache__")]
    for name in files:
      if not name.endswith(".py") or name == "sz.py": continue
      filename = os.path.join(path, name)
      with tokenize.open(filename) as f:
        tokens = [t for t in tokenize.generate_tokens(f.readline) if t.type in TOKENS and
                  not (t.type == token.STRING and t.line.lstrip().startswith(('"""', "'''")))]
      lines = len({line for t in tokens for line in range(t.start[0], t.end[0] + 1)})
      if lines: yield os.path.relpath(filename, root), lines, len(tokens) / lines

if __name__ == "__main__":
  rows = sorted(stats(sys.argv[1] if len(sys.argv) > 1 else "."), key=lambda row: (-row[1], row[0]))
  total = sum(row[1] for row in rows)
  density = sum(lines * density for _, lines, density in rows) / total
  print(tabulate([*rows, ("Total", total, density)],
                 headers=("Name", "Lines", "Tokens/Line"), floatfmt=".1f"))
