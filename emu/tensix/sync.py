# =============================================================================
# Cross-thread synchronization primitives:
#   - SyncUnit: SEMINIT/SEMPOST/SEMGET (8 hardware semaphores) and the
#     STALLWAIT/SEMWAIT instructions that install wait-gate latches.
#   - MutexSet: the 5 Tensix mutexes acquired/released by ATGETM/ATRELM.
#     An ATGETM that can't be granted replays the instruction back into the
#     issuing thread's FIFO, which is why acquire() returns a bool.
# =============================================================================


class SyncUnit:
  def __init__(self, semaphores):
    self.semaphores = semaphores

  def execute_seminit(self, d):
    for i in range(8):
      if d.sem_sel & (1 << i):
        self.semaphores.init(i, d.init_value, d.max_value)

  def execute_sempost(self, d):
    for i in range(8):
      if d.sem_sel & (1 << i): self.semaphores.post(i)

  def execute_semget(self, d):
    for i in range(8):
      if d.sem_sel & (1 << i): self.semaphores.get(i)

  def execute_stallwait(self, wait_gate, d):
    wait_gate.install_stallwait(d.stall_res, d.wait_res & 0x1FFF)

  def execute_semwait(self, wait_gate, d):
    wait_gate.install_semwait(d.stall_res, d.sem_sel, d.wait_sem_cond)


class MutexSet:
  """5 Tensix mutexes. owner = thread_id or None. Indexable like a list for
  tests and read-out convenience."""

  NUM_MUTEXES = 5

  def __init__(self):
    self.owners = [None] * self.NUM_MUTEXES

  def acquire(self, index, thread_id):
    """Try to acquire mutex `index` for `thread_id`. Returns True on success,
    False if held by another thread (caller should replay the instruction)."""
    if not 0 <= index < self.NUM_MUTEXES:
      return True  # out-of-range: treat as no-op grant
    owner = self.owners[index]
    if owner is not None and owner != thread_id:
      return False
    self.owners[index] = thread_id
    return True

  def release(self, index, thread_id):
    if 0 <= index < self.NUM_MUTEXES and self.owners[index] == thread_id:
      self.owners[index] = None

  def __getitem__(self, i): return self.owners[i]
  def __setitem__(self, i, v): self.owners[i] = v
  def __len__(self): return len(self.owners)
  def __iter__(self): return iter(self.owners)
