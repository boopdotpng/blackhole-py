# Llama 3 Blackhole kernels

All shapes in this document distinguish between:

- **Logical shape:** the tensor shape seen by the model.
- **Tiled shard shape:** how the tensor is divided across worker cores and
  32x32 tiles in DRAM.
- **Physical storage shape:** the dense allocation, including padding needed
  because every shard has the same stride.

The fixed prefill capacity is 1024 tokens, the embedding dimension is 2048,
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

Status: implemented with a fixed 1024-token capacity and runtime `valid_s`.

```text
x/output logical:        BF16[valid_s, 2048]
x/output allocated:      BF16[1024, 2048]
x/output physical:       (118, 18, 32, 32)

weight logical:          BF16[2048]
weight tiled:            (2, 32, 32), globally addressed
```

RMSNorm uses the embedding output's existing 118-core token sharding, so the
two operations compose without a reshard:

```text
cores 0..79:    80 cores x 9-token capacity
cores 80..117:  38 cores x 8-token capacity
```

For prefill, every RISC computes
`local_count = clamp(valid_s - token_start, 0, token_capacity)`. Padded rows
are never read or written and downstream kernels must also ignore them.

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
        issue them as one paired transaction for decode
        serialize them for fixed-capacity prefill to avoid NoC/DRAM saturation

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

The fixed-capacity implementation retains the optimized RMSNorm instruction
and dataflow body. Existing hardware measurements using the real
`model.layers.0.input_layernorm.weight` include:

```text
mode                valid_s / capacity   cores   median latency
------------------  ------------------   -----   --------------
decode              1 / 1                1       4.804 us
prefill             1024 / 1024          118     32.401 us
```

Decode is bit-exact. Across the measured prefill lengths, every non-exact
value differs from the fused FP32 CPU expression by one BF16 ULP at most
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
Blackhole 118 cores       32.40 us  ████████████████████████████
RTX 5090  eager exact     40.80 us  █████████████████████████████████████████
```

The retained optimized 118-core path is faster than the original 118-core
kernel's 36.589 us median. It deliberately gives up the previous 73-core
shape tuning so embedding and RMSNorm share one fixed prefill layout.

### Attention

Status: decode Q/K/V projection implemented; prefill and the remaining
attention kernels are planned. Prefill and decode have materially different
matrix shapes and use different schedules.

#### QKV projection matmuls

##### Prefill

```text
x: (valid_s, 2048), allocated to 1024 rows

Q = x @ Wq.T: (valid_s, 2048) -> (32, valid_s, 64)
K = x @ Wk.T: (valid_s,  512) -> ( 8, valid_s, 64)
V = x @ Wv.T: (valid_s,  512) -> ( 8, valid_s, 64)
```

These are matrix-matrix operations with `M_tiles = ceil(valid_s / 32)` inside
the fixed 1024-row allocation. Padded output rows must be ignored using the
same `valid_s`.

##### Decode

```text
x:       (1, 2048) logically
Wq:      (2048, 2048) as stored by Hugging Face
Wk, Wv: ( 512, 2048) as stored by Hugging Face

Q = Wq @ x: (2048,)
K = Wk @ x: ( 512,)
V = Wv @ x: ( 512,)
```

These are GEMVs, not one-core operations. The implementation shards weight
**output rows** and replicates only the two-tile activation. There is no
weight broadcast and no physical weight transpose.

```text
Q rows:
  cores 0..41:    18 rows/core
  cores 42..117:  17 rows/core
  physical weight shard stride: 18 rows x 2 tiles = 36 tiles/core
  physical weight storage:      (118, 36, 32, 32)

K or V rows:
  cores 0..39:     5 rows/core
  cores 40..117:   4 rows/core
  physical weight shard stride:  5 rows x 2 tiles = 10 tiles/core
  physical weight storage:      (118, 10, 32, 32)
