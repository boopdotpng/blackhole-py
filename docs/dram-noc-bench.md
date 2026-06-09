
## Observation

The single-bank endpoint sweep does not show a hidden `3x` gain from using all
three DRAM NoC endpoints. Directly targeting endpoint `0`, `1`, or `2` improves
single-core DRAM traffic versus the firmware-table path, typically from about
`36-37 GB/s` to about `69-73 GB/s`. Under multi-core pressure, all endpoint
modes converge around the same one-controller roof: roughly `60-80 GB/s`.

`split3` helps in some read cases, especially moderate core counts, but it does
not multiply the controller bandwidth. At 118 cores on bank 0:

| op | noc | preferred GB/s | best explicit/split GB/s |
|---|---:|---:|---:|
| read | 0 | `61.1` | `63.5` (`split3`) |
| read | 1 | `60.5` | `63.8` (`split3`) |
| write | 0 | `61.5` | `61.6` (`endpoint 1`) |
| write | 1 | `61.0` | `63.1` (`split3`) |

So the three endpoints appear to be routing/endpoint-queue conveniences rather
than independent controller bandwidth. They can reduce path or queue overhead,
but the DRAM controller remains the limiter.

## Packet And All-Bank Endpoint Sweep

The packet-size sweep used all-bank spread mode with `1 MiB/core`. For packet
sizes above `2048 B`, the harness directly targets the same preferred endpoint
instead of using the firmware tile-address helper, because that helper is
tile-sized.

At 118 cores:

| packet bytes | read NoC0 GB/s | read NoC1 GB/s | write NoC0 GB/s | write NoC1 GB/s |
|---:|---:|---:|---:|---:|
| `2048` | `298.4` | `200.7` | `154.0` | `245.9` |
| `4096` | `271.9` | `208.6` | `164.7` | `243.4` |
| `8192` | `287.3` | `211.2` | `160.7` | `245.2` |
| `16384` | `301.9` | `209.1` | `155.5` | `240.1` |

Larger packets improve single-core bandwidth and reduce command count, but they
do not unlock a large aggregate gain in this all-bank run. The aggregate limit
is still mostly routing/controller balance rather than only command issue.

The all-bank endpoint sweep at `2048 B` packets shows endpoint choice can matter
for the whole chip, especially for NoC1 writes:

| endpoint | read NoC0 GB/s | read NoC1 GB/s | write NoC0 GB/s | write NoC1 GB/s |
|---|---:|---:|---:|---:|
| `preferred` | `298.4` | `200.7` | `154.0` | `245.9` |
| `0` | `242.2` | `184.0` | `148.4` | `236.4` |
| `1` | `248.4` | `200.7` | `153.2` | `244.8` |
| `2` | `250.7` | `215.1` | `163.7` | `252.8` |
| `split3` | `299.2` | `224.7` | `160.7` | `305.3` |

Best current all-bank numbers from this harness:

- DRAM-to-L1 read: `301.9 GB/s` on NoC0 with `16384 B` packets.
- L1-to-DRAM write: `305.3 GB/s` on NoC1 with endpoint `split3`.

## Stateful NoC Posting And TT-Metal Streams

TT-Metal's normal worker data-movement kernels do not appear to use the full
NoC stream overlay for ordinary DRAM pages. The relevant fast path is the
stateful one-packet NoC API:

- `noc_async_read_one_packet_set_state(...)`
- `noc_async_read_one_packet_with_state(...)`
- `noc_async_write_one_packet_set_state(...)`
- `noc_async_write_one_packet_with_state(...)`

The blackhole-py harness now has `--stateful`, which mirrors that style by
programming fixed command fields once and only updating the changing source and
destination addresses per packet.

Small run, all-bank spread, `1 MiB/core`, preferred endpoint:

| op | noc | cores | standard GB/s | stateful GB/s |
|---|---:|---:|---:|---:|
| read | 0 | 1 | `36.3` | `62.7` |
| read | 1 | 1 | `36.3` | `78.2` |
| write | 0 | 1 | `37.3` | `63.5` |
| write | 1 | 1 | `37.3` | `73.3` |
| read | 0 | 118 | `297.7` | `243.8` |
| read | 1 | 118 | `202.1` | `202.3` |
| write | 0 | 118 | `154.3` | `164.1` |
| write | 1 | 118 | `244.6` | `245.0` |

So the stateful path clearly removes single-core command overhead, but it does
not move the aggregate roof much. NoC0 reads regressed in this specific
comparison because `--stateful` currently forces direct endpoint addressing
instead of the firmware bank-table path.

The full NoC stream overlay is still relevant for persistent producer/consumer
queues, remote circular buffers, command queues, and multicast style plumbing,
but it is much heavier than the worker NoC command-buffer path: phases, message
headers, local/remote buffers, credits, and stream register setup. It is not the
first thing to adapt for a raw DRAM bandwidth microbench.

## DRISC GDDR DMA Path

TT-Metal has a newer Blackhole-specific DRISC API in
`tt_metal/hw/inc/experimental/gddr_dma.h`. This is likely the right next path
for chasing the GDDR roof:

- DRISC L1 <-> GDDR, not worker L1 <-> DRAM endpoint via normal NoC commands.
- Two independent TX streams, `0` and `1`.
- Up to `255` outstanding reads and `15` outstanding writes.
- Transfer size cap is `262128` bytes, much larger than the NoC command-buffer
  `16 KiB` burst cap.
- There is a tunable AXI burst size; TT-Metal tests set it to `255`.

Blackhole-py cannot drop this into the current `Program` launcher as-is, because
that launcher targets worker Tensix cores. The GDDR DMA API is compiled for
DRISC and TT-Metal uses it from DRAM-core kernels such as
`dram_core_prefetcher.cpp`. Adapting it here means adding a DRAM-core/DRISC
launch path or a dedicated low-level harness for those cores, then measuring:

- GDDR -> DRISC L1 reads by bank/controller.
- DRISC L1 -> GDDR writes by bank/controller.
- One stream versus two streams.
- Transfer size and outstanding-depth sweep.
- Aggregate seven-controller spread.

For a `256-bit` GDDR6 bus, theoretical bandwidth is:

`bandwidth GB/s = 32 * data_rate_Gbps`

Examples: `14 Gbps = 448 GB/s`, `16 Gbps = 512 GB/s`,
`18 Gbps = 576 GB/s`, `20 Gbps = 640 GB/s`. The current worker NoC harness
tops out around `300 GB/s`, so we probably have not hit the raw GDDR roof yet.

