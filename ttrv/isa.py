"""Instruction encodings: RV32IM + Zicsr, the RISC-V extensions the Blackhole baby cores implement, and the Blackhole
Tensix ISA. RISC-V by mnemonic through rv()/v(); Tensix one function per instruction.

  from ttrv import isa
  isa.rv('addi', 5, 0, imm=1)                  # addi x5, x0, 1  -> 32-bit word
  isa.rv('sw', rs1=6, rs2=5, imm=8)            # sw x5, 8(x6)
  isa.rv('sh2add', 5, 6, 7)                    # x5 = x7 + (x6 << 2)                     (Zba, every core)
  isa.rv('fadd.s', 1, 2, 3)                    # f1 = f2 + f3                            (F, every core)
  isa.v('vsetvli', 5, 6, isa.vtype(32, 8))     # vsetvli x5, x6, e32, m8, tu, mu         (V, TRISC2 only)
  isa.v('vadd.vv', 1, 2, 3, masked=True)       # vadd.vv v1, v2, v3, v0.t
  isa.ELWMUL(dest_accum_en=1, dst=64)          # Tensix word, unrotated; hover for what each field means
  isa.inline(isa.SFPNOP())                     # as stored inline in a TRISC instruction stream (.ttinsn)
  isa.STALLWAIT(isa.Stall.CFG, isa.Wait.UNPACK0 | isa.Wait.MATH)

Registers are physical numbers and fields are raw values; nothing here knows about ttrv source. Encoders raise
ValueError when a value does not fit. rv_decode/tensix_decode invert them (None for anything else).

Sources, generated once: the Tensix layouts are tt-llk tt_llk_blackhole/common/inc/ckernel_ops.h (field names, shifts,
and widths from its _VALID macros). Titles, summaries and field meanings are from tt-ins-docs (72 of the 137
instructions are written up; the rest have the layout only). The value enums are from blackhole-py-old ttko. The
RISC-V extension encodings were checked against llvm-mc, and which core runs what against a p150 (see "RISC-V beyond
RV32IM" below).

Tensix words placed inline in a TRISC stream are rotated left by 2 (`.ttinsn`, see BabyRISCV/PushTensixInstruction.md
in tt-isa-documentation); words stored to INSTRN_BUF with sw and MOP_CFG words are not. Every Tensix opcode is below
0xC0, so an inline word never has its low two bits set and cannot be mistaken for an RV32 instruction."""
from enum import IntEnum

# ---- RV32IM ----

# name: (format, opcode, funct3, funct7). Formats UN/SYS/FU keep a full 12-bit bits[31:20] value in the funct7 slot,
# and R4 keeps its 2-bit fmt there.
RV = {
  "lui": ("U", 0x37, 0, 0), "auipc": ("U", 0x17, 0, 0), "jal": ("J", 0x6F, 0, 0), "jalr": ("I", 0x67, 0, 0),
  **{n: ("B", 0x63, f3, 0) for n, f3 in (("beq", 0), ("bne", 1), ("blt", 4), ("bge", 5), ("bltu", 6), ("bgeu", 7))},
  **{n: ("I", 0x03, f3, 0) for n, f3 in (("lb", 0), ("lh", 1), ("lw", 2), ("lbu", 4), ("lhu", 5))},
  **{n: ("S", 0x23, f3, 0) for n, f3 in (("sb", 0), ("sh", 1), ("sw", 2))},
  **{n: ("I", 0x13, f3, 0) for n, f3 in (("addi", 0), ("slti", 2), ("sltiu", 3), ("xori", 4), ("ori", 6), ("andi", 7))},
  **{n: ("SH", 0x13, f3, f7) for n, f3, f7 in (("slli", 1, 0), ("srli", 5, 0), ("srai", 5, 0x20))},
  **{n: ("R", 0x33, f3, f7) for n, f3, f7 in (("add", 0, 0), ("sub", 0, 0x20), ("sll", 1, 0), ("slt", 2, 0), ("sltu", 3, 0),
     ("xor", 4, 0), ("srl", 5, 0), ("sra", 5, 0x20), ("or", 6, 0), ("and", 7, 0), ("mul", 0, 1), ("mulh", 1, 1),
     ("mulhsu", 2, 1), ("mulhu", 3, 1), ("div", 4, 1), ("divu", 5, 1), ("rem", 6, 1), ("remu", 7, 1))},
  "fence": ("FENCE", 0x0F, 0, 0),
  **{n: ("CSR", 0x73, f3, 0) for n, f3 in (("csrrw", 1), ("csrrs", 2), ("csrrc", 3))},
  **{n: ("CSRI", 0x73, f3, 0) for n, f3 in (("csrrwi", 5), ("csrrsi", 6), ("csrrci", 7))},
}

# ---- RISC-V beyond RV32IM ----
#
# Which core runs what (tt-isa-documentation BlackholeA0/TensixTile/BabyRISCV/InstructionSet.md, and a probe on a
# p150a on 2026-11-14 that ran on every core and checked the results):
#   every core (BRISC, NCRISC, TRISC0-2)  Zba, Zbb, pack/brev8/grevi, Zaamo, the F and Zfh subsets, ebreak
#   BRISC and NCRISC only                 mret
#   TRISC2 only                           the V subset (RVV_* below). On the other cores vsetvli still returns a VL,
#                                         but the first vector load, ALU op or store hangs the core until tt-smi -r.
# Unimplemented encodings are UndefinedBehavior, not a trap, so the instructions the hardware lacks (fdiv, fsqrt,
# lr/sc, Zbs, vdiv, vfdiv, ...) are left out rather than encoded.
#
# None of these are used yet. They save an instruction here and there (zext.h for the 16-bit CB counter masks,
# sh1add for the DRAM bank table lookup), which is not enough to justify codegen for them.
RV |= {
  # Zba, every core: rd = rs2 + (rs1 << n), one-instruction array indexing. Probed: sh2add, sh3add.
  **{n: ("R", 0x33, f3, 0x10) for n, f3 in (("sh1add", 2), ("sh2add", 4), ("sh3add", 6))},
  # Zbb, every core. andn/orn/xnor: rs1 op ~rs2. min/max signed, minu/maxu unsigned. rol/ror rotate by rs2[4:0].
  # Probed: max, maxu, andn.
  **{n: ("R", 0x33, f3, f7) for n, f3, f7 in (("andn", 7, 0x20), ("orn", 6, 0x20), ("xnor", 4, 0x20),
     ("min", 4, 0x05), ("minu", 5, 0x05), ("max", 6, 0x05), ("maxu", 7, 0x05), ("rol", 1, 0x30), ("ror", 5, 0x30))},
  # Zbb unary: clz/ctz count leading/trailing zeros (32 for 0), cpop counts set bits, sext.b/sext.h/zext.h extend
  # the low byte/halfword, orc.b turns each nonzero byte into 0xFF, rev8 byte-swaps. Probed: clz, ctz, cpop, sext.b,
  # zext.h, rev8.
  **{n: ("UN", 0x13, 1, f12) for n, f12 in (("clz", 0x600), ("ctz", 0x601), ("cpop", 0x602), ("sext.b", 0x604),
     ("sext.h", 0x605))},
  **{n: ("UN", 0x13, 5, f12) for n, f12 in (("orc.b", 0x287), ("rev8", 0x698), ("brev8", 0x687))},
  "zext.h": ("UN", 0x33, 4, 0x080),                                            # pack rd, rs1, x0
  "rori": ("SH", 0x13, 5, 0x30),                                                # Zbb, probed
  # Beyond Zbb, every core. pack (Zbkb): rd = rs2[15:0] << 16 | rs1[15:0]. brev8 (Zbkb, above): reverse the bits in
  # each byte. grevi (Bitmanip 0.94 draft, not ratified, llvm-mc lacks it): generalized reverse, imm bit k swaps
  # adjacent 2^k-bit groups, so rev8 = grevi 24 and brev8 = grevi 7. Probed: pack, brev8.
  "pack": ("R", 0x33, 4, 0x04),
  "grevi": ("SH", 0x13, 5, 0x34),
  # Zaamo, every core: rd = mem[rs1]; mem[rs1] = mem[rs1] op rs2, atomically. Local L1 only, not MMIO and not other
  # tiles (use NoC atomics for those). The hardware ignores aq/rl and always runs them as aq+rl, so they are encoded
  # as 0. No lr.w/sc.w. Probed: amoadd.w, amoswap.w, amoor.w, amomaxu.w.
  **{n: ("R", 0x2F, 2, f7) for n, f7 in (("amoadd.w", 0x00), ("amoswap.w", 0x04), ("amoxor.w", 0x10),
     ("amoor.w", 0x20), ("amoand.w", 0x30), ("amomin.w", 0x40), ("amomax.w", 0x50), ("amominu.w", 0x60),
     ("amomaxu.w", 0x70))},
  # System. ebreak (every core) pauses the core for the debugger. mret (BRISC and NCRISC only) returns from an
  # interrupt handler. ecall is RV32I, but the docs do not say what it does here: nothing handles the trap.
  "ecall": ("SYS", 0x73, 0, 0x000), "ebreak": ("SYS", 0x73, 0, 0x001), "mret": ("SYS", 0x73, 0, 0x302),
}

# F (.s, fp32) and Zfh (.h), every core. These use their own register file, f0-f31; rd/rs1/rs2/rs3 below are f
# registers except where the name says x (fmv.x.*, fcvt.w*, fclass, feq/flt/fle write x; fmv.*.x, fcvt.*.w* read x).
#   - rm (rounding mode) is encoded but ignored: the hardware always rounds to nearest even. fcvt.w.s 3.75 with rtz
#     gives 4. fcsr exists; fflags and frm do not.
#   - fadd/fsub/fmul and the fused ops treat denormal inputs as zero and flush denormal results to zero (probed).
#   - fmadd/fmsub/fnmsub/fnmadd are not IEEE fused: rounding sits between separate mul+add and a true FMA
#     (Miscellaneous/FMA in tt-isa-documentation).
#   - No fdiv or fsqrt: they are UndefinedBehavior, so they are not encoded.
#   - Setting cfg0 (CSR 0x7C0) bit 30 makes the .h arithmetic BF16 instead of FP16 (bit 31: RTNE, else RTZ). In that
#     mode fcvt.s.h/fcvt.h.s still convert as FP16 (0x3FC0 -> 0x77C00000, probed), so convert bf16 <-> f32 with a
#     16-bit shift instead. The vector vfwcvt.f.f.v does follow the mode.
# Probed on every core: flw, fsw, fmv.x.w, fmv.w.x, fcvt.s.w, fcvt.w.s, fadd.s, fsub.s, fmul.s, fmadd.s, flt.s,
# fmax.s, fsgnjn.s, fclass.s, fmv.h.x, fmv.x.h, fadd.h (FP16 and BF16), fcvt.s.h, fcvt.h.s.
for _s, _fmt in ((".s", 0), (".h", 2)):
  RV |= {
    "flw" if _s == ".s" else "flh": ("I", 0x07, 2 if _s == ".s" else 1, 0),
    "fsw" if _s == ".s" else "fsh": ("S", 0x27, 2 if _s == ".s" else 1, 0),
    **{n + _s: ("FR", 0x53, 0, f5 << 2 | _fmt) for n, f5 in (("fadd", 0x00), ("fsub", 0x01), ("fmul", 0x02))},
    # sign injection: rd = |rs1| with sign rs2 / ~rs2 / rs1^rs2 (fmv.s, fneg.s, fabs.s are these with rs1 == rs2)
    **{n + _s: ("R", 0x53, f3, 0x10 | _fmt) for n, f3 in (("fsgnj", 0), ("fsgnjn", 1), ("fsgnjx", 2))},
    **{n + _s: ("R", 0x53, f3, 0x14 | _fmt) for n, f3 in (("fmin", 0), ("fmax", 1))},
    **{n + _s: ("R", 0x53, f3, 0x50 | _fmt) for n, f3 in (("feq", 2), ("flt", 1), ("fle", 0))},   # x rd = 0/1
    # fp -> int (x rd) and int (x rs1) -> fp; the u forms are unsigned
    **{f"fcvt.{i}{_s}": ("FU", 0x53, 0, (0x60 | _fmt) << 5 | k) for i, k in (("w", 0), ("wu", 1))},
    **{f"fcvt{_s}.{i}": ("FU", 0x53, 0, (0x68 | _fmt) << 5 | k) for i, k in (("w", 0), ("wu", 1))},
    "fmv.x.w" if _s == ".s" else "fmv.x.h": ("UN", 0x53, 0, (0x70 | _fmt) << 5),   # raw bits f -> x
    "fmv.w.x" if _s == ".s" else "fmv.h.x": ("UN", 0x53, 0, (0x78 | _fmt) << 5),   # raw bits x -> f
    "fclass" + _s: ("UN", 0x53, 1, (0x70 | _fmt) << 5),    # x rd = one-hot class: bit 0 -inf ... 6 +normal ... 9 qNaN
    **{n + _s: ("R4", op, 0, _fmt) for n, op in (("fmadd", 0x43), ("fmsub", 0x47), ("fnmsub", 0x4B), ("fnmadd", 0x4F))},
  }
RV |= {"fcvt.s.h": ("FU", 0x53, 0, 0x20 << 5 | 2), "fcvt.h.s": ("FU", 0x53, 0, 0x22 << 5 | 0)}

FORMAT_FIELDS = {"R": ("rd", "rs1", "rs2"), "I": ("rd", "rs1", "imm"), "SH": ("rd", "rs1", "imm"), "S": ("rs1", "rs2", "imm"),
                 "B": ("rs1", "rs2", "imm"), "U": ("rd", "imm"), "J": ("rd", "imm"), "FENCE": ("imm",),
                 "CSR": ("rd", "rs1", "imm"), "CSRI": ("rd", "rs1", "imm"),  # CSR*: imm = csr number; CSRI: rs1 = uimm5
                 "UN": ("rd", "rs1"), "SYS": (), "FR": ("rd", "rs1", "rs2", "rm"), "FU": ("rd", "rs1", "rm"),
                 "R4": ("rd", "rs1", "rs2", "rs3", "rm")}

def _signed(v, bits, align=1):
  if v % align or not -(1 << (bits - 1)) <= v < 1 << (bits - 1): raise ValueError(f"{v} does not fit signed {bits} bits")
  return v & ((1 << bits) - 1)
def _unsigned(v, bits):
  if not 0 <= v < 1 << bits: raise ValueError(f"{v} does not fit unsigned {bits} bits")
  return v
def _sext(v, bits): return v - (1 << bits) if v >> (bits - 1) & 1 else v

def rv(name: str, rd: int = 0, rs1: int = 0, rs2: int = 0, imm: int = 0, rs3: int = 0, rm: int = 0) -> int:
  """One RV32 instruction. U-format imm is the 20-bit upper value (as written in `lui rd, imm`). B/J imm is a byte offset.
  rm is the 3-bit FP rounding mode (0 = rne; the hardware ignores it)."""
  fmt, op, f3, f7 = RV[name]
  for r in (rd, rs1, rs2, rs3): _unsigned(r, 5)
  base = f3 << 12 | op
  match fmt:
    case "R": return f7 << 25 | rs2 << 20 | rs1 << 15 | base | rd << 7
    case "I": return _signed(imm, 12) << 20 | rs1 << 15 | base | rd << 7
    case "SH": return f7 << 25 | _unsigned(imm, 5) << 20 | rs1 << 15 | base | rd << 7
    case "S":
      i = _signed(imm, 12)
      return (i >> 5) << 25 | rs2 << 20 | rs1 << 15 | base | (i & 0x1F) << 7
    case "B":
      i = _signed(imm, 13, 2)
      return (i >> 12) << 31 | (i >> 5 & 0x3F) << 25 | rs2 << 20 | rs1 << 15 | base | (i >> 1 & 0xF) << 8 | (i >> 11 & 1) << 7
    case "U": return (imm & 0xFFFFF if -(1 << 19) <= imm < 0 else _unsigned(imm, 20)) << 12 | rd << 7 | op
    case "J":
      i = _signed(imm, 21, 2)
      return (i >> 20) << 31 | (i >> 1 & 0x3FF) << 21 | (i >> 11 & 1) << 20 | (i >> 12 & 0xFF) << 12 | rd << 7 | op
    case "FENCE": return _unsigned(imm or 0xFF, 12) << 20 | op           # imm = pred << 4 | succ, default iorw,iorw
    case "CSR" | "CSRI": return _unsigned(imm, 12) << 20 | rs1 << 15 | base | rd << 7
    case "UN": return f7 << 20 | rs1 << 15 | base | rd << 7
    case "SYS": return f7 << 20 | base
    case "FR": return f7 << 25 | rs2 << 20 | rs1 << 15 | _unsigned(rm, 3) << 12 | rd << 7 | op
    case "FU": return f7 << 20 | rs1 << 15 | _unsigned(rm, 3) << 12 | rd << 7 | op
    case "R4": return rs3 << 27 | f7 << 25 | rs2 << 20 | rs1 << 15 | _unsigned(rm, 3) << 12 | rd << 7 | op

