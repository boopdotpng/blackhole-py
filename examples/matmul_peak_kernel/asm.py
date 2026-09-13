"""Bind the recovered fixed-register kernel recipes to today's assembler/boot ABI."""
from ttko.asm import Asm
from fw.consts import Firmware
from .isa import *
from .mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscMailbox

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
        self.li(t0, interface + index * 32)
        for i, value in enumerate(words):
          self.li(t1, value); self.sw(t1, t0, i * 4)
    if role in ('brisc', 'ncrisc'):
      mailbox = BM if role == 'brisc' else NM
      self.write32(mailbox.RTA_L1_BASE_PTR, ARG_BASE + (0 if role == 'brisc' else 128))
      self.write32(mailbox.SEM_L1_BASE, SEM_BASE)
      for noc in range(2):
        self.read32(t2, 0xFFB20148 + noc * 0x10000)
        self.andi(t3, t2, 63); self.write8(mailbox.MY_X + noc, t3)
        self.srli(t3, t2, 6); self.andi(t3, t3, 63); self.write8(mailbox.MY_Y + noc, t3)
        for bank, endpoint in enumerate(CONTEXT['endpoints']):
          x,y = endpoint[noc]
          self.li(t0, mailbox.DRAM_BANK_TO_NOC_XY + (noc * len(CONTEXT['endpoints']) + bank) * 2)
          self.li(t1, x | y << 6); self.sh(t1, t0, 0)
      # The old dataflow recipes leave the local endpoint in write cmd buffers.
      noc = 0 if role == 'brisc' else 1
      self.read32(t2, 0xFFB20148 + noc * 0x10000)
      self.slli(t2, t2, 20); self.srli(t2, t2, 20)
      for buf in range(4):
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 0x18, 0)
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 0x2c, 0)
      for buf in (0,2):
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 4, 0)
        self.write32(0xFFB20000 + noc*0x10000 + buf*0x800 + 8, t2)
    self.fence()

  def read32(self, dst, address, *, tmp_addr=t0):
    if isinstance(address, Reg): return self.lw(dst, address, 0)
    self.li(tmp_addr, int(address)); return self.lw(dst, tmp_addr, 0)

  def write32(self, address, value, *, tmp_addr=t0, tmp_val=t1):
    if not isinstance(address, Reg): self.li(tmp_addr, int(address)); address = tmp_addr
    if not isinstance(value, Reg): self.li(tmp_val, int(value)); value = tmp_val
    return self.sw(value, address, 0)

  def read8(self, dst, address, *, tmp_addr=t0):
    if not isinstance(address, Reg): self.li(tmp_addr, int(address)); address = tmp_addr
    return self.lbu(dst, address, 0)

  def write8(self, address, value, *, tmp_addr=t0, tmp_val=t1):
    if not isinstance(address, Reg): self.li(tmp_addr, int(address)); address = tmp_addr
    if not isinstance(value, Reg): self.li(tmp_val, int(value)); value = tmp_val
    return self.sb(value, address, 0)

  def wait_sync_value(self, address, value_reg, *, ptr=t0, actual=t1):
    self.li(ptr, address)
    loop = self._new_label('sync')
    self.label(loop); self.fence(); self.lw(actual, ptr, 0); self.bne(actual, value_reg, loop)
    return self.fence()

  def wait8(self, address, value, *, ptr=t0, actual=t1, expected=t2):
    self.li(ptr, address); self.li(expected, value)
    loop = self._new_label('wait8')
    self.label(loop); self.fence(); self.lbu(actual, ptr, 0); self.bne(actual, expected, loop)
    return self.fence()

  def ret(self): return self  # lower() returns directly to central firmware.

  def lower(self):
    if self.role.startswith('trisc'): self.tensix_sync()
    self._scope.__exit__(None, None, None)
    return super().lower()
