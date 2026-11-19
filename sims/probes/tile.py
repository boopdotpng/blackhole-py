"""Direct-launch harness for probe kernels (probe.h) on blackhole-py's resident worker firmware. No CQ, no dispatch
core, no DRAM: the host writes a kernel, its parameters and GO straight into each tile's L1 and polls GO for the return.

The GO word's dispatch field is the tile's own coordinate, so the firmware's done-atomic lands in the tile's own
DONE_COUNT (0x11870) instead of on some other tile. The card itself is never reset here.
"""
import struct, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import fw  # noqa: E402
from system import PCIIface  # noqa: E402

# Per-role probe areas (probe.h gets these as -D defines): status block, log (to res + 0x10000), parameters.
LAYOUT = {"brisc": dict(res=0x20000, log=0x21000, params=fw.L1_PARAM_BASE),
          "ncrisc": dict(res=0x30000, log=0x31000, params=0x1FF00),
          "trisc0": dict(res=0x50000, log=0x51000, params=0x1FF40),
          "trisc1": dict(res=0x60000, log=0x61000, params=0x1FF80),
          "trisc2": dict(res=0x70000, log=0x71000, params=0x1FFC0)}
LOG_WORDS = 0xF000 // 4
ST_DONE, ST_TIMEOUT = 0xD0E0D0E0, 0x7E000000
SUBORDINATE_SYNC = 0x14


class KernelTimeout(Exception):
  """Soft: the kernel's own bounded wait gave up and it returned to firmware. The tile is usable."""


class HostTimeout(Exception):
  """Hard: the tile never returned to firmware within the host timeout (kernel or NoC stuck)."""


def build(src, role="brisc", **defines) -> bytes:
  """Compile one probe kernel (C file in sims/probes) for `role`. Cached by fw.compile."""
  lay = LAYOUT[role]
  defines = dict(RES=hex(lay["res"]), LOG=hex(lay["log"]), PARAM_AT=hex(lay["params"]),
                 RETURN_ADDR=hex(fw.RETURN[role]), **defines)
  flags = ["-O2", f"-I{HERE}", *(f"-D{k}={v}" for k, v in defines.items())]
  return fw.program({role: ([str(HERE / src)], flags)})[role]


def quiet_image(role) -> bytes:
  return build("k_quiet.c", role, **(dict(NO_TENSIX_CFG=1) if role == "ncrisc" else {}))