```

For each owned output row `r`, a core computes exactly these two partial dot
products and adds them:

```text
partial0 = sum(W[r,    0:1024] * x[   0:1024])
partial1 = sum(W[r, 1024:2048] * x[1024:2048])
y[r] = BF16(partial0 + partial1)
```

The input can be the fixed RMSNorm allocation `(1024, 2048)` with only token
0 valid. Token 0 is physical tiles 0 and 1, so every projection core takes a
zero-copy globally addressed view of those two tiles. Each core reads only
its local weight shard.

One packed scalar normally consumes a full tile. The NCRISC compacts the
local scalars into logical row 0 of a single output tile per core:

```text
Q compact output:   BF16[118, 18], physical (118, 1, 32, 32)
K/V compact output: BF16[118,  5], physical (118, 1, 32, 32)
```

The smaller Q shards leave slot 17 unused; the smaller K/V shards leave slot
4 unused. Concatenating only each core's valid slots reconstructs the model's
ordinary 2048- or 512-element logical vector. This compact sharded layout is
also the input layout expected by the future sharded RoPE/cache kernels.

The implementation uses both BF16 ELWMUL fidelity phases and FP32 Dst, then
performs FP32 SFPU accumulation. There is no LoFi projection path. Real
layer-0 weights validate against a NumPy FP32-sum forward reference:

```text
Q: 30.417 us median, relative L2 0.00647, PCC 0.999995109
K: 14.612 us median, relative L2 0.00679, PCC 0.999993437
V: 14.647 us median, relative L2 0.00709, PCC 0.999993998
```

The former one-phase ELWMUL path measured roughly 2.8--2.9% relative L2 and
is intentionally removed. RMSNorm remains on its exact SFPU implementation.

#### RoPE

The host computes the Llama 3 cosine and sine tables once in FP32 and uploads
them with BF16 round-to-nearest-even as compact global buffers. Each has
logical shape `(8192, 64)` and
occupies 1 MiB. One physical tile holds 16 positions; position `p` selects tile
`p // 16` and logical rows `2*(p % 16)` and `2*(p % 16)+1`. The device RoPE
kernels only read these resident values and apply the split-half rotation.

##### Prefill

Apply RoPE to all `valid_s` Q/K positions. Position IDs cover the full prompt,
and padded capacity rows are skipped.

```text
Q: (32, valid_s, 64)
K: ( 8, valid_s, 64)
```

##### Decode

Status: implemented as one fused 40-core launch. Workers 0--31 each own one Q
head and workers 32--39 each own one K/V head. V bypasses the RoPE arithmetic
but shares K's compact-to-head-major gather.

```text
input Q: compact BF16[118, 18]  -> output Q: BF16[32, 64]
input K: compact BF16[118,  5]  -> output K: BF16[ 8, 64]
input V: compact BF16[118,  5]  -> output V: BF16[ 8, 64]
```

For every head, the BRISC maps each feature back to the projection core and
slot that produced it. For a global compact tile `t`, the DRAM location is:

```text
bank       = t % 7
bank_row   = t // 7
byte_addr  = projection_base + bank_row * 2048
slot 0..15 byte offset = 2 * slot
slot 16/17 byte offset = 512 + 2 * (slot - 16)
```

Each Q worker reads the few complete aligned projection tiles intersecting its
64-element head. Each K/V worker reads the matching compact K and V tiles and
gathers both heads locally in L1. It applies RoPE only to K and writes V
unchanged in ordinary head-major form. Every worker also reads one cosine and
one sine tile for `start_pos`; each table tile supplies 16 runtime positions.

TRISC0/FPU moves four ordinary BF16 tiles into Dst: `x`,
`rotate_half(x)`, `cos`, and `sin`. SFPU expands the BF16 operands into full
FP32 lane registers and evaluates:

```text
result = x * cos + rotate_half(x) * sin
```

Only the final Q/K result is rounded to BF16, stored, and packed; V remains
bit-exact to the compact projection output. Simulator and real Blackhole
validation at positions 0, 1, 127, and 8191 agree with each other exactly.
Relative to an FP32 CPU expression with BF16 RNE output, the worst measured
Q/K relative L2 is `2.003e-4` and the worst absolute difference is
`0.00390625`; the few differences are BF16 midpoint tie handling. Hardware
latency is 12.114 us minimum / 12.172 us median across 20 measured launches,
up from roughly 10.3 us before adding V reassembly.

