# Movement kernels

Keep NoC/DRAM/L1 movement, embedding gather, and atomics in `test_noc.py`.
Packer and unpacker tests live in their named child directories. Cross-unit Dst,
FPU, and SFPU movement lives under `sfpu/` so it stays separate from arithmetic.

The direct NoC proof uses physical CB synchronization slot zero. Its payload is
ordinary L1, while its two shared monotonic 16-bit counters are stream-register
MMIO: `0xFFB48028 + slot * 0x1000` counts received/created pages and
`0xFFB48020 + slot * 0x1000` counts acked/consumed pages. Resident BRISC
firmware resets all 32 counter pairs before each launch. A producer may write
while `(received - acked) & 0xffff < depth`; a consumer may read while the
difference is nonzero. The payload slot is `counter % depth`, so no separate L1
pointer metadata is needed in this POC. Depth is an init-time option and the
payload allocation is exactly `depth * page_bytes`, bounded by available L1.

General lowering must retain the CB's L1 base, item size, depth, and allocated
physical synchronization slot. A RISC can keep its own current counter live as
this proof does, reread it from MMIO, or spill it to private RISC local memory;
it does not need to reserve ordinary payload L1 solely for CB bookkeeping.

The 2 KiB tile sweep and the 16 KiB saturation sweep answer different
questions. The former retains the ordinary tile shape and profiles RISC-V
interleaving overhead. The latter uses the maximum NoC packet, tunes CB depth
and producer/consumer batch size separately, then runs the same BRISC/NoC0 read
and NCRISC/NoC1 write kernel on 1..all workers. Every worker owns a 1 MiB shard
striped over all eight banks. Coherent 64-bit wall-clock records in worker L1
give the global read window, full-copy window, and tail/median core spread.

On card 0, depth 16 with an eight-page batch was the smallest 16 KiB
configuration within 2% of the best single-core useful-copy rate: it uses
256 KiB of CB payload L1 and measured about 64 GB/s DRAM-to-L1. Repeated
117-core runs with each bank's preferred endpoint measured roughly 186-188
GB/s useful copy bandwidth, or 370-377 GB/s counting both DRAM reads and
writes. No 10% aggregate collapse appeared through 117 cores, though the
slowest/median completion ratio was about 1.55-1.60 at 117 cores. This held for
both the 1 MiB/core weak-scaling curve and the approximately fixed 128 MiB
strong-scaling curve.

Spreading workers across the three mirrored endpoints of every bank raised the
combined result to about 407-416 GB/s. The one-way matrix identifies a strong
directional topology effect: NoC0 read reaches about 484 GB/s while NoC1 read
reaches only 214 GB/s; NoC1 write reaches about 382 GB/s while NoC0 write
reaches only 162 GB/s. The copy therefore uses the favorable NoC0-read and
NoC1-write directions. Mapping each worker to a single bank measured only
about 303-311 GB/s, and rotating the destination mapping away from the bank
being read measured about 401-408 GB/s rather than improving on the ordinary
split-endpoint mapping. These results reject generic route localization and
same-bank read/write contention as the primary explanations for the remaining
write-side gap. Removing response-marked acknowledgements does not close it:
the posted NoC1 write measured about 384 GB/s through local source completion,
versus about 387 GB/s for the remotely acknowledged form in the same run.
Posted completion is only an injection/source-lifetime measurement; it does
not prove remote DRAM visibility. Keep the live sweep rather than treating
these card-0 numbers as portable to future firmware, topologies, or clocks.

A globally disjoint four-bank input/four-bank output layout resolves nearly
all of the mixed-traffic deficit when the sets follow the two physical DRAM
columns. Banks 0-3 read to banks 4-7 write measured about 478 GB/s aggregate;
the reverse measured about 481 GB/s. Since the copy moves equal bytes in each
direction, that is roughly 239-241 GB/s read plus 239-241 GB/s write, against
the 256+256 GB/s four-bank ceilings. Depth 8 with a four-page batch was the
smallest configuration within 2%, using 128 KiB of CB payload L1. An even/odd
controller split remained at only about 416-418 GB/s despite having no bank
overlap. The optimization therefore requires both disjoint bank controllers
and column-aligned NoC routes; merely permuting or alternating banks does not
remove the congested router cuts.

