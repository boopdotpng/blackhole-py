# Blackhole Tensix synchronization, setup, and handoff protocols

Status: working hardware contract for `blackhole-py`

This document answers the operational question:

> If the lowerer explicitly emits operation X, what must it configure, what
> must it wait for, and what must it publish or release before operation Y?

The lowerer discussed here does **not** choose the data-movement or computation
schedule. It explicitly emits the intended sequence:

```text
NoC read -> L1/CB -> unpack -> FPU/SFPU -> pack -> L1/CB -> NoC write
```

The dependency graph records that chosen sequence. A protocol-expansion layer
adds or validates the stalls, semaphore operations, counter waits, context
operations, and configuration drains required by each explicit handoff.

The main references are:

- the working kernels in `examples/llama3.py`;
- the row-major bring-up in `examples/llama3_row_major.py`;
- `ttk/noc.py`, `ttk/cb.py`, `ttk/unpack.py`, `ttk/fpu.py`,
  `ttk/sfpu.py`, `ttk/pack.py`, `ttk/mop.py`, and `ttk/sync.py`;
- Blackhole LLK under
  `../tt-llk/tt_llk_blackhole/common/inc` and
  `../tt-llk/tt_llk_blackhole/llk_lib`;
- the older direct-to-Dst RMSNorm bring-up in git history.

Statements are classified as:

- **current**: used by a working `blackhole-py` Llama kernel;
- **LLK**: present in the official Blackhole LLK but not necessarily used by
  current `blackhole-py`;
- **empirical**: found necessary during local hardware bring-up;
- **incomplete**: partially implemented and unsafe to use as a complete
  protocol.

## 1. Dependency classes

Do not collapse all dependencies into “sync.” There are at least eight
different things that can make a consumer unsafe:

| dependency | question being answered | mechanism |
|---|---|---|
| data readiness | Have the bytes or engine values arrived? | NoC counters, CB credits, Src valid flags |
| storage lifetime | May the producer overwrite/reuse the storage? | NoC source completion, CB pop, Dst ownership |
| engine completion | Has an issued unpack/math/SFPU/pack command finished? | `TTSTALLWAIT` scoreboard |
| configuration visibility | Has a configuration write reached the engine? | `TRISC_CFG`, `CFG`, `THCON`, engine drains |
| cross-thread ownership | Which TRISC may use Dst or direct-to-Dst now? | Tensix semaphores |
| finite capacity | Is there room in a CB, TID bucket, Dst section, or Replay FIFO? | counters, sem max, allocation |
| address/counter state | Is the engine pointing at the intended fragment? | `SETADC*`, `SETRWC`, address modifiers, context selection |
| instruction latency | Is a register result ready for the next instruction? | compiler-inserted NOPs and fixed hazard rules |

A RISC-V `fence` only helps with RISC memory/MMIO ordering. It does not wait
for NoC data, unpack, math, SFPU, pack, or a Tensix semaphore condition.

## 2. Quick dependency chart

This is the first chart to consult while writing an explicit movement.