## Run 2026-06-06T23:56:34-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | 1 | 1.0 | 39037 | 26.861 | 36.3 | 0 |
| read | 0 | spread | 7 | 7.0 | 84466 | 86.899 | 117.3 | 0 |
| read | 0 | spread | 14 | 14.0 | 127271 | 115.345 | 155.7 | 0 |
| read | 0 | spread | 28 | 28.0 | 153031 | 191.857 | 259.0 | 0 |
| read | 0 | spread | 56 | 56.0 | 256135 | 229.255 | 309.5 | 0 |
| read | 0 | spread | 118 | 118.0 | 558459 | 221.560 | 299.1 | 0 |
| read | 1 | spread | 1 | 1.0 | 39039 | 26.860 | 36.3 | 0 |
| read | 1 | spread | 7 | 7.0 | 68423 | 107.274 | 144.8 | 0 |
| read | 1 | spread | 14 | 14.0 | 112950 | 129.970 | 175.5 | 0 |
| read | 1 | spread | 28 | 28.0 | 234616 | 125.141 | 168.9 | 0 |
| read | 1 | spread | 56 | 56.0 | 415387 | 141.363 | 190.8 | 0 |
| read | 1 | spread | 118 | 118.0 | 843757 | 146.644 | 198.0 | 0 |
| write | 0 | spread | 1 | 1.0 | 37956 | 27.626 | 37.3 | 0 |
| write | 0 | spread | 7 | 7.0 | 59637 | 123.078 | 166.2 | 0 |
| write | 0 | spread | 14 | 14.0 | 108344 | 135.495 | 182.9 | 0 |
| write | 0 | spread | 28 | 28.0 | 240904 | 121.875 | 164.5 | 0 |
| write | 0 | spread | 56 | 56.0 | 530905 | 110.604 | 149.3 | 0 |
| write | 0 | spread | 118 | 118.0 | 1083858 | 114.159 | 154.1 | 0 |
| write | 1 | spread | 1 | 1.0 | 37953 | 27.628 | 37.3 | 0 |
| write | 1 | spread | 7 | 7.0 | 82743 | 88.709 | 119.8 | 0 |
| write | 1 | spread | 14 | 14.0 | 129182 | 113.639 | 153.4 | 0 |
| write | 1 | spread | 28 | 28.0 | 207485 | 141.505 | 191.0 | 0 |
| write | 1 | spread | 56 | 56.0 | 359691 | 163.252 | 220.4 | 0 |
| write | 1 | spread | 118 | 118.0 | 679971 | 181.967 | 245.7 | 0 |

## Run 2026-06-06T23:56:47-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | 1 | 1.0 | 39053 | 26.850 | 36.2 | 0 |
| read | 0 | single-bank | 2 | 2.0 | 43000 | 48.771 | 65.8 | 0 |
| read | 0 | single-bank | 4 | 4.0 | 71295 | 58.830 | 79.4 | 0 |
| read | 0 | single-bank | 8 | 8.0 | 142071 | 59.045 | 79.7 | 0 |
| read | 0 | single-bank | 16 | 16.0 | 283652 | 59.147 | 79.8 | 0 |
| read | 0 | single-bank | 32 | 32.0 | 658558 | 50.951 | 68.8 | 0 |
| read | 0 | single-bank | 64 | 64.0 | 1483881 | 45.225 | 61.1 | 0 |
| read | 0 | single-bank | 118 | 118.0 | 2732556 | 45.281 | 61.1 | 0 |
| read | 1 | single-bank | 1 | 1.0 | 39039 | 26.860 | 36.3 | 0 |
| read | 1 | single-bank | 2 | 2.0 | 42955 | 48.822 | 65.9 | 0 |
| read | 1 | single-bank | 4 | 4.0 | 71683 | 58.512 | 79.0 | 0 |
| read | 1 | single-bank | 8 | 8.0 | 148971 | 56.310 | 76.0 | 0 |
| read | 1 | single-bank | 16 | 16.0 | 284481 | 58.975 | 79.6 | 0 |
| read | 1 | single-bank | 32 | 32.0 | 574985 | 58.357 | 78.8 | 0 |
| read | 1 | single-bank | 64 | 64.0 | 1417798 | 47.333 | 63.9 | 0 |
| read | 1 | single-bank | 118 | 118.0 | 2764260 | 44.761 | 60.4 | 0 |
| write | 0 | single-bank | 1 | 1.0 | 37956 | 27.626 | 37.3 | 0 |
| write | 0 | single-bank | 2 | 2.0 | 41821 | 50.146 | 67.7 | 0 |
| write | 0 | single-bank | 4 | 4.0 | 77649 | 54.016 | 72.9 | 0 |
| write | 0 | single-bank | 8 | 8.0 | 153454 | 54.665 | 73.8 | 0 |
| write | 0 | single-bank | 16 | 16.0 | 360065 | 46.595 | 62.9 | 0 |
| write | 0 | single-bank | 32 | 32.0 | 663088 | 50.603 | 68.3 | 0 |
| write | 0 | single-bank | 64 | 64.0 | 1460546 | 45.948 | 62.0 | 0 |
| write | 0 | single-bank | 118 | 118.0 | 2711713 | 45.629 | 61.6 | 0 |
| write | 1 | single-bank | 1 | 1.0 | 37953 | 27.628 | 37.3 | 0 |
| write | 1 | single-bank | 2 | 2.0 | 41811 | 50.158 | 67.7 | 0 |
| write | 1 | single-bank | 4 | 4.0 | 77972 | 53.792 | 72.6 | 0 |
| write | 1 | single-bank | 8 | 8.0 | 153650 | 54.596 | 73.7 | 0 |
| write | 1 | single-bank | 16 | 16.0 | 308186 | 54.439 | 73.5 | 0 |
| write | 1 | single-bank | 32 | 32.0 | 739622 | 45.367 | 61.2 | 0 |
| write | 1 | single-bank | 64 | 64.0 | 1487117 | 45.127 | 60.9 | 0 |
| write | 1 | single-bank | 118 | 118.0 | 2740026 | 45.157 | 61.0 | 0 |

