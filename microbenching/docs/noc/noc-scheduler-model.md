# NoC Scheduler Model

This is the working model for estimating Blackhole/P100a NoC cycle counts and
contention from a static set of transactions. It intentionally ignores DRISC DMA
for now and models the raw NIU/dataflow path.

## What Is Understood

- A raw on-device NoC command selects NoC0 vs NoC1 by programming the matching
  NIU register instance. The x/y target fields are separate from NoC selection.
- Each tile has two NIUs, one per NoC, with four request initiator command
  buffers.
- A single physical packet payload is at most 16 KiB. Larger transfers should be
  modeled as a stream of 16 KiB packets unless the benchmark explicitly relies
  on hardware auto-splitting.
- NoC writes move the payload from the initiator/source endpoint to the target
  endpoint.
- NoC reads issue a small request from the initiator to the target, then the
  payload returns from the target endpoint to the initiator endpoint. The
  scheduler charges a one-flit request path and then offsets the return payload
  path by the request arrival time.
- Harvested Tensix columns must be handled before route modeling. Friendly
  translated worker x coordinates do not necessarily equal physical router x
  positions.
- For this P100a, the observed harvested/remapped Tensix columns are physical
  columns 6 and 15. Friendly live worker coordinates skip/remap through the
  firmware/NIU translation table, so a scheduler must not assume compact worker
  x is physical x.
- DRAM endpoints are not worker tiles. The programmed bank table can expose
  translated endpoint coordinates around x=17/18 and y>=12, but route/contention
  modeling should use the physical DRAM router tiles from `ttk.addrs.Dram`:
  banks 0..3 at x=0, banks 4..7 at x=9, with three endpoint y choices per bank.
  The scheduler keeps this separate from the programmed coordinate layer.
- The physical route model uses the 17x12 Blackhole router grid from
  `ttk.blackhole_coords`. Older exploratory scripts had a 20x25 placeholder
  topology to explain host/translated coordinates; that is not the grid used
  for hop or contention modeling.

## Current Calibration Constants

These are the defaults in `microbenching/models/noc_scheduler.py`. They are
conservative and should be overwritten by per-device benchmark results when we
feed the scheduler real traces.

| quantity | default | source / interpretation |
|---|---:|---|
| clock | 1350 MHz | board runtime clock used by current benches |
| max payload packet | 16 KiB | Blackhole `NOC_MAX_BURST_SIZE` |
| per-hop startup latency | 9 cycles | one-way packet latency bench slope |
| packet base latency | 45 cycles | rough intercept, still needs refinement |
| packet issue cost | 8 cycles | placeholder for command-buffer pressure |
| link bandwidth | 61.2 B/cyc | fresh adjacent L1->L1 single-pair NoC0 run |
| L1 ingress bandwidth | 63.1 B/cyc | same-target arbitration aggregate on NoC0/NoC1 |
| DRAM endpoint read bandwidth | 47.3 B/cyc | single-bank raw NoC read ceiling |
| DRAM endpoint write bandwidth | 47.3 B/cyc | single-bank raw NoC write ceiling |
| DRAM read fabric NoC0 | 275.6 B/cyc | fitted internal resource for 118-core spread/split3 read |
| DRAM read fabric NoC1 | 164.7 B/cyc | fitted internal resource for 118-core spread/split3 read |
| DRAM write fabric NoC0 | 119.8 B/cyc | fitted internal resource for 118-core spread/split3 write |
| DRAM write fabric NoC1 | 253.6 B/cyc | fitted internal resource for 118-core spread/split3 write |
| multicast path-reserve overhead | 0 cycles | placeholder; scheduler can charge it but current default leaves it neutral |
| read request bytes | 64 B | conservative one-flit read command/request link occupancy |
| atomic request bytes | 64 B | conservative one-flit request-side link occupancy |
| atomic response bytes | 64 B | conservative one-flit response-side link occupancy |
| atomic target cycles | 24 cycles | placeholder target update cost; needs direct semaphore calibration |
| default NIU write pool | 1 | ordinary BRISC write-owned command slot, not a generic FIFO |
| physical NIU command slots | 4 | role-owned slots; exact traces may name `cmd_buf` 0..3 |
| command-buffer hold | 45 cycles | placeholder control-plane hold time per issued packet |
| route order | `xy` | dimension order used by current model; `yx` is also supported for experiments |

Important measured aggregate points:

