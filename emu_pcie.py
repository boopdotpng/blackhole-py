"""EMU=1 tt-kmd-shaped backend backed by ttsim's Blackhole simulator.

`EMU=1` makes `pcie.PCIDevice(...)` return an `EmuPCIDevice` instead of opening
/dev/tenstorrent/N. The adapter exposes the same TLB lifecycle that tt-kmd
provides, while internally forwarding the mapped-window reads/writes into ttsim.
"""
from __future__ import annotations

import ctypes
import os
import struct
from collections.abc import Iterable

from pcie import (
  BoardInfo, PCIDevice,
  DEFAULT_GDDR_ENABLED, _build_board_info,
  TLB_2M_COUNT, TLB_2M_SIZE, TLB_4G_COUNT, TLB_4G_SIZE, TLB_REGS_START,
)
from ttk.addrs import Dram, p100_dram_bank_base_coords

BAR0_BASE = 0x100000000
BAR4_BASE = 0x800000000
TLB_CFG_BASE = TLB_REGS_START
DEFAULT_CLOCKS_PER_READ = int(os.environ.get("TTSIM_CLOCKS_PER_READ", "2000"))
P100_ENABLED_TENSIX_COL = 0x3FF5
P100_BOARD_ID = 0x43 << 36
P100_EMU_ENABLED_GDDR = 0x7F
P100_EMU_HARVESTED_DRAM_BANK = 7

_DMA_RD_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)
_DMA_WR_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)


def _p100_emu_dram_coords() -> dict[tuple[int, int], tuple[int, int]]:
  bank_base = p100_dram_bank_base_coords(P100_EMU_HARVESTED_DRAM_BANK)
  out = {}
  for bank in range(Dram.BANK_COUNT):
    if not ((P100_EMU_ENABLED_GDDR >> bank) & 1):
      continue
    vx, vy = bank_base[bank]
    for port, py in enumerate(Dram.BANK_TILE_YS[bank]):
      out[(Dram.BANK_X[bank], py)] = (vx, vy + port)
  return out


P100_EMU_DRAM_COORDS = _p100_emu_dram_coords()


def _existing(paths: Iterable[str]) -> str | None:
  for path in paths:
    path = os.path.expanduser(path)
    if os.path.exists(path):
      return path
  return None


def _ttsim_lib_candidates(path: str) -> list[str]:
  path = os.path.abspath(os.path.expanduser(path))
  if os.path.isfile(path):
    return [path]
  return [
    os.path.join(path, "sim-bh", "libttsim_bh.so"),
    os.path.join(path, "libttsim_bh.so"),
    os.path.join(path, "src", "_out", "release_bh", "libttsim.so"),
    os.path.join(path, "src", "_out", "debug_bh", "libttsim.so"),
  ]


def _default_lib_path() -> str:
  override = os.environ.get("TTSIM_LIB")
  if override:
    return override
  here = os.path.dirname(os.path.abspath(__file__))
  ttsim_path = os.environ.get("TTSIM_PATH")
  if ttsim_path:
    found = _existing(_ttsim_lib_candidates(ttsim_path))
    if found:
      return found
    raise FileNotFoundError(
      "Blackhole ttsim library not found under TTSIM_PATH. Build ttsim "
      "(from that checkout, run ./make.py :build), or set TTSIM_PATH to a "
      "directory containing a Blackhole simulator .so.")
  found = _existing([
    os.path.join(here, "libttsim_bh.so"),
    *(_ttsim_lib_candidates(os.path.join(here, "ttsim"))),
    os.path.expanduser("~/tenstorrent/ttsim/sim-bh/libttsim_bh.so"),
    os.path.expanduser("~/tenstorrent/ttsim/src/_out/release_bh/libttsim.so"),
    os.path.expanduser("~/tenstorrent/ttsim/src/_out/debug_bh/libttsim.so"),
  ])
  if found:
    return found
  raise FileNotFoundError(
    "Blackhole ttsim library not found. Build the bundled ttsim checkout "
    "(from ./ttsim, run ./make.py :build), build ~/tenstorrent/ttsim, or set "
    "TTSIM_PATH to a directory containing a Blackhole simulator .so.")


_LIB = None


def _load_lib():
  global _LIB
  if _LIB is None:
    lib = ctypes.CDLL(_default_lib_path())
    lib.libttsim_init.restype = None
    lib.libttsim_init.argtypes = []
    lib.libttsim_exit.restype = None
    lib.libttsim_exit.argtypes = []
    lib.libttsim_clock.restype = None
    lib.libttsim_clock.argtypes = [ctypes.c_uint32]
    lib.libttsim_pci_mem_rd_bytes.restype = None
    lib.libttsim_pci_mem_rd_bytes.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32]
    lib.libttsim_pci_mem_wr_bytes.restype = None
    lib.libttsim_pci_mem_wr_bytes.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32]
    lib.libttsim_set_pci_dma_mem_callbacks.restype = None
    lib.libttsim_set_pci_dma_mem_callbacks.argtypes = [_DMA_RD_CB, _DMA_WR_CB]
    if hasattr(lib, "libttsim_dump_t_state"):
      lib.libttsim_dump_t_state.restype = None
      lib.libttsim_dump_t_state.argtypes = []
    _LIB = lib
  return _LIB


