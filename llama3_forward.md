# Llama 3.2 1B forward pass on Blackhole

This is the initial, deliberately unfused kernel plan for running the supplied
Llama 3.2 1B model in this runtime. Each numbered item is one device `Program`
launch at first. A `Program` may use BRISC/NCRISC for NOC traffic and
TRISC0/TRISC1/TRISC2 for unpack, math, and pack, but it implements only the one
semantic operation named by that item.

The point of this version is correctness and kernel bring-up. It avoids work
that is not semantically required: reshape-only operations are layouts, GQA
does not physically repeat K or V, K is not explicitly transposed, and no full
causal-mask tensor is allocated. Once every stage works, adjacent launches can
be fused.

## Model constants

| Name | Value |
|---|---:|
| hidden dimension, `D` | 2048 |
| transformer layers, `L` | 16 |
| query heads, `Hq` | 32 |
| KV heads, `Hkv` | 8 |
| head dimension, `Dh` | 64 |
| query heads per KV head, `G` | 4 |
| MLP dimension, `F` | 8192 |
| vocabulary, `V` | 128256 |
| maximum sequence length, `N` | 8192 |
| RMSNorm epsilon | `1e-5` |
| RoPE theta | `500000.0` |

Runtime symbols:

- `S`: valid tokens in this invocation. Initially `0<S<1024` for prefill and
  `S=1` for decode.
- `S_bucket=1024`: fixed physical token capacity of the initial prefill path.
- `start_pos`: absolute position of the first input token.
- `T = start_pos + S`: valid KV-cache length after this invocation.
- Batch size is one. Batch dimensions are omitted below.

### A tile is not 1024 sequence positions

A Tensix tile contains 1024 scalar elements because it is `32x32`. That is the
minimum physical allocation/transfer unit in this runtime, not the logical
sequence length.

- Decode has `S=1`. A tiled token-ID buffer can still occupy one 1024-element
  tile, with one valid ID and 1023 ignored elements.
- A token activation has 2048 elements, so one decode activation is two densely
  packed 1024-element vector tiles.
- Prefill has `S=prompt_length<1024`. Its fixed 1024-entry ID buffer is one
  tile, but only `[0:S)` is valid. The physical bucket size and valid length
  are separate launch parameters.
- Matrix-oriented kernels pad each matrix axis as required by their layout.
  Padding is never promoted to a real token and never participates in a
  reduction.

Treating all 1024 entries as valid during one-token decode would run a full
bucket prefill, not a decode. All launches therefore receive a logical valid
length even when their buffers are tile padded.

## Numerical and tiling contract

- Store weights, activations, RoPE coefficients, and the KV cache as BF16.
- Accumulate matrix multiplies and reductions in FP32 Dst.
- Pack ordinary activation results back to BF16 between unfused launches.
- Keep attention score intermediates FP32 initially. This is expensive but is
  a simple correctness baseline. A fused softmax/attention kernel should avoid
  writing them later.
- Logical tensors are padded to 32x32 tile boundaries in storage. Padding is
  always excluded from reductions and matmuls. In particular, `Dh=64`,
  `D=2048`, and `F=8192` are already tile aligned; `S`, `T`, and `V` may need
  masking/padding.
- Weights are prepacked on the host in the orientation required by Blackhole
  MVMUL. A runtime transpose of a weight or K tensor is not a model operation.

The notation below uses mathematical shapes. A kernel iterates over all tiles
covering that shape and may shard those tiles over worker cores.

## Persistent buffers and layouts

Use these logical layouts. Their physical tile order can change as the matmul
implementation evolves, provided the producer and consumer agree.

| Buffer | Logical shape | Notes |
|---|---|---|
| token activations `x` | `[S, D]` | token-major |
| projection output `q` | `[S, Hq, Dh]` | flattening the last two axes is `[S, D]` |
| projection output `k`, `v` | `[S, Hkv, Dh]` | each flattened row is 512 values |
| key cache | `[L, Hkv, N, Dh]` | only positions `[0:T)` are valid |
| value cache | `[L, Hkv, N, Dh]` | only positions `[0:T)` are valid |
| scores/probabilities | `[Hq, S, T]` | last axis padded to 32 |
| attention result | `[S, Hq, Dh]` | flattening gives `[S, D]` directly |
| MLP intermediates | `[S, F]` | gate and up buffers |
| RoPE cosine/sine | `[N, Dh]` each | prepared once and resident in DRAM |

