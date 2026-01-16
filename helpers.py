import os, sys, ctypes, fcntl, struct
from autogen import TENSTORRENT_IOCTL_MAGIC, TenstorrentGetDeviceInfoIn
from autogen import TenstorrentGetDeviceInfoOut, IOCTL_GET_DEVICE_INFO
from autogen import IOCTL_ALLOCATE_TLB, IOCTL_FREE_TLB, IOCTL_CONFIGURE_TLB
from dataclasses import dataclass
from pathlib import Path
from configs import TLBSize

DEBUG = int(os.environ.get("DEBUG", 0))
TT_HOME = Path(os.environ.get("TT_HOME", ""))

IOCTL_NAMES = {
  0: "GET_DEVICE_INFO", 2: "QUERY_MAPPINGS", 6: "RESET_DEVICE",
  7: "PIN_PAGES", 10: "UNPIN_PAGES", 11: "ALLOCATE_TLB",
  12: "FREE_TLB", 13: "CONFIGURE_TLB",
}

def dbg(level: int, tag: str, msg: str):
  if DEBUG >= level: print(f"{tag}: {msg}")

def warn(tag: str, msg: str):
  print(f"{tag}: {msg}", file=sys.stderr)

_TLB_IOCTLS = {IOCTL_ALLOCATE_TLB, IOCTL_FREE_TLB, IOCTL_CONFIGURE_TLB}

def trace_ioctl(nr: int, extra: str = ""):
  if DEBUG < 4 or nr in _TLB_IOCTLS: return
  name = IOCTL_NAMES.get(nr, str(nr))
  dbg(4, "ioctl", f"{name}{' ' + extra if extra else ''}")

def _IO(nr: int) -> int: return (TENSTORRENT_IOCTL_MAGIC << 8) | nr

def align_down(value: int, alignment: TLBSize) -> tuple[int, int]:
  base = value & ~(alignment.value - 1)
  return base, value - base

def format_bdf(pci_domain: int, bus_dev_fn: int) -> str:
  return f"{pci_domain:04x}:{(bus_dev_fn >> 8) & 0xFF:02x}:{(bus_dev_fn >> 3) & 0x1F:02x}.{bus_dev_fn & 0x7}"

def _get_bdf_for_path(path: str) -> str | None:
  try:
    fd = os.open(path, os.O_RDWR | os.O_CLOEXEC)
    in_sz = ctypes.sizeof(TenstorrentGetDeviceInfoIn)
    out_sz = ctypes.sizeof(TenstorrentGetDeviceInfoOut)
    buf = bytearray(in_sz + out_sz)
    TenstorrentGetDeviceInfoIn.from_buffer(buf).output_size_bytes = out_sz
    fcntl.ioctl(fd, _IO(IOCTL_GET_DEVICE_INFO), buf, True)
    os.close(fd)
    info = TenstorrentGetDeviceInfoOut.from_buffer(buf, in_sz)
    return format_bdf(info.pci_domain, info.bus_dev_fn)
  except OSError: return None

def find_dev_by_bdf(target_bdf: str) -> str | None:
  for entry in os.listdir("/dev/tenstorrent"):
    if not entry.isdigit(): continue
    path = f"/dev/tenstorrent/{entry}"
    if _get_bdf_for_path(path) == target_bdf: return path
  return None

@dataclass(frozen=True)
class PTLoad:
  paddr: int
  data: bytes
  memsz: int

def load_pt_load(path: str | os.PathLike[str]) -> list[PTLoad]:
  with open(os.fspath(path), "rb") as f: elf = f.read()
  e_phoff = struct.unpack_from("<I", elf, 28)[0]
  e_phentsize, e_phnum = struct.unpack_from("<HH", elf, 42)
  segs = []
  for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, _, p_paddr, p_filesz, p_memsz, _, _ = struct.unpack_from("<IIIIIIII", elf, off)
    if p_type != 1: continue  # PT_LOAD
    if p_offset + p_filesz > len(elf): raise ValueError("ELF truncated")
    segs.append(PTLoad(paddr=p_paddr, data=elf[p_offset:p_offset + p_filesz], memsz=p_memsz))
  return segs
