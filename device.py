from struct import Struct
import numpy as np
from pcie import PCIDevice, TLBWindow
from program import Dram, Program
from fw.consts import Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from isa import R, RV32
from cq import CommandQueue, Run, UnicastWrite
from fw.consts import CQConfig

class Device:
  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30):
    self.pcie = PCIDevice(index, sysmem_size)
    self.dram = Dram(self.pcie.harvested_dram_bank)
    self.program_queue = []
    self.cq = None
    self._staging_write = 0

  def reset_cores(self):
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as win:
      win.mcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)

  def init_device(self):
    from fw.brisc import build_brisc
    from fw.cq_dispatch import build_dispatch
    from fw.cq_prefetch import build_prefetch
    from fw.ncrisc import build_ncrisc
    from fw.trisc import build_trisc
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

  def queue(self, program: Program): self.program_queue.append(program); return program

  def _dram_program(self, buffer, *, write, offset=0):
    from fw.dram import ARGS_BASE, dram_read, dram_write
    if self.cq is None: raise RuntimeError("init_device() must be called before tensor transfer")
    if not 0 < buffer.page_size <= 16 * 1024 or buffer.page_size % 16:
      raise ValueError("DRAM transfer pages must be 16-byte aligned and at most 16 KiB")
    if offset + buffer.size > self.cq.dram_size:
      raise MemoryError(f"queued tensors need {offset + buffer.size} bytes; sysmem DRAM region has {self.cq.dram_size}")

    tiles = buffer.pages
    build = dram_write if write else dram_read
    program = build(self.pcie.cores[:tiles], buffer.dram_coords[1])
    tiles_per_core = (tiles + len(program.cores) - 1) // len(program.cores)
    sysmem_base = self.cq.noc + self.cq.dram + offset
    if sysmem_base + buffer.size > 1 << 32:
      raise ValueError("sysmem DRAM transfer crosses a 4 GiB NoC address window")
    args = []
    pack = Struct("<6I").pack
    for index in range(len(program.cores)):
      start = index * tiles_per_core
      count = max(0, min(tiles_per_core, tiles - start))
      args.append(pack(
        buffer.addr, sysmem_base + start * buffer.page_size, CQConfig.PCIE_MID,
        start, count, buffer.page_size,
      ))
    args_write = UnicastWrite(program.cores, ARGS_BASE, tuple(args))
    program.launch = (args_write,)
    return program

  @staticmethod
  def _tile_data(buffer, data, *, inverse=False):
    shape = buffer.padded_shape
    if len(shape) < 2 or shape[-2] % 32 or shape[-1] % 32:
      raise ValueError("buffer padding must be a multiple of 32 in its final two dimensions")
    prefix, height, width = shape[:-2], shape[-2], shape[-1]
    rank = len(prefix)
    values = np.frombuffer(data, dtype=np.dtype(f"V{buffer.dtype.itemsize}"))
    if inverse:
      values = values.reshape(*prefix, height // 32, width // 32, 2, 2, 16, 16)
      axes = (*range(rank), rank, rank + 2, rank + 4, rank + 1, rank + 3, rank + 5)
    else:
      values = values.reshape(*prefix, height // 32, 2, 16, width // 32, 2, 16)
      axes = (*range(rank), rank, rank + 3, rank + 1, rank + 4, rank + 2, rank + 5)
    return values.transpose(axes).reshape(-1).tobytes()

  def dram_write(self, buffer, data: bytes):
    if len(data) != buffer.size:
      raise ValueError(f"buffer write requires exactly {buffer.size} bytes")
    if self.cq is None: raise RuntimeError("init_device() must be called before tensor transfer")
    offset = self._staging_write
    program = self._dram_program(buffer, write=True, offset=offset)
    self.pcie.sysmem.write(self.cq.dram + offset, self._tile_data(buffer, data))
    self.pcie.sysmem.flush()
    self._staging_write += buffer.size
    return self.queue(program)

  def dram_read(self, buffer, *, timeout=10.0):
    self.run(self._dram_program(buffer, write=False), timeout=timeout)
    return self._tile_data(buffer, self.pcie.sysmem.read(self.cq.dram, buffer.size), inverse=True)

  write = dram_write
  read = dram_read

  def run(self, programs: Program | list[Program] | None = None, *, timeout=10.0):
    if self.cq is None: raise RuntimeError("init_device() must be called before run()")
    if programs is None:
      programs = self.program_queue
    elif isinstance(programs, Program):
      programs = (*self.program_queue, programs)
    else:
      programs = (*self.program_queue, *programs)
    results = [self.cq.submit((*program.commands(), Run(program.cores, 1)), timeout=timeout) for program in programs]
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
