# Data path — cycle timing

Unpacker(s), Packer(s), and TDMA / XMOV / Mover / ThCon. The L1 ↔ SrcA/SrcB ↔ Dst ↔ L1
path plus the scalar unit that manipulates GPRs and fires memory ops.

All cycle counts are in AICLK cycles (1.35 GHz) unless noted.

---

## 1. Unpacker

### L1 read bandwidth — three speeds

Source: `WormholeB0/TensixTile/TensixCoprocessor/UNPACR_Regular.md:574-598`
(mirrored in `blackhole-py/emu/specs/unpack-data-path.md:1313-1337`):

> "Each unpacker can be fetching from L1 at one of three possible speeds:
> x1 speed: Up to 16 bytes per cycle from L1.
> x2 speed: Up to 32 bytes per cycle from L1.
> x4 speed: Up to 64 bytes per cycle from L1."

Controlled by `Throttle_mode` field (0=x1, 1=x2, 2=x4). BH LLK default
(`cunpack_common.h:330`): `throttle_mode = 2` (x4).

### Initial address-computation (setup) latency

`UNPACR_Regular.md:574`:
> "An UNPACR instruction spends **at least two cycles** calculating the initial input
> address: uncompressed data requires **exactly two cycles**, whereas compressed data
> requires more. For the duration of these cycles, the issuing thread cannot start its
> next instruction, **nor can any other thread start an UNPACR instruction**."

This is the cross-thread backpressure bound for UNPACR. No format-specific
differentiation during setup — uniformly 2 cycles for uncompressed, >2 for compressed.

### UNPACR_NOP (Nop mode 0x2)

**1 cycle** — the only absolute single-number cycle count in the unpacker docs.
Source: `unpack-data-path.md:922` / `UNPACR_NOP_Nop.md`.

### Forced speed by mode/format

| Mode or format | Forced speed |
|---|---|
| Compressed (`!IsUncompressed`) | x1 |
| `DiscontiguousInputRows` (tilize) | x4 |
| `UpsampleZeroes >= 3` | x1 |
| `BFP2` or `BFP2a` | x1 |
| `UpsampleZeroes == 1` | x1 or x2 |
| `UnpackToDst` + (BFP4 or BFP4a) | x1 or x2 |
| all others | user choice via `Throttle_mode` |

### Dual-unpacker interference table

(Unp0 favored when both want ≥ x2.) `UNPACR_Regular.md:582-587`:

| Unp1 wants \ Unp0 wants | x1 | x2 | x4 |
|---|---|---|---|
| x1 | 0:x1, 1:x1 | 0:x2, 1:x1 | 0:x4, 1:x1 |
| x2 | 0:x1, 1:x2 | 0:x1, 1:x1 ⚠ | 0:x2, 1:x1 ⚠ |
| x4 | 0:x1, 1:x4 | 0:x1, 1:x2 ⚠ | 0:x2, 1:x2 ⚠ |

⚠ = degraded from requested.

### Bytes per datum (drives drain time at a given speed)

From `DatumSizeBytes` switch in `UNPACR_Regular.md:89-96`:

| Format | B/datum |
|---|---|
| BFP2, BFP2a | 0.25 |
| BFP4, BFP4a | 0.5 |
| BFP8, BFP8a, FP8, INT8 | 1 |
| FP16, BF16, INT16 | 2 |
| FP32, TF32, INT32 | 4 |

Drain time for a 32×32 face (1024 datums) at x4 (64 B/cycle), setup cycles excluded:

| Format | Bytes | Cycles at x4 |
|---|---|---|
| FP32/TF32/INT32 | 4096 | 64 |
| FP16/BF16/INT16 | 2048 | 32 |
| BFP8/INT8/FP8 | 1024 (+64 exp for BFP) | ~17 |
| BFP4 | 512 (+64 exp) | ~9 |
| BFP2 | 256 (+64 exp) | forced x1 → 16 |

Setup adds 2 cycles for all formats; more for compressed.

### Bank ownership / SETDVALID