The projection-native layout is `[token, head, head_element]`. Do not launch a
reshape or transpose after Q/K/V projection. The KV-cache write performs the
only required layout change, from token-major projection output to a
head-major persistent cache.

The KV cache costs 16 MiB per layer in BF16, or 256 MiB for all 16 layers.
Allocate it once per model and clear only its logical length when beginning a
new sequence; stale positions at or beyond `T` are never read.

## One-time RoPE table construction (host only)

This requires **zero Tenstorrent runtime kernels**. Precompute it on the host
while loading the model, convert the results to the device's tiled BF16 layout,
and upload the two immutable tables to DRAM once. Each table is
`8192 * 64 * 2` bytes, so cosine plus sine occupy 2 MiB total.

For `j in [0, 32)`:

```text
inv_freq[j] = 1 / theta ** ((2*j) / Dh)
wavelen[j]  = 2*pi / inv_freq[j]
cycles[j]   = 8192 / wavelen[j]
smooth[j]   = clamp((cycles[j] - 1) / (4 - 1), 0, 1)
inv_freq[j] = inv_freq[j] * (1/32 + smooth[j] * (1 - 1/32))
```

For every position `p`, compute 32 angles and duplicate them across the two
halves of the head:

```text
angle[p, j]      = p * inv_freq[j]
angle[p, j + 32] = p * inv_freq[j]
cos[p, :] = cos(angle[p, :])
sin[p, :] = sin(angle[p, :])
```

This matches the Llama 3 scaling rule in the supplied model. RoPE uses the
half-rotation convention `rotate_half([a, b]) = [-b, a]`, not adjacent even/odd
pairs. The device never computes frequencies, wavelengths, smoothing, angles,
cosine, or sine. K11 and K12 only calculate the address of table row
`start_pos+s`, read its two 64-element BF16 rows, and apply the rotation.

## Separate decode and prefill paths

The two paths implement the same transformer equations and use the shared
kernel definitions in the next section, but they should be separate compiled
programs. Decode is mostly GEMV with `S=1`; prefill is GEMM with `S>1`, has a
causal mask, and needs blocked attention for useful sequence lengths.

### Decode path (`S=1`)

The input ID buffer occupies at least one tile, but only element zero is valid.
Let `T=start_pos+1` after appending this token to the cache.

Important logical shapes for one layer are:

| Value | Logical shape | Dense 1024-element payloads |
|---|---:|---:|
| input token IDs | `[1]` | 1 allocation tile, 1 valid value |
| activation/residual | `[2048]` | 2 |
| Q | `[32,64]` | 2 |
| new K or V | `[8,64]` | 1 tile, 512 valid values |
| scores/probabilities | `[32,T]` | `ceil(T/32)` tiles in a `[32,T]` tiled matrix |
| context | `[32,64]` | 2 |
| gate, up, or hidden | `[8192]` | 8 |
| logits | `[128256]` | 126 dense payloads if materialized |

The persistent K and V cache each contain logical shape `[8,8192,64]` per
layer. Only `[8,0:T,64]` is readable. Their physical layout should be chosen
for attention reads; it need not be a densely flattened tensor.

Decode dispatches:

```text
D00  embedding_gather(one valid token)

for layer = 0..15:
  D01  input RMSNorm over one 2048-element vector
  D02  Q projection GEMV             [2048] -> [32,64]
  D03  K projection GEMV             [2048] -> [8,64]
  D04  V projection GEMV             [2048] -> [8,64]
  D05  RoPE Q at absolute start_pos
  D06  RoPE K at absolute start_pos
  D07  append one K row and one V row per KV head
  D08  grouped Q @ K-cache           [32,64] x [8,T,64] -> [32,T]
  D09  scale scores by 0.125
  D10  softmax each of 32 rows over valid columns [0:T)
  D11  grouped probabilities @ V-cache           -> [32,64]
  D12  output projection GEMV        [2048] -> [2048]
  D13  attention residual add
  D14  post-attention RMSNorm over one vector
  D15  gate projection GEMV          [2048] -> [8192]
  D16  up projection GEMV            [2048] -> [8192]
  D17  SiLU(gate)
  D18  SiLU(gate) * up
  D19  down projection GEMV          [8192] -> [2048]
  D20  MLP residual add

D21  final RMSNorm over one vector
D22  tied LM-head GEMV               [2048] -> [128256]
D23  distributed argmax              [128256] -> one token ID
```

There is no causal-mask launch in decode: K/V positions `0..T-1` are all past
or current positions. The score/softmax kernel must still ignore storage
columns from `T` through the end of the final 32-column tile.

