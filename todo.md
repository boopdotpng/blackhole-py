# blackhole-py-rewrite performance TODO

This backlog contains only behavior that is missing, incomplete, or likely
incorrect in `blackhole-py-rewrite`. It intentionally omits capabilities the
rewrite already has, including fixed-size NoC read/write streams, posted write
batches, modulo-safe completion waits, chunked linked multicast, two selectable
NoC instances, generic MOP/replay support, and basic unpack-to-Dst support.

## P0: correctness and pipeline foundations

### Fix pack tile selection

`Pack.move(tile_index=N)` currently runs the entire pack MOP `N + 1` times:

```py
self.tensix.mop.run(repeat=tile_index + 1, mop_type=1)
```

This does not match the Blackhole LLK pack path. Tile selection should program
the packer W address counter to `tile_index`, then execute the tile MOP once.

- Add the equivalent of `set_dst_write_addr(tile_index)` using `TTSETADC` with
  the packer channel and W dimension.
- Run the pack MOP exactly once per tile.
- Add tests for nonzero tile indices, especially the last BF16 and FP32 Dst
  slots.
- Verify both produced bytes and Tensix instruction count.

References:

- `ttk/pack.py`, `Pack.move`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h`,
  `set_dst_write_addr`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_pack.h`, `_llk_pack_`

### Implement circular-buffer synchronization

The rewrite records `CBConfig`, but it has no runtime circular-buffer API.
Implement the producer/consumer protocol needed to overlap BRISC reads, Tensix
compute, and NCRISC writes:

- `reserve_back`
- `push_back`
- `wait_front`
- `pop_front`
- read/write pointer access
- wrap-safe occupancy counters
- Tensix received/acknowledged integration

Port the working behavior from `../blackhole-py/ttk/cb.py` into the rewrite's
typed builder and fixed resident-firmware ABI. Do not restore the old launch
message or dynamic CB descriptor layout.

Add a two-slot pipeline test proving that the reader can fill tile N+1 while
math consumes tile N and the writer drains tile N-1.

### Replace ad hoc L1 flags with explicit pipeline primitives

`examples/add1.py` synchronizes roles with ordinary L1 polling flags. Retain
simple flags for bring-up tests, but production kernel examples should use CB
occupancy and Tensix semaphores so data movement and compute can overlap without
whole-stage serialization.

## P1: NoC and DRAM data movement

### Add a real DRAM/tensor address generator

`DramAllocator` allocates per-bank address space, but kernels have no accessor
that maps a logical page or tile to its DRAM bank, endpoint coordinate, and
bank-local byte address.

Implement specialized address generators for:

- sequential interleaved tiled pages
- row-major pages/sticks
- power-of-two page sizes without division
- compile-time constant page sizes and bank counts
- runtime page indices
- harvested DRAM endpoint maps
- sharded L1 and DRAM layouts

Avoid emitting `divu`/`remu` per page when a mask/shift or incrementing cursor
can be used. For sequential loops, expose an iterator/cursor that advances the
bank and local address incrementally.

Port the coordinate and harvesting behavior from:

- `../blackhole-py/ttk/addrs.py`
- `../blackhole-py/ttk/blackhole_coords.py`
- `../blackhole-py/ttk/noc.py`, `dram_tile_addr_static`

Use TT-Metal's `TensorAccessor` and power-of-two/interleaved accessors as the
semantic reference, not as an ABI dependency.

### Add transaction-ID-scoped completion

The rewrite can batch against global NIU counters, but it cannot tag independent
read/write streams and wait or poll for one pipeline slot without draining
unrelated traffic.

Add:

- packet-tag programming for transaction IDs 0-15
- safe reset of outstanding-ID counters
- per-ID read completion wait
- per-ID write-sent/completion wait where supported
- nonblocking per-ID polling
- issue-count protection against the 8-bit outstanding counter wrapping
- transaction IDs on stateful one-packet streams

Port the validated read path from `../blackhole-py/ttk/noc.py`, including
`noc_async_read_set_trid`, `noc_wait_trid_issue_safe`, and
`noc_async_read_barrier_with_trid`.

### Add topology-aware NoC selection

The builder exposes NoC 0 and NoC 1, but program lowering does not select them
using source/destination topology or traffic direction.

