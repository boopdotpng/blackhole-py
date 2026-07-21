# Llama 3 Blackhole kernels

All shapes in this document distinguish between:

- **Logical shape:** the tensor shape seen by the model.
- **Tiled shard shape:** how the tensor is divided across worker cores and
  32x32 tiles in DRAM.
- **Physical storage shape:** the dense allocation, including padding needed
  because every shard has the same stride.

The current prefill bucket is 1024 tokens, the embedding dimension is 2048,
and one token row therefore occupies two 32x32 BF16 tiles.

## Shared 118-core token layout

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

### Shapes

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

### Per-core dataflow

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

## block repeated 16 times

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

#### Shapes

```text
x logical:              BF16[1024, 2048]
x ragged tiled:         [80 x (9, 2, 32, 32)]
                        + [38 x (8, 2, 32, 32)]
x physical storage:     (118, 18, 32, 32)

weight logical:         BF16[2048]
weight tiled:           (2, 32, 32), globally addressed

output logical:         BF16[1024, 2048]
output ragged tiled:    [80 x (9, 2, 32, 32)]
                        + [38 x (8, 2, 32, 32)]
output physical storage:(118, 18, 32, 32)
```

#### Per-core dataflow

```text
At program start, on every core:
    BRISC reads weight[:1024]  -> persistent gamma_l1 tile 0
    BRISC reads weight[1024:]  -> persistent gamma_l1 tile 1

x_cb:
    BF16, depth 4 tiles
    enough buffering for two input tokens

output_cb:
    BF16, depth 4 tiles
    enough buffering for two output tokens

for local_token in range(compile_time_token_count):  # 9 or 8

    BRISC -- input DMA:
        read x[local_token, 0, :, :] from sharded DRAM -> x_cb
        read x[local_token, 1, :, :] from sharded DRAM -> x_cb

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

    TRISC1 / SFPU -- sum of squares:
        select Dst tile 0
        for each of its four faces:
            load FP32 x lanes
            square the lanes
            accumulate into SFPU L7

        select Dst tile 1
        for each of its four faces:
            load FP32 x lanes
            square the lanes
            accumulate into the same SFPU L7

    TRISC1 / SFPU -- scalar normalization factor:
        reduce the 32 accumulator lanes in L7 to sum(x^2)
        mean_square = sum(x^2) * (1 / 2048)
        adjusted = mean_square + 1e-5
        scale = rsqrt(adjusted)

        The final scale is broadcast across the SFPU lanes in L0.
        Reciprocal square root uses an FP32 initial approximation followed
        by refinement; the normalization arithmetic remains FP32.

    TRISC1 / SFPU -- apply scale and weight:
        select Dst tile 0:
            Dst0 = FP32(Dst0 * scale * Dst2)

        select Dst tile 1:
            Dst1 = FP32(Dst1 * scale * Dst3)

        Dst2 and Dst3 are the matching gamma tiles. This multiply happens
        in SFPU, not the BF16 FPU elementwise path, to preserve FP32 precision.

    TRISC2 -- pack:
        pack FP32 Dst0 -> BF16 output_cb tile
        pack FP32 Dst1 -> BF16 output_cb tile
        both tiles are packed under one Math-to-Pack destination handoff

    NCRISC -- output DMA:
        write output_cb -> output[local_token, 0, :, :]
        write output_cb -> output[local_token, 1, :, :]
```

BRISC, the three TRISCs, and NCRISC execute as a producer/consumer pipeline;
the circular buffers provide backpressure between stages. The loop count is
compiled into each core's 9-token or 8-token image.

Using the real `model.layers.0.input_layernorm.weight`, the 118-core kernel
measures 33.573 us best-case and about 36.8 us median. It matches 2,097,145 of
2,097,152 BF16 outputs exactly; the remaining seven values differ by one BF16
ULP (`max_abs = 0.000976562`, `relative_L2 = 5.95e-6`, PCC = 1.0).

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
Blackhole 118 cores       36.80 us  █████████████████████████████████████
RTX 5090  eager exact     40.80 us  █████████████████████████████████████████
Blackhole 64 cores        41.80 us  ██████████████████████████████████████████
```

The 118-core split lowers Blackhole median latency by about 12% relative to
the 64-core kernel. It is about 1.85x slower than the exact `torch.compile`
expression and 6.1x slower than the 5090 native fused RMSNorm.

### attention

#### qkv proj matmuls

#### apply rope 

#### save new kv cache to dram 

#### gqa shit somewhere? 

#### score matmul and sqrt head scaling

#### mask creation (prefill only)

#### softmax

#### output projection matmul 

### residual add (eltwise)

### rmsnorm part 2

### mlp

### residual add p2

## rmsnorm part 3

## logits = x @ self.embed_tokens.weight.T

## argmax 
