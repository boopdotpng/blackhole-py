"""Resident multicast, ordering, rotating credit rings, and launch reset."""
import hashlib
import os
from pathlib import Path
import struct
import unittest

import fw


@unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 to run on both cards")
class TestNocMulticastHardware(unittest.TestCase):
  def test_multicast_and_credits(self):
    from device import Device
    source = Path(__file__).parent / "kernels/noc_mcast.c"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    for card in (0, 1):
      dev = Device(card)
      try:
        # The last case also crosses the resident helper's 16 KiB burst boundary.
        for cols, rows, axes, iterations, size, launches in ((13, 1, 1, 1, 4096, 1), (1, 10, 2, 1, 4096, 1),
                                                           (13, 10, 3, 16, 4096, 5), (13, 10, 3, 16, 20480, 1)):
          with self.subTest(card=card, grid=(cols, rows), bytes=size, iterations=iterations):
            flags = (f"-DGCOLS={cols}", f"-DGROWS={rows}", f"-DAXES={axes}", f"-DITERATIONS={iterations}",
                     f"-DBYTES={size}", f"-DSOURCE_HASH={digest}")
            images = {role: fw._piece([source], role, flags) for role in ("brisc", "ncrisc", "trisc0")}
            cores = dev.worker_grid(cols, rows)
            for _ in range(launches):
              dev.run(images, cores=cores, data={fw.MCAST_CTRL_BASE: b"\xff" * 0x400, 0x50000: b"\xff" * 8})
              dev.synchronize()
              for core in cores:
                self.assertEqual(struct.unpack("<II", dev.read_l1(core, 0x50000, 8)), (0, iterations), (card, core))
      finally: dev.close()
