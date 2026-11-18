"""Allocate the firmware parameter block and worker L1 in declaration order."""

import fw
from .expand import TYPES
from .parse import Error, Num, Name


def options(decl, allowed):
  out = {}
  for a in decl.opts:
    if a.name is None and isinstance(a.value, Name) and a.value.id in ("keep", "mask"):
      key, v = a.value.id, True
    elif a.name not in ("keep", "mask") and a.op == "=" and isinstance(a.value, Num) and type(a.value.value) is int:
      key, v = a.name, a.value.value
    else:
      raise Error(a.loc, "option.value", "expected a constant declaration option")
    if key not in allowed or key in out:
      raise Error(a.loc, "option.name", f"invalid or repeated option {key}")
    out[key] = v
  return out


def layout(p, ceiling=0x180000, scratch_base=fw.DATA_BASE):
  slots, cursor, storage, params = 0, scratch_base, {}, {}
  for name, d in p.params.items():
    if d.range is not None:  # integer parameter: its value is the slot word
      params[name] = dict(slot=slots, kind="int", type=d.type.name, range=list(d.range))
      slots += 1
    elif "host" in {a.value.id for a in d.opts if a.name is None and hasattr(a.value, "id")}:
      if any(a.name is not None for a in d.opts):
        raise Error(d.loc, "param.opts", "a host buffer takes no options besides `host`")
      params[name] = dict(slot=slots, kind="host", type=d.type.name)
      slots += 2
    else:
      page = options(d, {"page"}).get("page", 1) * TYPES[d.type.name][1]
      if page <= 0 or page > 16384:
        raise Error(d.loc, "param.page", "invalid DRAM page size")
      params[name] = dict(slot=slots, kind="dram", type=d.type.name, page=page)
      slots += 1
    if slots > fw.PARAM_SIZE // 4:
      raise Error(d.loc, "param.slots", "parameter block exceeds 16 words")
  for name in p.names:
    if name not in p.l1 and name not in p.cbs:
      continue
    d = (p.l1 | p.cbs)[name]
    opts = options(d, {"align", "keep"} if name in p.l1 else {"align", "pages"})
    align, pages = opts.get("align", 64), opts.get("pages", 1)
    size, n = TYPES[d.type.name][0], d.type.count
    page = size * n if size else ((n // 16 + 15) // 16) * 16 + (n if d.type.name == "bfp8" else n // 2)
    if align < 64 or align & (align - 1):
      raise Error(d.loc, "storage.align", "alignment must be a power of two >= 64")
    address = (cursor + align - 1) & -align
    if opts.get("keep"):
      address = (ceiling - page * pages) & -align
    item = dict(address=address, size=page * pages, type=d.type.name, count=n)
    if name in p.cbs:
      cb = list(p.cbs).index(name)
      if cb >= 32 or not 1 <= pages <= 32768 or pages & (pages - 1) or page % 4:
        raise Error(d.loc, "cb.layout", "invalid CB capacity, page size or stream index")
      item.update(cb=cb, pages=pages, page=page)
    storage[name] = item
    if opts.get("keep"):
      item["keep"] = True
      ceiling = address
    else:
      cursor = address + item["size"]
    if cursor > ceiling:
      raise Error(d.loc, "storage.overflow", "worker L1 exhausted")
  return dict(grid=p.grid, params=params, storage=storage, scratch_end=cursor, keep_base=ceiling)