| explicit operation | wait before issue | required setup | wait before consuming/reusing result | handoff/release |
|---|---|---|---|---|
| NoC read to private L1 | free TID; old TID counters zero; issue-safe response count; NIU command slot free | endpoints, addresses, size, return coordinate, TID | `requests_outstanding[TID] == 0` before reading L1 | release TID after remote completion |
| NoC read to CB | `CB.reserve_back`; same NoC conditions as read | CB write pointer as target | read response complete before `CB.push_back` | push publishes page to consumer |
| local RISC fill of CB | `CB.reserve_back` | CB write pointer and exact local stores | local stores/fence complete before push | `CB.push_back` |
| consume CB in unpack | `CB.wait_front`; relevant Src bank clear | unpack context, descriptors, base, format, strides, ADCs, MOP | current conservative path drains `UNPACK0/1`, releases context, then pops | `CB.pop_front` only after unpack no longer reads page |
| unpack to SrcA | `SRCA_CLR`; free unpack context | unpacker 0 -> SrcA, address swizzle enabled, correct source format/layout | math waits `SRCA_VLD`; unpack waits `UNPACK0` before reconfigure/pop | math instruction must clear/release SrcA on its final use |
| unpack to SrcB | `SRCB_CLR`; free unpack context | unpacker 1 -> SrcB, correct source format/layout | math waits `SRCB_VLD`; unpack waits `UNPACK1` before reconfigure/pop | math instruction must clear/release SrcB on its final use |
| unpack directly to Dst | two-sided `MATH_DONE` / `UNPACK_TO_DEST` protocol; pack not using Dst | disable SrcA swizzle, direct-Dst mode, Dst byte address, direct-Dst stride, unpack context | **empirical:** drain `UNPACK0` after every direct `UNPACR`; final `THCON|UNPACK0` drain | restore stride/mode/swizzle; post `UNPACK_TO_DEST`; math gets token |
| FPU from SrcA/SrcB | Dst available; `SRCA_VLD` and/or `SRCB_VLD` | Dst base/view, address modifiers, fidelity, RWC counters, zero/accumulate policy | drain `MATH` before SFPU/config change/publish where required | final issue/address modifier clears consumed source banks |
| FPU accumulate into live Dst | caller already owns Dst; prior Dst producer complete | same Dst view/base; do not zero accumulator | drain relevant math before a different engine reads Dst | retain Dst ownership; do not post `MATH_PACK` yet |
| FPU -> SFPU on same Dst | caller owns Dst | SFPU Dst base/view and lane configuration | `STALL_SFPU` on `MATH` before SFPU reads | retain Dst or publish after SFPU drain |
| SFPU -> FPU/Dst reuse | caller owns Dst | SFPU stores result to defined Dst footprint; configure `MOVD2A/B` and source state | drain `SFPU` before math consumes stored Dst | retain Dst; source bank later released by math |
| publish Dst to pack | caller owns Dst; all Dst writers complete | none beyond consistent Dst section/view | drain `MATH|SFPU` | `SEMPOST(MATH_PACK)` exactly once per handoff |
| pack Dst to CB | `MATH_PACK != 0`; `CB.reserve_back` | pack source view, format, Dst offset, L1 destination, edge/row masks, ADCs, MOP | drain `PACK0` and PC buffer before push/reconfiguration | push CB; normally `ZEROACC`; `SEMGET(MATH_PACK)` |
| pack same Dst more than once | acquire `MATH_PACK` once | reprogram destination for each output as needed | drain each pack before reusing output slot | retain semaphore token and Dst contents until final copy |
| NoC write from CB | `CB.wait_front`; free TID and NIU slot | endpoints, source CB pointer, size, posted policy | wait `writes_outgoing[TID] == 0` before `CB.pop_front`; non-posted also waits remote ack | pop only when NIU no longer reads source |
| change unpack configuration | all selected contexts free or a free alternate context | descriptors/options/base/strides/context ID | `TRISC_CFG` before issue; selected unpack engine drain before overwrite | release/switch context |
| change FPU/SFPU Dst view/base | current math/SFPU access complete | FP32 flags, Dst row base, SFPU lane config | `STALL_CFG` on `MATH|SFPU` as applicable | new view becomes part of live Dst type |
| change pack configuration/destination | previous pack/THCON use complete | formats, strides, destination address/valid bit, offsets, masks | `STALL_CFG` on `PACK0`/`THCON`; `DMANOP` where required | subsequent pack uses new config |
| reprogram MOP | previous MOP expansion complete | nine MOP template words | `PC_BUF_MOP_SYNC` before overwrite | new template active |
| load/rewrite Replay slots | previous users of those slots complete | bounded non-overlapping slots and FIFO-safe sequence | `PC_BUF_SYNC` where the sequence requires it | slots remain live until no future play |
| return from a worker RISC | all async work owned by that RISC complete | completion/debug marker | NoC and engine drains as applicable | firmware subordinate reports `DONE` |

## 3. The core handoff graph

The ordinary full-Dst pipeline is:

```text
BRISC/NCRISC producer
    reserve CB
    fill CB page
    wait for NoC/local completion
    push CB
              |
              v
TRISC0 unpack
    wait CB front
    wait Src clear
    acquire/commit unpack context
    stall on TRISC_CFG
    issue unpack
    publish Src valid in hardware
    drain unpack/context
    pop CB
              |
              v
TRISC1 math/SFPU
    wait Dst available: MATH_PACK is not at max
    wait Src valid
    issue math and release Src on final use
    optionally hand Dst between FPU and SFPU
    drain writers
    post MATH_PACK
              |
              v
TRISC2 pack
    wait MATH_PACK is nonzero
    reserve output CB
    configure and issue pack
    drain PACK0
    push output CB
    clear/release Dst
    get MATH_PACK
              |
              v
BRISC/NCRISC consumer
    wait CB front
    issue NoC write
    wait until NIU releases local source
    optionally wait remote acknowledgement
    pop CB
```

The dependencies across those stages are not interchangeable. For example,
`CB.push_back` cannot replace `requests_outstanding == 0`: the push is only
correct after the read has completed. Likewise `MATH_PACK` does not indicate
that unpack has produced SrcA/SrcB; that is the source-valid scoreboard.

## 4. NoC transactions

### 4.1 Command-register availability

Each NIU has one command-register group. Before writing a command, wait for
`SEND_REQUEST == 0`. After setting `SEND_REQUEST = 1`, wait for it to return to
zero before reusing the command registers.

This only means that the NIU accepted and expanded the command. It does not
mean that read data arrived or that a write completed.

### 4.2 TID lifetime

Current `ttk` manages TIDs 1 through 15 separately for each NoC. Acquiring a
TID first verifies:

```text
writes_outgoing[TID] == 0
requests_outstanding[TID] == 0
```

