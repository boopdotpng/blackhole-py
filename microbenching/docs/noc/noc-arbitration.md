# Blackhole NoC Arbitration

Goal: infer the router arbitration policy when multiple injected streams share
one physical NoC link. This extends the aggregate write benchmarks by measuring
each stream independently rather than only the aggregate window.

The harness lives in `microbenching/noc/riscv_noc_arbitration_bench.py`. The
offline topology helper lives in `microbenching/noc/noc_topology.py`.

## Physical Path Model

`microbenching/noc/noc_topology.py` models the P100a physical router grid as coordinates
`x=0..19`, `y=0..24`. Worker tiles occupy columns `1..7,10..14` and rows
`2..11`; the worker-column gap at `x=8,9` remains visible in hop counts because
paths use physical router coordinates rather than compacted worker indices.

The model starts with the bench-plan assumptions:

- dimension-ordered routing, X leg first and then Y leg
- NoC0 moves in ascending x/y direction
- NoC1 moves in descending x/y direction
- torus wrap links exist

It provides `noc_path(src_xy, dst_xy, noc)`, `noc_hops(...)`, and
`shared_link(stream_a, stream_b, noc)`.

Offline check:

```sh
PYTHONPATH=. python3 microbenching/noc/noc_topology.py
```

## Experiment A

For each run, K sender BRISCs sit in one physical worker row and write toward a
single far-end receiver tile. NoC0 uses the right edge of the row as the target;
NoC1 uses the left edge. Every sender targets a separate L1 destination slice on
that receiver, so all streams contend on the same final directed link without
overwriting each other's sentinel word.

Each sender records:

- its own start and end `WALL_CLOCK`
- `NIU_MST_WR_ACK_RECEIVED` before and after
- `NIU_MST_NONPOSTED_WR_REQ_SENT` before and after
- `NIU_MST_RD_RESP_RECEIVED` before and after

Before the timed loop, the host writes a future 64-bit `WALL_CLOCK` threshold
into each sender's L1. Senders spin until their local clock reaches that
threshold, then snapshot counters and issue the first write. This removes most
host launch skew while keeping per-stream timing local to each core.

Default matrix:

- `K = 2,3,4,6,8`
- NoC `0,1`
- packet bytes `4096,16384`
- nonposted peer-L1 writes
- `256` packets per sender

Interpretation:

- roughly equal per-stream B/cyc: fair round-robin sharing
- nearest-to-target sender favored: through traffic tends to win over injection
- farthest-from-target sender favored: injection tends to win over through traffic

## How To Run

Device access must go through the serialized `tt-device-queue` MCP. From this
Codex environment, submit the command with `queue`/`queue_python`; do not run
the device-opening command directly in a shell:

```sh
PYTHONPATH=. TT_USB=1 python3 microbenching/noc/riscv_noc_arbitration_bench.py
```

For static validation without opening the device:

```sh
PYTHONPATH=. python3 microbenching/noc/riscv_noc_arbitration_bench.py --dry-run
```

Useful smoke-run options:

```sh
PYTHONPATH=. TT_USB=1 python3 microbenching/noc/riscv_noc_arbitration_bench.py \
  --counts 2 --nocs 0 --packet-bytes 4096 --packets 16 --no-report
```

Current guardrail: the benchmark aborts by default if any sender has a bad NIU
counter delta or a bad sender-side sentinel readback. `--allow-invalid` exists
only for deliberate debug runs that need to print invalid raw data. The full
Experiment A matrix is blocked until the tiny smoke reports `bad sentinels = 0`.

## L1 Layout

| Range | Address | Purpose |
|---|---:|---|
| sender result record | `0x150000` | one 24-word record per sender core |
| sender readback scratch | `0x150800` | untimed remote sentinel readback |
| sender start gate | `0x151000` | host-written 64-bit future `WALL_CLOCK` |
| sender packet source | `0x037000` | seeded packet payload |
| receiver destination slices | `0x037000 + sender_index * 0x8000` | per-stream target packet |

## Results

### Smoke Run 2026-06-09

- Queue job: `60aca0b8`
- Command: `PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=20 python3 microbenching/noc/riscv_noc_arbitration_bench.py --counts 2 --nocs 0 --packet-bytes 4096 --packets 16 --no-report`
- Scope: launch/counter/timing smoke only, not the full Experiment A matrix
- Note: this run used host-side target sentinel readback. The harness now also
  records an untimed sender-side NoC readback after the measured window.

