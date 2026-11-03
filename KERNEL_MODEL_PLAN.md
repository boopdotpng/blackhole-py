# Training a specialized kernel model for blackhole-py

Plan for a model that, given an op and a precision budget, chooses how to
lower it on Blackhole (FPU vs SFPU, fidelity, tiling, engine schedule) and
emits a fast kernel for this runtime. Trained with SFT plus multi-turn RL with
verifiable rewards, using the local cards as the environment and rented GPUs
for training. Written 2026-09-16 from the repo at `d8eae8f` plus working tree
and the published CUDA/Triton work.

## 1. What the model is

A plain decoder LLM. Nothing exotic: a Qwen base, continued pretraining on
the corpus, SFT on trajectories, then RL with verifiable rewards (RLVR is the
paradigm; GRPO, RLOO or TRLOO are interchangeable advantage estimators for
it). The algorithm is a commodity. What decides whether this works is the
environment: the language the model writes, the reference it reads, the task
suite, the reward, and the feedback it gets between turns. About 90% of the
work is in this repo, not in the trainer.

## 2. How it learns register layouts, launch constraints and hardware behavior

Four channels, each covering what the others cannot:

1. **The spec, in context.** A frozen, generated reference the model sees on
   every prompt: the ISA table with named fields and one-line semantics, the
   config/MMIO/mailbox register map, the launch ABI and L1 map, the macro
   reference, the rules that hang (what each RISC may do, what must be
   posted before what), and a hardware facts sheet with measured numbers
   (MVMUL one per cycle, unpacker byte rates, NoC and DRAM bandwidth, SFPU
   latencies, Dst capacity, fidelity phase costs). Declarative facts are
   cheap to read and do not need to be memorized. This is generated from
   `ttko/isa.py`, `ttko/registers.py`, `firmware/consts.py`, the macro
   library and the results markdown, so it cannot drift from the code.
2. **The corpus, by training.** Continued pretraining and SFT on the repo,
   tt-llk, tt-metal LLK, the ISA docs, boop-docs and the microbenchmark
   results teach idioms, not addresses: what a correct unpack/math/pack
   handoff looks like, how MOP templates are shaped, when replay pays off.
3. **The hardware, by reward.** Anything the docs get wrong or omit, the
   card corrects. A kernel that misreads a register hangs or fails
   validation and gets zero. A schedule that stalls the unpacker measures
   slow. Behavior the model cannot read anywhere is still learned because
   the reward is measured, not modeled. This is the channel a frontier
   model through an API never gets.
4. **Per-turn feedback, by text.** Between turns the harness returns parse
   and lint errors with line numbers, a validation diff summary (which
   faces or columns are wrong and how), device cycle counts, and stall
   attribution from the per-engine counters. This is what turns a failed
   sample into a lesson inside one trajectory.

Static checking matters more than it sounds. Every constraint that can be
checked before launch (unknown field, out-of-range immediate, NCRISC
emitting Tensix words, undefined label, L1 range overlap, semaphore waited
but never posted, CB pushed and popped unequal counts in static loops) is
a precise error message instead of a silent hang. That is the difference
between the model learning the rule in ten samples or a thousand.

## 3. The task is lowering, not just writing

Each task is an op plus a contract, and the same op appears under several
contracts so the model has to choose:

- **Precision tiers.** The same op at FP32-exact, BF16-round-trip, and
  loose (PCC 0.995) tolerances. FP32 sum of squares forces SFPU or FP32 Dst
  accumulation; loose tolerance permits HiFi2 or LoFi MVMUL. Reward is
  speed subject to the tier, with no bonus for extra precision, so the
  model learns to spend exactly what the contract requires.
- **Shape and scale.** Two, four, sixty-four tiles; one core or a grid.
  Small shapes make MOP setup a loss and explicit instructions a win, as
  the RMSNorm results already show. Large shapes flip it.
- **Engine choice as first-class.** Reductions on FPU via GAPOOL/MVMUL with
  a scaler, or on SFPU with shifts and transposes; elementwise on FPU with
  Dst accumulation or on SFPU with load macros. Both are in the test suite
  with numbers. The task prompt never says which; the reward does.
- **Hard limits as constraints, not preferences.** Text must fit the
  worker text region, L1 use must fit the map, Dst use must fit the mode.
  Violations are lint errors. Instruction count is reported but only used
  as a tie-breaker.
