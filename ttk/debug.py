from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class DebugEvent:
  index: int
  kind: str
  address: int
  name: str
  value: str | None = None

@dataclass(frozen=True)
class DebugRange:
  index: int
  kind: str
  address: int
  size: int
  name: str
  bank: int | None = None
  tile: int = 0

@dataclass(frozen=True)
class L1Timer:
  start: int
  end: int
  cycles: int
  us: float
