import math
import struct
from collections import deque

from .memory import Memory, Semaphores, INSTRN_BUF_T0, MOP_CFG_BASE
from dsl import decode_tensix

M32 = 0xFFFFFFFF

_TRISC_THREAD = {'trisc0': 0, 'trisc1': 1, 'trisc2': 2}


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

  def flip_to_fpu(self):
    self.banks[self.unpack_bank].allowed_client = "matrix_unit"
    self.unpack_bank ^= 1

  def release_from_fpu(self):
    self.banks[self.fpu_bank].allowed_client = "unpackers"
    self.fpu_bank ^= 1


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


# =============================================================================
# Per-thread frontend pipeline — FIFO + MOP + Replay + WaitGate
# =============================================================================

class InstructionFIFO:
  CAPACITY = 32

  def __init__(self):
    self._q = deque()

  def push(self, word):
    if len(self._q) >= self.CAPACITY: return False
    self._q.append(word & M32)
    return True

  def pop(self):
    return self._q.popleft() if self._q else None

  @property
  def full(self):  return len(self._q) >= self.CAPACITY
  @property
  def empty(self): return len(self._q) == 0
  def __len__(self): return len(self._q)


def _is_nop(word):
  return ((word >> 24) & 0xFF) == 0x02


class MOPExpander:
  def __init__(self):
    self.cfg = [0] * 9      # MopCfg[0..8], write-only from RISC-V
    self.mask_hi = 0        # set by MOP_CFG instruction (opcode 0x03)
    self._expansion = None  # iterator when expansion is in progress

  @property
  def busy(self):
    return self._expansion is not None

  def next(self, fifo):
    if self._expansion is not None:
      try:
        return next(self._expansion)
      except StopIteration:
        self._expansion = None
        # 1-cycle transition penalty after expansion ends.
        return None
    word = fifo.pop()
    if word is None: return None
    opcode = (word >> 24) & 0xFF
    if opcode == 0x03:  # MOP_CFG
      self.mask_hi = word & 0xFFFF
      return None
    if opcode == 0x01:  # MOP
      template = (word >> 23) & 1
      count1 = (word >> 16) & 0x7F
      mask_lo = word & 0xFFFF
      if template == 0:
        mask32 = (self.mask_hi << 16) | mask_lo
        self._expansion = self._expand_template0(mask32, count1)
      else:
        self._expansion = self._expand_template1()
      try:
        return next(self._expansion)
      except StopIteration:
        self._expansion = None
        return None
    return word  # pass-through

  def _expand_template0(self, mask, count1):
    flags = self.cfg[1]
    insn_b, insn_a0 = self.cfg[2], self.cfg[3]
    insn_a1, insn_a2, insn_a3 = self.cfg[4], self.cfg[5], self.cfg[6]
    skip_a0, skip_b = self.cfg[7], self.cfg[8]
    has_b = flags & 1
    has_a123 = flags & 2
    m = mask
    for _ in range(count1 + 1):
      if (m & 1) == 0:
        yield insn_a0
        if has_a123:
          yield insn_a1; yield insn_a2; yield insn_a3
        if has_b:
          yield insn_b
      else:
        yield skip_a0
        if has_b: yield skip_b
      m >>= 1

  def _expand_template1(self):
    outer_count = self.cfg[0] & 127
    inner_count = self.cfg[1] & 127
    start_op = self.cfg[2]
    end_op0, end_op1 = self.cfg[3], self.cfg[4]
    loop_op, loop_op1 = self.cfg[5], self.cfg[6]
    loop0_last, loop1_last = self.cfg[7], self.cfg[8]

    # If LoopOp1 is non-NOP, inner loop alternates between LoopOp and
    # LoopOp1 by XOR-flipping, and InnerCount doubles.
    if _is_nop(loop_op1):
      loop_op_flip = 0
    else:
      loop_op_flip = loop_op ^ loop_op1
      inner_count *= 2

    # Hardware bug: must be replicated exactly
    if outer_count == 1 and _is_nop(start_op) and inner_count == 0 and not _is_nop(end_op0):
      outer_count += 128

    cur_loop_op = loop_op
    for j in range(outer_count):
      if not _is_nop(start_op): yield start_op
      for i in range(inner_count):
        if i != inner_count - 1:     yield cur_loop_op
        elif j != outer_count - 1:   yield loop1_last  # last inner, not last outer
        else:                        yield loop0_last  # last inner of last outer
        cur_loop_op ^= loop_op_flip  # alternate LoopOp / LoopOp1
      if not _is_nop(end_op0):
        yield end_op0
        if not _is_nop(end_op1): yield end_op1


