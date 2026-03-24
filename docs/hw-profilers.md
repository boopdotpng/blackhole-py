# Blackhole HW Profilers

With `PROFILE=1`, `blackhole-py` now captures all currently wired-up TRISC1 hardware performance counters exposed by the bundled `tt-metal-deps` profiler integration.

Each counter is reported as:

- `counter_value`: the observed event/busy count (cycles or events depending on counter)
- `ref_cnt`: the reference cycle count for that sampling window
- `util_pct`: `counter_value / ref_cnt * 100`

Total counters captured: 94

All counters are measured on **TRISC1 only** (the MATH thread). The measurement window spans the entire user kernel execution — `perf_counter_start()` fires before the kernel call and `perf_counter_stop_and_capture()` fires after it returns. The compile flag `PROFILE_PERF_COUNTERS=0x3f` enables all 6 counter banks (FPU, PACK, UNPACK, L1_0, L1_1, INSTRN).

Thread indices used throughout: **T0 = UNPACK, T1 = MATH, T2 = PACK**.

---

## FPU (3)

Measures compute unit utilization. `util_pct` gives the fraction of the measurement window the unit was actively executing instructions.

| Counter | Description |
|---------|-------------|
| `FPU` | Cycles the Matrix Unit (FPU) was executing instructions (matrix multiply, element-wise ops on low-precision data) |
| `SFPU` | Cycles the Vector Unit (SFPU) was executing instructions (32-lane SIMD on FP32/INT32) |
| `MATH` | Cycles that *either* FPU or SFPU was active (logical OR of the above two) |

**Key metric — FPU Execution Efficiency:** `FPU / FPU_INSTRN_AVAILABLE_1` — ratio of actual FPU execution to cycles an FPU instruction was queued. Distinguishes compute-bound (high) from memory-bound (low) workloads.

## UNPACK (11)

Monitors the unpacker pipeline — data movement from L1 into SrcA/SrcB register files and handoff to math.

| Counter | Description |
|---------|-------------|
| `DATA_HAZARD_STALLS_MOVD2A` | Cycles stalled due to data hazards on MOVD2A (move-data-to-register-A) instructions — write-after-read / write-after-write register file conflicts |
| `MATH_INSTRN_STARTED` | Number of math instructions that began execution (**event count**, not cycles) |
| `MATH_INSTRN_AVAILABLE` | Cycles a math instruction was waiting in the buffer, ready to start but not yet issued |
| `SRCB_WRITE_AVAILABLE` | Cycles the SrcB register file write port was available (not blocked by backpressure from math) |
| `SRCA_WRITE_AVAILABLE` | Cycles the SrcA register file write port was available |
| `UNPACK0_BUSY_THREAD0` | Cycles unpacker 0 was busy on T0 (UNPACK thread) |
| `UNPACK1_BUSY_THREAD0` | Cycles unpacker 1 was busy on T0 |
| `UNPACK0_BUSY_THREAD1` | Cycles unpacker 0 was busy on T1 (MATH thread) |
| `UNPACK1_BUSY_THREAD1` | Cycles unpacker 1 was busy on T1 |
| `SRCB_WRITE` | Actual SrcB write completions (**event count** — number of data transfers written into SrcB) |
| `SRCA_WRITE` | Actual SrcA write completions (**event count** — number of data transfers written into SrcA) |

**Key metrics:**
- **Unpacker Write Efficiency:** `SRCA_WRITE / UNPACK0_BUSY_THREAD0` — fraction of busy time spent actually writing. Low ratio = unpacker busy but stalled (L1 contention or math backpressure).
- **Math Pipeline Utilization:** `MATH_INSTRN_STARTED / MATH_INSTRN_AVAILABLE` — close to 1.0 = healthy pipeline flow; low = instructions queued but pipeline stalled.
- **Backpressure Detection:** `SRCA_WRITE_AVAILABLE / UNPACK0_BUSY_THREAD0` — low ratio = unpacker busy but can't write because math hasn't consumed SrcA yet.

## PACK (3)

Monitors the packer pipeline — data movement from Dest register file back to L1.

| Counter | Description |
|---------|-------------|
| `PACKER_DEST_READ_AVAILABLE` | Cycles destination register data was available for the packer to read (math has produced output and placed it in Dest) |
| `PACKER_BUSY` | Cycles the packer was actively working (moving data from Dest to L1) |
| `AVAILABLE_MATH` | Cycles math results were available for packing |

**Key metrics:**
- **Packer Efficiency:** `PACKER_DEST_READ_AVAILABLE / PACKER_BUSY` — close to 1.0 = math is feeding the packer well; low = packer waiting for math output (math is the bottleneck). Only valid with HW dvalid-based synchronization, not STALLWAIT mode.
- **Math-to-Pack Handoff:** `AVAILABLE_MATH / PACKER_BUSY` — low ratio = packer busy but math output isn't ready (math bottleneck).

## L1 bank 0 (8)

NOC Ring 0 traffic and L1 memory arbitration. Uses mux bit 4 = 0 on the `PERF_CNT_MUX_CTRL` register.

| Counter | Description |
|---------|-------------|
| `NOC_RING0_INCOMING_1` | Cycles with incoming read/write transactions on NOC ring 0, channel 1, arriving at this tile |
| `NOC_RING0_INCOMING_0` | Cycles with incoming transactions on NOC ring 0, channel 0 |
| `NOC_RING0_OUTGOING_1` | Cycles with outgoing transactions on NOC ring 0, channel 1 |
| `NOC_RING0_OUTGOING_0` | Cycles with outgoing transactions on NOC ring 0, channel 0 |
| `L1_ARB_TDMA_BUNDLE_1` | Cycles the L1 arbiter granted access for TDMA bundle 1 (DMA engine had L1 bandwidth) |
| `L1_ARB_TDMA_BUNDLE_0` | Cycles the L1 arbiter granted access for TDMA bundle 0 |
| `L1_ARB_UNPACKER` | Cycles the L1 arbiter granted access for the unpacker (unpacker won arbitration for L1 bandwidth) |
| `L1_NO_ARB_UNPACKER` | Cycles the unpacker accessed L1 via the no-arbitration (bypass) path |