| noc | K | packet B | packets | target | sender order | per-stream B/cyc | spread | interpretation | bad counters | bad sentinels |
|---:|---:|---:|---:|---|---|---|---:|---|---:|---:|
| 0 | 2 | 4096 | 16 | `14,2` | `12,2` `13,2` | 27.995 28.681 | 0.024 | roughly equal | 0 | 2 |

Interpretation: the sender-side timing and NIU counters were healthy for this
small case, and the two streams were within 2.4% of each other. Because the
validation sentinels failed in the original host readback path, this smoke
should not be treated as a final arbitration result.

After that smoke, a follow-up device open and an MCP reset both failed with
`ARC not ready after 2.0s (boot_status=0xffffffff)`, so the full matrix was not
run in this session.

### Resume Attempt 2026-06-09

- Import-only queue jobs `a4f87f3e`/`dbdece92` failed before opening the device
  because `microbenching/noc/riscv_noc_arbitration_bench.py` was being imported as a package while
  it still depended on script-style sibling imports. The benchmark now has
  package-import fallbacks and a local `parse_nocs`, so queued helper scripts can
  import it directly.
- First hardware-opening validation job after that fix: `93b45543`.
- Log: `/home/boop/tenstorrent/tt-device-queue/logs/93b45543/output`.
- Result: failed during `Device()` construction with
  `ARC not ready after 2.0s (boot_status=0xffffffff)`.

Per the run rule for this shared card, no further hardware jobs were submitted
after job `93b45543`. The sender-side readback fix and the full Experiment A
matrix still need a healthy queue/device window to be measured.

### Validation Attempt 2026-06-09

- Queue job: `2ce998c5`
- Command shape: queued Python wrapper running
  `microbenching/noc/riscv_noc_arbitration_bench.py --counts 2 --nocs 0 --packet-bytes 4096 --packets 1 --no-report`
- Intended scope: smallest sender-side readback validation, K=2/NoC0/4 KiB/one
  packet per sender.
- Result: failed before benchmark launch during `Device()` construction with
  `ARC not ready after 2.0s (boot_status=0xffffffff)`.
- Log: `/home/boop/tenstorrent/tt-device-queue/logs/2ce998c5/output`.
- Follow-up MCP `tt_smi_status` also failed in `PCIDevice()` with the same ARC
  `0xffffffff` state.

No Experiment A data was collected in this attempt. The failure happened before
program construction or kernel execution, so it does not validate or invalidate
the sender-side readback path.

### Tiny Smoke 2026-06-09

- Pre-check: queue idle/empty; MCP `tt_smi_status` healthy with p100a, 120
  Tensix cores, AICLK `800 MHz`.
- Queue job: `88924c39`
- Command shape: queued Python wrapper running
  `microbenching/noc/riscv_noc_arbitration_bench.py --counts 2 --nocs 0 --packet-bytes 4096 --packets 1 --no-report`
- Scope: one cautious sender-side readback smoke only; no full Experiment A
  matrix.
- Post-check: queue idle/empty; MCP `tt_smi_status` still healthy with AICLK
  `800 MHz`.

| noc | K | packet B | packets | target | sender order | per-stream B/cyc | spread | interpretation | bad counters | bad sentinels |
|---:|---:|---:|---:|---|---|---|---:|---|---:|---:|
| 0 | 2 | 4096 | 1 | `14,2` | `12,2` `13,2` | 11.670 13.518 | 0.147 | near target favored | 0 | 2 |

The smoke completed without ARC-not-ready or core timeout, and NIU counters
matched the issued packet count. Sender-side sentinel readback still failed for
both senders (`bad sentinels = 2`), so the readback validation is not yet fixed
and the full matrix remains intentionally unrun.

### Static Debug Notes 2026-06-09

No hardware was run for this pass.

The unresolved observation is specific: sender-side timing and write counters
completed, but the validation word read from the target tile did not match
`0xA5000000 | (packet_bytes - 4)`. The previous output only reported the count
of bad sentinels, so it did not reveal whether the readback word was zero,
stale, or another unexpected value.

Static guardrails added:

- Future summaries include the raw per-sender readback sentinel words.
- The CLI now aborts by default on the first bad counter or sentinel validation,
  before a full matrix can continue or be appended as a normal result.
- `--allow-invalid` is available only for intentional debug collection.

Blocked status: the full Experiment A matrix should remain unrun as a
result-producing sweep until a one-packet K=2 smoke has `bad counters = 0` and
`bad sentinels = 0`. A safe next debug, when hardware is explicitly allowed
again, is one tiny smoke with raw sentinels enabled by the new summary output.