| bench | result |
|---|---:|
| raw DRAM read, spread, NoC0, 118 cores | about 279 GB/s |
| raw DRAM write, spread split3, NoC1, 118 cores | about 304-315 GB/s |
| raw DRAM single-bank endpoint | about 64 GB/s |
| fastest add1 so far, preferred read + split3 write | about 4996 us for 483328 tiles |
| fastest add1 effective traffic rate | about 594 GB/s, about 0.099 TFLOP/s |

Fresh 118-core raw DRAM spread/split3 run using 16 KiB packets and 1 MiB/core,
compared with the current default scheduler constants:

| op | NoC | measured B/cyc | measured GB/s | default model B/cyc | error |
|---|---:|---:|---:|---:|---:|
| read | 0 | 254.732 | 343.9 | 253.220 | -0.59% |
| read | 1 | 157.432 | 212.5 | 159.566 | +1.36% |
| write | 0 | 115.992 | 156.6 | 118.242 | +1.94% |
| write | 1 | 234.387 | 316.4 | 245.333 | +4.67% |

The `dram_*_fabric:nocN` constants are fitted internal resources, not raw
end-to-end benchmark rates. The model still charges endpoint resources, links,
L1 ingress, hop offsets, and packet startup on top of fabric pressure. Using the
raw measured B/cyc directly as the resource capacity double-counts those costs
and underpredicts throughput.

The calibration helper can refit these constants. Exact packet scheduling now
uses a heap of candidate streams and `record_packets=False` in the calibrator,
so it keeps exact resource timelines without materializing every packet in the
JSON/report structures. Use the compressed analytic mode for quick fabric-cap
exploration, then validate selected points with exact scheduling:

```bash
PYTHONPATH=. python3 microbenching/models/noc_scheduler_calibrate.py --fast-analytic --bytes-per-core 1048576 --iterations 12
PYTHONPATH=. python3 microbenching/models/noc_scheduler_calibrate.py --cases read:0 --bytes-per-core 1048576 --iterations 4
```

Current measured runtime on this host:

| mode | case | runtime |
|---|---|---:|
| exact cycle-only | one DRAM direction, 118 cores, 1 MiB/core, 1 bisection iteration | about 1.7 s |
| exact cycle-only | two DRAM directions, 118 cores, 1 MiB/core, 2 bisection iterations | about 6.5 s |
| analytic | four DRAM directions, 118 cores, 1 MiB/core, 12 bisection iterations | about 0.12 s |

At 256 KiB/core, analytic-vs-exact error with current defaults is:

| op | NoC | exact B/cyc | analytic B/cyc | analytic error |
|---|---:|---:|---:|---:|
| read | 0 | 254.220 | 274.073 | +7.81% |
| read | 1 | 160.940 | 164.146 | +1.99% |
| write | 0 | 118.178 | 119.511 | +1.13% |
| write | 1 | 244.928 | 252.288 | +3.01% |

Fresh adjacent L1->L1 NoC0 aggregate run:

| pairs | sender agg B/cyc | receiver agg B/cyc | note |
|---:|---:|---:|---|
| 1 | 61.184 | 61.677 | single adjacent pair |
| 2 | 122.126 | 123.224 | scales linearly |
| 4 | 241.802 | 243.983 | scales linearly |
| 8 | 448.925 | 452.289 | lower per-pair from launch/window skew, not a hard cap |
| 16 | 891.362 | 897.705 | still scales |
| 32 | 1778.943 | 1791.003 | still scales |
| 50 | 2764.940 | 2784.323 | no aggregate NoC0 cap observed here |

The add1 effective traffic metric counts read + compute input + write as 3 tile
touches. External DRAM traffic is 2/3 of that metric.

The L1 aggregate run is not evidence for a global NoC0 payload cap: 50 adjacent
pairs still scaled almost linearly. The lower per-pair 8+ pair windows include
core launch/window skew. The scheduler can model that if callers provide
per-stream `start_cycle`; otherwise it estimates the NoC portion from the point
where each stream is ready to issue.

With harvested-aware worker placement, physical DRAM bank endpoints, `xy` read
routes, `yx` write routes, directed-link resources, endpoint resources, and
fitted DRAM fabric resources, the scheduler now has fitted defaults for all four
DRAM NoC/op directions in the 118-core spread/split3 pattern.

The fitting utility is:

```bash
PYTHONPATH=. python3 microbenching/models/noc_scheduler_calibrate.py --bytes-per-core 1048576 --iterations 12
```

Fresh directed-link overlap runs using `riscv_noc_link_overlap.py`:

