# FP8 E4M3 coverage

The FP8 cases use standard E4M3FN bytes (bias 7, maximum finite magnitude 448),
not BFP8 or BFP4. A 1024-element input or output is 1024 bytes, with no tile
header or shared-exponent section. BF16 cases remain enabled.

Run on card 0, sequentially:

```sh
PYTHONPATH=. pytest -q tests/movement/unpacker tests/movement/packer \
  tests/compute/fpu --bh-hardware --bh-device=0
```

Coverage:

- Unpack every finite normal E4M3 encoding, both signs, through SrcA and SrcB;
  compare widened FP32 output against an independent host decoder. Also test
  FP8 round trips and simultaneous loading of different source banks.
- Pack FP32 Dst into FP8 across Dst tiles 0, 3, and 7, with full tiles and runtime
  tails of 1, 15, 16, 17, and 137 elements. Check output bytes and padding guards.
- Enumerate BF16 and FP8 inputs in the existing ELWADD, ELWMUL, MVMUL, GAPOOL,
  and GMPOOL source-slot cases, including distant, mismatched, and odd slots.
  References use the quantized input values. Compute and FP32 observation
  streams for the four passing operations are byte-identical between formats.

## Hardware details and observed limits

The descriptor uses LF8 code point 10 plus Blackhole's separate
`Unp_LF8_4b_exp` bit. Unpacking expands to FP16 registers: channel-1 strides
remain two bytes per element, and UNPACR/MOP counts remain counts of elements.
Only the L1 representation shrinks. The packer needs `Pac_LF8_4b_exp`, a zero
exponent-section size, and FP16 input after the gasket's 10-bit mantissa
conversion. Merely changing BF16 byte counts is insufficient.

Blackhole MOVA2D/MOVB2D with FP32 accumulation interprets the source as TF32.
For FP8 copy tests we instead preserve FP16 in native Dst and widen with the
packer. FPU arithmetic uses the implied source format and FP32 accumulation.

Card-0 observations are captured explicitly:

- The late FP8 pack conversion truncates mantissas rather than rounding to
  nearest even. A separate test checks positive and negative off-grid values.
  The host encoder uses nearest-even to prepare inputs; it is not a model of
  the packer's rounding.
- Standard E4M3 subnormals do not survive the tested unpack/pack paths.
  Strict expected-failure tests compare against standard E4M3 encodings;
  ordinary correctness cases exercise finite normal values.
- FP8/FP16-source GMPOOL with the existing FP32 Dst fixture fails the numerical
  reference. Those four cases remain strict expected failures. This does not
  establish that native FP16-Dst GMPOOL is unsupported; that alternative has
  not been implemented here.

The FP32-only direct-to-Dst helper remains FP32-only. No block formats, model
loading changes, or software subnormal fixups are included.

Register definitions and conversion setup follow the local Blackhole LLK
`cunpack_common.h` and `cpack_common.h`. The MOVA2D behavior is described in the
[ISA reference](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MOVA2D.md),
including its Blackhole-specific FP32-mode rule.
