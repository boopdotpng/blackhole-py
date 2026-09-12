
import pytest

from asm import Asm
from tests.profiler import Profiler


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
