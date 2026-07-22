# Llama 3 Blackhole kernels

All shapes in this document distinguish between:

- **Logical shape:** the tensor shape seen by the model.
- **Tiled shard shape:** how the tensor is divided across worker cores and
  32x32 tiles in DRAM.
- **Physical storage shape:** the dense allocation, including padding needed
  because every shard has the same stride.

The current prefill bucket is 1024 tokens, the embedding dimension is 2048,
and one token row therefore occupies two 32x32 BF16 tiles.

## Prefill 118-core token layout

The 1024 token rows are distributed as:

```text
cores 0..79:    80 cores x 9 tokens = 720 tokens
cores 80..117:  38 cores x 8 tokens = 304 tokens
                                      -----------
                                      1024 tokens
```

Each DRAM shard reserves space for nine tokens so all shard bases have one
fixed stride. The resulting views are:

```text
logical:          (1024, 2048)
ragged tiled:     [80 x (9, 2, 32, 32)] + [38 x (8, 2, 32, 32)]
physical storage: (118, 18, 32, 32)
```

The last 38 cores leave physical tile slots 16 and 17 unused. Those are the
two tiles for the absent ninth token; they are storage padding, not logical
tokens.

Two compile-time kernel variants are installed in one heterogeneous launch:
the first 80 cores receive a 9-token loop and the remaining 38 receive an
8-token loop. All 118 cores still start and finish as one program.

## Embedding lookup

### Prefill

Status: implemented. `valid_s` selects the real rows inside the fixed
1024-token allocation.

#### Shapes

```text
token_ids logical:       U32[1024]             # first S IDs are valid
token_ids physical:      (1, 1, 32, 32)        # one globally addressed tile

weight logical:          BF16[128256, 2048]
weight tiled:            (128256, 2, 32, 32)   # globally addressed

output logical:          BF16[1024, 2048]
output ragged tiled:     [80 x (9, 2, 32, 32)]
                         + [38 x (8, 2, 32, 32)]
output physical storage: (118, 18, 32, 32)
```

There is no numerical operation and no runtime reshape. Embedding is a tiled
DRAM gather followed by a sharded DRAM write.

#### Per-core dataflow

```text
At program start:
    local_count = clamp(S - token_start, 0, compile_time_capacity)
    compile_time_capacity is 9 or 8

BRISC:
    if local_count != 0:
        read the shared U32 token-ID tile from DRAM into local L1

    for local_token in range(local_count):
        global_token = token_start + local_token
        token_id = ids_l1[global_token]

        read weight[token_id, 0, :, :] -> embedding_cb
        read weight[token_id, 1, :, :] -> embedding_cb

embedding_cb:
    BF16, depth 4 tiles
    holds up to two complete 2048-element token rows

NCRISC:
    for local_token in range(local_count):
        write embedding_cb tile -> output[local_token, 0, :, :]
        write embedding_cb tile -> output[local_token, 1, :, :]

TRISC0 / TRISC1 / TRISC2:
    idle; embedding does not use unpack, FPU, SFPU, or pack
```

For a full 1024-token lookup using the real model weight, the 118-core kernel
is exact BF16 and measures 34.022 us minimum / 34.442 us median. Effective
embedding-row read plus output write bandwidth is 243.559 GB/s.

### Decode

Status: planned. Decode needs the same two-tile gather body with one token on
one core; launching the 118-core prefill program for one token would waste the
other workers.

```text
token_ids logical:   U32[1]
weight logical:      BF16[128256, 2048]
output logical:      BF16[1, 2048]
output tiled:        (1 core, 1 token, 2 tiles, 32, 32)
```

The decode image should load one token ID, gather the two weight-row tiles,
and write the two output tiles directly, with no token loop.

## Transformer block repeated 16 times

### RMSNorm

The fused operation is:

```text
xf = x.float()
output = (
    xf * rsqrt(mean(xf * xf, axis=-1, keepdims=True) + 1e-5)
       * weight.float()
).cast(BF16)
```

Normalization is independent for every token. A token is split across two
tiles, so both tiles must contribute to the same 2048-element sum of squares.

#### Prefill

Status: implemented with `valid_s` and buckets 128, 256, 512, and 1024.

```text
x/output logical:        BF16[valid_s, 2048]
x/output allocated:      BF16[bucket, 2048]

weight logical:          BF16[2048]
weight tiled:            (2, 32, 32), globally addressed
```

The prefill program selects a tuned core count for each bucket. The logical
shape remains unchanged; only the number and capacity of DRAM shards vary:

```text
valid_s     bucket   cores   token capacities/core   physical storage
-------     ------   -----   ---------------------   ----------------
2..128      128      64      64x2                    (64, 4, 32, 32)
129..256    256      64      64x4                    (64, 8, 32, 32)
257..512    512      73      1x8 + 72x7              (73, 16, 32, 32)
513..1024   1024     73      2x15 + 71x14            (73, 30, 32, 32)
```

For prefill, every RISC computes
`local_count = clamp(valid_s - token_start, 0, token_capacity)`. Padded rows
are never read or written and downstream bucketed kernels must also ignore
them.

#### Decode

Status: implemented as the loop-free specialization of the same RMSNorm code
generator.

```text
x logical:               BF16[1, 2048]
weight logical:          BF16[2048]
output logical:          BF16[1, 2048]
x/output physical:       (1 core, 2 tiles, 32, 32)
valid_s:                 1
```

Only one core is launched. Its BRISC reads the two input and two weight tiles,
and all five RISC images invoke the shared token body directly without a token
loop.

#### Shared per-core dataflow

```text
At program start, on every launched core:
    BRISC reads weight[:1024]  -> persistent gamma_l1 tile 0
    BRISC reads weight[1024:]  -> persistent gamma_l1 tile 1

x_cb:
    BF16, depth 4 tiles
    enough buffering for two input tokens

output_cb:
    BF16, depth 4 tiles
    enough buffering for two output tokens

prefill:
    local_count = clamp(valid_s - token_start, 0, token_capacity)
    execute token_body(local_token) for local_token in range(local_count)

decode:
    execute token_body(0) directly  # no loop

token_body(local_token):
    BRISC -- input DMA:
        read the two x tiles from sharded DRAM -> x_cb
        issue them as one paired transaction through bucket 512
        serialize them at bucket 1024 to avoid NoC/DRAM saturation

    TRISC0 -- unpack:
        unpack x tile 0 from x_cb       -> SrcA
        unpack x tile 1 from x_cb       -> SrcA
        unpack gamma_l1 tile 0          -> SrcA
        unpack gamma_l1 tile 1          -> SrcA

    TRISC1 / FPU -- BF16 to FP32 destination copies:
        SrcA x tile 0      -> FP32 Dst tile 0
        SrcA x tile 1      -> FP32 Dst tile 1
        SrcA gamma tile 0  -> FP32 Dst tile 2
        SrcA gamma tile 1  -> FP32 Dst tile 3
        configure common copy state once for all four tiles

    TRISC1 / SFPU -- sum of squares:
        select Dst tile 0
        for each of its four faces:
            load FP32 x lanes
            accumulate x*x into SFPU L7 with one fused MAD

        select Dst tile 1
        for each of its four faces:
            load FP32 x lanes
            square the lanes
            accumulate into the same SFPU L7

    TRISC1 / SFPU -- scalar normalization factor:
        butterfly-reduce the 32 accumulator lanes in L7 to sum(x^2)
        mean_square = sum(x^2) * (1 / 2048)
        adjusted = mean_square + 1e-5
        scale = rsqrt(adjusted)

        The final scale is broadcast across the SFPU lanes in L0.
        Reciprocal square root uses an FP32 initial approximation followed
        by refinement; the normalization arithmetic remains FP32.

    TRISC1 / SFPU -- apply scale and weight:
        process two independent 32-lane footprints together
        overlap x*scale with each gamma load using SFPLOADMACRO
        Dst0 = FP32(Dst0 * scale * Dst2)
        Dst1 = FP32(Dst1 * scale * Dst3)

        Dst2 and Dst3 are the matching gamma tiles. This multiply happens
        in SFPU, not the BF16 FPU elementwise path, to preserve FP32 precision.

    TRISC2 -- pack:
        pack FP32 Dst0 -> BF16 output_cb tile
        pack FP32 Dst1 -> BF16 output_cb tile
        configure common pack state once for both tiles
        both tiles share one Math-to-Pack destination handoff

    NCRISC -- output DMA:
        write both output tiles in one paired transaction
```

BRISC, the three TRISCs, and NCRISC execute as a producer/consumer pipeline;
the circular buffers provide backpressure between stages. Prefill capacity is
compiled into each core image while `valid_s` supplies the runtime loop bound.
The one-core decode specialization invokes the same token body directly.

Final 101-launch hardware measurements using the real
`model.layers.0.input_layernorm.weight`:

```text
valid_s / bucket   cores   min / p10 / median / p90 latency
----------------   -----   --------------------------------
1 / 1              1       4.787 / 4.795 / 4.804 / 4.844 us
128 / 128          64      9.176 / 9.224 / 9.316 / 9.478 us
256 / 256          64      11.872 / 12.070 / 12.274 / 12.584 us
512 / 512          73      17.790 / 18.102 / 18.584 / 19.173 us
1024 / 1024        73      28.273 / 28.564 / 28.995 / 29.504 us
```

Decode is bit-exact. Across the prefill buckets, every non-exact value differs
from the fused FP32 CPU expression by one BF16 ULP at most
(`max_abs = 0.000976562`, worst `relative_L2 = 8.8913e-6`, PCC = 1.0). At
1024 tokens, 2,097,144 of 2,097,152 values are exact.

For comparison, the multicast dispatcher launch floor is about 3.04 us for 118
cores. The previous serialized-unicast dispatcher cost 38.324 us for an empty
118-core launch and hid almost all of the benefit of this sharding.

The dispatcher writes the GO payload into its own L1, fences that store, and
then multicasts the word to three rectangles covering exactly the 118 worker
cores. The fence is required: without it, a cold first multicast can source
the previous zero value and desynchronize queued programs.

#### RMSNorm latency comparison

All GPU numbers below use BF16 input/output and CUDA device timing. The 5090
cold-DRAM test cycles through 256 MiB of inputs. Blackhole numbers include its
device launch floor.

```text
RTX 5090  F.rms_norm       6.02 us  ██████
RTX 5090  torch.compile   19.94 us  ████████████████████
Blackhole 73 cores        29.00 us  █████████████████████████████
RTX 5090  eager exact     40.80 us  █████████████████████████████████████████
Blackhole 64 cores        41.80 us  ██████████████████████████████████████████
```

The tuned Blackhole path is about 1.45x slower than the exact `torch.compile`
expression and 4.8x slower than the 5090 native fused RMSNorm. Relative to the
original 118-core Blackhole kernel's 36.589 us median, it is 20.8% faster.
Forcing the optimized implementation back to 118 cores gives 32.185 us median,
so both instruction/dataflow improvements and the lower-contention 73-core
split contribute.

### Attention

Status: planned. The prefill and decode paths have materially different
matrix shapes and should use different matmul schedules.

#### QKV projection matmuls

##### Prefill

```text
x: (valid_s, 2048), allocated to bucket rows

Q = x @ Wq.T: (valid_s, 2048) -> (32, valid_s, 64)
K = x @ Wk.T: (valid_s,  512) -> ( 8, valid_s, 64)
V = x @ Wv.T: (valid_s,  512) -> ( 8, valid_s, 64)
```

These are matrix-matrix operations with `M = bucket`; all 118 cores should
participate. Padded output rows must be ignored using the same `valid_s`.

##### Decode

```text
x: (1, 2048)

Q: (1, 2048) -> (32, 1, 64)
K: (1,  512) -> ( 8, 1, 64)
V: (1,  512) -> ( 8, 1, 64)
```

These are GEMVs, not one-core operations. Weight/output columns should be
sharded across all cores while the 2048-element activation is replicated.

#### RoPE

##### Prefill

Apply RoPE to all `valid_s` Q/K positions. Position IDs cover the full prompt,
and padded bucket rows are skipped.

```text
Q: (32, valid_s, 64)
K: ( 8, valid_s, 64)
```

##### Decode

Apply RoPE only to the newly generated Q/K vectors using the current absolute
position. This is 32 Q heads and 8 K heads at one position.

#### KV-cache write

##### Prefill

Write all valid prompt keys and values into cache positions `[0:valid_s]`:

```text
K cache update: (8, valid_s, 64)
V cache update: (8, valid_s, 64)
```

##### Decode

Append one K/V vector per KV head at cache position `kv_len - 1`:

```text
K cache update: (8, 1, 64)
V cache update: (8, 1, 64)
```

#### Grouped-query head mapping

There are 32 query heads and 8 KV heads, so each KV head serves four query
heads. Prefill and decode use the same 4:1 mapping; only their query counts
differ.

#### Score matmul and head scaling

##### Prefill

```text
Q:      (32, valid_s, 64)
K:      ( 8, valid_s, 64), shared 4:1
scores: (32, valid_s, valid_s)

scores = (Q @ K.T) * (1 / sqrt(64))
```

