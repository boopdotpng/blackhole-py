"""Device operand binding and Blackhole instruction recipes."""

import struct
from . import isa, hw, cfg
from .field import Space, words
from .parse import Name, Bin, Index, Num, Error
from .expand import SEMS
from .layout import options


def keyword(e):
  if isinstance(e, Name):
    return e.id
  raise Error(e.loc, "arg.name", "expected a named operand")


def number(e, lo=0, hi=0xFFFFFFFF):
  if isinstance(e, Num) and type(e.value) == int and lo <= e.value <= hi:
    return e.value
  raise Error(e.loc, "arg.range", f"expected constant in {lo}..{hi}")


def flags(e, values):
  if isinstance(e, Bin) and e.op == "|":
    return flags(e.a, values) | flags(e.b, values)
  k = keyword(e)
  if k not in values:
    raise Error(e.loc, "arg.enum", f"unknown {k}, expected one of {', '.join(values)}")
  return int(values[k])


def bind(s, fields="", optional="", flags_=""):
  fields = fields.split()
  opts = optional.split()
  switches = flags_.split()
  out = {}
  for i, a in enumerate(s.args):
    k = a.name
    if k is None:
      if isinstance(a.value, Name) and a.value.id in switches:
        k = a.value.id
      elif i < len(fields):
        k = fields[i]
    if k in switches and a.name is not None:
      raise Error(a.loc, "arg.flag", f"{k} is a bare flag")
    if k not in fields + opts + switches or k in out:
      raise Error(a.loc, "arg.invalid", f"unexpected or duplicate operand of {s.ns}.{s.name}")
    if a.op not in (None, "="):
      raise Error(a.loc, "arg.invalid", f"unexpected {a.op}")
    out[k] = a.value
  return out


def required(d, k, s):
  if k not in d:
    raise Error(s.loc, "arg.missing", f"{s.ns}.{s.name} needs {k}")
  return d[k]


def row(e):
  if not isinstance(e, Index) or not isinstance(e.base, Name) or e.base.id != "dst" or len(e.idx) != 1:
    raise Error(e.loc, "arg.dst", "expected dst[row]")
  return e.idx[0]


def cb_resource(g, s):
  d = bind(s, "q mode" if s.name == "read" else "q", "n")
  q = keyword(required(d, "q", s))
  if q not in g.p.cbs:
    g.fail("cb.name", q)
  item = g.m["storage"][q]
  producer = s.name in ("reserve", "push")
  return d, item, q, hw.cb_cursor(item["cb"], producer)


def cb(g, s):
  d, item, q, cursor = cb_resource(g, s)
  cap = item["pages"]
  pushed, popped = hw.cb_pushed(item["cb"]), hw.cb_popped(item["cb"])
  if s.name == "read":
    mode = flags(required(d, "mode", s), {"pushed": 0, "popped": 1})
    return [(g.mem("lhu", popped if mode else pushed), "u32")]
  producer = s.name in ("push", "reserve")
  if not producer and s.name not in ("pop", "wait"):
    g.fail("cb.op", s.name)
  owner = (q, "producer" if producer else "consumer")
  g.owners[owner] = g.role
  n = d.get("n", Num(1))
  if isinstance(n, Num):
    number(n, 1, cap)
  n = g.condition(n)
  own = g.mem("lw", cursor + 4)
  if s.name in ("push", "pop"):
    new = g.zext16(g.calc("add", own, n))  # stream counters are 16 bits
    g.mem("sw", cursor + 4, new)
    ptr = g.calc("add", g.mem("lw", cursor), g.calc("mul", n, g.li(item["page"])))
    inside = object()
    g.branch("bltu", ptr, g.li(item["address"] + item["size"]), inside)
    g.rv("sub", ptr, ptr, g.li(item["size"]))
    g.mark(inside)
    g.mem("sw", cursor, ptr)
    g.rv("fence")
    g.mem("sw", pushed if producer else popped, new)
    g.rv("fence")
    return []
  loop = object()
  g.mark(loop)
  other = g.mem("lhu", popped if producer else pushed)
  occ = g.calc("sub", own, other) if producer else g.calc("sub", other, own)
  occ = g.zext16(occ)
  free = g.calc("sub", g.li(cap), occ) if producer else occ
  g.branch("bltu", free, n, loop)
  g.rv("fence")
  return [(g.mem("lw", cursor), item["type"] + "*")]


