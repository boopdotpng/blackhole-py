# blackhole-py

A replacement for:
- basically their entire software stack above tt-kmd, including:
- tt-metal
- tt-umd
- tt-llk
- sfpi (C++ compiler)
- ttlang (technically, soon)

## run

```
PYTHONPATH=. python3 examples/add1.py
```

## SFPU programs

`p.sfpu.program()` builds one statically scheduled operation over the SFPU's
32 lanes. `finish()` freezes it, and a mapping method repeats that operation
over the desired Dst region:

```python
b = p.sfpu.program()
x = b.load(format=SfpuFormat.FP32, offset=0)
row_max = b.load(format=SfpuFormat.FP32, offset=64)
b.sub(x, row_max, into=x)
b.free(row_max)
b.exp(x, into=x)
b.store(x, format=SfpuFormat.FP32, offset=128)

p.sfpu.map(b.finish(), tile=0)
```

Pass `region="row"` or `region="column"` to select a partial traversal. Values
are compile-time LReg handles local to one program; explicitly store anything
that must survive. The builder provides load/store, exact constants, move,
add/subtract/multiply/MAD, scalar add/multiply, negation, exponential,
reciprocal, and reciprocal square root for finite positive inputs.

The smallest hardware example uses scalar addition:

```
PYTHONPATH=. python3 examples/add1.py --tiles 1
```

The broader hardware suite covers every public builder operation, all three
mapping regions, FP32 Dst, cross-tile offsets, and the inline fallback:

```
PYTHONPATH=. python3 examples/sfpu_ops.py --operation all
```

## requirements
- blackhole p100a (p150 may not work)
- tt-kmd > 2.9.0
