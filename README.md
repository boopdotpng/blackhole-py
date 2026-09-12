# blackhole-py

Single-card Llama inference on Tenstorrent Blackhole.
Requires `tt-kmd` > 2.9.0 and local checkpoints in the directories shown below.

Run from this directory:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

# Llama 3.2 1B BF16 — weights/llama3-1b/
.venv/bin/python -m examples.llama3_1b --device 0 --steps 32

# Llama 3 8B Instruct BF16 — weights/llama3-8b-bf16/
.venv/bin/python -m examples.llama3_8b --device 0 --steps 32

# Llama 3 8B Instruct FP8 — weights/llama3-8b-fp8/
.venv/bin/python -m examples.llama3_8b_fp8 --device 0 --steps 32
```

Add `--prompt "Your prompt"` to change the input or `--profile` for timing.
Checkpoints are not included in Git. Use `--safetensor` and `--tokenizer` to
specify different checkpoint and tokenizer paths.
