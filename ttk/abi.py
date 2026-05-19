from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LaunchAbi:
  """Offsets in the blackhole-py launch message ABI.

  These are not silicon constants. They are the runtime contract between
  program.py's final layout pass and the resident firmware.
  """

  base: int = 0x70
  kernel_config_base: int = 0
  sem_offset: int = 12
  local_cb_offset: int = 18
  remote_cb_offset: int = 20
  rta_offset: int = 22
  kernel_text_offset: int = 44
  local_cb_mask: int = 64
  enables: int = 76
  min_remote_cb_start_index: int = 82
  sub_device_origin_x: int = 92
  sub_device_origin_y: int = 93


@dataclass(frozen=True)
class RuntimeAbi:
  """Runtime mailbox values owned by blackhole-py firmware."""

  go_msg: int = 0x370
  go_signal: int = 0x373
  subordinate_sync: int = 0x68
  run_msg_go: int = 0x80
  run_msg_done: int = 0x00
  run_msg_load: int = 0x40


LAUNCH = LaunchAbi()
RUNTIME = RuntimeAbi()

ROLE_INDEX = {"brisc": 0, "ncrisc": 1, "trisc0": 2, "trisc1": 3, "trisc2": 4}
