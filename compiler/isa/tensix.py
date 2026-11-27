import struct
from dataclasses import dataclass
from hw import isa as hw_isa
from hw.sfpu_lat import disasm_sfpu, sfpu_hazards
from ..dtype import DType, dtypes
from ..uop import CallInfo, Ops, UOp, line_rewrite
from . import ISARenderer, compile_linear, rdef, regalloc
from .rv32 import DEFAULT_SCRATCH, DEFAULT_WGPR, LOCAL_BASE, RV_PHYSICAL_REGS, RVGroupOp, RVOps, RV32Renderer, encode_rv32, relax_branches

# ---- Blackhole Tensix Opcodes & Blackhole-specific GroupOps ----

TensixOps = hw_isa.TensixOp
O = TensixOps

class TensixGroupOp:
  Control = frozenset({O.MOP, O.MOP_CFG, O.REPLAY, O.NOP, O.STALLWAIT, O.SEMINIT, O.SEMPOST, O.SEMGET, O.SEMWAIT})
  Sync = frozenset({O.STALLWAIT, O.SEMINIT, O.SEMPOST, O.SEMGET, O.SEMWAIT})
  Config = frozenset({O.SETC16, O.WRCFG, O.RDCFG, O.RMWCIB0, O.RMWCIB1, O.RMWCIB2, O.RMWCIB3, O.CFGSHIFTMASK})
  ScalarUnit = frozenset({
    O.SETDMAREG, O.ADDDMAREG, O.SUBDMAREG, O.MULDMAREG, O.SHIFTDMAREG,
    O.LOADIND, O.STOREIND, O.LOADREG, O.STOREREG,
  })
  Adc = frozenset({O.SETADC, O.SETADCXX, O.SETADCXY, O.INCADCXY, O.ADDRCRXY, O.SETADCZW, O.INCADCZW, O.ADDRCRZW})
  Rwc = frozenset({O.SETRWC, O.INCRWC, O.CLEARDVALID})
  Unpack = frozenset({O.UNPACR, O.UNPACR_NOP})
  Pack = frozenset({O.PACR})
  Mover = frozenset({O.XMOV})
  FPU = frozenset({
    O.MVMUL, O.ELWADD, O.ELWSUB, O.ELWMUL, O.GMPOOL, O.GAPOOL,
    O.MOVA2D, O.MOVB2D, O.MOVD2A, O.MOVD2B, O.MOVB2A, O.TRNSPSRCB, O.ZEROACC, O.ZEROSRC,
  })
  SFPU = frozenset({
    O.SFPLOAD, O.SFPLOADI, O.SFPSTORE, O.SFPLUT, O.SFPMULI, O.SFPADDI, O.SFPDIVP2, O.SFPEXEXP, O.SFPEXMAN,
    O.SFPIADD, O.SFPSHFT, O.SFPSETCC, O.SFPMOV, O.SFPABS, O.SFPAND, O.SFPOR, O.SFPNOT, O.SFPLZ,
    O.SFPSETEXP, O.SFPSETMAN, O.SFPMAD, O.SFPADD, O.SFPMUL, O.SFPPUSHC, O.SFPPOPC, O.SFPSETSGN,
    O.SFPENCC, O.SFPCOMPC, O.SFPTRANSP, O.SFPXOR, O.SFP_STOCH_RND, O.SFPNOP, O.SFPCAST, O.SFPCONFIG,
    O.SFPSWAP, O.SFPLOADMACRO, O.SFPSHFT2, O.SFPLUTFP32, O.SFPLE, O.SFPGT, O.SFPMUL24, O.SFPARECIP,
  })
  SFPU_Mad = frozenset({O.SFPMAD, O.SFPADD, O.SFPMUL, O.SFPMUL24})
  SFPU_TwoInPlace = frozenset({O.SFPSWAP})
  SFPU_CC = frozenset({O.SFPSETCC, O.SFPPUSHC, O.SFPPOPC, O.SFPCOMPC, O.SFPENCC, O.SFPGT, O.SFPLE})
  SFPU_Mem = frozenset({O.SFPLOAD, O.SFPSTORE, O.SFPLOADMACRO})
  SFPU_NoRegWrite = frozenset({O.SFPSTORE, O.SFPNOP, O.SFPSETCC, O.SFPPUSHC, O.SFPPOPC, O.SFPCOMPC, O.SFPENCC, O.SFPCONFIG})

  # Per-TRISC instruction ownership
  Trisc0 = Unpack | Adc | Config | ScalarUnit | Control | Mover
  Trisc1 = FPU | SFPU | Rwc | Config | ScalarUnit | Control
  Trisc2 = Pack | Adc | Config | ScalarUnit | Control
  All = frozenset(TensixOps)

