# Blackhole Compiler Lowering Pipeline

Conversation export from T3 thread f752b57e-f5e9-4eb7-a1ba-65fd7e9e980a (gemini-4-neon). Text is verbatim.

---

## Turn 1

### User

llama-graph.txt; i think we have to bring in symbolic and rangeify from tinygrad to fix the embedding kernel madness that's going on right now; that should lower to just a single gather, right? do we have to carry over tinygrad's custom backwards function for embedding in our code? where do we handle that? i think other than that, the graph looks good enough to start the next step of lowering? do we have const folding / and the other rules? i think we need div/mod, symbolic? We can leave the backward pass and gradients for later. just inference / forward pass for now.

### Gemini

Short answer: **yes on all counts** — bringing in `symbolic` (with `div_and_mod`) + `rangeify` + `reduce_collapse` / `load_collapse` from tinygrad is the exact next step, you do **not** need tinygrad's custom embedding backward for inference, and aside from one small `dtype` tweak in `Embedding`, [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) is in great shape to start lowering.

### 1. The embedding "madness" → single gather (plus the 3 other `arange`s)
In [llama-graph.txt:187-206](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:187-206), there are **two** reductions stacked together:
1. **`arange(128256)` cumsum (`%187`–`%197`)**: the `(128256, 128256)` padded-repeat-sum trick. The exact same pattern also appears in RoPE ([llama-graph.txt:210-232](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:210-232)) and `argmax` ([llama-graph.txt:471-481](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:471-481)).
   - `run_rangeify` ([indexing.py:181](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py:181)) turns the movement ops into range math + `WHERE` gates, and **`pm_reduce_simplify` (`reduce_collapse` + `symbolic` + `div_and_mod_symbolic`)** ([simplify.py:98-154](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py:98-154)) collapses all four `arange` reductions directly to the loop range `r`.
2. **One-hot embedding sum (`%198`–`%205`)**: `REDUCE(ADD, r, WHERE(tok == r, t0[r, d], 0))`.
   - Once `arange` collapses to `r`, **`pm_load_collapse` / `pm_reduce_load_collapse`** ([simplify.py:122-161](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py:122-161)) matches `(idx == r).where(expr, 0).reduce(r, ADD)` and substitutes `r -> idx`, lowering the whole thing to **one bounds-checked gather**: `(0 <= tok < 128256).where(t0[tok, d], 0)`.

**One small catch in [llama3.py:62](/Users/boop/code/tenstorrent/blackhole-py/examples/llama3.py:62):**
```python
return hot.where(self.weight, 0.0).sum(-2)
```
Because `sum()` defaults to `fp32` accumulation for `bf16`, it inserts `%202 = cast %201 dtype=fp32` *between* `WHERE` and `REDUCE` ([llama-graph.txt:202-205](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:202-205)), which will block `pm_reduce_load_collapse` from matching `WHERE(...).reduce(...)`. Notice tinygrad explicitly passes `dtype=weight.dtype` in `_embedding_fwd` ([nn/__init__.py:362](/Users/boop/code/tenstorrent/tinygrad/tinygrad/nn/__init__.py:362)):
```python
return hot.where(self.weight, 0.0).sum(-2, dtype=self.weight.dtype)
```

### 2. Do we need tinygrad's custom backward for `Embedding`?
**No.** In tinygrad ([nn/__init__.py:360-387](/Users/boop/code/tenstorrent/tinygrad/tinygrad/nn/__init__.py:360-387)), `_embedding_bwd` is *only* a `grad_fxn` (atomic scatter-add) for training when `USE_ATOMICS` is set. The forward pass (`_embedding_fwd`) is just the plain one-hot `where(...).sum(-2, dtype=weight.dtype)` lowered through `pm_load_collapse`. Whenever we add autograd later, custom `grad_fxn`s hook onto `CALL`/`@function`, so nothing is needed for forward-pass inference.

### 3. Is the rest of [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) ready for lowering?
**Yes.** Everything else looks clean and canonical for Layer 0:
- `_block` (`%1`–`%169`) is deduplicated once and called 16 times with ping-pong `alloc`s (`a0`–`a15`) and `after` chains.
- RMSNorm, matmuls (fp32 accumulate), RoPE `shrink` on symbolic `start_pos`, KV-cache slice `store` + `after`, GQA `expand` + causal/dynamic `p1+1` attention, softmax, SwiGLU MLP, tied `t0` weights, and `argmax` are all clean.
- Note that `CALL(SINK, ...)` args like `%205` (embedding output into the first `_block` call at line 267) will need to be realized/staged at call boundaries during rangeify (same as `realize_custom_kernel_srcs` in [indexing.py:36-41](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py:36-41)).

### 4. What rules we already have vs. what we need to bring in
**Already implemented:**
- **Const folding & basic algebra** in [compiler/ops.py:68-113](/Users/boop/code/tenstorrent/blackhole-py/compiler/ops.py:68-113) (`pm_simplify`: ALU const folding, cast/bitcast folding, `0`/`1`/`-1` identities, idempotents, simple two-stage `ADD`/`MUL` const folding, basic bool/`WHERE`/`IF`).
- **Movement-op cleanup** in [compiler/tensor.py:284-325](/Users/boop/code/tenstorrent/blackhole-py/compiler/tensor.py:284-325) (`pm_frontend`: noop removal, merging adjacent movement ops, `SHRINK` past squeeze/unsqueeze `RESHAPE`, dropping redundant broadcast views, folding movement/cast on expanded consts).

**Missing and needed for rangeify + arange/embedding collapse:**
1. **Full `vmin`/`vmax` bounds + `Invalid` sentinel**: [uop.py:227-246](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:227-246) (`_min_max`) currently only handles `CONST`, `PARAM` vars, `CAST`, `NEG`, `ADD`, `SUB`, `MUL`, `MAX`, `DIV` — it needs `RANGE` (`0 .. smax(end)-1`), `MOD`, `CMPLT`/`CMPEQ`/`CMPNE`, `AND`/`OR`, `WHERE`, etc. Also tinygrad's `Invalid` sentinel (or gated `INDEX` valid) + multi-axis `INDEX(buf, *idxs)` during rangeify.
2. **`div_and_mod_symbolic`** ([divandmod.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/divandmod.py)): essential because `_apply_reshape` turns every `RESHAPE` into `%` and `//` chains; also needs `fold_add_divmod_recombine`, `r % end -> r`, `r // end -> 0`, `(x // c1) // c2 -> x // (c1*c2)`, and `divides`/`const_factor` helpers on `UOp`.
3. **Index/range `symbolic` + `pm_simplify_valid`** ([symbolic.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/symbolic.py)):
   - `vmin == vmax -> CONST` folding
   - Commutative canonicalization + moving consts right (`(x+c)+y -> (x+y)+c`) + term combining (`x*c0 + x*c1`, `x + x`, `y*(x+c)`)
   - Inequality/max folding (`c0 + x < c1`, `x // d < c`, `lt_folding`, `max(x, y)` from bounds)
   - `WHERE` & `Invalid` propagation (`pm_data_invalid`, nested `WHERE` merging, `(!c).where(t, f) -> c.where(f, t)`)
   - `pm_simplify_valid` (`uop_given_valid`, `simplify_valid`, `drop_and_clauses`) used by `RESHAPE` and `PAD` lowering.
4. **Rangeify & reduce/load collapse** ([indexing.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py), [rangeify.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/rangeify.py), [simplify.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py)):
   - `run_rangeify` (`apply_movement_op`, range propagation, realize map, `STAGE` / `REDUCE` with `RANGE`s)
   - `pm_reduce_simplify` (`reduce_unparented` + `reduce_collapse` for `arange`)
   - `pm_load_collapse` (`reduce_load_collapse` for one-hot embedding -> gather)
   - `pm_const_buffer_folding` + `pm_remove_bufferize` + `bufferize_to_store` + kernel splitting into `lower_tensor` ([compiler/tensor.py:334](/Users/boop/code/tenstorrent/blackhole-py/compiler/tensor.py:334)).

If you want, we can start right away with Step 1–3 (`vmin`/`vmax`, `Invalid`, `symbolic`, `div_and_mod_symbolic`) and then wire up `rangeify` + `reduce_collapse` + `load_collapse` and verify [llama3.py](/Users/boop/code/tenstorrent/blackhole-py/examples/llama3.py) lowers cleanly with the embedding reduced to a single gather.

---

## Turn 2

### User

can you explain the purpose of all of those and what they match / why we need them? i'm new to graph compilers / uops.

### Gemini

Think of the compiler as moving between two worlds:

- **Layer 0 (what's in [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt)):** *whole-tensor* ops (`reshape`, `permute`, `pad`, `shrink`, `expand`, `reduce`). There are no loops or memory addresses yet — just shapes.
- **Layer 1 (kernel IR):** *per-element* loop nests (`RANGE`, `INDEX`, `LOAD`, `STORE`, `END`, `REDUCE` over `RANGE`s). Every tensor value is now described as a formula of loop variables `r0, r1, ...`.

The whole trick of tinygrad's compiler is: **once movement ops become plain integer math on loop indices, ordinary algebra can crush crazy-looking tensor graphs down to almost nothing.**

Here is what each piece does, what it matches, and why we need it.

---

### 1. Rangeify (`indexing.py`) — *turn shapes into loops*
- **Purpose:** Eliminates all movement ops (`RESHAPE`, `EXPAND`, `PERMUTE`, `PAD`, `SHRINK`) by walking backwards from outputs, assigning a `RANGE` (loop variable) to each axis, and rewriting how each op transforms indices.
- **What it matches:** Every Layer 0 op:
  - `SHRINK` (slice `[off : off+sz]`) → shifts index `r` to `r + off`
  - `PERMUTE` → reorders the tuple of indices
  - `EXPAND` → drops the broadcast index (reading the same element for every iteration)
  - `PAD` → shifts index `r` to `r - off` and attaches a validity condition `(r >= off) & (r < size + off)` (outside that, value is `0`)
  - `RESHAPE` → flattens output indices into one linear integer, then splits it back into input indices using `//` and `%`
  - `REDUCE(n=1)` → introduces a new `RANGE` for the reduced axis
- **Why we need it:** Hardware doesn't have a "permute" or "pad" instruction — it has loops and memory addresses. Also, without converting movement ops to index formulas, you can't see that `arange`'s giant `(128256, 128256)` reshape/pad/shrink chain is actually just `i + r >= N - 1`.

---

### 2. `vmin` / `vmax` bounds — *prove what values an expression can take*
- **Purpose:** Every integer/bool UOp tracks its static `[vmin, vmax]` interval (like interval arithmetic).
  - `RANGE(N)` has `[0, N-1]`
  - `Variable("start_pos", 1, 8191)` has `[1, 8191]`
  - `a + b` has `[a.vmin + b.vmin, a.vmax + b.vmax]`
  - `a < b` has `[True, True]` if `a.vmax < b.vmin`, `[False, False]` if `a.vmin >= b.vmax`, else `[False, True]`
- **What it enables:** Whenever `x.vmin == x.vmax`, `x` is actually a **constant**!
  - E.g. if `r ∈ [0, 63]`, then `r < 64` has `vmin == vmax == True` → folds to `True`.
  - If `a ∈ [0, 3]` and `b ∈ [0, 3]`, then `a + b < 8` folds to `True` and `(a + b) // 8` folds to `0`.
- **Why we need it:** Rangeify generates lots of defensive bounds checks (from `PAD` and `RESHAPE`). `vmin`/`vmax` is how the compiler proves which checks are always true/false and deletes them.

---

### 3. `Invalid` sentinel + `pm_data_invalid` + `pm_simplify_valid` — *track out-of-bounds cleanly*
- **Purpose:** When `PAD` creates an out-of-bounds index, you must **not** actually load from that memory address (it could segfault or read garbage). Tinygrad represents a gated index as `WHERE(valid_cond, idx, Invalid)` where `Invalid` is a special constant meaning "this lane doesn't exist".
- **What it matches:**
  - `pm_data_invalid` ([symbolic.py:87-111](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/symbolic.py:87-111)): pushes math *inside* the gate so `Invalid` bubbles up to the `LOAD`/`STORE`:
    - `WHERE(cond, x, Invalid) + y` → `WHERE(cond, x + y, Invalid)`
    - `LOAD(INDEX(buf, Invalid))` → `0` (don't even touch memory!)
  - `pm_simplify_valid` ([symbolic.py:450-454](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/symbolic.py:450-454)):
    - `simplify_valid`: inside `c1 & c2 & c3`, assumes earlier clauses are true to simplify/delete redundant later clauses (e.g. `(r < 10) & (r < 20)` → `r < 10`).
    - `gated_given_valid`: inside `WHERE(cond, expr, Invalid)`, simplifies `expr` *assuming `cond` is true* (so `expr` only needs to be right on the valid lanes).
- **Why we need it:** Without `Invalid`, a rule like `0 * idx -> 0` could erase a `PAD` validity gate and accidentally read garbage, or `RESHAPE` after `PAD` wouldn't know which lanes are padded zeros.

---

### 4. `div_and_mod_symbolic` ([divandmod.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/divandmod.py)) — *cancel `//` and `%` from reshapes*
- **Purpose:** Every `RESHAPE` emits `//` and `%`. This pass simplifies integer division and modulo using `vmin`/`vmax` and divisibility.
- **What it matches:**
  - `r % N` → `r`, `r // N` → `0` (when `0 <= r < N`)
  - `(a*c + b) // c` → `a + b // c` (exact factor pulls out)
  - `(a*c + b) % c` → `b % c` (multiples of `c` vanish)
  - **Congruence folding** (`fold_divmod_general`): rewrites `x % c` by replacing each term's coefficient with its smallest remainder mod `c`, then checks if the result's `[lo, hi]` lies in a single bucket of width `c`.
    - Example: `(i * 2N + r) % (2N - 1)` — rewrite `2N` as `1 (mod 2N-1)`, getting `i + r`. Since `0 <= i + r <= 2N - 2 < 2N - 1`, it folds directly to **`i + r`**!
  - **Divmod recombine** (`fold_add_divmod_recombine` in [symbolic.py:47](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/symbolic.py:47)): `(x // c) * c + (x % c)` → `x` (cancels out reshape-then-reshape-back).
- **Why we need it:** Without this, every `reshape` in Llama (Q/K/V head splits, GQA `repeat_interleave`, `arange`) leaves behind slow integer divisions and prevents `arange` from simplifying at all.

---

### 5. `symbolic` ([symbolic.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/symbolic.py)) — *keep index algebra in a canonical, minimal form*
You already have basic constant folding in [compiler/ops.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/ops.py). Tinygrad's `symbolic` adds the integer/boolean rewrite rules that make patterns *match* reliably:
- **Canonical ordering & combining terms:**
  - `(x + c) + y` → `(x + y) + c` (constants drift to the right so they fold together)
  - `x * c0 + x * c1` → `x * (c0 + c1)`, `x + x` → `x * 2`, `c * (x + k)` → `c*x + c*k`
- **Inequality & `max` folding:**
  - `c0 + x < c1` → `x < c1 - c0`
  - `x // d < c` → `x < c * d`
  - `max(x, y)` → `x` when `x.vmin >= y.vmax`
- **Boolean & `WHERE` simplification:**
  - `(!c).where(t, f)` → `c.where(f, t)`
  - `a.where(b.where(x, d), d)` → `(a & b).where(x, d)` (merges nested `PAD` gates into one)
  - `vmin == vmax` → `CONST`
- **Why we need it:** Pattern matchers are syntactic — they look for specific tree shapes. Canonicalization ensures `a + 3 + b + 5` always becomes `(a + b) + 8` and nested `WHERE`s collapse so downstream rules (`divmod`, `reduce_collapse`) can recognize them.

---

### 6. `pm_reduce_simplify` / `reduce_collapse` ([simplify.py:83-154](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py:83-154)) — *kill `arange` reductions*
- **Purpose:** Evaluates a `REDUCE(ADD, r)` in closed form when the body only depends on `r` through comparisons (no buffer loads).
- **What it matches:**
  - `reduce_unparented`: `SUM_{r=0..N-1} val` (where `val` doesn't use `r`) → `N * val`
  - Lift loop-invariant terms out of `<`: `(r + y) < c` → `r < c - y`
  - **Counting rule** ([simplify.py:106-112](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py:106-112)):
    - `SUM_{r=0..N-1} WHERE(r < upper, val, 0)` → `max(min(upper, N), 0) * val`
    - `SUM_{r=0..N-1} WHERE(r < lower, 0, val)` → `max(N - max(lower, 0), 0) * val`
- **Why we need it:** This is what turns all 4 `arange` cumsums in [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) from $O(N^2)$ reductions into $O(1)$ loop variables.

---

### 7. `pm_load_collapse` / `reduce_load_collapse` ([simplify.py:122-161](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py:122-161)) — *turn one-hot embedding into a gather*
- **Purpose:** Collapses a sum over a Kronecker delta (`idx == r`) into a single direct lookup.
- **What it matches:**
  ```python
  REDUCE(ADD, r in [0, N), WHERE(idx == r, expr(r), 0))
  ```
  → rewrites to:
  ```python
  WHERE((idx >= 0) & (idx < N), expr(idx), 0)
  ```
- **Why we need it:** Because `idx == r` can only be true for *one* value of `r`, summing `128,256` rows of `weight` is identical to indexing `weight` directly at `r = idx`. That's how `Embedding` becomes a single gather with zero special embedding op!

---

### 8. Bufferize / Stage cleanup & Kernel splitting ([rangeify.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/rangeify.py))
- **Purpose:** Decides which intermediate tensors stay **fused in registers** vs. get **materialized into a buffer (`ALLOC` + `STORE` + separate kernel)**.
- **What it does:**
  - During `run_rangeify`, whenever a tensor has multiple consumers with different access patterns, or a reduction feeds a broadcast (like RMSNorm's scalar variance feeding all 2048 elements), it marks that node with `STAGE` (tinygrad's bufferize).
  - `pm_remove_bufferize` drops unnecessary `STAGE`s (e.g. a tiny cheap elementwise or pure index view that's faster to recompute than write to memory).
  - `bufferize_to_store` turns each surviving `STAGE` into `ALLOC` + `STORE(...).end(*ranges)`.
  - `split_kernels` wraps each top-level `STORE`/`END` into its own `CALL(SINK(...), *buffers)` — giving you the clean list of Layer 1 kernels to schedule onto Blackhole cores.

---

### Putting it all together: watching Embedding collapse step by step

Take `Embedding` in [llama-graph.txt:185-206](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:185-206) (`N = 128256`).

**Part A — `arange(N)` (`%187`–`%197`) for output index `i ∈ [0, N)`:**
1. **`rangeify`** walks backwards through `reduce` → `permute` → `shrink` → `reshape(N, 2N)` → `pad(0, N)` → `reshape` → `expand` → `pad(N-1, 0)` on const `1`:
   - Creates reduction range `r ∈ [0, N)`.
   - Flattened index entering `pad(0, N)` is `i * 2N + r`.
   - `pad(0, N)` adds validity check `i * 2N + r < 2N² - N`.
   - **`vmin`/`vmax` + `symbolic`**: max value of `i * 2N + r` is `(N-1)*2N + (N-1) = 2N² - N - 1`, which is strictly `< 2N² - N` → gate folds to `True` and disappears!
   - `reshape` + `expand` produces `(i * 2N + r) % (2N - 1)`.
   - **`div_and_mod_symbolic`**: since `2N ≡ 1 (mod 2N-1)` and `0 <= i + r <= 2N - 2 < 2N - 1`, `(i * 2N + r) % (2N - 1)` collapses to **`i + r`**.
   - `pad(N-1, 0)` adds gate `(i + r >= N - 1) & (i + r < 2N - 1)`.
   - **`vmin`/`vmax`**: `i + r < 2N - 1` is always `True` → only `!(i + r < N - 1)` remains.
   - The whole `128256 × 128256` subgraph is now just:
     ```
     SUM_{r=0..N-1} WHERE(i + r < N - 1, 0, 1)  +  (-1)
     ```
2. **`pm_reduce_collapse` + `symbolic`**:
   - Lift `i` out of `<`: `r < (N - 1) - i`.
   - Counting rule: `max(N - max(N - 1 - i, 0), 0) * 1`.
   - `vmin`/`vmax` proves `N - 1 - i >= 0`, so `max(N - 1 - i, 0) = N - 1 - i`.
   - Algebra: `N - (N - 1 - i) = i + 1`, then `(i + 1) + (-1)` = **`i`**.
   - The entire `arange` reduction is completely gone!

**Part B — One-hot lookup (`%198`–`%205`) for output indices `(b=0, s=0, d ∈ [0, 2048))`:**
3. With `arange` replaced by `i` (and `dtype=self.weight.dtype` on `.sum(-2)`), the embedding reduction is now:
   ```
   SUM_{i=0..128255} WHERE(tok[0] == i, t0[i, d], 0.0)
   ```
4. **`pm_load_collapse`** matches `(idx == i).where(expr, 0).reduce(i, ADD)` and substitutes `i = tok[0]`:
   ```
   WHERE((tok[0] >= 0) & (tok[0] < 128256), t0[tok[0], d], 0.0)
   ```
   A single gather loop over `d ∈ [0, 2048)` — no `128256` loop anywhere.

Everything in that chain — `rangeify`, `vmin`/`vmax`, `Invalid`, `div_and_mod`, `symbolic`, `reduce_collapse`, `load_collapse` — is just the minimal set of algebraic rules needed to make that derivation happen automatically and generally (not just for embedding, but for RoPE, `argmax`, GQA, matmul reshapes, and KV-cache slicing too).

---

## Turn 3

### User

Ok this is surprisingly understandable... what was the intuition behind rangeify turning shapes / reshapes into loops? can you pull when tinygrad had ShapeTracker and compare? how is this simpler? how are shapes tracked? every uop has a .shape as a computed property, not saved, yes? how is that computed

### Gemini

### 1. The intuition behind rangeify: a tensor is just a function of indices

Instead of thinking of a tensor of shape `(M, N)` as a box of numbers in memory, think of it as a **function `f(i, j)`** defined for `0 <= i < M, 0 <= j < N`.

From that point of view, **every movement op is just a coordinate transform** on the indices passed into `f`:

- **`PERMUTE([1, 0])`**: `g(i, j) = f(j, i)` (just swap the args)
- **`SHRINK` (offset `o`)**: `g(i) = f(i + o)`
- **`EXPAND` (add axis `k`)**: `g(k, i) = f(i)` (ignore `k`)
- **`PAD` (offset `o`, size `s`)**: `g(i) = f(i - o)` if `o <= i < o + s` else `0`
- **`RESHAPE` from `(A, B)` to `(C, D)`**: flatten `(c, d)` to a 1D index `k = c * D + d`, then unflatten to `(k // B, k % B)`:
  `g(c, d) = f((c*D + d) // B, (c*D + d) % B)`

Notice which direction that flows: **backwards, from output to input.**

That's all `rangeify` ([indexing.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py)) does:
1. Start at the final `STORE` (output buffer of shape `(M, N)`), and mint loop variables `r0 ∈ [0, M)`, `r1 ∈ [0, N)`.
2. Walk **backwards** through the graph, handing each node the coordinates its consumer wants:
   - Elementwise op (`add`, `mul`, `exp2`, …): passes the same `(r0, r1)` to its inputs → **automatic fusion!**
   - Movement op: transforms `(r0, r1)` with `apply_movement_op` ([indexing.py:163-178](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py:163-178)) and hands the transformed index expressions to its input.
   - `REDUCE`: mints a new loop variable `r_k` for the reduced axis and prepends it to the input's coordinates.
   - `BUFFER`: stops and emits `buf.index(idx0, idx1, ...)` — now you have the exact memory indexing formula.
3. Whenever a node has **multiple consumers asking for different coordinates** (or a `REDUCE` feeds a broadcast/expand), you can't just pass one set of loop variables through — so rangeify inserts a `STAGE` (materialization boundary), gives that node its own fresh output ranges, and each consumer indexes into the staged buffer.

---

### 2. Comparing with old tinygrad (`ShapeTracker`) — why rangeify is much simpler

In tinygrad's git history, `ShapeTracker` was deleted in commit `1d1e1d9d8` (*"delete the ShapeTracker (#12720)"*, Oct 2025). Right before deletion (`ee0382ad9~1`), `tinygrad/shape/view.py` + `shapetracker.py` was **~437 lines** of dense custom geometry code.

**How `ShapeTracker` worked:**
- Every buffer view carried a `ShapeTracker(views=(View1, View2, ...))` inside an `Ops.VIEW` node, where each `View` stored `(shape, strides, offset, mask)`.
- Whenever you did a movement op, it tried to eagerly merge consecutive `View`s into one `View` via:
  - `View.__add__` (~80 lines of projecting strides, offsets, and masks of one `View` onto another)
  - `_reshape_mask` (intricate case-by-case logic for splitting/merging rectangular pad masks across reshapes)
  - `merge_dims`, `minify`, `real_strides`
  - `invert()` (trying to run a `ShapeTracker` backwards so the scheduler could push views across reductions/fusion boundaries)
- And at codegen time, `views_to_valid_uop` *still* had to convert the whole `View` stack into UOp index math (`//`, `%`, `<`, `WHERE`) and run `sym` on it!

**Why `rangeify` is way simpler:**
1. **One algebra instead of two.** `ShapeTracker` had to maintain a whole second algebraic system (strides + rectangular masks + view merging) *in parallel* with UOp symbolic simplification. Rangeify deletes `ShapeTracker`, `View`, and `Ops.VIEW` completely. Look at the actual comment in [indexing.py:158](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/indexing.py:158):
   ```python
   # this simplify is doing a lot of heavy lifting. this is the replacement for the reshape view merging code
   return graph_rewrite(UOp.sink(*axes_out[::-1]), symbolic+pm_simplify_valid+pm_drop_and_clauses, name="reshape")
   ```
   All ~437 lines of `View`/`ShapeTracker` became **15 lines of `apply_movement_op`** + the *same* `symbolic` / `div_and_mod_symbolic` rewriter you already need for kernel index arithmetic anyway.
2. **No "unmergeable view stacks" or failed `invert()`.** `View` could only represent affine strides and axis-aligned rectangular masks. Anything weird (like `pad` → `reshape` in `arange`, or dynamic symbolic shapes) couldn't merge into one `View`, forcing multi-view stacks or extra kernel splits. With rangeify, indices are arbitrary UOp expressions, so non-rectangular masks, symbolic bounds, `arange`, and gather collapse all work uniformly.
3. **Fusion and indexing are unified.** Previously, scheduling/fusion had to reason about `ShapeTracker`s, swizzles, and `invert()` as a separate phase before lowering views to indices. In rangeify, *whether two consumers agree on their ranges* directly determines fusion vs. bufferization.

---

### 3. How shapes are tracked (and how `.shape` is computed)

**Yes — `.shape` is a computed property, not stored as a field on `UOp`.**

Both `blackhole-py` ([compiler/uop.py:93-178, 322-323](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:93-178)) and `tinygrad` ([tinygrad/uop/ops.py:318-425](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/ops.py:318-425)) use `@recursive_property`:
- Because `UOp` is immutable and hash-consed, its shape never changes.
- `@recursive_property` computes `.shape` **lazily** on first access, in **iterative post-order** (so deep graphs like 16 layers of Llama never hit Python's recursion limit), and caches the result in `u.__dict__["shape"]`.
- Even the shape arguments of `BUFFER`, `ALLOC`, `RESHAPE`, `PAD`, `SHRINK`, etc. aren't special metadata fields — they are regular UOps in `u.src` (`CONST` for 1D, `STACK` of `CONST`/symbolic `UOp`s for N-D), decoded via `as_shape` ([compiler/uop.py:334-337](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:334-337)). That's why symbolic shapes like `(1, 32, 1, (p1+1), 64)` just work as ordinary graph dependencies!

**How `shape_from_uop` derives each op's shape** ([compiler/uop.py:142-178](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:142-178)):

| Op kind | `.shape` rule |
|---|---|
| `CONST`, `RANGE`, `SPECIAL`, scalar `PARAM` var | `()` (0-D scalar) |
| `BUFFER`, `ALLOC`, shaped `PARAM` | `src[0].as_shape` (declared shape) |
| Unary (`NEG`, `EXP2`, `SIN`, …), `CAST`, `BITCAST`, `AFTER` | `src[0].shape` (passthrough) |
| Binary / Ternary (`ADD`, `MUL`, `WHERE`, …) | `_broadcast_shape(*(s.shape for s in src))` (right-aligned NumPy broadcasting) |
| `RESHAPE` | `marg` (verifies `sprod(in) == sprod(out)`) |
| `EXPAND` | `tuple(marg) + src[0].shape` (adds dims on the left) |
| `PERMUTE` | `tuple(ps[i] for i in marg)` |
| `PAD` / `SHRINK` | `tuple(sz for _, sz in marg)` |
| `REDUCE(op, n)` | `src[0].shape[n:]` (drops the `n` reduced leading axes) |
| `STACK` | `(len(src),) + src[0].shape` |

And once you enter **rangeify** (in [tinygrad/uop/ops.py:344-364](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/ops.py:344-364)), `INDEX` and `STAGE` are exact shape inverses of each other:
- **`INDEX(buf, r0, r1)`** *consumes* the leading indexed axes: indexing a `(128256, 2048)` buffer with 2 scalar ranges produces shape `()` (a single scalar element).
- **`STAGE(val, r0, r1)`** *re-introduces* axes from the ranges it closes: staging a scalar `val` over ranges `r0 ∈ [0, M)`, `r1 ∈ [0, N)` produces a buffer-like value of shape `(M, N)`.

So shapes aren't "tracked" by any side data structure at all — they are just a pure structural property of the UOp DAG, and once rangeify converts movement ops into `INDEX`es with `RANGE`s, every value inside a kernel simply has scalar shape `()`.

---

## Turn 4

### User

ok not bad at al.. can you add this to blackhole-py?

### Gemini

Added `symbolic`, `div_and_mod_symbolic`, `rangeify`, `reduce_collapse`, and `load_collapse` to `blackhole-py` and wired them into `lower_tensor`.

### What was added / changed
- **[compiler/dtype.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/dtype.py)**: Added the `Invalid` sentinel (`InvalidType`, `dtypes.from_py(Invalid) -> dtypes.bool`), `DType.min`/`DType.max`/`DType.const()`, and `dtypes.wints` / `dtypes.swints`.
- **[compiler/uop.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py)** & **[compiler/mixin.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/mixin.py)** & **[compiler/uir.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/uir.py)**:
  - Full iterative `@recursive_property` `_min_max` bounds (covering `RANGE`, `SPECIAL`, `MOD`, `DIV`, `CMPLT`/`CMPEQ`/`CMPNE`, `AND`/`OR`/`XOR`, `WHERE`, `CAST`, `PAD`, `INDEX`, etc.) and `ranges` / `tuplize` (`CONST` sorts last so commutative canonicalization keeps constants on the right).
  - Multi-axis `UOp.index(*idxs)`, `StageArg`, `Invalid` helpers (`valid()`, `get_idx()`, `get_valid()`, `Invalid` never casts), divisibility helpers (`const_factor`, `divides`, `divide_exact`, `gcd`, `split_uop`, `pop_const`), `BottomUpGate` in `graph_rewrite`, and `UPat` pattern builders (`cvar`, `cval`, `or_casted`, arithmetic/bool operators).
  - UIR render/parse support for `invalid` and `StageArg`.
- **[compiler/symbolic.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/symbolic.py)**:
  - `div_and_mod_symbolic` (`fold_divmod_general` congruence/factoring/nested-div/gcd rules + fast inline rules)
  - `pm_data_invalid`, `pm_remove_invalid`, `pm_uncast_const`
  - `symbolic_simple`, `commutative`, `symbolic` (normalizing `weakint` `SUB`/`NEG` to additive/multiplicative form, term combining, `vmin == vmax -> CONST`, `lt_folding`, `fold_add_divmod_recombine`, `WHERE`/bool/cast folding)
  - `pm_simplify_valid` (`parse_valid`, `uop_given_valid`, `simplify_valid`, `pm_drop_and_clauses`), `pm_move_where_on_load`, and `sym`.
- **[compiler/rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py)**:
  - `apply_movement_op` + `pm_mops`
  - `run_rangeify` (realize map including `CALL` args, user `.contiguous()` 1-src `STAGE`, and WAR hazards on `STORE`; backward range propagation; `REDUCE`/`PAD`/`STACK` lowering)
  - `pm_reduce_simplify` (`reduce_unparented` + `pm_reduce_collapse` — collapses `arange` cumsums to plain `RANGE`s)
  - `pm_load_collapse` (`pm_reduce_load_collapse` — collapses one-hot `where(idx == r, expr, 0).sum()` into a single gated gather, including pushing `CAST` through `WHERE(..., 0)` so default `bf16 -> fp32 -> bf16` `sum(-2)` collapses cleanly without changing model code)
  - `pm_const_buffer_folding`, `pm_remove_bufferize`, `pm_add_buffers` (handles symbolic shapes via `max_shape` `ALLOC`s), `split_kernels` (anonymous `KernelArg("")` for hash-cons deduplication + per-kernel `pm_load_collapse` + lowering read/gated `INDEX`es into Layer 1 `LOAD`/`STORE` with no `Invalid` remaining), and once-per-body lowering of `@function` `CALL`s.
- **[compiler/tensor.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/tensor.py)** & **[compiler/__init__.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/__init__.py)**: Wired `lower_tensor(root)` to `get_kernel_graph` and exported the new passes.
- **[test/test_rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/test/test_rangeify.py)**: Added unit tests + a minimal Layer 1 Python kernel interpreter to numerically verify lowered kernels.

### Verification
- `python3 -m unittest test/test_isa.py test/test_rangeify.py -v`: **17 tests run, all passed** (1 pre-existing skip for `sfpu.py`) in 0.74s:
  - `arange` (int, strided, negative step, float): lowers to 0 `REDUCE`s and executes identically to Python.
  - `Embedding` (both default `sum(-2)` and `sum(-2, dtype=w.dtype)`): lowers to a single 1D gated gather kernel (`0` reduces, single loop over `dim`), verified on both in-bounds and out-of-bounds token indices.
  - `argmax`, `matmul + silu + softmax`, and `KV cache` in-place `store`+`after` with symbolic `start_pos` inside `@function`: numerically verified across multiple runtime values of `start_pos`.
- Full **[examples/nanbeige.py](/Users/boop/code/tenstorrent/blackhole-py/examples/nanbeige.py)** (52 layers):
  - Decode lowers in **0.34s** to **17 unique Layer 1 kernels** (embedding is a single 19-line gated gather, RoPE COS/SIN have 0 reduces, `argmax` has no `arange` cumsum).
  - Prefill lowers in **0.34s**.
  - All 17 kernels pass `verify()` and round-trip identically through `parse_uir(render_uir(k)) is k`.
- Full **[examples/inkling.py](/Users/boop/code/tenstorrent/blackhole-py/examples/inkling.py)** decode & standalone MoE also lower and pass `verify()`.

---

## Turn 5

### User

nice. can you write the new graphs (replacing llama-graph.txt) so i can go through them? what's next?

### Gemini

Updated [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) with the lowered Layer 1 kernel graph for [examples/nanbeige.py](/Users/boop/code/tenstorrent/blackhole-py/examples/nanbeige.py) decode (1,123 lines, 17 unique kernels across all 52 layers).

### Highlights to look at in [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt)
- **Argmax** ([llama-graph.txt:1-19](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:1-19)): two 1D `max` reduces over `166912` — the `166912 × 166912` `arange` cumsum is gone.
- **Final RMSNorm + `lm_head` fused** ([llama-graph.txt:21-50](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:21-50)): `recip(rms) * x * norm_w` is fused straight into the `lm_head` matmul kernel.
- **Deduplicated `_block` body** ([llama-graph.txt:51-388](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:51-388)): 13 unique kernels (RMSNorm, Q/K/V/O matmuls, RoPE, KV-cache in-place stores, dynamic `(p1+1)` attention, softmax, SwiGLU MLP) called 52 times (`%387`).
- **Embedding gather** ([llama-graph.txt:440-460](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:440-460)): 16 lines, single gated `load` over `range 7168` (`0` reduces).
- **RoPE `COS` / `SIN` tables** ([llama-graph.txt:464-492](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:464-492)): `0` reduces — both `arange`s collapsed to `%465` and `%93 % 64`.

Also tested [examples/qwen.py](/Users/boop/code/tenstorrent/blackhole-py/examples/qwen.py) decode along the way and caught one edge case (a value-wrapping `AFTER` in Gated DeltaNet) — fixed in [compiler/rangeify.py:252-265](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py:252-265), so all three models (`nanbeige.py`, `qwen.py`, `inkling.py`) now lower cleanly and pass `verify()` (`qwen` decode lowers in 0.60s to 37 unique kernels).

---

### What's next (Layer 1 → Blackhole hardware)

Now that `lower_tensor` gives you a clean, verified Layer 1 kernel graph, the remaining pieces to run inference on Blackhole are:

1. **Schedule + buffer/memory planner (`create_schedule`)**
   - Toposort the kernel `CALL` graph into an execution queue (recursing into `@function` calls or keeping them callable).
   - **Buffer liveness / reuse:** right now [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) has 52 separate `(1, 1, 7168)` activation allocs (`a0`–`a51`) plus per-block temps; a linear-scan lifetime allocator collapses those into a handful of ping-pong buffers in DRAM/L1.
   - **One-time init hoisting:** kernels with no runtime inputs (like RoPE `COS`/`SIN` at lines 464–492) only need to run once at model init, not every decode step.

2. **Blackhole kernel optimizer & tiling (`RANGE` → cores + 32×32 tiles)**
   - Split outer `RANGE`s into **`SPECIAL` core grid axes** (sharding matmul output columns, attention heads, embedding dim, etc. across Blackhole's Tensix grid).
   - Split inner `RANGE`s into **32×32 tile chunks** (padding/gating non-multiples of 32 — e.g. decode `M=1` or dynamic `start_pos+1` — using the `symbolic` + `div_and_mod` machinery we just added).
   - Classify / match each kernel's compute pattern:
     - **Matmul / dot-product** (`REDUCE(ADD, mul(a, b))`) → FPU `MVMUL` + `UNPACR`/`PACR`
     - **Elementwise / reductions** (RMSNorm, softmax, SiLU, RoPE, argmax) → SFPU (`compiler/sfpu.py`) / FPU `ELW*`
     - **Gather / scatter / slice copy** (Embedding, KV-cache write) → BRISC/NCRISC NoC DMA (`fw/dma.c` / RV32).

3. **5-core kernel codegen (Layer 1 → `Ops.LINEAR` → `Ops.PROGRAM`)**
   - Finish porting [compiler/sfpu.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/sfpu.py) onto the current `UOp` core.
   - Emit the coordinated 5-core streams (`brisc` DRAM→L1 CB push, `ncrisc` L1→DRAM CB pop, `trisc0` `UNPACR`, `trisc1` FPU/SFPU math, `trisc2` `PACR`) and compile via existing `compiler/isa` (`RV32Renderer` + `BlackholeRenderer`).

4. **Host runtime (`Tensor.realize()`)**
   - Stream weights from `_BUFFER_SOURCE` (safetensors) into Blackhole DRAM, patch runtime args (buffer addresses + bound `start_pos`), launch the scheduled kernel binaries, and read back the output token.

A great incremental milestone before tackling full Llama is picking **one kernel** (e.g. `Embedding` gather on BRISC/NoC, or a single fused elementwise/RMSNorm kernel on SFPU, or one tiled matmul) and pushing it all the way from `Tensor` → `lower_tensor` → Blackhole silicon and checking the numbers against our Python evaluator in [test/test_rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/test/test_rangeify.py).

---

## Turn 6

### User

right now everything we've written is blackhole-independent, right? I'm going to go and read all the code and see if i can improve it

### Gemini

Yes — everything we added (`dtype.py`, `uop.py`, `mixin.py`, `uir.py`, `symbolic.py`, `rangeify.py`, `tensor.py`) is **100% Blackhole-independent** generic graph/loop IR (the only hardware-specific files in `compiler/` are `compiler/isa/*` and `compiler/sfpu.py`, plus the `bfp8`/`bfp4`/`e4m3` dtype entries already in `dtype.py`).

A few specific things worth eyeing while you read through it:

1. **Duplicate folding rules** between [compiler/ops.py:68-113](/Users/boop/code/tenstorrent/blackhole-py/compiler/ops.py:68-113) (`pm_simplify`) and [compiler/symbolic.py:165-232](/Users/boop/code/tenstorrent/blackhole-py/compiler/symbolic.py:165-232) (`symbolic_simple`) — left `pm_simplify` intact so `pm_frontend` / `sfpu.py` wouldn't change behavior, so there's an obvious cleanup to unify them.
2. **When to lower `Invalid`-gated `INDEX` → `LOAD`/`STORE`** ([compiler/rangeify.py:567-598](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py:567-598)): right now `_lower_kernel_mem` converts `INDEX` to `LOAD` and strips `Invalid` at the end of `_split_store` so kernels pass `verify()` and match `rv32.py`. If you later add a range-splitting/tiling pass (e.g. `pm_split_ranges` / `pm_simplify_ranges` for 32×32 tiles), you'll probably want to run that *before* `_lower_kernel_mem` while `Invalid` gates and `sym` still apply cleanly.
3. **`_remove_bufferize` fusion heuristic** ([compiler/rangeify.py:424-460](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py:424-460)): ported tinygrad's `len(accessed_buffers) > 3` and "don't inline reduces touching buffers" rules verbatim — you'll see in [llama-graph.txt:21-50](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt:21-50) that it fused RMSNorm scale into `lm_head`, which is nice, though you may want to tune what fuses vs. stages for Blackhole L1/CB limits later.
4. **Range merging / splitting**: we didn't port `pm_simplify_ranges` or `pm_split_ranges` from [tinygrad/codegen/simplify.py](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/simplify.py) yet — easy to add when you start tiling loops.

Have fun reading through it, and ping me if anything looks weird or you want to refactor/extend any part of it.

---

## Turn 7

### User

we havent generated kernels, right? it's more complicated than generating an ops.sink in certain places, how does this work in tinygrad? does it scan the graph for places where a barrier is inserted? i feel like tinygrad's fusion is not good enough for blackhole.

### Gemini

You're spot on — both about what we have right now and about tinygrad's fusion limits for Blackhole.

### 1. What we actually generated (and how tinygrad does it)
What `lower_tensor` produced in [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt) are **unoptimized kernel boundaries (kernel ASTs)** — the exact equivalent of tinygrad's `get_kernel_graph()`. We haven't mapped loops to cores/tiles or generated machine code yet.

Tinygrad does **not** scan for `BARRIER`s to split kernels; it works in the opposite order in two separate stages:

1. **Kernel splitting happens first, on `STAGE` (bufferize) boundaries** ([tinygrad/codegen/rangeify.py:295-335](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/rangeify.py:295-335)):
   - During `run_rangeify`, tinygrad inserts a `STAGE` (`AddrSpace.GLOBAL`) whenever:
     - a **`REDUCE` feeds a broadcast/expand** (RMSNorm scalar → 7168 elements, Softmax `max`/`sum` → seq_len, Matmul → next Matmul),
     - **multiple consumers** index a tensor with incompatible ranges (e.g. `scores` feeding both `max` and `sub`), or
     - there's a WAR hazard / explicit `.contiguous()` / too many buffers.
   - `pm_remove_bufferize` drops cheap elementwise `STAGE`s, and **every surviving `STAGE` becomes a global DRAM `ALLOC` + a separate kernel `CALL(SINK(...))`**.
   - You can see the exact result in [llama-graph.txt](/Users/boop/code/tenstorrent/blackhole-py/llama-graph.txt): `_block` got cut into **13 separate kernels** (e.g. RMSNorm became one kernel writing a single `fp32 (1,)` scalar `a66` to memory, then another kernel reading that 1 float back).

2. **`BARRIER`s only show up *later*, inside a single already-split kernel** ([tinygrad/codegen/__init__.py:150-158, 242-262](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/__init__.py:150-158)):
   - After splitting, tinygrad's per-kernel optimizer (`codegen/opt`) splits ranges into `GLOBAL` (thread blocks), `LOCAL` (workgroup threads), `UPCAST` (SIMD/regs), and `WARP` (tensor cores).
   - It only introduces `AddrSpace.LOCAL` (shared memory) + `Ops.BARRIER` inside *one* kernel for parallel `GROUP_REDUCE` (multiple threads reducing the same axis via shared memory), with `pm_implicit_barriers` automatically inserting RAW/WAR `BARRIER`s around local stores/loads.

---

### 2. Why tinygrad's fusion isn't good enough for Blackhole

Tinygrad's fusion model is designed around **GPU constraints**, which are almost the opposite of Blackhole's:

| | GPU (what tinygrad assumes) | Blackhole |
|---|---|---|
| **Memory hierarchy** | Tiny shared mem (~100 KB/SM), huge hardware **L2 cache** that silently catches small DRAM round-trips | **No hardware cache**, but **1.5 MB L1 SRAM per core (~180+ MB on-chip)** — any DRAM `ALLOC` is a real off-chip GDDR6 round-trip |
| **Inter-core comms** | SMs can't sync or talk directly → cross-chip reduce (RMSNorm, K-split matmul) **must** end the kernel | Cores talk directly over **2D NoC** (multicast / reduce-scatter / semaphores in L1) — no kernel exit needed |
| **Execution model** | Lockstep SIMT warps, uniform kernel per grid | 5 independent RISCs + FPU/SFPU per core, **Circular Buffers (CBs)** for producer-consumer streaming |

Concretely, tinygrad's `STAGE -> DRAM kernel` rule hurts Blackhole in four ways:
1. **Activations shouldn't touch DRAM at all during decode.** A `(1, 1, 7168)` bf16 activation is only 14 KB — tinygrad writes it (and RMSNorm's 4-byte scalar, Q/K/V, attention scores, SwiGLU hidden) to DRAM between every kernel, when the entire residual stream + intermediates fit in L1 SRAM across the grid.
2. **Multi-reduction fusion:** RMSNorm → Q/K/V matmuls, or FlashAttention (`QK^T → online softmax → @V`), or `gate_proj` + `up_proj` sharing the same L1-multicast input shouldn't bounce through DRAM.
3. **Horizontal / multi-output fusion:** Q, K, and V projections (or `gate_proj` and `up_proj`) read the exact same input vector; tinygrad splits them into 3 separate kernels because each has its own `STORE`. On Blackhole you either fuse them or multicast the input once over NoC.
4. **Persistent / megakernel execution:** On Blackhole decode, launching 13 × 52 = ~676 kernels from the host would drown in dispatch overhead compared to keeping activations L1-resident and syncing via NoC semaphores across layers (or running a single persistent loop over layers).

### How `rangeify` still fits in
The good news is you **don't** have to throw away `rangeify` + `symbolic`:
- `rangeify` + `pm_reduce_simplify` + `pm_load_collapse` is still what gives you the clean, movement-op-free loop/dataflow graph (with `arange` and `Embedding` already collapsed).
- The GPU-specific part is **only** the last 50 lines of [compiler/rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py) (`_remove_bufferize`, `_bufferize_to_store`, `_split_store`), which currently treat every surviving `STAGE` as a DRAM `ALLOC` + separate kernel.
- For Blackhole, instead of blindly mapping `STAGE -> DRAM + new kernel`, `STAGE` can carry a memory space / sharding choice:
  - **Registers / Dst** (fused, no `STAGE`),
  - **L1 / CB** (stays on-chip — either inside a fused/tiled kernel with a local/NoC barrier, or L1-sharded across kernels without ever touching DRAM),
  - **DRAM** (weights, KV cache, huge prefill buffers that genuinely spill L1).

That's a great lens to keep in mind while reading [compiler/rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py) — the top ~400 lines (movement lowering + range propagation + reduce/load collapse) are universal, and the bottom ~200 lines (`STAGE` placement + kernel splitting) are where Blackhole-specific fusion/L1 decisions belong.

---

## Turn 8

### User

I kind of want to start on the lowest side and build back up to a place where these can merge. i kept the top level purposefully similar to tinygrad (minus the kernel fusion rules i'm about to change) so that merging into tinygrad later is easier, but hte bottommost layer is ops.ins? or have htey replaced it with ops.native/ops.call? i'm not sure i understand how that works. we need to get all the way to a real risc-v program with fences, risc-v math, config words, etc, etc... there will be many stages. but we can start designing the lowest layer.

### Gemini

### 1. `UOp.ins` vs `Ops.NATIVE` / `Ops.CALL` — they're the same thing

Tinygrad has **no `Ops.INS` opcode**. `UOp.ins(...)` is just a helper constructor ([tinygrad/uop/ops.py:583-586](/Users/boop/code/tenstorrent/tinygrad/tinygrad/uop/ops.py:583-586)) that builds a `CALL` to a `NATIVE`:

```python
UOp.ins(op, src, dtype, *regs)
# literally constructs:
CALL(NATIVE(code=op, src=reg_metadata), *src)
```

How the two nodes split responsibilities:
- **`Ops.NATIVE`** is the "instruction descriptor":
  - `arg = NativeInfo(code=op)` holds the machine opcode / struct (e.g. `RVOps.ADDI`, `hw_isa.MOVA2D(...)`, `SfpSpec(...)`).
  - `src[0]` holds the **destination register metadata** (a physical register `PARAM`, or a virtual register `PARAM` + `STACK` of allowed physical registers via `AFTER`). Its `dtype` gives the instruction's result type.
- **`Ops.CALL`** is the actual instruction instance in the graph:
  - `src[0]` is that `NATIVE` (the `body`).
  - `src[1:]` are the **input operands** (other instructions, registers, immediates, or ordering deps).

**Why tinygrad does this:**
- Zero new core `Ops` per architecture — `CALL(NATIVE, *args)` works identically for x86 (`tinygrad/renderer/x86.py`), RV32, Tensix, or C/LLVM intrinsics.
- Because `NATIVE` sits in `src[0]` (`body`), `toposort(enter_calls=False)` and `src_without_body` naturally traverse only data/effect inputs while keeping register constraints attached to `NATIVE.src[0]`.

You **already have this exact mechanism built** in `blackhole-py`:
- [compiler/uop.py:567-575](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:567-575) (`UOp.ins`)
- [compiler/isa/__init__.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/__init__.py) (`vreg`, `ISARenderer`, CFG-aware `regalloc` with spilling, `to_program`)
- [compiler/isa/rv32.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/rv32.py) (`RVOps`, `RV32Renderer`, `encode_rv32` — already compiling loops, spills, and `BACKEDGE` polling loops to real RV32IM bytes!)
- [compiler/isa/tensix.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/tensix.py) (`tt_ins`, `sfp_ins`, `encode_tensix_inline`, `fix_sfpu_hazards_uops`, `split_roles`, `BlackholeRenderer`)

---

### 2. How a UOp DAG becomes real machine bytes (`to_program`)

In both tinygrad (`x86.py`) and [compiler/isa/__init__.py:242-257](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/__init__.py:242-257), the bottom layer is 5 clean passes:

1. **Instruction selection (`isel`, `graph_rewrite` on the DAG):** rewrites ALU/LOAD/STORE/BACKEDGE/Tensix ops into `UOp.ins(...)` with virtual registers (`vreg`).
2. **Linearization (`linearize -> list[UOp]`):** flattens the DAG into an ordered instruction list respecting `RANGE`/`END` nesting and `AFTER` chains. (Once in `Ops.LINEAR`, repeated identical ops like `MOVA2D` or `SFPNOP` no longer hash-cons collapse.)
3. **Pre-regalloc `line_rewrite`:** lowers `RANGE`/`END` into explicit counter init, `LABEL`, and `BGE`/`JAL` branches.
4. **CFG-aware `regalloc`:** computes liveness across branches and `BACKEDGE` loops, colors virtual registers onto physical pools (`x6..x29` for RV32, `L0..L7` for SFPU), and inserts spills/fills (`x30..x31` + `LOCAL_BASE`).
5. **Post-regalloc `line_rewrite` + `assemble`:** expands `LI -> LUI+ADDI`, inserts `SFPNOP` hazards, patches PC-relative branch offsets, emits 32-bit RV32IM + inline Tensix words (`hw.isa.inline`), and wraps into `Ops.PROGRAM(sink, linear, source, binary)`.

---

### 3. Designing the real Blackhole lowest layer (bottom-up)

Look at [fw/boot.c:28-36](/Users/boop/code/tenstorrent/blackhole-py/fw/boot.c:28-36) — your firmware ABI is already super clean for codegen:
- `boot.c` already initializes the base registers before jumping to `_end`:
  - `x3 (gp)` = `LOCAL_MEM + 2048`
  - `x4 (tp)` = `NOC_REGS(0)` (BRISC), `NOC_REGS(1)` (NCRISC), `TENSIX_CFG` (TRISC0), `PC_BUF` (TRISC1/2) `+ 2048`
  - `x5 (t0)` = `PC_BUF + 2048` (TRISC0)
- That means +/-2KB MMIO loads/stores to local mem, NoC regs, Tensix cfg, and `PC_BUF` are single `LW`/`SW` instructions off `x3`/`x4`/`x5` (which [rv32.py:56](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/rv32.py:56) already reserves!).

To build the lowest layer cleanly from silicon up (so it can run real programs on Blackhole right away and later meet the upper compiler in the middle), I'd break the bottom layer into **3 sub-layers**:

1. **Layer A — Real RV32 + MMIO + Inline Tensix emission (single core):**
   - **Volatile / ordered MMIO + `FENCE`:** make sure MMIO loads/stores (`NOC_REGS`, `TENSIX_CFG`, `OVERLAY_STREAMS`, `PC_BUF`), `FENCE`, and inline Tensix pushes carry an explicit **effect token** (`AFTER` chain) so `linearize` never reorders or CSEs two identical volatile reads (like polling a status register in a `BACKEDGE` loop!) or moves a store past a `FENCE`.
   - **RV32 missing bits:** signed/unsigned `LB`/`LH`/`SB`/`SH`, `IF`/else lowering in `rv32.py`, proper signed-offset folding for the `+2048`-biased `gp`/`tp`/`t0` base registers, and the exact entry/exit convention (`boot.c` jumps to `_end`, kernel finishes by returning/parking).
   - **TRISC Tensix stream:** inline Tensix words (`tt_ins`), SFPU register-allocated ops (`sfp_ins`), `MOP` / `REPLAY` buffer programming for tight tile inner loops, and `fix_sfpu_hazards_uops`.

2. **Layer B — Hardware primitive builders (reusable UOp macros per core role):**
   - **Config writer:** declarative Tensix config words (from [hw/cfg.py](/Users/boop/code/tenstorrent/blackhole-py/hw/cfg.py)) lowered to `TENSIX_CFG` `SW`s (or `WRCFG`/`SETC16`), with a small pass that diffs/dedups redundant config writes.
   - **NoC DMA & Semaphores (BRISC / NCRISC):** `noc_read`, `noc_write`, `noc_mcast`, `noc_sem_inc`, `noc_wait_reads`, `noc_wait_writes` — expanding directly to `NOC_BASE` `SW`s + `FENCE` + `BACKEDGE` polling loops (mirroring [fw/noc.c](/Users/boop/code/tenstorrent/blackhole-py/fw/noc.c) / [fw/dma.c](/Users/boop/code/tenstorrent/blackhole-py/fw/dma.c), except emitted as UOps so they optimize & compose with loop indices).
   - **Circular Buffers (overlay streams):** `cb_reserve_back`, `cb_push_back`, `cb_wait_front`, `cb_pop_front` as UOp macros over `STREAM_REG(s, CB_PUSHED/CB_POPPED)` + `FENCE`.
   - **Tensix tile ops (TRISC0/1/2):** `unpack_tile` (TRISC0), `matmul_tile` / `elw_tile` / `sfpu_tile` (TRISC1), `pack_tile` (TRISC2) + `SEMINIT`/`SEMPOST`/`SEMWAIT` sync between unpack/math/pack.

3. **Layer C — 5-core kernel assembly & hardware test loop:**
   - Each kernel compiles to 5 per-core `Ops.PROGRAM`s (packed as the `BH01` bundle), loaded directly onto Blackhole via `device.py` without needing `riscv-gcc` at all.
   - Once Layers A & B work and pass on silicon (e.g. a pure UOp-compiled NoC DMA copy, a CB streaming SFPU op, and a single-core tiled FPU matmul), the "merge point" with the upper graph compiler becomes crystal clear: the upper compiler just needs to tile/shard a Layer 1 kernel into a sequence of **Layer B primitives** (NoC transfers, CBs, config state, FPU/SFPU tile loops).

Want to start by checking what's missing in Layer A (`rv32.py` + `tensix.py` + MMIO/fence ordering + `boot.c` ABI) and building a first end-to-end UOp-compiled RV32+NoC / Tensix program?

---

## Turn 9

### User

A lot of things are going to have an effect token in this code, we should actually just assume everything has an after token in a sense (which doesn't work well on a graph...) you have to wait for config writes to populate; fence, STaLLWAIT, etc... so this is not ideal for that. unless you just want a ton of afters? can you read some ttrv lowered risc-v in blackhole-py-archive and see what it actually looks?

### Gemini

Looked at the actual lowered RISC-V from [embedding.ttrv](/Users/boop/code/tenstorrent/blackhole-py-archive/examples/shared/embedding.ttrv) and [projection.ttrv](/Users/boop/code/tenstorrent/blackhole-py-archive/examples/nanbeige/projection.ttrv) (plus [DESIGN.md](/Users/boop/code/tenstorrent/blackhole-py-archive/compiler/DESIGN.md) and [ttrv/ops.py](/Users/boop/code/tenstorrent/blackhole-py-archive/ttrv/ops.py)), and it completely confirms your intuition.

### What real lowered Blackhole RISC-V actually looks like

1. **Long strictly-ordered MMIO / config / sync sequences** — almost every instruction mutates hidden hardware state:
   - `projection.ttrv` `trisc0` (`00b0`–`013c`): **30+ consecutive `RMWCIB0/1/2/3` and `SETC16`** inline Tensix config writes in strict order.
   - `projection.ttrv` `trisc1` (`00e4`–`01a0`): `REPLAY(load_mode=1)` followed by **8 repeated `MVMUL`s** (several literally identical words: `MVMUL addr_mode=3`), immediately followed by the `ManualTTSync` sequence (`sw x0, -2040(x4)` → `lw x2, -2040(x4)` → `andi x2, x2, 0` to stall `PC_BUF`), then **9 consecutive `sw`s to `MOP_CFG` (`0xffb80000`)**.
   - `embedding.ttrv` `brisc` (`0010`–`009c`): NoC cmd-buf `sw`s → `fence` → tight polling loops (`lw x15, 64(x4); bne x15, x0, -4` and `lw x15, -1468(x4); bgeu x15, 128, -8`).
   - `cb.push` / `cb.wait` ([ttrv/ops.py:76-114](/Users/boop/code/tenstorrent/blackhole-py-archive/ttrv/ops.py:76-114)): `lw cursor` → `sw cursor` → `fence` → `sw stream_reg` → `fence` (or `lhu` poll → `fence` → `lw cursor`).

2. **Two glaring inefficiencies in `ttrv`'s direct emitter** that a real compiler layer fixes automatically:
   - `projection.ttrv` `trisc2` (`0020`–`0098`) emits **30 instructions of dead/constant arithmetic** (`mul x6, x6, x0`, `addi 224; addi 1; sub`, `divu` by constant `112`) for `shared { ... }` grid math that `symbolic` would fold to 2–3 instructions.
   - `projection.ttrv` `trisc1` (`012c`–`01a0`) re-emits `lui x5, 0xffb80` **9 times in a row** right before each `MOP_CFG` `sw` because `ttrv` emits each statement independently with no register/value reuse across statements.

---

### The right boundary: SSA DAG *above*, `Ops.LINEAR` (`list[UOp]`) *below*

Trying to represent those 30 `RMWCIB`s, 8 identical `MVMUL`s, `ttsync`, `fence`, `STALLWAIT`, and NoC/CB polls in a hash-consed UOp DAG forces you to thread dummy `AFTER` tokens through every single instruction — you'd just be encoding a linked list inside a DAG (which [DESIGN.md:107-113](/Users/boop/code/tenstorrent/blackhole-py-archive/compiler/DESIGN.md:107-113) also ran into).

The clean tinygrad-compatible way to avoid `AFTER` spam is to make **`Ops.LINEAR` (`list[UOp]`) + `line_rewrite`** the explicit boundary where program order *is* the effect token:

| Layer | Representation | What lives here | Why |
|---|---|---|---|
| **Upper (SSA DAG)** | `UOp` DAG + `graph_rewrite` | Layer 0/1 tensor ops, `symbolic` / `div_and_mod`, rangeify, tile/grid math, SFPU expression DAGs | Pure values — hash-consing, constant folding, and `symbolic` crush address/grid math (`mul _, 0`, `divu 112`, `arange`, `Embedding`). |
| **Lower (Imperative linear)** | `list[UOp]` / `Ops.LINEAR` + `line_rewrite` | Config writes (`RMWCIB`, `SETC16`), `UNPACR`/`MVMUL`/`PACR`, `REPLAY`/`MOP`, `STALLWAIT`/`SEM*`, `ttsync`, `FENCE`, NoC/CB MMIO & poll loops, `LABEL`/branches | **List order = execution order** (no `AFTER` chains). Identical repeated ops (`MVMUL`, `SFPNOP`) stay distinct. |
| **Bottom (Machine code)** | `regalloc` + `line_rewrite` + `assemble` → `Ops.PROGRAM` | Virtual→physical RV32 (`x6..x29`) & SFPU (`L0..L7`) coloring, hoisting repeated constants (`lui 0xffb80`), `SFPNOP` hazard insertion, long-branch relaxation (`±4KB`), RV32IM + inline Tensix encoding | Already works on `list[UOp]` in [compiler/isa/__init__.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/__init__.py), and stays 100% tinygrad `Ops.LINEAR` / `Ops.PROGRAM` compatible. |

Notice how nice the handoff between the two is:
- Inside a linear hardware recipe (like `noc_read(dst_expr, src_expr, n_expr)` or a loop body), the **address/index expressions** (`dst_expr`, `src_expr`, `n_expr`) are still pure SSA `UOp`s simplified by `symbolic` and selected into virtual-reg `UOp.ins` ops;
- While the **side-effectful hardware steps** (`SW` to NoC regs, `FENCE`, `LW` poll + `BNE`, `RMWCIB`, `MVMUL`, `ttsync`, `STALLWAIT`) are simply appended in order to a `list[UOp]` (with structured `for`/`while`/`if` helpers emitting `LABEL` + branch `UOp.ins`, or keeping `RANGE`/`END` until pre-regalloc).

If you like this split, we can start designing the bottommost `list[UOp]` / `Ops.LINEAR` layer right on top of [compiler/isa/rv32.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/rv32.py) and [compiler/isa/tensix.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/tensix.py) — e.g. starting with a small single-core builder for RV32 + MMIO (`gp`/`tp`/`t0` base-offset folding) + `fence`/`ttsync` + inline Tensix + long-branch relaxation, and testing it by compiling something like `embedding.ttrv` directly to RV32 bytes and diffing/verifying the instruction stream.

---

## Turn 10

### User

ah yes. so before we linearize, we need to do the transformation from loads/stores to noc reads/writes, the math needs to pick a place to be executed, and then we need to generate unpacks and packs around that. basically noc writes prepend a PACK, and any time you move from L1 into FPU or SFPU you need to insert an unpack, etc. there are concrete rules for this. but i think first we mark spaces (what is the tinygrad equivalent to this?) we also need to build a virtual allocator for dst tiles so we can use that as an accumulator (for both SFPU and FPU operations). and within the SFPU we need the ability for the expression compiler to hold an accumulator in the sfpu as an lreg. 

something like this. the fpu/sfpu split is literally just rules based on Dtype, and operation; there are like 6 fpu instructions, we can scan for those, (we need to add 8x16 16x16 padding like AMD does for tensor cores!) and then that will work. fpu can do bf16, bfp8, fp8 (e4m3), bfp4 operations only--f32acc works as well. SFPU is for things where the source register starts in f32? or something has to be computed *in* f32. we need precision modeling for this, its not a like a gpu. you can lose a lot of precision unexpectedtly. but that's for later ig

### Gemini

Yes — that mental model is spot on, and it maps really cleanly onto tinygrad's abstractions.

### 1. Marking spaces (tinygrad equivalent: `AddrSpace`)

In tinygrad, memory spaces are `AddrSpace` ([tinygrad/dtype.py:52-55](/Users/boop/code/tenstorrent/tinygrad/tinygrad/dtype.py:52-55): `GLOBAL`, `LOCAL`, `REG`, `ALU`), carried on storage/staging nodes (`BUFFER`, `ALLOC`, `PARAM`, `STAGE`).

On Blackhole, the exact same idea with Blackhole's real spaces (`DRAM`, `L1`, `SRCA`, `SRCB`, `DST`, `LREG`, `GPR`) turns all the NoC / unpack / pack / SFPU load-store insertion into a **mechanical edge-transition table**:

```text
DRAM ──(noc.read / noc.write)──► L1 / CB
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼ (UNPACR A/B)             ▼ (UNPACR to_dest, fp32)   ▼ (PACR, reverse)
     SrcA / SrcB                    │                        L1 / CB
         │ (FPU: MVMUL/ELW*/POOL)   │                          ▲
         └────────────► Dst ◄───────┘──────────────────────────┘
                        ▲ │
        (MOVD2A/B)      │ │ (SFPLOAD / SFPSTORE)
                        │ ▼
                       LReg (L0..L7)
```

Once every op declares what space its inputs must be in and what space its output lands in, **inserting transfers is just one pass**: for every edge `(producer -> consumer)` where `producer.space != consumer.expected_space`, insert the transition op (`noc.read`, `UNPACR`, `SFPLOAD`, `MOVD2A`, `PACR`, `noc.write`).

---

### 2. FPU vs SFPU split + `8×16×16` padding (tinygrad equivalent: `_apply_tc_opt`)

Yes — this is directly analogous to tinygrad's tensor-core matcher in [postrange.py:163-228](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/opt/postrange.py:163-228) (`_apply_tc_opt`):
1. Match `REDUCE(ADD, MUL(a, b))` (with optional `CAST` to `fp32` accumulator).
2. Check input dtypes are in `{bf16, bfp8, e4m3, bfp4}` (and acc is `fp32` or `bf16`).
3. Identify the `M` (`a`-only), `N` (`b`-only), and `K` (reduced) ranges — for decode (`M=1`), `M` is implicitly `1` padded up to `8`.
4. **`PADTO` the tile atom** (`8×16×16` for 1 `MVMUL`, `16×16×16` face, or `32×32×32` tile): pads the `RANGE` bound to a multiple of the atom and gates the loads with `r < orig_bound` (exact same mechanism tinygrad uses for AMD `16×16×16` WMMA).
5. Replace the inner `K` reduce with the FPU tile op (`MVMUL`).

For the other FPU ops, it's just a tiny table on `(op, input_dtypes)`:
- **`bf16` / `bfp8` / `e4m3` / `bfp4` inputs** (where 19-bit SrcA/SrcB is lossless):
  - `REDUCE(ADD, MUL)` → `MVMUL` (`8×16×16`)
  - `ADD` / `SUB` / `MUL` → `ELWADD` / `ELWSUB` / `ELWMUL` (`8×16`)
  - `REDUCE(MAX)` → `GMPOOL` (`16×16 → 1×16`, SFPU finishes the last 16)
  - `REDUCE(ADD)` → `MVMUL` by `1.0` (or `GAPOOL`), SFPU finishes the last 16
- **SFPU (`LReg`)**:
  - Anything with **`fp32` inputs** (must unpack `L1 -> Dst` directly, skipping `SrcA`/`SrcB` so you don't silently lose 4 bits of mantissa to TF32 truncation)
  - Transcendentals (`exp2`, `log2`, `sin`, `sqrt`, `recip`, `rsqrt`), bitwise/int ops, conditionals/masks (`WHERE`, `CMPLT`, causal masks), and reduction tails.

---

### 3. Virtual `Dst` tile allocator + SFPU `LReg` accumulators

You can actually reuse the **exact same `regalloc` machinery** already in [compiler/isa/__init__.py:91-238](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/__init__.py:91-238) for **all three** register files — just with different `file` pools:
- **RV32 GPRs:** `file="gpr"`, pool `X[6..29]` (spill to `LOCAL_BASE`)
- **Tensix `Dst` tiles:** `file="dst"`, pool `DST[0..7]` in `fp32` acc mode (`DST[0..15]` in `bf16` mode), shared by both FPU ops and `SFPLOAD`/`SFPSTORE`, with spill/fill = `PACR`/`UNPACR` to L1 scratch!
- **SFPU `LReg`s:** `file="lreg"`, pool `L0..L7` (spill to a `Dst` row), where a loop-carried reduction accumulator stays pinned in an `LReg` across tile/face iterations and only `SFPSTORE`s to `Dst` once when the reduction finishes (which you already prototyped in commit `5511c45` in [compiler/sfpu.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/sfpu.py)).

---

### How the whole pass stack lines up

```text
Layer 1 Kernel AST (SINK — SSA DAG, what lower_tensor produces now)
  1. Tile / pad / match engines (SSA DAG):
       • PADTO 8x16 / 16x16 / 32x32 + shard across core grid (SPECIAL)
       • Classify ops -> FPU (MVMUL/ELW*/GMPOOL) vs SFPU vs GPR
  2. Mark spaces & insert transfers (SSA DAG):
       • Tag every buffer/value with Space (DRAM / L1 / SRCA / SRCB / DST / LREG)
       • Auto-insert noc.read/write, UNPACR, PACR, SFPLOAD/STORE, MOVD2A/B on space mismatches
  3. Allocate tile resources (still structured):
       • Virtual Dst allocator (DST[0..7]), CB / L1 layout, SFPU LReg allocator (incl. loop accumulators)
  4. Linearize & split into 5 cores (Ops.LINEAR — list order = effect order!):
       • Expand config writes (RMWCIB/SETC16), NoC/CB polls, FENCE, ttsync, STALLWAIT, SEM*, REPLAY/MOP
       • Run per-core RV32 regalloc + SFPNOP hazard insertion + branch relaxation -> Ops.PROGRAM
```

Notice how cleanly that separates concerns: steps 1–2 are pure graph rewrites with zero `AFTER` spam, step 3 is standard register/tile allocation, and step 4 is where all the stateful `fence`/`STALLWAIT`/`RMWCIB`/`ttsync` ordering lives naturally in `Ops.LINEAR`.

---

## Turn 11

### User

how will we represent fpu ops (i guess this is a uop?) and then what do we do for sfpu computations in the op graph before lowering? ALSO we need to have all the core's graphs togehter when we insert syncs, then linearize 5 times? how do we get the core split here? tag each uop or build a PM that looks at certain groupops and splits them into many sinks? that seems clumsy

### Gemini

This is where the architecture gets really clean if you pick the right boundaries. Here is how all three pieces fit together without any clumsy tagging or 5-way graph splitting.

---

### 1. Representing FPU ops vs. SFPU computations in the tile graph

Both use `Ops.CALL` (zero new core `Ops` in `compiler/uop.py`):

- **FPU ops (and transfers) → `UOp.ins` (`CALL(NATIVE(spec), *srcs)`):**
  Each tile-level engine op is one SSA node whose `NativeInfo.code` is a small frozen spec dataclass (e.g. `FpuOp(MVMUL, shape=(8,16,16), fidelity=2)`, `FpuOp(ELWADD)`, `FpuOp(GMPOOL)`, `UnpackOp`, `PackOp`, `NocRead`, `NocWrite`):
  ```python
  # pure SSA at the tile level: inputs are tile UOps, output is a tile UOp in Dst
  acc = UOp.ins(FpuOp(TensixOps.MVMUL, fidelity=2), (src_a, src_b, acc), dtypes.fp32, dst_vreg)
  ```
  Each spec inherently knows its **space contract** (inputs in `SrcA`/`SrcB`, output in `Dst`) and its **owner core** (`trisc1`).

- **SFPU computations → outlined `CALL(SINK(sfpu_expr), *dst_inputs)`:**
  Don't leave 40-node `exp2`/`recip`/`rsqrt`/`WHERE` expansions loose in the tile graph. Instead, outline each maximal SFPU subgraph into a `CALL(SINK(...), *dst_inputs)` (exact same `@function` mechanism `blackhole-py` already uses for `_block`!):
  - **To the outer tile graph (Dst alloc, sync insertion, 5-core split):** the entire SFPU block (whether `x + 1` or a full `silu`/`softmax`/`rsqrt`) is **one single opaque `trisc1` node** taking `Dst` tiles in and producing `Dst` tile(s) out.
  - **To `compiler/sfpu.py`:** the `body` is a completely pure SSA expression DAG with zero NoC/CB/FPU clutter, so `sfpu.py` compiles it in isolation (polynomials, `LReg` allocation + loop accumulators, `SFPNOP` hazards) and splices the resulting `sfp_ins` list into `trisc1`.
  - **Free deduplication:** identical SFPU expressions hash-cons to the same `SINK` body and compile once.

---

### 2. How to keep all 5 cores together for syncs, then split cleanly (NO 5-way DAG PM!)

Trying to split a **DAG** into 5 `SINK`s with a `PatternMatcher` *is* clumsy — don't do it. Instead:

**Linearize ONCE into 1 joint sequential stream → insert syncs on that 1 stream → filter/project into 5 per-core streams.**

Why this works so well:

1. **You don't need to "tag" UOps with roles.** Every hardware op *inherently* belongs to one core by its op type:
   - `NocRead` → `brisc`
   - `NocWrite` → `ncrisc`
   - `Unpack` → `trisc0`
   - `FpuOp`, `SfpuCall` → `trisc1`
   - `Pack` → `trisc2`
   - Pure RV32 scalar/address math (`col = first_col + j`, `tile_addr`) has **no role** — it stays attached as SSA operand UOps on the hardware ops that read it.

2. **Linearize ONCE** on the unified tile graph. Now all 5 cores sit together in **one single-threaded, obviously-correct sequential trace**:
   ```text
   for j in 0..count:
     for k in 0..KT:
       [brisc]  noc_read(cb_w, weights[col, k])
       [trisc0] unpack(SrcA, cb_w)
       [trisc1] fpu_mvmul(Dst[0], SrcA, SrcB)
     [trisc1] sfpu_call(silu_sink, Dst[0])
     [trisc2] pack(cb_out, Dst[0])
     [ncrisc] noc_write(out[col], cb_out)
   ```

3. **Insert syncs mechanically in ONE pass over that joint trace.** Because producer and consumer are in the same sequential stream, you just track which role last touched each resource (`CB`, `SrcA`/`SrcB`, `Dst[i]`):
   - `brisc → trisc0` on `cb_w`: emit `[brisc] cb.reserve` before `noc_read`, `[brisc] cb.push` after `noc_wait`; emit `[trisc0] cb.wait` before `unpack`, `[trisc0] cb.pop` after `unpack`.
   - `trisc0 → trisc1` on `SrcA`/`SrcB`: `UNPACR` sets `dvalid`, `FPU` clears `dvalid`.
   - `trisc1 → trisc2` on `Dst[0]`: emit `[trisc1] sem.wait(max)` / `sem.post`, `[trisc2] sem.wait(0)` / `sem.get`.
   - `trisc2 → ncrisc` on `cb_out`: emit `[trisc2] cb.reserve` / `cb.push`, `[ncrisc] cb.wait` / `cb.pop`.

   Every sync is emitted as a **matched producer/consumer pair** at the exact same loop depth — so mismatched loops or missing halves are structurally impossible.

4. **Split into 5 per-core `Ops.LINEAR` streams = a ~25-line projection** (you actually already have the prototype of this in [compiler/isa/tensix.py:226-257](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/tensix.py:226-257) `split_roles`!):
   - For each role `r ∈ (brisc, ncrisc, trisc0, trisc1, trisc2)`:
     - Keep only the hardware/sync ops owned by `r`.
     - Keep a `RANGE`/`END` loop iff its body contains at least one op for `r`.
     - Materialize **only** the pure RV32 index/address UOps referenced by `r`'s ops (so `brisc` compiles `weights[col, k]`, `ncrisc` compiles `out[col]`, and `trisc0/1/2` don't emit any DRAM address math at all!).
   - Then each core's `list[UOp]` runs through its own recipe expansion (`RMWCIB`/`SETC16`, `FENCE`, `ttsync`, `CB`/`NoC` polls, `sfpu.py`, `REPLAY`/`MOP`) → `RV32` `isel` + `regalloc` + `SFPNOP` hazards → `Ops.PROGRAM`.

### Putting the whole flow on one screen

```text
  [1 unified SSA DAG]   tile + pad + match FPU & outline SFPU CALL(SINK) + mark spaces + insert transfers + Dst/CB alloc
          │
          ▼  linearize ONCE
  [1 joint trace]       single sequential stream of role-inherent ops + loops
          │
          ▼  1-pass sync insertion (matched CB / dvalid / sem pairs)
  [1 synced trace]
          │
          ▼  project by op.role (keep only needed loops + each core's index math)
  [5 per-core Ops.LINEAR]  expand hw recipes (cfg, fence, ttsync, sfpu.py, NoC/CB) -> RV32 regalloc -> 5 binaries
```

Nothing gets linearised 5 times, no `AFTER` token spaghetti, no clumsy DAG splitting, and `sfpu.py` stays completely decoupled as a pure SSA expression compiler inside `CALL(SINK)`.

---

## Turn 12

### User

nice. what happens if you want to optimize sfpu instruction chains or tensix instructions into MOPs / replay buffers or SFPMACROs? when does that happen?

### Gemini

All three (`SFPLOADMACRO`, `REPLAY`, `MOP`) are **late, per-TRISC linear compression passes** that run **after** 5-core splitting, `L0..L7` SFPU regalloc, and concrete Tensix instruction selection — and **before** `RANGE`/`END` loops are lowered to RV32 branches and RV32 `regalloc`.

### Why right there?
- **Not earlier (not on the DAG):** all three need **concrete, register-allocated 32-bit Tensix words** (exact `LReg` numbers, `addr_mod`s, `dst` row parity, exact cycle delays) and need to see consecutive Tensix words with no RV32 ops mixed in.
- **Not later (not after RV32 branch lowering):** `MOP` needs to recognize **structured 1- or 2-level static-count loops** (`RANGE`/`END`) and collapse them before they turn into RV32 `addi`/`bge`/`jal` instructions, and all three hoist setup writes (`SFPCONFIG`, `REPLAY(load)`, `MOP_CFG` `sw`s) into the kernel prologue so RV32 `regalloc` can allocate/hoist their base addresses (`lui 0xffb80` once instead of 9 times).

---

### Strict order — each pass feeds the next

Running on each TRISC's `list[UOp]` (still having structured `RANGE`/`END` around concrete `tt_ins`/`sfp_ins` words):

1. **Pass 1 — `SFPLOADMACRO` (`trisc1` only, peephole):**
   - Anchors on `SFPLOAD r, dst[off]` and fuses up to 1 op per SFPU sub-unit (`simple`, `mad`, `round`, `store`) subject to hardware rules (`r` used once in `vb`/`vc`, `(dst_row & 1) == (r // 4)`, delays `0..7`, max 4 macro slots + 4 `SFPCONFIG` templates — see [ttrv/sfpmacro.py](/Users/boop/code/tenstorrent/blackhole-py-archive/ttrv/sfpmacro.py)).
   - Hoists `SFPCONFIG` template setup to prologue; replaces the multi-word chain with 1 `SFPLOADMACRO` word.

2. **Pass 2 — `REPLAY` (per-TRISC, 32-word budget per thread):**
   - Scans for contiguous runs of `2..32` constant Tensix words (now **including** `SFPLOADMACRO` words, no RV32 ops inside) executed `>= 2` times.
   - Ranks by `(execs - 1) * len`, packs into the 32-word replay buffer `[0..32)`, hoists `REPLAY(load_mode=1)` + body to prologue, and replaces every occurrence with 1 `REPLAY(load_mode=0)` word.

3. **Pass 3 — `MOP` Template 1 (per-TRISC, structural loop matcher):**
   - Matches 1- or 2-level static-count `RANGE`/`END` nests (`1..1023`) whose body has now shrunk to `<= 1` prologue word, `1–2` inner words (often `REPLAY(run)` + `INCRWC`), and `<= 2` epilogue words.
   - Hoists `ttsync` + `MOP_CFG` MMIO writes to prologue and replaces the entire loop nest with **1 `MOP` word**. Anything that doesn't fit stays a plain RV32 loop around `REPLAY` or raw Tensix words.

4. **Then finish lowering:**
   - `fix_sfpu_hazards_uops` (inside any uncompressed SFPU sequences and replay bodies, checking loop wraparound too)
   - Lower remaining `RANGE`/`END` → RV32 branches + RV32 `regalloc` + `assemble` → `Ops.PROGRAM`.

For example, in RMSNorm `apply_pair` ([DESIGN.md:262-266](/Users/boop/code/tenstorrent/blackhole-py-archive/compiler/DESIGN.md:262-266)), a `4 faces × (4 pairs × 11 words + 2 rwc)` loop compresses step by step: `SFPLOADMACRO` (`11 -> 9 words`) → `REPLAY` (`9 -> 1 word`) → `MOP` (whole 1024-element tile = **1 `MOP` word**).

The nicest architectural property: **all three passes are strictly optional.** You can bring up the entire compiler end-to-end with plain RV32 loops + inline Tensix words first, verify bit-exactness on silicon, and then turn on `SFPLOADMACRO → REPLAY → MOP` one pass at a time while checking identical output against the uncompressed baseline.

---

## Turn 13

### User

what have we not thought about? i think this is pretty well defined. obviously hardware semantics and random stuff will get us, but for overall device functionality and lowering, i think we're good

### Gemini

The core pipeline is really solid — the main things we haven't explicitly nailed down yet are the **7 practical seams** that will show up as soon as you go from toy ops to real Nanbeige/Qwen/Inkling kernels on silicon:

1. **Tile / block-float / DRAM-bank layouts**
   - Our Layer 1 IR is currently flat row-major, while Blackhole's `UNPACR`/`PACR`/`MVMUL` expect **32×32 face-packed tiles** (`4 × 16×16` faces), weights are often **`bfp8`/`bfp4`** (non-integer `itemsize`: 8.5 / 4.5 bits/elem, shared exponents), and fast DRAM reads need **8-bank striping / pitch padding** (`NT_PITCH`) so adjacent cores don't collide on one GDDR6 bank.
   - Clean fix: attach a `Layout` (row-major vs. face-tiled vs. bank-striped) to `BUFFER`/`ALLOC` so only the `DRAM↔L1` and `L1↔Src/Dst` transfer recipes care about it.

2. **Inter-core collectives & sync (beyond the 5 cores *inside* one tile)**
   - Our linear sync pass handles **intra-core** sync (`brisc ↔ trisc0 ↔ trisc1 ↔ trisc2 ↔ ncrisc` via CBs, `dvalid`, `math_pack` sem).
   - You'll also need **inter-core** primitives: NoC **multicast** (e.g. sharing `X` across a row or `W` down a column in prefill / RMSNorm→QKV), **Split-K / `PEERS` reduction** (RMSNorm over `7168`, `argmax` over `166912`, under-subscribed matmuls), and **global core-grid barriers** between stages. Treating collectives as first-class ops in the tile IR lets the same sync pass generate their NoC semaphore/ack pairs.

3. **Tail padding semantics (`0.0` vs `-inf`) & runtime args (`start_pos`)**
   - Real NoC doesn't zero-pad partial tiles or dynamic lengths (`start_pos + 1` in KV-cache attention). Tail lanes need explicit fill (`0.0` for `ADD`/matmul, `-inf` for `MAX`/softmax/argmax) via L1 zeroing or SFPU lane masks (`SFPSETCC`).
   - Runtime `Variable`s (`start_pos`, buffer addresses) need a fixed L1 arg-block convention (`L1_PARAM_BASE` read via `LW` off `LOCAL_BASE`) that the host patches before pulsing `GO_FLAG`.

4. **Per-core L1 memory allocator & double-buffering (`DEPTH=2`)**
   - Alongside `Dst`, `LReg`, and `GPR` allocators, each core needs a simple **L1 scratchpad allocator** (~1.5 MB minus fw/code/stack) that lays out CB ring buffers, hoisted loop-invariant buffers (like RMSNorm `gamma` or matmul `x`), and L1-resident activations.
   - Overlapping DRAM reads with compute needs `CB` ring `pages >= 2` (and double-buffered `Dst` halves `0..3` / `4..7` to overlap `trisc1` math with `trisc2` pack).

5. **Sticky Tensix hardware state (`TENSIX_CFG`, `ADDR_MOD`, `ZEROACC`, `RWC`, `dvalid`)**
   - Config registers and `Dst`/`Src` state are sticky across phases and across kernels. When a kernel switches engines/formats mid-stream (e.g. `MVMUL` → `SFPU` → `MVMUL`, or `bfp8` on `SrcA` + `bf16` on `SrcB`), a small stateful tracker during recipe expansion avoids both redundant `RMWCIB`/`SETC16` writes and stale-state bugs on kernel exit.

6. **Host vs. on-chip dispatch for decode**
   - Even with only 17 unique kernels for 52-layer Nanbeige (37 for 64-layer Qwen), host-side PCIe launch per kernel (~700 launches/token) will bottleneck decode. Keeping the unique kernel binaries resident in DRAM/L1 and running a compact device-side dispatch table (or persistent loop across layers) avoids PCIe launch overhead — and deduplicated `KernelArg("")` kernels already set you up for it.

7. **Pre-silicon verification (emulator / adversarial sync checker)**
   - A missing `fence`, `ttsync`, `STALLWAIT`, or mismatched CB/sem hangs the chip silently. Extending the RV32 emulator in [test/test_isa.py](/Users/boop/code/tenstorrent/blackhole-py/test/test_isa.py) (or a lightweight 5-core interleaving checker) to test lowered 5-core bundles before touching hardware will save huge debugging time.

None of these change the overall pipeline structure — they all plug cleanly into specific slots of the architecture we mapped out.

---

## Turn 14

### User

who handles sharding the workload over N cores and assigning cores? i just realized that's what's missing. right now we can ignore cross core communication and such and just make that a DRAM boundary.

### Gemini

With cross-core communication ignored (every cross-core dependency = a DRAM boundary between kernels), this splits cleanly into two pieces:

1. **Sharding the workload over `N` cores** → a **per-kernel grid-sharding pass** (tinygrad's `codegen/opt` equivalent), sitting **right after `rangeify` and before tiling/space-marking**.
2. **Assigning physical cores** → **SPMD via `Ops.SPECIAL` + `fw/boot.c` + `Device.run`** (most of the plumbing for this is already in your repo!).

---

### 1. Who shards the workload: the Per-Kernel Sharding Pass

Right now, `lower_tensor` ([rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py)) outputs hardware-agnostic Layer 1 kernels with plain `RANGE` loops. Immediately after that — at the very top of Step 1 in the pipeline above — you add a **sharding/tiling pass** that takes `(kernel_sink, num_workers)`:

```text
Layer 1 Kernel AST (plain RANGEs, hardware-agnostic)
  ├── 1a. Shard across N cores     <── turns outer parallel RANGE(s) into SPECIAL("worker_id", N) + local RANGE
  ├── 1b. Tile inner RANGEs        <── splits inner RANGEs into 32×32 / 8×16×16 + PADTO
  ├── 1c. Match FPU / outline SFPU
  ├── 2.  Mark spaces & insert transfers (DRAM <-> L1 <-> Src/Dst <-> LReg)
  └── 3–4. Alloc -> linearize once -> intra-core syncs -> split 5 cores -> RV32/Tensix
```

Concretely, what **1a (Shard across `N` cores)** does for one kernel:

1. **Find the parallelizable (non-reduced) axes** — the outer output `RANGE`s of the `STORE` (since we're ignoring cross-core comms, we don't shard `REDUCE` axes across cores yet).
2. **Split out the tile granularity first** (e.g. `32×32` tiles for FPU/SFPU, or 64B-aligned chunks for BRISC gather/copy), leaving `W` independent work units (tiles).
3. **Pick `N = min(W, num_workers)`** (e.g. `num_workers = len(device.workers)`: 119 on p100a, 139 on p150 — [device.py:198-204](/Users/boop/code/tenstorrent/blackhole-py/device.py:198-204)).
4. **Replace the outer `RANGE(W)` with `Ops.SPECIAL` + a per-core `RANGE`:**
   - You already have `UOp.special(end, name)` in [uop.py:736](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py:736), and `vmin`/`vmax`/`symbolic` already understand it.
   - Two ways to slice `W` tiles across `N` cores:
     - **Contiguous blocks** (`split_work_to_cores` style — better DRAM page locality):
       each core gets `start = core * q + min(core, r)` and runs `for local in range(q + (core < r))` (with `q, r = divmod(W, N)`).
     - **Cyclic / strided** (tinygrad `split_range` style — simpler index math for `symbolic` / `div_and_mod`):
       `tile_idx = core + local * N` for `local in range(ceil(W / N))`, gated by `tile_idx < W`.
5. **What about big reductions with tiny outputs** (like `RMSNorm` → `(1,)` or `argmax` → `(1,)`)?
   - **Simplest bring-up:** `W = 1` → `N = 1` (runs on core 0; fine for 14 KB RMSNorm).
   - **If you want parallelism without NoC comms:** split the reduction into **two kernels across a DRAM boundary** (tinygrad's two-stage reduce): Kernel 1 shards the reduce axis across `N` cores and writes `N` partial values to a tiny DRAM buffer; Kernel 2 reduces those `N` values on 1 core. Still zero cross-core NoC comms.

---

### 2. Who assigns cores: `boot.c` + `rv32.py` + `Device.run`

With DRAM boundaries between kernels, every kernel is **pure SPMD** — every core runs the exact same 5-core binary, differentiated only by its core ID. There is no complex core-assignment table needed at all, because your firmware and device layer already handle it:

1. **Firmware already numbers every core:**
   - [boot.c:108-112](/Users/boop/code/tenstorrent/blackhole-py/fw/boot.c:108-112) computes each worker's logical `(x, y)` and linear `worker_id = x * 10 + y` (`0 .. NUM_WORKERS - 1`) and stores them in L1 at fixed addresses ([hw.h:11-15](/Users/boop/code/tenstorrent/blackhole-py/fw/hw.h:11-15)):
     - `WORKER_X = 0x20`, `WORKER_Y = 0x24`, `WORKER_ID = 0x28`, `NUM_WORKERS = 0x2C`.
2. **Compiler lowers `Ops.SPECIAL` to one RV32 load:**
   - In [rv32.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/rv32.py), `SPECIAL("worker_id", N)` lowers directly to `LW rd, 0x28(x0)` (since L1 starts at address `0x0`).
   - If `N < NUM_WORKERS` (e.g. 32 attention heads on a 139-core chip, or a 1-core reduction), the kernel emits one guard at the top: `if worker_id >= N: return` (falls straight into `park.c`).
3. **Runtime / Scheduler launches one kernel at a time:**
   - [Device.run](/Users/boop/code/tenstorrent/blackhole-py/device.py:265-283) already broadcasts the 5-core image to all workers via `self.worker_rects` (fast multicast write, instead of per-core PCIe writes), or optionally to a subset via `cores=self.workers[:N]`.
   - Between kernel $k$ and kernel $k+1$ (where there's a DRAM dependency), the host/dispatcher waits for all cores to complete kernel $k$ before launching kernel $k+1$ — and kernel $k+1$ is free to pick a completely different `N` and sharding.

---

### Why this ages well when you *do* add cross-core comms later

Because sharding is isolated to Pass **1a** and talks to the rest of the compiler purely through `Ops.SPECIAL`:
- **Now (DRAM-only):** 1D `SPECIAL("worker_id", N)` + DRAM boundary between kernels.
- **Later (NoC multicast / Split-K / L1-sharded):** the same pass upgrades to 2D `SPECIAL("worker_x", cols)` / `SPECIAL("worker_y", rows)` (already in `0x20`/`0x24`!) and can choose a core sub-grid (`cores = rect`) + L1/NoC `STAGE`s instead of DRAM — without changing `rangeify`, `symbolic`, intra-core syncs, or RV32/Tensix codegen.

---

## Turn 15

### User

oh. we also need some kind of Config or StateTracker per core, so that we can figure out what config writes to emit (so we're not emitting every single config write again). like what's in each MOP, waht the unpacker contexts are set to, etc.

probably a few statetrackers per core and then a global one

*global one meaning per tile

### Gemini

Your split — **one per-tile tracker + per-RISC trackers** — maps 1-to-1 onto Blackhole's actual register architecture (and directly onto the `Space.CONFIG` vs `Space.THREAD` split in [hw/cfg.py:6-9](/Users/boop/code/tenstorrent/blackhole-py/hw/cfg.py:6-9)):

| Tracker | Scope | What it tracks | What it emits on diff |
|---|---|---|---|
| **`TileStateTracker`** | Shared across the Tensix tile (`trisc0/1/2`), per config bank (`0`/`1`) | `Space.CONFIG` (`TENSIX_CFG` words): unpacker descriptors & contexts (`THCON_SEC0/1`), math `ALU_FORMAT` / `fp32_dest_acc`, packer formats & strides (`PCK0`), `SEMINIT` max values | `RMWCIB` / `WRCFG` / `TENSIX_CFG` `SW` (plus `STALLWAIT` or bank-flip if another TRISC is still using the old config) |
| **`TriscStateTracker`** (×3) | Private to each TRISC (`trisc0`, `trisc1`, `trisc2`) | `Space.THREAD` (`ADDR_MOD[0..7]`, `PACK_ADDR_MOD[0..3]`, `dst_offset`, `unpack_ctx_offset`, `cfg_bank`, `sfpu_dst_fmt`), **`MOP_CFG` slot**, **`REPLAY[0..32)` buffer contents**, `RWC`/`ADC` counters, `ZEROACC` dirty flag; plus `SFPCONFIG` macro templates & `L11..L14` constants on `trisc1` | `SETC16`, `MOP_CFG` `SW` + `ttsync`, `REPLAY(load)`, `SETRWC`/`SETADC`, `SFPCONFIG` |
| **`NocStateTracker`** (×2) | Private to `brisc` (NoC0) and `ncrisc` (NoC1) | Per-`CMD_BUF` (`READ`/`WRITE`/`MCAST`/`ATOMIC`) sticky fields: `CTRL`, `TARG_COORD`/`RET_COORD`, `AT_LEN_BE`, `BRCST_EXCLUDE` (starting from the initial state [boot.c:39-51](/Users/boop/code/tenstorrent/blackhole-py/fw/boot.c:39-51) sets) | Only the NoC MMIO `SW`s whose fields actually changed |

Two design rules keep this clean and bug-free:
- **Every tracked slot is `int | UNKNOWN`** (initialized to the exact reset values from [boot.c:64-78](/Users/boop/code/tenstorrent/blackhole-py/fw/boot.c:64-78)). At any control-flow join (end of `if/else` or loop header), intersect states (`same -> keep`, `differ -> UNKNOWN`), so a diff never elides a needed write across a branch or loop backedge.
- Because [hw/cfg.py:12-21](/Users/boop/code/tenstorrent/blackhole-py/hw/cfg.py:12-21) already models every register as `Field(space, word, shift, width)` and `Set(field, value)`, a tracker's `apply(sets)` can batch multiple changed fields in the same word into a single `SETC16` / `RMWCIB` / `SW` automatically.

---

## Turn 16

### User

Implemented the Blackhole 3-tier fusion rules (`INLINE` / `L1` / `DRAM`) in `compiler/rangeify.py` and ported tinygrad's `TLSFAllocator` + DRAM/L1 lifetime memory planners to `compiler/memory.py`.

### Gemini

#### 1. What was added / changed
- **[compiler/uop.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/uop.py)** & **[compiler/ops.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/ops.py)**:
  - Added `space: str = "dram"` to `BufferArg` and `StageArg` (plus `inline: bool = True` on `StageArg`) and optional `addr`/`space` kwargs on `UOp.alloc` / `UOp.buffer`. Defaults omit cleanly from UIR; L1 buffers render as `alloc ... space=l1`.
  - Allowed `Ops.AFTER` on kernel-local L1 `ALLOC`s inside Layer 1 `verify()`.
- **[compiler/memory.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/memory.py)**:
  - Ported `TLSFAllocator` and `BumpAllocator` from tinygrad (`tinygrad/runtime/support/memory.py`).
  - Added `linearize_schedule` (topologically flattens kernel `CALL` graphs, optionally expanding `@function` calls with call-scoped local `ALLOC`s), `plan_dram_memory` (cross-kernel transient DRAM arena), `plan_l1_memory` (per-core intra-kernel L1 scratchpad arena), and `apply_memory_plan`.
- **[compiler/rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/rangeify.py)**:
  - **Tier 1 (`INLINE`):** Raised `MAX_INLINE_BUFFERS` from `3` → `16` (Blackhole has 32 CBs/core). Added `_mark_keep_staged` so nontrivial float prologues inside a `REDUCE` that are loop-invariant wrt an outer range (like `rmsnorm(x)` inside `lm_head`/`SwiGLU` or `exp2(scores - max)` inside `attn @ V`) are NOT inlined into the inner reduction loop (`inline=False`), while `bool` masks (`Embedding` one-hot) still inline and collapse to a single gather.
  - **Tier 2 (`L1`):**
    - *Partial-axis L1 staging* in `run_rangeify`: tracks `reduce_ranges` and `ended_ranges_map` so shared outer parallel `RANGE`s (like head axis `r_h`) stay open across reductions/multi-consumer splits when the closed slice fits `L1_STAGE_BUDGET` (`256 KB`). Pure `Elementwise` ops with all axes open propagate `cur_ended` down to the underlying `REDUCE` instead of creating bogus 0-D L1 buffers.
    - *Whole-tensor L1 prologue promotion* (`_promote_l1_stages`): bottom-up pass promoting small, cheap whole-tensor stages (`<= 64 KB` buffer, `<= 256 KB` underlying DRAM reads — e.g. `rms`, `xn`, Inkling `mix`, MoE router) to `space="l1"`, while blocking heavy weight-reading matmuls (`SwiGLU`, `Q/K/V`, `o_proj`, `lm_head`) from ever replicating across cores.
    - Inside `_split_store`, L1 `ALLOC`s and their `STORE`/`END`/`AFTER` stay inside the consuming kernel (no DRAM kernel split), flattened to 1D and canonically named `l0, l1, ...` for hash-cons deduplication.
  - **Tier 3 (`DRAM`):** Cross-core shuffles, persistent buffers (`KV cache`, `DeltaNet state`, `conv_state`), `@function` boundaries, and stages exceeding L1/read budgets split cleanly into DRAM kernels.
- **[test/test_rangeify.py](/Users/boop/code/tenstorrent/blackhole-py/test/test_rangeify.py)**: Extended `_eval_kernel` to execute kernel-local L1 `ALLOC` + `AFTER` (memoized by active open ranges) and added tests for L1-hoisted RMSNorm+matmul, single-kernel fused multi-head Attention, `TLSFAllocator`, and DRAM/L1 memory planning.

#### 2. Measured results across all 3 models (decode, `start_pos ∈ [1, 8191]`)

Every kernel across all 3 models passes `verify()` and round-trips identically via `parse_uir(render_uir(k)) is k`:

| Model | Mode | Unique Kernels | Total Launches | Transient DRAM (raw → TLSF arena) | Peak L1/core | Compile Time |
|---|---|---:|---:|---|---:|---:|
| **Nanbeige-52L** | baseline (`l1=0`) | 17 | 682 | 61.88 MB → 9.35 MB (577 allocs) | 0.0 KB | 0.31s |
| **Nanbeige-52L** | **Blackhole (`l1=256KB`)** | **11** (6/layer) | **317** (**2.15×↓**) | 13.26 MB → **8.48 MB** (~90 KB excl. RoPE) | **62.6 KB** (4.2% L1) | **0.24s** |
| **Qwen-64L** | baseline (`l1=0`) | 36 | 1110 | 194.52 MB → 7.76 MB (981 allocs) | 0.0 KB | 0.59s |
| **Qwen-64L** | **Blackhole (`l1=256KB`)** | **20** | **533** (**2.08×↓**) | 178.62 MB → **7.76 MB** (404 allocs) | **120.1 KB** (8.0% L1) | **0.40s** |
| **Inkling-24L** | baseline (`l1=0`) | 151 | 3160 | 21.80 MB → 0.93 MB (2871 allocs) | 0.0 KB | 8.08s |
| **Inkling-24L** | **Blackhole (`l1=256KB`)** | **143** | **1060** (**2.98×↓**) | 18.50 MB → **0.89 MB** (771 allocs) | **146.4 KB** (9.8% L1) | **7.03s** |

Also enforced a strict **non-hybrid kernel boundary** for codegen: a kernel is either a **Tensix kernel** (RV32 only does loop control, integer address math, NoC DMA, CB/sync, and pushing Tensix words — scalar broadcasts enter via `UNPACR`/`SFPLOAD`, never RV32 float math) or a **pure RV32/NoC kernel** (TRISCs held in reset via `ROLE_PC = 0` — e.g. `Embedding` gather, KV-cache row copy, or tiny scalar tails).

---

## Turn 17

### User

Tilization & FPU layout notes for lowering:

- **Drop `32×32` Z-order tiles completely.** Blackhole has no requirement for `32×32` Z-order (that was Wormhole legacy from having 4 separate packers). Blackhole's true native unit is a **`16×16` face** (and **`8×16`** along `M` for small-batch activations).
- **Minimum hardware granularity per unit:**
  - **FPU `MVMUL`:** `SrcB` = `8×16` (8-row aligned, higher fidelity), `SrcA` = `16×16` (16-row aligned), `Dst` = `8×16`. Hits **1.0 cyc/op** when rotating across `>= 6` distinct `8×16` `Dst` blocks (hiding 6-cycle `Dst` accumulate RAW latency, e.g. `8×96`, `8×128`, or `16×64`).
  - **FPU `ELW*` / `GAPOOL`:** `8×16` minimum; **SFPU:** `4×8` (32 lanes). Apply the same TC / `PADTO` tiling logic uniformly to **every** FPU op (`MVMUL`, `ELWMUL`, `ELWADD`, `ELWSUB`, `GAPOOL`/`GMPOOL`).
  - **Unpacker (`UNPACR`):** `8×16` (2.0 cyc BF16) or `16×16` (4.0 cyc BF16, 2.02 cyc FP8, 2.2 cyc BFP8/BFP4 with exact 16 B exponent alignment) — already hits 100% 128 B/cyc L1 bandwidth. Fill 2–4 faces (up to 64 rows) per `Src` bank before flipping `dvalid` to avoid the ~8 cyc face-level `dvalid` round-trip.
  - **Packer (`PACR`):** `4×16` (all 4 read interfaces = 64 datums/PACR); `8×16` = 2 `PACR`s, `16×16` = 4 `PACR`s at 100% packer width.
  - **DRAM / NoC:** store faces contiguously along the inner dim (`[M/16, N/16, 16, 16]` or `[1, K/16, 8, 16]` for `M <= 8` decode) so 4 consecutive `16×16` faces = 2 KiB BF16 / 1 KiB FP8 / 1088 B BFP8 in one DRAM read and one `UNPACR(n=1024)`.
- **Single uniform internal layout (`16×16` / `8×16` face-tiled):**
  - All weights ship pre-tilized in `[N/16, K/16, 16, 16]` (shared by decode and prefill; upper tinygrad graph doesn't know about this, lowering assumes it).
  - All internally produced activations stay face-tiled (`16×16` or `8×16`) across every kernel — avoids the ~2 cyc/UNPACR row-major address-counter penalty (critical for FP8/BFP8/BFP4 where compute outpaces unpacker) and avoids re-tilizing mid-graph.
  - Pure 4D block indexing (`reshape(M//16, 16, N//16, 16).swapaxes(1, 2)`) instead of 6D Z-face math; `W^T`/`K^T` is just outer swap + `Haloize_mode=1` on Unpacker A (0 extra cycles).
  - **Free hardware pack-untilize on output:** `PACR(DstAccessMode=1, ReadIntfSel=0b1111)` reads 4 horizontal `16×16` (`Stride=16`, `remap_addrs=1`) or `8×16` (`Stride=8`, `remap_addrs=0`) blocks as **64 contiguous row-major elements in one `PACR`** at 100% full packer speed.

### Gemini

That `16×16` / `8×16` face-tiled architecture is a huge simplification over `32×32` Z-order:

1. **Device-vs-host boundary rule (solving the "read back to device" question cleanly):**
   - **Every device-resident buffer** (weights, KV caches, recurrent state, intermediate activations, and any `Tensor.realize()` output that might be fed into a subsequent graph) stays **`16×16` (or `8×16`) face-tiled** in DRAM. That guarantees a device buffer is **never** unpacked row-major or re-tilized mid-graph.
   - **Hardware `PACR(DstAccessMode=1)` row-major untilize** is used strictly on **host-readback outputs** (buffers marked `host_out` / final unconsumed output when the caller only reads back to CPU — and for LLM decode, the only host readback per token is `argmax`'s 4-byte `i32 (1,)` scalar anyway!).
   - If the user ever calls `.numpy()` on an arbitrary already-realized device buffer (for debugging or inspecting an intermediate), `Buffer.numpy()` can simply run the 1-line NumPy untile (`swapaxes(1, 2).reshape(M, N)`) on the host copy after `copyout` — leaving the on-device buffer face-tiled with zero re-tilize cost if another kernel later reads it.
2. **Uniform FPU `PADTO` rule:**
   - Every FPU op (`MVMUL`, `ELWADD`, `ELWSUB`, `ELWMUL`, `GAPOOL`/`GMPOOL`) goes through the exact same tile-padding pass (`M` padded to `8` for `M <= 8` decode else `16`; `N` and `K` padded to `16`, rotating across `>= 6` `8×16` `Dst` blocks for `MVMUL` to hide 6-cycle RAW latency, and placing the higher-precision / activation operand in `SrcB`).

---

## Turn 18

### User

Policy decision: all weights pre-tilized in safetensors, all internal device activations stay `16×16` / `8×16` face-tiled, and row-major only appears at the host boundary (courtesy of `PACR(DstAccessMode=1)` on output). SFPU stays completely clean because SFPU only touches `Dst` (`N_rows × 16` cols) and `SFPLOAD`/`SFPSTORE`'s `4×8` alternating-column pattern is its own inverse (elementwise loops `Addr += 2` transparently, RoPE gets `(2i, 2i+1)` in matching lanes for free, row reductions fold 16→8 in one `SFPADD`). What about host-uploaded tensors?

### Gemini

- **Never do tilization as `reshape`/`permute`/`.contiguous()` in tinygrad** — keep tinygrad 100% layout-blind and handle host-uploaded tensors strictly inside `copyin` (`Buffer.copy_from` in [device.py:183-190](/Users/boop/code/tenstorrent/blackhole-py/device.py:183-190)):
  1. **Default — CPU tilize during DMA staging:** overlap the `16×16` (or `8×16` for `M <= 8`) pad + block-copy right into `device.py`'s existing 4-thread DMA staging copy (~30–60 GB/s, hiding behind PCIe bandwidth with zero extra kernel launch). Pre-tilized safetensors skip this and use zero-copy `_direct()`.
  2. **Optional — one-time device tilize kernel:** for huge (>16 MB) un-tilized host tensors, `_direct()` DMA raw bytes to scratch DRAM then run a tiny 1-kernel device tilizer (`brisc` strided row reads → `PACR` face-tiled).
- **Reshape invariance note:** pure `16×16` face-tiling survives almost all real LLM reshapes as a free no-op (`D -> (H, head_dim)` whenever `head_dim % 16 == 0`, merging/splitting `(B, S)`). Only a cross-kernel reshape that cuts across a `16`-column boundary or flattens `M > 1` with `N` requires an explicit untilize/re-tilize boundary.

---

## Turn 19

### User

Silicon probe results on both cards (`probes/tf32/` in `blackhole-py-archive`), settling **Q2** (row reductions + broadcast) and **Q3** (precision & `Dst` mode):

- **P0 (TF32 Src strides — critical hardware quirk):** A TF32 value takes **4 bytes** in `SrcA`/`SrcB`, not 2. Unpacker Src `row_stride` must be **64** and `face_stride` **1024** (2-byte strides scramble faces with TF32).
- **P1 (fp32 → Src always truncates, never rounds):** `fp32 → TF32` matches `x & ~0x1FFF` bit-for-bit; `fp32 → bf16` matches `x & ~0xFFFF` bit-for-bit. `SrcA` drops the lowest TF32 mantissa bit when multiplying; `SrcB` keeps all 10 mantissa bits.
- **P2 (mixed `bf16` SrcA × `TF32` SrcB works):** Even though FPU takes its mode from `SrcA`, `SrcB` still preserves all 10 TF32 mantissa bits.
- **P3 (K=2048 accuracy, `−log₂(max_err / Σ|w·x|)`, higher = better):**
  - `SrcA=W bf16, SrcB=x TF32`: **14.4 bits** at **3 phases `{0,1,2}`** and **14.4 bits** at 4 phases (datapath limit 15.1 bits).
  - `SrcA=W bf16, SrcB=x bf16`: 11.6 bits at 3 phases / 11.7 bits at 4 phases.
  - `SrcA=x TF32, SrcB=W bf16` (swapped): 13.5 bits (loses ~1 bit to SrcA's dropped mantissa bit).
  - **Takeaways:** **3 phases `{0,1,2}` are enough** (25% faster than 4 phases); activation always goes in `SrcB` as TF32, weight in `SrcA` as `bf16`; hi+lo splitting only gains ~0.7 bits for 2× cost (not worth it).
- **P4 (`fp32 + fp32` via `ELWADD`):** loses ~13 mantissa bits (worst error `2^-10.2` of `|x|+|y|`).
- **Locked policies:**
  - **Q3a:** **`fp32_dest_acc = 1` globally, always, zero mode switching** (matches all 38 TTRV kernels; avoids unpredictable 16-bit LSB after 32-bit Dst op). 16-bit values only ever live in L1 and `SrcA`/`SrcB`.
  - **Q3b:** `fp32 @ bf16` `MVMUL` → `SrcA=bf16`, `SrcB=TF32` (with 4-byte Src strides `row=64, face=1024`), `fp32 Dst`, **3 fidelity phases `{0,1,2}`**. *(Corollary: for Qwen/Inkling `fp32 × fp32` matmuls like `Q @ K^T` / `attn @ V` / DeltaNet `f32mm`, both `SrcA` and `SrcB` unpack as TF32 and need 4-byte Src strides.)*
  - **Q3c:** Any `fp32` elementwise, norm, or recurrent state → unpack straight to `Dst` (`UNPACR to_dest`) and run on **SFPU**. FPU `ELW*` only when both operands are `<= bf16`.
  - **Q2:** Never fold 16→1 on FPU. After `MVMUL` (`tensix.stall sync, math|sfpu`), reduce rows on **SFPU** with `reduce_lanes` (`SFPSHFT2` + `SFPTRANSP`). Broadcast is **free** because `reduce_lanes` leaves the reduced scalar in all 32 SFPU lanes.

---

## Turn 20

### User

Let's lock down **Q4** (multi-phase L1 sync & L1 layout) and **Q5** (`Dst` sub-block allocator & `MVMUL` unrolling) based on the TTRV kernels in `blackhole-py-archive`, and **Q6** (GPU-like flat DRAM addressing hiding bank interleaving & page sizes from tinygrad and kernel codegen).

### Gemini

#### Q4 — Multi-phase L1-staged kernel sync & L1 layout (from `attention.ttrv`, `gdn_state.ttrv`, `projection.ttrv`, `ttrv/layout.py`)

1. **One universal intra-core sync mechanism: Overlay-stream CBs (`CB_STREAM0..31`) — for streaming rings, static multi-phase L1 buffers, AND phase barriers:**
   - Every kernel-local `ALLOC(..., space="l1")` from 3-tier fusion (`l0`, `l1`, ...) is lowered as a **`pages=1` CB** (1 of the 32 overlay streams):
     - Producer (`trisc2` `PACR` or `brisc` `noc.read`) wraps its `STORE`/`END` in `cb.reserve` / `cb.push`.
     - Consumer (`trisc0` `UNPACR`) calls `cb.wait` **once** before its reusing loop (e.g. `query` in `attention.ttrv:273`, `activations` in `projection.ttrv:152`) and `cb.pop` **once** after its last read.
     - Pure phase barriers (e.g. `UNPACR to_dest` → SFPU → `PACR` in `gdn_state.ttrv:29-31`) also use 0-byte/1-page overlay CBs (`loaded`, `updated`, `packed`).
   - Streaming DRAM inputs/outputs use `pages = DEPTH * BATCH` (`DEPTH = 2` double-buffered ring).
   - `trisc0 → trisc1` on `SrcA`/`SrcB` uses hardware `dvalid`; `trisc1 ↔ trisc2` on `Dst` uses `sem math_pack` (`max=1` or `max=2`).
2. **L1 layout (`[code_end .. 1.5 MB]`, 64B-aligned):**
   - Static L1 stage buffers (`l0..lk`) are lifetime-packed via `plan_l1_memory` ([compiler/memory.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/memory.py)) so non-overlapping phases share the same L1 arena.
   - Streaming double-buffered CB rings take the remaining L1 headroom (`BATCH` sized to fit).

#### Q5 — `Dst` sub-block allocator (`8×16` slots) & `MVMUL` unrolling

1. **Allocator granularity = 1 `8×16` block (8 `Dst` rows):**
   - With `fp32_dest_acc = 1` locked in globally, `Dst` has **512 rows × 16 cols** (`64` slots of `8×16`, or `32` `16×16` faces).
   - **Default (double-buffered, `sem math_pack, max=2`):** split into two 256-row halves (`32` `8×16` slots per half), toggling `dst_offset = (iter & 1) * 256` on `trisc1` and `trisc2` whenever a kernel needs `<= 32` simultaneously live `8×16` slots.
   - **Multi-accumulator fallback (`sem math_pack, max=1`):** kernels like `Attention` or `DeltaNet` needing `> 32` live `8×16` slots use all `64` slots (`0..511`, single-buffered, matching `attention.ttrv` / `gdn_state.ttrv`).
2. **`MVMUL` register blocking (1.0 cyc/op, hiding 6-cycle `Dst` accumulate RAW latency):**
   - **Decode (`M <= 8`):** unroll **`N_BLK = 8`** horizontal `8×16` output blocks (`8×128` = 64 `Dst` rows; or `6` blocks = `8×96` when `N_faces % 8 != 0`). Fill `SrcB` with `4 × (8×16)` = `8×64` and `SrcA` with `4 × (16×16)` (1 `dvalid` per bank), rotating `MVMUL` across all `8` `Dst` blocks across `3` fidelity phases (`1` for `bfp4`, `2` for `bfp8`, `3` for `bf16`/`TF32`).
   - **Prefill (`M > 8`):** unroll **`2 × 4` = 8 `8×16` blocks** (`16×64` = 4 `16×16` faces = 64 `Dst` rows), rotating across all 8 distinct `Dst` blocks. Both strips align cleanly with 4-interface `PACR(DstAccessMode=1, ReadIntfSel=0b1111)`.

#### Q6 — GPU-like flat virtual DRAM addressing, resident `noc_move`, & completion/dispatch (`fw/`)

1. **Flat virtual 64-bit DRAM pointer (already built in [device.py:16-20](/Users/boop/code/tenstorrent/blackhole-py/device.py:16-20) + [fw/noc.c:34-88](/Users/boop/code/tenstorrent/blackhole-py/fw/noc.c:34-88)):**
   - Every DRAM buffer is a single 64-bit virtual address: `(1 << 63) | page_tag | flat_byte_offset`.
   - **Default stripe size = `4096 B` (`shift = 12`, zero runtime division!)** for all normal buffers (including the single TLSF transient DRAM arena from `plan_dram_memory`, where sub-allocations only need 64B alignment in flat space!).
   - Small tensors (`size < 4096 B`) naturally issue 1 NoC transfer of `size` bytes; large transfers (`size > 4096 B`) automatically split at stripe boundaries and rotate `bank = (bank + 1) % BANKS` (`7` on p100a, `8` on p150) and `port = (port + 1) % 3` — even for `bfp8` (`1088 B`) or `bfp4` (`576 B`) blocks straddling a 4 KB boundary. (Hot weight tensors can still opt into an exact page tag like `page=1088` via `dram(offset, page=1088)` with zero kernel codegen changes!)
   - Because weights are stored **`[N/16, K/16, 16, 16]`** (PyTorch `[out, in]` order), each core reading `K = 0..K_max` for its assigned output columns reads a **single contiguous byte stream** — automatically striping across all 7/8 banks and all 3 ports at 100% bandwidth with **zero `NT_PITCH` padding**!
2. **Resident `noc_move` in `fw/boot.c` (zero bank/page logic in tinygrad or kernel codegen):**
   - Link `fw/noc.c` (~350 B, compiled for `BANKS = 7 or 8`) into the `brisc`/`ncrisc` boot stub and export fixed entry points (`FN_NOC_READ`, `FN_NOC_WRITE`, `FN_NOC_WAIT`) in the L1 header (`0x70..0x7F`).
   - Kernel codegen only computes a flat byte offset `off` and emits `jal FN_NOC_READ(buf_lo, buf_hi, off, nbytes, l1_dst, tid)`. The ~20-cycle call overhead is completely hidden behind 500–2,000-cycle GDDR6 latency + `DEPTH=2` CB overlap.
3. **Runtime ABI, `fw/park.c` done barrier, & resident dispatch:**
   - **L1 Arg Block (`0x80..0xFF`, 16 × 8B slots):** holds `u64` flat DRAM buffer pointers + `u32` runtime `Variable`s (`start_pos`, low word of 8B slot).
   - **Completion barrier (`fw/park.c`):** subordinates (`ncrisc`, `trisc0..2`) drain `COPROCESSOR_DONE_CHECK` + `fence` and write done to `SUBORDINATE_SYNC`; `brisc` waits on subordinates + NoC, atomically increments `LEADER_COORD` (`0x1C`); leader waits for `NUM_WORKERS`, resets counter, and writes sequence number to `HOST_SIGNAL_ADDR` over PCIe (host waits via `Signal.wait`).
   - **Resident wait-loop:** instead of spinning forever (`1: j 1b`), `brisc` loops back to wait for the next `GO_FLAG` epoch + launch descriptor so 317 decode kernels run without resetting cores.

---

## Turn 21

### User

Locked in the final three design questions: **Q1** (pre-flattening N-D handoff), **Q5/Q7** (unified FPU+SFPU lowering, `sfpu.py` refactor contract, and non-spilling `Dst` slot assignment), and **Q8** (`M_TILE = 8` everywhere for activations + `PADTO`/`WHERE` tail & causal masking).

### Gemini

#### Q1 — Pre-flattening handoff (zero Blackhole leakage into tinygrad or `rangeify`)
- `rangeify.py` stays 100% Blackhole-independent and matches upstream tinygrad ([tinygrad/codegen/rangeify.py:260-262, 302](/Users/boop/code/tenstorrent/tinygrad/tinygrad/codegen/rangeify.py:260-262)): `_split_store` leaves kernel `PARAM`s as `UOp.param(slot, dtype, (numel,)).reshape(max_shape)` with multi-axis `INDEX(param.reshape(N, K), r_col, r_k)`. *(Keep a `flatten_1d=True` mode only for the generic Python test interpreter.)*
- Inside the **Blackhole backend** (strictly below `rangeify`):
  1. **Pass 1 (sharding + tiling + uniform FPU `PADTO` + engine matching)** splits the last two logical axes by `(8, 16)` (activations) or `(16, 16)` (weights).
  2. **Pass 2 (transfer/NoC lowering)** converts outer face indices `(f_r, f_c)` directly into flat DRAM byte offsets `(f_r * (N_pad // 16) + f_c) * face_bytes` for `FN_NOC_READ`/`FN_NOC_WRITE`.

#### Q5 / Q7 — Joint FPU + SFPU lowering, `compiler/sfpu.py` contract, & non-spilling `Dst` slot assigner
- **Unified FPU + SFPU tile-math pass:** lower FPU (`MVMUL`, `ELW*`) and SFPU together in one pass so FPU → SFPU chains (`MVMUL` → `tensix.stall sync, math|sfpu` → `silu`/`tanh`/`reduce_lanes`/`mask_tail`) execute in place on the exact same `fp32` `Dst` blocks with a single `PACR` at the end. (SFPU → FPU chains like `P → P @ V` transition through a `pages=1` L1 CB per Q4.)
- **No `Dst` spilling:** replace virtual-reg spilling on `Dst` with a **hard-budget lifetime slot assigner** (`8×16` = 8-row slots):
  1. Try `32` slots per half (`sem math_pack, max=2`, double-buffered).
  2. If peak live slots `> 32`, trim `MVMUL` `N_BLK` (`8 → 6`) or drop to `64` slots (`max=1`, single-buffered).
  3. If it still doesn't fit, **never spill `Dst`** — demote an intermediate to a `pages=1` L1 CB or split into a separate kernel.
  *(Only `L0..L7` SFPU regs — which can borrow 1 spare `Dst` row — and RV32 GPRs `x6..x29` ever spill.)*
- **`compiler/sfpu.py` refactor contract:**
  - **Input:** outlined pure SSA `CALL(SINK(expr_body), *dst_slots)` with concrete `Dst` row bases (`8×16` blocks).
  - **Stages:** (1) port existing minimax decompositions (`exp2`, `log2`, `sin`, `recip`, `rsqrt`, `sqrt`, `bits=23` fp32 / `11` bf16) onto dtype-free `UOp` + `sfp_ins`, (2) select `sfp_ins` + color `L0..L7` via the shared `regalloc` in [compiler/isa/__init__.py](/Users/boop/code/tenstorrent/blackhole-py/compiler/isa/__init__.py) (pinning loop accumulators in `LReg`), (3) wrap in `INCRWC dst+2` (`4` steps per `8×16` block) + `reduce_lanes` (`SFPSHFT2` + `SFPTRANSP`).
  - **Output:** `list[UOp]` of `sfp_ins` spliced into `trisc1`'s `Ops.LINEAR` stream (before `SFPLOADMACRO → REPLAY → MOP → fix_sfpu_hazards_uops`).

#### Q8 — Always `8×16` activations + `PADTO`/`WHERE` → `SFPSETCC` masking
- **Single activation tile height everywhere (`M_TILE = 8`):**
  - **All activations (decode, prefill, residuals, intermediate buffers):** always **`[M/8, N/16, 8, 16]`** (`0%` loss on prefill `x @ W` weight reuse — `trisc0` simply unpacks 2 or 4 `8×16` blocks into `SrcB` against the same `16×16` weight face in `SrcA`; `100%` `UNPACR`/`PACR`/pack-untilize bandwidth; less padding waste than `16×16`).
  - **All weights:** always **`[N/16, K/16, 16, 16]`** (exact 16 B BFP8/BFP4 exponent alignment + contiguous K-reads).
  - **For `act @ act` matmuls where an activation enters `SrcA` (`16` rows):** non-transposed (`P @ V`, `f32mm(t, vb)`) unpacks two `8×16` strips sequentially into `SrcA` rows `0..7` and `8..15` at 100% speed; transposed (`Q @ K^T`, `kb @ k^T`) pairs `block[2t, d]` and `block[2t+1, d]` into adjacent L1 slots (`l1 + 0`, `l1 + 256`) to form a contiguous `16×16` face for `UNPACR(Haloize_mode=1)`.
- **Dynamic loops & masking:**
  - Dynamic KV-cache length `T = start_pos + 1` keeps `RANGE(ceil(T / 16))` as a plain RV32 `BGE` loop (late `MOP` pass only collapses static-count loops).
  - `PADTO` emits `WHERE(face * 16 + lane < T, val, identity)` (`-inf` for `MAX`, `0.0` for `ADD`); `symbolic` eliminates it completely when `N % 16 == 0`, and `sfpu.py` lowers any surviving tail or prefill causal `WHERE(col <= row, score, -inf)` mechanically to `SFPSETCC` on the tail/diagonal face only.

All 8 design questions (Q1–Q8) are now locked in — the full end-to-end compiler blueprint from `Tensor` to Blackhole silicon is complete.
