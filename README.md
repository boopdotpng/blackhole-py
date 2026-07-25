# blackhole-py

Try llama3.2 1b instruct (you will need the unsloth safetensors file):
```sh
PYTHONPATH=. python3 examples/llama3.py --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

## requirements
- tt-kmd > 2.9.0
- p100a only (p150 support coming soon)
