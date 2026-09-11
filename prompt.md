# Blackhole operation PoCs: coordinator and shared agent instructions

## Goal and scope

Build reusable raw hardware implementations, independent correctness tests and benchmarks for individual operations so lowering/codegen can later reuse proven recipes. Read [hardware-coverage-matrix.md](hardware-coverage-matrix.md). It is the active scope. The broader audit reference is historical evidence, not an instruction to implement inference, training, codegen, arbitrary-length compute or composed reduction kernels.

Use **five agents in the same repository**, `/home/boop/tenstorrent/blackhole-py`. Two agents may execute hardware jobs concurrently, one per card; all five may author/assemble/analyze code concurrently. These prompt files are preparation only: creating them does not launch agents.

Each assigned agent must read this entire file and its individual prompt before working. Read any applicable AGENTS.md. User scope and the queue rules below are mandatory.

## Exclusive ownership

| Agent | Prompt | Exclusive writable subtree |
|---|---|---|
| A — transport | [01-transport.md](prompts/01-transport.md) | `tests/operation_pocs/transport/` |
| B — FPU/Dst | [02-fpu.md](prompts/02-fpu.md) | `tests/operation_pocs/fpu/` |
| C — SFPU math | [03-sfpu-math.md](prompts/03-sfpu-math.md) | `tests/operation_pocs/sfpu_math/` |
| D — SFPU movement/control | [04-sfpu-movement.md](prompts/04-sfpu-movement.md) | `tests/operation_pocs/sfpu_movement/` |
| E — external movement/sync | [05-runtime.md](prompts/05-runtime.md) | `tests/operation_pocs/runtime/` |

An agent may create helper modules, tests, local `__init__.py`, README and result files **only within its assigned subtree**. Logs/build outputs must use that subtree or a unique agent-specific temporary directory. Parent directory creation is fine; parent `__init__.py`, parent conftest/config and shared registries belong to the coordinator. Python namespace subpackages can be used under the existing `tests` package; do not race to create shared package files.

All existing files are read-only during parallel work, including `ttk/model.py`, `isa.py`, `asm.py`, `regalloc.py`, firmware, device/runtime code, `tests/harness.py`, `tests/conftest.py`, `tests/profiler.py`, existing test/helper files, root docs and these prompts. Preserve all pre-existing tracked/untracked changes. Do not switch branches, create worktrees, commit, reset, clean, revert, move or format another agent's files. Do not spawn further agents.

If a shared fix is necessary, send the coordinator the exact issue/proposed patch and continue independent work. The coordinator alone schedules shared edits after affected jobs finish. A missing encoder can be prototyped in an owned helper using existing emission facilities; do not monkey-patch shared modules globally. Do not silently change the model/API to make a test pass.

Read/import stable existing helpers freely. New cross-agent imports require the owning agent to publish a stable interface and promise it will stay frozen for the consuming job. Prefer small local adapters initially; the coordinator can consolidate them after correctness. Never edit a file being consumed by your queued/running job. Freeze all owned code relevant to a submission until it finishes or is confirmed canceled. Do not run another agent's mutable tests without coordinating a freeze.

## Mandatory two-card/two-queue protocol

There are **two Blackhole cards: device 0 and device 1**, and **two independent queues: queue 0 and queue 1**. `tt-device-queue` is on PATH. **Every command that may access hardware must go through it**, including tests, probes, device inspection/telemetry, boot, benchmarks and recovery. The pytest fixture's card lock is additional protection, not a replacement for the queue. CPU-only editing, assembly, host references and device-free collection/tests can run normally.

Before each hardware submission:

1. Run `tt-device-queue --json status` (queue-service metadata; no device access). Inspect `devices`, `worker.devices`, `running` and `pending`. Ignore `recent` when comparing queue depth.
2. Among healthy, enabled queues with live workers and no pending reset, choose the **less full queue**, counting running plus pending jobs per `device_id`. If tied, alternate or choose randomly so agents do not all prefer card 0. Recheck after each completed job; do not permanently pin an agent to a card.
3. Set the physical device used by the command to the same chosen number: `--device 0` with pytest `--bh-device=0` / `Device(0)`; `--device 1` with `--bh-device=1` / `Device(1)`. The service **does not** set `TT_VISIBLE_DEVICES` or choose hardware for the process. Standalone scripts must take an explicit device argument; no hidden/default `Device()`.
4. Submit a bounded job, record its ID, and monitor it. A status/submit race can change which queue is shorter but does not violate safety: FIFO serialization still applies. Keep at most one outstanding hardware job per agent, and use manageable batches so others get service.
5. One queued command must use only its matching card, with one device-owning process. No background hardware children, hardware xdist, nested queue submissions, or commands touching both cards. Completion must mean all hardware work and children have finished.

