# blackhole-py

A tinygrad-style tensor compiler, RISC-V/Tensix assembler, and bare-metal runtime for Tenstorrent Blackhole.

- **Tensor & UOp IR** with symbolic simplification, rangeify fusion, and lifetime-planned DRAM allocation
- **Blackhole compiler** lowering kernels to a tile DAG, joint 5-core schedule (`BRISC`, `NCRISC`, `TRISC0–2`), and machine code
- **Bare-metal runtime** talking directly to `/dev/tenstorrent` (Linux) or DriverKit (macOS) over PCIe/DMA/NoC

No TTRV, no TTNN, no tt-metal, and no CPU kernel fallback.

---

### Laziness & fusion

Write normal tensor math. Rangeify fuses elementwise, reduction, and matmul epilogues into a single 5-core Blackhole megakernel:

```python
import numpy as np
from compiler import Tensor, dtypes

a = Tensor(np.random.randn(64, 1024).astype(np.float32), dtype=dtypes.bf16)
g = Tensor(np.random.randn(256, 1024).astype(np.float32), dtype=dtypes.bf16)
u = Tensor(np.random.randn(256, 1024).astype(np.float32), dtype=dtypes.bf16)

# Fused 2D multicast SwiGLU: two matmuls + silu + mul in one kernel launch
y = (a.matmul(g.T, dtype=dtypes.fp32).silu() * a.matmul(u.T, dtype=dtypes.fp32)).numpy()
```

### Models

Full 52-layer **Nanbeige4.3-33B** runs natively on a single Blackhole P150 (BFP8 attention & LM head, BFP4 MLP, BF16 embeddings & norms), matching the archived TTRV reference token-for-token:

```sh
python3 examples/nanbeige.py --device 0 --prompt 'The capital of France is' --tokens 8 --timing
```

| Model / Benchmark | Hardware | Metric |
| --- | --- | --- |
| Nanbeige4.3-33B (52L mixed BFP4/BFP8) | P150 | **~2.06 warm tok/s** (exact token match) |
| Matmul `1024 × 7168 × 22016` (BF16) | P150 (130 cores, 2D SUMMA) | **16.06 TFLOP/s** (6.11× over 1D) |
| Matmul `1024 × 7168 × 22016` (BFP8) | P150 (130 cores, 2D SUMMA) | **17.04 TFLOP/s** (4.56× over 1D) |
| Matmul `1024 × 7168 × 22016` (BFP4) | P150 (130 cores, 2D SUMMA) | **17.74 TFLOP/s** (3.69× over 1D) |

Projections with `M > 8` automatically lower to a 2D multicast grid (up to 13×10 cores on P150) using NoC0 row multicasts, NoC1 column multicasts, and two-slot credit rings (`BH_MCAST=0` forces the 1D path). Decode (`M <= 8`) uses the 1D path with runtime position arguments.

```sh
python3 examples/benchmark_matmul_mcast.py --card 0
python3 examples/benchmark_projection.py --card 0
```

---

## Requirements

- Linux with `/dev/tenstorrent` (IOMMU enabled) or macOS with `macos/ttgpu-dext`
- Python 3, `numpy`, `tokenizers` (for `examples/nanbeige.py`)
- `clang`, `lld`, and `llvm-objcopy` with RISC-V target support (for `fw/`)

If a card hangs after an aborted workload, reset attached cards with:

```sh
python3 smi.py -r
```

---

## Architecture

```text
Tensor / UOp  ──►  rangeify  ──►  tile DAG  ──►  joint linearize + sync  ──►  5-core RV32 / Tensix
```

- [`compiler/`](compiler/) — UOp IR, dtypes, symbolic algebra, rangeify, lifetime DRAM planner, and RV32/Tensix ISA assembler (`compiler/isa/`)
- [`compiler/blackhole/`](compiler/blackhole/) — Blackhole tile lowering (`lower.py`, `matmul.py`, `mcast.py`, `map.py`, `reduction.py`, `argmax.py`, `sfpu.py`, `recipes.py`, `pipeline.py`, `runtime.py`)
- [`fw/`](fw/) — resident RISC-V boot/park stubs, DMA engine, and NoC/multicast helpers
- [`hw/`](hw/) — Blackhole ISA encodings, Tensix config fields, and measured SFPU latency/hazard model
- [`device.py`](device.py), [`pci.py`](pci.py), [`pci_linux.py`](pci_linux.py), [`pci_macos.py`](pci_macos.py) — host PCIe/TLB/DMA/FaceBuffer runtime
- [`examples/`](examples/) — Nanbeige4.3-33B inference (`nanbeige.py`) and matmul/projection benchmarks
- [`docs/`](docs/) — Blackhole hardware reference (`index.html`) and unified middle-end lowering architecture (`lowering.md`)

---

## Tests

```sh
python3 -m pytest -q                                       # CPU compiler, ISA, hazard, and control tests
BH_HW=1 python3 -m pytest -q                               # hardware tests on both P150 cards
BH_MCAST_REAL=1 python3 -m pytest -q test/test_matmul_mcast.py -k real_nanbeige
BH_NANBEIGE=1 python3 -m pytest -q test/test_nanbeige_e2e.py
```
