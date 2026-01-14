import ctypes, fcntl, mmap, os, time
from dataclasses import dataclass
from autogen import *
from tlb import TLBConfig, TLBWindow, TLBMode, TLBSize

# UT3G cannot support fast dispatch because of the 1g iommu map requirement 
# will test this later 
# used by default
# SLOW_DISPATCH = int(os.environ.get("TT_SLOW_DISPATCH", 0)) == 1
DEBUG = int(os.environ.get("DEBUG", 0)) > 1

@dataclass
class Harvesting:
  tensix: int
  dram: int
  eth: int
  pcie: int

  def __repr__(self) -> str:
    return (
      "Harvesting masks: "
      f"tensix=0x{self.tensix:x} "
      f"dram=0x{self.dram:x} "
      f"eth=0x{self.eth:x} "
      f"pcie=0x{self.pcie:x}"
    )


ARC_CORE = (8, 0)
ARC_NOC_BASE = 0x80000000
SCRATCH_RAM_13 = 0x30434
CSM_START = 0x10000000
CSM_END = 0x1007FFFF

HARVESTING_NOC_LOCATIONS = [1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10]
SORTED_LOCATIONS = sorted(HARVESTING_NOC_LOCATIONS)
HARVESTING_INDEX_BY_LOC = {loc: idx for idx, loc in enumerate(SORTED_LOCATIONS)}

def _IO(nr: int) -> int: return (TENSTORRENT_IOCTL_MAGIC << 8) | nr
def _align_down(value: int, alignment: int) -> int: return value & ~(alignment - 1)

def shuffle_tensix_harvesting_mask(raw_mask: int) -> int:
  new_mask = 0
  for pos, loc in enumerate(HARVESTING_NOC_LOCATIONS):
    if raw_mask & (1 << pos):
      new_mask |= 1 << HARVESTING_INDEX_BY_LOC[loc]
  return new_mask

def _get_bdf_for_path(path: str) -> str | None:
  """Get BDF for a device path, or None if it fails."""
  try:
    fd = os.open(path, os.O_RDWR | os.O_CLOEXEC)
    in_sz = ctypes.sizeof(TenstorrentGetDeviceInfoIn)
    out_sz = ctypes.sizeof(TenstorrentGetDeviceInfoOut)
    buf = bytearray(in_sz + out_sz)
    TenstorrentGetDeviceInfoIn.from_buffer(buf).output_size_bytes = out_sz
    fcntl.ioctl(fd, _IO(IOCTL_GET_DEVICE_INFO), buf, True)
    if DEBUG: print(f"ioctl get device info: output_size_bytes: {out_sz}")
    os.close(fd)
    info = TenstorrentGetDeviceInfoOut.from_buffer(buf, in_sz)
    bdf = info.bus_dev_fn
    return f"{info.pci_domain:04x}:{(bdf >> 8) & 0xFF:02x}:{(bdf >> 3) & 0x1F:02x}.{bdf & 0x7}"
  except: return None

def find_dev_by_bdf(target_bdf: str) -> str | None:
  for entry in os.listdir("/dev/tenstorrent"):
    if not entry.isdigit(): continue
    path = f"/dev/tenstorrent/{entry}"
    if _get_bdf_for_path(path) == target_bdf: return path
  return None

