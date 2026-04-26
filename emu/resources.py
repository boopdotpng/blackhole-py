from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Resource(Enum):
  RV_EX = auto()
  RV_LSU = auto()
  TENSIX_FIFO = auto()
  TENSIX_SYNC = auto()
  TENSIX_CFG = auto()
  TENSIX_THCON = auto()
  TENSIX_UNPACK = auto()
  TENSIX_MATH = auto()
  TENSIX_SFPU = auto()
  TENSIX_PACK = auto()
  TENSIX_MOVER = auto()
  NOC = auto()
  L1 = auto()


@dataclass(frozen=True)
class Reservation:
  resource: Resource | str
  owner: str
  ready_cycle: int


class Scoreboard:
  def __init__(self):
    self._ready: dict[Resource | str, Reservation] = {}

  def ready_at(self, resource: Resource | str) -> int:
    reservation = self._ready.get(resource)
    return 0 if reservation is None else reservation.ready_cycle

  def is_ready(self, resource: Resource | str, cycle: int) -> bool:
    return self.ready_at(resource) <= cycle

  def reserve(self, resource: Resource | str, owner: str, ready_cycle: int) -> None:
    current = self._ready.get(resource)
    if current is None or ready_cycle >= current.ready_cycle:
      self._ready[resource] = Reservation(resource, owner, ready_cycle)

  def block_reason(self, resources: list[Resource | str], cycle: int) -> str | None:
    blocked = [
      f"{resource_name(r)} until {self.ready_at(r)}"
      for r in resources if not self.is_ready(r, cycle)
    ]
    return ", ".join(blocked) if blocked else None


def resource_name(resource: Resource | str) -> str:
  if isinstance(resource, Resource):
    return resource.name
  return resource
