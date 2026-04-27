from __future__ import annotations

from dataclasses import dataclass

from .memory import BANK_TO_NOC_SCRATCH, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE, KERNEL_CONFIG_BASE


@dataclass(frozen=True)
class RuntimeLayout:
  """Runtime-owned address layout for kernel scratch/config regions."""

  kernel_config_base: int = KERNEL_CONFIG_BASE
  reader_rta_base: int = KERNEL_CONFIG_BASE
  writer_rta_base: int = KERNEL_CONFIG_BASE
  compute_rta_base: int = KERNEL_CONFIG_BASE
  semaphore_base: int = KERNEL_CONFIG_BASE
  cb_config_base: int = CB_L1_CONFIG_BASE
  bank_table_base: int = BANK_TO_NOC_SCRATCH
  trisc_cb_interface_base: int = 0x20

  def cb_config_addr(self, cb: int) -> int:
    return self.cb_config_base + cb * CB_CONFIG_BYTES

  def trisc_cb_interface_addr(self, cb: int) -> int:
    return self.trisc_cb_interface_base + cb * 32

  @property
  def trisc_rta_base(self) -> int:
    return self.compute_rta_base
