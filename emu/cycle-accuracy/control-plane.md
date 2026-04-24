# Control plane — cycle timing

Baby RISC-V cores, Tensix instruction frontend (FIFO / MOP / Replay / Wait Gate),
Sync unit (STALLWAIT / SEMWAIT / mutexes), Configuration unit, and the current
state of the emulator.

All cycle counts are in AICLK cycles (1.35 GHz) unless noted.

---

## 1. Current emulator state

**No cycle counts are enforced.** The only timing state in `blackhole-py/emu/`:

- `Device._clock` (`device.py:292, 443`) — integer, advanced once per outer
  `_step_loop` iteration. Mirrored to `WALL_CLOCK_L/H` MMIO at `device.py:445`.
- `WaitGate._one_cycle_hold` (`tensix/frontend.py:256, 267, 276, 287, 291-293`) —
  bool, consumed on next `is_blocking()` call. This is the one latency hook that
  actually fires.
- `MOPExpander.next()` (`tensix/frontend.py:54-55`) returns `None` once after
  expansion ends to model the 1-cycle transition penalty.

Capacity constants that imply (but do not implement) timing:

- `InstructionFIFO.CAPACITY = 32` (`frontend.py:14`)
- `_PCBufFIFO.CAPACITY = 16` (`coprocessor.py:29`)

Every other unit completes in the same outer step as it is issued: NoC fires
synchronously (`noc.py:159`), Mover transfers synchronously (`mover.py` sets C9
clear), FPU / SFPU / Packer / Unpacker all return in-cycle.

Comments that name cycle counts but don't enforce them (selected):

- `math.py:308` — `# FP32 FMA arithmetic (MAD sub-unit, 2-cycle)`
- `specs/mutexes.md:213` — "For a cycle-accurate emulator, `exec_atgetm` should be
  called each cycle while the thread's instruction pointer is parked."
- `specs/additional-scalar-unit-instructions.md:53, 100` — "3 cycles / 4 cycles" for
  ADDDMAREG / MULDMAREG.
- `specs/specialty-fpu-operations.md:81, 146, 288` — IPC/latency for GAPOOL, DOTPV,
  SHIFTXB hazard.
- `specs/config-sync-instructions.md:88-89, 158, 276` — WRCFG = 2 cyc, RDCFG ≥3,
  STREAMWRCFG ≥5.

### Hook points for inserting cycle models

| Subunit | Function | File:line |
|---|---|---|
| RV core step | `Core.step()` | `core.py:36` |
| Tensix thread step | `TensixCoprocessor._step_thread(thread)` | `coprocessor.py:119` |
| FPU / SFPU / all Tensix dispatch | `TensixCoprocessor._dispatch(thread, word)` | `coprocessor.py:127` |
| MOP transition penalty | `MOPExpander.next()` | `frontend.py:48-55` |
| Wait-gate one-cycle hold | `WaitGate.is_blocking()` | `frontend.py:289-293` |
| NoC fire | `NOC._fire(buf_idx)` | `noc.py:159` |
| Mover | `Mover.transfer(...)` | `mover.py:35` |
| FIFO push backpressure | `_InstrnHandler.write32()` | `coprocessor.py:412` |

### Timebase recommendation

Keep the single global `Device._clock`. Give each backend unit a `busy_until: int`
threshold measured in `_clock` units; dispatch reads it to decide whether to stall the
thread. This fits the existing serialized step loop and needs no rewrite.

---

## 2. Baby RISC-V cores (BRISC, NCRISC, TRISC0-2, ERISC)

**Clock**: all RV cores run at **1.35 GHz**, one instruction/cycle target.
Source: `BlackholeA0/TensixTile/BabyRISCV/README.md:3`:
> "Each RISCV core is intended to execute one RISCV instruction per cycle, running
> at a clock speed of 1.35 GHz."

Same clock for ERISC: `EthernetTile/BabyRISCV/README.md:3`.

### Pipeline

Source: `BabyRISCV/README.md:17-29`.

> "Every instruction spends at least one cycle in EX1, and then: Memory load / store /
> atomic / fence instructions spend at least one cycle in the Load/Store Unit; Integer
> multiply and floating-point arithmetic instructions spend one cycle in EX2; Other
> instructions proceed directly to the Retire Unit."

