> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv v1 decisions and compile-time syntax proposal

This records the scope decisions following the review, and reviews
[Fable's additions](ttrv_spec_additions.md). Macro invocation uses the agreed
`name!(...)` spelling; the remaining expansion rules are proposed, not implemented.
The accepted SFPU/host-write requirements are also recorded
in [the main draft](ttrv_spec_new.md).

## Scope decisions

- Compute stays native FPU/SFPU instructions, named fields, and explicit syncs.
- NoC starts as readable wrappers over the current RISC-V sequences. Authors write
  the CB and remote publication protocols; no automatic transaction lifetime.
- Per-core parameter tables are not required. Derive work from `core.x` / `core.y`
  and launch parameters; settle exact mapping with the runtime.
- Abstract `SFPLOADI` encoding: accept full constants or runtime scalar values.
  FP8 scale parameters contain values, not instructions. Loading float bits and
  converting an integer to a float are distinct operations.
- Audit SFPU lane configuration, active masks, condition codes, and index mode;
  provide a readable lane/mask helper. Signature awaits that audit.
- Pack/unpack design remains deferred to its own review.
- DRAM lookup stays under the NoC helpers. Remote L1 is ordinary writes/atomics.
  Add host writes with a full device-visible address and hidden PCIe encoding.

These decisions supersede suggestions in the earlier review/contract for mandatory
per-core bindings or author-managed DRAM page lookup. They do not require a new
algorithm layer, multi-reader CB abstraction, or general ownership type system.

## A small macro system

Use four pieces: `#define` constants/field lists, `#if` selection, parameterized
`macro` blocks, and compile-time `repeat`. Keep runtime `fn` and `loop` unchanged.

```text
#define ROW_GROUPS 8

macro accumulate(base, sum) {
    repeat row, ROW_GROUPS {
        sfp.load l0, dst[base + row * 2], fmt=fp32
        sfp.add sum, sum, l0
    }
}

fn trisc1 {
    sfp.li l7, 0.0
    repeat face, 4 {
        accumulate!(face * 16, l7)
    }
}
```

This is a syntax/expansion example, not a complete reduction kernel: the caller
must establish config, Dst counters, ownership, and synchronization. It expands to
32 explicit load/add pairs, with no loop counter or call instructions. `l0` is an
explicit clobber; `sum` names the SFPU accumulator supplied by the caller.

`name!(...)` expands a macro inline. `name(...)` remains a real
function call. No implicit inlining heuristic. A macro can also expand inside a
replay or MOP definition where its resulting statements are legal.

Rules:

1. Macros are defined at file level. Parameters substitute operands or constant
   expressions, not arbitrary text or statement blocks. No variadics, token
   pasting, stringification, or recursion. Macros may expand other macros through
   an acyclic expansion graph.
2. `repeat i, N { ... }` expands for `i = 0 .. N-1`. `N` must be a nonnegative
   compile-time integer; zero emits nothing. `i` is a scoped constant. Runtime
   unrolling is never inferred from `loop`.
3. Constant expressions can use macro arguments and repeat indices. A register
   argument is legal as an instruction operand, but not in a constant expression,
   `repeat` count, or compile-time condition. Fail at the use that requires a
   constant. No separate macro type system is necessary.
4. Scalar temporaries introduced by a macro are local to that expansion; caller
   registers are accessed through parameters. A macro writes an output by taking
   its destination as a parameter, like an instruction. File-level resources and
   constants remain visible. Each repeat iteration gets fresh local temporaries;
   loop-carried values must come from the enclosing scope.
5. Physical SFPU registers are never renamed. Explicit `l0` means `l0`; pass a
   scratch register as a parameter when reuse requires a different register.
   Configuration, counters, predicates, and syncs remain real visible effects.
6. `#if` inside a macro/repeat is evaluated after its arguments/indices are bound.
   Undefined condition names are errors. This needs a small structured expander,
   not a separate C-preprocessor pass that runs everything before macro expansion.
   Keep `#else` / `#endif`; omit function-like `#define` macros to avoid two ways
   to define parameterized code. Field-list `#define` remains supported.
7. Disallow `ret` and a `break` targeting outside the expansion in v1. Ordinary
   runtime `if`/`loop` inside a macro are fine. This keeps a reusable instruction
   sequence from unexpectedly returning from its caller.
8. Apply the normal engine, operand, resource, and hazard checks to expanded code.
   Bound expansion size and report overflow as a normal diagnostic. Diagnostics
   show both definition and expansion sites; an `expand` listing shows the result.

That is enough to replace ordinary Python code-generation loops without embedding
Python in the language. Irregular finite traversals can use nested repeats and
explicit expansions initially; defer lists, generators, and compile-time functions
until a port demonstrates that they materially simplify source.

## Review of Fable's additions

Useful additions worth carrying forward:

- A launch-state table (as a target runtime contract, not a description of today's
  firmware), L1/CB declarations, retained-buffer behavior, and explicit `drain`.
- NoC setup/request/wait signatures with issue-only requests and explicit waits.
- Named Dst-format setup and ZEROACC access.
- An end-to-end embedding example, which exposes setup and wait placement.

Reconcile before merging:

| Topic | Finding / action |
| --- | --- |
| Per-core parameters | Deferred by the current scope decision. Do not replace `core.id` with new rank/count requirements yet. |
| DRAM API | The proposed manual `page_addr` helper conflicts with the chosen helper-managed lookup. Keep bank/port tuning where useful without requiring authors to encode the standard mapping. |
| Host output | `addr` is explicitly 32 bits in the additions. Add full host-endpoint addressing and routing; do not require raw high-word/PCIe fields. |
| Launch state | “Every fn starts from the same state” must mean entry functions at launch. Subroutine calls do not reset engines, counters, or registers. |
| CB address calculation | `sll` works for power-of-two page bytes, but page bytes are unrestricted. Use multiplication or restrict/document the supported page sizes; BFP sizes cannot generally use that shift recipe. |
| CB wrap | Specify the maximum capacity below the 16-bit counter modulus so empty/full remain distinguishable, plus dynamic `n` preconditions. Re-reading `wptr`/`rptr` without changing the counters returns the same page, not the next one. |
| CB ordering | The listed push/pop sequences omit fences. Document the required ordering for payload accesses and counter publication, whether in the wrappers or explicitly in source. |
| Endpoint ownership | Count CB endpoints by executing RISC, including calls, rather than by textual `fn`; two subroutines on the same RISC are not two producers. |
| NoC flow control | “Every transfer uses the same in-flight count” is insufficient. Reads, outgoing writes, acknowledgements, and atomic responses use different counter conditions. Lift the per-kind recipe. |
| NoC reconfiguration | Define when `noc.fmt` may overwrite a command buffer and how outstanding requests retain their completion identity. It cannot blindly rewrite a busy buffer or forget requests from the previous kind. |
| Dynamic NoC selection | If `noc=` is runtime-selected, resource-conflict checking must account for both possible interfaces across RISCs. |
| Atomic response storage | A fixed `ret` slot needs a rule for multiple outstanding atomics: wait before reuse or supply distinct slots. |
| Multicast | Posted-only multicast plus explicitly unordered requests does not define a payload-before-notification protocol. State the ordering used by the existing sequence; a local send wait alone is not arrival. |
| Grammar | The three-positional-operand cap conflicts with both `sfp.mad` and the proposed four-operand NoC calls. Remove the cap. Reserving `a`/`b` as register names also conflicts with the worked example's scalar `a`. |

The additions help close the missing surface area. They are not new hardware
evidence: their opening explicitly says the proposed forms are unimplemented and
unmeasured. Preserve that distinction when merging the documentation.
