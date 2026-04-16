from emu.device import Device, SOFT_RESET_ALL
from emu.memory import (
  SOFT_RESET_0,
  TRISC0_RESET_PC, TRISC1_RESET_PC, TRISC2_RESET_PC, TRISC_RESET_PC_OVR,
  NCRISC_RESET_PC, NCRISC_RESET_PC_OVR,
  GO_MESSAGES, WALL_CLOCK_L,
)
from emu.fw import SOFT_RESET_BRISC_ONLY, _make_jal
from emu.core import BRISC
from emu.tests._helpers import mini_device


# -- instruction encoding helpers ------------------------------------------

def _addi(rd, rs1, imm):
  return ((imm & 0xFFF) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13

def _lui(rd, upper20):
  return (upper20 << 12) | (rd << 7) | 0x37

def _sw(rs2, offset, rs1):
  return (((offset >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) \
       | (2 << 12) | ((offset & 0x1F) << 7) | 0x23


# -- device reset state ----------------------------------------------------

def test_device_starts_all_in_reset():
  dev = mini_device()
  for xy, tile in dev.tiles.items():
    for core in tile.cores:
      assert core.in_reset, f"core at {xy} not in reset"
    sr = tile.brisc.mem.read32(SOFT_RESET_0)
    assert sr == SOFT_RESET_ALL


# -- release transitions ---------------------------------------------------

def test_release_brisc_only():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
  assert not tile.brisc.in_reset
  assert tile.brisc.pc == 0
  assert tile.ncrisc.in_reset
  assert tile.trisc0.in_reset
  assert tile.trisc1.in_reset
  assert tile.trisc2.in_reset


def test_release_all_cores():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  tile.brisc.mem.write32(SOFT_RESET_0, 0)
  for core in tile.cores:
    assert not core.in_reset


def test_reassert_reset():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  tile.brisc.mem.write32(SOFT_RESET_0, 0)
  assert not tile.brisc.in_reset
  tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_ALL)
  for core in tile.cores:
    assert core.in_reset


# -- RESET_PC override mechanism -------------------------------------------

def test_reset_pc_with_override():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  mmio = tile.mmio
  mmio.write32(TRISC0_RESET_PC, 0x5A40)
  mmio.write32(NCRISC_RESET_PC, 0x5440)
  mmio.write32(TRISC_RESET_PC_OVR, 0b001)
  mmio.write32(NCRISC_RESET_PC_OVR, 0x1)
  tile.brisc.mem.write32(SOFT_RESET_0, 0)
  assert tile.trisc0.pc == 0x5A40
  assert tile.ncrisc.pc == 0x5440
  assert tile.brisc.pc == 0


def test_reset_pc_without_override():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  tile.mmio.write32(TRISC0_RESET_PC, 0x5A40)
  # TRISC_RESET_PC_OVR defaults to 0 — no override
  tile.brisc.mem.write32(SOFT_RESET_0, 0)
  assert tile.trisc0.pc == 0


def test_individual_trisc_override_bits():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  mmio = tile.mmio
  mmio.write32(TRISC0_RESET_PC, 0x100)
  mmio.write32(TRISC1_RESET_PC, 0x200)
  mmio.write32(TRISC2_RESET_PC, 0x300)
  # only enable TRISC1 override (bit 1)
  mmio.write32(TRISC_RESET_PC_OVR, 0b010)
  tile.brisc.mem.write32(SOFT_RESET_0, 0)
  assert tile.trisc0.pc == 0      # no override
  assert tile.trisc1.pc == 0x200  # override enabled
  assert tile.trisc2.pc == 0      # no override


# -- _step_loop respects in_reset -----------------------------------------

def test_step_loop_skips_cores_in_reset():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  # BRISC starts at 0 — put an instruction there
  tile.l1.write32(0, _addi(10, 0, 42))
  # TRISC0 would start at 0x200 — put instruction there too
  tile.l1.write32(0x200, _addi(10, 0, 99))
  tile.mmio.write32(TRISC0_RESET_PC, 0x200)
  tile.mmio.write32(TRISC_RESET_PC_OVR, 0b001)
  # Release only BRISC
  tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
  # Step one tick
  dev._step_loop([tile], lambda: True, 1)
  assert tile.brisc.regs[10] == 42
  # TRISC0 still in reset, never stepped
  assert tile.trisc0.in_reset
  assert tile.trisc0.regs[10] == 0


def test_wall_clock_increments_during_reset():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  # All cores in reset — wall clock should still advance
  assert tile.mmio.read32(WALL_CLOCK_L) == 0
  dev._step_loop([tile], lambda: dev._clock >= 5, 10)
  assert tile.mmio.read32(WALL_CLOCK_L) >= 5


# -- BRISC releases subordinates via firmware write ------------------------

def test_brisc_releases_subordinates_via_soft_reset():
  dev = mini_device()
  tile = list(dev.tiles.values())[0]
  mmio = tile.mmio

  # Set subordinate reset PCs and enable overrides
  mmio.write32(TRISC0_RESET_PC, 0x200)
  mmio.write32(TRISC1_RESET_PC, 0x200)
  mmio.write32(TRISC2_RESET_PC, 0x200)
  mmio.write32(NCRISC_RESET_PC, 0x200)
  mmio.write32(TRISC_RESET_PC_OVR, 0b111)
  mmio.write32(NCRISC_RESET_PC_OVR, 0x1)

  # Subordinate code at 0x200: ADDI x11, x0, 77 (then halt on 0)
  tile.l1.write32(0x200, _addi(11, 0, 77))

  # BRISC code at L1[0]:
  #   LUI  a0, 0xFFB12        # a0 = 0xFFB12000
  #   SW   x0, 0x1B0(a0)      # SOFT_RESET_0 = 0 → release all
  tile.l1.write32(0x00, _lui(10, 0xFFB12))
  tile.l1.write32(0x04, _sw(0, 0x1B0, 10))

  # Release BRISC only
  tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
  assert tile.ncrisc.in_reset
  assert tile.trisc0.in_reset

  # Step until subordinates have executed
  def done():
    return all(c.regs[11] == 77
               for c in [tile.ncrisc, tile.trisc0, tile.trisc1, tile.trisc2])
  dev._step_loop([tile], done, 10)

  # All cores should now be released
  for core in tile.cores:
    assert not core.in_reset
  # Subordinates ran from their RESET_PCs
  for name, core in [('ncrisc', tile.ncrisc), ('trisc0', tile.trisc0),
                      ('trisc1', tile.trisc1), ('trisc2', tile.trisc2)]:
    assert core.regs[11] == 77, f"{name} didn't execute"


# -- JAL encoding ----------------------------------------------------------

def test_make_jal_to_brisc_fw_base():
  jal = _make_jal(0x3840)
  core = BRISC(pc=0)
  core.in_reset = False
  core.l1.load(0, jal)
  core.l1.write32(0x3840, _addi(10, 0, 55))
  core.step()  # JAL
  assert core.pc == 0x3840
  core.step()  # ADDI
  assert core.regs[10] == 55


def test_make_jal_roundtrip():
  for target in [0x100, 0x3840, 0x5440, 0x6A40]:
    jal = _make_jal(target)
    core = BRISC(pc=0)
    core.in_reset = False
    core.l1.load(0, jal)
    core.step()
    assert core.pc == target, f"JAL to {target:#x}: pc={core.pc:#x}"
