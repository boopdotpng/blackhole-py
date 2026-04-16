import struct

from emu.memory import Memory
from emu.core import BRISC
from emu.noc import (NOC, noc_key,
          AT_INCR_GET_PTR, AT_SWAP_4B, AT_STORE_IND,
          AT_GET_TILE_MAP, AT_ACC,
          ACC_FP32, ACC_FP16_A, ACC_FP16_B, ACC_INT32,
          ACC_INT32_SAT, ACC_INT32_UNS, ACC_INT8)
from emu import memory as M

# -- helpers -------------------------------------------------------------------

def make_tile(network, x, y):
  l1 = Memory()
  core = BRISC(l1=l1)
  network[noc_key(x, y)] = l1
  noc0 = NOC(0, l1, network, x, y)
  noc1 = NOC(1, l1, network, x, y)
  noc0.pre_populate()
  noc1.pre_populate()
  core.mem.default = Memory()
  core.mem.register(M.NOC0_BASE, M.NOC0_BASE + M.NOC_SIZE - 1, noc0)
  core.mem.register(M.NOC1_BASE, M.NOC1_BASE + M.NOC_SIZE - 1, noc1)
  return core, l1, noc0, noc1


def program_write(regs, buf, src_addr, dst_x, dst_y, dst_addr, length,
         resp_marked=True):
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, src_addr)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (dst_y << 6) | dst_x)
  regs.write32(base + M.NIU_RET_ADDR_LO, dst_addr)
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  regs.write32(base + M.NIU_RET_ADDR_HI, (dst_y << 6) | dst_x)
  regs.write32(base + M.NIU_AT_LEN_BE, length)
  ctrl = M.NOC_CTRL_WR
  if resp_marked:
    ctrl |= M.NOC_CTRL_RESP_MARKED
  regs.write32(base + M.NIU_CTRL, ctrl)


def program_read(regs, buf, src_x, src_y, src_addr, dst_addr, length):
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, src_addr)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (src_y << 6) | src_x)
  regs.write32(base + M.NIU_RET_ADDR_LO, dst_addr)
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  regs.write32(base + M.NIU_AT_LEN_BE, length)
  regs.write32(base + M.NIU_CTRL, 0)  # read: AT=0, WR=0


# -- tests ---------------------------------------------------------------------

def test_pre_populate():
  network = {}
  m = Memory()
  network[noc_key(5, 7)] = m
  noc = NOC(0, m, network, 5, 7)
  noc.pre_populate()
  regs = noc.regs
  assert regs.read32(M.NIU_ID_LOGICAL) == (7 << 6) | 5
  for buf in range(4):
    assert regs.read32(buf * M.NIU_CMD_BUF_STRIDE + M.NIU_NODE_ID) == (7 << 6) | 5
  assert regs.read32(M.NIU_CMD_BUF_AVAIL) == 0x1F1F1F1F

def test_unicast_write():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  core_b, l1_b, _, _ = make_tile(network, 3, 4)

  # Write test data to tile A's L1
  l1_a.load(0x1000, b"\xDE\xAD\xBE\xEF\xCA\xFE\xBA\xBE")

  # Program NOC0 buf0 for a DMA write: A[0x1000] → B[0x2000], 8 bytes
  program_write(noc0_a.regs, buf=0,
         src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x2000, length=8)

  # Fire via core store to CMD_CTRL (routed through tile router to NOC)
  core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  # Verify data arrived at tile B
  assert l1_b.read32(0x2000) == 0xEFBEADDE
  assert l1_b.read32(0x2004) == 0xBEBAFECA

def test_unicast_write_counter():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, _, _, _ = make_tile(network, 3, 4)

  l1_a.write32(0x1000, 0x42)
  program_write(noc0_a.regs, buf=0,
         src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x2000, length=4,
         resp_marked=True)
  core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  regs = noc0_a.regs
  assert regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 1
  assert regs.read32(M.NIU_MST_NONPOSTED_WR_REQ_SENT) == 1

def test_unicast_write_posted():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, _, _, _ = make_tile(network, 3, 4)

  l1_a.write32(0x1000, 0x42)
  program_write(noc0_a.regs, buf=0,
         src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x2000, length=4,
         resp_marked=False)
  core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  regs = noc0_a.regs
  assert regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 0
  assert regs.read32(M.NIU_MST_POSTED_WR_REQ_SENT) == 1

def test_unicast_read():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Write data into tile B
  l1_b.load(0x5000, b"\x01\x02\x03\x04")

  # Program NOC0 buf1 for a read: B[0x5000] → A[0x6000], 4 bytes
  program_read(noc0_a.regs, buf=1,
        src_x=3, src_y=4, src_addr=0x5000, dst_addr=0x6000, length=4)
  core_a.mem.write32(M.NOC0_BASE + 1 * M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)

  assert l1_a.read32(0x6000) == 0x04030201
  assert noc0_a.regs.read32(M.NIU_MST_RD_RESP_RECEIVED) == 1

