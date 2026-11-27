"""Late SFPU selection: scalar UOps in LREG space -> register-level UOp.ins.

The caller supplies an already projected, ordered expression stream. This
module neither linearizes the tile graph nor allocates Dst tiles. Structured
footprint loops remain the responsibility of the enclosing recipe expansion.
"""
import math, struct

from hw import isa
from ..dtype import dtypes
from ..uop import Ops, UOp
from ..isa import IselContext, LinearContext, regalloc, regs
from ..isa.tensix import (BlackholeRenderer, LREGS, LREGS_ALL, SfpSpec, TensixOps as O,
                         fix_sfpu_hazards_uops, sfp_ins)
from .specs import SfpLoadOp, SfpStoreOp, SfpReduceLanes, SfpReduceRows, SfpBroadcastRows


def mad(a, b, c, *, neg_ab=False, neg_c=False):
  return UOp(Ops.MULACC, (a, b, c), (neg_ab, neg_c))


def horner(x, coeffs):
  result = UOp.const(coeffs[-1], dtypes.fp32)
  for c in reversed(coeffs[:-1]): result = mad(result, x, UOp.const(c, dtypes.fp32))
  return result


def decompose(u):
  x = u.src[0]
  one = UOp.const(1., dtypes.fp32)
  if u.op is Ops.DIV: return x * u.src[1].recip()
  if u.op is Ops.EXP2:
    # Preserve the validated magic-rounding polynomial from compiler/sfpu.py.
    xc = (x < -126.).where(-126., (x < 127.).where(x, 127.))
    rounded = xc + 12582912.
    fraction = xc - (rounded - 12582912.)
    exponent = ((rounded.bitcast(dtypes.i32) + 127) << 23).bitcast(dtypes.fp32)
    poly = horner(fraction, (1., .6931471824645996, .2402210682630539, .055503569543361664,
                            .009676031768321991, .0013390863314270973))
    return (x < -126.).where(0., exponent * poly)
  if u.op is Ops.SQRT:
    y = (UOp.const(0x5F1110A0, dtypes.u32) - (x.bitcast(dtypes.u32) >> 1)).bitcast(dtypes.fp32)
    t = -(x * y) * y
    y = y * mad(t, t + 2.2533049, UOp.const(2.2825186, dtypes.fp32))
    s = x * y
    return mad(mad(s, s, x, neg_ab=True), y * .5, s)
  if u.op is Ops.SIN:
    rounded = mad(x, UOp.const(1. / math.pi, dtypes.fp32), UOp.const(12582912., dtypes.fp32))
    n = rounded - 12582912.
    r = x
    for c in (3.1416015625, -8.907169103622437e-06, -1.741103261565513e-09):
      r = mad(n, UOp.const(c, dtypes.fp32), r, neg_ab=True)
    result = r * horner(r * r, (1., -.16666658222675323, .008333049714565277,
                                -.0001980901724891737, 2.6051077384181553e-06))
    return (result.bitcast(dtypes.u32) ^ (rounded.bitcast(dtypes.u32) << 31)).bitcast(dtypes.fp32)
  if u.op is Ops.LOG2:
    bits = x.bitcast(dtypes.u32)
    exponent = (((bits >> 23) & 255).cast(dtypes.i32) - 127).cast(dtypes.fp32)
    mantissa = ((bits & 0x7FFFFF) | 0x3F800000).bitcast(dtypes.fp32)
    t = (mantissa - one) * (mantissa + one).recip()
    return mad(t, horner(t * t, (2.885390043258667, .9618448615074158, .5733158588409424, .48057064414024353)), exponent)
  return None


class SpillCapacityError(RuntimeError): pass


