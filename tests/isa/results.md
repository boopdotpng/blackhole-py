# Validation — 2026-09-17

The final combined run on device 0, worker-core index 0, passed:
**33,725 passed, 60 deselected, 5 xfailed in 179.05 seconds**.
Queue job: `531310e844f84262b8e4498f408caa70`.
Compact outcomes and source fingerprints are in
[evidence/final.json](evidence/final.json); [audit.md](audit.md) uses this run.

```sh
../.venv/bin/python -m pytest \
  tests/isa tests/operation_pocs/fpu tests/operation_pocs/sfpu_math \
  tests/operation_pocs/sfpu_movement tests/operation_pocs/transport \
  tests/movement/sfpu tests/movement/packer \
  tests/movement/unpacker/test_unpack.py tests/movement/unpacker/test_dst_paths.py \
  tests/movement/unpacker/test_unpack_fp8.py \
  tests/compute/sfpu/test_loadmacro_pipeline.py \
  tests/operation_pocs/runtime/test_runtime.py \
  -k 'not external and not cb_ and not benchmark' --bh-hardware -q \
  -p tests.isa.record --isa-record=/tmp/isa-final-evidence.json --isa-memory-checks
```

This command was executed through `tt-device-queue` with a 600-second timeout.
The keyword filter excludes external/CB/benchmark cases and also matches 33
ISA encoding parameter cases; those cases were exercised in the unfiltered
ISA run below. The final combined run includes all 9,572 new ISA hardware cases,
23,188 offline ISA checks, and 965 passing existing tests. Five existing FP8
subnormal divergences remain xfailed; their expectations were not weakened.

## Unfiltered ISA validation

The complete ISA suite passed under GDB with the normal allocator and pytest
capture: **32,793 passed in 41.56 seconds**, third repetition in queue job
`4cc533e5a4f34b198ded16bfacf05638`. All three inferiors exited normally.
The full suite comprises:

- 23,211 offline encoding/inventory checks for 137 encoders and 517 fields.
- 10 offline audit/diagnostic checks.
- 5,424 predicate-stack hardware cases.
- 1,122 SFPU bit/flag hardware cases.
- 594 scalar GPR hardware cases.
- 2,408 semaphore/mutex hardware cases.
- 24 integer-to-float cast hardware cases.

See [crash_investigation.md](crash_investigation.md) for the other GDB and debug
allocator runs. The earlier intermittent native crash is **unresolved**;
successful repetitions do not establish a fix.

## Existing tests and regression fix

The reviewed FPU/SFPU/movement/runtime selection independently passed with
**877 passed, 27 deselected, 5 xfailed in 66.09 seconds**. Full transport initially
failed on a stale `__import__('isa')`; both stale references now use
`from ttko.isa import Tensix as TT`. After this correction, **88 transport cases
passed in 61.92 seconds**, including default prefix lengths 1 through 128.
Both selections passed again in the final combined run.

Historical compact evidence is retained alongside the final record:
[existing](evidence/existing.json), [synchronization](evidence/synchronization.json),
[cast](evidence/cast.json), [debug allocator](evidence/diagnostic_full.json),
[transport before fix](evidence/transport_before_fix.json), and
[transport after fix](evidence/transport_after_fix.json).
The original 30,357-case ISA-plus-predication run also passed before this expansion
(queue job `4b3d17eb683c4067a9649ca073a3bda9`).

These results support only the listed assertions and parameters. They do not
establish every instruction/modifier interaction, all cores/cards, or exhaustive
concurrency semantics. See [review.md](review.md) for the remaining work.
