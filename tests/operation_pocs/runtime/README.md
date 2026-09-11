# External movement and handoff primitives

Callable raw emitters are in `ops.py`; independent hardware oracles and isolated device-cycle intervals are in `test_runtime.py`. No shared runtime/model files were changed. Resume work preserved the prior implementations and fixed the source-flag fixture's unpack configuration credit leak.

## Operation ledger

`k` is an explicit `Asm`; `Transfer` owns an L1 interval and one NIU command slot/TID. `config` is the read-only shared `noc.InterleavedConfig`; `bank=0/1` selects SrcA/SrcB. All signatures return `k`.

| Operation / signature | Footprint and result | State, completion, setup | Test and measured cost |
|---|---|---|---|
| `read_from(k, spec, external_address, serial=False)` | Byte-exact single-bank DRAM to selected dense L1, no conversion | BRISC/NCRISC; chosen NoC/command/TID exclusively owned; includes command initialization, address arithmetic and marked response drain | `test_external`; BF16/FP32, N=128/256, both NoCs; final tables in `results.md` |
| `write_to(k, spec, external_address, serial=False)` | Byte-exact selected dense L1 to single-bank DRAM, no conversion | Separately drains local source reads then remote acknowledgments; source is reusable and destination visible on return | `test_external`; independent timing from read |
| `cb_action(k, config, 'reserve', count=1)` | Wait for free credits, no counter mutation or memory claim against other producers | Single producer; acquired count fits depth; counter subtraction wraps modulo 65536 | `test_cb_primitive`, `test_cb_blocking`; K=16 uncontended, K=1 delayed peer |
| `cb_action(k, config, 'publish', count=1)` | Increment selected received counter | Caller first completes payload production; emits publication fence | `test_cb_primitive`; K=16 |
| `cb_action(k, config, 'wait', count=1)` | Wait for available received-minus-acked credits, no mutation | Single consumer; acquire fence after satisfied condition | `test_cb_primitive`, `test_cb_blocking`; K=16/K=1 |
| `cb_action(k, config, 'release', count=1)` | Increment selected acknowledged counter | Caller first consumes payload and drains outstanding source reads; release itself is not a NoC drain | `test_cb_primitive`; K=16 |
| `semaphore_action(k, semaphore, 'post')` | Increment one of eight hardware semaphores, saturating at 15 | TRISC; caller drains payload before handoff; PC synchronization included | `test_semaphore_primitive`; K=7, semaphores 1/2/5/7 |
| `semaphore_action(k, semaphore, 'get')` | Decrement selected semaphore, saturating at zero | Same ownership and completion as post | `test_semaphore_primitive`; K=7 |
| `semaphore_action(k, semaphore, 'wait_ready')` | Wait while selected semaphore is zero | SYNC-gated dependent empty-mask SEMPOST then PC synchronization | `test_semaphore_primitive`, `test_semaphore_blocking`; K=7/K=1 |
| `semaphore_action(k, semaphore, 'wait_space')` | Wait while value is at least configured maximum | Same wait completion; maximum belongs to caller configuration | `test_semaphore_primitive`, `test_semaphore_blocking`; K=7/K=1 |
| `source_flag(k, bank, 'publish')` | Give current unpacker ping-pong bank to matrix unit and flip unpacker selection | TRISC; inherits configured output format; wait for unpacker completion then PC synchronization | `test_source_flags`; both A/B, K=8 accumulated intervals |
| `source_flag(k, bank, 'release')` | Give matrix bank to unpacker and flip matrix selection | Whole physical bank ownership; wait for matrix completion then PC synchronization | `test_source_flags`; both A/B, K=8 |
| `source_flag(k, bank, 'wait_valid')` | Wait for current matrix bank to become valid | SYNC dependency consumes wait gate; PC synchronization included | `test_source_flags`, `test_source_flag_blocking`; K=8/K=1 |
| `source_flag(k, bank, 'wait_free')` | Wait for current unpacker bank to become free | Same wait completion; no payload modification | `test_source_flags`; K=8 uncontended; delayed-peer coverage unresolved |

