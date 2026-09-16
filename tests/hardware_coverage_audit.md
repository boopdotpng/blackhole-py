**Blackhole hardware coverage audit — 2026-09-16**

Reviewed the working-tree suite: 42 `test_*.py` files, 112 test functions before parametrization, and their test helpers. This includes the uncommitted RMSNorm work. Baseline commits: blackhole-py `68d6dd7`, local tt-metal `e8ebdec7e45`, ISA documentation `82f600d`. This is a source audit, not a hardware run or a claim that all existing cases pass. Performance benefits below are hypotheses to measure.

The suite is strong on selected raw movement/arithmetic recipes, placement guards, and timing. The most useful missing coverage is **other modes of already-used engines**, plus **DRISC DMA and actual overlay message transport**. Opcode-presence counts would be misleading: ELWSUB is dispatched dynamically, some tests import example emitters, and timing-only instructions do not establish correctness.

**Follow-up hardware work:** min/max and paired indices, a 250k SFPU argmax, packer L1 accumulation, and pipelined load macros now have [card-0 results and tests](compute/sfpu/hardware_probe_results.md): 76 passing cases. The inventory and gap table below retain the original audit snapshot.

**Suggested order**

| Priority | Experiment | Why it could matter | Existing coverage / missing distinction |
|---|---|---|---|
| 1 | SFPSWAP min/max/argmax + other shuffle modes | Softmax max reduction, greedy decoding, top-k; potentially fewer predicate/move instructions | Only unconditional swap is timed; no swap result oracle |
| 1 | Packer L1 accumulation | Accumulate spilled partial sums without unpacking them back into Dst | Current pack tests overwrite; address reuse is not accumulation |
| 1 | Broader SFPLOADMACRO schedules | Fuse conversion/activation/quantization with load, arithmetic and store | RMSNorm macros exist; round/simple sub-unit combinations and timing contracts lack isolated coverage |
| 1 | Unpack transpose/tilize/broadcast + format/context changes | Remove software layout work, reuse operands, reduce setup and synchronization | Raw row-major movement is broad; these transformations and transitions are not |
| 2 | Core-to-core overlay stream with backpressure | Reduce per-message RISC issue/poll/bookkeeping work | Overlay counters are used as CB metadata; autonomous message movement is not tested |
| 2 | GDDR → DRISC L1 → Tensix forwarding | Bank-local prefetch, multicast reuse, fewer worker-side read requests | No DRISC launch role or GDDR DMA register use in blackhole-py |
| 2 | Native block formats / INT8 FPU | Lower weight bandwidth and potentially cheaper quantized compute | E4M3 and Q6 decode are tested; full BFP tiles and integer matmul are not |
| 2 | L1 contention, source reuse, and long-running handoffs | Reveal performance cliffs hidden by isolated prepared-engine tests | Dst FPU/SFPU contention already exists; other shared paths and protocol stress remain |
| 3 | Local mover, TRISC2 RVV, scalar atomics/bitmanip | Accelerate small copies, metadata and irregular tails | No dedicated correctness/performance coverage |

**What is already covered well enough not to propose as new**

- DRAM: both NoCs, interleaved read/write/copy, CB depth and issue batches, many-core scaling, three controller ports, bank skew/splits, one-way traffic, static/dynamic VCs, and priority sweeps. These are all inside [test_noc.py](movement/test_noc.py), despite that file containing only three top-level tests. Some sweep variants measure traffic/timing rather than validating each result.
- Remote movement: unicast/multicast CB sends and NoC fetch-add, including returning versus discarded-return forms. Indexed gather/scatter includes duplicate-index semantics. Host upload tests cover staging tails, bank/page combinations, ordering and slot reuse.
- Transport: full and partial L1→source/Dst paths, exact FP32 lane insertion, source/Dst poison guards, scattered allocations, one/four pack interfaces, output tails and a wrapping local CB.
- Formats: BF16/FP32 conversion, packer ReLU/clamp, deterministic and stochastic BF16 packing, E4M3 normal encodings and explicit subnormal expected failures. There is already a raw BFP4 forced-exponent probe: it does not demonstrate E2M1/MXFP4 support.
- Compute: basic SFPU math, masks, aliases, exp/reciprocal boundaries; FPU ELWADD/SUB/MUL, MVMUL, GAPOOL, GMPOOL, basic source/Dst moves, BF16 Dst, elementwise broadcast modes, source slot placement; mean/RMSNorm fidelity and scheduling variants; Q6 dequantization.
- Synchronization/timing: CB counter wrap, deliberately blocking CB/semaphore/source-valid waits, firmware cache/fusion bits, RISC and SFPU timing slopes, Dst payload throughput, FPU/SFPU Dst contention and switching frequency. MOP, replay, source-bank handoff and SFPU load macros are already exercised.

