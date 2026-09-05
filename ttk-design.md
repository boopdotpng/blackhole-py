# TTK shape

Status: design proposal

This replaces the plan in `ttk_new.md`, which specifies too much. The target
here is the smallest thing that lets Llama 3 row-major be hand-written without
reaching into private methods, and that a tinygrad lowerer can later target
unchanged.

## 1. What went wrong

Old `ttk` helpers were not operations; each was a complete protocol.
`Unpack.move_pair` is CB wait + source stall + two full descriptor writes +
config commit + MOP configure + issue + engine drain + two CB pops. `Fpu.binary`
is semaphore wait + Dst view config + three address-modifier writes + RWC reset
+ source stall + MOP configure + run.

Sealed protocols do not compose. You cannot fuse two unpacks, hoist a shared
descriptor, retain Dst across a pack, or reuse a MOP template, because every
call re-establishes the whole world. So the callers broke in instead: the two
Llama examples call `ttk` private methods 52 times. `llama3.py` reimplements
Dst selection (`_rms_select_tile`), SFPU mapping (`_rms_map_acquired`) and its
own MOP configuration on top of `sfpu._issue`.

The fix is not a different surface. The surface is roughly right, and roughly
what you already want:

```python
u.unpack(weight_cb, Src.A)
u.unpack(token_l1,  Src.B)
f.mul(Src.A, Src.B, Dst[0])
s.map(program, Dst[0])
p.pack(Dst[0], out_cb)
```

The fix is that these calls must **append records, not protocols**. Waits,
configuration, CB credits and MOP templates get inserted afterwards by passes
that can see the whole stream.

## 2. The model already exists in asm.py

The working tree just moved RISC-V registers to this model, and it is the right
one to generalize.

```text
before:  k.reg() takes a physical register from a scoped free list;
         callers pass exclude= to avoid clobbers
after:   k.reg() mints a VReg; Insn records go in a list;
         allocate() assigns physical registers at lower()
```

Every remaining Tensix problem has the same shape — a resource whose assignment
must be decided with more context than one call site has:

| resource | decided by | pass |
|---|---|---|
| RV32 GPRs | live ranges | `regalloc.allocate` (done) |
| unpack/pack/Dst config registers | last-writer value numbering | config pass |
| stalls, semaphores, CB credits | producer/consumer edges | sync pass |
| MOP/Replay templates | repeated instruction runs | mop pass |
| SFPU LRegs | live ranges within one program | `SfpuProgramBuilder` (done) |

So: `ttk` calls emit records into five ordered per-RISC streams, and lowering
runs four passes over them. Nothing else changes.

## 3. The op record

```python
@dataclass(frozen=True)
class Op:
  risc: KernelRole
  issue: tuple[TensixWord | Insn, ...]   # the "do it" instructions only
  config: ConfigNeed = ()                # required engine state, not writes
  reads:  tuple[Use, ...] = ()
  writes: tuple[Use, ...] = ()
  frees:  tuple[Use, ...] = ()
  engine: Engine | None = None           # scoreboard bit signalling completion
  protocol: str | None = None            # named escape, see §7
```

`issue` holds only the instructions that perform the work — `UNPACR`, `ELWMUL`,
`PACR`. Not `STALLWAIT`, not `SEMWAIT`, not `SETC16`, not CB counter updates.
If a `ttk` method emits one of those directly, it is wrong.

`config` is a *requirement*, not writes: "unpacker 0 reads BF16 row-major from
this base with x_dim 1024, writes SrcA". The pass materializes register writes
only when the required state differs from the state already live. Two unpacks
sharing a descriptor emit one config. Today they emit two, ~20 register writes
each.

Resources are deliberately few:

```python
Src.A, Src.B          # generation counter
Dst[i]                # version + ownership
cb                    # credits + ring generation
noc_tid               # source and remote completion
```

Effects are `read` / `write` / `free`. That is enough. `ttk_new.md`'s six access
modes crossed with four completion points is a matrix nothing in Llama needs.

## 4. Passes

**config** — value-number the Tensix configuration state per engine. Walk each
stream, diff `op.config` against live state, emit the minimal writes plus the
required `TRISC_CFG`/`CFG` visibility stall. This is where the bulk of today's
generated code disappears.

**sync** — build producer/consumer edges from resource identity, then look each
edge up in a table keyed by `(producer engine, consumer engine, resource)`.
That table is literally the quick dependency chart in `syncs.md` §2. Emit the
stall, semaphore, drain or CB counter update it names.

The critical property: edges come from **shared value identity**, not from
scanning generated instructions. `f.mul(Src.A, Src.B, Dst[0])` after
`u.unpack(cb, Src.A)` creates the SrcA edge because both name `Src.A`, and the
table says that edge is `stall MATH on SRCA_VLD` before, and source release on
final use after. No instruction pattern matching.

**mop** — see §5.

**encode** — existing `Asm.instructions()` path.

