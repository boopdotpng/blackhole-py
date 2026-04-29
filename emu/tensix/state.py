# =============================================================================
# Tensix shared backend state — register files and thread-level counters that
# are produced by one pipeline and consumed by another (Src/Dest, RWC, ADC,
# GPR, Semaphores). No instruction decode lives here; units reach in to read
# or mutate these structures.
# =============================================================================

from ..memory import _SEM_WIN_LO

M32 = 0xFFFFFFFF


# =============================================================================
# Register files — SrcA/SrcB double-banked, Dest 1024x16
# =============================================================================

class SrcBank:
  __slots__ = ('rows', 'allowed_client')

  def __init__(self):
    # 64 rows x 16 cols, stored as 32-bit ints (19-bit values)
    self.rows = [[0] * 16 for _ in range(64)]
    self.allowed_client = "unpackers"  # "unpackers" or "matrix_unit"


class SrcRegFile:
  def __init__(self, name="Src"):
    self.name = name
    self.banks = [SrcBank(), SrcBank()]
    self.fpu_bank = 0       # which bank the Matrix Unit reads from
    self.unpack_bank = 0    # which bank the unpacker writes to
    self._valid_queue = []  # banks handed to Matrix Unit, in SETDVALID order

  def flip_to_fpu(self):
    bank = self.unpack_bank
    self.banks[bank].allowed_client = "matrix_unit"
    if bank not in self._valid_queue:
      self._valid_queue.append(bank)
    if self.banks[self.fpu_bank].allowed_client != "matrix_unit":
      self.fpu_bank = self._valid_queue[0]
    self.unpack_bank = self._next_unpack_bank(bank)

  def release_from_fpu(self, release=True):
    bank = self.fpu_bank
    released = self.banks[bank].allowed_client == "matrix_unit"
    if not release:
      return released
    if bank in self._valid_queue:
      self._valid_queue.remove(bank)
    if release:
      self.banks[bank].allowed_client = "unpackers"
    next_fpu = self._valid_queue[0] if self._valid_queue else bank
    self.fpu_bank = next_fpu
    if self.banks[self.unpack_bank].allowed_client != "unpackers":
      self.unpack_bank = bank
    return released

  def clear_fpu_bank(self, keep_reading_same=False):
    bank = self.fpu_bank
    released = self.banks[bank].allowed_client == "matrix_unit"
    self.banks[bank].allowed_client = "unpackers"
    if bank in self._valid_queue:
      self._valid_queue.remove(bank)
    next_fpu = bank if keep_reading_same or not self._valid_queue else self._valid_queue[0]
    self.fpu_bank = next_fpu
    if self.banks[self.unpack_bank].allowed_client != "unpackers":
      self.unpack_bank = bank
    return released

  def reset_sync(self):
    self.fpu_bank = 0
    self.unpack_bank = 0
    self._valid_queue.clear()
    self.banks[0].allowed_client = "unpackers"
    self.banks[1].allowed_client = "unpackers"

  def _next_unpack_bank(self, current):
    other = current ^ 1
    if self.banks[other].allowed_client == "unpackers":
      return other
    if self.banks[current].allowed_client == "unpackers":
      return current
    return other


class DestRegFile:
  ROWS = 1024
  COLS = 16

  def __init__(self):
    self.bits = [[0] * self.COLS for _ in range(self.ROWS)]
    self.valid = [False] * self.ROWS

  def clear_valid(self, row):
    if 0 <= row < self.ROWS: self.valid[row] = False

  def clear_range(self, start, count):
    for r in range(start, min(start + count, self.ROWS)):
      self.valid[r] = False

  def clear_half(self, which):
    base = 512 if which else 0
    for r in range(base, base + 512):
      self.valid[r] = False

  def clear_all(self):
    self.valid = [False] * self.ROWS


# =============================================================================
# Per-thread address counters: RWC, AddrMod, ADC
# =============================================================================

