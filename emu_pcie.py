"""EMU=1 PCIe backend backed by ttsim's Blackhole simulator.

`EMU=1` makes `pcie.PCIDevice(...)` return an `EmuPCIDevice` instead of opening
sysfs/VFIO resources. The adapter forwards BAR reads/writes into ttsim and
keeps blackhole-py's existing slow-dispatch TLBWindow/DRAM code unchanged.
"""
from __future__ import annotations

import ctypes
import os
import struct
from collections.abc import Iterable

from pcie import (
  BoardInfo, PCIDevice,
  DEFAULT_GDDR_ENABLED, P100_TENSIX_X,
  TLB_2M_COUNT, TLB_2M_SIZE, TLB_4G_COUNT, TLB_4G_SIZE, TLB_REGS_START,
)
from ttk.addrs import Dram

BAR0_BASE = 0x100000000
BAR4_BASE = 0x800000000
TLB_CFG_BASE = TLB_REGS_START
DEFAULT_CLOCKS_PER_READ = int(os.environ.get("TTSIM_CLOCKS_PER_READ", "2000"))

_DMA_RD_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)
_DMA_WR_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)


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
    _LIB = lib
  return _LIB


class _EmuMapping:
  def __init__(self, dev: "EmuPCIDevice", kind: str, base: int, size: int):
    self.dev, self.kind, self.base, self.size = dev, kind, base, size
    self.closed = False

  def _check_range(self, offset: int, size: int):
    if offset < 0 or size < 0 or offset + size > self.size:
      raise ValueError(f"mapping range out of bounds: offset=0x{offset:x} size=0x{size:x} mapping_size=0x{self.size:x}")

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
    self.sysfs = None
    self.bdf = "emu:0000:00.0"
    self.bar0 = self.bar0_wc = self.bar2 = None
    self.bar0_u32 = self.bar2_u32 = None
    self._has_vfio = False
    self._unbind_vfio_on_close = False

    self._tlb_cfg: dict[int, dict] = {}
    self._tlb_2m = [False] * TLB_2M_COUNT
    self._tlb_2m[TLB_2M_COUNT - 1] = True
    self._bar4_4g_count = TLB_4G_COUNT
    self._tlb_4g = [False] * self._bar4_4g_count
    self._iatu_regions = [False] * 16
    self._pinnings: dict[int, dict] = {}
    self._next_iova = 1 << 30
    self._dram_xlate = self._build_dram_xlate()

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

  def _program_unicast_2m(self, lt_index: int, page: int, x: int, y: int):
    self._write_tlb_cfg(lt_index, (page & ((1 << 43) - 1)) | (x << 43) | (y << 49))

  def _program_unicast_4g(self, lt_index: int, page: int, x: int, y: int):
    self._write_tlb_cfg(lt_index, (page & 0xFFFFFFFF) | (x << 32) | (y << 38))

  @staticmethod
  def _targets(cfg: dict):
    if cfg["mcast"]:
      return [(x, y) for x in range(cfg["xs"], cfg["xe"] + 1)
              for y in range(cfg["ys"], cfg["ye"] + 1)]
    return [(cfg["xe"], cfg["ye"])]

  @staticmethod
  def _dram_bank_virtual_coords(harvested: int | None, ports: int = 3):
    if harvested is None:
      return {b: (17 if b < 4 else 18, 12 + (b % 4) * ports) for b in range(Dram.BANK_COUNT)}
    h, half = harvested, 4
    mirror = h + half - 1 if h < half else h - half
    if h < half:
      right = list(range(half - 1))
      left = [b for b in range(half - 1, Dram.BANK_COUNT - 1) if b != mirror] + [mirror]
    else:
      left = [b for b in range(half) if b != mirror] + [mirror]
      right = list(range(half, Dram.BANK_COUNT - 1))
    bank_xy = {b: (18, 12 + i * ports) for i, b in enumerate(right)}
    bank_xy.update({b: (17, 12 + i * ports) for i, b in enumerate(left)})
    return bank_xy

  def _build_dram_xlate(self):
    enabled_gddr, harvested = 0x7F, 7
    enabled_banks = [b for b in range(Dram.BANK_COUNT) if (enabled_gddr >> b) & 1]
    bank_xy = self._dram_bank_virtual_coords(harvested)
    bank_port = [[2, 1], [0, 1], [0, 1], [0, 1], [2, 1], [2, 1], [2, 1], [2, 1]]
    xlate = {}
    for pos, bank in enumerate(enabled_banks):
      host = (Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][0])
      vx, vy = bank_xy[pos]
      ports = tuple((vx, vy + port) for port in range(Dram.TILES_PER_BANK))
      read_port = (vx, vy + bank_port[pos][1])
      xlate[host] = {"read": read_port, "write": ports}
    return xlate

  def _xlate_dram(self, x: int, y: int) -> dict:
    v = self._dram_xlate.get((x, y))
    if v is None:
      raise RuntimeError(f"EMU: no DRAM virtual-coord mapping for physical NOC ({x},{y})")
    return v

  def _bar0_write(self, abs_off: int, data: bytes):
    window = abs_off // TLB_2M_SIZE
    cfg = self._tlb_cfg[window]
    for x, y in self._targets(cfg):
      self._program_unicast_2m(window, cfg["addr"] >> 21, x, y)
      self._wr(BAR0_BASE + abs_off, data)

  def _bar0_read(self, abs_off: int, n: int) -> bytes:
    window = abs_off // TLB_2M_SIZE
    cfg = self._tlb_cfg[window]
    self._program_unicast_2m(window, cfg["addr"] >> 21, cfg["xe"], cfg["ye"])
    data = self._rd(BAR0_BASE + abs_off, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  def _bar4_write(self, window: int, inner: int, data: bytes):
    lt = TLB_2M_COUNT + window
    cfg = self._tlb_cfg[lt]
    base = BAR4_BASE + window * TLB_4G_SIZE + inner
    for x, y in self._targets(cfg):
      for vx, vy in self._xlate_dram(x, y)["write"]:
        self._program_unicast_4g(lt, cfg["addr"] >> 32, vx, vy)
        self._wr(base, data)

  def _bar4_read(self, window: int, inner: int, n: int) -> bytes:
    lt = TLB_2M_COUNT + window
    cfg = self._tlb_cfg[lt]
    vx, vy = self._xlate_dram(cfg["xe"], cfg["ye"])["read"]
    self._program_unicast_4g(lt, cfg["addr"] >> 32, vx, vy)
    data = self._rd(BAR4_BASE + window * TLB_4G_SIZE + inner, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int,
                    x_end: int, y_end: int, noc: int = 0, mcast: int = 0,
                    ordering: int = 1, linked: int = 0, static_vc: int = 0):
    self._tlb_cfg[index] = {
      "addr": addr, "xs": x_start, "ys": y_start, "xe": x_end, "ye": y_end,
      "mcast": mcast,
    }

  def tlb_window(self, index: int, wc: bool = False) -> _EmuMapping:
    if index >= TLB_2M_COUNT:
      raise RuntimeError("4G TLB windows are owned by TLBWindow(size=TLBWindow.SIZE_4G, wc=True)")
    return _EmuMapping(self, "bar0", index * TLB_2M_SIZE, TLB_2M_SIZE)

  def map_bar4_window(self, window: int, size: int = TLB_4G_SIZE) -> _EmuMapping:
    return _EmuMapping(self, "bar4", window, size)

  def board_info(self, layout: dict | None = None, fast_dispatch: bool = False) -> BoardInfo:
    columns = P100_TENSIX_X
    workers = [(x, y) for x in columns for y in range(2, 12)]
    rightmost_x = columns[-1]
    prefetch_core = (rightmost_x, 2)
    dispatch_core = (rightmost_x, 3)
    cq_cores = {prefetch_core, dispatch_core}
    effective_gddr = 0x7F & DEFAULT_GDDR_ENABLED
    harvested = [bank for bank in range(8) if ((effective_gddr >> bank) & 1) == 0]
    bank_ys = (
      (0, 1, 11), (2, 3, 10), (4, 8, 9), (5, 6, 7),
      (0, 1, 11), (2, 3, 10), (4, 8, 9), (5, 6, 7),
    )
    return BoardInfo(
      board="p100a",
      worker_cores=workers,
      program_cores=[core for core in workers if not fast_dispatch or core not in cq_cores],
      dram_tiles=[
        (bank, 0 if bank < 4 else 9, y)
        for bank in range(8)
        if (effective_gddr >> bank) & 1
        for y in bank_ys[bank]
      ],
      prefetch_core=prefetch_core,
      dispatch_core=dispatch_core,
      harvested_dram_bank=harvested[0] if harvested else None,
    )

  def telemetry_layout(self) -> dict:
    return {}

  def set_power_state(self, busy: bool):
    pass

  def pin_pages(self, buf) -> int:
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
      self.lib.libttsim_exit()
    finally:
      EmuPCIDevice._running = False

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    self.close()