**DRISC GDDR DMA: the engine on the DRAM RISC cores**

This is a separate hardware path from the NoC-driven service in [firmware/dma.c](../firmware/dma.c), PCIe DMA, and Tensix TDMA/XMOV. The local Metal API explicitly describes **GDDR ↔ DRISC L1**, with two TX streams, up to 255 outstanding reads and 15 writes per stream. Transfers use 16-byte units; the size field permits at most 262128 bytes, but the actual stage must fit the much smaller available DRISC L1 budget.

Useful starting sources:

- [GDDR DMA API](../../tt-metal/tt_metal/hw/inc/experimental/gddr_dma.h): read/write, per-stream barriers, outstanding counts, burst size.
- [Blackhole register definitions](../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/gddr_dma_regs.h): separate stream registers at `0xFC000000` / `0xFC000100`, global controls at `0xFC001000`, auto-increment fields.
- [DMA-only benchmark kernel](../../tt-metal/tests/tt_metal/tt_metal/test_kernels/misc/drisc_l1_dram_dma.cpp).
- [DMA plus Tensix forwarding kernel](../../tt-metal/tests/tt_metal/tt_metal/test_kernels/misc/drisc_mcast_writes_tensix.cpp): multicast and double-buffered unicast alternatives.
- [Existing tensor prefetcher design](../../tt-metal/tt_metal/impl/buffers/prefetcher_matmul_design.md): one DRISC sender per bank, DMA into a small stage, NoC push to receivers. This establishes a concrete software use case, not a measured win for blackhole-py.

The useful comparison is:

`Tensix NoC read from GDDR → Tensix L1`

versus

`GDDR DMA → DRISC L1 → NoC write/multicast → Tensix L1`.

For a single consumer already saturating its bank, the second route can lose: it introduces a staging buffer and another producer/consumer handoff. It does not remove the final NoC payload transfer. It becomes more interesting when one fetched chunk is broadcast to several consumers, when the worker RISC is issue-bound, or when independent bank-side prefetch can overlap useful compute. My assessment is medium priority for single-consumer decode, higher for multicast/reused weights or a persistent prefetch architecture.

Interleaving is a software layout question here. Under the suite's page striping, logical page `p` resides in bank `p % B` at bank-local page `p // B`. A DRISC can walk its own contiguous physical pages; the forwarding stage must put them in the correct receiver order/offsets. Start with a bank-local shard before implementing multi-bank reconstruction. Auto-increment register fields are worth probing after basic DMA, but they do not establish a general scatter/gather or arbitrary 2-D DMA capability.

One important implementation constraint: **DRISC NIU mode changes the endpoint's meaning**. NOC2AXI allows ordinary remote GDDR access and prevents DRISC-initiated NoC traffic; stream mode permits DRISC NoC initiation but makes incoming traffic terminate at DRISC L1 on that NIU. Do not run the ordinary GDDR path through the same switched endpoint. Restore NIU mode and modified DMA attributes before returning. This is documented in [drisc_mode.h](../../tt-metal/tt_metal/hw/inc/experimental/drisc_mode.h), also [available upstream](https://github.com/tenstorrent/tt-metal/blob/main/tt_metal/hw/inc/experimental/drisc_mode.h).

First tests, in order:

1. Add a minimal DRISC launch/readback harness; [KernelRole](../firmware/consts.py) currently contains only the five Tensix RISCs. Prove one aligned read and write with full payload and guard checks, stream 0 then 1, and state restoration.
2. Sweep chunk sizes that fit the reserved stage, burst sizes (including the default 16 and 255), queue depth, and one/two streams. Distinguish issue time from read/write completion. Test buffer reuse only after the relevant completion event. Validate FIFO completion before relying on `wait_n` to release the oldest buffer.
3. Double-buffer GDDR→DRISC→one Tensix. Check every chunk with a unique sequence number and checksum; retain output or validate it before ring reuse.
4. Compare one, several and many receivers, both NoCs, one versus multiple banks, and worker compute overlap. Compare against the already-tuned direct read path, not a serialized read baseline. Report receiver-complete useful GB/s, worker RISC work, setup cost, and L1 consumed.

**Overlay streams: untested data transport, partially used registers**

[movement/noc.py](movement/noc.py) uses `0xFFB48020` / `0xFFB48028` and per-stream spacing for CB counters. That does not exercise message descriptors, hardware forwarding, credit return, phase transitions or auto-configuration. Neither `TTSTREAMWAIT` nor `TTSTREAMWRCFG` is used by the suite.

Use the [Blackhole overlay register header](../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_overlay_parameters.h) as the register-map source. The [Wormhole overlay explanation](../../tt-isa-documentation/WormholeB0/NoC/Overlay/README.md) is useful conceptual background, but its register layout and some buffer behavior differ. For example, Blackhole has separate `STREAM_ONETIME_MISC_CFG` and message-info wrapping controls. Do not copy Wormhole constants or assume every behavior transfers.

A focused prototype can avoid DRAM interleaving entirely: prefill one producer's L1 and have an overlay stream deliver messages into a consumer ring. Compare with the existing software remote-CB sender. Then add a deliberately slow consumer, repeated data/header-buffer wrap, and auto-advanced phase changes. This directly measures whether autonomous forwarding and credits save CPU work.

The potential goes beyond fewer NoC MMIO writes: `STREAMWAIT` can gate Tensix work on received-message count or phase, and `STREAMWRCFG` can bring a stream register into backend configuration, potentially shortening the RISC-mediated unpack handoff. Despite its name, **STREAMWRCFG reads the overlay and writes Tensix configuration**, not the reverse. Its [Blackhole specification](../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STREAMWRCFG.md) describes an ordering bug and recommends a following STALLWAIT; include an explicit completion protocol.

Then test multicast with a lagging receiver, and packer/unpacker integration through `PACR_SETREG` / `UNPACR_NOP` stream-related fields. Reserve stream IDs so the new configuration cannot overwrite existing CB counter registers.

Your interleaving concern is well founded: a linear FIFO plus remote endpoint is not automatically the mapping `bank=p%B, offset=(p//B)*page_bytes`. Candidate approaches are one stream per physical producer/bank, phase changes with precomputed routing, or software gathering into a contiguous staging ring. Each can move CPU cost into descriptor construction, phase transitions or receiver reordering. Start with core-to-core streams and bank-local data; only generalize if the savings survive those costs. DRAM-named scratch fields in the overlay header also describe NCRISC-managed behavior; their names alone do not establish autonomous interleaved DRAM reads.

Measure setup-inclusive and steady-state latency separately, messages/s, payload GB/s, sender/receiver RISC cycles or useful concurrent scalar work, and compute overlap. A faster isolated sender that makes the receiver spend more cycles is not a win.

**Instruction modes and operands worth testing explicitly**

