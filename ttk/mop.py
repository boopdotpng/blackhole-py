from dataclasses import dataclass, field

from isa import Tensix as TT
from ttk.sync import mop_sync

MOP_CFG = 0xFFB80000
REPLAY_SIZE = 32
NOP = TT.TTNOP()

def _replays(values): return tuple(dict.fromkeys(x for x in values if isinstance(x, Replay)))
def _slot_word(value): return value.play_word() if isinstance(value, Replay) else value

class Replay:
  def __init__(self, start, words):
    self.start, self.words = start, tuple(words)

  def play_word(self): return TT.TTREPLAY(self.start, len(self.words), 0, 0)

@dataclass(frozen=True)
class LoopTemplate:
  outer: int
  inner: int
  loop: object
  start: object = NOP
  end0: object = NOP
  end1: object = NOP
  alternate: object = NOP
  last: object = NOP
  outer_last: object = NOP

  def values(self):
    return self.outer, self.inner, self.start, self.end0, self.end1, self.loop, self.alternate, self.last, self.outer_last

  def words(self): return tuple(map(_slot_word, self.values()))
  def replays(self): return _replays(self.values())

@dataclass(frozen=True)
class MaskTemplate:
  a0: object
  skip_a0: object
  b: object = None
  a1: object = None
  a2: object = None
  a3: object = None
  skip_b: object = None

  def values(self):
    extended = any(x is not None for x in (self.a1, self.a2, self.a3))
    word = lambda x: NOP if x is None else x
    return 0, int(self.b is not None) | int(extended) << 1, word(self.b), self.a0, \
      word(self.a1), word(self.a2), word(self.a3), self.skip_a0, word(self.skip_b)

  def words(self): return tuple(map(_slot_word, self.values()))
  def replays(self): return _replays(self.values())

@dataclass
class ReplayBuffer:
  used: set[int] = field(default_factory=set)

  def allocate(self, length, start=None, lower=0, upper=REPLAY_SIZE):
    if length <= 0 or not 0 <= lower <= upper <= REPLAY_SIZE or length > upper - lower: raise ValueError("invalid replay allocation")
    starts = range(lower, upper - length + 1) if start is None else (start,)
    for candidate in starts:
      slots = set(range(candidate, candidate + length))
      if lower <= candidate and candidate + length <= upper and not slots & self.used:
        self.used |= slots; return candidate
    raise MemoryError("replay buffer is full")

@dataclass
class MopState:
  config: tuple = (0,) * 9
  masked: bool = False
  replay: ReplayBuffer = field(default_factory=ReplayBuffer)

class Mop:
  def __init__(self, kernel, pipe):
    role = getattr(kernel, "role", f"trisc{pipe}")
    if pipe not in range(3) or role != f"trisc{pipe}":
      raise RuntimeError(f"{role} cannot use this MOP")
    self.k, self.pipe, self.state = kernel, pipe, MopState()

  def load(self, replay, execute=False, initialize=False):
    words = (TT.TTREPLAY(replay.start, len(replay.words), int(execute), 1), *replay.words)
    if initialize: self.k.initialize_tensix(*words)
    else:
      for word in words: self.k.emit(word)
    return self

  def _replay(self, start, length):
    self.k.emit(TT.TTREPLAY(start, length, 0, 0)); return self

  def replay(self, replay):
    return self._replay(replay.start, len(replay.words))

  def configure(self, template):
    for replay in template.replays(): self.load(replay)
    words = template.words()
    mop_sync(self.k)
    for index, word in enumerate(words): self.k.write(MOP_CFG + index * 4, word)
    self.state.config, self.state.masked = words, isinstance(template, MaskTemplate)
    return self

  def run(self, count=None, mask=0):
    if self.state.masked:
      self.k.emit(TT.TTMOP_CFG(mask >> 16))
      self.k.emit(TT.TTMOP(0, count - 1, mask & 0xFFFF))
    else: self.k.emit(TT.TTMOP(1, 0, 0))
    return self
