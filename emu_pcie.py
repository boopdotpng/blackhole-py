"""EMU=1 backend: a mock PCIe Blackhole device backed by ttsim's `libttsim.so`.

Set `EMU=1` (together with slow dispatch, i.e. `TT_USB=1`) and `pcie.PCIDevice(...)`
transparently returns an `EmuPCIDevice`. No real hardware, VFIO, or `tt-metal` is
involved; kernels execute inside the in-process ttsim simulator.

How it maps onto ttsim
----------------------
`libttsim.so` *is* a mock PCIe endpoint. Its stable C ABI models the physical
interface only:

    libttsim_init() / libttsim_exit()
    libttsim_clock(n)                       # the sim only advances when clocked
    libttsim_pci_config_rd32(bdf, off)
    libttsim_pci_mem_rd_bytes(paddr, p, n)  # BAR memory, paddr = BARx_BASE + offset
    libttsim_pci_mem_wr_bytes(paddr, p, n)
    libttsim_set_pci_dma_mem_callbacks(rd, wr)

ttsim implements the TLB windows *and* the TLB config registers internally (the
same `0x1FC00000` region blackhole-py programs), so BAR bytes forwarded at
`BARx_BASE + offset` get NOC-routed by the simulator. Two wrinkles drive the
design here:

1. **ttsim's BAR-TLB decoder is unicast-only and strict.** It reads the target
   from the `x_end`/`y_end` fields and rejects nonzero `x_start`/`y_start`/
   `ordering` bits (it is deliberately more restrictive than silicon). blackhole-py
   sets `x_start == x_end == target` for unicast and uses BAR-level *multicast*
   for firmware boot / go-msg / reset. So we do not forward TLB configs verbatim:
   `configure_tlb` records the target in Python, and at access time we reprogram
   ttsim's TLB in the unicast form it accepts, **expanding multicast into a
   per-core loop**.

2. **The sim must be clocked.** Following tt-umd's driver, we pump
   `libttsim_clock(N)` after every read. blackhole-py's slow-dispatch poll loops
   (boot-done, go-msg done, DRAM barrier) thus advance the simulation naturally.

Only the slow-dispatch path is supported (no command queue / sysmem DMA).
"""
from __future__ import annotations

import ctypes
import os
import struct

import pcie
from pcie import (
  BoardInfo, PCIDevice, NocOrdering,
  TLB_2M_COUNT, TLB_2M_SIZE, TLB_4G_COUNT, TLB_4G_SIZE, TLB_REGS_START,
  dram_layout_for_board, tensix_columns_for_board, worker_cores_from_columns,
)
from ttk.addrs import Dram

# Physical BAR bases exported by libttsim (see ttsim/src/libttsim.cpp).
BAR0_BASE = 0x100000000
BAR2_BASE = 0x120000000
BAR4_BASE = 0x800000000

# BAR0 offset of the TLB config registers (identical to pcie.TLB_REGS_START).
TLB_CFG_BASE = TLB_REGS_START  # 0x1FC00000

# Clocks advanced per read. Larger = faster convergence of poll loops; overshoot
# is harmless (idle/finished cores just keep stepping). tt-umd uses 10.
DEFAULT_CLOCKS_PER_READ = 2000

# ctypes prototypes for the DMA-memory callbacks ttsim invokes (device -> host).
_DMA_RD_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)
_DMA_WR_CB = ctypes.CFUNCTYPE(None, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32)


def _default_lib_path() -> str:
  here = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(here, "libttsim_bh.so")
  if not os.path.exists(path):
    raise FileNotFoundError(
      f"ttsim simulator not found at {path}. Copy a Blackhole libttsim.so there "
      f"(e.g. from ttsim/src/_out/release_bh/libttsim.so).")
  return path


