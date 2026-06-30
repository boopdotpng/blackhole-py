
## Run 2026-06-23T15:03:46-04:00 DRISC GDDR DMA Aggregate

- Command: `microbenching/tensix/microbench_drisc_gddr_dma_aggregate.py --page-size 16384 --pages 2048 --pipe-depth 4 --gate-delay-ms 100 --timeout 10`
- Scope: one DRISC per selected GDDR bank; same-stream pipelined GDDR reads into DRISC-local L1
- Banks: 0,1,2,4,5,6,7; endpoint: 0
- Page size: 16384; pages per bank: 2048; pipe depth: 4
- Clock assumption: 1350.0 MHz

| bank | endpoint | core | cycles | B/cyc | GB/s | ok | detail |
|---:|---:|---|---:|---:|---:|---|---|
| 0 | 0 | `0,0` | 708970 | 47.328 | 63.9 | True | status=0x00000000 checked_slots=4 |
| 1 | 0 | `0,2` | 708045 | 47.390 | 64.0 | True | status=0x00000000 checked_slots=4 |
| 2 | 0 | `0,4` | 708045 | 47.390 | 64.0 | True | status=0x00000000 checked_slots=4 |
| 4 | 0 | `9,0` | 708045 | 47.390 | 64.0 | True | status=0x00000000 checked_slots=4 |
| 5 | 0 | `9,2` | 708045 | 47.390 | 64.0 | True | status=0x00000000 checked_slots=4 |
| 6 | 0 | `9,4` | 708367 | 47.369 | 63.9 | True | status=0x00000000 checked_slots=4 |
| 7 | 0 | `9,5` | 708367 | 47.369 | 63.9 | True | status=0x00000000 checked_slots=4 |

Aggregate max-duration window: 708970 cycles; aggregate: 447.3 GB/s; per-channel target sum: 448.0 GB/s; saturation: 99.8%
