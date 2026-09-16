"""Bind the recovered fixed-register kernel recipes to today's assembler/boot ABI."""
from ttko.asm import Asm
from fw.consts import Firmware
from ttko.isa import R, Tensix as TT
from ttko.registers import BriscMailbox as BM, NcriscMailbox as NM, TriscMailbox

CONTEXT = None
ARG_BASE = 0x30000
GRID_BASE = 0x30300  # 64 physical row coords, then 64 column coords (common u32s)
SEM_BASE = 0x30200
A_DONE = SEM_BASE + 96

class KernelBase(Asm):
  def __init__(self, *, role):
    super().__init__(role)
    self._scope = self.scope()
    self._scope.__enter__()
    self.base = CONTEXT['address']
    # Central firmware retains instruction fusion enabled. This prologue only
    # supplies the kernel-local state previously built by the old launcher.
    cbs = CONTEXT['cbs']
    if role != 'trisc1':
      interface = BM.CB_INTERFACE if role == 'brisc' else NM.CB_INTERFACE if role == 'ncrisc' else TriscMailbox.DATA_COMMON['cb_interface']
      shift = 4 if role.startswith('trisc') else 0
      for index, address, size, pages in cbs:
        words = (size >> shift, (address + size) >> shift, (size // pages) >> shift, pages,
                 address >> shift, address >> shift, 0, 0)
        self.li(R.T0, interface + index * 32)
        for i, value in enumerate(words):
          self.li(R.T1, value); self.sw(R.T1, R.T0, i * 4)
    if role in ('brisc', 'ncrisc'):
      mailbox = BM if role == 'brisc' else NM
      self.write32(mailbox.RTA_L1_BASE_PTR, ARG_BASE + (0 if role == 'brisc' else 128))
      self.write32(mailbox.SEM_L1_BASE, SEM_BASE)
      for noc in range(2):
        self.read32(R.T2, 0xFFB20148 + noc * 0x10000)
        self.andi(R.T3, R.T2, 63); self.write8(mailbox.MY_X + noc, R.T3)
        self.srli(R.T3, R.T2, 6); self.andi(R.T3, R.T3, 63); self.write8(mailbox.MY_Y + noc, R.T3)
        for bank, endpoint in enumerate(CONTEXT['endpoints']):
          x,y = endpoint[noc]
          self.li(R.T0, mailbox.DRAM_BANK_TO_NOC_XY + (noc * len(CONTEXT['endpoints']) + bank) * 2)
          self.li(R.T1, x | y << 6); self.sh(R.T1, R.T0, 0)
      # The old dataflow recipes leave the local endpoint in write cmd buffers.
      noc = 0 if role == 'brisc' else 1
      self.read32(R.T2, 0xFFB20148 + noc * 0x10000)
      self.slli(R.T2, R.T2, 20); self.srli(R.T2, R.T2, 20)
      for buf in range(4):
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 0x18, 0)
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 0x2c, 0)
      for buf in (0,2):
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 4, 0)
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 8, R.T2)
    self.fence()

  def ret(self): return self  # lower() returns directly to central firmware.

  def lower(self):
    if self.role.startswith('trisc'): self.tensix_sync()
    self._scope.__exit__(None, None, None)
    return super().lower()