# ---- Physical Tensix SFPU registers (L0..L15) ----

LREGS_ALL = tuple(UOp.param(i, dtypes.fp32, name=f"l{i}", file="lreg") for i in range(16))
LREGS = LREGS_ALL[:8]
L0, L1, L2, L3, L4, L5, L6, L7 = LREGS
L_CONST_0_8373, L_ZERO, L_ONE, L_NEG_ONE = LREGS_ALL[8:12]
L_CFG0, L_CFG1, L_CFG2, L_LANE_X2 = LREGS_ALL[12:16]
LCONST = {0.0: L_ZERO, 1.0: L_ONE, -1.0: L_NEG_ONE}
TENSIX_PHYSICAL_REGS = frozenset(LREGS_ALL)

ROLES = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")

# ---- Tensix UOp.ins descriptors & builders ----

@dataclass(frozen=True)
class SfpSpec:
  """Register-allocated SFPU instruction descriptor carried in NativeInfo.code."""
  op: hw_isa.TensixOp
  mod: int = 0
  imm: int = 0
  fmt: int = 0
  addr_mod: int = 0
  addr: int = 0
  rounding: int = 0

  def __repr__(self) -> str:
    extra = [f"{k}={v}" for k, v in (("mod", self.mod), ("imm", self.imm), ("fmt", self.fmt),
                                     ("addr_mod", self.addr_mod), ("addr", self.addr)) if v]
    return f"{self.op.name}({', '.join(extra)})" if extra else self.op.name

def tt_ins(inst: hw_isa.Tensix, *deps: UOp, role: str = "") -> UOp:
  """Wrap any concrete hw.isa.Tensix instruction into a UOp.ins."""
  return UOp.ins(inst, deps, dtypes.void, role=role)

def sfp_ins(
  op: hw_isa.TensixOp,
  src: tuple[UOp, ...] = (),
  dtype: DType = dtypes.fp32,
  *dst_lregs: UOp,
  mod: int = 0,
  imm: int = 0,
  fmt: int = 0,
  addr_mod: int = 0,
  addr: int = 0,
  rounding: int = 0,
  role: str = "trisc1",
) -> UOp:
  """Build a register-level SFPU instruction as UOp.ins(SfpSpec(...), src, dtype, *dst_lregs)."""
  return UOp.ins(SfpSpec(op, mod, imm, fmt, addr_mod, addr, rounding), src, dtype, *dst_lregs, role=role)

def is_tensix_ins(u: UOp) -> bool:
  return u.is_ins and isinstance(u.ins_op, (hw_isa.Tensix, SfpSpec))

def tensix_op(u: UOp) -> hw_isa.TensixOp | None:
  if not u.is_ins: return None
  code = u.ins_op
  if isinstance(code, hw_isa.Tensix): return code.op
  if isinstance(code, SfpSpec): return code.op
  return None

# ---- Tensix encoding (UOp.ins -> 32-bit Tensix word & inline TRISC word) ----

_SFP_ALU_ENC = {
  O.SFPARECIP: hw_isa.SFPARECIP, O.SFPMOV: hw_isa.SFPMOV, O.SFPABS: hw_isa.SFPABS,
  O.SFPAND: hw_isa.SFPAND, O.SFPOR: hw_isa.SFPOR, O.SFPXOR: hw_isa.SFPXOR, O.SFPNOT: hw_isa.SFPNOT,
  O.SFPLZ: hw_isa.SFPLZ, O.SFPSHFT: hw_isa.SFPSHFT, O.SFPSHFT2: hw_isa.SFPSHFT2, O.SFPIADD: hw_isa.SFPIADD,
  O.SFPEXEXP: hw_isa.SFPEXEXP, O.SFPEXMAN: hw_isa.SFPEXMAN, O.SFPDIVP2: hw_isa.SFPDIVP2,
  O.SFPSETEXP: hw_isa.SFPSETEXP, O.SFPSETMAN: hw_isa.SFPSETMAN, O.SFPSETSGN: hw_isa.SFPSETSGN,
  O.SFPSWAP: hw_isa.SFPSWAP, O.SFPTRANSP: hw_isa.SFPTRANSP, O.SFPENCC: hw_isa.SFPENCC,
  O.SFPSETCC: hw_isa.SFPSETCC, O.SFPGT: hw_isa.SFPGT, O.SFPLE: hw_isa.SFPLE,
  O.SFPPUSHC: hw_isa.SFPPUSHC, O.SFPPOPC: hw_isa.SFPPOPC, O.SFPCOMPC: hw_isa.SFPCOMPC,
}

