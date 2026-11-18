"""Compile load-macro sequences and assign the four shared SFPU instruction templates."""

from . import isa
from .layout import options
from .parse import Name, Num, Index
from .ops import bind, number, keyword, required, operand, REG, addr, row, field_word

UNITS = ("simple", "mad", "round", "store")
FORMATS = {"fp32": 3, "bf16": 2, "fp16": 1, "i32": 4}


def prepare(g):
  g.sfprograms = {}
  templates = {}
  kinds = {}
  store_fmt = None
  uses_load = 0
  for t in g.p.templates.values():
    if t.kind != "sfpmacro":
      continue
    g.loc = t.loc
    slot = options(t, {"slot"}).get("slot")
    if slot not in range(4):
      g.fail("sfpmacro.slot", "expected slot=0..3")
    seq = 0
    words = []
    schedules = {}
    after = 0
    for line in t.body:
      op = line.stmt
      g.loc = op.loc
      unit = line.label
      if unit not in UNITS or unit in schedules or op.ns != "sfp":
        g.fail("sfpmacro.unit", unit)
      signatures = {
        "mov": ("simple", "rd vc"),
        "add": ("mad", "rd vb vc"),
        "mul": ("mad", "rd va vb"),
        "mad": ("mad", "rd va vb vc"),
        "shft2": ("round", "rd vc mode"),
        "store": ("store", "dst src"),
      }
      if op.name not in signatures or signatures[op.name][0] != unit:
        g.fail("sfpmacro.unit", f"{unit} cannot issue {op.name}")
      d = bind(op, signatures[op.name][1], "delay after fmt" if unit == "store" else "delay after")
      timing = [k for k in ("after", "delay") if k in d]
      if len(timing) != 1:
        g.fail("sfpmacro.delay", "specify delay or after")
      timing = timing[0]
      delay = number(d[timing], 0, 7)
      if kinds.setdefault(unit, timing) != timing:
        g.fail("sfpmacro.delay", f"inconsistent {unit} timing")
      if timing == "after":
        after = max(after, delay)

      def reg(k):
        return keyword(required(d, k, op))

      if unit == "store":
        e = required(d, "dst", op)
        if not (
          isinstance(e, Name) and e.id == "dst" or isinstance(e, Index) and isinstance(row(e), Name) and row(e).id == "x"
        ):
          g.fail("sfpmacro.store", "use dst[x] for the loaded row")
        source = reg("src")
        if source not in ("x", "l16"):
          g.fail("sfpmacro.store", source)
        byte = 3 | int(source == "l16") << 6
        if "fmt" in d:
          fmt = operand(d["fmt"], FORMATS)
          if store_fmt not in (None, fmt):
            g.fail("sfpmacro.format", "macros share the store format")
          store_fmt = fmt
        else:
          uses_load |= 1 << slot
      else:
        dest = reg("rd")
        if dest not in ("x", "l16"):
          g.fail("sfpmacro.dest", dest)
        inputs = [k for k in ("va", "vb", "vc") if k in d and reg(k) == "x"]
        if len(inputs) != 1 or inputs[0] == "va":
          g.fail("sfpmacro.input", "x must occur once as VB or VC")

        def source(k):
          return 0 if reg(k) == "x" else operand(d[k], REG)

        if op.name == "mov":
          w = isa.tensix("SFPMOV", 0, source("vc"))
        elif op.name == "shft2":
          w = isa.tensix("SFPSHFT2", 0, source("vc"), 0, operand(required(d, "mode", op), {"rotate": 3}))
        else:
          va = 10 if op.name == "add" else source("va")
          vc = 9 if op.name == "mul" else source("vc")
          w = isa.tensix("SFP" + op.name.upper(), va, source("vb"), vc)
        index = templates.setdefault(w, len(templates))
        if index >= 4:
          g.fail("sfpmacro.slots", "more than four shared instruction templates")
        words.append(w | ((12 + index) << 4))
        byte = (4 + index) | int(inputs[0] == "vb") << 7 | int(dest == "l16") << 6
      schedules[unit] = (delay, byte)
      seq |= (byte | delay << 3) << (8 * UNITS.index(unit))
    if "simple" in schedules and "round" in schedules:
      a, b = schedules["simple"], schedules["round"]
      if a[0] == b[0] and (a[1] ^ b[1]) & 64 == 0:
        g.fail("sfpmacro.collision", "simple and round write the same register in one cycle")
    g.sfprograms[t.name] = (slot, words, seq, after)
  g.sfmisc = (
    (store_fmt or 0) | (uses_load << 4) | sum((1 << (8 + UNITS.index(k))) for k, t in kinds.items() if t == "after")
  )


def emit(g, s):
  d = bind(s, "template reg dst" if s.name == "run" else "template", "fmt addr" if s.name == "run" else "")
  name = keyword(required(d, "template", s))
  if name not in g.sfprograms:
    g.fail("sfpmacro.name", name)
  slot, words, seq, after = g.sfprograms[name]
  if s.name == "load":
    g.event("require", "SFPU schedule complete")
    for w in words:
      g.word(isa.inline(w))
    if seq >> 16:
      g.tt("SFPLOADI", 0, 8, seq >> 16)
      g.tt("SFPLOADI", 0, 10, seq & 65535)
      g.tt("SFPCONFIG", 0, 4 + slot, 0)
    else:
      g.tt("SFPCONFIG", seq, 4 + slot, 1)
    g.tt("SFPCONFIG", g.sfmisc, 8, 1)
    g.tt("SFPNOP")
    g.event("clear", *("loaded " + k for k, v in g.sfprograms.items() if v[0] == slot))
    g.event("set", "loaded " + name)
  elif s.name == "run":
    g.event("require", "loaded " + name)
    r = operand(required(d, "reg", s), REG)
    e = row(required(d, "dst", s))
    if r > 7 or isinstance(e, Num) and (number(e, 0, 1023) & 1) != r // 4:
      g.fail("sfpmacro.parity", "register group and Dst row parity disagree")
    fields = dict(
      lreg_ind=(slot << 2) | (r & 3),
      instr_mod0=operand(d["fmt"], FORMATS) if "fmt" in d else 0,
      sfpu_addr_mode=addr(g, d.get("addr", Num(0))),
    )
    field_word(g, "SFPLOADMACRO", fields, "dest_reg_addr", e)
    g.event("tick")
    if after:
      g.event("clear", "SFPU schedule complete", *(f"SFPU cycle {i}" for i in range(1, after)))
  else:
    g.fail("sfpmacro.op", s.name)