`UNPACR_NOP_SETDVALID.md`:
> "This instruction does not automatically wait at the Wait Gate to ensure that
> AllowedClient == SrcClient::Unpackers, so unless sequenced after an UNPACR or
> UNPACR_NOP (ZEROSRC) instruction which performs the desired wait, software may wish
> to use STALLWAIT (with block bit B3 and condition code C10 or C11) prior to
> UNPACR_NOP."

No cycle count for the flip itself.

### Pipelined fetch

`UNPACR_Regular.md:574`:
> "Once these [2 setup] cycles are complete, execution proceeds in a pipelined fashion,
> with the primary bottleneck being the fetching of bytes from L1."

No Unpacker-FPU overlap depth is published. Sync is via `AllowedClient` bank ownership.

### Needs microbenching (unpacker)

1. **Per-format end-to-end UNPACR cycles** (not just bandwidth). Issue a solo UNPACR
   (1 tile, format X, x4 mode), wrap with `STALLWAIT(STALL_UNPACK, 0)` and
   `WALL_CLOCK_L` reads. Sweep all 12 formats.
2. **Compressed-data extra setup cycles** (spec says ">2" with no number).
3. **BFP exponent-section overhead vs. `Force_shared_exp`.**
4. **ZEROSRC cycle cost** (clears 1024 cells/bank; no published number). Sweep
   `BothBanks = 0/1`.
5. **SETDVALID visibility latency to FPU.**
6. **Context-switch via WRCFG minimum STALLWAIT duration.**
7. **Unpacker internal instruction-FIFO depth** (how many UNPACRs can be in flight
   before the issuing thread stalls).

---

## 2. Packer

### PACR issue throughput

`WormholeB0/TensixTile/TensixCoprocessor/Packers/README.md:21`:
> "At most one of these instructions can be started per cycle. For both of these
> instructions, the issuing Tensix thread will be blocked until the packers referenced
> by the instruction have _accepted_ the work, and then the thread can proceed on to
> its next instruction."

Issue rate: **1 PACR/cycle** (shared across threads). Thread unblocks on accept
(input side), not on L1 write completion — to wait for completion use
`STALLWAIT(C3–C6)`.

### Packer → L1 write bandwidth

`WormholeB0/TensixTile/L1.md:43`:
> "There are four packers, each theoretically capable of one 128-bit write per cycle,
> or one 128-bit atomic accumulate (4 lanes of 32-bit or 8 lanes of 16-bit) every five
> cycles, or one 128-bit non-atomic accumulate every two cycles."

| Mode | BW per packer |
|---|---|
| Normal write | 128-bit write / cycle (16 B/cyc) |
| Atomic accumulate (Pack_L1_Acc) | 128-bit every 5 cycles (3.2 B/cyc) |
| Non-atomic accumulate | 128-bit every 2 cycles (8 B/cyc) |

`L1.md:45` (L1-to-L1 pack, packer 0 only):
> "one 128-bit read and one 128-bit write per cycle, or one 128-bit read and one
> 128-bit accumulate every five cycles."

**Granularity**: always aligned 16-byte writes to L1; datums accumulate in a bottom-of-
pipeline buffer until 16 B, then flush (or forced by `Flush` / `Last`).

### Dst → Packer read: 4-cycle hazard

Same rule as FPU reads (see compute-units.md § Dst hazard):
> "... PACR instruction which wants to read from that block [will be stalled] for an
> appropriate number of cycles. [...] at least five distinct 8x16 blocks of Dst to
> avoid being stalled." (`BlackholeA0/Dst.md:96-97`)

### Bytes per datum from Dst

From `In_data_format` bits [1:0] in `blackhole-py/emu/specs/pack-data-path.md § 3.2`:

| Format | B/datum from Dst |
|---|---|
| FP32 / TF32 / INT32 | 4 |
| FP16 / BF16 / INT16 | 2 |
| BFP8/4/2 (A or B), INT8, FP8 | 1 |

### BFP shared-exponent late conversion

`WormholeB0/TensixTile/TensixCoprocessor/Packers/FormatConversion.md:56-58`:
> "To BFP8: Converted to BF16 (as per first row), then round to BFP8 with one shared 8b
> exponent per 16 datums. To BFP8a: Converted to E5M7 (saturate if there is narrowing
> of exponent, then truncate if there is narrowing of mantissa), then round to BFP8a
> with one shared 5b exponent per 16 datums."

