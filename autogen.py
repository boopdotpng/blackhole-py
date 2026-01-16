from ctypes import LittleEndianStructure as S, c_uint8 as u8, c_uint16 as u16, c_uint32 as u32, c_uint64 as u64, sizeof

TENSTORRENT_IOCTL_MAGIC = 0xFA
IOCTL_GET_DEVICE_INFO = 0
IOCTL_QUERY_MAPPINGS = 2
IOCTL_RESET_DEVICE = 6
IOCTL_PIN_PAGES = 7
IOCTL_UNPIN_PAGES = 10
IOCTL_ALLOCATE_TLB = 11
IOCTL_FREE_TLB = 12
IOCTL_CONFIGURE_TLB = 13

TENSTORRENT_RESET_DEVICE_ASIC_RESET = 4
TENSTORRENT_RESET_DEVICE_ASIC_DMC_RESET = 5
TENSTORRENT_RESET_DEVICE_POST_RESET = 6

class QueryMappingsIn(S):
  _fields_ = [("output_mapping_count", u32), ("reserved", u32)]

class TenstorrentMapping(S):
  _fields_ = [("mapping_id", u32), ("reserved", u32), ("mapping_base", u64), ("mapping_size", u64)]

class ResetDeviceIn(S):
  _fields_ = [("output_size_bytes", u32), ("flags", u32)]

class ResetDeviceOut(S):
  _fields_ = [("output_size_bytes", u32), ("result", u32)]

class PinPagesIn(S):
  _fields_ = [("output_size_bytes", u32), ("flags", u32), ("virtual_address", u64), ("size", u64)]

class PinPagesOut(S):
  _fields_ = [("physical_address", u64)]

class PinPagesOutExtended(S):
  _fields_ = [("physical_address", u64), ("noc_address", u64)]

class UnpinPagesIn(S):
  _fields_ = [("virtual_address", u64), ("size", u64), ("reserved", u64)]

class AllocateTlbIn(S):
  _fields_ = [("size", u64), ("reserved", u64)]

class AllocateTlbOut(S):
  _fields_ = [("tlb_id", u32), ("reserved0", u32), ("mmap_offset_uc", u64), ("mmap_offset_wc", u64), ("reserved1", u64)]

class FreeTlbIn(S):
  _fields_ = [("tlb_id", u32)]

class NocTlbConfig(S):
  _fields_ = [
    ("addr", u64), ("x_end", u16), ("y_end", u16), ("x_start", u16), ("y_start", u16),
    ("noc", u8), ("mcast", u8), ("ordering", u8), ("linked", u8), ("static_vc", u8),
    ("reserved0_0", u8), ("reserved0_1", u8), ("reserved0_2", u8), ("reserved1_0", u32), ("reserved1_1", u32),
  ]

class ConfigureTlbIn(S):
  _fields_ = [("tlb_id", u32), ("reserved", u32), ("config", NocTlbConfig)]

class TenstorrentGetDeviceInfoIn(S):
  _fields_ = [("output_size_bytes", u32)]

class TenstorrentGetDeviceInfoOut(S):
  _fields_ = [
    ("output_size_bytes", u32), ("vendor_id", u16), ("device_id", u16), ("subsystem_vendor_id", u16),
    ("subsystem_id", u16), ("bus_dev_fn", u16), ("max_dma_buf_size_log2", u16), ("pci_domain", u16), ("reserved", u16),
  ]