| NoC | route | case | streams | measured sender B/cyc | model B/cyc | note |
|---:|---|---|---:|---:|---:|---|
| 0 | xy | parallel | 6 | 364.764 | 365.855 | disjoint physical links overlap |
| 0 | xy | shared link | 6 | 62.302 | 61.130 | six streams serialize on one directed link |
| 1 | yx | parallel | 6 | 364.680 | 365.855 | NoC1 also overlaps disjoint links |
| 1 | yx | shared link | 6 | 62.295 | 61.130 | NoC1 also serializes shared directed links |

The same runs used `ENABLED_TENSIX_COL=0x00003bf7`, harvested raw Tensix
columns `[6, 15]`, and live raw columns `[1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14,
16]`. This is strong evidence that the directed-link resource model is the right
shape for unicast L1 writes: independent links overlap, and one shared directed
link collapses aggregate bandwidth to about one stream.

Fresh same-target arbitration run using `riscv_noc_arbitration_bench.py` with
16 KiB packets and 64 packets/sender:

| NoC | senders | target | aggregate B/cyc | per-stream B/cyc | note |
|---:|---:|---|---:|---|---|
| 0 | 2 | `14,4` | 62.566 | `31.283 31.524` | roughly equal |
| 0 | 4 | `14,4` | 62.978 | `15.745 15.803 21.087 31.601` | near target favored |
| 0 | 8 | `14,4` | 63.108 | `7.889 7.904 9.035 10.533 12.590 15.769 21.023 31.494` | near target favored |
| 1 | 2 | `1,4` | 62.581 | `31.524 31.291` | roughly equal |
| 1 | 4 | `1,4` | 62.933 | `31.532 21.057 15.794 15.735` | position-biased |
| 1 | 8 | `1,4` | 63.044 | `31.442 21.016 15.701 12.620 10.522 9.023 7.896 7.881` | position-biased |

This validates the scheduler's aggregate `l1_in:<target>` resource at about
63.1 B/cyc. It does not yet validate per-stream fairness: the hardware clearly
does not divide target ingress evenly under a many-to-one line pattern.

Fresh mixed L1 read/write runs using `riscv_noc_mixed_rw_overlap.py` with
distinct active source cores, 256 KiB per stream:

| NoC | case | read payload | write payload | mixed aggregate B/cyc | model aggregate B/cyc | note |
|---:|---|---|---|---:|---:|---|
| 0 | independent | `1,4->4,4` | `10,5->13,5` | 117.897 | 120.600 | read-return and write payload use disjoint directed links |
| 0 | shared payload link | `1,4->4,4` | `2,4->5,4` | 62.744 | 60.683 | both streams serialize on shared directed links |
| 1 | independent | `4,4->1,4` | `13,5->10,5` | 117.950 | 120.600 | NoC1 also overlaps independent mixed traffic |
| 1 | shared payload link | `4,4->1,4` | `5,4->2,4` | 62.505 | 60.747 | NoC1 also serializes shared mixed links |

This validates mixed read/write L1 traffic for distinct initiators: no extra
global read/write interference term is needed beyond directed links, endpoint
resources, and NIU issue pressure. The older same-core VC sweep in
`riscv_noc_contention_probe.py e --vc-sweep` hung on this device when BRISC and
NCRISC issued simultaneous read/write traffic against the same remote L1 address
range; treat that probe shape as unsafe until debugged.

## 2026-06-13 Hardware Sweep

This sweep was run through `tt-device-queue` to refresh the scheduler-facing NoC
coverage. Detailed tables were appended by the individual report-capable
benchmarks under `microbenching/docs/noc/`.

### NIU Command Width / Queueing

Treat ordinary BRISC writes as one-wide. The NIU has four physical command
slots, but Metal assigns those slots by owner and role rather than exposing them
as four interchangeable write queue entries. In dynamic BRISC/NCRISC mode,
BRISC owns slots 0 and 1, with slot 0 used for writes and slot 1 used for
read/atomic traffic; NCRISC similarly uses slots 2 and 3.

The practical scheduler rule is:

- Do not model `cmd_buf` 0..3 as a generic write FIFO.
- If a write helper reuses the write-owned slot, it can issue another packet
  when that slot is ready and drain write acks later; that is outstanding fabric
  traffic, not extra NIU write queue width.
- Only model more than one write command slot when a low-level trace proves the
  extra slot was fully initialized as a write slot and is intentionally stolen
  from its normal role.

The exploratory round-robin command-buffer probe was removed after confirming
that the unsafe case was only exercising an invalid firmware/helper setup.

### Position-Dependent Many-To-One Writes

