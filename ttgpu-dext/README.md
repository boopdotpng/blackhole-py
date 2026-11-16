# ttgpu-dext

A DriverKit extension for Tenstorrent Blackhole on macOS (Apple Silicon, over Thunderbolt). There is no tt-kmd on
macOS, so this driver claims the card (PCI `1e52:b140`) and lets blackhole-py open it directly through IOKit:

- `IOConnectMapMemory64` types 0-5 map a BAR into the caller; type >= 6 allocates that many bytes of DMA-prepared
  host memory (the dext writes the segment table at the start of the buffer).
- Scalar methods: config space read/write, PCIe reset, DMA prepare, and ARC messages (power votes).

Everything else tt-kmd does (TLB windows, iATU, ARC queue) is in `../system_darwin.py`. Derived from tinygrad's
TinyGPU dext; the app is `TTGPU.app`, the extension `com.boopapps.ttgpu.driver`.

## Install (development build, SIP off)

An ad-hoc signed dext only loads with System Integrity Protection disabled and system extension developer mode on.

1. Install Xcode (not just the command line tools) and select it:
   `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`
2. Disable SIP: boot into Recovery (hold the power button), open Terminal, run `csrutil disable`, reboot.
3. Turn on developer mode: `systemextensionsctl developer on`
4. Build, install to `/Applications` and activate:
   ```sh
   ./ttgpu-dext/install_nosip.sh          # or --build to only build into ttgpu-dext/build/Debug
   ```
5. Approve it in System Settings > Privacy & Security (or General > Login Items & Extensions > Driver Extensions).
6. Plug in the card and check:
   ```sh
   systemextensionsctl list               # com.boopapps.ttgpu.driver [activated enabled]
   ioreg -n ttgpu                         # the driver is attached to the card
   /Applications/TTGPU.app/Contents/MacOS/TTGPU status
   ```

To remove it: `/Applications/TTGPU.app/Contents/MacOS/TTGPU uninstall`.

## Notes

- One card, device index 0.
- Only 2 MB TLB windows: the 4 GB windows (BAR4) don't map over Thunderbolt.
- Driver logs: `log stream --predicate 'eventMessage CONTAINS "tinygpu"'`
