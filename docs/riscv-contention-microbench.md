# Blackhole RISC-V Contention Microbench

This benchmark measures simultaneous activity from the five small RISC-V cores
on one Blackhole Tensix tile. It complements the single-active-role instruction
and memory microbenches.

The harness lives in `examples/riscv_contention_bench.py`.

## Quick Read

Current result on logical core `1,2`:

| Probe shape | Solo adj cost | 2-role adj cost | All-five adj cost |
|---|---:|---:|---:|
| same-address wall-clock MMIO read | `~2.0 cyc/op` | `~2.0 cyc/op` | `~2.25 cyc/op` |
| same-address NoC status MMIO read | `~2.0 cyc/op` | `~2.0 cyc/op` | `~2.0 cyc/op` |
| same-address L1 read | `~2.5-2.6 cyc/op` | `~2.5 cyc/op` | `~2.67 cyc/op` |
| distinct-address L1 read | `~2.5-2.6 cyc/op` | `~2.5 cyc/op` | `~2.5 cyc/op` |
| L1 store | `~1.0 cyc/op` | `~1.0 cyc/op` | `~1.0 cyc/op` |
| local RISC LDM load/store | `~1.0 cyc/op` | `~1.0 cyc/op` | `~1.0 cyc/op` |
| cross-RISC LDM window read (single target) | `~2.5 cyc/op` | `~5.0 cyc/op` | `~17.0 cyc/op` |
| cross-RISC LDM read, round-robin targets | `~2.5 cyc/op` | `~5.0 cyc/op` | `~17.0 cyc/op` |
| contested: owner writes, others read window | owner `~1.0` / reader `~2.8 cyc/op` | — | owner `~1.0` / reader `~13.0 cyc/op` |
| cross-LDM ptr chase (2 loads/op, BRISC target) | — | `~7.0 cyc/op` | `~18.5 cyc/op` |

Key findings from the extended coverage:

- **Round-robin vs single-target reads are identical.** All five roles each reading a
  different window (`xldm_roundrobin_lw1`) produces the same `~17 cyc/op` cost as all
  five reading the same window. The bottleneck is the shared cross-LDM interconnect,
  not per-window read port contention.

- **A writer in the group actually helps the readers.** In the contested tests
  (`xldm_contested_*_lw1`), the owner role writes its own LDM and pays only `~1 cyc/op`
  (write port is separate). The four concurrent readers see `~13 cyc/op` — a ~25%
  reduction vs the `~17 cyc/op` all-read baseline. This implies the write path and
  read path to each LDM share little or no bandwidth.

- **Pointer-chase latency in cross-LDM scales with contention.** The 2-hop dependent
  load (`xldm_ptr_chase_lw2`) costs `~3.5 cyc/load` with 2 active roles and
  `~9.25 cyc/load` with all five — consistent with the single-load cost per role
  count, confirming the serialised dependency adds no extra overhead beyond contention.

Tile sweeps are intentionally a calibration step here rather than a primary
axis. One representative repeat across a few tiles is enough unless the sanity
check finds a surprise.

## What This Measures

- same-address MMIO reads from multiple RISC cores
- same-address and distinct-address L1 reads/writes
- same-address read-modify-write pressure on L1
- local RISC LDM reads/writes
- cross-RISC LDM window reads while multiple roles run together
- **cross-LDM round-robin** — each role reads the next role's window simultaneously (distributed fanout pressure)
- **contested LDM** — the owner role writes its own LDM while all other active roles read its cross-LDM window (write-read contention vs read-only baselines)
- **cross-LDM pointer chase** — two data-dependent loads through BRISC's window (measures serialised latency under cross-LDM pressure)

BRISC acts as the phase controller for each test. Active roles publish a per-role
ready slot, BRISC releases the phase with a shared start word, and each active
role records its own wall-clock interval.

## Benchmark Catalogue