### P150 DRAM column map and preferred placement

The P150 firmware exposes the two physical DRAM columns through translated NoC
X coordinates 17 and 18. The left column contains banks 0-3; the middle column
contains banks 4-7. Each bank has three vertically adjacent router ports. The
preferred NoC0/NoC1 coordinates reported by card 0 and the complete port ranges
used by the split3 sweep are:

| bank | physical column | translated X | three port Y values | preferred NoC0 | preferred NoC1 |
|---:|---|---:|---|---|---|
| 0 | left | 17 | 12, 13, 14 | `(17,14)` | `(17,13)` |
| 1 | left | 17 | 15, 16, 17 | `(17,15)` | `(17,16)` |
| 2 | left | 17 | 18, 19, 20 | `(17,18)` | `(17,19)` |
| 3 | left | 17 | 21, 22, 23 | `(17,21)` | `(17,22)` |
| 4 | middle | 18 | 12, 13, 14 | `(18,14)` | `(18,13)` |
| 5 | middle | 18 | 15, 16, 17 | `(18,17)` | `(18,16)` |
| 6 | middle | 18 | 18, 19, 20 | `(18,20)` | `(18,19)` |
| 7 | middle | 18 | 21, 22, 23 | `(18,23)` | `(18,22)` |

The placement rule is that concurrently read and written tensors should occupy
opposite DRAM columns. Their allocations and the read/write engines remain
independent; hardware does not require the direction to alternate. Ping-pong
is merely the natural strategy for a dependent chain: when one kernel writes
an activation to banks 4-7, that allocation is the next kernel's input, so its
new output can use banks 0-3 without an extra relocation. Independent kernels,
fixed inputs, and terminal outputs need not switch. Both column directions
measured within about 1% of each other, so the small difference is treated as
run-to-run variation rather than an asymmetric placement rule. Use all three
ports per bank across workers, BRISC/NoC0 for reads, and NCRISC/NoC1 for writes.

### Asymmetric traffic and bank allocation

The asymmetric benchmark gives the read stream and write stream separate L1
rings and separate hardware CB counter slots. BRISC produces the input CB and
TRISC0 consumes it; TRISC1 produces the output CB and NCRISC consumes it. Thus
the requested read and write byte counts are independent while the benchmark
still exercises normal CB backpressure. It uses all 117 workers, 16 KiB
packets, depth-eight rings with four-page batches, three DRAM ports, disjoint
bank sets, and reports the median of three runs.

Measured best results for each requested traffic ratio were:

| DRAM read:write bytes | best banks read:write | aggregate GB/s | two-bank-minimum result |
|---:|---:|---:|---:|
| 1:1 | 4:4 | 485.3 | 485.3 (4:4) |
| 2:1 | 5:3 | 468.7 | 468.7 (5:3) |
| 3:1 | 6:2 | 500.9 | 500.9 (6:2) |
| 4:1 | 6:2 | 472.8 | 472.8 (6:2) |
| 7:1 | 7:1 | 505.0 | 433.7 (6:2) |

These points are within roughly 1-5% of a simple independent-bank model: each
bank supplies 64 GB/s and completion is set by the more heavily loaded
direction. In particular, 6:2 sustains about 380 GB/s of reads plus the
appropriately amortized write share. One output bank caps active writes near
64 GB/s, so 7:1 is useful only when the kernel really has approximately 7:1
traffic. It is badly mismatched to balanced or moderately read-heavy kernels.

The initial static lowering rule should therefore classify a kernel by total
DRAM bytes, then choose the closest split: 4:4 for 1:1, 5:3 around 2:1, and
6:2 around 3:1 and above when both directions require at least two banks. A
7:1 specialization is worthwhile for genuinely 7:1-or-higher, read-dominated
traffic if a one-bank output allocation is acceptable. This is a per-kernel
traffic decision, not a universal rule that all weights use seven banks: a
permanent 7-bank weight layout also limits every kernel that reads it to that
placement and leaves all output traffic contending on one controller.

