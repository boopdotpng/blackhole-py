#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

JOBS="${TEST_JOBS:-4}"
start=$SECONDS
echo "Running emulator pytest suite with ${JOBS} worker(s)..."
echo

uv run pytest -q -n "$JOBS" "$@"
status=$?

elapsed=$((SECONDS - start))
echo
if [ "$status" -eq 0 ]; then
  echo "Summary: PASS in ${elapsed}s"
else
  echo "Summary: FAIL in ${elapsed}s"
fi

exit "$status"
