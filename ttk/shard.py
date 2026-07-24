"""Helpers for programs whose work is split into per-core item shards.

A sharded buffer gives every core a contiguous range of items (tokens, rows,
...) described by `item_starts` and `item_counts`.  At runtime only the first
`valid` items are live, so each core has to clamp its own range; at build time
the cores hold different item counts, so each distinct count needs its own
loop bound.
"""


def local_range(kernel, program, valid, start_const, capacity, count, start):
  """start = this core's first item; count = clamp(valid - start, 0, capacity).

  `valid` and `start_const` are Program constants: `valid` is the runtime item
  count shared by every core, `start_const` is this core's shard offset.
  """
  kernel.read(start, program.param_addr(start_const))
  with kernel.scope():
    live, limit = kernel.reg(2, exclude=(count, start))
    kernel.read(live, program.param_addr(valid))
    kernel.li(limit, capacity)
    kernel.li(count, 0)
    done = kernel._new_label("local_range_done")
    kernel.bgeu(start, live, done)          # shard starts past the live items
    kernel.sub(count, live, start)
    kernel.bltu(count, limit, done)
    kernel.mv(count, limit)                 # shard is full
    kernel.label(done)
  return kernel


def specialize(build, cores, counts):
  """Build one program per distinct item count, then launch them together.

  `build(count)` returns a Program written for a core holding `count` items.
  The lowered kernels are recombined into a single heterogeneous launch that
  gives every core in `cores` the variant matching its own count.
  """
  variants = {count: build(count) for count in sorted(set(counts))}
  lowered = {count: program.lower() for count, program in variants.items()}
  combined = variants[max(variants)]
  combined._kernels = {
    core: dict(lowered[count][core]) for core, count in zip(cores, counts)
  }
  return combined