SRC = {"none": 0, "a": 1, "b": 2}
UNITS = {k.lower(): v for k, v in isa.Stall.__members__.items()}
WAIT = {k.lower(): v for k, v in isa.Wait.__members__.items()}
REG = {k.lower(): v for k, v in isa.LReg.__members__.items() if v < 16} | {f"l{i}": i for i in range(12, 15)}
FMT = hw.FORMAT
SFP_FORMAT = {"fp32": isa.SfpuFormat.FP32, "bf16": isa.SfpuFormat.BF16, "fp16": isa.SfpuFormat.FP16,
              "i32": isa.SfpuFormat.INT32}  # SFPLOAD / SFPSTORE instr_mod0


def operand(e, table):
  k = keyword(e)
  if k not in table:
    raise Error(e.loc, "arg.enum", f"unexpected {k}")
  return table[k]


def addr(g, e):
  # Slot 0 is `hold` (spec §10): never written, zero since launch, the default for an omitted addr=.
  return number(e, 0, 7) if isinstance(e, Num) else operand(e, {"hold": 0, **g.addrmods})


def sfp(g, s):
  name = s.name
  signatures = {
    "nop": "",
    "transp": "",
    "mov": "rd a",
    "add": "rd a b",
    "mul": "rd a b",
    "mad": "rd a b c",
    "shft2": "rd a mode",
    "load": "rd dst",
    "store": "dst a",
    "li": "rd value",
    "const": "rd value",
    "shr": "rd a n", "sar": "rd a n", "shift": "rd a b", "abs": "rd a mode",
    "minmax": "rd a", "and": "rd a b", "or": "rd a b", "xor": "rd a b",
    "iadd": "rd a n", "isub": "rd a n", "cast": "rd a", "recip": "rd a",
    "exexp": "rd a", "exman": "rd a", "setexp": "rd a n", "setsgn": "rd a n",
    "rnd": "rd a", "addi": "rd a n",
  }
  if name in ("begin_if", "otherwise", "end_if", "begin_index", "end_index"):
    if name == "begin_if":
      e = s.args[0].value
      if not isinstance(e, Bin): g.fail("sfp.condition", "expected a comparison")
      if g.predicate_depth: g.tt("SFPPUSHC")
      else: g.tt("SFPENCC", 1, 0, 0, 2)
      g.predicate_depth += 1
      a = operand(e.a, REG)
      if isinstance(e.b, Num) and e.b.value == 0:
        g.tt("SFPSETCC", 0, a, 0, {"<":0, "!=":2, ">=":4, "==":6}[e.op])
      else:
        b = operand(e.b, REG)
        vc, vd = (a,b) if e.op in ("<", ">=") else (b,a)
        g.tt("SFPGT" if e.op in ("<", ">") else "SFPLE", 0, vc, vd, 1)
    elif name == "otherwise": g.tt("SFPCOMPC")
    elif name == "end_if":
      g.predicate_depth -= 1
      if g.predicate_depth: g.tt("SFPPOPC")
      else: g.tt("SFPENCC", 0, 0, 0, 2)
    elif name == "begin_index":
      # LaneConfig bit 2 pairs the index registers, bit 3 captures Dst addresses.
      g.index_bits = operand(s.args[0].value, {"capture":0x0c, "paired":4})
      g.tt("SFPCONFIG", g.index_bits, 15, 3)
    else: g.tt("SFPCONFIG", 65535 ^ g.index_bits, 15, 5)
    return
  if name not in signatures:
    g.fail("sfp.op", name)
  optional = {"load":"fmt addr", "store":"fmt addr", "li":"fmt", "const":"fmt", "rnd":"to", "exman":"hidden", "setexp":"from"}
  switches = {"mul":"neg", "mad":"neg_ab neg_c"}
  d = bind(s, signatures[name], optional.get(name, ""), switches.get(name, ""))
  for k in signatures[name].split():
    required(d, k, s)
  regs = {k: operand(d[k], REG) for k in ("rd", "a", "b", "c") if k in d}
  rd = regs.get("rd", 0)
  dest = rd
  if name == "const":
    if not 12 <= rd <= 14:
      g.fail("sfp.const", "expected l12..l14")
    rd = 0
  if rd > 7:
    g.fail("sfp.dest", "destination must be l0..l7")
  a, b, c = (regs.get(k, 0) for k in "abc")
  if name in ("shr", "sar"):
    g.tt("SFPSHFT", -number(d["n"], 0, 31) & 4095, a, rd, 7 if name == "sar" else 5)
  elif name == "shift":
    if a != rd: g.fail("sfp.operand", "shift requires its destination as first input")
    g.tt("SFPSHFT", 0, b, rd)
  elif name in ("and", "or"): g.tt("SFP" + name.upper(), a, b, rd, 1)
  elif name == "xor":
    if a != rd: g.fail("sfp.operand", "xor requires its destination as first input")
    g.tt("SFPXOR", 0, b, rd)
  elif name == "minmax": g.tt("SFPSWAP", 0, a, rd, 1)
  elif name == "abs": g.tt("SFPABS", 0, a, rd, operand(d["mode"], {"int":0, "float":1}))
  elif name in ("iadd", "isub", "setexp", "setsgn"):
    e = d["n"]
    imm = isinstance(e, Num)
    if not imm and operand(e, REG) != rd: g.fail("sfp.operand", "expected destination register")
    if name in ("iadd", "isub"):
      if imm and name == "isub": g.fail("sfp.operand", "isub requires a register")
      g.tt("SFPIADD", number(e,-2048,2047) & 4095 if imm else 0, a, rd, 4 | int(imm) | (name == "isub") << 1)
    else:
      mode = operand(d["from"], {"fp32":2, "int":0}) if "from" in d else 0
      g.tt("SFP" + name.upper(), number(e,0,255 if name == "setexp" else 1) if imm else 0, a, rd, mode | int(imm))
  elif name == "cast": g.tt("SFPCAST", a, rd)
  elif name == "recip": g.tt("SFPARECIP", 0, a, rd)
  elif name == "exexp": g.tt("SFPEXEXP", 0, a, rd)
  elif name == "exman": g.tt("SFPEXMAN", 0, a, rd, 1 - number(d.get("hidden",Num(1)),0,1))
  elif name == "rnd": g.tt("SFP_STOCH_RND", 0, 0, 0, a, rd, operand(d["to"], {"bf16":1, "fp16":0, "u16":6}))
  elif name == "addi":
    if rd != a or not isinstance(d["n"], Num): g.fail("sfp.operand", "addi requires rd, rd, immediate")
    bits = int.from_bytes(struct.pack("<f", d["n"].value), "little")
    if bits & 65535: g.fail("sfp.operand", "expected exact BF16 immediate")
    g.tt("SFPADDI", bits >> 16, rd)
  elif name == "mov":
    g.tt("SFPMOV", 0, a, rd)
  elif name == "shft2":
    g.tt("SFPSHFT2", 0, a, rd, operand(d["mode"], {"rotate": 3}))
  elif name == "add":
    g.tt("SFPADD", 10, a, b, rd)
  elif name == "mul":
    g.tt("SFPMUL", a, b, 9, rd, int("neg" in d))
  elif name == "mad":
    g.tt("SFPMAD", a, b, c, rd, int("neg_ab" in d) | int("neg_c" in d) << 1)
  elif name in ("nop", "transp"):
    g.tt("SFP" + name.upper())
  elif name in ("li", "const"):
    e = d["value"]
    fmt = keyword(d.get("fmt", Name("fp32")))
    if fmt not in ("i32", "u32", "fp32", "bf16"):
      g.fail("sfp.fmt", fmt)
    if fmt == "bf16":
      if isinstance(e, Num):
        bits = int.from_bytes(struct.pack("<f", e.value), "little")
        g.tt("SFPLOADI", rd, 0, ((bits + 0x7fff + ((bits >> 16) & 1)) >> 16) & 0xffff)
      else:
        r, t = g.expr(e)
        if t != fmt: g.fail("sfp.type", "expected bf16")
        runtime_word(g, "SFPLOADI", dict(lreg_ind=rd, instr_mod0=0), "imm16", r)
    elif isinstance(e, Num):
      bits = (
        int.from_bytes(struct.pack("<f", e.value), "little")
        if fmt == "fp32"
        else number(e, -(2**31) if fmt == "i32" else 0, 2**31 - 1 if fmt == "i32" else 2**32 - 1) & 0xFFFFFFFF
      )
      g.tt("SFPLOADI", rd, 8, bits >> 16)
      g.tt("SFPLOADI", rd, 10, bits & 65535)
    else:
      r, t = g.expr(e)
      if t != fmt:
        g.fail("sfp.type", f"expected {fmt}")
      runtime_word(g, "SFPLOADI", dict(lreg_ind=rd, instr_mod0=8), "imm16", g.imm("srli", r, 16))
      runtime_word(g, "SFPLOADI", dict(lreg_ind=rd, instr_mod0=10), "imm16", r)
    if name == "const":
      g.tt("SFPCONFIG", 0, dest, 0)
      g.tt("SFPNOP")
  else:
    fmt = operand(d["fmt"], SFP_FORMAT) if "fmt" in d else isa.SfpuFormat.DEFAULT
    e = row(d["dst"])
    fields = dict(lreg_ind=rd if name == "load" else a, instr_mod0=fmt, sfpu_addr_mode=addr(g, d.get("addr", Num(0))))
    field_word(g, "SFP" + name.upper(), fields, "dest_reg_addr", e)


