from __future__ import annotations

from dataclasses import dataclass
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

  def schedule(self, delay: int, callback: Callable[["SimContext"], None],
               label: str = "") -> None:
    self.simulator.schedule(self.cycle + delay, callback, label)


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
    self._objects_snapshot: tuple[SimObject, ...] = ()
    self._events: list[tuple[int, int, ScheduledEvent]] = []
    self._seq = count()

  def add(self, obj: SimObject) -> None:
    self._objects.append(obj)
    self._objects_snapshot = tuple(self._objects)

  def schedule(self, cycle: int, callback: Callable[[SimContext], None],
               label: str = "") -> None:
    if cycle < self.cycle:
      raise ValueError(f"cannot schedule event in the past: {cycle} < {self.cycle}")
    event = ScheduledEvent(cycle, callback, label)
    heappush(self._events, (cycle, next(self._seq), event))

  def tick(self) -> None:
    ctx = SimContext(self.cycle, self)
    objects = self._objects_snapshot
    for phase in self.PHASES:
      if phase is Phase.COMPLETE:
        self._complete_due_events(ctx)
      for obj in objects:
        obj.tick(ctx, phase)
    self.cycle += 1

  def run(self, cycles: int) -> int:
    for _ in range(cycles):
      self.tick()
    return self.cycle

  def _complete_due_events(self, ctx: SimContext) -> None:
    while self._events and self._events[0][0] <= self.cycle:
      _cycle, _seq, event = heappop(self._events)
      event.callback(ctx)
