from __future__ import annotations
import struct
import time
from asm import FIRMWARE_TEXT_BASE, Kernel, boot_jal
import fw
from l1 import Core, TensixL1, TensixMMIO, align_down
from pcie import BoardInfo, PCIDevice, TLBWindow, TT_USB
from program import DevMsgs, GoMsg, IRCommand, McastWrite, Program, Run, UnicastWrite, mcast_rects

class Device:
  def __init__(self, index: int = 0):
    self.index = index
    self.dev = PCIDevice(index=index)
    self.board_info: BoardInfo = self.dev.board_info()
    self.all_cores = list(self.board_info.worker_cores)
    self.cores = [
      core for core in self.all_cores
      if TT_USB or core not in self.board_info.cq_cores
    ]
    self.programs: list[Program] = []
    self.use_slow_dispatch = TT_USB

  def close(self):
    if self.dev is not None:
      self.dev.close()
      self.dev = None

  def __enter__(self):
    return self

  def __exit__(self, *_):
    self.close()

  def upload_firmware(self, firmware: dict[str, Kernel] | None = None):
    firmware = firmware or fw.build_all()
    all_cores = self.all_cores
    if not all_cores:
      raise ValueError("no cores to upload firmware to")

    mmio_base, _ = align_down(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TLBWindow.SIZE_2M)
    reset_off = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - mmio_base
    rects = mcast_rects(all_cores)
    go_init = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_INIT)

    with TLBWindow(self.dev, start=all_cores[0]) as uc, \
         TLBWindow(self.dev, start=all_cores[0], wc=True) as wc:
      for x0, x1, y0, y1 in rects:
        uc.target((x0, y0), (x1, y1), addr=mmio_base)
        uc.write32(reset_off, TensixMMIO.SOFT_RESET_ALL)

      for x0, x1, y0, y1 in rects:
        wc.target((x0, y0), (x1, y1))
        for kernel in firmware.values():
          for segment in kernel.compile():
            wc.write(segment.addr, segment.data)
        wc.write(0, boot_jal(FIRMWARE_TEXT_BASE["brisc"]))
        wc.write(TensixL1.GO_MSG, go_init)
      wc.mm[0]

      for x0, x1, y0, y1 in rects:
        uc.target((x0, y0), (x1, y1), addr=mmio_base)
        uc.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC - mmio_base, FIRMWARE_TEXT_BASE["ncrisc"])
        uc.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC - mmio_base, FIRMWARE_TEXT_BASE["trisc0"])
        uc.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC - mmio_base, FIRMWARE_TEXT_BASE["trisc1"])
        uc.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC - mmio_base, FIRMWARE_TEXT_BASE["trisc2"])
        uc.write32(reset_off, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)

  def boot(self):
    self.upload_firmware()
    return self

  def queue(self, program: Program):
    self.programs.append(program)
    return self

  def run(self):
    for program in self.programs:
      if self.use_slow_dispatch:
        self.run_slow(program)
      else:
        self.run_fast(program)
    self.programs.clear()
    return self

  def run_fast(self, program: Program):
    raise NotImplementedError("fast dispatch will be implemented by cq.py")

  def run_slow(self, program: Program):
    commands = program.lower(self.cores, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST)
    with TLBWindow(self.dev, start=self.cores[0]) as win:
      self._run_slow_ir(win, commands)

  def _run_slow_ir(self, win: TLBWindow, commands: list[IRCommand]):
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