## L1 bank 1 (8)

NOC Ring 1 traffic and TDMA arbitration. Uses mux bit 4 = 1 on the `PERF_CNT_MUX_CTRL` register.

| Counter | Description |
|---------|-------------|
| `NOC_RING1_INCOMING_1` | Cycles with incoming transactions on NOC ring 1, channel 1 |
| `NOC_RING1_INCOMING_0` | Cycles with incoming transactions on NOC ring 1, channel 0 |
| `NOC_RING1_OUTGOING_1` | Cycles with outgoing transactions on NOC ring 1, channel 1 |
| `NOC_RING1_OUTGOING_0` | Cycles with outgoing transactions on NOC ring 1, channel 0 |
| `TDMA_BUNDLE_1_ARB` | Cycles TDMA bundle 1 competed for / held L1 access from the ring 1 side |
| `TDMA_BUNDLE_0_ARB` | Cycles TDMA bundle 0 competed for / held L1 access |
| `TDMA_EXT_UNPACK_9_10` | Cycles the TDMA extended unpacker interface was active (channels 9 and 10) |
| `TDMA_PACKER_2_WR` | Cycles the TDMA packer 2 write interface was active (writing to L1) |

## INSTRN (61)

Instruction-level diagnostics from the coprocessor instruction issue unit. All `_0`, `_1`, `_2` suffixes refer to coprocessor threads: **0 = T0 (UNPACK), 1 = T1 (MATH), 2 = T2 (PACK)**.

### Instruction Availability (24 counters)

Cycles an instruction of the given type was in the thread's instruction buffer, ready to issue. High counts mean that instruction type was frequently queued; low counts suggest the thread was idle or doing other work.

| Counter | Description |
|---------|-------------|
| `CFG_INSTRN_AVAILABLE_[0-2]` | Cycles a CFG (configuration) instruction was available per thread |
| `SYNC_INSTRN_AVAILABLE_[0-2]` | Cycles a SYNC instruction was available per thread |
| `THCON_INSTRN_AVAILABLE_[0-2]` | Cycles a THCON (scalar unit) instruction was available per thread |
| `XSEARCH_INSTRN_AVAILABLE_[0-2]` | Cycles an XSEARCH instruction was available per thread |
| `MOVE_INSTRN_AVAILABLE_[0-2]` | Cycles a MOVE (bulk L1 DMA / mover) instruction was available per thread |
| `FPU_INSTRN_AVAILABLE_[0-2]` | Cycles an FPU/SFPU instruction was available per thread |
| `UNPACK_INSTRN_AVAILABLE_[0-2]` | Cycles an UNPACK instruction was available per thread |
| `PACK_INSTRN_AVAILABLE_[0-2]` | Cycles a PACK instruction was available per thread |

### Thread Stalls (3 counters)

| Counter | Description |
|---------|-------------|
| `THREAD_STALLS_[0-2]` | Total cycles the coprocessor thread was stalled (unable to issue any instruction) |

### Wait Reasons (31 counters)

These identify *why* a thread was waiting — the specific resource or condition it was blocked on.

| Counter | Description |
|---------|-------------|
| `WAITING_FOR_SRCA_CLEAR` | Cycles waiting for SrcA register file to be cleared (math hasn't consumed the previous data yet) |
| `WAITING_FOR_SRCB_CLEAR` | Cycles waiting for SrcB register file to be cleared |
| `WAITING_FOR_SRCA_VALID` | Cycles waiting for SrcA data to become valid (unpacker hasn't filled it yet) |
| `WAITING_FOR_SRCB_VALID` | Cycles waiting for SrcB data to become valid |
| `WAITING_FOR_THCON_IDLE_[0-2]` | Cycles thread N was waiting for the ThCon (scalar unit) to be idle |
| `WAITING_FOR_UNPACK_IDLE_[0-2]` | Cycles thread N was waiting for unpackers to finish |
| `WAITING_FOR_PACK_IDLE_[0-2]` | Cycles thread N was waiting for packers to finish |
| `WAITING_FOR_MATH_IDLE_[0-2]` | Cycles thread N was waiting for math (FPU/SFPU) to finish |
| `WAITING_FOR_NONZERO_SEM_[0-2]` | Cycles thread N was blocked on `semaphore_wait` (waiting for a semaphore value to become > 0) |
| `WAITING_FOR_NONFULL_SEM_[0-2]` | Cycles thread N was blocked on semaphore post overflow check (waiting for semaphore value < max) |
| `WAITING_FOR_MOVE_IDLE_[0-2]` | Cycles thread N was waiting for the mover (bulk L1 DMA engine) to be idle |
| `WAITING_FOR_MMIO_IDLE_[0-2]` | Cycles thread N was waiting for MMIO to be idle |
| `WAITING_FOR_SFPU_IDLE_[0-2]` | Cycles thread N was waiting for the SFPU (vector unit) to be idle |

### Thread Instruction Counts (3 counters)

| Counter | Description |
|---------|-------------|
| `THREAD_INSTRUCTIONS_[0-2]` | Total coprocessor instructions executed by thread N (**event count**, not cycles) |
