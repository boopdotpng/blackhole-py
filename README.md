# blackhole-py

Run LLMs on a Tenstorrent Blackhole card from plain Python. Kernels are written in TTRV, a small language with one
function per RISC-V core of a Tensix tile. The compiler, firmware and dispatcher all live in this repo. Needs
`tt-kmd` >= 2.12.0, `numpy`, `tiktoken`, `tokenizers`, `clang` and `llvm-objcopy`.

```python
import numpy as np
from ttrv import Device

d = Device(0)
embed = d.kernel("examples/llama3/embedding.ttrv")                     # compile the TTRV kernel, install it
weights = d.array(np.random.randn(16, 2048).astype(np.float32), "bf16")  # DRAM buffers, filled from the host
history = d.array(np.arange(16, dtype=np.uint32))
out = d.empty(2048, "bf16")
embed(history=history, weights=weights, output=out, token_pos=3)       # queued; returns at once
print(out.numpy())                                                     # waits, copies back: row 3 as BF16 bits
```

## Writing model kernels

- `include ../common/attention` loads declarations from a path relative to the including file. Each kernel expands a
  shared module once. The module uses the kernel's constants, types and resource declarations.
- `const ROW_OFFSETS = [0, 2, dst.face, dst.face + 2]` names an ordered list of compile-time values.
  `repeat offset in ROW_OFFSETS` unrolls the body in that order. `ROW_OFFSETS[i]` accepts a compile-time index.
- `tileptr(weights, tile)` addresses a DRAM tile by its ordinal for both scalar and packed formats.
  For example, `noc.read page, tileptr(weights, tile), n=1024, wait` reads one tile. The length counts elements.
- `reads = noc.group read` allocates a transaction ID without issuing a request. Use `tid=reads` on the reads that
  can overlap, then `noc.wait reads` before consuming the data or reusing its storage. A group may be empty.

## Benchmarks

| Model | Weights | Prefill 1× (tok/s) | Decode 1× (tok/s) | Decode 2× (tok/s) | Speedup |
| --- | --- | ---: | ---: | ---: | ---: |
| Llama 3.2 1B | BF16 | 8,555 | 160.6 | 262.0 | 1.63× |
| Llama 3 8B | BF16 | 2,351 | 30.3 | 52.7 | 1.74× |
| Llama 3 8B | BFP8_B | 2,981 | 48.3 | 75.7 | 1.57× |
| Qwen3.8-27B | BFP8_B + BFP4_B | 186 | 17.5 | 29.1 | 1.66× |
| Nanbeige4.3-33B | BFP8_B + BFP4_B | 1,294 | 19.3 | 31.8 | 1.65× |

Batch-one greedy on p150a cards; 2× is tensor parallel over TT-link. Median of three warm runs: a 320-token prefix,
then the 32 tokens after the first output, excluding loading and compilation.

## Weights

| Model | Checkpoint | Format |
| --- | --- | --- |
| Llama 3.2 1B | `weights/llama3-1b/` (2.4 GB) | Hugging Face BF16 |
| Llama 3 8B | `weights/llama3-8b-bf16/` (15 GB) | Hugging Face BF16 |
| Llama 3 8B | `weights/llama3-8b-bfp8/model.safetensors` (8.5 GB) | packed: all projections and LM head BFP8_B |
| Qwen3.8-27B | `../weights/qwen3.8-27b/mixed_bfp4mlp_bfp8down_bfp8attn/model.safetensors` (25 GB) | packed: attention, linear attention, MLP down BFP8_B; gate, up BFP4_B; LM head BF16 |
| Nanbeige4.3-33B | `../weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors` (23 GB) | packed: attention, LM head BFP8_B; all MLP BFP4_B |

Packed tensors are `U8` block-float tiles, named in the header metadata `blackhole.layout: kn_tiles_32x32_v1` and
`blackhole.formats` (tensor to `bfp8_b` or `bfp4_b`); embeddings and norms stay BF16. `config.json` and `tokenizer.json`
go beside the checkpoint (Qwen: `--metadata`, default `~/models/qwen3.8-27b/bf16`). One card holds 32 GB.

## Run

```sh
python examples/llama3.py --model 1b --tokens 64     # or 8b-bf16, 8b-bfp8
python examples/qwen38.py --tokens 12                 # --tp 2 for two cards
python examples/nanbeige.py --tokens 64 --timing
python eth/llama3_tp.py --model 8b-bf16               # two cards: ethernet channel 11 cabled straight across
python sims/probes/model_rates.py 8b-bfp8             # one benchmark row; eth/tp_rates.py for 2×
PROFILE=1 python examples/llama3.py                   # per-kernel hardware counters at exit
```
