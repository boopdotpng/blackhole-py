#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

PYTHON="${PYTHON:-$ROOT/../.venv/bin/python}"
JOBS="${TEST_JOBS:-4}"
start=$SECONDS

pytest_args=(-q)
if [ "$JOBS" != "1" ] && "$PYTHON" -c 'import xdist' >/dev/null 2>&1; then
  pytest_args+=(-n "$JOBS")
  echo "Running emulator pytest suite with ${JOBS} worker(s)..."
else
  echo "Running emulator pytest suite serially..."
fi
echo

"$PYTHON" -m pytest "${pytest_args[@]}" "$@"
status=$?

elapsed=$((SECONDS - start))
echo
if [ "$status" -eq 0 ]; then
  echo "Summary: PASS in ${elapsed}s"
else
  echo "Summary: FAIL in ${elapsed}s"
fi

exit "$status"