The user note that same-target arbitration follows a position-dependent
sequence is confirmed by the refreshed arbitration run, job `62d0798e`.
Aggregate target ingress stays near one L1 write port, about 61-63 B/cyc, while
the per-stream distribution follows the expected near/far priority ratios.

Examples with 16 KiB packets and 128 packets/sender:

| NoC | senders | aggregate B/cyc | per-stream B/cyc |
|---:|---:|---:|---|
| 0 | 2 | 62.783 | `31.392 31.508` |
| 0 | 4 | 63.062 | `15.766 15.795 21.020 31.611` |
| 0 | 8 | 63.098 | `7.887 7.895 9.024 10.521 12.623 15.766 21.006 31.505` |
| 1 | 2 | 62.811 | `31.520 31.407` |
| 1 | 4 | 63.013 | `31.520 21.051 15.784 15.754` |
| 1 | 8 | 63.182 | `31.558 21.080 15.799 12.643 10.536 9.035 7.906 7.898` |

Scheduler implication: the aggregate `l1_in:<target>` resource is enough for
hotspot/cycle prediction, but completion-order prediction needs a deterministic
position-priority model rather than equal fair sharing.

### Other Refreshed Runs

| area | job | command shape | result |
|---|---|---|---|
| packet latency | `3373c44a` | read/write, NoC0/1, 4..16 KiB, 1D and 2D auto routes | PASS; small-packet intercept remains high, slope about 7-8 cyc/hop in this loop |
| row stream sweep | `1c04b1f3` | row mode, NoC0/1, <=8 hops, 1 MiB streams | PASS after passing harvested coordinate map into the helper |
| all-to-one stream sweep | `37c36d52` | target `(1,2)`, 8 sources, 1 MiB streams | PASS; single source/target streams stay near 63-65 B/cyc |
| DRAM preferred | `055589e4` | spread, preferred endpoint, 1..118 cores | PASS; 118-core read N0 about 285 GB/s, write N1 about 245 GB/s |
| DRAM split3 | `dca60895` | spread, split3 endpoint, 1..118 cores | PASS; 118-core read N0 about 294 GB/s, write N1 about 315 GB/s |
| mixed read/write | `4a4b3479`, `acf58a23` | distinct sources, independent vs shared payload link, 1 MiB | PASS; independent about 124/122 B/cyc, shared-link about 63.5 B/cyc |
| multicast one-way | `b262e02b` | row/column/rect, NoC0/1, x/y majors | PASS |
| multicast VC-linked | `31528b9a` | NoC0/1, x/y, depths 1/2/4, 64..16 KiB | PASS |
| dual multicast | `d5ea13a3` | solo/disjoint/shared-columns, NoC0/1, x/y | PASS |
| overlap multicast | `b7ce0d93` | two overlapping rectangles, NoC0/1, x/y | PASS |
| competing matmul-style multicast | `6e08eedc` | disjoint/adjacent/overlap/nested, chunks 1/4 | PASS |
| rect sweep | `3052ebb0` | logical rectangles, skip unmapped harvested coords | PASS; NoC1 logical encoding only partially covers some physical rectangles |
| topology | `27b58305` | experiments C/D | PASS |
| packet latency | `9bc25ff5` | read/write, NoC0/1, 4..16 KiB, 1D and 2D routes | PASS; blocking small-packet intercept about 175-186 cycles, slope about 4.8-5.3 cyc/hop |
| same-target arbitration | `6e017354` | K=2..8, 16 KiB, NoC0/1 | PASS; aggregate about 63 B/cyc, deterministic position-biased split |
| DRAM endpoint matrix | `3e59ab0d` | banks 0..6, endpoints 0..2, read/write, NoC0/1, one core | PASS; single-source endpoint variation is small |
| same-initiator active commands | `17d0478d`, `bbc60434` | one BRISC, same NoC, read slot 1 plus write slot 0 | PASS; read+write reaches about 120-122 B/cyc with separate targets and also completes with same remote target |

Known failures / unsafe shapes from this sweep:

- Extra NIU write slots: skipped by default. Metal's command-buffer ownership
  makes ordinary BRISC writes effectively one-wide unless a trace proves custom
  command-buffer initialization.
- Same-core BRISC+NCRISC mixed read/write: current two-RISC probe shape timed
  out even with distinct remote L1 targets. A BRISC-only same-initiator probe
  passes, so treat this as a probe/startup issue, not as a NoC limitation.
