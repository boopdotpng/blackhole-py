# SFPU movement kernels

Handwritten PoCs for Dst-to-SFPU, SFPU-to-Dst, Src-to-Dst, Dst-to-Src, LReg
copy/constants/rotates/transposes, and broadcasts belong in `test_moves.py`.

## SFPLOAD lane mapping on Blackhole

```sh
PYTHONPATH=. pytest -q -s tests/movement/sfpu/test_load_lanes.py \
  --bh-hardware --bh-device=0 --bh-core=28
```

One hardware test passed on device 0, worker 28. It unpacks FP32 arange(256)
from L1 to logical Dst rows 0–15: two logical 128-element slots, occupying
four physical 16-bit allocator blocks. Eight SFPLOADs use effective addresses
0, 2, 4, 6, 8, 10, 12, 14 and fill LRegs 0–7 before any register is reused.

Each vector is stored into the even columns of a separate four-row output
window. After storing all eight vectors, LReg15's hardware lane IDs (lane*2)
are copied to LReg0 and stored as raw integers in the adjacent odd columns.
The host reconstructs vectors using these IDs, checking all 32 IDs per vector.
This avoids assuming that a same-address load/store round trip proves lane
order. FP32 packing to L1 occurs after SFPU completion; the output sentinel
is also checked. These are fully enabled loads/stores, not a predication test.

Observed vectors, expressed as Python ranges (32 values each):

```python
l0 = list(range(  0,  64, 2))
l1 = list(range(  1,  64, 2))
l2 = list(range( 64, 128, 2))
l3 = list(range( 65, 128, 2))
l4 = list(range(128, 192, 2))
l5 = list(range(129, 192, 2))
l6 = list(range(192, 256, 2))
l7 = list(range(193, 256, 2))
```

The test prints every element of each vector. Thus each consecutive
64-element region becomes two vectors: its even-indexed elements and its
odd-indexed elements.

## Lane predication

```sh
PYTHONPATH=. pytest -q -s tests/movement/sfpu/test_predication.py \
  --bh-hardware --bh-device=0 --bh-core=28
```

Six hardware cases passed. Each unpacks FP32 arange(128), then builds an
index predicate from hardware LReg15 (2*lane) plus the vector position's
logical offset. Cutoffs 64 and 73 exercise whole-vector masks and masks that
split individual vectors, respectively.

- Masked add: load every lane, conditionally add 5, then store every lane.
  This checks that inactive arithmetic lanes retain the original values.
- Masked store: load and add 5 in every lane, then conditionally store.
  This checks that inactive stores leave Dst unchanged.
- Masked load: initialize every LReg lane to -100, conditionally load, then
  store every lane. This checks that inactive loads retain the sentinel.

Both add/store cases produce exactly `x[start:] += 5`. Load cases produce
`where(index >= start, index, -100)`. All cases also verify the next logical
Dst slot remains zero and the packed output's trailing sentinel is intact.
Cutoff 64 alone could be implemented by processing only vector positions
2 and 3; cutoff 73 additionally establishes lane-level discrimination.
