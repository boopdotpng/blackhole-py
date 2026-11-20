# blackhole-py

Run LLMs on a Tenstorrent Blackhole card from plain Python. Kernels are written in TTRV, a small language with one
function per RISC-V core of a Tensix tile. The compiler, firmware and dispatcher all live in this repo. Needs
`tt-kmd` >= 2.12.0, `numpy`, `tiktoken`, `tokenizers`, `clang` and `llvm-objcopy`.

```python
import numpy as np
from ttrv import Device

d = Device(0)
embed = d.kernel("examples/llama3/embedding.ttrv")                     # compile the TTRV kernel, install it
weights = d.array(np.random.randn(16, 2048).astype(np.float32), "bf16")  # DRAM buffers, filled from the host
history = d.array(np.arange(16, dtype=np.uint32))
out = d.empty(2048, "bf16")
embed(history=history, weights=weights, output=out, token_pos=3)       # queued; returns at once
print(out.numpy())                                                     # waits, copies back: row 3 as BF16 bits
```

## Writing model kernels

- `include ../common/attention` loads declarations from a path relative to the including file. Each kernel expands a
  shared module once. The module uses the kernel's constants, types and resource declarations.
- `const ROW_OFFSETS = [0, 2, dst.face, dst.face + 2]` names an ordered list of compile-time values.
  `repeat offset in ROW_OFFSETS` unrolls the body in that order. `ROW_OFFSETS[i]` accepts a compile-time index.
- `tileptr(weights, tile)` addresses a DRAM tile by its ordinal for both scalar and packed formats.
  For example, `noc.read page, tileptr(weights, tile), n=1024, wait` reads one tile. The length counts elements.
- `reads = noc.group read` allocates a transaction ID without issuing a request. Use `tid=reads` on the reads that
  can overlap, then `noc.wait reads` before consuming the data or reusing its storage. A group may be empty.

## Benchmarks

| Model | Weights | Prefill 1× (tok/s) | Decode 1× (tok/s) | Decode 2× (tok/s) | Speedup |
| --- | --- | ---: | ---: | ---: | ---: |
| Llama 3.2 1B | BF16 | 8,630 | 163.7 | 263.9 | 1.61× |
| Llama 3 8B | BF16 | 2,362 | 30.5 | 53.9 | 1.77× |
| Llama 3 8B | BFP8_B | 2,986 | 48.0 | 76.1 | 1.59× |
| Qwen3.8-27B | BFP8_B + BFP4_B | 193 | 17.6 | 29.3 | 1.66× |
| Nanbeige4.3-33B | BFP8_B + BFP4_B | 1,296 | 19.4 | 31.9 | 1.64× |

Batch-one greedy on p150a cards; 2× is tensor parallel over TT-link. Median of three warm runs: a 320-token prefix,
then the 32 tokens after the first output, excluding loading and compilation.

## Weights

| Model | Checkpoint | Format |
| --- | --- | --- |
| Llama 3.2 1B | `weights/llama3-1b/` (2.4 GB) | Hugging Face BF16 |
| Llama 3 8B | `weights/llama3-8b-bf16/` (15 GB) | Hugging Face BF16 |
| Llama 3 8B | `weights/llama3-8b-bfp8/model.safetensors` (8.5 GB) | packed: all projections and LM head BFP8_B |
| Qwen3.8-27B | `../weights/qwen3.8-27b/mixed_bfp4mlp_bfp8down_bfp8attn/model.safetensors` (25 GB) | packed: attention, linear attention, MLP down BFP8_B; gate, up BFP4_B; LM head BF16 |
| Nanbeige4.3-33B | `../weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors` (23 GB) | packed: attention, LM head BFP8_B; all MLP BFP4_B |

Packed tensors are `U8` block-float tiles, named in the header metadata `blackhole.layout: kn_tiles_32x32_v1` and
`blackhole.formats` (tensor to `bfp8_b` or `bfp4_b`); embeddings and norms stay BF16. `config.json` and `tokenizer.json`
go beside the checkpoint (Qwen: `--metadata`, default `~/models/qwen3.8-27b/bf16`). One card holds 32 GB.

## Run

```sh
python examples/llama3.py --model 1b --tokens 64     # or 8b-bf16, 8b-bfp8
python examples/qwen38.py --tokens 12                 # --tp 2 for two cards
python examples/nanbeige.py --tokens 64 --timing
python eth/llama3_tp.py --model 8b-bf16               # two cards: ethernet channel 11 cabled straight across
python sims/probes/model_rates.py 8b-bfp8             # one benchmark row; eth/tp_rates.py for 2×
PROFILE=1 python examples/llama3.py                   # per-kernel hardware counters at exit
```

## Offline cycle estimates

From this directory, simulate one kernel with its launch arguments. This example uses the saved 1B embedding launch and zero-filled DRAM.

```sh
python3 -m ttrv build examples/llama3/embedding.ttrv --cycles \
  --args sims/results/2026-11-18-kernels-1b-card1/embedding/args0.bin
```