- `riscv_noc_mcast_throughput.py` full matrix with NoC0/1, x/y, counts
  1/2/4/8, sizes 64/1024/16384 timed out on receiver `(10,4)`. Smaller split
  runs passed for NoC0/x and NoC1/y with counts 1/2/4.
- `riscv_noc_mcast_rect_sweep.py` old default aborted on translated x=8, which
  is unmapped on this harvested chip. The script now skips unmapped rectangles.

## Scheduler Resource Model

The scheduler splits every transaction into packets and treats each transaction
as an active stream once its dependencies are satisfied. Exact scheduling uses a
min-heap of stream candidates. When a candidate reaches the top, its feasible
start is recomputed against the latest resource timelines before launch, which
preserves earliest-feasible ordering without rescanning every active stream for
every packet. Independent streams overlap, while streams sharing a link, L1
ingress, DRAM endpoint, DRAM fabric, command buffer, or initiator NIU serialize
on that resource.
The model assumes `start_cycle` is the cycle where that stream is ready to
issue after dependency release. Device benchmark wall windows include core
launch/skew costs unless the benchmark records and supplies per-stream starts.

Transaction-level `depends_on` constraints model static program order, stage
barriers, and synchronization edges. A dependent transaction is not activated
until every named predecessor transaction has completed its final packet.
Transactions can also set `issue_stream` (or the shorter alias `stream`) to
represent commands issued by the same RISC/program-order source. The scheduler
automatically adds an ordering edge from each transaction in a stream to the
previous transaction in that same stream. Different streams can still overlap
whenever their resources permit it.

Each packet is scheduled against named resources:

- `niu:nocN:<initiator>`: command issue pressure on the initiator NIU.
- `cmd_buf_pool:nocN:<initiator>`: default finite pool of NIU request command
  buffers for traces that do not specify an exact buffer.
- `cmd_buf:nocN:<initiator>:bX`: exact command-buffer occupancy when a trace
  specifies `cmd_buf`.
- `link:nocN:x0,y0->x1,y1`: directed physical/router link occupancy.
- `l1_in:<endpoint>`: payload arriving into a worker L1.
- `dram_read:<endpoint>`: payload sourced by a DRAM endpoint.
- `dram_write:<endpoint>`: payload sunk by a DRAM endpoint.
- `dram_read_fabric:nocN`: aggregate DRAM-read fabric pressure for that NoC.
- `dram_write_fabric:nocN`: aggregate DRAM-write fabric pressure for that NoC.
- `mcast_path_reserve:nocN`: optional per-packet reservation overhead for
  multicast requests using `CMD_PATH_RESERVE`.
- `atomic_target:<endpoint>`: target-side atomic/semaphore update pressure.
- `atomic_resp_in:<initiator>`: small response/ack arriving back at the
  issuing core.

Resource names use canonical physical endpoint identity, not the optional JSON
`label`. Labels are display names for `payload_src` / `payload_dst`; they must
not affect contention. For example, two differently labeled targets at physical
worker `(10,2)` both reserve `l1_in:l1@10,2`.

For each packet:

1. Compute the dominant payload route.
2. For reads, first add the one-flit request route from initiator to target.
   The return payload resources are offset until that request reaches the
   target.
3. Expand payload routes into directed links on the physical 17x12 torus. This
   is deliberately separate from older programmed-coordinate experiments that
   used x=17/18 DRAM aliases.
4. Assign a timing offset to each resource. The first link is offset 0, later
   links are offset by `hop_index * hop_latency`, and the destination ingress is
   offset by `hops * hop_latency`.
5. Find the earliest launch cycle where every required resource will be
   available at its offset.
6. Reserve every resource use for `bytes / resource_bandwidth` at its offset.
7. Report completion at `start + packet_base_latency + max(resource_offset + resource_time)`.

`packet_base_latency` is currently kept out of resource availability because it
is a common fixed startup term in the present model. That preserves contention
ordering while keeping the resource timeline focused on bandwidth occupancy.

This is intentionally a throughput/contention model first. It should predict
which resource is hot and rough wall cycles for long streams. Single-packet
absolute latency still needs tighter intercept calibration.

## NIU Command Buffers

Each transaction packet charges NIU issue pressure and command-buffer occupancy.
If a JSON transaction omits `cmd_buf`, the scheduler uses
`cmd_buf_pool:nocN:<initiator>` with `calibration.niu_cmd_bufs` slots. The
default is one slot because ordinary BRISC writes have one write-owned command
buffer under Metal's dynamic mode.

