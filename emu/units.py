from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

from .isa import Instruction
from .resources import Resource, Scoreboard
from .sim import Phase, SimContext


@dataclass
class Completion:
  instruction: Instruction
  owner: str
  commit: Callable[[SimContext], None] | None = None


class TimedUnit:
  """A single-issue unit with explicit completion and commit phases."""

  def __init__(self, name: str, resource: Resource, scoreboard: Scoreboard):
    self.name = name
    self.resource = resource
    self.scoreboard = scoreboard
    self._pending_commits: deque[Completion] = deque()

  def can_accept(self, insn: Instruction, cycle: int) -> bool:
    return self.scoreboard.block_reason(insn.issue_resources, cycle) is None

  def issue(self, owner: str, insn: Instruction, ctx: SimContext,
            commit: Callable[[SimContext], None] | None = None) -> bool:
    reason = self.scoreboard.block_reason(insn.issue_resources, ctx.cycle)
    if reason is not None:
      ctx.log(f"{owner} stalls on {insn.name}: {reason}")
      return False

    ready_cycle = ctx.cycle + max(1, insn.latency)
    self.scoreboard.reserve(self.resource, owner, ready_cycle)
    for write in insn.writes:
      self.scoreboard.reserve(write, owner, ready_cycle)

    def complete(_ctx: SimContext) -> None:
      self._pending_commits.append(Completion(insn, owner, commit))

    ctx.schedule(max(1, insn.latency), complete, f"{owner}:{insn.name}")
    ctx.log(f"{owner} issued {insn.name} on {self.name}, ready {ready_cycle}")
    return True

  def tick(self, ctx: SimContext, phase: Phase) -> None:
    if phase is not Phase.COMMIT:
      return
    while self._pending_commits:
      completion = self._pending_commits.popleft()
      if completion.commit is not None:
        completion.commit(ctx)
      ctx.log(f"{completion.owner} committed {completion.instruction.name}")