### Prefill path (`S=seq_len<1024`, `S_bucket=1024`)

The initial prefill implementation has one fixed 1024-token capacity and starts
at position zero. It accepts the actual prompt length as `valid_S`, and every
kernel processes only `[0:valid_S)`. Supporting chunked prefill, larger
prefills, or multiple buckets is deferred.

Worst-case buffer capacities for this bucket are:

| Value | Physical capacity | Maximum 1024-element tiles |
|---|---:|---:|
| input token IDs | `[S_bucket]` | 1 |
| activation/residual | `[S_bucket,2048]` | 2048 |
| Q | `[S_bucket,32,64]` | 2048 |
| new K or V | `[S_bucket,8,64]` | 512 each |
| scores/probabilities | `[32,S_bucket,S_bucket]` | 32768 each |
| context | `[S_bucket,32,64]` | 2048 |
| gate, up, or hidden | `[S_bucket,8192]` | 8192 each |
| final hidden vector used by LM head | `[2048]` | 2 |
| logits | `[128256]` | 126 dense payloads if materialized |

The logical shapes use `S`, not `S_bucket`: for example, valid scores are
`[32,S,T]`. The table shows fixed worst-case capacity if buffers are allocated
once. The maximum score tile count assumes matrix view `[32*1024,1024]`; FP32
scores consume 128 MiB per intermediate at full capacity. A dynamic allocator
may instead reserve only the tiles needed by the actual `S`.

Prefill dispatches:

```text
P00  embedding_gather(valid_S token IDs from the 1024-entry tile)

for layer = 0..15:
  P01  input RMSNorm over S rows
  P02  Q projection GEMM             [S,2048] -> [S,32,64]
  P03  K projection GEMM             [S,2048] -> [S,8,64]
  P04  V projection GEMM             [S,2048] -> [S,8,64]
  P05  RoPE Q at positions start_pos + [0:S)
  P06  RoPE K at positions start_pos + [0:S)
  P07  append S K rows and S V rows per KV head
  P08  grouped Q @ K-cache           -> [32,S,T]
  P09  scale scores by 0.125
  P10  causal-mask scores
  P11  softmax every (query head, query token) row over valid keys
  P12  grouped probabilities @ V-cache -> [S,32,64]
  P13  output projection GEMM        [S,2048] -> [S,2048]
  P14  attention residual add
  P15  post-attention RMSNorm over S rows
  P16  gate projection GEMM          [S,2048] -> [S,8192]
  P17  up projection GEMM            [S,2048] -> [S,8192]
  P18  SiLU(gate)
  P19  SiLU(gate) * up
  P20  down projection GEMM          [S,8192] -> [S,2048]
  P21  MLP residual add

P22  select x[S-1,:] by address; no kernel
P23  final RMSNorm over that one vector
P24  tied LM-head GEMV               [2048] -> [128256]
P25  distributed argmax              [128256] -> one token ID
```

Yes, masking is part of prefill. For query row `s`, P10 preserves keys through
absolute position `start_pos+s` and writes `-inf` to later keys:

```text
valid(s, key_position) = key_position <= start_pos + s
```

It also masks key padding from `T` through the final tile boundary. Query rows
`[valid_S:S_bucket)` are invalid and should not be computed or stored. With
this initial prefill `start_pos=0` and `T=S`, so this is the usual
lower-triangular causal mask. The formula is already suitable for a later
chunked-prefill implementation with `start_pos>0`.

Semantically, prefill is the decode equation evaluated for `S` query tokens.
It is not literally the high-performance decode binary with a larger loop
bound: GEMV becomes GEMM, masking appears, and attention needs a different
blocked dataflow.

## Shared unfused kernel definitions

### 0. Embedding lookup

**K00 `embedding_gather`**

```text
input:  token_ids[S]                         integer IDs
weight: embed_tokens[V, D]                   BF16
output: x[S, D]                              BF16
x[s, :] = embed_tokens[token_ids[s], :]
```

BRISC should gather the 64 logical 32-element segments belonging to each token
row. When the embedding table is tiled, read only the selected row stripe from
each tile rather than transferring the other 31 rows. This is a gather, not a
one-hot matmul. Invalid token IDs are a host error.

### 1. Transformer layer

Run the following sequence for `layer = 0 .. 15`. Let `residual` refer to the
layer input `x`; preserve it until the corresponding residual add.

#### 1A. Input RMSNorm

These seven launches form `input_layernorm(x)`.

