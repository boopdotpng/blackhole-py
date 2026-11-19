"""Unpack and pack recipes. Config fields are named as in cfg_defines.h (see hw.py); THCON_SEC0 is unpacker A and the
packer, THCON_SEC1 unpacker B. L1 addresses in config are in 16-byte words minus one."""

from . import hw, isa
from . import cfg
from .ops import FMT, bind, required, flags, keyword, number, row, runtime_word, rmw, setc16
from .parse import Num

UNPACK_SYNC = 1 << hw.Sem.UNPACK_SYNC  # semaphore mask of the unpack credit
UNPACK_CREDIT = hw.semaphore(hw.Sem.UNPACK_SYNC)


def movement(g, s):
  if s.ns == "unpack":
    if s.name == "dest":
      unpack_dest(g, s)
      return
    if s.name in ("acquire", "post", "release"):
      bind(s)
      g.unpack_credit = True
      if s.name == "acquire":
        wait_unpack_credit(g)
      elif s.name == "post":
        g.mem("sw", UNPACK_CREDIT, hw.SEM_POST)
      else:
        g.tt("SEMGET", UNPACK_SYNC)
      return
    opts = {
      "shape": ("src", "n faces ctx", ""),
      "base": ("src p", "ctx", ""),
      "reset_zw": ("src", "", ""),
      "face": ("src", "ctx", "next_l1_face next_tile_face dvalid"),
      "fmt": ("src", "in out shared_exp", "transpose"),
      "move": ("src p", "n ctx", "dvalid"),
      "ctx": ("src", "count", "reset"),
      "dvalid": ("src", "", ""),
    }
    if s.name not in opts:
      g.fail("unpack.op", s.name)
    d = bind(s, *opts[s.name])
    mask = flags(required(d, "src", s), {"a": 1, "b": 2})
    if s.name == "reset_zw":
      g.tt("SETADCZW", mask, 0, 0, 0, 0, 15)
      return
    if s.name == "face" and mask not in (1, 2):
      g.fail("unpack.face", "select one source bank")
    for i in range(2):
      if mask & 1 << i:
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
    size = {"fp32": 4, "bf16": 2, "fp16": 2, "bfp8": 1}[src]  # bytes per datum read from Dst
    for write in (
      cfg.THCON_SEC0_REG1_Disable_zero_compress(1),
      cfg.THCON_SEC0_REG1_Out_data_format(FMT[out]),
      cfg.THCON_SEC0_REG1_In_data_format(FMT[src]),
      cfg.PCK_DEST_RD_CTRL_Round_10b_mant(src == "fp16"),
      cfg.THCON_SEC0_REG1_Pac_LF8_4b_exp(out == "e4m3"),
      cfg.PCK0_ADDR_CTRL_XY_REG_0_Ystride(16 * size),    # Dst row
      cfg.PCK0_ADDR_CTRL_ZW_REG_0_Zstride(256 * size),   # face
      cfg.PCK0_ADDR_CTRL_ZW_REG_0_Wstride(1024 * size),  # tile
    ):
      rmw(g, write)
    rmw(g, cfg.PACK_COUNTERS_SEC0_pack_per_xy_plane(0), cfg.PACK_COUNTERS_SEC0_pack_reads_per_xy_plane(16))
    rmw(g, cfg.PCK_EDGE_OFFSET_SEC0_mask(0xFFFF))
    g.event("clear", *("pack output " + t for t in FMT))
    g.event("set", "pack output " + out)
    # Packer address modifiers: 0 steps one row, 1 rewinds to the next face, 2 steps to the next tile.
    m = hw.PACK_ADDR_MOD
    setc16(g, m[0].ysrc_incr(4), m[0].ydst_incr(4))
    setc16(g, m[1].ysrc_clear(1), m[1].ydst_clear(1), m[1].zsrc_clear(1))
    setc16(g, m[2].ysrc_clear(1), m[2].ydst_incr(4), m[2].zsrc_incr(1))
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
    if out == "u32": out = "fp32"  # raw 32-bit pack into integer storage
    if out not in FMT:
      g.fail("pack.pointer", t)
    g.event("require", "pack output " + out)
    bfp = out in ("bfp8", "bfp4")
    if bfp and n not in (128, 256, 512, 1024):
      g.fail("pack.shape", "unsupported BFP count")
    exp_words = (n + 255) // 256 if bfp else 0
    rmw(g, cfg.THCON_SEC0_REG1_Exp_section_size(exp_words))
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
  a = g.imm("addi", g.imm("srli", p, 4), -1)
  # SETDMAREG writes one 16-bit half of a GPR, its immediate split across the two Payload fields.
  gpr = hw.GPR_PACK_L1_ADDRESS
  low = g.zext16(a)
  g.mem("sw", hw.INSTRN_BUF, g.calc("or", g.li(isa.tensix("SETDMAREG", RegIndex16b=2 * gpr)), g.imm("slli", low, 8)))
  runtime_word(g, "SETDMAREG", dict(Payload_SigSelSize=2, RegIndex16b=2 * gpr + 1), "Payload_SigSel", g.imm("srli", a, 16))
  g.tt("STALLWAIT", isa.Stall.CFG, isa.Wait.THCON | isa.Wait.PACK0)
  g.tt("WRCFG", gpr, 0, cfg.THCON_SEC0_REG1_L1_Dest_addr.word)


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
  rmw(g, cfg.THCON_SEC0_REG1_Pack_L1_Acc("acc" in d))
  pack_address(g, p)
  g.tt("SETADC", 4, 0, 3, 0)
  g.tt("SETADCXY", 4, 0, 0, 0, 0, 11)
  g.tt("SETADCZW", 4, 0, 0, 0, 0, 15)
  slots = g.imm("srli", g.imm("andi", p, 15), 1 if t == "bf16*" else 2)
  aligned = object()
  g.branch("beq", slots, 0, aligned)
  runtime_word(g, "SETADCXX", dict(CntSetMask=4), "x_end2", g.imm("addi", slots, -1))
  g.tt("PACR", ReadIntfSel=1, ZeroWrite=1)
  g.tt("STALLWAIT", isa.Stall.TDMA, isa.Wait.PACK0)
  g.mark(aligned)
  remaining = g.alloc()
  row_reg = g.alloc()
  g.mov(remaining, g.condition(n))
  g.mov(row_reg, g.condition(row_expr))
  stride = g.condition(step)
  col = g.condition(col_expr)
  # Both X endpoints select the same column.
  x = g.calc("or", col, g.imm("slli", col, 10))
  g.mem("sw", hw.INSTRN_BUF, g.calc("or", x, g.li(isa.tensix("SETADCXX", 4))))
  loop, final = object(), object()
  g.mark(loop)
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
    rmw(g, cfg.THCON_SEC0_REG1_Pack_L1_Acc(0))


