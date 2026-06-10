# Blackhole NoC Topology Probe

Goal: recover two structural facts about the Blackhole NoC from timing:
whether the worker-visible fabric has usable torus wrap links, and whether
diagonal traffic routes X-then-Y or Y-then-X.

The harness lives in `microbenching/noc/riscv_noc_topology_probe.py`.

## What This Measures

Experiment C compares three single write streams:

- NoC0 high-x to low-x, the nominally backward direction for an ascending ring.
- A same-row NoC0 forward reference with the same modeled short wrap distance.
- The same high-x to low-x endpoints on NoC1, whose direction is descending.

If the NoC0 high-to-low stream matches the forward reference, the behavior is
consistent with a true wraparound link. If it is much worse, times out, or only
works cleanly on NoC1, the worker-visible behavior is effectively mesh-like for
that direction.

Experiment D runs a diagonal victim stream, then repeats it with a crossing
stream on the source-row X leg and again with a crossing stream on the
source-column Y leg. The crossing stream that slows the victim identifies the
dimension used by the route out of the source tile.

## Method Notes

- Traffic is BRISC-driven nonposted L1-to-L1 unicast writes only.
- Transfers are chunked into `NOC.MAX_BURST_SIZE` 16 KiB commands.
- Each sender records local `WALL_CLOCK` start/end timestamps and
  `NIU_MST_WR_ACK_RECEIVED` deltas.
- A wall-clock start gate can align simultaneous senders before the timed
  window; set `--gate-cycles 0` to disable it for smoke testing.
- The host-side path labels use a minimal physical model: NoC0 ascends
  right/down, NoC1 descends left/up, coordinates are a 20x25 torus, and the
  x=8,9 worker gap still counts as physical router distance.

## How To Run

Validate without hardware:

```sh
PYTHONPATH=. python3 microbenching/noc/riscv_noc_topology_probe.py --dry-run
```

Run small hardware probes through the shared `tt-device-queue` device owner:

```sh
queue: timeout 120 env PYTHONPATH=. TT_USB=1 python3 microbenching/noc/riscv_noc_topology_probe.py --bytes 262144 --repeats 4
```

If a device run wedges, reset through the same queue owner before retrying:

```sh
tt-device-queue.reset
```

Useful options:

- `--experiments C` or `--experiments D`: run only one experiment.
- `--d-noc 0|1`: choose the NoC instance for Experiment D.
- `--bytes N`: bytes per stream repeat; must be a multiple of 16 KiB.
- `--repeats N`: repeat the chunk train to increase contention signal.
- `--no-report`: print results without appending this file.

## Result Interpretation

For Experiment C, compare `noc0_wrap_high_to_low` against
`noc0_forward_same_hops`. A wrap/reference bandwidth ratio near 1 indicates a
usable torus wrap link. A much lower ratio, especially if the NoC1 reference is
healthy, indicates mesh-like behavior or mandatory direction selection.

For Experiment D, compare the `diagonal_victim` row in
`cross_source_row_x_leg` and `cross_source_col_y_leg` against
`diagonal_baseline`. A stronger slowdown from the X-leg crossing stream points
to X-then-Y routing; a stronger slowdown from the Y-leg crossing stream points
to Y-then-X routing.

## Results

Initial hardware numbers from the shared device queue are recorded below.

## Current Conclusion

Latest run: `2026-06-09T01:42:23-04:00`, after the shared card reboot, with
AICLK reported externally as 800 MHz. Treat cycles as the primary measurement.

- Experiment C: NoC0 high-x to low-x completed in `16969` cycles versus
  `16825` cycles for the same-hop NoC0 forward reference, a wrap/reference
  bandwidth ratio of `0.992`. The NoC1 same-endpoint directional reference was
  also healthy at `16839` cycles. Conclusion: the high-x to low-x NoC0 path is
  not mesh-blocked; behavior is consistent with a usable torus wrap link.
