## blackhole-py

A minimal Python driver for the Tenstorrent Blackhole accelerator. Compiles and dispatches RISC-V kernels directly from Python — no TT-Metal runtime required.

> **~7.5k lines of code** (2.5k Python + 5k C++ firmware) — the entire driver, compiler, firmware, and dispatch stack. TT-Metal's `tt_metal/` directory alone is ~430k lines of C++.

### Requirements

> You must unload tt-kmd (`modprobe -r tenstorrent`). You may need to prevent the module from auto-loading on reboot and then reboot the computer.

- **Hardware**: Blackhole P100A and P150 (all variants). 
- **Kernel**: VFIO (`modprobe vfio-pci`). This is only required for fast dispatch (i.e anywhere where pinning memory is required.)
- **Python**: 3.10+, numpy

#### vfio? 
For fast dispatch to work, we need to pin and unpin pages so that the card can copy data back and forth. Without VFIO, you would mmap 1GB of memory, `mlock` it so it can't be swapped out, and then read procfs to get the pagemap. On most systems, this will result in 50000+ non-contiguous pages, which the tenstorrent card cannot use. This setup (without VFIO) works with tinygrad+AMD because there is hardware on AMD GPUs that stores a page-map and allows the GPU to see thousands of scattered pages as one range. Since tenstorrent has no such hardware, we have to rely on the IOMMU to maintain this mapping and present a contiguous IOVA range to the device. 

**Does not support multi-chip / distributed yet.**

### Setup

```sh
./setup-deps.sh          # downloads SFPI compiler toolchain + TT-Metal headers
./setup_python_cap.sh    # grants Python the capabilities needed for VFIO access (prompts for sudo)
```

### Usage

```sh
PYTHONPATH=. uv run examples/matmul_peak.py 
```

#### Dispatch modes

Fast dispatch uses on-device command queues (prefetch + dispatch cores). Slow dispatch (`TT_USB=1`) drives the chip over the UT3G USB-C adapter via host TLB writes.

```sh
PYTHONPATH=. uv run examples/matmul_peak.py              # fast dispatch (on-device CQ)
PYTHONPATH=. TT_USB=1 uv run examples/matmul_peak.py     # slow dispatch (over UT3G USB adapter)
```