_LIB = None  # process-wide CDLL handle (libttsim has global state)


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
    lib.libttsim_pci_config_rd32.restype = ctypes.c_uint32
    lib.libttsim_pci_config_rd32.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    lib.libttsim_pci_mem_rd_bytes.restype = None
    lib.libttsim_pci_mem_rd_bytes.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32]
    lib.libttsim_pci_mem_wr_bytes.restype = None
    lib.libttsim_pci_mem_wr_bytes.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32]
    lib.libttsim_set_pci_dma_mem_callbacks.restype = None
    lib.libttsim_set_pci_dma_mem_callbacks.argtypes = [_DMA_RD_CB, _DMA_WR_CB]
    _LIB = lib
  return _LIB


class _Bar0View:
  """BAR0 byte access (`dev.bar0` / `dev.bar0_wc`), keyed by absolute BAR0 offset.

  blackhole-py reaches us via `tlb_window()` returning `(self, index * TLB_2M_SIZE)`,
  so a key is always `window_index * TLB_2M_SIZE + inner`. We route it through the
  device's TLB-aware emulation.
  """
  __slots__ = ("_dev",)

  def __init__(self, dev):
    self._dev = dev

  def __getitem__(self, key):
    if isinstance(key, slice):
      start = key.start or 0
      return self._dev._bar0_read(start, (key.stop if key.stop is not None else start) - start)
    return self._dev._bar0_read(key, 1)[0]

  def __setitem__(self, key, value):
    if isinstance(key, slice):
      self._dev._bar0_write(key.start or 0, bytes(value))
    else:
      self._dev._bar0_write(key, bytes((value & 0xFF,)))


class _Bar4WindowView:
  """One BAR4 4G aperture, keyed by the offset within the window (base is 0)."""
  __slots__ = ("_dev", "_window")

  def __init__(self, dev, window):
    self._dev, self._window = dev, window

  def __getitem__(self, key):
    if isinstance(key, slice):
      start = key.start or 0
      return self._dev._bar4_read(self._window, start, (key.stop if key.stop is not None else start) - start)
    return self._dev._bar4_read(self._window, key, 1)[0]

  def __setitem__(self, key, value):
    if isinstance(key, slice):
      self._dev._bar4_write(self._window, key.start or 0, bytes(value))
    else:
      self._dev._bar4_write(self._window, key, bytes((value & 0xFF,)))


class _Bar4Map:
  """Mimics pcie._MappedBar's `.view` / `.close()` contract for TLBWindow(4G)."""
  __slots__ = ("view",)

  def __init__(self, dev, window):
    self.view = _Bar4WindowView(dev, window)

  def close(self):
    pass