### Long-stream, VC, and priority sweep

Increasing the winning column-separated case from 1 MiB to 8 MiB per worker
raised aggregate bandwidth from about 477-481 GB/s to about 486-489 GB/s. The
remaining short-run loss is therefore partly pipeline ramp/drain amortization,
but the placement result does not depend on the short tensor.

All 49 combinations of dynamic allocation and static VCs 0-5 were tested for
NoC0 reads and NoC1 writes at 8 MiB per worker. Dynamic allocation is acceptable
for the read request but consistently bad for the payload-carrying write path:
a dynamic write VC measured about 431-447 GB/s, while every static write VC
measured about 482-490 GB/s. No individual static pair won repeatably. In a
five-run confirmation, the existing VC1/VC1 default had a 484.4 GB/s median
and a candidate selected from the matrix had a 485.7 GB/s median, with broadly
overlapping ranges. Retain static VC1 for both directions unless a future
topology-specific sweep demonstrates a stable improvement.

Uniform arbitration priorities 0, 1, 2, 4, 8, and 15 also remained within
normal run variation, roughly 484-488 GB/s. Mixed priorities are unsafe for
this sustained all-core workload: assigning priority 15 to the previous slow
quarter and priority 1 to the other workers left 114 of 117 workers unfinished
after ten seconds and required `tt-smi -r` to clear the outstanding NoC state.
Use priority 0 (round-robin/no priority) for the saturation kernel. Priority is
a strict contention/fairness control, not a general bandwidth multiplier.

The NIU has four physical command slots, but they are role-owned rather than a
generic four-deep request FIFO. This proof uses BRISC's read slot 1 and
NCRISC's write slot 2. Packet overlap comes from outstanding requests and the
ring CB, not round-robin theft of all four command slots.
### Remote L1 atomic increment

`atomic.py` programs Blackhole's NIU `INCR_GET` command directly from RISC-V.
The minimal correctness case uses two Tensix cores: one core increments a
32-bit word in the other's L1 and receives the old value.  The fan-in case has
eight cores increment the same receiver word 64 times each; the exact final
value of 512 proves the operation is atomic under contention.

Measured at a 1.35 GHz worker clock on P150:

| NoC | senders | form | slowest sender cycles/op | receiver-visible cycles/op | aggregate Mops/s |
|---:|---:|---|---:|---:|---:|
| 0 | 1 | returned old value | 31.89 | 29.91 | 45.14 |
| 0 | 1 | discarded return | 29.36 | 29.56 | 45.67 |
| 0 | 8 | returned old value | 100.27 | 12.31 | 109.63 |
| 0 | 8 | discarded return | 69.52 | 12.24 | 110.29 |
| 1 | 1 | returned old value | 32.14 | 28.58 | 47.24 |
| 1 | 1 | discarded return | 29.33 | 28.14 | 47.97 |
| 1 | 8 | returned old value | 98.89 | 12.14 | 111.23 |
| 1 | 8 | discarded return | 76.89 | 12.09 | 111.65 |

A single producer is command-issue/round-trip limited to roughly 28-32 cycles
per increment. With eight independent producers, the receiver-side
serialization rate becomes the bottleneck at roughly 12.1-12.3 cycles per
increment and is effectively the same for both NoCs and both return policies.
Discarding the return saves the sender's final response drain, so that sender
retires earlier; it does not make the shared target counter update faster. The
no-return timing is therefore reported with both sender-issue and
receiver-visible completion.

On Blackhole, do not implement the discarded-return form by clearing
`RESP_MARKED`: truly posted atomics can hang when the destination memory ports
are contended.  The POC uses the established semaphore convention of keeping
the atomic response-marked, routing the unused return to coordinate zero, and
using the receiver's counter as the completion barrier.

Counters only require 4-byte alignment.  `INCR_GET` selects one 32-bit word
inside a 16-byte L1 region through `AT_LEN_BE.IND_32`; the 16-byte alignment
rule for ordinary NoC payload transfers does not apply to the counter itself.