def test_inline_write():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  regs = noc0_a.regs
  buf = 2  # WR_REG_CMD_BUF
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, 0x7000)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (4 << 6) | 3)  # target = (3,4)
  regs.write32(base + M.NIU_AT_DATA, 0xDEADBEEF)
  regs.write32(base + M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_WR_INLINE | M.NOC_CTRL_RESP_MARKED)
  regs.write32(base + M.NIU_AT_LEN_BE, 4)

  core_a.mem.write32(M.NOC0_BASE + buf * M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)
  assert l1_b.read32(0x7000) == 0xDEADBEEF

def test_multicast_write():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_00, _, _ = make_tile(network, 5, 5)
  _, l1_01, _, _ = make_tile(network, 5, 6)
  _, l1_10, _, _ = make_tile(network, 6, 5)
  _, l1_11, _, _ = make_tile(network, 6, 6)

  l1_a.load(0x1000, b"\xAB\xCD\xEF\x01")

  regs = noc0_a.regs
  buf = 0
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, 0x1000)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_RET_ADDR_LO, 0x3000)
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  # Multicast rect: start=(5,5) end=(6,6)
  mcast_xy = (6) | (6 << 6) | (5 << 12) | (5 << 18)
  regs.write32(base + M.NIU_RET_ADDR_HI, mcast_xy)
  regs.write32(base + M.NIU_AT_LEN_BE, 4)
  regs.write32(base + M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_RESP_MARKED | M.NOC_CTRL_BRCST)

  core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  for l1 in [l1_00, l1_01, l1_10, l1_11]:
    assert l1.read32(0x3000) == 0x01EFCDAB

def test_atomic_incr_get():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Set initial value at target
  l1_b.write32(0x8000, 42)

  regs = noc0_a.regs
  buf = 3  # AT_CMD_BUF
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, 0x8000)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (4 << 6) | 3)
  regs.write32(base + M.NIU_RET_ADDR_LO, 0x0004)  # NOC_ATOMIC_RET_VAL
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  # AT_INCR_GET (0x1) in bits [15:12], increment=1 in bits [9:6]
  regs.write32(base + M.NIU_AT_LEN_BE, (0x1 << 12) | (1 << 6))
  regs.write32(base + M.NIU_CTRL, M.NOC_CTRL_AT)

  core_a.mem.write32(M.NOC0_BASE + buf * M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)

  # Old value returned to local ret_addr
  assert l1_a.read32(0x0004) == 42
  # Target incremented
  assert l1_b.read32(0x8000) == 43
  # Counter incremented
  assert regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 1

def test_cmd_ctrl_clears_after_fire():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, _, _, _ = make_tile(network, 3, 4)

  l1_a.write32(0x1000, 0x42)
  program_write(noc0_a.regs, buf=0,
         src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x2000, length=4)
  core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  # CMD_CTRL should be 0 now (ready for next command)
  assert noc0_a.regs.read32(M.NIU_CMD_CTRL) == 0

def test_counter_accumulates():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, _, _, _ = make_tile(network, 3, 4)

  for i in range(5):
    l1_a.write32(0x1000, i)
    program_write(noc0_a.regs, buf=0,
           src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x2000, length=4)
    core_a.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

  assert noc0_a.regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 5

def test_noc1_independent():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_a.write32(0x1000, 0xAAAA)

  # Use NOC1 buf0 for a write
  noc1 = noc1_a.regs
  program_write(noc1, buf=0,
         src_addr=0x1000, dst_x=3, dst_y=4, dst_addr=0x4000, length=4)
  core_a.mem.write32(M.NOC1_BASE + M.NIU_CMD_CTRL, 1)

  assert l1_b.read32(0x4000) == 0xAAAA
  # NOC1 counter incremented, NOC0 untouched
  assert noc1.read32(M.NIU_MST_WR_ACK_RECEIVED) == 1
  assert noc0_a.regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 0


# -- atomic operation helpers --------------------------------------------------

def program_atomic(regs, buf, targ_x, targ_y, targ_addr, ret_addr,
         at_len_be, at_data=0, l1_acc_at_en=False, l1_acc_instrn=0):
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, targ_addr)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (targ_y << 6) | targ_x)
  regs.write32(base + M.NIU_RET_ADDR_LO, ret_addr)
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  regs.write32(base + M.NIU_AT_LEN_BE, at_len_be)
  regs.write32(base + M.NIU_AT_DATA, at_data)
  ctrl = M.NOC_CTRL_AT
  if l1_acc_at_en:
    ctrl |= M.NOC_CTRL_L1_ACC_AT_EN
    regs.write32(base + M.NIU_L1_ACC_AT_INSTRN, l1_acc_instrn)
  regs.write32(base + M.NIU_CTRL, ctrl)