If the static trace knows the exact hardware command buffer, set `"cmd_buf":
0..3` and the scheduler will use a single `cmd_buf:nocN:<initiator>:bX`
resource instead. Exact `cmd_buf` means "this trace deliberately used this
role-owned slot," not "choose any free entry from a four-deep write FIFO."

The default `cmd_buf_hold_cycles` is a placeholder control-plane hold time, not
a final hardware-calibrated constant. It is meant to stop short-packet traces
from unrealistically issuing unlimited outstanding commands from one NIU. The
bulk 16 KiB streaming cases are usually dominated by links/endpoints rather
than this resource.

## Atomic/Semaphore Model

The scheduler supports `atomic_inc`, `semaphore_inc`, `sem_inc`, and
`noc_semaphore_inc`. These are modeled as synchronization transactions rather
than bulk payload moves.

For each atomic increment:

1. The initiator NIU issues one command.
2. A small request flit travels from initiator to target over the normal
   directed-link route.
3. The target endpoint charges `atomic_target:<endpoint>` for the update.
4. A small response flit travels back from target to initiator on the same NoC.
5. The initiator charges `atomic_resp_in:<initiator>` when the response arrives.

If `bytes` is omitted in JSON, atomic/semaphore increment transactions default
to 4 bytes. Use `count` for repeated increments. The request/response link
occupancy defaults to one 64-byte flit in each direction because the register
programming path returns an atomic response, but this still needs direct
calibration against `microbench_noc_mcast_mixed.py`.

## Multicast Model

The scheduler now supports `mcast_write`, `multicast_write`, and
`sem_mcast_set` transaction ops. For these ops, the initiator is the source L1
and the receiver set can be provided either as explicit `targets` or as a
non-wrapping rectangular `rect`.

The model treats multicast as a fanout tree, not as independent unicasts:

1. Pick a major route order from `mcast_major`: `x` maps to `xy`, and `y` maps
   to `yx`. A transaction can still override this with `route_order`.
2. Compute the physical path from the source to every receiver.
3. Take the union of those directed links. A shared trunk link is charged once
   for the source packet bytes.
4. Charge `l1_in:<receiver>` once for every receiver, because every destination
   L1 still receives a full copy.
5. Report `bytes` as source payload bytes and `delivered_bytes` as source bytes
   multiplied by receiver count.

This is the right scheduler shape for planning fanout, but it is still an
approximation of the hardware tree. The exact Blackhole multicast router tree,
path-reserve state lifetime, and `VC_LINKED` interactions need more calibration.
For static scheduling, the conservative assumption is:

- Disjoint multicast trees can overlap if they do not share directed links,
  receiver L1 ingress resources, or the same initiator NIU.
- Overlapping multicast trees contend on every shared directed link in the
  approximated tree.
- `CMD_PATH_RESERVE` can be modeled by setting
  `calibration.mcast_path_reserve_cycles`; the default is zero until the reserve
  cost is pinned to a stable benchmark.

## JSON Spec Shape

Example:

```json
{
  "enabled_tensix_col": 15351,
  "harvested_dram_bank": 7,
  "transactions": [
    {
      "name": "dram-read",
      "op": "read",
      "noc": 0,
      "issue_stream": "worker-ncrisc",
      "bytes": 1048576,
      "initiator": {
        "kind": "l1",
        "space": "translated_tensix_noc0",
        "coord": [6, 2],
        "label": "worker"
      },
      "target": {
        "kind": "dram",
        "bank": 0,
        "endpoint": 2
      }
    },
    {
      "name": "mcast-row",
      "op": "mcast_write",
      "noc": 0,
      "issue_stream": "mcast-brisc",
      "major": "x",
      "bytes": 16384,
      "count": 64,
      "initiator": {
        "kind": "l1",
        "coord": [1, 4],
        "label": "sender"
      },
      "rect": {
        "kind": "l1",
        "x0": 2,
        "y0": 4,
        "x1": 5,
        "y1": 4,
        "label": "row"
      }
    },
    {
      "name": "semaphore-inc",
      "op": "semaphore_inc",
      "noc": 0,
      "issue_stream": "mcast-brisc",
      "cmd_buf": 3,
      "depends_on": "mcast-row",
      "count": 8,
      "initiator": {
        "kind": "l1",
        "coord": [1, 4],
        "label": "producer"
      },
      "target": {
        "kind": "l1",
        "coord": [5, 4],
        "label": "consumer-sem"
      }
    }
  ]
}
```

Run:

```bash
PYTHONPATH=. python3 microbenching/models/noc_scheduler.py spec.json
PYTHONPATH=. python3 microbenching/models/noc_scheduler.py spec.json --json
PYTHONPATH=. python3 microbenching/models/noc_scheduler.py --self-test
```