class ReplayExpander:
  def __init__(self):
    self.buffer = [0] * 32    # 32-slot circular buffer, not CPU-accessible
    self._playback = None     # iterator during playback
    self._recording = None    # dict with recording state, or None
    self._pending_from_mop = None

  @property
  def busy(self):
    return self._playback is not None or self._recording is not None

  def next(self, mop, fifo):
    if self._playback is not None:
      try:
        return next(self._playback)
      except StopIteration:
        self._playback = None  # no transition penalty (unlike MOP)

    if self._recording is not None:
      word = mop.next(fifo)
      if word is None:
        return self._pending_from_mop
      rec = self._recording
      self.buffer[(rec['start'] + rec['count']) % 32] = word
      rec['count'] += 1
      if rec['count'] >= rec['total']:
        self._recording = None
      return word if rec['exec'] else None

    word = mop.next(fifo)
    if word is None: return None
    opcode = (word >> 24) & 0xFF
    if opcode != 0x04: return word  # pass-through

    # Decode REPLAY instruction
    start_idx = (word >> 14) & 0x1F   # low 5 bits used (wraps mod 32)
    length = (word >> 4) & 0x3F       # low 6 bits; 0 means 64
    exec_while = (word >> 1) & 1
    load_mode = word & 1
    if length == 0: length = 64

    if load_mode:
      self._recording = {'start': start_idx, 'total': length, 'count': 0, 'exec': bool(exec_while)}
      return None
    # Playback: emit `length` instructions from buffer
    self._playback = self._play(start_idx, length)
    try:
      return next(self._playback)
    except StopIteration:
      self._playback = None
      return None

  def _play(self, start, count):
    for i in range(count):
      yield self.buffer[(start + i) % 32]


# Block mask bits (stall_res field, 9 bits)
STALL_TDMA   = 0x001  # B0: Misc, Mover, ThCon, Packer
STALL_SYNC   = 0x002  # B1: Sync unit
STALL_PACK   = 0x004  # B2: Packer
STALL_UNPACK = 0x008  # B3: Unpacker
STALL_XMOV   = 0x010  # B4: Mover
STALL_THCON  = 0x020  # B5: Scalar/ThCon
STALL_MATH   = 0x040  # B6: Matrix Unit (FPU)
STALL_CFG    = 0x080  # B7: Config unit
STALL_SFPU   = 0x100  # B8: Vector Unit (SFPU)
STALL_THREAD = 0x1FF  # all bits: block everything

# Condition mask bits for STALLWAIT (wait_res field, 13 bits)
COND_THCON     = 0x001   # C0: ThCon outstanding
COND_UNPACK0   = 0x002   # C1: Unpacker 0 pipeline
COND_UNPACK1   = 0x004   # C2: Unpacker 1 pipeline
COND_PACK0     = 0x008   # C3: Packer pipeline
COND_MATH      = 0x010   # C4: FPU pipeline
COND_SRCA_CLR  = 0x020   # C5: SrcA unpack bank not owned by Unpackers
COND_SRCB_CLR  = 0x040   # C6: SrcB unpack bank not owned by Unpackers
COND_SRCA_VLD  = 0x080   # C7: SrcA FPU bank not owned by MatrixUnit
COND_SRCB_VLD  = 0x100   # C8: SrcB FPU bank not owned by MatrixUnit
COND_XMOV      = 0x200   # C9: Mover outstanding
COND_TRISC_CFG = 0x400   # C10: RISC-V config write pending
COND_SFPU      = 0x800   # C11: SFPU pipeline
COND_CFGEXU    = 0x1000  # C12: Config unit pipeline (any thread)

_OPCODE_BLOCK_BITS = {}

def _register_block_bits():
  for op in (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6):  # Sync unit (B1)
    _OPCODE_BLOCK_BITS[op] = STALL_SYNC
  for op in (0x42, 0x43):                                # Unpack (B3)
    _OPCODE_BLOCK_BITS[op] = STALL_UNPACK
  for op in (0x08, 0x0A, 0x10, 0x11, 0x13, 0x16, 0x26, 0x27, 0x28, 0x30,
             0x33, 0x36, 0x37, 0x38):                    # FPU / Matrix Unit (B6)
    _OPCODE_BLOCK_BITS[op] = STALL_MATH
  for op in (0xB0, 0xB1, 0xB2, 0xB3, 0xB4):              # Config unit (B7)
    _OPCODE_BLOCK_BITS[op] = STALL_CFG
  for op in (0x45, 0x58, 0x5A, 0x5B, 0x5C, 0x5D, 0x60):  # Scalar/ThCon (B5), also B0
    _OPCODE_BLOCK_BITS[op] = STALL_THCON | STALL_TDMA
  _OPCODE_BLOCK_BITS[0x46] = STALL_THCON | STALL_TDMA    # FLUSHDMA: blocks all ThCon use
  _OPCODE_BLOCK_BITS[0x41] = STALL_PACK | STALL_TDMA     # Packer (B2), also B0
  for op in range(0x70, 0x9A):                           # SFPU (B8)
    _OPCODE_BLOCK_BITS[op] = STALL_SFPU
  for op in (0x50, 0x51, 0x54, 0x55, 0x5E):              # ADC / Misc (B0)
    _OPCODE_BLOCK_BITS[op] = STALL_TDMA
  _OPCODE_BLOCK_BITS[0x02] = STALL_THREAD                # NOP: blocked only if all bits set

_register_block_bits()


def _instruction_block_bits(word):
  return _OPCODE_BLOCK_BITS.get((word >> 24) & 0xFF, 0)


