import os, struct, time, fw
from concurrent.futures import ThreadPoolExecutor, wait
from cq import ComputeQueue, CopyQueue, Graph, HWQueue, Ring, Launch, dram, rects
from helpers import PAGE, round_up
from system import PCIDevice, Sysmem

class Device:
  def __init__(self, index:int=0):
    self.pci_dev = PCIDevice(index)
    self.sysmem, self.readers, self.all = None, None, None
    try:
      cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if cols not in (12, 14): raise RuntimeError(f"unsupported {self.pci_dev.card}: {cols} Tensix columns enabled")
      right = 2 + cols
      self.all = ((1, 2), (right, 11))
      self.cq_core, self.dma_core = (right, 2), (right, 3)  # the top of the rightmost column
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12)
                      if (x, y) not in (self.cq_core, self.dma_core)]
      self._boot()
      # one pinned buffer: [arena (rings, signals, heap) | stage 0 | stage 1]
      self.arena_size, self.stage_size = 16 << 20, 8 << 20
      self.sysmem = Sysmem(self.pci_dev.fd, self.arena_size + 2 * self.stage_size)
      self.signals = 2 * fw.RING_SIZE
      self.heap, self.transfers, self.dram_top = self.signals + PAGE, 0, 0
      self.transfer_signal = 255  # copied: transfers the copy queue has finished (copyin, copyout, load, zero)
      self.readers, self.zeros = ThreadPoolExecutor(4), 0  # load's file readers; zero's source region
      self.stage_done, self.stage_next = [0, 0], 0 # transfer count that frees each buffer, the one to fill next
      self.sysmem.mem[self.signals:self.heap] = bytes(self.heap - self.signals)
      self.compute = self._create_queue(self.cq_core, 0, "dispatch", cmdbuf_size=1 << 20)
      self.copy = self._create_queue(self.dma_core, fw.RING_SIZE, "dma")
      self.descriptor_top = fw.DESCRIPTOR_L1
      self.run(fw.images()["init"], self.workers)
    except BaseException:
      self.close()
      raise

  def close(self):
    if self.pci_dev is None: return
    if self.all is not None: self._reset()  # stop service loops before unpinning their rings
    self._free()

  def _free(self):
    if self.readers is not None: self.readers.shutdown()
    try:
      if self.sysmem is not None: self.sysmem.close()
    finally:
      self.pci_dev.close()
      self.pci_dev = None

  def _telemetry(self, tag:int) -> int:
    dev = self.pci_dev
    table = dev.read32(fw.ARC, fw.TELEMETRY_PTR)
    n = dev.read32(fw.ARC, table + 4)
    assert 0 < n <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := dev.read32(fw.ARC, table + 8 + 4 * i)) & 0xFFFF == tag: return dev.read32(fw.ARC, table + 8 + 4 * n + 4 * (e >> 16))
    raise RuntimeError(f"ARC telemetry has no tag {tag}")

  def _reset(self): self.pci_dev.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL)  # every RISC of every worker core

  def _boot(self):
    dev, images = self.pci_dev, fw.images()
    self._reset()
    dev.write32(self.all, fw.GO_SIGNAL, 0)
    for role in fw.ROLES: dev.write(self.all, fw.FW[role][0], images[f"worker_{role}"])
    dev.write32(self.all, 0, fw.jal(fw.FW["brisc"][0]))  # BRISC always starts at 0
    dev.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)

  def _create_queue(self, core, offset:int, loop:str, cmdbuf_size:int=0) -> Ring:
    ring, dev = Ring(self.pci_dev, core, self.sysmem, offset, self.alloc(cmdbuf_size), cmdbuf_size), self.pci_dev
    dev.write(core, fw.STATE, bytes(fw.STATE_SIZE))
    dev.write(core, fw.RING_LO, struct.pack("<II", ring.addr & 0xFFFFFFFF, ring.addr >> 32))
    prog = fw.images()[loop]  # a service loop is an ordinary program, started directly
    for role, image in prog.items(): dev.write(core, fw.CODE[role], image)
    dev.write32(core, fw.LAUNCH, sum(1 << fw.ROLES.index(r) for r in prog))
    dev.write32(core, fw.GO_SIGNAL, 0x80)
    return ring

  def alloc(self, size:int, align:int=64) -> int:
    offset = round_up(self.heap, align)
    if offset + size > self.arena_size:
      raise MemoryError(f"arena is full: {size} bytes requested, {self.arena_size - offset} left")
    self.heap = offset + size
    return offset
  def addr(self, offset:int) -> int: return self.sysmem.noc_addr + offset
  def write(self, offset:int, data:bytes): self.sysmem.mem[offset:offset + len(data)] = data

  def signal(self, i:int) -> int: return self.addr(self.signals + 16 * i)
  def read_signal(self, i:int) -> tuple[int, int]: return struct.unpack_from("<QQ", self.sysmem.mem, self.signals + 16 * i)
  def wait(self, i:int, value:int, timeout=10.0) -> int:
    deadline = time.monotonic() + timeout
    while (v := self.read_signal(i))[0] < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal {i} is {v[0]}, waiting for {value}")
    return v[1]

  def alloc_dram(self, size:int) -> int:
    offset, end = self.dram_top, self.dram_top + round_up(size, fw.DRAM_BANKS * fw.DRAM_PAGE_MAX)
    if end > (total := fw.DRAM_BANKS * fw.DRAM_BANK_SIZE):
      raise MemoryError(f"DRAM is full: {size} bytes requested, {total - offset} left")
    self.dram_top = end
    return offset

  def bind(self, images:dict, args_size:int=0) -> Launch:
    """Upload packed code once to DRAM and bind immutable transfer geometry in dispatcher L1.
    images maps worker coordinates to {role: bytes}. Dispatch installs each launch into whichever of the two slots is
    free, fw.CODE[role] or fw.CODE[role] + fw.SLOT_STRIDE, so images must be position-independent (fw.program, fw.ret)."""
    assert images and set(images) <= set(self.workers)
    assert 0 <= args_size <= fw.PARAM_SIZE and args_size % 16 == 0
    groups = {}
    for core, roles in images.items():
      for role, image in roles.items():
        assert role in fw.ROLES and 0 < len(image) <= fw.CODE_SIZE[role] and len(image) % 4 == 0
        groups.setdefault((fw.CODE[role], image), []).append(core)
      mask = sum(1 << fw.ROLES.index(r) for r in roles)
      groups.setdefault((fw.LAUNCH, struct.pack('<I', mask)), []).append(core)
    payload, transfers = bytearray(), []
    encode = lambda cores: [fw.noc(s) | fw.noc(e) << 12 for s, e in rects(cores)]
    for (addr, image), cores in groups.items():
      payload.extend(bytes(-len(payload) % 64))
      rs = encode(cores)
      transfers.extend([len(payload), addr, len(image), len(rs), *rs])
      payload.extend(image)
    payload.extend(bytes(-len(payload) % 64))
    assert len(payload) <= fw.STAGE_SIZE, f"program payload too large: {len(payload)}"
    rs = encode(images)
    size = 4 * (8 + len(rs) + len(transfers))
    at = self.descriptor_top
    if at + size > fw.DESCRIPTOR_END: raise MemoryError("dispatcher descriptor arena full")
    addr = self.upload(bytes(payload))
    words = [len(images), len(rs), args_size, len(payload), addr & 0xFFFFFFFF, addr >> 32, len(groups), 0, *rs, *transfers]
    self.pci_dev.write(self.cq_core, at, struct.pack(f'<{len(words)}I', *words))
    self.descriptor_top = round_up(at + size, 64)
    launch = Launch(at, args_size)
    launch.payload_bytes, launch.multicasts = len(payload), sum(len(rects(cs)) for cs in groups.values())
    return launch

  def run(self, prog:dict[str, bytes], cores, params:bytes=b"", timeout=10.0):
    """Bind a program, run it once, and wait. For setup, not the hot path."""
    params = params.ljust(round_up(len(params), 16), b'\0')
    launch = self.bind({tuple(c): prog for c in cores}, len(params))
    q = ComputeQueue().exec(launch, self.upload(params) if params else 0)
    self.runs = getattr(self, "runs", 0) + 1
    q.signal(self.signal(254), self.runs).submit(self.compute)
    self.wait(254, self.runs, timeout)

  def capture(self, q:ComputeQueue) -> Graph:
    """Upload q's packets to DRAM once. replay() then runs all of them for the cost of one ring packet."""
    ops = [struct.unpack_from("<I", q.blob, i)[0] for i in range(0, len(q.blob), fw.PACKET)]
    return Graph(self.upload(bytes(q.blob)), len(q.blob), ops.count(fw.Op.EXEC))

  def replay(self, graph:Graph, before:HWQueue|None=None, wait:bool=True, timeout=10.0) -> int:
    """Push [before's packets, CALL graph, signal 253] to the CQ ring. Returns the replay number to wait() on."""
    assert before is None or type(before) is HWQueue, "before must be a plain HWQueue: STORE, WAIT, TIMESTAMP"
    self.replays = getattr(self, "replays", 0) + 1
    q = HWQueue()
    if before is not None: q.blob.extend(before.blob)
    q.call(graph).signal(self.signal(253), self.replays).submit(self.compute)
    if wait: self.wait(253, self.replays, timeout)
    return self.replays

  def upload(self, blob:bytes) -> int:
    """Copy blob into DRAM, for programs (EXEC reads it there instead of from host memory) and graphs."""
    addr = dram(self.alloc_dram(len(blob)), fw.DRAM_PAGE_MAX)
    self.copyin(addr, blob)
    return addr

  def _stage(self, timeout:float) -> int:
    """Wait for the next staging slot to be free; returns its sysmem offset."""
    i = self.stage_next
    self.wait(self.transfer_signal, self.stage_done[i], timeout)
    self.stage_next ^= 1
    return self.arena_size + i * self.stage_size
  def _submit(self, q:CopyQueue, buf:int):
    self.transfers += 1
    try:
      q.signal(self.signal(self.transfer_signal), self.transfers).submit(self.copy)
    except BaseException:
      self.close()  # a partial submission may still reference this staging slot
      raise
    self.stage_done[(buf - self.arena_size) // self.stage_size] = self.transfers

  def _put(self, copies:list[tuple[int, int, int]], fill, timeout:float):
    """Fill a free staging slot, then publish copies [(dst, slot offset, bytes)].
    DMA of the previous slot can overlap the fill; a failed fill publishes nothing."""
    buf = self._stage(timeout)
    q = CopyQueue()
    for dst, at, n in copies: q.copy(dst, self.addr(buf + at), n)
    fill(buf)
    self._submit(q, buf)

  def copyin(self, dev:int, host, timeout=60.0):
    host = memoryview(host).cast("B")
    for off in range(0, len(host), self.stage_size):
      n = min(self.stage_size, len(host) - off)
      def fill(buf): self.sysmem.mem[buf:buf + n] = host[off:off + n]
      self._put([(dev + off, 0, n)], fill, timeout)
    self.wait(self.transfer_signal, self.transfers, timeout)

  def copyout(self, host, dev:int, timeout=60.0):
    host, pending = memoryview(host).cast("B"), []
    def drain(buf, off, n, value):
      self.wait(self.transfer_signal, value, timeout)
      host[off:off + n] = self.sysmem.mem[buf:buf + n]
    for off in range(0, len(host), self.stage_size):
      buf, n = self._stage(timeout), min(self.stage_size, len(host) - off)
      self._submit(CopyQueue().copy(self.addr(buf), dev + off, n), buf)
      pending.append((buf, off, n, self.transfers))
      if len(pending) == 2: drain(*pending.pop(0))
    for p in pending: drain(*p)

  def load(self, sources:list[tuple[int, str|os.PathLike, int, int]], timeout=60.0):
    """Stream file ranges [(dst, path, file offset, bytes)] into the device. Ranges are packed back to back into the
    staging slots, each at a 64-byte aligned slot offset whatever its file offset (safetensors data is not aligned),
    and read in place with buffered preads on a few threads. No copy of the file and no pinning beyond sysmem."""
    S, slots, slot, pos = self.stage_size, [], [], 0
    for dst, path, offset, n in sources:
      done = 0
      while done < n:  # a range is split where it crosses a slot
        if pos == S: slots.append(slot); slot, pos = [], 0
        k = min(n - done, S - pos)
        slot.append((dst + done, path, offset + done, k, pos))
        pos, done = round_up(pos + k, 64), done + k
    if slot: slots.append(slot)
    fds = {}
    def read(piece):
      view, fd, offset = piece
      while len(view):
        if not (r := os.preadv(fd, [view], offset)): raise ValueError(f"file ended at {offset}")
        view, offset = view[r:], offset + r
    try:
      for slot in slots:
        def fill(buf, slot=slot):
          mem, pieces = self.sysmem.mem, []
          for _, path, offset, n, at in slot:
            fd = fds[path] if path in fds else fds.setdefault(path, os.open(path, os.O_RDONLY))
            pieces += [(mem[buf + at + o:buf + at + min(n, o + (1 << 20))], fd, offset + o) for o in range(0, n, 1 << 20)]
          futures = []
          try:
            for piece in pieces: futures.append(self.readers.submit(read, piece))
            for future in futures: future.result()
          finally:
            for future in futures: future.cancel()
            wait(futures)  # readers must release the slot and fds even when one read fails
        self._put([(dst, at, n) for dst, _, _, n, at in slot], fill, timeout)
    finally:
      for fd in fds.values(): os.close(fd)
    self.wait(self.transfer_signal, self.transfers, timeout)

  def zero(self, dst:int, size:int, timeout=60.0):
    """Zero DRAM on the device: DRAM -> DRAM copies from a zeroed region, nothing over PCIe."""
    if not self.zeros:
      self.zeros = dram(self.alloc_dram(self.stage_size), fw.DRAM_PAGE_MAX)
      self.copyin(self.zeros, bytes(self.stage_size))
    q = CopyQueue()
    for off in range(0, size, self.stage_size): q.copy(dst + off, self.zeros, min(self.stage_size, size - off))
    self.transfers += 1
    q.signal(self.signal(self.transfer_signal), self.transfers).submit(self.copy)
    self.wait(self.transfer_signal, self.transfers, timeout)
