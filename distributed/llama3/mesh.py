"""Static BHP1 topology compiler; deterministic shortest-path routes.

Ports are logical ERISC indices, not QSFP cage numbers. Input must come from
reciprocal peer discovery before installation. This does not install routes.
"""
from collections import deque


def routes(topology):
    if topology.get('version') != 1 or not 0 < topology.get('epoch', 0) < 2**32:
        raise ValueError('unsupported topology version/epoch')
    ranks = topology['ranks']
    if not ranks or len(set(ranks)) != len(ranks) or any(type(r) is not int or not 0 <= r < 65536 for r in ranks):
        raise ValueError('invalid ranks')
    graph = {r: [] for r in ranks}
    occupied = set()
    for edge in topology['links']:
        a, b = edge['a'], edge['b']  # [rank, logical ERISC]
        if a[0] == b[0]:
            raise ValueError('self link')
        for rank, port in (a,b):
            if rank not in graph or type(port) is not int or not 0 <= port < 12 or (rank,port) in occupied:
                raise ValueError('unknown rank, invalid or multiply assigned port')
            occupied.add((rank,port))
        graph[a[0]].append((b[0],a[1]))
        graph[b[0]].append((a[0],b[1]))
    output = {}
    for source in sorted(ranks):
        found = {source: None}
        todo = deque([source])
        while todo:
            here = todo.popleft()
            for peer, port in sorted(graph[here]):
                if peer not in found:
                    first = (peer,port) if here == source else found[here]
                    found[peer] = first
                    todo.append(peer)
        if len(found) != len(ranks):
            raise ValueError('disconnected mesh')
        output[source] = {dst: dict(next_rank=first[0], port=first[1])
                          for dst,first in found.items() if first is not None}
    return output