- Translate logical worker and DRAM coordinates into each NoC's raw view.
- Estimate directional torus hops for both NoCs.
- Select or specialize the reader/writer NoC per core and bank.
- Prefer complementary NoCs for concurrent reader and writer traffic.
- Preserve an explicit override for experiments and deterministic tests.

### Add missing NoC operations and options

Add only operations that provide a concrete synchronization or instruction
count benefit:

- register/32-bit inline writes with byte enables
- custom virtual-channel selection
- multicast semaphore set/increment
- multicast atomic increment
- configurable atomic increment and wrap values
- source-including/loopback multicast
- full, read, write, flush-only, and atomic barrier forms
- nonblocking completion tests

Blackhole inline writes to L1 may be emulated through a scratch location due to
the hardware workaround. Benchmark them before using them as the default L1
semaphore path; inline register writes remain independently useful.

## P1: reusable FPU math paths

### Replace raw per-example math sequences with typed templates

`ttk/math.py` currently configures formats and runs an arbitrary MOP, but does
not describe or construct the standard Blackhole math operations. Add named,
validated templates for:

- `ELWADD`, `ELWSUB`, and `ELWMUL`
- unary SrcA-to-Dst and SrcB-to-Dst copies
- matmul/MVMUL
- SUM/AVG/MAX/MIN reductions using GAPOOL/GMPOOL
- destination transpose

Each template must model:

- LoFi, HiFi2, HiFi3, and HiFi4 where the hardware operation supports them
- none, row, column, and scalar SrcB broadcast
- accumulate-to-Dst
- destination reuse into SrcA or SrcB
- BF16 versus FP32 Dst accumulation
- half/full Dst synchronization
- one-, two-, and four-face tensor shapes
- partial/tiny faces where the LLK supports them

The generated MOP, replay contents, address modifiers, and required stalls
should be owned by the template rather than copied into examples.

References:

- `../tt-llk/tt_llk_blackhole/llk_lib/llk_math_eltwise_binary.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_math_matmul.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_math_reduce.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_math_unary_datacopy.h`

### Add fused multiply/reduce-scalar

Add the Blackhole GAPOOL-based fused multiply/reduce path as an alternative to
performing an entire RMSNorm square and reduction through SFPU rows.

The implementation needs:

- destination-to-SrcA/SrcB reuse
- column reduction across one-, two-, or four-face tiles
- final scalar reduction
- LoFi through HiFi4 phases
- FP32 accumulation support
- explicit DVALID cleanup

Reference:

- `../tt-llk/tt_llk_blackhole/llk_lib/experimental/llk_math_mul_reduce_scalar.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/experimental/llk_unpack_mul_reduce_scalar.h`

Keep this behind an experimental API until it is compared with the SFPU path
for accuracy and cycles on hardware.

## P1: SFPU layer

### Implement a typed SFPU API

The assembler contains the raw Blackhole SFPU encodings, but the rewrite has no
`ttk/sfpu.py`. Add a deliberately small layer that provides:

- allocation and lifetime tracking for L0-L7
- named programmable and architectural constants
- typed Dst loads/stores for FP32, FP16A, BF16, INT32, INT8, LO16, and HI16
- arithmetic, MAD, immediate arithmetic, and `SFPARECIP`
- comparisons and structured condition-code scopes
- casts and stochastic rounding
- exponent, mantissa, sign, shift, and bitwise operations
- LUT and FP32-LUT operations
- transpose and lane/row reshuffling
- reusable face/slice iteration with correct RWC/address-modifier setup
- explicit hazard insertion where Blackhole requires it

Do not begin by porting every TT-Metal activation. First provide trustworthy
primitives and use them to implement the hot Llama operations: exp, reciprocal,
rsqrt, SiLU, rotary arithmetic, masking, and reductions.

### Prototype the Blackhole SDPA SFPU fast path

The current TT-Metal Blackhole SDPA implementation contains useful kernels the
rewrite does not expose:

- scaled exponential with selectable polynomial degree
- native-approximate versus polynomial exponential
- BF16 versus FP32-Dst variants
- first-column reciprocal
- fused max selection, max subtraction, exponential rescaling, and sum update

Reference:

- `../tt-metal/tt_metal/hw/ckernels/blackhole/metal/llk_api/experimental/llk_sfpu/ckernel_sfpu_sdpa.h`

Treat this as experimental. Add accuracy vectors and cycle counts before using
it in the default attention path.

## P1: unpack fast paths

