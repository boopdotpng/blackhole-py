#!/bin/bash
# Download and setup tt-metal dependencies for blackhole-py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$SCRIPT_DIR/tt-metal-deps"
TARBALL="$SCRIPT_DIR/tt-metal-deps.tar.gz"
TOTAL_STEPS=4

print_stage() {
  local step="$1"
  local message="$2"
  printf '\n[%s/%s] %s\n' "$step" "$TOTAL_STEPS" "$message"
}

print_done() {
  local message="$1"
  printf '[ok] %s\n' "$message"
}

cleanup_tarball() {
  if [ -f "$TARBALL" ]; then
    rm -f "$TARBALL"
  fi
}

trap cleanup_tarball EXIT

# Check if already installed
if [ -f "$DEST/sfpi-toolchain/bin/riscv-tt-elf-g++" ]; then
  echo "Dependencies already installed at $DEST"
  exit 0
fi

# Detect platform
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS-$ARCH" in
  Darwin-arm64)
    echo "macOS builds not available for v0.7.0" >&2
    exit 1
    ;;
  Linux-x86_64)
    URL="https://github.com/boopdotpng/blackhole-py/releases/download/v0.7.0/tt-metal-deps.tar.gz"
    ;;
  *)
    echo "Unsupported platform: $OS $ARCH" >&2
    exit 1
    ;;
esac

print_stage 1 "Preparing tt-metal dependencies for $OS $ARCH"
mkdir -p "$SCRIPT_DIR"
print_done "Install location: $DEST"

print_stage 2 "Downloading tt-metal dependencies"
printf 'Source: %s\n' "$URL"
printf 'Progress: total, received, speed, and ETA shown below.\n'
curl --fail --location "$URL" --output "$TARBALL"
print_done "Download complete"

print_stage 3 "Extracting archive"
tar -xzf "$TARBALL" -C "$SCRIPT_DIR"
print_done "Archive extracted to $SCRIPT_DIR"

print_stage 4 "Cleaning up temporary files"
cleanup_tarball
trap - EXIT
print_done "Removed $TARBALL"

echo
echo "Dependencies installed to $DEST"
"$DEST/sfpi-toolchain/bin/riscv-tt-elf-g++" --version | head -1
