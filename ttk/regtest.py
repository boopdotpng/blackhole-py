"""Self-test for the scratch-GPR allocator (asm.RegAlloc).

    PYTHONPATH=. python3 ttk/regtest.py

Proves: (1) nested leases are disjoint (no clobber under composition), (2)
sequential leases reuse registers, (3) allocation is deterministic, (4)
exhaustion raises instead of silently reusing a live register, (5) reserve()
takes registers out of the pool.
"""
from __future__ import annotations

import sys

from asm import KernelBase, RegAlloc, with_scope
from dsl import t0, t1, t2, a0
from ttk.cb import Cb


class _K(Cb, KernelBase):
  """A kernel that composes the Cb mixin, for exercising decorated helpers."""


class _Composed(KernelBase):
  """Two @with_scope helpers where the outer holds regs live across the inner
  call — the inner must not receive the outer's registers."""

  @with_scope
  def inner(self):
    a, b = self.tmp(2)
    return {int(a), int(b)}

  @with_scope
  def outer(self):
    x, y, z = self.tmp(3)              # held live across inner()
    inner_ids = self.inner()          # nested scope, disjoint by construction
    return {int(x), int(y), int(z)}, inner_ids


def _check(label: str, cond: bool) -> bool:
  print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
  return cond


def main() -> int:
  ok = True

  # (1) nested leases must be disjoint: this is the anti-clobber guarantee.
  a = RegAlloc()
  seen = set()
  with a.scratch(3) as (x, y, z):
    with a.scratch(2) as (p, q):
      inner = {int(x), int(y), int(z), int(p), int(q)}
      seen = inner
  ok &= _check("nested leases hand out 5 distinct registers", len(seen) == 5)

  # (2) after a scope closes, its registers return to the pool and get reused.
  a = RegAlloc()
  with a.scratch(3) as first:
    first_ids = {int(r) for r in first}
  with a.scratch(3) as second:
    second_ids = {int(r) for r in second}
  ok &= _check("sequential leases reuse the freed registers", first_ids == second_ids)

  # (3) determinism: same program -> same physical registers -> same bytes.
  def run():
    al = RegAlloc()
    out = []
    with al.scratch(2) as (u, v):
      out += [int(u), int(v)]
      with al.scratch() as w:
        out.append(int(w))
    return out
  ok &= _check("allocation is deterministic across runs", run() == run())
  ok &= _check("allocates lowest-ranked first (t0,t1,t2)",
               run() == [int(t0), int(t1), int(t2)])

  # (4) exhaustion is a hard error, never a silent live-register reuse.
  a = RegAlloc()
  raised = False
  try:
    with a.scratch(7):          # whole temp pool
      with a.scratch(1):        # one too many
        pass
  except RuntimeError:
    raised = True
  ok &= _check("over-allocation raises instead of clobbering a live reg", raised)

  # (5) reserve() removes a register from the allocatable pool.
  a = RegAlloc().reserve(t0)
  with a.scratch(2) as (r0, r1):
    ok &= _check("reserved t0 is never handed out",
                 int(t0) not in {int(r0), int(r1)})
  # non-temp regs can be reserved too without disturbing the pool
  a = RegAlloc().reserve(a0)
  ok &= _check("reserving a non-pool register is a no-op on the pool",
               len(a._free) == 7)

  # (6) the ergonomic path: @with_scope + flat self.tmp(), no per-block `with`.
  #     Composed helpers nest along the call stack -> caller's live regs are
  #     never handed to the callee.
  k = _Composed()
  outer_ids, inner_ids = k.outer()
  ok &= _check("nested @with_scope helpers get disjoint registers",
               outer_ids.isdisjoint(inner_ids))
  ok &= _check("after outer() returns, the whole pool is free again",
               len(k.regs._free) == 7 and not k.regs._scopes)

  # (7) a real decorated helper assembles and leaves the pool clean.
  k = _K()
  n_before = len(k.items)
  k.cb_reserve_back(0x1000, cb_index=0, count=1)
  ok &= _check("decorated cb_reserve_back emitted instructions", len(k.items) > n_before)
  ok &= _check("cb_reserve_back freed all its scratch on return",
               len(k.regs._free) == 7 and not k.regs._scopes)

  # (8) tmp() outside any scope is a hard error (catches undeclared scratch use).
  raised = False
  try:
    RegAlloc().tmp(1)
  except RuntimeError:
    raised = True
  ok &= _check("tmp() with no open scope raises", raised)

  print("\nRESULT:", "PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  sys.exit(main())
