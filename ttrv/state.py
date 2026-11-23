"""Check launch state on the emitted control-flow graph. Each fact must hold on every incoming path."""

from collections import deque
from functools import lru_cache
from .parse import Error


def verify(g):
  initial = frozenset(g.initial)

  @lru_cache(None)
  def function(name, entry):
    start = g.labels[name]
    states = {start: entry}
    work = deque([start])
    result = None
    while work:
      pc = work.popleft()
      state = states[pc]
      item, loc = g.items[pc]
      for op, facts, at in g.events.get(pc, ()):
        if op == "require":
          if missing := facts - state:
            raise Error(at, "state.required", f"{name} requires {', '.join(sorted(missing))} on every path")
        elif op == "tick":
          for i in range(7):
            if f"SFPU cycle {i + 1}" in state:
              state = state | {f"SFPU cycle {i}" if i else "SFPU schedule complete"}
        elif op == "set":
          state = state | facts
        else:
          state = state - facts
      if pc == g.ends[name]:
        if name == g.role:
          if missing := g.completions - state:
            raise Error(loc, "noc.pending", f"return with pending {', '.join(sorted(missing))}")
        result = state if result is None else result & state
        continue
      following = [pc + 1]
      if isinstance(item, tuple):
        op, a, _, label = item
        if op == "jal" and a:
          state = function(label, state)
          if state is None:
            continue
        elif op == "jal":
          following = [g.labels[label]]
        else:
          following.append(g.labels[label])
      for nxt in following:
        merged = states[nxt] & state if nxt in states else state
        if states.get(nxt) != merged:
          states[nxt] = merged
          work.append(nxt)
    return result

  function(g.role, initial)
