# tenstorrent ptx-ish isa documentation (in progress)

Goals:
1. you should never write config registers and manual stores to config registers
2. you should never write long sequences of risc-v instructions / logic to set up noc transfers, fpu instructions, address math, etc.
3. you should never manage noc transactions, acks, starts, ends, etc, just state the copy and we track it.
4. you should be able to program every part of the device, nothing should be abstracted away from you except the above.
5. you should never write a kernel per risc. you write one program kernel and the compiler lowers it into five (brisc, ncrisc, trisc0, trisc1, trisc2).
6. you should never need to go below this layer (i.e. needing to write raw risc-v or embedding risc-v into the kernel to do things)

## concepts in blackhole + mapping to ptx

### kernels, entry points and launch metadata

we steal `.visible .entry function()` from ptx. ptx puts tuning directives after the parameter list (`.maxntid`, `.reqntid`, `.maxnreg`); ours carry launch metadata the same way:

```
.visible .entry qkv (.param .u64 x, .param .u64 w, .param .u64 out) .cores 120
```

- `.cores N` or an explicit grid says how many / which cores the launch uses.
- `.param` covers both uniform args (same on every core) and per-core args (multicast matmul gives each core different ones). need a qualifier to tell them apart.
- the assembler emits the manifest entry (cores, per_core variants, params) from these directives.

no unrolling by default (unless you specify the ptx equivalent of pragma unroll). everything jumps and calls functions.

### memory spaces

ptx has `.global / .shared / .local / .param / .const`. ours:

| space | what it is |
| --- | --- |
| `.dram` | dram, bank interleaving handled by the compiler |
| `.l1` | this core's l1 |
| `.l1` + core coordinate | another core's l1 |
| `.local` | the risc's private stack memory |
| `.param` | launch args |
| `.const` | data compiled into the kernel image |
| `.reg` | dst, srcA, srcB, lregs. not addressable memory, but allocated like it |

the space is part of the pointer type. that is how the compiler knows a load is a noc transaction rather than a risc-v load.

### noc reads and writes

`cp.async.global` and wait/commit groups. we coalesce loads together (the data is contiguous if you include interleaving, and in the ptx we treat a tensor as just loading from an address, where the compiler takes care of the interleaving logic and noc specific transactions).

additions:
- reads have one completion point (data is in l1). writes have two: departed (the source buffer can be reused) and landed (visible at the destination). there needs to be a wait for each.
- memory visibility: the isa defines when a noc write that landed in l1 is visible to a local load on that core. if the riscs cache l1, the compiler emits the invalidate; you never do. (verify against the hardware.)
- flow control: "state the copy and we track it" has to include who guarantees the receiver has room. see circular buffers.

`.multicast::cluster` for multicasting something from one core to the others (used in matmul).

noc atomic operations across cores for tree reductions (probably an atomic add wrapped as a ptx instruction, whatever the closest analog is).

### circular buffers

tensors split into tiles for computation. the unit of movement in brisc, ncrisc, and dram-land. we need to stream data into kernels, so this is necessary at some level: either the compiler does them manually and we just declare loads (loads in a loop is not the greatest idea, especially if you have to write that manually for each kernel), or:

proposal: a cb is a declared, typed channel (size, tile count, storage format, producer, consumer). reserve / push / wait / pop are derived from the loads and stores that name it, and cross-core channels carry credits so the sender can never overrun the receiver.

### datatypes

two separate classes. storage formats never appear on a register, and compute never happens in them.

register types (what compute sees):
- lregs: `.f32`, plus integer views `.s32` / `.u32` since the sfpu does integer ops.
- dst slots: `.b16` or `.b32`. this is not fp, it is just 16 or 32 bits, same idea as ptx's untyped bits types.
- srcA / srcB: one fixed internal type.

storage formats (what lives in l1 and dram): bf16, fp16, fp8, bfp8, bfp4. these exist only as qualifiers on the unpack and pack instructions. the unpacker outputs all of them as bf16, the packer rounds back:

```
ld.tile.bfp8  %srcA, [x]       // unpack, converts to the internal type
st.tile.bfp4  [y], %dst3       // pack, rounds back. rounding mode is a modifier here
```

fidelity is a modifier on the fpu op, like ptx's `.rn` / `.rz`:

