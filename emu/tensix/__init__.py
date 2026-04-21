from ..memory import Memory, Semaphores, INSTRN_BUF_T0, MOP_CFG_BASE
from ..dsl import decode_tensix
from .frontend import TensixThread
from .sync import SyncUnit
from .config import ConfigUnit, ScalarUnit, GPRFile
from .regfile import SrcRegFile, DestRegFile
from .fpu import FPU
from .sfpu import SFPU
from .rwc import RWCState, AddrModState, ADCState
from .trisc0 import TRISC0Decoder
from .trisc1 import TRISC1Decoder
from .trisc2 import TRISC2Decoder

_TRISC_THREAD = {'trisc0': 0, 'trisc1': 1, 'trisc2': 2}


class TensixCoprocessor:
  def __init__(self):
    # Shared backend state. The 8 hardware semaphores live inside the
    # coprocessor (per emu-specs/semaphores.md); TRISC RISC-V cores reach
    # them through the PCBuf semaphore window, which the device wires to
    # this object.
    self.semaphores = Semaphores()
    self.gpr = GPRFile()
    self.sync = SyncUnit(self.semaphores)
    self.config_unit = ConfigUnit(self.gpr)
    self.scalar = ScalarUnit(self.gpr)
    self.srca = SrcRegFile("SrcA")
    self.srcb = SrcRegFile("SrcB")
    self.dest = DestRegFile()
    self.fpu = FPU(self.srca, self.srcb, self.dest)
    self.sfpu = SFPU(self.dest)
    self.rwc = [RWCState() for _ in range(3)]
    self.addr_mod = AddrModState()
    self.adc = [ADCState() for _ in range(3)]
    self.threads = [TensixThread(i) for i in range(3)]
    self.mutexes = [None] * 5  # 5 mutexes, owner = thread_id or None
    self.trisc0 = TRISC0Decoder(self)
    self.trisc1 = TRISC1Decoder(self)
    self.trisc2 = TRISC2Decoder(self)
    # Tensix backend config register file (0xFFEF0000..0xFFEFFFFF).
    self.cfg = Memory()

  def instrn_handler_for(self, role):
    if role == 'brisc':       return _InstrnHandler(self, _brisc_thread_of_addr)
    if role in _TRISC_THREAD: return _InstrnHandler(self, _const(_TRISC_THREAD[role]))
    return None  # ncrisc — no push capability

  def mop_handler_for(self, role):
    if role in _TRISC_THREAD: return _MopCfgHandler(self, _TRISC_THREAD[role])
    return None  # brisc/ncrisc — no MOP cfg access

  def push_instruction(self, thread_id, word):
    return self.threads[thread_id].fifo.push(word)

  def step(self):
    for thread in self.threads:
      self._step_thread(thread)

  def _step_thread(self, thread):
    insn = thread.next_instruction()
    if insn is None: return
    if thread.wait_gate.is_blocking(insn, self._hw_state(), thread.id): return
    self._dispatch(thread, insn)

  def _dispatch(self, thread, word):
    d = decode_tensix(word)
    adc = self.adc[thread.id]
    match d.name:
      case 'NOP' | 'DMANOP': pass
      # Sync unit: mutexes, semaphores, stall/wait
      case 'ATGETM':
        if d.mutex_index < len(self.mutexes):
          owner = self.mutexes[d.mutex_index]
          if owner is not None and owner != thread.id:
            thread.replay_instruction(word)  # block: put it back in the FIFO
            return
          self.mutexes[d.mutex_index] = thread.id
      case 'ATRELM':
        mi = d.mutex_index
        if mi < len(self.mutexes) and self.mutexes[mi] == thread.id:
          self.mutexes[mi] = None
      case 'STALLWAIT': self.sync.execute_stallwait(thread.wait_gate, d)
      case 'SEMINIT':   self.sync.execute_seminit(d)
      case 'SEMPOST':   self.sync.execute_sempost(d)
      case 'SEMGET':    self.sync.execute_semget(d)
      case 'SEMWAIT':   self.sync.execute_semwait(thread.wait_gate, d)
      # Config unit
      case 'WRCFG':   self.config_unit.execute_wrcfg(d, thread.id)
      case 'RDCFG':   self.config_unit.execute_rdcfg(d, thread.id)
      case 'SETC16':  self.config_unit.execute_setc16(d, thread.id)
      case 'RMWCIB0': self.config_unit.execute_rmwcib(d, byte_index=0)
      case 'RMWCIB1': self.config_unit.execute_rmwcib(d, byte_index=1)
      # Scalar unit (ThCon)
      case 'SETDMAREG': self.scalar.execute_setdmareg(d, thread.id)
      case 'ADDDMAREG': self.scalar.execute_adddmareg(d, thread.id)
      case 'MULDMAREG': self.scalar.execute_muldmareg(d, thread.id)
      # ADC (any thread can issue)
      case 'SETADC':   adc.execute_setadc(d)
      case 'SETADCXY': adc.execute_setadcxy(d)
      case 'SETADCZW': adc.execute_setadczw(d)
      case 'INCADCZW': adc.execute_incadczw(d)
      case 'SETADCXX': adc.execute_setadcxx(d)
      case _:
        # Try TRISC1 (FPU/SFPU/RWC), then TRISC0 (Unpack), then TRISC2 (Pack).
        # Unknown opcodes are silently ignored for functional emulation.
        (self.trisc1.dispatch(word, thread)
         or self.trisc0.dispatch(word, thread)
         or self.trisc2.dispatch(word, thread))

  def _hw_state(self):
    return HardwareState(self.semaphores, self.srca, self.srcb)

  def write_mop_cfg(self, thread_id, reg_index, value):
    if 0 <= reg_index < 9:
      self.threads[thread_id].mop.cfg[reg_index] = value

  def read_pcbuf(self, thread_id, offset):
    # Resolves immediately in functional emulation (synchronous dispatch).
    return 0


