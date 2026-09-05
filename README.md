# blackhole-py

Raw Blackhole assembly tests and a byte-buffer runtime. `ttk/model.py` is the
starting point for a new TTK; no runtime or test imports it. The old TTK,
tensor runtime, Llama examples, and compiler design drafts have been removed.

Read the code in this order:

1. `fw/c/` and `fw/consts.py`: resident C firmware and its memory/launch ABI.
2. `pcie.py`: device discovery, pinned host memory, TLB windows, allocation.
3. `cq.py`: host command records, queue submission, completion, diagnostics.
4. `program.py`: per-core RISC images, parameter tables, L1 initialization.
5. `device.py`: boot, DRAM byte transfers, program launch, shutdown.
6. `isa.py`, `asm.py`, `regalloc.py`: instruction records and assembly.
7. `tests/harness.py` and `tests/movement/`, `tests/compute/`: hardware proofs.

```python
from asm import Asm
from device import Device
from program import Program

device = Device()  # Device.DEFAULT_INDEX, or pass a card index explicitly
try:
  device.boot()
  buffer = device.alloc_interleaved_dram(128 * 2)
  device.write_dram(buffer, bytes(buffer.size))
  core = device.cores[0]
  program = Program({core: {"brisc": Asm("brisc").lower()}})
  device.run(program, params={core: (buffer.address,)})
  assert device.read_dram(buffer) == bytes(buffer.size)
finally:
  device.close()
```

`Program` takes assembled bytes for each participating core. Missing RISC roles
return immediately to firmware. Parameter values are raw u32 words; the runtime
does not perform tensor conversion, tilization, kernel lowering, or automatic
device-side synchronization. Repeated launches currently upload images again.
Host trace capture and resident-kernel caching are not implemented by this
runtime.

Firmware stays in C: `fw.h` supplies shared MMIO, NoC, and entry helpers;
`cq.h` defines the service queue ABI. Prefetch moves host records, dispatch
launches workers, and the DRAM service handles host transfers and completion.
Worker firmware resets hardware, enters raw kernels, and reports completion.
The removed trace and parameter-template paths are no longer in firmware.

Run the tests from this directory:

```sh
PYTHONPATH=. python3 -m pytest -q
PYTHONPATH=. python3 -m pytest -q tests/movement tests/compute \
  --bh-hardware --bh-device=0
```

Hardware tests run sequentially and hold a per-card lock. See
[tests/README.md](tests/README.md) for the harness and cycle profiler.

Requires `tt-kmd` > 2.9.0 and a supported P100A or P150A/B/C. P100 uses seven
DRAM banks; P150 uses eight and supports the stock 120-core or restored
140-core firmware topology. Firmware compilation uses a RISC-V toolchain;
`fw/c_firmware.py` discovers it and builds the firmware images.
