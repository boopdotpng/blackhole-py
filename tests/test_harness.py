from asm import Asm
from tests.harness import RawHarness


class FakeDevice:
  cores = ((1, 2),)

  def launch(self, core_images, **options):
    self.core_images = core_images
    return "done"


def test_launch_fills_missing_worker_roles():
  device = FakeDevice()
  result = RawHarness(device).launch({"brisc": b"custom"})
  images = device.core_images[(1, 2)]

  assert result == "done"
  assert images["brisc"] == b"custom"
  assert set(images) == {"brisc", "ncrisc", "trisc0", "trisc1", "trisc2"}
  for role in images.keys() - {"brisc"}:
    assert images[role] == Asm(role).lower()