The counter bucket must not be reused while either old payload reads or old
responses remain.

The issue path also waits until the selected counter is below 129. A command
that can auto-split into 128 or more packets first drains the counter to zero.
This avoids counter half-range ambiguity/overflow.

### 4.3 Read completion

A NoC read is safe to consume only after:

```text
requests_outstanding[TID] == 0
```

Consequences:

- do not load the destination L1 bytes before this wait;
- do not push a CB page before this wait;
- do not allow unpack to read the page before the push;
- do not release the TID before the wait.

`read_into_cb` and `read_tiles_into_cb` obey this order.

### 4.4 Write completion

There are two different completion points:

```text
writes_outgoing[TID] == 0
    NIU has finished reading the local L1/CB source

requests_outstanding[TID] == 0
    response/acknowledgement for a non-posted operation has returned
```

Wait for source completion before:

- popping or overwriting a source CB page;
- reusing private L1 scratch;
- returning while the source belongs to a transient kernel allocation.

Use a non-posted write and wait for remote completion when a following
operation, core, or host action depends on remote visibility. A posted write
does not create a remote acknowledgement.

Current Llama output writes are generally non-posted. The argmax reducer also
uses a non-posted write for the `{key, id, ready}` record before the reducer
polls `ready` in its local L1.

### 4.5 Atomics and publication

An atomic or flag write is not automatically a data barrier for unrelated
earlier transactions. A cross-core publication protocol must state how data
visibility is ordered before the flag/atomic becomes observable. The safe
baseline is:

```text
issue data write non-posted
wait remote completion
issue publication write/atomic
wait required completion
```

If a weaker sequence is proven for a specific NoC ordering mode, record it as
a separate protocol rather than assuming it globally.

### 4.6 Alignment and packet shape are setup constraints

The row-major K0 bring-up found that full-page read destinations must begin at
the required NoC burst alignment; 16-byte alignment alone shifted the logical
row on that path. Exact-span helpers must encode:

- source and destination alignment;
- maximum 16 KiB packet size and auto-splitting;
- DRAM stripe/bank boundaries;
- exact live byte count;
- private aligned scratch for any final transport word.

These are not synchronization conditions, but getting them wrong produces the
same symptoms as a bad handoff.

## 5. Circular buffers

Current CBs are software-managed L1 rings with 16-bit producer and consumer
counters. There are 32 channels.

For each page:

```text
producer: reserve_back -> write/fill -> push_back
consumer: wait_front   -> read/use   -> pop_front
```

### 5.1 Producer rules

`reserve_back(count)` waits until at least `count` pages are free. It must
happen before obtaining and writing the producer pointer.

`push_back(count)` is a release/publication operation. Everything that fills
the page must be complete first:

- a NoC read must have reached response completion;
- local RISC stores must be ordered;
- pack must have drained `PACK0` and any required PC-buffer work.

### 5.2 Consumer rules

`wait_front(count)` happens before reading the consumer pointer.

`pop_front(count)` releases storage back to the producer. It must happen only
after the consumer no longer accesses the page:

- unpack has drained the selected engine and context on the conservative path;
- a NoC write has reached source completion;
- local gathering/scattering has completed.

### 5.3 Initialization and topology

BRISC firmware resets the shared received/acked counters before each worker
launch. Each RISC stream initializes its private pointer and local count state
in its prologue.

The normal model is one producer and one consumer per channel. Multiple
consumers require an explicit reference-count/publication protocol; a second
consumer cannot independently `pop_front` the same single credit.

The row-major K0 uses one-credit internal CBs as readiness flags. This is valid
because the same reserve/push/wait/pop ownership protocol still applies even
when the CB page bytes are not the payload.

## 6. Tensix scoreboard: `TTSTALLWAIT`

`TTSTALLWAIT(stall_resources, wait_conditions)` connects hardware engine
scoreboards. It is the primary engine-completion mechanism.

The stallable resources are:

```text
TDMA   SYNC   PACK   UNPACK   XMOV   THCON   MATH   CFG   SFPU
```

The wait conditions are:

```text
THCON    UNPACK0   UNPACK1   PACK0   MATH
SRCA_CLR SRCB_CLR  SRCA_VLD  SRCB_VLD
XMOV     TRISC_CFG SFPU      CFGEXU
```

The left side says which hardware pipe is prevented from advancing. The right
side says which outstanding condition must clear or become satisfied. A bad
stall-resource mask can allow later instructions to pass even if the RISC
instruction stream appears ordered.

Frequently required combinations are:

| purpose | stall | wait for |
|---|---|---|
| do not overwrite SrcA | `UNPACK` | `SRCA_CLR` |
| do not overwrite SrcB | `UNPACK` | `SRCB_CLR` |
| math consumes SrcA | `MATH` | `SRCA_VLD` |
| math consumes SrcB | `MATH` | `SRCB_VLD` |
| apply TRISC unpack config before issue | `UNPACK` | `TRISC_CFG` |
| wait unpacker 0 completion | `UNPACK` or `CFG` as appropriate | `UNPACK0` |
| wait unpacker 1 completion | `UNPACK` or `CFG` as appropriate | `UNPACK1` |
| change math/SFPU-sensitive config | `CFG` | `MATH|SFPU` |
| SFPU reads FPU-produced Dst | `SFPU` | `MATH` |
| math reads SFPU-produced Dst | `MATH` | `SFPU` |
| change pack/THCON configuration | `CFG` | `PACK0|THCON` |
| publish math/SFPU Dst | `SYNC` | `MATH|SFPU` |
| finish pack before CB push | `SYNC` | `PACK0` |

There is no observed `DST_VALID`, `DST_READY`, or `DST_CLEAR` scoreboard
condition.

## 7. SrcA and SrcB lifecycle

The source banks have an actual hardware rendezvous:

```text
CLEAR
  -> unpack writes bank
  -> VALID
  -> math reads bank
  -> final math issue releases/clears bank
  -> CLEAR
```

### 7.1 Unpack side

Before loading a source bank:

```text
stall UNPACK on SRCA_CLR and/or SRCB_CLR
```

Unpack configuration selects whether unpacker 0 writes SrcA and whether
unpacker 1 writes SrcB. The unpack instruction or its paired `DVALID` behavior
publishes validity.

### 7.2 Math side

Before consuming sources:

```text
stall MATH on SRCA_VLD and/or SRCB_VLD
```

The final FPU instruction or address-modifier phase must release each bank that
will be refilled. In current code this is encoded in instruction `clear` bits,
address-modifier `src*_clear` fields, or a final `SETRWC`.

Failing to release a source generally makes the next unpack wait forever on
`SRC*_CLR`. Releasing too early allows unpack to overwrite data still needed by
the current math sequence and produces wrong results without necessarily
hanging.

### 7.3 Unary oddity

Current `copy_a` notes that the unary SrcA unpack path also advances an empty
SrcB bank, so its final `MOVA2D` releases both banks. The lowerer must use the
protocol of the selected unpack/FPU macro rather than infer source release only
from the logical number of operands.

### 7.4 Dst reuse into sources

`MOVD2A` and `MOVD2B` are math-engine operations. They do not create a magical
layout-free view of Dst. The sequence must define:

- the Dst row/view being read;
- the Src row mapping;
- whether a dummy source-valid event is required;
- source counter reset/gating (`GATESRCRST` on affected Blackhole paths);
- address-modifier increments and final source release.

The LLK explicitly waits on source valid before whole-face `MOVD2A/B` helpers
because those macros assume unpack has generated a dummy validity event. This
is one reason Dst reuse must be a named protocol rather than a raw move opcode.

## 8. Unpack setup and context lifecycle

An unpack is not just `UNPACR`. At minimum the selected macro must define:

```text
input data format
output data format
tile/fragment descriptor and dimensions
base address in unpack address units
X/Y/Z/W strides and offsets
SrcA/SrcB/direct-Dst destination
address swizzle state
transpose/haloize behavior
unpack context ID
ADC start/end counters
MOP or direct issue sequence
```

### 8.1 Configuration context

Blackhole supports two unpack configuration contexts. Official LLK pipelines
them. Current `ttk` deliberately uses a conservative stateless context-0 path:

1. poll the PC-buffer `UNPACK_SYNC` value until the selected context is free;
2. write descriptors, base addresses, strides, and options;
3. select context 0;
4. commit by writing zero to the PC-buffer semaphore access for
   `UNPACK_SYNC`, which increments the semaphore;
5. stall unpack on `TRISC_CFG` before issuing;
6. drain the selected unpack engine;
7. `TTSEMGET(UNPACK_SYNC)` to release the live context;
8. perform PC-buffer sync before reconfiguration/return on the current path.

The PC-buffer semaphore access is unusual:

```text
read                 -> current semaphore value
write value with LSB 0 -> atomic increment / POST
write value with LSB 1 -> atomic decrement / GET
```

`TTSEMPOST` and `TTSEMGET` operate on the same underlying Tensix semaphore but
through Tensix instructions.

### 8.2 Configuration visibility

Writing a config register from TRISC does not make it immediately usable by an
unpack issue. The required ordering point is normally:

```text
stall UNPACK on TRISC_CFG
```

Before overwriting configuration already in use, also drain the relevant
unpack engine or wait for all live contexts to be released.

### 8.3 Completion versus source validity

The math engine may begin after source validity is published. The current
`ttk` path nevertheless drains `UNPACK0/1` before releasing the context and
popping the input CB. This is conservative and simplifies correctness.

Future pipelining may overlap these events, but then context lifetime, CB page
lifetime, and source-bank lifetime must be represented separately.

## 9. Direct unpack to Dst

Direct-to-Dst is a separate two-sided protocol, not an alternate destination
bit on an ordinary unpack.