- EX1 → (optional EX2 for mul/FP) → Retire Unit (8-entry retire-order queue).
- TRISC2 only gets EX3 for vector ops.
- Store queue: **4 entries** (`MemoryOrdering.md:9`).
- Retire-order queue: **8 entries** (`MemoryOrdering.md:9`).

### Instruction latencies

| Class | Latency | Source |
|---|---|---|
| RV32I ALU, Zba/Zbb | 1 cycle (forwarded next cycle) | `README.md:49` |
| `mul`, `mulh`, `mulhsu`, `mulhu` | 2 cycles (EX1+EX2) | `README.md:59` |
| `div`, `divu`, `rem`, `remu` | 2 cyc if divisor 0/1 or `INT_MIN/-1`; **6–33 cyc** otherwise (blocks EX1) | `README.md:51-54` |
| Mispredicted branch | **4-cycle pipeline bubble** (5 cyc end-to-end + I-cache miss) | `README.md:55` |
| FP arith (`fadd.s`, `fmul.s`, `fmadd.s`) | 2 cycles (EX1+EX2, structural) | `README.md` (structural) |

WH for comparison: 2-cycle branch bubble (`WormholeB0/.../README.md:50`).

### Load latency tiers (from the RV core's perspective)

Source: `BabyRISCV/README.md:75-83`.

| Address range | Latency |
|---|---|
| Local data RAM / L1 with L0-cache hit | **2 cycles** |
| Mailboxes, PCBufs, Manual TTSync, Tensix semaphores | **≥ 3 cycles** (more if FIFO empty) |
| Tensix GPRs, Tensix backend config, TDMA-RISC | **≥ 4 cycles** (more if Auto-TTSync stalls) |
| Tile ctrl/debug/status, PIC, NoC0/NoC1 config, NoC overlay | **≥ 7 cycles** |
| Local data RAM via slow path (`0xFFB1_4000–DFFF`) | **≥ 8 cycles** |
| L1 with L0-cache miss | **≥ 8 cycles** (more for port/bank conflicts) |
| L1 with atomic instruction | **≥ 12 cycles** |

> "A latency of N cycles means that N − 1 independent instructions need to follow the
> load if the latency is to be entirely hidden." (`README.md:73`)

### Store throughput to L1

Source: `BabyRISCV/README.md:85`.

> "...if [the store queue can coalesce] entire aligned 128-bit blocks, the constituent
> stores have a throughput of one store every cycle, otherwise the throughput is one
> coalesced store every five cycles."

### L0 data cache

- **64 bytes total** (4 lines × 16 B). Hit → 2 cyc, miss → ≥ 8 cyc.
  Source: `README.md:140`.
- ~0.8% chance per cache-hit access to flush whole L0 unless
  `cfg0.DisLowCachePeriodicFlush` set. (`MemoryOrdering.md:59`)
- `fence` / atomic unconditionally flushes L0.

### `.ttinsn` fusion (TRISC0/1/2 only)

Source: `PushTensixInstruction.md:19`.
> "sequences of up to four adjacent `.ttinsn` instructions can be fused together ... and
> executed in a single cycle (this allows four Tensix instructions to be queued up per
> thread per cycle, but the maximum dequeue rate is only one instruction per thread per
> cycle)."

### ncrisc.cc annotation

`tt-metal/tt_metal/hw/firmware/src/tt-1xx/ncrisc.cc:199`:
> "This loop unrolls to 54 instructions, taking 110 cycles (assuming all branches are
> mispredicted)."

### Needs microbenching (RV core)

1. **ALU forwarding chain latency.** Docs confirm 1-cycle throughput intent but no
   explicit BH back-to-back latency number. Bench: chain 100 dependent `addi` and
   measure `mcycle`.
2. **`fence` exact cost.** Documented as "drain store queue + drain in-flight loads +
   flush L0" with no fixed number. Bench: `fence` with (a) empty queue, (b) 4 full
   store entries, (c) an L1 miss in flight.
3. **`csrr mcycle` cost in isolation.** No per-CSR cycle given; docs say it causes
   full frontend drain (default `DisCsrSync=0`). Bench: `csrr t0, mcycle; csrr t1,
   mcycle`; compute `t1 - t0 - 1`. Repeat with `DisCsrSync=1`.
4. **Wall-clock MMIO read (`0xFFB1_21F0`) exact cost.** Table says ≥ 7 cyc, no upper
   bound.
