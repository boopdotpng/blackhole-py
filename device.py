from __future__ import annotations
import struct
import time
from asm import Kernel
import fw
from l1 import Core, TensixL1, align_down
from pcie import BoardInfo, PCIDevice, TLBWindow, TT_USB
from program import (
  DevMsgs, GoMsg, IRCommand, McastMmioWrite32, McastWrite, PollL1Byte, Program,
  Run, UnicastWrite, lower_firmware_boot, mcast_rects,
)

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

  def close(self):
    if self.dev is not None:
      self.dev.close()
      self.dev = None

  def upload_firmware(self, firmware: dict[str, Kernel] | None = None):
    commands = lower_firmware_boot(
      firmware or fw.build_all(),
      self.all_cores,
      self.board_info.harvested_dram_bank,
    )
    self._run_firmware_ir(commands)

  def _run_firmware_ir(self, commands: list[IRCommand]):
    start = self.all_cores[0]
    with TLBWindow(self.dev, start=start) as uc, \
         TLBWindow(self.dev, start=start, wc=True) as wc:
      self._run_ir(commands, uc=uc, wc=wc)

  def boot(self):
    self.upload_firmware()
    return self

  def queue(self, program: Program):
    self.programs.append(program)
    return self

  def run(self):
    for program in self.programs:
      if TT_USB:
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
    self._run_ir(commands, uc=win)

  def _run_ir(self, commands: list[IRCommand], *, uc: TLBWindow, wc: TLBWindow | None = None):
    wc = wc or uc
    for cmd in commands:
      match cmd:
        case UnicastWrite(cores=cores, addr=addr, data=data):
          for core, blob in zip(cores, data):
            wc.target(core)
            wc.write(addr, blob)
        case McastWrite(rects=rects, addr=addr, data=data):
          for x0, x1, y0, y1 in rects:
            wc.target((x0, y0), (x1, y1))
            wc.write(addr, data)
        case McastMmioWrite32(rects=rects, addr=addr, value=value):
          mmio_base, _ = align_down(addr, TLBWindow.SIZE_2M)
          for x0, x1, y0, y1 in rects:
            uc.target((x0, y0), (x1, y1), addr=mmio_base)
            uc.write32(addr - mmio_base, value)
        case PollL1Byte(core=core, addr=addr, value=value, timeout_s=timeout_s):
          uc.target(core)
          deadline = time.perf_counter() + timeout_s
          while uc.mm[addr] != value:
            if time.perf_counter() > deadline:
              raise TimeoutError(f"timeout waiting for L1[0x{addr:x}] == 0x{value:02x} on core {core}")
            time.sleep(0.001)
        case Run(cores=cores):
          go = GoMsg()
          go.bits.signal = DevMsgs.RUN_MSG_GO
          go_blob = struct.pack("<I", go.all)
          for x0, x1, y0, y1 in mcast_rects(cores):
            wc.target((x0, y0), (x1, y1))
            wc.write(TensixL1.GO_MSG, go_blob)
          for core in cores:
            uc.target(core)
            deadline = time.perf_counter() + 10.0
            while uc.mm[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
              if time.perf_counter() > deadline:
                raise TimeoutError(f"timeout waiting for core {core}")