The JSON report groups the active RISC cores under each tile’s NoC coordinates. Each core has its start, finish, elapsed AICLK cycles, dynamic instruction count and cycle breakdown. A tile’s interval runs from its earliest entry to its latest return. The top-level interval spans all tiles. These intervals exclude code installation and dispatcher retirement. `backend_finish` includes outstanding Tensix work after a RISC returns.

The RISC `breakdown` sums to that core’s elapsed cycles. `poll_cycles` counts time in recognized polling loops. The TRISC `backend` counters describe the asynchronous Tensix instruction stream, including source-valid waits and semaphore stalls. `unit_busy` reports modeled FPU, SFPU, packer and unpacker service cycles. These counters can overlap RISC execution. NoC statistics include requests, bytes, data hops and accumulated completion latency.

Use the same `-D NAME=VALUE` overrides as the real build. A saved argument block preserves the address-to-bank mapping. Alternatively, `--bind NAME=INT` accepts scalar values and runtime-encoded buffer addresses. `--input NAME=FILE` initializes a DRAM argument from bytes in host page order. Other memory starts at zero. The simulator executes scalar branches and moves data through L1 and the NoCs. For the supported BF16 decoder argmax images, it also computes the SFPU lane winners and packs their keys and indices for scalar code. Other Tensix arithmetic and packing currently contribute timing only. RISC control flow that depends on computed tensor values can therefore differ from hardware.

Long kernels are not simulated iteration by iteration. The compiler records which `shared` values bound a runtime loop (`count` in `first, count = split(N)`) and where each role's prelude leaves them (`Kernel.timing`). For a trip count of at least `4 * N`, the simulator runs the launch twice with every such count scaled to about `N` and `2N` iterations. It then extrapolates each tile and RISC linearly to its real count. The prologue, epilogue, pipeline fill and drain are charged once, and the steady-state cost of one iteration is charged for each remaining iteration. `--sample-iterations N` sets N (default 32). `--sample-iterations 0` simulates every iteration. The report's `sampling` field records the scales used. Llama 1B's LM head takes about 20 s this way, against more than 15 minutes for a full simulation.

Poll loops cost no simulation time. A RISC whose loop iteration stores nothing and leaves its registers unchanged sleeps until the NoC counter, CB register, semaphore or L1 word it read changes. It is charged the skipped iterations at the loop's period.

`--samples 5` varies the unknown DRAM refresh and NCRISC polling phases. Each tile and role gets a sampled range and median. The start, finish and breakdown fields come from one representative simulated launch. `--max-cycles N` bounds execution, including waits.

Worker entry offsets are calibrated against the resident firmware sources. A firmware mismatch selects simultaneous role entry and records that assumption in the report. `--startup simultaneous` selects it explicitly. To measure a new calibration after changing the firmware, run the first command on card 0 and pass the resulting file with `--startup /tmp/ttrv-startup.json`. The second command checks every tile and RISC against its hardware median and exits nonzero when any interval exceeds 3% error.

```sh
flock /tmp/tt-device.lock python3 sims/probes/role_cycles.py --device 0 --grid 88 --startup-only /tmp/ttrv-startup.json
flock /tmp/tt-device.lock python3 sims/probes/role_cycles.py --device 0 --grid 88 --full-projection --check
```

The model is experimental. The per-core ±3% target remains open for contended launches. See [the timing status](sims/STATUS.md).

The checkpoint-backed probe compares the same kernel image, argument block, tile coordinate and RISC against repeated card 0 launches. By default it samples the first binding of each distinct image. Use `--all-launches` to include repeated layers. Replay needs only the capture. It exits with status 1 when any interval misses the target.

```sh
python3 sims/probes/decode_intervals.py replay sims/results/2026-11-19-decode-1b-card0.jsonl.gz --kernel embedding attention argmax --by-role --csv /tmp/ttrv-errors.csv
flock /tmp/tt-device.lock python3 sims/probes/decode_intervals.py capture /tmp/qwen-projection.jsonl.gz --model qwen38 --launch 0 43 --repeats 7
```

`--launch GRAPH INDEX` runs the preceding kernels with their original images and stamps only the selected launch. Indices start at zero. `--rows N` selects a prefill chunk. Each repetition reconstructs the model on a fresh device open. For an indexed launch, `--mark-ncrisc-instruction PC` timestamps the final visit to a selected NCRISC command strobe or fence. Replay with `--by-role` to see the measured interval from that point to return.

For a kernel that consumes retained worker L1 state from a previous launch, `--l1 X,Y,NAME=FILE` supplies the initial bytes of a named L1 allocation at one physical tile. Repeat the option for different tiles or allocations.

Each role’s NoC counters split accumulated read, write and atomic completion latency into command issue, request routing, endpoint credit and bank queue waits, endpoint service, and return routing. Stages sum to the completion latency across that role’s transactions. Concurrent transactions contribute overlapping time. For RISC wall time spent polling, use the role’s `poll_cycles`.
