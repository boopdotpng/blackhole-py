"""Labeled cycle markers for raw hardware tests."""

from struct import Struct

from asm import Asm
from fw.consts import KERNEL_ROLES, TensixL1, TensixMMIO


MAX_SECTIONS = 3
PROFILE_SAMPLE_SIZE = MAX_SECTIONS * 8
PROFILE_L1_SIZE = 32
PROFILE_L1_BASE = TensixL1.DATA_BUFFER_SPACE_END - PROFILE_L1_SIZE
_SAMPLES = Struct(f"<{MAX_SECTIONS * 2}I")

# Minimal NoC-0 command-buffer map used only by the post-kernel L1 -> DRAM
# sample copy. Keeping it here avoids making raw component tests depend on ttk.
_NOC_BASE = 0xFFB20000
_NOC_LOGICAL_NODE_ID = _NOC_BASE + 0x148
_NOC_COMMAND_SEND = _NOC_BASE + 0x40
_NOC_STATUS_BASE = _NOC_BASE + 0x200
_NOC_REQUESTS_OUTSTANDING = _NOC_STATUS_BASE + 0x40
_NOC_WRITES_OUTGOING = _NOC_STATUS_BASE + 0x80
_NOC_TID = 15
_NOC_WRITE_NONPOSTED = (1 << 1) | (1 << 4) | (1 << 7) | (1 << 13)

class Profiler:
  """Call ``record(label)`` before and after up to three measured sections."""

  def __init__(self, kernel, *, l1_address=PROFILE_L1_BASE):
    if type(l1_address) is not int or l1_address % 16:
      raise ValueError("profiler L1 address must be a 16-byte-aligned integer")
    if not 0 <= l1_address <= TensixL1.SIZE - PROFILE_L1_SIZE:
      raise ValueError("profiler samples do not fit in worker L1")
    self.kernel = kernel
    self.l1_address = l1_address
    self._labels, self._open, self._modes, self._starts = {}, set(), {}, {}
    self.last = {}

  def record(self, label):
    """Start or stop the section named ``label`` at the current instruction."""
    if type(label) is not str or not label:
      raise ValueError("profiler label must be a non-empty string")

    index = self._labels.get(label)
    if index is None:
      if len(self._labels) == MAX_SECTIONS:
        raise ValueError(f"profiler supports at most {MAX_SECTIONS} sections")
      index = self._labels[label] = len(self._labels)
      self._modes[label] = "difference"
      self._open.add(label)
      offset, stopped = index * 8, False
    else:
      if self._modes[label] != "difference":
        raise ValueError(f"profiler section {label!r} is an accumulated section")
      if label not in self._open:
        raise ValueError(f"profiler section {label!r} was already stopped")
      self._open.remove(label)
      offset, stopped = index * 8 + 4, True

    timestamp = self.kernel.reg()
    self.kernel.read(timestamp, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    self.kernel.write(self.l1_address + offset, timestamp)
    if stopped: self.kernel.fence()  # Make the final sample visible on return.
    return self

  def accumulate(self, label):
    """Start/stop one interval and add its cycles to a reusable section.

    Unlike ``record``, the same label can be opened and closed repeatedly. This
    is useful for timing only the NoC portion of every iteration in a loop while
    excluding CB-credit stalls and address bookkeeping between requests.
    """
    if type(label) is not str or not label:
      raise ValueError("profiler label must be a non-empty string")
    index = self._labels.get(label)
    if index is None:
      if len(self._labels) == MAX_SECTIONS:
        raise ValueError(f"profiler supports at most {MAX_SECTIONS} sections")
      index = self._labels[label] = len(self._labels)
      self._modes[label] = "accumulate"
      self.kernel.write(self.l1_address + index * 8, 0)
      self.kernel.write(self.l1_address + index * 8 + 4, 0)
    elif self._modes[label] != "accumulate":
      raise ValueError(f"profiler section {label!r} is a difference section")

    if label not in self._open:
      started = self.kernel.reg()
      self.kernel.read(started, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
      self._starts[label] = started
      self._open.add(label)
      return self

    stopped, elapsed, total = self.kernel.reg(3)
    self.kernel.read(stopped, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    self.kernel.sub(elapsed, stopped, self._starts.pop(label))
    self.kernel.read(total, self.l1_address + index * 8 + 4)
    self.kernel.add(total, total, elapsed)
    self.kernel.write(self.l1_address + index * 8 + 4, total)
    self.kernel.fence()
    self._open.remove(label)
    return self

  @property
  def size(self):
    return len(self._labels) * 8

  def _validate(self, l1=None):
    if not self._labels: raise ValueError("profiler has no sections")
    if self._open:
      raise ValueError(
        f"profiler sections were not stopped: {', '.join(self._open)}",
      )
    start, end = self.l1_address, self.l1_address + PROFILE_L1_SIZE
    for address, data in ({} if l1 is None else dict(l1)).items():
      if address < end and start < address + len(data):
        raise ValueError("L1 initialization overlaps profiler samples")

  def _export_images(self, output):
    kernels = {role: Asm(role) for role in KERNEL_ROLES}
    kernel = kernels["brisc"]
    local_coordinate = kernel.reg()
    kernel.read(local_coordinate, _NOC_LOGICAL_NODE_ID)
    kernel.slli(local_coordinate, local_coordinate, 20)
    kernel.srli(local_coordinate, local_coordinate, 20)

    # Wait for command buffer zero, program one non-posted write, then wait for
    # both its local payload read and remote acknowledgement.
    kernel.wait(_NOC_COMMAND_SEND, 0)
    command = (
      self.l1_address, 0, local_coordinate,
      output.address, 0, output.coordinate,
      _NOC_TID << 10, _NOC_WRITE_NONPOSTED, self.size, 0, 0, 0,
      0, 0, 0,
    )
    for index, value in enumerate(command):
      kernel.write(_NOC_BASE + index * 4, value)
    kernel.write(_NOC_COMMAND_SEND, 1)
    kernel.wait(_NOC_COMMAND_SEND, 0)
    kernel.wait(_NOC_WRITES_OUTGOING + _NOC_TID * 4, 0)
    kernel.wait(_NOC_REQUESTS_OUTSTANDING + _NOC_TID * 4, 0)
    return {role: candidate.lower() for role, candidate in kernels.items()}

  def _report(self, device, core, timeout):
    self._validate()
    output = device.alloc_dram(self.size)
    device.launch({core: self._export_images(output)}, timeout=timeout)
    data = device.read_dram(output, timeout=timeout)
    words = _SAMPLES.unpack(data[:PROFILE_SAMPLE_SIZE].ljust(
      PROFILE_SAMPLE_SIZE, b"\0",
    ))
    self.last = {
      label: (words[2 * index + 1] - words[2 * index]) & 0xFFFFFFFF
      for label, index in self._labels.items()
    }
    print("cycle profile:")
    for label, index in self._labels.items():
      print(f"  [{index + 1}] {label}: {self.last[label]} cycles")