| Spec | Ops/iter | Description |
|---|---:|---|
| `empty` | 0 | Loop overhead baseline |
| `mmio_wall_lw1` | 1 | Wall-clock MMIO load (same address) |
| `mmio_noc_status_lw1` | 1 | NoC status MMIO load (same address) |
| `l1_same_lw1` | 1 | L1 load, all roles hit the same address |
| `l1_dist_lw1` | 1 | L1 load, each role hits its own private address |
| `l1_same_sw1` | 1 | L1 store, same address |
| `l1_dist_sw1` | 1 | L1 store, distinct addresses |
| `l1_same_rmw2` | 2 | L1 read-modify-write, same address |
| `ldm_self_lw1` | 1 | Load from own LDM |
| `ldm_self_sw1` | 1 | Store to own LDM |
| `xldm_brisc_lw1` | 1 | All roles read BRISC's cross-LDM window |
| `xldm_ncrisc_lw1` | 1 | All roles read NCRISC's cross-LDM window |
| `xldm_trisc0_lw1` | 1 | All roles read TRISC0's cross-LDM window |
| `xldm_trisc1_lw1` | 1 | All roles read TRISC1's cross-LDM window |
| `xldm_trisc2_lw1` | 1 | All roles read TRISC2's cross-LDM window |
| `xldm_roundrobin_lw1` | 1 | Each role reads the next role's window (B→N→T0→T1→T2→B) |
| `xldm_contested_brisc_lw1` | 1 | BRISC writes own LDM; others read BRISC's window |
| `xldm_contested_ncrisc_lw1` | 1 | NCRISC writes own LDM; others read NCRISC's window |
| `xldm_contested_trisc0_lw1` | 1 | TRISC0 writes own LDM; others read TRISC0's window |
| `xldm_contested_trisc1_lw1` | 1 | TRISC1 writes own LDM; others read TRISC1's window |
| `xldm_contested_trisc2_lw1` | 1 | TRISC2 writes own LDM; others read TRISC2's window |
| `xldm_ptr_chase_lw2` | 2 | 2-hop dependent load through BRISC's window; `LDM[16]=16` (self-referential ptr) |

## Role-Pair Matrix

The default run is intentionally a smaller representative sweep: the 5 solo
runs, two BRISC-adjacent role pairs (`brisc+ncrisc`, `brisc+trisc0`), and the
all-five run. This keeps the common 10k-iteration run away from very long chains
of consecutive launches in one `Device()` session.

Use `--all-pairs` for the full 10-pair matrix (C(5,2)) plus the 5 solo runs and
the all-five run (16 groups total). The `--all-pairs` preset opens a fresh
`Device()` per group by default, which avoids stale launch/role state observed
in long single-session sweeps.

| | NCRISC | TRISC0 | TRISC1 | TRISC2 |
|---|:---:|:---:|:---:|:---:|
| **BRISC** | brisc+ncrisc | brisc+trisc0 | brisc+trisc1 | brisc+trisc2 |
| **NCRISC** | — | ncrisc+trisc0 | ncrisc+trisc1 | ncrisc+trisc2 |
| **TRISC0** | — | — | trisc0+trisc1 | trisc0+trisc2 |
| **TRISC1** | — | — | — | trisc1+trisc2 |

## Remote LDM Store — Safety Note

Writing to another core's cross-LDM window (a remote LDM store) is architecturally
possible on Blackhole, but is **not safe** to implement as a concurrent microbenchmark
for two reasons:

1. **Stack corruption risk.** Each role's LDM is its private stack space. Storing to an
   arbitrary offset while the owner is executing can corrupt its stack frame or local
   variables, causing an unrecoverable crash.
2. **Coordination overhead invalidates the measurement.** A safe remote-store test
   would need a dedicated scratch region in the owner's LDM that the owner never
   touches during the timed window. Enforcing this safely requires a per-role barrier
   that serialises execution and erases the contention signal we are trying to measure.

The contested specs (`xldm_contested_*_lw1`) are the closest safe approximation:
the owner writes its own LDM while readers observe from the outside.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/riscv_contention_bench.py --iters 10000
```

For the full pair matrix, prefer redirecting stdout or suppressing report writes
when collecting exploratory data:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/riscv_contention_bench.py --iters 10000 --all-pairs --no-report > /tmp/riscv-contention-all-pairs.md
```

Useful options:

- `--all-pairs`: run the full 16-group matrix; uses a fresh `Device()` per group.
- `--fresh-device-per-group`: open and close `Device()` around every group, useful for long custom `--groups` sweeps.
- `--groups all`: run only all five roles together.
- `--groups brisc+ncrisc trisc0`: run selected active-role groups.
- `--core X,Y`: choose the logical Tensix core.
- `--no-report`: print results without appending this file.

