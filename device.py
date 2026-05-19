from __future__ import annotations
import os
import struct
import time
from cq import (
  CQ_COMPLETION_Q0_EVENT, CQ_COMPLETION_Q1_EVENT, CQ_COMPLETION_RD_PTR, CQ_COMPLETION_WR_PTR,
  CQ_DISPATCH_CB_PAGES, CQ_DISPATCH_SYNC_SEM, CommandQueue,
)
from dram import Allocator, DramBuffer, Shape, tilize, untilize
import fw
from l1 import Core, Dram, L1_ALIGN, TensixL1, TensixMMIO, align_down, align_up, as_bytes
from pcie import BoardInfo, PCIDevice, TLBWindow
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
    self.dram = Allocator(self.dev, self._dram_tiles())
    self.cq: CommandQueue | None = None
    self._upload_firmware()
    if self.fast_dispatch:
      self._start_dispatch_cores()

  @property
  def cores(self) -> list[Core]:
    return list(self.board_info.program_cores)

  def close(self):
    self.dev.set_power_state(False)
    if self.cq is not None:
      self._halt_cores()
      self.cq.close()
    self.dram.close()
    self.dev.close()

  def _dram_tiles(self) -> list[tuple[int, int, int]]:
    return [
      (bank, Dram.BANK_X[bank], y)
      for bank in range(Dram.BANK_COUNT)
      if (self.board_info.enabled_gddr >> bank) & 1
      for y in Dram.BANK_TILE_YS[bank]
    ]

  def _upload_firmware(self):
    core_fw = fw.build_all()
    commands = lower_firmware_boot(
      core_fw,
      self.board_info.worker_cores,
      self.board_info.harvested_dram_bank,
    )
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
    self.dev.set_power_state(True)
    try:
      if not self.fast_dispatch:
        return self._run_slow_dispatch()
      return self._run_fast_dispatch()
    finally:
      self.programs.clear()
      self.dev.set_power_state(False)

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
            win.write32(addr - mmio_base, value)
        case PollL1Byte(core=core, addr=addr, value=value, timeout_s=timeout_s):
          win.target(core)
          deadline = time.perf_counter() + timeout_s
          while win.mm[addr] != value:
            if time.perf_counter() > deadline:
              raise TimeoutError(f"timeout waiting for L1[0x{addr:x}] == 0x{value:02x} on core {core}")
            time.sleep(0.001)
        case Run(cores=cores):
          go = GoMsg()
          go.bits.signal = DevMsgs.RUN_MSG_GO
          go_blob = struct.pack("<I", go.all)
          for x0, x1, y0, y1 in mcast_rects(cores):
            win.target((x0, y0), (x1, y1))
            win.write(TensixL1.GO_MSG, go_blob)
          for core in cores:
            win.target(core)
            deadline = time.perf_counter() + 10.0
            while win.mm[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
              if time.perf_counter() > deadline:
                raise TimeoutError(f"timeout waiting for core {core}")
              time.sleep(0.001)

  def _run_slow_dispatch(self):
    timings = []
    cores = self.cores
    with TLBWindow(self.dev, start=cores[0]) as win:
      for program in self.programs:
        t0 = time.perf_counter()
        self._run_slow_ir(program.lower(cores, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST), win)
        elapsed_us = (time.perf_counter() - t0) * 1e6
        timings.append({
          "cycles": 0,
          "us": elapsed_us,
          "freq_mhz": 1350,
          "name": getattr(program, "name", ""),
        })
    return timings

  def _run_fast_dispatch(self):
    if self.cq is None:
      raise RuntimeError("fast dispatch is not initialized")
    cores = self.cores
    programs = [
      program.lower(cores, dispatch_mode=DevMsgs.DISPATCH_MODE_DEV, host_assigned_id=i)
      for i, program in enumerate(self.programs)
    ]
    return self.cq.submit_ir(programs, self._go_word(), names=[getattr(p, "name", "") for p in self.programs])

  def _start_dispatch_cores(self):
    prefetch_core = self.board_info.prefetch_core
    dispatch_core = self.board_info.dispatch_core
    self.cq = CommandQueue(self.dev, prefetch_core, dispatch_core)

    from fw import cq as cq_fw

    kernel_off = L1_ALIGN + 2 * L1_ALIGN
    prefetch_img = b"\0" * L1_ALIGN + struct.pack("<I", CQ_DISPATCH_CB_PAGES).ljust(L1_ALIGN, b"\0") + b"\0" * L1_ALIGN
    prefetch_segments = cq_fw.build_prefetch().compile()
    dispatch_segments = cq_fw.build_dispatch().compile()
    dispatch_sub_segments = cq_fw.build_dispatch_subordinate().compile()

    self._upload_cq_core(
      prefetch_core,
      prefetch_img,
      self._build_cq_launch(kernel_off, sem_off=L1_ALIGN),
      [(kernel_off, prefetch_segments)],
    )

    dispatch_win = self.cq.dispatch_win
    dispatch_win.target(dispatch_core)
    base_16b = self.cq.completion_base_16b
    dispatch_win.write32(CQ_COMPLETION_WR_PTR, base_16b)
    dispatch_win.write32(CQ_COMPLETION_RD_PTR, base_16b)
    dispatch_win.write32(CQ_COMPLETION_Q0_EVENT, 0)
    dispatch_win.write32(CQ_COMPLETION_Q1_EVENT, 0)
    dispatch_win.mm[CQ_DISPATCH_SYNC_SEM : CQ_DISPATCH_SYNC_SEM + 8 * L1_ALIGN] = b"\0" * (8 * L1_ALIGN)

    dispatch_size = max((segment.addr + len(segment.data) for segment in dispatch_segments), default=0)
    ncrisc_off = align_up(kernel_off + dispatch_size, L1_ALIGN)
    dispatch_img = b"\0" * (3 * L1_ALIGN)
    self._upload_cq_core(
      dispatch_core,
      dispatch_img,
      self._build_cq_launch(kernel_off, ncrisc_off, sem_off=L1_ALIGN),
      [(kernel_off, dispatch_segments), (ncrisc_off, dispatch_sub_segments)],
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
  def _build_cq_launch(brisc_text_off: int, ncrisc_text_off: int = 0, sem_off: int = 16) -> LaunchMsg:
    launch = LaunchMsg()
    cfg = launch.kernel_config
    for i in range(DevMsgs.ProgrammableCoreType_COUNT):
      cfg.kernel_config_base[i] = TensixL1.KERNEL_CONFIG_BASE
    cfg.sem_offset[0] = sem_off
    cfg.rta_offset[0].rta_offset = 0
    cfg.rta_offset[0].crta_offset = L1_ALIGN
    cfg.kernel_text_offset[0] = brisc_text_off
    cfg.kernel_text_offset[1] = ncrisc_text_off
    cfg.enables = 1 | (2 if ncrisc_text_off else 0)
    cfg.brisc_noc_id = 1 if ncrisc_text_off else 0
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
        win.write32(reset_off, TensixMMIO.SOFT_RESET_ALL)

  def alloc_write(self, data: bytes, dtype: Dtype, shape: Shape, name: str = "") -> DramBuffer:
    buf = self.dram.alloc(len(data) // dtype.tile_size, dtype, name, shape)
    self.dram_write(buf, data)
    return buf

  def dram_write(self, buf: DramBuffer, data: bytes):
    if buf.shape is not None:
      data = tilize(data, buf.dtype.bpe, buf.shape)
    self.dram.write(buf, data)

  def dram_read(self, buf: DramBuffer) -> bytes:
    if self.programs:
      self.run()
    data = self.dram.read(buf)
    if buf.shape is not None:
      return untilize(data, buf.dtype.bpe, buf.shape)
    return data
