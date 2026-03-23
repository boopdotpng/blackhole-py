"""Structured Tensix state dumps using tt-exalens metadata."""

from __future__ import annotations

from dataclasses import dataclass

from debug.debug_bus import DebugBus
from debug.regs import DEBUG_TLB_BASE
from hw import NocOrdering

from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.blackhole.functional_worker_debug_bus_signals import (
  debug_bus_signal_map,
  group_map,
  tensix_debug_bus_description,
)
from ttexalens.hardware.blackhole.functional_worker_registers import (
  register_map,
  tensix_registers_descriptions,
)
from ttexalens.register_store import (
  ConfigurationRegisterDescription,
  DebugRegisterDescription,
  REGISTER_DATA_TYPE,
  TensixGeneralPurposeRegisterDescription,
  format_register_value,
)


DEBUG_REG_BASE = 0xFFB12000
TENSIX_GPR_BASE = 0xFFE00000

DEBUG_BUS_INIT = DebugBusSignalStore.create_initialization(group_map, debug_bus_signal_map)


@dataclass(frozen=True)
class _ShiftMask:
  shift: int
  mask: int


class TensixStateReader:
  GROUPS = ("all", "alu", "pack", "unpack", "gpr", "rwc", "adc")

  def __init__(self, win, debugger):
    self.win = win
    self.debugger = debugger
    self.debug_bus = DebugBus(win, debugger.core)

  def _target_debug_regs(self):
    self.win.target(self.debugger.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  @staticmethod
  def _debug_reg_offset(offset: int) -> int:
    return (DEBUG_REG_BASE + offset) - DEBUG_TLB_BASE

  @staticmethod
  def _mask_bits(mask: int) -> int:
    return max(1, mask.bit_count())

  def _format_value(self, value: int, data_type: REGISTER_DATA_TYPE, mask: int) -> str:
    return str(format_register_value(value, data_type, self._mask_bits(mask)))

  def _read_config_register(self, register: ConfigurationRegisterDescription) -> int:
    self._target_debug_regs()
    self.win.write32(self._debug_reg_offset(register_map["RISCV_DEBUG_REG_CFGREG_RD_CNTL"].offset), register.index)
    raw = self.win.read32(self._debug_reg_offset(register_map["RISCV_DEBUG_REG_CFGREG_RDDATA"].offset))
    return (raw & register.mask) >> register.shift

  def _read_debug_register(self, register: DebugRegisterDescription) -> int:
    self._target_debug_regs()
    raw = self.win.read32(self._debug_reg_offset(register.offset))
    return (raw & register.mask) >> register.shift

  def _read_tensix_gpr(self, register: TensixGeneralPurposeRegisterDescription) -> int:
    if not self.debugger.is_halted():
      raise RuntimeError("tensix gpr dump requires the RISC to be DR-halted")
    raw = self.debugger.read_memory(TENSIX_GPR_BASE + register.offset)
    return (raw & register.mask) >> register.shift

  def _read_register(self, register_name: str) -> dict:
    register = register_map[register_name]
    if isinstance(register, ConfigurationRegisterDescription):
      value = self._read_config_register(register)
    elif isinstance(register, DebugRegisterDescription):
      value = self._read_debug_register(register)
    elif isinstance(register, TensixGeneralPurposeRegisterDescription):
      value = self._read_tensix_gpr(register)
    else:
      raise TypeError(f"unsupported register type for {register_name}")
    return {
      "raw": value,
      "hex": f"0x{value:x}",
      "formatted": self._format_value(value, register.data_type, register.mask),
    }

  def _read_register_section(self, section_name: str, rows: list[dict[str, str]]) -> dict:
    section_rows = []
    for row in rows:
      values = {field_name: self._read_register(register_name) for field_name, register_name in row.items()}
      section_rows.append(values)
    return {
      "name": section_name,
      "rows": section_rows,
    }

  def _read_debug_bus_group_unsafe(self, group_name: str) -> dict:
    daisy_sel, sig_sel = DEBUG_BUS_INIT.group_map[group_name]
    data = 0
    for rd_sel in range(4):
      data |= self.debug_bus.read_signal(sig_sel, daisy_sel, rd_sel) << (32 * rd_sel)
    signals = {}
    for signal_name, shift_mask in DEBUG_BUS_INIT.signal_groups[group_name].items():
      value = (data & shift_mask.mask) >> shift_mask.shift
      signals[signal_name] = {
        "raw": value,
        "hex": f"0x{value:x}",
        "formatted": str(bool(value)) if shift_mask.mask.bit_count() == 1 else f"0x{value:x}",
      }
    return {
      "name": group_name,
      "signals": signals,
    }

  def read_group(self, group: str = "all") -> dict:
    if group not in self.GROUPS:
      raise ValueError(f"group must be one of {', '.join(self.GROUPS)}")

    payload: dict[str, object] = {"group": group, "groups": {}}

    if group in ("alu", "all"):
      payload["groups"]["alu"] = {
        "sections": [
          self._read_register_section("alu_config", tensix_registers_descriptions.alu_config),
        ]
      }

    if group in ("unpack", "all"):
      payload["groups"]["unpack"] = {
        "sections": [
          self._read_register_section("tile_descriptor", tensix_registers_descriptions.unpack_tile_descriptor),
          self._read_register_section("config", tensix_registers_descriptions.unpack_config),
        ]
      }

    if group in ("pack", "all"):
      payload["groups"]["pack"] = {
        "sections": [
          self._read_register_section("config", tensix_registers_descriptions.pack_config),
          self._read_register_section("relu_config", tensix_registers_descriptions.relu_config),
          self._read_register_section("dest_rd_ctrl", tensix_registers_descriptions.pack_dest_rd_ctrl),
          self._read_register_section("edge_offset", tensix_registers_descriptions.pack_edge_offset),
          self._read_register_section("counters", tensix_registers_descriptions.pack_counters),
          self._read_register_section("strides", tensix_registers_descriptions.pack_strides),
        ]
      }

    if group in ("gpr", "all"):
      gpr_payload = {"sections": []}
      try:
        gpr_payload["sections"] = [
          self._read_register_section(f"thread_{thread_id}", [thread_map])
          for thread_id, thread_map in enumerate(tensix_registers_descriptions.general_purpose_registers)
        ]
      except Exception as exc:
        gpr_payload["error"] = str(exc)
      payload["groups"]["gpr"] = gpr_payload

    if group in ("rwc", "all"):
      payload["groups"]["rwc"] = {
        "sections": [
          self._read_debug_bus_group_unsafe(group_name)
          for group_name in tensix_debug_bus_description.register_window_counter_groups
        ]
      }

    if group in ("adc", "all"):
      payload["groups"]["adc"] = {
        "sections": [
          self._read_debug_bus_group_unsafe(group_name)
          for group_name in tensix_debug_bus_description.address_counter_groups
        ]
      }

    return payload