A runnable mixed example covering L1 unicast, DRAM read, DRAM write,
multicast, and semaphore increment lives at:

```bash
PYTHONPATH=. python3 microbenching/models/noc_scheduler.py microbenching/models/noc_scheduler_example.json
```

For larger workloads, hand-writing every transaction is error-prone. Use the
compact workload expander to generate ordinary scheduler JSON from harvested-
aware patterns:

```bash
PYTHONPATH=. python3 microbenching/models/noc_workload_expand.py microbenching/models/noc_workload_example.json -o /tmp/noc_workload_expanded.json --estimate
PYTHONPATH=. python3 microbenching/models/noc_scheduler.py /tmp/noc_workload_expanded.json
PYTHONPATH=. python3 microbenching/models/noc_workload_expand.py --self-test
```

The expander currently supports these pattern kinds:

- `dram_stream`: one read/write transaction per selected core. `cores` may be
  `translated_live`, `live`, `live_raw`, or an explicit coordinate list.
  `bank_mode` may be `round_robin`, `nearest`, `nearest_balanced`, or
  `balanced`; `endpoint_mode` may be `split3`, `nearest`, or a fixed endpoint
  index. `nearest` minimizes routed payload hops for each core, but it does not
  try to balance bank pressure. `nearest_balanced` first finds the nearest
  endpoint distance, then chooses the least-loaded endpoint within
  `balance_hop_slack` hops of that distance. `balanced` ignores the nearest
  filter and chooses the least-loaded candidate, using hop count only as a tie
  breaker.
- `unicast_pairs`: explicit L1-to-L1 pair list with harvested-aware coordinate
  validation.
- `mcast_rect`: one multicast write to a rectangular target set.

Patterns may set `issue_stream` or `stream` as a Python-format template. For
`dram_stream`, available fields are `{name}`, `{op}`, `{noc}`, `{i}`, `{x}`,
`{y}`, `{raw_x}`, `{raw_y}`, `{bank}`, and `{endpoint}`. The compact add1
example uses `add1-core-{raw_x}-{raw_y}` on both read and write patterns so
each physical worker's write stream is automatically ordered after that same
worker's read stream. For `unicast_pairs`, the template fields include source
and target aliases like `{sx}`, `{sy}`, `{tx}`, `{ty}`, `{raw_sx}`, `{raw_sy}`,
`{raw_tx}`, and `{raw_ty}`. For `mcast_rect`, the source fields are `{sx}`,
`{sy}`, `{raw_sx}`, and `{raw_sy}`.

Current add1-shaped example comparison, using 118 translated-live cores,
1 MiB/core read and 1 MiB/core write, per-core read/write `issue_stream`
ordering, NoC0 reads with `xy`, and NoC1 writes with `yx`:

| workload | bank policy | endpoint policy | endpoints used/read | max cores per endpoint | estimated cycles | estimated us |
|---|---|---|---:|---:|---:|---:|
| `noc_workload_nearest_example.json` | `nearest` | `nearest` | 17 | 24 | 687202.9 | 509.039 |
| `noc_workload_balanced_example.json` | `nearest_balanced`, slack 2 | `nearest` | 21 | 11 | 573851.5 | 425.075 |

The nearest-only policy makes physical endpoint `dram.b6.e0@9,4` the dominant
endpoint hotspot at about 532k busy cycles for both read and write. The
nearest-balanced policy reduces that endpoint to about 244k busy cycles and
shifts the top hotspots to aggregate DRAM fabric pressure, which is the behavior
we want from a throughput-aware placement policy.

Endpoint coordinate spaces:

- `route`: coordinates are already physical/router coordinates for this model.
- `translated_tensix_noc0`: worker coordinates are translated through the
  harvested-column map from `enabled_tensix_col` before routing.
- `dram` endpoints specified by `bank`/`endpoint` use physical DRAM router
  coordinates, not the programmed x=17/18 bank-table coordinates.
- `calibration.route_order` can be set to `xy` or `yx` to compare dimension
  order assumptions.

The `--json` output includes a `transactions` summary with start/end cycles,
bytes, B/cyc, and top hotspots for each transaction. It also includes per-packet
`resource_cycles`, `resource_offsets`, and `resource_uses`, which are the
fields to compare against link/contention microbench traces. `resource_cycles`
aggregates all uses of the same named resource inside one packet, while
`resource_uses` preserves each individual offset/cycle pair.
The top-level `slot_available` field reports final availability for finite-slot
resources such as command-buffer pools.
- The top-level `transaction_completion` field reports the final completion
  cycle for every named transaction.
