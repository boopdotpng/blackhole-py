# Blackhole SFPU Transcendentals Microbench

Goal: measure the TRISC1 SFPU vector path for `exp`, `rsqrt`, `recip`,
`sigmoid`, and `silu` with the three-number method from
`tensix-backend-bench-plan.md`: issue cost, single-op completion latency, and
steady-state throughput.

The harness lives in `microbenching/tensix/microbench_sfpu.py`.

## Scope

- one active TRISC1 role on one Tensix core
- BF16 Dest storage, 32 SFPU lanes per load/store group, 32 groups per tile
- cycle counts are primary; ns/us columns assume AICLK `800 MHz`
- result records in L1 at `0x12a000`
- validation readback scratch in L1 at `0x12b000`
- no packer in the timed path
- completion with `TTSTALLWAIT(SYNC, SFPU)` plus `PC_BUF_SYNC`
- Dest observation with a local debug readback helper using
  `DBG_ARRAY_RD_{EN,CMD,DATA}` and `RISCV_DEBUG_REG_DEST_CG_CTRL`. The same
  helper is the natural dedupe point for the `TTMOVDBGA2D` staging path needed
  when reading SrcA through Dest.

## SFPU Opcode Inventory

`dsl.py` currently exposes the Blackhole SFPU instruction family from
`TTSFPLOAD` (`0x70`) through `TTSFPARECIP` (`0x99`): load/load-immediate/store,
LUT/LUT-FP32, immediate add/mul/divp2, exponent/mantissa helpers, integer add,
shift/shift2, condition-code helpers, move/abs/logic, set exponent/mantissa/sign,
MAD/add/mul/mul24, push/pop/enable/compare CC, transpose, stochastic round,
cast, config, swap, less/greater compare, nop, and approximate reciprocal.

Hardware-touching runs must go through the Tenstorrent device queue.

## How To Run

Non-device assembly check:

```sh
PYTHONPATH=. python3 microbenching/tensix/microbench_sfpu.py --build-only --iters 1 --ops exp
```

Device run through the queue, only after the quarantine below is lifted:

```sh
PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_sfpu.py --iters 4 --ops exp --no-report
PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_sfpu.py --iters 4
```

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--ops exp,recip`: run a subset of ops.
- `--tests exp_latency,exp_validate`: run exact rows for bisecting hangs.
- `--build-only`: compile Program/assembly without opening the device.
- `--no-report`: print without appending this document.

The benchmark builds one isolated firmware image per measured row during real
device runs. `--build-only` mirrors that launch pattern so the generated TRISC1
images stay below the L1 text/result scratch region.

## Interpretation

Each op gets three timing rows:

- `*_issue`: seeds Dest, issues one tile op, timestamps before the untimed drain.
- `*_latency`: seeds Dest, issues one tile op, drains inside the timed window.
- `*_throughput`: seeds Dest, issues eight tile ops, then drains once; the table
  divides by eight for steady-state cycles/tile.

The validation rows are deliberately separate. They seed a known scalar tile,
run one SFPU tile op, drain the SFPU, then read a Dest row into L1 via the
debug-array path. The first validation target is `exp(0) = 1.0` (`0x3f80`
bf16).

`rsqrt` currently uses the near-unit Newton path already used by the llama
RMSNorm POC and validates at `rsqrt(1) = 1`. It is a useful iterative-latency
row, not a complete wide-range library rsqrt yet.

## Current Status

Assembly/import validation passes before hardware runs. Device numbers will be
appended below by successful queued runs.

Queued smoke attempts from this implementation:

- `exp_validate` with the first draft TDMA-store interpretation completed
  without hanging, but read back `0x00000000` instead of `0x3f80`. Local LLK docs
  then showed `MOVDBGA2D` stages SrcA into Dest; Dest itself is read through
  `DBG_ARRAY_RD_{EN,CMD,DATA}`.
- After switching validation to the debug-array Dest path, the shared device
  failed before the benchmark opened PCIe: `ARC not ready after 2.0s
  (boot_status=0xffffffff)`. A queued reset and queued `tt-smi` status hit the
  same ARC-not-ready failure.
- After the later card reboot, queued job `acdde664` ran
  `timeout 45 env PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_sfpu.py
  --iters 1 --tests exp_validate --no-report`. It reached the first isolated
  `empty` baseline launch, then failed with `TimeoutError: timeout waiting for
  core (1, 2)`. Per queue discipline, no further hardware rows were queued from
  this workspace, so no validated timing numbers are recorded yet.
- Fresh retry after the next reported reboot used `queue_python` job `54d50950`
  for `exp_validate` first, as required. It failed before benchmark execution:
  `Device()` reported `ARC not ready after 2.0s (boot_status=0xffffffff)`.
  The follow-up MCP reset job `9817af3c` failed with the same ARC-not-ready
  state. The full per-op suite was therefore not queued.
- After a later healthy-card report, queued `exp_validate` job `90dd487f`
  completed without hanging but failed validation: the corrected debug-array
  readback returned `0x007f007f` for word 0, while the expected bf16 value for
  `exp(0)` was `0x3f80`. This suggests the benchmark reached the SFPU/debug
  path, but either the Dest selector/format is wrong or the SFPU result is not
  being read from the intended Dest row.
- Follow-up diagnostic job `535ef8c9`, which opened `Device()` and attempted a
  direct `TLBWindow` read of the L1 readback scratch, hung with no output for
  several minutes and resisted queue SIGINT. This coincided with the host
  crash/reboot investigation window.

## Quarantine

SFPU validation/readback hardware probing is paused as of the `535ef8c9`
incident. Do not queue additional `microbenching/tensix/microbench_sfpu.py --tests exp_validate`
runs, direct `Device()+TLBWindow` diagnostics, debug-array readback probes, or
reset loops for this benchmark until the device owner explicitly clears SFPU
readback work again. The software remains import/build-valid, but per-op timing
numbers are intentionally absent until the readback path can be debugged safely.

The hardware-crash risk is real: the last direct L1 readback diagnostic produced
no output, resisted queue SIGINT, blocked recovery, and overlapped the host
crash/reboot investigation. Treat this as a device-stability issue, not a normal
benchmark failure. Until cleared, only static inspection and `--build-only`
assembly checks are in scope.

## Re-enable Requirements

Before re-enabling SFPU validation/readback work, require all of the following:

- Explicit owner clearance that SFPU debug-array and Dest-readback experiments
  are allowed again.
- Queue health verified externally; no agent should self-clear this from inside
  the SFPU benchmark task.
- A watchdog plan for any `Device()` or L1/debug-register read that can kill the
  process if Python ignores SIGINT.
- No direct post-run `TLBWindow` scratch inspection. The benchmark must emit all
  diagnostic readback words through its normal L1 result record so a separate
  readback job is not needed.
- First run must be a non-readback timing/control row, then the smallest
  readback row, then stop for manual log review. Do not jump straight to the
  full per-op suite.

Suggested staged restart after clearance:

1. Static only: `PYTHONPATH=. python3 microbenching/tensix/microbench_sfpu.py --build-only --iters 1 --tests exp_validate`.
2. Queue one no-readback control row such as `empty,sync_empty` or `exp_latency`
   with a short timeout.
3. Queue exactly one validation row and make it print/store every
   `DBG_ARRAY_RD_DATA` selector word in the benchmark result record.
4. If validation still returns `0x007f007f`, debug the Dest selector/format in
   code review first. Do not run direct TLB scratch reads to inspect state.
5. Only after `exp_validate` passes and logs are reviewed, run the full
   three-number suite.
