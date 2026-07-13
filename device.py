import time
from struct import Struct
from pcie import PCIDevice, TLBWindow
from program import Dram, Program
from asm import KernelBuilder
from fw.consts import Firmware, FirmwareControl, RunMsg, TensixL1, TensixMMIO
from isa import R, RV32
from cq import CommandQueue, Run, UnicastWrite
from fw.consts import CQ

class Device:
  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30):
    self.pcie = PCIDevice(index, sysmem_size)
    self.dram = Dram()
    self.program_queue = []
    self.cq = None
    self._dram_programs = {}

  def reset_cores(self):
    cores = (self.pcie.prefetch_core, self.pcie.dispatch_core)
    with TLBWindow(self.pcie.fd, cores[0]) as win:
      base = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 & -win.SIZE
      for core in cores:
        win.target(base, core)
        win.write(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - base, TensixMMIO.SOFT_RESET_ALL)

  def upload_fw(self):
    from fw.brisc import build as build_brisc
    from fw.ncrisc import build as build_ncrisc
    from fw.trisc import build_trisc0, build_trisc1, build_trisc2
    images = {
      "brisc": build_brisc().lower(), "ncrisc": build_ncrisc().lower(),
      "trisc0": build_trisc0().lower(), "trisc1": build_trisc1().lower(), "trisc2": build_trisc2().lower(),
    }
    cores = [*self.pcie.cores, self.pcie.prefetch_core, self.pcie.dispatch_core]
    with TLBWindow(self.pcie.fd, cores[0]) as win:
      reset_base = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 & -win.SIZE
      for core in cores:
        win.target(reset_base, core)
        win.write(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - reset_base, TensixMMIO.SOFT_RESET_ALL)
        win.target(0, core)
        for role, image in images.items():
          if len(image) > Firmware.TEXT_SIZE[role]: raise ValueError(f"{role} firmware is too large")
          win.write(Firmware.TEXT_BASE[role], image)
        win.write(TensixL1.BOOT, RV32().jal(R.ZERO, Firmware.TEXT_BASE["brisc"]).to_bytes(4, "little"))
        win.target(reset_base, core)
        win.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC - reset_base, Firmware.TEXT_BASE["ncrisc"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC - reset_base, Firmware.TEXT_BASE["trisc0"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC - reset_base, Firmware.TEXT_BASE["trisc1"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC - reset_base, Firmware.TEXT_BASE["trisc2"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE - reset_base, 0b111)
        win.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE - reset_base, 1)
        win.write(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 - reset_base, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)
      pending, deadline = set(cores), time.monotonic() + 5
      while pending:
        for core in tuple(pending):
          win.target(0, core)
          if win.read(FirmwareControl.GO_SIGNAL, 1) == bytes((RunMsg.DONE,)): pending.remove(core)
        if time.monotonic() >= deadline: raise TimeoutError(f"resident firmware did not boot on {sorted(pending)}")
    self.upload_cq_fw()

  def upload_cq_fw(self):
    from fw.cq_dispatch import build_dispatch
    from fw.cq_prefetch import build_prefetch
    cq_images = {
      self.pcie.prefetch_core: build_prefetch().lower(),
      self.pcie.dispatch_core: build_dispatch().lower(),
    }
    with TLBWindow(self.pcie.fd, self.pcie.prefetch_core) as win:
      for core, image in cq_images.items():
        win.target(0, core)
        win.write(TensixL1.WORKER_TEXT_BASE["brisc"], image)
        for role in ("ncrisc", "trisc0", "trisc1", "trisc2"):
          empty = KernelBuilder(role, core).lower()
          win.write(TensixL1.WORKER_TEXT_BASE[role], empty)
    self.cq = CommandQueue(self.pcie)
    with TLBWindow(self.pcie.fd, self.pcie.prefetch_core) as win:
      for core in cq_images:
        win.target(0, core)
        win.write(FirmwareControl.GO_SIGNAL, int(RunMsg.GO), bytes=1)

  def queue(self, program: Program): self.program_queue.append(program)

  def _dram_program(self, write, core_count):
    key = write, core_count
    if key not in self._dram_programs:
      from fw.dram import dram_read, dram_write
      from ttk.dram import endpoint_coords
      build = dram_write if write else dram_read
      self._dram_programs[key] = build(
        self.pcie.cores[:core_count], endpoint_coords(self.pcie.harvested_dram_bank, 1),
      )
    return self._dram_programs[key]

  def _dram_transfer(self, buffer, *, write, timeout=10.0):
    from fw.dram import ARGS_BASE
    if self.cq is None: raise RuntimeError("upload_fw() must be called before tensor transfer")
    if not 0 < buffer.page_size <= 16 * 1024 or buffer.page_size % 16:
      raise ValueError("DRAM transfer pages must be 16-byte aligned and at most 16 KiB")
    if buffer.size > self.cq.dram_size:
      raise MemoryError(f"tensor needs {buffer.size} bytes; sysmem DRAM region has {self.cq.dram_size}")
    if self.program_queue: self.run()

    tiles = buffer.pages
    program = self._dram_program(write, min(tiles, len(self.pcie.cores)))
    tiles_per_core = (tiles + len(program.cores) - 1) // len(program.cores)
    sysmem_base = self.cq.noc + self.cq.dram
    if sysmem_base + buffer.size > 1 << 32:
      raise ValueError("sysmem DRAM transfer crosses a 4 GiB NoC address window")
    args = []
    pack = Struct("<6I").pack
    for index in range(len(program.cores)):
      start = index * tiles_per_core
      count = max(0, min(tiles_per_core, tiles - start))
      args.append(pack(
        buffer.addr, sysmem_base + start * buffer.page_size, CQ.PCIE_MID,
        start, count, buffer.page_size,
      ))
    args_write = UnicastWrite(program.cores, ARGS_BASE, tuple(args))
    return self.cq.submit((*program.commands(), args_write, Run(program.cores, 1)), timeout=timeout)

  def dram_write(self, buffer, data: bytes, *, timeout=10.0):
    if not isinstance(data, bytes) or len(data) != buffer.size:
      raise ValueError(f"buffer write requires exactly {buffer.size} bytes")
    if self.cq is None: raise RuntimeError("upload_fw() must be called before tensor transfer")
    self.pcie.sysmem.write(self.cq.dram, data)
    self.pcie.sysmem.flush()
    return self._dram_transfer(buffer, write=True, timeout=timeout)

  def dram_read(self, buffer, *, timeout=10.0):
    self._dram_transfer(buffer, write=False, timeout=timeout)
    return self.pcie.sysmem.read(self.cq.dram, buffer.size)

  write = dram_write
  read = dram_read

  def run(self):
    if self.cq is None: raise RuntimeError("upload_fw() must be called before run()")
    results = [self.cq.submit((*program.commands(), Run(program.cores, 1))) for program in self.program_queue]
    self.program_queue.clear()
    return results

  def close(self):
    if self.pcie.fd < 0:
      return
    self.reset_cores()
    if self.cq is not None:
      self.cq.close()
      self.cq = None
    self.pcie.close()
