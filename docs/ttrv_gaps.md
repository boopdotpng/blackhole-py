# TTRV gaps found by porting all of Llama 3

Writing every Llama 3 decode kernel in TTRV ([examples](examples/)) against the
spec turned up the questions below. Each one names the kernel and line where it
showed up (`// GAP:` comments in the sources). Items are grouped by theme;
nothing here is decided yet.

## A. Compile time and types

Resolved in the spec (§3, §4): items 1–5. A compile-time `if` now splices like
C's `#if` (no scope; untaken branches only parse), `grid` is chosen by a
compile-time `if`, and there are float constants (`1.0 / sqrt(HEAD_DIM)`) and
`type NAME = T`. The kernels still carry the old workarounds.

1. **`grid` can't follow `-D`.** FP8 projections use 96 workers and BF16 88;
   attention uses `KV_HEADS * PARTITIONS`. §4 forbids `-D` from changing `grid`,
   yet `grid` takes a constant expression. Decide whether `grid` may depend on
   overridable consts. (qkv:32, gate:35, attention:25)
2. **No type-valued constants.** Declarations that differ only in element type
   (`e4m3` vs `bf16`) are written twice under `if FP8`. Something like
   `type ACT = e4m3 if FP8 else bf16`. (qkv:60, gate:59)
3. **A compile-time `if` opens a scope.** A value assigned only in one branch
   can't be used after it, so kernels re-wait CB pages or duplicate loops.
   Wrapping identical code in `if FP8 {} else {}` also changed the BF16 image
   (register lifetimes). Proposal: a constant `if` splices its taken branch in
   place, with no new scope. (qkv:257, gate:408, o)
4. **No float constant expressions.** `1 / DIM` and `1/sqrt(HEAD_DIM)` are spelled
   out per variant. Allow constant float arithmetic in float operands.
   (qkv:158, gate:381, attention:280)
5. **Untaken branches are only parsed.** FP8 code can break silently in BF16
   builds; tests should build every variant.
6. **Constant tuples.** Attention repeats chunk-address formulas such as
   `(i & 1) * ODD + (i >> 1) * RIGHT` because `repeat i` can't index a constant
   list or select `l0..l3` by index.

## B. Launch data and scalar code

