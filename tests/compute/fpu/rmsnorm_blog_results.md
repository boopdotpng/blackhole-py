# RMSNorm article comparison

Measured on physical Blackhole card 1, worker index 2 (NoC coordinate `(1, 4)`),
with `test_rmsnorm_blog.py`. Each kernel processes one vector of 2048 BF16
activations and 2048 BF16 weights, with FP32 intermediates and epsilon `1e-5`.

| Interval | SFPU median (min–max) | HiFi4 hybrid median (min–max) |
| --- | ---: | ---: |
| L1 inputs → completed BF16 output in L1 | 1471 (1455–1489) | 1306 (1292–1321) |
| Unpack, source-to-Dst moves, and math | 1084.5 (1069–1103) | 911 (897–927) |
| Output publication and packing | 305 (305–305) | 305 (305–305) |

All values are device wall-clock cycles. The hybrid uses **11.22% fewer total
cycles**, or **1.126× speedup**. These are measured implementations, not minimum
instruction counts or a claim about peak performance.

## Text for the article

### comparing cycle counts

For the 2048-element example, I measured **1471 cycles for the SFPU version**
and **1306 cycles for the HiFi4 hybrid**: moving the weight multiplication to
the FPU saved **11.2% of the cycles**, a **1.13× speedup**.

These are medians over 100 runs after two warmups, alternating which kernel
runs first. Timing starts with both inputs already in L1 and ends when the
packer has finished writing the BF16 output to L1. It includes configuration,
unpacking, copies into dst, math, synchronization, and packing; it excludes
DRAM/NoC transfers and host launch overhead. Packing took 305 cycles in both.

Both kernels issue their math explicitly, without SFPU load macros, math MOPs,
or replay. They share the same unpack/pack MOPs and source-bank prefetching,
the same square-sum accumulation and reduction, and the same rsqrt routine.
The SFPU version uses the x/γ/output layout above and computes `(x*r)*γ`;
the hybrid uses the scratch/product layout and computes `(x*γ)*r` with four
FPU fidelity phases. The hybrid can overlap independent FPU and SFPU work,
though these timings do not establish how much overlap actually occurs.

Both passed checks against a float64 reference using the quantized BF16
inputs, on normal, increasing, small, zero, and outlier-heavy inputs with
signed nonconstant weights. Their BF16 outputs matched on these cases, with
a maximum relative error of 0.3882% against the reference. That does not imply
bitwise equivalence for every input or equivalence to the tinygrad version's
extra BF16 cast before multiplying by the weights.

## Reproduce

From the repository root:

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest -q -s tests/compute/fpu/test_rmsnorm_blog.py --bh-hardware --bh-device=1 --bh-core=2'
```

The benchmark checks every output, output bounds, and that neither kernel
exports an extra scale tensor. Initial math configuration is included in the
total but excluded from the middle interval. Timestamp overhead is retained;
the inner intervals are not an exact decomposition of the total. Unpack and
pack configuration are inside their measured intervals in both kernels.

Queue job: `4b10b544b4cd4542993810524c61e91f`.