class WaitGate:
  def __init__(self):
    self.opcode = None       # "STALLWAIT", "SEMWAIT", or None
    self.block_mask = 0      # 9-bit
    self.cond_mask = 0       # 13-bit (STALLWAIT only)
    self.sem_mask = 0        # 8-bit (SEMWAIT only)
    self.sem_cond = 0        # 2-bit (SEMWAIT only)
    self._one_cycle_hold = False

  def install_stallwait(self, block_mask, cond_mask):
    # Default substitutions per ISA spec
    if block_mask == 0: block_mask = STALL_MATH
    if cond_mask == 0:  cond_mask = 0x0F  # C0|C1|C2|C3
    self.opcode = "STALLWAIT"
    self.block_mask = block_mask
    self.cond_mask = cond_mask
    self.sem_mask = 0
    self.sem_cond = 0
    self._one_cycle_hold = True

  def install_semwait(self, block_mask, sem_mask, sem_cond):
    if block_mask == 0: block_mask = STALL_MATH
    self.opcode = "SEMWAIT"
    self.block_mask = block_mask
    self.cond_mask = 0
    self.sem_mask = sem_mask
    self.sem_cond = sem_cond
    self._one_cycle_hold = True

  def is_blocking(self, word, hw, thread_id):
    if self.opcode is None: return False
    if self._one_cycle_hold:
      self._one_cycle_hold = False
      return True
    if not self._evaluate(hw, thread_id):
      self.opcode = None  # condition cleared — release latch
      return False
    # Condition still active — only block if this insn's category is in block_mask.
    return bool(_instruction_block_bits(word) & self.block_mask)

  def _evaluate(self, hw, thread_id):
    if self.opcode == "STALLWAIT": return self._eval_stallwait(hw, thread_id)
    if self.opcode == "SEMWAIT":   return self._eval_semwait(hw)
    return False

  def _eval_stallwait(self, hw, thread_id):
    # For functional (synchronous) emulation, pipeline occupancy signals
    # (C0-C4, C9-C12) are always cleared — only bank ownership (C5-C8) matters.
    cond = self.cond_mask
    if (cond >> 5) & 1 and hw.srca_unpack_bank_owner != "unpackers":   return True  # C5
    if (cond >> 6) & 1 and hw.srcb_unpack_bank_owner != "unpackers":   return True  # C6
    if (cond >> 7) & 1 and hw.srca_fpu_bank_owner    != "matrix_unit": return True  # C7
    if (cond >> 8) & 1 and hw.srcb_fpu_bank_owner    != "matrix_unit": return True  # C8
    return False

  def _eval_semwait(self, hw):
    sem = hw.semaphores
    for i in range(8):
      if not (self.sem_mask >> i) & 1: continue
      val, mx = sem.value[i], sem.max[i]
      if (self.sem_cond >> 0) & 1 and val == 0:  return True  # STALL_ON_ZERO
      if (self.sem_cond >> 1) & 1 and val >= mx: return True  # STALL_ON_MAX
    return False


class TensixThread:
  def __init__(self, thread_id):
    self.id = thread_id
    self.fifo = InstructionFIFO()
    self.mop = MOPExpander()
    self.replay = ReplayExpander()
    self.wait_gate = WaitGate()
    self._replay_word = None  # for re-inserting a blocked instruction

  def next_instruction(self):
    if self._replay_word is not None:
      word = self._replay_word
      self._replay_word = None
      return word
    # Walk the pipeline: Replay ← MOP ← FIFO
    return self.replay.next(self.mop, self.fifo)

  def replay_instruction(self, word):
    self._replay_word = word


# =============================================================================
# Backend units: GPRFile, ConfigUnit, ScalarUnit, SyncUnit
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
      self.regs[thread_id][reg] = (old & 0x0000FFFF) | ((value & 0xFFFF) << 16)
    else:
      self.regs[thread_id][reg] = (old & 0xFFFF0000) | (value & 0xFFFF)


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


# =============================================================================
# FPU — Matrix Unit. Reads SrcA/SrcB (19-bit), writes Dest (FP32 bits).
# =============================================================================

def _19bit_to_float(val):
  # Layout: { sign[18], mantissa[17:8] (10 bits), exponent[7:0] (8 bits) }
  sign = (val >> 18) & 1
  mant = (val >> 8) & 0x3FF
  exp  = val & 0xFF
  # Map to FP32: mantissa zero-padded from 10 to 23 bits
  fp32_bits = (sign << 31) | (exp << 23) | (mant << 13)
  return struct.unpack('f', struct.pack('I', fp32_bits))[0]

def _float_to_19bit(f):
  if math.isnan(f):
    return (0x7F << 8) | 0x200  # NaN marker: exp=0x7F in bits[7:0], quiet-NaN mant bit in bits[17:8]
  bits = struct.unpack('I', struct.pack('f', float(f)))[0]
  sign = (bits >> 31) & 1
  exp  = (bits >> 23) & 0xFF
  mant = (bits >> 13) & 0x3FF
  return (sign << 18) | (mant << 8) | exp