**K01 `square`**

```text
norm_sq[S, D] = fp32(x) * fp32(x)
```

**K02 `row_sum`**

```text
norm_sum[S] = sum(norm_sq[S, :])              FP32
```

The reduction spans all 64 hidden-dimension tiles for each logical row. Padded
token rows do not produce output.

**K03 `scalar_mul`**

```text
norm_mean[S] = norm_sum[S] * (1 / 2048)
```

**K04 `scalar_add`**

```text
norm_eps[S] = norm_mean[S] + 1e-5
```

**K05 `rsqrt`**

```text
inv_rms[S] = rsqrt(norm_eps[S])               FP32
```

**K06 `row_broadcast_mul`**

```text
normalized[S, D] = fp32(x[S, D]) * inv_rms[S, None]
```

**K07 `elementwise_mul`**

```text
attn_in[S, D] = bf16(normalized) * input_norm_weight[D]
```

Pack `attn_in` as BF16. Keep the original `x` for K20.

#### 1B. Q, K, and V projections

There are no biases.

**K08 `linear_q`**

```text
q[S, Hq, Dh] = attn_in[S, D] @ Wq[D, Hq*Dh]
```

**K09 `linear_k`**

```text
k_new[S, Hkv, Dh] = attn_in[S, D] @ Wk[D, Hkv*Dh]
```

**K10 `linear_v`**

```text
v_new[S, Hkv, Dh] = attn_in[S, D] @ Wv[D, Hkv*Dh]
```

Each is a general tiled matmul with FP32 accumulation and BF16 output. Write
directly in projection-native `[S, heads, 64]` order.

#### 1C. Rotary position embedding

**K11 `rope_q`**

For every `s`, query head `h`, and `j in [0, 32)` with
`p = start_pos + s`:

```text
a = q[s, h, j]
b = q[s, h, j + 32]
q_rot[s, h, j]      = a*cos[p, j]      - b*sin[p, j]
q_rot[s, h, j + 32] = b*cos[p, j + 32] + a*sin[p, j + 32]
```

**K12 `rope_k`**

Apply the identical operation to `k_new`, over only eight KV heads, producing
`k_rot`.

Position selects are address arithmetic into the resident tables. Do not
materialize sliced or broadcast cosine/sine tensors.

#### 1D. KV-cache update

**K13 `kv_cache_write`**

```text
for s in [0, S), hk in [0, Hkv):
  key_cache[layer, hk, start_pos+s, :]   = k_rot[s, hk, :]
  value_cache[layer, hk, start_pos+s, :] = v_new[s, hk, :]
```

This is a BF16 scatter/layout kernel. It writes K and V in one launch and must
complete before K14 reads the cache. It does not clear or concatenate cache
contents. For decode it writes one 64-element row per KV head to each cache.

#### 1E. Attention scores

**K14 `gqa_qk_matmul`**

```text
for hq in [0, Hq):
  hk = hq // G
  scores[hq, :, :] = q_rot[:, hq, :] @
                     transpose(key_cache[layer, hk, 0:T, :])
```

Input shapes per query head are `[S, 64] @ [64, T]`; output is `[S, T]`.
Accumulate in FP32. `transpose(...)` describes the mathematical read pattern;
the unpacker should feed cache tiles in the required orientation. Do not
launch a K transpose and do not repeat K four times for GQA.

**K15 `attention_scale`**

```text
scores *= 1 / sqrt(64)                        # exactly 0.125
```

**K16 `causal_mask_inplace` — prefill only**

For score row belonging to query token `s`, valid keys satisfy:

```text
key_position <= start_pos + s
```

Write `-inf` to invalid score elements and to padding columns `T:round_up(T,32)`.
This kernel uses index predicates; it does not read or write a mask tensor.

For decode, `S=1` and the cache ends at the current position, so every key in
`[0, T)` is valid. Skip K16, but K17 must still exclude padded columns.

#### 1F. Row-wise softmax

Softmax is over the `T` keys independently for every `(hq, s)` row. The six
launches below are the unfused correctness path.

**K17a `row_max`**

```text
score_max[Hq, S] = max(scores[Hq, S, 0:T])    FP32
```

Initialize reductions with `-inf`. Ignore padded columns.

**K17b `row_broadcast_sub`**

```text
shifted = scores - score_max[:, :, None]
```

**K17c `exp`**

```text
exponents = exp(shifted)
```

Masked `-inf` elements become zero.

**K17d `row_sum`**