- **Fusion is optional scope.** Tasks can be composed ops (RMSNorm then
  quantize, SwiGLU with paired inputs) with a single reference function;
  no fuser is required because the model writes the fused kernel directly.
  Add these once single-op tasks are solid.

Make the reasoning visible: the prompt format asks for a short lowering
plan (engines, dtype path, fidelity, tiling, buffering) before the code, and
the feedback quotes the measured cycles back against that plan. The plan
is not rewarded directly, but it makes the trace useful as SFT data and
makes failures diagnosable.

## 4. What to build in the fork

Everything below is new top-level packages plus small runtime changes. Order
follows dependency. Each item has an acceptance test you can run before
moving on.

### 4.1 `bhasm/` — the language the model writes

- `grammar.md`: the frozen `bhasm v1` spec. One document, sections
  `params`, `l1`, `brisc`, `ncrisc`, `trisc0`, `trisc1`, `trisc2`.
  RISC-V lines with `v0..vN` virtual registers and labels; physical
  registers allowed. Tensix lines as `TTMVMUL addr_mode=2 dst=64`.
  Macro lines as `@cb_wait cb=0 tiles=2`. Raw escape `.word 0x...` and
  `.tt 0x..` so the action space includes bit patterns nobody has tried.
- `parse.py`: text to one `Asm` per role. Reuses `asm.py` unchanged for
  allocation, relaxation and encoding. Errors carry line numbers.
- `macros.py`: the frozen macro library. Each macro is a Python function
  that emits through the existing ttko helpers, with a typed signature and
  a docstring; the spec exporter reads these. Initial set: `cb_wait`,
  `cb_pop`, `cb_push`, `cb_reserve`, `sem_wait`, `sem_post`, `sem_get`,
  `stall`, `noc_read`, `noc_write`, `noc_multicast`, `noc_barrier`,
  `unpack_cfg`, `pack_cfg`, `mop_cfg`, `mop_run`, `replay_load`,
  `dst_publish`, `dst_acquire`, `profile_mark`, `counter_start/stop`.
  Coarse first; expose finer variants per family only where the frontier
  baseline is clearly suboptimal.
- `render.py`: `Asm` items back to text. Needed to turn every existing
  ttko kernel into training data and for the round-trip test.
- `lint.py`: the static checks listed in section 2, plus role capability
  checks and L1 overlap with the profiler and CB regions.
- `spec_export.py`: writes `spec/` from code. Include a version hash that
  is stamped into every trajectory and every prompt.
- Acceptance: render then parse every kernel in `tests/` and `examples/`
  and get identical instruction words; lint rejects a curated set of
  known-hanging kernels.

### 4.2 `spec/` — generated reference the model reads

`isa.md`, `registers.md`, `abi.md`, `macros.md`, `rules.md`,
`hardware_facts.md`. Target under 40k tokens total so it fits in the system
prompt with room for an eight-turn trajectory. Facts come from the results
markdown already in the repo and from `boop-docs/microbenching`; keep each
fact with its source file so it can be re-measured.

### 4.3 `tasks/` — the suite

- `Task` dataclass: name, family, numpy reference, input generator with
  seed, shape list, input/output dtypes, tolerance tier, launch ABI
  (buffers and params), core set, baseline kernel and measured baseline
  cycles, spec version.
- Families to start: elementwise unary and binary, row/col/all reductions
  (sum, max), softmax stages, RMSNorm, RoPE, argmax, conversions (BF16 to
  FP8, Q6 dequant), tilize/untilize/transpose, gather/scatter, matmul at
  the llama shapes, attention score and PV blocks. Around 30 families times
  tiers times shapes gives 200 to 300 tasks. Hold out 20% by family, not
  by shape, so held-out means unseen op.
- Baselines: the tuned kernels already in the repo where they exist,
  otherwise a plain correct template. Record baseline cycles on the same
  card the reward server uses.
- Acceptance: every baseline passes its own task at its tier, deterministic
  across three seeds.

### 4.4 `evalserver/` — the reward environment

- Long-lived process owning `Device(1)`; device stays open between
  launches (measured 0.30 ms per launch, 0.34 ms with readback, 0.70 ms on
  all 117 cores). On timeout: close, reboot, continue (measured 1.03 s
  end to end at a 0.5 s timeout). Consider a lighter path that only resets
  cores and re-pushes firmware if hang rates make the reboot dominant.