### 9.1 Math side

The LLK protocol is conceptually:

```text
publish requested Dst address to unpack mailbox
wait while MATH_DONE is at max
post MATH_DONE                       # math is ready for unpack
wait until UNPACK_TO_DEST is nonzero # unpack finished tile
get UNPACK_TO_DEST
drain math/SFPU before consuming Dst
```

### 9.2 Unpack side

The matching unpack sequence is:

```text
wait until MATH_DONE is nonzero
get MATH_DONE
wait while UNPACK_TO_DEST is at max

disable SrcA address swizzle
save normal unpack Z stride
enable direct-Dst interface for selected context
program direct Dst byte address and direct-Dst stride
stall UNPACK on TRISC_CFG and PACK0 as required

issue direct UNPACR face 0
drain UNPACK0                         # empirical local requirement
issue direct UNPACR face 1
drain UNPACK0
issue direct UNPACR face 2
drain UNPACK0
issue direct UNPACR face 3
drain UNPACK0
final drain THCON | UNPACK0

release UNPACK_SYNC context
restore normal unpack stride
disable direct-Dst interface
restore normal destination address
re-enable SrcA address swizzle
post UNPACK_TO_DEST
```

### 9.3 Empirical per-face drain

The older RMSNorm hardware bring-up observed only the final face when four
direct `UNPACR` operations were issued without an `UNPACK0` stall after each
one. The working bring-up sequence was:

```text
repeat four times:
    UNPACR(to_dst)
    TTSTALLWAIT(STALL_UNPACK, UNPACK0)
```

This is stronger than simply placing all four direct issues inside one MOP and
draining after the MOP. Preserve it as an empirical Blackhole protocol until a
replacement sequence is independently validated. Do not allow a generic MOP
combiner to remove these drains.

### 9.4 Current implementation status

`ttk/unpack.py` contains the unpack-side waits, mode changes, and final post,
but normal current Llama kernels do not call `UnpackTarget.DST`. There is no
general current math-side producer/consumer in `ttk` that completes the full
`MATH_DONE`/`UNPACK_TO_DEST` handshake.

Therefore the current direct-to-Dst helper is **incomplete** and must not be a
codegen target without implementing and validating the complete two-sided
protocol, including the per-face drain.

## 10. Dst ownership, validity, and view

### 10.1 There is no Dst-valid flag to wait on

Blackhole exposes no `DST_VLD`/`DST_CLR` condition analogous to SrcA/SrcB.
Current code tracks Dst through:

1. the `MATH_PACK` semaphore for math/SFPU versus pack ownership;
2. program knowledge of which Dst rows contain defined values;
3. Dst base/view configuration;
4. explicit `ZEROACC` when old contents must become zero/undefined;
5. engine drains before another engine observes the data.

`MATH_PACK` does not describe which tiles are valid. One post publishes the
chosen Dst section according to the program's contract.

### 10.2 Full-Dst ownership

Current `blackhole-py` uses full-Dst synchronization with semaphore max 1:

```text
math/SFPU:
    wait while MATH_PACK == max
    own and modify Dst
    drain MATH/SFPU
    POST MATH_PACK

pack:
    wait while MATH_PACK == 0
    read/pack Dst
    drain PACK0
    normally ZEROACC
    GET MATH_PACK
```

Posting more than once for one handoff or getting without a post corrupts the
ownership count and can deadlock a later launch phase.

### 10.3 Half-Dst ownership

Official LLK supports `SyncHalf`:

- `MATH_PACK` maximum is 2;
- math and pack maintain matching low/high Dst offset IDs;
- math flips its section after publishing;
- pack clears and flips its section after consuming.

Current `ttk` does not implement this protocol. It must not independently flip
only math or only pack offsets.

### 10.4 Dst FP32/BF16 view

The Dst view affects:

- FPU FP32 accumulation enable;
- SFPU FP32 Dst interpretation;
- tile capacity and row addressing;
- `ZEROACC` mode/addressing;
- pack source width and conversion;
- packer destination-read configuration.

Current `Dst` capacity is eight 32-bit tiles or sixteen 16-bit tiles. A Dst
tile base is represented in rows, currently `tile * 64` at the `ttk` level.

Changing the view while live data exists is not a harmless config write. Drain
math/SFPU and pack as applicable, ensure both consumers agree on the view, and
treat the view as part of the value's physical type.

### 10.5 Zeroing and accumulation

Several FPU instructions accumulate into Dst rather than overwrite it. The
lowerer must distinguish:

```text
define/overwrite result -> clear or mark target appropriately first
accumulate result       -> retain defined Dst contents and matching view
```

Current HiFi2 ELWMUL zeros all four FP32 faces when `accumulate=False`.
MVMUL similarly zeros its target unless accumulation is requested.

Pack normally zeroes Dst before returning ownership. A custom persistent-Dst
sequence may intentionally omit that clear, but then Dst contents and ownership
remain explicit live state.

