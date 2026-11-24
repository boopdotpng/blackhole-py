#!/bin/bash
# Reinstall the macOS TTGPU dext and wait for the card to come back.
set -e
cd "$(dirname "$0")"
APP=/Applications/TTGPU.app/Contents/MacOS/TTGPU

pkill -f "TTGPU server" || true               # the server holds the dext's user client open
systemextensionsctl list 2>/dev/null | grep -q com.boopapps.ttgpu.driver && "$APP" uninstall
./ttgpu-dext/install.sh

echo "waiting for the card..."
for _ in $(seq 60); do
  if python3 -c "import pci_macos as p; print(f'card is back: ARC boot status {p._arc_boot_status():#x}')" 2>/dev/null; then
    systemextensionsctl list 2>/dev/null | grep com.boopapps.ttgpu.driver
    exit 0
  fi
  sleep 1
done
echo "card did not come back within 60 s; try 'python3 smi.py' or check System Settings for a pending approval" >&2
exit 1