def _rv_key(fmt, op, f3, f7):
  match fmt:
    case "UN" | "SYS": return ("f12", op, f3, f7)
    case "FU" | "FR" | "R4": return (fmt, op, f7)       # funct3 is rm, an operand
    case "R" | "SH": return ("f7", op, f3, f7)
    case "U" | "J": return ("op", op)
    case _: return ("f3", op, f3)
_RV_BY_KEY = {_rv_key(*spec): n for n, spec in RV.items()}

def rv_decode(w: int) -> tuple[str, dict] | None:
  """Inverse of rv() and v(), or None if the word is not an instruction in RV or RVV."""
  op, rd, f3, rs1, rs2, f7 = w & 0x7F, w >> 7 & 0x1F, w >> 12 & 7, w >> 15 & 0x1F, w >> 20 & 0x1F, w >> 25
  keys = (("f12", op, f3, w >> 20), ("FU", op, w >> 20), ("FR", op, f7), ("R4", op, f7 & 3), ("f7", op, f3, f7),
          ("f3", op, f3), ("op", op))
  name = next((_RV_BY_KEY[k] for k in keys if k in _RV_BY_KEY), None)
  if name is None: return v_decode(w)
  fmt = RV[name][0]
  imm = {"I": _sext(w >> 20, 12), "SH": rs2, "S": _sext((w >> 25) << 5 | rd, 12),
         "B": _sext((w >> 31) << 12 | (w >> 7 & 1) << 11 | (w >> 25 & 0x3F) << 5 | (w >> 8 & 0xF) << 1, 13),
         "U": w >> 12, "J": _sext((w >> 31) << 20 | (w >> 12 & 0xFF) << 12 | (w >> 20 & 1) << 11 | (w >> 21 & 0x3FF) << 1, 21),
         "FENCE": w >> 20, "CSR": w >> 20, "CSRI": w >> 20}.get(fmt, 0)
  f = dict(rd=rd, rs1=rs1, rs2=rs2, imm=imm, rs3=w >> 27, rm=f3)
  out = {k: f[k] for k in FORMAT_FIELDS[fmt]}
  return (name, out) if rv(name, **out) == w else v_decode(w)   # rejects words with stray bits in fixed fields

# ---- RVV: the V subset, TRISC2 only ----
#
# VLEN = 128 bits (vlenb = 16), ELEN = 32: SEW is 8, 16 or 32, so one register holds 16/8/4 elements and an LMUL=8
# group 128/64/32. vtype() refuses SEW=64; a vsetvli with e64 hung TRISC2. Widening ops need 2*SEW <= 32.
# ta/ma are ignored (always undisturbed); there is no vill bit. No vdiv/vdivu/vrem/vremu, vfdiv/vfrdiv, vfsqrt,
# vfrsqrt7 or vfrec7 (left out). FP ops have the scalar caveats (rne only, denormals flushed, non-IEEE fused ops), and
# at SEW=16 they follow cfg0's BF16 bit like Zfh. Performance (camel-cdr's rvv-bench, tt_t2): most ops carry a false
# dependency on vd, fractional LMUL behaves like LMUL>1, and LMUL>1 is split into micro-ops.
# Probed on TRISC2: vsetvli, vle16/32, vse16/32, vlse32, vadd.vv, vmul.vv, vmv.s.x, vmv.x.s, vmv.v.i, vredsum.vs,
# vredmaxu.vs, vfadd.vv, vfmul.vv, vfmv.s.f, vfmv.f.s, vfredmax.vs, vfredusum.vs, vmflt.vf, vcpop.m, vfwcvt.f.f.v
# (bf16 -> f32 in BF16 mode), vfadd.vv at e16 in BF16 mode. Copying 4 KiB of L1 with vle32/vse32 at m8 took 1298 cycles
# against 3349 for an 8x-unrolled lw/sw loop; summing 1024 words, 1372 against 4092.
#
# Operands are in assembly order, so the multiply-adds take (vd, vs1, vs2) and their .vx/.vf forms (vd, rs1, vs2).
# masked=True appends v0.t. The .vvm/.vxm/.vim/.vfm forms (vadc, vmerge, ...) always read v0 and have no masked flag.
# Loads take (vd, rs1 base[, rs2 stride | vs2 index]); stores take (vs3 value, rs1 base[, ...]).
# Reductions: vd[0] = op(vs1[0], vs2[*]); vw* widen the accumulator. Integer compares and vmf* write a mask.
# vadc/vsbc/vmadc/vmsbc chain carries through v0. Fixed-point ops (vsadd, vaadd, vsmul, vssrl, vnclip, ...) round per
# vxrm.

# operand: (shift, bits, signed)
_VFIELD = {"vd": (7, 5, 0), "rd": (7, 5, 0), "fd": (7, 5, 0), "vs3": (7, 5, 0), "vs2": (20, 5, 0), "rs2": (20, 5, 0),
           "vs1": (15, 5, 0), "rs1": (15, 5, 0), "fs1": (15, 5, 0), "simm": (15, 5, 1), "uimm": (15, 5, 0),
           "vtype": (20, 11, 0), "ivtype": (20, 10, 0)}
RVV = {}   # name: (word with every fixed bit set, operands in assembly order, maskable)

def _vdef(name, base, ops, maskable=True): RVV[name] = (base, tuple(ops.split()), maskable)
def _opv(name, f3, funct6, ops, vm=None, vs1=None, vs2=None):
  _vdef(name, funct6 << 26 | (vm or 0) << 25 | (vs2 or 0) << 20 | (vs1 or 0) << 15 | f3 << 12 | 0x57, ops, vm is None)

# form: (funct3, suffix, operands, fixed vm)
_OPI = {"vv": (0, ".vv", "vd vs2 vs1", None), "vx": (4, ".vx", "vd vs2 rs1", None), "vi": (3, ".vi", "vd vs2 simm", None),
        "vu": (3, ".vi", "vd vs2 uimm", None), "wv": (0, ".wv", "vd vs2 vs1", None), "wx": (4, ".wx", "vd vs2 rs1", None),
        "wu": (3, ".wi", "vd vs2 uimm", None), "vs": (0, ".vs", "vd vs2 vs1", None),
        "vvm": (0, ".vvm", "vd vs2 vs1", 0), "vxm": (4, ".vxm", "vd vs2 rs1", 0), "vim": (3, ".vim", "vd vs2 simm", 0),
        "vv-": (0, ".vv", "vd vs2 vs1", 1), "vx-": (4, ".vx", "vd vs2 rs1", 1), "vi-": (3, ".vi", "vd vs2 simm", 1)}
_OPM = {"vv": (2, ".vv", "vd vs2 vs1", None), "vx": (6, ".vx", "vd vs2 rs1", None), "vs": (2, ".vs", "vd vs2 vs1", None),
        "wv": (2, ".wv", "vd vs2 vs1", None), "wx": (6, ".wx", "vd vs2 rs1", None), "mm": (2, ".mm", "vd vs2 vs1", 1),
        "vm": (2, ".vm", "vd vs2 vs1", 1), "acc.vv": (2, ".vv", "vd vs1 vs2", None), "acc.vx": (6, ".vx", "vd rs1 vs2", None)}
_OPF = {"vv": (1, ".vv", "vd vs2 vs1", None), "vf": (5, ".vf", "vd vs2 fs1", None), "vs": (1, ".vs", "vd vs2 vs1", None),
        "wv": (1, ".wv", "vd vs2 vs1", None), "wf": (5, ".wf", "vd vs2 fs1", None), "vfm": (5, ".vfm", "vd vs2 fs1", 0),
        "acc.vv": (1, ".vv", "vd vs1 vs2", None), "acc.vf": (5, ".vf", "vd fs1 vs2", None)}
for _forms, _table in ((_OPI, """
    00 vadd vv vx vi | 02 vsub vv vx | 03 vrsub vx vi | 04 vminu vv vx | 05 vmin vv vx | 06 vmaxu vv vx | 07 vmax vv vx
    09 vand vv vx vi | 0a vor vv vx vi | 0b vxor vv vx vi | 0c vrgather vv vx vu | 0e vrgatherei16 vv
    0e vslideup vx vu | 0f vslidedown vx vu | 10 vadc vvm vxm vim | 11 vmadc vvm vxm vim vv- vx- vi-
    12 vsbc vvm vxm | 13 vmsbc vvm vxm vv- vx- | 17 vmerge vvm vxm vim
    18 vmseq vv vx vi | 19 vmsne vv vx vi | 1a vmsltu vv vx | 1b vmslt vv vx | 1c vmsleu vv vx vi | 1d vmsle vv vx vi
    1e vmsgtu vx vi | 1f vmsgt vx vi | 20 vsaddu vv vx vi | 21 vsadd vv vx vi | 22 vssubu vv vx | 23 vssub vv vx
    25 vsll vv vx vu | 27 vsmul vv vx | 28 vsrl vv vx vu | 29 vsra vv vx vu | 2a vssrl vv vx vu | 2b vssra vv vx vu
    2c vnsrl wv wx wu | 2d vnsra wv wx wu | 2e vnclipu wv wx wu | 2f vnclip wv wx wu | 30 vwredsumu vs | 31 vwredsum vs"""),
  (_OPM, """
    00 vredsum vs | 01 vredand vs | 02 vredor vs | 03 vredxor vs | 04 vredminu vs | 05 vredmin vs | 06 vredmaxu vs
    07 vredmax vs | 08 vaaddu vv vx | 09 vaadd vv vx | 0a vasubu vv vx | 0b vasub vv vx | 0e vslide1up vx
    0f vslide1down vx | 17 vcompress vm | 18 vmandn mm | 19 vmand mm | 1a vmor mm | 1b vmxor mm | 1c vmorn mm
    1d vmnand mm | 1e vmnor mm | 1f vmxnor mm | 24 vmulhu vv vx | 25 vmul vv vx | 26 vmulhsu vv vx | 27 vmulh vv vx
    29 vmadd acc.vv acc.vx | 2b vnmsub acc.vv acc.vx | 2d vmacc acc.vv acc.vx | 2f vnmsac acc.vv acc.vx
    30 vwaddu vv vx | 31 vwadd vv vx | 32 vwsubu vv vx | 33 vwsub vv vx | 34 vwaddu.w wv wx | 35 vwadd.w wv wx
    36 vwsubu.w wv wx | 37 vwsub.w wv wx | 38 vwmulu vv vx | 3a vwmulsu vv vx | 3b vwmul vv vx
    3c vwmaccu acc.vv acc.vx | 3d vwmacc acc.vv acc.vx | 3e vwmaccus acc.vx | 3f vwmaccsu acc.vv acc.vx"""),
  (_OPF, """
    00 vfadd vv vf | 01 vfredusum vs | 02 vfsub vv vf | 03 vfredosum vs | 04 vfmin vv vf | 05 vfredmin vs
    06 vfmax vv vf | 07 vfredmax vs | 08 vfsgnj vv vf | 09 vfsgnjn vv vf | 0a vfsgnjx vv vf | 0e vfslide1up vf
    0f vfslide1down vf | 17 vfmerge vfm | 18 vmfeq vv vf | 19 vmfle vv vf | 1b vmflt vv vf | 1c vmfne vv vf | 1d vmfgt vf
    1f vmfge vf | 24 vfmul vv vf | 27 vfrsub vf | 28 vfmadd acc.vv acc.vf | 29 vfnmadd acc.vv acc.vf
    2a vfmsub acc.vv acc.vf | 2b vfnmsub acc.vv acc.vf | 2c vfmacc acc.vv acc.vf | 2d vfnmacc acc.vv acc.vf
    2e vfmsac acc.vv acc.vf | 2f vfnmsac acc.vv acc.vf | 30 vfwadd vv vf | 31 vfwredusum vs | 32 vfwsub vv vf
    33 vfwredosum vs | 34 vfwadd.w wv wf | 36 vfwsub.w wv wf | 38 vfwmul vv vf | 3c vfwmacc acc.vv acc.vf
    3d vfwnmacc acc.vv acc.vf | 3e vfwmsac acc.vv acc.vf | 3f vfwnmsac acc.vv acc.vf""")):
  for _entry in _table.replace("\n", "|").split("|"):
    if not _entry.strip(): continue
    _funct6, _mn, *_fs = _entry.split()
    for _f in _fs:
      _f3, _sfx, _ops, _vm = _forms[_f]
      _opv(_mn.removesuffix(".w") + _sfx, _f3, int(_funct6, 16), _ops, _vm)   # vwadd.w + .wv -> vwadd.wv

# Unary and move forms: a fixed vs1 (or vs2) selects the operation inside one funct6.
_opv("vmv.v.v", 0, 0x17, "vd vs1", vm=1, vs2=0)               # vd = vs1 (splat forms: .v.x, .v.i, vfmv.v.f)
_opv("vmv.v.x", 4, 0x17, "vd rs1", vm=1, vs2=0)
_opv("vmv.v.i", 3, 0x17, "vd simm", vm=1, vs2=0)
_opv("vfmv.v.f", 5, 0x17, "vd fs1", vm=1, vs2=0)
for _n in (1, 2, 4, 8): _opv(f"vmv{_n}r.v", 3, 0x27, "vd vs2", vm=1, vs1=_n - 1)   # whole-register copy, ignores vl
_opv("vmv.x.s", 2, 0x10, "rd vs2", vm=1, vs1=0x00)             # x rd = vs2[0]
_opv("vcpop.m", 2, 0x10, "rd vs2", vs1=0x10)                   # x rd = number of set mask bits
_opv("vfirst.m", 2, 0x10, "rd vs2", vs1=0x11)                  # x rd = index of the first set mask bit, or -1
_opv("vmv.s.x", 6, 0x10, "vd rs1", vm=1, vs2=0)                # vd[0] = x rs1
_opv("vfmv.f.s", 1, 0x10, "fd vs2", vm=1, vs1=0x00)            # f fd = vs2[0]
_opv("vfmv.s.f", 5, 0x10, "vd fs1", vm=1, vs2=0)               # vd[0] = f fs1
for _n, _k in (("vzext.vf4", 4), ("vsext.vf4", 5), ("vzext.vf2", 6), ("vsext.vf2", 7)):  # vf8 needs SEW=64
  _opv(_n, 2, 0x12, "vd vs2", vs1=_k)
for _n, _k in (("vmsbf.m", 1), ("vmsof.m", 2), ("vmsif.m", 3), ("viota.m", 0x10)):
  _opv(_n, 2, 0x14, "vd vs2", vs1=_k)
_opv("vid.v", 2, 0x14, "vd", vs1=0x11, vs2=0)                  # vd[i] = i
for _n, _k in (("vfcvt.xu.f.v", 0), ("vfcvt.x.f.v", 1), ("vfcvt.f.xu.v", 2), ("vfcvt.f.x.v", 3), ("vfcvt.rtz.xu.f.v", 6),
               ("vfcvt.rtz.x.f.v", 7), ("vfwcvt.xu.f.v", 8), ("vfwcvt.x.f.v", 9), ("vfwcvt.f.xu.v", 10),
               ("vfwcvt.f.x.v", 11), ("vfwcvt.f.f.v", 12), ("vfwcvt.rtz.xu.f.v", 14), ("vfwcvt.rtz.x.f.v", 15),
               ("vfncvt.xu.f.w", 16), ("vfncvt.x.f.w", 17), ("vfncvt.f.xu.w", 18), ("vfncvt.f.x.w", 19),
               ("vfncvt.f.f.w", 20), ("vfncvt.rod.f.f.w", 21), ("vfncvt.rtz.xu.f.w", 22), ("vfncvt.rtz.x.f.w", 23)):
  _opv(_n, 1, 0x12, "vd vs2", vs1=_k)
_opv("vfclass.v", 1, 0x13, "vd vs2", vs1=0x10)