# Bound at registration time by `instrn_handler_for(role)`:
#   BRISC decodes the thread from the address (T0/T1/T2 = +0/+0x10000/+0x20000);
#   TRISCs always target their own thread.
def _brisc_thread_of_addr(addr): return (addr - INSTRN_BUF_T0) >> 16
def _const(x):
  def f(_addr): return x
  return f


class _InstrnHandler:
  def __init__(self, tensix, thread_of_addr):
    self.tensix = tensix
    self._thread = thread_of_addr

  def read8(self, addr):  return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val):  pass
  def write16(self, addr, val): pass
  def write32(self, addr, val): self.tensix.push_instruction(self._thread(addr), val)


class _MopCfgHandler:
  def __init__(self, tensix, thread):
    self.tensix = tensix
    self.thread = thread

  def read8(self, addr):  return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val):  pass
  def write16(self, addr, val): pass
  def write32(self, addr, val):
    reg_index = (addr - MOP_CFG_BASE) >> 2
    self.tensix.write_mop_cfg(self.thread, reg_index, val)


class HardwareState:
  __slots__ = ('semaphores', 'srca', 'srcb',
               'srca_unpack_bank_owner', 'srcb_unpack_bank_owner',
               'srca_fpu_bank_owner', 'srcb_fpu_bank_owner')

  def __init__(self, semaphores, srca, srcb):
    self.semaphores = semaphores
    self.srca = srca
    self.srcb = srcb
    # Functional emu: pipeline occupancy signals are idle (synchronous
    # completion). Only bank ownership matters.
    self.srca_unpack_bank_owner = srca.banks[srca.unpack_bank].allowed_client
    self.srcb_unpack_bank_owner = srcb.banks[srcb.unpack_bank].allowed_client
    self.srca_fpu_bank_owner = srca.banks[srca.fpu_bank].allowed_client
    self.srcb_fpu_bank_owner = srcb.banks[srcb.fpu_bank].allowed_client
