# Pack/Unpack Unit Microbenchmarks

This is the Blackhole Python port of the pack/unpack unit sketch. The entry
point is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 microbenching/tensix/microbench_pack_unpack_units.py --list
```

The combined harness reuses the native Blackhole Python assembly emitters from
`microbench_unpack_backend.py` and `microbench_pack_backend.py`, then reports a
single table of adjusted cycles.

For a real CB-fed unpack stream, use:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 microbenching/tensix/microbench_unpack_stream.py --dtype bf16 --tiles 8 --dump-cb
```

The combined entry point is safe by default: it runs baseline launch/readback
rows only. Name real rows explicitly while bringing up the unit paths:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 microbenching/tensix/microbench_pack_unpack_units.py --unit unpack --unpack-only empty,matmul_unpack_row --unpack-iters 1 --no-report
PYTHONDONTWRITEBYTECODE=1 python3 microbenching/tensix/microbench_pack_unpack_units.py --unit pack --pack-only empty,cb16_final_l1acc_off_room2x --pack-iters 1 --validate-pack --no-report
```

## What We Microbench

- `unpack`: TRISC0 backend/control cost for matmul-style unpack rows. The timed
  path writes unpack base cfg, issues `TTUNPACR`/`TTMOP`, waits on
  `UNPACK_SYNC`, and flips `UNPACK_MISC_CFG_CfgContext`. Synthetic L1 scratch
  pages stand in for CB/DRAM input, so this is not a NOC-feed benchmark.
- `unpack stream`: real BRISC-fed CB0 -> TRISC0 unpack -> SrcA stream. TRISC1
  runs a normal MOVA2D math-consumer MOP so SrcA valid state drains in hardware
  cadence. This answers "once CB data is flowing, what does an unpack tile cost?"
- `unpack` plumbing probes: `PC_UNPACK_SYNC` polling/writes, unpack cfg context
  flips, and `TTSTALLWAIT(UNPACK, TRISC_CFG)`.
- `pack`: TRISC2 backend cost for packing a 2x2 BF16 output subblock into an
  output CB. The standalone pack path seeds DEST with `TTZEROACC`, grants
  `MATH_PACK` tokens, emits the normal pack tile sequence, and can read back L1
  output with `--validate-pack`.

The baseline row is `empty`; displayed cycles per iter/tile subtract that
baseline. Full L1-to-L1 copy, DRAM feed pressure, and concurrent unpack+pack L1
contention are intentionally separate follow-up experiments.

## Bring-Up Notes

As of June 14, 2026, the combined wrapper's baseline launch/readback path passes
on hardware for both TRISC0/unpack and TRISC2/pack. The first real standalone
unpack row and first real standalone pack row both time out on the current dirty
tree, so the next fix is in the copied assembly/config sequence rather than the
host-side result plumbing.

`microbench_unpack_stream.py` now passes for real CB-backed streams. Initial
single-core measurements:

| dtype | tile bytes | tiles | cycles | cycles/tile |
|---|---:|---:|---:|---:|
| bf16 | 2048 | 2 | 752 | 376.0 |
| bf16 | 2048 | 8 | 4507 | 563.4 |
| bf16 | 2048 | 16 | 9466 | 591.6 |
| fp16 | 2048 | 8 | 4457 | 557.1 |
| fp32 | 4096 | 8 | 4915 | 614.4 |

BF16 and FP16 are effectively the same here. FP32 is slower, consistent with the
tile being twice as many bytes. `--dump-cb` confirms unpack leaves the CB0 tile
bytes in L1; it consumes CB state/counters and places decoded data into SrcA.
