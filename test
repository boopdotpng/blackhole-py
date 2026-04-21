#!/usr/bin/env bash
# Run the emulator spec tests. Passes extra args through to pytest.
# Examples:
#   ./test                                      # all spec tests, quiet
#   ./test -v                                   # verbose
#   ./test -k incr_get                          # tests matching a pattern
#   ./test tests/spec/test_noc_atomics.py       # one file
set -euo pipefail
cd "$(dirname "$0")/extra/emu"
exec uv run --with pytest python -m pytest tests/spec/ -q "$@"