def setc16(g, *sets):
  """Write one ThreadConfig word with SETC16: cfg.FIELD(value), ... all in the same word. The rest of the word becomes
  zero."""
  if any(s.field.space is not Space.THREAD for s in sets):
    raise ValueError("SETC16 writes ThreadConfig fields")
  placed = words(sets)
  if len(placed) != 1:
    raise ValueError(f"SETC16 writes one word, got {sorted(placed)}")
  (word, v), = placed.items()
  g.tt("SETC16", word, v)


def rmw(g, *sets):
  """Read-modify-write Config fields with RMWCIB<byte>: one instruction per byte the fields touch, other bits kept."""
  by_byte = {}
  for s in sets:
    if s.field.space is not Space.CONFIG:
      raise ValueError(f"{s.field.name} is not a Config field")
    for i in range(4):
      mask = s.field.mask >> (8 * i) & 255
      if mask:
        m, v = by_byte.get((s.field.word, i), (0, 0))
        by_byte[(s.field.word, i)] = (m | mask, v | (s.bits >> (8 * i) & mask))
  for (word, i), (mask, v) in by_byte.items():
    g.tt("RMWCIB" + str(i), mask, v, word)


def runtime_word(g, op, fields, field, r):
  _, shift, width = next(v for v in isa.TENSIX[op][1] if v[0] == field)
  r = g.calc("and", r, g.li((1 << width) - 1))
  if shift:
    r = g.imm("slli", r, shift)
  g.mem("sw", hw.INSTRN_BUF, g.calc("or", r, g.li(isa.tensix(op, **fields))))


