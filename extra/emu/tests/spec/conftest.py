"""Shared fixtures and markers for spec-organized tests.

Every test in this directory is pinned to one or more clauses in an
`extra/emu/clauses/<doc>.md` ledger via the `@spec("CLAUSE.ID", ...)`
decorator. Each ledger cites the authoritative prose spec in `extra/emu/specs/<doc>.md`.
The pytest plugin (future work) scans these markers and produces a coverage
matrix proving every clause has at least one test.
"""

import pytest

from emu import memory as M
from emu.core import BRISC
from emu.memory import Memory
from emu.noc import NOC, noc_key


def spec(*clause_ids):
  """Pin a test to one or more clause ids from a clauses/<doc>.md ledger.

  Usage:
    @spec("NOC-AT.INCR_GET_PTR.WRAP_SEMANTIC")
    def test_incr_get_ptr_wraps_at_boundary(...): ...

  The decorator attaches a pytest marker so a future plugin can build a
  clause -> test coverage map.
  """
  return pytest.mark.spec(*clause_ids)


# Tile and NOC fixtures

def _make_tile(network, x, y):
  """Build a BRISC + NOC0/NOC1 + L1, register in the shared network."""
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


@pytest.fixture
def two_tile_network():
  """Source tile (1,2) and target tile (3,4) on the same NOC network."""
  network = {}
  src = _make_tile(network, 1, 2)          # core_a, l1_a, noc0_a, noc1_a
  dst = _make_tile(network, 3, 4)          # core_b, l1_b, noc0_b, noc1_b
  return dict(
    network=network,
    src_core=src[0], src_l1=src[1], src_noc0=src[2], src_noc1=src[3],
    dst_core=dst[0], dst_l1=dst[1], dst_noc0=dst[2], dst_noc1=dst[3],
    src_xy=(1, 2), dst_xy=(3, 4),
  )


# Atomic command helpers

def program_atomic(regs, *, buf, targ_x, targ_y, targ_addr, ret_addr,
                   at_len_be, at_data=0,
                   resp_marked=True,
                   l1_acc_at_en=False, l1_acc_instrn=0):
  """Program one of the 4 NIU command buffers for an atomic op.

  Does not fire the command — call fire_atomic() for that.
  """
  base = buf * M.NIU_CMD_BUF_STRIDE
  regs.write32(base + M.NIU_TARG_ADDR_LO, targ_addr & 0xFFFFFFFF)
  regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
  regs.write32(base + M.NIU_TARG_ADDR_HI, (targ_y << 6) | targ_x)
  regs.write32(base + M.NIU_RET_ADDR_LO, ret_addr & 0xFFFFFFFF)
  regs.write32(base + M.NIU_RET_ADDR_MID, 0)
  regs.write32(base + M.NIU_AT_LEN_BE, at_len_be)
  regs.write32(base + M.NIU_AT_DATA, at_data & 0xFFFFFFFF)
  ctrl = M.NOC_CTRL_AT
  if resp_marked:
    ctrl |= M.NOC_CTRL_RESP_MARKED
  if l1_acc_at_en:
    ctrl |= M.NOC_CTRL_L1_ACC_AT_EN
    regs.write32(base + M.NIU_L1_ACC_AT_INSTRN, l1_acc_instrn)
  regs.write32(base + M.NIU_CTRL, ctrl)


def fire_atomic(core, noc_idx, buf):
  """Write 1 to CMD_CTRL for the given buffer, routed through the core's mmap."""
  base = M.NOC0_BASE if noc_idx == 0 else M.NOC1_BASE
  core.mem.write32(base + buf * M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)


@pytest.fixture
def atomic():
  """Bundle program + fire into a single callable for terse test bodies."""
  def _go(net, *, op, targ_addr, ret_addr=0x4,
          at_len_be=None, at_data=0,
          resp_marked=True,
          l1_acc_at_en=False, l1_acc_instrn=0,
          buf=3, noc_idx=0):
    # If caller passes just `op`, pack it into at_len_be[15:12].
    if at_len_be is None:
      at_len_be = (op & 0xF) << 12
    program_atomic(
      net['src_noc0' if noc_idx == 0 else 'src_noc1'].regs,
      buf=buf,
      targ_x=net['dst_xy'][0], targ_y=net['dst_xy'][1],
      targ_addr=targ_addr, ret_addr=ret_addr,
      at_len_be=at_len_be, at_data=at_data,
      resp_marked=resp_marked,
      l1_acc_at_en=l1_acc_at_en, l1_acc_instrn=l1_acc_instrn,
    )
    fire_atomic(net['src_core'], noc_idx, buf)
  return _go


# pytest configuration

def pytest_configure(config):
  config.addinivalue_line(
    "markers",
    "spec(*clause_ids): pin a test to spec clauses from extra/emu/clauses/<doc>.md",
  )
