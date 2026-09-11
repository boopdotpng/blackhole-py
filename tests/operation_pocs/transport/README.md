# Allocation-scoped transport PoCs

Final hardware evidence: **24 full-sweep tests passed** (2,564 operation cases,
seven measured samples each), plus **8 signed/rounding-edge tests passed**.
All four operation families cover both formats; see results.md and final-sweep.json.
Existing emitters were continued and fixture/protocol bugs fixed within this subtree.

All lengths are runtime **element** counts starting at logical element zero.
Source slot indices are 0..7 (128 elements); FP32 Dst slot indices are 0..63
(each occupies two aligned 16-bit allocation units). The caller validates
1 <= N <= capacity; N=0 and overflow are outside these contracts.

| Operation | Callable emitter | Footprint and formats | State/completion | Tests and evidence |
|---|---|---|---|---|
| L1 to SrcA | `ops.unpack_source(k, target=SRCA, slot=..., source=..., count=Reg, scratch=..., input_format=BF16, capacity=128, publish=True)` | One selected slot; zero tail. `capacity=256` owns an even-aligned A pair. BF16 identity; FP32 input intentionally narrowed to BF16 by truncation. Scratch owns `capacity*input_item_bytes+64` bytes, 16-byte aligned. | TRISC0, selected bank unpack-owned, source row counter initially zero. Configures unpack engine, drains engine and instruction FIFO. `publish=True` flips source bank to math; false retains unpack ownership. No implicit bank clear. | `test_source_prefixes`: low/high A/B and aligned A pairs, both formats. Full sweep passed. |
| L1 to SrcB | Same with `target=SRCB` | One B slot, independent A placement; same staging contract. No 256-element B mode. | As above, unpacker 1. | Same test; full sweep passed. |
| L1 to Dst | `dst.unpack_dst(k, dst_slot=..., source=..., count=Reg, input_format=F32)` | One 128-element FP32 slot, tail zero. Exact N naturally aligned scalar input reads. No L1/source/Dst scratch. BF16 widens; FP32 bits inserted with SFPU immediates. | TRISC1 owns Dst. Clobbers L0/L7, CC (returns all enabled), FP32 math configuration and address counters. Drains SFPU and instruction FIFO. Caller handles handoff. | `test_dst_prefixes`: slots 0/31/63, all Dst and both source-bank guards captured before observation scratch. Full sweep passed. |
| Dst to L1 CB | `ops.pack_exact(k, dst_slot=..., output=..., count=Reg, scratch=..., output_format=F32)` | Exact `N*output_item_bytes` final output bytes, no output alignment requirement. Owns 576-byte, 16-byte-aligned scratch page for hardware rounded pack writes. Source Dst preserved. FP32 identity; BF16 uses configured deterministic pack conversion. | TRISC2; consumes one MATH_PACK publication. Includes pack configuration, pack completion/FIFO drain, scalar exact-byte final copy and fence. Clobbers pack configuration, MOP and DMA address registers. | `test_pack_all_prefixes`: slots 0/31/63 and both formats, immediate output sentinels, scratch boundary guards, all 64 Dst slots observed. Full N=1..128 sweep passed. |

These are standalone operation recipes. Configuration is not restored; downstream
consumers must configure their own engine modes. Scratch must be disjoint from
inputs, outputs, guards, and profiler storage. `stage_prefix` reads precisely N
input elements using byte loads and initializes all engine-visible scratch bytes;
neighbor poison alone is not the no-overread proof. Hardware reads operate only
on explicitly owned staging. `copy_bytes` requires disjoint byte ranges.

Emitters accept optional `profile=Profiler` on pack/source operations. It adds one
nested section for final exact copy or staging/zero-fill. Complete timing includes
that section's marker overhead. Without the optional parameter signatures remain
compatible with the inherited code. These signatures are stable; see the numerical restrictions below.

Tests assemble once per format/placement and vary N via PARAM_BASE, never generate
O(N) literal instructions. Default partial sweep is N=1..128; `TRANSPORT_LENGTHS`
selects a diagnostic subset. Full A pairs use N=256. Each length warms up once and
records seven measured K=1 samples, with correctness on every launch. Empty-marker
controls are raw counts; no subtraction or fixed timing assertions. Reserved
profiler storage is the final 32 bytes of DATA_BUFFER_SPACE; other data is below
BASE+0x18040. Fixture setup and post-operation observation are outside timing.

Numerical contract: finite normalized values are covered, including positive and
negative values, smallest normal magnitude, and conversion ties. FP32 Dst load and
FP32 pack preserve signed zero. BF16 pack canonicalizes negative zero and rounds
halfway magnitude **away from zero**, as observed with this configuration; do not
assume nearest-even from the historical shared README. SrcA/SrcB paths narrow FP32
by truncation, and observation through MOVA2D/MOVB2D canonicalizes signed zero. The
source test does not distinguish whether that canonicalization occurs at unpack or
movement. NaN payloads, infinities and subnormals are not characterized here.

`test_signed_and_rounding_edges` retains seven measured samples per operation/format.
`code-costs.json` records assembled primitive size (including runtime count load and
return, without profiler markers): pack 1300 bytes; SrcA 656, SrcB 648; Dst BF16 548,
Dst FP32 660. Scalar staging uses a pointer/value and runtime-loop registers;
`unpack_dst` uses L0/L7 and four fixed lane loops. Exact staging and final copies
use conservative scalar byte loops. Their measured costs dominate long transfers;
an aligned word-copy candidate is a future optimization, not an unmeasured claim.

All source and Dst allocations are captured before observation scratch is reused.
Observation uses explicit row addresses, retains source ownership for every row,
and releases the banks once afterward. Source fixture initialization acknowledges
UNPACK_SYNC before subsequent unpack reconfiguration. Publishing the untouched
source bank uses its seeded UNPACR; the old UNPACR_NOP variant cleared that bank.

Reusing a core across separately booted processes can still stall CQ1 in this dirty
runtime. Final evidence uses documented valid fresh worker indices. This shared
boot/recovery limitation was reported to the coordinator; no shared files changed.
