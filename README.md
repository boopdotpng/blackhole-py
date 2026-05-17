## blackhole-py

A minimal Python driver for the Tenstorrent Blackhole accelerator. Emits RISC-V
(and Tensix) instructions directly from Python -- no SFPI toolchain, no TT-Metal runtime,
no C++ firmware.

> **Status: currently non-functional on hardware.** The old C++ firmware / SFPI compile
> path has been torn out and the examples still reference the removed `compiler`,
> `firmware`, and `kernels` modules.

### Direction

Instead of shipping a C++ toolchain to turn kernel source into RISC-V, we emit RISC-V
straight from Python. `dsl.py` is an instruction-level DSL for RV32I + M + the Tensix
instruction push.

Reference notes live in [boopdotpng/tenstorrent-docs](https://github.com/boopdotpng/tenstorrent-docs).

### Requirements

- **Python**: 3.10+, numpy
- **Hardware**: Blackhole P100A and P150. tt-kmd must be unloaded (`modprobe -r tenstorrent`); you may need to blacklist it to survive a reboot.
- **Kernel (eventually)**: VFIO (`modprobe vfio-pci`), required for fast dispatch so the device can DMA against a contiguous IOVA range.

#### Why VFIO?
For fast dispatch to work, we need to pin and unpin pages so the card can copy data back
and forth. Without VFIO, you would mmap 1GB of memory, `mlock` it so it can't be swapped
out, and then read procfs to get the pagemap. On most systems, this will result in 50000+
non-contiguous pages, which the Tenstorrent card cannot use. This setup (without VFIO)
works with tinygrad+AMD because there is hardware on AMD GPUs that stores a page-map and
allows the GPU to see thousands of scattered pages as one range. Since Tenstorrent has no
such hardware, we have to rely on the IOMMU to maintain this mapping and present a
contiguous IOVA range to the device.

**Does not support multi-chip / distributed.**

### Dispatch modes (hardware path, when restored)

Fast dispatch uses on-device command queues (prefetch + dispatch cores). Slow dispatch
(`TT_USB=1`) drives the chip over the UT3G USB-C adapter via host TLB writes. The setcap
helper for VFIO lives at the repo root:

```sh
./setup_python_cap.sh   # grants Python the capabilities needed for VFIO
```
