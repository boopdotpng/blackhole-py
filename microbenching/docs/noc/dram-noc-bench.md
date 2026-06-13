
## Run 2026-06-13T16:45:48-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `preferred`
- Posting mode: `standard`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | posting | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | preferred | standard | 1 | 1.0 | 22618 | 46.360 | 62.6 | 0 |
| read | 0 | spread | preferred | standard | 7 | 7.0 | 84571 | 86.791 | 117.2 | 0 |
| read | 0 | spread | preferred | standard | 14 | 14.0 | 128480 | 114.260 | 154.3 | 0 |
| read | 0 | spread | preferred | standard | 28 | 28.0 | 161047 | 182.308 | 246.1 | 0 |
| read | 0 | spread | preferred | standard | 56 | 56.0 | 274864 | 213.634 | 288.4 | 0 |
| read | 0 | spread | preferred | standard | 118 | 118.0 | 585333 | 211.387 | 285.4 | 0 |
| read | 1 | spread | preferred | standard | 1 | 1.0 | 22643 | 46.309 | 62.5 | 0 |
| read | 1 | spread | preferred | standard | 7 | 7.0 | 68450 | 107.232 | 144.8 | 0 |
| read | 1 | spread | preferred | standard | 14 | 14.0 | 112922 | 130.002 | 175.5 | 0 |
| read | 1 | spread | preferred | standard | 28 | 28.0 | 232147 | 126.472 | 170.7 | 0 |
| read | 1 | spread | preferred | standard | 56 | 56.0 | 428325 | 137.093 | 185.1 | 0 |
| read | 1 | spread | preferred | standard | 118 | 118.0 | 840611 | 147.193 | 198.7 | 0 |
| write | 0 | spread | preferred | standard | 1 | 1.0 | 22300 | 47.021 | 63.5 | 0 |
| write | 0 | spread | preferred | standard | 7 | 7.0 | 65022 | 112.885 | 152.4 | 0 |
| write | 0 | spread | preferred | standard | 14 | 14.0 | 110056 | 133.387 | 180.1 | 0 |
| write | 0 | spread | preferred | standard | 28 | 28.0 | 236395 | 124.199 | 167.7 | 0 |
| write | 0 | spread | preferred | standard | 56 | 56.0 | 527543 | 111.309 | 150.3 | 0 |
| write | 0 | spread | preferred | standard | 118 | 118.0 | 1080217 | 114.544 | 154.6 | 0 |
| write | 1 | spread | preferred | standard | 1 | 1.0 | 22694 | 46.205 | 62.4 | 0 |
| write | 1 | spread | preferred | standard | 7 | 7.0 | 81249 | 90.340 | 122.0 | 0 |
| write | 1 | spread | preferred | standard | 14 | 14.0 | 128773 | 114.000 | 153.9 | 0 |
| write | 1 | spread | preferred | standard | 28 | 28.0 | 213745 | 137.361 | 185.4 | 0 |
| write | 1 | spread | preferred | standard | 56 | 56.0 | 359606 | 163.291 | 220.4 | 0 |
| write | 1 | spread | preferred | standard | 118 | 118.0 | 682209 | 181.370 | 244.8 | 0 |

## Run 2026-06-13T16:45:49-04:00

- Bytes per core: `1048576`
- Packet size: `2048` bytes
- DRAM banks/controllers used by allocator: `7`
- Endpoint mode: `split3`
- Posting mode: `standard`
- Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier

| op | noc | mode | endpoint | posting | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| read | 0 | spread | split3 | standard | 1 | 1.0 | 22608 | 46.381 | 62.6 | 0 |
| read | 0 | spread | split3 | standard | 7 | 7.0 | 103418 | 70.974 | 95.8 | 0 |
| read | 0 | spread | split3 | standard | 14 | 14.0 | 138602 | 105.915 | 143.0 | 0 |
| read | 0 | spread | split3 | standard | 28 | 28.0 | 159822 | 183.705 | 248.0 | 0 |
| read | 0 | spread | split3 | standard | 56 | 56.0 | 276542 | 212.338 | 286.7 | 0 |
| read | 0 | spread | split3 | standard | 118 | 118.0 | 567465 | 218.043 | 294.4 | 0 |
| read | 1 | spread | split3 | standard | 1 | 1.0 | 22616 | 46.364 | 62.6 | 0 |
| read | 1 | spread | split3 | standard | 7 | 7.0 | 85185 | 86.166 | 116.3 | 0 |
| read | 1 | spread | split3 | standard | 14 | 14.0 | 105961 | 138.542 | 187.0 | 0 |
| read | 1 | spread | split3 | standard | 28 | 28.0 | 228292 | 128.608 | 173.6 | 0 |
| read | 1 | spread | split3 | standard | 56 | 56.0 | 374201 | 156.922 | 211.8 | 0 |
| read | 1 | spread | split3 | standard | 118 | 118.0 | 743071 | 166.514 | 224.8 | 0 |
| write | 0 | spread | split3 | standard | 1 | 1.0 | 22300 | 47.021 | 63.5 | 0 |
| write | 0 | spread | split3 | standard | 7 | 7.0 | 60018 | 122.297 | 165.1 | 0 |
| write | 0 | spread | split3 | standard | 14 | 14.0 | 111748 | 131.368 | 177.3 | 0 |
| write | 0 | spread | split3 | standard | 28 | 28.0 | 232562 | 126.246 | 170.4 | 0 |
| write | 0 | spread | split3 | standard | 56 | 56.0 | 478391 | 122.745 | 165.7 | 0 |
| write | 0 | spread | split3 | standard | 118 | 118.0 | 1039322 | 119.051 | 160.7 | 0 |
| write | 1 | spread | split3 | standard | 1 | 1.0 | 22308 | 47.004 | 63.5 | 0 |
| write | 1 | spread | split3 | standard | 7 | 7.0 | 114998 | 63.827 | 86.2 | 0 |
| write | 1 | spread | split3 | standard | 14 | 14.0 | 157895 | 92.974 | 125.5 | 0 |
| write | 1 | spread | split3 | standard | 28 | 28.0 | 204341 | 143.682 | 194.0 | 0 |
| write | 1 | spread | split3 | standard | 56 | 56.0 | 318835 | 184.171 | 248.6 | 0 |
| write | 1 | spread | split3 | standard | 118 | 118.0 | 530974 | 233.028 | 314.6 | 0 |
