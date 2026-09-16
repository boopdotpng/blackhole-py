# Llama 3 8B FP8 upload measurements

Measured on device 0 (P150a, PCIe Gen 5 x16), September 15, 2026.
Device 1 was not used. Local checkpoint files were warm in the OS page cache;
these numbers do not describe cold-storage throughput.

The timed interval is the complete `_upload_weights()` call, including file
reads, weight preparation, host staging and final device completion. The
10,159,136,768-byte numerator includes embeddings, weights, RoPE tables and KV
cache initialization. Device boot, DRAM allocation and kernel compilation are
outside this interval. Bandwidth uses decimal GB/s. Each row is the median of
three complete uploads.

| Implementation | Wall time | Full upload GB/s |
|---|---:|---:|
| Original sequential preparation/staging/submission | 15.636 s | 0.650 |
| Two asynchronous host slots, original preparation | 15.464 s | 0.657 |
| Reuse checkpoint reader; remove redundant FP8 cleanup | 3.278 s | 3.099 |
| Read files directly into pinned slots; 4 MiB slots | 0.799 s | 12.714 |

Original individual times: 15.734181, 15.600985, 15.636420 seconds.
Final individual times: 0.799049, 0.816322, 0.798123 seconds.
The final implementation is 19.6 times faster end to end.

The original preparation path rebuilt the safetensors reader for every tensor,
including parsing the index and resolving shard paths. It also copied FP8
weights into NumPy, cleared subnormals, and copied them back to Python bytes.
Device-0 tests across all 256 encodings and both unpack source banks establish
that the hardware output is byte-identical with and without that cleanup.

The final loader retains checkpoint metadata and reads bounded file ranges
straight into two pinned slots. Each slot is reused only after its completion
event. Device transfers overlap host reading; no full-tensor Python bytes object
is created for checkpoint weights. Chunk boundaries preserve DRAM bank striping.
In the median final run, filling slots took 0.759 s, waiting 0.011 s, submitting
0.016 s, and other preparation about 0.007 s. Filling includes file reads and
copying generated initialization data. These are host timings, not a separate
measurement of PCIe bandwidth.

Reproduce the full upload benchmark:

```sh
../.venv/bin/python -m tools.bench_llama_upload --device 0 --dtype fp8 --repeats 3
```

Hardware validation:

```sh
../.venv/bin/python -m pytest tests/movement/test_dma_upload.py \
  tests/movement/test_upload_stream.py tests/movement/unpacker/test_unpack_fp8.py \
  --bh-hardware --bh-device=0 -q
```

Result: 40 passed, 4 existing expected failures (standard FP8 subnormal
preservation). Full 8B FP8 and BF16 decode smoke tests both generated Paris.
