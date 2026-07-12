# Tenstorrent KMD ioctls

This document describes the Linux driver interface used by
[`pcie.py`](../pcie.py). It talks directly to `tt-kmd` through
`fcntl.ioctl` and `libc.mmap`; it does not depend on TT-UMD.

## Device lifecycle

`PCIDevice(index=0, sysmem_size=1 << 30)` performs this sequence:

1. Reads `/sys/class/tenstorrent/tenstorrent!N/tt_card_type` and accepts only
   `p100a`.
2. Opens `/dev/tenstorrent/N` with `O_RDWR | O_CLOEXEC | O_APPEND`.
3. Requests maximum AI clock and Tensix enable with `SET_POWER_STATE`.
4. Allocates a temporary 2 MiB TLB window to read ARC telemetry and determine
   the harvested GDDR bank.
5. Creates anonymous host system memory and pins it for NoC DMA.

`O_APPEND` is significant to current KMD power policy: the file descriptor
starts with a zero power request, and userspace then contributes its explicit
`SET_POWER_STATE` request.

On normal `close()`, `PCIDevice` unpins and unmaps system memory, submits a
zero power request for the flags it controls, and closes the device fd.
`Device.close()` first resets the worker and command-queue cores through a TLB
window.

## Request encoding

KMD defines `TENSTORRENT_IOCTL_MAGIC` as `0xFA` and these requests with Linux
`_IO`, which carries no direction or size bits. The request is therefore:

```py
request = (0xFA << 8) | nr
fcntl.ioctl(fd, request, payload)
```

`_TT_IOCTL()` constructs a fresh zero-initialized `ctypes.Structure`, applies
the wrapper defaults and caller keyword arguments, submits it, and optionally
returns its `out` substructure. Python's `fcntl.ioctl` raises `OSError` when
the driver rejects a request.

`pcie.py` uses six KMD ioctls:

| Python wrapper | KMD request | Number | Request value | Used by |
|---|---|---:|---:|---|
| `PinPages` | `TENSTORRENT_IOCTL_PIN_PAGES` | 7 | `0xFA07` | `Sysmem` construction |
| `UnpinPages` | `TENSTORRENT_IOCTL_UNPIN_PAGES` | 10 | `0xFA0A` | `Sysmem.close()` |
| `AllocateTlb` | `TENSTORRENT_IOCTL_ALLOCATE_TLB` | 11 | `0xFA0B` | `TLBWindow` construction |
| `FreeTlb` | `TENSTORRENT_IOCTL_FREE_TLB` | 12 | `0xFA0C` | `TLBWindow.close()` and error cleanup |
| `ConfigureTlb` | `TENSTORRENT_IOCTL_CONFIGURE_TLB` | 13 | `0xFA0D` | `TLBWindow.target()` |
| `SetPowerState` | `TENSTORRENT_IOCTL_SET_POWER_STATE` | 15 | `0xFA0F` | device open and close |

All other KMD ioctls are outside the current API.

## ABI layouts

The `ctypes` declarations intentionally match the native 64-bit C ABI in
[`tt-kmd/ioctl.h`](../../tt-kmd/ioctl.h). Underscore-prefixed Python fields are
reserved, ignored outputs, or values fixed by the wrapper.

| Payload | Size | Input bytes | Output bytes |
|---|---:|---:|---:|
| `PinPagesPayload` | 40 | 0–23 | 24–39 |
| `UnpinPagesPayload` | 24 | 0–23 | none |
| `AllocateTlbPayload` | 48 | 0–15 | 16–47 |
| `FreeTlbPayload` | 4 | 0–3 | none |
| `ConfigureTlbPayload` | 48 | 0–39 | 40–47, reserved |
| `PowerState` | 40 | entire structure | none |

The driver ABI uses one structure for both input and output. Fields not
explicitly populated remain zero because `ctypes.Structure` zero-initializes
the payload.

## Pinning system memory

`Sysmem(fd, size)` rounds `size` up to the host page size, creates a
`PROT_READ | PROT_WRITE`, `MAP_SHARED | MAP_ANONYMOUS` mapping, and submits:

```py
PinPages(
  fd,
  virtual_address=host_address,
  size=rounded_size,
)
```

The wrapper supplies these hidden fields:

| `tenstorrent_pin_pages_in` field | Value | Meaning |
|---|---:|---|
| `output_size_bytes` | `16` | request the extended two-word output |
| `flags` | `2` | `TENSTORRENT_PIN_PAGES_NOC_DMA` |
| `virtual_address` | mapping address | original page-aligned userspace VA |
| `size` | rounded mapping size | pinned byte count |

