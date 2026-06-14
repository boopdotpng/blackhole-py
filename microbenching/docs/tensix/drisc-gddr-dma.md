# DRISC GDDR DMA Microbench

Bench source: `microbenching/tensix/microbench_drisc_gddr_dma.py`.

Scope: DRISC DMA engine only, copying between GDDR and the DRISC local L1
staging window. These rows do not include the later DRISC-L1 to worker-L1 NoC
stage.

## Current Findings

- Proven paths:
  - single DMA stream, fixed GDDR address, read and write;
  - same-stream pipelined GDDR reads using the documented `read_ready` +
    outstanding-read wait pattern.
- Peak observed read bandwidth: about 57 GB/s at 64 KiB transfers.
- Peak observed write bandwidth: about 64 GB/s by 32-64 KiB transfers.
- One-transfer latency-ish timing at 1350 MHz: read is about 195-200 cycles for
  16-256 B and write is about 97-101 cycles for 16-256 B.
- Stream 1 works and is effectively equivalent to stream 0 for the sampled
  4 KiB and 64 KiB rows.
- Same-stream pipelined reads are the important small-page lever found so far:
  depth 2 raises 4 KiB reads from about 22 GB/s to about 39 GB/s, and depth 4
  raises 4 KiB reads to about 61 GB/s. Depth 2/4 plateau around 63 GB/s for
  16-32 KiB pages.
- Bank/endpoint placement sampled on bank 0 endpoints 0/1/2 and bank 4 endpoint
  0 is effectively flat.
- GDDR offsets +1, +8, +16, +64, and +4096 all completed for the sampled rows;
  ordinary 16-byte-aligned offsets did not materially affect throughput.
- `DMA_CTRL_ATTRS_BURST_255 = 0x0003ff01` is not uniquely required for these
  runs. `0x00000101` is much slower; `0x00000f01`, `0x00003f01`,
  `0x0000ff01`, and `0x0003ff01` are effectively tied for the sampled
  4 KiB/64 KiB rows.

## Open Gaps

- Two-stream read (`dma2`) is implemented in the overlap bench but currently
  times out before the first transfer completes; do not trust it yet.
- Two-stream write is not characterized.
- Two-stream GDDR read is distinct from the now-proven same-stream pipelined
  read pattern. The checked-in tt-metal code we found also uses same-stream
  outstanding reads, not stream0+stream1 bandwidth striping.
- Pipe-mode page size is limited by available DRISC L1 staging slots below the
  result area. With the default stage/result layout, 64 KiB pages do not fit at
  depth 2; use 32 KiB or smaller at depth 2, and 16 KiB or smaller at depth 4.
- Transfer-attribute base bits beyond the known read `0x83000000` and write
  `0x10000000` values are not swept yet.

## Run 2026-06-14T00:25:56-04:00 Same-Stream Pipelined Reads

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,32768 --pages 32 --directions read --modes single,pipe --pipe-depth 2 --timeout 10 --no-report`
- Scope: compare proven single-transfer/barrier path with same-stream pipelined
  reads on stream 0.

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 32 | 0.125 | 0 | 8026 | 8026 | 0 | 16.331 | 22.0 | True | depth=1 poc_kernel checked_slots=1 |
| read | single | 32768 | 32 | 1.000 | 0 | 27132 | 27132 | 0 | 38.647 | 52.2 | True | depth=1 poc_kernel checked_slots=1 |
| read | pipe | 4096 | 32 | 0.125 | 0 | 4486 | 4279 | 207 | 29.218 | 39.4 | True | depth=2 local_kernel checked_slots=2 |
| read | pipe | 32768 | 32 | 1.000 | 0 | 22362 | 21049 | 1313 | 46.891 | 63.3 | True | depth=2 local_kernel checked_slots=2 |

## Run 2026-06-14T00:25:56-04:00 Same-Stream Depth 4 Reads

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,8192,16384 --pages 64 --directions read --modes single,pipe --pipe-depth 4 --timeout 10 --no-report`
- Scope: stream 0, four L1 staging slots.

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 64 | 0.250 | 0 | 16138 | 16138 | 0 | 16.244 | 21.9 | True | depth=1 poc_kernel checked_slots=1 |
| read | single | 8192 | 64 | 0.500 | 0 | 21510 | 21510 | 0 | 24.374 | 32.9 | True | depth=1 poc_kernel checked_slots=1 |
| read | single | 16384 | 64 | 1.000 | 0 | 32948 | 32948 | 0 | 31.825 | 43.0 | True | depth=1 poc_kernel checked_slots=1 |
| read | pipe | 4096 | 64 | 0.250 | 0 | 5766 | 5475 | 291 | 45.464 | 61.4 | True | depth=4 local_kernel checked_slots=4 |
| read | pipe | 8192 | 64 | 0.500 | 0 | 11291 | 10650 | 641 | 46.434 | 62.7 | True | depth=4 local_kernel checked_slots=4 |
| read | pipe | 16384 | 64 | 1.000 | 0 | 22351 | 21024 | 1327 | 46.914 | 63.3 | True | depth=4 local_kernel checked_slots=4 |