def _lreg_num(u: UOp, ren: ISARenderer | None = None) -> int:
  if ren is not None:
    r = rdef(u, ren)
    if r is not None and r.arg.file == "lreg": return int(r.arg.slot)
  if u.op is Ops.PARAM and u.arg.file == "lreg" and u.arg.slot >= 0: return int(u.arg.slot)
  if u.is_ins and u.body.src:
    s = u.body.src[0]
    p = s.src[0] if s.op is Ops.AFTER else s
    if p.op is Ops.PARAM and p.arg.file == "lreg" and p.arg.slot >= 0: return int(p.arg.slot)
  raise RuntimeError(f"expected physical SFPU LReg, got {u.op.name} ({u.arg})")

def encode_tensix(u: UOp, ren: ISARenderer | None = None) -> int:
  """Encode a Tensix UOp.ins into an unrotated 32-bit Tensix instruction word."""
  code = u.ins_op
  if isinstance(code, hw_isa.Tensix): return int(code)
  if not isinstance(code, SfpSpec): raise RuntimeError(f"not a Tensix instruction UOp: {code!r}")
  op, src = code.op, u.src_without_body
  if op is O.SFPNOP: return int(hw_isa.SFPNOP())
  if op is O.SFPLOAD: return int(hw_isa.SFPLOAD(lreg=_lreg_num(u, ren), format=code.fmt, addr_mod=code.addr_mod, addr=code.addr))
  if op is O.SFPSTORE: return int(hw_isa.SFPSTORE(lreg=_lreg_num(src[0], ren), format=code.fmt, addr_mod=code.addr_mod, addr=code.addr))
  if op is O.SFPLOADI: return int(hw_isa.SFPLOADI(lreg=_lreg_num(u, ren), mode=code.mod, imm=code.imm))
  if op is O.SFPADDI: return int(hw_isa.SFPADDI(imm=code.imm, dest=_lreg_num(u, ren), mode=code.mod))
  if op is O.SFPMULI: return int(hw_isa.SFPMULI(imm=code.imm, dest=_lreg_num(u, ren), mode=code.mod))
  if op is O.SFPCAST: return int(hw_isa.SFPCAST(src=_lreg_num(src[0], ren), dest=_lreg_num(u, ren), mode=code.mod))
  if op is O.SFP_STOCH_RND:
    return int(hw_isa.SFP_STOCH_RND(src=_lreg_num(src[0], ren), b=9, dest=_lreg_num(u, ren),
                                   mode=code.mod, rounding=code.rounding, imm=code.imm))
  if op in (O.SFPMAD, O.SFPADD, O.SFPMUL, O.SFPMUL24):
    fn = {O.SFPMAD: hw_isa.SFPMAD, O.SFPADD: hw_isa.SFPADD, O.SFPMUL: hw_isa.SFPMUL, O.SFPMUL24: hw_isa.SFPMUL24}[op]
    a = _lreg_num(src[0], ren) if len(src) > 0 else 0
    b = _lreg_num(src[1], ren) if len(src) > 1 else 0
    c = _lreg_num(src[2], ren) if len(src) > 2 else 0
    return int(fn(a=a, b=b, c=c, dest=_lreg_num(u, ren), mode=code.mod))
  if op in _SFP_ALU_ENC:
    s0 = _lreg_num(src[0], ren) if src else 0
    dst = _lreg_num(src[1], ren) if (op in TensixGroupOp.SFPU_NoRegWrite and len(src) > 1) else (
      0 if op in TensixGroupOp.SFPU_NoRegWrite else _lreg_num(u, ren))
    return int(_SFP_ALU_ENC[op](imm=code.imm, src=s0, dest=dst, mode=code.mod))
  raise RuntimeError(f"unsupported SfpSpec op {op}")

def encode_tensix_inline(u: UOp, ren: ISARenderer | None = None) -> int:
  return hw_isa.inline(encode_tensix(u, ren))

# ---- SFPU hazard fixing directly on list[UOp] ----