class RWCState:
  def __init__(self):
    self.a = 0       # SrcA row offset (6-bit)
    self.b = 0       # SrcB row offset (6-bit)
    self.d = 0       # Dest row offset (10-bit)
    self.cr = 0      # FidelityPhase (2-bit in spec; stored 3-bit here)
    self.a_cr = 0    # SrcA_Cr checkpoint
    self.b_cr = 0    # SrcB_Cr checkpoint
    self.d_cr = 0    # Dst_Cr   checkpoint

  def execute_setrwc(self, d):
    # BitMask selects which counters to update, and rwc_cr carries
    # CR_A/CR_B/CR_D/C_TO_CR_MODE flags that turn the new value into an
    # increment relative to the checkpoint (or current value for C_TO_CR_MODE
    # on Dst). SET_* also updates the corresponding checkpoint (_Cr).
    bm  = d.BitMask
    crm = d.rwc_cr  # CR_A=1, CR_B=2, CR_D=4, C_TO_CR_MODE=8
    if bm & 0x01:
      val = d.rwc_a & 0x3F
      if crm & 0x01: val = (val + self.a_cr) & 0x3F
      self.a = val
      self.a_cr = val
    if bm & 0x02:
      val = d.rwc_b & 0x3F
      if crm & 0x02: val = (val + self.b_cr) & 0x3F
      self.b = val
      self.b_cr = val
    if bm & 0x04 or crm & 0x08:
      val = d.rwc_d & 0x3FF
      if crm & 0x08:   val = (val + self.d)    & 0x3FF  # C_TO_CR: base = current Dst
      elif crm & 0x04: val = (val + self.d_cr) & 0x3FF  # CR_D:   base = checkpoint
      self.d = val
      self.d_cr = val
    if bm & 0x08:
      self.cr = 0  # SET_F clears FidelityPhase to 0
    return d.clear_ab_vld

  def execute_incrwc(self, d):
    # Per spec §2.4: rwc_cr flags toggle "CR mode" per counter. In CR mode
    # the checkpoint is incremented and the live counter is reset to match;
    # otherwise the live counter is incremented and the checkpoint is left
    # alone. FidelityPhase is not touched by INCRWC.
    crm = d.rwc_cr
    if crm & 0x01:
      self.a_cr = (self.a_cr + d.rwc_a) & 0x3F
      self.a    = self.a_cr
    else:
      self.a    = (self.a    + d.rwc_a) & 0x3F
    if crm & 0x02:
      self.b_cr = (self.b_cr + d.rwc_b) & 0x3F
      self.b    = self.b_cr
    else:
      self.b    = (self.b    + d.rwc_b) & 0x3F
    if crm & 0x04:
      self.d_cr = (self.d_cr + d.rwc_d) & 0x3FF
      self.d    = self.d_cr
    else:
      self.d    = (self.d    + d.rwc_d) & 0x3FF


class AddrModDescriptor:
  __slots__ = ('srca_incr', 'srcb_incr', 'dest_incr', 'cr_incr',
               'srca_clr', 'srcb_clr', 'dest_clr', 'fidelity_incr')

  def __init__(self):
    self.srca_incr = 0
    self.srcb_incr = 0
    self.dest_incr = 0
    self.cr_incr = 0
    self.srca_clr = False
    self.srcb_clr = False
    self.dest_clr = False
    self.fidelity_incr = 0


class AddrModState:
  def __init__(self):
    self.descriptors = [AddrModDescriptor() for _ in range(8)]

  def apply(self, index, rwc):
    if not 0 <= index < 8: return
    desc = self.descriptors[index]
    rwc.a = 0 if desc.srca_clr else (rwc.a + desc.srca_incr) & 0xF
    rwc.b = 0 if desc.srcb_clr else (rwc.b + desc.srcb_incr) & 0xF
    rwc.d = 0 if desc.dest_clr else (rwc.d + desc.dest_incr) & 0xF
    rwc.cr = (rwc.cr + desc.cr_incr) & 0x7


class ADCCounter:
  __slots__ = ('val', 'cr')

  def __init__(self):
    self.val = 0
    self.cr = 0


class ADCChannel:
  def __init__(self):
    self.x = ADCCounter()
    self.y = ADCCounter()
    self.z = ADCCounter()
    self.w = ADCCounter()

  def dim(self, index):
    return (self.x, self.y, self.z, self.w)[index]


class ADCUnit:
  def __init__(self):
    self.channels = [ADCChannel(), ADCChannel()]