- `depends_on` may be either a string or a list of transaction names. All names
  must be unique when dependencies are used; unknown dependencies and dependency
  cycles are rejected.
- `issue_stream` / `stream` serializes transactions that came from the same
  issuing RISC or static command stream by adding implicit dependencies in JSON
  order.
- Individual transactions may override the global route order with
  `"route_order": "xy"` or `"route_order": "yx"`.

For the currently observed P100a harvested columns 6 and 15, the physical live
worker columns are:

```text
1 2 3 4 5 7 10 11 12 13 14 16
```

Friendly translated x=6 maps to physical x=7, and friendly translated x=14 maps
to physical x=16. Raw physical x=6 and x=15 are harvested positions on this
chip and must not be used for normal live-worker throughput benchmarks.

Bench generators and scheduler specs must use the telemetry-derived translation
map rather than the old `1..7,10..14` physical list. In code, use
`tensix_coordinate_map(...)` plus either `translated_live_tensix_cores(...)`
when launching kernels by translated worker coordinates, or
`live_raw_tensix_cores(...)` when modeling route/link resources directly.
The hidden translated slots that route to harvested raw columns are only for
explicit dead-column probes.

## What Is Still Worth Benchmarking

The NoC is much better understood now, but not fully closed if we want a
scheduler that can estimate arbitrary static binaries.

- L1 target-ingress priority/fairness: aggregate target-ingress bandwidth now
  matches the model. The refreshed K=2..8 run gives a deterministic
  position-biased split; the remaining work is encoding that priority rule in
  the scheduler.
- NIU command-buffer pressure: ordinary BRISC writes should be modeled as
  one-wide. More write slots should only appear in a scheduler trace if the
  firmware explicitly initialized and used those role-owned command buffers for
  writes.
- Read request overhead: blocking small-packet read/write latency is now
  measured over hop distance and size. The remaining work is reducing the
  intercept into request-leg and fixed-loop pieces.
- Mixed read/write with shared initiator or DRAM endpoints: distinct-source L1
  mixed traffic now matches the directed-link model, and one BRISC can keep
  read slot 1 plus write slot 0 active on the same NoC. The remaining unsafe
  shape is the two-RISC BRISC+NCRISC concurrent probe.
- Atomics/semaphores: the scheduler now models request/target/response
  resources, but the default target/update constants are placeholders until a
  focused safe calibration run pins them down.
- Multicast path reserve and `vc_linked`: bounded one-way, VC-linked,
  dual/overlap, rect, and competing-rectangle runs now pass. The remaining work
  is documentation and reducing those measurements into stable scheduler
  constants/policies.
- DRAM endpoint asymmetry: single-source per-bank/per-endpoint rates are now
  measured and are nearly flat. Aggregate spread/split3 DRAM fabric is still
  where the large asymmetry lives.
- Scheduler runtime: exact scheduling now uses a heap of stream candidates and
  the calibrator can run cycle-only without packet records. Very large arbitrary
  traces may still need higher-level compression by repeated pattern.
- Route dimension order: synthetic DRAM write modeling is very sensitive to
  whether packets take X-then-Y or Y-then-X turns. The estimator exposes
  `calibration.route_order` so this can be fit against overlap benches instead
  of assumed.
- Static binary extraction: the estimator currently consumes JSON with explicit
  dependencies and per-RISC `issue_stream` ordering. The next step is extracting
  those transactions, stream IDs, command-buffer IDs, and synchronization edges
  from generated kernels or a trace emitted by the lowering path.

## Current Answer

No, the NoC is not fully understood in the sense needed for a perfect compiler
scheduler. We understand enough to build a useful static estimator: route
packets over the physical torus, split to 16 KiB, charge NIU issue, charge the
role-owned NIU command-buffer slot, charge directed links, charge L1/DRAM
endpoint resources, model DRAM fabric pressure, model multicast as a
first-order fanout tree, enforce explicit transaction dependencies and
per-issuer program order, and let resource availability produce contention.

The remaining work is calibration reduction and trace extraction, not basic
mechanics. The biggest unknowns for scheduling quality are encoding
target-ingress position priority, decomposing small-read intercepts into
request/fixed costs, deciding how to model cross-RISC command ownership when
BRISC and NCRISC both issue NoC traffic, exact atomic/semaphore constants once
we decide to include them, and turning the multicast reservation/`VC_LINKED`
sweeps into compact scheduler constants.