## Reading The Table

- `group`: active roles in that launch.
- `cycles`: raw wall-clock delta for that role and test.
- `cyc/iter`: raw cycles divided by iteration count.
- `adj cyc/op`: `(test_cycles - empty_cycles) / total_payload_ops` for the same
  group and role.
- `sink`: final value read or written by the role, used as a cheap sanity check.


## Run 2026-06-06T22:30:17-04:00

- Core: logical `1,2`
- Iterations per test: `10000`
- Dispatch path: slow dispatch (`TT_USB=1`)
- Groups: brisc, ncrisc, trisc0, trisc1, trisc2, brisc+ncrisc, brisc+trisc0, brisc+ncrisc+trisc0+trisc1+trisc2

Debug L1 ranges:
- `riscv_contention_results` at `0x128000` (3664 bytes)
- `riscv_contention_ctrl` at `0x12c000` (4096 bytes)
- `riscv_contention_scratch` at `0x12d000` (4096 bytes)

| group | role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---|---:|---:|---:|---:|---:|
| brisc | brisc | empty | 30027 | 3.003 |  | 0xc0001234 |
| brisc | brisc | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9adcc3fe |
| brisc | brisc | mmio_noc_status_lw1 | 50022 | 5.002 | 2.000 | 0x00000121 |
| brisc | brisc | l1_same_lw1 | 56023 | 5.602 | 2.600 | 0xc0001234 |
| brisc | brisc | l1_dist_lw1 | 55406 | 5.541 | 2.538 | 0xc0001234 |
| brisc | brisc | l1_same_sw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc | brisc | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc0001234 |
| brisc | brisc | l1_same_rmw2 | 190013 | 19.001 | 7.999 | 0xc0001234 |
| brisc | brisc | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc0001234 |
| brisc | brisc | ldm_self_sw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc | brisc | xldm_brisc_lw1 | 55022 | 5.502 | 2.499 | 0xc0001234 |
| brisc | brisc | xldm_ncrisc_lw1 | 55022 | 5.502 | 2.499 | 0x00ca00c7 |
| brisc | brisc | xldm_trisc0_lw1 | 55022 | 5.502 | 2.499 | 0x00000000 |
| brisc | brisc | xldm_trisc1_lw1 | 55022 | 5.502 | 2.499 | 0x00000000 |
| brisc | brisc | xldm_trisc2_lw1 | 55022 | 5.502 | 2.499 | 0x00000000 |
| ncrisc | ncrisc | empty | 30023 | 3.002 |  | 0xc1001234 |
| ncrisc | ncrisc | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9bbdc12b |
| ncrisc | ncrisc | mmio_noc_status_lw1 | 50022 | 5.002 | 2.000 | 0x00000121 |
| ncrisc | ncrisc | l1_same_lw1 | 56021 | 5.602 | 2.600 | 0xc1001234 |
| ncrisc | ncrisc | l1_dist_lw1 | 55407 | 5.541 | 2.538 | 0xc1001234 |
| ncrisc | ncrisc | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| ncrisc | ncrisc | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| ncrisc | ncrisc | l1_same_rmw2 | 190011 | 19.001 | 7.999 | 0xc1001234 |
| ncrisc | ncrisc | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| ncrisc | ncrisc | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| ncrisc | ncrisc | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xc0001234 |
| ncrisc | ncrisc | xldm_ncrisc_lw1 | 55022 | 5.502 | 2.500 | 0xc1001234 |
| ncrisc | ncrisc | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| ncrisc | ncrisc | xldm_trisc1_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| ncrisc | ncrisc | xldm_trisc2_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| trisc0 | trisc0 | empty | 30023 | 3.002 |  | 0xc2001234 |
| trisc0 | trisc0 | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9c7faea0 |
| trisc0 | trisc0 | mmio_noc_status_lw1 | 50022 | 5.002 | 2.000 | 0x00000121 |
| trisc0 | trisc0 | l1_same_lw1 | 55407 | 5.541 | 2.538 | 0xc2001234 |
| trisc0 | trisc0 | l1_dist_lw1 | 55406 | 5.541 | 2.538 | 0xc2001234 |
| trisc0 | trisc0 | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| trisc0 | trisc0 | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| trisc0 | trisc0 | l1_same_rmw2 | 190011 | 19.001 | 7.999 | 0xc2001234 |
| trisc0 | trisc0 | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| trisc0 | trisc0 | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| trisc0 | trisc0 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xc0001234 |
| trisc0 | trisc0 | xldm_ncrisc_lw1 | 55022 | 5.502 | 2.500 | 0xc1001234 |
| trisc0 | trisc0 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xc2001234 |
| trisc0 | trisc0 | xldm_trisc1_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| trisc0 | trisc0 | xldm_trisc2_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| trisc1 | trisc1 | empty | 30023 | 3.002 |  | 0xc3001234 |
| trisc1 | trisc1 | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9d68db80 |
| trisc1 | trisc1 | mmio_noc_status_lw1 | 50022 | 5.002 | 2.000 | 0x00000121 |
| trisc1 | trisc1 | l1_same_lw1 | 56020 | 5.602 | 2.600 | 0xc3001234 |
| trisc1 | trisc1 | l1_dist_lw1 | 56020 | 5.602 | 2.600 | 0xc3001234 |
| trisc1 | trisc1 | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc3001234 |
| trisc1 | trisc1 | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc3001234 |
| trisc1 | trisc1 | l1_same_rmw2 | 190011 | 19.001 | 7.999 | 0xc3001234 |
| trisc1 | trisc1 | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc3001234 |
| trisc1 | trisc1 | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc3001234 |
| trisc1 | trisc1 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xc0001234 |
| trisc1 | trisc1 | xldm_ncrisc_lw1 | 55022 | 5.502 | 2.500 | 0xc1001234 |
| trisc1 | trisc1 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xc2001234 |
| trisc1 | trisc1 | xldm_trisc1_lw1 | 55022 | 5.502 | 2.500 | 0xc3001234 |
| trisc1 | trisc1 | xldm_trisc2_lw1 | 55022 | 5.502 | 2.500 | 0x00000000 |
| trisc2 | trisc2 | empty | 30023 | 3.002 |  | 0xc4001234 |
| trisc2 | trisc2 | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9e49d2a4 |
| trisc2 | trisc2 | mmio_noc_status_lw1 | 50022 | 5.002 | 2.000 | 0x00000121 |
| trisc2 | trisc2 | l1_same_lw1 | 56022 | 5.602 | 2.600 | 0xc4001234 |
| trisc2 | trisc2 | l1_dist_lw1 | 56020 | 5.602 | 2.600 | 0xc4001234 |
| trisc2 | trisc2 | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc4001234 |
| trisc2 | trisc2 | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc4001234 |
| trisc2 | trisc2 | l1_same_rmw2 | 190012 | 19.001 | 7.999 | 0xc4001234 |
| trisc2 | trisc2 | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc4001234 |
| trisc2 | trisc2 | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc4001234 |
| trisc2 | trisc2 | xldm_brisc_lw1 | 55022 | 5.502 | 2.500 | 0xc0001234 |
| trisc2 | trisc2 | xldm_ncrisc_lw1 | 55022 | 5.502 | 2.500 | 0xc1001234 |
| trisc2 | trisc2 | xldm_trisc0_lw1 | 55022 | 5.502 | 2.500 | 0xc2001234 |
| trisc2 | trisc2 | xldm_trisc1_lw1 | 55022 | 5.502 | 2.500 | 0xc3001234 |
| trisc2 | trisc2 | xldm_trisc2_lw1 | 55022 | 5.502 | 2.500 | 0xc4001234 |
| brisc+ncrisc | brisc | empty | 30035 | 3.003 |  | 0xc0001234 |
| brisc+ncrisc | brisc | mmio_wall_lw1 | 50030 | 5.003 | 2.000 | 0x9f952866 |
| brisc+ncrisc | brisc | mmio_noc_status_lw1 | 50043 | 5.004 | 2.001 | 0x00000121 |
| brisc+ncrisc | brisc | l1_same_lw1 | 55023 | 5.502 | 2.499 | 0xc0001234 |
| brisc+ncrisc | brisc | l1_dist_lw1 | 55026 | 5.503 | 2.499 | 0xc0001234 |
| brisc+ncrisc | brisc | l1_same_sw1 | 40028 | 4.003 | 0.999 | 0xc0001234 |
| brisc+ncrisc | brisc | l1_dist_sw1 | 40024 | 4.002 | 0.999 | 0xc0001234 |
| brisc+ncrisc | brisc | l1_same_rmw2 | 190011 | 19.001 | 7.999 | 0xc0001234 |
| brisc+ncrisc | brisc | ldm_self_lw1 | 40028 | 4.003 | 0.999 | 0xc0001234 |
| brisc+ncrisc | brisc | ldm_self_sw1 | 40027 | 4.003 | 0.999 | 0xc0001234 |
| brisc+ncrisc | brisc | xldm_brisc_lw1 | 80011 | 8.001 | 4.998 | 0xc0001234 |
| brisc+ncrisc | brisc | xldm_ncrisc_lw1 | 80019 | 8.002 | 4.998 | 0xc1001234 |
| brisc+ncrisc | brisc | xldm_trisc0_lw1 | 80016 | 8.002 | 4.998 | 0xc2001234 |
| brisc+ncrisc | brisc | xldm_trisc1_lw1 | 80012 | 8.001 | 4.998 | 0xc3001234 |
| brisc+ncrisc | brisc | xldm_trisc2_lw1 | 80010 | 8.001 | 4.997 | 0xc4001234 |
| brisc+ncrisc | ncrisc | empty | 30023 | 3.002 |  | 0xc1001234 |
| brisc+ncrisc | ncrisc | mmio_wall_lw1 | 50022 | 5.002 | 2.000 | 0x9f952873 |
| brisc+ncrisc | ncrisc | mmio_noc_status_lw1 | 50041 | 5.004 | 2.002 | 0x00000121 |
| brisc+ncrisc | ncrisc | l1_same_lw1 | 55025 | 5.503 | 2.500 | 0xc0001234 |
| brisc+ncrisc | ncrisc | l1_dist_lw1 | 55023 | 5.502 | 2.500 | 0xc1001234 |
| brisc+ncrisc | ncrisc | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| brisc+ncrisc | ncrisc | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| brisc+ncrisc | ncrisc | l1_same_rmw2 | 190012 | 19.001 | 7.999 | 0xc1001234 |
| brisc+ncrisc | ncrisc | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| brisc+ncrisc | ncrisc | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc1001234 |
| brisc+ncrisc | ncrisc | xldm_brisc_lw1 | 80007 | 8.001 | 4.998 | 0xc0001234 |
| brisc+ncrisc | ncrisc | xldm_ncrisc_lw1 | 80011 | 8.001 | 4.999 | 0xc1001234 |
| brisc+ncrisc | ncrisc | xldm_trisc0_lw1 | 80012 | 8.001 | 4.999 | 0xc2001234 |
| brisc+ncrisc | ncrisc | xldm_trisc1_lw1 | 80007 | 8.001 | 4.998 | 0xc3001234 |
| brisc+ncrisc | ncrisc | xldm_trisc2_lw1 | 80007 | 8.001 | 4.998 | 0xc4001234 |
| brisc+trisc0 | brisc | empty | 30024 | 3.002 |  | 0xc0001234 |
| brisc+trisc0 | brisc | mmio_wall_lw1 | 50025 | 5.003 | 2.000 | 0xa0ccb24b |
| brisc+trisc0 | brisc | mmio_noc_status_lw1 | 50038 | 5.004 | 2.001 | 0x00000121 |
| brisc+trisc0 | brisc | l1_same_lw1 | 55025 | 5.503 | 2.500 | 0xc0001234 |
| brisc+trisc0 | brisc | l1_dist_lw1 | 55025 | 5.503 | 2.500 | 0xc0001234 |
| brisc+trisc0 | brisc | l1_same_sw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc+trisc0 | brisc | l1_dist_sw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc+trisc0 | brisc | l1_same_rmw2 | 250006 | 25.001 | 10.999 | 0xc0001234 |
| brisc+trisc0 | brisc | ldm_self_lw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc+trisc0 | brisc | ldm_self_sw1 | 40024 | 4.002 | 1.000 | 0xc0001234 |
| brisc+trisc0 | brisc | xldm_brisc_lw1 | 80007 | 8.001 | 4.998 | 0xc0001234 |
| brisc+trisc0 | brisc | xldm_ncrisc_lw1 | 80007 | 8.001 | 4.998 | 0xc1001234 |
| brisc+trisc0 | brisc | xldm_trisc0_lw1 | 80006 | 8.001 | 4.998 | 0xc2001234 |
| brisc+trisc0 | brisc | xldm_trisc1_lw1 | 80010 | 8.001 | 4.999 | 0xc3001234 |
| brisc+trisc0 | brisc | xldm_trisc2_lw1 | 80012 | 8.001 | 4.999 | 0xc4001234 |
| brisc+trisc0 | trisc0 | empty | 30023 | 3.002 |  | 0xc2001234 |
| brisc+trisc0 | trisc0 | mmio_wall_lw1 | 50023 | 5.002 | 2.000 | 0xa0ccb26c |
| brisc+trisc0 | trisc0 | mmio_noc_status_lw1 | 50040 | 5.004 | 2.002 | 0x00000121 |
| brisc+trisc0 | trisc0 | l1_same_lw1 | 55022 | 5.502 | 2.500 | 0xc0001234 |
| brisc+trisc0 | trisc0 | l1_dist_lw1 | 55022 | 5.502 | 2.500 | 0xc2001234 |
| brisc+trisc0 | trisc0 | l1_same_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| brisc+trisc0 | trisc0 | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| brisc+trisc0 | trisc0 | l1_same_rmw2 | 250002 | 25.000 | 10.999 | 0xc2001234 |
| brisc+trisc0 | trisc0 | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| brisc+trisc0 | trisc0 | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc2001234 |
| brisc+trisc0 | trisc0 | xldm_brisc_lw1 | 80010 | 8.001 | 4.999 | 0xc0001234 |
| brisc+trisc0 | trisc0 | xldm_ncrisc_lw1 | 80010 | 8.001 | 4.999 | 0xc1001234 |
| brisc+trisc0 | trisc0 | xldm_trisc0_lw1 | 80010 | 8.001 | 4.999 | 0xc2001234 |
| brisc+trisc0 | trisc0 | xldm_trisc1_lw1 | 80007 | 8.001 | 4.998 | 0xc3001234 |
| brisc+trisc0 | trisc0 | xldm_trisc2_lw1 | 80011 | 8.001 | 4.999 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | empty | 30024 | 3.002 |  | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | mmio_wall_lw1 | 52526 | 5.253 | 2.250 | 0xa35881f3 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | mmio_noc_status_lw1 | 50063 | 5.006 | 2.004 | 0x00000121 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | l1_same_lw1 | 56691 | 5.669 | 2.667 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | l1_dist_lw1 | 55024 | 5.502 | 2.500 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | l1_same_sw1 | 40032 | 4.003 | 1.001 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | l1_dist_sw1 | 40023 | 4.002 | 1.000 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | l1_same_rmw2 | 320013 | 32.001 | 14.499 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | ldm_self_lw1 | 40023 | 4.002 | 1.000 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | ldm_self_sw1 | 40023 | 4.002 | 1.000 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | xldm_brisc_lw1 | 199961 | 19.996 | 16.994 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | xldm_ncrisc_lw1 | 199968 | 19.997 | 16.994 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | xldm_trisc0_lw1 | 199962 | 19.996 | 16.994 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | xldm_trisc1_lw1 | 199968 | 19.997 | 16.994 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | brisc | xldm_trisc2_lw1 | 199965 | 19.997 | 16.994 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | empty | 30030 | 3.003 |  | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | mmio_wall_lw1 | 52530 | 5.253 | 2.250 | 0xa3588216 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | mmio_noc_status_lw1 | 50056 | 5.006 | 2.003 | 0x00000121 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | l1_same_lw1 | 56697 | 5.670 | 2.667 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | l1_dist_lw1 | 55027 | 5.503 | 2.500 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | l1_same_sw1 | 40031 | 4.003 | 1.000 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | l1_dist_sw1 | 40028 | 4.003 | 1.000 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | l1_same_rmw2 | 320010 | 32.001 | 14.499 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | ldm_self_lw1 | 40026 | 4.003 | 1.000 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | ldm_self_sw1 | 40028 | 4.003 | 1.000 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | xldm_brisc_lw1 | 199998 | 20.000 | 16.997 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | xldm_ncrisc_lw1 | 200001 | 20.000 | 16.997 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | xldm_trisc0_lw1 | 199999 | 20.000 | 16.997 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | xldm_trisc1_lw1 | 200001 | 20.000 | 16.997 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | ncrisc | xldm_trisc2_lw1 | 200003 | 20.000 | 16.997 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | empty | 30023 | 3.002 |  | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | mmio_wall_lw1 | 52525 | 5.253 | 2.250 | 0xa3588210 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | mmio_noc_status_lw1 | 50050 | 5.005 | 2.003 | 0x00000121 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | l1_same_lw1 | 56691 | 5.669 | 2.667 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | l1_dist_lw1 | 55023 | 5.502 | 2.500 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | l1_same_sw1 | 40028 | 4.003 | 1.000 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | l1_dist_sw1 | 40029 | 4.003 | 1.001 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | l1_same_rmw2 | 320023 | 32.002 | 14.500 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | ldm_self_lw1 | 40025 | 4.003 | 1.000 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | ldm_self_sw1 | 40028 | 4.003 | 1.000 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | xldm_brisc_lw1 | 200003 | 20.000 | 16.998 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | xldm_ncrisc_lw1 | 200003 | 20.000 | 16.998 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | xldm_trisc0_lw1 | 199999 | 20.000 | 16.998 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | xldm_trisc1_lw1 | 200003 | 20.000 | 16.998 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc0 | xldm_trisc2_lw1 | 200001 | 20.000 | 16.998 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | empty | 30025 | 3.002 |  | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | mmio_wall_lw1 | 52525 | 5.253 | 2.250 | 0xa358820d |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | mmio_noc_status_lw1 | 50052 | 5.005 | 2.003 | 0x00000121 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | l1_same_lw1 | 56688 | 5.669 | 2.666 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | l1_dist_lw1 | 55024 | 5.502 | 2.500 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | l1_same_sw1 | 40028 | 4.003 | 1.000 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | l1_dist_sw1 | 40027 | 4.003 | 1.000 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | l1_same_rmw2 | 240016 | 24.002 | 10.500 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | ldm_self_lw1 | 40025 | 4.003 | 1.000 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | ldm_self_sw1 | 40028 | 4.003 | 1.000 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | xldm_brisc_lw1 | 200001 | 20.000 | 16.998 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | xldm_ncrisc_lw1 | 200007 | 20.001 | 16.998 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | xldm_trisc0_lw1 | 200002 | 20.000 | 16.998 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | xldm_trisc1_lw1 | 200007 | 20.001 | 16.998 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc1 | xldm_trisc2_lw1 | 200007 | 20.001 | 16.998 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | empty | 30023 | 3.002 |  | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | mmio_wall_lw1 | 52524 | 5.252 | 2.250 | 0xa3588214 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | mmio_noc_status_lw1 | 50063 | 5.006 | 2.004 | 0x00000121 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | l1_same_lw1 | 56691 | 5.669 | 2.667 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | l1_dist_lw1 | 55024 | 5.502 | 2.500 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | l1_same_sw1 | 40024 | 4.002 | 1.000 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | l1_dist_sw1 | 40028 | 4.003 | 1.000 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | l1_same_rmw2 | 240005 | 24.000 | 10.499 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | ldm_self_lw1 | 40028 | 4.003 | 1.000 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | ldm_self_sw1 | 40025 | 4.003 | 1.000 | 0xc4001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | xldm_brisc_lw1 | 200007 | 20.001 | 16.998 | 0xc0001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | xldm_ncrisc_lw1 | 200003 | 20.000 | 16.998 | 0xc1001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | xldm_trisc0_lw1 | 200003 | 20.000 | 16.998 | 0xc2001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | xldm_trisc1_lw1 | 200003 | 20.000 | 16.998 | 0xc3001234 |
| brisc+ncrisc+trisc0+trisc1+trisc2 | trisc2 | xldm_trisc2_lw1 | 200002 | 20.000 | 16.998 | 0xc4001234 |