def fix_sfpu_hazards_uops(lst: list[UOp], ren: ISARenderer | None = None, is_loop: bool = False) -> list[UOp]:
  """Insert tt_ins(SFPNOP()) between consecutive SFPU UOp.ins nodes with undetected RAW hazards."""
  out: list[UOp] = []
  run: list[UOp] = []

  def flush(loop_flag: bool):
    if not run: return
    words = [encode_tensix(u, ren) for u in run]
    cur_uops = list(run)
    for _ in range(len(words) + 4):
      hz = sfpu_hazards(words)
      if not hz and loop_flag and len(words) > 0:
        wrap_hz = sfpu_hazards(words + words[:4])
        if any(pos >= len(words) for pos, _ in wrap_hz):
          nop_u = tt_ins(hw_isa.SFPNOP(), role=cur_uops[0].arg.role if hasattr(cur_uops[0].arg, "role") else "trisc1")
          words.append(int(hw_isa.SFPNOP()))
          cur_uops.append(nop_u)
          continue
      if not hz: break
      pos, _ = hz[0]
      nop_u = tt_ins(hw_isa.SFPNOP(), role=cur_uops[0].arg.role if hasattr(cur_uops[0].arg, "role") else "trisc1")
      words.insert(pos, int(hw_isa.SFPNOP()))
      cur_uops.insert(pos, nop_u)
    out.extend(cur_uops)
    run.clear()

  for u in lst:
    if (op := tensix_op(u)) is not None and op in TensixGroupOp.SFPU:
      run.append(u)
    else:
      flush(False)
      out.append(u)
  flush(is_loop)
  return out

# ---- 5-core bundle packing / unpacking ----

_BUNDLE_MAGIC = b"BH01"

def pack_bundle(images: dict[str, bytes]) -> bytes:
  parts = [_BUNDLE_MAGIC, struct.pack("<I", len(images))]
  for role, data in images.items():
    rb = role.encode("utf-8")
    parts.append(struct.pack("<II", len(rb), len(data)))
    parts.append(rb)
    parts.append(data)
  return b"".join(parts)

def unpack_bundle(blob: bytes) -> dict[str, bytes]:
  if blob[:4] != _BUNDLE_MAGIC: raise ValueError(f"bad Blackhole bundle magic {blob[:4]!r}")
  (count,) = struct.unpack_from("<I", blob, 4)
  off = 8
  out: dict[str, bytes] = {}
  for _ in range(count):
    rlen, dlen = struct.unpack_from("<II", blob, off)
    off += 8
    role = blob[off:off + rlen].decode("utf-8")
    off += rlen
    out[role] = blob[off:off + dlen]
    off += dlen
  return out

def split_roles(uops: list[UOp], roles: tuple[str, ...] = ROLES) -> UOp:
  """Project owned effects and their scalar dependencies, preserving enclosing loops.

  Cross-core value edges express synchronization, not local computation. Their
  producer must never be copied into the consumer's instruction stream.
  """
  stack: list[UOp] = []
  enclosing: list[tuple[UOp, ...]] = []
  ends: dict[UOp, UOp] = {}
  def owner(u: UOp) -> str:
    return u.arg.role if isinstance(u.arg, CallInfo) else ""
  for u in uops:
    if (role := owner(u)) and role not in roles: raise ValueError(f"unknown Blackhole core role {role!r}")
    if u.op is Ops.RANGE:
      enclosing.append(tuple(stack))
      stack.append(u)
    elif u.op is Ops.END:
      for r in u.src[1:]:
        if not stack or stack[-1] is not r: raise ValueError("non-nested RANGE/END in joint stream")
        ends[r] = u
        stack.pop()
      enclosing.append(tuple(stack))
    else:
      enclosing.append(tuple(stack))
  if stack: raise ValueError("unclosed RANGE in joint stream")

  buckets: dict[str, list[UOp]] = {}
  for role in roles:
    needed: set[UOp] = set()
    pending = [node for i, u in enumerate(uops) if owner(u) == role for node in (u, *enclosing[i])]
    while pending:
      u = pending.pop()
      if u in needed or (owner(u) and owner(u) != role): continue
      needed.add(u)
      pending.extend(u.src_without_body)
      if u.op is Ops.RANGE and u in ends:
        # END's effect operand can belong to another core. Keep the marker,
        # but do not follow that operand and import unrelated computation.
        needed.add(ends[u])
    buckets[role] = [u for u in uops if u in needed]
  return UOp.linear(*(UOp.linear(*buckets[r], arg=r) for r in roles), arg="blackhole")