class ADCState:
  def __init__(self):
    self.unpackers = [ADCUnit(), ADCUnit()]
    self.packers = ADCUnit()

  def _selected_units(self, mask):
    units = []
    if mask & 1: units.append(self.unpackers[0])
    if mask & 2: units.append(self.unpackers[1])
    if mask & 4: units.append(self.packers)
    return units

  def execute_setadc(self, d):
    for unit in self._selected_units(d.CntSetMask):
      counter = unit.channels[d.ChannelIndex].dim(d.DimensionIndex)
      counter.val = d.Value & M32
      counter.cr = d.Value & M32

  def execute_setadcxy(self, d):
    bm = d.BitMask
    for unit in self._selected_units(d.CntSetMask):
      if bm & 0x01:
        unit.channels[0].x.val = d.Ch0_X & M32
        unit.channels[0].x.cr = d.Ch0_X & M32
      if bm & 0x02:
        unit.channels[0].y.val = d.Ch0_Y & M32
        unit.channels[0].y.cr = d.Ch0_Y & M32
      if bm & 0x04:
        unit.channels[1].x.val = d.Ch1_X & M32
        unit.channels[1].x.cr = d.Ch1_X & M32
      if bm & 0x08:
        unit.channels[1].y.val = d.Ch1_Y & M32
        unit.channels[1].y.cr = d.Ch1_Y & M32

  def execute_setadczw(self, d):
    bm = d.BitMask
    for unit in self._selected_units(d.CntSetMask):
      if bm & 0x01:
        unit.channels[0].z.val = d.Ch0_Z & M32
        unit.channels[0].z.cr = d.Ch0_Z & M32
      if bm & 0x02:
        unit.channels[0].w.val = d.Ch0_W & M32
        unit.channels[0].w.cr = d.Ch0_W & M32
      if bm & 0x04:
        unit.channels[1].z.val = d.Ch1_Z & M32
        unit.channels[1].z.cr = d.Ch1_Z & M32
      if bm & 0x08:
        unit.channels[1].w.val = d.Ch1_W & M32
        unit.channels[1].w.cr = d.Ch1_W & M32

  def execute_incadczw(self, d):
    for unit in self._selected_units(d.CntSetMask):
      unit.channels[0].z.val = (unit.channels[0].z.val + d.Ch0_Z) & M32
      unit.channels[0].w.val = (unit.channels[0].w.val + d.Ch0_W) & M32
      unit.channels[1].z.val = (unit.channels[1].z.val + d.Ch1_Z) & M32
      unit.channels[1].w.val = (unit.channels[1].w.val + d.Ch1_W) & M32

  def execute_setadcxx(self, d):
    for unit in self._selected_units(d.CntSetMask):
      unit.channels[0].x.val = d.x_start & M32
      unit.channels[0].x.cr = d.x_start & M32
      unit.channels[1].x.val = d.x_end2 & M32
      unit.channels[1].x.cr = d.x_end2 & M32


# =============================================================================
# GPR file — 3 threads × 64 × 32-bit
# =============================================================================

class GPRFile:
  def __init__(self):
    # regs[thread][index] = 32-bit value
    self.regs = [[0] * 64 for _ in range(3)]

  def read32(self, thread_id, reg_index):
    return self.regs[thread_id][reg_index & 63]

  def write32(self, thread_id, reg_index, value):
    self.regs[thread_id][reg_index & 63] = value & M32

  def read16(self, thread_id, reg_index_16b):
    reg = (reg_index_16b >> 1) & 63
    val = self.regs[thread_id][reg]
    return (val >> 16) & 0xFFFF if reg_index_16b & 1 else val & 0xFFFF

  def write16(self, thread_id, reg_index_16b, value):
    reg = (reg_index_16b >> 1) & 63
    old = self.regs[thread_id][reg]
    if reg_index_16b & 1:
      self.regs[thread_id][reg] = ((old & 0x0000FFFF) | ((value & 0xFFFF) << 16)) & M32
    else:
      self.regs[thread_id][reg] = ((old & 0xFFFF0000) | (value & 0xFFFF)) & M32


# =============================================================================
# Hardware semaphores — 8 per tile, 4-bit value + 4-bit max. MMIO-mapped
# through the PCBuf semaphore window so TRISC RISC-V cores can post/get.
# =============================================================================

class Semaphores:
  def __init__(self):
    self.value = [0] * 8
    self.max = [0] * 8

  def init(self, idx, value, max_value):
    self.value[idx] = value & 0xF
    self.max[idx] = max_value & 0xF

  def post(self, idx):
    if self.value[idx] < 0xF:
      self.value[idx] += 1

  def get(self, idx):
    if self.value[idx] > 0:
      self.value[idx] -= 1

  # -- router handler API ----------------------------------------------------
  # Reads return the semaphore value; writes are post (bit 0 clear) or get (set).

  def read8(self, addr):  return self.read32(addr & ~3) >> ((addr & 3) * 8) & 0xFF
  def read16(self, addr): return self.read32(addr & ~3) >> ((addr & 2) * 8) & 0xFFFF
  def read32(self, addr): return self.value[(addr - _SEM_WIN_LO) >> 2]

  def write8(self, addr, val):  self.write32(addr & ~3, val)
  def write16(self, addr, val): self.write32(addr & ~3, val)
  def write32(self, addr, val):
    idx = (addr - _SEM_WIN_LO) >> 2
    if val & 1 == 0: self.post(idx)
    else:            self.get(idx)
