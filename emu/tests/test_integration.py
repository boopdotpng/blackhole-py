"""End-to-end integration: fw.boot → device.run with real RVIR firmware.

Boots the full 5-core firmware image into an emulated tile, then dispatches
a trivial no-op kernel and verifies go_msg cycles GO → DONE.
"""
import struct
import sys
from pathlib import Path

# rvir-kernels lives as a sibling of extra/; add blackhole-py/ to sys.path
# so `firmware` is importable.
_BH = Path(__file__).resolve().parents[3]   # .../blackhole-py
_RVIR_KERNELS = _BH / "rvir-kernels"
for p in (str(_BH), str(_RVIR_KERNELS)):
  if p not in sys.path:
    sys.path.insert(0, p)

import pytest

from emu import device as fw
from emu.device import Device, RUN_MSG_DONE
from emu.memory import (
  GO_MESSAGES, SUBORDINATE_SYNC, LAUNCH_MSG_RD_PTR, LAUNCH_MSG_RING,
  KERNEL_CONFIG_BASE, DATA_BUFFER_SPACE_BASE,
)
from ._helpers import mini_device


# JALR x0, x1, 0  — `ret` (a minimal kernel: returns immediately)
RET = struct.pack("<I", 0x00008067)
NOOP_KERNEL = dict(brisc=RET, ncrisc=RET, trisc=(RET, RET, RET))


@pytest.fixture(scope="module")
def firmware_image():
  from firmware import build_all
  return build_all()


@pytest.fixture
def booted(firmware_image):
  """Fresh 1-tile device, booted, ready to dispatch. Returns (dev, tile, l1)."""
  dev = mini_device()
  fw.boot(dev, firmware_image)
  tile = next(iter(dev.tiles.values()))
  return dev, tile, tile.l1


def test_boot_reaches_done(booted):
  """fw.boot should drive BRISC through init and land at go_msg == DONE."""
  dev, tile, l1 = booted
  assert l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE
  assert l1.read32(SUBORDINATE_SYNC) == 0  # all subordinates signaled DONE
  for core in tile.cores:
    assert not core.in_reset


def test_dispatch_twice(booted):
  """Two back-to-back dispatches — ring must keep working. Also covers no-op dispatch."""
  dev, tile, l1 = booted
  for _ in range(2):
    dev.run(**NOOP_KERNEL)
    assert l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE


def test_launch_msg_fields(booted):
  """device.run() populates launch_msg with the tt-metal layout fields."""
  dev, tile, l1 = booted

  cbs = [(0, 2048, 2), (16, 2048, 2)]
  dev.run(
    **NOOP_KERNEL,
    writer_args=[[0xAAAA1111, 0xAAAA2222, 7]],   # 3 args × 4 B = 12 B
    reader_args=[[0xBBBB3333, 4]],                # 2 args × 4 B = 8 B
    compute_args=[[9]],                           # 1 arg × 4 B = 4 B
    cbs=cbs,
    num_semaphores=2,
  )
  lm = LAUNCH_MSG_RING  # slot 0

  # kernel_config_base[0..2]
  for j in range(3):
    assert l1.read32(lm + j * 4) == KERNEL_CONFIG_BASE

  # Layout: writer RTA = 12 B, reader RTA = 8 B, compute RTA = 4 B
  # max_w=12, max_r=8, max_c=4, total=24, aligned to 16 → sem_off=32
  assert l1.read16(lm + 12) == 32  # sem_offset[0]
  assert l1.read16(lm + 14) == 32  # sem_offset[1]
  assert l1.read16(lm + 16) == 32  # sem_offset[2]

  # local_cb_off = align(32 + 2*16, 16) = 64
  assert l1.read16(lm + 18) == 64
  # CB blob: mask.bit_length() with CB 0 and CB 16 → bit_length=17 → 17×16 = 272 B
  # remote_cb_off = 64 + 272 = 336
  assert l1.read16(lm + 20) == 336

  # rta_offset[0..4]
  assert l1.read16(lm + 22 + 0 * 4) == 0        # brisc rta = 0
  assert l1.read16(lm + 22 + 1 * 4) == 12       # ncrisc rta = max_w
  assert l1.read16(lm + 22 + 2 * 4) == 20       # trisc0 rta = max_w + max_r
  # crta_offset for each = local_cb_off
  for j in range(5):
    assert l1.read16(lm + 22 + j * 4 + 2) == 64

  # mode = DISPATCH_MODE_HOST
  assert l1.read8(lm + 42) == 1

  # local_cb_mask = bit 0 | bit 16
  assert l1.read32(lm + 64) == (1 | (1 << 16))

  # enables (all 5 cores have a kernel)
  assert l1.read32(lm + 76) == 0b11111


def test_rtas_written_to_l1(booted):
  """device.run() writes per-processor RTAs at KERNEL_CONFIG_BASE + rta_offset."""
  dev, tile, l1 = booted
  dev.run(
    **NOOP_KERNEL,
    writer_args=[[0x11111111, 0x22222222]],
    reader_args=[[0x33333333]],
    compute_args=[[0x44444444, 0x55555555, 0x66666666]],
  )
  # writer RTAs at offset 0; reader at max_w=8; compute at max_w+max_r=12
  expected = [
    (0,  0x11111111), (4,  0x22222222),
    (8,  0x33333333),
    (12, 0x44444444), (16, 0x55555555), (20, 0x66666666),
  ]
  for off, val in expected:
    assert l1.read32(KERNEL_CONFIG_BASE + off) == val


def test_cbs_written_to_l1(booted):
  """CB config blob at KERNEL_CONFIG_BASE + local_cb_off records (addr, size, tiles, page_size)."""
  dev, tile, l1 = booted
  dev.run(**NOOP_KERNEL, cbs=[(0, 1024, 4), (1, 512, 8)])
  lm = LAUNCH_MSG_RING
  cb_base = KERNEL_CONFIG_BASE + l1.read16(lm + 18)

  # Each CB slot: (addr, total_size, num_tiles, page_size) at 16-byte stride
  cb_records = [
    (0,  DATA_BUFFER_SPACE_BASE,        1024 * 4, 4, 1024),  # CB 0
    (16, DATA_BUFFER_SPACE_BASE + 4096,  512 * 8, 8,  512),  # CB 1
  ]
  for slot, addr, size, tiles, page in cb_records:
    assert l1.read32(cb_base + slot + 0)  == addr
    assert l1.read32(cb_base + slot + 4)  == size
    assert l1.read32(cb_base + slot + 8)  == tiles
    assert l1.read32(cb_base + slot + 12) == page
