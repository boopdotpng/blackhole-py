"""Hybrid 2048-element BF16 RMSNorm, adapted from examples/rmsnorm_hybrid.py.

PYTHONPATH=. python3 ttk/sketches/rmsnorm_hybrid.py --stage graph
PYTHONPATH=. python3 ttk/sketches/rmsnorm_hybrid.py --stage linear
PYTHONPATH=. python3 ttk/sketches/rmsnorm_hybrid.py --stage render --per-thread

SrcA is read twice: MOVE preserves x in scratch, then FPU_ELW computes x*weight.
Plain SFPU loads/MULACC replace the square macros; loads/MUL/STORE replace the
normalization macro. Scratch occupies one tile; products occupy two more.

Current gaps exposed by this port:
- fidelity=4 records intent; the fake renderer does not expand HiFi4 phases.
- scale stays live across normalization but has no physical LREG pin constraint.
- PACK does not yet express the original kernel's explicit gasket configuration.
This is a protocol sketch, not an executable or cycle-equivalent hardware port.
"""
import argparse

from ttk.model import Buffer, Dtype, trace, loop, dst, l1, noc, unpack, pack, sfpu, cb, fpu
from ttk.linearize import linearize
from ttk.render import FakeRenderer
from ttk.sketches.rmsnorm import N, BLOCKS, EPS, graph_text, linear_text

TILES = N // 1024
TILE_BLOCKS = 8


def rmsnorm_hybrid(activations: Buffer, weight: Buffer, output: Buffer):
  inputs, weights = cb.read(activations), cb.read(weight)
  a_ring = cb.alloc(kind='SRCA', dtype=Dtype.bf16)
  b_ring = cb.alloc(kind='SRCB', dtype=Dtype.bf16)
  scratch = dst.alloc(TILE_BLOCKS, dtype=Dtype.f32)
  products = dst.alloc(BLOCKS, dtype=Dtype.f32)

  def tile(i, acc):
    # One iteration does everything for tile i. Producer reads, bank fills,
    # FPU work and SFPU accumulation sit on different queues; the rings'
    # depth is what lets lowering overlap iterations.
    x_item, w_item = inputs.next(), weights.next()
    a, b = a_ring.acquire(), b_ring.acquire()
    unpack(x_item, into=a)
    unpack(w_item, into=b)
    fpu.move(a, into=scratch)
    fpu.op('mul', a, b, into=products.blocks(offset=i * TILE_BLOCKS, count=TILE_BLOCKS), fidelity=4)
    # Both operations read the same SrcA occupancy; reuse waits for both reads.

    def sum_squares(block, total):
      for lanes in sfpu.lanes(scratch[block]):
        value = sfpu.load(lanes)
        total = sfpu.mad(value, value, total)
      return total

    return loop(TILE_BLOCKS, sum_squares, carry=acc, name='squares')

  acc = loop(TILES, tile, carry=sfpu.const(0.0), name='tiles')
  scale = sfpu.rsqrt(sfpu.lane_sum(acc) * (1.0 / N) + EPS)

  def normalize(block):
    for lanes in sfpu.lanes(products[block]):
      sfpu.store(sfpu.load(lanes) * scale, lanes)

  loop(BLOCKS, normalize, name='normalize')
  result = l1.alloc(N * 2, dtype=Dtype.bf16)
  pack(products, into=result)
  noc.write(result, output)


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--stage', choices=('graph', 'linear', 'render'), default='graph')
  parser.add_argument('--per-thread', action='store_true', help='project rendered output per thread')
  args = parser.parse_args()
  if args.per_thread and args.stage != 'render': parser.error('--per-thread requires --stage render')
  buffers = tuple(Buffer(name, Dtype.bf16, N * 2) for name in ('activations', 'weight', 'output'))
  program = trace(rmsnorm_hybrid, *buffers)
  program.verify()
  if args.stage == 'graph': print(graph_text(program.sink))
  else:
    nodes = linearize(program.sink)
    if args.stage == 'linear': print(linear_text(nodes))
    else: print(FakeRenderer().render(nodes, per_thread=args.per_thread), end='')


if __name__ == '__main__': main()
