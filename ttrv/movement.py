"""Unpack and pack recipes. Runtime addresses are in 16-byte words minus one."""

from . import hw, isa
from .ops import FMT, bind, required, flags, keyword, number, row, runtime_word
from .parse import Num


def field(g, word, shift, width, value):
  mask = ((1 << width) - 1) << shift
  for i in range(4):
    byte = mask >> (8 * i) & 255
    if byte:
      g.tt("RMWCIB" + str(i), byte, (value << shift) >> (8 * i) & byte, word)


def movement(g, s):
  if s.ns == "unpack":
    opts = {
      "fmt": ("src", "in out shared_exp", "transpose"),
      "move": ("src p", "n ctx", "dvalid"),
      "ctx": ("src", "count", "reset"),
      "dvalid": ("src", "", ""),
    }
    if s.name not in opts:
      g.fail("unpack.op", s.name)
    d = bind(s, *opts[s.name])
    mask = flags(required(d, "src", s), {"a": 1, "b": 2})
    for i in range(2):
      if mask & 1 << i:
        with g.temps():
          unpack(g, s, d, i)
  elif s.name == "fmt":
    d = bind(s, "", "in out")
    src = keyword(required(d, "in", s))
    out = keyword(required(d, "out", s))
    pairs = {
      "fp32": ("bf16", "fp32", "bfp8", "bfp4"),
      "bf16": ("bf16", "fp32", "bfp8", "bfp4"),
      "bfp8": ("bfp8", "bfp4"),
      "fp16": ("e4m3",),
    }
    if out not in pairs.get(src, ()):
      g.fail("pack.format", f"{src} to {out}")
    g.event("clear", "gather format bf16", "gather format fp32")
    if src in ("bf16", "fp32") and not (src == "bf16" and out == "fp32"):
      g.event("set", "gather format " + out)
    size = {"fp32": 4, "bf16": 2, "fp16": 2, "bfp8": 1}[src]
    for word, shift, width, value in (
      (70, 0, 1, 1),
      (70, 4, 4, FMT[out]),
      (70, 8, 4, FMT[src]),
      (18, 3, 1, int(src == "fp16")),
      (71, 23, 1, int(out == "e4m3")),
      (12, 16, 16, 16 * size),
      (13, 0, 16, 256 * size),
      (13, 16, 16, 1024 * size),
      (28, 0, 16, 0x1000),
      (24, 0, 16, 65535),
    ):
      field(g, word, shift, width, value)
    g.event("clear", *("pack output " + t for t in FMT))
    g.event("set", "pack output " + out)
    for slot, v in enumerate((0x104, 0x2820, 0x1120)):
      g.tt("SETC16", 37 + slot, v)
  elif s.name == "move":
    d = bind(s, "p dst", "n")
    n = number(d.get("n", Num(1024)), 64, 1024)
    r = number(row(required(d, "dst", s)), 0, 960)
    if n % 64 or r % 64:
      g.fail("pack.shape", "expected aligned row and 64-datum groups")
    p, t = g.expr(required(d, "p", s))
    if not t.endswith("*"):
      g.fail("pack.pointer", t)
    out = t[:-1]
    if out not in FMT:
      g.fail("pack.pointer", t)
    g.event("require", "pack output " + out)
    bfp = out in ("bfp8", "bfp4")
    if bfp and n not in (128, 256, 512, 1024):
      g.fail("pack.shape", "unsupported BFP count")
    exp_words = (n + 255) // 256 if bfp else 0
    field(g, 68, 16, 16, exp_words)
    from .expand import TYPES

    size = exp_words * 16 + (n if out == "bfp8" else n // 2) if bfp else n * TYPES[out][0]
    g.check_pointer(d["p"], 16, size)
    g.tt("SETADC", 4, 0, 3, r // 64)
    pack_address(g, p)
    g.tt("SETADCXX", 4, 15, 0)
    g.tt("SETADCXY", 4, 0, 0, 0, 0, 11)
    g.tt("SETADCZW", 4, 0, 0, 0, 0, 5)
    g.tt("STALLWAIT", isa.Stall.CFG, isa.Wait.PACK0)
    for j in range(n // 64):
      g.tt("PACR", AddrMode=1 if j + 1 == n // 64 else 0, Last=int(j + 1 == n // 64))
  elif s.name == "gather":
    gather(g, s)
  else:
    g.fail("pack.op", s.name)


def pack_address(g, p):
  with g.temps():
    a = g.imm("addi", g.imm("srli", p, 4), -1)
    # SETDMAREG carries a 16-bit immediate across the two Payload fields.
    low = g.imm("srli", g.imm("slli", a, 16), 16)
    g.mem("sw", hw.FIFO, g.calc("or", g.li(isa.tensix("SETDMAREG", RegIndex16b=24)), g.imm("slli", low, 8)))
    runtime_word(g, "SETDMAREG", dict(Payload_SigSelSize=2, RegIndex16b=25), "Payload_SigSel", g.imm("srli", a, 16))
    g.tt("STALLWAIT", isa.Stall.CFG, isa.Wait.THCON | isa.Wait.PACK0)
    g.tt("WRCFG", 12, 0, 69)


def gather(g, s):
  from .parse import Index, Name

  d = bind(s, "p dst", "n step", "acc")
  dst = required(d, "dst", s)
  if not isinstance(dst, Index) or not isinstance(dst.base, Name) or dst.base.id != "dst" or len(dst.idx) != 2:
    g.fail("pack.dst", "expected dst[row, col]")
  p, t = g.expr(required(d, "p", s))
  if t not in ("bf16*", "fp32*"):
    g.fail("pack.gather", "gather requires BF16 or FP32 output")
  row_expr, col_expr = dst.idx
  n = d.get("n", Num(1))
  step = d.get("step", Num(1))
  if isinstance(col_expr, Num):
    number(col_expr, 0, 15)
  if isinstance(n, Num):
    number(n, 1, 64)
  if all(isinstance(e, Num) for e in (n, step, row_expr)):
    number(row_expr, 0, 511)
    if row_expr.value + (n.value - 1) * step.value >= 512:
      g.fail("pack.row", "gather exceeds FP32 Dst")
  g.event("require", "gather format " + t[:-1])
  field(g, 71, 19, 1, int("acc" in d))
  pack_address(g, p)
  g.tt("SETADC", 4, 0, 3, 0)
  g.tt("SETADCXY", 4, 0, 0, 0, 0, 11)
  g.tt("SETADCZW", 4, 0, 0, 0, 0, 15)
  with g.temps():
    slots = g.imm("srli", g.imm("andi", p, 15), 1 if t == "bf16*" else 2)
    aligned = object()
    g.branch("beq", slots, 0, aligned)
    runtime_word(g, "SETADCXX", dict(CntSetMask=4), "x_end2", g.imm("addi", slots, -1))
    g.tt("PACR", ReadIntfSel=1, ZeroWrite=1)
    g.tt("STALLWAIT", isa.Stall.TDMA, isa.Wait.PACK0)
    g.mark(aligned)
  with g.temps():
    remaining = g.alloc()
    row_reg = g.alloc()
    g.mov(remaining, g.condition(n))
    g.mov(row_reg, g.condition(row_expr))
    stride = g.condition(step)
    col = g.condition(col_expr)
    # Both X endpoints select the same column.
    x = g.calc("or", col, g.imm("slli", col, 10))
    g.mem("sw", hw.FIFO, g.calc("or", x, g.li(isa.tensix("SETADCXX", 4))))
    loop, final = object(), object()
    g.mark(loop)
    with g.temps():
      runtime_word(g, "SETADC", dict(CntSetMask=4, DimensionIndex=1), "Value", row_reg)
    g.rv("addi", remaining, remaining, imm=-1)
    g.branch("beq", remaining, 0, final)
    g.tt("PACR", ReadIntfSel=1)
    g.tt("STALLWAIT", isa.Stall.TDMA, isa.Wait.PACK0)
    g.rv("add", row_reg, row_reg, stride)
    g.jump(loop)
    g.mark(final)
    g.tt("PACR", ReadIntfSel=1, Last=1)
  if "acc" in d:
    g.tt("STALLWAIT", isa.Stall.CFG, isa.Wait.PACK0)
    field(g, 71, 19, 1, 0)


def unpack(g, s, d, i):
  sec = 64 + 48 * i
  selector = 1 << i
  if s.name == "fmt":
    src = keyword(required(d, "in", s))
    out = keyword(d.get("out", d["in"]))
    if src == "fp32" and "out" not in d:
      out = "bf16"
    if src not in FMT or out not in FMT or (out not in ("bf16", "fp16") if src == "fp32" else out != src):
      g.fail("unpack.format", f"{src} to {out}")
    if "transpose" in d and i:
      g.fail("unpack.transpose", "transpose requires SrcA")
    if "shared_exp" in d and src not in ("bfp4", "bfp8"):
      g.fail("unpack.shared_exp", "requires BFP input")
    field(g, sec + 9, 8, 1, int("shared_exp" in d))
    if "shared_exp" in d:
      field(g, 62 if i else 50, 0, 8, number(d["shared_exp"], 0, 255))
    fmt = FMT[out]
    size = 1 if fmt in (6, 7, 10) else 2
    for word, shift, width, v in (
      (sec, 0, 4, FMT[src]),
      (sec + 1, 0, 16, 1),
      (sec + 8, 0, 4, fmt),
      (sec + 8, 4, 2, 2),
      (sec + 8, 8, 1, int("transpose" in d)),
      (sec + 9, 0, 4, 15),
      (sec + 9, 16, 4, 15),
      (sec + 7, 22, 1, int(src == "e4m3")),
      (56 + 2 * i, 16, 16, 16 * size),
      (57 + 2 * i, 0, 16, 256 * size),
      (1, 17 + 4 * i, 4, fmt),
    ):
      field(g, word, shift, width, v)
    field(g, sec + 8, 14, 1, 1)
    for ctx in range(2 if i else 8):
      field(g, sec + 28 + ctx % 4, 16 + 8 * (ctx // 4), 8, FMT[src] | fmt << 4)
    if not i:
      field(g, 50, 8, 1, 1)
      g.tt("SETC16", 5, 4)
  elif s.name == "ctx":
    if "count" in d:
      field(g, sec + 9, 9, 4, 8 + number(d["count"], 1, 2 if i else 8) - 1)
    if "reset" in d:
      g.tt("SETC16", 41, 1 << (4 + 8 * i))
      g.tt("UNPACR_NOP", i, 0, 0, 0, 0, 0, 0, 0, 2)
      g.tt("SETC16", 41, 0)
  elif s.name == "dvalid":
    g.tt("UNPACR_NOP", i, 0, 0, 1, 0, 0, 0, 0, 1)
  else:
    n = number(d.get("n", Num(1024)), 1, 1024)
    ctx = number(d.get("ctx", Num(0)), 0, 1 if i else 7)
    p, t = g.expr(required(d, "p", s))
    if not t.endswith("*"):
      g.fail("unpack.pointer", t)
    g.check_pointer(d["p"], 16)
    bfp = t[:-1] in ("bfp4", "bfp8")
    if bfp and n not in (128, 256, 512, 1024):
      g.fail("unpack.shape", "invalid BFP block")
    faces = max(1, n // 256) if bfp else 1
    x = n // faces
    g.unpack_credit = True
    # A single credit serializes base updates, including repeated use of the same context.
    again = object()
    g.mark(again)
    g.branch("bne", g.mem("lw", hw.UNPACK_CREDIT), 0, again)
    field(g, sec + 1, 16, 16, faces)
    field(g, sec, 16, 16, x)
    if not i:
      field(g, sec + 20 + (ctx % 4) // 2, (ctx % 2) * 16, 16, 64)
      field(g, sec + 22 + (ctx % 4) // 2, (ctx % 2) * 16, 16, x)
    a = hw.CONFIG + 4 * (sec + 12 + ctx)
    g.mem("sw", a, g.imm("addi", g.imm("srli", p, 4), -1))
    g.imm("andi", g.mem("lw", a), 0)
    g.mem("sw", hw.UNPACK_CREDIT, 0)
    g.tt("SETADCXX", selector, x - 1, 0)
    g.tt("SETADCZW", selector, 0, 0, 0, 0, 15)
    g.tt("STALLWAIT", isa.Stall.UNPACK, isa.Wait.TRISC_CFG | (isa.Wait.SRCB_CLR if i else isa.Wait.SRCA_CLR))
    for j in range(faces):
      g.tt("UNPACR", i, 0x11 if bfp else 0, 0, ctx, 0, 1, int("dvalid" in d and j + 1 == faces), 0, 0, 0, 0, 0, 1)
    g.tt("STALLWAIT", isa.Stall.SYNC, isa.Wait.UNPACK1 if i else isa.Wait.UNPACK0)
    g.tt("SEMGET", 1 << 5)
