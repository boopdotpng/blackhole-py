from .memory import (
  Memory,
  STREAM_BASE, STREAM_END, STREAM_STRIDE,
  STREAM_TILES_ACKED, STREAM_TILES_RECEIVED, STREAM_SYNC_REG,
  STREAM_DISPATCH_REG, STREAM_DISPATCH_ID, CB_STREAM_ID_OFFSET,
  NIU_CMD_BUF_STRIDE, NIU_TARG_ADDR_LO, NIU_TARG_ADDR_MID,
  NIU_TARG_ADDR_HI, NIU_RET_ADDR_LO, NIU_RET_ADDR_MID, NIU_RET_ADDR_HI,
  NIU_CTRL, NIU_AT_LEN_BE, NIU_AT_DATA, NIU_CMD_CTRL, NIU_NODE_ID,
  NIU_ID_LOGICAL, NIU_CMD_BUF_AVAIL,
  NIU_L1_ACC_AT_INSTRN,
  NIU_MST_ATOMIC_RESP_RECEIVED, NIU_MST_WR_ACK_RECEIVED,
  NIU_MST_RD_RESP_RECEIVED, NIU_MST_NONPOSTED_WR_REQ_SENT,
  NIU_MST_POSTED_WR_REQ_SENT, NIU_MST_RD_REQ_SENT,
  NOC_CTRL_AT, NOC_CTRL_WR, NOC_CTRL_WR_INLINE,
  NOC_CTRL_RESP_MARKED, NOC_CTRL_BRCST, NOC_CTRL_BRCST_SRC_INCLUDE,
  NOC_CTRL_L1_ACC_AT_EN,
  NOC0_BASE, NOC1_BASE,
)

import math
import struct

M32 = 0xFFFFFFFF
M16 = 0xFFFF
M8  = 0xFF

# Atomic operation opcodes (NOC_AT_LEN_BE bits [15:12])
AT_NOP          = 0x0
AT_INCR_GET     = 0x1
AT_INCR_GET_PTR = 0x2
AT_SWAP         = 0x3
AT_CAS          = 0x4
AT_GET_TILE_MAP = 0x5
AT_STORE_IND    = 0x6
AT_SWAP_4B      = 0x7
AT_ACC          = 0x9

# ACC format codes (NOC_L1_ACC_AT_INSTRN bits [2:0])
ACC_FP32       = 0
ACC_FP16_A     = 1
ACC_FP16_B     = 2  # BFloat16
ACC_INT32      = 3
ACC_INT32_SAT  = 4  # two's complement with saturation
ACC_INT32_UNS  = 5  # unsigned
ACC_INT8       = 6


def noc_key(x, y):
  return (y << 6) | x


# Stream / NOC overlay registers — [0xFFB40000, 0xFFB7FFFF)
#
# Real hardware: 64 "streams" per tile, each a 4 KiB register page driving
# the NOC overlay engine (source/dest buffers, phase pointer, credits — an
# autonomous DMA that can move tiles without RISC-V in the data path).
# tt-metal doesn't use the overlay; it repurposes four slots as plain MMIO
# that every RISC on the tile can see, and that remote tiles can hit with
# NOC atomic increments.  Only these slots matter for kernel execution:
#
#   stream N, reg 8  (+0x020) — tiles_acked   (cb_pop_front target)
#   stream N, reg 10 (+0x028) — tiles_received (cb_push_back target)
#       CB sync is just (received - acked) in uint16 modular arithmetic.
#   stream 0, reg 31 (+0x07C)     — get_sync_register_ptr (BRISC/NCRISC)
#   stream 48, reg 270 (@ 0xFFB70438) — DISPATCH_MESSAGE_ADDR; go_msg
#       dispatch_message_offset picks stream (48+k)/reg 270.
#
# CB N maps directly to stream N (OPERAND_START_STREAM = 0 in stream_io_map.h;
# trisc.cc:init_sync_registers iterates from stream 0 via get_operand_stream_id).
# fw_brisc.S pins s11 to 0xffb70438 across the main loop.
#
# A sparse Memory suffices as the backing store — reads of untouched regs
# return 0, writes stick, atomic increments (via NOC) land the same as any
# other write.  No overlay semantics are emulated; firmware doesn't depend
# on any.  The tile wires one StreamRegisters onto both the local RISC-V
# bus (at STREAM_BASE..STREAM_END) and the NOC network entry, so local
# loads/stores and remote NOC atomic updates see the same state.
class StreamRegisters(Memory):
  pass


