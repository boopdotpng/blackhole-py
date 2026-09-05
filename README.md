# blackhole-py

Run Llama 3.2 1B Instruct end-to-end decode:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --safetensor weights/model.safetensors \
  --tokenizer weights \
  --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

## Requirements

- `tt-kmd` > 2.9.0
- P100A with 120 Tensix cores, or P150A/P150B/P150C with either the stock
  120-core firmware topology or a restored 140-core topology

P150 uses all eight DRAM banks; P100A uses its seven enabled banks. Set
`Device.DEFAULT_INDEX` to `0` or `1` in `device.py` to select the default card;
an individual caller can override it with `Device(index)`.
