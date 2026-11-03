# Intermittent native crash investigation

The original crash is **unresolved and has not reproduced**. No production
runtime change is claimed to fix it.

## Original observation

Queue job `7a0da9470a66407aa6fdbca68426f314` exited 139 during the first combined
run. Python reported pytest capture teardown (`_pytest/capture.py:592`, reading
the capture file), without a test assertion failure. Sanitized journal evidence
is retained in [evidence/original_crash.json](evidence/original_crash.json).
The recorded native stack ends at `0x7ff76a1153c8`, within the anonymous
`7ff76a114000-7ff76a118000 rw-p` mapping. This suggests an invalid execution
target; it does not identify the source of corruption or prove a hardware,
Python, pytest, or runtime bug. The original core could not be read with the
available account permissions. Python's optional JIT was not enabled through
`PYTHON_JIT` in the recorded environment.

## Follow-up runs

| Configuration | Result |
|---|---|
| Original predicate suite alone | 5,424 passed |
| Original ISA suite plus existing predicates | 30,357 passed |
| GDB with `PYTHONMALLOC=debug` | 30,351 passed; inferior exited normally |
| Debug allocator plus native mapping bounds checks | 32,759 passed |
| GDB, normal allocator/capture, repeat 1 | 32,769 passed |
| GDB, normal allocator/capture, repeat 2 | 32,769 passed |
| GDB, normal allocator/capture, repeat 3 | 32,793 passed |

Counts increased as synchronization, audit, and cast tests were added. The first
GDB queue command itself exited 1 because it requested registers after normal
process exit; that was a debugger command error, not a test failure. The checked-in
GDB script avoids that error. No bounds violation or allocator diagnostic
appeared. Passing repetitions cannot establish that the intermittent fault is fixed.
The latest combined validation is recorded in [results.md](results.md).

## Reproduction and diagnostics

From `blackhole-py`, reserve the device before running:

```sh
tt-device-queue run --device 0 --timeout 600 --cwd "$PWD" -- \
  'gdb --batch --return-child-result -x tests/isa/debug.gdb --args ../.venv/bin/python -m pytest tests/isa --bh-hardware -xq'
```

[debug.gdb](debug.gdb) stops native faults before Python's handler, prints native
backtraces/registers/mappings and writes `/tmp/blackhole-isa-reproduced.core`.

The optional Python plugin records outcomes, source hashes and the current test
in a separate `.current.json` file so the last node survives a native crash:

```sh
tt-device-queue run --device 0 --timeout 600 --cwd "$PWD" -- \
  'PYTHONMALLOC=debug ../.venv/bin/python -m pytest tests/isa --bh-hardware -q -p tests.isa.record --isa-record=/tmp/isa-debug.json --isa-memory-checks'
```

`--isa-memory-checks` checks bounds and closed mappings before existing Sysmem
and TLB read/write methods call ctypes. It is an opt-in test diagnostic, not a
complete memory-safety proof: direct pointer operations and device writes are
outside those wrappers. A reproducible native stop or accessible original core
is still needed to establish the crash's root cause.
