# Review brief: blackhole-py cleanup

You are one of four independent reviewers (different models). Do NOT edit any file in the repos. This is a read-only review; the only file you write is your report.

## Context
- Workspace: ~/tenstorrent. Main repo: ~/tenstorrent/blackhole-py (git). Llama 3 decode on a Tenstorrent Blackhole card from Python: host runtime (helpers.py, system.py, ops_blackhole.py, llama3.py, bench.py, smi.py), C firmware (fw/), prebuilt RISC-V kernel images (kernels/), the TTRV kernel language + compiler (ttrv/, docs/ttrv_spec.md, docs/ttrv_gaps.md, docs/examples/*.ttrv), and tooling/experiments (kperf/, kview/, play/, sync/, chat/).
- ~/tenstorrent/blackhole-py-old is the predecessor (asm.py, cq.py, device.py, program.py, ttko, firmware/). Some prebuilt images in blackhole-py/kernels/ were exported from it (e.g. kernels/zero/export.py still imports blackhole-py-old; ttrv/isa.py borrows ttko enums).
- Neighbouring reference repos (tt-metal, tt-llk, tt-isa-documentation, sfpi, tt-lang, tinygrad, tt-kmd) are there for reference only.

## What the owner wants
1. Cut the repo down: too much stuff. Identify what is dead, duplicated, experimental, or should move out (play/, sync/, kperf vs play duplicates, checked-in traces/.npz/.json artifacts, docs that are stale, etc.). Be concrete: list files/dirs to delete, merge, or relocate.
2. Fully move away from blackhole-py-old: no exporter, no prebuilt images exported from it, no borrowed code paths. Lay out what still depends on it (directly or via prebuilt kernels/ blobs), and a migration order to get every Llama 3 kernel built from TTRV source.
3. Remove hand assembly from blackhole-py where TTRV (or a small, well-defined lower layer) should own it.
4. Consolidate the runtime, flags/CLI options, firmware build/load, and device setup into one coherent, smaller surface. Point out duplicated device-open/alloc/queue/launch logic, inconsistent flags across scripts, and config scattered across files.
5. Code review / bug report: real bugs, races, wrong assumptions about hardware, error handling holes, things that will break. Give file:line and why. Separate confirmed bugs from suspicions.
6. Write code better: simplifications, smaller abstractions, places where 3 functions should be 1, where tables should replace branches, where names are misleading.
7. TTRV language ideas: read docs/ttrv_spec.md, docs/ttrv_gaps.md and the example kernels. Propose language features/sugar/idioms that make kernels shorter and easier to read (show before/after snippets using real kernels from docs/examples). Also flag spec features that add complexity without paying for themselves.

## Report
Write your report as markdown to ~/tenstorrent/reviews/blackhole-py-2026-11-18/<your-model-name>.md with sections:
- TL;DR (top 10 actions, ranked by payoff/effort)
- Bugs (confirmed / suspected), with file:line
- Delete / merge / move list
- Leaving blackhole-py-old: dependency inventory + migration plan
- Runtime/flags/firmware consolidation proposal (sketch the target module layout and public API)
- Code quality simplifications
- TTRV language ideas (before/after snippets)
- Open questions for the owner
Prioritise depth and specificity over coverage; verify claims by reading code. You may run read-only commands and pure-Python tests that do not need hardware (e.g. `python test_ttrv.py`, `python -m ttrv build ...` into a temp dir). Do not touch the device. When done, reply with the report path and your top 5 findings.