5. **L1 cache tag search accelerator latency.** `L1CacheTagSearchAccel.md` gives zero
   timing. Bench: trigger a cache miss on the configured address with
   `Search_Enable=1` and time it vs. a normal L1 miss.
6. **Mailbox / PCBuf round-trip latency** in the non-empty case. Bench: pre-fill,
   then time a pop.
7. **INSTRN_BUF push stall onset.** FIFO "soft" full at 28 vs. hard full at 32 (see
   frontend section). Bench from BRISC writing to `INSTRN_BUF_BASE`.
8. **Branch-predictor characterization.** 4-cycle penalty documented; predictor
   policy / miss rate unknown. Bench forward vs. backward branches, compare with
   `cfg0.DisBp=1`.
9. **FP arithmetic latency confirmation** (chain dependent `fadd.s`).
10. **Atomic (Zaamo) cycle breakdown.** "≥ 12 cyc" is only a bound.
11. **Store-to-L1 coalescing window.** `cfg0.StMergeTimer` initialized to 16 — sweep.

---

## 3. Tensix frontend (FIFO / MOP / Replay / Wait Gate)

### Instruction FIFO

**Capacity = 32 entries/thread**, but **effective push threshold = 28** due to Auto
TTSync tracking (applies even when Auto TTSync is off).

Source: `PushTensixInstruction.md:15`:
> "The very first FIFO has a capacity of 32 instructions, but this capacity can only be
> hit by starting with 28 instructions and pushing four instructions in a single cycle
> via `.ttinsn` fusion. Once the FIFO contains more than 28 instructions, it needs to
> drop back down to 28 instructions before it'll accept any more."

Backpressure: hardware stalls the RV core transparently
(`clauses/instruction-push.md § IPUSH.FIFO.FULL_REJECTS_PUSH`).

Push rate: up to **4 pushes/cycle** via `.ttinsn` fusion; dequeue rate: **1/cycle/thread**.

### MOP expander

Source: `specs/mop-and-replay-expanders.md` (MOP Performance table):

| Mode | Ingest | Emit |
|---|---|---|
| Pass-through (non-MOP) | 1/cycle | 1/cycle |
| During expansion | 0 (blocked) | 1/cycle |
| After expansion ends | 0 | 0 (1-cycle transition penalty) |

Max expansion: Template 0 up to 32,639 instructions; Template 1 OuterCount≤127 (or
255 via HW bug), InnerCount≤127 (or 254 with LoopOp1).

Hardware bug to replicate: when `OuterCount==1 AND IsNop(StartOp) AND InnerCount==0 AND
NOT IsNop(EndOp0)`, OuterCount += 128 → 129
(`clauses/mop-and-replay-expanders.md § MOP.T1.HW_BUG_OUTER_COUNT`).

### Replay expander

| Mode | Ingest | Emit |
|---|---|---|
| Pass-through | 1/cycle | 1/cycle |
| Playback (`Load=0`) | 0 (stalls) | 1/cycle from buffer |
| Record+Execute (`Load=1, Exec=1`) | 1/cycle | 1/cycle |
| Record only | 1/cycle | 0 |

**No transition penalty** (unlike MOP). Buffer: 32-slot × 32-bit, no CPU address.
`REPLAY len=0` replays 64 instructions (buffer wraps twice).

### Thread arbitration

Three frontend pipelines are **fully independent**. Contention happens only at shared
backend units (Sync, Config, Vector). The only published arbitration rule: **round-robin
mutex release** — `ATRELM.md:48`:
> "If a mutex is released by thread `i`, and both of the other threads are trying to
> acquire it using ATGETM, then thread `(i + 1) % 3` is always chosen."

### Wait Gate

**Per-thread**, independent. Three waits it can latch: STALLWAIT / SEMWAIT / STREAMWAIT.

One-cycle hold (quoted identically in STALLWAIT.md:30, SEMWAIT.md:31, STREAMWAIT.md:38):
> "There is a one cycle lag between the condition(s) being met and the block mask being
> removed — in particular this means that the instruction immediately after STALLWAIT
> will always be subject to the block mask for at least one cycle, even if the
> condition(s) are met immediately."

Already modeled in `frontend.py:291-293` via `_one_cycle_hold`.

### Per-unit accept rates (from ISA docs)