#### KV-cache write

##### Prefill

Write all valid prompt keys and values into cache positions `[0:valid_s]`:

```text
K cache update: (8, valid_s, 64)
V cache update: (8, valid_s, 64)
```

##### Decode

Status: implemented for the one-token decode path. Append one K/V vector per
KV head at `start_pos`:

```text
K/V input:       BF16[8, 64]
K/V cache:       BF16[8, 8192, 64] each
cache update:    cache[:, start_pos, :]
```

The logical caches remain head-major `[8,8192,64]`, but their physical layout
is ordinary 2-D tiles:

```text
physical view = [8 heads, 256 time blocks, 2 feature halves, 32, 32]
tile(h, p, f) = h * 512 + (p // 32) * 2 + f
row(h, p, f)  = p % 32
f = 0 for features 0:32, f = 1 for features 32:64
```

Eight BRISC-only workers divide the update by KV head. Worker `h` reads one K
and one V source tile, then writes the two 32-element feature halves to one
row of two standard cache tiles. Each row is two aligned 32-byte physical face
segments. The workers own disjoint cache regions, so there is no
synchronization or write collision. The kernel never reads the cache and does
not overwrite another token, including when `start_pos` crosses positions
15/16, 31/32, or reaches 8191.

Simulator and hardware validation initialize both complete caches with a
sentinel, update positions 0, 1, 15, 16, 31, 32, 127, and 8191, then verify the
written rows and every untouched cache element. Blackhole latency is
3.635 us minimum / 3.674 us median in the boundary-validation run.

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

The allocation reserves the fixed prefill capacity in both score dimensions.

##### Decode

```text
Q:       (32, 1, 64)
K cache: ( 8, kv_len, 64), shared 4:1
scores:  (32, 1, kv_len)
```

Status: implemented as one eight-worker launch, including the `0.125` scale.
Worker `hk` owns KV head `hk` and query heads `4*hk : 4*hk+4`. For each
32-token history block it computes:

```text
Q0[4,32] @ K0[32,32].T + Q1[4,32] @ K1[32,32].T
```

The two matrix products use HiFi2 BF16 operand multiplication and accumulate
into the same FP32 Dst tile. SFPU then applies the exact `1/8` scale in FP32.
A full K transpose requires two pieces: the unpacker transposes each 16x16
face, and transpose-aware FPU address modifiers swap the off-diagonal faces.

Scores use physical storage `[8,256,32,32]`; rows 0--3 of each tile are the
four Q heads sharing that KV head. The runtime launches
`ceil(kv_len/32)` blocks. Columns after `kv_len` in the final tile are not
valid and must be excluded by softmax.

Hardware validation results:

| `kv_len` | blocks | median latency | relative L2 | PCC |
|---:|---:|---:|---:|---:|
| 1 | 1 | 20.959 us | 0.004292 | 0.999994225 |
| 33 | 2 | 32.101 us | 0.003935 | 0.999995757 |
| 127 | 4 | 54.869 us | 0.003959 | 0.999995628 |
| 8192 | 256 | 2919.036 us | 0.003952 | 0.999995693 |

#### Attention mask

##### Prefill

Apply the causal mask and mask padded key positions `>= valid_s`. Padded query
rows are not executed.

##### Decode

There are no future cached positions, so only invalid/padded KV-capacity entries
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

This is a fixed-capacity matrix-matrix operation using all cores.

##### Decode

```text
(1, 2048) @ (2048, 2048) -> (1, 2048)
```

This is an all-core GEMV with output columns sharded across cores.

### Attention residual add

#### Prefill

Elementwise add two `BF16[valid_s, 2048]` tensors in the fixed allocation
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

Both outputs are fixed-capacity `BF16[valid_s, 8192]` tensors.

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

Elementwise add two `BF16[valid_s, 2048]` tensors in the fixed allocation.

#### Decode

Elementwise add two `BF16[1, 2048]` tensors on one core until fused.

## Final RMSNorm

Prefill and decode use the same implemented RMSNorm code generator. Prefill
uses the fixed capacity and runtime `valid_s`; decode selects the loop-free one-core
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
