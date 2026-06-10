# Blackhole NoC Contention Probes

Goal: recover behavioral structure of the Blackhole NoC under controlled
contention: through-traffic vs injected traffic, read/write virtual-channel
isolation, vertical bisection bandwidth, and dependent per-hop latency.

The harness lives in `microbenching/noc/riscv_noc_contention_probe.py`.

## Method

The script uses peer L1 unicast traffic only. Bulk streams are issued as 16 KiB
NoC commands from BRISC, with one result record per active stream containing
the local `WALL_CLOCK` window and the relevant NIU master counter delta.

The host labels every row with a small physical path model:

- NoC0 advances in positive X then positive Y.
- NoC1 advances in negative X then negative Y.
- The model is a 25 x 25 torus and uses physical worker coordinates directly.
- Worker columns are `1..7,10..14`, so the x=8,9 gap still counts as routers
  traversed by the path model.

This model is intentionally local to the harness for now.
`# DEDUPE: shares logic with microbenching/noc/noc_topology.py` marks it for later consolidation
if a shared topology helper lands.

## Experiments

### B. Crossing-Traffic Victim

One long victim write stream runs from one row edge to the other. A second write
stream injects at each intermediate worker router on the victim path and targets
the same sink. The output table reports victim throughput as the injection
point moves downstream.

Interpretation:

- Flat victim throughput across injection positions suggests position-neutral
  arbitration.
- Victim throughput falling as the injector moves closer to the sink suggests
  a positional bias or local injection advantage.
- Strong victim collapse at any one injection point is evidence of starvation or
  a pathological collision on that link.

### E. Virtual-Channel Isolation

A read stream and a write stream run from the same source tile to the same
target tile concurrently, using BRISC for the write saturator and NCRISC for
the read stream. The script first measures read-alone throughput, then read
throughput while the write stream is active.

Interpretation:

- Read throughput unchanged from read-alone means request/response traffic is
  likely isolated from the write stream by separate VCs or buffers.
- Read slowdown means the two operations share at least one constrained queue,
  link VC, or NIU resource.
- `--vc-sweep` tries default commands and static VC combinations using VC 1 and
  VC 5 fields exposed through `ttk/noc.py`.

### F. Bisection Bandwidth

The harness pairs left-half workers with right-half workers on the same rows,
launches simultaneous NoC0 write streams across the vertical midline, and
compares aggregate cross-section bandwidth with a single stream baseline.

Interpretation:

- `aggregate / single-link` is the approximate number of single-link-equivalent
  channels across the bisection.
- This is a behavioral estimate. It can be lower than physical link count if
  the endpoints, NIUs, command buffers, or row selection saturate first.

### Aux. Dependent Per-Hop Latency

The pointer-chase mode reads one 4-byte remote L1 word at a time. The next read
address is the value returned by the previous read, so requests cannot pipeline.
Rows are swept by true hop count from the path model and fit with:

```text
cycles_per_iteration = fixed_NIU_cost + hops * cycles_per_hop
```

Interpretation:

- The slope is the per-hop latency estimate.
- The intercept is the fixed local NIU, command-buffer, response, and flush
  cost.
- This should expose the per-hop term that the original independent hop sweep
  could not see.

## How To Run

All hardware runs must go through the shared device queue. Plain `python3` is
only for import and dry-run checks.

Non-device checks:

```sh
PYTHONPATH=. python3 -m py_compile microbenching/noc/riscv_noc_contention_probe.py
PYTHONPATH=. python3 microbenching/noc/riscv_noc_contention_probe.py b --dry-run --bytes 16384 --repeats 1
PYTHONPATH=. python3 microbenching/noc/riscv_noc_contention_probe.py e --dry-run --bytes 16384 --repeats 1 --vc-sweep
PYTHONPATH=. python3 microbenching/noc/riscv_noc_contention_probe.py f --dry-run --bytes 16384 --repeats 1 --max-pairs 4
PYTHONPATH=. python3 microbenching/noc/riscv_noc_contention_probe.py hop --dry-run --iters 4 --max-hops 2
```

Queued hardware examples:

```sh
PYTHONPATH=. timeout 120 python3 microbenching/noc/riscv_noc_contention_probe.py b --bytes 16384 --repeats 1 --gate-delay-cycles 0
PYTHONPATH=. timeout 120 python3 microbenching/noc/riscv_noc_contention_probe.py e --bytes 16384 --repeats 1 --gate-delay-cycles 0
PYTHONPATH=. timeout 120 python3 microbenching/noc/riscv_noc_contention_probe.py f --bytes 16384 --repeats 1 --max-pairs 4 --gate-delay-cycles 0
PYTHONPATH=. timeout 120 python3 microbenching/noc/riscv_noc_contention_probe.py hop --iters 8 --max-hops 2 --gate-delay-cycles 0
```

For stable measurements, increase payloads after smoke testing, for example
`--bytes 262144 --repeats 2` for B/E/F and `--iters 64` for hop.

## Current Status

Implemented and import/dry-run validated on 2026-06-09:

- Experiment B crossing-traffic victim probe.
- Experiment E same-source read/write VC isolation probe, including optional
  static VC field sweep.
- Experiment F left-half to right-half bisection probe.
- Dependent pointer-chase per-hop latency probe with host-side line fit.

Hardware result sections below are appended by the harness after successful
queued runs.

## Queued Smoke Attempt 2026-06-09

- Job `61d5ffbf`: `hop --iters 4 --max-hops 1 --gate-delay-cycles 0 --no-report`
  through `tt-device-queue`.
- Result: failed after `21.32s` with `TimeoutError: timeout waiting for core
  (2, 2)` while polling `device.run()`.
- Follow-up reset job `e94a138f`: failed with `ARC not ready after 2.0s
  (boot_status=0xffffffff)`.