def fire_atomic(core, noc_idx, buf):
  noc_base = M.NOC0_BASE if noc_idx == 0 else M.NOC1_BASE
  core.mem.write32(noc_base + buf * M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)


# -- INCR_GET_PTR tests -------------------------------------------------------

def test_atomic_incr_get_ptr_basic():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 2)  # current pointer = 2

  # INCR_GET_PTR: opcode=0x2, incr=1 (bits [9:6]), wrap=5 (bits [5:2])
  at_len_be = (AT_INCR_GET_PTR << 12) | (1 << 6) | (5 << 2)
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004, at_len_be=at_len_be)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 2   # old value returned
  assert l1_b.read32(0x8000) == 3   # 2 + 1 = 3, < 5 so no wrap

def test_atomic_incr_get_ptr_wraps():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 4)  # current pointer = 4

  # wrap=5, incr=1 → 4+1=5 >= 5 → wraps to 0
  at_len_be = (AT_INCR_GET_PTR << 12) | (1 << 6) | (5 << 2)
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004, at_len_be=at_len_be)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 4   # old value
  assert l1_b.read32(0x8000) == 0   # wrapped to 0

def test_atomic_incr_get_ptr_no_wrap():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 100)

  # wrap=0, incr=3
  at_len_be = (AT_INCR_GET_PTR << 12) | (3 << 6) | (0 << 2)
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004, at_len_be=at_len_be)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 100
  assert l1_b.read32(0x8000) == 103


# -- SWAP_4B tests -------------------------------------------------------------

def test_atomic_swap_4b():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0xDEADBEEF)

  at_len_be = AT_SWAP_4B << 12
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=at_len_be, at_data=0xCAFEBABE)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 0xDEADBEEF  # old value returned
  assert l1_b.read32(0x8000) == 0xCAFEBABE  # new value at target


# -- STORE_IND tests -----------------------------------------------------------

def test_atomic_store_ind():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Target contains a pointer to 0x9000
  l1_b.write32(0x8000, 0x9000)
  l1_b.write32(0x9000, 0)  # initially zero at indirect location

  at_len_be = AT_STORE_IND << 12
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=at_len_be, at_data=0x12345678)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 0x9000      # old pointer value returned
  assert l1_b.read32(0x9000) == 0x12345678   # data written at indirect addr
  assert l1_b.read32(0x8000) == 0x9000       # pointer itself unchanged


# -- GET_TILE_MAP tests --------------------------------------------------------

def test_atomic_get_tile_map():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0x42)

  at_len_be = AT_GET_TILE_MAP << 12
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004, at_len_be=at_len_be)
  fire_atomic(core_a, 0, 3)

  assert l1_a.read32(0x0004) == 0x42  # table value returned
  assert l1_b.read32(0x8000) == 0x42  # target unchanged


# -- ACC tests (FP32) ---------------------------------------------------------

def test_atomic_acc_fp32():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Store 1.5f at target
  l1_b.write32(0x8000, struct.unpack('<I', struct.pack('<f', 1.5))[0])

  # ACC with L1_ACC_AT_EN, format=FP32
  l1_acc_instrn = (AT_ACC << 12) | ACC_FP32
  operand = struct.unpack('<I', struct.pack('<f', 2.25))[0]
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=operand,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  # Old value returned
  old = struct.unpack('<f', struct.pack('<I', l1_a.read32(0x0004)))[0]
  assert old == 1.5
  # Target accumulated: 1.5 + 2.25 = 3.75
  result = struct.unpack('<f', struct.pack('<I', l1_b.read32(0x8000)))[0]
  assert result == 3.75

def test_atomic_acc_fp32_saturation():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Store FLT_MAX
  flt_max = struct.unpack('<I', struct.pack('<f', 3.4028235e+38))[0]
  l1_b.write32(0x8000, flt_max)

  l1_acc_instrn = (AT_ACC << 12) | ACC_FP32  # sat_dis=0
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=flt_max,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  result_bits = l1_b.read32(0x8000)
  result = struct.unpack('<f', struct.pack('<I', result_bits))[0]
  import math
  assert not math.isinf(result)  # saturated, not inf
  assert result_bits == 0x7F7FFFFF  # FP32 max finite


# -- ACC tests (FP16) ---------------------------------------------------------

def test_atomic_acc_fp16a():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Store 1.0 as FP16 in lower 16 bits
  val_a = struct.unpack('<H', struct.pack('<e', 1.0))[0]
  l1_b.write32(0x8000, val_a)

  val_b = struct.unpack('<H', struct.pack('<e', 0.5))[0]
  l1_acc_instrn = (AT_ACC << 12) | ACC_FP16_A
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=val_b,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  result_bits = l1_b.read32(0x8000) & 0xFFFF
  result = struct.unpack('<e', struct.pack('<H', result_bits))[0]
  assert result == 1.5  # 1.0 + 0.5


