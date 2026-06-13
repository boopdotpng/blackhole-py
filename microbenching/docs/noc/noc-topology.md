
## Run 2026-06-13T16:46:17-04:00

- Experiments: `C,D`
- Bytes per repeat: `262144`
- Repeats: `2`
- Gate cycles: `200000000`
- Traffic: BRISC nonposted L1-to-L1 unicast writes, 16 KiB chunks, sender wall-clock plus NIU write-ack counters
- Path labels: local model assumes NoC0 ascending/right/down, NoC1 descending/left/up, 20x25 torus, and reports `xy/yx` hop counts

- `C/noc0_wrap_high_to_low`: NoC0 high-x to low-x; a fast result means the ascending ring wraps.
- `C/noc0_forward_same_hops`: Same-row NoC0 forward reference with the same modeled 7-hop distance.
- `C/noc1_high_to_low`: NoC1 direction-compatible high-x to low-x endpoint reference.
- `D/diagonal_baseline`: Diagonal victim alone.
- `D/cross_source_row_x_leg`: Crossing stream on the source-row X leg; slowdown points to X-then-Y routing.
- `D/cross_source_col_y_leg`: Crossing stream on the source-column Y leg; slowdown points to Y-then-X routing.

| exp | scenario | stream | noc | source | target | hops xy/yx | total KiB | cycles | B/cyc | ack chunks | recv sentinel |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| C | noc0_wrap_high_to_low | wrap_wrong_direction | 0 | `14,2` | `1,2` | 7/7 | 512.0 | 8611 | 60.886 | 32 | 0xa5003ffc |
| C | noc0_forward_same_hops | forward_reference | 0 | `7,2` | `14,2` | 7/7 | 512.0 | 8603 | 60.942 | 32 | 0xa5003ffc |
| C | noc1_high_to_low | noc1_directional_reference | 1 | `14,2` | `1,2` | 13/13 | 512.0 | 8650 | 60.611 | 32 | 0xa5003ffc |
| D | diagonal_baseline | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 512.0 | 8707 | 60.215 | 32 | 0xa5003ffc |
| D | cross_source_row_x_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 512.0 | 17009 | 30.824 | 32 | 0xa5003ffc |
| D | cross_source_row_x_leg | x_leg_cross | 0 | `2,2` | `5,2` | 3/3 | 512.0 | 16651 | 31.487 | 32 | 0xa5003ffc |
| D | cross_source_col_y_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 512.0 | 8761 | 59.843 | 32 | 0xa5003ffc |
| D | cross_source_col_y_leg | y_leg_cross | 0 | `1,3` | `1,6` | 3/3 | 512.0 | 8563 | 61.227 | 32 | 0xa5003ffc |

- Experiment C: NoC0 wrap/reference bandwidth ratio is `0.999`.
- Experiment C interpretation: high-x to low-x behaves like the short forward path, consistent with a real wrap link.
- Experiment D: victim bandwidth ratios vs baseline are X-leg `0.512`, Y-leg `0.994`.
- Experiment D interpretation: source-row X crossing interferes more, consistent with X-then-Y routing.