## Run 2026-06-07T00:03:32-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | preferred | 1 | 1.0 | 39036 | 26.862 | 36.3 | 0 |
| read | 0 | single-bank | preferred | 2 | 2.0 | 42989 | 48.783 | 65.9 | 0 |
| read | 0 | single-bank | preferred | 4 | 4.0 | 71235 | 58.880 | 79.5 | 0 |
| read | 0 | single-bank | preferred | 8 | 8.0 | 186808 | 44.905 | 60.6 | 0 |
| read | 0 | single-bank | preferred | 16 | 16.0 | 372296 | 45.064 | 60.8 | 0 |
| read | 0 | single-bank | preferred | 32 | 32.0 | 743222 | 45.147 | 60.9 | 0 |
| read | 0 | single-bank | preferred | 64 | 64.0 | 1432500 | 46.847 | 63.2 | 0 |
| read | 0 | single-bank | preferred | 118 | 118.0 | 2731738 | 45.294 | 61.1 | 0 |
| read | 1 | single-bank | preferred | 1 | 1.0 | 39105 | 26.814 | 36.2 | 0 |
| read | 1 | single-bank | preferred | 2 | 2.0 | 42919 | 48.863 | 66.0 | 0 |
| read | 1 | single-bank | preferred | 4 | 4.0 | 71792 | 58.423 | 78.9 | 0 |
| read | 1 | single-bank | preferred | 8 | 8.0 | 142319 | 58.942 | 79.6 | 0 |
| read | 1 | single-bank | preferred | 16 | 16.0 | 378665 | 44.306 | 59.8 | 0 |
| read | 1 | single-bank | preferred | 32 | 32.0 | 618383 | 54.262 | 73.3 | 0 |
| read | 1 | single-bank | preferred | 64 | 64.0 | 1446143 | 46.405 | 62.6 | 0 |
| read | 1 | single-bank | preferred | 118 | 118.0 | 2761315 | 44.809 | 60.5 | 0 |
| write | 0 | single-bank | preferred | 1 | 1.0 | 37949 | 27.631 | 37.3 | 0 |
| write | 0 | single-bank | preferred | 2 | 2.0 | 45053 | 46.549 | 62.8 | 0 |
| write | 0 | single-bank | preferred | 4 | 4.0 | 77652 | 54.014 | 72.9 | 0 |
| write | 0 | single-bank | preferred | 8 | 8.0 | 178958 | 46.875 | 63.3 | 0 |
| write | 0 | single-bank | preferred | 16 | 16.0 | 342862 | 48.933 | 66.1 | 0 |
| write | 0 | single-bank | preferred | 32 | 32.0 | 723410 | 46.384 | 62.6 | 0 |
| write | 0 | single-bank | preferred | 64 | 64.0 | 1459470 | 45.982 | 62.1 | 0 |
| write | 0 | single-bank | preferred | 118 | 118.0 | 2714000 | 45.590 | 61.5 | 0 |
| write | 1 | single-bank | preferred | 1 | 1.0 | 37956 | 27.626 | 37.3 | 0 |
| write | 1 | single-bank | preferred | 2 | 2.0 | 41840 | 50.123 | 67.7 | 0 |
| write | 1 | single-bank | preferred | 4 | 4.0 | 90927 | 46.128 | 62.3 | 0 |
| write | 1 | single-bank | preferred | 8 | 8.0 | 180719 | 46.418 | 62.7 | 0 |
| write | 1 | single-bank | preferred | 16 | 16.0 | 341544 | 49.122 | 66.3 | 0 |
| write | 1 | single-bank | preferred | 32 | 32.0 | 692050 | 48.486 | 65.5 | 0 |
| write | 1 | single-bank | preferred | 64 | 64.0 | 1487286 | 45.122 | 60.9 | 0 |
| write | 1 | single-bank | preferred | 118 | 118.0 | 2738237 | 45.187 | 61.0 | 0 |

## Run 2026-06-07T00:03:35-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `0`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | 0 | 1 | 1.0 | 20416 | 51.361 | 69.3 | 0 |
| read | 0 | single-bank | 0 | 2 | 2.0 | 35859 | 58.483 | 79.0 | 0 |
| read | 0 | single-bank | 0 | 4 | 4.0 | 99277 | 42.248 | 57.0 | 0 |
| read | 0 | single-bank | 0 | 8 | 8.0 | 143248 | 58.560 | 79.1 | 0 |
| read | 0 | single-bank | 0 | 16 | 16.0 | 357755 | 46.896 | 63.3 | 0 |
| read | 0 | single-bank | 0 | 32 | 32.0 | 747900 | 44.865 | 60.6 | 0 |
| read | 0 | single-bank | 0 | 64 | 64.0 | 1494816 | 44.894 | 60.6 | 0 |
| read | 0 | single-bank | 0 | 118 | 118.0 | 2742173 | 45.122 | 60.9 | 0 |
| read | 1 | single-bank | 0 | 1 | 1.0 | 20480 | 51.200 | 69.1 | 0 |
| read | 1 | single-bank | 0 | 2 | 2.0 | 36138 | 58.032 | 78.3 | 0 |
| read | 1 | single-bank | 0 | 4 | 4.0 | 71658 | 58.532 | 79.0 | 0 |
| read | 1 | single-bank | 0 | 8 | 8.0 | 142165 | 59.006 | 79.7 | 0 |
| read | 1 | single-bank | 0 | 16 | 16.0 | 355685 | 47.169 | 63.7 | 0 |
| read | 1 | single-bank | 0 | 32 | 32.0 | 598000 | 56.111 | 75.7 | 0 |
| read | 1 | single-bank | 0 | 64 | 64.0 | 1450837 | 46.255 | 62.4 | 0 |
| read | 1 | single-bank | 0 | 118 | 118.0 | 2766504 | 44.725 | 60.4 | 0 |
| write | 0 | single-bank | 0 | 1 | 1.0 | 19325 | 54.260 | 73.3 | 0 |
| write | 0 | single-bank | 0 | 2 | 2.0 | 41032 | 51.110 | 69.0 | 0 |
| write | 0 | single-bank | 0 | 4 | 4.0 | 76166 | 55.068 | 74.3 | 0 |
| write | 0 | single-bank | 0 | 8 | 8.0 | 152297 | 55.081 | 74.4 | 0 |
| write | 0 | single-bank | 0 | 16 | 16.0 | 360706 | 46.512 | 62.8 | 0 |
| write | 0 | single-bank | 0 | 32 | 32.0 | 726964 | 46.157 | 62.3 | 0 |
| write | 0 | single-bank | 0 | 64 | 64.0 | 1449538 | 46.297 | 62.5 | 0 |
| write | 0 | single-bank | 0 | 118 | 118.0 | 2716775 | 45.544 | 61.5 | 0 |
| write | 1 | single-bank | 0 | 1 | 1.0 | 19330 | 54.246 | 73.2 | 0 |
| write | 1 | single-bank | 0 | 2 | 2.0 | 44842 | 46.768 | 63.1 | 0 |
| write | 1 | single-bank | 0 | 4 | 4.0 | 76134 | 55.091 | 74.4 | 0 |
| write | 1 | single-bank | 0 | 8 | 8.0 | 151902 | 55.224 | 74.6 | 0 |
| write | 1 | single-bank | 0 | 16 | 16.0 | 360269 | 46.569 | 62.9 | 0 |
| write | 1 | single-bank | 0 | 32 | 32.0 | 740670 | 45.303 | 61.2 | 0 |
| write | 1 | single-bank | 0 | 64 | 64.0 | 1486413 | 45.148 | 61.0 | 0 |
| write | 1 | single-bank | 0 | 118 | 118.0 | 2728894 | 45.341 | 61.2 | 0 |

