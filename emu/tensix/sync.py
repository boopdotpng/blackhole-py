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