### Remote CB send

`remote_cb.py` implements the fourth movement primitive: send ready pages from
a local L1 CB to the same CB address on one core or a static list of cores. One
destination uses unicast. Rectangular groups use one hardware multicast, and
arbitrary lists are decomposed into exact rectangles. After the ready run, the
sender advances every receiver's real hardware `tiles_received` counter with
a 4-byte inline NoC write; NCRISC waits and pops through the ordinary
`tiles_received`/`tiles_acked` CB counters.

The default page is one 1,024-element BF16 tile (2 KiB). There is no special
initial-fill branch: the same transfer loop coalesces the contiguous pages the
caller says are ready, up to the 16 KiB packet limit. Thus steady state is
normally one 2 KiB page while an eight-page ready run can use one request. A
partial page transfers its exact byte count; the two-element BF16 hardware
case copies four bytes, publishes one occupied page, and verifies the following
guard remains intact. No payload padding is copied.

P150 CB-visible completion measurements at 1.35 GHz, including credit
publication and zero-delay NCRISC page pops:

| NoC | tiles | destinations | source GB/s | delivered GB/s |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 8.98 | 8.98 |
| 0 | 8 | 1 | 28.21 | 28.21 |
| 0 | 1 | 8 multicast | 7.14 | 57.15 |
| 0 | 8 | 8 multicast | 25.57 | 204.56 |
| 1 | 1 | 1 | 6.78 | 6.78 |
| 1 | 8 | 1 | 24.94 | 24.94 |
| 1 | 1 | 8 multicast | 6.95 | 55.57 |
| 1 | 8 | 8 multicast | 24.71 | 197.71 |

The page-sized request loop was compared with coalescing an eight-page ready
run into one 16 KiB request; the completion difference was only about 1-5.5%.
Coalescing remains because it is generic—the low-level caller supplies the
ready contiguous run—and requires no special initial-fill branch.
`emit_wait_and_pop_pages(..., delay_cycles=...)` can model a slower consumer;
delay-zero is used above so simulated compute is not reported as NoC time.

### Indexed rows

`indexed.py` proves generic indexed row movement rather than embedding-specific
machinery. BRISC loads four u32 indices from L1, computes each row's logical
byte offset, maps every covered page to one of eight interleaved DRAM banks,
and emits ordinary exact-byte NoC requests. The 768-byte hardware rows start
inside 2 KiB pages and can cross page and bank boundaries.

Gather uses IDs `(21, 2, 21, 16)`; the repeated ID verifies that both output
positions receive the same row. Scatter uses `(22, 1, 22, 17)` and drains each
row before issuing the next, defining deterministic last-write-wins behavior
for the repeated destination. Both BRISC hardware cases pass. Scatter-add is
not part of this primitive: embedding backward must reduce duplicate IDs
before writing or use a future numeric accumulation mechanism.

The embedding benchmark uses the repository's Llama 3.2 1B shape:
BF16 `[128256, 2048]`, or 4 KiB per selected row and about 501 MiB for the
complete table. The table retains 2 KiB interleaved pages, matching its two
tiles per vocabulary row. BRISC/NoC0 overlaps disjoint gather rows in bounded
request batches; scatter retains its per-row completion fence for duplicate
ordering. Median-of-seven card-0 timings were:

| lookups | useful bytes | cycles | latency (us) | useful GB/s |
|---:|---:|---:|---:|---:|
| 1 | 4,096 | 781 | 0.579 | 7.08 |
| 4 | 16,384 | 1,643 | 1.217 | 13.46 |
| 16 | 65,536 | 5,362 | 3.972 | 16.50 |
| 64 | 262,144 | 20,412 | 15.120 | 17.34 |

Batch-one decode therefore spends about 0.58 us fetching its embedding row.
That case is random-read latency bound rather than card-bandwidth bound: one
row is only two 2 KiB requests. Larger batches amortize command and completion
latency but remain a small-request indexed workload, not the 16 KiB sequential
stream used by the peak-bandwidth tests.