## Run 2026-06-07T00:03:38-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `1`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | 1 | 1 | 1.0 | 20425 | 51.338 | 69.3 | 0 |
| read | 0 | single-bank | 1 | 2 | 2.0 | 48288 | 43.430 | 58.6 | 0 |
| read | 0 | single-bank | 1 | 4 | 4.0 | 99063 | 42.340 | 57.2 | 0 |
| read | 0 | single-bank | 1 | 8 | 8.0 | 142197 | 58.993 | 79.6 | 0 |
| read | 0 | single-bank | 1 | 16 | 16.0 | 283510 | 59.177 | 79.9 | 0 |
| read | 0 | single-bank | 1 | 32 | 32.0 | 621045 | 54.029 | 72.9 | 0 |
| read | 0 | single-bank | 1 | 64 | 64.0 | 1482963 | 45.253 | 61.1 | 0 |
| read | 0 | single-bank | 1 | 118 | 118.0 | 2741670 | 45.130 | 60.9 | 0 |
| read | 1 | single-bank | 1 | 1 | 1.0 | 20416 | 51.361 | 69.3 | 0 |
| read | 1 | single-bank | 1 | 2 | 2.0 | 36064 | 58.151 | 78.5 | 0 |
| read | 1 | single-bank | 1 | 4 | 4.0 | 71382 | 58.759 | 79.3 | 0 |
| read | 1 | single-bank | 1 | 8 | 8.0 | 142168 | 59.005 | 79.7 | 0 |
| read | 1 | single-bank | 1 | 16 | 16.0 | 307789 | 54.509 | 73.6 | 0 |
| read | 1 | single-bank | 1 | 32 | 32.0 | 627753 | 53.452 | 72.2 | 0 |
| read | 1 | single-bank | 1 | 64 | 64.0 | 1499574 | 44.752 | 60.4 | 0 |
| read | 1 | single-bank | 1 | 118 | 118.0 | 2754852 | 44.914 | 60.6 | 0 |
| write | 0 | single-bank | 1 | 1 | 1.0 | 19325 | 54.260 | 73.3 | 0 |
| write | 0 | single-bank | 1 | 2 | 2.0 | 44653 | 46.966 | 63.4 | 0 |
| write | 0 | single-bank | 1 | 4 | 4.0 | 76166 | 55.068 | 74.3 | 0 |
| write | 0 | single-bank | 1 | 8 | 8.0 | 152062 | 55.166 | 74.5 | 0 |
| write | 0 | single-bank | 1 | 16 | 16.0 | 361261 | 46.441 | 62.7 | 0 |
| write | 0 | single-bank | 1 | 32 | 32.0 | 724930 | 46.286 | 62.5 | 0 |
| write | 0 | single-bank | 1 | 64 | 64.0 | 1463959 | 45.841 | 61.9 | 0 |
| write | 0 | single-bank | 1 | 118 | 118.0 | 2712786 | 45.611 | 61.6 | 0 |
| write | 1 | single-bank | 1 | 1 | 1.0 | 19329 | 54.249 | 73.2 | 0 |
| write | 1 | single-bank | 1 | 2 | 2.0 | 44642 | 46.977 | 63.4 | 0 |
| write | 1 | single-bank | 1 | 4 | 4.0 | 76165 | 55.069 | 74.3 | 0 |
| write | 1 | single-bank | 1 | 8 | 8.0 | 167163 | 50.182 | 67.7 | 0 |
| write | 1 | single-bank | 1 | 16 | 16.0 | 303429 | 55.292 | 74.6 | 0 |
| write | 1 | single-bank | 1 | 32 | 32.0 | 716841 | 46.809 | 63.2 | 0 |
| write | 1 | single-bank | 1 | 64 | 64.0 | 1488425 | 45.087 | 60.9 | 0 |
| write | 1 | single-bank | 1 | 118 | 118.0 | 2737670 | 45.196 | 61.0 | 0 |

## Run 2026-06-07T00:03:41-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `2`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | 2 | 1 | 1.0 | 20432 | 51.320 | 69.3 | 0 |
| read | 0 | single-bank | 2 | 2 | 2.0 | 35974 | 58.296 | 78.7 | 0 |
| read | 0 | single-bank | 2 | 4 | 4.0 | 71317 | 58.812 | 79.4 | 0 |
| read | 0 | single-bank | 2 | 8 | 8.0 | 142105 | 59.031 | 79.7 | 0 |
| read | 0 | single-bank | 2 | 16 | 16.0 | 373937 | 44.866 | 60.6 | 0 |
| read | 0 | single-bank | 2 | 32 | 32.0 | 717994 | 46.734 | 63.1 | 0 |
| read | 0 | single-bank | 2 | 64 | 64.0 | 1493258 | 44.941 | 60.7 | 0 |
| read | 0 | single-bank | 2 | 118 | 118.0 | 2735945 | 45.225 | 61.1 | 0 |
| read | 1 | single-bank | 2 | 1 | 1.0 | 20480 | 51.200 | 69.1 | 0 |
| read | 1 | single-bank | 2 | 2 | 2.0 | 36073 | 58.136 | 78.5 | 0 |
| read | 1 | single-bank | 2 | 4 | 4.0 | 71449 | 58.703 | 79.2 | 0 |
| read | 1 | single-bank | 2 | 8 | 8.0 | 142392 | 58.912 | 79.5 | 0 |
| read | 1 | single-bank | 2 | 16 | 16.0 | 358950 | 46.740 | 63.1 | 0 |
| read | 1 | single-bank | 2 | 32 | 32.0 | 752212 | 44.608 | 60.2 | 0 |
| read | 1 | single-bank | 2 | 64 | 64.0 | 1496856 | 44.833 | 60.5 | 0 |
| read | 1 | single-bank | 2 | 118 | 118.0 | 2758180 | 44.860 | 60.6 | 0 |
| write | 0 | single-bank | 2 | 1 | 1.0 | 19325 | 54.260 | 73.3 | 0 |
| write | 0 | single-bank | 2 | 2 | 2.0 | 43458 | 48.257 | 65.1 | 0 |
| write | 0 | single-bank | 2 | 4 | 4.0 | 76170 | 55.065 | 74.3 | 0 |
| write | 0 | single-bank | 2 | 8 | 8.0 | 152289 | 55.083 | 74.4 | 0 |
| write | 0 | single-bank | 2 | 16 | 16.0 | 360162 | 46.582 | 62.9 | 0 |
| write | 0 | single-bank | 2 | 32 | 32.0 | 724995 | 46.282 | 62.5 | 0 |
| write | 0 | single-bank | 2 | 64 | 64.0 | 1461460 | 45.919 | 62.0 | 0 |
| write | 0 | single-bank | 2 | 118 | 118.0 | 2717703 | 45.528 | 61.5 | 0 |
| write | 1 | single-bank | 2 | 1 | 1.0 | 19329 | 54.249 | 73.2 | 0 |
| write | 1 | single-bank | 2 | 2 | 2.0 | 38262 | 54.810 | 74.0 | 0 |
| write | 1 | single-bank | 2 | 4 | 4.0 | 76134 | 55.091 | 74.4 | 0 |
| write | 1 | single-bank | 2 | 8 | 8.0 | 151874 | 55.234 | 74.6 | 0 |
| write | 1 | single-bank | 2 | 16 | 16.0 | 360033 | 46.599 | 62.9 | 0 |
| write | 1 | single-bank | 2 | 32 | 32.0 | 676688 | 49.586 | 66.9 | 0 |
| write | 1 | single-bank | 2 | 64 | 64.0 | 1484489 | 45.207 | 61.0 | 0 |
| write | 1 | single-bank | 2 | 118 | 118.0 | 2731580 | 45.297 | 61.2 | 0 |

