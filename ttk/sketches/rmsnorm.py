"""RMSNorm of 2048 BF16 activations with 2048 BF16 weights, both in DRAM.

PYTHONPATH=. python3 ttk/sketches/rmsnorm.py --stage graph
PYTHONPATH=. python3 ttk/sketches/rmsnorm.py --stage linear
PYTHONPATH=. python3 ttk/sketches/rmsnorm.py --stage render [--per-thread]

The graph view prints the exact nested UOp expression, with references for
shared nodes. Linear/render views share global % IDs.
"""
import argparse

from ttk.model import Buffer, Dtype, trace, loop, dst, l1, noc, unpack, pack, sfpu, cb
from ttk.linearize import linearize
from ttk.render import FakeRenderer

N = 2048
BLOCKS = N // 128
EPS = 1e-5


def rmsnorm(activations: Buffer, weight: Buffer, output: Buffer):
  inputs = cb.read(activations)
  weights = cb.read(weight)
  x = dst.alloc(BLOCKS, dtype=Dtype.f32)
  w = dst.alloc(BLOCKS, dtype=Dtype.f32)
  def load_tile(tile):
    x_item, w_item = inputs.next(), weights.next()
    unpack(x_item, into=x.blocks(offset=tile * 8, count=8))
    unpack(w_item, into=w.blocks(offset=tile * 8, count=8))

  loop(N // 1024, load_tile)

  def sum_squares(block, acc):
    for lanes in sfpu.lanes(x[block]):
      value = sfpu.load(lanes)
      acc = sfpu.mad(value, value, acc)
    return acc

  acc = loop(BLOCKS, sum_squares, carry=sfpu.const(0.0))
  scale = sfpu.rsqrt(sfpu.lane_sum(acc) * (1.0 / N) + EPS)

  def normalize(block):
    for x_lanes, w_lanes in zip(sfpu.lanes(x[block]), sfpu.lanes(w[block])):
      sfpu.store(sfpu.load(x_lanes) * sfpu.load(w_lanes) * scale, x_lanes)

  loop(BLOCKS, normalize)
  result = l1.alloc(N * 2, dtype=Dtype.bf16)
  pack(x, into=result)
  noc.write(result, output)



def graph_text(sink):
  return sink.pretty()


def linear_text(nodes):
  ids = {node: i for i, node in enumerate(nodes)}
  lines = ['// Global topological order; thread placement has not run']
  from ttk.linearize import end_groups
  groups = end_groups(nodes)
  depth = 0
  for node in nodes:
    if node.op.name == 'END' and node is groups[node.src[1]][0]: depth -= 1
    deps = ', '.join(f'%{ids[src]}' for src in node.src)
    lines.append('  '*depth + f'%{ids[node]}: {node.op.name}({deps}) arg={node.arg!r} -> {node.dtype}')
    if node.op.name == 'RANGE': depth += 1
  return '\n'.join(lines)


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--stage', choices=('graph', 'linear', 'render'), default='graph')
  parser.add_argument('--per-thread', action='store_true', help='project rendered output per thread')
  args = parser.parse_args()
  if args.per_thread and args.stage != 'render': parser.error('--per-thread requires --stage render')
  buffers = tuple(Buffer(name, Dtype.bf16, N * 2) for name in ('activations', 'weight', 'output'))
  program = trace(rmsnorm, *buffers)
  if args.stage == 'graph': print(graph_text(program.sink))
  else:
    nodes = linearize(program.sink)
    if args.stage == 'linear': print(linear_text(nodes))
    else: print(FakeRenderer().render(nodes, per_thread=args.per_thread), end='')


if __name__ == '__main__': main()
