from dataclasses import dataclass
from struct import Struct
import time
import ctypes

from ttko.cq import (
  ALIGN, DRAM_BRISC_READY, DRAM_NCRISC_READY, CommandQueue, DramCopy,
  DramRecord, McastWrite, Run, Signal, UnicastWrite, noc_coord,
)
from firmware.consts import (
  Firmware, FirmwareControl, KERNEL_ROLES, RunState, TensixL1, TensixMMIO,
)
from device import Device as RawDevice
from ttko.isa import R, RV32
from pcie import PCIDevice, TLBWindow
from ttko.program import (
  PARAM_BASE, RETURN_KERNEL, Buffer, Dram, Program, rectangles,
)
from ttko import DType

class PhysicalUploadStream:
  """Copy physical tensor bytes through two completion-protected host slots.

  Writes publish immediately; finish/context exit waits for the final transfers.
  A stream owns the device's DRAM staging arena until it exits.
  """
  def __init__(self, device, slot_bytes=4 << 20, timeout=60.0):
    self.device, self.timeout = device, timeout
    self.slot_bytes = slot_bytes
    self.events = [0, 0]
    self.slot = 0
    self.copy_s = self.wait_s = self.submit_s = 0.0
    self.active = False

  def __enter__(self):
    device = self.device
    if device.cq is None:
      raise RuntimeError("init_device() must be called before uploading")
    if (device._upload_stream is not None or device.program_queue or
        device.read_queue or device._staging_next):
      raise RuntimeError("flush queued work before starting an upload stream")
    self.slot_bytes = min(self.slot_bytes, device.cq.dram_size // 2) & -64
    if self.slot_bytes <= 0:
      raise ValueError("upload slots must contain at least 64 bytes")
    device._upload_stream = self
    self.active = True
    return self

  def _wait_slot(self, slot):
    if self.events[slot]:
      started = time.perf_counter()
      self.device.cq.wait(self.events[slot], timeout=self.timeout)
      self.wait_s += time.perf_counter() - started
      self.events[slot] = 0

  def write(self, buffer, data):
    if not self.active:
      raise RuntimeError("upload stream is not active")
    data = bytes(data)
    if len(data) != buffer.size:
      raise ValueError("streamed uploads require exact physical buffer bytes")
    # Keep data alive through memmove, without copying tensor slices.
    source = ctypes.cast(ctypes.c_char_p(data), ctypes.c_void_p).value
    def fill(target, offset):
      ctypes.memmove(ctypes.addressof(target), source + offset, len(target))
    self.write_from(buffer, fill)

  def write_from(self, buffer, fill):
    """Call fill(writable_buffer, tensor_byte_offset) for each host slot."""
    if not self.active:
      raise RuntimeError("upload stream is not active")
    banks, page = buffer.banks, buffer.tile_size
    endpoints = self.device.pcie.dram_endpoints
    if (not 0 < banks <= len(endpoints) or
        tuple(buffer.dram_endpoints) != endpoints[:banks]):
      raise ValueError("streamed uploads require a prefix of DRAM banks")
    # Every chunk starts at bank zero in the existing descriptor format.
    chunk_pages = self.slot_bytes // (banks * page) * banks
    if not chunk_pages:
      raise ValueError("upload slot is smaller than one DRAM bank stripe")
    for first in range(0, buffer.physical_tiles, chunk_pages):
      count = min(chunk_pages, buffer.physical_tiles - first)
      slot = self.slot
      self._wait_slot(slot)
      offset = self.device.cq.dram + slot * self.slot_bytes
      started = time.perf_counter()
      target = (ctypes.c_ubyte * (count * page)).from_address(
        self.device.pcie.sysmem.addr + offset,
      )
      fill(target, first * page)
      self.copy_s += time.perf_counter() - started
      command = DramCopy(
        buffer.addr + (first // banks) * page,
        self.device.pcie.sysmem.noc_addr + offset, page, count, banks,
      )
      started = time.perf_counter()
      self.events[slot] = self.device.cq.enqueue((command,))
      self.submit_s += time.perf_counter() - started
      self.slot ^= 1

  def finish(self):
    for slot in range(2): self._wait_slot(slot)

  def __exit__(self, exc_type, exc, tb):
    try:
      self.finish()
    except Exception:
      # A timed-out transfer may still be reading its slot. Keep the arena
      # reserved; the caller must close/reset the device before reusing it.
      self.active = False
      raise
    self.active = False
    self.device._upload_stream = None


class Readback:
  def __init__(self, device, buffer, offset):
    self.device, self.buffer, self.offset, self.data = device, buffer, offset, None

  def result(self):
    if self.data is None: raise RuntimeError("DRAM read has not completed")
    return self.data

  def _finish(self):
    data = self.device.pcie.sysmem.read(self.device.cq.dram + self.offset, self.buffer.size)
    self.data = self.buffer.unpad_data(data)


@dataclass(frozen=True)
class _TraceParam:
  offset: int
  size: int
  program: Program
  values: object


@dataclass(frozen=True)
class _TraceRuntime:
  offset: int
  size: int
  names: tuple[str, ...]
  values: tuple[int, ...]
  rects: tuple


class DeviceTrace:
  """A pre-lowered range with either compact or legacy PARAM patching."""

  def __init__(self, device, trace, params=(), runtime=None,
               template_count=0):
    self.device = device
    self.trace = trace
    self._legacy_params = tuple(params)
    self.runtime = runtime
    self.params = (
      self._legacy_params if runtime is None else runtime.names
    )
    self.template_count = template_count
    self.last_profile = {}
    self.profile_totals = {}
    self.profile_replays = 0

  def _record_profile(self, profile):
    self.last_profile = dict(profile)
    for name, value in profile.items():
      self.profile_totals[name] = self.profile_totals.get(name, 0.0) + value
    self.profile_replays += 1

  def average_profile(self):
    if not self.profile_replays:
      return {}
    return {
      name: total / self.profile_replays
      for name, total in self.profile_totals.items()
    }

  def replay(self, params=None, timeout=30.0, *, wait=True):
    overrides = {} if params is None else dict(params)
    if self.runtime is not None:
      started = time.perf_counter_ns()
      unknown = set(overrides) - set(self.runtime.names)
      if unknown:
        raise KeyError(
          f"trace has no runtime parameters: {sorted(unknown)}",
        )
      selected = dict(zip(self.runtime.names, self.runtime.values))
      selected.update(overrides)
      words = tuple(selected[name] for name in self.runtime.names)
      if any(type(value) is not int or not 0 <= value < 1 << 32
             for value in words):
        raise ValueError("trace runtime parameters must be 32-bit integers")
      record = McastWrite(
        self.runtime.rects, TensixL1.RUNTIME_PARAM_BASE,
        Struct(f"<{len(words)}I").pack(*words),
      ).lower()
      encoded = time.perf_counter_ns()
      if len(record) != self.runtime.size:
        raise RuntimeError("compact runtime-state record changed size")
      self.device.cq.patch_trace(self.trace, self.runtime.offset, record)
      patched = time.perf_counter_ns()
      result = self.device.cq.replay_trace(self.trace, timeout=timeout, wait=wait)
      self._record_profile({
        "runtime_encode_us": (encoded - started) / 1e3,
        "runtime_patch_us": (patched - encoded) / 1e3,
        **self.device.cq.last_replay_profile,
        # HCQSignal timestamps are absolute device-clock values. The full
        # trace interval is the host-observed doorbell-to-completion duration.
        "device_us": self.device.cq.last_replay_profile["device_wait_us"],
      })
      return result

    unknown = set(overrides) - {
      name for patch in self._legacy_params for name in patch.program.params
    }
    if unknown:
      raise KeyError(f"trace has no runtime parameters: {sorted(unknown)}")
    for patch in self._legacy_params:
      selected = {
        name: value for name, value in overrides.items()
        if name in patch.program.params
      }
      if not selected:
        continue
      values = {} if patch.values is None else dict(patch.values)
      values.update(selected)
      record = UnicastWrite(
        patch.program.cores, PARAM_BASE,
        patch.program._param_table(values),
      ).lower()
      if len(record) != patch.size:
        raise RuntimeError("runtime PARAM record changed size during replay")
      self.device.cq.patch_trace(self.trace, patch.offset, record)
    return self.device.cq.replay_trace(self.trace, timeout=timeout, wait=wait)

class Device(RawDevice):
  command_queue_type = CommandQueue

  def __init__(self, index: int = 0, sysmem_size: int = 1 << 30):
    super().__init__(index, sysmem_size)
    self.dram = Dram(
      len(self.pcie.dram_endpoints), self.pcie.cores,
      self.pcie.dram_endpoints,
    )
    self.dram.allocator = self._dram
    self.program_queue, self.read_queue = [], []
    self.cq = None
    self._staging_next = 0
    self._upload_stream = None
    self._cached_static = {}
    self._kernel_cache_buffer = None
    self._resident_programs = {}
    self._param_templates = {}
    self._param_template_next = TensixL1.KERNEL_CACHE_BASE

  def reset_cores(self):
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as win:
      address = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0
      win.target(address & -TLBWindow.SIZE, (1, 2), (14, 11))
      win.write(address % TLBWindow.SIZE, TensixMMIO.SOFT_RESET_ALL)

  def init_device(self):
    return self.boot()

  def upload_stream(self, slot_bytes=4 << 20, timeout=60.0):
    return PhysicalUploadStream(self, slot_bytes, timeout)

  def _check_upload_idle(self):
    if self._upload_stream is not None:
      raise RuntimeError("exit the upload stream before submitting other work")

  def queue(self, program: Program, params=None, report=True):
    self._check_upload_idle()
    self.program_queue.append((program, params, None, report))
    return program

  def _dram_copy_program(self, buffer, write, offset=0,
                         dram_endpoints=None):
    if self.cq is None:
      raise RuntimeError("init_device() must be called before tensor transfer")
    if offset + buffer.size > self.cq.dram_size:
      raise MemoryError(
        f"queued tensors need {offset + buffer.size} bytes; "
        f"sysmem DRAM region has {self.cq.dram_size}",
      )
    endpoints = (
      self.pcie.dram_endpoints
      if dram_endpoints is None else tuple(dram_endpoints)
    )
    if not endpoints or endpoints != self.pcie.dram_endpoints[:len(endpoints)]:
      raise ValueError("CQ DRAM copies require a non-empty prefix of DRAM banks")
    source = self.pcie.sysmem.noc_addr + self.cq.dram + offset
    command = DramCopy(
      buffer.addr, source, buffer.tile_size, buffer.physical_tiles,
      len(endpoints), int(not write),
    )
    program = Program((), images={})
    program.launch = (command,)
    return program

  def _write_physical(self, buffer, data: bytes, *, dram_endpoints=None):
    """Upload already-physical tile bytes without applying tensor tilization."""
    self._check_upload_idle()
    data = bytes(data)
    if len(data) > buffer.size:
      raise ValueError("physical upload exceeds its DRAM buffer")
    offset = self._staging_next
    program = self._dram_copy_program(
      buffer, write=True, offset=offset, dram_endpoints=dram_endpoints,
    )
    self.pcie.sysmem.write(
      self.cq.dram + offset, data.ljust(buffer.size, b"\0"),
    )
    self._staging_next += buffer.size
    return self.queue(program, report=False)

  def cache_programs(self, programs, timeout=30.0):
    """Place immutable lowered CQ records in one bank of device DRAM.

    Runtime PARAM and launch records remain inline. Each immutable record is
    replaced by a 64-byte DramRecord descriptor that prefetch dereferences.
    """
    if self.cq is None:
      raise RuntimeError("init_device() must be called before caching programs")
    programs = tuple(dict.fromkeys(programs))
    uncached = tuple(
      program for program in programs if program not in self._cached_static
    )
    if not uncached:
      return {
        "programs": len(programs),
        "records": 0,
        "bytes": 0,
      }
    if self._kernel_cache_buffer is not None:
      raise RuntimeError(
        "the DRAM program cache is immutable; cache all programs in one call",
      )
    if self.program_queue or self.read_queue:
      raise RuntimeError("flush queued work before building the program cache")

    lowered = {
      program: tuple(command.lower() for command in program.static_commands())
      for program in uncached
    }
    unique = tuple(dict.fromkeys(
      record for records in lowered.values() for record in records
    ))
    offsets, size = {}, 0
    for record in unique:
      size = (size + ALIGN - 1) & -ALIGN
      offsets[record] = size
      size += len(record)
    physical_size = (size + 4095) & -4096
    if not physical_size:
      for program in uncached: self._cached_static[program] = ()
      return {
        "programs": len(uncached),
        "records": 0,
        "bytes": 0,
      }

    address = self.dram.allocator.alloc(physical_size, ALIGN)
    core = self.pcie.cores[0]
    arena = Buffer(
      "cq_kernel_cache", address, DType.U32, (physical_size // 4,),
      None, (core,), 1, True, True, (self.pcie.dram_endpoints[0],),
    )
    blob = bytearray(physical_size)
    for record, offset in offsets.items():
      blob[offset:offset + len(record)] = record

    # A single-bank arena makes every cached record a linear DRAM read.
    endpoint = self.pcie.dram_endpoints[0]
    self._write_physical(arena, blob, dram_endpoints=(endpoint,))
    self.run(timeout=timeout)
    coord = noc_coord(endpoint[0])
    entries = {
      record: DramRecord(address + offset, coord, len(record))
      for record, offset in offsets.items()
    }
    for program, records in lowered.items():
      self._cached_static[program] = tuple(
        entries[record] for record in records
      )
    self._kernel_cache_buffer = arena
    return {
      "programs": len(uncached),
      "records": len(unique),
      "bytes": size,
    }

  def cache_kernels(self, programs, timeout=30.0):
    """Install unique worker kernels below the shared template arena."""
    if self.cq is None:
      raise RuntimeError("init_device() must be called before caching kernels")
    if self.program_queue or self.read_queue:
      raise RuntimeError("flush queued work before building the kernel cache")
    programs = tuple(dict.fromkeys(programs))
    if any(program._l1_constants for program in programs):
      raise ValueError(
        "resident kernel traces do not yet support per-program L1 constants",
      )
    if self._resident_programs:
      raise RuntimeError("resident kernels can only be installed once")
    if self._param_templates:
      raise RuntimeError("resident kernels must be installed before templates")

    next_address = {
      core: TensixL1.KERNEL_CACHE_BASE for core in self.pcie.cores
    }
    resident = {core: {} for core in self.pcie.cores}
    uploads = {}
    global_images = set()

    for program in programs:
      kernels = program.lower()
      entries = {}
      for core in program.cores:
        role_addresses = []
        for role in KERNEL_ROLES:
          image = kernels[core].get(role, RETURN_KERNEL[role])
          key = role, image
          global_images.add(key)
          if key not in resident[core]:
            address = (next_address[core] + ALIGN - 1) & -ALIGN
            following = address + len(image)
            if following > TensixL1.KERNEL_CACHE_END:
              raise MemoryError(
                f"resident kernel arena is full on core {core}",
              )
            pc = address + len(image) - 4
            offset = Firmware.TEXT[role][0] - pc
            if not -(1 << 20) <= offset < 1 << 20:
              raise ValueError("resident kernel return is outside JAL range")
            relocated = (
              image[:-4] +
              RV32().jal(R.ZERO, offset).to_bytes(4, "little")
            )
            resident[core][key] = address
            uploads.setdefault((address, relocated), []).append(core)
            next_address[core] = following
          role_addresses.append(resident[core][key])
        entries[core] = tuple(role_addresses)
      self._resident_programs[program] = entries

    commands = []
    for (address, image), cores in uploads.items():
      cores = tuple(cores)
      for offset in range(0, len(image), 16 * 1024):
        chunk = image[offset:offset + 16 * 1024]
        if len(cores) == 1:
          commands.append(UnicastWrite(
            cores, address + offset, (chunk,),
          ))
        else:
          commands.append(McastWrite(
            rectangles(cores), address + offset, chunk,
          ))

    active = {
      core for program in programs for core in program.cores
    }
    cores = tuple(core for core in self.pcie.cores if core in active)
    if commands:
      noop = Program(cores, images={})
      self.cq.submit(
        (*noop.static_commands(), *commands, Run(cores)),
        timeout=timeout,
      )
    used = tuple(
      next_address[core] - TensixL1.KERNEL_CACHE_BASE for core in cores
    )
    alignment = TensixL1.PARAM_TEMPLATE_ALIGNMENT
    self._param_template_next = (
      max(next_address.values(), default=TensixL1.KERNEL_CACHE_BASE)
      + alignment - 1
    ) & -alignment
    if self._param_template_next > TensixL1.KERNEL_CACHE_END:
      raise MemoryError("resident kernels exceed the persistent program arena")
    return {
      "programs": len(programs),
      "images": len(global_images),
      "records": len(commands),
      "source_bytes": sum(len(image) for _, image in global_images),
      "max_bytes_per_core": max(used, default=0),
      "average_bytes_per_core": sum(used) / len(used) if used else 0.0,
    }

  def _install_param_templates(self, queued, runtime_names, timeout=30.0):
    runtime_ids = {name: index for index, name in enumerate(runtime_names)}
    addresses, writes, defaults, seen = [], [], {}, set()

    for program, values, _, _ in queued:
      if not program.params:
        addresses.append(0)
        continue
      count = len(program.params)
      if count > TensixL1.PARAM_TEMPLATE_MAX_PARAMS:
        raise ValueError(
          f"trace program has {count} parameters; resident templates support "
          f"at most {TensixL1.PARAM_TEMPLATE_MAX_PARAMS}",
        )
      names = tuple(program.params)
      ids = bytes(runtime_ids.get(name, 0xFF) for name in names)
      tables = program._param_table(values)
      payloads = []
      resident = self._resident_programs.get(program)
      for core, table in zip(program.cores, tables):
        if len(table) != count * 4:
          raise RuntimeError("program parameter table has an invalid size")
        payload = bytearray(TensixL1.PARAM_TEMPLATE_STRIDE)
        payload[0:4] = count.to_bytes(4, "little")
        start = TensixL1.PARAM_TEMPLATE_VALUES
        payload[start:start + len(table)] = table
        start = TensixL1.PARAM_TEMPLATE_IDS
        payload[start:start + len(ids)] = ids
        if resident is not None:
          entries = resident[core]
          start = TensixL1.PARAM_TEMPLATE_KERNELS
          payload[start:start + 4 * len(entries)] = Struct(
            f"<{len(entries)}I",
          ).pack(*entries)
        payloads.append(bytes(payload))

      # Identical core-local tables share one address across trace launches.
      key = program.cores, tuple(payloads)
      if key in self._param_templates:
        address = self._param_templates[key]
      else:
        address = self._param_template_next
        following = address + TensixL1.PARAM_TEMPLATE_STRIDE
        if following > TensixL1.KERNEL_CACHE_END:
          raise MemoryError("worker-L1 persistent program arena is full")
        self._param_template_next = following
        self._param_templates[key] = address
        writes.append(UnicastWrite(program.cores, address, tuple(payloads)))
      addresses.append(address)

      for slot, name in enumerate(names):
        if name not in runtime_ids:
          continue
        seen.add(name)
        core_values = {
          int.from_bytes(table[slot * 4:slot * 4 + 4], "little")
          for table in tables
        }
        if len(core_values) != 1:
          raise ValueError(
            f"compact runtime parameter {name!r} must be uniform across cores",
          )
        value = core_values.pop()
        if name in defaults and defaults[name] != value:
          raise ValueError(
            f"compact runtime parameter {name!r} has conflicting "
            "capture-time values",
          )
        defaults[name] = value
    missing = set(runtime_names) - seen
    if missing:
      raise KeyError(
        f"trace programs have no runtime parameters: {sorted(missing)}",
      )
    if writes:
      active = {core for write in writes for core in write.cores}
      cores = tuple(core for core in self.pcie.cores if core in active)
      noop = Program(cores, images={})
      self.cq.submit(
        (*noop.static_commands(), *writes, Run(cores)),
        timeout=timeout,
      )
    return tuple(addresses), tuple(defaults[name] for name in runtime_names)

  def capture_trace(self, runtime_params=None, *, profile=False):
    """Consume queued programs and capture them as one replayable CQ range."""
    if self.cq is None:
      raise RuntimeError("init_device() must be called before trace capture")
    if self.read_queue:
      raise ValueError("DRAM readbacks are not supported inside a trace")
    if not self.program_queue:
      raise ValueError("trace capture requires at least one queued program")

    if runtime_params is not None:
      runtime_names = tuple(runtime_params)
      if not runtime_names:
        raise ValueError("compact trace requires at least one runtime parameter")
      if len(set(runtime_names)) != len(runtime_names):
        raise ValueError("compact trace runtime parameter names must be unique")
      if any(type(name) is not str or not name for name in runtime_names):
        raise TypeError("compact trace runtime parameters must be named strings")
      if len(runtime_names) > TensixL1.RUNTIME_PARAM_SLOTS:
        raise ValueError(
          f"compact trace supports at most "
          f"{TensixL1.RUNTIME_PARAM_SLOTS} runtime parameters",
        )
      queued = tuple(self.program_queue)
      template_addresses, defaults = self._install_param_templates(
        queued, runtime_names,
      )
      records, dispatch_sizes = [], []

      def append_compact(command):
        record = command.lower()
        records.append(record)
        dispatch_sizes.append(
          command.size if isinstance(command, DramRecord) else len(record),
        )
        return len(records) - 1, len(record)

      active = {
        core for program, _, _, _ in queued for core in program.cores
      }
      cores = tuple(core for core in self.pcie.cores if core in active)
      rects = rectangles(cores)
      runtime_index, runtime_size = append_compact(McastWrite(
        rects, TensixL1.RUNTIME_PARAM_BASE,
        Struct(f"<{len(defaults)}I").pack(*defaults),
      ))

      marker_offsets = []
      if profile:
        marker_base = self.cq.trace_allocator.alloc((len(queued)+1)*16)
        def mark():
          offset = marker_base + len(marker_offsets)*16
          marker_offsets.append(offset)
          append_compact(Signal(self.pcie.sysmem.noc_addr + offset, 1))
        mark()
      for (program, values, _, _), template in zip(
        queued, template_addresses,
      ):
        static = (
          () if program in self._resident_programs
          else self._cached_static.get(program)
        )
        if static is None: static = program.static_commands()
        for command in static:
          append_compact(command)
        runtime = program.runtime_commands(values)
        if program.params:
          runtime = runtime[1:]
        for command in runtime:
          append_compact(command)
        if program.cores:
          append_compact(Run(program.cores, param_template=template))
        if profile: mark()

      trace = self.cq.capture_trace(records, dispatch_sizes)
      runtime = _TraceRuntime(
        trace.record_offsets[runtime_index], runtime_size,
        runtime_names, defaults, rects,
      )
      self.program_queue.clear()
      self._staging_next = 0
      result = DeviceTrace(
        self, trace, runtime=runtime,
        template_count=sum(address != 0 for address in template_addresses),
      )
      result.marker_offsets = marker_offsets
      return result

    if profile: raise ValueError('profiling requires compact runtime parameters')
    records, dispatch_sizes, param_specs = [], [], []

    def append(command):
      index = len(records)
      record = command.lower()
      records.append(record)
      dispatch_sizes.append(
        command.size if isinstance(command, DramRecord) else len(record),
      )
      return index, len(record)

    for program, values, _, _ in self.program_queue:
      static = self._cached_static.get(program)
      if static is None:
        static = program.static_commands()
      for command in static: append(command)
      runtime = program.runtime_commands(values)
      if program.params:
        index, size = append(runtime[0])
        param_specs.append((index, size, program, values))
        runtime = runtime[1:]
      for command in runtime: append(command)
      if program.cores: append(Run(program.cores))

    trace = self.cq.capture_trace(records, dispatch_sizes)
    patches = tuple(
      _TraceParam(
        trace.record_offsets[index], size, program, values,
      )
      for index, size, program, values in param_specs
    )
    self.program_queue.clear()
    self._staging_next = 0
    return DeviceTrace(self, trace, patches)

  def write(self, buffer, data: bytes):
    if buffer.tilized:
      from ttko.layout import write_tiled
      return write_tiled(self, buffer, data)
    return self._write_physical(buffer, buffer.pad_data(data))

  def queue_read(self, buffer):
    self._check_upload_idle()
    if buffer.tilized:
      from ttko.layout import queue_read_tiled
      return queue_read_tiled(self, buffer)
    offset = self._staging_next
    program = self._dram_copy_program(buffer, write=False, offset=offset)
    readback = Readback(self, buffer, offset)
    self._staging_next += buffer.size
    self.read_queue.append((program, None, readback, False))
    return readback

  def read(self, buffer, timeout=10.0):
    readback = self.queue_read(buffer)
    self.run(timeout=timeout)
    return readback.result()

  def run(self, *programs: Program, params=None, timeout=10.0):
    self._check_upload_idle()
    if self.cq is None: raise RuntimeError("init_device() must be called before run()")
    if params is not None and len(programs) != 1:
      raise ValueError("parameter overrides require exactly one explicit program")
    for program in programs: self.queue(program, params)
    batch = (*self.program_queue, *self.read_queue)
    results = []
    pending = []
    for index, (program, values, readback, report) in enumerate(batch):
      static = self._cached_static.get(program)
      commands = program.commands(values) if static is None else (
        *static, *program.runtime_commands(values),
      )
      completion = (
        report or readback is not None or index == len(batch) - 1
      )
      if program.cores: commands = (*commands, Run(program.cores))
      event = self.cq.enqueue(commands, completion=completion)
      if completion:
        pending.append((event, readback, report))

    for event, readback, report in pending:
      timestamp = self.cq.wait(event, timeout=timeout)
      if report: results.append(timestamp)
      if readback is not None: readback._finish()
    self.program_queue.clear(); self.read_queue.clear()
    self._staging_next = 0
    return results

  def close(self):
    return super().close()