| Instruction / configuration | Missing experiment | Practical target |
|---|---|---|
| `SFPSWAP` Mod1 1–8; `ENABLE_DEST_INDEX`, `EXCHANGE_SRCB_SRCC` | Lane/subvector min-max and paired index swaps, including ties, signed zeros, masks and aliases. Test raw outputs, not just completion. | Softmax max and argmax/top-k; compare against compare/select recipes |
| `SFPSHFT2` modes other than the existing rotate-by-one recipe | COPY4, chained copy, rotate-and-copy, zero-filling shift; test all affected LRegs and masked lanes | Shorter reductions and sliding-window/data rearrangement |
| `SFPLUT`, `SFPLUTFP32` | Table modes, boundary values and signs, isolated approximation error and throughput | Activation approximations; packed FP16 three-entry LUT has a documented indirect-destination quirk |
| `SFPMAD` / `SFPMUL` / `SFPMUL24` indirect operands | Per-lane L7-selected input/output, distinct values in every candidate LReg, legal destination aliases; MUL24 high/low product | Small in-register selection/quantization operations; MUL24 is 23×23 despite its name |
| `SFPCAST`, `SFPSTOCHRND` | Two's-complement↔sign-magnitude, integer absolute value, float→integer saturation/rounding, negative values and bounds | Quantization/dequantization; current Q6 casts are a narrow positive-integer path |
| `SFPPUSHC`, `SFPPOPC`, `SFPCOMPC`; alternate compare/flag modes | Nested predicate restoration and masked flag changes | Composable conditional SFPU kernels; current masks don't establish stack semantics |
| `SFPEXEXP`, `SFPEXMAN`, `SFPSETEXP/MAN/SGN`, `SFPDIVP2`, `SFPLZ` | Legal modifier forms and edge bit patterns with independent raw-bit models | Exponent-based approximations, power-of-two scaling, normalization |
| `MVMUL` broadcast bit | Unique source rows, every resulting Dst row and guard row | Vector/matrix cases; documented broadcast is unusual and does not simply produce eight identical rows |
| `GMPOOL` index enable, SrcB exponent scaling, native FP16 Dst | Index mapping/ties, negative-only input and Dst seed semantics, FP8→native-FP16 observation | Fast maxima/argmax and resolution of current FP8 GMPOOL expected failure |
| FPU implied formats / overrides / fidelity base | Mixed source formats, changing format with bank flips, phase-specific low mantissa bits, long cancellation-heavy reductions | Reliable HiFi3/HiFi4 choices and fewer redundant format reconfigurations |
| Unpack `srcb_bcast`, transpose/tilize, zero-write, context IDs | Full lane map and ownership guards, alternating descriptors/formats over many iterations | Persistent vector operands, prefill layouts, fewer copies and setup stalls |
| Pack `Pack_L1_Acc`, threshold/zeroing modes, context/flush/concat controls | Nonzero initial L1, zero contributions, multiple contributions, tails, format changes and restoration | Partial-sum accumulation and fused output transformations |
| Address modifiers / counters | Carry/reset/stride combinations with sentinel allocations; compare modifier-driven sequences against explicit immediate addresses | Eliminate per-iteration RISC arithmetic and repeated configuration |

The Blackhole [SFPSWAP spec](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/TensixTile/TensixCoprocessor/SFPSWAP.md) also gives a concrete scheduling candidate: inserting SFPNOP after swap can be faster than relying on its automatic stall. The existing timing suite already compares swap with/without NOP; the missing work is correctness and the nonzero modifier modes.

For GMPOOL index mode, the shared ISA model only tracks indices from the first eight rows even though the maximum can involve sixteen rows, and encodes indices nonlinearly. Test this explicitly before treating it as general argmax. For FP8 GMPOOL, the current expected failure concerns a particular FP32-Dst path; it does not prove the native FP16-Dst path is unusable. See [fp8.md](fp8.md).

**Packer L1 accumulation deserves its own small proof**

Start with `L1 = initial + packed(Dst)` for exactly representable values, then repeated contributions, cancellation and zeros. Observe untouched L1, Dst and neighboring buffers. Blackhole LLK's [reconfigure_packer_l1_acc](../../tt-llk/tt_llk_blackhole/common/inc/cpack_common.h) sets both `Pack_L1_Acc` and `Disable_pack_zero_flags`; otherwise zero contributions can interact incorrectly with packer zero metadata.

Benchmark a real spilled-partial-sum loop against unpack-old-sum→FPU-add→pack, including setup and synchronization. Retaining the sum in Dst remains another baseline when capacity allows. Formats and accumulation order can change numerical error, so report that with throughput. L1 accumulation does not by itself implement a remote all-reduce.