def field_word(g, op, fields, field, e):
  if isinstance(e, Num):
    g.tt(op, **fields, **{field: number(e)})
  else:
    runtime_word(g, op, fields, field, g.condition(e))


def math(g, s):
  if s.name == "addrmod" or s.name == "rwc":
    mod = s.name == "addrmod"
    mask = cr = release = 0
    counters = []  # (counter index, mode, n): srca, srcb, dst, fidelity
    val = [0, 0, 0, 0]
    modes = set()
    seen = set()
    sp = None
    slot = None
    label = None
    for a in s.args:
      k, e = a.name, a.value
      if k is None:
        if mod:
          label = keyword(e)
        elif keyword(e) == "reset":
          mask = 15
          modes.add(False)
        else:
          g.fail("math.rwc", "expected reset")
      elif k == "slot" and mod:
        slot = number(e, 0, 7)
        if slot == 0:
          g.fail("math.addrmod", "slot 0 is reserved as `hold` (spec §10); use slots 1..7")
      elif k == "sp" and not mod:
        if sp is not None or a.op != "=":
          g.fail("math.rwc", "sp requires one absolute assignment")
        sp = number(e, 0, 1023)
        modes.add(False)
      elif k == "release" and not mod:
        release = flags(e, SRC)
      else:
        if k not in ("srca", "srcb", "dst", "fidelity") or k in seen:
          g.fail("math.counter", str(k))
        seen.add(k)
        i = ("srca", "srcb", "dst", "fidelity").index(k)
        mode = a.op
        if isinstance(e, Bin) and e.op == "+" and mode == "=":
          mode = keyword(e.a)
          e = e.b
        n = number(e, 0, (63, 63, 1023, 3)[i] if mod else 15)
        if mode not in ("=", "+=", "cr", "c") or mode == "c" and i != 2:
          g.fail("math.counter", mode)
        if i == 3 and not mod and (mode != "=" or n):
          g.fail("math.rwc", "fidelity only supports =0")
        if i == 3 and mode not in ("=", "+="):
          g.fail("math.counter", "invalid fidelity base")
        if mode == "=" and n and mod:
          g.fail("math.counter", "absolute addrmod must be zero")
        if mod:
          counters.append((i, mode, n))
        else:
          modes.add(mode == "+=")
          mask |= 1 << i
          cr |= (int(mode in ("c", "cr")) << i) | (int(mode == "c") << 3)
          val[i] = n
    if mod:
      if slot is None or label is None:
        g.fail("math.addrmod", "expected name and slot")
      if label == "hold":
        g.fail("math.addrmod", "`hold` is the reserved slot 0")
      if g.addrmods.setdefault(label, slot) != slot:
        g.fail("math.addrmod", "ambiguous slot name")
      m = hw.ADDR_MOD[slot]
      sets = []
      for i, mode, n in counters:
        sets += [m.incr[i](n), m.clear[i](mode == "=")]
        if i < 3:
          sets.append(m.cr[i](mode == "cr"))
        if i == 2:
          sets.append(m.c_to_cr(mode == "c"))
      placed = words(sets)
      for word in m.words:  # whole words: AB2 (the 1-bit increments) is always cleared
        g.tt("SETC16", word, placed.get(word, 0))
    elif True in modes:
      if len(modes) > 1 or release or val[3]:
        g.fail("math.rwc", "invalid mixed increment")
      g.tt("INCRWC", 0, val[2], val[1], val[0])
    else:
      if sp is not None:
        g.tt("SETRWC", 0, 0, sp >> 8, sp >> 4 & 15, sp & 15, 16)
      if mask or release or sp is None:
        g.tt("SETRWC", release, cr, val[2], val[1], val[0], mask)
  elif s.name == "fmt":
    d = bind(s, "", "dst sfp")
    dst_formats = {"fp32": hw.DataFormat.FLOAT32, "bf16": hw.DataFormat.FLOAT16_B}
    f = operand(required(d, "dst", s), dst_formats)
    sf = operand(d.get("sfp", d["dst"]), dst_formats)
    fp32 = hw.DataFormat.FLOAT32
    rmw(g, cfg.ALU_FORMAT_SPEC_REG2_Dstacc(f), cfg.ALU_ACC_CTRL_Fp32_enabled(f == fp32),
        cfg.ALU_ACC_CTRL_SFPU_Fp32_enabled(sf == fp32))
    # The packer reads the same physical Dst width, independently of its input conversion.
    rmw(g, cfg.PCK_DEST_RD_CTRL_Read_32b_data(f == fp32))
    setc16(g, cfg.SFPU_DEST_FMT_Enable(1), cfg.SFPU_DEST_FMT_Base(sf))
  elif s.name == "cfg":
    d = bind(s, "", "dst_offset")
    e = required(d, "dst_offset", s)
    if isinstance(e, Num):
      setc16(g, cfg.DEST_TARGET_REG_CFG_MATH_Offset(number(e, 0, 4095)))
    else:  # a runtime offset: build the SETC16 word on the RISC (the field is alone in its ThreadConfig word)
      f = cfg.DEST_TARGET_REG_CFG_MATH_Offset
      r = g.calc("and", g.condition(e), g.li((1 << f.width) - 1))
      if f.shift: r = g.imm("slli", r, f.shift)
      runtime_word(g, "SETC16", dict(setc16_reg=f.word), "setc16_value", r)
  elif s.name == "zero":
    d = bind(s, "", "face fmt")
    # face counts 16-row faces of the whole Dst from row 0 (not from the dst_offset); tile t is faces 4t..4t+3.
    g.tt("ZEROACC", 1, operand(required(d, "fmt", s), {"fp32": 1, "bf16": 0}), 0, 1, number(required(d, "face", s), 0, 63))
  elif s.name == "mova2d":
    d = bind(s, "dst", "addr src rows")
    rows = number(d.get("rows", Num(8)), 1, 8)
    if rows not in (1, 8): g.fail("math.rows", "expected 1 or 8")
    fields = dict(src=number(d.get("src", Num(0)),0,63), addr_mode=addr(g,d.get("addr", Num(0))), instr_mod=2 if rows == 8 else 0)
    field_word(g, "MOVA2D", fields, "dst", row(d["dst"]) if "dst" in d else Num(0))
  elif s.name == "mvmul":
    d = bind(s, "dst", "addr release")
    fields = dict(addr_mode=addr(g, d.get("addr", Num(0))), clear_dvalid=flags(d.get("release", Name("none")), SRC))
    field_word(g, "MVMUL", fields, "dst", row(d["dst"]) if "dst" in d else Num(0))
  elif s.name in ("elwmul", "elwadd", "elwsub"):
    d = bind(s, "dst", "addr release broadcast", "accumulate")
    fields = dict(
      addr_mode=addr(g, d.get("addr", Num(0))),
      clear_dvalid=flags(d.get("release", Name("none")), SRC),
      dest_accum_en=int("accumulate" in d),
      instr_mod19=operand(d.get("broadcast", Name("none")), {"none": 0, "column": 1, "row": 2, "scalar": 3}),
    )
    field_word(g, s.name.upper(), fields, "dst", row(d["dst"]) if "dst" in d else Num(0))
  else:
    g.fail("math.op", s.name)