- Experiment D: the diagonal victim took `16937` cycles alone, `33519` cycles
  with the source-row X-leg crossing stream, and `16951` cycles with the
  source-column Y-leg crossing stream. Conclusion: the route uses the X leg
  first, consistent with X-then-Y dimension order.

## Run 2026-06-09T00:43:19-04:00

- Experiments: `C,D`
- Bytes per repeat: `262144`
- Repeats: `4`
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
| C | noc0_wrap_high_to_low | wrap_wrong_direction | 0 | `14,2` | `1,2` | 7/7 | 1024.0 | 16825 | 62.322 | 64 | 0xa5003ffc |
| C | noc0_forward_same_hops | forward_reference | 0 | `7,2` | `14,2` | 7/7 | 1024.0 | 16825 | 62.322 | 64 | 0xa5003ffc |
| C | noc1_high_to_low | noc1_directional_reference | 1 | `14,2` | `1,2` | 13/13 | 1024.0 | 16895 | 62.064 | 64 | 0xa5003ffc |
| D | diagonal_baseline | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 16937 | 61.910 | 64 | 0xa5003ffc |
| D | cross_source_row_x_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 33528 | 31.275 | 64 | 0xa5003ffc |
| D | cross_source_row_x_leg | x_leg_cross | 0 | `2,2` | `5,2` | 3/3 | 1024.0 | 33161 | 31.621 | 64 | 0xa5003ffc |
| D | cross_source_col_y_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 16944 | 61.885 | 64 | 0xa5003ffc |
| D | cross_source_col_y_leg | y_leg_cross | 0 | `1,3` | `1,6` | 3/3 | 1024.0 | 16881 | 62.116 | 64 | 0xa5003ffc |

- Experiment C: NoC0 wrap/reference bandwidth ratio is `1.000`.
- Experiment C interpretation: high-x to low-x behaves like the short forward path, consistent with a real wrap link.
- Experiment D: victim bandwidth ratios vs baseline are X-leg `0.505`, Y-leg `1.000`.
- Experiment D interpretation: source-row X crossing interferes more, consistent with X-then-Y routing.

## Run 2026-06-09T01:42:23-04:00

- Experiments: `C,D`
- Bytes per repeat: `262144`
- Repeats: `4`
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
| C | noc0_wrap_high_to_low | wrap_wrong_direction | 0 | `14,2` | `1,2` | 7/7 | 1024.0 | 16969 | 61.794 | 64 | 0xa5003ffc |
| C | noc0_forward_same_hops | forward_reference | 0 | `7,2` | `14,2` | 7/7 | 1024.0 | 16825 | 62.322 | 64 | 0xa5003ffc |
| C | noc1_high_to_low | noc1_directional_reference | 1 | `14,2` | `1,2` | 13/13 | 1024.0 | 16839 | 62.271 | 64 | 0xa5003ffc |
| D | diagonal_baseline | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 16937 | 61.910 | 64 | 0xa5003ffc |
| D | cross_source_row_x_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 33519 | 31.283 | 64 | 0xa5003ffc |
| D | cross_source_row_x_leg | x_leg_cross | 0 | `2,2` | `5,2` | 3/3 | 1024.0 | 33161 | 31.621 | 64 | 0xa5003ffc |
| D | cross_source_col_y_leg | diagonal_victim | 0 | `1,2` | `4,5` | 6/6 | 1024.0 | 16951 | 61.859 | 64 | 0xa5003ffc |
| D | cross_source_col_y_leg | y_leg_cross | 0 | `1,3` | `1,6` | 3/3 | 1024.0 | 16849 | 62.234 | 64 | 0xa5003ffc |

- Experiment C: NoC0 wrap/reference bandwidth ratio is `0.992`.
- Experiment C interpretation: high-x to low-x behaves like the short forward path, consistent with a real wrap link.
- Experiment D: victim bandwidth ratios vs baseline are X-leg `0.505`, Y-leg `0.999`.
- Experiment D interpretation: source-row X crossing interferes more, consistent with X-then-Y routing.
