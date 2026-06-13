from __future__ import annotations
import ctypes
import mmap
import os
import struct
import time
from cq import (
  CQ_COMPLETION_Q0_EVENT, CQ_COMPLETION_Q1_EVENT, CQ_COMPLETION_RD_PTR, CQ_COMPLETION_WR_PTR,
  CQ_DISPATCH_CB_PAGES, CQ_DISPATCH_SYNC_SEM, CommandQueue,
)
from dram import Allocator, DramBuffer, Shape, tilize, untilize
import fw
from ttk.addrs import Core, L1_ALIGN, align_down, align_up, as_bytes
from ttk.noc import NOC
from ttk.tensix import TensixL1, TensixMMIO
from pcie import BoardInfo, Mapping, NOC_PCIE_OFFSET, PCIDevice, PCIE_NOC_XY, TLBWindow
from program import (
  DevMsgs, Dtype, FAST_CQ_NUM_CIRCULAR_BUFFERS, GoMsg, IRCommand, LaunchMsg,
  McastMmioWrite32, McastWrite, PollL1Byte, Program, Run, UnicastWrite,
  lower_firmware_boot, mcast_rects,
)

class Device:
  def __init__(self, index: int = 0):
    self.fast_dispatch = os.environ.get("TT_USB") != "1"
    self.dev = PCIDevice(index=index, use_vfio=self.fast_dispatch)
    self.board_info: BoardInfo = self.dev.board_info(fast_dispatch=self.fast_dispatch)
    self.programs: list[Program] = []
    self.dram = Allocator(self.dev, self.board_info.dram_tiles)
    self.cq: CommandQueue | None = None
    self._dram_sysmem: DramSysmem | None = None
    self._dram_fill_kernel = None
    self._dram_drain_kernel = None
    self.dev.set_power_state(True)  # session-scoped; close() powers down
    self._upload_firmware()
    if self.fast_dispatch:
      self._start_dispatch_cores()

  @property
  def cores(self) -> list[Core]:
    return list(self.board_info.program_cores)

  def close(self):
    if self.cq is not None:
      self._halt_cores()
      self.cq.close()
      self.cq = None
    if self._dram_sysmem is not None:
      self._dram_sysmem.close()
      self._dram_sysmem = None
    self.dram.close()
    self.dev.set_power_state(False)
    self.dev.close()

  def _upload_firmware(self):
    core_fw = fw.build_all()
    commands = lower_firmware_boot(
      core_fw,
      self.board_info.worker_cores,
      self.board_info.harvested_dram_bank,
    )
    run_ir = getattr(self.dev, "run_ir", None)
    if run_ir is not None:
      run_ir(commands)
      return
    start = self.board_info.worker_cores[0]
    with TLBWindow(self.dev, start=start) as win:
      self._run_slow_ir(commands, win)

  def queue(self, program: Program):
    self.programs.append(program)
    return self

  def run(self, program: Program | None = None):
    if program is not None:
      self.queue(program)
    if not self.programs:
      return []
    try:
      if not self.fast_dispatch:
        return self._run_slow_dispatch()
      return self._run_fast_dispatch()
    finally:
      self.programs.clear()

  def _run_slow_ir(self, commands: list[IRCommand], win: TLBWindow):
    for cmd in commands:
      match cmd:
        case UnicastWrite(cores=cores, addr=addr, data=data):
          for core, blob in zip(cores, data):
            win.target(core)
            win.write(addr, blob)
        case McastWrite(rects=rects, addr=addr, data=data):
          for x0, x1, y0, y1 in rects:
            win.target((x0, y0), (x1, y1))
            win.write(addr, data)
        case McastMmioWrite32(rects=rects, addr=addr, value=value):
          mmio_base, _ = align_down(addr, TLBWindow.SIZE_2M)
          for x0, x1, y0, y1 in rects:
            win.target((x0, y0), (x1, y1), addr=mmio_base)
            win.write(addr - mmio_base, struct.pack("<I", value & 0xFFFFFFFF))
        case PollL1Byte(core=core, addr=addr, value=value, timeout_s=timeout_s):
          win.target(core)
          deadline = time.perf_counter() + timeout_s
          while win.read(addr, 1)[0] != value:
            if time.perf_counter() > deadline:
              raise TimeoutError(f"timeout waiting for L1[0x{addr:x}] == 0x{value:02x} on core {core}")
            time.sleep(0.001)
        case Run(cores=cores):
          go = GoMsg()
          go.bits.signal = DevMsgs.RUN_MSG_GO
          go_blob = struct.pack("<I", go.all)
          timeout_s = float(os.environ.get("BLACKHOLE_RUN_TIMEOUT_S", "10.0"))
          for x0, x1, y0, y1 in mcast_rects(cores):
            win.target((x0, y0), (x1, y1))
            win.write(TensixL1.GO_MSG, go_blob)
          for core in cores:
            win.target(core)
            deadline = time.perf_counter() + timeout_s
            while win.read(TensixL1.GO_MSG + 3, 1)[0] != DevMsgs.RUN_MSG_DONE:
              if time.perf_counter() > deadline:
                dump = getattr(self.dev, "dump_t_state", None)
                if dump is not None:
                  dump()
                raise TimeoutError(f"timeout waiting for core {core}")
              time.sleep(0.001)

  def _run_slow_dispatch(self):
    cores = self.cores
    run_ir = getattr(self.dev, "run_ir", None)
    if run_ir is not None:
      for program in self.programs:
        run_ir(program.lower(cores, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST))
      return []
    with TLBWindow(self.dev, start=cores[0]) as win:
      for program in self.programs:
        self._run_slow_ir(program.lower(cores, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST), win)
    return []

  def _run_fast_dispatch(self):
    if self.cq is None:
      raise RuntimeError("fast dispatch is not initialized")
    cores = self.cores
    programs = [
      program.lower(cores, dispatch_mode=DevMsgs.DISPATCH_MODE_DEV, host_assigned_id=i)
      for i, program in enumerate(self.programs)
    ]
    return self.cq.submit_ir(programs, self._go_word(), names=[getattr(p, "name", "") for p in self.programs])

  def recover_dispatch(self):
    """Full CQ recovery after a wedged program: reset workers + CQ cores,
    re-upload firmware, restart dispatch with the SAME pinned sysmem so
    pre-encoded CQ records remain valid. DRAM contents are untouched."""
    self._halt_cores()
    self._upload_firmware()
    sysm = self.cq.sysmem
    sysm.issue_wr = 0
    sysm.prefetch_q_wr_idx = 0
    sysm.dispatch_cb_page_pos = 0
    sysm.event_id = 0
    sysm.completion_rd_16b = sysm.completion_base_16b
    sysm.completion_rd_toggle = 0
    import cq as cq_mod
    sysm.prefetch_win.write(cq_mod.CQ_PREFETCH_Q_RD_PTR,
                            struct.pack("<I", cq_mod.CQ_PREFETCH_Q_BASE + cq_mod.CQ_PREFETCH_Q_SIZE))
    sysm.prefetch_win.write(cq_mod.CQ_PREFETCH_Q_PCIE_RD,
                            struct.pack("<I", (sysm.noc_local + cq_mod._HOST_ISSUE_BASE) & 0xFFFFFFFF))
    sysm.prefetch_win.write(cq_mod.CQ_PREFETCH_Q_BASE, bytes(cq_mod.CQ_PREFETCH_Q_SIZE))
    sysm.write_sysmem32(cq_mod._HOST_CQ_WR_OFF, sysm.completion_base_16b)
    sysm.write_sysmem32(cq_mod._HOST_CQ_RD_OFF, sysm.completion_base_16b)
    self._boot_dispatch_cores()

  def _start_dispatch_cores(self):
    prefetch_core = self.board_info.prefetch_core
    dispatch_core = self.board_info.dispatch_core
    self.cq = CommandQueue(self.dev, prefetch_core, dispatch_core)
    self._boot_dispatch_cores()

  def _boot_dispatch_cores(self):
    prefetch_core = self.board_info.prefetch_core
    dispatch_core = self.board_info.dispatch_core

    from fw import cq as cq_fw

    kernel_off = L1_ALIGN + 2 * L1_ALIGN
    prefetch_img = b"\0" * L1_ALIGN + struct.pack("<I", CQ_DISPATCH_CB_PAGES).ljust(L1_ALIGN, b"\0") + b"\0" * L1_ALIGN
    prefetch_segments = cq_fw.build_prefetch().compile()
    dispatch_segments = cq_fw.build_dispatch().compile()

    self._upload_cq_core(
      prefetch_core,
      prefetch_img,
      self._build_cq_launch(kernel_off, sem_off=L1_ALIGN),
      [(kernel_off, prefetch_segments)],
    )

    dispatch_win = self.cq.dispatch_win
    dispatch_win.target(dispatch_core)
    base_16b = self.cq.completion_base_16b
    dispatch_win.write(CQ_COMPLETION_WR_PTR, struct.pack("<I", base_16b))
    dispatch_win.write(CQ_COMPLETION_RD_PTR, struct.pack("<I", base_16b))
    dispatch_win.write(CQ_COMPLETION_Q0_EVENT, struct.pack("<I", 0))
    dispatch_win.write(CQ_COMPLETION_Q1_EVENT, struct.pack("<I", 0))
    dispatch_win.write(CQ_DISPATCH_SYNC_SEM, b"\0" * (8 * L1_ALIGN))

    dispatch_img = b"\0" * (3 * L1_ALIGN)
    self._upload_cq_core(
      dispatch_core,
      dispatch_img,
      self._build_cq_launch(kernel_off, sem_off=L1_ALIGN, brisc_noc_id=1),
      [(kernel_off, dispatch_segments)],
    )

  def _upload_cq_core(self, core: Core, image: bytes, launch: LaunchMsg, kernels: list[tuple[int, list]]):
    assert self.cq is not None
    win = self.cq.prefetch_win if core == self.board_info.prefetch_core else self.cq.dispatch_win
    win.target(core)
    win.write(TensixL1.KERNEL_CONFIG_BASE, image)
    for base, segments in kernels:
      for segment in segments:
        win.write(TensixL1.KERNEL_CONFIG_BASE + base + segment.addr, segment.data)
    win.write(TensixL1.LAUNCH, as_bytes(launch))
    go = GoMsg()
    go.bits.signal = DevMsgs.RUN_MSG_GO
    win.write(TensixL1.GO_MSG, struct.pack("<I", go.all))

  @staticmethod
  def _build_cq_launch(brisc_text_off: int, sem_off: int = 16, brisc_noc_id: int = 0) -> LaunchMsg:
    launch = LaunchMsg()
    cfg = launch.kernel_config
    for i in range(DevMsgs.ProgrammableCoreType_COUNT):
      cfg.kernel_config_base[i] = TensixL1.KERNEL_CONFIG_BASE
    cfg.sem_offset[0] = sem_off
    cfg.rta_offset[0].rta_offset = 0
    cfg.rta_offset[0].crta_offset = L1_ALIGN
    cfg.kernel_text_offset[0] = brisc_text_off
    cfg.enables = 1
    cfg.brisc_noc_id = brisc_noc_id
    cfg.mode = DevMsgs.DISPATCH_MODE_HOST
    cfg.min_remote_cb_start_index = FAST_CQ_NUM_CIRCULAR_BUFFERS
    return launch

  def _go_word(self) -> int:
    go = GoMsg()
    go.bits.signal = DevMsgs.RUN_MSG_GO
    go.bits.master_x, go.bits.master_y = self.board_info.dispatch_core
    return go.all

  def _halt_cores(self):
    cores = self.board_info.worker_cores
    mmio_base, _ = align_down(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TLBWindow.SIZE_2M)
    reset_off = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - mmio_base
    with TLBWindow(self.dev, start=cores[0], addr=mmio_base) as win:
      for x0, x1, y0, y1 in mcast_rects(cores):
        win.target((x0, y0), (x1, y1), addr=mmio_base)
        win.write(reset_off, struct.pack("<I", TensixMMIO.SOFT_RESET_ALL))

  def alloc_write(self, data: bytes, dtype: Dtype, shape: Shape, name: str = "") -> DramBuffer:
    buf = self.dram.alloc(len(data) // dtype.tile_size, dtype, name, shape)
    self.dram_write(buf, data)
    return buf

  def _ensure_dram_sysmem(self, required_size: int) -> "DramSysmem":
    max_size = 1 << 30
    if required_size > max_size:
      raise ValueError(f"DRAM transfer needs {required_size} bytes, max sysmem buffer is {max_size} bytes")
    size = align_up(required_size, mmap.PAGESIZE)
    if self._dram_sysmem is not None and self._dram_sysmem.size >= size:
      return self._dram_sysmem
    if self._dram_sysmem is not None:
      self._dram_sysmem.close()
    self._dram_sysmem = DramSysmem(self.dev, size)
    return self._dram_sysmem

  def _empty_kernel(self):
    from asm import KernelBase

    return KernelBase()

  def _dram_fill(self):
    if self._dram_fill_kernel is None:
      from fw.dram import build_fill

      self._dram_fill_kernel = build_fill()
    return self._dram_fill_kernel

  def _dram_drain(self):
    if self._dram_drain_kernel is None:
      from fw.dram import build_drain

      self._dram_drain_kernel = build_drain()
    return self._dram_drain_kernel

  def _run_dram_transfer(self, buf: DramBuffer, kernel, n_tiles: int, *, name: str):
    if n_tiles <= 0:
      return
    if not self.fast_dispatch:
      raise RuntimeError("DRAM transfer kernels require fast dispatch")
    if self.cq is None:
      raise RuntimeError("fast dispatch is not initialized")
    if self.programs:
      self.run()

    sm = self._ensure_dram_sysmem(n_tiles * buf.page_size)
    noc_local = sm.noc_addr - NOC_PCIE_OFFSET
    if noc_local < 0:
      raise RuntimeError(f"bad DRAM sysmem NOC address: 0x{sm.noc_addr:x}")
    if (noc_local & 0xFFFFFFFF) + n_tiles * buf.page_size > (1 << 32):
      raise RuntimeError("DRAM sysmem transfer crossed a 4GB NOC window")

    cores = self.cores[:min(len(self.cores), n_tiles)]
    tiles_per_core = (n_tiles + len(cores) - 1) // len(cores)
    core_index = {core: i for i, core in enumerate(cores)}
    bank_count = len(self.dram.bank_tiles)
    sysmem_lo = noc_local & 0xFFFFFFFF
    sysmem_mid = NOC.PCIE_MID | ((noc_local >> 32) & 0xF)

    kernel.rta(lambda x, y: [
      buf.addr, (1 << 24) | PCIE_NOC_XY, sysmem_lo, sysmem_mid,
      core_index[(x, y)] * tiles_per_core,
      max(0, min(tiles_per_core, n_tiles - core_index[(x, y)] * tiles_per_core)),
      buf.page_size, bank_count,
    ])

    empty = self._empty_kernel()
    program = Program(
      brisc=empty,
      ncrisc=kernel,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      cbs=[(0, buf.page_size, 2)],
      num_cores=len(cores),
    )
    program.name = name
    ir = program.lower(self.cores, dispatch_mode=DevMsgs.DISPATCH_MODE_DEV)
    self.cq.submit_ir([ir], self._go_word(), names=[name])

  @staticmethod
  def _buffer_nbytes(data) -> int:
    return memoryview(data).nbytes

  @staticmethod
  def _copy_bytes_to(dst, data: bytes) -> int:
    view = memoryview(dst)
    if view.readonly:
      raise ValueError("destination buffer must be writable")
    if not view.c_contiguous:
      raise ValueError("destination buffer must be C-contiguous")
    if view.nbytes < len(data):
      raise ValueError(f"destination buffer too small: need {len(data)} bytes, have {view.nbytes}")
    dst_addr = ctypes.addressof(ctypes.c_char.from_buffer(view))
    ctypes.memmove(ctypes.c_void_p(dst_addr), ctypes.c_char_p(data), ctypes.c_size_t(len(data)))
    return len(data)

  def _prepare_write_data(self, buf: DramBuffer, data, *, tiled: bool):
    if buf.shape is not None and not tiled:
      return tilize(data, buf.dtype.bpe, buf.shape)
    return data

  def dram_write(self, buf: DramBuffer, data: bytes):
    return self.dram_write_from(buf, data)

  def dram_write_from(self, buf: DramBuffer, data, *, tiled: bool = False):
    data = self._prepare_write_data(buf, data, tiled=tiled)
    data_size = self._buffer_nbytes(data)
    assert data_size <= buf.size
    if self.fast_dispatch:
      n_tiles = (data_size + buf.page_size - 1) // buf.page_size
      transfer_size = n_tiles * buf.page_size
      sm = self._ensure_dram_sysmem(transfer_size)
      sm.mapping.copy_from(0, data, data_size)
      if transfer_size > data_size:
        sm.mapping.view_at(data_size, transfer_size - data_size)[:] = b"\0" * (transfer_size - data_size)
      sm.mapping.flush(0, transfer_size)
      self._run_dram_transfer(buf, self._dram_fill(), n_tiles, name=f"dram_fill:{buf.name}")
      return
    self.dram.write(buf, data)

  def _drain_to_sysmem(self, buf: DramBuffer) -> "DramSysmem":
    if self.programs:
      self.run()
    sm = self._ensure_dram_sysmem(buf.size)
    self._run_dram_transfer(buf, self._dram_drain(), buf.num_tiles, name=f"dram_drain:{buf.name}")
    return sm

  def dram_read(self, buf: DramBuffer) -> bytes:
    if self.fast_dispatch:
      sm = self._drain_to_sysmem(buf)
      data = sm.mapping.read(0, buf.size)
    else:
      if self.programs:
        self.run()
      data = self.dram.read(buf)
    if buf.shape is not None:
      return untilize(data, buf.dtype.bpe, buf.shape)
    return data

  def dram_read_into(self, buf: DramBuffer, dst, *, tiled: bool = False) -> int:
    if self.fast_dispatch and (buf.shape is None or tiled):
      sm = self._drain_to_sysmem(buf)
      return sm.mapping.copy_to(0, dst, buf.size)

    data = self.dram_read(buf)
    return self._copy_bytes_to(dst, data)


class DramSysmem:
  def __init__(self, dev: PCIDevice, size: int = 1 << 30):
    self.dev = dev
    self.mapping = Mapping(size)
    self.size = self.mapping.size
    self.noc_addr = dev.pin_pages(self.mapping, preferred_iatu_region=0)

  def close(self):
    try:
      self.dev.unpin_pages(self.mapping, self.noc_addr)
    finally:
      self.mapping.close()