def allocate_replay(g, t, length=None):
  """Replays pack into the thread's 32-word buffer in load order. `replay name, at=N` pins one at word N instead, and
  may overlap others: the kernel reloads whatever it overwrote before running that again. length: the lowered word
  count when known (a load), else an estimate from the ops."""
  if length is None: length = sum(2 if op.ns == "sfp" and op.name == "li" else 1 for op in t.body)
  at = options(t, {"at"}).get("at")
  pinned = g.__dict__.setdefault("pinned_replays", set())
  start = at if at is not None else sum(n for k, (_, n) in g.replays.items() if k not in pinned)
  if not length or start + length > 32:
    g.fail("replay.size", "replay exceeds 32 words")
  if at is not None: pinned.add(t.name)
  g.replays[t.name] = start, length


def templates(g, s):
  d = bind(s, "template", "n mask" if s.ns == "mop" and s.name == "run" else "")
  k = keyword(required(d, "template", s))
  t = g.p.templates.get(k)
  if not t or t.kind != s.ns:
    g.fail("template.name", k)
  if s.name == "run":
    g.event("require", "loaded " + k)
    if t.kind == "mop":
      masked = any(a.name is None and isinstance(a.value, Name) and a.value.id == "mask" for a in t.opts)
      if masked:
        n = d.get("n", Num(1))
        m = d.get("mask", Num(0))
        if isinstance(n, Num):
          number(n, 1, 128)
        if isinstance(m, Num) and isinstance(n, Num):
          v = number(m)
          g.tt("MOP_CFG", v >> 16)
          g.tt("MOP", 0, n.value - 1, v & 65535)
        else:
          v = g.condition(m)
          cnt = g.imm("addi", g.condition(n), -1)
          runtime_word(g, "MOP_CFG", {}, "zmask_hi16", g.imm("srli", v, 16))
          lo = g.imm("srli", g.imm("slli", v, 16), 16)
          bits = g.calc("or", g.imm("slli", g.imm("andi", cnt, 127), 16), lo)
          g.mem("sw", hw.INSTRN_BUF, g.calc("or", g.li(isa.tensix("MOP")), bits))
      else:
        if len(d) != 1:
          g.fail("mop.run", "n and mask require a mask MOP")
        g.tt("MOP", 1)
    else:
      if k not in g.replays:
        allocate_replay(g, t)
      g.tt("REPLAY", *g.replays[k])
    return
  if s.name != "load":
    g.fail("template.op", s.name)
  words = []
  for line in t.body:
    op = line.stmt if t.kind == "mop" else line
    native = op.ns in ("math", "sfp", "tensix", "sfpmacro") or (op.ns, op.name) == ("unpack", "face")
    if not (native or (t.kind, op.ns, op.name) == ("mop", "replay", "run")):
      g.fail("template.body", "expected a native instruction")
    start = len(g.items)
    g.loc = op.loc
    lower(g, op)
    items = [item for item in g.items[start:] if item[0] is not None]
    events = [event for pc in range(start, len(g.items)) for event in g.events.pop(pc, [])]
    del g.items[start:]
    for effect, facts, _ in events:
      if effect == "require":
        g.event(effect, *facts)
    if not items or any(not isinstance(w, int) or w & 3 == 3 for w, _ in items):
      g.fail("template.runtime", "constant Tensix words required")
    if t.kind == "mop" and len(items) != 1:
      g.fail("template.slot", "MOP slot needs one word")
    words.extend(isa.outline(w) for w, _ in items)
  g.loc = s.loc
  if t.kind == "replay":
    if k not in g.replays:
      allocate_replay(g, t, len(words))
    start, n = g.replays[k]
    if n != len(words):
      g.fail("replay.body", "expected native replay instructions")
    g.tt("REPLAY", start, n, 0, 1)
    for w in words:
      g.word(isa.inline(w))
  else:
    opts = options(t, {"inner", "outer", "mask"})
    if opts.get("mask"):
      groups = {
        label: [w for line, w in zip(t.body, words) if line.label == label] for label in ("a", "b", "skip_a", "skip_b")
      }
      if (
        set(opts) != {"mask"}
        or sum(map(len, groups.values())) != len(words)
        or len(groups["a"]) not in (1, 4)
        or any(len(groups[k]) > 1 for k in ("b", "skip_a", "skip_b"))
      ):
        g.fail("mop.labels", "invalid mask MOP slots")
      nop = isa.tensix("NOP")
      config = [
        0,
        int(bool(groups["b"])) | int(len(groups["a"]) == 4) << 1,
        *(groups["b"] or [nop]),
        *groups["a"],
        *([nop] * (4 - len(groups["a"]))),
        *(groups["skip_a"] or [nop]),
        *(groups["skip_b"] or [nop]),
      ]
    else:
      outer, inner = opts.get("outer", 1), opts.get("inner", 1)
      labels = {line.label: w for line, w in zip(t.body, words)}
      if (
        len(labels) != len(words)
        or labels.keys() - set("start loop0 loop1 end0 end1 last_inner last".split())
        or "loop0" not in labels
      ):
        g.fail("mop.labels", k)
      if not 1 <= outer <= 1023 or not 0 <= inner <= 1023 or inner == 0 and "start" not in labels:
        g.fail("mop.count", k)
      nop = isa.tensix("NOP")
      last = labels.get("last_inner", labels.get("loop1", labels["loop0"]))
      config = [
        outer,
        inner,
        *[labels.get(i, nop) for i in ("start", "end0", "end1", "loop0", "loop1")],
        labels.get("last", last),
        last,
      ]
    g.ttsync(hw.MOP_EXPANDER_DONE_CHECK)  # the expander must be idle before its template changes
    assert len(config) == hw.MOP_CFG_WORDS
    for i, w in enumerate(config):
      g.mem("sw", hw.MOP_CFG + 4 * i, g.li(w))
    g.rv("fence")
    g.event("clear", *("loaded " + x for x, t in g.p.templates.items() if t.kind == "mop"))
  g.event("set", "loaded " + k)