class _EmuMapping:
  def __init__(self, dev: "EmuPCIDevice", kind: str, base: int, size: int):
    self.dev, self.kind, self.base, self.size = dev, kind, base, size
    self.closed = False

  def _check_range(self, offset: int, size: int):
    if offset < 0 or size < 0 or offset + size > self.size:
      raise ValueError(f"mapping range out of bounds: offset=0x{offset:x} size=0x{size:x} mapping_size=0x{self.size:x}")

  def __len__(self) -> int:
    return self.size

  def read(self, offset: int, size: int) -> bytes:
    self._check_range(offset, size)
    if self.kind == "bar0":
      return self.dev._bar0_read(self.base + offset, size)
    return self.dev._bar4_read(self.base, offset, size)

  def write(self, offset: int, data: bytes):
    data = bytes(data)
    self._check_range(offset, len(data))
    if self.kind == "bar0":
      self.dev._bar0_write(self.base + offset, data)
    else:
      self.dev._bar4_write(self.base, offset, data)

  def close(self):
    self.closed = True


class EmuPCIDevice(PCIDevice):
  _running = False

  def __init__(self, index: int = 0, use_vfio: bool = True):
    if index != 0:
      raise RuntimeError("EMU exposes one simulated Blackhole device at index 0")
    if EmuPCIDevice._running:
      raise RuntimeError("an EMU device is already running in this process")

    os.environ["TT_USB"] = "1"
    self.lib = _load_lib()
    self._clocks_per_read = DEFAULT_CLOCKS_PER_READ
    self._install_dma_callbacks()
    self.lib.libttsim_init()
    EmuPCIDevice._running = True

    self._closed = False
    self.index = index
    self.path = "emu:0000:00.0"
    self.sysfs = None
    self.bdf = "emu:0000:00.0"

    self._tlbs: dict[int, int] = {}
    self._tlb_2m = [False] * TLB_2M_COUNT
    self._tlb_2m[TLB_2M_COUNT - 1] = True
    self._tlb_4g = [False] * TLB_4G_COUNT
    self._pinnings: dict[int, tuple[int, int]] = {}

  def _wr(self, paddr: int, data: bytes):
    buf = (ctypes.c_char * len(data)).from_buffer_copy(data)
    self.lib.libttsim_pci_mem_wr_bytes(ctypes.c_uint64(paddr), buf, len(data))

  def _rd(self, paddr: int, n: int) -> bytes:
    buf = (ctypes.c_char * n)()
    self.lib.libttsim_pci_mem_rd_bytes(ctypes.c_uint64(paddr), buf, n)
    return bytes(buf)

  def _wr32(self, paddr: int, word: int):
    self._wr(paddr, struct.pack("<I", word & 0xFFFFFFFF))

  def _write_tlb_cfg(self, lt_index: int, val: int):
    off = BAR0_BASE + TLB_CFG_BASE + lt_index * 12
    for i in range(3):
      self._wr32(off + i * 4, (val >> (32 * i)) & 0xFFFFFFFF)

  @staticmethod
  def _ttsim_coord(x: int, y: int) -> tuple[int, int]:
    return P100_EMU_DRAM_COORDS.get((x, y), (x, y))

  def _bar0_write(self, abs_off: int, data: bytes):
    self._wr(BAR0_BASE + abs_off, data)

  def _bar0_read(self, abs_off: int, n: int) -> bytes:
    data = self._rd(BAR0_BASE + abs_off, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  def _bar4_write(self, window: int, inner: int, data: bytes):
    self._wr(BAR4_BASE + window * TLB_4G_SIZE + inner, data)

  def _bar4_read(self, window: int, inner: int, n: int) -> bytes:
    data = self._rd(BAR4_BASE + window * TLB_4G_SIZE + inner, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int,
                    x_end: int, y_end: int, noc: int = 0, mcast: int = 0,
                    ordering: int = 1, linked: int = 0, static_vc: int = 0):
    if index not in self._tlbs:
      raise RuntimeError(f"TLB {index} is not allocated by this EMU device")
    if noc or linked or static_vc:
      raise NotImplementedError("EMU/ttsim TLB configs support noc=0, linked=0, static_vc=0 only")
    x_end, y_end = self._ttsim_coord(x_end, y_end)
    x_start, y_start = self._ttsim_coord(x_start, y_start)
    if index < TLB_2M_COUNT:
      cfg_x_start = x_start if mcast else 0
      cfg_y_start = y_start if mcast else 0
      val = (
        ((addr >> 21) & ((1 << 43) - 1)) |
        ((x_end & 0x3F) << 43) | ((y_end & 0x3F) << 49) |
        ((cfg_x_start & 0x3F) << 55) | ((cfg_y_start & 0x3F) << 61) |
        ((mcast & 1) << 69) | ((ordering & 0x3) << 70)
      )
    else:
      if mcast:
        raise NotImplementedError("EMU/ttsim BAR4 TLB configs do not support multicast")
      val = (
        ((addr >> 32) & 0xFFFFFFFF) |
        ((x_end & 0x3F) << 32) | ((y_end & 0x3F) << 38) |
        ((ordering & 0x3) << 59)
      )
    self._write_tlb_cfg(index, val)

  def alloc_tlb(self, size: int) -> int:
    if size == TLB_2M_SIZE:
      for i, used in enumerate(self._tlb_2m):
        if not used:
          self._tlb_2m[i] = True
          self._tlbs[i] = size
          return i
      raise RuntimeError("EMU: no free 2M TLB slots")
    if size == TLB_4G_SIZE:
      for i, used in enumerate(self._tlb_4g):
        if not used:
          self._tlb_4g[i] = True
          index = TLB_2M_COUNT + i
          self._tlbs[index] = size
          return index
      raise RuntimeError("EMU: no free 4G TLB slots")
    raise ValueError(f"EMU: invalid TLB size: {size}")

  def free_tlb(self, index: int):
    size = self._tlbs.pop(index, None)
    if size is None:
      return
    if index < TLB_2M_COUNT:
      self._tlb_2m[index] = False
      return
    window = index - TLB_2M_COUNT
    if 0 <= window < len(self._tlb_4g):
      self._tlb_4g[window] = False

  def tlb_window(self, index: int, wc: bool = False) -> _EmuMapping:
    if index not in self._tlbs:
      raise RuntimeError(f"TLB {index} is not allocated by this EMU device")
    if index >= TLB_2M_COUNT:
      return _EmuMapping(self, "bar4", index - TLB_2M_COUNT, TLB_4G_SIZE)
    return _EmuMapping(self, "bar0", index * TLB_2M_SIZE, TLB_2M_SIZE)

  def map_bar4_window(self, window: int, size: int = TLB_4G_SIZE) -> _EmuMapping:
    return _EmuMapping(self, "bar4", window, size)

  def board_info(self, layout: dict | None = None, fast_dispatch: bool = False) -> BoardInfo:
    effective_gddr = P100_EMU_ENABLED_GDDR & DEFAULT_GDDR_ENABLED
    return _build_board_info("p100a", effective_gddr, fast_dispatch)

  def telemetry_layout(self) -> dict:
    return {}

  def telemetry_tag(self, layout: dict, tag: str | int) -> int | None:
    tag_id = {"BOARD_ID_HIGH": 1, "BOARD_ID_LOW": 2, "ENABLED_TENSIX_COL": 34, "ENABLED_GDDR": 36}.get(tag, tag)
    if tag_id == 1:
      return (P100_BOARD_ID >> 32) & 0xFFFFFFFF
    if tag_id == 2:
      return P100_BOARD_ID & 0xFFFFFFFF
    if tag_id == 34:
      return P100_ENABLED_TENSIX_COL
    if tag_id == 36:
      return P100_EMU_ENABLED_GDDR
    return None

  def set_power_state(self, busy: bool):
    pass

  def dump_t_state(self):
    if hasattr(self.lib, "libttsim_dump_t_state"):
      self.lib.libttsim_dump_t_state()

  def pin_pages(self, buf, preferred_iatu_region: int | None = None) -> int:
    raise NotImplementedError("EMU supports slow dispatch only; EMU=1 forces TT_USB=1.")

  def unpin_pages(self, buf, noc_addr: int):
    pass

  def _install_dma_callbacks(self):
    def _rd(paddr, p, size):
      ctypes.memset(p, 0, size)

    def _wr(paddr, p, size):
      pass

    self._dma_rd = _DMA_RD_CB(_rd)
    self._dma_wr = _DMA_WR_CB(_wr)
    self.lib.libttsim_set_pci_dma_mem_callbacks(self._dma_rd, self._dma_wr)

  def close(self):
    if getattr(self, "_closed", True):
      return
    self._closed = True
    try:
      for tlb in list(self._tlbs):
        self.free_tlb(tlb)
      self.lib.libttsim_exit()
    finally:
      EmuPCIDevice._running = False

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    self.close()