Run them in that order, per stream, with the cross-stream edges resolved by the
sync pass before any stream is encoded.

## 5. Is MOP required?

You asked whether MOP is needed for function or only speed. It is only speed,
and the current code proves it both ways:

- `Sfpu._prepare` falls back to `_inline_faces`, issuing the body 8x4 times
  literally, when no Replay slot is free. Same result, more instructions.
- `Fpu.reduce_row_sum` issues sixteen raw `MVMUL` words with no MOP at all.

So build without it. Correctness first, then add the pass when a kernel is
instruction-issue bound. It will be: TRISC issue rate is what caps FPU
throughput, which is why `matmul_peak` needed MOP plus split Replay to keep the
FPU fed. Treat MOP as a peephole that compresses a run of identical words with a
regular address-modifier stride into a `LoopTemplate`, and Replay as caching for
a repeated body.

Two things the pass must not do: rewrite a template while an earlier expansion
is live (needs `PC_BUF_MOP_SYNC`, per `syncs.md` §14), and coalesce away the
per-face `UNPACK0` drains in the direct-to-Dst sequence (`syncs.md` §9.3 — that
one is empirical and load-bearing).

## 6. Files

```text
ttk/types.py    DType, Layout, L1/CB/Src/Dst views          plain data
ttk/cb.py       ring + registry                             keep, it is good
ttk/noc.py      NIU command programming                     rebuild (see §8)
ttk/unpack.py   descriptor construction + UNPACR issue
ttk/fpu.py      one method per FPU macro + addr-mod tables
ttk/sfpu.py     SfpuProgramBuilder + map                    keep, it is good
ttk/pack.py     pack config + PACR issue
ttk/op.py       Op record, Engine, resource/effect types
ttk/config.py   Tensix config state model + pass
ttk/sync.py     protocol table + pass
ttk/mop.py      MOP/Replay compression pass                 last
```

`cb.py` and `sfpu.py` survive as-is. `SfpuProgramBuilder` is already exactly the
right shape — a linear builder with an allocator and static hazard NOPs — which
is worth noticing, because it is the one part of old `ttk` nobody had to break
into.

## 7. Escapes

Two are needed, both real:

`Op(protocol=...)` — a named hand-written sequence for a handoff the table does
not model. GQA's retained-Dst double pack is the current example: pack `Dst[0]`
twice, keep `Dst[1..5]` live, `SEMGET` without `ZEROACC`. Do not try to
generalize this before a second case exists.

`emit(word, effects=...)` — raw instruction with declared effects, for a verified
opcode without a typed wrapper yet. It must reject sync/semaphore opcodes and
must reject missing effects, otherwise it becomes the hole the whole design
leaks through, which is what happened to `_issue`.

## 8. Order of work

The tree is mid-surgery: `ttk/noc.py` is a 61-line stub that does not parse
(line 9, `NOC_TARGET_ADDRESS_MIDDLE o 0x04`), and everything except `cb.py` is
deleted. So:

1. Rebuild `ttk/noc.py` on vregs. Nothing runs until this parses.
2. Add `Op`, the five streams, and passes that are deliberately **maximally
   conservative** — materialize all config every time, insert every wait. Target:
   byte-identical output to today's known-good sequences for row-major K0, which
   already runs on hardware. This is the checkpoint that says the plumbing is
   right before any pass gets clever.
3. Config pass: diff instead of always-write. Verify K0 still passes.
4. Sync pass: table-driven instead of always-maximal.
5. Hand-write row-major Llama K1..Kn on the resulting API. No private access —
   if a kernel needs to break in, that is the bug report for this design.
6. MOP pass, when a kernel is measurably issue-bound.
7. tinygrad: `codegen/tensix.py` emits these same `Op` records.

Step 5 before step 7 is the right call. Hand-writing Llama defines the op set
the compiler has to target — the ISA falls out of what the kernels actually
need, instead of being guessed. Both paths then share every pass, because the
hand-written kernel and the lowered UOp graph produce the same records.

## 9. Row-major specifics

Dropping host tilization changes two things, and both belong in the new modules
rather than as the special-case flags they are today:

- unpack forms faces from row-major L1, so `x_dim`, strides and the tilize path
  become ordinary descriptor fields;
- pack writes row-major spans, so layout is an ordinary pack option.

This deletes the compact/dense gather-scatter kernels in `llama3.py`
(`_decode_projection_residual_program`, `decode_compact_to_dense`, the face
offset arithmetic in `_bf16_tile_byte_offset`) — several hundred lines whose
only job is undoing tilization.

## 10. The main risk

A wrong generic pass is far harder to debug on hardware than a wrong explicit
sequence, because the failure is silent and non-local. Mitigations, in order of
value: step 2 above (prove plumbing against known-good output before optimizing),
a dump of the generated protocol per stream so a hang can be read rather than
bisected, and keeping the conservative pass available behind a flag so any new
kernel can be A/B'd against it.