Resolved in the spec (§4): items 7, 9 and 10. Parameters are now one kind of
thing, like CUDA kernel arguments: `param x: bf16[]` (buffer address, `host` for
pinned host memory, indexable as an endpoint) or `param start_pos: u32 in 0..8192`
(an integer value, like tinygrad's `Variable`, readable on every CPU). The runtime
binds them per graph run, tinygrad-style. The kernels still use the old forms.

7. **No scalar launch values reach the TRISCs.** Attention fans the token position
   out through three CBs (one per TRISC, since each CB has one consumer); FP8
   scales cost a NoC read and a CB handoff. Options: a shared launch scalar, or
   CBs with several consumers. (attention:88, o, argmax:35)
8. **Scalar code can't write float constants or reinterpret pointers.** There's
   no way to fill bf16 L1 with `-inf` or `0.0` (`p[i] = -inf`, or viewing `bf16*`
   as `u32*`). Argmax masks padding on the SFPU instead. (argmax:84, attention:690)
9. **Host endpoints take no offset.** Argmax writes the token to a per-position
   `u64` slot instead of `host + 16 * pos`. (argmax:135)
10. **Device-side launch publication (§12 item 7).** Next-token parameters for
    autonomous replay were dropped. Per-launch zeroing became `keep` slots plus a
    rearmed arrival counter. (argmax:63, 146)

## C. NoC

11. **Partial and misaligned DRAM writes (§12 item 4).** KV-cache append (32-byte
    rows, L1/DRAM offsets differ mod 64), argmax history append (64-byte
    read-modify-write where 4 bytes would do). (attention:425, argmax:115, 139)
12. **Declaring a handle without a request.** Sharing one handle across a runtime
    loop forced peeling the first iteration. Something like `h = noc.handle read`.
    (attention:403)

## D. Unpack, pack, math

13. **Resolved by probe (§9):** an unpack to A leaves SrcB alone, `release=a` is
    enough after `math.mova2d`, and releasing an unpublished B bank shifts SrcB state
    for later kernels. Originally: **Does `unpack.move a` touch SrcB, and is `release=a` enough after
    `math.mova2d`?** The old copy released both banks because its unary unpack
    also advanced SrcB. Every port that copies to Dst depends on this; it needs a
    probe and a §9 rule. (qkv:362, lm:221, gate:146, o, argmax:179, attention)
14. **`.fmt` boolean options have no "off" spelling.** Does
    `unpack.fmt a, in=bf16` without `transpose` clear it? (attention:482)
15. **E4M3 pack path.** The only working path is `pack.fmt in=fp16, out=e4m3`
    from 32-bit Dst (with `round10`). §9 should list it. (qkv:417, gate:480, o)
16. **Integer pack.** Argmax packs (key, index) bit patterns as fp32 → fp32 into a
    `u32` page; pack must not flush the denormal-looking indices. Needs an `i32`
    format or an explicit rule. (argmax:48)
17. **FP32 into Dst (§12 item 6).** Merge states lose bits through SrcA (TF32).
    (attention:495)
18. **Scalar pack.** `pack.gather` zero-fills each 16-byte block, so dot results
    still go through full-tile pack plus an NCRISC copy. (gate, o)
19. **`math.cfg dst_offset` and MVMUL.** Attention assumes the offset applies to
    MVMUL as well as SFPU addressing; unprobed.
20. **Unpack bank protocol.** Whether `unpack.move` waits for a writable bank
    itself; ports keep explicit `srca_clr` stalls. (argmax:157)

## E. SFPU

21. **Fixed in the spec:** a compare operand in L12–L14 lands in the destination
    field and becomes a backdoor template write; and `sfp.minmax x, one` (clamp
    against a constant) must be allowed. Both are now in §10. (gate:214, 251;
    attention:237)
22. **Mask-producing compare.** Exp's 2-instruction `SFPGT`-to-register + `AND`
    becomes a ~5-instruction `sfp.if`. Consider `sfp.gt rd, a, b` / `sfp.le`.
    (gate:196, attention:204)
23. **Compound conditions.** The argmax bounds check needs two outermost `sfp.if`s
    per datum; `a <= x < b` or `&&` would halve it. (argmax:84)
24. **`sfp.if` in scalar loops and replay bodies.** The body rules list `repeat`
    and macros but not scalar `loop`; replay plausibly works since it lowers to
    plain instructions. Say so. (argmax:189)
25. **`sfp.const` lowering.** The current compiler emits an `SFPNOP` after
    `SFPCONFIG`, contradicting "nothing inserted". The spec should also say that
    `sfp.const` accepts a runtime scalar as `sfp.li` does. (o)
26. **Hazard in the old reciprocal.** A `mad` feeds `minmax` with no NOP, a case
    the ISA lists as not auto-stalled. Probe it. (gate:253)

## F. Templates

27. **Resolved (§10):** slot 0 is now the reserved `hold` modifier and the default for every omitted `addr=`. The kernels still define `still` and put `step` in slot 0, so they need updating. Originally: **`sfpmacro.run` and SFPU defaults need `addr=`.** `sfp.load/store` default to
    `addr=0`, whatever slot 0 holds (often a stepping addrmod), so every port
    writes `addr=still`. The default should probably be "no counter change".
    (qkv:105, lm:75, gate:104)
28. **RMSNorm `sfpmacro` form (§12 item 8).** How options attach to unit lines,
    and the backdoor CONFIG0 template install. (qkv:97, gate:97)
29. **Replay budget.** FP8 round + accumulate use 26 of 32 words; SwiGLU bodies
    don't fit beside the RMSNorm replays, so they run as TRISC loops. The spec
    should say how many words multi-word ops take and whether finished templates
    free their space; the listing should report usage per TRISC.
    (qkv:207, gate:274, o)
30. **Macros can't take a statement body.** The tile-walk pattern
    (`over_tile!(replay, n)`) works only for replays; inline bodies need a
    separate macro. Most repeated pattern across the projections.

## G. Kernel-level notes (not language gaps)

- lm writes a dense row-major logits vector; argmax reads it with `split(VOCAB)`
  (the old pair used compact per-core tiles).
- Attention ports only the split path (`PARTITIONS` 4 or 8; 12 needs a
  non-power-of-two ring). BRISC appends K/V. The merged context is written as
  one aligned request.
- O/down FP8 keeps 2×BATCH_TILES weight pages in flight, versus 16 rows in the
  old kernel.