**SFPLOADMACRO coverage should expand, not start over**

Current RMSNorm tests cover load/MAD square accumulation and load/multiply/store. Missing isolated cases include a rounding stage, simple+MAD combinations, LReg16 intermediates, cycle-counted versus instruction-counted delays, operand substitution, and long sequences with normal instructions between macros. The [Blackhole specification](../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADMACRO.md) notes that a scheduled instruction can silently displace a normal instruction targeting the same sub-unit that cycle. A completed kernel is not sufficient evidence of a correct macro schedule.

Good next workload: load→scale/bias→convert→store, with a known-good explicit instruction sequence and a raw/numerical oracle. Sweep legal delays and pipeline depth, check a long stream with a short tail, and time both complete L1→L1 work and the prepared core loop.

**Other useful device paths**

- **Native BFP8/BFP4/BFP2 and integer FPU.** Full exponent-section pack/unpack, signed extremes, mixed scales, INT8×INT8 accumulation and saturation. The FP4 probe uses a forced exponent and established BFP4 semantics; it is not a full block-format test. Q6 dequantization does not test integer FPU arithmetic. Judge compressed formats using bytes moved, accuracy and complete compute time.
- **Local copies and zeroing.** Compare TDMA/XMOV, NoC loopback, and scalar copies, with small/large blocks and concurrent pack/unpack traffic. There is a [Blackhole TDMA interface](../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tdma_xmov.h); missing Blackhole ISA detail should be resolved before porting Wormhole assumptions. This engine is distinct from DRISC GDDR DMA.
- **TRISC2 RVV and scalar ISA features.** Blackhole [documents](../../tt-isa-documentation/BlackholeA0/TensixTile/BabyRISCV/InstructionSet.md) a partial vector extension on TRISC2, local-L1 AMOs, address-generation/bit-manipulation instructions, and scalar half/BF16 FP modes. Candidate uses are metadata, small tails and packed conversion. Compare total overhead with SFPU/NoC paths and test supported instructions individually; TRISC2 is already valuable as the pack controller.
- **L1 arbitration and ordering.** Sweep relative buffer offsets/alignment with simultaneous NoC, unpack, pack and RISC accesses. Add producer→consumer visibility tests under repeated reuse. Existing Dst contention results do not determine L1 contention, and scalar FENCE timing does not prove all MMIO ordering. Use Blackhole-specific memory-ordering rules; the shared Wormhole L1 page contains numerical/ISA claims that do not all apply to Blackhole.
- **Configuration and launch amortization.** Test alternating `CFG_STATE_ID` contexts, AutoTTSync tracking versus explicit synchronization, replay load-and-execute and MOP boundary cases against equal-output baselines. Existing firmware tests check cache/fusion configuration; they don't characterize code-size/alignment thresholds or all state changes over repeated warm launches.
- **Wider system scope.** Ethernet transport, L2 CPU/cache and physical PCIe DMA do not have dedicated tests here. They are lower priority for the current single-card decode program unless the intended architecture starts using them.

**Strengthen two existing baselines before comparing new transport engines**

1. [Remote CB test](movement/test_remote_cb.py): sends one or eight pages into depth eight, with repeated first/last-word values. It does not explicitly force sustained ring wrap or a slow-consumer episode, even though the helper supports a delay. Send many ring capacities with per-page identities, a delayed receiver and full payload checks. This would catch stale/reordered/overwritten middle pages that endpoint sentinels miss.
2. [NoC test data](movement/test_noc.py): the pattern repeats every 4096 bytes, and several later sweeps check only timing. Whole 16 KiB page or equal-pattern shard swaps can be invisible to the current byte comparison. Give each bank/page/core/iteration a distinct pattern, poison destinations between selected cases, and verify each transport variant before trusting its throughput. The asymmetric traffic test explicitly only asserts positive reported rates.

**How to explore modifier bits productively**

Use a constrained matrix of documented encodings and independently varied operands, not unconstrained random instruction words. Some encoder arguments reserve more bits than are meaningful; a value fitting the Python encoder is not proof of supported hardware semantics. Keep unknown/reserved-bit characterization separate from supported-operation tests.