**No separate cycle count for the shared-exponent stage is published.** This is a
documented pipeline stage with unstated per-format latency — high priority gap.

### Multiple PACRs in flight

`PACR.md:43`:
> "if there are multiple PACR instructions in-flight within a given packer, they will
> observe the value of these configuration fields as they were when _one_ of the
> in-flight instructions started."

Packer pipeline depth is **not published**. Issue stalls only at the packer input
gate, not at L1 write.

### PACR_SETREG

`PACR_SETREG.md:19`:
> "Once all previous PACR instructions have gotten past the packer's late format
> conversion stage, flush any data in the packer buffers just before L1 and
> simultaneously perform a 32-bit memory write within a small window of the MMIO
> address space."

Barrier after late conversion (not after L1 write). Issue rate = 1/cycle.

### Performance counters

`tt-llk/docs/performance_counters/performance_counters.md:171-177`:
- `PACKER_DEST_READ_AVAILABLE` — cycles data was available for packer to read
- `PACKER_BUSY` — cycles packer was actively working
- `AVAILABLE_MATH` — cycles math results were available for packing
- `PACK_INSTRN_AVAILABLE_2` (INSTRN_THREAD bank ID 23)

### Needs microbenching (packer)

These are all (instruction × dest-format) combinations with **no numeric value in any
document**:

1. **PACR accept latency by format.** Solo PACR (N=16 datums) for each (in, out) format
   pair; time TRISC2 unblock via `PACK_INSTRN_AVAILABLE_2`.
2. **PACR end-to-end pipeline latency by format** — FP32→FP32, BF16→BF16, FP32→BF16,
   FP32→BFP8/4/2, FP32→INT8/INT32/FP16. STALLWAIT(C3-C6) after one PACR; count cycles
   to release.
3. **BFP shared-exponent extra cycles vs. BF16 at same N.** Δ = BFP overhead.
4. **PACR_SETREG MMIO barrier latency.** Poll MMIO target after PACR_SETREG.
5. **Flush / Last flag cost** (15-datum pack vs. 16-datum pack).
6. **Tilize/untilize strided write cost** with PackerMask = `0b1111` vs. `0b0101` vs.
   `0b1010`.
7. **Edge-masking extra cycles** (`PCK_EDGE_MODE != 0`).
8. **Dst → packer read bandwidth in datums/cycle** (only B/datum from format is
   documented). Sweep `InputNumDatums` 1–256.
9. **Back-to-back PACR initiation interval** (is it 1 cycle or stall-on-accept?).

---

## 3. TDMA / XMOV / Mover / ThCon

Primary: `WormholeB0/TensixTile/Mover.md` and the per-instruction `.md` files in
`WormholeB0/TensixTile/TensixCoprocessor/`.

### XMOV / Mover measured throughput

`Mover.md:62-64` (verbatim in `specs/xmov-and-tdma-mover.md § 6`):
> "Eight 128b reads and eight 128b writes every 11 cycles i.e. 93.1 bits copied per
> cycle (memcpy, ideal).
> One 128b read and one 128b write every four cycles i.e. 32 bits copied per cycle
> (memcpy, with L1 port contention).
> One 128b write per cycle i.e. 128 bits written per cycle (L1 memset, ideal).
> One 128b write every three cycles i.e. 42.7 bits written per cycle (L1 memset,
> contention).
> One 128b write per cycle i.e. 128 bits written per cycle (non-L1 memset — no L1
> contention, same both columns)."

### XMOV issue protocol

`XMOV.md:33-34`:
> "The thread issuing an XMOV instruction will be automatically stalled until the
> mover is able to _start_ work, at which point XMOV will execute in a single cycle -
> the mover proceeds with the task in the background."

Setup: 0 extra cycles once Mover free; instruction itself is 1 cycle. Completion
tracked by C9 (STALLWAIT condition).

### TDMA command queue

Depth = **4 entries** (`TDMA-RISC.md:142`, from the `CommandQueue.Capacity()` note).
ParameterCredits = 2 (line 97 of the same file).

### CLK_GATE registers 0x24/0x28

