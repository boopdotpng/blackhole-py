
## Run 2026-06-30T02:37:26-04:00 NoC counter probe

- NoC: `0`; source: `1,4`; target: `6,4`; route: `1,4 2,4 3,4 4,4 5,4 6,4`
- Static VC: `1`; priority: `0`; posted: `False`
- Packets: `16`; bytes/packet: `16384`; sampler iterations: `512`
- Each row is a RISC-side before/after delta from that core's local NoC/NIU registers. `vc p1/p2 flits` are router flit counter deltas for the selected VC only.

| core | role | window cyc | cmd accepted | np wr req sent | np data sent | p wr req sent | p data sent | ack recv | slv req accepted | slv np wr recv | slv np data recv | slv p wr recv | slv p data recv | slv ack sent | out max | cmd avail min | selected vc p1 | selected vc p2 | nonzero flit counters | cmd ovfl |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `1,4` | sender | 4462 | 17 | 17 | 4097 | 0 | 0 | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `6,4` | receiver | 14530 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 17 | 4097 | 0 | 0 | 17 | 0 | 0x00000000 | 0 | 0 | `vc6:p1=0:p2=9 vc7:p1=0:p2=8` | 0 |
| `2,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `3,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `4,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `5,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |

Interpretation:

- The NIU master/slave counters are volume-aware. For 16 full-size 16 KiB
  packets plus the 4-byte marker, the sender and receiver report `4097` data
  words (`16 * 256 + 1`) and `17` requests.
- The router per-VC counter exposed at `PORT*_FLIT_COUNTER_*` increments once
  per packet/header in this command-buffer path. A size check with the same 17
  commands but 1 KiB payloads reported `257` NIU data words while the selected
  VC router counter still reported `17`.
- The route samplers on `2,4` through `5,4` all see `vc1:p2=17`, matching the
  static VC chosen for the forward write stream. That makes the register useful
  for proving route/VC usage, even though it does not expose payload volume.
- Nonposted write ACKs show up at the receiver/router as `vc6/vc7` traffic and
  as `slv ack sent`; posted writes remove that return traffic while preserving
  the forward `vc1` packet count.

## Run 2026-06-30T02:37:30-04:00 NoC counter probe

- NoC: `0`; source: `1,4`; target: `6,4`; route: `1,4 2,4 3,4 4,4 5,4 6,4`
- Static VC: `1`; priority: `0`; posted: `True`
- Packets: `16`; bytes/packet: `16384`; sampler iterations: `512`
- Each row is a RISC-side before/after delta from that core's local NoC/NIU registers. `vc p1/p2 flits` are router flit counter deltas for the selected VC only.

| core | role | window cyc | cmd accepted | np wr req sent | np data sent | p wr req sent | p data sent | ack recv | slv req accepted | slv np wr recv | slv np data recv | slv p wr recv | slv p data recv | slv ack sent | out max | cmd avail min | selected vc p1 | selected vc p2 | nonzero flit counters | cmd ovfl |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `1,4` | sender | 4278 | 17 | 0 | 0 | 17 | 4097 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `6,4` | receiver | 14508 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 0 | 0 | 17 | 4097 | 0 | 0 | 0x00000000 | 0 | 0 | `-` | 0 |
| `2,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `3,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `4,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
| `5,4` | sampler | 14880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x00000000 | 0 | 17 | `vc1:p1=0:p2=17` | 0 |