The original ledger selected external transfers and four CB actions before implementation. The prior agent also implemented the semaphore/source ownership handoffs required by existing compute recipes; this catalog retains and validates them. These synchronous external transfers themselves need no extra Tensix semaphore or source flag action.

## Address and ownership contract

Addresses, offsets and strides are **bytes**. `external_address` is a register holding a 32-bit bank-local base; it must be 32-byte aligned and its selected span must fit the caller's external allocation without 32-bit overflow. High address words are zero. This is a concrete raw adapter: model `Buffer.read_from/write_to` only records offset/stride and does not establish units, default stride, or induction behavior. No model change is implied.

`elements` is a positive multiple of 128, `element_bytes` is 2 or 4 (BF16/FP32 storage, bit-exact with no numeric interpretation), external block stride is the distance between starts of 128-element blocks, and zero means dense. Require nonoverlapping external blocks and 32-byte-aligned offsets/strides/L1. L1 is always dense. Physical read/write byte counts equal each full block's logical byte count; there is no hidden padded source read. Guard values alone are not proof of that read footprint: the emitted NIU command's explicit byte count is the addressing proof.

External tests vary L1 placements 0/0x4000/0x8000/0xC000 relative to the arena plus a 64-byte guard, first/last discovered DRAM banks, both NoCs, and dense/strided blocks. They inspect immediate L1 prefix/suffix guards, external prefix/suffix and stride gaps, an adjacent DRAM allocation, and the entire unchanged read source. No payload staging scratch is required.

CB counters occupy a selected physical sync slot, independently of payload addresses. Tests cover slots 0/31, ordinary and 65535 wrap state, a sentinel neighbor counter pair, and delayed peer release/publication. Capacity and credit distance stay below 65536. Reserve/wait do not reserve memory against multiple concurrent producers/consumers.

Semaphore tests inspect selected values and a different sentinel semaphore. Source flag recipes own the whole physical ping-pong bank, independently of allocation-scoped payload ownership. Fixtures cycle banks and preserve L1 sentinels; they do not establish preservation of every Src/Dst datum (these primitives contain no payload instructions). Static source format configuration is reusable setup, outside timed intervals. Flag-only fixtures must use `configure_unpacker(..., commit=False)`: committing data-unpack configuration without data-unpack completion consumes credits and eventually hangs. The operation must not silently reconfigure/clear an entire bank.

## Timing and reusable state

The profiler explicitly reserves the final 32 bytes of the L1 data arena. All kernels leave that reservation disjoint from operands/guards. Each case has one warmup and seven measured launches. Results retain raw/control samples, min/median/max, K, normalized cycles, physical card/core and job ID; no subtraction or timing assertions. An empty adjacent marker control is measured under the same conditions. Short CB/semaphore loops are unrolled, with no runtime loop overhead; their normalized costs include per-call register/address setup and completion. Source flag timing accumulates eight separately marked intervals, so its matched control also accumulates eight intervals. Delayed-peer cases include start notification and intentional 1024-iteration waiting and are not uncontended latency claims.

All helper-created temporaries use assembler virtual RISC registers (no fixed caller register clobber); actual physical registers follow the assembler allocator. `Transfer` uses six explicit temporaries plus local-coordinate and shared NIU helper temporaries; CB uses three plus shared helper temporaries. Semaphore/source adapters use PC synchronization temporaries. No LReg/Dst scratch is used. Assembled image sizes are retained per case; fixtures and profiler contribute to those sizes, so image size is not falsely labeled emitter-only cost.

The simple serial baseline drains each block; the selected batched version drains once after the bounded sequence. Both include required command configuration and complete with the same oracle. The 128-block software ceiling protects 8-bit NIU outstanding counters, but only 1/2-block sequences are hardware-proven here; longer statically unrolled programs may exceed firmware text slots. Partial external blocks, interleaved multi-bank transfers, posted-write completion, arbitrary atomics/collectives and numeric conversion are not claimed.

A delayed-peer source-free experiment that publishes both ping-pong banks timed out; that fixture is not included in the final passing suite. Source-free is measured/correctness-tested in uncontended balanced bank cycles, but blocking source-free behavior remains an explicit gap. Delayed source-valid waits are independently tested for both A/B. Failed experimental queue evidence is retained in `results.md`.
