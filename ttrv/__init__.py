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
    Replay variables are patched into role-private arguments by the worker."""
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


def build(source, defines=None, file="<string>"):
  p = source if isinstance(source, Program) else expand(parse(source, file), defines)
  return compile_program(p)


def compile_program(p, ceiling=hw.L1_SIZE, scratch_base=fw.DATA_BASE, kept=None):
  m = layout(p, ceiling, scratch_base, kept)
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


def __getattr__(name):  # the runtime opens devices; importing ttrv to compile does not need it
  if name in ("Device", "Var", "Buffer"):
    from . import runtime
    return getattr(runtime, name)
  raise AttributeError(name)
