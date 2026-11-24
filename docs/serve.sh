#!/bin/sh
# Rebuild docs/index.html from hw/*.py + docs/notes.toml and open it.
cd "$(dirname "$0")" || exit 1
python3 build.py || exit 1
if command -v open >/dev/null 2>&1; then open index.html; else xdg-open index.html; fi
