"""Compile expanded TTRV kernels and install them on the column-major worker grid."""

from dataclasses import dataclass
import struct
import fw
from .parse import parse, Error
from .expand import expand, Program
from .layout import layout
from .codegen import Generator
from . import hw


@dataclass
class Kernel:
  images: dict
  manifest: dict
  listing: dict
  program: Program
  timing: dict = None  # cycle-model metadata: where shared values live and which bound runtime loops (cycles.py)

  def install(self, dev, *, scratch_base=fw.DATA_BASE):
    from ops_blackhole import blackhole_build_grid_program

    grid = self.manifest["grid"]
    if grid > len(dev.workers):
      raise ValueError(f"grid {grid} exceeds {len(dev.workers)} workers")
    ceiling = dev.ttrv_keep_base
    kernel = self
    if not fw.DATA_BASE <= scratch_base <= ceiling:
      raise ValueError("invalid worker scratch base")
    if scratch_base != fw.DATA_BASE or (
      any(v.get("keep") for v in self.manifest["storage"].values()) and ceiling != hw.L1_SIZE
    ):
      kernel = compile_program(self.program, ceiling, scratch_base)
    m = kernel.manifest
    if max(m["scratch_end"], dev.ttrv_scratch_end) > min(ceiling, m["keep_base"]):
      raise ValueError("worker scratch overlaps installed persistent storage")
    workers = dev.workers[:grid]
    descriptor = blackhole_build_grid_program(dev, grid, kernel.images, self.args_size)
    for v in m["storage"].values():
      if v.get("keep"):
        zeros = bytes(v["size"])
        for core in workers:
          dev.iface.write(core, v["address"], zeros)
    dev.ttrv_keep_base = min(ceiling, m["keep_base"])
    dev.ttrv_scratch_end = max(dev.ttrv_scratch_end, m["scratch_end"])
    return InstalledKernel(descriptor.addr, descriptor.args_size, m)

  @property
  def args_size(self):
    n = max((d["slot"] + (d["kind"] != "dram") + 1 for d in self.manifest["params"].values()), default=0)
    return (n * 4 + 15) & -16

  def arguments(self, bindings):
    """The launch's argument block: DRAM buffer addresses from the device allocator, device-visible host addresses,
    and integer values."""
    blob = bytearray(self.args_size)
    self.bind(blob, 0, bindings)
    return bytes(blob)

  def bind(self, mem, base, bindings):
    """Write bindings into an argument block at mem[base:]. Parameters not named keep their current words.
    Integer values that change between graph runs are written by queued STOREs instead (BlackholeComputeQueue.store)."""
    params = self.manifest["params"]
    if not bindings.keys() <= params.keys():
      raise ValueError(f"unknown parameters {sorted(bindings.keys() - params.keys())}; expected {list(params)}")
    for k, v in bindings.items():
      d = params[k]
      off = base + d["slot"] * 4
      if d["kind"] == "int":
        struct.pack_into("<Q", mem, off, v & 0xFFFFFFFF)
      elif d["kind"] == "host":
        struct.pack_into("<Q", mem, off, v)
      else:
        page = d["page"]
        offset = v & ((1 << 48) - 1)
        shift = v >> 56 & 63
        bound_page = 1 << shift if shift else ((v >> 48 & 255) + 1) * 64
        if not v >> 63 or bound_page != page or offset % page:
          raise ValueError(f"{k} requires an aligned {page}-byte page binding")
        struct.pack_into("<I", mem, off, (offset // page // 8) * page + (offset // page % 8))


@dataclass(frozen=True)
class InstalledKernel:
  addr: int
  args_size: int
  manifest: dict


def build(source, defines=None, file="<string>"):
  p = source if isinstance(source, Program) else expand(parse(source, file), defines)
  return compile_program(p)


def compile_program(p, ceiling=hw.L1_SIZE, scratch_base=fw.DATA_BASE):
  m = layout(p, ceiling, scratch_base)
  images = {}
  listings = {}
  shared = {}
  owners = {}
  unpack_credit = False
  application_credit = None
  for role in fw.ROLES:
    if role not in p.fns:
      continue
    gen = Generator(p, m, role)
    images[role], listings[role] = gen.generate()
    shared[role] = {name: {"pc": gen.offsets[i], "loc": list(loc)} for i, name, loc in gen.shared_marks}
    unpack_credit |= gen.unpack_credit
    application_credit = gen.app_unpack_sem or application_credit
    for end in gen.owners:
      if end in owners:
        raise Error(p.cbs[end[0]].loc, "cb.owner", f"{end} has multiple owners")
      owners[end] = role
  if unpack_credit and application_credit:
    raise Error(application_credit, "sem.reserved", "unpack credit operations own unpack_sync")
  for q in p.cbs:
    for end in ("producer", "consumer"):
      if (q, end) not in owners:
        raise Error(p.cbs[q].loc, "cb.owner", f"{q} has no {end}")
      m["storage"][q][end] = owners[q, end]
  return Kernel(images, m, listings, p, {"shared": shared, "trip_counts": sorted(trip_names(p))})


def trip_names(p):
  """Shared values that set how many times a runtime loop runs, directly or through local integer assignments.

  A `for i in lo..hi` loop counts the names in hi that lo does not read, so `first..first + count` names count."""
  from .expand import _walk_stmts, _walk_expr
  from .parse import Assign, For, Loop, Name

  shared = {t.id for a in p.shared for t in a.targets}
  found = set()
  for fn in p.fns.values():
    stmts = list(_walk_stmts(fn.body))
    deps = {}
    for st in stmts:
      if isinstance(st, Assign) and not any(st is a for a in p.shared):
        for t in st.targets:
          if isinstance(t, Name):
            deps.setdefault(t.id, set()).update(x.id for x in _walk_expr(st.value) if isinstance(x, Name))

    def names(e, seen=()):
      out = set()
      for x in _walk_expr(e):
        if isinstance(x, Name):
          if x.id in shared:
            out.add(x.id)
          elif x.id in deps and x.id not in seen:
            for d in deps[x.id]:
              out |= names(Name(d, None), (*seen, x.id))
      return out

    for st in stmts:
      if isinstance(st, Loop) and st.count is not None:
        found |= names(st.count)
      elif isinstance(st, For):
        found |= names(st.hi) - names(st.lo)
  return found


def __getattr__(name):  # the runtime opens devices; importing ttrv to compile does not need it
  if name in ("Device", "Var", "Buffer"):
    from . import runtime
    return getattr(runtime, name)
  raise AttributeError(name)