```text
exp_sum[Hq, S] = sum(exponents[:, :, 0:T])    FP32
```

**K17e `reciprocal`**

```text
inv_exp_sum[Hq, S] = 1 / exp_sum
```

**K17f `row_broadcast_mul`**

```text
probabilities = exponents * inv_exp_sum[:, :, None]
```

Pack probabilities to BF16 for the value matmul. FP32 row reductions must
accumulate across all score tiles owned by a row, not normalize each 32-column
tile independently.

#### 1G. Attention values and output projection

**K18 `gqa_av_matmul`**

```text
for hq in [0, Hq):
  hk = hq // G
  context[:, hq, :] = probabilities[hq, :, 0:T] @
                       value_cache[layer, hk, 0:T, :]
```

Input shapes per query head are `[S, T] @ [T, 64]`; output is `[S, 64]`.
Accumulate in FP32 and pack BF16. Read V directly for the mapped KV head; do
not repeat V. Store context as `[S, Hq, Dh]`, whose flattened tail is already
`[S, D]`.

**K19 `linear_o`**

```text
attn_out[S, D] = context[S, D] @ Wo[D, D]
```

**K20 `residual_add`**

```text
x_after_attn[S, D] = residual[S, D] + attn_out[S, D]
```

The result becomes both the next sublayer's input and its preserved residual.

#### 1H. Post-attention RMSNorm

Run the same seven primitive kernels as K01-K07, now with
`x_after_attn` and `post_attention_layernorm.weight`:

**K21 `square`**

```text
mlp_sq = fp32(x_after_attn) * fp32(x_after_attn)
```

**K22 `row_sum`**

```text
mlp_sum = sum(mlp_sq, hidden_axis)
```

**K23 `scalar_mul`**

```text
mlp_mean = mlp_sum * (1 / 2048)
```

**K24 `scalar_add`**

```text
mlp_eps = mlp_mean + 1e-5
```

**K25 `rsqrt`**

```text
mlp_inv_rms = rsqrt(mlp_eps)
```

**K26 `row_broadcast_mul`**

```text
mlp_normalized = fp32(x_after_attn) * mlp_inv_rms[:, None]
```

**K27 `elementwise_mul`**

```text
mlp_in = bf16(mlp_normalized) * post_attn_norm_weight[D]
```

#### 1I. SwiGLU MLP

**K28 `linear_gate`**

```text
gate[S, F] = mlp_in[S, D] @ W_gate[D, F]
```

**K29 `linear_up`**

```text
up[S, F] = mlp_in[S, D] @ W_up[D, F]
```

**K30 `silu`**

```text
activated_gate = silu(gate) = gate / (1 + exp(-gate))
```

This is one SFPU semantic kernel even if its implementation uses multiple
instructions per element.

**K31 `elementwise_mul`**

```text
hidden[S, F] = activated_gate[S, F] * up[S, F]
```

**K32 `linear_down`**

```text
mlp_out[S, D] = hidden[S, F] @ W_down[F, D]
```

**K33 `residual_add`**

```text
x[S, D] = x_after_attn[S, D] + mlp_out[S, D]
```

This `x` is the input to the next transformer layer.

### 2. Final norm, tied output projection, and greedy token

Only the last token is consumed by the caller. After layer 15, take a view of
`x[S-1, :]`; do not normalize all prefill rows and do not launch a slice
kernel.

Run the RMSNorm primitive sequence over that one row with `model.norm.weight`:

**K34 `square`**: `final_sq[D] = fp32(x_last) ** 2`

**K35 `row_sum`**: `final_sum = sum(final_sq)`

**K36 `scalar_mul`**: `final_mean = final_sum * (1 / 2048)`

**K37 `scalar_add`**: `final_eps = final_mean + 1e-5`

**K38 `rsqrt`**: `final_inv_rms = rsqrt(final_eps)`

**K39 `row_broadcast_mul`**: `final_normalized = fp32(x_last) * final_inv_rms`

**K40 `elementwise_mul`**:

```text
final_x[D] = bf16(final_normalized) * final_norm_weight[D]
```

**K41 `tied_lm_head_matmul`**

```text
logits[V] = final_x[D] @ transpose(embed_tokens[V, D])
```

The embedding table is the LM-head weight; there is no separate `lm_head`
copy and no bias. Shard vocabulary columns/rows across cores. The padded
vocabulary range `[V:round_up(V,32))` must never win argmax.

**K42 `argmax_partial`**

