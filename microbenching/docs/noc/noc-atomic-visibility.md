
# NoC Atomic Visibility

Bench source: `microbenching/noc/riscv_noc_atomic_visibility_bench.py`.

This report covers BRISC-issued NoC atomic/semaphore increments with target-side
polling of the final L1 value. The matrix includes:

- many initiators into one target, with row/column/diagonal placement;
- one initiator fanning out to many targets;
- same-target versus separate-target streams;
- atomics interleaved with nonposted unicast writes to the same target L1.

The default `representative` suite is intentionally small. Run the full host
lowering check without hardware access:

```bash
PYTHONPATH=. python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --dry-run --suite full --counts 2 --iters 4
```

Submit the full hardware matrix through the shared queue:

```bash
PYTHONPATH=. python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --suite full --counts 2,4 --iters 128
```

The first hardware subset below was queued as job `68f36e58`:

```bash
PYTHONPATH=. python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0 --counts 2 --cases same-row-atomic,same-row-sem,mixed-row --iters 32 --max-polls 10000000
```

The second hardware subset below was queued as job `574beee0`:

```bash
PYTHONPATH=. python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0 --counts 2 --cases same-col-atomic,same-diag-atomic,separate-row-atomic,one-many-row-atomic --iters 32 --max-polls 10000000
```

Scheduler note: the pure atomic/semaphore same-target K=2 rows give an
observed-window mean near 19.5 cycles/atomic op before subtracting hop,
response, and polling effects. That supports the existing
`atomic_target_cycles = 24.0` default as a conservative placeholder, but it is
not enough evidence to retune the model globally.

## Run 2026-06-13T17:35:32-04:00

- Suite: `representative`
- Iterations per sender-target edge: `32`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `19.6 cycles/op observed-window mean across same-target rows`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | noc | K | op | initiators | targets | hops | atomic ops | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same-row-atomic | 0 | 2 | atomic | `12,4` `13,4` | `14,4` | 1..2 | 64 | 1378 | 0.04644 | 1253 | 0.05108 | -125 | 0.000 | 0 | 90 |
| same-row-sem | 0 | 2 | sem | `12,4` `13,4` | `14,4` | 1..2 | 64 | 1385 | 0.04621 | 1254 | 0.05104 | -131 | 0.001 | 0 | 90 |
| same-row-mixed | 0 | 2 | mixed | `12,4` `13,4` | `14,4` | 1..2 | 64 | 2248 | 0.02847 | 2159 | 0.02964 | -89 | 0.003 | 0 | 146 |

## Run 2026-06-13T17:36:04-04:00

- Suite: `representative`
- Iterations per sender-target edge: `32`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `19.4 cycles/op observed-window mean across same-target rows`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | noc | K | op | initiators | targets | hops | atomic ops | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same-col-atomic | 0 | 2 | atomic | `1,9` `1,10` | `1,11` | 1..2 | 64 | 1333 | 0.04801 | 1229 | 0.05207 | -104 | 0.001 | 0 | 89 |
| same-diag-atomic | 0 | 2 | atomic | `12,9` `13,10` | `14,11` | 2..4 | 64 | 1482 | 0.04318 | 1260 | 0.05079 | -222 | 0.001 | 0 | 90 |
| separate-row-atomic | 0 | 2 | atomic | `1,4` `2,4` | `3,4` `4,4` | 2 | 64 | 1370 | 0.04672 | 1218 | 0.05255 | -152 | 0.000 | 0 | 88 |
| one-many-row-atomic | 0 | 2 | atomic | `1,4` | `2,4` `3,4` | 1..2 | 64 | 2417 | 0.02648 | 2255 | 0.02838 | -162 | 0.000 | 0 | 164 |