For each mode: distinct lane/register values; legal source/destination aliasing; sign/zero/boundary values; sparse predicates; boundary addresses and poison guards; and a control sequence implementing the same operation. Randomize operands and legal placements after the small discriminating cases. Inspect raw outputs before using pack conversion as an oracle for unfamiliar integer or mixed-format Dst layouts.

For performance: record completion inside the interval, separate setup-inclusive from prepared steady-state timings, warm up, interleave baseline/candidate runs, and retain useful bytes or operations rather than just instruction count. For streams/DMA, include a useful concurrent RISC/compute workload to quantify offload, and report receiver completion and stage memory alongside bandwidth. No new hardware experiments were run for this audit.

**Complete test-file inventory**

The following inventory is generated from the reviewed Python ASTs; function counts are before parametrization. Names identify intended coverage, not proof that every variant has a complete correctness oracle.

| File | Functions | Explicit test subjects |
|---|---:|---|
| [compute/fpu/test_arithmetic_slots.py](compute/fpu/test_arithmetic_slots.py) | 1 | arithmetic source slot placement |
| [compute/fpu/test_dst_bandwidth.py](compute/fpu/test_dst_bandwidth.py) | 3 | dst payload throughput; dst contention; dst switch frequency |
| [compute/fpu/test_elwmul_slots.py](compute/fpu/test_elwmul_slots.py) | 1 | hifi2 elwmul source slot placement |
| [compute/fpu/test_mean.py](compute/fpu/test_mean.py) | 2 | arange1024 mean; mean bf16 precision control |
| [compute/fpu/test_mean_fpu_only.py](compute/fpu/test_mean_fpu_only.py) | 2 | mean fpu only; mean tf32 recopy precision |
| [compute/fpu/test_rmsnorm_blog.py](compute/fpu/test_rmsnorm_blog.py) | 2 | blog comparison; matched optimized comparison |
| [compute/fpu/test_rmsnorm_hybrid.py](compute/fpu/test_rmsnorm_hybrid.py) | 7 | hybrid rmsnorm; square macro precision; unpack prefetch; unpack prefetch timeline; elwmul mop; elwmul mop production; hifi3 |
| [compute/fpu/test_rmsnorm_llama3.py](compute/fpu/test_rmsnorm_llama3.py) | 2 | llama3 rmsnorm; rmsnorm side by side |
| [compute/fpu/test_rmsnorm_reduce.py](compute/fpu/test_rmsnorm_reduce.py) | 5 | arange1024 bf16 rmsnorm reduce; arange1024 bf16 rmsnorm; rmsnorm weight cycles; rmsnorm reduce cycles; rmsnorm cycles |
| [compute/fpu/test_sum_finish.py](compute/fpu/test_sum_finish.py) | 2 | sum finish cycles; sum finish precision |
| [compute/sfpu/test_q6.py](compute/sfpu/test_q6.py) | 4 | q6 byte transport; q6 decode; q6 large transport; q6 full batch |
| [movement/packer/test_pack.py](movement/packer/test_pack.py) | 3 | pack runtime rows from dst to row major cb; packer activation is a standalone partial kernel; deterministic and stochastic bf16 format conversion |
| [movement/packer/test_pack_fp8.py](movement/packer/test_pack_fp8.py) | 3 | fp8 pack runtime tail; fp8 pack zero and subnormal values; fp8 pack truncates mantissa |
| [movement/packer/test_scatter.py](movement/packer/test_scatter.py) | 3 | pack contiguous vs scattered dst to dram; pack reused output address to dram; pack four read interfaces to dram |
| [movement/packer/test_scatter_formats.py](movement/packer/test_scatter_formats.py) | 3 | scatter pack formats and order; scatter pack exact tail; scatter pack wrapping cb |
| [movement/sfpu/test_column_exchange.py](movement/sfpu/test_column_exchange.py) | 1 | column exchange |
| [movement/sfpu/test_load_lanes.py](movement/sfpu/test_load_lanes.py) | 1 | arange256 sfpu lanes |
| [movement/sfpu/test_predication.py](movement/sfpu/test_predication.py) | 1 | sfpu predication |
| [movement/test_atomic.py](movement/test_atomic.py) | 2 | two core atomic fetch add returns old value; atomic return and no return timing |
| [movement/test_dma_upload.py](movement/test_dma_upload.py) | 3 | upload block tails; queued upload download overwrite; tagged dma uses upload scatter |
| [movement/test_indexed.py](movement/test_indexed.py) | 3 | brisc indexed gather with duplicate ids; brisc indexed scatter last duplicate wins; llama3 embedding gather benchmark |
| [movement/test_noc.py](movement/test_noc.py) | 3 | interleaved dram bandwidth through cb; asymmetric interleaved bank split bandwidth; many core interleaved dram copy scaling |
| [movement/test_remote_cb.py](movement/test_remote_cb.py) | 1 | send pages remote cb unicast and multicast |
| [movement/test_upload_stream.py](movement/test_upload_stream.py) | 4 | upload slot reuse and tails; upload context drains on exception; upload rejects queued staging; direct checkpoint upload |
| [movement/unpacker/test_dst_paths.py](movement/unpacker/test_dst_paths.py) | 2 | l1 to dst paths; dst path precision |
| [movement/unpacker/test_fp4_probe.py](movement/unpacker/test_fp4_probe.py) | 1 | raw fp4 probe |
| [movement/unpacker/test_unpack.py](movement/unpacker/test_unpack.py) | 5 | unpack f32 row major to each dst tile; partial unpack to dst uses a runtime bounded mop; unpack bf16 row major tile to source bank; parallel unpack places two row major tiles in srca and srcb; benchmark parallel unpack against two individual unpacks |
| [movement/unpacker/test_unpack_fp8.py](movement/unpacker/test_unpack_fp8.py) | 3 | fp8 source bank; fp8 parallel source banks; fp8 host subnormal cleanup is redundant |
| [operation_pocs/fpu/test_bf16.py](operation_pocs/fpu/test_bf16.py) | 1 | bf16 dst |
| [operation_pocs/fpu/test_fpu.py](operation_pocs/fpu/test_fpu.py) | 1 | operation |
| [operation_pocs/fpu/test_row_major_mapping.py](operation_pocs/fpu/test_row_major_mapping.py) | 1 | row major matrix mapping |
| [operation_pocs/runtime/test_runtime.py](operation_pocs/runtime/test_runtime.py) | 7 | external; cb primitive; semaphore primitive; cb blocking; semaphore blocking; source flags; source flag blocking |
| [operation_pocs/sfpu_math/test_math.py](operation_pocs/sfpu_math/test_math.py) | 9 | operations; masks placement; aliases; native; repeated short operations; reciprocal boundaries; exp boundaries; exp same domain comparison; exception characterization |
| [operation_pocs/sfpu_movement/test_operations.py](operation_pocs/sfpu_movement/test_operations.py) | 5 | load lane mapping; movement; predicate; registers and aliases; immediate and store bits |
| [operation_pocs/transport/test_dst.py](operation_pocs/transport/test_dst.py) | 1 | dst prefixes |
| [operation_pocs/transport/test_edges.py](operation_pocs/transport/test_edges.py) | 1 | signed and rounding edges |
| [operation_pocs/transport/test_scatter_unpack.py](operation_pocs/transport/test_scatter_unpack.py) | 5 | scattered source unpack; scattered matrix pairs; native scattered source unpack; native scattered matrix pairs; scattered dst unpack |
| [operation_pocs/transport/test_source.py](operation_pocs/transport/test_source.py) | 1 | source prefixes |
| [operation_pocs/transport/test_transport.py](operation_pocs/transport/test_transport.py) | 1 | pack all prefixes |
| [test_profiler.py](test_profiler.py) | 1 | profiles a kernel on hardware |
| [timing/test_firmware_cache.py](timing/test_firmware_cache.py) | 2 | firmware instruction fusion; worker instruction caches |
| [timing/test_instruction_timing.py](timing/test_instruction_timing.py) | 3 | riscv timing; sfpu timing; timing context |
