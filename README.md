# blackhole-py

Single-card Llama inference on Tenstorrent Blackhole.
Requires `tt-kmd` > 2.9.0 and local checkpoints in the directories shown below.

Run from this directory:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

# Llama 3.2 1B BF16 — weights/llama3-1b/
.venv/bin/python -m examples.llama3 --model 1b --device 0 --steps 32

# Llama 3 8B Instruct BF16 — weights/llama3-8b-bf16/
.venv/bin/python -m examples.llama3 --model 8b --device 0 --steps 32

# Llama 3 8B Instruct FP8 — weights/llama3-8b-fp8/
.venv/bin/python -m examples.llama3 --model 8b --dtype fp8 --device 0 --steps 32

# Llama 3 8B BF16 with chunked prefill
.venv/bin/python -m examples.llama3 --model 8b --prefill --device 0 --steps 32
```

The default is 1B BF16. Add `--prompt "Your prompt"` to change the input or
`--profile` for timing. For chunked prompt ingestion on 8B BF16, add `--prefill`
and optionally `--prefill-chunk-size 1..8` (default: 4). FP8 mode loads the
published FP8 weights and their stored scales, with subnormal weights flushed
to signed zero by default. Activations are scaled and packed inside the existing
compute kernels.

Run `.venv/bin/python -m examples.llama3 --help` for all options.
Checkpoints are not included in Git. Use `--safetensor` and `--tokenizer` to
specify different checkpoint and tokenizer paths.
