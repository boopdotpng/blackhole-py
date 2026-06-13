
## Run 2026-06-13T16:45:45-04:00

- Mode: `all-to-one`
- Traffic: same-row peer-tile L1 unicast stream, chunked into 16 KiB NoC commands
- Timing: issue all chunks, then one read flush or write barrier; subtract empty loop
- Target policy: all selected program cores transfer to one fixed target; no DRAM writes and no multicast

| noc | source | peer | logical dist | bytes/op | repeats | total MiB/op | read cyc | read B/cyc | write cyc | write B/cyc | read sink | write sink |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `1,2` | `1,2` | 0 | 1048576 | 4 | 4.0 | 65783 | 63.760 | 66367 | 63.199 | 0xa5000000 | 0xa5000000 |
| 0 | `2,2` | `1,2` | 1 | 1048576 | 4 | 4.0 | 65767 | 63.775 | 64980 | 64.548 | 0xa5000000 | 0xa5000000 |
| 0 | `3,2` | `1,2` | 2 | 1048576 | 4 | 4.0 | 66263 | 63.298 | 64988 | 64.540 | 0xa5000000 | 0xa5000000 |
| 0 | `4,2` | `1,2` | 3 | 1048576 | 4 | 4.0 | 66255 | 63.305 | 64988 | 64.540 | 0xa5000000 | 0xa5000000 |
| 0 | `5,2` | `1,2` | 4 | 1048576 | 4 | 4.0 | 65751 | 63.791 | 64980 | 64.548 | 0xa5000000 | 0xa5000000 |
| 0 | `6,2` | `1,2` | 5 | 1048576 | 4 | 4.0 | 66775 | 62.812 | 65084 | 64.444 | 0xa5000000 | 0xa5000000 |
| 0 | `7,2` | `1,2` | 6 | 1048576 | 4 | 4.0 | 65758 | 63.784 | 64980 | 64.548 | 0xa5000000 | 0xa5000000 |
| 0 | `10,2` | `1,2` | 9 | 1048576 | 4 | 4.0 | 65758 | 63.784 | 64988 | 64.540 | 0xa5000000 | 0xa5000000 |
| 1 | `1,2` | `1,2` | 0 | 1048576 | 4 | 4.0 | 65826 | 63.718 | 66375 | 63.191 | 0xa5000000 | 0xa5000000 |
| 1 | `2,2` | `1,2` | 1 | 1048576 | 4 | 4.0 | 66538 | 63.036 | 65015 | 64.513 | 0xa5000000 | 0xa5000000 |
| 1 | `3,2` | `1,2` | 2 | 1048576 | 4 | 4.0 | 66155 | 63.401 | 64999 | 64.529 | 0xa5000000 | 0xa5000000 |
| 1 | `4,2` | `1,2` | 3 | 1048576 | 4 | 4.0 | 66283 | 63.279 | 65767 | 63.775 | 0xa5000000 | 0xa5000000 |
| 1 | `5,2` | `1,2` | 4 | 1048576 | 4 | 4.0 | 66283 | 63.279 | 65767 | 63.775 | 0xa5000000 | 0xa5000000 |
| 1 | `6,2` | `1,2` | 5 | 1048576 | 4 | 4.0 | 65771 | 63.771 | 64999 | 64.529 | 0xa5000000 | 0xa5000000 |
| 1 | `7,2` | `1,2` | 6 | 1048576 | 4 | 4.0 | 65782 | 63.761 | 65767 | 63.775 | 0xa5000000 | 0xa5000000 |
| 1 | `10,2` | `1,2` | 9 | 1048576 | 4 | 4.0 | 66285 | 63.277 | 65007 | 64.521 | 0xa5000000 | 0xa5000000 |

## Run 2026-06-13T16:46:48-04:00

- Mode: `row`
- Traffic: same-row peer-tile L1 unicast stream, chunked into 16 KiB NoC commands
- Timing: issue all chunks, then one read flush or write barrier; subtract empty loop
- Direction policy: NoC0 to the right, NoC1 to the left; no DRAM writes and no multicast

| noc | source | peer | logical dist | bytes/op | repeats | total MiB/op | read cyc | read B/cyc | write cyc | write B/cyc | read sink | write sink |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `1,2` | `2,2` | Route(raw0_source=(1, 2), raw0_peer=(2, 2), raw_source=(1, 2), raw_peer=(2, 2), hops=1, x_hops=1, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66764 | 62.823 | 64988 | 64.540 | 0xa5000000 | 0xa5000000 |
| 0 | `1,2` | `3,2` | Route(raw0_source=(1, 2), raw0_peer=(3, 2), raw_source=(1, 2), raw_peer=(3, 2), hops=2, x_hops=2, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66539 | 63.035 | 65007 | 64.521 | 0xa5000000 | 0xa5000000 |
| 0 | `1,2` | `4,2` | Route(raw0_source=(1, 2), raw0_peer=(4, 2), raw_source=(1, 2), raw_peer=(4, 2), hops=3, x_hops=3, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 65778 | 63.765 | 64999 | 64.529 | 0xa5000000 | 0xa5000000 |
| 0 | `1,2` | `5,2` | Route(raw0_source=(1, 2), raw0_peer=(5, 2), raw_source=(1, 2), raw_peer=(5, 2), hops=4, x_hops=4, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 65771 | 63.771 | 65767 | 63.775 | 0xa5000000 | 0xa5000000 |
| 0 | `1,2` | `6,2` | Route(raw0_source=(1, 2), raw0_peer=(7, 2), raw_source=(1, 2), raw_peer=(7, 2), hops=6, x_hops=6, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66796 | 62.793 | 65055 | 64.473 | 0xa5000000 | 0xa5000000 |
| 1 | `14,2` | `13,2` | Route(raw0_source=(16, 2), raw0_peer=(14, 2), raw_source=(0, 9), raw_peer=(2, 9), hops=2, x_hops=2, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66140 | 63.416 | 65748 | 63.794 | 0xa5000000 | 0xa5000000 |
| 1 | `14,2` | `12,2` | Route(raw0_source=(16, 2), raw0_peer=(13, 2), raw_source=(0, 9), raw_peer=(3, 9), hops=3, x_hops=3, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66538 | 63.036 | 65007 | 64.521 | 0xa5000000 | 0xa5000000 |
| 1 | `14,2` | `11,2` | Route(raw0_source=(16, 2), raw0_peer=(12, 2), raw_source=(0, 9), raw_peer=(4, 9), hops=4, x_hops=4, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 65771 | 63.771 | 64999 | 64.529 | 0xa5000000 | 0xa5000000 |
| 1 | `14,2` | `10,2` | Route(raw0_source=(16, 2), raw0_peer=(11, 2), raw_source=(0, 9), raw_peer=(5, 9), hops=5, x_hops=5, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 66531 | 63.043 | 65007 | 64.521 | 0xa5000000 | 0xa5000000 |
| 1 | `14,2` | `7,2` | Route(raw0_source=(16, 2), raw0_peer=(10, 2), raw_source=(0, 9), raw_peer=(6, 9), hops=6, x_hops=6, y_hops=0, wraps=0) | 1048576 | 4 | 4.0 | 65771 | 63.771 | 65007 | 64.521 | 0xa5000000 | 0xa5000000 |
