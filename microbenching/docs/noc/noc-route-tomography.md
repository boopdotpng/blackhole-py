# NoC Route Tomography

This report is appended by `microbenching/noc/riscv_noc_route_tomography.py`.

The benchmark generates diagonal L1 victim payloads and two adversaries per
case: a same-row stream that overlaps the victim only under `xy`, and a
same-column stream that overlaps only under `yx`. The adversary that causes the
larger victim slowdown votes for the payload route order. DRAM rows in this
report are generated model coverage for read/write endpoint routes; endpoint
bandwidth is measured separately by `riscv_dram_noc_bench.py`.

Full L1 route-order matrix:

```bash
PYTHONPATH=. python3 microbenching/noc/riscv_noc_route_tomography.py --nocs 0,1 --ops write,read --quadrants ne,nw,sw,se --include-dram-model
```

Use `--max-cases N` to run a representative prefix through the device queue
before launching the full matrix.

## Run 2026-06-13T17:33:54-04:00

- NoCs: `0`
- Ops: `write,read`
- Quadrants requested: `ne`
- Bytes per stream repeat: `131072`
- Repeats: `1`
- Start gate lead: `50000000` cycles
- ENABLED_TENSIX_COL: `0x00003bf7`
- Harvested raw Tensix columns: `[6, 15]`
- Traffic: L1 write/read route tomography runs one victim alone, then victim plus an X-leg adversary, then victim plus a Y-leg adversary.
- Interpretation: the adversary that slows the victim more identifies the route-order leg used by the payload.

Generated L1 cases:

| case | noc | quadrant | victim translated | victim raw | xy adversary translated/raw | yx adversary translated/raw | xy-only links | yx-only links |
|---|---:|---|---|---|---|---|---:|---:|
| qne_noc0_1,2_to_2,5 | 0 | ne | `1,2->2,5` | `1,2->2,5` | `13,2->2,2` / `14,2->2,2` | `1,3->1,4` / `1,3->1,4` | 4 | 4 |

Measured L1 results:

| op | noc | quadrant | victim raw | baseline B/cyc | xy-cross victim B/cyc | yx-cross victim B/cyc | xy ratio | yx ratio | vote | counters base/xy/yx | adversary B/cyc xy/yx |
|---|---:|---|---|---:|---:|---:|---:|---:|---|---|---|
| write | 0 | ne | `1,2->2,5` | 54.432 | 29.231 | 53.984 | 0.537 | 0.992 | xy | 8/8/8 | 30.503/57.716 |
| read | 0 | ne | `1,2->2,5` | 53.740 | 29.871 | 53.109 | 0.556 | 0.988 | xy | 8/8/8 | 30.804/57.087 |

- NoC0 read: votes xy/yx/inconclusive = `1/0/0`, mean victim ratios xy/yx = `0.556/0.988`, route-order readout `xy`.
- NoC0 write: votes xy/yx/inconclusive = `1/0/0`, mean victim ratios xy/yx = `0.537/0.992`, route-order readout `xy`.
- Scheduler implication: this subset supports `route_order="xy"` for NoC0 L1 read payloads.
- Scheduler implication: this subset supports `route_order="xy"` for NoC0 L1 write payloads.
- Scheduler constants: no bandwidth or latency constants are changed by this route-order run.

Generated DRAM endpoint route cases (model coverage; run `riscv_dram_noc_bench.py` for endpoint bandwidth):

| op | noc | quadrant | worker translated/raw | bank | endpoint | dram router | hops xy/yx | unique links xy/yx |
|---|---:|---|---|---:|---:|---|---:|---:|
| dram_read | 0 | ne | `1,5` / `1,5` | 0 | 0 | `0,0` | 6/6 | 6/6 |
| dram_write | 0 | ne | `4,10` / `4,10` | 3 | 2 | `9,11` | 6/6 | 6/6 |