class SfpuRenderer(BlackholeRenderer):
  """Use the shared allocator, with spills into explicitly reserved Dst rows."""
  def __init__(self, spill_row=448, end_row=512):
    super().__init__()
    self.scratch_regs = (LREGS[3], LREGS[6], LREGS[7])
    self.spill_row, self.end_row = spill_row, end_row

  def copy(self, x, reg): return sfp_ins(O.SFPMOV, (x,), x.dtype, reg)

  def spill(self, slot, x):
    row = self.spill_row + 2 * (slot // 4)
    if row + 6 > self.end_row - 2: raise SpillCapacityError("SFPU spill exceeds reserved Dst rows")
    return sfp_ins(O.SFPSTORE, (x,), dtypes.void, fmt=isa.SfpuFormat.INT32, addr=row)

  def fill(self, slot, x, reg):
    row = self.spill_row + 2 * (slot // 4)
    if row + 6 > self.end_row - 2: raise SpillCapacityError("SFPU fill exceeds reserved Dst rows")
    return sfp_ins(O.SFPLOAD, (), x.dtype, reg, fmt=isa.SfpuFormat.INT32, addr=row)


class Selector:
  def __init__(self):
    self.ctx = IselContext()
    self.out = []
    self.values = {}

  def emit(self, op, src=(), dtype=dtypes.fp32, *, dest=None, choices=LREGS, **kw):
    dst = () if dtype is dtypes.void else dest if dest is not None else self.ctx.vreg(dtype, choices)
    u = sfp_ins(op, src, dtype, *dst, **kw)
    self.out.append(u)
    return u

  def constant(self, u):
    val = u.val
    if u.dtype.is_float and val in (0., 1., -1.): return LREGS_ALL[{0.: 9, 1.: 10, -1.: 11}[val]]
    bits = struct.unpack('<I', struct.pack('<f', val))[0] if u.dtype.is_float else int(val) & 0xFFFFFFFF
    if bits == 0: return LREGS_ALL[9].bitcast(u.dtype)
    high = self.emit(O.SFPLOADI, dtype=u.dtype, mod=isa.LoadImm.FLOATB, imm=bits >> 16)
    if bits & 0xFFFF:
      return self.emit(O.SFPLOADI, (high,), u.dtype, dest=regs(high), mod=isa.LoadImm.LOWER, imm=bits & 0xFFFF)
    return high

  def destructive(self, op, source, initial, dtype, **kw):
    copy = self.emit(O.SFPMOV, (initial,), dtype)
    return self.emit(op, (source, copy), dtype, dest=regs(copy), **kw)

  def expand(self, root):
    for node in root.toposort(gate=lambda node: node not in self.values):
      if node not in self.values: self.values[node] = self.select(node)
    return self.values[root]

  def where(self, cond, yes, no, dtype):
    initial = self.emit(O.SFPMOV, (no,), dtype)
    self.emit(O.SFPENCC, dtype=dtypes.void, imm=1, mod=2)
    self.emit(O.SFPSETCC, (cond,), dtypes.void, mod=2)
    result = self.emit(O.SFPMOV, (yes, initial), dtype, dest=regs(initial))
    self.emit(O.SFPENCC, dtype=dtypes.void, mod=2)
    return result

  def float_to_int(self, value, dtype):
    # SFPSTOCHRND's integer modes saturate at 8 or 16 bits. Extract and
    # shift the IEEE significand instead, retaining the full 32-bit range.
    def integer(x): return self.constant(UOp.const(x, dtypes.i32))
    exponent = self.emit(O.SFPSHFT, (value,), dtypes.u32, imm=(-23) & 0xFFF, mod=5)
    exponent = self.destructive(O.SFPAND, integer(255), exponent, dtypes.i32)
    shift = self.destructive(O.SFPIADD, integer(-150), exponent, dtypes.i32, mod=4)
    mantissa = self.destructive(O.SFPAND, integer(0x7FFFFF), value, dtypes.u32)
    mantissa = self.destructive(O.SFPOR, integer(0x800000), mantissa, dtypes.u32)
    magnitude = self.destructive(O.SFPSHFT, shift, mantissa, dtype, mod=0)
    absolute = self.destructive(O.SFPAND, integer(0x7FFFFFFF), value, dtypes.fp32)
    small = self.destructive(O.SFPGT, absolute, LREGS_ALL[10], dtypes.bool, mod=8)
    magnitude = self.where(small, LREGS_ALL[9], magnitude, dtype)
    negative = self.destructive(O.SFPGT, value, LREGS_ALL[9], dtypes.bool, mod=8)
    negated = self.destructive(O.SFPIADD, LREGS_ALL[9], magnitude, dtype, mod=6)
    return self.where(negative, negated, magnitude, dtype)

  def reduce_lanes(self, value, op, rows_only=False):
    def combine(a, b):
      if op == "add": return self.emit(O.SFPADD, (LREGS_ALL[10], a, b))
      if op == "max":
        cond = self.destructive(O.SFPGT, a, b, dtypes.bool, mod=8)
        return self.where(cond, b, a, dtypes.fp32)
      raise ValueError(f"unsupported lane reduction {op}")
    for shift in (4, 2, 1):
      rotated = self.emit(O.SFPMOV, (value,))
      for _ in range(shift): rotated = self.emit(O.SFPSHFT2, (rotated,), dest=regs(rotated), mod=3)
      value = combine(value, rotated)
    if rows_only: return value
    copies = [self.emit(O.SFPMOV, (value,), dest=(reg,)) for reg in LREGS[:4]]
    # TRANSP writes the complete physical register bank, not just VD. Declare
    # every clobber so unrelated live vectors cannot be colored into it.
    self.emit(O.SFPTRANSP, tuple(copies), dest=LREGS)
    return combine(combine(LREGS[0], LREGS[1]), combine(LREGS[2], LREGS[3]))

  def select(self, u):
    if u.is_const: return self.constant(u)
    if u in LREGS_ALL: return u
    src = tuple(self.values.get(s, s) for s in u.src_without_body)
    if u.op is Ops.AFTER: return src[0]
    if u.op in (Ops.NOOP, Ops.SINK): return u
    if u.op in (Ops.EXP2, Ops.SQRT, Ops.SIN, Ops.DIV, Ops.LOG2): return self.expand(decompose(u))
    if u.is_ins:
      spec = u.ins_op
      if isinstance(spec, SfpLoadOp):
        row = spec.dst_slot * 8 + spec.sub_row
        return self.emit(O.SFPLOAD, dtype=u.dtype, addr=row,
                         fmt=isa.SfpuFormat.FP32 if spec.fmt == "fp32" else isa.SfpuFormat.INT32,
                         choices=LREGS[4:8] if row & 1 else LREGS[:4])
      if isinstance(spec, SfpStoreOp):
        return self.emit(O.SFPSTORE, src, dtypes.void, addr=spec.dst_slot * 8 + spec.sub_row,
                         fmt=isa.SfpuFormat.FP32 if spec.fmt == "fp32" else isa.SfpuFormat.INT32)
      if isinstance(spec, SfpReduceLanes): return self.reduce_lanes(src[0], spec.op)
      if isinstance(spec, SfpReduceRows): return self.reduce_lanes(src[0], spec.op, rows_only=True)
      if isinstance(spec, SfpBroadcastRows):
        copies = [self.emit(O.SFPMOV, src, dest=(reg,)) for reg in LREGS[:4]]
        self.emit(O.SFPTRANSP, tuple(copies), dest=LREGS)
        return self.emit(O.SFPMOV, (LREGS[0],))
      if isinstance(spec, SfpSpec):
        raise ValueError("SFPU selection expects abstract inputs, not previously selected instructions")
    if u.op is Ops.BITCAST: return src[0].bitcast(u.dtype)
    if u.op is Ops.CAST and u.dtype == u.src[0].dtype: return src[0]
    if u.op is Ops.CAST:
      old = u.src[0].dtype
      if old.is_int and u.dtype.is_int: return src[0].bitcast(u.dtype)
      if old.is_int and u.dtype.is_float:
        sm = self.emit(O.SFPCAST, src, dtypes.i32, mod=3)
        return self.emit(O.SFPCAST, (sm,), u.dtype)
      if old is dtypes.fp32 and u.dtype is dtypes.bf16:
        return self.emit(O.SFP_STOCH_RND, src, u.dtype, mod=1)
      if old is dtypes.bf16 and u.dtype is dtypes.fp32: return src[0].bitcast(u.dtype)
      if old.is_float and u.dtype.is_int:
        return self.float_to_int(src[0], u.dtype)
    if u.op is Ops.WHERE: return self.where(*src, u.dtype)
    if u.op is Ops.CMPLT and u.src[0].dtype.is_float:
      return self.destructive(O.SFPGT, src[0], src[1], dtypes.bool, mod=8)
    if u.op in (Ops.CMPEQ, Ops.CMPNE) and u.src[0].dtype.is_float:
      diff = self.emit(O.SFPADD, (LREGS_ALL[10], *src), dtypes.fp32, mod=2)
      initial = self.emit(O.SFPMOV, (LREGS_ALL[9],), dtypes.bool)
      self.emit(O.SFPENCC, dtype=dtypes.void, imm=1, mod=2)
      self.emit(O.SFPSETCC, (diff,), dtypes.void, mod=6 if u.op is Ops.CMPEQ else 2)
      result = self.emit(O.SFPLOADI, (initial,), dtypes.bool, dest=regs(initial), mod=isa.LoadImm.SHORT, imm=0xFFFF)
      self.emit(O.SFPENCC, dtype=dtypes.void, mod=2)
      return result
    if u.op is Ops.MAX and u.dtype.is_float:
      return self.expand((u.src[0] < u.src[1]).where(u.src[1], u.src[0]))
    if u.op in (Ops.ADD, Ops.SUB, Ops.MUL) and u.dtype.is_float:
      a, b = src
      if u.op is Ops.MUL: return self.emit(O.SFPMUL, (a, b, LREGS_ALL[9]), u.dtype)
      return self.emit(O.SFPADD, (LREGS_ALL[10], a, b), u.dtype, mod=2 if u.op is Ops.SUB else 0)
    if u.op is Ops.MULACC:
      neg_ab, neg_c = u.arg if isinstance(u.arg, tuple) else (False, False)
      return self.emit(O.SFPMAD, src, u.dtype, mod=int(neg_ab) | (int(neg_c) << 1))
    if u.op is Ops.NEG and u.dtype.is_float: return self.emit(O.SFPMOV, src, u.dtype, mod=1)
    if u.op in (Ops.ADD, Ops.SUB) and u.dtype.is_int:
      return self.destructive(O.SFPIADD, src[0], src[1], u.dtype, mod=4 if u.op is Ops.ADD else 6)
    if u.op in (Ops.SHL, Ops.SHR) and u.src[1].is_const:
      amount = int(u.src[1].val) * (1 if u.op is Ops.SHL else -1)
      return self.emit(O.SFPSHFT, (src[0],), u.dtype, imm=amount & 0xFFF,
                       mod=7 if u.op is Ops.SHR and u.dtype.is_signed else 5)
    if u.op in (Ops.XOR, Ops.AND, Ops.OR):
      return self.destructive({Ops.XOR: O.SFPXOR, Ops.AND: O.SFPAND, Ops.OR: O.SFPOR}[u.op],
                              src[1], src[0], u.dtype)
    if u.op is Ops.RECIP:
      y = self.emit(O.SFPARECIP, src, u.dtype)
      # Three Newton steps reduce the measured seed error (<0.0056) below
      # fp32 rounding error; no change to the input's exponent representation.
      for _ in range(3):
        error = self.emit(O.SFPMAD, (src[0], y, LREGS_ALL[10]), u.dtype, mod=1)
        y = self.emit(O.SFPMAD, (error, y, y), u.dtype)
      return y
    raise NotImplementedError(f"SFPU selection for {u.op.name}: {u.arg!r}")

  def lower(self, stream):
    for u in stream:
      self.values[u] = self.select(u)
    return self.out


def select_sfpu(stream: list[UOp], *, spill_row=448, end_row=512) -> list[UOp]:
  ren = SfpuRenderer(spill_row, end_row)
  selected = Selector().lower(stream)
  allocated = regalloc(LinearContext(ren), selected, ren)
  return fix_sfpu_hazards_uops(allocated, ren, is_loop=True)
