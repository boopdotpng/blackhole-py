"""Role-templated multicast matmul protocol sketch (text only, one tile/core).

K blocks are explicitly unrolled to carry the depth-one L1 partial between them.
This exercises the remote protocol and fringes, not the reference's performance
schedule, tiled DRAM layout, FP8 conversion, or optional writer-wave barrier.
"""
from dataclasses import dataclass
from ttk.model import Buffer, Param, Dtype, cb, dst, fpu, noc, pack, trace, unpack
from ttk.uop import Thread
from ttk.remote import Connection, verify_roles


@dataclass(frozen=True)
class Role:
  a_sender: bool
  b_sender: bool
  output_noc: int


def matmul_peak(role, *, rows=2, cols=2, blocks=2, shape=(32, 32, 32)):
  ri, ci = Param('ri', Dtype.i32, 0, rows-1), Param('ci', Dtype.i32, 0, cols-1)
  a = Buffer('a', Dtype.bf16, rows*blocks*2048)
  b = Buffer('b', Dtype.bf16, cols*blocks*2048)
  c = Buffer('c', Dtype.bf16, rows*cols*2048)
  rings = [cb.alloc(slot=i, capacity=2, producer='local' if sender else 'remote')
           for i, sender in enumerate((role.a_sender, role.b_sender))]
  peers = [None, None]
  for i, (sender, count, name) in enumerate(((role.a_sender, cols-1, 'a'), (role.b_sender, rows-1, 'b'))):
    if sender and count:
      coords = tuple(Param(f'{name}_{axis}', Dtype.u32, 0, 63) for axis in ('x0','y0','x1','y1','sx','sy'))
      peers[i] = cb.peer(name, receivers=count, coordinates=coords, slot=i, capacity=2)
  ar, br = cb.alloc(kind='SRCA'), cb.alloc(kind='SRCB')
  partials = cb.alloc(slot=24, capacity=1, storage='output')
  outputs = cb.alloc(slot=16, capacity=1, storage='output')
  result = dst.alloc(8)
  partial = None
  a_done = None
  for k in range(blocks):
    items = []
    for i, (sender, buffer, index, thread) in enumerate(((role.a_sender, a, ri, Thread.BRISC),
                                                       (role.b_sender, b, ci, Thread.NCRISC))):
      if sender:
        item = rings[i].acquire()
        noc.read(buffer, into=item, offset=(index*blocks+k)*2048, thread=thread)
        done = noc.multicast(item, peers[i], thread=thread) if peers[i] else item.last_effect
        if i == 0: a_done = done
      else:
        name = 'a' if i == 0 else 'b'
        item = rings[i].receive(sender=tuple(Param(f'{name}_{axis}', Dtype.u32, 0, 63) for axis in ('sx','sy')), thread=thread)
      items.append(item)
    aa, bb = ar.acquire(), br.acquire()
    unpack(items[0], into=aa); unpack(items[1], into=bb)
    a_done = items[0].last_effect
    fpu.op('mvmul', aa, bb, into=result, shape=shape)
    if partial is None:
      partial = partials.acquire()
      pack(result, into=partial)
    else:
      partial = pack(result, into=partial, accumulate=True)
  partial = partial.handoff(outputs)
  noc.write(partial, c, offset=(ri*cols+ci)*2048,
            thread=Thread.NCRISC, noc=role.output_noc,
            after=a_done if role.output_noc == 0 else None)


def templates(*, rows=2, cols=2, blocks=2, shape=(32,32,32)):
  if min(rows, cols, blocks) <= 0: raise ValueError('positive grid and block counts required')
  return {role: trace(matmul_peak, role, rows=rows, cols=cols, blocks=blocks, shape=shape)
          for role in (Role(a, b, n) for a in (True, False) for b in (True, False) for n in (0,1))}


def grid(*, rows=2, cols=2, blocks=2, shape=(32,32,32)):
  variants = templates(rows=rows, cols=cols, blocks=blocks, shape=shape)
  roles = {f'{r},{c}': variants[Role(c == 0, r == 0, 1-c%2)] for r in range(rows) for c in range(cols)}
  links = [Connection(f'{r},0', 'a', tuple(f'{r},{c}' for c in range(1,cols))) for r in range(rows) if cols > 1]
  links += [Connection(f'0,{c}', 'b', tuple(f'{r},{c}' for r in range(1,rows))) for c in range(cols) if rows > 1]
  verify_roles(roles, links)
  return variants, roles, links


if __name__ == '__main__':
  variants, _, _ = grid()
  print(variants[Role(True, True, 0)].render(per_thread=True))
