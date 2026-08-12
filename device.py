from dataclasses import dataclass

from cq import (
  MAX_WRITE_SIZE, CommandBuffer, CommandQueues, Copy, Exec, Write,
)
import fw
from fw import (
  Firmware, FirmwareControl, KERNEL_ROLES, RunState, TensixL1, TensixMMIO,
)
from isa import R, RV32
from memory import Buffer, Dram
from pcie import PCIDevice, TLBWindow
from program import Program


RETURN_KERNEL = {
  role: RV32().jal(
    R.ZERO, Firmware.TEXT[role][0] - TensixL1.WORKER_TEXT_BASE[role],
  ).to_bytes(4, "little")
  for role in KERNEL_ROLES
}


@dataclass(frozen=True)
class Launch:
  program: Program
  bufs: tuple
  vals: tuple
  report: bool = True


class Device:
  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30, *, idx: int = 0):
    if type(idx) is not int or idx < 0:
      raise ValueError("device idx must be a non-negative integer")
    self.idx = idx
    self.pcie = PCIDevice(index, sysmem_size)
    self.dram = None
    self.queues = self.compute = self.dma = None
    self.program_queue = []
    self._resident_programs = {}
    self._args = {}

  def _worker_mcast(self, window, address, value):
    end_x = self.pcie.dispatch_core[0]
    for start, end in (((1, 2), (7, 11)), ((10, 2), (end_x, 11))):
      window.mcast(address, value, start, end)

  def reset_cores(self):
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      self._worker_mcast(
        window,
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_ALL,
      )

  def init_device(self):
    pcie_mid = self.pcie.sysmem.noc_addr >> 32
    images = fw.build(
      pcie_mid, self.pcie.prefetch_core, self.pcie.dispatch_core,
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

      self._worker_mcast(
        window,
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_ALL,
      )
      self._worker_mcast(window, firmware_base, worker_blob)
      boot = RV32().jal(R.ZERO, firmware_base + 4).to_bytes(4, "little")
      self._worker_mcast(window, TensixL1.BOOT, boot)
      self._worker_mcast(window, FirmwareControl.GO_SIGNAL & -4, 0)
      self._worker_mcast(
        window,
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
    self.dram = Dram(self.dma.banks)
    return self

  def _require_ready(self):
    if self.queues is None:
      raise RuntimeError("init_device() must be called before submission")

  def queue(self, program: Program, *bufs, vals=(), report=True):
    self.program_queue.append(Launch(program, tuple(bufs), tuple(vals), report))
    return program

  def _dma_command(self, buffer: Buffer, direction):
    self._require_ready()
    if buffer.size > self.dma.staging_size:
      raise MemoryError(
        f"buffer needs {buffer.size} DMA staging bytes; "
        f"only {self.dma.staging_size} are available",
      )
    return Copy(
      buffer.addr, self.dma.staging_address, buffer.size,
      direction,
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

  def write_safetensor(self, buffer: Buffer, name,
                       path="weights/model.safetensors", timeout=30.0):
    from st import Safetensor

    command = self._dma_command(buffer, 0)
    tensor = Safetensor(path)
    info = tensor.info(name)
    if info.nbytes != buffer.size:
      raise ValueError(
        f"tensor {name!r} has {info.nbytes} bytes, "
        f"buffer requires {buffer.size}",
      )
    tensor.readinto(
      name, self.pcie.sysmem.view(self.dma.staging_offset, buffer.size),
    )
    self.dma.wait(self.dma.submit(command), timeout=timeout)
    return buffer

  def read(self, buffer: Buffer, timeout=30.0):
    command = self._dma_command(buffer, 1)
    self.dma.wait(self.dma.submit(command), timeout=timeout)
    return self.pcie.sysmem.read(self.dma.staging_offset, buffer.size)

  def _args_for(self, launches, dedicated=False):
    occurrences, args = {}, []
    for launch in launches:
      data = launch.program.kernargs.pack(launch.bufs, launch.vals)
      if not data:
        args.append((0, 0)); continue
      occurrence = occurrences.get(launch.program, 0)
      occurrences[launch.program] = occurrence + 1
      key = launch.program, occurrence
      if dedicated: address = self.compute.alloc_args(data)
      else:
        if key not in self._args: self._args[key] = self.compute.alloc_args(data)
        else: self.compute.write_host(self._args[key], data)
        address = self._args[key]
      args.append((address, len(data)))
    return tuple(args)

  def _load_commands(self, program):
    commands, kernels = [], program.images
    for role in KERNEL_ROLES:
      groups = {}
      for core in program.cores:
        image = kernels[core].get(role, RETURN_KERNEL[role])
        if len(image) > TensixL1.WORKER_TEXT_SIZE[role]:
          raise ValueError(f"{role} kernel exceeds its text partition")
        groups.setdefault(image, []).append(core)
      for image, cores in groups.items():
        for offset in range(0, len(image), MAX_WRITE_SIZE):
          commands.append(Write(
            tuple(cores), TensixL1.WORKER_TEXT_BASE[role] + offset,
            image[offset:offset + MAX_WRITE_SIZE],
          ))
    for address, data in program.l1_data:
      for offset in range(0, len(data), MAX_WRITE_SIZE):
        commands.append(Write(
          program.cores, address + offset, data[offset:offset + MAX_WRITE_SIZE],
        ))
    return commands

  def _commands_for(self, launch, args):
    program = launch.program
    resident = self._resident_programs.get(program)
    commands = [] if resident is not None else self._load_commands(program)
    if program.cores:
      entries = (
        tuple(TensixL1.WORKER_TEXT_BASE[role] for role in KERNEL_ROLES)
        if resident is None else resident
      )
      commands.append(Exec(
        program.cores, entries, *args,
      ))
    return commands

  def run(self, program: Program | None = None, *bufs, vals=(), timeout=10.0):
    self._require_ready()
    if program is not None: self.queue(program, *bufs, vals=vals)
    elif bufs or vals: raise ValueError("buffers and values require an explicit program")
    if not self.program_queue: return []
    launches = tuple(self.program_queue)
    kernargs = self._args_for(launches)
    commands, reports = [], 0
    for launch, args in zip(launches, kernargs):
      commands.extend(self._commands_for(launch, args))
      reports += bool(launch.report)
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
      kernels = program.images
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
        commands.append(Write(
          cores, addresses[(role, image)] + offset, data,
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
    launches = tuple(self.program_queue)
    kernargs = self._args_for(launches, dedicated=True)
    commands = []
    for launch, args in zip(launches, kernargs):
      commands.extend(self._commands_for(launch, args))
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