The 16-byte output contains `physical_address` followed by `noc_address`;
`Sysmem` retains only `noc_address`. This is the NoC-visible base used
to reach host system memory. `Sysmem.alloc()` returns offsets from a monotonic
bump allocator, page-aligned by default; it does not create additional mappings
or pins.

`Sysmem.flush()` calls `msync(mapping, size, MS_SYNC)`. Closing submits
`UNPIN_PAGES` with the exact original virtual address and size, then calls
`munmap`. KMD does not support unpinning only part of a pinned range.

If pinning fails, construction immediately unmaps the anonymous allocation.

## TLB windows

`TLBWindow(fd, core)` owns one dynamically allocated 2 MiB inbound TLB and its
uncached mapping.

### Allocate

`AllocateTlb(fd)` sends a 48-byte payload whose input requests `size = 2 MiB`.
`TLBWindow` uses the returned `id` and `mmap_offset_uc`; it ignores the WC
offset. It accepts only IDs 0–200. Blackhole's 2 MiB window 201 is reserved by
the kernel, and higher IDs are outside this class's accepted range. A rejected
allocation is freed immediately.

The accepted window is mapped with:

```text
mmap(NULL, 2 MiB, PROT_READ | PROT_WRITE, MAP_SHARED,
     device_fd, mmap_offset_uc)
```

If `mmap` fails, the allocated TLB is freed before the exception is raised.

### Configure

```py
window.target(addr, start=None, end=None)
```

`start` defaults to the core passed to `TLBWindow`; `end` defaults to `start`.
`ConfigureTlbPayload` contains the allocated ID and this
`tenstorrent_noc_tlb_config` image:

| Field | Configured value |
|---|---|
| `addr` | target address at window offset zero |
| `x_start`, `y_start` | `start` coordinate |
| `x_end`, `y_end` | `end` coordinate |
| `noc` | `0` |
| `mcast` | `1` when `start != end`, otherwise `0` |
| `ordering` | `1` |
| `linked`, `static_vc` | `0` |
| reserved fields | `0` |

The Python `_noc_mcast` two-byte array occupies the C `noc` and `mcast`
fields. `_unused` covers `linked`, `static_vc`, and their padding. A unicast
target addresses one core; a multicast target addresses the inclusive
`start`–`end` rectangle.

Retargeting does not allocate or remap anything. Reads and writes access the
same host virtual window after `CONFIGURE_TLB` changes its NoC destination.
`TLBWindow.write()` encodes integer values as little-endian or copies a supplied
bytes-like value. `read()` returns bytes.

### Free

Closing first unmaps the 2 MiB window and then submits `FREE_TLB` with its ID.
The object is a context manager, so the normal form is:

```py
with TLBWindow(device.fd, core) as window:
  window.target(base)
  window.write(offset, value)
```

## Power state

`PowerState` is the 40-byte `tenstorrent_power_state` ABI. The wrapper always
sets:

| Field | Value |
|---|---:|
| `argsz` | `40` |
| `flags` and `reserved0` | `0` |
| `validity` | `3` |
| `power_settings[14]` | all zero |

`validity = 3` means three power flags and zero numeric settings are valid.
The API therefore controls flag bits 0–2:

| Bit | KMD name | Open request | Close request |
|---:|---|---:|---:|
| 0 | `TT_POWER_FLAG_MAX_AI_CLK` | 1 | 0 |
| 1 | `TT_POWER_FLAG_MRISC_PHY_WAKEUP` | 0 | 0 |
| 2 | `TT_POWER_FLAG_TENSIX_ENABLE` | 1 | 0 |
| 3 | `TT_POWER_FLAG_L2CPU_ENABLE` | not valid | not valid |

KMD aggregates power requests from all open clients. A zero in this fd's
request removes its contribution for a valid flag; it does not override
another client's request.

## Ownership and cleanup rules

- A pinned range is paired with the device fd that pinned it and must be
  unpinned with its original VA and full size.
- A TLB ID is allocated, configured, mapped, unmapped, and freed through the
  same fd.
- `TLBWindow` handles allocation and mapping failures, but callers should use
  its context-manager form to guarantee normal cleanup.
- `PCIDevice.close()` is idempotent after its fd becomes negative.
- The ioctl wrappers expose native ABI objects, not portable serialized
  packets; their layout assumes the same little-endian 64-bit Linux ABI as
  Blackhole hosts.

## Sources

- [`pcie.py`](../pcie.py), the implementation described here
- [`device.py`](../device.py), device reset and close ordering
- [`tt-kmd/ioctl.h`](../../tt-kmd/ioctl.h), the kernel userspace ABI
