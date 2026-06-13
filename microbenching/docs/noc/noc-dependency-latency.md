## Run 2026-06-13T17:34:19-04:00 NoC dependency latency

- NoCs: `0`
- Modes: `posted_write,nonposted_write,read_flush,atomic_inc`
- Sizes: `4,64` bytes; atomic_inc is fixed 4-byte request/response
- Iters: `4`
- Pairs: `1,2:2,2`
- Traffic: one source issues one dependency-forming transaction per iteration while the target polls for receiver-visible modes.
- Read rows report sender-side response flush only; NoC slave read service has no receiver-side counter in this harness.
- Full matrix command: `python3 microbenching/noc/riscv_noc_dependency_latency.py --nocs 0,1 --modes posted_write,nonposted_write,read_flush,atomic_inc --sizes 4,16,64,256,4096,16384 --iters 16`
- ENABLED_TENSIX_COL: `0x00003bf7`
Live raw Tensix columns: `[1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14, 16]`
Harvested raw Tensix columns: `[6, 15]`
Translated live x -> raw NoC0 x: `1->1, 2->2, 3->3, 4->4, 5->5, 6->7, 7->10, 10->11, 11->12, 12->13, 13->14, 14->16`
Translated hidden x -> harvested raw NoC0 x: `15->6, 16->15`

| mode | noc | source | target | raw noc route | hops | bytes | iters | sent-issue cyc | done-issue cyc | seen-issue cyc | seen-done cyc | sent ctr | resp ctr | recv polls | recv final |
|---|---:|---|---|---|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| posted_write | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 4 | 4 | min=74 avg=75.750 med=74.500 max=80 | min=97 avg=98.750 med=97.500 max=103 | min=91 avg=97.250 med=92.000 max=114 | min=-6 avg=-1.500 med=-5.500 max=11 | 4 | 0 | 1141 | 0xa7000004 |
| posted_write | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 64 | 4 | min=74 avg=76.250 med=74.500 max=82 | min=97 avg=99.250 med=97.500 max=105 | min=87 avg=90.500 med=87.500 max=100 | min=-10 avg=-8.750 med=-10.000 max=-5 | 4 | 0 | 1154 | 0xa7000004 |
| nonposted_write | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 4 | 4 | min=74 avg=75.250 med=74.000 max=79 | min=248 avg=249.250 med=248.000 max=253 | min=91 avg=95.250 med=94.000 max=102 | min=-157 avg=-154.000 med=-154.000 max=-151 | 4 | 4 | 1183 | 0xa7000004 |
| nonposted_write | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 64 | 4 | min=74 avg=74.750 med=74.000 max=77 | min=248 avg=248.750 med=248.000 max=251 | min=87 avg=92.250 med=93.000 max=96 | min=-161 avg=-156.500 med=-156.500 max=-152 | 4 | 4 | 1193 | 0xa7000004 |
| read_flush | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 4 | 4 | n/a | min=248 avg=248.000 med=248.000 max=248 | n/a | n/a | 0 | 4 | 0 | 0x00000000 |
| read_flush | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 64 | 4 | n/a | min=240 avg=240.000 med=240.000 max=240 | n/a | n/a | 0 | 4 | 0 | 0x00000000 |
| atomic_inc | 0 | `1,2` | `2,2` | `1,2->2,2` | 1 | 4 | 4 | n/a | min=250 avg=250.000 med=250.000 max=250 | min=81 avg=82.250 med=81.500 max=85 | min=-169 avg=-167.750 med=-168.500 max=-165 | 0 | 4 | 1181 | 0x00000004 |
