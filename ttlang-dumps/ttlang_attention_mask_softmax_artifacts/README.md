# TT-Lang Attention Mask + Softmax Artifacts

These dumps target the Llama attention score path for `B=1`, `n_heads=32`, and tiled score rows shaped as flattened `(B * n_heads * ceil(S / 32), ceil(T / 32))`.

The checked-in generated cases use one S tile per head and four T tiles:

- Logical score shape: `(B=1, n_heads=32, S=32, T=128)`
- Flattened tiled tensor shape: `(1024, 128)` elements, or `(32, 4)` tiles
- Grid: `(1, 32)`, one core per head/S-tile row
- Score dtype: f32

`mask_scale_add_f32` compiles the scale plus mask-bias add stage:

```text
masked_scores = scores * 0.125 + mask_bias
```

The mask is modeled as an input f32 bias tensor because this TT-Lang build exposes elementwise compares (`lt`, `gt`) but no `where`/`select` primitive for generating a per-element causal mask in the compute DSL.

`softmax_row_f32` compiles the f32 row-softmax stage:

```text
mx = reduce_max(masked_scores, dim=T)
ex = exp(masked_scores - broadcast(mx))
den = reduce_sum(ex, dim=T)
probs = ex * recip(broadcast(den))
```

The output is f32 in this artifact so the generated path keeps probabilities in f32. Packing probabilities to bf16 can be done as a follow-up output dtype change once the f32 score path is wired into the model.

The softmax harness reads the score row into two f32 CBs. This is intentional: TT-Lang currently rejects a single f32 CB feeding both the reduce/FPU path and the SFPU `sub`/`exp` path because those consumers need incompatible unpack modes.
