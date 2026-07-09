#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <probe-name> <artifact-dir>" >&2
  exit 2
fi

probe_name="$1"
artifact_dir="$2"
blackhole_py="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tenstorrent_root="$(cd "${blackhole_py}/.." && pwd)"
tt_lang="${tenstorrent_root}/tt-lang"

mkdir -p "${artifact_dir}"
rm -f \
  "${artifact_dir}/initial.mlir" \
  "${artifact_dir}/final.mlir" \
  "${artifact_dir}/brisc.cpp" \
  "${artifact_dir}/ncrisc.cpp" \
  "${artifact_dir}/trisc.cpp" \
  "${artifact_dir}"/ttlang_kernel_*.cpp
rm -rf "${artifact_dir}/asm"

set +u
source "${tt_lang}/build-gcc/env/activate"
set -u

export TTLANG_DUMP_ARTIFACTS_DIR="${artifact_dir}"
export TTLANG_INITIAL_MLIR="${artifact_dir}/initial.mlir"
export TTLANG_FINAL_MLIR="${artifact_dir}/final.mlir"
export TTLANG_VERIFY="${TTLANG_VERIFY:-0}"

python "${blackhole_py}/ttlang-dumps/probes/llama_kernel_probes.py" "${probe_name}"