- `POST /eval {task, kernel_text}` returns JSON: stage reached (parse,
  lint, assemble, launch, validate, time), errors with lines, hang flag,
  max abs error, PCC, tier passed, device cycles from the wall clock and
  profiler, per-engine counters where the kernel used them, instruction
  counts per role, text bytes per role. Batch endpoint for a whole GRPO
  group.
- Anti-hacking built in: poison-fill the output region before launch,
  fresh random inputs for the validation run and again for the timing
  run, at least two shapes per task, reject nondeterministic output,
  time on the device clock only.
- Runs through the `tt-device-queue` Python client or CLI (the MCP server
  failed to connect this session; do not depend on it).
- Acceptance: 100 evaluations per second sustained on passing kernels;
  a deliberately hanging kernel costs about one second and the next
  evaluation is clean.

### 4.5 `feedback/` — result to text

Turns the JSON into the message the model sees next turn: error lines,
a diff summary that names faces, rows or columns and the error pattern,
cycles against baseline and against the model's own previous turn, and
stall attribution in plain words ("unpacker idle 62% of math interval").
This is also where a profiling term for the reward is computed later.

### 4.6 `datagen/` — data

- `synthetic.py`: parameterized ttko templates over the task families,
  rendered to `bhasm`, verified on the card, emitted as (task, plan,
  kernel) pairs. Thousands for free; teaches syntax and idioms.
- `corpus.py`: continued-pretraining text from this repo, `../tt-llk`,
  tt-metal LLK, the ISA docs, boop-docs and the disassembly corpus,
  stamped with the spec version.
- `distill.py`: agent loop running a frontier model with tools against
  `evalserver` on the task suite, keeping passing trajectories with their
  feedback. Rejection sampling by tier and speed.
- `trajectory.jsonl` format: system (spec hash), task prompt, turns with
  plan, kernel, feedback, reward.

### 4.7 `search/` — inference-time optimizer and expert iteration

A population loop per task: keep the top-k kernels with measured cycles,
prompt the model with them and their profiles and ask for something
faster, evaluate, replace. Best-of-N and mutation of macro parameters
(buffer depth, block sizes, fidelity) sit alongside model proposals. Cheap
because evaluation is sub-millisecond. Used three ways: to beat baselines
at inference time, to produce better SFT data than the model's single
samples (expert iteration), and to run the frontier baseline under equal
search budget so comparisons are fair. This is CUDA-L1's contrastive loop
and AlphaEvolve's outer loop; it is where results past the training
distribution come from.

### 4.8 `train/` — trainer glue

verl configs for SFT and multi-turn GRPO with vLLM rollouts; a reward
function that calls `evalserver`; the prompt builder that injects `spec/`;
TRLOO or Kevin's discounted turn-sum for advantages; an evaluation script
that reports Fast@1.0 and Fast@1.2 on the held-out set for the model, the
model plus search, and the frontier baseline through the same harness.

### 4.9 Runtime changes inside blackhole-py

- A standard task launch ABI: fixed param slots for buffer addresses and
  shapes, a fixed output region, reserved profiler and counter regions.
- Generalize the per-engine counters from `examples/matmul_peak_kernel`
  into macros any kernel can use.
- Poison-fill and region readback helpers on `RawHarness`.
- Optional: a faster hang recovery than a full reboot.

## 5. Reward