# Loads and stores: unit-stride, strided (rs2 = byte stride), indexed (vs2 = byte offsets, u unordered / o ordered),
# whole-register (vl<n>re<w>/vs<n>r copy n registers regardless of vl and vtype), and mask (vlm/vsm, ceil(vl/8) bytes).
# Not encoded: segment (nf > 0) and fault-only-first loads.
for _w, _f3 in ((8, 0), (16, 5), (32, 6)):
  _vdef(f"vle{_w}.v", _f3 << 12 | 0x07, "vd rs1")
  _vdef(f"vse{_w}.v", _f3 << 12 | 0x27, "vs3 rs1")
  _vdef(f"vlse{_w}.v", 2 << 26 | _f3 << 12 | 0x07, "vd rs1 rs2")
  _vdef(f"vsse{_w}.v", 2 << 26 | _f3 << 12 | 0x27, "vs3 rs1 rs2")
  for _mop, _k in ((1, "u"), (3, "o")):
    _vdef(f"vl{_k}xei{_w}.v", _mop << 26 | _f3 << 12 | 0x07, "vd rs1 vs2")
    _vdef(f"vs{_k}xei{_w}.v", _mop << 26 | _f3 << 12 | 0x27, "vs3 rs1 vs2")
  for _n in (1, 2, 4, 8): _vdef(f"vl{_n}re{_w}.v", (_n - 1) << 29 | 1 << 25 | 8 << 20 | _f3 << 12 | 0x07, "vd rs1", False)
for _n in (1, 2, 4, 8): _vdef(f"vs{_n}r.v", (_n - 1) << 29 | 1 << 25 | 8 << 20 | 0x27, "vs3 rs1", False)
_vdef("vlm.v", 1 << 25 | 0xB << 20 | 0x07, "vd rs1", False)
_vdef("vsm.v", 1 << 25 | 0xB << 20 | 0x27, "vs3 rs1", False)

# Configuration: rd = vl = min(AVL, VLMAX) for the new vtype. AVL is x rs1 (vsetvli/vsetvl; rs1 = x0 with rd != x0
# means VLMAX) or a 5-bit immediate (vsetivli). vsetvl takes vtype from x rs2.
_vdef("vsetvli", 7 << 12 | 0x57, "rd rs1 vtype", False)
_vdef("vsetivli", 3 << 30 | 7 << 12 | 0x57, "rd uimm ivtype", False)
_vdef("vsetvl", 1 << 31 | 7 << 12 | 0x57, "rd rs1 rs2", False)

_LMUL = {1: 0, 2: 1, 4: 2, 8: 3, 1 / 8: 5, 1 / 4: 6, 1 / 2: 7}
def vtype(sew: int = 32, lmul: float = 1, ta: bool = False, ma: bool = False) -> int:
  """vtype immediate for vsetvli/vsetivli. sew in (8, 16, 32); lmul in (1/8, 1/4, 1/2, 1, 2, 4, 8). The hardware
  ignores ta/ma and always leaves tail and masked-off elements undisturbed."""
  if sew not in (8, 16, 32): raise ValueError(f"SEW={sew}: TRISC2 supports e8/e16/e32 (ELEN=32; e64 hung the core)")
  if lmul not in _LMUL: raise ValueError(f"LMUL={lmul} is not one of 1/8, 1/4, 1/2, 1, 2, 4, 8")
  return int(ma) << 7 | int(ta) << 6 | (sew.bit_length() - 4) << 3 | _LMUL[lmul]

def v(name: str, *args: int, masked: bool = False, **fields: int) -> int:
  """One RVV instruction (TRISC2 only). Operands positionally in assembly order (RVV[name][1]) or by name."""
  base, ops, maskable = RVV[name]
  vals = dict(zip(ops, args)) | fields
  if len(args) > len(ops) or set(vals) != set(ops): raise ValueError(f"{name} takes {', '.join(ops)}")
  if masked and not maskable: raise ValueError(f"{name} cannot be masked")
  w = base | (0 if masked or not maskable else 1 << 25)
  for o in ops:
    shift, bits, signed = _VFIELD[o]
    w |= (_signed(vals[o], bits) if signed else _unsigned(vals[o], bits)) << shift
  if name in ("vsetvli", "vsetivli"):
    t = vals[ops[2]]
    if t >> 3 & 7 > 2 or t & 7 == 4 or t >> 8: raise ValueError(f"{name}: vtype {t:#x} is reserved or SEW > 32 (use vtype())")
  return w

def _vmask(base, ops, maskable):
  m = 0xFFFFFFFF
  for o in ops: m &= ~(((1 << _VFIELD[o][1]) - 1) << _VFIELD[o][0])
  return m & ~(maskable << 25)
_RVV_MATCH = [(n, _vmask(*spec), spec[0]) for n, spec in RVV.items()]

def v_decode(w: int) -> tuple[str, dict] | None:
  """Inverse of v(), or None. Fields are named as in RVV[name][1], plus masked for maskable instructions."""
  for name, mask, base in _RVV_MATCH:
    if w & mask != base: continue
    _, ops, maskable = RVV[name]
    out = {}
    for o in ops:
      shift, bits, signed = _VFIELD[o]
      x = w >> shift & ((1 << bits) - 1)
      out[o] = _sext(x, bits) if signed else x
    if maskable: out["masked"] = not w >> 25 & 1
    try:
      if v(name, **out) == w: return name, out
    except ValueError: pass
  return None

# ---- Tensix ----

def tensix(name: str, *args: int, **fields: int) -> int:
  """One Tensix instruction, unrotated. Fields positionally in tt-llk argument order, or by name; missing fields are 0."""
  op, spec = TENSIX[name]
  if len(args) > len(spec): raise ValueError(f"{name} takes {len(spec)} fields")
  vals = dict(zip((f for f, _, _ in spec), args)) | fields
  if unknown := set(vals) - {f for f, _, _ in spec}: raise ValueError(f"{name} has no field {unknown}")
  w = op << 24
  for f, shift, width in spec:
    v = vals.get(f, 0)
    if not 0 <= v < 1 << width: raise ValueError(f"{name}.{f}={v} does not fit {width} bits")
    w |= v << shift
  return w


def tensix_decode(w: int) -> tuple[str, dict] | None:
  name = _TENSIX_BY_OP.get(w >> 24)
  if name is None: return None
  out = {f: w >> s & ((1 << n) - 1) for f, s, n in TENSIX[name][1]}
  return (name, out) if tensix(name, **out) == w else None

def inline(w: int) -> int:
  """A Tensix word as stored in a TRISC instruction stream."""
  return (w << 2 | w >> 30) & 0xFFFFFFFF
def outline(w: int) -> int: return (w >> 2 | w << 30) & 0xFFFFFFFF

# ---- named field values (blackhole-py-old ttko) ----

class Stall(IntEnum):
  """STALLWAIT/SEMWAIT stall_res: which units of this thread are blocked."""
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF

class Wait(IntEnum):
  """STALLWAIT wait_res: the conditions waited for (all must clear)."""
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (
    1 << x for x in range(13))

class SemWait(IntEnum):
  """SEMWAIT wait_sem_cond."""
  STALL_ON_ZERO, STALL_ON_MAX = 1, 2

class LReg(IntEnum):
  """SFPU register operands (lreg_*)."""
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)        # read/write
  CONST_0_8373, ZERO, ONE, NEG_ONE = 8, 9, 10, 11  # read-only; firmware loads -1.0 into 11 every launch
  CONFIG0, CONFIG1, CONFIG2 = 12, 13, 14           # SFPCONFIG-programmable constants
  LANE_X2 = 15                                     # read-only lane index * 2
  LOAD_MACRO = 16                                  # SFPLOADMACRO pipeline register, never an ordinary operand

class SfpuFormat(IntEnum):
  """SFPLOAD/SFPSTORE instr_mod0."""
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO, INT32_SIGN_MAGNITUDE = range(10, 13)
  INT8_COMPAT, LO16_ONLY, HI16_ONLY = range(13, 16)

class LoadImm(IntEnum):
  """SFPLOADI instr_mod0: how imm16 is interpreted."""
  FLOATB, FLOATA, USHORT, SHORT, UPPER, LOWER = 0, 1, 2, 4, 8, 10

class Broadcast(IntEnum):
  """ELWADD/ELWSUB/ELWMUL instr_mod19: SrcB broadcast."""
  NONE, COLUMN, ROW, SCALAR = range(4)


# ---- Not covered (to look up) ----
#
# RISC-V the baby cores lack (UndefinedBehavior, so not encoded): fdiv/fsqrt (.s and .h), lr.w/sc.w, Zbs, Zbc,
# packh/zip/unzip, and in RVV vdiv/vdivu/vrem/vremu, vfdiv/vfrdiv, vfsqrt, vfrsqrt7, vfrec7. Implemented but not
# encoded: RVV segment and fault-only-first loads/stores (untested on hardware); vzext/vsext.vf8 need SEW=64.
# cycle and instret are CSRs 0xC00 and 0xC02 (csrrs rd, csr, x0); time is not implemented.
#
# Tensix instructions with an encoding but no written-up field meanings (65 of 137):
#   ADDDMAREG ADDRCRXY ADDRCRZW APOOL3S1 APOOL3S2 ATCAS ATGETM ATINCGET ATINCGETPTR ATRELM ATSWAP BITWOPDMAREG
#   CFGSHIFTMASK CLREXPHIST CMPDMAREG CONV3S1 CONV3S2 DOTPV FLUSHDMA INCADCXY INCADCZW LOADIND LOADREG MFCONV3S1
#   MOP_CFG MOVDBGA2D MOVDBGB2D MPOOL3S1 MPOOL3S2 MULDMAREG PACR_SETREG RAREB REG2FLOP RESOURCEDECL RSTDMA SETASHRMH
#   SETASHRMH0 SETASHRMH1 SETASHRMV SETDVALID SETIBRWC SETPKEDGOF SFPCOMPC SFPDIVP2 SFPGT SFPLE SFPLUT SFPLUTFP32
#   SFPLZ SFPMUL24 SFPNOT SFPSETMAN SFPSETSGN SFP_STOCH_RND SHIFTDMAREG SHIFTXA SHIFTXB STOREIND STOREREG STREAMWAIT
#   STREAMWRCFG SUBDMAREG TBUFCMD TRNSPSRCA XMOV

