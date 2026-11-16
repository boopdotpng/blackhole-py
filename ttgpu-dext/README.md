# ttgpu-dext

A DriverKit extension for Tenstorrent Blackhole on macOS (Apple Silicon, over Thunderbolt). There is no tt-kmd on
macOS, so this driver claims the card (PCI `1e52:b140`) and lets blackhole-py open it directly through IOKit:

- `IOConnectMapMemory64` types 0-5 map a BAR into the caller; type >= 6 allocates that many bytes of DMA-prepared
  host memory (the dext writes the segment table at the start of the buffer).
- Scalar methods: config space read/write, PCIe reset, DMA prepare, and ARC messages (power votes).

Everything else tt-kmd does (TLB windows, iATU, ARC queue) is in `../system_darwin.py`. Derived from tinygrad's
TinyGPU dext; the app is `TTGPU.app`, the extension `com.boopapps.ttgpu.driver`.

## Install (Apple Development signing, SIP on)

The Debug configuration signs automatically with team `7AMV998SSP`, using Xcode's team provisioning profiles
("Mac Team Provisioning Profile: com.boopapps.ttgpu" and "DriverKit Team Provisioning Profile: com.boopapps.ttgpu.driver").
The dext needs `com.apple.developer.driverkit`, `driverkit.transport.pci` and `driverkit.allow-any-userclient-access`
on its profile, and the app needs `system-extension.install`. A dext signed this way loads with SIP enabled, and you
don't need `systemextensionsctl developer on`.

1. Install full Xcode and sign in to an account on the team (Xcode > Settings > Accounts). `install.sh` uses
   `/Applications/Xcode.app` even if `xcode-select` points at the command line tools.
2. Build, install to `/Applications` and activate:
   ```sh
   ./ttgpu-dext/install.sh                # or --build to only build into ttgpu-dext/build/dd
   ```
3. Approve it in System Settings > Privacy & Security (or General > Login Items & Extensions > Driver Extensions).
4. Plug in the card and check:
   ```sh
   systemextensionsctl list               # 7AMV998SSP  com.boopapps.ttgpu.driver ... [activated enabled]
   ioreg -n ttgpu                         # the driver is attached to the card
   /Applications/TTGPU.app/Contents/MacOS/TTGPU status
   ```

On a different team: in Xcode, set the team on both targets (TinyGPU and TinyGPUDriver) and change the bundle IDs
to ones you own. Keep the driver's ID the app's ID plus a suffix, and update `dextID` in `Shared/TinyGPUApp.swift`.
If Xcode can't add the DriverKit entitlements to the profile, request them for your team from Apple
(developer.apple.com/system-extensions).

To remove it: `/Applications/TTGPU.app/Contents/MacOS/TTGPU uninstall`.

### Without a developer account (SIP off)

`install_nosip.sh` ad-hoc signs the build instead. That only loads with SIP disabled: boot into Recovery, run
`csrutil disable`, reboot, then `systemextensionsctl developer on` and `./ttgpu-dext/install_nosip.sh`.

## Notes

- One card, device index 0.
- Only 2 MB TLB windows: the 4 GB windows (BAR4) don't map over Thunderbolt.
- Driver logs: `log stream --predicate 'eventMessage CONTAINS "tinygpu"'`
