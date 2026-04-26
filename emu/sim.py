from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from heapq import heappop, heappush
from itertools import count
from typing import Callable, Protocol


class Phase(Enum):
  COMPLETE = auto()
  COMMIT = auto()
  ISSUE = auto()
  LATCH = auto()


@dataclass(frozen=True)
class ScheduledEvent:
  cycle: int
  callback: Callable[["SimContext"], None]
  label: str = ""


class SimObject(Protocol):
  def tick(self, ctx: "SimContext", phase: Phase) -> None:
    ...


@dataclass
class SimContext:
  cycle: int
  simulator: "Simulator"
  trace_enabled: bool = False
  trace: list[str] = field(default_factory=list)

  def schedule(self, delay: int, callback: Callable[["SimContext"], None],
               label: str = "") -> None:
    self.simulator.schedule(self.cycle + delay, callback, label)

  def log(self, msg: str) -> None:
    if self.trace_enabled:
      self.trace.append(f"{self.cycle:08d}: {msg}")


class Simulator:
  """Small phased simulator kernel.

  Events scheduled for cycle N run in COMPLETE for cycle N. Mutations that
  should become externally visible should normally be staged by the event and
  published by an object's COMMIT phase.
  """

  PHASES = (Phase.COMPLETE, Phase.COMMIT, Phase.ISSUE, Phase.LATCH)

  def __init__(self):
    self.cycle = 0
    self._objects: list[SimObject] = []
    self._events: list[tuple[int, int, ScheduledEvent]] = []
    self._seq = count()
    self.trace_enabled = False
    self.trace: list[str] = []

  def add(self, obj: SimObject) -> None:
    self._objects.append(obj)

  def schedule(self, cycle: int, callback: Callable[[SimContext], None],
               label: str = "") -> None:
    if cycle < self.cycle:
      raise ValueError(f"cannot schedule event in the past: {cycle} < {self.cycle}")
    event = ScheduledEvent(cycle, callback, label)
    heappush(self._events, (cycle, next(self._seq), event))

  def tick(self) -> None:
    ctx = SimContext(self.cycle, self, self.trace_enabled, self.trace)
    for phase in self.PHASES:
      if phase is Phase.COMPLETE:
        self._complete_due_events(ctx)
      for obj in tuple(self._objects):
        obj.tick(ctx, phase)
    self.cycle += 1

  def run(self, cycles: int) -> int:
    for _ in range(cycles):
      self.tick()
    return self.cycle

  def _complete_due_events(self, ctx: SimContext) -> None:
    while self._events and self._events[0][0] <= self.cycle:
      _cycle, _seq, event = heappop(self._events)
      if event.label:
        ctx.log(f"complete {event.label}")
      event.callback(ctx)