def unpack(g, s, d, i):
  u = hw.UNPACKER[i]
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
    rmw(g, u.force_shared_exp("shared_exp" in d))
    if "shared_exp" in d:
      rmw(g, u.shared_exp(number(d["shared_exp"], 0, 255)))
    fmt = FMT[out]
    one_byte = (hw.DataFormat.BFP8_B, hw.DataFormat.BFP4_B, hw.DataFormat.LF8)
    size = 1 if fmt in one_byte else 2  # bytes per datum in the Src register
    rmw(g, u.in_data_format(FMT[src]))
    rmw(g, u.y_dim(1))
    rmw(g, u.out_data_format(fmt))
    rmw(g, u.throttle_mode(2))
    rmw(g, u.haloize_mode("transpose" in d))
    rmw(g, *(f(1) for f in u.disable_zero_compress[:4]))
    rmw(g, *(f(1) for f in u.disable_zero_compress[4:]))
    rmw(g, u.lf8_e4m3(src == "e4m3"))
    rmw(g, u.row_stride(16 * size))
    rmw(g, u.face_stride(256 * size))
    rmw(g, u.alu_format(fmt))
    rmw(g, u.ovrd_data_format(1))
    for in_format, out_format in zip(u.context_in_format, u.context_out_format):
      rmw(g, in_format(FMT[src]), out_format(fmt))
    if not i:
      rmw(g, cfg.UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr(1))
      setc16(g, cfg.SRCA_SET_SetOvrdWithAddr(1))
  elif s.name in ("shape", "face", "base"):
    ctx = number(d.get("ctx", Num(0)), 0, 1 if i else 7)
    if s.name == "face":
      g.tt("UNPACR", Unpack_block_selection=i, AddrMode=0x11 if "next_tile_face" in d else int("next_l1_face" in d),
           CfgContextId=ctx, OvrdThreadId=1, SetDatValid=int("dvalid" in d), Last=1)
    elif s.name == "shape":
      x = number(required(d, "n", s), 1, 1024)
      faces = number(required(d, "faces", s), 1, 4)
      unpack_shape(g, i, ctx, x, faces)
      g.tt("SETADCXX", selector, x - 1, 0)
    else:
      p, t = g.expr(required(d, "p", s))
      if not t.endswith("*"):
        g.fail("unpack.pointer", t)
      g.check_pointer(d["p"], 16)
      unpack_base(g, i, ctx, p)
  elif s.name == "ctx":
    if "count" in d:
      count = number(d["count"], 1, len(u.context_in_format))
      rmw(g, u.context_count(count - 1), u.context_count_en(1))
    if "reset" in d:
      setc16(g, u.context_reset(1))
      g.tt("UNPACR_NOP", i, 0, 0, 0, 0, 0, 0, 0, 2)
      setc16(g, u.context_reset(0))
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
    wait_unpack_credit(g)
    unpack_shape(g, i, ctx, x, faces)
    unpack_base(g, i, ctx, p)
    g.mem("sw", UNPACK_CREDIT, hw.SEM_POST)
    g.tt("SETADCXX", selector, x - 1, 0)
    g.tt("SETADCZW", selector, 0, 0, 0, 0, 15)
    g.tt("STALLWAIT", isa.Stall.UNPACK, isa.Wait.TRISC_CFG | (isa.Wait.SRCB_CLR if i else isa.Wait.SRCA_CLR))
    for j in range(faces):
      g.tt("UNPACR", i, 0x11 if bfp else 0, 0, ctx, 0, 1, int("dvalid" in d and j + 1 == faces), 0, 0, 0, 0, 0, 1)
    g.tt("STALLWAIT", isa.Stall.SYNC, isa.Wait.UNPACK1 if i else isa.Wait.UNPACK0)
    g.tt("SEMGET", UNPACK_SYNC)