## 11. FPU setup and source release

Before an FPU macro, explicitly define:

```text
Dst availability and target base
FP32/BF16 Dst mode
SrcA/SrcB required-valid set
address-modifier slots
source increments/carry/clear
Dst increments/carry/clear
fidelity phase increment/clear
RWC counter reset/start
broadcast mode
zero versus accumulate behavior
MOP/Replay sequence
```

The normal sequence is:

```text
wait MATH_PACK not at max             # unless already retaining Dst ownership
configure Dst base/view
wait CFG against MATH/SFPU as needed
reset RWC counters
wait SRCA_VLD/SRCB_VLD
issue FPU macro
release source banks on final use
retain Dst or drain and publish
```

Do not infer hardware release from the end of the Python function. It comes
from the actual instruction/address-modifier fields.

Fidelity state is another persistent hardware counter. HiFi2 sequences must
increment and clear it at the intended face/phase boundaries. A missing clear
can corrupt later operations even when all semaphores are balanced.

## 12. FPU and SFPU handoffs

FPU and SFPU share TRISC1 and Dst but are different engines.

### 12.1 FPU to SFPU

For SFPU to read an FPU-produced Dst fragment:

```text
retain Dst ownership
configure SFPU Dst base and FP32 view
stall SFPU on MATH
issue SFPU loads/operations
```

Current `Sfpu.map()` performs `STALL_SFPU` on `MATH` after setting its Dst
view. It does not require a pack/unpack round trip.

### 12.2 SFPU to FPU

An SFPU LReg is not directly visible as SrcA/SrcB. The usual route is:

```text
SFPU store -> defined Dst footprint
drain SFPU
MOVD2A or MOVD2B -> source fragment
perform any required source gate/counter reset
FPU consumes source
```

Math must stall on SFPU completion before consuming a just-stored Dst value.
The exact `MOVD2A/B` protocol also depends on the required dummy-valid and
source-counter state.

### 12.3 Multiple SFPU maps under one Dst lease

Current Llama SwiGLU and GQA issue several SFPU maps before a final publish.
Each map waits for Dst availability, but because `MATH_PACK` remains below max
the same TRISC1 phase retains ownership. Only the final operation posts
`MATH_PACK`.

The lowerer must represent this as one Dst ownership region, not independent
acquire/publish pairs for every SFPU node.

### 12.4 LReg latency hazards

SFPU register readiness is static instruction scheduling, not cross-thread
synchronization. Current `SfpuProgramBuilder` tracks `ready_at` per LReg and
inserts `SFPNOP` for read-after-write latency. Ordinary arithmetic commonly has
two-cycle result latency, and `SFPSWAP` requires a forced following NOP on
Blackhole.

These NOPs cannot be removed because the dependency graph contains a data edge;
the hardware issue latency still matters within one SFPU instruction stream.

## 13. Pack setup and completion

Packing requires more state than a Dst tile and output address:

```text
Dst source width/view
input and output data formats
rounding/accumulation controls
Dst row/section offset
L1 destination address and valid-address bit
X/Y/Z/W strides
edge masks and row mapping
packer counters
address modifiers
ADC starts and limits
MOP template
```

### 13.1 Ordinary pack protocol

Current full-Dst pack follows:

```text
wait MATH_PACK nonzero
reserve output CB
drain old PACK0/THCON configuration users
program format, view, counters, masks, and destination
stall CFG on required PACK0/THCON conditions
issue pack MOP
stall on PACK0 completion
PC-buffer sync
push output CB
ZEROACC full Dst
GET MATH_PACK
```

The CB push must be after pack completion, not merely after pack issue.

### 13.2 Retaining Dst across pack

GQA packs probability Dst0 twice for two PV consumers while retaining Dst1-5
as online-softmax state:

```text
wait MATH_PACK once
pack Dst0 -> probability CB
drain
pack Dst0 -> probability CB again
drain
GET MATH_PACK without ZEROACC
```

Later math reacquires Dst and continues accumulating into the persistent
tiles. The final context pack uses the ordinary full-Dst release and clear.

This is a named nonstandard handoff. Generic `pack` must not automatically
clear persistent tiles, and generic `release Dst` must not assume that a pack
always consumed every live Dst tile.

### 13.3 Reprogramming pack destination

Before `WRCFG` changes the L1 destination or Dst offset, the configuration path
must wait for the relevant `THCON`/`PACK0` users. Blackhole LLK additionally
places `DMANOP` instructions after some `WRCFG` sequences. Treat those fixed
delays as part of the pack configuration protocol.

## 14. MOP and Replay reconfiguration

### 14.1 MOP reconfiguration

MOP templates are shared state for the selected pipe. Before overwriting the
nine MOP configuration words, current `Mop.configure()` performs
`PC_BUF_MOP_SYNC`.

Do not rewrite a template while an earlier MOP expansion still depends on it.