# name: (opcode, ((field, shift, width), ...))
TENSIX = {
  'ADDDMAREG': (0x58, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'ADDRCRXY': (0x53, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3), ('BitMask', 0, 6))),
  'ADDRCRZW': (0x56, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3), ('BitMask', 0, 6))),
  'APOOL3S1': (0x25, (('clear_dvalid', 22, 2), ('pool_addr_mode', 15, 7), ('index_en', 14, 1), ('dst', 0, 14))),
  'APOOL3S2': (0x32, (('clear_dvalid', 22, 2), ('pool_addr_mode', 15, 7), ('index_en', 14, 1), ('dst', 0, 14))),
  'ATCAS': (0x64, (('MemHierSel', 23, 1), ('SwapVal', 18, 5), ('CmpVal', 14, 4), ('Sel32b', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'ATGETM': (0xa0, (('mutex_index', 0, 24),)),
  'ATINCGET': (0x61, (('MemHierSel', 23, 1), ('WrapVal', 14, 9), ('Sel32b', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'ATINCGETPTR': (0x62, (('MemHierSel', 23, 1), ('NoIncr', 22, 1), ('IncrVal', 18, 4), ('WrapVal', 14, 4), ('Sel32b', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'ATRELM': (0xa1, (('mutex_index', 0, 24),)),
  'ATSWAP': (0x63, (('MemHierSel', 23, 1), ('SwapMask', 14, 9), ('DataRegIndex', 6, 8), ('AddrRegIndex', 0, 6))),
  'BITWOPDMAREG': (0x5b, (('OpBisConst', 23, 1), ('OpSel', 18, 5), ('ResultRegIndex', 12, 6), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'CFGSHIFTMASK': (0xb8, (('disable_mask_on_old_val', 23, 1), ('operation', 20, 3), ('mask_width', 15, 5), ('right_cshift_amt', 10, 5), ('scratch_sel', 8, 2), ('CfgReg', 0, 8))),
  'CLEARDVALID': (0x36, (('cleardvalid', 22, 2), ('reset', 0, 22))),
  'CLREXPHIST': (0x21, ()),
  'CMPDMAREG': (0x5d, (('OpBisConst', 23, 1), ('OpSel', 18, 5), ('ResultRegIndex', 12, 6), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'CONV3S1': (0x22, (('clear_dvalid', 22, 2), ('rotate_weights', 17, 5), ('addr_mode', 14, 3), ('dst', 0, 14))),
  'CONV3S2': (0x23, (('clear_dvalid', 22, 2), ('rotate_weights', 17, 5), ('addr_mode', 14, 3), ('dst', 0, 14))),
  'DMANOP': (0x60, ()),
  'DOTPV': (0x29, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWADD': (0x28, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWMUL': (0x27, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWSUB': (0x30, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'FLUSHDMA': (0x46, (('FlushSpec', 0, 24),)),
  'GAPOOL': (0x34, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('pool_addr_mode', 15, 4), ('max_pool_index_en', 14, 1), ('dst', 0, 14))),
  'GATESRCRST': (0x35, (('reset_srcb_gate_control', 1, 23), ('reset_srca_gate_control', 0, 1))),
  'GMPOOL': (0x33, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('pool_addr_mode', 15, 4), ('max_pool_index_en', 14, 1), ('dst', 0, 14))),
  'INCADCXY': (0x52, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3))),
  'INCADCZW': (0x55, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3))),
  'INCRWC': (0x38, (('rwc_cr', 18, 6), ('rwc_d', 14, 4), ('rwc_b', 10, 4), ('rwc_a', 6, 4))),
  'LOADIND': (0x49, (('SizeSel', 22, 2), ('OffsetIndex', 14, 8), ('AutoIncSpec', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'LOADREG': (0x68, (('TdmaDataRegIndex', 18, 6), ('RegAddr', 0, 18))),
  'MFCONV3S1': (0x3a, (('clear_dvalid', 22, 2), ('rotate_weights', 17, 5), ('addr_mode', 14, 3), ('dst', 0, 14))),
  'MOP': (0x01, (('mop_type', 23, 1), ('loop_count', 16, 7), ('zmask_lo16_or_loop_count', 0, 16))),
  'MOP_CFG': (0x03, (('zmask_hi16', 0, 24),)),
  'MOVA2D': (0x12, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVB2A': (0x0b, (('srca', 17, 7), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('srcb', 0, 12))),
  'MOVB2D': (0x13, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('movb2d_instr_mod', 11, 3), ('dst', 0, 11))),
  'MOVD2A': (0x08, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVD2B': (0x0a, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVDBGA2D': (0x09, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVDBGB2D': (0x0c, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('movb2d_instr_mod', 11, 3), ('dst', 0, 11))),
  'MPOOL3S1': (0x24, (('clear_dvalid', 22, 2), ('pool_addr_mode', 15, 7), ('index_en', 14, 1), ('dst', 0, 14))),
  'MPOOL3S2': (0x31, (('clear_dvalid', 22, 2), ('pool_addr_mode', 15, 7), ('index_en', 14, 1), ('dst', 0, 14))),
  'MULDMAREG': (0x5a, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'MVMUL': (0x26, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'NOP': (0x02, ()),
  'PACR': (0x41, (('CfgContext', 21, 3), ('RowPadZero', 18, 3), ('DstAccessMode', 17, 1), ('AddrMode', 15, 2), ('AddrCntContext', 13, 2), ('ZeroWrite', 12, 1), ('ReadIntfSel', 8, 4), ('OvrdThreadId', 7, 1), ('Concat', 4, 3), ('CtxtCtrl', 2, 2), ('Flush', 1, 1), ('Last', 0, 1))),
  'PACR_SETREG': (0x4a, (('Push', 23, 1), ('ModeSel', 22, 1), ('Unused', 12, 10), ('DisableStall', 10, 2), ('AddrSel', 8, 2), ('StreamId', 2, 6), ('Flush', 1, 1), ('Last', 0, 1))),
  'RAREB': (0x15, ()),
  'RDCFG': (0xb1, (('GprAddress', 16, 8), ('CfgReg', 0, 16))),
  'REG2FLOP': (0x48, (('SizeSel', 22, 2), ('TargetSel', 20, 2), ('ByteOffset', 18, 2), ('ContextId_2', 16, 2), ('FlopIndex', 6, 10), ('RegIndex', 0, 6))),
  'REPLAY': (0x04, (('start_idx', 14, 10), ('len', 4, 10), ('execute_while_loading', 1, 3), ('load_mode', 0, 1))),
  'RESOURCEDECL': (0x05, (('linger_time', 13, 11), ('resources', 4, 9), ('op_class', 0, 4))),
  'RMWCIB0': (0xb3, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB1': (0xb4, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB2': (0xb5, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB3': (0xb6, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RSTDMA': (0x44, ()),
  'SEMGET': (0xa5, (('sem_sel', 2, 22),)),
  'SEMINIT': (0xa3, (('max_value', 20, 4), ('init_value', 16, 4), ('sem_sel', 2, 14))),
  'SEMPOST': (0xa4, (('sem_sel', 2, 22),)),
  'SEMWAIT': (0xa6, (('stall_res', 15, 9), ('sem_sel', 2, 13), ('wait_sem_cond', 0, 2))),
  'SETADC': (0x50, (('CntSetMask', 21, 3), ('ChannelIndex', 20, 1), ('DimensionIndex', 18, 2), ('Value', 0, 18))),
  'SETADCXX': (0x5e, (('CntSetMask', 21, 3), ('x_end2', 10, 11), ('x_start', 0, 10))),
  'SETADCXY': (0x51, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3), ('BitMask', 0, 6))),
  'SETADCZW': (0x54, (('CntSetMask', 21, 3), ('Ch1_W', 15, 6), ('Ch1_Z', 12, 3), ('Ch0_W', 9, 3), ('Ch0_Z', 6, 3), ('BitMask', 0, 6))),
  'SETASHRMH': (0x1e, (('reg_mask', 1, 23), ('halo_mask', 0, 1))),
  'SETASHRMH0': (0x1a, (('reg_mask', 1, 23), ('halo_mask', 0, 1))),
  'SETASHRMH1': (0x1b, (('reg_mask', 1, 23), ('halo_mask', 0, 1))),
  'SETASHRMV': (0x1c, (('reg_mask2', 0, 24),)),
  'SETC16': (0xb2, (('setc16_reg', 16, 8), ('setc16_value', 0, 16))),
  'SETDMAREG': (0x45, (('Payload_SigSelSize', 22, 2), ('Payload_SigSel', 8, 14), ('SetSignalsMode', 7, 1), ('RegIndex16b', 0, 7))),
  'SETDVALID': (0x57, (('setvalid', 0, 24),)),
  'SETIBRWC': (0x39, (('rwc_cr', 18, 6), ('rwc_bias', 6, 12), ('set_inc_ctrl', 0, 6))),
  'SETPKEDGOF': (0x1d, (('y_end', 12, 12), ('y_start', 8, 4), ('x_end', 4, 4), ('x_start', 0, 4))),
  'SETRWC': (0x37, (('clear_ab_vld', 22, 2), ('rwc_cr', 18, 4), ('rwc_d', 14, 4), ('rwc_b', 10, 4), ('rwc_a', 6, 4), ('BitMask', 0, 6))),
  'SFPABS': (0x7d, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPADD': (0x85, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPADDI': (0x75, (('imm16_math', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPAND': (0x7e, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPARECIP': (0x99, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPCAST': (0x90, (('lreg_src_c', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPCOMPC': (0x8b, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPCONFIG': (0x91, (('imm16_math', 8, 16), ('config_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPDIVP2': (0x76, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPENCC': (0x8a, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPEXEXP': (0x77, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPEXMAN': (0x78, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPGT': (0x97, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPIADD': (0x79, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPLE': (0x96, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPLOAD': (0x70, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPLOADI': (0x71, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('imm16', 0, 16))),
  'SFPLOADMACRO': (0x93, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPLUT': (0x73, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('dest_reg_addr', 0, 16))),
  'SFPLUTFP32': (0x95, (('lreg_dest', 4, 20), ('instr_mod1', 0, 4))),
  'SFPLZ': (0x81, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMAD': (0x84, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMOV': (0x7c, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMUL': (0x86, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMUL24': (0x98, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMULI': (0x74, (('imm16_math', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPNOP': (0x8f, ()),
  'SFPNOT': (0x80, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPOR': (0x7f, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPPOPC': (0x88, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPPUSHC': (0x87, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETCC': (0x7b, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETEXP': (0x82, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETMAN': (0x83, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETSGN': (0x89, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSHFT': (0x7a, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSHFT2': (0x94, (('imm12_math', 12, 12), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSTORE': (0x72, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPSWAP': (0x92, (('imm12_math', 12, 12), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPTRANSP': (0x8c, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPXOR': (0x8d, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFP_STOCH_RND': (0x8e, (('rnd_mode', 21, 3), ('imm8_math', 16, 5), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SHIFTDMAREG': (0x5c, (('OpBisConst', 23, 1), ('OpSel', 18, 5), ('ResultRegIndex', 12, 6), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'SHIFTXA': (0x17, (('log2_amount2', 2, 22), ('shift_mode', 0, 2))),
  'SHIFTXB': (0x18, (('addr_mode', 14, 10), ('rot_shift', 10, 4), ('shift_row', 0, 10))),
  'STALLWAIT': (0xa2, (('stall_res', 15, 9), ('wait_res', 0, 15))),
  'STOREIND': (0x66, (('MemHierSel', 23, 1), ('SizeSel', 22, 1), ('RegSizeSel', 21, 1), ('OffsetIndex', 14, 7), ('AutoIncSpec', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'STOREREG': (0x67, (('TdmaDataRegIndex', 18, 6), ('RegAddr', 0, 18))),
  'STREAMWAIT': (0xa7, (('stall_res', 15, 9), ('target_value', 4, 11), ('target_sel', 3, 1), ('wait_stream_sel', 0, 3))),
  'STREAMWRCFG': (0xb7, (('stream_id_sel', 21, 3), ('StreamRegAddr', 11, 10), ('CfgReg', 0, 11))),
  'SUBDMAREG': (0x59, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'TBUFCMD': (0x4b, ()),
  'TRNSPSRCA': (0x14, ()),
  'TRNSPSRCB': (0x16, ()),
  'UNPACR': (0x42, (('Unpack_block_selection', 23, 1), ('AddrMode', 15, 8), ('CfgContextCntInc', 13, 2), ('CfgContextId', 10, 3), ('AddrCntContextId', 8, 2), ('OvrdThreadId', 7, 1), ('SetDatValid', 6, 1), ('srcb_bcast', 5, 1), ('ZeroWrite2', 4, 1), ('AutoIncContextID', 3, 1), ('RowSearch', 2, 1), ('SearchCacheFlush', 1, 1), ('Last', 0, 1))),
  'UNPACR_NOP': (0x43, (('Unpacker_Select', 23, 1), ('Stream_Id', 16, 7), ('Msg_Clr_Cnt', 12, 4), ('Set_Dvalid', 8, 4), ('Clr_to1_fmt_Ctrl', 6, 2), ('Stall_Clr_Cntrl', 5, 1), ('Bank_Clr_Ctrl', 4, 1), ('Src_ClrVal_Ctrl', 2, 2), ('Unpack_Pop', 0, 2))),
  'WRCFG': (0xb0, (('GprAddress', 16, 8), ('wr128b', 15, 1), ('CfgReg', 0, 15))),
  'XMOV': (0x40, (('Mov_block_selection', 23, 1), ('Last', 0, 23))),
  'ZEROACC': (0x10, (('clear_mode', 19, 5), ('use_32_bit_mode', 18, 1), ('clear_zero_flags', 17, 1), ('addr_mode', 14, 3), ('where', 0, 14))),
  'ZEROSRC': (0x11, (('zero_val', 4, 20), ('write_mode', 3, 1), ('bank_mask', 2, 1), ('src_mask', 0, 2))),
}
_TENSIX_BY_OP = {op: n for n, (op, _) in TENSIX.items()}

# ---- Tensix, one function per instruction ----

def ADDDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x58. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  ResultRegIndex [22:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('ADDDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def ADDRCRXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=0):
  """0x53. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  CntSetMask [23:21]
  Ch1_Y [20:15]
  Ch1_X [14:12]
  Ch0_Y [11:9]
  Ch0_X [8:6]
  BitMask [5:0]"""
  return tensix('ADDRCRXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask)

def ADDRCRZW(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=0):
  """0x56. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  CntSetMask [23:21]
  Ch1_Y [20:15]
  Ch1_X [14:12]
  Ch0_Y [11:9]
  Ch0_X [8:6]
  BitMask [5:0]"""
  return tensix('ADDRCRZW', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask)

def APOOL3S1(clear_dvalid=0, pool_addr_mode=0, index_en=0, dst=0):
  """0x25. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  pool_addr_mode [21:15]
  index_en [14]
  dst [13:0]"""
  return tensix('APOOL3S1', clear_dvalid, pool_addr_mode, index_en, dst)

def APOOL3S2(clear_dvalid=0, pool_addr_mode=0, index_en=0, dst=0):
  """0x32. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  pool_addr_mode [21:15]
  index_en [14]
  dst [13:0]"""
  return tensix('APOOL3S2', clear_dvalid, pool_addr_mode, index_en, dst)

def ATCAS(MemHierSel=0, SwapVal=0, CmpVal=0, Sel32b=0, DataRegIndex=0, AddrRegIndex=0):
  """0x64. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  MemHierSel [23]
  SwapVal [22:18]
  CmpVal [17:14]
  Sel32b [13:12]
  DataRegIndex [11:6]
  AddrRegIndex [5:0]"""
  return tensix('ATCAS', MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex)

def ATGETM(mutex_index=0):
  """0xA0. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  mutex_index [23:0]"""
  return tensix('ATGETM', mutex_index)

def ATINCGET(MemHierSel=0, WrapVal=0, Sel32b=0, DataRegIndex=0, AddrRegIndex=0):
  """0x61. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  MemHierSel [23]
  WrapVal [22:14]
  Sel32b [13:12]
  DataRegIndex [11:6]
  AddrRegIndex [5:0]"""
  return tensix('ATINCGET', MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex)

def ATINCGETPTR(MemHierSel=0, NoIncr=0, IncrVal=0, WrapVal=0, Sel32b=0, DataRegIndex=0, AddrRegIndex=0):
  """0x62. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  MemHierSel [23]
  NoIncr [22]
  IncrVal [21:18]
  WrapVal [17:14]
  Sel32b [13:12]
  DataRegIndex [11:6]
  AddrRegIndex [5:0]"""
  return tensix('ATINCGETPTR', MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex)

def ATRELM(mutex_index=0):
  """0xA1. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  mutex_index [23:0]"""
  return tensix('ATRELM', mutex_index)

def ATSWAP(MemHierSel=0, SwapMask=0, DataRegIndex=0, AddrRegIndex=0):
  """0x63. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  MemHierSel [23]
  SwapMask [22:14]
  DataRegIndex [13:6]
  AddrRegIndex [5:0]"""
  return tensix('ATSWAP', MemHierSel, SwapMask, DataRegIndex, AddrRegIndex)

def BITWOPDMAREG(OpBisConst=0, OpSel=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x5B. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  OpSel [22:18]
  ResultRegIndex [17:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('BITWOPDMAREG', OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex)

def CFGSHIFTMASK(disable_mask_on_old_val=0, operation=0, mask_width=0, right_cshift_amt=0, scratch_sel=0, CfgReg=0):
  """0xB8. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  disable_mask_on_old_val [23]
  operation [22:20]
  mask_width [19:15]
  right_cshift_amt [14:10]
  scratch_sel [9:8]
  CfgReg [7:0]"""
  return tensix('CFGSHIFTMASK', disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg)

def CLEARDVALID(cleardvalid=0, reset=0):
  """Release source banks to unpackers (Control, 0x36). Release the selected SrcA/SrcB banks and optionally switch which
  banks the FPU reads.

  cleardvalid [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                      consumed bank back to the unpacker unless clearing is disabled in configuration.
  reset       [21:0]  Packed low bits: bit 0 resets source synchronization; bit 1 keeps reading the same bank after
                      release. The remaining encoder bits are not public operands.
  Note: Reset mode is discouraged by the manual and unsupported by ttsim; it may produce nondeterministic hangs."""
  return tensix('CLEARDVALID', cleardvalid, reset)

def CLREXPHIST():
  """0x21. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile."""
  return tensix('CLREXPHIST')

def CMPDMAREG(OpBisConst=0, OpSel=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x5D. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  OpSel [22:18]
  ResultRegIndex [17:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('CMPDMAREG', OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex)

def CONV3S1(clear_dvalid=0, rotate_weights=0, addr_mode=0, dst=0):
  """0x22. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  rotate_weights [21:17]
  addr_mode [16:14]
  dst [13:0]"""
  return tensix('CONV3S1', clear_dvalid, rotate_weights, addr_mode, dst)

def CONV3S2(clear_dvalid=0, rotate_weights=0, addr_mode=0, dst=0):
  """0x23. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  rotate_weights [21:17]
  addr_mode [16:14]
  dst [13:0]"""
  return tensix('CONV3S2', clear_dvalid, rotate_weights, addr_mode, dst)

def DMANOP():
  """Scalar/DMA no operation (Control, 0x60). Issue a no-op on the scalar/DMA path.

  Note: Used near configuration and packing setup. A no-op is not a replacement for waiting for outstanding DMA or pack
        work."""
  return tensix('DMANOP')

def DOTPV(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """0x29. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  dest_accum_en [21]
  instr_mod19 [20:19]
  addr_mode [18:14]
  dst [13:0]"""
  return tensix('DOTPV', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def ELWADD(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise addition (FPU, 0x28). Add aligned 8 x 16 blocks from SrcA and SrcB, optionally accumulating into Dst.

  clear_dvalid  [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                        consumed bank back to the unpacker unless clearing is disabled in configuration.
  dest_accum_en [21]    0 overwrites Dst with the result; 1 adds the result to existing Dst.
  instr_mod19   [20:19] SrcB broadcast: 0 none; 1 column 0; 2 one row; 3 one scalar (row plus column broadcast).
  addr_mode     [18:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                        byte stride. The Python bit field is wider than the semantic selector; do not assume every
                        encodable value is valid.
  dst           [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned
                        for the instruction footprint. This is not an L1 byte address.
  Note: Data formats and FP32 accumulation are configured separately. Source-bank ownership must permit math to read
        both sources.
  Note: Multiplication precision depends on fidelity phases. The retained HiFi2 tests issue phase 0 for all output
        blocks, then phase 1. ELWADD/ELWSUB require fidelity phase zero."""
  return tensix('ELWADD', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def ELWMUL(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise multiplication (FPU, 0x27). Multiply aligned 8 x 16 blocks from SrcA and SrcB, optionally accumulating
  into Dst over fidelity phases.

  clear_dvalid  [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                        consumed bank back to the unpacker unless clearing is disabled in configuration.
  dest_accum_en [21]    0 overwrites Dst with the result; 1 adds the result to existing Dst.
  instr_mod19   [20:19] SrcB broadcast: 0 none; 1 column 0; 2 one row; 3 one scalar (row plus column broadcast).
  addr_mode     [18:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                        byte stride. The Python bit field is wider than the semantic selector; do not assume every
                        encodable value is valid.
  dst           [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned
                        for the instruction footprint. This is not an L1 byte address.
  Note: Data formats and FP32 accumulation are configured separately. Source-bank ownership must permit math to read
        both sources.
  Note: Multiplication precision depends on fidelity phases. The retained HiFi2 tests issue phase 0 for all output
        blocks, then phase 1. ELWADD/ELWSUB require fidelity phase zero."""
  return tensix('ELWMUL', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def ELWSUB(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise subtraction (FPU, 0x30). Subtract aligned SrcB values from SrcA, optionally accumulating into Dst.

  clear_dvalid  [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                        consumed bank back to the unpacker unless clearing is disabled in configuration.
  dest_accum_en [21]    0 overwrites Dst with the result; 1 adds the result to existing Dst.
  instr_mod19   [20:19] SrcB broadcast: 0 none; 1 column 0; 2 one row; 3 one scalar (row plus column broadcast).
  addr_mode     [18:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                        byte stride. The Python bit field is wider than the semantic selector; do not assume every
                        encodable value is valid.
  dst           [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned
                        for the instruction footprint. This is not an L1 byte address.
  Note: Data formats and FP32 accumulation are configured separately. Source-bank ownership must permit math to read
        both sources.
  Note: Multiplication precision depends on fidelity phases. The retained HiFi2 tests issue phase 0 for all output
        blocks, then phase 1. ELWADD/ELWSUB require fidelity phase zero."""
  return tensix('ELWSUB', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def FLUSHDMA(FlushSpec=0):
  """0x46. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  FlushSpec [23:0]"""
  return tensix('FLUSHDMA', FlushSpec)

def GAPOOL(clear_dvalid=0, instr_mod19=0, pool_addr_mode=0, max_pool_index_en=0, dst=0):
  """Four-row weighted reduction (FPU, 0x34). Compute Dst[4 x 16] += SrcB[4 x 16] @ SrcA[16 x 16]. This is weighted
  summation, not an automatic mean.

  clear_dvalid      [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands
                            the consumed bank back to the unpacker unless clearing is disabled in configuration.
  instr_mod19       [21:19] Keep zero for the documented operation. The Python encoder exposes these bits, but they are
                            not an independent supported operand in the reference syntax.
  pool_addr_mode    [18:15] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not
                            a byte stride. The Python bit field is wider than the semantic selector; do not assume every
                            encodable value is valid.
  max_pool_index_en [14]    Keep 0 for the repository's non-index reduction. Index output is a separate mode requiring
                            additional configuration.
  dst               [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then
                            aligned for the instruction footprint. This is not an L1 byte address.
  Note: SrcA uses an aligned 16 x 16 footprint. SrcB begins at an eight-row boundary. GAPOOL reads four SrcB rows;
        GMPOOL uses one row for exponent scaling (the tests use B=1).
  Note: The allocator reserves a 128-element Dst slot even though these instructions write fewer rows. Do not assume the
        unused rows are overwritten."""
  return tensix('GAPOOL', clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst)

def GATESRCRST(reset_srcb_gate_control=0, reset_srca_gate_control=0):
  """Invalidate the SrcB operand cache (Control, 0x35). Forcibly invalidate the one-slot SrcB operand cache feeding the
  FPU.

  reset_srcb_gate_control [23:1]  1 invalidates the SrcB operand cache.
  reset_srca_gate_control [0]     Keep zero for the documented operation. The Python encoder exposes these bits, but
                                  they are not an independent supported operand in the reference syntax.
  Note: This is cache invalidation, not source-bank ownership transfer."""
  return tensix('GATESRCRST', reset_srcb_gate_control, reset_srca_gate_control)

def GMPOOL(clear_dvalid=0, instr_mod19=0, pool_addr_mode=0, max_pool_index_en=0, dst=0):
  """Column-wise maximum reduction (FPU, 0x33). Reduce SrcA rows to a maximum per column, combine with the first Dst row,
  and clear the next three Dst rows in the normal non-index mode.

  clear_dvalid      [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands
                            the consumed bank back to the unpacker unless clearing is disabled in configuration.
  instr_mod19       [21:19] Keep zero for the documented operation. The Python encoder exposes these bits, but they are
                            not an independent supported operand in the reference syntax.
  pool_addr_mode    [18:15] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not
                            a byte stride. The Python bit field is wider than the semantic selector; do not assume every
                            encodable value is valid.
  max_pool_index_en [14]    Keep 0 for the repository's non-index reduction. Index output is a separate mode requiring
                            additional configuration.
  dst               [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then
                            aligned for the instruction footprint. This is not an L1 byte address.
  Note: SrcA uses an aligned 16 x 16 footprint. SrcB begins at an eight-row boundary. GAPOOL reads four SrcB rows;
        GMPOOL uses one row for exponent scaling (the tests use B=1).
  Note: The allocator reserves a 128-element Dst slot even though these instructions write fewer rows. Do not assume the
        unused rows are overwritten."""
  return tensix('GMPOOL', clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst)

def INCADCXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0):
  """0x52. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  CntSetMask [23:21]
  Ch1_Y [20:15]
  Ch1_X [14:12]
  Ch0_Y [11:9]
  Ch0_X [8:6]"""
  return tensix('INCADCXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X)

def INCADCZW(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0):
  """0x55. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  CntSetMask [23:21]
  Ch1_Y [20:15]
  Ch1_X [14:12]
  Ch0_Y [11:9]
  Ch0_X [8:6]"""
  return tensix('INCADCZW', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X)

def INCRWC(rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0):
  """Increment math read/write counters (Addressing, 0x38). Advance SrcA, SrcB and Dst read/write counters without issuing
  arithmetic.

  rwc_cr [23:18] 1 increments SrcA carry/reset then copies to SrcA; 2 similarly for SrcB; 4 similarly for Dst. With a
                 bit clear only the running counter advances. Keep unsupported high bits zero.
  rwc_d  [17:14] Unsigned four-bit Dst increment.
  rwc_b  [13:10] Unsigned four-bit SrcB increment.
  rwc_a  [9:6]   Unsigned four-bit SrcA increment.
  Note: Llama uses TTINCRWC(0, 2, 0, 0) to advance the Dst selection between even/odd vector chunks. This is a row-
        address counter operation, not a byte-pointer increment."""
  return tensix('INCRWC', rwc_cr, rwc_d, rwc_b, rwc_a)

def LOADIND(SizeSel=0, OffsetIndex=0, AutoIncSpec=0, DataRegIndex=0, AddrRegIndex=0):
  """0x49. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  SizeSel [23:22]
  OffsetIndex [21:14]
  AutoIncSpec [13:12]
  DataRegIndex [11:6]
  AddrRegIndex [5:0]"""
  return tensix('LOADIND', SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex)

def LOADREG(TdmaDataRegIndex=0, RegAddr=0):
  """0x68. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  TdmaDataRegIndex [23:18]
  RegAddr [17:0]"""
  return tensix('LOADREG', TdmaDataRegIndex, RegAddr)

def MFCONV3S1(clear_dvalid=0, rotate_weights=0, addr_mode=0, dst=0):
  """0x3A. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  rotate_weights [21:17]
  addr_mode [16:14]
  dst [13:0]"""
  return tensix('MFCONV3S1', clear_dvalid, rotate_weights, addr_mode, dst)

def MOP(mop_type=0, loop_count=0, zmask_lo16_or_loop_count=0):
  """Execute a configured macro-op (Control, 0x01). Expand a configured macro-op template into ordinary Tensix
  instructions.

  mop_type                 [23]    Template selector: 0 uses instruction count/mask fields with configuration; 1 takes
                                   the loop structure from configuration.
  loop_count               [22:16] Template-0 Count1 field; ignored by the template-1 repository usage.
  zmask_lo16_or_loop_count [15:0]  Template-0 low zero-mask/count payload, depending on template configuration. Ordinary
                                   template-1 calls pass zero.
  Note: The repository programs template words first, then executes TTMOP(1, 0, 0). MOP, REPLAY and SFPLOADMACRO are
        three different mechanisms."""
  return tensix('MOP', mop_type, loop_count, zmask_lo16_or_loop_count)

def MOP_CFG(zmask_hi16=0):
  """0x03. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  zmask_hi16 [23:0]"""
  return tensix('MOP_CFG', zmask_hi16)

def MOVA2D(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move SrcA to Dst (FPU, 0x12). Transfer rows from SrcA into Dst, with format handling determined by the math
  configuration.

  dest_32b_lo [23]    Low-half Dst write selector. Keep 0 for the normal FP32 path. UseDst32bLo with a TF32-style move
                      can corrupt data on Blackhole (TEN-4245).
  src         [22:17] SrcA row offset added to its RWC.
  addr_mode   [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                      byte stride. The Python bit field is wider than the semantic selector; do not assume every
                      encodable value is valid.
  instr_mod   [13:12] 0 moves one row; 2 moves an aligned eight-row block.
  dst         [11:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned for
                      the instruction footprint. This is not an L1 byte address.
  Note: Blackhole FP32 accumulation causes source-to-Dst moves to write FP32 Dst values. Wait before consuming the
        affected Dst rows with SFPU."""
  return tensix('MOVA2D', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVB2A(srca=0, addr_mode=0, instr_mod=0, srcb=0):
  """Move SrcB to SrcA (FPU, 0x0B). Copy one row or an aligned four-row block from SrcB to SrcA.

  srca      [23:17] SrcA destination row offset added to its RWC.
  addr_mode [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a byte
                    stride. The Python bit field is wider than the semantic selector; do not assume every encodable
                    value is valid.
  instr_mod [13:12] 0 moves one row; 2 moves four rows aligned to multiples of four.
  srcb      [11:0]  SrcB source row offset added to its RWC.
  Note: Automatically waits for SrcB ownership, but does not automatically wait for SrcA ownership."""
  return tensix('MOVB2A', srca, addr_mode, instr_mod, srcb)

def MOVB2D(dest_32b_lo=0, src=0, addr_mode=0, movb2d_instr_mod=0, dst=0):
  """Move SrcB to Dst (FPU, 0x13). Transfer rows from SrcB into Dst, with format handling determined by the math
  configuration.

  dest_32b_lo      [23]    Low-half Dst write selector. Keep 0 for the normal FP32 path. UseDst32bLo with a TF32-style
                           move can corrupt data on Blackhole (TEN-4245).
  src              [22:17] SrcB row offset added to its RWC.
  addr_mode        [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not
                           a byte stride. The Python bit field is wider than the semantic selector; do not assume every
                           encodable value is valid.
  movb2d_instr_mod [13:11] Bit flags: 1 broadcasts column 0; 2 broadcasts one row to eight Dst rows; 4 moves an aligned
                           four-row block.
  dst              [10:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned
                           for the instruction footprint. This is not an L1 byte address.
  Note: Blackhole FP32 accumulation causes source-to-Dst moves to write FP32 Dst values. Wait before consuming the
        affected Dst rows with SFPU."""
  return tensix('MOVB2D', dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst)

def MOVD2A(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move Dst to SrcA (FPU, 0x08). Move one row or an aligned four-row block from Dst to SrcA, with configured format
  conversion.

  dest_32b_lo [23]    Select the low half of a 32-bit Dst datum before conversion; normally zero.
  src         [22:17] SrcA destination row offset added to its RWC.
  addr_mode   [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                      byte stride. The Python bit field is wider than the semantic selector; do not assume every
                      encodable value is valid.
  instr_mod   [13:12] 0 moves one row; 2 moves four rows, rounding both row addresses down to multiples of four.
  dst         [11:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned for
                      the instruction footprint. This is not an L1 byte address.
  Note: Dst is the source despite the Python dst argument name. Src row is the destination.
  Note: MOVD2B uses the SrcA format configuration to derive SrcB style; the shared manual explicitly calls out this
        behavior."""
  return tensix('MOVD2A', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVD2B(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move Dst to SrcB (FPU, 0x0A). Move one row or an aligned four-row block from Dst to SrcB, with configured format
  conversion.

  dest_32b_lo [23]    Select the low half of a 32-bit Dst datum before conversion; normally zero.
  src         [22:17] SrcB destination row offset added to its RWC.
  addr_mode   [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                      byte stride. The Python bit field is wider than the semantic selector; do not assume every
                      encodable value is valid.
  instr_mod   [13:12] 0 moves one row; 2 moves four rows, rounding both row addresses down to multiples of four.
  dst         [11:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned for
                      the instruction footprint. This is not an L1 byte address.
  Note: Dst is the source despite the Python dst argument name. Src row is the destination.
  Note: MOVD2B uses the SrcA format configuration to derive SrcB style; the shared manual explicitly calls out this
        behavior."""
  return tensix('MOVD2B', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVDBGA2D(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """0x09. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  dest_32b_lo [23]
  src [22:17]
  addr_mode [16:14]
  instr_mod [13:12]
  dst [11:0]"""
  return tensix('MOVDBGA2D', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVDBGB2D(dest_32b_lo=0, src=0, addr_mode=0, movb2d_instr_mod=0, dst=0):
  """0x0C. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  dest_32b_lo [23]
  src [22:17]
  addr_mode [16:14]
  movb2d_instr_mod [13:11]
  dst [10:0]"""
  return tensix('MOVDBGB2D', dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst)

def MPOOL3S1(clear_dvalid=0, pool_addr_mode=0, index_en=0, dst=0):
  """0x24. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  pool_addr_mode [21:15]
  index_en [14]
  dst [13:0]"""
  return tensix('MPOOL3S1', clear_dvalid, pool_addr_mode, index_en, dst)

def MPOOL3S2(clear_dvalid=0, pool_addr_mode=0, index_en=0, dst=0):
  """0x31. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  clear_dvalid [23:22]
  pool_addr_mode [21:15]
  index_en [14]
  dst [13:0]"""
  return tensix('MPOOL3S2', clear_dvalid, pool_addr_mode, index_en, dst)

def MULDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x5A. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  ResultRegIndex [22:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('MULDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def MVMUL(clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0):
  """Matrix multiply-accumulate (FPU, 0x26). Compute Dst[8 x 16] += SrcB[8 x 16] @ SrcA[16 x 16]. A full 32 x 32 tile
  operation is a sequence of these instructions.

  clear_dvalid [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                       consumed bank back to the unpacker unless clearing is disabled in configuration.
  instr_mod19  [21:19] Normal mode is 0. The documented low-bit mode broadcasts one SrcB row to alternating output rows;
                       this is not ordinary eight-row broadcast.
  addr_mode    [18:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not a
                       byte stride. The Python bit field is wider than the semantic selector; do not assume every
                       encodable value is valid.
  dst          [13:0]  Dst row offset added to the math target offset, Dst RWC and configured Dst base, then aligned for
                       the instruction footprint. This is not an L1 byte address.
  Note: Always accumulates. Initialize Dst first if an assignment is intended. Multipliers consume partial mantissas;
        choose and schedule the required fidelity phases.
  Note: The retained Blackhole FPU test report observes that SrcA starts round down to an even 128-element slot. Use
        aligned 16-row A pairs. This is stricter than the current shared manual's A-row mask;
        tests/compute/fpu/README.md records the discrepancy."""
  return tensix('MVMUL', clear_dvalid, instr_mod19, addr_mode, dst)

def NOP():
  """Tensix no operation (Control, 0x02). Issue a frontend no-op, useful as a harmless instruction in MOP/replay templates
  or as spacing.

  Note: TTNOP, TTSFPNOP and TTDMANOP target different instruction paths. None is a universal completion barrier."""
  return tensix('NOP')

def PACR(*args, **fields):
  """Pack Dst into L1 (Unpack / pack, 0x41). Issue work to the configured packers, converting Dst values to an output
  format and writing the result to L1.

  CfgContext     [23:21] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not
                         an independent supported operand in the reference syntax.
  RowPadZero     [20:18] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not
                         an independent supported operand in the reference syntax.
  DstAccessMode  [17]    Keep zero for the documented operation. The Python encoder exposes these bits, but they are not
                         an independent supported operand in the reference syntax.
  AddrMode       [16:15] Select a configured packer ADC address-modifier slot (0-3) for the following pack operation.
  AddrCntContext [14:13] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not
                         an independent supported operand in the reference syntax.
  ZeroWrite      [12]    1 uses zero input instead of reading Dst.
  ReadIntfSel    [11:8]  Packer mask: 0 or 1 selects packer 0; 2, 4, 8 select one other packer; 3 selects 0+1; 12
                         selects 2+3; 15 selects all. Other combinations are not generally supported.
  OvrdThreadId   [7]     Overrides the ADC thread selection; leave 0 for the ordinary current-thread path.
  Concat         [6:4]   Compression-row continuation control. Only the documented Concat bit is meaningful; normal
                         uncompressed packing uses 0.
  CtxtCtrl       [3:2]   Keep zero for the documented operation. The Python encoder exposes these bits, but they are not
                         an independent supported operand in the reference syntax.
  Flush          [1]     Flush output buffers without fetching new input datums; reset output-address state for the next
                         command.
  Last           [0]     Flush the output after this pack and start fresh output addresses on the next PACR.
  Note: Output address, format, count, strides, activation and rounding come from configuration and ADC state, not these
        instruction arguments.
  Note: Several legacy fields in the Python signature are absent from the shared public syntax. Repository calls keep
        them zero. Do not infer supported padding or context functionality from their names.
  Note: The Last bit finalizes the packer stream; it is not a cross-unit memory barrier. Use the repository's completion
        synchronization before publishing or reusing buffers."""
  return tensix('PACR', *args, **fields)

def PACR_SETREG(Push=0, ModeSel=0, Unused=0, DisableStall=0, AddrSel=0, StreamId=0, Flush=0, Last=0):
  """0x4A. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  Push [23]
  ModeSel [22]
  Unused [21:12]
  DisableStall [11:10]
  AddrSel [9:8]
  StreamId [7:2]
  Flush [1]
  Last [0]"""
  return tensix('PACR_SETREG', Push, ModeSel, Unused, DisableStall, AddrSel, StreamId, Flush, Last)

def RAREB():
  """0x15. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile."""
  return tensix('RAREB')

def RDCFG(GprAddress=0, CfgReg=0):
  """Read backend configuration into a GPR (Control, 0xB1). Copy a backend configuration value into a Tensix GPR.

  GprAddress [23:16] Destination Tensix GPR index.
  CfgReg     [15:0]  Backend configuration word index, not a byte address."""
  return tensix('RDCFG', GprAddress, CfgReg)

def REG2FLOP(SizeSel=0, TargetSel=0, ByteOffset=0, ContextId_2=0, FlopIndex=0, RegIndex=0):
  """0x48. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  SizeSel [23:22]
  TargetSel [21:20]
  ByteOffset [19:18]
  ContextId_2 [17:16]
  FlopIndex [15:6]
  RegIndex [5:0]"""
  return tensix('REG2FLOP', SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex)

def REPLAY(start_idx=0, len=0, execute_while_loading=0, load_mode=0):
  """Record or replay instructions (Control, 0x04). Store a sequence in the thread's replay buffer, optionally executing
  while recording, or expand a previously recorded sequence.

  start_idx             [23:14] First replay-buffer slot. The Python encoder exposes ten bits; actual buffer capacity is
                                architecture-specific.
  len                   [13:4]  Number of instructions to record or replay. This is a sequence length, not a repeat
                                count.
  execute_while_loading [3:1]   0 records without execution; 1 also executes during recording. Other values in the wider
                                encoder field are not documented ordinary modes.
  load_mode             [0]     1 records incoming instructions; 0 replays stored instructions.
  Note: Recording consumes the next len Tensix words. A later replay expands the stored words once; repetition comes
        from a MOP or software loop.
  Note: The available shared manual describes the Wormhole buffer size and field widths. Do not carry its 32-slot
        capacity or count-zero behavior over to Blackhole. Use the Blackhole replay helper limits and the retained
        replay_fifo_probe when exploring capacity."""
  return tensix('REPLAY', start_idx, len, execute_while_loading, load_mode)

def RESOURCEDECL(linger_time=0, resources=0, op_class=0):
  """0x05. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  linger_time [23:13]
  resources [12:4]
  op_class [3:0]"""
  return tensix('RESOURCEDECL', linger_time, resources, op_class)

def RMWCIB0(Mask=0, Data=0, CfgRegAddr=0):
  """Update configuration byte 0 (Control, 0xB3). Read-modify-write byte 0 of a backend configuration register using an
  immediate mask and data.

  Mask       [23:16] Eight-bit update mask for the selected byte; 1 bits select the bits to change.
  Data       [15:8]  New bits for the selected byte. Use values consistent with the mask.
  CfgRegAddr [7:0]   Backend configuration register index in the byte-immediate instruction's addressable range.
  Note: These four opcodes choose which byte is changed. They do not take an additional byte-selector argument."""
  return tensix('RMWCIB0', Mask, Data, CfgRegAddr)

def RMWCIB1(Mask=0, Data=0, CfgRegAddr=0):
  """Update configuration byte 1 (Control, 0xB4). Read-modify-write byte 1 of a backend configuration register using an
  immediate mask and data.

  Mask       [23:16] Eight-bit update mask for the selected byte; 1 bits select the bits to change.
  Data       [15:8]  New bits for the selected byte. Use values consistent with the mask.
  CfgRegAddr [7:0]   Backend configuration register index in the byte-immediate instruction's addressable range.
  Note: These four opcodes choose which byte is changed. They do not take an additional byte-selector argument."""
  return tensix('RMWCIB1', Mask, Data, CfgRegAddr)

def RMWCIB2(Mask=0, Data=0, CfgRegAddr=0):
  """Update configuration byte 2 (Control, 0xB5). Read-modify-write byte 2 of a backend configuration register using an
  immediate mask and data.

  Mask       [23:16] Eight-bit update mask for the selected byte; 1 bits select the bits to change.
  Data       [15:8]  New bits for the selected byte. Use values consistent with the mask.
  CfgRegAddr [7:0]   Backend configuration register index in the byte-immediate instruction's addressable range.
  Note: These four opcodes choose which byte is changed. They do not take an additional byte-selector argument."""
  return tensix('RMWCIB2', Mask, Data, CfgRegAddr)

def RMWCIB3(Mask=0, Data=0, CfgRegAddr=0):
  """Update configuration byte 3 (Control, 0xB6). Read-modify-write byte 3 of a backend configuration register using an
  immediate mask and data.

  Mask       [23:16] Eight-bit update mask for the selected byte; 1 bits select the bits to change.
  Data       [15:8]  New bits for the selected byte. Use values consistent with the mask.
  CfgRegAddr [7:0]   Backend configuration register index in the byte-immediate instruction's addressable range.
  Note: These four opcodes choose which byte is changed. They do not take an additional byte-selector argument."""
  return tensix('RMWCIB3', Mask, Data, CfgRegAddr)

def RSTDMA():
  """0x44. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile."""
  return tensix('RSTDMA')

def SEMGET(sem_sel=0):
  """Decrement semaphore values (Control, 0xA5). Decrement each selected Tensix semaphore value.

  sem_sel [23:2]  Semaphore bitmask, not index: use 1 << semaphore_number. The architecture has eight semaphore
                  selectors despite the wider Python field.
  Note: Use SEMWAIT to test availability separately. Do not assume the GET/POST name implies a blocking wait or source-
        bank transfer."""
  return tensix('SEMGET', sem_sel)

def SEMINIT(max_value=0, init_value=0, sem_sel=0):
  """Initialize semaphores (Control, 0xA3). Set the maximum and initial value of selected Tensix semaphores.

  max_value  [23:20] Maximum semaphore value (four bits).
  init_value [19:16] Initial semaphore value (four bits); choose a value within the configured maximum.
  sem_sel    [15:2]  Semaphore bitmask, not an index.
  Note: Included as supporting reference even when initialization is emitted through other setup mechanisms."""
  return tensix('SEMINIT', max_value, init_value, sem_sel)

def SEMPOST(sem_sel=0):
  """Increment semaphore values (Control, 0xA4). Increment each selected Tensix semaphore value.

  sem_sel [23:2]  Semaphore bitmask, not index: use 1 << semaphore_number. The architecture has eight semaphore
                  selectors despite the wider Python field.
  Note: Use SEMWAIT to test availability separately. Do not assume the GET/POST name implies a blocking wait or source-
        bank transfer."""
  return tensix('SEMPOST', sem_sel)

def SEMWAIT(stall_res=0, sem_sel=0, wait_sem_cond=0):
  """Wait on semaphore conditions (Control, 0xA6). Block selected instruction classes while selected semaphores are empty
  and/or full.

  stall_res     [23:15] Same instruction-class block mask as Blackhole STALLWAIT.
  sem_sel       [14:2]  Semaphore bitmask: 1 << semaphore_number, or OR several bits.
  wait_sem_cond [1:0]   1 waits while any selected semaphore is zero; 2 waits while any selected semaphore is at its
                        maximum; 3 requires neither empty nor full. Zero is not a valid wait condition.
  Note: This does not increment or decrement the semaphore. Combine it with GET or POST as required by the ownership
        protocol."""
  return tensix('SEMWAIT', stall_res, sem_sel, wait_sem_cond)

def SETADC(CntSetMask=0, ChannelIndex=0, DimensionIndex=0, Value=0):
  """Set an address counter (Addressing, 0x50). Assign one selected X/Y/Z/W counter and its carry/reset value for the
  chosen unit(s).

  CntSetMask     [23:21] Unit mask: 1 unpacker 0, 2 unpacker 1, 4 packers; OR bits to update multiple units.
  ChannelIndex   [20]    Address-generator channel: 0 or 1.
  DimensionIndex [19:18] Dimension selector: 0 X, 1 Y, 2 Z, 3 W.
  Value          [17:0]  New counter value. The high bits can encode a thread override; ordinary use keeps those zero.
  Note: Counter units depend on the configured address generator. They are not universally bytes: packer Y/Z/W can
        address rows, faces and tiles."""
  return tensix('SETADC', CntSetMask, ChannelIndex, DimensionIndex, Value)

def SETADCXX(CntSetMask=0, x_end2=0, x_start=0):
  """Set both X counters (Addressing, 0x5E). Set channel 0 X and channel 1 X for selected unpackers or packers.

  CntSetMask [23:21] Unit mask: 1 unpacker 0, 2 unpacker 1, 4 packers; OR bits to update multiple units.
  x_end2     [20:10] Channel 1 X. In the repository's regular unpack/pack setup this is the inclusive end (element count
                     minus one). The semantic value is 10 bits despite the wider Python field.
  x_start    [9:0]   Channel 0 X start value (10 bits).
  Note: For 16 datums starting at zero, the repository uses x_end2=15 and x_start=0. Both counters' carry/reset copies
        are updated."""
  return tensix('SETADCXX', CntSetMask, x_end2, x_start)

def SETADCXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=0):
  """Set X/Y address counters (Addressing, 0x51). Assign selected channel 0 and 1 X/Y counters and their carry/reset
  copies.

  CntSetMask [23:21] Unit mask: 1 unpacker 0, 2 unpacker 1, 4 packers; OR bits to update multiple units.
  Ch1_Y      [20:15] New channel 1 Y value; documented semantic value is three bits. Upper encoder bits are not ordinary
                     counter payload.
  Ch1_X      [14:12] New channel 1 X value (three bits).
  Ch0_Y      [11:9]  New channel 0 Y value (three bits).
  Ch0_X      [8:6]   New channel 0 X value (three bits).
  BitMask    [5:0]   Update mask: 1 Ch0 X, 2 Ch0 Y, 4 Ch1 X, 8 Ch1 Y; 15 updates all four. Upper encoder bits are not
                     ordinary mask bits."""
  return tensix('SETADCXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask)

def SETADCZW(CntSetMask=0, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=0):
  """Set Z/W address counters (Addressing, 0x54). Assign selected channel 0 and 1 Z/W counters and their carry/reset
  copies.

  CntSetMask [23:21] Unit mask: 1 unpacker 0, 2 unpacker 1, 4 packers; OR bits to update multiple units.
  Ch1_W      [20:15] New channel 1 W value; documented semantic value is three bits. Upper encoder bits are not ordinary
                     counter payload.
  Ch1_Z      [14:12] New channel 1 Z value (three bits).
  Ch0_W      [11:9]  New channel 0 W value (three bits).
  Ch0_Z      [8:6]   New channel 0 Z value (three bits).
  BitMask    [5:0]   Update mask: 1 Ch0 Z, 2 Ch0 W, 4 Ch1 Z, 8 Ch1 W; 15 updates all four. Upper encoder bits are not
                     ordinary mask bits."""
  return tensix('SETADCZW', CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask)

def SETASHRMH(reg_mask=0, halo_mask=0):
  """0x1E. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  reg_mask [23:1]
  halo_mask [0]"""
  return tensix('SETASHRMH', reg_mask, halo_mask)

def SETASHRMH0(reg_mask=0, halo_mask=0):
  """0x1A. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  reg_mask [23:1]
  halo_mask [0]"""
  return tensix('SETASHRMH0', reg_mask, halo_mask)

def SETASHRMH1(reg_mask=0, halo_mask=0):
  """0x1B. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  reg_mask [23:1]
  halo_mask [0]"""
  return tensix('SETASHRMH1', reg_mask, halo_mask)

def SETASHRMV(reg_mask2=0):
  """0x1C. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  reg_mask2 [23:0]"""
  return tensix('SETASHRMV', reg_mask2)

def SETC16(setc16_reg=0, setc16_value=0):
  """Write thread configuration (Control, 0xB2). Write a 16-bit immediate to a thread configuration register.

  setc16_reg   [23:16] Thread-configuration register index, not its byte MMIO address.
  setc16_value [15:0]  16-bit immediate configuration value.
  Note: SETC16 targets thread configuration. WRCFG and RMWCIB operate on a different configuration address space. The
        same integer index does not mean the same register across these instructions."""
  return tensix('SETC16', setc16_reg, setc16_value)

def SETDMAREG(Payload_SigSelSize=0, Payload_SigSel=0, SetSignalsMode=0, RegIndex16b=0):
  """Set a Tensix GPR half-word (Control, 0x45). Write 16 immediate bits into one half of a Tensix GPR, preserving the
  other half.

  Payload_SigSelSize [23:22] For immediate writes, this field carries the high two payload bits in the legacy split
                             encoding. Zero with a small immediate.
  Payload_SigSel     [21:8]  Low 14 bits of the immediate payload. The complete immediate spans encoder bits 23:8
                             together with Payload_SigSelSize.
  SetSignalsMode     [7]     0 selects immediate half-register writes. Special signal reads use a different command
                             mode.
  RegIndex16b        [6:0]   Half-register index: even selects low 16 bits, odd selects high 16 bits of GPR[index // 2].
  Note: This is the scalar Tensix GPR file, not the SFPU LRegs and not RV32 registers. The repository can fill the
        immediate field dynamically by combining a base word with shifted bits."""
  return tensix('SETDMAREG', Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b)

def SETDVALID(setvalid=0):
  """0x57. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  setvalid [23:0]"""
  return tensix('SETDVALID', setvalid)

def SETIBRWC(rwc_cr=0, rwc_bias=0, set_inc_ctrl=0):
  """0x39. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  rwc_cr [23:18]
  rwc_bias [17:6]
  set_inc_ctrl [5:0]"""
  return tensix('SETIBRWC', rwc_cr, rwc_bias, set_inc_ctrl)

def SETPKEDGOF(y_end=0, y_start=0, x_end=0, x_start=0):
  """0x1D. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  y_end [23:12]
  y_start [11:8]
  x_end [7:4]
  x_start [3:0]"""
  return tensix('SETPKEDGOF', y_end, y_start, x_end, x_start)

def SETRWC(clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=0):
  """Set math read/write counters (Addressing, 0x37). Set selected SrcA, SrcB and Dst counters, optionally reset fidelity,
  and optionally release source banks.

  clear_ab_vld [23:22] Source-bank release mask: 0 keeps both, 1 flips/releases SrcA, 2 SrcB, 3 both. Release hands the
                       consumed bank back to the unpacker unless clearing is disabled in configuration.
  rwc_cr       [21:18] Carry/reset controls: 1 SrcA, 2 SrcB, 4 Dst; 8 adds the current Dst counter rather than its
                       carry/reset copy when setting Dst.
  rwc_d        [17:14] New Dst counter contribution (four bits).
  rwc_b        [13:10] New SrcB counter contribution (four bits).
  rwc_a        [9:6]   New SrcA counter contribution (four bits).
  BitMask      [5:0]   Update mask: 1 SrcA, 2 SrcB, 4 Dst, 8 reset fidelity to zero. 15 resets all with zero counter
                       operands.
  Note: rwc_cr changes whether values are relative to saved carry/reset counters. BitMask determines which counters
        actually change. Zero-valued arguments do not reset a counter whose mask bit is clear."""
  return tensix('SETRWC', clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask)

def SFPABS(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Vector absolute value (SFPU, 0x7D). Take the lanewise absolute value of two’s-complement integers or FP32 values.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 selects two’s-complement integer absolute value; 1 selects FP32.
  Note: FP32 negative NaNs retain their sign. Integer -2147483648 is unchanged."""
  return tensix('SFPABS', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPADD(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Floating-point add or subtract (SFPU, 0x85). Compute VD = B + C using the MAD datapath with A fixed to L10 (1.0).

  lreg_src_a [23:16] A register index. For SFPADD use L10, the 1.0 constant; ordinary register indices are four bits
                     despite this eight-bit encoder field.
  lreg_src_b [15:12] B register index.
  lreg_src_c [11:8]  C register index. For SFPMUL use L9, the 0.0 constant.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Blackhole flags: 1 negates A, 2 negates C, 4 takes A index from L7 low four bits, 8 takes
                     destination index from L7. Combine flags with bitwise OR; 0 is ordinary arithmetic.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP.
  Note: Multiply-add is partially fused, not an exact IEEE fused multiply-add. Denormal inputs are treated as zero and
        denormal outputs flush to signed zero; Blackhole uses round-to-nearest, ties-to-even."""
  return tensix('SFPADD', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPADDI(imm16_math=0, lreg_dest=0, instr_mod1=0):
  """Floating-point add with an immediate (SFPU, 0x75). Convert a BF16 immediate to FP32 and add it with the old
  destination in each active lane.

  imm16_math [23:8]  BF16 immediate bit pattern, widened to FP32 by shifting left 16 bits. Not an integer numerical
                     value.
  lreg_dest  [7:4]   LReg index used as both input and output.
  instr_mod1 [3:0]   Blackhole flags: 1 negates A, 2 negates C, 4 takes A index from L7 low four bits, 8 takes
                     destination index from L7. Combine flags with bitwise OR; 0 is ordinary arithmetic.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP."""
  return tensix('SFPADDI', imm16_math, lreg_dest, instr_mod1)

def SFPAND(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Vector bitwise AND (SFPU, 0x7E). Apply bitwise AND to each pair of 32-bit lanes.

  imm12_math [23:12] Blackhole VB selector occupies the low four bits of this raw 12-bit encoder field; keep the upper
                     bits zero.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Bit 0 selects VB as the first input. When clear, the destination register is also the first input.
  Note: VB selection is a Blackhole extension; the Wormhole two-input form always reuses VD."""
  return tensix('SFPAND', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPARECIP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Approximate reciprocal or exponential (SFPU, 0x99). Compute a Blackhole hardware reciprocal or restricted-range
  exponential estimate in each active lane.

  imm12_math [23:12] VB register index for conditional reciprocal; its signed integer sign decides whether to apply the
                     reciprocal. Zero is sufficient in unconditional mode.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 reciprocal with sign preserved; 1 conditional reciprocal of the magnitude when VB is negative; 2
                     approximate exponential of the magnitude with the original sign reattached.
  Note: An estimate is a building block for refinement, not full-accuracy division. The reciprocal estimate of 1.0 is
        0.99609375.
  Note: Exponential mode is useful for input magnitudes below 2. For negative inputs it returns a negative estimate of
        exp(abs(x)), not exp(x); a subsequent conditional reciprocal can be part of a composed exp sequence."""
  return tensix('SFPARECIP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPCAST(lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Convert integer representations (SFPU, 0x90). Convert sign-magnitude integers to FP32, convert between integer
  representations, or take integer absolute values.

  lreg_src_c [23:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 converts sign-magnitude int32 to FP32 with nearest-even rounding; 1 uses stochastic rounding; 2
                     computes two's-complement absolute value (prefer SFPABS); 3 converts between two's-complement and
                     sign-magnitude.
  Note: Some integer paths use sign-magnitude, others two's complement. A register bit-copy is not a numerical cast."""
  return tensix('SFPCAST', lreg_src_c, lreg_dest, instr_mod1)

def SFPCOMPC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x8B. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPCOMPC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPCONFIG(imm16_math=0, config_dest=0, instr_mod1=0):
  """Configure SFPU lanes and load macros (SFPU, 0x91). Write SFPU constant registers, lane configuration, instruction
  templates or load-macro sequences.

  imm16_math  [23:8]  Immediate value when modifier bit 0 is set, otherwise input normally comes from the first eight
                      lanes of L0. With modifier bit 3 this supplies a lane mask.
  config_dest [7:4]   0-3 instruction templates; 4-7 sequences; 8 miscellaneous macro control; 9 PRNG state; 11-14
                      programmable constants; 15 lane configuration. Consult the reference for destination-specific
                      handling.
  instr_mod1  [3:0]   1 selects immediate input; 2 ORs, 4 ANDs, 6 XORs where supported; 8 applies the immediate lane
                      mask. Templates require L0 because the instruction is 32 bits.
  Note: Configuration input is sampled from the first eight lanes and replicated across four lane groups. Destination
        selection changes which operations and immediate forms are legal.
  Note: Llama records an arithmetic instruction with destination CONFIG0, then sets sequence 0 with config_dest=4 and
        miscellaneous control with config_dest=8."""
  return tensix('SFPCONFIG', imm16_math, config_dest, instr_mod1)

def SFPDIVP2(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x76. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPDIVP2', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPENCC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Enable or reset lane predication (SFPU, 0x8A). Control whether per-lane flags gate subsequent SFPU instructions, and
  reset the flags.

  imm12_math [23:12] Low bit selects whether lane flags are used for enable; bit 1 supplies a new flag value when
                     requested by Mod1.
  lreg_c     [11:8]  Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_dest  [7:4]   Normally zero; only relevant to backdoor instruction recording.
  instr_mod1 [3:0]   1 toggles predicate use; 2 assigns predicate use from immediate bit 0; 8 assigns flags from
                     immediate bit 1. If 8 is absent, flags become true.
  Note: This configures predication, not a floating-point comparison. Restore all-lane behavior explicitly after a
        predicated region."""
  return tensix('SFPENCC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPEXEXP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Extract a floating-point exponent (SFPU, 0x77). Extract the FP32 exponent bits into an integer vector, optionally
  removing the exponent bias.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 extracts exponent minus 127; OR 1 to keep the bias; OR 2 to set flags from the result sign; OR 8
                     to invert that condition.
  Note: This manipulates the representation rather than evaluating log, exp or a general transcendental function. Exact
        modifiers are listed in the source reference."""
  return tensix('SFPEXEXP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPEXMAN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Extract a floating-point mantissa (SFPU, 0x78). Extract the low 23 mantissa bits into an integer, optionally setting
  bit 23 to represent the hidden leading bit.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 includes a 1 in bit 23 (hidden leading bit); 1 leaves bit 23 zero. The upper eight output bits
                     are zero.
  Note: This manipulates the representation rather than evaluating log, exp or a general transcendental function. Exact
        modifiers are listed in the source reference."""
  return tensix('SFPEXMAN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPGT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x97. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPGT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPIADD(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Integer add or subtract (SFPU, 0x79). Perform 32-bit integer arithmetic on register bit patterns, optionally updating
  per-lane condition flags.

  imm12_math [23:12] Signed 12-bit immediate encoded as value & 0xfff, used when modifier bit 0 is set.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination and, in register mode, the second source operand. Subtraction is VC - old VD.
  instr_mod1 [3:0]   1 selects immediate addition; 2 selects VC - VD; otherwise VC + VD. OR 4 to preserve condition
                     flags. Without 4, flags reflect a negative result; 8 inverts the condition.
  Note: Llama uses modifier 6 (2 | 4) to subtract the shifted FP32 bit pattern from an inverse-square-root seed without
        changing lane flags.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP."""
  return tensix('SFPIADD', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPLE(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x96. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPLE', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPLOAD(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Load Dst into a vector register (SFPU, 0x70). Read up to 32 values from Dst into one SFPU register, converting from
  the selected Dst storage format.

  lreg_ind       [23:20] Destination LReg index. Loads write L0-L7.
  instr_mod0     [19:16] Transfer format: 0 follows configured format, 1 FP16, 2 BF16, 3 FP32. Integer and partial-word
                         modes have distinct meanings; see the mode constants and ISA reference. This is not the same
                         mode numbering as SFPLOADI.
  sfpu_addr_mode [15:13] Raw SFPU address-modifier field, applied after the transfer. It advances SrcA/SrcB/Dst
                         counters, not fidelity. Llama uses 7 with its configured counters. Do not interpret this as a
                         byte increment.
  dest_reg_addr  [12:0]  Dst address immediate plus configured offsets and RWCs. For normal addressing, the effective
                         low 10 bits select four rows (bits 9:2) and even/odd columns (bit 1); bit 0 is unused. Keep
                         reserved upper bits zero.
  Note: One vector covers even or odd columns of four consecutive 16-column Dst rows. Lane n reads row (address & ~3) +
        n//8 and column 2*(n%8), plus the odd-column selection. Lane configuration can block or exchange columns.
  Note: An FPU write to the same Dst region needs at least three unrelated Tensix instructions before SFPLOAD. ZEROACC
        alone does not establish valid values for an SFPU load."""
  return tensix('SFPLOAD', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPLOADI(lreg_ind=0, instr_mod0=0, imm16=0):
  """Load an immediate into a vector register (SFPU, 0x71). Broadcast a 16-bit immediate to active lanes, either converting
  it to 32 bits or replacing half of each register value.

  lreg_ind   [23:20] Destination register L0-L7.
  instr_mod0 [19:16] 0: BF16 bits shifted into the high half; 1: FP16-like conversion; 2: zero-extended uint16; 4: sign-
                     extended int16; 8: replace upper 16 bits; 10: replace lower 16 bits.
  imm16      [15:0]  16-bit bit pattern, not a Python float. Modes 8 and 10 preserve the opposite half.
  Note: Llama installs exact FP32 constants with LOWER (10) followed by UPPER (8). For pi, the two immediates are 0x0fdb
        and 0x4049. Both writes obey lane predication."""
  return tensix('SFPLOADI', lreg_ind, instr_mod0, imm16)

def SFPLOADMACRO(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Load and launch an SFPU sequence (SFPU, 0x93). Perform a Dst load and schedule preconfigured simple, MAD, round and
  store operations behind it.

  lreg_ind       [23:20] Packed selector: high two bits select macro sequence 0-3; low two bits supply the low
                         destination-register bits.
  instr_mod0     [19:16] Transfer format: 0 follows configured format, 1 FP16, 2 BF16, 3 FP32. Integer and partial-word
                         modes have distinct meanings; see the mode constants and ISA reference. This is not the same
                         mode numbering as SFPLOADI.
  sfpu_addr_mode [15:13] Raw SFPU address-modifier field, applied after the transfer. It advances SrcA/SrcB/Dst
                         counters, not fidelity. Llama uses 7 with its configured counters. Do not interpret this as a
                         byte increment.
  dest_reg_addr  [12:0]  Load address field. Its low bit participates in the macro destination selection; other address
                         bits follow the load encoding. Use the SFPLOADMACRO-specific syntax, not an arbitrary SFPLOAD
                         address.
  Note: Requires prior template, sequence and delay configuration. It can overlap SFPU subunits, unlike issuing one
        ordinary instruction per cycle.
  Note: Automatic dependency stalls do not protect instructions inside a macro. Program delays explicitly, including the
        two-cycle MAD result dependency."""
  return tensix('SFPLOADMACRO', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPLUT(lreg_ind=0, instr_mod0=0, dest_reg_addr=0):
  """0x73. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  lreg_ind [23:20]
  instr_mod0 [19:16]
  dest_reg_addr [15:0]"""
  return tensix('SFPLUT', lreg_ind, instr_mod0, dest_reg_addr)

def SFPLUTFP32(lreg_dest=0, instr_mod1=0):
  """0x95. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  lreg_dest [23:4]
  instr_mod1 [3:0]"""
  return tensix('SFPLUTFP32', lreg_dest, instr_mod1)

def SFPLZ(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x81. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPLZ', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPMAD(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Multiply then add (SFPU, 0x84). Compute VD = A * B + C independently in each active FP32 lane, with optional sign and
  indirect-register modifiers.

  lreg_src_a [23:16] A register index. For SFPADD use L10, the 1.0 constant; ordinary register indices are four bits
                     despite this eight-bit encoder field.
  lreg_src_b [15:12] B register index.
  lreg_src_c [11:8]  C register index. For SFPMUL use L9, the 0.0 constant.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Blackhole flags: 1 negates A, 2 negates C, 4 takes A index from L7 low four bits, 8 takes
                     destination index from L7. Combine flags with bitwise OR; 0 is ordinary arithmetic.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP.
  Note: Multiply-add is partially fused, not an exact IEEE fused multiply-add. Denormal inputs are treated as zero and
        denormal outputs flush to signed zero; Blackhole uses round-to-nearest, ties-to-even."""
  return tensix('SFPMAD', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPMOV(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Copy or negate a vector (SFPU, 0x7C). Copy a register, toggle its sign bit, bypass predication, or read special SFPU
  state.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 copies VC to VD; 1 toggles the FP32/sign-magnitude sign bit; 2 copies with all lanes enabled; 8
                     reads special state selected by VC.
  Note: Negation flips bit 31. It is not two's-complement integer negation. In special mode, VC=9 advances the hardware
        PRNG."""
  return tensix('SFPMOV', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPMUL(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Floating-point multiply (SFPU, 0x86). Compute VD = A * B using the MAD datapath with C fixed to L9 (0.0).

  lreg_src_a [23:16] A register index. For SFPADD use L10, the 1.0 constant; ordinary register indices are four bits
                     despite this eight-bit encoder field.
  lreg_src_b [15:12] B register index.
  lreg_src_c [11:8]  C register index. For SFPMUL use L9, the 0.0 constant.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Blackhole flags: 1 negates A, 2 negates C, 4 takes A index from L7 low four bits, 8 takes
                     destination index from L7. Combine flags with bitwise OR; 0 is ordinary arithmetic.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP.
  Note: Multiply-add is partially fused, not an exact IEEE fused multiply-add. Denormal inputs are treated as zero and
        denormal outputs flush to signed zero; Blackhole uses round-to-nearest, ties-to-even."""
  return tensix('SFPMUL', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPMUL24(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """0x98. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  lreg_src_a [23:16]
  lreg_src_b [15:12]
  lreg_src_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPMUL24', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPMULI(imm16_math=0, lreg_dest=0, instr_mod1=0):
  """Floating-point multiply with an immediate (SFPU, 0x74). Convert a BF16 immediate to FP32 and multiply it with the old
  destination in each active lane.

  imm16_math [23:8]  BF16 immediate bit pattern, widened to FP32 by shifting left 16 bits. Not an integer numerical
                     value.
  lreg_dest  [7:4]   LReg index used as both input and output.
  instr_mod1 [3:0]   Blackhole flags: 1 negates A, 2 negates C, 4 takes A index from L7 low four bits, 8 takes
                     destination index from L7. Combine flags with bitwise OR; 0 is ordinary arithmetic.
  Note: Blackhole MAD has a two-cycle result latency and usually stalls direct dependencies automatically. Load-macro
        sequences and some consumers (including SFPIADD, SFPSHFT, SFPSWAP and SFPSHFT2 modes) need explicit spacing.
        Llama commonly inserts TTSFPNOP."""
  return tensix('SFPMULI', imm16_math, lreg_dest, instr_mod1)

def SFPNOP():
  """SFPU no operation (SFPU, 0x8F). Occupy an SFPU instruction slot without changing arithmetic data.

  Note: Useful for explicit SFPU dependency spacing, including cases missed by Blackhole automatic stalls. It is not a
        global completion barrier."""
  return tensix('SFPNOP')

def SFPNOT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x80. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPNOT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPOR(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Vector bitwise OR (SFPU, 0x7F). Apply bitwise OR to each pair of 32-bit lanes.

  imm12_math [23:12] Blackhole VB selector occupies the low four bits of this raw 12-bit encoder field; keep the upper
                     bits zero.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Bit 0 selects VB as the first input. When clear, the destination register is also the first input.
  Note: VB selection is a Blackhole extension; the Wormhole two-input form always reuses VD."""
  return tensix('SFPOR', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPPOPC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Pop conditional state (SFPU, 0x88). Save or restore the SFPU per-lane conditional-execution state using the predicate
  stack.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_dest  [7:4]   Normally zero; not a data-register output.
  instr_mod1 [3:0]   0 pops and restores both flags and predicate enable; 1-12 peek and combine flags with stack-top
                     flags; 13 inverts flags; 14 enables predication with true flags; 15 enables it with false flags. Do
                     not pop an empty stack or use peek modes on a full stack.
  Note: Useful for nested predication. This is a predicate stack, not a Dst data spill or the RV32 call stack."""
  return tensix('SFPPOPC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPPUSHC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Push conditional state (SFPU, 0x87). Save or restore the SFPU per-lane conditional-execution state using the predicate
  stack.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_dest  [7:4]   Normally zero; not a data-register output.
  instr_mod1 [3:0]   Keep zero. Pushes lane flags and the predicate-enable state onto the eight-entry conditional stack;
                     do not overflow it.
  Note: Useful for nested predication. This is a predicate stack, not a Dst data spill or the RV32 call stack."""
  return tensix('SFPPUSHC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETCC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Set per-lane condition flags (SFPU, 0x7B). Update per-lane flags from the sign or zero status of a register or an
  immediate condition.

  imm12_math [23:12] Low immediate bit supplies the condition in immediate mode; zero for register comparisons.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Normally zero; not the destination of a vector arithmetic result.
  instr_mod1 [3:0]   0 tests sign/negative, 2 nonzero, 4 nonnegative, 6 zero; 1 selects immediate bit 0; 8 clears flags.
                     Conditions update lane flags as specified by the functional model.
  Note: SFPENCC controls whether these flags gate instruction execution. This writes predication state, not a vector of
        integer booleans."""
  return tensix('SFPSETCC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETEXP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Replace a floating-point exponent (SFPU, 0x82). Replace the source exponent using immediate or destination-register
  bits, preserving source sign and mantissa.

  imm12_math [23:12] Unsigned eight-bit biased exponent in immediate mode. Keep the remaining encoder bits zero.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   1 selects the immediate exponent; otherwise take bits from old VD. With register input, OR 2 takes
                     VD exponent bits 30:23 instead of its low eight integer bits.
  Note: This manipulates the representation rather than evaluating log, exp or a general transcendental function. Exact
        modifiers are listed in the source reference."""
  return tensix('SFPSETEXP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETMAN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x83. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPSETMAN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETSGN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """0x89. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  imm12_math [23:12]
  lreg_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFPSETSGN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSHFT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Shift integer bits within each lane (SFPU, 0x7A). Shift the old destination left or logically right. This changes bits
  inside each lane; it does not move data between lanes.

  imm12_math [23:12] Signed shift amount encoded in 12 bits when modifier 1 is used. Positive shifts left; negative
                     shifts right.
  lreg_c     [11:8]  Register supplying the shift amount when immediate mode is disabled.
  lreg_dest  [7:4]   Register holding the data to shift, overwritten with the result.
  instr_mod1 [3:0]   1 selects immediate shift amount; 0 selects the register shift amount.
  Note: Llama uses imm12_math=0xfff (-1), modifier 1 to shift a positive FP32 bit representation right by one for rsqrt
        estimation."""
  return tensix('SFPSHFT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSHFT2(imm12_math=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Shuffle lanes or shift bits (SFPU, 0x94). Move values between lanes or perform per-lane shifts, depending on the
  selected mode.

  imm12_math [23:12] Mode-dependent VB register index or signed 12-bit immediate. Zero in Llama's lane-rotation mode.
  lreg_src_c [11:8]  Source vector VC for the single-vector shuffle modes.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   0 shifts L0-L3 register contents; 1 chained copy; 2 rotate-and-copy; 3 rotates right within each
                     eight-lane group; 4 shifts right within each group with zero fill; 5 register-controlled bit shift;
                     6 immediate bit shift.
  Note: Mode 3 wraps lane 7 into lane 0 independently in each eight-lane group. Llama composes rotations, addition and
        SFPTRANSP to reduce across 32 lanes.
  Note: Blackhole fixes the zero-fill shuffle bug present in Wormhole. Some modes have dependency-stall exceptions; keep
        the explicit delay used in the kernels."""
  return tensix('SFPSHFT2', imm12_math, lreg_src_c, lreg_dest, instr_mod1)

def SFPSTORE(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Store a vector register into Dst (SFPU, 0x72). Write active SFPU lanes into Dst with the selected format conversion.
  This does not write L1; packing is a separate step.

  lreg_ind       [23:20] Source LReg index. Normal data registers are L0-L7; constants can also be read.
  instr_mod0     [19:16] Transfer format: 0 follows configured format, 1 FP16, 2 BF16, 3 FP32. Integer and partial-word
                         modes have distinct meanings; see the mode constants and ISA reference. This is not the same
                         mode numbering as SFPLOADI.
  sfpu_addr_mode [15:13] Raw SFPU address-modifier field, applied after the transfer. It advances SrcA/SrcB/Dst
                         counters, not fidelity. Llama uses 7 with its configured counters. Do not interpret this as a
                         byte increment.
  dest_reg_addr  [12:0]  Dst address immediate plus configured offsets and RWCs. For normal addressing, the effective
                         low 10 bits select four rows (bits 9:2) and even/odd columns (bit 1); bit 0 is unused. Keep
                         reserved upper bits zero.
  Note: Normal lane mapping is the inverse of SFPLOAD. An SFPU register is 32 lanes arranged as four groups of eight,
        not one contiguous tensor row.
  Note: Writing only part of an undefined Dst row is not a valid way to initialize it. Initialize the row before a
        partial or predicated store."""
  return tensix('SFPSTORE', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPSWAP(imm12_math=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Swap or compare-exchange vectors (SFPU, 0x92). Swap two registers, or compute a minimum and maximum simultaneously in
  each lane.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_src_c [11:8]  VC is both an input and an output. In mode 1 it receives the maximum.
  lreg_dest  [7:4]   VD is both an input and an output. In mode 1 it receives the minimum.
  instr_mod1 [3:0]   0 swaps unconditionally; 1 gives VD=min, VC=max; 2-8 choose opposite min/max placement for
                     different eight-lane subgroups; 9 gives VD=max, VC=min.
  Note: Comparison ordering and special floating-point values follow the hardware model, not Python min/max. Both
        operands are modified. Additional argmin/argmax behavior depends on lane configuration."""
  return tensix('SFPSWAP', imm12_math, lreg_src_c, lreg_dest, instr_mod1)

def SFPTRANSP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Transpose between vector registers (SFPU, 0x8C). Transpose the register axis and four-row lane-group axis for both
  L0-L3 and L4-L7.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_dest  [7:4]   Normally zero. This field gates backdoor-template behavior; it does not select a single output
                     register.
  instr_mod1 [3:0]   Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  Note: Treat each group of four registers as a 4 x 4 x 8 array. This swaps the first two axes, preserving the eight-
        column axis. It is not a 4 x 8 tensor transpose. Both register groups are affected."""
  return tensix('SFPTRANSP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPXOR(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Vector bitwise XOR (SFPU, 0x8D). XOR each destination lane with the corresponding VC lane.

  imm12_math [23:12] Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  lreg_c     [11:8]  Source vector register index (VC). L0-L7 are writable vectors; higher indices select constants or
                     special registers.
  lreg_dest  [7:4]   Destination vector register index (VD). Normal arithmetic writes L0-L7. Destinations 12-15 can
                     record instruction templates when backdoor loading is enabled.
  instr_mod1 [3:0]   Keep zero for the documented operation. The Python encoder exposes these bits, but they are not an
                     independent supported operand in the reference syntax.
  Note: The destination is both input and output."""
  return tensix('SFPXOR', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFP_STOCH_RND(rnd_mode=0, imm8_math=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """0x8E. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  rnd_mode [23:21]
  imm8_math [20:16]
  lreg_src_b [15:12]
  lreg_src_c [11:8]
  lreg_dest [7:4]
  instr_mod1 [3:0]"""
  return tensix('SFP_STOCH_RND', rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SHIFTDMAREG(OpBisConst=0, OpSel=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x5C. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  OpSel [22:18]
  ResultRegIndex [17:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('SHIFTDMAREG', OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex)

def SHIFTXA(log2_amount2=0, shift_mode=0):
  """0x17. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  log2_amount2 [23:2]
  shift_mode [1:0]"""
  return tensix('SHIFTXA', log2_amount2, shift_mode)

def SHIFTXB(addr_mode=0, rot_shift=0, shift_row=0):
  """0x18. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  addr_mode [23:14]
  rot_shift [13:10]
  shift_row [9:0]"""
  return tensix('SHIFTXB', addr_mode, rot_shift, shift_row)

def STALLWAIT(stall_res=0, wait_res=0):
  """Wait for selected hardware resources (Control, 0xA2). Latch conditions that block selected classes of subsequent
  instructions until the conditions clear.

  stall_res [23:15] Instruction-class bitmask. Repository bit numbers: 0 TDMA, 1 SYNC, 2 PACK, 3 UNPACK, 4 XMOV, 5
                    THCON, 6 MATH, 7 CFG, 8 SFPU. Set a bit using 1 << bit_number.
  wait_res  [14:0]  Blackhole condition bitmask. Repository bit numbers: 0 THCON, 1 UNPACK0, 2 UNPACK1, 3 PACK0, 4 MATH,
                    5 SRCA_CLR, 6 SRCB_CLR, 7 SRCA_VLD, 8 SRCB_VLD, 9 XMOV, 10 TRISC_CFG, 11 SFPU, 12 CFGEXU. See the
                    source condition table for the precise wait predicate.
  Note: The issuing thread can continue until it reaches a blocked instruction class. This is not equivalent to
        immediately stopping every unit.
  Note: Resource-completion waits and semaphore waits have different conditions; do not substitute one for the other."""
  return tensix('STALLWAIT', stall_res, wait_res)

def STOREIND(MemHierSel=0, SizeSel=0, RegSizeSel=0, OffsetIndex=0, AutoIncSpec=0, DataRegIndex=0, AddrRegIndex=0):
  """0x66. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  MemHierSel [23]
  SizeSel [22]
  RegSizeSel [21]
  OffsetIndex [20:14]
  AutoIncSpec [13:12]
  DataRegIndex [11:6]
  AddrRegIndex [5:0]"""
  return tensix('STOREIND', MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex)

def STOREREG(TdmaDataRegIndex=0, RegAddr=0):
  """0x67. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  TdmaDataRegIndex [23:18]
  RegAddr [17:0]"""
  return tensix('STOREREG', TdmaDataRegIndex, RegAddr)

def STREAMWAIT(stall_res=0, target_value=0, target_sel=0, wait_stream_sel=0):
  """0xA7. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  stall_res [23:15]
  target_value [14:4]
  target_sel [3]
  wait_stream_sel [2:0]"""
  return tensix('STREAMWAIT', stall_res, target_value, target_sel, wait_stream_sel)

def STREAMWRCFG(stream_id_sel=0, StreamRegAddr=0, CfgReg=0):
  """0xB7. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  stream_id_sel [23:21]
  StreamRegAddr [20:11]
  CfgReg [10:0]"""
  return tensix('STREAMWRCFG', stream_id_sel, StreamRegAddr, CfgReg)

def SUBDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """0x59. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  OpBisConst [23]
  ResultRegIndex [22:12]
  OpBRegIndex [11:6]
  OpARegIndex [5:0]"""
  return tensix('SUBDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def TBUFCMD():
  """0x4B. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile."""
  return tensix('TBUFCMD')

def TRNSPSRCA():
  """0x14. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile."""
  return tensix('TRNSPSRCA')

def TRNSPSRCB():
  """Transpose SrcB rows 16–31 (FPU, 0x16). Transpose the 16 × 16 matrix in rows 16 through 31 of the current SrcB bank.

  Note: Waits for the FPU to own SrcB. No row or tile selector is encoded."""
  return tensix('TRNSPSRCB')

def UNPACR(Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=0,
           SetDatValid=0, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=0):
  """Unpack L1 into source or destination registers (Unpack / pack, 0x42). Issue work to unpacker 0 or 1. Configuration
  supplies formats, base addresses, tensor dimensions and the output interface.

  Unpack_block_selection [23]    0 selects unpacker 0 (SrcA or direct Dst); 1 selects unpacker 1 (SrcB).
  AddrMode               [22:15] Four two-bit increments: bits 7:6 Ch1 Y, 5:4 Ch1 Z, 3:2 Ch0 Y, 1:0 Ch0 Z. Applied for
                                 the next unpack operation.
  CfgContextCntInc       [14:13] Keep 0 for a regular unpack. Nonzero values select the separate context-counter command
                                 form.
  CfgContextId           [12:10] Configuration context number when explicit multi-context selection is active.
  AddrCntContextId       [9:8]   Address-counter context selector in multi-context mode. Regular repository calls use 0.
  OvrdThreadId           [7]     Selects multi-context behavior in the reference model; the legacy argument name is
                                 misleading. Repository regular calls use 1.
  SetDatValid            [6]     1 gives the filled source bank to math and flips the unpacker bank. Direct-to-Dst calls
                                 handle synchronization separately.
  srcb_bcast             [5]     Keep 0 for the regular unpack form. This bit is not ordinary FPU SrcB broadcasting.
  ZeroWrite2             [4]     1 replaces unpacked datums with zero.
  AutoIncContextID       [3]     Use/increment the configured context counter rather than only the immediate context
                                 selector.
  RowSearch              [2]     Select row-search addressing. Repository regular calls keep 0.
  SearchCacheFlush       [1]     Selects the separate decompression-cache flush command. Keep 0 for ordinary unpack.
  Last                   [0]     Keep 0 for the regular unpack form; this is not the packer Last bit.
  Note: Unpacker 0 can write Dst directly, but doing so clobbers its SrcA bank. It still waits on SrcA ownership.
        Unpacker 1 cannot perform this direct-to-Dst path.
  Note: ADC counters and format configuration determine actual data movement. A bare TTUNPACR does not include a pointer
        or byte count.
  Note: The shared manual includes explicit Blackhole branches for 32-element unpack rows and throttle behavior. Some
        multi-context and compressed modes are not fully characterized."""
  return tensix('UNPACR', Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId,
                OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last)

def UNPACR_NOP(Unpacker_Select=0, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=0, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0,
               Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=0):
  """Unpacker-sequenced control (Unpack / pack, 0x43). Perform an action ordered with unpacking: publish a source bank,
  clear sources, write selected registers, or occupy an unpacker cycle.

  Unpacker_Select  [23]    0 selects unpacker 0; 1 selects unpacker 1.
  Stream_Id        [22:16] Stream identifier for the overlay-clear variant; zero for bank publication.
  Msg_Clr_Cnt      [15:12] Message clear count for the overlay-clear variant; zero for bank publication.
  Set_Dvalid       [11:8]  Dvalid control. Repository SrcB publication uses 1 with Unpack_Pop=1.
  Clr_to1_fmt_Ctrl [7:6]   Format control for the source-clear variant; keep 0 for bank publication.
  Stall_Clr_Cntrl  [5]     Stall-clear control for variant-specific behavior; keep 0 for bank publication.
  Bank_Clr_Ctrl    [4]     Bank-clear control for source clearing; keep 0 for bank publication.
  Src_ClrVal_Ctrl  [3:2]   Source fill selector for the source-clear variant; keep 0 for bank publication.
  Unpack_Pop       [1:0]   Selects command behavior together with the other control bits. Repository publication uses 1.
  Note: This is not necessarily a no-op: the repository uses TTUNPACR_NOP(1, 0, 0, 1, 0, 0, 0, 0, 1) to give SrcB to
        math.
  Note: The public reference defines separate command forms. The full cross-product of legacy field values is not
        documented; consult the specific form before changing the publication recipe."""
  return tensix('UNPACR_NOP', Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl,
                Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop)

def WRCFG(GprAddress=0, wr128b=0, CfgReg=0):
  """Write backend configuration from GPRs (Control, 0xB0). Copy Tensix GPR data into backend configuration registers.

  GprAddress [23:16] Source Tensix GPR index, not an RV32 register number.
  wr128b     [15]    0 writes one 32-bit word; 1 writes a 128-bit group. Respect group alignment for the wide form.
  CfgReg     [14:0]  Backend configuration word index, not its byte address.
  Note: The packer setup uses TTWRCFG after writing the output destination into a Tensix GPR. Synchronize CPU-to-
        configuration visibility as required by the surrounding sequence."""
  return tensix('WRCFG', GprAddress, wr128b, CfgReg)

def XMOV(Mov_block_selection=0, Last=0):
  """0x40. Not written up in tt-ins-docs; see tt-isa-documentation BlackholeA0/TensixTile.
  Mov_block_selection [23]
  Last [22:0]"""
  return tensix('XMOV', Mov_block_selection, Last)

def ZEROACC(clear_mode=0, use_32_bit_mode=0, clear_zero_flags=0, addr_mode=0, where=0):
  """Invalidate accumulator rows (FPU, 0x10). Mark Dst rows undefined so later FPU accumulation reads an identity value,
  and packer reads produce zeros.

  clear_mode       [23:19] Raw five-bit field in isa.py. The shared manual places Mode in bits 20:19 and UseDst32b in
                           bit 21, so these semantic fields fall within this Python argument.
  use_32_bit_mode  [18]    Encoder bit 18. Despite this name, the shared manual labels bit 18 Revert, not UseDst32b.
                           Treat nonzero use as an unresolved encoder/manual discrepancy.
  clear_zero_flags [17]    Encoder bit 17; not documented as a public operand in the shared ZEROACC syntax. Keep zero
                           unless separately verified.
  addr_mode        [16:14] Raw address-modifier field. Selects preconfigured counter updates after the instruction, not
                           a byte stride. The Python bit field is wider than the semantic selector; do not assume every
                           encodable value is valid.
  where            [13:0]  Mode-dependent row/block selection. In the shared model: mode 0 selects an offset row, 1
                           selects a 16-row block, 2 a Dst half, 3 all Dst. Do not translate existing Python calls using
                           argument names alone.
  Note: Important source mismatch: the Python wrapper and shared ISA diagram disagree on operand naming and placement.
        Existing calls use TTZEROACC(3, 1, 0, 1, ...); this page preserves them without claiming the shared model
        explains that combination. A focused hardware probe is required before changing this encoding.
  Note: ZEROACC does not physically fill Dst with zeros. SFPU loads from undefined rows are undefined, and partial
        SFPU/unpacker writes to such rows are also unsafe."""
  return tensix('ZEROACC', clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where)

def ZEROSRC(zero_val=0, write_mode=0, bank_mask=0, src_mask=0):
  """Clear source register banks (FPU, 0x11). Clear all rows of selected SrcA/SrcB banks to zero, with an optional
  negative-infinity value for SrcA.

  zero_val   [23:4]  0 writes zero; the documented low-bit option writes negative infinity to SrcA. The wider encoder
                     field is not a general fill immediate.
  write_mode [3]     For a single-bank clear: 1 selects the math-owned bank; 0 selects the unpacker-owned bank.
  bank_mask  [2]     1 clears both banks; 0 clears one bank selected by write_mode.
  src_mask   [1:0]   Bitmask: 1 SrcA, 2 SrcB, 3 both.
  Note: Clearing source storage and transferring source-bank ownership are separate actions. Synchronize before clearing
        a bank still used by another unit."""
  return tensix('ZEROSRC', zero_val, write_mode, bank_mask, src_mask)
