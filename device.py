from cq import (
  CommandBuffer, CommandQueues, DMACopy, McastWrite, Run, UnicastWrite,
  rectangles,
)
import fw
from fw import (
  Firmware, FirmwareControl, KERNEL_ROLES, RunState, TensixL1, TensixMMIO,
)
from isa import R, RV32
from pcie import PCIDevice, TLBWindow
from program import RETURN_KERNEL, Buffer, Dram, Program


class Device:
  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30):
    self.pcie = PCIDevice(index, sysmem_size)
    self.dram = Dram(
      len(self.pcie.dram_endpoints), self.pcie.cores,
      self.pcie.dram_endpoints,
    )
    self.queues = self.compute = self.dma = None
    self.program_queue = []
    self._resident_programs = {}
    self._args = {}

  def reset_cores(self):
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      window.mcast(
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_ALL,
      )

  def init_device(self):
    pcie_mid = self.pcie.sysmem.noc_addr >> 32
    images = fw.build(
      pcie_mid, self.pcie.dram_endpoints,
      self.pcie.prefetch_core, self.pcie.dispatch_core,
    )
    worker_blob = b"".join(
      image.ljust(size, b"\0")
      for (_, size), image in zip(Firmware.TEXT.values(), images.workers)
    )
    firmware_base = Firmware.TEXT["brisc"][0]

    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      def service_mmio(core, address, value):
        base = address & -TLBWindow.SIZE
        window.target(base, core)
        window.write(address - base, value)

      window.mcast(
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_ALL,
      )
      window.mcast(firmware_base, worker_blob)
      boot = RV32().jal(R.ZERO, firmware_base + 4).to_bytes(4, "little")
      window.mcast(TensixL1.BOOT, boot)
      window.mcast(FirmwareControl.GO_SIGNAL & -4, 0)
      window.mcast(
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
      )

      service_images = (
        (self.pcie.prefetch_core, {"brisc": images.prefetch}),
        (self.pcie.dispatch_core, {"brisc": images.dispatch}),
        (self.pcie.dma_core, {
          "brisc": images.dma_brisc,
          "ncrisc": images.dma_ncrisc,
        }),
      )
      for core, _ in service_images:
        service_mmio(
          core,
          TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
          TensixMMIO.SOFT_RESET_ALL,
        )
      for core, role_images in service_images:
        window.target(0, core)
        for role, image in role_images.items():
          window.write(TensixL1.WORKER_TEXT_BASE[role], image)
        window.write(
          TensixL1.BOOT,
          RV32().jal(
            R.ZERO, TensixL1.WORKER_TEXT_BASE["brisc"],
          ).to_bytes(4, "little"),
        )

      # Initialize both submission ABIs while their service cores are reset.
      self.queues = CommandQueues(self.pcie)
      self.compute = self.queues.compute
      self.dma = self.queues.dma

      for core in (self.pcie.prefetch_core, self.pcie.dispatch_core):
        service_mmio(
          core,
          TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
          TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
        )
      service_mmio(
        self.pcie.dma_core,
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
      )

    self.dma.wait_ready()
    return self

  def _require_ready(self):
    if self.queues is None:
      raise RuntimeError("init_device() must be called before submission")

  def queue(self, program: Program, params=None, report=True):
    self.program_queue.append((program, params, report))
    return program

  def _dma_command(self, buffer: Buffer, direction):
    self._require_ready()
    if buffer.size > self.dma.staging_size:
      raise MemoryError(
        f"buffer needs {buffer.size} DMA staging bytes; "
        f"only {self.dma.staging_size} are available",
      )
    if buffer.dram_endpoints != self.pcie.dram_endpoints[:buffer.banks]:
      raise ValueError("DMA buffers must use a prefix of the device DRAM banks")
    return DMACopy(
      buffer.addr, self.dma.staging_address, buffer.size,
      buffer.page_size, buffer.banks, direction,
    )

  def write(self, buffer: Buffer, data: bytes, timeout=30.0):
    data = bytes(data)
    if len(data) != buffer.size:
      raise ValueError(
        f"buffer {buffer.name!r} requires exactly {buffer.size} bytes, "
        f"got {len(data)}",
      )
    command = self._dma_command(buffer, 0)
    self.pcie.sysmem.write(self.dma.staging_offset, data)
    self.dma.wait(self.dma.submit(command), timeout=timeout)
    return buffer

  def read(self, buffer: Buffer, timeout=30.0):
    command = self._dma_command(buffer, 1)
    self.dma.wait(self.dma.submit(command), timeout=timeout)
    return self.pcie.sysmem.read(self.dma.staging_offset, buffer.size)

  def _args_for(self, program, values):
    data = program.arg_data(values)
    if not data: return 0, 0
    key = program, data
    if key in self._args: return self._args[key], len(data)
    address = self.compute.alloc_args(data)
    self._args[key] = address
    return address, len(data)

  def _commands_for(self, program, values):
    resident = self._resident_programs.get(program)
    commands = [] if resident is not None else list(program.static_commands())
    commands.extend(program.runtime_commands(values))
    if program.cores:
      args_addr, args_size = self._args_for(program, values)
      entries = (
        tuple(TensixL1.WORKER_TEXT_BASE[role] for role in KERNEL_ROLES)
        if resident is None else resident
      )
      commands.append(Run(
        program.cores, entries, args_addr, args_size,
      ))
    return commands

  def run(self, *programs: Program, params=None, timeout=10.0):
    self._require_ready()
    if params is not None and len(programs) != 1:
      raise ValueError("parameter overrides require exactly one explicit program")
    for program in programs: self.queue(program, params)
    if not self.program_queue: return []
    commands, reports = [], 0
    for program, values, report in self.program_queue:
      commands.extend(self._commands_for(program, values))
      reports += bool(report)
    event = self.compute.submit(commands)
    completion = self.compute.wait(event, timeout=timeout)
    self.program_queue.clear()
    return [completion] if reports else []

  def cache_kernels(self, programs, timeout=30.0):
    """Install uniform worker images once and dispatch through entry words."""
    self._require_ready()
    if self.program_queue:
      raise RuntimeError("flush queued work before caching worker programs")
    programs = tuple(dict.fromkeys(programs))
    if self._resident_programs:
      raise RuntimeError("resident worker programs can only be installed once")

    cursor = TensixL1.KERNEL_CACHE_BASE
    addresses = {}
    uploads = {}
    program_addresses = {}
    for program in programs:
      kernels = program.lower()
      role_addresses = []
      for role in KERNEL_ROLES:
        role_images = {
          kernels[core].get(role, RETURN_KERNEL[role])
          for core in program.cores
        }
        if len(role_images) != 1:
          raise ValueError("resident programs require one image per role across their cores")
        image = role_images.pop()
        key = role, image
        if key not in addresses:
          address = (cursor + 63) & -64
          following = address + len(image)
          if following > TensixL1.KERNEL_CACHE_END:
            raise MemoryError("resident worker program arena is full")
          pc = address + len(image) - 4
          offset = Firmware.TEXT[role][0] - pc
          relocated = image[:-4] + RV32().jal(R.ZERO, offset).to_bytes(4, "little")
          addresses[key] = address
          uploads[key] = [relocated, set()]
          cursor = following
        uploads[key][1].update(program.cores)
        role_addresses.append(addresses[key])
      program_addresses[program] = tuple(role_addresses)

    commands = []
    for (role, image), (relocated, cores) in uploads.items():
      cores = tuple(core for core in self.pcie.cores if core in cores)
      for offset in range(0, len(relocated), 16 * 1024):
        data = relocated[offset:offset + 16 * 1024]
        if len(cores) == 1:
          commands.append(UnicastWrite(
            cores, addresses[(role, image)] + offset, (data,),
          ))
        else:
          commands.append(McastWrite(
            rectangles(cores), addresses[(role, image)] + offset, data,
          ))
    if commands:
      event = self.compute.submit(commands)
      self.compute.wait(event, timeout=timeout)

    for program, role_addresses in program_addresses.items():
      self._resident_programs[program] = role_addresses
    return {
      "programs": len(programs),
      "images": len(addresses),
      "records": len(commands),
      "bytes": cursor - TensixL1.KERNEL_CACHE_BASE,
    }

  def capture_trace(self):
    self._require_ready()
    if not self.program_queue:
      raise ValueError("trace capture requires at least one queued program")
    commands = []
    for program, values, _ in self.program_queue:
      commands.extend(self._commands_for(program, values))
    command_buffer = self.compute.capture(commands)
    self.program_queue.clear()
    return command_buffer

  def replay(self, command_buffer: CommandBuffer, timeout=30.0):
    self._require_ready()
    event = self.compute.replay(command_buffer)
    return self.compute.wait(event, timeout=timeout, poll_interval=0.0)

  def close(self):
    if self.pcie.fd < 0: return
    self.reset_cores()
    if self.queues is not None:
      self.queues.close()
      self.queues = self.compute = self.dma = None
    self.pcie.close()