**Not** real clock-gating — they're unpacker `SetRegAddr` and `SetScaler`
registers reused for packer config (`TDMA-RISC.md:28-29`). The emulator
(`tensix/tdma.py:86`) already treats them as no-ops.

### ThCon scalar op latencies

`ADDDMAREG.md:31` (same wording in `MULDMAREG.md`):
> "The RightImm6 variant takes three cycles. The RightReg variant takes three cycles
> if LeftReg and RightReg come from the same aligned group of four GPRs, or four
> cycles otherwise."

Same 3/4-cycle rule for SHIFTDMAREG / BITWOPDMAREG / CMPDMAREG
(`specs/additional-scalar-unit-instructions.md:53`).

### LOADIND / STOREIND / LOADREG / STOREREG

All **"at least 3 cycles"** in the Scalar Unit, "possibly longer if the memory
subsystem is busy" (`LOADIND.md:56`, `STOREIND_L1.md:44`, `LOADREG.md:41`,
`STOREREG.md:34`). For result visibility, `LOADIND.md:52` suggests 7 DMANOP as
"usually sufficient" but "inherently racy" — correct barrier is `STALLWAIT C0`.

### ATINCGET / ATSWAP

`ATINCGET.md:51`:
> "The instruction occupies the Scalar Unit (ThCon) for at least three cycles ... due
> to limits on the number of in-flight L1 requests from the Scalar Unit, sustained
> throughput is (at best) one ATINCGET instruction every 12 cycles."

Result-visibility heuristic: 24 DMANOP. ATSWAP has the same 3-cycle / 12-cycle
throughput.

### ATCAS

`ATCAS.md:35`:
> "This instruction takes at least 15 cycles to execute, possibly longer if there is
> L1 access port or bank contention. If the comparison fails, each subsequent attempt
> takes another 15 (or more) cycles, until the comparison eventually succeeds."

Holds Scalar Unit for full duration (blocking all other ThCon ops).

### FLUSHDMA

`FLUSHDMA.md:46`:
> "The instruction occupies the Scalar Unit (ThCon) for at least two cycles, and for
> as many additional cycles as required for the selected conditions to be met."

`ConditionMask==0` defaults to `0xF`. **Blocks all threads' ThCon**, unlike
`STALLWAIT C0` which only blocks the issuing thread's Wait Gate.

### REG2FLOP

`REG2FLOP_Configuration.md:40`:
> "This instruction usually takes two cycles, though it will take longer if
> Configuration Unit instructions (from any Tensix thread or any baby RISCV) are
> contending for write bandwidth to THCON configuration."

### DMANOP

Single cycle; waits at Wait Gate if ThCon is busy.

### STALLWAIT interaction

Every ThCon op is blocked by **both B0 (STALL_TDMA) and B5 (STALL_THCON)**. XMOV is
blocked by **B0 and B4** (not B5). `STALLWAIT.md` line 210 on C9:
> "This won't prevent other threads (or TDMA-RISC) from issuing new instructions to
> the mover though, and those new instructions will cause this thread to continue to
> wait."

### Needs microbenching (TDMA/XMOV/Mover/ThCon)

1. **XMOV startup stall when Mover busy.** Spec says "automatically stalled" with no
   cycle count. Bench: XMOV right after a long XMOV_L1_TO_L1 (16 KB).
2. **TDMA-RISC command-queue write → Mover-busy latency.** RISC-V writes
   COMMAND_ADDR, then polls STATUS bit 0.
3. **LOADIND / LOADREG exact result-visible latency** (spec says ≥ 3 but 7-DMANOP
   heuristic implies 7–8). Sweep DMANOP padding 1–8.
4. **ATINCGET L1-in-flight limit** — is 12 cycles a fixed pipeline depth or a credit
   counter?
5. **MOVREG2DMEM** — name appears in the original request; not in any ISA doc, LLK,
   or emulator code. Either a WH-era removed name or a macro. Needs header grep /
   clarification.
6. **MOVB2D / MOVD2A / MOVD2B / MOVA2D** are FPU/Matrix Unit ops (blocked by B6) —
   latencies in [`compute-units.md`](compute-units.md). No timing published; bench
   via C4 clearing after issue.
