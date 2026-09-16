# Tests

Low-level Blackhole hardware tests: instruction behavior, compute, data movement,
synchronization, and timing. Model/runtime integration and CPU-only tests are removed.
The `operation_pocs/runtime` tests cover hardware primitives such as circular
buffers, semaphores, and NoC transfers.

Run from the repository using the shared workspace virtualenv:

```sh
../.venv/bin/python -m pytest tests --bh-hardware --bh-device=0 -q
```

Reserve the card with `tt-device-queue` when sharing it. Tests run sequentially;
do not use xdist. Without `--bh-hardware`, the suite skips all tests.

The `bh` fixture provides raw DRAM/L1 access and kernel launches. Kernels use
`Asm` directly; `bh.launch` fills missing RISC roles with firmware-return stubs.
A RISC-V `ret` cannot return from a worker kernel.

`tests/profiler.py` records device cycle intervals. Put completion waits inside
an interval when measuring completed work. The [test viewer](../tools/viewer/README.md)
can inspect generated instructions offline; captures do not establish hardware correctness.
