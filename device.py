from struct import Struct

from cq import CommandQueue, Run, UnicastWrite
from fw.consts import CQConfig, Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from fw.core import build_brisc, build_ncrisc, build_trisc
from fw.cq import build_dispatch, build_prefetch
from fw.dram import ARGS_BASE, dram_read, dram_write
from isa import R, RV32
from pcie import PCIDevice, TLBWindow
from program import Dram, Program

class Device:
  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30):
    self.pcie = PCIDevice(index, sysmem_size)
    self.dram = Dram(len(self.pcie.dram_endpoints), self.pcie.cores)
    self.program_queue = []
    self.cq = None
    self._staging_write = 0

  def reset_cores(self):
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as win:
      win.mcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)

  def init_device(self):
    images = (build_brisc(), build_ncrisc(), *(build_trisc(i) for i in range(3)))
    firmware = b"".join(image.lower().ljust(size, b"\0")
                        for (_, size), image in zip(Firmware.TEXT.values(), images))
    firmware_base = Firmware.TEXT["brisc"][0]
    prefetch, dispatch = build_prefetch().lower(), build_dispatch().lower()
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as win:
      win.mcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)
      win.mcast(firmware_base, firmware)
      boot = RV32().jal(R.ZERO, firmware_base).to_bytes(4, "little")
      win.mcast(TensixL1.BOOT, boot)
      win.mcast(FirmwareControl.GO_SIGNAL, int(RunState.DONE), bytes=1)
      win.mcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)
      for core, image in ((self.pcie.prefetch_core, prefetch), (self.pcie.dispatch_core, dispatch)):
        win.target(0, core)
        win.write(TensixL1.WORKER_TEXT_BASE["brisc"], image)
      self.cq = CommandQueue(self.pcie)
      for core in (self.pcie.prefetch_core, self.pcie.dispatch_core):
        win.target(0, core)
        win.write(FirmwareControl.GO_SIGNAL, int(RunState.GO), bytes=1)

  def queue(self, program: Program, params=None):
    self.program_queue.append((program, params))
    return program

  def _dram_program(self, buffer, write, offset=0):
    if self.cq is None: raise RuntimeError("init_device() must be called before tensor transfer")
    if not 0 < buffer.tile_size <= 16 * 1024 or buffer.tile_size % 16:
      raise ValueError("DRAM transfer tiles must be 16-byte aligned and at most 16 KiB")
    if offset + buffer.size > self.cq.dram_size:
      raise MemoryError(f"queued tensors need {offset + buffer.size} bytes; sysmem DRAM region has {self.cq.dram_size}")

    build = dram_write if write else dram_read
    program = build(buffer.cores, self.pcie.dram_endpoints)
    sysmem_base = self.cq.noc + self.cq.dram + offset
    if sysmem_base + buffer.size > 1 << 32:
      raise ValueError("sysmem DRAM transfer crosses a 4 GiB NoC address window")
    args = []
    pack = Struct("<6I").pack
    for index in range(len(program.cores)):
      start = buffer.tile_starts[index]
      args.append(pack(
        buffer.addr, sysmem_base + start * buffer.tile_size, CQConfig.PCIE_MID,
        start, buffer.tiles_per_core, buffer.tile_size,
      ))
    args_write = UnicastWrite(program.cores, ARGS_BASE, tuple(args))
    program.launch = (args_write,)
    return program

  def write(self, buffer, data: bytes):
    offset = self._staging_write
    program = self._dram_program(buffer, write=True, offset=offset)
    self.pcie.sysmem.write(self.cq.dram + offset, buffer.tile_data(data))
    self.pcie.sysmem.flush()
    self._staging_write += buffer.size
    return self.queue(program)

  def read(self, buffer, timeout=10.0):
    self.run(self._dram_program(buffer, write=False), timeout=timeout)
    return buffer.tile_data(
      self.pcie.sysmem.read(self.cq.dram, buffer.size), inverse=True,
    )

  def run(self, *programs: Program, params=None, timeout=10.0):
    if self.cq is None: raise RuntimeError("init_device() must be called before run()")
    if params is not None and len(programs) != 1:
      raise ValueError("parameter overrides require exactly one explicit program")
    for program in programs: self.queue(program, params)
    results = [
      self.cq.submit((*program.commands(values), Run(program.cores)), timeout=timeout)
      for program, values in self.program_queue
    ]
    self.program_queue.clear()
    self._staging_write = 0
    return results

  def close(self):
    if self.pcie.fd < 0:
      return
    self.reset_cores()
    if self.cq is not None:
      self.cq.close()
      self.cq = None
    self.pcie.close()