## Run 2026-06-07T00:03:44-04:00

- Bytes per core: `1048576`
- Page size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `split3`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | single-bank | split3 | 1 | 1.0 | 22624 | 46.348 | 62.6 | 0 |
| read | 0 | single-bank | split3 | 2 | 2.0 | 34289 | 61.161 | 82.6 | 0 |
| read | 0 | single-bank | split3 | 4 | 4.0 | 68139 | 61.555 | 83.1 | 0 |
| read | 0 | single-bank | split3 | 8 | 8.0 | 135890 | 61.731 | 83.3 | 0 |
| read | 0 | single-bank | split3 | 16 | 16.0 | 350066 | 47.926 | 64.7 | 0 |
| read | 0 | single-bank | split3 | 32 | 32.0 | 639993 | 52.429 | 70.8 | 0 |
| read | 0 | single-bank | split3 | 64 | 64.0 | 1426676 | 47.039 | 63.5 | 0 |
| read | 0 | single-bank | split3 | 118 | 118.0 | 2629984 | 47.047 | 63.5 | 0 |
| read | 1 | single-bank | split3 | 1 | 1.0 | 20432 | 51.320 | 69.3 | 0 |
| read | 1 | single-bank | split3 | 2 | 2.0 | 34331 | 61.086 | 82.5 | 0 |
| read | 1 | single-bank | split3 | 4 | 4.0 | 68348 | 61.367 | 82.8 | 0 |
| read | 1 | single-bank | split3 | 8 | 8.0 | 135862 | 61.744 | 83.4 | 0 |
| read | 1 | single-bank | split3 | 16 | 16.0 | 357260 | 46.961 | 63.4 | 0 |
| read | 1 | single-bank | split3 | 32 | 32.0 | 547593 | 61.276 | 82.7 | 0 |
| read | 1 | single-bank | split3 | 64 | 64.0 | 1417235 | 47.352 | 63.9 | 0 |
| read | 1 | single-bank | split3 | 118 | 118.0 | 2619858 | 47.229 | 63.8 | 0 |
| write | 0 | single-bank | split3 | 1 | 1.0 | 22299 | 47.023 | 63.5 | 0 |
| write | 0 | single-bank | split3 | 2 | 2.0 | 37261 | 56.283 | 76.0 | 0 |
| write | 0 | single-bank | split3 | 4 | 4.0 | 78391 | 53.505 | 72.2 | 0 |
| write | 0 | single-bank | split3 | 8 | 8.0 | 147447 | 56.892 | 76.8 | 0 |
| write | 0 | single-bank | split3 | 16 | 16.0 | 336409 | 49.871 | 67.3 | 0 |
| write | 0 | single-bank | split3 | 32 | 32.0 | 702778 | 47.745 | 64.5 | 0 |
| write | 0 | single-bank | split3 | 64 | 64.0 | 1463691 | 45.849 | 61.9 | 0 |
| write | 0 | single-bank | split3 | 118 | 118.0 | 2715378 | 45.567 | 61.5 | 0 |
| write | 1 | single-bank | split3 | 1 | 1.0 | 19328 | 54.252 | 73.2 | 0 |
| write | 1 | single-bank | split3 | 2 | 2.0 | 36829 | 56.943 | 76.9 | 0 |
| write | 1 | single-bank | split3 | 4 | 4.0 | 70842 | 59.206 | 79.9 | 0 |
| write | 1 | single-bank | split3 | 8 | 8.0 | 179589 | 46.710 | 63.1 | 0 |
| write | 1 | single-bank | split3 | 16 | 16.0 | 362576 | 46.272 | 62.5 | 0 |
| write | 1 | single-bank | split3 | 32 | 32.0 | 720322 | 46.583 | 62.9 | 0 |
| write | 1 | single-bank | split3 | 64 | 64.0 | 1418376 | 47.314 | 63.9 | 0 |
| write | 1 | single-bank | split3 | 118 | 118.0 | 2645435 | 46.772 | 63.1 | 0 |

## Run 2026-06-07T00:17:22-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | preferred | 1 | 1.0 | 39045 | 26.856 | 36.3 | 0 |
| read | 0 | spread | preferred | 7 | 7.0 | 83594 | 87.806 | 118.5 | 0 |
| read | 0 | spread | preferred | 14 | 14.0 | 124874 | 117.559 | 158.7 | 0 |
| read | 0 | spread | preferred | 28 | 28.0 | 159067 | 184.577 | 249.2 | 0 |
| read | 0 | spread | preferred | 56 | 56.0 | 210796 | 278.564 | 376.1 | 0 |
| read | 0 | spread | preferred | 118 | 118.0 | 559716 | 221.062 | 298.4 | 0 |
| read | 1 | spread | preferred | 1 | 1.0 | 39066 | 26.841 | 36.2 | 0 |
| read | 1 | spread | preferred | 7 | 7.0 | 68401 | 107.309 | 144.9 | 0 |
| read | 1 | spread | preferred | 14 | 14.0 | 112267 | 130.760 | 176.5 | 0 |
| read | 1 | spread | preferred | 28 | 28.0 | 225870 | 129.987 | 175.5 | 0 |
| read | 1 | spread | preferred | 56 | 56.0 | 441200 | 133.092 | 179.7 | 0 |
| read | 1 | spread | preferred | 118 | 118.0 | 832099 | 148.699 | 200.7 | 0 |
| write | 0 | spread | preferred | 1 | 1.0 | 37949 | 27.631 | 37.3 | 0 |
| write | 0 | spread | preferred | 7 | 7.0 | 59625 | 123.103 | 166.2 | 0 |
| write | 0 | spread | preferred | 14 | 14.0 | 108734 | 135.009 | 182.3 | 0 |
| write | 0 | spread | preferred | 28 | 28.0 | 240914 | 121.870 | 164.5 | 0 |
| write | 0 | spread | preferred | 56 | 56.0 | 531733 | 110.432 | 149.1 | 0 |
| write | 0 | spread | preferred | 118 | 118.0 | 1084695 | 114.071 | 154.0 | 0 |
| write | 1 | spread | preferred | 1 | 1.0 | 37951 | 27.630 | 37.3 | 0 |
| write | 1 | spread | preferred | 7 | 7.0 | 82679 | 88.777 | 119.8 | 0 |
| write | 1 | spread | preferred | 14 | 14.0 | 128937 | 113.855 | 153.7 | 0 |
| write | 1 | spread | preferred | 28 | 28.0 | 207525 | 141.478 | 191.0 | 0 |
| write | 1 | spread | preferred | 56 | 56.0 | 358750 | 163.680 | 221.0 | 0 |
| write | 1 | spread | preferred | 118 | 118.0 | 679176 | 182.180 | 245.9 | 0 |

