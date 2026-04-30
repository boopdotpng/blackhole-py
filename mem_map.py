"""Repo-owned Blackhole Tensix L1 memory map.

Keep these values in sync with firmware/blackhole_mem_map.h.  The host uses
them to upload firmware init data and runtime launch state; firmware uses the
same layout to copy init data into local memory and find shared scratch tables.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BlackholeL1Map:
  l1_base: int = 0x0
  l1_size: int = 1536 * 1024

  local_base: int = 0xFFB00000
  brisc_local_size: int = 8 * 1024
  ncrisc_local_size: int = 8 * 1024
  trisc_local_size: int = 4 * 1024

  mailbox_base: int = 0x60
  mailbox_size: int = 12768
  zeros_size: int = 512
  llk_debug_size: int = 1024

  brisc_firmware_size: int = 7 * 1024
  ncrisc_firmware_size: int = 1536
  trisc0_firmware_size: int = 1536
  trisc1_firmware_size: int = 1536
  trisc2_firmware_size: int = 1536

  noc_counter_l1_size: int = 5 * 2 * 2 * 4
  fabric_counter_l1_size: int = 3 * 2 * 4 + 8
  routing_table_size: int = 2288
  offset_of_routing_paths: int = 484
  routing_path_size_1d: int = 256
  compressed_routing_path_size_2d: int = 512
  exit_node_table_size: int = 1024
  routing_table_padding: int = 12
  tensix_fabric_connections_size: int = 656
  packet_header_max_size: int = 112
  num_packet_headers: int = 6 * 2 * 2

  bank_to_noc_xy_size: int = 1024
  bank_offset_size: int = 1024
  logical_to_virtual_size: int = 20 + 12

  launch: int = 0x70
  go_msg: int = 0x370
  go_msg_index: int = 0x3A0
  kernel_config_base: int = 0x86B0
  data_buffer_space_base: int = 0x37000
  timing_control: int = 0x9C0

  @staticmethod
  def align32(value: int) -> int:
    return (value + 31) & ~31

  @property
  def mailbox_end(self) -> int:
    return self.mailbox_base + self.mailbox_size

  @property
  def zeros_base(self) -> int:
    return self.align32(self.mailbox_end)

  @property
  def llk_debug_base(self) -> int:
    return self.zeros_base + self.zeros_size

  @property
  def brisc_firmware_base(self) -> int:
    return self.llk_debug_base + self.llk_debug_size

  @property
  def ncrisc_firmware_base(self) -> int:
    return self.brisc_firmware_base + self.brisc_firmware_size

  @property
  def trisc0_firmware_base(self) -> int:
    return self.ncrisc_firmware_base + self.ncrisc_firmware_size

  @property
  def trisc1_firmware_base(self) -> int:
    return self.trisc0_firmware_base + self.trisc0_firmware_size

  @property
  def trisc2_firmware_base(self) -> int:
    return self.trisc1_firmware_base + self.trisc1_firmware_size

  @property
  def noc_counter_base(self) -> int:
    return self.trisc2_firmware_base + self.trisc2_firmware_size

  @property
  def fabric_counter_base(self) -> int:
    return self.noc_counter_base + self.noc_counter_l1_size

  @property
  def tensix_routing_table_base(self) -> int:
    return self.fabric_counter_base + self.fabric_counter_l1_size

  @property
  def tensix_routing_path_base(self) -> int:
    return self.tensix_routing_table_base + self.offset_of_routing_paths

  @property
  def tensix_routing_path_size(self) -> int:
    return self.routing_path_size_1d + self.compressed_routing_path_size_2d

  @property
  def tensix_exit_node_table_base(self) -> int:
    return self.tensix_routing_path_base + self.tensix_routing_path_size

  @property
  def tensix_fabric_connections_base(self) -> int:
    return self.tensix_exit_node_table_base + self.exit_node_table_size + self.routing_table_padding

  @property
  def packet_header_pool_base(self) -> int:
    return self.tensix_fabric_connections_base + self.tensix_fabric_connections_size

  @property
  def packet_header_pool_size(self) -> int:
    return self.packet_header_max_size * self.num_packet_headers

  @property
  def map_end(self) -> int:
    return self.packet_header_pool_base + self.packet_header_pool_size

  @property
  def brisc_init_local_l1_base_scratch(self) -> int:
    return self.map_end

  @property
  def ncrisc_init_local_l1_base_scratch(self) -> int:
    return self.brisc_init_local_l1_base_scratch + self.brisc_local_size

  @property
  def trisc0_init_local_l1_base_scratch(self) -> int:
    return self.ncrisc_init_local_l1_base_scratch + self.ncrisc_local_size

  @property
  def trisc1_init_local_l1_base_scratch(self) -> int:
    return self.trisc0_init_local_l1_base_scratch + self.trisc_local_size

  @property
  def trisc2_init_local_l1_base_scratch(self) -> int:
    return self.trisc1_init_local_l1_base_scratch + self.trisc_local_size

  @property
  def ncrisc_init_iram_l1_base_scratch(self) -> int:
    return self.trisc2_init_local_l1_base_scratch + self.trisc_local_size

  @property
  def bank_to_noc_scratch(self) -> int:
    return self.ncrisc_init_iram_l1_base_scratch + self.ncrisc_local_size

  @property
  def bank_to_noc_size(self) -> int:
    return self.bank_to_noc_xy_size + self.bank_offset_size

  @property
  def logical_to_virtual_scratch(self) -> int:
    return self.bank_to_noc_scratch + self.bank_to_noc_size

  def firmware_init_scratch(self) -> dict[str, int]:
    return {
      "brisc": self.brisc_init_local_l1_base_scratch,
      "ncrisc": self.ncrisc_init_local_l1_base_scratch,
      "trisc0": self.trisc0_init_local_l1_base_scratch,
      "trisc1": self.trisc1_init_local_l1_base_scratch,
      "trisc2": self.trisc2_init_local_l1_base_scratch,
    }

  def cache_key(self) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((name, int(value)) for name, value in self.firmware_init_scratch().items())) + (
      ("bank_to_noc_scratch", self.bank_to_noc_scratch),
      ("logical_to_virtual_scratch", self.logical_to_virtual_scratch),
      ("kernel_config_base", self.kernel_config_base),
      ("brisc_firmware_base", self.brisc_firmware_base),
    )


BLACKHOLE_L1 = BlackholeL1Map()

