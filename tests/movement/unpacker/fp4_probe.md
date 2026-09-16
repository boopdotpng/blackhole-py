# Raw E2M1 nibble probe on Blackhole

Measured 2026-09-15 on device 0, worker (1, 2), with the custom runtime.

```sh
tt-device-queue run --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 120 -- \
  ../.venv/bin/python -m pytest -x -s -q tests/movement/unpacker/test_fp4_probe.py --bh-hardware --bh-device=0
```

Result: **4 passed**, 16 hardware launches (two source banks × two forced
exponents × source snapshot/FPU multiply × raw/control inputs).
Queue job: `2de04dae29064c02bbea3852a6fcf732`.

Each raw operand is exactly 64 bytes: an 8×16 block of packed nibbles, low
nibble first. Every row contains all 16 encodings in a different permutation.
The unpacker is explicitly configured as hardware BFP4 (format code 7), with
a forced shared exponent and no exponent header. The other operand is BF16
ones. ELWMUL uses HiFi2 and zeroed FP32 accumulation. A separate launch copies
the selected source bank to native BF16 Dst for observation, avoiding the
TF32 interpretation of MOVA/B2D in FP32 Dst mode.

| Nibble | Intended E2M1 | Unpacked, exponent 128 | FPU × 1 |
|---|---:|---:|---:|
| 0x0 | 0 | 0 | 0 |
| 0x1 | 0.5 | 0.5 | 0.5 |
| 0x2 | 1 | 1 | 1 |
| 0x3 | 1.5 | 1.5 | 1.5 |
| 0x4 | 2 | 2 | 2 |
| 0x5 | 3 | 2.5 | 2.5 |
| 0x6 | 4 | 3 | 3 |
| 0x7 | 6 | 3.5 | 3.5 |
| 0x8 | −0 | −∞ | −∞ |

Codes 0x9–0xf produce the negatives of codes 0x1–0x7. With exponent 129,
finite outputs double: magnitudes are 0 through 7. Both source banks agree.
All 128 lanes match the BFP4 reference. The decoded BF16 control matches the
intended E2M1 numerical values for both snapshots and multiplication (zero
sign is not asserted). Input bytes remain unchanged and output guards pass.

Conclusion: feeding packed E2M1 codes to the BFP4 unpacker changes their
meaning before arithmetic; the FPU faithfully multiplies those expanded
values. This probes the documented BFP4 path, not an undocumented E2M1 mode
or a direct packed-nibble injection into source registers. It is a correctness
probe, not a throughput benchmark or a full MXFP4 block-scale implementation.
