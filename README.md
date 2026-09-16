# blackhole-py

Single-card Llama inference on Tenstorrent Blackhole.
Requires `tt-kmd` > 2.9.0 and local checkpoints in the directories shown below.

Use the shared `~/tenstorrent/.venv` and run from this directory. C firmware
in `fw/` compiles on every device boot; install Clang and RISC-V binutils
(`riscv64-linux-gnu-ld` and `riscv64-linux-gnu-objcopy`).

```sh
../.venv/bin/pip install -r requirements.txt

# Llama 3.2 1B BF16 — weights/llama3-1b/
../.venv/bin/python -m examples.llama3 --model 1b --device 0 --steps 32

# Llama 3 8B Instruct BF16 — weights/llama3-8b-bf16/
../.venv/bin/python -m examples.llama3 --model 8b --device 0 --steps 32

# Llama 3 8B Instruct FP8 — weights/llama3-8b-fp8/
../.venv/bin/python -m examples.llama3 --model 8b --dtype fp8 --device 0 --steps 32

# Llama 3 8B BF16 with chunked prefill
../.venv/bin/python -m examples.llama3 --model 8b --prefill --device 0 --steps 32
```

The default is 1B BF16. Add `--prompt "Your prompt"` to change the input or
`--profile` for timing. For chunked prompt ingestion on 8B BF16, add `--prefill`
and optionally `--prefill-chunk-size 1..8` (default: 4). FP8 mode loads the
published FP8 weights and their stored scales, with subnormal weights flushed
to signed zero by default. Activations are scaled and packed inside the existing
compute kernels.

Run `../.venv/bin/python -m examples.llama3 --help` for all options.
Checkpoints are not included in Git. Use `--safetensor` and `--tokenizer` to
specify different checkpoint and tokenizer paths.

Multicast matmul benchmark, recovered from `079993d` and ported to the current
assembler and runtime. BF16 uses HiFi2; FP8 uses E4M3 inputs with FP16 output and
partial accumulation. Instruction fusion stays enabled and is checked on every
TRISC after each measured launch.

```sh
# Compile only; dimensions are M N K.
../.venv/bin/python -m examples.matmul_peak 5000 5000 5000 --dtype fp8
# Reserve the card, run, and validate against NumPy.
tt-device-queue run --device 0 --cwd "$PWD" -- \
  ../.venv/bin/python -m examples.matmul_peak 5000 5000 5000 --dtype fp8 --run --runs 10 --profile
```

A row sender multicasts on NoC0, a column sender multicasts on NoC1, and each
core runs separate unpack, math, and pack kernels. Output writers alternate NoC0
and NoC1 by core column. NoC0 writers wait for their local A reader to finish;
writes use a bounded transaction queue and drain before launch completion.
Use `--output-noc 0`, `--output-noc 1`, or `--output-noc split` (default) to compare.
DRAM remains interleaved with one storage tile per page.

The program has one BRISC image, one NCRISC image, and three shared TRISC images.
RV32 branches select A senders with `ci == 0` and B senders with `ri == 0`; the
writer uses `1 - ci % 2` as a runtime NoC selector. `GridProgram` packages these
as one binary plus `global_size = (rows, cols)`. The launcher supplies logical
ranks as L1 data and broadcasts identical buffer arguments and a physical
coordinate map. The kernels compute offsets, sender coordinates, and multicast
rectangles on-core. There are no role-specific images, host-written per-core
recipe tables, or entry trampolines. Shape-specific math is still compiled once
per controller; the experimental `ttk` effect-region/frontend work is separate.

Worker firmware enters the shared images through a common address table.
Rebuild serialized firmware with `../.venv/bin/python -m firmware` (ABI `BHCQ0002`); old blobs
are rejected. Direct `Program` launches still work and restore their fixed entry
addresses when switching from a grid program.

Edge arithmetic uses 8-row by 16-column output fragments and 16-element K steps.
Storage still uses four-face 32×32 containers, and equal core partitions add some
padding: 5000³ computes 5040×5008×5104 (M×K×N), about 3.1% extra arithmetic.
Reported logical TFLOP/s uses the requested dimensions; padded TFLOP/s counts
this arithmetic padding, not the larger storage allocation.

FP8 encoding saturates finite inputs at ±448, rounds ties to even, and flushes
subnormal encodings to signed zero to match the supported hardware unpack path.
Validation compares against the quantized inputs. It checks all outputs for
finiteness and compares all values for outputs up to one million elements;
larger outputs compare 1024 sampled dot products. Timing spans the earliest
reader start through the latest writer completion, including input, math, and
output traffic, excluding host transfers, kernel upload, and one warmup.

Additional tuning: `--block-k`, `--subblock H W`, and `--writer-wave-rows`.
Default K blocks are selected up to 6 tiles for BF16 and 10 for FP8. Writer waves
are disabled by default. On the development card, 5000³ FP8 with split output
measured about 331 logical TFLOP/s; 400 has not yet been reached. After runtime
role selection, five 5000³ repetitions measured 180.06 logical TFLOP/s for BF16
and 330.81 for FP8. BF16 matched the role-specialized baseline at the reported
precision. These are device-kernel timings with quantized-input validation,
not end-to-end host timings.
