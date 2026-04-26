from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from .resources import Resource


class OpKind(Enum):
  RV = auto()
  TENSIX = auto()


@dataclass(frozen=True)
class Instruction:
  word: int
  name: str
  kind: OpKind
  unit: Resource
  latency: int = 1
  resources: tuple[Resource | str, ...] = ()
  reads: tuple[str, ...] = ()
  writes: tuple[str, ...] = ()
  payload: object = field(default=None, compare=False)

  @property
  def issue_resources(self) -> list[Resource | str]:
    return [self.unit, *self.resources, *self.reads]
