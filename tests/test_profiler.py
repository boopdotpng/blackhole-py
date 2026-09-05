from struct import pack
from types import SimpleNamespace

import pytest

from asm import Asm
from fw.consts import TensixMMIO
from tests.profiler import PROFILE_L1_BASE, Profiler


class FakeDevice:
  def __init__(self, data): self.data = data

  def alloc_dram(self, size):
    assert size == 16
    return SimpleNamespace(address=0x40, coordinate=0x81, size=size)

  def launch(self, core_images, timeout):
    assert tuple(core_images) == ((1, 2),)
    assert set(core_images[(1, 2)]) == {
      "brisc", "ncrisc", "trisc0", "trisc1", "trisc2",
    }
    assert all(image and len(image) % 4 == 0
               for image in core_images[(1, 2)].values())

  def read_dram(self, output, timeout):
    assert (output.address, output.coordinate, output.size) == (0x40, 0x81, 16)
    return self.data


def test_records_and_reports_labeled_cycle_differences(capsys):
  kernel = Asm.firmware("trisc1")
  profile = Profiler(kernel)
  profile.record("kernel")
  kernel.addi(kernel.reg(), kernel.reg(), 1)
  profile.record("kernel")
  profile.record("sfpu")
  profile.record("sfpu")

  reads = [
    item for item in kernel.items
    if getattr(item, "op", None) == "lw"
  ]
  assert len(reads) == 4
  assert kernel.lower()

  # The subtraction is intentionally modulo 2^32, including wraparound.
  profile._report(
    FakeDevice(pack("<4I", 100, 175, 0xFFFFFFF0, 0x20)), (1, 2), 10.0,
  )
  assert profile.last == {"kernel": 75, "sfpu": 48}
  assert capsys.readouterr().out == (
    "cycle profile:\n"
    "  [1] kernel: 75 cycles\n"
    "  [2] sfpu: 48 cycles\n"
  )


def test_rejects_open_repeated_and_excess_sections():
  kernel = Asm.firmware("brisc")
  with pytest.raises(ValueError, match="16-byte-aligned"):
    Profiler(kernel, l1_address=PROFILE_L1_BASE + 4)
  profile = Profiler(kernel)
  profile.record("one")
  with pytest.raises(ValueError, match="not stopped"):
    profile._validate()
  profile.record("one")
  with pytest.raises(ValueError, match="already stopped"):
    profile.record("one")

  for label in ("two", "three"):
    profile.record(label)
    profile.record(label)
  with pytest.raises(ValueError, match="at most 3"):
    profile.record("four")


def test_accumulates_repeated_intervals():
  kernel = Asm.firmware("brisc")
  profile = Profiler(kernel)
  for _ in range(3):
    profile.accumulate("NoC write")
    kernel.addi(kernel.reg(), kernel.reg(), 1)
    profile.accumulate("NoC write")

  profile._validate()
  assert profile.size == 8
  assert kernel.lower()


def test_uses_the_worker_wall_clock_register():
  class Kernel:
    def __init__(self): self.calls = []
    def reg(self): return object()
    def read(self, target, address): self.calls.append(("read", address))
    def write(self, address, value): self.calls.append(("write", address))
    def fence(self): self.calls.append(("fence", 0))

  kernel = Kernel()
  profile = Profiler(kernel)
  profile.record("operation")
  profile.record("operation")
  assert kernel.calls == [
    ("read", TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L),
    ("write", PROFILE_L1_BASE),
    ("read", TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L),
    ("write", PROFILE_L1_BASE + 4),
    ("fence", 0),
  ]


@pytest.mark.parametrize(("profile_role", "section_count"), [
  ("brisc", 1), ("ncrisc", 2), ("trisc1", 3),
])
def test_profiles_a_kernel_on_hardware(bh, profile_role, section_count):
  kernel = Asm(profile_role)
  profile = Profiler(kernel)
  for section in range(section_count):
    label = f"risc work {section + 1}"
    profile.record(label)
    value = kernel.reg()
    kernel.li(value, 0)
    for _ in range(64): kernel.addi(value, value, 1)
    profile.record(label)

  bh.launch(
    {profile_role: kernel.lower()}, profiler=profile,
  )
  assert len(profile.last) == section_count
  assert all(cycles > 0 for cycles in profile.last.values())
