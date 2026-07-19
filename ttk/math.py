from dataclasses import dataclass

_DST_ROW_BASE = 1
_ADDR_MOD_AB, _ADDR_MOD_DST, _ADDR_MOD_BIAS = 12, 28, 47

@dataclass(frozen=True)
class SourceCounter:
  increment: int = 0
  clear: bool = False
  advance_carry: bool = False

  def word(self): return self.increment & 0x3F | self.advance_carry << 6 | self.clear << 7

@dataclass(frozen=True)
class DestinationCounter:
  increment: int = 0
  clear: bool = False
  advance_carry: bool = False
  save_to_carry: bool = False

  def word(self):
    return self.increment & 0x3FF | self.advance_carry << 10 | self.clear << 11 | self.save_to_carry << 12

@dataclass(frozen=True)
class PhaseCounter:
  increment: int = 0
  clear: bool = False

@dataclass(frozen=True)
class AddressModifier:
  source_a: SourceCounter = SourceCounter()
  source_b: SourceCounter = SourceCounter()
  destination: DestinationCounter = DestinationCounter()
  fidelity: PhaseCounter = PhaseCounter()
  bias: PhaseCounter = PhaseCounter()

  def configure(self, math, section):
    source = self.source_a.word() | self.source_b.word() << 8
    destination = self.destination.word() | (self.fidelity.increment & 3 | self.fidelity.clear << 2) << 13
    bias = self.bias.increment & 0xF | self.bias.clear << 4
    for register, value in (
      (_ADDR_MOD_AB + section, source),
      (_ADDR_MOD_DST + section, destination),
      (_ADDR_MOD_BIAS + section, bias),
    ): math.set_thread_cfg(register, value)
    return math

def set_dst_row_base(math, row=0): return math.set_thread_cfg(_DST_ROW_BASE, row)