class EmuPCIDevice(PCIDevice):
  """A `PCIDevice` whose BAR/TLB I/O is served by ttsim instead of real hardware.

  Inherits `alloc_tlb`/`free_tlb` (pure bitmap logic) from PCIDevice and overrides
  every method that would otherwise touch VFIO/ARC/sysfs or the real BARs.
  """

  _running = False  # libttsim has process-global state; only one live sim.

  def __init__(self, index: int = 0, use_vfio: bool = True):
    if EmuPCIDevice._running:
      raise RuntimeError("an EMU device is already running in this process")
    self.lib = _load_lib()
    self._clocks_per_read = DEFAULT_CLOCKS_PER_READ

    # DMA callbacks must be installed before init. Slow dispatch never triggers
    # device->host DMA; install guards so a stray access fails loudly.
    self._install_dma_callbacks()
    self.lib.libttsim_init()
    EmuPCIDevice._running = True

    self._closed = False
    self.sysfs = None
    self.bdf = "emu:0000:00.0"

    # index -> {addr, xs, ys, xe, ye, mcast}; populated by configure_tlb.
    self._tlb_cfg: dict[int, dict] = {}
    self._bar0_view = _Bar0View(self)
    self.bar0 = self._bar0_view
    self.bar0_wc = self._bar0_view  # WC vs UC is irrelevant in simulation.
    self.bar2 = None
    self.bar0_u32 = None
    self.bar2_u32 = None

    # TLB allocation bitmaps (must match PCIDevice for inherited alloc/free_tlb).
    self._tlb_2m = [False] * TLB_2M_COUNT
    self._tlb_2m[TLB_2M_COUNT - 1] = True  # reserve index 201, as on real HW
    self._bar4_4g_count = TLB_4G_COUNT
    self._tlb_4g = [False] * self._bar4_4g_count

    # DMA pinning state (unused in slow dispatch, kept for API parity).
    self._iatu_regions = [False] * 16
    self._pinnings: dict[int, dict] = {}
    self._next_iova = 1 << 30

    # Host<->device DRAM coordinate agreement (see _build_dram_xlate).
    self._dram_xlate = self._build_dram_xlate()

  # ---- ttsim low-level I/O ----

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
    # ttsim's BH config region requires aligned 4-byte writes; emit 3 words.
    off = BAR0_BASE + TLB_CFG_BASE + lt_index * 12
    for i in range(3):
      self._wr32(off + i * 4, (val >> (32 * i)) & 0xFFFFFFFF)

  def _program_unicast_2m(self, lt_index: int, page: int, x: int, y: int):
    # Unicast 2M descriptor ttsim accepts: target in x_end/y_end, start=0.
    self._write_tlb_cfg(lt_index, (page & ((1 << 43) - 1)) | (x << 43) | (y << 49))

  def _program_unicast_4g(self, lt_index: int, page: int, x: int, y: int):
    self._write_tlb_cfg(lt_index, (page & 0xFFFFFFFF) | (x << 32) | (y << 38))

  @staticmethod
  def _targets(cfg: dict):
    if cfg["mcast"]:
      return [(x, y) for x in range(cfg["xs"], cfg["xe"] + 1)
              for y in range(cfg["ys"], cfg["ye"] + 1)]
    return [(cfg["xe"], cfg["ye"])]  # unicast target lives in x_end/y_end

  # ---- DRAM coordinate translation (host physical -> ttsim virtual) ----

  @staticmethod
  def _dram_bank_virtual_coords(harvested, ports=3):
    # Mirror ttk.addrs.build_bank_noc_table's per-bank `bank_xy` assignment so the
    # host targets the exact same DRAM tiles the device bank table (and kernels) use.
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
    # blackhole-py addresses DRAM from the host using *physical* NOC coords
    # (Dram.BANK_X / BANK_TILE_YS) while the device bank table uses *virtual* coords.
    # ttsim's DRAM remap is mirrored vs blackhole-py's physical convention, so the
    # only requirement for a correct round-trip is that host writes and device reads
    # land on the same ttsim tile per bank. We map each bank's host first-tile coord
    # to the same virtual coord build_bank_noc_table assigned to that bank.
    enabled_gddr, harvested = 0x7F, 7  # p100a (matches board_info())
    enabled_banks = [b for b in range(Dram.BANK_COUNT) if (enabled_gddr >> b) & 1]
    bank_xy = self._dram_bank_virtual_coords(harvested)
    xlate = {}
    for pos, bank in enumerate(enabled_banks):
      host = (Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][0])
      xlate[host] = bank_xy[pos]
    return xlate

  def _xlate_dram(self, x, y):
    v = self._dram_xlate.get((x, y))
    if v is None:
      raise RuntimeError(f"EMU: no DRAM virtual-coord mapping for physical NOC ({x},{y})")
    return v

  # ---- BAR0 (2M windows: L1 / NOC / MMIO regs) ----

  def _bar0_write(self, abs_off: int, data: bytes):
    window = abs_off // TLB_2M_SIZE
    cfg = self._tlb_cfg[window]
    page = cfg["addr"] >> 21
    for x, y in self._targets(cfg):
      self._program_unicast_2m(window, page, x, y)
      self._wr(BAR0_BASE + abs_off, data)

  def _bar0_read(self, abs_off: int, n: int) -> bytes:
    window = abs_off // TLB_2M_SIZE
    cfg = self._tlb_cfg[window]
    x, y = cfg["xe"], cfg["ye"]  # reads are always unicast
    self._program_unicast_2m(window, cfg["addr"] >> 21, x, y)
    data = self._rd(BAR0_BASE + abs_off, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  # ---- BAR4 (4G windows: DRAM) ----

  def _bar4_write(self, window: int, inner: int, data: bytes):
    lt = TLB_2M_COUNT + window
    cfg = self._tlb_cfg[lt]
    page = cfg["addr"] >> 32
    base = BAR4_BASE + window * TLB_4G_SIZE + inner
    for x, y in self._targets(cfg):  # DRAM writes are unicast in practice
      vx, vy = self._xlate_dram(x, y)
      self._program_unicast_4g(lt, page, vx, vy)
      self._wr(base, data)

  def _bar4_read(self, window: int, inner: int, n: int) -> bytes:
    lt = TLB_2M_COUNT + window
    cfg = self._tlb_cfg[lt]
    vx, vy = self._xlate_dram(cfg["xe"], cfg["ye"])
    self._program_unicast_4g(lt, cfg["addr"] >> 32, vx, vy)
    data = self._rd(BAR4_BASE + window * TLB_4G_SIZE + inner, n)
    self.lib.libttsim_clock(self._clocks_per_read)
    return data

  # ---- overridden PCIDevice surface ----

  def configure_tlb(self, index, addr, x_start, y_start, x_end, y_end,
                    noc=0, mcast=0, ordering=1, linked=0, static_vc=0):
    # Record only; the real (unicast) ttsim TLB is programmed lazily per access.
    self._tlb_cfg[index] = {"addr": addr, "xs": x_start, "ys": y_start,
                            "xe": x_end, "ye": y_end, "mcast": mcast}

  def tlb_window(self, index, wc=False):
    if index < TLB_2M_COUNT:
      return self._bar0_view, index * TLB_2M_SIZE
    raise RuntimeError("4G TLB windows are owned by TLBWindow(size=TLBWindow.SIZE_4G, wc=True)")

  def map_bar4_window(self, window, size=TLB_4G_SIZE):
    return _Bar4Map(self, window)

  def board_info(self, layout=None, fast_dispatch=False) -> BoardInfo:
    # Hardcoded p100a: 12 Tensix columns (120 cores), one harvested DRAM bank.
    board = "p100"
    columns = tensix_columns_for_board(board)
    workers = worker_cores_from_columns(columns)
    enabled_gddr = 0x7F  # bank 7 harvested
    effective_gddr, harvested_dram_bank = dram_layout_for_board(board, enabled_gddr)
    rightmost_x = columns[-1]
    prefetch_core = (rightmost_x, 2)
    dispatch_core = (rightmost_x, 3)
    cq_cores = {prefetch_core, dispatch_core}
    program_cores = [c for c in workers if not fast_dispatch or c not in cq_cores]
    return BoardInfo(
      board_id=0x43 << 36,
      arch="p100a",
      board=board,
      enabled_tensix_col=(1 << len(columns)) - 1,
      tensix_columns=columns,
      worker_cores=workers,
      program_cores=program_cores,
      enabled_gddr=effective_gddr,
      harvested_dram_bank=harvested_dram_bank,
      prefetch_core=prefetch_core,
      dispatch_core=dispatch_core,
    )

  def set_power_state(self, busy: bool):
    pass  # no ARC in the simulator

  def pin_pages(self, buf) -> int:
    raise NotImplementedError(
      "EMU supports slow dispatch only (no command queue / sysmem DMA). "
      "Run with TT_USB=1.")

  def unpin_pages(self, buf, noc_addr: int):
    pass

  def _install_dma_callbacks(self):
    def _rd(paddr, p, size):
      ctypes.memset(p, 0, size)  # slow dispatch never DMAs; zero-fill defensively

    def _wr(paddr, p, size):
      pass

    self._dma_rd = _DMA_RD_CB(_rd)  # keep refs alive
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