def lower(g, s):
  ns, n = s.ns, s.name
  if ns == "l1" and n == "copy_words":
    operands = bind(s, "dst src", "n")
    words = number(required(operands, "n", s), 1, 512)
    dst, src = (required(operands, key, s) for key in ("dst", "src"))
    out, dtype = g.expr(dst)
    data, stype = g.expr(src)
    if dtype != stype or not dtype.endswith("*"):
      g.fail("l1.copy", "expected two L1 pointers of the same type")
    for ptr in (dst, src): g.check_pointer(ptr, align=4, length=4 * words)
    # Up to four loads go out before their stores so the L1 latencies overlap; dst must not overlap src.
    for first in range(0, words, 4):
      regs = []
      for i in range(first, min(first + 4, words)):
        regs.append(g.alloc())
        g.rv("lw", regs[-1], data, imm=4*i)
      for i, reg in zip(range(first, words), regs):
        g.rv("sw", 0, out, reg, imm=4*i)
    return []
  if ns == "cb":
    return cb(g, s)
  if ns == "noc":
    from .noc import noc

    if g.role not in ("brisc", "ncrisc"):
      g.fail("op.role", "NoC requires a data-movement RISC")
    return noc(g, s)
  # Unpack and pack stay on their threads (their CBs and semaphores belong to them). Any TRISC may issue math and
  # SFPU instructions: RWCs, ADDR_MODs and the Dst offset are per-thread state, and an SFPU stream from another
  # thread overlaps the math thread's FPU work.
  if (
    not g.role.startswith("trisc")
    or ns in ("unpack", "pack")
    and g.role != {"unpack": "trisc0", "pack": "trisc2"}[ns]
  ):
    g.fail("op.role", f"{ns}.{n} cannot run on {g.role}")
  if ns == "math":
    math(g, s)
  elif ns == "sfp":
    sfp(g, s)
    if g.sfprograms:
      g.event("tick")
  elif ns == "sfpmacro":
    if g.role != "trisc1":
      g.fail("op.role", "SFPMACRO requires TRISC1")
    from .sfpmacro import emit

    emit(g, s)
  elif ns in ("mop", "replay"):
    templates(g, s)
  elif ns in ("unpack", "pack"):
    from .movement import movement

    movement(g, s)
  elif ns == "tensix" and n == "wait":
    bind(s)
    g.drain()
  elif ns == "tensix" and n == "stall":
    d = bind(s, "units conditions")
    g.tt("STALLWAIT", flags(required(d, "units", s), UNITS), flags(required(d, "conditions", s), WAIT))
  elif ns == "sem":
    d = bind(
      s,
      "units sems cond" if n == "stall" else "sems",
      "max value" if n == "init" else "",
      "risc" if n in ("inc", "dec") else "",
    )
    names = {k: 1 << i for i, k in enumerate(SEMS)}
    names.update({k: names[t.hw] for k, t in g.p.sems.items()})
    mask = flags(required(d, "sems", s), names)
    if mask & (1 << hw.Sem.UNPACK_SYNC):
      g.app_unpack_sem = s.loc
    for alias in g.p.sems.values():
      if not mask & names[alias.hw]:
        continue
      maximum = options(alias, {"max"}).get("max", 1)
      if n == "init":
        # max=1 restores the boot state (firmware initializes every semaphore once, to max 1): a kernel that raised
        # the maximum puts it back when done, since kernels with max=1 semaphores rely on it without an init.
        if number(d.get("max", Num(1)), 0, 15) not in (maximum, 1):
          g.fail("sem.max", f"{alias.name} requires max={maximum}")
        g.event("set" if number(d.get("max", Num(1)), 0, 15) == maximum else "clear", "initialized " + alias.hw)
      elif maximum != 1:
        g.event("require", "initialized " + alias.hw)
    if n == "init":
      maximum = number(d.get("max", Num(1)), 0, 15)
      g.tt("SEMINIT", maximum, number(d.get("value", Num(0)), 0, maximum), mask)
    elif n == "stall":
      g.tt(
        "SEMWAIT", flags(required(d, "units", s), UNITS), mask, operand(required(d, "cond", s), {"nonzero": 1, "notmax": 2})
      )
    elif n == "read" or "risc" in d:
      if n == "read" and mask.bit_count() != 1:
        g.fail("sem.read", "expected one semaphore")
      for i in range(8):
        if mask & 1 << i:
          a = hw.semaphore(i)
          if n == "read":
            return [(g.mem("lw", a), "u32")]
          g.mem("sw", a, g.li(hw.SEM_POST if n == "inc" else hw.SEM_GET))
    elif n in ("inc", "dec"):
      g.tt("SEMPOST" if n == "inc" else "SEMGET", mask)
    else:
      g.fail("sem.op", n)
  else:
    g.fail("op.unknown", f"{ns}.{n}")
  return []
