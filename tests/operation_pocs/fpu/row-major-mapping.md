# Native row-major matrix mapping

Hardware: Blackhole device 0, worker 28 (3,10), September 8, 2026.
`test_row_major_mapping.py`: 24 passed. Full zero-initialized output matrices
are in `row-major-mapping-results.json`.

Run through the device queue:

```sh
tt-device-queue run --device 0 --cwd /home/boop/tenstorrent/blackhole-py -- 'PYTHONPATH=. /home/boop/tenstorrent/.venv/bin/python -m pytest -q -s tests/operation_pocs/fpu/test_row_major_mapping.py --bh-hardware --bh-device=0 --bh-core=28'
```

The existing fixture loads sequential BF16 bytes with non-tilizing unpack,
executes one logical HiFi2 operation (two fidelity instructions for multiply),
and packs FP32 results without reordering. A128 allocation pairs are one
16x16 matrix, not two 16x16 matrices. B128 is an 8x16 matrix.

For A = arange(256).reshape(16,16), B = arange(128).reshape(8,16), the
mathematical MVMUL result is D[r,c] += 19840 + 30720*r + (120 + 256*r)*c.
GAPOOL computes the same product for r=0..3 and preserves rows 4..7.
Measured HiFi2 maximum absolute deviations are 4 and 1 respectively; the
test allows those bounds only inside the affected arange product footprint.
These are characterization bounds for these inputs, not general precision
guarantees. For example, MVMUL returns D[2,1]=81913 versus exact 81912,
and D[7,15]=263563 versus exact 263560.

Two additional B selector matrices select A rows 0..7 and 8..15, respectively.
Both match exactly and expose the complete coordinate mapping independently
of the arange arithmetic deviations. With B=1, GAPOOL produces four identical
rows [1920,1936,...,2160]; it does not divide by 16 automatically. With B=1,
GMPOOL produces [240,241,...,255] in row 0, clears rows 1..3, and preserves
rows 4..7. General GMPOOL exponent scaling is outside this test's contract.

All cases run at the first and last legal allocation placements, with Dst
initialized to zero and to 2**20. The latter checks additive accumulation and
max retention. Untouched Dst values and trailing L1 guards must match exactly.
An exploratory 1,000,000 GMPOOL seed returned 999,936: GMPOOL does not preserve
arbitrary FP32 accumulator precision. The final exact max-retention control
uses 2**20, which is exactly representable in the pooling datapath.

In `blackhole-py-llama3-8b/examples/llama3.py`, `_projection_dot_math` uses
ELWMUL plus SFPU summation for decode GEMV. Matching contiguous weight and
activation chunks require no tilization. Attention uses `move_matmul` and
`fpu.matmul` on internally tiled fragments; score multiplication explicitly
enables a SrcA face transpose. Row-max reduction also explicitly transposes
faces before GMPOOL. Non-tilizing unpack is not a promise that no transpose
or internal layout conversion occurs elsewhere in inference.
