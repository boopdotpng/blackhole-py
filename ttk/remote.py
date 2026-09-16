"""Compose ordinary producer/consumer graphs with explicit participant wiring.

Remote credit/publication edges exist only in this verifier. Device sync is a
later lowering decision; the authored graphs contain no protocol/wait nodes.
"""
from dataclasses import dataclass
from .uop import Ops, UOp, is_ring, PeerGroup, _verify_execution, _acyclic
from .loops import expand, trip_count
from .memory import infer, accesses


@dataclass(frozen=True)
class Connection:
  sender: str
  group: str
  receivers: tuple[str, ...]


def _writes(n):
  return n.op is Ops.NOC_WRITE and n.arg and isinstance(n.arg[0],PeerGroup)


def _signature(sink, predicate):
  seen, result = set(), []
  for access in accesses(sink):
    if not predicate(access): continue
    key = access.item.storage,access.item.sequence
    if key in seen: continue
    seen.add(key)
    result.append(tuple(trip_count(n) for n in access.item.sequence.toposort() if n.op is Ops.RANGE))
  return result


def verify_roles(roles, connections):
  expanded, plans, extra = {}, {}, {}
  for name,kernel in roles.items():
    mapped = {}
    for n in kernel.sink.toposort(): mapped[n] = UOp(n.op,tuple(mapped[s] for s in n.src),n.arg,n.dtype,n.thread)
    sink = expanded[name] = expand(mapped[kernel.sink])
    _verify_execution(sink)
    plans[name] = infer(sink); extra.update(plans[name].edges)
  connected_writes,connected_rings = set(),set()
  for link in connections:
    if link.sender not in roles or any(r not in roles for r in link.receivers): raise ValueError('unknown role')
    if not link.receivers or len(set(link.receivers)) != len(link.receivers) or link.sender in link.receivers:
      raise ValueError('connection requires distinct remote receivers')
    transfers = [a for a in accesses(expanded[link.sender]) if a.write and _writes(a.operation)
                 and a.operation.arg[0].name == link.group]
    if not transfers: raise ValueError('connection has no sender writes')
    if any(a.operation in connected_writes for a in transfers): raise ValueError('duplicate sender connection')
    connected_writes.update(a.operation for a in transfers)
    target = transfers[0].item.storage
    if any(a.item.storage is not target or a.operation.arg[0].receivers != len(link.receivers) for a in transfers):
      raise ValueError('peer layout or receiver count mismatch')
    spec = target.arg[0]
    outgoing = plans[link.sender].items[target]
    signature = _signature(roles[link.sender].sink, lambda a:a.write and _writes(a.operation) and a.operation.arg[0].name == link.group)
    for receiver in link.receivers:
      rings = [s for s in plans[receiver].items if s.arg[0].producer == 'remote' and s.arg[0].slot == spec.slot]
      if len(rings) != 1: raise ValueError('missing or ambiguous remote storage')
      ring = rings[0]; rs = ring.arg[0]
      if ring in connected_rings: raise ValueError('remote storage has multiple producers')
      connected_rings.add(ring)
      if (rs.kind,rs.item,rs.depth,rs.dtype,rs.storage) != (spec.kind,spec.item,spec.depth,spec.dtype,spec.storage):
        raise ValueError('remote storage layout mismatch')
      incoming = plans[receiver].items[ring]
      if set(outgoing) != set(incoming): raise ValueError('remote producer/consumer sequence count mismatch')
      recv_signature = _signature(roles[receiver].sink,lambda a:not a.write and a.item.storage.arg[0].producer == 'remote' and a.item.storage.arg[0].slot == spec.slot)
      if signature != recv_signature: raise ValueError('remote loop nesting/trip count mismatch')
      for seq,occupancy in incoming.items():
        write = outgoing[seq].writes[0].operation
        extra[write] = (*extra.get(write,()),occupancy.credit)
        for read in occupancy.reads: extra[read.operation] = (*extra.get(read.operation,()),write)
  for name,sink in expanded.items():
    for n in sink.toposort():
      if _writes(n) and n not in connected_writes: raise ValueError('unconnected peer write')
      if is_ring(n) and n.arg[0].producer == 'remote' and n not in connected_rings: raise ValueError('unconnected remote storage')
  if not _acyclic(UOp(Ops.SINK,tuple(expanded.values())),extra): raise ValueError('remote credit/publication dependency cycle')