Per turn: 0 if any stage fails; otherwise `0.3 + min(cycles_baseline /
cycles_kernel, 3)`. Both Kevin and Dr. Kernel found either extreme
plateaus. Across turns use a discounted sum (gamma 0.4) or TRLOO. Add a
profiling term (ratio of the bottleneck engine's busy time) only after the
model passes most tasks; it stops "lazy" kernels that are correct and
barely faster. Instruction count is a tie-breaker with negligible weight.

## 6. Can it go past what it has seen, and past the frontier

Honest answer in three parts.

- **Past its training data: yes, within the action space.** RL with a
  measured reward keeps whatever is faster, whether or not anyone wrote it
  before. Kevin, CUDA-L1 and Dr. Kernel all report kernels that differ from
  anything in their SFT data, and CUDA-L1's largest wins were schedules
  humans had not tried. The mechanism is exploration plus ground truth,
  and the search loop in 4.7 multiplies it. Novelty is bounded by what the
  language lets it express, which is why `bhasm` keeps raw instruction and
  field escapes and why macros should be coarse only where you already
  know the answer.
- **Past the frontier on this hardware: plausible.** A frontier model has
  read the same public docs and never had a Blackhole in a loop. Its
  kernels here are first drafts. A 27B model with thousands of measured
  attempts per task family, the corrected facts, and inference-time
  search has an advantage no amount of general capability makes up for.
  Dr. Kernel-14B already beats Claude 4.5 Sonnet and GPT-5 on Fast@1.2
  for CUDA fusion tasks, where the frontier has far more prior exposure
  than it has here.
- **Past the frontier in general: no.** It will not reason better about
  a new problem. It will be a better Blackhole kernel engineer. Expect the
  gap to be largest on families with rich schedule choices (matmul,
  attention pieces, mixed FPU/SFPU reductions) and smallest on trivial
  elementwise ops where everyone's kernel is bandwidth-bound.

Novel hardware behavior, meaning tricks not in any doc, can only be found
if the reward can see them. Undocumented config bits, unusual addr_mode
combinations, replay and MOP interactions all become reachable through the
raw escapes, and the population search will try them at scale. Treat every
such discovery as a new fact to add to `hardware_facts.md`, so the next
training run starts from it. That loop, discovery to spec to training, is
what compounds.

## 7. Compute, assuming rented GPUs

Prices in September 2026 are roughly $2.5 to $3.5 per H100-hour and $4 to
$5.5 per B200-hour on dedicated clouds. One node is enough.

| Phase | Hardware | Time | Cost |
|---|---|---|---|
| Sections 4.1 to 4.6 | this machine, card 1 | 3 to 4 weeks | 0 |
| Pipeline bring-up, Qwen3-8B, LoRA SFT + GRPO | 1 x H100 | 30 to 50 h | ~$150 |
| Distillation and frontier baseline | frontier API | days, in parallel | $2k to $5k |
| Continued pretraining + SFT on 27B, ZeRO-3 | 8 x H100 | 4 to 8 h per run | $150 to $300 per run |
| Multi-turn GRPO on 27B | 8 x H100 or 8 x B200 | 1 to 2 weeks | $4k to $10k |
| Expert iteration rounds and eval | same node | a few days each | $1k to $2k per round |

Order of $10k to $20k over eight to ten weeks. Kevin ran 32B on 8 GPUs and
reported "multiple days" for 40 steps at 16k to 22k tokens per response.
The macro layer is what keeps responses in that range here. The reward
server is not on the critical path at any budget.

## 8. Model and stack

- Base: Qwen3.8-27B dense (Apache 2.0, August 2026); tt-blacksmith #689
  targeted the same for TT-Metal before it was closed. Bring up on
  Qwen3-8B-Base. Qwen3-Coder-30B-A3B if rollout cost dominates.
- verl for multi-turn GRPO with vLLM rollouts and FSDP; Unsloth for one-GPU
  LoRA experiments. Response cap 8k to 16k tokens; 8 tasks x 16 samples per
  step; 3 to 4 turns in training, 8 at eval; learning rate 1e-6.

## 9. Order of work

1. `bhasm` parse, render, macros, lint, spec export. Round-trip test green.
2. Task suite v0 with 30 to 50 tasks and baselines. Reward server on card 1
   at 100 evaluations per second.
3. Frontier model through the harness with and without search. This is the
   number to beat and the first distillation data.
4. Synthetic pairs, corpus, SFT on 8B on one rented GPU until it parses and
   passes simple tiers.
5. 27B SFT, then GRPO on a node. Track held-out Fast@1.2 every few steps.
6. Expert iteration: search with the trained model, harvest, retrain.
7. Point it at the real backlog in `PREFILL_8B_PLAN.md`.

## 10. Risks

- Macro granularity decides both cost and ceiling. Start coarse, open up
  per family with evidence.
- Reward hacking appears while the model is weak. The poison fill, fresh
  inputs, shape variation and determinism check cover the known patterns;
  watch for new ones in the first RL runs.
- Speed is harder than correctness. Kevin's mean was 1.10x over eager. The
  realistic milestone is beating the frontier on the held-out suite,
  then beating the repo's tuned kernels on a subset, then contributing to
  prefill.
- The spec must be right. A wrong fact in `hardware_facts.md` is learned
  as truth until RL contradicts it. Every fact needs a source and a
  re-measurement path.