| Unit | Accept rate | Source |
|---|---|---|
| Sync (ATGETM/ATRELM different mutexes) | up to 3/cycle | `SyncUnit.md:6` |
| Sync (SEMINIT/POST/GET, STALLWAIT, SEMWAIT, STREAMWAIT, RV sem write) | 1/cycle shared | `SyncUnit.md:7-8` |
| Config (SETC16 — ThreadConfig group) | 3/cycle (1/thread) | `ConfigurationUnit.md` |
| Config (WRCFG/RDCFG/RMWCIB/CFGSHIFTMASK/STREAMWRCFG — Config group) | 1/cycle shared | `ConfigurationUnit.md:19` |
| Matrix Unit (FPU) | 1/cycle regardless of thread | `specs/tensix-coprocessor-pipeline.md` |
| Vector Unit (SFPU) | 1/cycle | `VectorUnit.md` |
| Unpackers, Packers, Mover/TDMA, ThCon | not numerically specified | — |

### Needs microbenching (frontend)

1. **FIFO soft-vs-hard full threshold (28 vs. 32).** Emulator models hard = 32; need to
   verify and implement the 28 soft limit.
2. **Thread-vs-thread arbitration at shared backend units.** If T0 and T1 both issue a
   Config instruction in the same cycle, which wins? ISA mentions starvation but
   doesn't publish priority.
3. **MOP expansion startup latency.** Does first emission happen on the cycle MOP is
   seen, or one cycle later?
4. **STREAMWAIT re-evaluation latency** vs. STALLWAIT / SEMWAIT (stream-reg read may
   add extra pipeline delay).
5. **Replay playback drain vs. MOP emission** — interaction when MOP emits a REPLAY
   as its loop body while a prior REPLAY is still playing back.
6. **Config-unit backpressure Wait-Gate hold** — the stall visible at the Wait Gate
   when a Config instruction can't enter the pipeline.

---

## 4. Sync unit

All sync ops: **1-cycle latency**, shared-group throughput as above.
Source: `SyncUnit.md:6-10`.

### STALLWAIT / SEMWAIT / STREAMWAIT

- 1-cycle dispatch + 1-cycle lag before block mask lifts (always, even if condition
  met immediately) — quoted above.
- Per-thread independent gate.
- Multi-condition masks: "only forgotten once all of the conditions are simultaneously
  met" (`STALLWAIT.md`).
- `SEMWAIT`, `STALLWAIT`, `STREAMWAIT` themselves are blocked by **any** block bit
  (B0–B8).

### SEMINIT / SEMPOST / SEMGET

**1-cycle**, atomic (`SEMPOST.md`, `SEMINIT.md`, `SEMGET.md`).

### ATGETM / ATRELM

Uncontended: **1 cycle**. Contended: **0, 1, or 2 extra cycles** (non-deterministic
"maybe wait" in the functional pseudocode).

`ATGETM.md:22-45`:
> "// Maybe wait for a cycle or two. These waits can happen if other threads are also
> trying to either acquire or release the mutex in question. if (maybe) wait; if
> (maybe) wait;"

`ATGETM` blocks at the Wait Gate if another thread holds the mutex (bounded by when
that thread releases).

### STREAMWRCFG

Sits in the Config unit but worth noting here for cross-reference:
> "This instruction requires at least five cycles to execute, with additional cycles at
> the start if there is contention for NoC Overlay reads. Assuming no contention, it is
> fully pipelined, so a STREAMWRCFG instruction can be started every cycle." (`STREAMWRCFG.md:31`)

Hardware bug: during the "≥1 cycle prepare" phase, other Config instructions from the
same thread can re-order ahead of the pending STREAMWRCFG.

### SEMPOST → SETDVALID ordering

Only guidance is a `STALLWAIT B1` between them (`SEMPOST.md:29-31`). No cycle-precise
window is published.

### Needs microbenching (sync)

1. **SEMPOST → SEMWAIT cross-thread propagation cycles.** T0 SEMPOST → T1's first
   post-SEMWAIT instruction: how many cycles?
2. **ATGETM / ATRELM exact contention penalty.** The 0/1/2 in the spec is
   non-deterministic; measure the real distribution.
3. **STREAMWAIT stream-register poll-to-unblock latency.** Compare C0 (phase) vs. C1
   (msg count) conditions.
4. **Multi-condition STALLWAIT release ordering** (e.g., C3|C4 = packer + FPU) —
   simultaneous-clear vs. per-condition evaluation delay.
