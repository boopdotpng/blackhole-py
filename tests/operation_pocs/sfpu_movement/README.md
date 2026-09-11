# SFPU movement and control recipes

Reusable raw emitters are in `emitters.py`. The existing implementation was preserved on resumption. Hardware status and raw measurements are in `results.md`, `baseline.log` and `baseline-results.json`; the final 238-case suite passed on card 0/core index 1 in queue job `1e6cf52ff6e347c08d6bbf5eec17f738`. Core index 0 currently times out on both cards.

All registers are integer indices. Writable destinations are l0–l7; sources are l0–l15. The public model's foreign-register and allocation validation is checked only on CPU. These emitters do not lower model records automatically.

| Operation | Signature and footprint | Precision/state and scratch | Tests and evidence |
|---|---|---|---|
| `load` | `load(k, dst, allocation_start, position=0, block=0, blocks=1)`; read 32 selected FP32 Dst values, write one LReg | Mode 3, active lanes only; inactive LReg lanes preserved; no scratch | `test_load_lane_mapping`, `test_predicate[load]`; baseline pass at starts 0,14,126 and all four positions |
| `store` | `store(k, src, allocation_start, ..., raw=False, scratch=5)`; write 32 selected Dst values | Mode 3 flushes FP32 subnormals to signed zero. `raw=True` mode 4 preserves bits. l12–l15 require copy through declared writable scratch to avoid backdoor semantics; other sources need none | `test_movement[store]`, `test_predicate[store]` baseline pass; all-register and special-bit extensions validated by final run |
| `loadi` | `loadi(k, dst, value)` or `loadi_bits(k, dst, uint32_bits)` | One high-half immediate and optional low-half immediate; writes active lanes only; no scratch; Python value rounded to FP32 | `test_movement[loadi]` baseline pass; `test_immediate_and_store_bits` and masked loadi validated by final run |
| `copy` | `copy(k, dst, src)`; one LReg vector | One SFPMOV; self alias allowed, active lanes only; no scratch | `test_movement[copy]` baseline pass; all 16 sources × eight destinations and masked copy validated by final run |
| exposed registers/constants | `register(index, writable=False)`, model `.regs`, `.l0`–`.l15`, `.zero`, `.one` | l8=FP32(0.8373), l9=0, l10=1, l15 integer `2*lane`. l11–l14 are configurable vectors, not immutable constants; fixture SFPCONFIG broadcasts eight source lanes to 32 | `test_movement[zero/one/l8/l15]` baseline pass; `test_registers_and_aliases` validated by final run; `test_cpu_operand_validation` passes |
| `predicate(mask)` | `predicate(k, uint32_mask, scratch=(6,7))`; bit i selects physical lane i | Replaces previous mask even after all-off. Nontrivial mask clobbers two distinct writable LRegs, no Dst scratch. All-on/off use two instructions and no actual LReg writes. General mask uses 8 or 9 instructions depending on immediate low half | `test_predicate` all-on/off, alternating, 32 individual bits; baseline load/store/add pass; complete predicate+masked-op intervals and matching accumulated controls validated by final run |
| `predicate(None)` | `predicate(k)` | One SFPENCC disables lane flags and sets all flags true; no LReg/Dst scratch. This resets to all-on, does not restore an arbitrary earlier mask or condition stack | Every predicate test observes reset using a subsequent unmasked store and immediate; updated timing validated by final run |

`allocation_start` is an **even physical 16-bit allocation-unit index**, not an element index. A block is 128 FP32 values and owns two consecutive units. Bounds require `allocation_start + 2*blocks <= 128`. The emitted address is `allocation_start*4 + block*8 + position*2`.

For position p and physical lane i, the logical element within a block is
`64*(p//2) + 16*(i//8) + 2*(i%8) + p%2`.
The mapping test independently stores each loaded vector alongside hardware l15 lane tags. It is not a round-trip-only oracle.

Before use, the caller establishes FP32 Dst configuration, zero Dst base/target/stack offsets, zero address-modifier increments and no lane column exchange, blocked accesses or implicit index capture. The fixture clears thread configuration indices 12,28,47 and resets RWCs. Finish prior producer work before SFPU reads (including the documented FPU→SFPU hazard); the fixture waits for unpack completion. Emitters preserve this static configuration and do not allocate or initialize whole banks.

`drain(k)` emits `STALLWAIT(SYNC, SFPU)` and belongs inside measured completion intervals. Dst handoff to another thread additionally uses `pc_sync`/`publish_dst` in the fixture. The helpers do not themselves publish a Dst semaphore. Unpack, configuration, observation pack and host readback are outside operation timing.

The fixture owns full-Dst poison initialization and full-bank read-only observation to detect corruption of every non-owned Dst allocation. Operations own only their stated selected vectors. Mapping observation owns logical blocks 28–29 and l4; predicate reset observation owns position 0 of logical block 30 and l2; register tests own position 0 of logical blocks 16–23 and 40. Predicate scratch is l6/l7; special-register store scratch is l5. The register-config fixture additionally owns l0 and the configured l11–l14. SrcA/B are not used by the tested emitters.

L1 input is `[DATA_BUFFER_SPACE_BASE, +32768)`, output starts 65536 bytes above that base and occupies 32768 bytes plus a 64-byte guard. The existing Profiler reserves the last aligned 32 bytes of DATA_BUFFER_SPACE, disjoint from both. Each launch checks every Dst word and output guard.

Benchmarks use one warmup and seven measured independent launches, retain all raw counts, and have no timing assertions. Short operations are unrolled K=16 (four positions for load/store, giving 64 vector operations); no loop/replay overhead is hidden. These are issue-plus-drain sequence costs, not peak SFPU throughput. Predicate tests accumulate four separately bracketed intervals including mask construction and the masked operation; reset and empty controls use the same four-interval scheme. No marker subtraction is performed. Baseline predicate normalization is superseded and must not be used as a valid per-call cost.

Interfaces in `emitters.py` are frozen for Agent C. Additional ISA conversion modes, arbitrary offsets, tensor-length sweeps, condition-stack save/restore and arithmetic implementations are outside this owned contract. No candidate optimization was selected without a validated same-card comparison.