def _dest_to_float(val):
  return struct.unpack('f', struct.pack('I', val & M32))[0]

def _float_to_dest(f):
  if math.isnan(f):
    return 0x7FC00000
  return struct.unpack('I', struct.pack('f', float(f)))[0]

# 19-bit -inf for ZEROSRC with write_mode=1 (SrcA negative-infinity fill)
# Layout: sign=1, mant=0, exp=0xFF in bits[7:0]
_NEG_INF_19BIT = (1 << 18) | 0xFF


class FPU:
  def __init__(self, srca, srcb, dest):
    self.srca = srca
    self.srcb = srcb
    self.dest = dest

  def zeroacc(self, d):
    if d.clear_mode == 0:   self.dest.clear_valid(d.where)
    elif d.clear_mode == 1: self.dest.clear_range(d.where, 16)
    elif d.clear_mode == 2: self.dest.clear_half(d.where & 1)
    else:                   self.dest.clear_all()

  def zerosrc(self, d):
    if d.src_mask & 1:  # SrcA
      fill = _NEG_INF_19BIT if d.write_mode else 0
      bank = self.srca.banks[self.srca.fpu_bank]
      for r in range(64):
        for c in range(16):
          bank.rows[r][c] = fill
    if d.src_mask & 2:  # SrcB (always zero, never -inf)
      bank = self.srcb.banks[self.srcb.fpu_bank]
      for r in range(64):
        for c in range(16):
          bank.rows[r][c] = 0

  def mvmul(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    srca_base = rwc.a * 16
    srcb_base = rwc.b * 8
    for row in range(8):
      for col in range(16):
        acc = 0.0
        for k in range(16):
          srca_row = (srca_base + k) % 64
          srcb_row = (srcb_base + row) % 64
          a = _19bit_to_float(srca_bank.rows[srca_row][col])
          b = _19bit_to_float(srcb_bank.rows[srcb_row][k])
          acc += a * b
        dest_row = (dst_base + row) % self.dest.ROWS
        if self.dest.valid[dest_row]:
          acc += _dest_to_float(self.dest.bits[dest_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(acc)
        self.dest.valid[dest_row] = True

  def elwadd(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    srca_base = rwc.a * 16
    srcb_base = rwc.b * 16
    for row in range(16):
      for col in range(16):
        srca_row = (srca_base + row) % 64
        srcb_row = (srcb_base + row) % 64
        a = _19bit_to_float(srca_bank.rows[srca_row][col])
        b = _19bit_to_float(srcb_bank.rows[srcb_row][col])
        result = a + b
        dest_row = (dst_base + row) % self.dest.ROWS
        if d.dest_accum_en and self.dest.valid[dest_row]:
          result += _dest_to_float(self.dest.bits[dest_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(result)
        self.dest.valid[dest_row] = True

  def gmpool(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srca_base = rwc.a * 16
    for row in range(16):
      srca_row = (srca_base + row) % 64
      dest_row = (dst_base + row) % self.dest.ROWS
      was_valid = self.dest.valid[dest_row]
      for col in range(16):
        val = _19bit_to_float(srca_bank.rows[srca_row][col])
        if was_valid:
          old = _dest_to_float(self.dest.bits[dest_row][col])
          val = max(val, old)
        self.dest.bits[dest_row][col] = _float_to_dest(val)
      self.dest.valid[dest_row] = True

  def movb2d(self, d, rwc):
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    m = d.movb2d_instr_mod
    nrows = 1 if m == 0 else (4 if m == 1 else 8)
    for row in range(nrows):
      src_row = (d.src + row) % 64
      dest_row = (d.dst + rwc.d * 16 + row) % self.dest.ROWS
      for col in range(16):
        val = _19bit_to_float(srcb_bank.rows[src_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(val)
        self.dest.valid[dest_row] = True

  def _movd2x(self, d, rwc, bank):
    nrows = 1 if d.instr_mod == 0 else 4
    for row in range(nrows):
      dest_row = (d.dst + rwc.d * 16 + row) % self.dest.ROWS
      dst_row = (d.src + row) % 64
      for col in range(16):
        val = _dest_to_float(self.dest.bits[dest_row][col]) if self.dest.valid[dest_row] else 0.0
        bank.rows[dst_row][col] = _float_to_19bit(val)

  def movd2a(self, d, rwc): self._movd2x(d, rwc, self.srca.banks[self.srca.fpu_bank])
  def movd2b(self, d, rwc): self._movd2x(d, rwc, self.srcb.banks[self.srcb.fpu_bank])

  def cleardvalid(self, d):
    if d.cleardvalid & 1: self.srca.release_from_fpu()
    if d.cleardvalid & 2: self.srcb.release_from_fpu()

  def trnspsrcb(self, d):
    bank = self.srcb.banks[self.srcb.fpu_bank]
    block = [[bank.rows[16 + r][c] for c in range(16)] for r in range(16)]
    for r in range(16):
      for c in range(16):
        bank.rows[16 + r][c] = block[c][r]


# =============================================================================
# SFPU — 32-lane SIMD Vector Unit. Reads/writes Dest via SFPLOAD/SFPSTORE.
# =============================================================================

def _to_float(bits): return struct.unpack('f', struct.pack('I', bits & M32))[0]
def _to_bits(f):     return struct.unpack('I', struct.pack('f', float(f)))[0]
def _sign(bits):     return (bits >> 31) & 1
def _exp(bits):      return (bits >> 23) & 0xFF
def _mant(bits):     return bits & 0x7FFFFF
def _is_neg(bits):   return bool(bits & 0x80000000)

POS_INF      = 0x7F800000
NEG_INF      = 0xFF800000
CONST_0P8363 = 0x3F560000
CONST_ONE    = 0x3F800000

def _bf16_to_fp32(bf16):
  return (bf16 & 0xFFFF) << 16

def _fp16_to_fp32(fp16):
  s = (fp16 >> 15) & 1
  e = (fp16 >> 10) & 0x1F
  m = fp16 & 0x3FF
  if e == 0:
    if m == 0: return s << 31
    while not (m & 0x400):  # denorm -> normalized FP32
      m <<= 1
      e -= 1
    e += 1
    m &= 0x3FF
    return (s << 31) | ((e + 112) << 23) | (m << 13)
  if e == 0x1F:
    return (s << 31) | (0xFF << 23) | (m << 13)
  return (s << 31) | ((e + 112) << 23) | (m << 13)


class SFPU:
  NUM_LREGS = 17
  NUM_LANES = 32

  def __init__(self, dest):
    self.dest = dest
    # LReg file: 17 registers x 32 lanes x 32 bits
    self.lregs = [[0] * self.NUM_LANES for _ in range(self.NUM_LREGS)]
    self.lane_flags = [False] * self.NUM_LANES  # per-lane condition flags
    self.flag_stack = []                        # stack for nested predication
    self.use_lane_flags = False                 # master predication enable
    for lane in range(self.NUM_LANES):
      self.lregs[8][lane] = POS_INF
      self.lregs[9][lane] = NEG_INF
      self.lregs[10][lane] = CONST_0P8363
      self.lregs[15][lane] = lane * 2  # TILEID
      self.lregs[16][lane] = CONST_ONE

  def _is_writable(self, idx):
    return 0 <= idx <= 7 or 11 <= idx <= 14

  def _lane_enabled(self, lane):
    return self.lane_flags[lane] if self.use_lane_flags else True

  def _lanes(self):
    for lane in range(self.NUM_LANES):
      if self._lane_enabled(lane):
        yield lane

  # ── Data movement: Dest <-> LReg ─────────────────────────────────────

  def sfpload(self, d, rwc):
    if not self._is_writable(d.lreg_ind): return
    base = (d.dest_reg_addr + rwc.d * 16) % self.dest.ROWS
    for lane in self._lanes():
      row = (base + lane // 16) % self.dest.ROWS
      col = lane % 16
      val = self.dest.bits[row][col] if self.dest.valid[row] else 0
      self.lregs[d.lreg_ind][lane] = val & M32

  def sfploadi(self, d):
    if not self._is_writable(d.lreg_ind): return
    for lane in self._lanes():
      match d.instr_mod0:
        case 0:  val = _bf16_to_fp32(d.imm16)  # BF16 -> FP32
        case 2:  val = _fp16_to_fp32(d.imm16)  # FP16 -> FP32
        case 4:  val = d.imm16                 # U16
        case 6:                                # S15 — sign-extend bit 14
          v = d.imm16 & 0x7FFF
          val = v | 0xFFFF8000 if v & 0x4000 else v
        case 8:  val = (self.lregs[d.lreg_ind][lane] & 0xFFFF) | (d.imm16 << 16)
        case 10: val = (self.lregs[d.lreg_ind][lane] & 0xFFFF0000) | d.imm16
        case _:  val = d.imm16
      self.lregs[d.lreg_ind][lane] = val & M32

  def sfpstore(self, d, rwc):
    base = (d.dest_reg_addr + rwc.d * 16) % self.dest.ROWS
    for lane in self._lanes():
      row = (base + lane // 16) % self.dest.ROWS
      col = lane % 16
      self.dest.bits[row][col] = self.lregs[d.lreg_ind][lane] & M32
      self.dest.valid[row] = True

  # ── FP32 FMA arithmetic (MAD sub-unit, 2-cycle) ─────────────────────

  def sfpmad(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    neg_c = (d.instr_mod1 >> 1) & 1
    for lane in self._lanes():
      a = _to_float(self.lregs[d.lreg_src_a][lane])
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      c = _to_float(self.lregs[d.lreg_src_c][lane])
      if neg_b: b = -b
      if neg_c: c = -c
      self.lregs[d.lreg_dest][lane] = _to_bits(a * b + c)

  def sfpadd(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    neg_c = (d.instr_mod1 >> 1) & 1
    for lane in self._lanes():
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      c = _to_float(self.lregs[d.lreg_src_c][lane])
      if neg_b: b = -b
      if neg_c: c = -c
      self.lregs[d.lreg_dest][lane] = _to_bits(b + c)

  def sfpmul(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    for lane in self._lanes():
      a = _to_float(self.lregs[d.lreg_src_a][lane])
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      if neg_b: b = -b
      self.lregs[d.lreg_dest][lane] = _to_bits(a * b)

  # ── FP32 immediate arithmetic ────────────────────────────────────────

  def sfpmuli(self, d):
    if not self._is_writable(d.lreg_dest): return
    imm = _to_float(_bf16_to_fp32(d.imm16_math))
    for lane in self._lanes():
      x = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(x * imm)

  def sfpaddi(self, d):
    if not self._is_writable(d.lreg_dest): return
    imm = _to_float(_bf16_to_fp32(d.imm16_math))
    for lane in self._lanes():
      x = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(x + imm)

  # ── FP utilities ─────────────────────────────────────────────────────

  def sfpexexp(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      exp = _exp(self.lregs[d.lreg_c][lane])
      if d.instr_mod1 & 1:  # debiased
        result = (exp - 127) & M32 if exp > 0 else 0
      else:
        result = exp
      self.lregs[d.lreg_dest][lane] = result

  def sfpexman(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      m = _mant(self.lregs[d.lreg_c][lane])
      if not (d.imm12_math & 2): m |= 0x800000  # add implicit 1
      self.lregs[d.lreg_dest][lane] = m

  def sfpsetexp(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      new_exp = (d.imm12_math & 0xFF) if d.instr_mod1 & 1 else (self.lregs[d.lreg_dest][lane] & 0xFF)
      self.lregs[d.lreg_dest][lane] = (_sign(c) << 31) | (new_exp << 23) | _mant(c)

  def sfpdivp2(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      if d.instr_mod1 & 1:  # set exponent directly
        new_exp = d.imm12_math & 0xFF
      else:                 # add to exponent
        exp_add = d.imm12_math & 0xFF
        if d.imm12_math & 0x800: exp_add -= 256  # sign-extend
        new_exp = max(0, min(255, _exp(c) + exp_add))
      self.lregs[d.lreg_dest][lane] = (_sign(c) << 31) | (new_exp << 23) | _mant(c)

  def sfpabs(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_c][lane] & 0x7FFFFFFF

  def sfpsetsgn(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1:
        case 0: self.lregs[d.lreg_dest][lane] = c & 0x7FFFFFFF
        case 1: self.lregs[d.lreg_dest][lane] = c | 0x80000000
        case 2:
          d_sign = self.lregs[d.lreg_dest][lane] & 0x80000000
          self.lregs[d.lreg_dest][lane] = d_sign | (c & 0x7FFFFFFF)
        case _: self.lregs[d.lreg_dest][lane] = c

  # ── Integer arithmetic ───────────────────────────────────────────────

  def sfpiadd(self, d):
    if not self._is_writable(d.lreg_dest): return
    use_imm = d.instr_mod1 & 1
    negate = (d.instr_mod1 >> 1) & 1
    set_cc = (d.instr_mod1 >> 2) & 1
    # Sign-extend 12-bit immediate
    imm = d.imm12_math if not (d.imm12_math & 0x800) else (d.imm12_math | 0xFFFFF000)
    imm &= M32
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      b = imm if use_imm else self.lregs[d.lreg_dest][lane]
      result = ((c - b) if negate else (c + b)) & M32
      self.lregs[d.lreg_dest][lane] = result
      if set_cc: self.lane_flags[lane] = bool(result & 0x80000000)

  def sfpmul24(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      a = self.lregs[d.lreg_src_a][lane] & 0xFFFFFF
      b = self.lregs[d.lreg_src_b][lane] & 0xFFFFFF
      self.lregs[d.lreg_dest][lane] = (a * b) & M32

  # ── Bit manipulation ─────────────────────────────────────────────────

  def sfpand(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] &= self.lregs[d.lreg_c][lane]

  def sfpor(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] |= self.lregs[d.lreg_c][lane]

  def sfpnot(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = (~self.lregs[d.lreg_c][lane]) & M32

  def sfpxor(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = (self.lregs[d.lreg_dest][lane] ^ self.lregs[d.lreg_c][lane]) & M32

  def sfplz(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      val = self.lregs[d.lreg_c][lane]
      self.lregs[d.lreg_dest][lane] = 32 if val == 0 else 31 - val.bit_length() + 1

  # ── Shifts ───────────────────────────────────────────────────────────

  def sfpshft(self, d):
    if not self._is_writable(d.lreg_dest): return
    shift = d.imm12_math & 0x1F
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1:
        case 0: result = (c << shift) & M32        # logical left
        case 1: result = c >> shift                # logical right
        case 2:                                    # arithmetic right
          if c & 0x80000000:
            result = ((c >> shift) | (M32 << (32 - shift))) & M32
          else:
            result = c >> shift
        case _: result = c
      self.lregs[d.lreg_dest][lane] = result

  def sfpshft2(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      b = self.lregs[d.lreg_dest][lane]
      shift = self.lregs[d.lreg_c][lane] & 0x1F
      if d.instr_mod1 == 0:
        self.lregs[d.lreg_dest][lane] = (b << shift) & M32
      else:
        self.lregs[d.lreg_dest][lane] = b >> shift

  # ── Comparison / predication ─────────────────────────────────────────

  def sfpsetcc(self, d):
    for lane in range(self.NUM_LANES):
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1 & 3:
        case 0: self.lane_flags[lane] = _is_neg(c)
        case 1: self.lane_flags[lane] = (c & 0x7FFFFFFF) != 0
        case 2: self.lane_flags[lane] = not _is_neg(c)
        case 3: self.lane_flags[lane] = (c & 0x7FFFFFFF) == 0

  def sfpgt(self, d):
    for lane in range(self.NUM_LANES):
      vd = _to_float(self.lregs[d.lreg_dest][lane])
      vc = _to_float(self.lregs[d.lreg_c][lane])
      self.lane_flags[lane] = vd > vc

  def sfpencc(self, d):
    if d.instr_mod1 == 0:
      self.use_lane_flags = False
    else:
      self.use_lane_flags = True
      if d.instr_mod1 == 1:   self.lane_flags = [True] * self.NUM_LANES
      elif d.instr_mod1 == 2: self.lane_flags = [False] * self.NUM_LANES

  def sfppushc(self, d): self.flag_stack.append(list(self.lane_flags))
  def sfppopc(self, d):
    if self.flag_stack: self.lane_flags = self.flag_stack.pop()
  def sfpcompc(self, d): self.lane_flags = [not f for f in self.lane_flags]

  # ── Move ─────────────────────────────────────────────────────────────

  def sfpmov(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      if d.instr_mod1 == 1: c ^= 0x80000000  # flip sign
      self.lregs[d.lreg_dest][lane] = c

  # ── Type conversion / rounding ───────────────────────────────────────

  def sfpstochrnd(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_src_c][lane]

  def sfpcast(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_src_c][lane]

  # ── Configuration ────────────────────────────────────────────────────

  def sfpconfig(self, d):
    if 11 <= d.config_dest <= 14:
      val = _bf16_to_fp32(d.imm16_math)
      for lane in range(self.NUM_LANES):
        self.lregs[d.config_dest][lane] = val

  # ── Approximate reciprocal ──────────────────────────────────────────

  def sfparecip(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c_bits = self.lregs[d.lreg_c][lane]
      c = _to_float(c_bits)
      if c == 0.0:
        self.lregs[d.lreg_dest][lane] = POS_INF if not _is_neg(c_bits) else NEG_INF
      elif math.isinf(c):
        self.lregs[d.lreg_dest][lane] = 0x80000000 if _is_neg(c_bits) else 0
      else:
        self.lregs[d.lreg_dest][lane] = _to_bits(1.0 / c)

  # ── LUT ──────────────────────────────────────────────────────────────

  def sfplutfp32(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      x = _to_float(self.lregs[3][lane])
      abs_x = abs(x)
      i = 0 if abs_x < 1.0 else (1 if abs_x < 2.0 else 2)
      slope = _to_float(self.lregs[i][lane])
      intercept = _to_float(self.lregs[4 + i][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(slope * abs_x + intercept)

  # ── Swap ─────────────────────────────────────────────────────────────

  def sfpswap(self, d):
    if not (self._is_writable(d.lreg_dest) and self._is_writable(d.lreg_c)): return
    for lane in self._lanes():
      c = _to_float(self.lregs[d.lreg_c][lane])
      vd = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(min(c, vd))
      self.lregs[d.lreg_c][lane] = _to_bits(max(c, vd))


# =============================================================================
# TensixCoprocessor — aggregates all the above; steps 3 threads per cycle.
# =============================================================================

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
    rwc = self.rwc[thread.id]
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
      case 'ADDDMAREG':    self.scalar.execute_adddmareg(d, thread.id)
      case 'MULDMAREG':    self.scalar.execute_muldmareg(d, thread.id)
      case 'BITWOPDMAREG': self.scalar.execute_bitwopdmareg(d, thread.id)
      case 'SHIFTDMAREG':  self.scalar.execute_shiftdmareg(d, thread.id)
      case 'CMPDMAREG':    self.scalar.execute_cmpdmareg(d, thread.id)
      # FLUSHDMA: in synchronous emulation the pipeline conditions (C0-C3)
      # are always idle, so the wait is a no-op. Kept as a named dispatch so
      # decode_tensix resolves to 'FLUSHDMA' rather than UNKNOWN_0x46.
      case 'FLUSHDMA':     pass
      # ADC (any thread can issue)
      case 'SETADC':   adc.execute_setadc(d)
      case 'SETADCXY': adc.execute_setadcxy(d)
      case 'SETADCZW': adc.execute_setadczw(d)
      case 'INCADCZW': adc.execute_incadczw(d)
      case 'SETADCXX': adc.execute_setadcxx(d)
      # TRISC0 — unpack
      case 'UNPACR':
        if d.SetDatValid:
          (self.srca if d.Unpack_block_selection == 0 else self.srcb).flip_to_fpu()
      case 'UNPACR_NOP':
        if d.Set_Dvalid & 1:
          (self.srca if d.Unpacker_Select == 0 else self.srcb).flip_to_fpu()
        clr = d.Src_ClrVal_Ctrl
        if clr & 1: _clear_src_bank(self.srca)
        if clr & 2: _clear_src_bank(self.srcb)
      # TRISC1 — FPU / SFPU / RWC
      case 'ZEROACC':     self.fpu.zeroacc(d)
      case 'ZEROSRC':     self.fpu.zerosrc(d)
      case 'MOVB2D':      self.fpu.movb2d(d, rwc)
      case 'TRNSPSRCB':   self.fpu.trnspsrcb(d)
      case 'MVMUL':       self.fpu.mvmul(d, rwc)
      case 'ELWADD':      self.fpu.elwadd(d, rwc)
      case 'GMPOOL':      self.fpu.gmpool(d, rwc)
      case 'CLEARDVALID': self.fpu.cleardvalid(d)
      case 'MOVD2A':      self.fpu.movd2a(d, rwc)
      case 'MOVD2B':      self.fpu.movd2b(d, rwc)
      case 'SETRWC':
        clear_ab = rwc.execute_setrwc(d)
        if clear_ab & 1: self.srca.release_from_fpu()
        if clear_ab & 2: self.srcb.release_from_fpu()
      case 'INCRWC':      rwc.execute_incrwc(d)
      case 'SFPLOAD':     self.sfpu.sfpload(d, rwc)
      case 'SFPLOADI':    self.sfpu.sfploadi(d)
      case 'SFPSTORE':    self.sfpu.sfpstore(d, rwc)
      case 'SFPMULI':     self.sfpu.sfpmuli(d)
      case 'SFPADDI':     self.sfpu.sfpaddi(d)
      case 'SFPDIVP2':    self.sfpu.sfpdivp2(d)
      case 'SFPEXEXP':    self.sfpu.sfpexexp(d)
      case 'SFPEXMAN':    self.sfpu.sfpexman(d)
      case 'SFPSETEXP':   self.sfpu.sfpsetexp(d)
      case 'SFPIADD':     self.sfpu.sfpiadd(d)
      case 'SFPMUL24':    self.sfpu.sfpmul24(d)
      case 'SFPSHFT':     self.sfpu.sfpshft(d)
      case 'SFPSHFT2':    self.sfpu.sfpshft2(d)
      case 'SFPSETCC':    self.sfpu.sfpsetcc(d)
      case 'SFPGT':       self.sfpu.sfpgt(d)
      case 'SFPMOV':      self.sfpu.sfpmov(d)
      case 'SFPABS':      self.sfpu.sfpabs(d)
      case 'SFPSETSGN':   self.sfpu.sfpsetsgn(d)
      case 'SFPAND':      self.sfpu.sfpand(d)
      case 'SFPOR':       self.sfpu.sfpor(d)
      case 'SFPNOT':      self.sfpu.sfpnot(d)
      case 'SFPLZ':       self.sfpu.sfplz(d)
      case 'SFPXOR':      self.sfpu.sfpxor(d)
      case 'SFPMAD':      self.sfpu.sfpmad(d)
      case 'SFPADD':      self.sfpu.sfpadd(d)
      case 'SFPMUL':      self.sfpu.sfpmul(d)
      case 'SFPPUSHC':    self.sfpu.sfppushc(d)
      case 'SFPPOPC':     self.sfpu.sfppopc(d)
      case 'SFPENCC':     self.sfpu.sfpencc(d)
      case 'SFPCOMPC':    self.sfpu.sfpcompc(d)
      case 'SFPSTOCHRND': self.sfpu.sfpstochrnd(d)
      case 'SFPCAST':     self.sfpu.sfpcast(d)
      case 'SFPCONFIG':   self.sfpu.sfpconfig(d)
      case 'SFPSWAP':     self.sfpu.sfpswap(d)
      case 'SFPLOADMACRO':self.sfpu.sfpload(d, rwc)
      case 'SFPLUTFP32':  self.sfpu.sfplutfp32(d)
      case 'SFPARECIP':   self.sfpu.sfparecip(d)
      case 'SFPNOP':      pass
      # TRISC2 — pack. Functional emulation only; no actual pack path
      # (would read Dest, format-convert, write to L1 with edge mask/ReLU).
      case 'PACR': pass
      # Unknown opcodes: no-op (for functional emulation).
      case _: pass

  def _hw_state(self):
    return HardwareState(self.semaphores, self.srca, self.srcb)

  def write_mop_cfg(self, thread_id, reg_index, value):
    if 0 <= reg_index < 9:
      self.threads[thread_id].mop.cfg[reg_index] = value

  def read_pcbuf(self, thread_id, offset):
    # Resolves immediately in functional emulation (synchronous dispatch).
    return 0


def _clear_src_bank(srcregfile):
  bank = srcregfile.banks[srcregfile.unpack_bank]
  for r in range(64):
    for c in range(16):
      bank.rows[r][c] = 0


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
