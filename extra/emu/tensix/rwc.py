# ── RWC — Read-Write Counters (per-thread) ───────────────────────────────

class RWCState:
  def __init__(self):
    self.a = 0    # SrcA offset (4-bit)
    self.b = 0    # SrcB offset (4-bit)
    self.d = 0    # Dest offset (4-bit)
    self.cr = 0   # CR / fidelity offset (3-bit)

  def execute_setrwc(self, d):
    bm = d.BitMask
    if bm & 0x01: self.a = d.rwc_a
    if bm & 0x02: self.b = d.rwc_b
    if bm & 0x04: self.d = d.rwc_d
    if bm & 0x08: self.cr = d.rwc_cr
    return d.clear_ab_vld

  def execute_incrwc(self, d):
    self.a  = (self.a  + d.rwc_a)  & 0xF
    self.b  = (self.b  + d.rwc_b)  & 0xF
    self.d  = (self.d  + d.rwc_d)  & 0xF
    self.cr = (self.cr + d.rwc_cr) & 0x7


# ── AddrMod — post-instruction address modification descriptors ──────────

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


# ── ADC — Address Counters (per-thread, per-unit) ────────────────────────

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
      unit.channels[d.ChannelIndex].dim(d.DimensionIndex).val = d.Value

  def execute_setadcxy(self, d):
    bm = d.BitMask
    for unit in self._selected_units(d.CntSetMask):
      if bm & 0x01: unit.channels[0].x.val = d.Ch0_X
      if bm & 0x02: unit.channels[0].y.val = d.Ch0_Y
      if bm & 0x04: unit.channels[1].x.val = d.Ch1_X
      if bm & 0x08: unit.channels[1].y.val = d.Ch1_Y

  def execute_setadczw(self, d):
    bm = d.BitMask
    for unit in self._selected_units(d.CntSetMask):
      if bm & 0x01: unit.channels[0].z.val = d.Ch0_Z
      if bm & 0x02: unit.channels[0].w.val = d.Ch0_W
      if bm & 0x04: unit.channels[1].z.val = d.Ch1_Z
      if bm & 0x08: unit.channels[1].w.val = d.Ch1_W

  def execute_incadczw(self, d):
    for unit in self._selected_units(d.CntSetMask):
      unit.channels[0].z.val += d.Ch0_Z
      unit.channels[0].w.val += d.Ch0_W
      unit.channels[1].z.val += d.Ch1_Z
      unit.channels[1].w.val += d.Ch1_W

  def execute_setadcxx(self, d):
    for unit in self._selected_units(d.CntSetMask):
      for ch in unit.channels:
        ch.x.val = d.x_start
        ch.x.cr = d.x_end2  # store end value in carry register
