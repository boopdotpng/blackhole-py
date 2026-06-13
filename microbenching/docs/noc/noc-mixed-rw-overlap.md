
## Run 2026-06-13T16:45:50-04:00

- NoC: `0`
- Bytes per stream repeat: `1048576`
- Repeats: `1`
- Start gate lead: `200000000` cycles
- Traffic: one read stream plus one write stream, with distinct active source cores

| case | noc | read payload | write payload | read-alone B/cyc | write-alone B/cyc | mixed read B/cyc | mixed write B/cyc | mixed aggregate B/cyc | mixed window cyc |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| independent | 0 | `1,4->4,4` | `10,5->13,5` | 61.681 | 62.808 | 62.046 (64) | 62.699 (64) | 124.077 | 16902 |
| shared-payload-link | 0 | `1,4->4,4` | `2,4->5,4` | 62.046 | 62.838 | 31.756 (64) | 31.824 (64) | 63.512 | 33020 |

## Run 2026-06-13T16:45:52-04:00

- NoC: `1`
- Bytes per stream repeat: `1048576`
- Repeats: `1`
- Start gate lead: `200000000` cycles
- Traffic: one read stream plus one write stream, with distinct active source cores

| case | noc | read payload | write payload | read-alone B/cyc | write-alone B/cyc | mixed read B/cyc | mixed write B/cyc | mixed aggregate B/cyc | mixed window cyc |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| independent | 1 | `4,4->1,4` | `13,5->10,5` | 62.094 | 62.804 | 61.088 (64) | 62.729 (64) | 122.126 | 17172 |
| shared-payload-link | 1 | `4,4->1,4` | `5,4->2,4` | 61.580 | 62.119 | 31.725 (64) | 31.879 (64) | 63.446 | 33054 |
