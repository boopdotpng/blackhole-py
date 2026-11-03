# Tests

Low-level Blackhole hardware tests: instruction behavior, compute, data movement,
synchronization, and timing. Model/runtime integration tests are removed.
The [ISA conformance suite](isa/README.md) additionally has offline checks for
all Tensix encoders and hardware tests with a documented coverage inventory.
Its encoding checks do not establish full functional ISA coverage.
The `operation_pocs/runtime` tests cover hardware primitives such as circular
buffers, semaphores, and NoC transfers.

Run from the repository using the shared workspace virtualenv:

```sh
../.venv/bin/python -m pytest tests --bh-hardware --bh-device=0 -q
```

Reserve the card with `tt-device-queue` when sharing it. Tests run sequentially;
do not use xdist. Without `--bh-hardware`, hardware tests skip; ISA encoding
checks run offline.

The `bh` fixture provides raw DRAM/L1 access and kernel launches. Kernels use
`Asm` directly; `bh.launch` fills missing RISC roles with firmware-return stubs.
A RISC-V `ret` cannot return from a worker kernel.

`tests/profiler.py` records device cycle intervals. Put completion waits inside
an interval when measuring completed work. The [test viewer](../tools/viewer/README.md)
can inspect generated instructions offline; captures do not establish hardware correctness.