## Run 2026-06-07T00:17:25-04:00

- Bytes per core: `1048576`
- Packet size: `4096` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | preferred | 1 | 1.0 | 22616 | 46.364 | 62.6 | 0 |
| read | 0 | spread | preferred | 7 | 7.0 | 76640 | 95.773 | 129.3 | 0 |
| read | 0 | spread | preferred | 14 | 14.0 | 118893 | 123.473 | 166.7 | 0 |
| read | 0 | spread | preferred | 28 | 28.0 | 196359 | 149.523 | 201.9 | 0 |
| read | 0 | spread | preferred | 56 | 56.0 | 326944 | 179.603 | 242.5 | 0 |
| read | 0 | spread | preferred | 118 | 118.0 | 614405 | 201.385 | 271.9 | 0 |
| read | 1 | spread | preferred | 1 | 1.0 | 19456 | 53.895 | 72.8 | 0 |
| read | 1 | spread | preferred | 7 | 7.0 | 67465 | 108.798 | 146.9 | 0 |
| read | 1 | spread | preferred | 14 | 14.0 | 113784 | 129.017 | 174.2 | 0 |
| read | 1 | spread | preferred | 28 | 28.0 | 220756 | 132.998 | 179.5 | 0 |
| read | 1 | spread | preferred | 56 | 56.0 | 415298 | 141.393 | 190.9 | 0 |
| read | 1 | spread | preferred | 118 | 118.0 | 800776 | 154.515 | 208.6 | 0 |
| write | 0 | spread | preferred | 1 | 1.0 | 22294 | 47.034 | 63.5 | 0 |
| write | 0 | spread | preferred | 7 | 7.0 | 61171 | 119.992 | 162.0 | 0 |
| write | 0 | spread | preferred | 14 | 14.0 | 114281 | 128.456 | 173.4 | 0 |
| write | 0 | spread | preferred | 28 | 28.0 | 235305 | 124.775 | 168.4 | 0 |
| write | 0 | spread | preferred | 56 | 56.0 | 513321 | 114.393 | 154.4 | 0 |
| write | 0 | spread | preferred | 118 | 118.0 | 1014067 | 122.016 | 164.7 | 0 |
| write | 1 | spread | preferred | 1 | 1.0 | 19624 | 53.433 | 72.1 | 0 |
| write | 1 | spread | preferred | 7 | 7.0 | 80494 | 91.187 | 123.1 | 0 |
| write | 1 | spread | preferred | 14 | 14.0 | 131570 | 111.576 | 150.6 | 0 |
| write | 1 | spread | preferred | 28 | 28.0 | 215702 | 136.114 | 183.8 | 0 |
| write | 1 | spread | preferred | 56 | 56.0 | 361139 | 162.597 | 219.5 | 0 |
| write | 1 | spread | preferred | 118 | 118.0 | 686163 | 180.324 | 243.4 | 0 |

## Run 2026-06-07T00:17:28-04:00

- Bytes per core: `1048576`
- Packet size: `8192` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | preferred | 1 | 1.0 | 17866 | 58.691 | 79.2 | 0 |
| read | 0 | spread | preferred | 7 | 7.0 | 76376 | 96.104 | 129.7 | 0 |
| read | 0 | spread | preferred | 14 | 14.0 | 114088 | 128.673 | 173.7 | 0 |
| read | 0 | spread | preferred | 28 | 28.0 | 185783 | 158.035 | 213.3 | 0 |
| read | 0 | spread | preferred | 56 | 56.0 | 311269 | 188.648 | 254.7 | 0 |
| read | 0 | spread | preferred | 118 | 118.0 | 581488 | 212.785 | 287.3 | 0 |
| read | 1 | spread | preferred | 1 | 1.0 | 17864 | 58.698 | 79.2 | 0 |
| read | 1 | spread | preferred | 7 | 7.0 | 67134 | 109.334 | 147.6 | 0 |
| read | 1 | spread | preferred | 14 | 14.0 | 111106 | 132.127 | 178.4 | 0 |
| read | 1 | spread | preferred | 28 | 28.0 | 210125 | 139.727 | 188.6 | 0 |
| read | 1 | spread | preferred | 56 | 56.0 | 398965 | 147.181 | 198.7 | 0 |
| read | 1 | spread | preferred | 118 | 118.0 | 790770 | 156.470 | 211.2 | 0 |
| write | 0 | spread | preferred | 1 | 1.0 | 22278 | 47.068 | 63.5 | 0 |
| write | 0 | spread | preferred | 7 | 7.0 | 66300 | 110.709 | 149.5 | 0 |
| write | 0 | spread | preferred | 14 | 14.0 | 115460 | 127.144 | 171.6 | 0 |
| write | 0 | spread | preferred | 28 | 28.0 | 240641 | 122.008 | 164.7 | 0 |
| write | 0 | spread | preferred | 56 | 56.0 | 522000 | 112.491 | 151.9 | 0 |
| write | 0 | spread | preferred | 118 | 118.0 | 1039407 | 119.041 | 160.7 | 0 |
| write | 1 | spread | preferred | 1 | 1.0 | 21392 | 49.017 | 66.2 | 0 |
| write | 1 | spread | preferred | 7 | 7.0 | 81093 | 90.514 | 122.2 | 0 |
| write | 1 | spread | preferred | 14 | 14.0 | 128486 | 114.254 | 154.2 | 0 |
| write | 1 | spread | preferred | 28 | 28.0 | 208405 | 140.880 | 190.2 | 0 |
| write | 1 | spread | preferred | 56 | 56.0 | 362884 | 161.816 | 218.5 | 0 |
| write | 1 | spread | preferred | 118 | 118.0 | 681165 | 181.648 | 245.2 | 0 |

## Run 2026-06-07T00:17:30-04:00

