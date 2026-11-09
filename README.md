# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python.

## Requirements

- `tt-kmd` > 2.9.0
- Python with `numpy`, `tokenizers`, `jinja2`
- `clang` and `llvm-objcopy` (the firmware builds at startup)
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Run

```sh
python llama3.py --model 8b-fp8 --chat --port 8000   # web chat on http://<host>:8000
python llama3.py --model 1b --prompt "Hello"         # one prompt in the terminal
```

Models: `1b` (161 tok/s), `8b-fp8` (52 tok/s), `8b-bf16` (30 tok/s) on a p150a.