```
mvmul.p2  %dst0, %srcA, %srcB
```

the minimum phase count comes from the format that was unpacked into the sources: bf16 needs at least 2, fp8 and below need 1. the assembler tracks the source format (state tracker 6), defaults the phase count from it, and rejects anything below the minimum. accumulate is a modifier in the same position.

### risc-v registers

risc-v registers become regular virtual registers. ambitiously, we should not even be using these: the risc-v host code exists only to run the coprocessor. risc-v code is a side effect of the control / math code we write. virtual scalar registers and operations on them stay available for things like argmax, and probably embedding if you want to do noc copy math.

ordering: tensix instructions are queued, risc-v loads and stores are immediate. anything that reads a coprocessor result back into a scalar register (argmax) implies a drain of the queue first. the compiler inserts it.

### sfpu

sfpu registers are another virtual register space, with all the ops the sfpu supports. we take long chains of these and just run them, virtually allocating and deallocating.

additions:
- spilling: there are only a handful of physical lregs, and the only place to spill is dst rows. so the lreg allocator and the dst allocator are one problem.
- predication: control flow in the sfpu is per-lane, a condition-code stack, not branches. ptx `.pred` registers and `@p` guards are the analog. nesting depth is bounded and the assembler checks it.
- constants: loading immediates and the programmable constant lregs are allocator-managed too.

### dst, srcA, srcB

dst needs to be split up into many allocations, this is where the results of fpu are written to. you get 8 `.b32` allocations or 16 `.b16` allocations, i think.

srcA and srcB: one tile each (verify), fixed internal type, you just copy fewer bits in.

address counters (rwc / adc) are implicit operands of nearly every fpu, unpack and pack instruction. in the isa you name a dst slot and a row range; the compiler owns the counters (state tracker 7).

### manual unpacker and packer copies and one-time stuff

not sure yet. `stmatrix` and `ldmatrix` cover the case where you are copying data from an l1 cb (or whatever we end up doing with cbs) into srcA or srcB; these need a special instruction because we need to tilize, rather than just copying elements row major like the default unpack and pack paths do.

### MOPs

for now written by us, not autogenerated by the compiler. we need some way to define a mop template, load it, then run it. you never write tensix instructions manually, just our instructions that manage all of that. we use these for the unpacker, packer, and fpu, and in some rare cases the sfpu (although this is better served by SFPMACRO, which is another mop but only for sfpu instructions).

the template shapes (loop nesting, last-iteration substitution, zmask skip) and the replay buffer slot count are resource limits. document them and have the assembler check them.

## state trackers

1. how are we viewing dst? 16-bit or 32-bit? which slots are 32 and which are 16?
2. unpacker and packer state (config context switching, permanently set config buffers and what is in the context so we can diff them in the compiler, so that we only write the necessary configs?)
3. sfpu config (similar to above)
4. fpu config (similar to above)
5. which template is loaded into the mop and replay buffer currently? it's read-only actually, so we have to write a new one each time, unless we're positive it hasn't changed in the (TODO: finish this thought)
6. which storage format was last unpacked into srcA and into srcB (drives the fidelity minimum)
7. address counters (rwc / adc)
8. sfpu lane-flag stack depth

### how tracking works without unrolling

this is forward dataflow over the control-flow graph, the same shape as constant propagation. no unrolling, and no abi the user has to write.

- every tracked field is either `known = v` or `unknown`.
- at a join, values that agree stay known, values that disagree become unknown. loops iterate to a fixpoint.
- at each use, emit a write only if the value the instruction needs is not already known.
- placement: done naively, a loop head sees "unknown from entry, A from the back edge" and rewrites A every iteration. the fix is to place the write on the entry edge (the preheader) so both edges agree. this is what gcc's mode-switching pass does with lazy code motion.
- calls: closed-world, so analyse the whole call graph and compute each function's requires / clobbers automatically. if a function is called under two different states, clone it. far cheaper than unrolling.
- entry: all state is unknown at `.entry`. costs one batch of config writes per launch.
- with no escape hatch, every write to tracked state goes through the compiler, so the tracker is never wrong.

## tooling

- a ptxas-style assembler
- a disassembler, so the five lowered kernels can be read back
- a reference interpreter, so kernels can be tested off-device