- Bytes per core: `1048576`
- Packet size: `16384` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | preferred | 1 | 1.0 | 17856 | 58.724 | 79.3 | 0 |
| read | 0 | spread | preferred | 7 | 7.0 | 77236 | 95.034 | 128.3 | 0 |
| read | 0 | spread | preferred | 14 | 14.0 | 118807 | 123.562 | 166.8 | 0 |
| read | 0 | spread | preferred | 28 | 28.0 | 179305 | 163.744 | 221.1 | 0 |
| read | 0 | spread | preferred | 56 | 56.0 | 307248 | 191.117 | 258.0 | 0 |
| read | 0 | spread | preferred | 118 | 118.0 | 553272 | 223.637 | 301.9 | 0 |
| read | 1 | spread | preferred | 1 | 1.0 | 19769 | 53.041 | 71.6 | 0 |
| read | 1 | spread | preferred | 7 | 7.0 | 66730 | 109.996 | 148.5 | 0 |
| read | 1 | spread | preferred | 14 | 14.0 | 108480 | 135.325 | 182.7 | 0 |
| read | 1 | spread | preferred | 28 | 28.0 | 204581 | 143.513 | 193.7 | 0 |
| read | 1 | spread | preferred | 56 | 56.0 | 398459 | 147.368 | 198.9 | 0 |
| read | 1 | spread | preferred | 118 | 118.0 | 798782 | 154.901 | 209.1 | 0 |
| write | 0 | spread | preferred | 1 | 1.0 | 22272 | 47.080 | 63.6 | 0 |
| write | 0 | spread | preferred | 7 | 7.0 | 65741 | 111.651 | 150.7 | 0 |
| write | 0 | spread | preferred | 14 | 14.0 | 118213 | 124.183 | 167.6 | 0 |
| write | 0 | spread | preferred | 28 | 28.0 | 242411 | 121.117 | 163.5 | 0 |
| write | 0 | spread | preferred | 56 | 56.0 | 525785 | 111.681 | 150.8 | 0 |
| write | 0 | spread | preferred | 118 | 118.0 | 1073897 | 115.218 | 155.5 | 0 |
| write | 1 | spread | preferred | 1 | 1.0 | 22273 | 47.078 | 63.6 | 0 |
| write | 1 | spread | preferred | 7 | 7.0 | 83219 | 88.201 | 119.1 | 0 |
| write | 1 | spread | preferred | 14 | 14.0 | 130753 | 112.273 | 151.6 | 0 |
| write | 1 | spread | preferred | 28 | 28.0 | 211867 | 138.578 | 187.1 | 0 |
| write | 1 | spread | preferred | 56 | 56.0 | 381643 | 153.862 | 207.7 | 0 |
| write | 1 | spread | preferred | 118 | 118.0 | 695730 | 177.845 | 240.1 | 0 |

## Run 2026-06-07T00:17:33-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `0`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | 0 | 1 | 1.0 | 20424 | 51.340 | 69.3 | 0 |
| read | 0 | spread | 0 | 7 | 7.0 | 89481 | 82.029 | 110.7 | 0 |
| read | 0 | spread | 0 | 14 | 14.0 | 142677 | 102.890 | 138.9 | 0 |
| read | 0 | spread | 0 | 28 | 28.0 | 205258 | 143.040 | 193.1 | 0 |
| read | 0 | spread | 0 | 56 | 56.0 | 380264 | 154.420 | 208.5 | 0 |
| read | 0 | spread | 0 | 118 | 118.0 | 689651 | 179.412 | 242.2 | 0 |
| read | 1 | spread | 0 | 1 | 1.0 | 20424 | 51.340 | 69.3 | 0 |
| read | 1 | spread | 0 | 7 | 7.0 | 91886 | 79.882 | 107.8 | 0 |
| read | 1 | spread | 0 | 14 | 14.0 | 120635 | 121.690 | 164.3 | 0 |
| read | 1 | spread | 0 | 28 | 28.0 | 251572 | 116.707 | 157.6 | 0 |
| read | 1 | spread | 0 | 56 | 56.0 | 456441 | 128.648 | 173.7 | 0 |
| read | 1 | spread | 0 | 118 | 118.0 | 907699 | 136.314 | 184.0 | 0 |
| write | 0 | spread | 0 | 1 | 1.0 | 19326 | 54.257 | 73.2 | 0 |
| write | 0 | spread | 0 | 7 | 7.0 | 71556 | 102.577 | 138.5 | 0 |
| write | 0 | spread | 0 | 14 | 14.0 | 125201 | 117.252 | 158.3 | 0 |
| write | 0 | spread | 0 | 28 | 28.0 | 245622 | 119.534 | 161.4 | 0 |
| write | 0 | spread | 0 | 56 | 56.0 | 533399 | 110.087 | 148.6 | 0 |
| write | 0 | spread | 0 | 118 | 118.0 | 1125474 | 109.938 | 148.4 | 0 |
| write | 1 | spread | 0 | 1 | 1.0 | 19328 | 54.252 | 73.2 | 0 |
| write | 1 | spread | 0 | 7 | 7.0 | 102912 | 71.323 | 96.3 | 0 |
| write | 1 | spread | 0 | 14 | 14.0 | 154160 | 95.226 | 128.6 | 0 |
| write | 1 | spread | 0 | 28 | 28.0 | 191554 | 153.273 | 206.9 | 0 |
| write | 1 | spread | 0 | 56 | 56.0 | 374151 | 156.943 | 211.9 | 0 |
| write | 1 | spread | 0 | 118 | 118.0 | 706531 | 175.126 | 236.4 | 0 |

## Run 2026-06-07T00:17:36-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `1`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | 1 | 1 | 1.0 | 20426 | 51.335 | 69.3 | 0 |
| read | 0 | spread | 1 | 7 | 7.0 | 68112 | 107.764 | 145.5 | 0 |
| read | 0 | spread | 1 | 14 | 14.0 | 118343 | 124.047 | 167.5 | 0 |
| read | 0 | spread | 1 | 28 | 28.0 | 192008 | 152.911 | 206.4 | 0 |
| read | 0 | spread | 1 | 56 | 56.0 | 369922 | 158.737 | 214.3 | 0 |
| read | 0 | spread | 1 | 118 | 118.0 | 672430 | 184.007 | 248.4 | 0 |
| read | 1 | spread | 1 | 1 | 1.0 | 20432 | 51.320 | 69.3 | 0 |
| read | 1 | spread | 1 | 7 | 7.0 | 68354 | 107.383 | 145.0 | 0 |
| read | 1 | spread | 1 | 14 | 14.0 | 113589 | 129.238 | 174.5 | 0 |
| read | 1 | spread | 1 | 28 | 28.0 | 220411 | 133.206 | 179.8 | 0 |
| read | 1 | spread | 1 | 56 | 56.0 | 430363 | 136.444 | 184.2 | 0 |
| read | 1 | spread | 1 | 118 | 118.0 | 832084 | 148.701 | 200.7 | 0 |
| write | 0 | spread | 1 | 1 | 1.0 | 20220 | 51.858 | 70.0 | 0 |
| write | 0 | spread | 1 | 7 | 7.0 | 74237 | 98.873 | 133.5 | 0 |
| write | 0 | spread | 1 | 14 | 14.0 | 128217 | 114.494 | 154.6 | 0 |
| write | 0 | spread | 1 | 28 | 28.0 | 257346 | 114.088 | 154.0 | 0 |
| write | 0 | spread | 1 | 56 | 56.0 | 501046 | 117.195 | 158.2 | 0 |
| write | 0 | spread | 1 | 118 | 118.0 | 1090590 | 113.454 | 153.2 | 0 |
| write | 1 | spread | 1 | 1 | 1.0 | 22309 | 47.002 | 63.5 | 0 |
| write | 1 | spread | 1 | 7 | 7.0 | 81339 | 90.240 | 121.8 | 0 |
| write | 1 | spread | 1 | 14 | 14.0 | 128814 | 113.963 | 153.9 | 0 |
| write | 1 | spread | 1 | 28 | 28.0 | 211642 | 138.725 | 187.3 | 0 |
| write | 1 | spread | 1 | 56 | 56.0 | 357947 | 164.047 | 221.5 | 0 |
| write | 1 | spread | 1 | 118 | 118.0 | 682250 | 181.359 | 244.8 | 0 |

