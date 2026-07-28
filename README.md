# blackhole-py

> [!WARNING]
> **The current repository state is broken.** The dense row-major storage
> rewrite is incomplete, so the Llama example and hardware paths are not
> expected to run end to end.

Run Llama 3.2 1B Instruct end-to-end decode:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --safetensor weights/model.safetensors \
  --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

## Requirements

- `tt-kmd` > 2.9.0
- P100a (P150 support is not implemented)
