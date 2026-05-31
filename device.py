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
from ttk.addrs import Core, L1_ALIGN, align_down, as_bytes
from ttk.tensix import TensixL1, TensixMMIO
from pcie import BoardInfo, PCIDevice, TLBWindow
from program import (
  DevMsgs, Dtype, FAST_CQ_NUM_CIRCULAR_BUFFERS, GoMsg, IRCommand, LaunchMsg,
  McastMmioWrite32, McastWrite, PollL1Byte, Program, Run, UnicastWrite,
  lower_firmware_boot, mcast_rects,
)

class Device:
  def __init__(self, index: int = 0, fast_dispatch: bool | None = None):
    self.fast_dispatch = os.environ.get("TT_USB") != "1" if fast_dispatch is None else fast_dispatch
    self.dev = PCIDevice(index=index, use_vfio=self.fast_dispatch)
    self.board_info: BoardInfo = self.dev.board_info(fast_dispatch=self.fast_dispatch)
    self.programs: list[Program] = []
    self.dram = Allocator(self.dev, self.board_info.dram_tiles)
    self.cq: CommandQueue | None = None
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
                raise TimeoutError(f"timeout waiting for core {core}")
              time.sleep(0.001)

  def _run_slow_dispatch(self):
    cores = self.cores
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

  def _start_dispatch_cores(self):
    prefetch_core = self.board_info.prefetch_core
    dispatch_core = self.board_info.dispatch_core
    self.cq = CommandQueue(self.dev, prefetch_core, dispatch_core)

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
