
## Run 2026-06-30T20:34:11-04:00 NoC same-VC crossing probe

- NoC: `0`
- VCs: `1`
- Bytes per sender: `262144`
- Route order assumed for link-set selection: `xy`
- Traffic: posted unicast writes, all streams in a case use the same static VC

| case | noc | vc | streams | pairs | raw routes | shared router nodes | shared directed links | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | per-stream mean B/cyc | per-stream min | per-stream max | bad sentinel rows | note |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cross-router-single-0 | 0 | 1 | 1 | `7,10->11,10` | `10,10->12,10` | 0 | 0 | 0.25 | 4058 | 64.599 | 4379 | 59.864 | 59.864 | 59.864 | 59.864 | 0 | single-stream baseline for paired case |
| cross-router-single-1 | 0 | 1 | 1 | `10,9->10,11` | `11,9->11,11` | 0 | 0 | 0.25 | 4018 | 65.242 | 4334 | 60.485 | 60.485 | 60.485 | 60.485 | 0 | single-stream baseline for paired case |
| cross-router | 0 | 1 | 2 | `7,10->11,10 10,9->10,11` | `10,10->12,10 11,9->11,11` | 1 | 0 | 0.50 | 4672 | 112.219 | 4976 | 105.363 | 60.605 | 60.499 | 60.710 | 0 | paths share router node raw 11,10 but share 0 directed links; all route nodes are live Tensix raw positions |
| shared-link-single-0 | 0 | 1 | 1 | `1,2->5,10` | `1,2->5,10` | 0 | 0 | 0.25 | 4018 | 65.242 | 4418 | 59.335 | 59.335 | 59.335 | 59.335 | 0 | single-stream baseline for paired case |
| shared-link-single-1 | 0 | 1 | 1 | `2,2->5,11` | `2,2->5,11` | 0 | 0 | 0.25 | 4026 | 65.113 | 4419 | 59.322 | 59.322 | 59.322 | 59.322 | 0 | single-stream baseline for paired case |
| shared-link | 0 | 1 | 2 | `1,2->5,10 2,2->5,11` | `1,2->5,10 2,2->5,11` | 10 | 11 | 0.50 | 7923 | 66.173 | 8578 | 61.120 | 31.262 | 31.016 | 31.508 | 0 | paths share 11 directed link(s), including raw 2,2->3,2; all route nodes are live Tensix raw positions |