Example submissions from the repository root (replace the subtree/client tag with yours; choose **one** according to current load):

```bash
tt-device-queue --client-id poc-A --json queue --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -p no:cacheprovider tests/operation_pocs/transport --bh-hardware --bh-device=0 --bh-core=0 --bh-timeout=10'
tt-device-queue --client-id poc-A --json queue --device 1 --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -p no:cacheprovider tests/operation_pocs/transport --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10'
```

Queue 0/card 0 and queue 1/card 1 matching is mandatory even if a previous test only worked on one device. Default to an available valid worker index rather than assuming a historical worker 27/28 exists or is suitable; hardware discovery must itself be queued. Use per-card topology from the runtime; do not share cached device objects or assumptions across cards.

Monitor without holding a long blocking tool call:

```bash
tt-device-queue job JOB_ID
tt-device-queue logs JOB_ID --offset 0 --limit 16384
tt-device-queue result JOB_ID
```

`queue` returns immediately. Use bounded polling/log reads while running; `result` waits, so retrieve it once complete or through a yielding tool. Interrupting a wait **does not cancel** the job. Inspect metadata after disconnect/timeout before resubmitting; never assume the card is free because the client stopped waiting. Distinguish test timeout, queue timeout, skip and hardware pass.

For suspected breakage, inspect queue status and notify the coordinator. Resets must also go through `tt-device-queue reset --device N`; they can interrupt the current job, so coordinate recovery and ensure it cannot disrupt another agent's work. Never use bare reset (both cards), raw `tt-smi`/sysfs reset outside the service, or kill another agent's job. Do not use resets to shorten waits or as routine benchmark setup. A dead/disabled queue is unavailable; do not bypass it. No all-card tools under a single queue reservation.

## Shared operation and allocation requirements

- One source slot is 128 elements. One 128-element FP32 Dst slot occupies two adjacent aligned 16-bit allocation units.
- ELWADD/SUB/MUL use one A slot, one independent B slot and one FP32 Dst slot. MVMUL/GAPOOL/GMPOOL use one aligned A pair `(0,1)`, `(2,3)`, `(4,5)` or `(6,7)`, any B slot and one FP32 Dst slot. Keep useful result vs physical write footprint explicit.
- Tests must vary legal slot placement and preserve all non-owned allocations. No hidden whole-bank unpack or whole-Dst clear inside the operation under test. Fixture-only poison/observation can access guards but must be distinguished from the tested operation and must not hide its side effects.
- FPU compute uses whole allocations. Partial transfers are a separate individual-operation requirement: N=1..127, plus full control N=128, to selected SrcA/SrcB/Dst slots and from selected Dst to CB. First-phase partial unpack zero-fills the remainder; no arbitrary-length compute suite.
- Physical CB padding/staging, if required, must be explicitly owned and measured. Do not label padded output as exact-N adjacent-buffer preservation. A result sentinel alone cannot establish no overread.
- SFPU tests target public `SFPU`/`SFPURegister` operations and fixed lane masks. `exp`/`reciprocal` are public operations requiring implementations even if multi-instruction internally. Do not add rsqrt/log2/reduction/activation-chain algorithms absent from the current API.
- Read local architecture documentation, existing tests and ISA definitions for semantic expectations. tinygrad is reference-only here; no tinygrad backend or codegen work.

## Mandatory per-operation kernel profiling

**Every hardware operation PoC must include device-side cycle profiling.** Correctness alone or host launch time is not sufficient. Each tested operation/mode/length must produce a labeled cycle result, visible with pytest `-s`, and the final measurements must be retained in the agent's owned `results.md` or an accompanying CSV/JSON file. Fixture-only helper kernels need no separate benchmark unless they are themselves assigned operations.

Use the existing `tests.profiler.Profiler` read-only wherever practical: place `record(label)` immediately before the main operation and the matching record after its required completion/drain, pass the profiler to the harness launch and capture `profiler.last[label]`. The current helper supports at most three labeled sections; use additional launches or an owned profiling adapter when needed rather than modifying shared profiler code. Reserve its L1 storage explicitly and keep it disjoint from operands, scratch and guards.

Timing boundaries:

1. Finish fixture input staging, static configuration and prior outstanding work before the start marker. Record which setup is assumed reusable by the operation.
2. Time the actual assigned operation, including instructions/synchronization needed to make its result ready for its consumer. A RISC timestamp after asynchronous instruction issue does not prove hardware completion; insert the appropriate FPU/SFPU/packer/unpacker/NoC drain before the end marker.
3. Keep unrelated output packing/readback/reference comparison and host launch overhead outside the main interval. If pack or unpack is itself the assigned operation, its transfer and completion belong inside. For partial transfers, required fill/staging/final copying belongs in the complete-operation cost; optionally time the hardware engine portion separately.
4. Where per-call configuration or handoff is required, report a second complete-operation interval including it, or include it in the primary interval. Do not hide mandatory work as reusable fixture setup. For synchronization operations distinguish uncontended overhead from intentional waiting time.

For short operations, time a known number K of repeated operations and report both the raw interval and cycles/operation = interval/K. State loop/replay overhead and whether dependencies make this latency or throughput. Make repeated execution valid (accumulator values, CB credits and buffers included); do not change the operation's contract solely to get a low number. Tiny single-instruction measurements must acknowledge marker overhead.

Measure an empty-marker/control interval under the same conditions. Always preserve raw cycle counts; any overhead-subtracted estimate must also state its control and formula. Do not silently subtract waits or publish negative/unsupported corrected costs. Timers, profiling stores and measurement loops must not corrupt the result, operands or state being verified. Keep 32-bit timing intervals short enough to avoid ambiguous multiple wraps.

Collect repeated samples for final results (at least seven measured samples per reported case after a stated warmup policy). Record minimum, median and maximum, K, cycles/operation, physical card/core, queue job ID, operation name, dtype, mode/fidelity, allocation placement and N for partial transfers. Compare baseline and candidate on the same card/configuration; do not pool cards' samples. A full sweep may use compact machine-readable records with representative summaries in `results.md`, but no assigned operation should lack a cycle count.

Correctness must pass for the measured final implementation. Add no fixed-cycle pass/fail assertions: the counts are optimization evidence. All profiling runs obey the same two-card queue rules as correctness tests.

## Required deliverables within each owned subtree

1. Reusable callable raw emitter(s), separate from host data/reference code, accepting explicit allocations, modes and operands. No host-computed replacement for the operation.
2. Hardware correctness tests using the existing `bh` harness and independent oracles. Include guards, distinct lanes, aliases and relevant numeric/format edge cases. CPU validation/codegen tests supplement hardware, never substitute for it. Avoid success-by-skip/xfail.
3. Benchmarks isolating the operation from setup/transport/observation; drain dependencies correctly. Record median/distribution over repeated samples, instruction/register/scratch costs and numerical contract. Where meaningful, distinguish dependent latency from independent throughput. Do not assert brittle fixed cycle limits.
4. `README.md`: one row per owned operation, signature/footprint, precision, clobbers/state, synchronization, setup/restore requirements, test names, evidence, cost and remaining gaps. This is the future lowering recipe.
5. `results.md`: exact queued job IDs, commands, physical card/core, relevant firmware/config context obtained through queued execution, pass/fail/skip counts, baseline/candidate measurements and conclusions. Do not average away card-specific differences. Confirm the final selected version, not merely an earlier candidate.

Prioritize a correct runnable PoC for every assigned operation, then optimize expensive cases using measured hypotheses. Keep baseline/reference comparison and choose a simpler version when a more complex candidate has no repeatable benefit. Do not endlessly tune one operation while leaving others unimplemented. Record unsupported modes/real hardware limitations precisely rather than changing scope silently.

CPU collection example, after verifying module import is device-free:

```bash
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /home/boop/tenstorrent/.venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/operation_pocs/YOUR_SUBTREE
```

Before finishing, check your owned diff and run its final hardware tests through the less-full healthy queue. Report files changed, operation coverage, job IDs/results, optimizations and genuine blockers to the coordinator. Do not claim “entire chip supported” from the current API subset.

## Coordinator responsibilities

Launch exactly one agent per prompt when implementation is requested. Agents share this checkout and follow the exclusive ownership table. Preserve existing dirty files. Do not revive any old agent with its earlier ownership/task; if reusing one, replace its instructions with this prompt and its new assignment first.

Resolve shared-file requests centrally, with affected jobs drained before editing. Publish stable cross-agent helper interfaces explicitly. After individual jobs finish, review the five result catalogs and queue combined regression tests on stable files; require partial transport and allocation preservation to remain correct. Keep hardware concurrency at two, enforced exclusively by the queue service. Consolidation/codegen/model kernels are later work, not part of these prompts.
