# blackhole-py

Llama 3 8B chat on a single Tenstorrent Blackhole card.

Use the shared `~/tenstorrent/.venv` and run from this directory:

```sh
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m tools.chat --device 0
```

Open **http://127.0.0.1:8000** and select **8B FP8** or **8B BF16**.
The server listens on all interfaces by default; from another machine, open
`http://<server-ip>:8000`. Use `--host` to choose a different bind address.
The model loads on the first message; switching models starts a new conversation.
No prefill: new prompt and response tokens run through decode. Matching
conversation history reuses the resident KV cache. Responses stream until EOS or the 8192-token context fills. This limit
includes conversation history, chat formatting, and the generated response.

Requires `tt-kmd` > 2.9.0, Clang, and RISC-V binutils
(`riscv64-linux-gnu-ld` and `riscv64-linux-gnu-objcopy`). C firmware in
`firmware/` compiles on every device boot. Place local checkpoints and tokenizers
in `weights/llama3-8b-fp8/` and `weights/llama3-8b-bf16/`.
Checkpoints are not included in Git. Use `--port` to change the HTTP port.

Optional FP8 decode modes are available with `--lm-head-dtype fp8` and
`--split-attention` in `examples.llama3`. They can change numerical results;
the default keeps the BF16 LM head and original attention arithmetic. See
[FP8 decode optimization results](tools/llama_fp8_speedup.md) for measurements,
validation, environment switches for chat/API use, and reproduction commands.