# -- ACC tests (BF16) ---------------------------------------------------------

def test_atomic_acc_bf16():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # BF16 for 1.0 = upper 16 bits of FP32(1.0) = 0x3F80
  bf16_1_0 = 0x3F80
  l1_b.write32(0x8000, bf16_1_0)

  # BF16 for 2.0 = 0x4000
  bf16_2_0 = 0x4000
  l1_acc_instrn = (AT_ACC << 12) | ACC_FP16_B
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=bf16_2_0,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  result_bits = l1_b.read32(0x8000) & 0xFFFF
  # BF16 for 3.0 = 0x4040
  assert result_bits == 0x4040


# -- ACC tests (INT32) --------------------------------------------------------

def test_atomic_acc_int32():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 100)

  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=50,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  assert l1_b.read32(0x8000) == 150

def test_atomic_acc_int32_negative():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 10)

  # -3 as unsigned 32-bit
  neg3 = ((-3) & 0xFFFFFFFF)
  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=neg3,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  assert l1_b.read32(0x8000) == 7  # 10 + (-3) = 7

def test_atomic_acc_int32_saturates():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0x7FFFFFFF)  # INT32_MAX

  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32  # sat_dis=0
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=1,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  assert l1_b.read32(0x8000) == 0x7FFFFFFF  # clamped to max


# -- ACC tests (INT32_UNS) ----------------------------------------------------

def test_atomic_acc_int32_unsigned():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0xFFFFFFFE)

  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32_UNS  # sat_dis=0
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=5,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  assert l1_b.read32(0x8000) == 0xFFFFFFFF  # saturated to UINT32_MAX


# -- ACC tests (INT8) ---------------------------------------------------------

def test_atomic_acc_int8():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Target: [10, 20, 30, 40]
  target = 10 | (20 << 8) | (30 << 16) | (40 << 24)
  l1_b.write32(0x8000, target)

  # Operand: [5, -3, 10, -10] where -3 = 0xFD, -10 = 0xF6
  operand = 5 | (0xFD << 8) | (10 << 16) | (0xF6 << 24)
  l1_acc_instrn = (AT_ACC << 12) | ACC_INT8
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=operand,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  result = l1_b.read32(0x8000)
  b0 = result & 0xFF          # 10 + 5 = 15
  b1 = (result >> 8) & 0xFF   # 20 + (-3) = 17
  b2 = (result >> 16) & 0xFF  # 30 + 10 = 40
  b3 = (result >> 24) & 0xFF  # 40 + (-10) = 30
  assert b0 == 15
  assert b1 == 17
  assert b2 == 40
  assert b3 == 30

def test_atomic_acc_int8_saturates():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  # Target: [120, 0, 0, 0]
  l1_b.write32(0x8000, 120)

  # Operand: [100, 0, 0, 0] — would overflow signed byte (120+100=220 > 127)
  l1_acc_instrn = (AT_ACC << 12) | ACC_INT8  # sat_dis=0
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=100,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  result = l1_b.read32(0x8000) & 0xFF
  assert result == 127  # clamped to INT8_MAX


# -- ACC with sat_dis=1 -------------------------------------------------------

def test_atomic_acc_int32_no_saturation():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0x7FFFFFFF)  # INT32_MAX

  # sat_dis=1 (bit 3 of l1_acc_instrn)
  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32 | (1 << 3)
  program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
         targ_addr=0x8000, ret_addr=0x0004,
         at_len_be=0, at_data=1,
         l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
  fire_atomic(core_a, 0, 3)

  # Wraps to 0x80000000 (INT32_MIN) instead of saturating
  assert l1_b.read32(0x8000) == 0x80000000


# -- ACC counter tracking -----------------------------------------------------

def test_atomic_acc_increments_counter():
  network = {}
  core_a, l1_a, noc0_a, noc1_a = make_tile(network, 1, 2)
  _, l1_b, _, _ = make_tile(network, 3, 4)

  l1_b.write32(0x8000, 0)

  l1_acc_instrn = (AT_ACC << 12) | ACC_INT32
  for i in range(3):
    program_atomic(noc0_a.regs, buf=3, targ_x=3, targ_y=4,
           targ_addr=0x8000, ret_addr=0x0004,
           at_len_be=0, at_data=1,
           l1_acc_at_en=True, l1_acc_instrn=l1_acc_instrn)
    fire_atomic(core_a, 0, 3)

  assert l1_b.read32(0x8000) == 3
  assert noc0_a.regs.read32(M.NIU_MST_ATOMIC_RESP_RECEIVED) == 3