class Card:
  def __init__(self, index: int):
    self.index, self.iface = index, PCIIface(index)
    try:
      cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if cols not in (12, 14): raise RuntimeError(f"unsupported card: {cols} Tensix columns enabled")
      right = 2 + cols
      self.workers = {(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12)}
      self.booted, self.code, self.running = set(), {}, {}
      self.quiet, self.quiet_applied, self.fillers = False, False, {}
      self.quiet_roles = None  # quiet only these roles (default: every role the probe does not use)  # quiet: unused roles run k_quiet.c instead of polling L1 in firmware
    except BaseException:
      self.iface.close()
      raise

  def _telemetry(self, tag: int) -> int:
    rd = lambda addr: self.iface.read32(fw.ARC, addr)
    table = rd(fw.TELEMETRY_PTR)
    assert 0 < (n := rd(table + 4)) <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := rd(table + 8 + 4 * i)) & 0xFFFF == tag: return rd(table + 8 + 4 * n + 4 * (e >> 16))
    raise RuntimeError(f"ARC telemetry has no tag {tag}")

  def boot(self, tiles, timeout=0.5):
    """Hold the tiles' RISCs in soft reset, install the resident worker firmware, release BRISC, wait until the
    subordinates report booted. Only the given tiles are touched."""
    io, images = self.iface, fw.images()
    tiles = [t for t in tiles if t not in self.booted]
    for t in tiles:
      if t not in self.workers: raise ValueError(f"{t} is not an enabled worker tile")
      io.write32(t, fw.SOFT_RESET, fw.RESET_ALL)
      io.write32(t, fw.GO_SIGNAL, 0)
      io.write32(t, SUBORDINATE_SYNC, 0)
      for role in fw.ROLES: io.write(t, fw.FW[role][0], images[f"worker_{role}"])
      io.write32(t, 0, fw.jal(fw.FW["brisc"][0]))
      io.write32(t, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    deadline = time.monotonic() + timeout
    for t in tiles:
      while io.read32(t, SUBORDINATE_SYNC) != 0x02020202:
        if time.monotonic() > deadline: raise HostTimeout(f"{t}: firmware did not boot (sync {io.read32(t, SUBORDINATE_SYNC):#x})")
      self.booted.add(t)
      for r in fw.ROLES: self.code.pop((t, r), None)

  def launch(self, tile, images, params=(), l1=None):
    """images: {role: image} (or one BRISC image); params: words per role ({role: [...]}) or one list for every
    role. Installs everything, then one GO starts all roles together."""
    io = self.iface
    if isinstance(images, (bytes, bytearray)): images = {"brisc": bytes(images)}
    if not isinstance(params, dict): params = {r: params for r in images}
    if tile not in self.booted: self.boot([tile])
    fillers = [r for r in (self.quiet_roles or fw.ROLES) if r not in images] if self.quiet else []
    if fillers:
      images = {**images, **{r: quiet_image(r) for r in fillers}}
    if (go := io.read32(tile, fw.GO_SIGNAL)) & 0xFF: raise HostTimeout(f"{tile}: still running a launch (GO={go:#x})")
    for role, image in images.items():
      lay, words = LAYOUT[role], list(params.get(role, ()))
      if len(words) > 16: raise ValueError("at most 16 parameter words")
      if self.code.get((tile, role)) != image:
        if len(image) > fw.CODE_SIZE[role]: raise ValueError(f"{role} kernel too large")
        io.write(tile, fw.CODE[role], image)
        self.code[(tile, role)] = image
      io.write(tile, lay["params"], struct.pack("<16I", *(w & 0xFFFFFFFF for w in words), *[0] * (16 - len(words))))
      io.write(tile, lay["res"], bytes(0x100))
    for addr, data in (l1 or {}).items(): io.write(tile, addr, data)
    io.write32(tile, fw.LAUNCH, sum(1 << fw.ROLES.index(r) for r in images))
    io.write32(tile, fw.GO_SIGNAL, 0x80 | fw.noc(tile) << 8)
    self.running[tile] = tuple(images)
    self.fillers[tile] = tuple(fillers)

  def wait(self, tiles, timeout: float, sites=None):
    """Wait until every tile has returned to firmware, then check each launched role's status."""
    io, deadline = self.iface, time.monotonic() + timeout
    for t in tiles:  # quiet: once every measured role has a status, stop the fillers
      if not (fillers := self.fillers.pop(t, ())): continue
      for role in self.running[t]:
        if role in fillers: continue
        while not io.read32(t, LAYOUT[role]["res"]):
          if time.monotonic() > deadline: raise HostTimeout(f"{t} {role}: no status within {timeout} s")
      for role in fillers: io.write32(t, LAYOUT[role]["res"] + 0x80, 1)
    for t in tiles:
      while io.read32(t, fw.GO_SIGNAL) & 0xFF:
        if time.monotonic() > deadline: raise HostTimeout(f"{t}: kernel did not return within {timeout} s")
    for t in tiles:
      for role in self.running.pop(t, ("brisc",)):
        res = LAYOUT[role]["res"]
        status, site = io.read32(t, res), io.read32(t, res + 4)
        if status == ST_DONE: continue
        name = (sites or {}).get(site, site)
        if status == ST_TIMEOUT: raise KernelTimeout(f"{t} {role}: gave up waiting at {name}")
        raise KernelTimeout(f"{t} {role}: returned without a status ({status:#x})")

  def run(self, jobs, timeout: float, sites=None):
    """jobs: [(tile, images, params, l1)], launched in order (start receivers before senders). Quiet applies to
    single-tile launches only: the extra host writes per tile would skew the start of multi-tile launches."""
    quiet, self.quiet_applied = self.quiet, self.quiet and len(jobs) == 1
    self.quiet = self.quiet_applied
    try:
      for job in jobs: self.launch(*job)
    finally: self.quiet = quiet
    self.wait([j[0] for j in jobs], timeout, sites)

  def log(self, tile, n: int, role="brisc"):
    if n > LOG_WORDS: raise ValueError("log longer than the log area")
    return struct.unpack(f"<{n}I", self.iface.read(tile, LAYOUT[role]["log"], 4 * n)) if n else ()

  def aux(self, tile, n: int, role="brisc"):
    return struct.unpack(f"<{n}I", self.iface.read(tile, LAYOUT[role]["res"] + 0x10, 4 * n))

  def clock(self, tile):
    """The tile's wall clock, read over PCIe (latches the high word)."""
    return self.iface.read32(tile, 0xFFB121F0)

  def close(self, hold=True):
    """hold: put every booted tile's RISCs back in soft reset (skip after a hard failure; leave state for inspection)."""
    if self.iface is None: return
    for fn in reversed(self.__dict__.get('cleanup', [])):
      try: fn()
      except Exception as e: print(f'cleanup: {e}')
    try:
      if hold:
        for t in self.booted: self.iface.write32(t, fw.SOFT_RESET, fw.RESET_ALL)
    finally:
      self.iface.close()
      self.iface = None