### Automatically ping-pong unpack configuration contexts

The rewrite can configure contexts 0 and 1, but ordinary `move()` calls do not
acquire, alternate, and release them as a pipeline. Implement the LLK-style
context protocol:

- wait for the next free context
- program only that context's base/offset words
- publish context acquisition
- issue the MOP
- release and toggle the context

Preserve an explicit context-selection escape hatch for unusual kernels and
tests.

### Add operation-specific unpack templates

Add named unpack paths for:

- A only, including none/row/column/scalar broadcast
- fused A+B eltwise
- matmul A+B with reuse-A/reuse-B selection and replay-driven address advance
- unpack-to-Dst and destination reuse
- tilize A
- tilize A plus B/reload
- untilize
- SUM/AVG/MAX/MIN reduction
- fused multiply/reduce-scalar phase switching

The templates must support transpose-of-faces, within-face transpose/haloize,
one/two/four faces, partial faces, zero fill, negative-infinity fill, and the
format combinations actually accepted by the hardware.

References:

- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_A.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB_matmul.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_untilize.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB_reduce.h`

### Investigate excess unpack-to-Dst serialization

The direct-to-Dst path currently inserts a scoreboard drain after every face.
This is known-safe for TTSIM and the ported RMSNorm path, but may serialize more
than the hardware requires. Compare it against TT-LLK's MOP/context sequences
and retain the per-face drain only where device tests demonstrate it is needed.

## P1: pack fast paths and features

### Add contiguous multi-tile block pack

Implement a pack path that programs replay/MOP once and packs a runtime number
of contiguous Dst tiles to dense L1. Changing only `num_tiles` must not require
reprogramming tile geometry.

Reference:

- `../tt-metal/tt_metal/hw/ckernels/blackhole/metal/llk_api/experimental/llk_pack_block_api.h`

### Add pack tilize, untilize, and row paths

Implement specialized address modifiers and MOP/replay programs for:

- tilize
- row-at-a-time tilize
- untilize
- strided untilize
- dense two-face untilize
- partial-row pack

References:

- `../tt-metal/tt_metal/hw/ckernels/blackhole/metal/llk_api/experimental/llk_pack_fast_tilize_api.h`
- `../tt-metal/tt_metal/hw/ckernels/blackhole/metal/llk_api/experimental/llk_pack_fast_untilize_api.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_pack_untilize.h`
- `../tt-llk/tt_llk_blackhole/llk_lib/llk_pack_rows.h`

Keep the TT-Metal `fast_*` variants experimental until benchmarked against the
ordinary pack implementation.

### Add missing packer configuration

The rewrite currently covers a basic tile conversion and FP32-Dst read mode.
Add typed state and minimal-diff lowering for:

- stochastic rounding in the packer and gasket
- pack-time ReLU/min/max thresholding
- L1 accumulation
- zero-output mode
- reduction masks
- one-, two-, and four-face shapes
- tiny/partial faces
- multiple tiles per MOP
- source/destination format reconfiguration without rebuilding unrelated state

## P2: data formats

### Expand `DType`

`program.DType` currently supports only F32 and BF16. Add correct storage size,
tile size, descriptor encoding, unpack conversion, SFPU load/store modifier,
and pack behavior for:

- FP16A
- BFP8/BFP8-B
- BFP4/BFP4-B
- BFP2/BFP2-B
- TF32
- LF8
- FP8 e4m3 where the software encoding is required
- INT8/UINT8
- UINT16
- INT32/UINT32

Compressed BFP tile size must include exponent storage and must not be derived
as `1024 * itemsize`.

Reject unsupported source/destination combinations at program construction
rather than silently selecting BF16 as the unpack output format.

## Verification and performance gates

Every fast path should have three levels of validation:

1. Encoding/state tests that compare configuration words, MOP words, replay
   contents, address modifiers, and emitted instruction counts with the
   corresponding Blackhole LLK sequence.
2. TTSIM tests for data, context ownership, scoreboard behavior, CB wrap, and
   role synchronization.
3. Hardware microbenchmarks reporting cycles/tile, NoC bytes/cycle, issue
   instructions/transaction, numerical error, and behavior at counter wrap.

Do not adopt the deprecated NoC blitz-write setup. The rewrite's stateful
stream abstraction is the correct base; extend it with transaction IDs,
address generators, and missing operation types instead.
