# =============================================================================
# Per-thread instruction frontend — FIFO, MOP expander, Replay expander, and
# the WaitGate that holds a thread back while a STALLWAIT/SEMWAIT latch is
# active. One TensixThread exists per TRISC (T0/T1/T2); each has its own
# pipeline but all feed a shared backend (FPU/SFPU/ThCon/Sync).
# =============================================================================

from collections import deque

M32 = 0xFFFFFFFF


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


# =============================================================================
# Block / wait masks — consulted by WaitGate
# =============================================================================

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
  for op in (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7):  # Sync unit (B1)
    _OPCODE_BLOCK_BITS[op] = STALL_SYNC
  for op in (0x42, 0x43):                                # Unpack (B3)
    _OPCODE_BLOCK_BITS[op] = STALL_UNPACK
  for op in (0x08, 0x0A, 0x10, 0x11, 0x12, 0x13, 0x16, 0x17, 0x18, 0x21, 0x26,
             0x27, 0x28, 0x29, 0x30, 0x33, 0x34, 0x35, 0x36, 0x37,
             0x38):  # FPU / Matrix Unit (B6)
    _OPCODE_BLOCK_BITS[op] = STALL_MATH
  for op in (0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB7, 0xB8):  # Config unit (B7)
    _OPCODE_BLOCK_BITS[op] = STALL_CFG
  for op in (0x45, 0x48, 0x58, 0x5A, 0x5B, 0x5C, 0x5D, 0x60):  # Scalar/ThCon (B5), also B0
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

  def install_streamwait(self, block_mask, target_value, target_sel, stream_sel):
    if block_mask == 0: block_mask = STALL_MATH
    self.opcode = "STREAMWAIT"
    self.block_mask = block_mask
    self.cond_mask = 1 << (target_sel & 1)
    self.sem_mask = 0
    self.sem_cond = 0
    self.target_value = target_value & M32
    self.stream_sel = stream_sel & 3
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
    bits = _instruction_block_bits(word)
    if bits == STALL_THREAD:
      if self.block_mask == STALL_THREAD:
        return True
      unpack_clear = (1 << 5) | (1 << 6)
      return self.block_mask == STALL_UNPACK and bool(self.cond_mask & unpack_clear)
    return bool(bits & self.block_mask)

  def _evaluate(self, hw, thread_id):
    if self.opcode == "STALLWAIT": return self._eval_stallwait(hw, thread_id)
    if self.opcode == "SEMWAIT":   return self._eval_semwait(hw)
    if self.opcode == "STREAMWAIT": return False
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
