# Scattered transfer follow-up

The 2026-09-06 audit follow-up fixes matrix A pair placement and adds **116
hardware cases**: 56 unpack and 60 pack. Two CPU checks ensure the largest new
kernels fit resident worker text partitions. All allocations remain multiples
of 128 elements; FP32 Dst uses two physical units per logical slot and BF16 one.

## Unpack coverage

`operation_pocs/transport/test_scatter_unpack.py` covers:

- Dense L1 input split into nonconsecutive SrcA, SrcB or FP32 Dst allocations.
- BF16 and FP32 input; source input is converted to BF16 as in the existing API.
- Contiguous, irregular and reverse orders; all eight source slots and six Dst
  segments, including logical Dst slot 63.
- Independently sized prefixes `(1,17,73,127)`, with zero-fill confined to the
  selected allocation. A256 pairs include lengths 129 and 255 at starts 6 and 0.
- One final source-bank publication after all segments. The observation uses
  actual FPU source-to-Dst moves and checks both source banks and every Dst slot.
- Untouched L1 source, output guards, and scratch guards, with alternating poison.

Twenty of these cases use a new direct full-block recipe,
`transport/ops.py::unpack_source_scatter`: configure once, replace the input base
and destination per segment, drain each transfer, publish on the last segment.
These use no scalar staging or scratch. The 26 staged source cases retain exact
prefix handling; the 10 Dst cases use the source-preserving SFPU insertion recipe.
Dst timings therefore do not claim direct-UNPACR performance.

Representative direct-unpack medians, card 0/worker index 12, one warmup and
three retained launches, including configuration and completion:

| Input / target | Contiguous four A/B128 blocks | Irregular four A/B128 blocks |
|---|---:|---:|
| BF16 / SrcA | 341 cycles | 341 cycles |
| BF16 / SrcB | 336 cycles | 336 cycles |
| FP32 / SrcA | 353 cycles | 353 cycles |
| FP32 / SrcB | 348 cycles | 348 cycles |

Two A256 pairs cost 255 cycles for BF16 input, 265 for FP32, both for `(0,2)` and
`(6,0)` pair starts. These are concrete drained schedules; no timing assertions
or claim of peak throughput. Original sample job:
`745d479dd74d4d268d68333620d843cc`.

## Pack coverage

`movement/packer/test_scatter_formats.py` adds:

- All four combinations of BF16/FP32 Dst storage and BF16/FP32 output format.
- One and four read interfaces; contiguous, reverse, irregular, eight-segment,
  and repeated-source orders. Last legal slots 63 and 127 are exercised.
- Exact final tails of 1,17,127 elements, with nonzero and unaligned L1 output
  offsets 17,66,79. Full blocks gather directly; tails pack to scratch and copy
  exactly the requested bytes to the output view.
- Unique signed, finite BF16-exact input values across the entire Dst, independent
  expected gather order, full-Dst preservation, and output/scratch sentinels.
- A two-page CB shared by the packer and a separate NCRISC consumer. Six pages
  cycle the physical ring three times, starting credit counters at 65534 and
  checking both wrap to 4. Every publication shifts the selected source slots,
  so stale data differs from the expected page. Consumer delay and a full-page
  snapshot before release test reuse under pressure. Both full and 73-element
  tails run for all four format combinations.

Single-page timings cover pack address setup, PACRs and drain, excluding initial
format setup, exact tail copying and observation. CB timing reports only the
last page's pack interval; it excludes waits, copies and reader delay. Hardware
assertions check all six CB pages, including unused bytes, not just the timed one.

This adds format/order/CB proofs alongside the original optimized scatter test;
it does not replace that test or introduce a model backend.

## Model and SFPU decisions

`Kernel.allocate()` now derives the required start parity from each matrix A
view. It accounts for view offsets and rejects incompatible requirements on one
root allocation. Six added frontend cases cover live single-block interference,
all three matrix/pool operations, view offsets, contradictory views and the last
legal pair. Block counts and ordinary source alignment are unchanged.

The loop-backedge issue is explained but intentionally not changed. A value
initialized before a loop and read near its beginning remains needed by the next
iteration; scratch written near the end cannot reuse that storage. The current
linear interval calculation misses that dependency.

No SFPU API changes were made. With caller-owned L0–L7, numerical helpers can
accept explicit scratch registers without introducing an SFPU register allocator.
The same rule should cover predicate construction and special-register stores
that need a writable intermediary. Automatic scratch selection would be a
separate design choice. Item 6 integration work is deferred.

## Fixture corrections found during development

- Unrolling source scatter plus eight copies of Dst setup exceeded TRISC0's text
  partition at eight segments. The scatter fixture now initializes the full Dst
  with one existing runtime-size unpack. Existing prefix fixtures keep their old
  setup. A CPU image-size regression covers this failure.
- A 1024-row MOP observation emitted no BF16 output. Full BF16 Dst observation
  now uses two 512-row MOPs, keeping the output stream open between them. No
  production packer behavior was weakened to make this pass.

Hardware jobs ran sequentially through `tt-device-queue`, card 0/worker index 12.
No resets were issued. Final verification and retained evidence are listed below.

Final combined job `d730949ce3184eefb3b81dd61657e07a`: **164 passed in 55.90 s**,
zero failures/skips. This includes all 116 new hardware cases, two new CPU image-
size checks, 32 existing transport cases with their full prefix sweeps, three
existing scatter-pack tests, and all 11 frontend model cases.

```sh
tt-device-queue --client-id scatter-audit --json queue --device 0 \
  --cwd /home/boop/tenstorrent/blackhole-py --timeout 300 \
  --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 --env TRANSPORT_DEVICE=0 -- \
  '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/test_model.py tests/operation_pocs/transport tests/movement/packer/test_scatter.py tests/movement/packer/test_scatter_formats.py --bh-hardware --bh-device=0 --bh-core=12 --bh-timeout=10 --junitxml=/tmp/scatter-final.xml'
```

Retained evidence: [JUnit](operation_pocs/evidence/scatter-final.xml),
[queue metadata and source hashes](operation_pocs/evidence/scatter-final.json),
and [complete compressed log](operation_pocs/evidence/scatter-final.log.gz).
The entire CPU-only suite passed separately: **58 passed, 897 hardware skips**.