class NOC:
  def __init__(self, noc_id, l1, network, x, y):
    self.noc_id = noc_id
    self.base = NOC0_BASE if noc_id == 0 else NOC1_BASE
    self.regs = Memory()    # per-NOC register file (shared by all 5 cores on this tile)
    self.l1 = l1            # Memory — shared tile L1
    self.network = network  # dict[int, Memory] — shared routing table for this physical NOC
    self.x = x
    self.y = y

  def pre_populate(self):
    xy = noc_key(self.x, self.y)
    self.regs.write32(NIU_ID_LOGICAL, xy)
    for buf in range(4):
      self.regs.write32(buf * NIU_CMD_BUF_STRIDE + NIU_NODE_ID, xy)
    self.regs.write32(NIU_CMD_BUF_AVAIL, 0x1F1F1F1F)

  # -- router handler API ----------------------------------------------------
  # The tile router dispatches accesses in [base, base + 64KiB) to these.

  def read8(self, addr):  return self.regs.read8(addr - self.base)
  def read16(self, addr): return self.regs.read16(addr - self.base)
  def read32(self, addr): return self.regs.read32(addr - self.base)

  def write8(self, addr, val):  self.regs.write8(addr - self.base, val)
  def write16(self, addr, val): self.regs.write16(addr - self.base, val)

  def write32(self, addr, val):
    off = addr - self.base
    self.regs.write32(off, val)
    # Writing 1 to a buffer's CMD_CTRL fires the command.
    if (off & 0x7FF) == NIU_CMD_CTRL and val == 1:
      self._fire(off >> 11)   # 0x800 stride → buffer index

  def _reg(self, buf_idx, offset):
    return self.regs.read32(buf_idx * NIU_CMD_BUF_STRIDE + offset)

  def _inc_counter(self, addr):
    val = self.regs.read32(addr)
    self.regs.write32(addr, (val + 1) & M32)

  # -- coordinate decoding ---------------------------------------------------

  @staticmethod
  def _unicast_xy(raw):
    return raw & 0x3F, (raw >> 6) & 0x3F

  @staticmethod
  def _mcast_rect(raw):
    return ((raw >> 12) & 0x3F, (raw >> 18) & 0x3F,
        raw & 0x3F, (raw >> 6) & 0x3F)

  def _atomic_targets(self, xy, is_mcast, mcast_src_include):
    if not is_mcast:
      return [self._unicast_xy(xy)]
    sx, sy, ex, ey = self._mcast_rect(xy)
    targets = []
    for y in range(sy, ey + 1):
      for x in range(sx, ex + 1):
        if not mcast_src_include and x == self.x and y == self.y:
          continue
        targets.append((x, y))
    return targets

  # -- network helpers -------------------------------------------------------

  def _net_read(self, x, y, addr, length):
    mem = self.network[noc_key(x, y)]
    return bytes(mem.read8(addr + i) for i in range(length))

  def _net_write(self, x, y, addr, data):
    mem = self.network[noc_key(x, y)]
    for i, b in enumerate(data):
      mem.write8(addr + i, b)

  # -- transaction execution -------------------------------------------------

  def _fire(self, buf_idx):
    ctrl = self._reg(buf_idx, NIU_CTRL)

    is_at     = bool(ctrl & NOC_CTRL_AT)
    is_wr     = bool(ctrl & NOC_CTRL_WR)
    is_inline = bool(ctrl & NOC_CTRL_WR_INLINE)
    is_resp   = bool(ctrl & NOC_CTRL_RESP_MARKED)
    is_mcast  = bool(ctrl & NOC_CTRL_BRCST)
    mcast_src_include = bool(ctrl & NOC_CTRL_BRCST_SRC_INCLUDE)

    targ_lo  = self._reg(buf_idx, NIU_TARG_ADDR_LO)
    targ_mid = self._reg(buf_idx, NIU_TARG_ADDR_MID)
    targ_xy  = self._reg(buf_idx, NIU_TARG_ADDR_HI)
    ret_lo   = self._reg(buf_idx, NIU_RET_ADDR_LO)
    ret_mid  = self._reg(buf_idx, NIU_RET_ADDR_MID)
    ret_xy   = self._reg(buf_idx, NIU_RET_ADDR_HI)
    length   = self._reg(buf_idx, NIU_AT_LEN_BE)
    at_data  = self._reg(buf_idx, NIU_AT_DATA)

    targ_addr = targ_lo | ((targ_mid & 0xF) << 32)
    ret_addr  = ret_lo  | ((ret_mid  & 0xF) << 32)

    # Clear CMD_CTRL (signals "ready" to firmware)
    self.regs.write32(buf_idx * NIU_CMD_BUF_STRIDE + NIU_CMD_CTRL, 0)

    if is_at:
      l1_acc_at_en = bool(ctrl & NOC_CTRL_L1_ACC_AT_EN)
      l1_acc_instrn = self._reg(buf_idx, NIU_L1_ACC_AT_INSTRN) if l1_acc_at_en else 0
      for tx, ty in self._atomic_targets(targ_xy, is_mcast, mcast_src_include):
        self._exec_atomic(noc_key(tx, ty), targ_addr, ret_addr, length, at_data,
                 l1_acc_at_en, l1_acc_instrn, is_resp)
    elif is_wr:
      if is_inline:
        self._exec_inline_write(targ_xy, targ_addr, at_data,
                    is_mcast, is_resp, mcast_src_include)
      else:
        self._exec_write(targ_addr, ret_xy, ret_addr, length,
                is_mcast, is_resp, mcast_src_include)
    else:
      self._exec_read(targ_xy, targ_addr, ret_addr, length)

  def _exec_read(self, targ_xy, src_addr, dst_addr, length):
    sx, sy = self._unicast_xy(targ_xy)
    data = self._net_read(sx, sy, src_addr, length)
    for i, b in enumerate(data):
      self.l1.write8(dst_addr + i, b)
    self._inc_counter(NIU_MST_RD_RESP_RECEIVED)
    self._inc_counter(NIU_MST_RD_REQ_SENT)

  def _write_targets(self, xy, is_mcast, mcast_src_include, dst_addr, data):
    count = 0
    if is_mcast:
      sx, sy, ex, ey = self._mcast_rect(xy)
      for y in range(sy, ey + 1):
        for x in range(sx, ex + 1):
          if not mcast_src_include and x == self.x and y == self.y:
            continue
          self._net_write(x, y, dst_addr, data)
          count += 1
    else:
      dx, dy = self._unicast_xy(xy)
      self._net_write(dx, dy, dst_addr, data)
      count = 1
    return count

  def _inc_write_counters(self, is_resp, ack_count=1):
    if is_resp:
      for _ in range(ack_count):
        self._inc_counter(NIU_MST_WR_ACK_RECEIVED)
      self._inc_counter(NIU_MST_NONPOSTED_WR_REQ_SENT)
    else:
      self._inc_counter(NIU_MST_POSTED_WR_REQ_SENT)

  def _exec_write(self, src_addr, ret_xy, dst_addr, length,
          is_mcast, is_resp, mcast_src_include=True):
    data = bytes(self.l1.read8(src_addr + i) for i in range(length))
    ack_count = self._write_targets(ret_xy, is_mcast, mcast_src_include, dst_addr, data)
    self._inc_write_counters(is_resp, ack_count)

  def _exec_inline_write(self, targ_xy, dst_addr, data_word,
             is_mcast, is_resp, mcast_src_include=True):
    data = struct.pack("<I", data_word)
    ack_count = self._write_targets(targ_xy, is_mcast, mcast_src_include, dst_addr, data)
    self._inc_write_counters(is_resp, ack_count)

  # -- accumulate helpers ----------------------------------------------------

  @staticmethod
  def _bf16_to_f32(bits):
    return struct.unpack('<f', struct.pack('<I', (bits & M16) << 16))[0]

  @staticmethod
  def _f32_to_bf16(val):
    bits = struct.unpack('<I', struct.pack('<f', val))[0]
    rounding = 0x7FFF + ((bits >> 16) & 1)
    bits = (bits + rounding) & 0xFFFFFFFF
    return (bits >> 16) & M16

  @staticmethod
  def _to_signed32(val):
    val &= M32
    return val - 0x100000000 if val >= 0x80000000 else val

  @staticmethod
  def _to_signed8(val):
    val &= M8
    return val - 0x100 if val >= 0x80 else val

  @staticmethod
  def _pack_f32(val, sat_dis=False):
    FP32_MAX = 3.4028235e+38
    if not sat_dis and (math.isinf(val) or abs(val) > FP32_MAX):
      val = math.copysign(FP32_MAX, val)
    bits = struct.unpack('<I', struct.pack('<f', val))[0]
    if (bits & 0x7F800000) == 0 and (bits & 0x007FFFFF):
      bits &= 0x80000000
    return bits

  def _acc_compute(self, mem, addr, at_data, acc_fmt, sat_dis):
    base = addr & ~0xF
    match acc_fmt:
      case 0:  # FP32
        b = struct.unpack('<f', struct.pack('<I', at_data & M32))[0]
        for lane in range(4):
          lane_addr = base + lane * 4
          a = struct.unpack('<f', struct.pack('<I', mem.read32(lane_addr)))[0]
          mem.write32(lane_addr, self._pack_f32(a + b, sat_dis))

      case 1:  # FP16_A (IEEE half)
        b = [
          struct.unpack('<e', struct.pack('<H', at_data & M16))[0],
          struct.unpack('<e', struct.pack('<H', (at_data >> 16) & M16))[0],
        ]
        for lane in range(8):
          lane_addr = base + lane * 2
          a = struct.unpack('<e', struct.pack('<H', mem.read16(lane_addr)))[0]
          result = a + b[lane & 1]
          if not sat_dis and math.isinf(result):
            result = math.copysign(65504.0, result)
          mem.write16(lane_addr, struct.unpack('<H', struct.pack('<e', result))[0])

      case 2:  # FP16_B (BFloat16)
        b = [self._bf16_to_f32(at_data & M16),
             self._bf16_to_f32((at_data >> 16) & M16)]
        for lane in range(8):
          lane_addr = base + lane * 2
          a = self._bf16_to_f32(mem.read16(lane_addr))
          result = a + b[lane & 1]
          if not sat_dis and math.isinf(result):
            result = math.copysign(3.4028235e+38, result)
          mem.write16(lane_addr, self._f32_to_bf16(result))

      case 3:  # INT32 (signed)
        a = self._to_signed32(mem.read32(addr))
        b = self._to_signed32(at_data)
        result = a + b
        if not sat_dis:
          result = max(-0x80000000, min(0x7FFFFFFF, result))
        mem.write32(addr, result & M32)

      case 4:  # INT32 wrapping lanes
        b = at_data & M32
        for lane in range(4):
          lane_addr = base + lane * 4
          mem.write32(lane_addr, (mem.read32(lane_addr) + b) & M32)

      case 5:  # INT32_UNS (unsigned)
        a = mem.read32(addr)
        result = a + (at_data & M32)
        if not sat_dis:
          result = min(result, M32)
        mem.write32(addr, result & M32)

      case 6:  # INT8 (4 packed signed bytes)
        old = mem.read32(addr)
        result = 0
        for i in range(4):
          a = self._to_signed8((old >> (i * 8)) & M8)
          b = self._to_signed8((at_data >> (i * 8)) & M8)
          s = a + b
          if not sat_dis:
            s = max(-128, min(127, s))
          result |= (s & M8) << (i * 8)
        mem.write32(addr, result)

      case 7:  # UINT8 saturating lanes
        for lane in range(16):
          lane_addr = base + lane
          a = mem.read8(lane_addr)
          b = (at_data >> ((lane & 3) * 8)) & M8
          result = a + b
          if not sat_dis:
            result = min(result, M8)
          mem.write8(lane_addr, result & M8)

  # -- atomic execution ------------------------------------------------------

  def _exec_atomic(self, targ_xy, targ_addr, ret_addr, at_len_be, at_data,
          l1_acc_at_en=False, l1_acc_instrn=0, is_resp=True):
    tx, ty = self._unicast_xy(targ_xy)
    target_mem = self.network[noc_key(tx, ty)]

    opcode = ((l1_acc_instrn >> 12) & 0xF) if l1_acc_at_en else ((at_len_be >> 12) & 0xF)
    acc_addr = targ_addr & ~0xF
    old_val = target_mem.read32(acc_addr if opcode == 0x9 else targ_addr)

    match opcode:
      case 0x0:  # NOP
        pass

      case 0x1:  # INCR_GET
        target_mem.write32(targ_addr, (old_val + at_data) & M32)

      case 0x2:  # INCR_GET_PTR
        incr = (at_len_be >> 6) & 0xF
        if incr == 0:
          incr = 1
        wrap = (at_len_be >> 2) & 0xF
        new_val = old_val + incr
        if wrap > 0 and new_val >= wrap:
          new_val = 0
        target_mem.write32(targ_addr, new_val & M32)

      case 0x3:  # SWAP
        base = targ_addr & ~0xF
        mask = (at_len_be >> 4) & 0xFF
        for lane in range(8):
          if (mask >> lane) & 1:
            value = (at_data >> ((lane & 1) * 16)) & M16
            target_mem.write16(base + lane * 2, value)

      case 0x7:  # SWAP_4B
        target_mem.write32(targ_addr, at_data & M32)

      case 0x4:  # CAS
        compare = at_data & 0xFFFF
        swap_val = (at_data >> 16) & 0xFFFF
        if (old_val & 0xFFFF) == compare:
          target_mem.write32(targ_addr, (old_val & 0xFFFF0000) | swap_val)

      case 0x5:  # GET_TILE_MAP
        pass

      case 0x6:  # STORE_IND
        target_mem.write32(old_val, at_data & M32)

      case 0x9:  # ACC
        acc_fmt = l1_acc_instrn & 0x7 if l1_acc_at_en else 0
        sat_dis = bool((l1_acc_instrn >> 3) & 1) if l1_acc_at_en else False
        self._acc_compute(target_mem, targ_addr, at_data, acc_fmt, sat_dis)

    if is_resp:
      self.l1.write32(ret_addr, old_val)
      self._inc_counter(NIU_MST_ATOMIC_RESP_RECEIVED)
