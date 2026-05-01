#!/bin/bash
set -euo pipefail

# cd to repo root so `uv run` resolves this project's interpreter
cd "$(dirname "$0")"

CAPS='cap_dac_override,cap_sys_rawio,cap_sys_admin,cap_ipc_lock=ep'
declare -a PYTHONS=()

add_python() {
  local exe="$1"
  [[ -n "$exe" ]] || return 0
  [[ -e "$exe" ]] || return 0
  readlink -f "$exe"
}

if [[ $# -gt 0 ]]; then
  for exe in "$@"; do
    PYTHONS+=("$(add_python "$exe")")
  done
else
  # Current shell/default python3.
  PYTHONS+=("$(add_python "$(python3 -c 'import sys; print(sys.executable)')")")

  # Activated virtualenv, if any.
  if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python3" ]]; then
    PYTHONS+=("$(add_python "$VIRTUAL_ENV/bin/python3")")
  fi

  # uv-managed project interpreter, if this directory is in a uv project.
  if command -v uv >/dev/null 2>&1; then
    UV_PYTHON="$(uv run --no-sync python3 -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
    if [[ -n "$UV_PYTHON" ]]; then
      PYTHONS+=("$(add_python "$UV_PYTHON")")
    fi
  fi
fi

mapfile -t PYTHONS < <(printf '%s\n' "${PYTHONS[@]}" | sort -u)

if [[ ${#PYTHONS[@]} -eq 0 ]]; then
  echo "No Python interpreters found" >&2
  exit 1
fi

for python_path in "${PYTHONS[@]}"; do
  echo "Setting capabilities on: $python_path"
  sudo setcap "$CAPS" "$python_path"
  getcap "$python_path"
done
