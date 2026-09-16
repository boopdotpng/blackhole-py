# blackhole-py

Llama 3 8B chat on a single Tenstorrent Blackhole card.

Use the shared `~/tenstorrent/.venv` and run from this directory:

```sh
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m tools.chat --device 0
```

Open **http://127.0.0.1:8000** and select **8B FP8** or **8B BF16**.
The model loads on the first message; switching models starts a new conversation.
No prefill: all prompt, conversation history, and response tokens run through
decode. Responses stream as they are generated, up to 512 tokens per turn,
within an 8192-token context.

Requires `tt-kmd` > 2.9.0, Clang, and RISC-V binutils
(`riscv64-linux-gnu-ld` and `riscv64-linux-gnu-objcopy`). C firmware in
`firmware/` compiles on every device boot. Place local checkpoints and tokenizers
in `weights/llama3-8b-fp8/` and `weights/llama3-8b-bf16/`.
Checkpoints are not included in Git. Use `--port` to change the HTTP port.