5. **Min cycle gap between SETDVALID and SEMPOST** for correctness (math → pack
   handoff).

---

## 5. Configuration unit

All from `ConfigurationUnit.md` table (in order of appearance):

| Instruction | Latency | IPC | Group |
|---|---|---|---|
| `SETC16` | 1 cyc | **3** (1 per thread) | ThreadConfig |
| `WRCFG` | 2 cyc | 1 | Config |
| `RMWCIB` (1/2/4-byte variants all same) | 1 cyc | 1 | Config |
| `CFGSHIFTMASK` | 2 cyc | **0.5** (not pipelined) | Config |
| `RDCFG` | ≥ 2 cyc | 1 | Config |
| `STREAMWRCFG` | ≥ 5 cyc | 1 | Config |

"Config group" sustained throughput: **1/cycle globally** across all threads
(`ConfigurationUnit.md:19`). CFGSHIFTMASK halves this to 0.5/cycle.

### WRCFG

`WRCFG.md:35`:
> "This instruction requires two cycles to execute, but is fully pipelined, so a WRCFG
> instruction can be started every cycle."

`WRCFG.md:39`:
> "Software must ensure that the instruction immediately after WRCFG is not trying to
> consume the configuration written by the WRCFG instruction. A NOP instruction can be
> inserted to ensure this."

LLK confirmation (`tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB_matmul.h:68`):
`// Added to ensure WRCFG instruction has finished, since it takes 2 cycles.`

### RDCFG

`RDCFG.md:30-33`:
> "...at least two cycles, and then additional cycles if there is contention for GPR
> writes. ... In _most_ cases, this applies to the one instruction after RDCFG, but it
> can apply to more than one instruction if there is contention."

### CFGSHIFTMASK

2 cycles, **not pipelined** — IPC = 0.5. Same-group consecutive CFGSHIFTMASK is safe
because the Config pipeline inserts the idle cycle automatically; the 1-NOP rule only
applies if a non-Config-group consumer follows.
Confirmed in `tt-metal/.../llk_unpack_AB_custom_mm.h:64`:
`// This nop is required in post0 as CFGSHIFTMASK is a 2 cycle instruction`.

### SFPCONFIG

Actually executes on the **Vector Unit**, not the Config Unit — gated by `STALL_SFPU`
(B8), not `STALL_CFG` (B7).

| Mode | Latency |
|---|---|
| LReg-write (VD 11–14) | 1 cyc |
| LaneConfig / LoadMacroConfig (VD 0–10, 15) | ≤ 2 cyc |

`SFPCONFIG.md:139`:
> "If SFPCONFIG is used to change the value of `LaneConfig.DISABLE_BACKDOOR_LOAD`, the
> next Vector Unit (SFPU) instruction might observe either the old value or the new
> value. ... software should insert an SFPNOP instruction immediately after."

### C12 (Config-pipeline occupancy) and STALL_CFG (B7)

- C12: "Any thread has an instruction in any stage of the Configuration Unit pipeline."
- B7 (`STALL_CFG = 0x80`): "Block thread from starting new Configuration Unit
  instructions."

Canonical idiom in LLK: `TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON)` — stall
Config until ThCon idle (waits for prior `LOADREG`/`SETDMAREG` GPR write to commit
before issuing WRCFG). Seen in `cpack_common.h:183`, `llk_unpack_AB_matmul.h:65`, etc.

### STATE_ID ping-pong

`WRCFG.md:22`: "`uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;`" —
the config bank is chosen at WRCFG's stage −1 (GPR read). **No separate
commit-to-consumer latency number is published** beyond the 1-NOP rule.

### Needs microbenching (config)

1. **RDCFG contention ceiling.** "≥ 2 cyc + more with GPR-write contention" has no
   upper bound.
2. **WRCFG → consumer-in-other-unit minimum NOP count.** LLK comments suggest 1 NOP
   only when a SETDMAREG already consumed the cycle before; confirm in isolation.
3. **SFPCONFIG LaneConfig exact cycles** (1 or 2 — spec says ≤ 2).
4. **STATE_ID context-switch latency to Unpack/Pack/FPU consumers.** Not numerically
   documented.
5. **Cross-thread Config-write starvation threshold.** How many consecutive T0 WRCFGs
   before T1's RV access sees an N-cycle stall?
6. **STREAMWRCFG no-contention minimum** (spec only says ≥ 5).
