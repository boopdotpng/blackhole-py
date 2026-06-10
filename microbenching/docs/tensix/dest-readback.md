# Blackhole Dest Readback Microbench

Goal: validate a RISC-visible path for inspecting Tensix internal register-file
state without routing through the packer first.

The harness lives in `microbenching/tensix/microbench_dest_readback.py`.

## Quarantine Notice

Do not run `microbenching/tensix/microbench_dest_readback.py` or pack/readback
validation jobs on shared hardware until this path is explicitly cleared.

This microbench is quarantined as a suspected hardware-wedge path. Job
`728a4309` timed out in the no-readback baseline while waiting for core `(1,2)`,
and earlier readback variants (`7eb9e874`, `33c4e400`) perturbed the final
packed matmul output (`rel_l2=1.0`). The failure mode is not yet isolated well
enough to distinguish a clean Dest debug-array cycle bound from readback
behavior that changes downstream pack output or wedges the core.

Resumption guardrails:

1. Resume only after explicit clearance that this suspected wedge path may touch
   shared hardware again.
2. Use `tt-device-queue` only. Do not run this benchmark, pack `--validate`, or
   any device-opening Python directly from a shell.
3. Start from static checks (`--build-only`) and a clean non-readback
   full-pipeline matmul baseline on the chosen core.
4. Queue one small hardware job at a time with short timeouts. Stop on the first
   timeout, all-`0xff` readback, ARC readiness failure, non-finite output, or
   validation mismatch.
5. Report a readback perturbation cycle bound only when both no-readback and
   readback runs finish, the readback bytes match the known matmul tile, and the
   packed output after readback still validates. If pack output changes, that is
   a blocker, not a bound.
6. If perturbation recurs, bisect the readback scope before retrying the full
   64-row proof: row count, pack-after-readback enabled/disabled, and
   `DEST_CG_CTRL` handling are the first toggles to isolate.

## Quick Read

Current scope:

- one logical Tensix core, tiny `64x32x64` BF16 matmul
- normal `matmul_peak.py` unpack, math, pack, and output writer pipeline
- TRISC1 snapshots Dest after math completion and before `MATH_PACK` is posted
- snapshot path writes Dest debug-array rows to L1 at `0x12d400`
- timing path measures the same math subblock with and without readback
- local `--build-only` mode verifies imports, assembly, and `Program` layout
  without opening the PCIe device

The path is a correctness and observability tool. It is not required for raw
math timing, where `TTSTALLWAIT(SYNC, MATH|SFPU)` plus `PC_BUF_SYNC` already
provides a completion edge.

## How To Run

Hardware runs are currently paused by the quarantine above. Keep these commands
for reference only until the path is explicitly cleared.

From `blackhole-py`, use the device queue for hardware:

```sh
timeout 60 env PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=15 \
  python3 microbenching/tensix/microbench_dest_readback.py --core 1,2
```

For non-device checks:

```sh
PYTHONPATH=. python3 microbenching/tensix/microbench_dest_readback.py --build-only
```

## What This Reads

Blackhole exposes a debug array read port through:

| Register | Address | Purpose |
|---|---:|---|
| `RISCV_DEBUG_REG_DBG_ARRAY_RD_EN` | `0xffb12060` | enable debug-array reads |
| `RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD` | `0xffb12064` | select array, row, and 32-bit word |
| `RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA` | `0xffb1206c` | read selected 32-bit word |
| `RISCV_DEBUG_REG_DEST_CG_CTRL` | `0xffb12240` | disable Dest clock gating while reading |

The additive helper is in `ttk.tensix.Tensix.debug_array_row_to_l1`.
For Dest it reads the selected row directly. For SrcA/SrcB it first routes the
source row through a temporary Dest row using the debug variants
`TTMOVDBGA2D` / `TTMOVDBGB2D`, then reads that Dest row through the same debug
array port.

## L1 Result Layout

| Range | Address | Size | Purpose |
|---|---:|---:|---|
| `dest_readback_result` | `0x12d000` | `128` bytes | header + timing record |
| `dest_readback_rows` | `0x12d400` | `2048` bytes | 64 Dest rows, 8 words per row |

The current validation reads one 64-row Dest tile. Earlier four-tile attempts
over-addressed the debug row path and perturbed the pack result; keeping to the
documented 64-row debug walk is the safer baseline.

## Validation

The harness validates in two layers:

- The no-readback run must produce a `matmul_peak.py` output that passes the
  existing NumPy reference check.
- The readback run compares the L1 debug-row snapshot against the corresponding
  packed BF16 tile bytes, accepting whichever 32-bit debug word byte order
  matches.

The script compares readback bytes against the no-readback matmul output, then
separately reports whether the pack output after readback still passes the
NumPy matmul check. Cycle counts are primary; current reporting converts
microseconds with `AICLK_MHZ = 800.0`.

## Results

Local build-only check:

```text
build-only readback=False: 17 segments, 8600 bytes
build-only readback=True: 17 segments, 22656 bytes
```

Queued hardware attempts on 2026-06-09:

| job | readback rows | result |
|---|---:|---|
| `7eb9e874` | 256 | failed: readback variant perturbed final pack output (`rel_l2=1.0`) |
| `33c4e400` | 256 | failed the same way after matching TT-exalens command thread bits |
| `65f4fb03` | 64 | blocked before launch: device open failed with ARC not ready (`boot_status=0xffffffff`) |
| `728a4309` | 64 | failed before readback proof: no-readback baseline timed out waiting for core `(1,2)` |
| `014f149f` | 64 | blocked before launch: queued `queue_python` run failed opening the device with ARC not ready (`boot_status=0xffffffff`) |

Historical note: queued reset job `60b3d008` and `tt_smi_status` both failed
with the same ARC-not-ready signature before the later card reboot. The resumed
post-reboot run `728a4309` did open the device and reached program execution,
but timed out in the baseline matmul, so no current readback-match proof or pack
validation result is available from this pass.

Follow-up queue reset `914fecf0` also failed with ARC not ready after resetting
the PCIe secondary bus. Because device open is still failing, the pack
`--validate` run was not attempted in this pass.

## Known Limitations

- The debug-array read path still needs final hardware confirmation against a
  packed matmul tile.
- SrcA/SrcB readback is helper-level support only; the microbench currently
  validates Dest.
- Reading Dest before pack may perturb pack if the debug path is over-addressed
  or clock-gating state is wrong. That perturbation is part of what this bench
  is meant to expose.