# ---- BlackholeRenderer (RV32IM + inline Tensix + 5-core Ops.LINEAR -> Ops.BINARY) ----

class BlackholeRenderer(RV32Renderer):
  physical_regs = RV_PHYSICAL_REGS | TENSIX_PHYSICAL_REGS

  def __init__(self, wgpr: tuple[UOp, ...] = DEFAULT_WGPR, scratch_regs: tuple[UOp, ...] = DEFAULT_SCRATCH,
               spill_base: UOp = LOCAL_BASE, spill_offset: int = 0):
    super().__init__(wgpr=wgpr, scratch_regs=scratch_regs, spill_base=spill_base, spill_offset=spill_offset)

  def assemble(self, uops: list[UOp]) -> bytes:
    """Encode a mixed RV32IM + inline Tensix list[UOp] into little-endian 32-bit machine code."""
    uops = relax_branches(uops, self)
    targets: dict[UOp, int] = {}
    pc = 0
    for u in uops:
      if not u.is_ins: continue
      if self.is_label(u): targets[u.src_without_body[0]] = pc
      else: pc += 4
    words: list[int] = []
    pc = 0
    for u in uops:
      if not u.is_ins or self.is_label(u): continue
      if is_tensix_ins(u): words.append(encode_tensix_inline(u, self))
      else: words.append(encode_rv32(u, self, targets, pc))
      pc += 4
    return struct.pack(f"<{len(words)}I", *words)

  def disasm(self, uops: list[UOp]) -> str:
    """Format a .lst-style listing of a mixed RV32IM + inline Tensix instruction stream."""
    uops = relax_branches(uops, self)
    targets: dict[UOp, int] = {}
    pc = 0
    for u in uops:
      if not u.is_ins: continue
      if self.is_label(u): targets[u.src_without_body[0]] = pc
      else: pc += 4
    lines: list[str] = []
    pc = 0
    for u in uops:
      if not u.is_ins or self.is_label(u): continue
      if is_tensix_ins(u):
        raw = encode_tensix(u, self)
        inl = hw_isa.inline(raw)
        dec = hw_isa.decode(raw)
        lines.append(f"{pc:04x}  {inl:08x}  {dec!r}" if dec is not None else f"{pc:04x}  {inl:08x}  0x{raw:08x}")
      else:
        w = encode_rv32(u, self, targets, pc)
        lines.append(f"{pc:04x}  {w:08x}  {u.ins_op.name.lower()}")
      pc += 4
    return "\n".join(lines)

  def compile_core(self, uops: list[UOp], *, fix_sfpu: bool = True) -> tuple[list[UOp], bytes]:
    lin_ctx = self.linear_ctx_type(self)
    lst = line_rewrite(uops, self.pre_regalloc_matcher, lin_ctx)
    lst = regalloc(lin_ctx, lst, self)
    lst = lin_ctx.insert_linearized(lst)
    lst = line_rewrite(lst, self.post_regalloc_matcher, lin_ctx)
    if fix_sfpu: lst = fix_sfpu_hazards_uops(lst, self)
    return lst, self.assemble(lst)

  def compile_linear_bundle(self, lin: UOp) -> UOp:
    """Compile a 5-core nested Ops.LINEAR (or single Ops.LINEAR) into Ops.PROGRAM(lin, compiled, source, binary)."""
    if lin.op is not Ops.LINEAR: raise TypeError(f"expected Ops.LINEAR, got {lin.op.name}")
    if lin.src and all(s.op is Ops.LINEAR for s in lin.src):
      compiled_cores: list[UOp] = []
      images: dict[str, bytes] = {}
      listings: list[str] = []
      for i, core_lin in enumerate(lin.src):
        role = str(core_lin.arg or f"core{i}")
        lst, binary = self.compile_core(list(core_lin.src), fix_sfpu=(role == "trisc1"))
        compiled_cores.append(UOp.linear(*lst, arg=role))
        images[role] = binary
        listings.append(f"=== {role} ({len(binary)}B) ===\n{self.disasm(lst)}")
      out_lin = UOp.linear(*compiled_cores, arg=lin.arg)
      return UOp.program(lin, out_lin, UOp.source("\n".join(listings)), UOp.binary(pack_bundle(images)), arg=lin.arg)
    lst, binary = self.compile_core(list(lin.src))
    out_lin = UOp.linear(*lst, arg=lin.arg)
    return UOp.program(lin, out_lin, UOp.source(self.disasm(lst)), UOp.binary(binary), arg=lin.arg)
