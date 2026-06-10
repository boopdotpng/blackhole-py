# Blackhole Tensix Coprocessor Backend Benchmark Plan

Goal: systematize microbenchmarking of the Tensix compute backend — unpack,
math/FPU (matmul), SFPU (vector), pack, and the internal XMOV/TDMA mover — and
extend it to the two engines not covered today (SFPU, XMOV). The central problem
is that the Tensix backend has **no directly-readable clock**: only the 5 RISC
cores can read `WALL_CLOCK`. This plan defines how we time async Tensix engines
anyway, how we observe completion, and how we validate the results.

The existing benches (`microbench_math_backend`, `microbench_unpack_backend`,
`microbench_pack_backend`, `tensix_instr_bench`, `microbench_sem_cb`) already
prove the core method works for unpack/math/pack. This plan generalizes that
method and fills the gaps the docs flag (isolated MVMUL, true multi-tile
subblock, SFPU, XMOV, and missing output validation).

## The Timing Principle: the RISC is the clock

We do not need a Tensix-side clock. The issuing TRISC:

1. stamps `WALL_CLOCK` (`RISCV_DEBUG_REG_WALL_CLOCK_L/H`, `ttk/tensix.py:122`)
   via the torn-read retry helper `read_wall_clock`,
2. pushes Tensix instructions into the instruction FIFO
   (`INSTRN_BUF_BASE = 0xFFE40000`) by storing words to it,
3. blocks until the backend signals **completion**,
4. stamps `WALL_CLOCK` again.

Everything hinges on step 3 — getting a clean **completion edge**. There are
three families, in increasing fidelity.

### Completion signal family 1 — FIFO / PC_BUF drain

Write-then-read-back `PC_BUF_SYNC` (`0xFFE80004`) or `PC_BUF_MOP_SYNC`
(`0xFFE80008`). The read-back *stalls the RISC until the instruction FIFO drains*
(`Tensix.tensix_sync` `ttk/tensix.py:324`, `mop_sync` `:310`). Add a
data-dependency fence so the read cannot be reordered.

- Coarsest: tells you the backend *consumed* the pushed ops, not that a specific
  engine retired a specific result.
- This is the workhorse in every current bench.

### Completion signal family 2 — in-stream stall + semaphore token

Issue `TTSTALLWAIT(SYNC, MATH|SFPU)` into the stream and consume an engine token
with `TTSEMGET` / `TTSEMWAIT` (conditions `STALL_ON_MAX=0x2`, `STALL_ON_ZERO=0x1`
in `TensixSemWait`). Named tokens in `TensixSem`: `MATH_PACK`, `UNPACK_SYNC`,
`PACK_DONE`, `MATH_DONE`, `UNPACK_MATH_DONE`, `FPU_SFPU`, etc.

- Sharper than the global drain: this is per-engine "*this* engine finished."
- The catch: those tokens normally come from the *other* engine in the
  producer/consumer pipeline, so an isolated row has to fake them
  (`TTSEMINIT(..., init=15, max=15)`) — which caps iterations per launch.

### Completion signal family 3 — observe the value getting written

Poll until the result actually appears in a RISC-readable location. This is the
*architectural* definition of "done," and it doubles as a correctness check.

- **Pack:** trivially available — pack writes real tiles to a CB in L1, so a
  RISC polls the CB write pointer (`cb_write_ptr`, `ttk/cb.py`) or a sentinel
  word in the output tile.
- **Unpack / math / SFPU:** *not* directly available — see next section.

## Key structural fact: only the packer produces L1-visible output

A RISC can only read L1 (and MMIO / its own LDM). The internal regfiles are not
L1 addresses:

- **Unpack** writes SrcA / SrcB.
- **Math/FPU** and **SFPU** write the Dest register file.

None of SrcA/SrcB/Dest are RISC-addressable. This single fact explains two
things:

1. **Why isolated unpack/math/SFPU rows hang.** Nothing downstream drains
   SrcA/SrcB/Dest, so the engine backpressures. The docs state this for unpack
   ("needs the TRISC1 clear-valid companion … otherwise repeated unpack rows
   backpressure"), for math ("a true four-tile subblock does not drain without
   TRISC0/unpack participation; a second isolated K step hangs"), and for pack
   ("times out without the full producer pipeline").
2. **Why value-observation (family 3) needs help for those engines.** There is
   nothing in L1 to poll, so they fall back to family 1/2 — which can *time* the
   op but cannot *validate* the result.

## The dest-readback path — what it is actually for

To *see* a math/SFPU/unpack result, Dest must be externalized to L1. Two routes:

- **(a) Chain a real packer** — pack reads Dest → writes L1. Works, but drags in
  the entire pack pipeline plus pack's own latency, so it **contaminates timing**
  of the engine under test and requires healthy pack machinery.
- **(b) Debug-move readback** — `TTMOVDBGA2D` (0x09) / `TTMOVDBGB2D` (0x0C)
  (`dsl.py:395/398`) plus the dest debug path (`RISCV_DEBUG_REG_DEST_CG_CTRL`,
  `0xFFB12240`, `ttk/tensix.py:130`) to lift a Dest row out cheaply, without the
  packer. **Preferred**, because it doesn't pollute timing.

**Why we want this — precisely, and what it does NOT buy:**

- It is **primarily a correctness / SFPU-enablement tool, not a timing
  requirement.** For unpack/math timing, family 1/2 already give a usable
  completion edge; value-observation is an upgrade (true result-visible latency),
  not a prerequisite.
- It **is** a prerequisite for two things:
  1. **Validation.** The pack bench reported timings for runs that produced
     **non-finite garbage** — timing without checking the value is how that slips
     through. A readback lets every timed row also assert correctness.
  2. **SFPU at all.** SFPU's entire output is in Dest. With no pack and no
     readback you cannot observe an SFPU result — cannot validate it, cannot even
     confirm `exp` executed. So SFPU value-observation timing and validation both
     depend on this path.
- "Verifiable immediately against a known matmul output" = to test the *readback
  mechanism itself*, run a matmul whose Dest values are already known from
  `matmul_peak`, read them back, confirm they match. Trust the readback before
  relying on it for novel SFPU numbers.

If the debug-move route proves unreliable, the pack-chain (a) is the fallback for
correctness, accepting the timing contamination.

## Handling the "isolated engine hangs" failure mode

Toolbox, cheapest to most robust:

- **Companion drainer thread** — an untimed TRISC loop that consumes the engine's
  output state, e.g. the unpack bench's TRISC1 `TTSETRWC(clear_ab_vld)` loop that
  clears SrcA/SrcB valid.
- **Pre-seeded semaphore tokens** — `TTSEMINIT(MATH_PACK, init=15, max=15)` to
  fake an absent producer (caps you at ~15 iters/launch).
- **One-shot launches** — one fresh device launch per measured row (math bench
  does this). Reliable but slow.
- **Minimal real pipeline scaffold** — the smallest genuine unpack→math→pack
  triangle, then time one engine inside it. Most robust; recommended investment.

## Methodology: three numbers per op (generalize `tensix_instr_bench`)

`tensix_instr_bench` already separates *issue-only* (stamp before an untimed
drain) from *issue+drain* (drain inside the timed loop). Generalize to three
measurements per op:

1. **Issue cost** — push N ops, stamp, then drain untimed. (RISC FIFO push rate.)
2. **Completion latency** — issue 1, drain, stamp. (One op end-to-end.)
3. **Steady-state throughput** — pipeline N ops then a single drain; throughput
   amortizes the fixed drain cost.

Comparing single-op latency (2) against N-op throughput (3) is a Little's-law
read on the engine's **pipeline depth / occupancy** — i.e. how many ops it keeps
in flight — which is a direct structural fact about the hardware.

## Per-engine plan

| Engine | Status | Cleanest completion signal | What to measure / what it reveals |
|---|---|---|---|
| **Unpack** (TRISC0) | exists | `PC_UNPACK_SYNC` poll + `TTSEMGET(UNPACK_SYNC)`; clear-valid companion | per-tile unpack cost vs block width; reload + context-flip cost; datapath width |
| **Math / FPU** (TRISC1) | exists | `TTSTALLWAIT(SYNC, MATH)` + `PC_BUF_SYNC` | **isolated MVMUL** (systolic fill/drain, the 16-cyc claim) and true multi-tile subblock — both currently hang without unpack |
| **SFPU** (vector) | **missing** | dest-readback (family 3) for value+validate; family 1/2 for raw timing | per-op throughput for `exp`/`rsqrt`/`recip`/`sigmoid`/`silu`; reveals SFPU lane count, LUT-vs-iterative, op latency. Needs `ttk/sfpu.py` recovered (llama-plan §4 item 1) |
| **Pack** (TRISC2) | exists | **CB write-pointer / L1 sentinel** (family 3, already value-observable) | per-subblock cost CB16/CB24, L1-accumulate on/off; **add the validation the current bench lacks** |
| **XMOV / mover** (TDMA) | **missing** | `TTSTALLWAIT(SYNC, XMOV)` + `PC_BUF_SYNC`; dest-readback to verify | cost of internal Dest↔Src moves (`TTMOVD2A` 0x08 / `TTMOVA2D` 0x12 / `TTMOVD2B` 0x0A), `TTSETDMAREG`; reveals the internal mover bandwidth that gates SFPU↔math and transpose |

## Current Suite Status

Dest readback and pack/readback validation are quarantined on shared hardware as
suspected hardware-wedge paths. Do not queue `microbenching/tensix/microbench_dest_readback.py` or
pack `--validate` jobs until the quarantine is explicitly cleared. The status
below is from static/docs review only; no new hardware runs were performed while
the quarantine is active.

| Area | Current usable result | Correctness status | Blocker / next step |
|---|---|---|---|
| **Unpack timing** | `unpack-backend-microbench.md` has successful isolated timing rows for `matmul_2x2_bw1` through `bw6`, reload, and control costs. Use these as timing-model inputs within the documented clear-valid companion setup. | Timing-valid. Direct SrcA/SrcB value validation is not present because those arrays are not RISC-visible. | Direct value validation would need the quarantined debug-move/readback path or a minimal real pipeline that consumes the values without wedging. |
| **Unpack blocked rows** | Combined long sweeps, `bw=6` at 10 iterations, and direct standalone cfg stores timed out. | Not valid for headline constants. | Resume only with one-shot/small-iters queue jobs after the suite is otherwise healthy; keep the clear-valid companion. |
| **Math timing** | `math-backend-microbench.md` has successful one-output-tile K-step and control rows. | Timing-valid for the one-shot isolated smoke rows only. Math Dest values are not directly validated. | True multi-tile subblocks and repeated K steps need a real unpack producer/drainer or validated Dest readback. |
| **Pack empty smoke** | `pack-backend-microbench.md` has a successful `empty` row proving launch/result plumbing. | Valid only as plumbing/baseline smoke. | None for the empty row. |
| **Pack real-pipeline counters** | The real `matmul_peak.py` profile counters provide usable pack timing-model calibration (`CB16 final`, `CB24 partial off`, inferred `CB24 partial on`). | Timing counters are usable, but those runs failed output validation on non-finite padded outputs, so they are not correctness-valid pack-output proof. | Re-run validation only after the pack/readback quarantine is lifted, or use a non-readback full-pipeline validation path first. |
| **Standalone pack rows** | Implemented behind `--allow-standalone-pack`; CB16 standalone attempt timed out. | Not valid. | Needs a better producer-side scaffold or full pipeline. Pack `--validate` hardware use is paused under quarantine. |
| **Pack `--validate`** | Static code exists to check output-CB sentinel overwrite and finite zero BF16 values from seeded `TTZEROACC`. | Not hardware-confirmed. | Quarantined with Dest readback/pack validation until explicitly cleared. |
| **Dest/Src readback** | Additive helper and build-only program assembly exist; `dest-readback.md` records build-only success. | No clean hardware proof. Earlier 256-row attempts perturbed pack output; 64-row proof was blocked/timed out. | Quarantined. Needs staged re-enable guardrails below before any shared-hardware retry. |

Before resuming quarantined rows, require all of the following guardrails:

1. Explicit clearance from the hardware owner that the suspected wedge path may
   be retried.
2. Hardware access only through `tt-device-queue`; no direct device-opening
   Python.
3. One small queued job at a time, with short host and benchmark timeouts, and
   stop on the first timeout, non-finite output, all-`0xff` readback, or ARC
   readiness failure.
4. Establish a clean non-readback full-pipeline matmul baseline on the target
   core before enabling any debug-array readback.
5. Treat a cycle delta as a **clean perturbation bound** only if both the
   no-readback and readback runs finish, the no-readback output validates, the
   readback bytes match the known matmul tile, and the post-readback packed
   output also validates. If pack output changes, report it as perturbing
   behavior, not as a timing bound.
6. If perturbation recurs, bisect with progressively smaller readback scope and
   explicit toggles for pack-after-readback, row count, and `DEST_CG_CTRL`
   handling before returning to the full 64-row proof.

## Two new harness capabilities (build in this order)

1. **Dest / SrcA / SrcB readback path** (`TTMOVDBGA2D` → L1 → RISC poll). Unlocks
   correctness validation for every internal-result engine and value-observation
   timing where wanted; prerequisite for the SFPU bench. Verify against a known
   `matmul_peak` Dest output first.
2. **Minimal real pipeline scaffold** — smallest unpack→math→pack triangle so any
   single engine can be timed in steady state without backpressure, replacing the
   fragile fake-token / one-shot approach.

## Suggested order

1. Dest-readback path + validate against known matmul output.
2. Retrofit validation onto the existing pack bench (close the non-finite-output
   gap).
3. Minimal pipeline scaffold.
4. Isolated MVMUL + true multi-tile subblock (math), inside the scaffold.
5. **SFPU bench** (highest external leverage — unblocks rmsnorm/softmax/swiglu in
   the llama work).
6. XMOV / mover bench.

## Limitations / honest caveats

- **No Tensix clock and no per-engine retirement counter** exist — completion is
  always inferred from a RISC-side blocking read (PC_BUF drain) or a consumed
  semaphore token. All "engine cycles" are RISC-observed deltas, so they include
  the fixed sync-marker cost (`sync_empty` ≈ 9.24 cyc) which must be subtracted as
  a baseline.
- **Cross-engine completion handshakes normally come from other engines**, so
  isolated rows fake them and are capped per launch — absolute throughput from
  faked-token rows is an upper bound, not the in-pipeline steady state. Prefer the
  scaffold for headline numbers.
- **Dest-readback semantics need to be confirmed** before trust — hence the
  matmul cross-check. If the debug-move path is unreliable, fall back to a
  pack-chain for correctness and accept timing contamination.
- The debug-move and dest readback may perturb engine/clock-gating state
  (`DEST_CG_CTRL`); measure with and without readback to bound its effect.