## Run 2026-06-07T00:17:39-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `2`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | 2 | 1 | 1.0 | 20416 | 51.361 | 69.3 | 0 |
| read | 0 | spread | 2 | 7 | 7.0 | 75784 | 96.855 | 130.8 | 0 |
| read | 0 | spread | 2 | 14 | 14.0 | 120943 | 121.380 | 163.9 | 0 |
| read | 0 | spread | 2 | 28 | 28.0 | 198399 | 147.985 | 199.8 | 0 |
| read | 0 | spread | 2 | 56 | 56.0 | 364442 | 161.124 | 217.5 | 0 |
| read | 0 | spread | 2 | 118 | 118.0 | 666344 | 185.688 | 250.7 | 0 |
| read | 1 | spread | 2 | 1 | 1.0 | 20424 | 51.340 | 69.3 | 0 |
| read | 1 | spread | 2 | 7 | 7.0 | 58870 | 124.682 | 168.3 | 0 |
| read | 1 | spread | 2 | 14 | 14.0 | 110810 | 132.480 | 178.8 | 0 |
| read | 1 | spread | 2 | 28 | 28.0 | 204918 | 143.277 | 193.4 | 0 |
| read | 1 | spread | 2 | 56 | 56.0 | 409764 | 143.303 | 193.5 | 0 |
| read | 1 | spread | 2 | 118 | 118.0 | 776449 | 159.356 | 215.1 | 0 |
| write | 0 | spread | 2 | 1 | 1.0 | 19326 | 54.257 | 73.2 | 0 |
| write | 0 | spread | 2 | 7 | 7.0 | 60365 | 121.594 | 164.2 | 0 |
| write | 0 | spread | 2 | 14 | 14.0 | 112210 | 130.827 | 176.6 | 0 |
| write | 0 | spread | 2 | 28 | 28.0 | 235021 | 124.926 | 168.6 | 0 |
| write | 0 | spread | 2 | 56 | 56.0 | 508544 | 115.467 | 155.9 | 0 |
| write | 0 | spread | 2 | 118 | 118.0 | 1020216 | 121.280 | 163.7 | 0 |
| write | 1 | spread | 2 | 1 | 1.0 | 19332 | 54.240 | 73.2 | 0 |
| write | 1 | spread | 2 | 7 | 7.0 | 85602 | 85.746 | 115.8 | 0 |
| write | 1 | spread | 2 | 14 | 14.0 | 148744 | 98.693 | 133.2 | 0 |
| write | 1 | spread | 2 | 28 | 28.0 | 229537 | 127.910 | 172.7 | 0 |
| write | 1 | spread | 2 | 56 | 56.0 | 363663 | 161.469 | 218.0 | 0 |
| write | 1 | spread | 2 | 118 | 118.0 | 660653 | 187.287 | 252.8 | 0 |

## Run 2026-06-07T00:17:41-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `split3`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | split3 | 1 | 1.0 | 20424 | 51.340 | 69.3 | 0 |
| read | 0 | spread | split3 | 7 | 7.0 | 103097 | 71.195 | 96.1 | 0 |
| read | 0 | spread | split3 | 14 | 14.0 | 138090 | 106.308 | 143.5 | 0 |
| read | 0 | spread | split3 | 28 | 28.0 | 156446 | 187.669 | 253.4 | 0 |
| read | 0 | spread | split3 | 56 | 56.0 | 274983 | 213.541 | 288.3 | 0 |
| read | 0 | spread | split3 | 118 | 118.0 | 558281 | 221.630 | 299.2 | 0 |
| read | 1 | spread | split3 | 1 | 1.0 | 20432 | 51.320 | 69.3 | 0 |
| read | 1 | spread | split3 | 7 | 7.0 | 84117 | 87.260 | 117.8 | 0 |
| read | 1 | spread | split3 | 14 | 14.0 | 105413 | 139.262 | 188.0 | 0 |
| read | 1 | spread | split3 | 28 | 28.0 | 226627 | 129.553 | 174.9 | 0 |
| read | 1 | spread | split3 | 56 | 56.0 | 384007 | 152.915 | 206.4 | 0 |
| read | 1 | spread | split3 | 118 | 118.0 | 743482 | 166.422 | 224.7 | 0 |
| write | 0 | spread | split3 | 1 | 1.0 | 19326 | 54.257 | 73.2 | 0 |
| write | 0 | spread | split3 | 7 | 7.0 | 60026 | 122.281 | 165.1 | 0 |
| write | 0 | spread | split3 | 14 | 14.0 | 111732 | 131.386 | 177.4 | 0 |
| write | 0 | spread | split3 | 28 | 28.0 | 232271 | 126.405 | 170.6 | 0 |
| write | 0 | spread | split3 | 56 | 56.0 | 478722 | 122.660 | 165.6 | 0 |
| write | 0 | spread | split3 | 118 | 118.0 | 1039735 | 119.003 | 160.7 | 0 |
| write | 1 | spread | split3 | 1 | 1.0 | 22309 | 47.002 | 63.5 | 0 |
| write | 1 | spread | split3 | 7 | 7.0 | 115051 | 63.798 | 86.1 | 0 |
| write | 1 | spread | split3 | 14 | 14.0 | 157915 | 92.962 | 125.5 | 0 |
| write | 1 | spread | split3 | 28 | 28.0 | 215354 | 136.334 | 184.1 | 0 |
| write | 1 | spread | split3 | 56 | 56.0 | 316481 | 185.541 | 250.5 | 0 |
| write | 1 | spread | split3 | 118 | 118.0 | 547041 | 226.184 | 305.3 | 0 |