Each worker scans its vocabulary shard and writes one `(max_value, token_id)`
pair. Compare FP32 values. On equal values, retain the lower token ID so the
result is deterministic.

**K43 `argmax_final`**

Reduce the per-core pairs with the same comparison and write one integer token
ID to a small host-visible result buffer.

The host reads only that token ID, decodes it, checks EOS, and uses it as the
next decode input. Logits need not cross PCIe.

## Host call semantics

### Prefill

```text
token_ids = tokenizer(prompt)
assert 0 < len(token_ids) < 1024
token_id_buffer[0:1024] = padding
token_id_buffer[0:len(token_ids)] = token_ids
valid_S   = len(token_ids)
start_pos = 0
T         = valid_S
next_id   = prefill_forward(token_id_buffer, valid_S, start_pos=0)
```

All valid query rows need causal masking. Every layer populates cache positions
`[0:valid_S)` before attention. Unused ID-buffer entries and padded query/key
positions are never interpreted as tokens.

### One-token decode

```text
token_ids = [previously_generated_id]
S         = 1
start_pos = prompt_length + generated_index
T         = start_pos + 1
next_id   = decode_forward(token_ids, start_pos)
```

Each layer appends the current token's K/V before attending, so the current
position is included in `[0:T)`. Skip the causal-mask launch. All other model
operations are the same. The cache must be reset logically before a new,
unrelated prompt.

## Unique kernels the runtime needs

The numbered schedule expands to many launches, but it requires this reusable
kernel inventory:

| Kernel family | Required cases |
|---|---|
| gather | embedding-row gather from tiled DRAM |
| dense matmul | `[S,K] @ [K,N]`, FP32 accumulate, BF16 pack; all projection sizes above |
| batched attention matmul | GQA QK and AV with direct `hq -> hk` mapping and dynamic `S,T` |
| elementwise binary | add, multiply, subtract; equal-shape and row-broadcast forms |
| elementwise scalar | add and multiply |
| elementwise unary | square, exp, reciprocal, rsqrt, SiLU |
| row reduction | sum and max across an arbitrary number of tiles, with a valid-column bound |
| RoPE | BF16 half-rotation using absolute-position cosine/sine rows |
| cache update | token-major K/V to persistent head-major cache scatter |
| causal fill | predicate-based `-inf` fill, including tile padding |
| indexed reduction | sharded `(value,index)` argmax and final pair reduction |

Reshape, flatten, head split/merge, K transpose, GQA repeat, RoPE-table slice,
last-token selection, and KV concatenation are intentionally absent. They are
views, addressing rules, or avoidable materializations rather than kernels.

## Bring-up order in this repository

The existing runtime already demonstrates one-tile BF16 matmul, elementwise
FPU/SFPU work, and one-tile row reductions. A practical dependency order is:

1. Generalize matmul from one tile to arbitrary M/K/N tile loops with FP32 Dst,
   then shard output tiles over cores.
2. Generalize row sum/max across multiple width tiles and add a valid-column
   bound. This unlocks RMSNorm and decode softmax.
3. Add row broadcasts plus the square, exp, reciprocal, rsqrt, and SiLU SFPU
   mappings.
4. Add embedding gather and the K/V cache scatter.
5. Add RoPE over `[token, head, 64]` vectors.
6. Add GQA QK matmul, causal fill, and GQA AV matmul with dynamic `T`.
7. Add sharded argmax with token indices.
8. Validate one layer, then all 16 layers, first at `S=1`, then short prefill.

## Fusion targets after the unfused path is correct

The first decode implementation above is roughly 600 device launches per
token, so launch fusion is mandatory for high token throughput. The natural
fusion boundaries are:

1. RMSNorm: square + row sum + scale + epsilon + rsqrt + both multiplies.
2. QKV: one activation read feeding all three projection matmuls.
3. Projection + RoPE + cache write for K, and projection + cache write for V.
4. QK scale + decode masking/padding + online softmax.
5. Softmax + AV as a FlashAttention-style streaming kernel, never writing the
   score or probability tensors to DRAM.
6. Output projection + attention residual add.
7. Post-attention RMSNorm feeding both gate and up projections.
8. Gate projection + SiLU + up multiply, followed by down projection.
9. Down projection + MLP residual add.
10. Final RMSNorm + sharded tied LM head + distributed argmax, without
    materializing the complete logits vector.

For decode, weight traffic dominates. Fusion should prioritize keeping the
one-token activation resident while streaming multiple weights and avoiding
round trips of RMSNorm, score, probability, and MLP intermediate buffers.
