# blackhole-py

Run Llama 3.2 1B Instruct end-to-end decode:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --safetensor weights/model.safetensors \
  --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

`examples/rand.py` is retained as a standalone hardware RNG kernel utility.

## Requirements

- `tt-kmd` > 2.9.0
- P100a (P150 support is not implemented)
