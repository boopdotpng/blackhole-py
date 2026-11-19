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
    n = sum(2 if d["kind"] == "host" else 1 for d in self.manifest["params"].values())
    return (n * 4 + 15) & -16

  def arguments(self, bindings):
    """The launch's argument block: DRAM buffer addresses from the device allocator, device-visible host addresses,
    and integer values (checked against their declared range)."""
    blob = bytearray(self.args_size)
    self.bind(blob, 0, bindings)
    return bytes(blob)

  def bind(self, mem, base, bindings):
    """Write bindings into an argument block at mem[base:]. Rebinding only some parameters (say the integers
    before each run, tinygrad style) leaves the others as they were."""
    params = self.manifest["params"]
    if not bindings.keys() <= params.keys():
      raise ValueError(f"unknown parameters {sorted(bindings.keys() - params.keys())}; expected {list(params)}")
    for k, v in bindings.items():
      d = params[k]
      off = base + d["slot"] * 4
      if d["kind"] == "int":
        lo, hi = d["range"]
        if not lo <= v < hi:
          raise ValueError(f"{k}={v} is outside its range {lo}..{hi}")
        struct.pack_into("<i" if d["type"] == "i32" else "<I", mem, off, v)
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
  owners = {}
  unpack_credit = False
  application_credit = None
  for role in fw.ROLES:
    if role not in p.fns:
      continue
    gen = Generator(p, m, role)
    images[role], listings[role] = gen.generate()
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
  return Kernel(images, m, listings, p)