### 14.2 Replay storage

Replay has 32 instruction slots in the current model. Loading and playing
Replay also interacts with the PC/instruction expansion pipeline; current
matmul and SFPU code uses explicit `sync()` at validated boundaries.

### 14.3 Deferred: slot and expansion-FIFO capacity

The SFPU implementation records a Blackhole-specific hazard: a four-face MOP
containing Replay instructions can saturate the FIFO between the MOP and Replay
expanders. Current code runs one face per MOP. `row_major_mvmul.py` similarly
splits long MVMUL Replay sequences.

Replay slot allocation, MOP expansion capacity, and the MOP-to-Replay FIFO will
eventually need explicit capacity resources. They are intentionally outside the
first operation/handoff IR. For now:

- use only already-tested MOP/Replay templates;
- preserve their existing split points verbatim;
- do not combine adjacent MOP or Replay runs as an optimization;
- investigate and model capacity when a new sequence reaches this limit.

## 15. Configuration ownership and mutexes

Some configuration registers are shared across TRISCs. Official LLK uses:

| mutex | index | purpose |
|---|---:|---|
| `REG_RMW` | 0 | atomic read-modify-write of shared configuration registers |
| `SFPU` | 4 | SFPU ownership when instructions may be issued from TRISC1 and TRISC2 |

`isa.py` encodes `ATGETM` and `ATRELM`, but current `ttk` does not expose or use
a mutex protocol.

This is a current gap. In particular, unpack, math, and pack all modify fields
within shared ALU/config words. A safe lowerer must either:

1. prove those configuration phases cannot overlap, then drain the relevant
   engines before each write; or
2. acquire the official `REG_RMW` mutex around shared RMW sequences.

If SFPU remains exclusively on TRISC1, mutex 4 may be unnecessary. If codegen
allows TRISC2 SFPU issue, mutex 4 becomes part of every ownership transfer.

## 16. Tensix semaphores

Blackhole has eight architecturally assigned Tensix semaphores:

| index | name | protocol | current status |
|---:|---|---|---|
| 0 | `FPU_SFPU` | custom FPU/SFPU or producer/SFPU handoff | current code uses it for BRISC PRNG seed publication |
| 1 | `MATH_PACK` | Dst ownership between math/SFPU and pack | active in all compute Llama kernels |
| 2 | `UNPACK_TO_DEST` | unpack direct-to-Dst completion/ownership | unpack side present; complete generic protocol missing |
| 3 | `UNPACK_OPERAND_SYNC` | unpack operand mailbox get/release with math/pack | defined, unused in current `ttk` |
| 4 | `PACK_DONE` | pack-iteration instrumentation/delay or custom pack->unpack sync | defined, unused in current `ttk` |
| 5 | `UNPACK_SYNC` | live unpack configuration contexts | active |
| 6 | `UNPACK_MATH_DONE` | instrumentation around either unpack or math iteration | defined, unused in current `ttk` |
| 7 | `MATH_DONE` | math-ready half of direct-to-Dst handshake | firmware initializes it; no complete current producer API |

Semaphore semantics:

```text
SEMINIT(max, initial)
SEMPOST -> increment up to max
SEMGET  -> decrement down to zero
SEMWAIT(..., STALL_ON_ZERO) -> block selected resources while value == 0
SEMWAIT(..., STALL_ON_MAX)  -> block selected resources while value == max
```

The semaphore selector is a bit mask, not the raw index.

Current BRISC firmware explicitly initializes semaphores 0, 1, 2, and 7 to
initial 0, max 1 before each launch. Semaphore 5 is maintained by balanced
PC-buffer post/get operations. Any new use of semaphores 3, 4, or 6 must define
and perform initialization rather than relying on stale state.

## 17. Firmware launch and completion

Before each worker launch, current firmware:

- resets most Tensix configuration state;
- clears Dst with `ZEROACC`;
- establishes SFPU constant/config state;
- initializes semaphores 0, 1, 2, and 7;
- resets shared CB counters;
- zeroes each TRISC register file in its run prologue;
- publishes `GO` to NCRISC and the three TRISCs.

BRISC then executes its own worker image and waits for all four subordinates to
report `DONE`. Only then does it mark the worker launch complete and increment
the dispatch completion counter.

Returning from a RISC image is therefore an ownership handoff to firmware. A
stream must not return while it still owns:

- a NoC source buffer being read by the NIU;
- a required non-posted response;
- an unpack context;
- a source bank that a following launch assumes clear;
- unpublished or pack-owned Dst state;
- an outstanding pack whose CB has not been published;
- a mutex.

Firmware reset provides a useful launch boundary, but it is not a substitute
for completing external NoC effects or balanced software protocols.

## 18. RISC memory flags and cross-core handoffs

Current code also uses ordinary L1 flags and NoC-written records. The protocol
is:

```text
producer writes payload
producer orders/completes remote write
producer writes ready flag or includes ready in the completed record

consumer polls ready with RISC loads
consumer uses fence in polling loop
consumer reads payload only after ready
```

