# NoC Cross-Endpoint Interference

This report covers peer-L1 streams launched on NoC0 and NoC1 at the same time.
The matrix cases are:

- `same-l1-target`: two source cores write into one L1 target endpoint.
- `same-l1-source`: one source core launches BRISC/NoC0 and NCRISC/NoC1 streams.
- `disjoint-l1`: both source and target endpoints are disjoint.

Full matrix command:

```bash
python3 microbenching/noc/riscv_noc_cross_endpoint_interference.py \
  --cases same-l1-target,same-l1-source,disjoint-l1 \
  --bytes 262144 --repeats 2
```

Scheduler implication from the representative hardware run: L1 source and
target endpoint pressure does not appear shared across NoC0 and NoC1 at this
packet size. Same-source, same-target, and disjoint cases all reached about
110 B/cyc aggregate from two about-56 B/cyc single streams, with only small
per-stream loss.

## Run 2026-06-13T17:36:38-04:00 L1 cross-NoC endpoint interference

- Bytes per stream repeat: `131072`
- Repeats: `1`
- Start gate lead: `200000000` cycles
- Traffic: two peer-L1 nonposted write streams, one on NoC0 and one on NoC1
- Counters: parentheses show per-stream NIU write-ack counter delta

| case | stream A | stream B | A alone B/cyc (ctr) | B alone B/cyc (ctr) | A mixed B/cyc (ctr) | B mixed B/cyc (ctr) | mixed aggregate B/cyc | mixed window cyc |
|---|---|---|---:|---:|---:|---:|---:|---:|
| same-l1-target | NoC0 `1,4->4,4` | NoC1 `10,4->4,4` | 56.327 (8) | 56.914 (8) | 55.026 (8) | 55.072 (8) | 109.960 | 2384 |
| same-l1-source | NoC0 `4,4->7,4` | NoC1 `4,4->1,4` | 56.521 (8) | 56.497 (8) | 55.422 (8) | 56.351 (8) | 110.843 | 2365 |
| disjoint-l1 | NoC0 `1,5->4,5` | NoC1 `13,6->10,6` | 56.717 (8) | 56.889 (8) | 55.823 (8) | 56.399 (8) | 111.408 | 2353 |