class Device:
  def __init__(self, path: str = "/dev/tenstorrent/0"):
    self.path = path
    self.fd = os.open(self.path, os.O_RDWR | os.O_CLOEXEC)
    if DEBUG: print(f"opened {path}, file descriptor {self.fd}")
    self._setup()
    self.harvesting = self.get_harvesting()
    print(self.harvesting)

  # determine harvesting, very important
  # different Tensix tiles and DRAM cores are turned off per p100a. you must not access them
  # you can get these by mapping a TLB window onto the ARC tile
  def get_harvesting(self) -> Harvesting:
    tlb_config = TLBConfig(
      addr = ARC_NOC_BASE,
      start = ARC_CORE,
      end = ARC_CORE,
      noc = 0,
      mcast = False,
      mode = TLBMode.STRICT
    )

    with TLBWindow(self.fd, TLBSize.MiB_2, tlb_config) as arc:
      telem_struct_addr = arc.read32(SCRATCH_RAM_13)

      if telem_struct_addr == 0:
        raise RuntimeError("telemetry struct address is 0 (ARC not ready)")
      if not (CSM_START <= telem_struct_addr <= CSM_END):
        raise RuntimeError(f"invalid telemetry struct address: 0x{telem_struct_addr:08x}")

      csm_base = _align_down(telem_struct_addr, TLBSize.MiB_2)
      csm_offset = telem_struct_addr - csm_base
      arc.configure(TLBConfig(
        addr = csm_base,
        start = ARC_CORE,
        end = ARC_CORE,
        noc = 0,
        mcast = False,
        mode = TLBMode.STRICT
      ))

      entry_count = arc.read32(csm_offset + 4)
      tags_base = csm_offset + 8
      data_base = csm_offset + 8 + (entry_count * 4)

      tag_to_offset = {}
      for i in range(entry_count):
        tag_offset = arc.read32(tags_base + (i * 4))
        tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF

      def read_tag(tag: int, default: int) -> int:
        if tag not in tag_to_offset: return default
        return arc.read32(data_base + (tag_to_offset[tag] * 4))

      tensix_enabled = read_tag(34, 0x3FFF)
      eth_enabled = read_tag(35, 0x3FFF)
      gddr_enabled = read_tag(36, 0xFF)
      pcie_usage = read_tag(38, 0x5)

      pcie_harvest = 0
      if (pcie_usage & 0x3) != 1: pcie_harvest |= 0x1
      if ((pcie_usage >> 2) & 0x3) != 1: pcie_harvest |= 0x2

    return Harvesting(
      # tensix tile harvesting is per-column; the mask is reordered to match sorted NOC X columns.
      tensix = shuffle_tensix_harvesting_mask(~tensix_enabled & 0x3FFF),
      # dram harvesting is a direct bank mask (bit N => DRAM bank N disabled).
      dram = ~gddr_enabled & 0xFF,
      # ethernet harvesting is a direct mask over 14 ETH cores (bit N => ETH core N disabled).
      eth = ~eth_enabled & 0x3FFF,
      # PCIe harvesting is a 2-bit mask: bit 0 = PCIe0 disabled, bit 1 = PCIe1 disabled.
      pcie = pcie_harvest,
    )

  def _setup(self, retried: bool = False):
    self.arch = self._get_arch()
    if self.arch not in ("p100a", "p150b"):
      if retried:
        os.close(self.fd)
        raise SystemExit("device still in bad state after reset")
      confirm = input("only blackhole is supported. alternatively, the card might be in a bad state. reset y/n: ")
      if confirm.lower() == 'y':
        self.reset(dmc_reset=True)
        return
      os.close(self.fd)
      raise SystemExit("exiting")
        

    print(f"opened blackhole {self.arch} at {self.get_bdf()}")
    self._map_bars()

  def _close(self):
    if hasattr(self, 'mm0'): self.mm0.close()
    if hasattr(self, 'mm1'): self.mm1.close()
    os.close(self.fd)
    if DEBUG: print("device closed")

  def get_bdf(self):
    in_sz = ctypes.sizeof(TenstorrentGetDeviceInfoIn)
    out_sz = ctypes.sizeof(TenstorrentGetDeviceInfoOut)
    buf = bytearray(in_sz + out_sz)
    TenstorrentGetDeviceInfoIn.from_buffer(buf).output_size_bytes = out_sz

    fcntl.ioctl(self.fd, _IO(IOCTL_GET_DEVICE_INFO), buf, True)
    # we only really care about the bdf
    bdf = TenstorrentGetDeviceInfoOut.from_buffer(buf, in_sz).bus_dev_fn
    pci_domain = TenstorrentGetDeviceInfoOut.from_buffer(buf, in_sz).pci_domain

    return f"{pci_domain:04x}:{(bdf >> 8) & 0xFF:02x}:{(bdf >> 3) & 0x1F:02x}.{bdf & 0x7}"

  def _map_bars(self):
    in_sz = ctypes.sizeof(QueryMappingsIn)
    out_sz = ctypes.sizeof(TenstorrentMapping)
    buf = bytearray(in_sz + 6 * out_sz)
    QueryMappingsIn.from_buffer(buf).output_mapping_count = 6
    fcntl.ioctl(self.fd, _IO(IOCTL_QUERY_MAPPINGS), buf, True)
    bars = list((TenstorrentMapping * 6).from_buffer(buf, in_sz))

    # UC bars for bar0 and bar1 are 0,2 (the others are WC which is bad for reading/writing registers)
    # we don't need to mmap global vram (4+5), that is done through the dram tiles and the NoC
    self.mm0 = mmap.mmap(self.fd, bars[0].mapping_size, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE, offset=bars[0].mapping_base)
    self.mm1 = mmap.mmap(self.fd, bars[2].mapping_size, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE, offset=bars[2].mapping_base)

    if DEBUG:
      print(f"mapped bar 0 (0x{bars[0].mapping_size:x} bytes) at address 0x{bars[0].mapping_base:x}")
      print(f"mapped bar 1 (0x{bars[2].mapping_size:x} bytes) at address 0x{bars[2].mapping_base:x}")
    
  def reset(self, dmc_reset:bool=False) -> int:
    # mirrors reset logic in tt-kmd/tools/reset.c 
    bdf = self.get_bdf()
    print(f"resetting device {bdf}")
    in_sz, out_sz = ctypes.sizeof(ResetDeviceIn), ctypes.sizeof(ResetDeviceOut)

    buf = bytearray(in_sz + out_sz)
    view = ResetDeviceIn.from_buffer(buf)
    view.output_size_bytes, view.flags = out_sz, (TENSTORRENT_RESET_DEVICE_ASIC_DMC_RESET if dmc_reset else TENSTORRENT_RESET_DEVICE_ASIC_RESET)
    fcntl.ioctl(self.fd, _IO(IOCTL_RESET_DEVICE), buf, True)
    self._close()

    # poll for device to come back by bus, device, function from get_device_info (up to 10s)
    print("waiting for device to come back...")
    for _ in range(50):
      time.sleep(0.2)
      if (path := find_dev_by_bdf(bdf)):
        self.path = path
        break
    else:
      raise RuntimeError(f"device {bdf} didn't come back after reset")

    print(f"device back at {self.path}")

    # open fd first, then POST_RESET to reinit hardware, then finish setup
    self.fd = os.open(self.path, os.O_RDWR | os.O_CLOEXEC)

    # post reset: without this, the device doesn't init again
    buf = bytearray(in_sz + out_sz)
    view = ResetDeviceIn.from_buffer(buf)
    view.output_size_bytes, view.flags = out_sz, TENSTORRENT_RESET_DEVICE_POST_RESET
    fcntl.ioctl(self.fd, _IO(IOCTL_RESET_DEVICE), buf, True)
    result = ResetDeviceOut.from_buffer(buf, in_sz).result
    print(f"reset complete, result={result}")

    self._setup(retried=True)
    return result
  
  def _get_arch(self):
    ordinal = self.path.split('/')[-1]
    with open(f"/sys/class/tenstorrent/tenstorrent!{ordinal}/tt_card_type", "r") as f: return f.read().strip()
  
  def close(self): self._close()

def main():
  device = Device()
  device.close()
  
if __name__ == "__main__":
  main()