The allocation uses the selected sequence bucket in both score dimensions.

##### Decode

```text
Q:       (32, 1, 64)
K cache: ( 8, kv_len, 64), shared 4:1
scores:  (32, 1, kv_len)
```

Parallelism comes from heads and shards of the KV-cache length.

#### Attention mask

##### Prefill

Apply the causal mask and mask padded key positions `>= valid_s`. Padded query
rows are not executed.

##### Decode

There are no future cached positions, so only invalid/padded KV-bucket entries
need masking. The real reduction length is `kv_len`.

#### Softmax

##### Prefill

```text
input/output: (32, valid_s, valid_s)
reduction:    each query row across valid key positions
```

The tiled implementation reduces row maxima and sums across all key tiles for
each 32-row query block.

##### Decode

```text
input/output: (32, 1, kv_len)
reduction:    one score row per query head across the KV cache
```

This needs a head/KV-length sharding strategy rather than the 1024-query-block
prefill layout.

#### Attention-value matmul

##### Prefill

```text
probabilities: (32, valid_s, valid_s)
V:             ( 8, valid_s, 64), shared 4:1
context:       (32, valid_s, 64) -> (valid_s, 2048)
```

##### Decode

```text
probabilities: (32, 1, kv_len)
V cache:       ( 8, kv_len, 64), shared 4:1
context:       (32, 1, 64) -> (1, 2048)
```

#### Attention output projection

##### Prefill

```text
(valid_s, 2048) @ (2048, 2048) -> (valid_s, 2048)
```

This is a bucketed matrix-matrix operation using all cores.

##### Decode

```text
(1, 2048) @ (2048, 2048) -> (1, 2048)
```

This is an all-core GEMV with output columns sharded across cores.

### Attention residual add

#### Prefill

Elementwise add two `BF16[valid_s, 2048]` tensors using the selected bucket
layout and skipping padded rows.

#### Decode

Elementwise add two `BF16[1, 2048]` tensors. This is two tiles and will likely
run on one core until it is fused with a neighboring kernel.

### Post-attention RMSNorm

Prefill and decode use the same implemented RMSNorm variants described above,
with a different layer weight.

### MLP

Status: planned. Prefill needs GEMMs; decode needs all-core GEMVs.

#### Gate and up projections

##### Prefill

```text
gate = x @ W_gate.T: (valid_s, 2048) @ (2048, 8192)
up   = x @ W_up.T:   (valid_s, 2048) @ (2048, 8192)
```

Both outputs are bucketed `BF16[valid_s, 8192]` tensors.

##### Decode

```text
gate: (1, 2048) @ (2048, 8192) -> (1, 8192)
up:   (1, 2048) @ (2048, 8192) -> (1, 8192)
```

All cores own output-neuron slices; decode must not run these projections on
one core.

#### SiLU and gated multiply

##### Prefill

```text
hidden = silu(gate) * up: BF16[valid_s, 8192]
```

Use `valid_s` to skip padded rows.

##### Decode

```text
hidden = silu(gate) * up: BF16[1, 8192]
```

The 8192 features remain distributed like the gate/up GEMV outputs.

#### Down projection

##### Prefill

```text
(valid_s, 8192) @ (8192, 2048) -> (valid_s, 2048)
```

##### Decode

```text
(1, 8192) @ (8192, 2048) -> (1, 2048)
```

Decode shards the 8192-element reduction and/or 2048 output features across
all cores, followed by the required cross-core accumulation.

### MLP residual add

#### Prefill

Elementwise add two `BF16[valid_s, 2048]` tensors in the selected bucket.

#### Decode

Elementwise add two `BF16[1, 2048]` tensors on one core until fused.

## Final RMSNorm

Prefill and decode use the same implemented RMSNorm code generator. Prefill
selects a bucket and runtime `valid_s`; decode selects the loop-free one-core
image.

## Logits projection

### Prefill

If logits are required for every prompt position:

```text
(valid_s, 2048) @ embedding_weight.T -> (valid_s, 128256)
```

For generation, computing only the final valid prompt row avoids unnecessary
prompt-position logits.

### Decode

```text
(1, 2048) @ embedding_weight.T -> (1, 128256)
```

This is an all-core GEMV sharded across vocabulary columns.

## Token selection

### Prefill

Select from the logits for the last valid prompt position when beginning
generation.

### Decode

Run argmax or sampling over the 128256 vocabulary logits. The vocabulary
reduction should be distributed; only the winning token/scalar state needs to
leave the device.