def unpack_dest(g, s):
  """Synchronously move a full FP32 tile directly into Dst. The caller owns the destination until packed."""
  d = bind(s, "p dst")
  ptr, ty = g.expr(required(d, "p", s))
  tile_row = number(row(required(d, "dst", s)), 0, 448)
  if ty not in ("fp32*", "u32*") or tile_row % 64:
    g.fail("unpack.dest", "expected a 32-bit L1 tile and tile-aligned FP32 Dst")
  g.check_pointer(d["p"], 16, 4096)
  u = hw.UNPACKER[0]
  fp = FMT["fp32"]
  g.drain()
  rmw(g, u.in_data_format(fp), u.y_dim(1))
  rmw(g, u.out_data_format(fp), u.throttle_mode(2), u.haloize_mode(0))
  rmw(g, *(f(1) for f in u.disable_zero_compress[:4]))
  rmw(g, *(f(1) for f in u.disable_zero_compress[4:]))
  rmw(g, u.context_in_format[0](fp), u.context_out_format[0](fp))
  rmw(g, u.ovrd_data_format(1))
  rmw(g, u.row_stride(64))
  rmw(g, u.face_stride(1024))
  rmw(g, cfg.UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr(1))
  unpack_shape(g, 0, 0, 256, 4)
  rmw(g, u.dest_address[0](64 + tile_row * 16))
  rmw(g, cfg.THCON_SEC0_REG2_Unpack_if_sel_cntx0(1))
  setc16(g, cfg.SRCA_SET_SetOvrdWithAddr(0))
  unpack_base(g, 0, 0, ptr)
  g.tt("SETADCXX", 1, 255, 0)
  g.tt("SETADCZW", 1, 0, 0, 0, 0, 15)
  g.tt("STALLWAIT", isa.Stall.UNPACK, isa.Wait.TRISC_CFG)
  for _ in range(4): g.tt("UNPACR", 0, 0x11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1)
  g.drain()
  rmw(g, cfg.THCON_SEC0_REG2_Unpack_if_sel_cntx0(0))
  rmw(g, u.dest_address[0](64))
  setc16(g, cfg.SRCA_SET_SetOvrdWithAddr(1))


def wait_unpack_credit(g):
  retry = object()
  g.mark(retry)
  g.branch("bne", g.mem("lw", UNPACK_CREDIT), 0, retry)


def unpack_shape(g, i, ctx, x, faces):
  u = hw.UNPACKER[i]
  rmw(g, u.z_dim(faces))
  rmw(g, u.x_dim(x))
  if not i:  # TTRV sets the per-context overrides on unpacker A only
    rmw(g, u.dest_address[ctx % 4](64))
    rmw(g, u.tile_x_dim[ctx % 4](x))


def unpack_base(g, i, ctx, pointer):
  """Store the base by MMIO, then read it back and consume the value so the write lands before the next UNPACR."""
  addr = hw.TENSIX_CFG + 4 * hw.UNPACKER[i].base_address[ctx].word
  g.mem("sw", addr, g.imm("addi", g.imm("srli", pointer, 4), -1))
  g.imm("andi", g.mem("lw", addr), 0)
