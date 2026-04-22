# =============================================================================
# ThCon pipe — "thread controller" path. Any TRISC can issue these:
#   - ConfigUnit: WRCFG/RDCFG/SETC16/RMWCIB* — read/write the Tensix config
#     register file (shared config has 2 state banks × 256 words; thread-local
#     config is 3 × 64 words).
#   - ScalarUnit: SETDMAREG + *DMAREG arithmetic — scalar integer ops on the
#     shared GPR file (3 × 64 × 32-bit).
#
# The sync primitives (mutexes / semaphores / stallwait) also fall into the
# "any thread can issue" bucket but live in sync.py — they coordinate threads
# rather than compute values.
# =============================================================================

M32 = 0xFFFFFFFF


class ConfigUnit:
  NUM_STATES = 2        # Shared config: 2 state banks x 256 ADDR32 words
  CFG_WORDS = 256
  THREAD_CFG_WORDS = 64 # ThreadConfig: 3 threads x 64 ADDR32 words

  def __init__(self, gpr):
    self.gpr = gpr
    self.cfg = [[0] * self.CFG_WORDS for _ in range(self.NUM_STATES)]
    self.thread_cfg = [[0] * self.THREAD_CFG_WORDS for _ in range(3)]

  def execute_setc16(self, d, thread_id):
    if d.setc16_reg < self.THREAD_CFG_WORDS:
      self.thread_cfg[thread_id][d.setc16_reg] = d.setc16_value

  def _state_id(self, thread_id):
    # Config state selection: ADDR32 42 bit 0 in thread_cfg
    return self.thread_cfg[thread_id][42] & 1 if 42 < self.THREAD_CFG_WORDS else 0

  def execute_wrcfg(self, d, thread_id):
    state_id = self._state_id(thread_id)
    addr32 = (d.CfgReg >> 2) & 0x1FF
    if d.wr128b:
      # Write 4 consecutive 32-bit words from 4 consecutive GPRs
      for i in range(4):
        target = (addr32 + i) & 0xFF
        val = self.gpr.read32(thread_id, (d.GprAddress + i) & 63)
        if state_id < self.NUM_STATES and target < self.CFG_WORDS:
          self.cfg[state_id][target] = val
    else:
      val = self.gpr.read32(thread_id, d.GprAddress)
      if state_id < self.NUM_STATES and addr32 < self.CFG_WORDS:
        self.cfg[state_id][addr32] = val

  def execute_rdcfg(self, d, thread_id):
    state_id = self._state_id(thread_id)
    addr32 = (d.CfgReg >> 2) & 0x1FF
    val = self.cfg[state_id][addr32] if state_id < self.NUM_STATES and addr32 < self.CFG_WORDS else 0
    self.gpr.write32(thread_id, d.GprAddress, val)

  def execute_rmwcib(self, d, byte_index):
    # RMW uses state 0 always (per ISA convention for shared config)
    if d.CfgRegAddr < self.CFG_WORDS:
      old = self.cfg[0][d.CfgRegAddr]
      shift = byte_index * 8
      byte_mask = d.Mask << shift
      byte_data = d.Data << shift
      self.cfg[0][d.CfgRegAddr] = (old & ~byte_mask) | (byte_data & byte_mask)


class ScalarUnit:
  def __init__(self, gpr):
    self.gpr = gpr

  def execute_setdmareg(self, d, thread_id):
    # In 16b-payload mode (Payload_SigSelSize=0) the full 16-bit immediate
    # spans both fields: [Payload_SigSelSize:2][Payload_SigSel:14].
    imm16 = (d.Payload_SigSelSize << 14) | d.Payload_SigSel
    self.gpr.write16(thread_id, d.RegIndex16b, imm16)

  def _binop(self, d, thread_id, op):
    result_idx = d.ResultRegIndex & 0x3F  # low 6 bits of 11-bit field
    a = self.gpr.read32(thread_id, d.OpARegIndex)
    b = d.OpBRegIndex if d.OpBisConst else self.gpr.read32(thread_id, d.OpBRegIndex)
    self.gpr.write32(thread_id, result_idx, op(a, b) & M32)

  def execute_adddmareg(self, d, thread_id): self._binop(d, thread_id, lambda a, b: a + b)
  def execute_muldmareg(self, d, thread_id): self._binop(d, thread_id, lambda a, b: a * b)

  def execute_bitwopdmareg(self, d, thread_id):
    # ResultRegIndex is 6 bits here; _binop masks to 6 already
    match d.OpSel:
      case 0: op = lambda a, b: a & b
      case 1: op = lambda a, b: a | b
      case 2: op = lambda a, b: a ^ b
      case _: return  # undefined: leave GPR untouched
    self._binop(d, thread_id, op)

  def execute_shiftdmareg(self, d, thread_id):
    # Shift amount is low 5 bits of OpB (both reg-reg and reg-imm).
    a = self.gpr.read32(thread_id, d.OpARegIndex)
    raw_b = d.OpBRegIndex if d.OpBisConst else self.gpr.read32(thread_id, d.OpBRegIndex)
    shift = raw_b & 0x1F
    match d.Mode:
      case 0: result = (a << shift) & M32   # left
      case 1: result = (a & M32) >> shift   # right (unsigned)
      case _: return
    self.gpr.write32(thread_id, d.ResultRegIndex, result)

  def execute_cmpdmareg(self, d, thread_id):
    # Unsigned compare. Result is 0 or 1.
    a = self.gpr.read32(thread_id, d.OpARegIndex)
    b = d.OpBRegIndex if d.OpBisConst else self.gpr.read32(thread_id, d.OpBRegIndex)
    a &= M32; b &= M32
    match d.OpSel:
      case 0: result = 1 if a >  b else 0
      case 1: result = 1 if a <  b else 0
      case 2: result = 1 if a == b else 0
      case _: return
    self.gpr.write32(thread_id, d.ResultRegIndex, result)
