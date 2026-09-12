# Tests

Hardware tests are opt-in; reserve the selected card with `tt-device-queue`:

```sh
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'PYTHONPATH=. .venv/bin/python -m pytest -q tests/movement tests/compute --bh-hardware --bh-device=0'
```

Hardware tests run sequentially and share the session's device. Do not use xdist.
The `bh` fixture provides raw DRAM/L1 access and kernel launches. Kernels use
`Asm` directly; `bh.launch` fills missing RISC roles with firmware-return stubs.
A RISC-V `ret` cannot return from a worker kernel.

`tests/profiler.py` records device cycle intervals. Place completion waits inside
an interval when measuring completed work.

Use the [test viewer](../tools/viewer/README.md) to inspect generated instructions
offline. Viewer captures do not establish hardware correctness.