No benchmark numbers are recorded from this attempt. The harness remains
validated only for import and dry-run assembly/program lowering until the
shared device is reset cleanly.

## Queued Runs 2026-06-09 After Device Reboot

- Device note: AICLK was reported as `800 MHz`; cycle-domain values are the
  primary result.
- Queue policy: one isolated hardware job at a time through `tt-device-queue`.
- Payloads were intentionally tiny bring-up runs: B/E/F use one `16 KiB`
  command per stream; hop requested `16` dependent reads per point.

### Experiment B Result

- Job: `8710cc02`
- Command: `b --bytes 16384 --repeats 1 --gate-delay-cycles 0 --no-report`
- Result: completed.

NoC0 victim `1,2` -> `14,2` (true hops 13)

| case | injection | path index | victim B/cyc | injector B/cyc | victim counter | injector counter |
|---|---|---:|---:|---:|---:|---:|
| baseline |  | 0 | 31.208 |  | 1 |  |
| inject@2,2 | `2,2` | 1 | 22.979 | 31.208 | 1 | 1 |
| inject@3,2 | `3,2` | 2 | 30.510 | 31.629 | 1 | 1 |
| inject@4,2 | `4,2` | 3 | 30.510 | 31.691 | 1 | 1 |
| inject@5,2 | `5,2` | 4 | 30.510 | 31.691 | 1 | 1 |
| inject@6,2 | `6,2` | 5 | 30.510 | 31.691 | 1 | 1 |
| inject@7,2 | `7,2` | 6 | 30.062 | 32.063 | 1 | 1 |
| inject@10,2 | `10,2` | 7 | 30.510 | 31.691 | 1 | 1 |
| inject@11,2 | `11,2` | 8 | 30.510 | 31.691 | 1 | 1 |
| inject@12,2 | `12,2` | 9 | 30.007 | 31.691 | 1 | 1 |
| inject@13,2 | `13,2` | 10 | 30.341 | 31.691 | 1 | 1 |

Interpretation: at this tiny one-command payload, the victim only slows
substantially when the injector is the immediate next tile on the path
(`2,2`), dropping from `31.208` to `22.979 B/cyc` (`0.736x` baseline).
Other injection positions stay near baseline (`30.0-30.5 B/cyc`). This is not
enough to claim a global positional arbitration law, but it does show a local
near-source collision effect and no obvious starvation from downstream
injection points.

### Experiment E Result

- Job: `833b06e4`
- Command: `e --bytes 16384 --repeats 1 --vc-sweep --gate-delay-cycles 0 --no-report`
- Result: completed.

NoC0 same-core read/write `1,2` -> `14,2` (true hops 13)

| read VC | write VC | read-alone B/cyc | read+write B/cyc | read slowdown | write B/cyc | read ctr | write ctr |
|---:|---:|---:|---:|---:|---:|---:|---:|
| default | default | 32.125 | 21.787 | 1.475x | 30.118 | 1 | 1 |
| 1 | 1 | 30.567 | 21.445 | 1.425x | 30.567 | 1 | 1 |
| 1 | 5 | 30.397 | 21.223 | 1.432x | 30.118 | 1 | 1 |
| 5 | 1 | 30.567 | 21.445 | 1.425x | 30.567 | 1 | 1 |
| 5 | 5 | 30.567 | 21.445 | 1.425x | 30.567 | 1 | 1 |

Interpretation: the read stream slows under a saturating write stream in every
tested command-field configuration. Default commands slow from `32.125` to
`21.787 B/cyc` (`1.475x` slower), and static VC combinations still slow by
`1.425-1.432x`. Behaviorally, this looks like shared/constrained read-write
resources rather than clean VC isolation for this same-source path. The static
VC fields tested here did not recover read-alone throughput.

### Experiment F Result

- Job: `dca5e1cf`
- Command: `f --bytes 16384 --repeats 1 --max-pairs 4 --gate-delay-cycles 0 --no-report`
- Result: completed.

NoC0 left-half -> right-half bisection, 4 pairs

| pairs | single-link B/cyc | aggregate cross-section B/cyc | aggregate / single-link | bad counters |
|---:|---:|---:|---:|---:|
| 4 | 31.208 | 49.461 | 1.585 | 0 |

Interpretation: with four same-row left-to-right pairs, aggregate bisection
throughput is `49.461 B/cyc`, or `1.585x` the single-stream baseline. This
bring-up-sized result is endpoint/NIU sensitive and should not yet be read as a
physical link count. It does show that four simultaneous midline crossings do
not scale linearly from a single stream under this setup.

### Aux Hop Result

- Job: `a0eafbe1`
- Command: `hop --iters 16 --max-hops 4 --gate-delay-cycles 0 --no-report`
- Result: failed after `11.36s`.
- Failure: `TimeoutError: timeout waiting for core (2, 2)` while polling
  `device.run()`.
- Follow-up reduced-scope job: `bdd8d830`
- Command: `hop --nocs 0 --core 3,2 --max-hops 4 --iters 16
  --gate-delay-cycles 0 --no-report`
- Result: failed after `11.36s`.
- Failure: `TimeoutError: timeout waiting for core (4, 2)` while polling
  `device.run()`.
- A patched source-only pointer-chase attempt was queued as `2afd5260`, but was
  not allowed to run after the safety update. Queue status recorded it as
  `FAIL(-1)` with no elapsed time.

Per-hop slope/intercept were not measured. Hardware attempts stopped at this
high-risk path. The two completed hop attempts both timed out waiting for the
passive target core, first `(2,2)` and then `(4,2)`, while B/E/F completed after
the device reboot. Treat the dependent pointer-chase harness as paused until it
is explicitly cleared for hardware again; the completed B/E/F results above are
the current NoC contention data.
