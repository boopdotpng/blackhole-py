from __future__ import annotations

from collections import deque

from .isa import Instruction


class InstructionFIFO:
  def __init__(self, capacity: int = 32, soft_capacity: int | None = 28):
    self.capacity = capacity
    self.soft_capacity = soft_capacity
    self._q: deque[Instruction] = deque()
    self._over_soft = False

  def push(self, insn: Instruction, fused_count: int = 1) -> bool:
    limit = self.capacity
    if self.soft_capacity is not None and self._over_soft:
      limit = self.soft_capacity
    if len(self._q) + fused_count > limit:
      return False
    self._q.append(insn)
    self._over_soft = len(self._q) > (self.soft_capacity or self.capacity)
    return True

  def pop(self) -> Instruction | None:
    if not self._q:
      return None
    insn = self._q.popleft()
    if self.soft_capacity is not None and len(self._q) <= self.soft_capacity:
      self._over_soft = False
    return insn

  def push_front(self, insn: Instruction) -> None:
    self._q.appendleft(insn)

  @property
  def full(self) -> bool:
    limit = self.soft_capacity if self._over_soft and self.soft_capacity else self.capacity
    return len(self._q) >= limit

  def __len__(self) -> int:
    return len(self._q)
