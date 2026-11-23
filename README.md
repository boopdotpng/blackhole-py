# Single-card Blackhole runtime

The Python host installs TTRV kernel images, argument blocks and a table of kernel calls in each worker's L1. A graph replay binds its integer arguments and starts the workers with a multicast TLB write. Each of the five RISCs walks its own cursor, calls its entry point when it has work, and returns to firmware. Each generated token uses one replay from embedding through argmax. Prefill and decode have separate L1 images. At a phase boundary the host waits for workers, multicasts the new kernels and table, and starts the next graph. A phase switch resets temporary worker L1. KV caches, convolution history and recurrent state survive in DRAM.

A table row describes the worker range and entry point for each role. Dependent rows join on the card. Disjoint worker ranges can share a join using `_async=True`. NCRISC waits for local role completion before resetting the group's circular-buffer counters. Worker zero collects arrivals from the participating tiles and multicasts the release. Decode projection BRISCs can start streaming weights into a dedicated CB31 while the previous group finishes. NCRISC drains output as the projection computes.

On a 140-tile card, 139 tiles run the model. The remaining tile handles pinned sysmem/DRAM DMA and has no compute dispatch role. Model weights and KV caches live in DRAM. Nanbeige and Qwen keep their decode residuals and packed RMSNorm/SwiGLU outputs in L1 shards. Inkling passes the embedding to its first block mix in L1. Other intermediates use the storage declared by the ported kernels.

## Prompt execution

Inkling processes up to eight prompt tokens per chunk in layer and recurrent-pass order. Dense Q/K/V and output projections share weights across rows. The block mixes, message gates, router and selected experts run across token lanes. Each token keeps its own routes and activation buffers. Attention and the convolution histories advance in causal order within each chunk.

Qwen processes up to 64 prompt tokens per chunk. Two-panel chunks multicast projection operands over the worker grid and unpack tiled outputs for the row-major recurrent and attention kernels. Full panels fuse the MLP gate/up projection with SwiGLU and feed its tiled output directly to the down projection. The GDN kernel keeps each worker's recurrent matrix shard in L1 across the chunk and writes the last update to DRAM. Attention publishes the chunk's KV rows per head before the workers evaluate their causally masked queries in parallel.

Nanbeige processes up to 320 positions per prompt chunk.

## Serving

`examples/serve.py` is an OpenAI-compatible server (`/v1/chat/completions`, `/v1/completions`, `/v1/models`, `/health`) over the continuous-batching engine in `examples/engine.py`. Each live request owns a slot of per-sequence state in DRAM. One decode graph advances every live slot per step, one 32-row panel row per sequence, for up to 64 sequences. New prompts prefill in their own L1 phases between decode steps. Each prompt chunk shape (64 or 320 rows) has its own phase, and a phase switch costs about 5 ms. `--slots 0` (the default) allocates as many slots of `--context` positions as DRAM holds after the weights.

A slot's state is saved to a prefix store (`examples/kvstore.py`) when another request is about to overwrite it, and every slot is saved at shutdown. The store keeps 8 GB in host RAM and spills to SSD (`--offload-ssd`, 64 GB by default, under `~/.cache/blackhole-py/prefixes`). SSD entries persist across restarts, keyed by the checkpoint and the state layout. A prompt restores the longest matching prefix, so a new session that shares a long system prompt skips its prefill. Restores move about 10 GB/s from SSD and tens of GB/s over PCIe on card 0.

```sh
python3 examples/serve.py --model nanbeige --context 8192 --port 8000
python3 examples/batch_check.py --model nanbeige     # greedy batch outputs against single-sequence decode
python3 examples/offload_check.py --model nanbeige   # RAM, SSD and restart restores against cold prefill
```

Nanbeige decodes at 57 ms per step for 1 to 16 live sequences. Its prompts prefill at about 2,700 tok/s for 320 tokens and 2,100 tok/s for 2,000 tokens.

## Running on hardware

Run from this directory with Python, NumPy, tokenizers, Clang, LLD and LLVM objcopy available. The model scripts use the checkpoints under `../weights`. Qwen also reads the source model configuration and tokenizer from `~/models/qwen3.8-27b/bf16`, configurable with `--metadata`.

```sh
python3 examples/nanbeige.py --device 0 --tokens 16 --timing
python3 examples/qwen38.py --device 0 --tokens 16 --profile
python3 examples/inkling.py --device 0 --tokens 16
python3 -m pytest -q
```

Each invocation owns one card. The hardware tests use card 0 and include a pinned-memory DMA round trip, cross-worker reduction, DRAM bandwidth and resident replay. To run the table test alone on another card, use `PYTHONPATH=. python3 test/test_table.py 1`.