There is no general cross-core barrier in current `ttk`. Cross-core reductions,
barriers, and multicasts need named protocols with explicit participant count,
publication address, reset owner, and memory-ordering rule.

## 19. What the current Llama kernels demonstrate

### 19.1 GEMV projection

`_decode_projections_program` demonstrates:

```text
BRISC:
    NoC-read persistent token to private L1
    reserve/read/push streamed weight CB

TRISC0:
    wait weight CB and Src banks
    unpack weight + persistent token into SrcA/SrcB
    drain unpack and pop weight CB

TRISC1:
    wait sources and Dst availability
    HiFi2 ELWMUL
    SFPU accumulates Dst into persistent L7
    finalize scalar into Dst
    drain and publish MATH_PACK

TRISC2:
    wait MATH_PACK
    scalar pack into CB
    drain, push, clear/release Dst

NCRISC:
    wait scalar CB
    gather live BF16 scalar into compact L1
    pop scalar CB
    non-posted NoC write of compact output
```

This is the basic explicit row-major GEMV handoff model even though the current
inter-kernel compact layout is tiled/padded.

### 19.2 RMSNorm

Current `rmsnorm` avoids direct-to-Dst:

1. unpack four SrcA tiles;
2. FPU `MOVA2D` copies them to FP32 Dst tiles;
3. SFPU reads and reduces Dst, applies scale/gamma, and retains one Dst lease;
4. SFPU publishes once;
5. pack consumes two output tiles and releases full Dst.

This is evidence for ordinary SrcA->FPU->Dst->SFPU->pack transitions, not for
the dormant direct-to-Dst helper.

### 19.3 SwiGLU and RoPE

SwiGLU and RoPE demonstrate multiple source unpacks and multiple SFPU maps
under one retained Dst ownership region. They configure/select different Dst
tiles explicitly and publish only after the final SFPU result is in place.

### 19.4 GQA attention

GQA demonstrates the nonstandard persistent-Dst pack handoff:

- Dst1/2 hold online output accumulators;
- Dst3/4/5 hold online softmax state;
- Dst0 holds probabilities;
- math publishes Dst so pack can copy Dst0 twice;
- pack drains each copy but does not clear persistent Dst;
- pack gets `MATH_PACK`, returning ownership to math;
- math performs PV accumulations and the next online update;
- the final publish/pack uses the ordinary full-Dst clear/release.

This must be modeled as an explicit `pack-retain-dst` protocol, not inferred
from a generic pack node.

## 20. Required protocol names for the explicit lowering IR

The lowering IR should not contain raw semaphore indices and scoreboard masks
at graph construction time. It should contain explicit movements plus named
handoffs that expand to the sequences above:

```text
noc_read_complete
noc_write_source_complete
noc_write_remote_complete

cb_produce
cb_consume

unpack_rm_to_srca
unpack_rm_to_srcb
unpack_pair_to_sources
unpack_direct_to_dst_empirical

fpu_consume_sources
fpu_retain_dst
fpu_to_sfpu
sfpu_to_fpu_via_dst

publish_dst_to_pack
pack_release_dst
pack_retain_dst

reconfigure_unpack
reconfigure_math_view
reconfigure_pack
reconfigure_mop
load_replay

cross_core_publish
kernel_drain_and_return
```

Each named protocol should carry concrete operands such as CB ID/depth, source
banks, Dst rows/view, engines touched, TID, posted policy, unpack context,
Replay range, and whether the downstream operation needs source or remote NoC
completion.

The implementation can then emit explicit movement operations while using the
protocol name to produce and verify the exact waits/setup. It does not need an
automatic scheduler to prevent a missing source release, premature CB pop, or
unbalanced Dst handoff.

## 21. Known gaps and probes still required

1. Implement and validate the complete two-sided direct-to-Dst protocol.
2. Preserve and retest the per-direct-`UNPACR` `UNPACK0` drain.
3. Determine exactly which shared config RMWs require mutex 0 in our execution
   model.
4. Decide whether SFPU will ever issue outside TRISC1; if so, add mutex 4.
5. Define a safe, tested Dst->SrcA and Dst->SrcB reuse protocol including dummy
   source-valid and gate reset behavior.
6. Define full-Dst versus half-Dst as explicit mutually exclusive modes; do not
   partially implement offset flipping.
7. Define exact pack edge/tail protocols for arbitrary dense row-major spans.
8. Later: model Replay slots, MOP expansion capacity, and MOP-to-Replay FIFO
   pressure. Until then preserve tested split points.
9. Add launch-time assertions or explicit initialization for every semaphore a
   generated program uses.
10. Add progress markers immediately before and after waits that can wedge so a
    timeout identifies the blocked protocol state.

Until these are resolved, generated code should use only the named protocols
already demonstrated by current Llama kernels or isolated hardware tests.