## Run 2026-06-14T00:25:56-04:00 Stream 1 Pipelined Reads

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,16384 --pages 64 --directions read --modes pipe --pipe-depth 4 --stream 1 --timeout 10 --no-report`
- Scope: confirm same-stream pipelined read path on DMA stream 1.

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | pipe | 4096 | 64 | 0.250 | 1 | 5787 | 5492 | 295 | 45.299 | 61.2 | True | depth=4 local_kernel checked_slots=4 |
| read | pipe | 16384 | 64 | 1.000 | 1 | 22365 | 21050 | 1315 | 46.885 | 63.3 | True | depth=4 local_kernel checked_slots=4 |

## Run 2026-06-14T00:02:13-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536 --pages 256 --directions read,write --modes single --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 16 | 256 | 0.004 | 0 | 42760 | 42760 | 0 | 0.096 | 0.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 32 | 256 | 0.008 | 0 | 42676 | 42676 | 0 | 0.192 | 0.3 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 64 | 256 | 0.016 | 0 | 42770 | 42770 | 0 | 0.383 | 0.5 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 128 | 256 | 0.031 | 0 | 42686 | 42686 | 0 | 0.768 | 1.0 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 256 | 256 | 0.062 | 0 | 45584 | 45584 | 0 | 1.438 | 1.9 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 512 | 256 | 0.125 | 0 | 46718 | 46718 | 0 | 2.806 | 3.8 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 1024 | 256 | 0.250 | 0 | 49210 | 49210 | 0 | 5.327 | 7.2 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 2048 | 256 | 0.500 | 0 | 53424 | 53424 | 0 | 9.814 | 13.2 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 4096 | 256 | 1.000 | 0 | 67270 | 67270 | 0 | 15.588 | 21.0 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 8192 | 256 | 2.000 | 0 | 85330 | 85330 | 0 | 24.577 | 33.2 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 16384 | 256 | 4.000 | 0 | 131488 | 131488 | 0 | 31.899 | 43.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 32768 | 256 | 8.000 | 0 | 217308 | 217308 | 0 | 38.602 | 52.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 396186 | 396186 | 0 | 42.347 | 57.2 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 16 | 256 | 0.004 | 0 | 19226 | 19226 | 0 | 0.213 | 0.3 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 32 | 256 | 0.008 | 0 | 19222 | 19222 | 0 | 0.426 | 0.6 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 64 | 256 | 0.016 | 0 | 19222 | 19222 | 0 | 0.852 | 1.2 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 128 | 256 | 0.031 | 0 | 19222 | 19222 | 0 | 1.705 | 2.3 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 256 | 256 | 0.062 | 0 | 19222 | 19222 | 0 | 3.409 | 4.6 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 512 | 256 | 0.125 | 0 | 19222 | 19222 | 0 | 6.819 | 9.2 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 1024 | 256 | 0.250 | 0 | 22806 | 22806 | 0 | 11.495 | 15.5 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 2048 | 256 | 0.500 | 0 | 26390 | 26390 | 0 | 19.867 | 26.8 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 8192 | 256 | 2.000 | 0 | 55062 | 55062 | 0 | 38.087 | 51.4 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 16384 | 256 | 4.000 | 0 | 91182 | 91182 | 0 | 45.999 | 62.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 32768 | 256 | 8.000 | 0 | 176824 | 176824 | 0 | 47.440 | 64.0 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 353766 | 353766 | 0 | 47.425 | 64.0 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:02:26-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 16,64,256,1024,4096,16384,65536 --pages 1 --directions read,write --modes single --stream 0 --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 16 | 1 | 0.000 | 0 | 199 | 199 | 0 | 0.080 | 0.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 64 | 1 | 0.000 | 0 | 195 | 195 | 0 | 0.328 | 0.4 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 256 | 1 | 0.000 | 0 | 195 | 195 | 0 | 1.313 | 1.8 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 1024 | 1 | 0.001 | 0 | 209 | 209 | 0 | 4.900 | 6.6 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 4096 | 1 | 0.004 | 0 | 279 | 279 | 0 | 14.681 | 19.8 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 16384 | 1 | 0.016 | 0 | 531 | 531 | 0 | 30.855 | 41.7 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 1 | 0.062 | 0 | 1567 | 1567 | 0 | 41.823 | 56.5 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 16 | 1 | 0.000 | 0 | 101 | 101 | 0 | 0.158 | 0.2 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 64 | 1 | 0.000 | 0 | 97 | 97 | 0 | 0.660 | 0.9 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 256 | 1 | 0.000 | 0 | 97 | 97 | 0 | 2.639 | 3.6 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 1024 | 1 | 0.001 | 0 | 111 | 111 | 0 | 9.225 | 12.5 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 4096 | 1 | 0.004 | 0 | 167 | 167 | 0 | 24.527 | 33.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 16384 | 1 | 0.016 | 0 | 377 | 377 | 0 | 43.459 | 58.7 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 1 | 0.062 | 0 | 1259 | 1259 | 0 | 52.054 | 70.3 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:02:28-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,65536 --pages 256 --directions read,write --modes single --stream 1 --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 1 | 63984 | 63984 | 0 | 16.388 | 22.1 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 1 | 397269 | 397269 | 0 | 42.231 | 57.0 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 1 | 35094 | 35094 | 0 | 29.879 | 40.3 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 1 | 354189 | 354189 | 0 | 47.368 | 63.9 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:05-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,65536 --pages 256 --directions read,write --modes single --gddr-offset 16 --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 64576 | 64576 | 0 | 16.238 | 21.9 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 397282 | 397282 | 0 | 42.230 | 57.0 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 354172 | 354172 | 0 | 47.370 | 63.9 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:07-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,65536 --pages 256 --directions read,write --modes single --gddr-offset 64 --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 65164 | 65164 | 0 | 16.091 | 21.7 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 396736 | 396736 | 0 | 42.288 | 57.1 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 0) code_B=324 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 353766 | 353766 | 0 | 47.425 | 64.0 | True | dram_core=(0, 0) code_B=320 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:09-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --sizes 4096,65536 --pages 256 --directions read,write --modes single --gddr-offset 4096 --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 64036 | 64036 | 0 | 16.375 | 22.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 396732 | 396732 | 0 | 42.289 | 57.1 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 353766 | 353766 | 0 | 47.425 | 64.0 | True | dram_core=(0, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:18-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --endpoint 1 --sizes 4096,65536 --pages 256 --directions read,write --modes single --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 63984 | 63984 | 0 | 16.388 | 22.1 | True | dram_core=(0, 1) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 395906 | 395906 | 0 | 42.377 | 57.2 | True | dram_core=(0, 1) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 1) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 353766 | 353766 | 0 | 47.425 | 64.0 | True | dram_core=(0, 1) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:20-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --endpoint 2 --sizes 4096,65536 --pages 256 --directions read,write --modes single --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 63942 | 63942 | 0 | 16.399 | 22.1 | True | dram_core=(0, 11) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 395976 | 395976 | 0 | 42.369 | 57.2 | True | dram_core=(0, 11) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(0, 11) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 354214 | 354214 | 0 | 47.365 | 63.9 | True | dram_core=(0, 11) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |

## Run 2026-06-14T00:03:37-04:00 DRISC GDDR DMA

- Command: `microbenching/tensix/microbench_drisc_gddr_dma.py --bank 4 --endpoint 0 --sizes 4096,65536 --pages 256 --directions read,write --modes single --timeout 10`
- Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots
- Clock assumption: 1350.0 MHz

| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| read | single | 4096 | 256 | 1.000 | 0 | 65104 | 65104 | 0 | 16.106 | 21.7 | True | dram_core=(9, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| read | single | 65536 | 256 | 16.000 | 0 | 396550 | 396550 | 0 | 42.308 | 57.1 | True | dram_core=(9, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel final_slot=0 mismatch=-1 |
| write | single | 4096 | 256 | 1.000 | 0 | 37142 | 37142 | 0 | 28.232 | 38.1 | True | dram_core=(9, 0) code_B=316 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
| write | single | 65536 | 256 | 16.000 | 0 | 353766 | 353766 | 0 | 47.425 | 64.0 | True | dram_core=(9, 0) code_B=312 status0=0x00000000 status1=0x00000000 poc_kernel fixed_slots=1 |
