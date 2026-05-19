## blackhole-py

A Python driver for the Tenstorrent Blackhole accelerator. The goal is to
launch and run programs on the card with zero C++ and zero tt-metal — RISC-V
goes straight from Python to the cores.

### Quick start

Run the current smoke test from the repo root:

```sh
python3 -m examples.ret_smoke
```

Use the standalone status tool:

```sh
python3 tt-smi.py              # live status view
python3 tt-smi.py --snapshot   # one-shot telemetry snapshot
python3 tt-smi.py -r           # reset device 0
```

### Status

Working today:

- `examples/ret_smoke.py` launches trivial `ret` kernels on the Tensix cores
  and prints timing data.
- `tt-smi.py` is a working standalone Blackhole status/reset tool.

Still in progress:

- Tile math kernels. `examples/add1.py` is the active bring-up target.
- Fast dispatch with on-device prefetch/dispatch cores.
- tinygrad backend integration.

### Contents

- `dsl.py` — instruction-level DSL for the RISC-V + Tensix ISA
- `asm.py` — assembler / kernel container
- `pcie.py`, `device.py`, `dram.py`, `cq.py` — host-side device access
- `program.py` — tile / dtype bookkeeping
- `tt-smi.py` — standalone status/reset tool, no tt-metal
- `ttk/` — addresses, NOC, CB, tensix register tables
- `fw/` — per-core firmware skeletons (brisc / ncrisc / trisc / cq)

### Todo

- [x] Bring up standalone Blackhole telemetry/reset (`tt-smi.py`).
- [x] Launch a minimal RISC-V program on Tensix cores (`ret_smoke.py`).
- [ ] Get the `add1.py` tile math example passing on hardware.
- [ ] Wire up fast dispatch with on-device prefetch/dispatch cores.
- [ ] Connect this lowering layer to a tinygrad backend.

### Requirements

- Python 3.10+, numpy.
- Hardware: Blackhole P100A or P150.
- The in-kernel Tenstorrent driver must be unloaded before using this driver.

Reference notes: [boopdotpng/tenstorrent-docs](https://github.com/boopdotpng/tenstorrent-docs).
