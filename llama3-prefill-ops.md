# Llama 3 prefill kernels

Assumptions: batch size 1, `S <= 2048` tokens, hidden dimension 2048, BF16.

## Embedding

This kernel worked on hardware in
`0b33083:examples/llama3_prefill.py`.

### Shapes

```text
token IDs       U32[S]                 row-major
weight          BF16[128256, 2048]     row-major

output logical  BF16[S, 2048]
output tiled    BF16[ceil(S/32), 64, 32, 32]
```

At the maximum sequence length, the output tile grid is
`BF16[64, 64, 32, 32]`. Tile `[token_block, feature_block]` contains 32
tokens by 32 features in normal face-tiled order.

### Sharding

At `S=2048`, the kernel uses 64 cores. Each core owns one 32-token block and
produces its 64 feature tiles:

```text
core 0   -> tokens    0..31   -> output tile row 0
core 1   -> tokens   32..63   -> output tile row 1
...
core 63  -> tokens 2016..2047 -> output tile row 63
```

For shorter prompts, the same assignment needs `ceil(S / 32)` active cores.
Unused rows in the final tile must be zero.

### Work per core

Each core:

1. Reads its 32 token IDs.
2. Gathers 32 complete embedding rows from DRAM.
3. Stages a row-major `BF16[32, 2048]` block in L1: 128 KiB.
4. Splits it into two `BF16[32, 1024]` blocks.
5. Tilizes four adjacent 32x32 output tiles per chunk.
6. Produces 16 chunks, or 64 output tiles total.
7. Writes its 128 KiB face-tiled output shard to DRAM.

### Per-core data path

```text
 token IDs in DRAM
        |
        | BRISC NoC read
        v
 token IDs in L1
        |
        | indexed row addresses
        v
 embedding weight in DRAM   BF16[128256, 2048], row-major
        |
        | BRISC NoC gather: 32 rows
        v
 row-major input CB in L1   BF16[32, 2048], 128 KiB
        |
        | TRISC0 / UNPACK
        | 32 rows x 128 features per chunk
        v
 SrcA
        |
        | TRISC1 / FPU MOVA2D
        v
 16-bit Dst                 four tiles per chunk
        |
        | TRISC2 / PACK
        v
 face-tiled output CB       64 tiles total
        |
        | NCRISC NoC write
        v
 output shard in DRAM       BF16[1, 64, 32, 32]
```

No numerical math or SFPU work happens in embedding. The FPU is used only to
move the tilized data from SrcA to Dst for PACK.

### Exact tilize configuration

The unusual Blackhole UNPACK/FPU/PACK flags were added in commit `d9f73de`:

```text
ttk/unpack.py   Unpack.fast_tilize_blocks
ttk/fpu.py      Fpu.fast_tilize
ttk/pack.py     Pack.fast_tilize
```

Read them directly with:

```bash
git show d9f73de:ttk/unpack.py
git show d9f73de:ttk/fpu.py
git show d9f73de:ttk/pack.py
```

The embedding call site that connects those three stages is in commit
`0b33083`, file `examples/llama3_prefill.py`, function `prefill_embedding`.

## Next

Prefill RMSNorm was unfinished in the historical implementation, so its
kernel will be a hypothetical design rather than a recovered working kernel.
