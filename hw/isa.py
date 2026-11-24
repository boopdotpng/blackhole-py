"""Instruction encodings: RV32IM + Zicsr, the RISC-V extensions the Blackhole baby cores implement, and the Blackhole
Tensix ISA. RISC-V by mnemonic through rv()/v(); Tensix one function per instruction.

  from hw import isa
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

Sources: the Tensix layouts are tt-llk tt_llk_blackhole/common/inc/ckernel_ops.h (field names, shifts, and widths
from its _VALID macros). TENSIX holds the 97 of its 137 instructions that ttrv emits or that a lowering has a use for;
the rest are listed under "Not covered" with the reason. What each instruction and field does is from
tt-isa-documentation (BlackholeA0, and the WormholeB0 pages it shares), corrected by the cfgprobe hardware runs
of 2026-11-23 where they measured something; `UNCERTAIN:` in a docstring marks what is still unmeasured. The RISC-V
extension encodings were checked against llvm-mc, and which core runs what against a p150 (see "RISC-V beyond RV32IM"
below).

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

# ---- named field values ----

class Stall(IntEnum):
  """STALLWAIT/SEMWAIT stall_res: which classes of this thread's later instructions are held back."""
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF

class Wait(IntEnum):
  """STALLWAIT wait_res: the conditions waited for (all must clear). Blackhole numbering; the shared Wormhole pages
  of tt-isa-documentation quote Wormhole's, which differs.
    THCON      the scalar unit is busy or has memory requests outstanding (needed between a GPR write and its WRCFG)
    UNPACK0/1  that unpacker's pipeline is busy
    PACK0      the packer's pipeline is busy
    MATH       the FPU's pipeline is busy
    SRCA_CLR / SRCB_CLR  the unpackers do not own a bank of that Src to fill
    SRCA_VLD / SRCB_VLD  math does not own a bank of that Src to read
    XMOV       the mover is busy
    TRISC_CFG  a RISC MMIO write to the config is pending
    SFPU       the SFPU is busy
    CFGEXU     the configuration unit is busy"""
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (
    1 << x for x in range(13))

class SemWait(IntEnum):
  """SEMWAIT wait_sem_cond."""
  STALL_ON_ZERO, STALL_ON_MAX = 1, 2

class LReg(IntEnum):
  """SFPU register operands (lreg_*)."""
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)        # read/write (32 independent lanes)
  CONST_0_8373, ZERO, ONE = 8, 9, 10               # read-only hardware constants (0.8373, 0, 1.0)
  NEG_ONE, CONFIG0, CONFIG1, CONFIG2 = 11, 12, 13, 14  # SFPCONFIG-programmable (8-lane broadcast); fw sets L11=-1.0
  LANE_X2 = 15                                     # read-only lane index * 2 (0, 2, ..., 62)
  LOAD_MACRO = 16                                  # SFPLOADMACRO pipeline register, never an ordinary operand

class SfpuFormat(IntEnum):
  """SFPLOAD/SFPSTORE instr_mod0: how Dst is read into / written from the 32-bit lanes.
    DEFAULT    FP32 when cfg.MATH.sfpu_fp32_acc=1; else cfg.THREAD.sfpu_dst_fmt when sfpu_dst_fmt_en=1, else FP16 or
               BF16 from cfg.MATH.srcb_fmt (probed)
    FP16, BF16 16-bit Dst rows, converted to and from FP32 (stores truncate)
    FP32       32-bit Dst rows; stores flush denormals to zero
    INT32      32-bit Dst rows, raw bits both ways
    INT8, INT16  16-bit Dst rows holding sign-magnitude integers
    UINT16, LO16  16-bit Dst rows, zero-extended on load; UINT16 stores the low half, LO16 the datum rotated by 16
    HI16       loads 16 bits into the high half (low half 0)
    LO16_ONLY, HI16_ONLY  load into / store from one half of the lane, leaving the other half alone
    INT32_ALL  as INT32 but ignores the lane flags and addresses Dst through the SFPU stack pointer: a store writes at
               Sp + cfg dst_sp_base and then adds sfpu_stack_incr to Sp, a load first subtracts it (probed). Sp survives
               kernel reloads; set it with SETRWC BitMask=16 before relying on it.
    ZERO       loads 0 / stores 0
  Codes 12 and 13 are deprecated on Blackhole and left out."""
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO = 10, 11
  LO16_ONLY, HI16_ONLY = 14, 15

class LoadImm(IntEnum):
  """SFPLOADI instr_mod0: how imm16 is interpreted."""
  FLOATB, FLOATA, USHORT, SHORT, UPPER, LOWER = 0, 1, 2, 4, 8, 10

class Broadcast(IntEnum):
  """ELWADD/ELWSUB/ELWMUL instr_mod19: SrcB broadcast."""
  NONE, COLUMN, ROW, SCALAR = range(4)


# ---- Not covered ----
#
# RISC-V the baby cores lack (UndefinedBehavior, so not encoded): fdiv/fsqrt (.s and .h), lr.w/sc.w, Zbs, Zbc,
# packh/zip/unzip, and in RVV vdiv/vdivu/vrem/vremu, vfdiv/vfrdiv, vfsqrt, vfrsqrt7, vfrec7. Implemented but not
# encoded: RVV segment and fault-only-first loads/stores (untested on hardware); vzext/vsext.vf8 need SEW=64.
# cycle and instret are CSRs 0xC00 and 0xC02 (csrrs rd, csr, x0); time is not implemented.
#
# Tensix instructions left out of TENSIX (40 of tt-llk's 137; opcode in brackets), and why:
#   do nothing useful on Blackhole   APOOL3S1 [25] APOOL3S2 [32] MPOOL3S1 [24] MPOOL3S2 [31] CONV3S1 [22] CONV3S2 [23]
#                                    MFCONV3S1 [3a] (legacy: they add 0 or act as a degenerate GMPOOL), DOTPV [29]
#                                    (MVMUL without the broadcast bit), SHIFTXA [17] (cannot choose its input rows)
#   unsupported on Blackhole         SETDVALID [57] (leaves the Src format unpredictable; UNPACR's SetDatValid does
#                                    the job), REG2FLOP [48]
#   need the NoC overlay we bypass   STREAMWAIT [a7] STREAMWRCFG [b7]
#   debug, or superseded             MOVDBGA2D [09] MOVDBGB2D [0c] (MOVA2D/MOVB2D without the bank wait), DMANOP [60]
#                                    FLUSHDMA [46] (STALLWAIT does it), RESOURCEDECL [05] (Auto TTSync tuning),
#                                    CLREXPHIST [21], BITWOPDMAREG [5b] CMPDMAREG [5d]
#   L1 atomics and mutexes           ATCAS [64] ATINCGET [61] ATINCGETPTR [62] ATSWAP [63] ATGETM [a0] ATRELM [a1]
#                                    (the RISCs own cross-thread and cross-core sync here)
#   no description anywhere          RAREB [15] SETASHRMH [1e] SETASHRMH0 [1a] SETASHRMH1 [1b] SETASHRMV [1c]
#                                    SETPKEDGOF [1d] RSTDMA [44] TBUFCMD [4b]
#   probed: no effect                TRNSPSRCA [14] (SrcA tile unchanged), SETIBRWC [39] (later ELWADD addressing
#                                    unchanged), GATESRCRST [35] (tt-llk issues it after MOVD2B, TRNSPSRCB and
#                                    MOVB2A; the next FPU instruction saw the new SrcB without it in all 24 cases,
#                                    also back to back from a REPLAY)
#   probed: nothing we want          SHIFTXB [18] (rotates one SrcB row left by one lane, or shifts in a zero)
#   probed: hazardous                PACR_SETREG [4a] (wedges the packer until a card reset, and the MMIO write
#                                    never lands; STALLWAIT + STOREREG is the pack-done signal instead)
# Their field layouts are in tt-llk tt_llk_blackhole/common/inc/ckernel_ops.h.

# name: (opcode, ((field, shift, width), ...)). Layouts are tt-llk's. Several fields are wider than the bits the
# hardware reads (a Dst row is 10 bits, a Src row 6, an address-modifier slot 3); the docstrings give the real widths.
TENSIX = {
  # control
  'NOP': (0x02, ()),
  'MOP': (0x01, (('mop_type', 23, 1), ('loop_count', 16, 7), ('zmask_lo16_or_loop_count', 0, 16))),
  'MOP_CFG': (0x03, (('zmask_hi16', 0, 24),)),
  'REPLAY': (0x04, (('start_idx', 14, 10), ('len', 4, 10), ('execute_while_loading', 1, 3), ('load_mode', 0, 1))),
  'STALLWAIT': (0xa2, (('stall_res', 15, 9), ('wait_res', 0, 15))),
  'SEMINIT': (0xa3, (('max_value', 20, 4), ('init_value', 16, 4), ('sem_sel', 2, 14))),
  'SEMPOST': (0xa4, (('sem_sel', 2, 22),)),
  'SEMGET': (0xa5, (('sem_sel', 2, 22),)),
  'SEMWAIT': (0xa6, (('stall_res', 15, 9), ('sem_sel', 2, 13), ('wait_sem_cond', 0, 2))),
  # configuration
  'SETC16': (0xb2, (('setc16_reg', 16, 8), ('setc16_value', 0, 16))),
  'RMWCIB0': (0xb3, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB1': (0xb4, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB2': (0xb5, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'RMWCIB3': (0xb6, (('Mask', 16, 8), ('Data', 8, 8), ('CfgRegAddr', 0, 8))),
  'WRCFG': (0xb0, (('GprAddress', 16, 8), ('wr128b', 15, 1), ('CfgReg', 0, 15))),
  'RDCFG': (0xb1, (('GprAddress', 16, 8), ('CfgReg', 0, 16))),
  'CFGSHIFTMASK': (0xb8, (('disable_mask_on_old_val', 23, 1), ('operation', 20, 3), ('mask_width', 15, 5), ('right_cshift_amt', 10, 5), ('scratch_sel', 8, 2), ('CfgReg', 0, 8))),
  # scalar unit: the thread's 64 Tensix GPRs
  'SETDMAREG': (0x45, (('Payload_SigSelSize', 22, 2), ('Payload_SigSel', 8, 14), ('SetSignalsMode', 7, 1), ('RegIndex16b', 0, 7))),
  'ADDDMAREG': (0x58, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'SUBDMAREG': (0x59, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'MULDMAREG': (0x5a, (('OpBisConst', 23, 1), ('ResultRegIndex', 12, 11), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'SHIFTDMAREG': (0x5c, (('OpBisConst', 23, 1), ('OpSel', 18, 5), ('ResultRegIndex', 12, 6), ('OpBRegIndex', 6, 6), ('OpARegIndex', 0, 6))),
  'LOADIND': (0x49, (('SizeSel', 22, 2), ('OffsetIndex', 14, 8), ('AutoIncSpec', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'STOREIND': (0x66, (('MemHierSel', 23, 1), ('SizeSel', 22, 1), ('RegSizeSel', 21, 1), ('OffsetIndex', 14, 7), ('AutoIncSpec', 12, 2), ('DataRegIndex', 6, 6), ('AddrRegIndex', 0, 6))),
  'LOADREG': (0x68, (('TdmaDataRegIndex', 18, 6), ('RegAddr', 0, 18))),
  'STOREREG': (0x67, (('TdmaDataRegIndex', 18, 6), ('RegAddr', 0, 18))),
  # address counters (unpackers and packer)
  'SETADC': (0x50, (('CntSetMask', 21, 3), ('ChannelIndex', 20, 1), ('DimensionIndex', 18, 2), ('Value', 0, 18))),
  'SETADCXX': (0x5e, (('CntSetMask', 21, 3), ('x_end2', 10, 11), ('x_start', 0, 10))),
  'SETADCXY': (0x51, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3), ('BitMask', 0, 6))),
  'SETADCZW': (0x54, (('CntSetMask', 21, 3), ('Ch1_W', 15, 6), ('Ch1_Z', 12, 3), ('Ch0_W', 9, 3), ('Ch0_Z', 6, 3), ('BitMask', 0, 6))),
  'INCADCXY': (0x52, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3))),
  'INCADCZW': (0x55, (('CntSetMask', 21, 3), ('Ch1_W', 15, 6), ('Ch1_Z', 12, 3), ('Ch0_W', 9, 3), ('Ch0_Z', 6, 3))),
  'ADDRCRXY': (0x53, (('CntSetMask', 21, 3), ('Ch1_Y', 15, 6), ('Ch1_X', 12, 3), ('Ch0_Y', 9, 3), ('Ch0_X', 6, 3), ('BitMask', 0, 6))),
  'ADDRCRZW': (0x56, (('CntSetMask', 21, 3), ('Ch1_W', 15, 6), ('Ch1_Z', 12, 3), ('Ch0_W', 9, 3), ('Ch0_Z', 6, 3), ('BitMask', 0, 6))),
  # unpack, pack, mover
  'UNPACR': (0x42, (('Unpack_block_selection', 23, 1), ('AddrMode', 15, 8), ('CfgContextCntInc', 13, 2), ('CfgContextId', 10, 3), ('AddrCntContextId', 8, 2), ('OvrdThreadId', 7, 1), ('SetDatValid', 6, 1), ('srcb_bcast', 5, 1), ('ZeroWrite2', 4, 1), ('AutoIncContextID', 3, 1), ('RowSearch', 2, 1), ('SearchCacheFlush', 1, 1), ('Last', 0, 1))),
  'UNPACR_NOP': (0x43, (('Unpacker_Select', 23, 1), ('Stream_Id', 16, 7), ('Msg_Clr_Cnt', 12, 4), ('Set_Dvalid', 8, 4), ('Clr_to1_fmt_Ctrl', 6, 2), ('Stall_Clr_Cntrl', 5, 1), ('Bank_Clr_Ctrl', 4, 1), ('Src_ClrVal_Ctrl', 2, 2), ('Unpack_Pop', 0, 2))),
  'PACR': (0x41, (('CfgContext', 21, 3), ('RowPadZero', 18, 3), ('DstAccessMode', 17, 1), ('AddrMode', 15, 2), ('AddrCntContext', 13, 2), ('ZeroWrite', 12, 1), ('ReadIntfSel', 8, 4), ('OvrdThreadId', 7, 1), ('Concat', 4, 3), ('CtxtCtrl', 2, 2), ('Flush', 1, 1), ('Last', 0, 1))),
  'XMOV': (0x40, (('Mov_block_selection', 23, 1), ('Last', 0, 23))),
  # FPU
  'MVMUL': (0x26, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWADD': (0x28, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWSUB': (0x30, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'ELWMUL': (0x27, (('clear_dvalid', 22, 2), ('dest_accum_en', 21, 1), ('instr_mod19', 19, 2), ('addr_mode', 14, 5), ('dst', 0, 14))),
  'GAPOOL': (0x34, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('pool_addr_mode', 15, 4), ('max_pool_index_en', 14, 1), ('dst', 0, 14))),
  'GMPOOL': (0x33, (('clear_dvalid', 22, 2), ('instr_mod19', 19, 3), ('pool_addr_mode', 15, 4), ('max_pool_index_en', 14, 1), ('dst', 0, 14))),
  'MOVA2D': (0x12, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVB2D': (0x13, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('movb2d_instr_mod', 11, 3), ('dst', 0, 11))),
  'MOVD2A': (0x08, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVD2B': (0x0a, (('dest_32b_lo', 23, 1), ('src', 17, 6), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('dst', 0, 12))),
  'MOVB2A': (0x0b, (('srca', 17, 7), ('addr_mode', 14, 3), ('instr_mod', 12, 2), ('srcb', 0, 12))),
  'TRNSPSRCB': (0x16, ()),
  'ZEROACC': (0x10, (('clear_mode', 19, 5), ('use_32_bit_mode', 18, 1), ('clear_zero_flags', 17, 1), ('addr_mode', 14, 3), ('where', 0, 14))),
  'ZEROSRC': (0x11, (('zero_val', 4, 20), ('write_mode', 3, 1), ('bank_mask', 2, 1), ('src_mask', 0, 2))),
  'CLEARDVALID': (0x36, (('cleardvalid', 22, 2), ('reset', 0, 22))),
  'SETRWC': (0x37, (('clear_ab_vld', 22, 2), ('rwc_cr', 18, 4), ('rwc_d', 14, 4), ('rwc_b', 10, 4), ('rwc_a', 6, 4), ('BitMask', 0, 6))),
  'INCRWC': (0x38, (('rwc_cr', 18, 6), ('rwc_d', 14, 4), ('rwc_b', 10, 4), ('rwc_a', 6, 4))),
  # SFPU
  'SFPLOAD': (0x70, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPSTORE': (0x72, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPLOADI': (0x71, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('imm16', 0, 16))),
  'SFPLOADMACRO': (0x93, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('sfpu_addr_mode', 13, 3), ('dest_reg_addr', 0, 13))),
  'SFPCONFIG': (0x91, (('imm16_math', 8, 16), ('config_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPNOP': (0x8f, ()),
  'SFPMAD': (0x84, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPADD': (0x85, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMUL': (0x86, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPADDI': (0x75, (('imm16_math', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMULI': (0x74, (('imm16_math', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMUL24': (0x98, (('lreg_src_a', 16, 8), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPLUT': (0x73, (('lreg_ind', 20, 4), ('instr_mod0', 16, 4), ('dest_reg_addr', 0, 16))),
  'SFPLUTFP32': (0x95, (('lreg_dest', 4, 20), ('instr_mod1', 0, 4))),
  'SFPARECIP': (0x99, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPMOV': (0x7c, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPABS': (0x7d, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPAND': (0x7e, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPOR': (0x7f, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPXOR': (0x8d, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPNOT': (0x80, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPLZ': (0x81, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSHFT': (0x7a, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSHFT2': (0x94, (('imm12_math', 12, 12), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPIADD': (0x79, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPCAST': (0x90, (('lreg_src_c', 8, 16), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFP_STOCH_RND': (0x8e, (('rnd_mode', 21, 3), ('imm8_math', 16, 5), ('lreg_src_b', 12, 4), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPEXEXP': (0x77, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPEXMAN': (0x78, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETEXP': (0x82, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETMAN': (0x83, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETSGN': (0x89, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPDIVP2': (0x76, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSWAP': (0x92, (('imm12_math', 12, 12), ('lreg_src_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPTRANSP': (0x8c, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPENCC': (0x8a, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPSETCC': (0x7b, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPGT': (0x97, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPLE': (0x96, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPPUSHC': (0x87, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPPOPC': (0x88, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
  'SFPCOMPC': (0x8b, (('imm12_math', 12, 12), ('lreg_c', 8, 4), ('lreg_dest', 4, 4), ('instr_mod1', 0, 4))),
}
_TENSIX_BY_OP = {op: n for n, (op, _) in TENSIX.items()}

# ---- Tensix, one function per instruction ----
#
# Each docstring says what the instruction does on Blackhole and what every field means, with the tt-llk field's bit
# range in brackets. Statements marked (probed) were measured on a p150 by the cfgprobe runs of 2026-11-23; the rest is
# from tt-isa-documentation or from what ttrv kernels do every day. `UNCERTAIN:` marks what neither settles.

# ---- control ----

def NOP():
  """Tensix no-op (control, 0x02). Does nothing. It is the filler for unused MOP template slots (the MOP expander
  skips a slot holding exactly this word) and the spacer after a config write whose next instruction would consume
  it. It is not a wait: use STALLWAIT to order units."""
  return tensix('NOP')

def MOP(mop_type=0, loop_count=0, zmask_lo16_or_loop_count=0):
  """Expand a macro-op template (control, 0x01). The thread's MOP expander turns this one word into a looped sequence
  of instructions taken from the 9 MOP_CFG words (MMIO at hw.MOP_CFG, written by the RISC).

  mop_type                 [23]    Template: 0 mask-driven, 1 nested loop.
  loop_count               [22:16] Template 0: iterations minus 1.
  zmask_lo16_or_loop_count [15:0]  Template 0: low 16 bits of the skip mask. Template 1: keep 0.
  Template 1, words (outer, inner, start, end0, end1, loop0, loop1, last_inner, last): repeat outer times
    { start; inner times { loop0; loop1 }; end0; end1 }, where the very last loop instruction of each outer pass is
    replaced by last_inner, and by last on the final pass. A slot holding NOP is skipped. loop1 present doubles the
    inner instruction count. Counts are 10 bits.
  Template 0, words (-, flags, b, a0, a1, a2, a3, skip_a, skip_b): for i in 0..loop_count, if bit i of the 32-bit mask
    is clear emit a0 (then a1..a3 with flags bit 1) then b (with flags bit 0); if set emit skip_a then skip_b. The mask
    is MOP_CFG's 16 bits above this word's 16.
  Wait for hw.MOP_EXPANDER_DONE_CHECK before rewriting the template words. A template-1 MOP whose start slot is NOP
  with an inner count of 0 hits a hardware bug."""
  return tensix('MOP', mop_type, loop_count, zmask_lo16_or_loop_count)

def MOP_CFG(zmask_hi16=0):
  """Set the high half of the MOP skip mask (control, 0x03). Stores bits 31:16 of the mask the next template-0 MOPs
  use. It is per thread and stays until changed.

  zmask_hi16 [23:0] The 16 mask bits (only 16 are read)."""
  return tensix('MOP_CFG', zmask_hi16)

def REPLAY(start_idx=0, len=0, execute_while_loading=0, load_mode=0):
  """Record or replay instructions (control, 0x04). Each thread has a 32-word replay buffer.

  start_idx             [23:14] First buffer slot.
  len                   [13:4]  Number of instructions to record or replay.
  execute_while_loading [3:1]   With load_mode=1: 1 also executes the instructions as they are recorded, 0 only stores.
  load_mode             [0]     1 records the next len Tensix words into the buffer. 0 replays len stored words once.
  Repetition comes from a MOP or a software loop around the replay, not from this instruction."""
  return tensix('REPLAY', start_idx, len, execute_while_loading, load_mode)

def STALLWAIT(stall_res=0, wait_res=0):
  """Hold back instruction classes until conditions clear (control, 0xA2).

  stall_res [23:15] isa.Stall mask: which classes of this thread's later instructions wait.
  wait_res  [14:0]  isa.Wait mask: what they wait for. All selected conditions must clear.
  The thread keeps issuing instructions until it reaches one in a held class, so this orders units without stopping
  the others. It is the only reliable ordering between units: NOPs are not."""
  return tensix('STALLWAIT', stall_res, wait_res)

def SEMINIT(max_value=0, init_value=0, sem_sel=0):
  """Initialise semaphores (control, 0xA3).

  max_value  [23:20] Maximum value (4 bits).
  init_value [19:16] Initial value (4 bits).
  sem_sel    [15:2]  Semaphore mask, 1 << number, for the 8 semaphores (hw.Sem)."""
  return tensix('SEMINIT', max_value, init_value, sem_sel)

def SEMPOST(sem_sel=0):
  """Increment semaphores (control, 0xA4).

  sem_sel [23:2] Semaphore mask, 1 << number. Does not block."""
  return tensix('SEMPOST', sem_sel)

def SEMGET(sem_sel=0):
  """Decrement semaphores (control, 0xA5).

  sem_sel [23:2] Semaphore mask, 1 << number. Does not block: pair it with SEMWAIT to wait for a value."""
  return tensix('SEMGET', sem_sel)

def SEMWAIT(stall_res=0, sem_sel=0, wait_sem_cond=0):
  """Hold back instruction classes on a semaphore (control, 0xA6).

  stall_res     [23:15] isa.Stall mask, as STALLWAIT.
  sem_sel       [14:2]  Semaphore mask, 1 << number.
  wait_sem_cond [1:0]   isa.SemWait: 1 wait while any selected semaphore is 0, 2 wait while any is at its maximum.
  It does not change the semaphore."""
  return tensix('SEMWAIT', stall_res, sem_sel, wait_sem_cond)

# ---- configuration ----
#
# A config write is not visible to the instruction immediately after it. Put one unrelated instruction (NOP) between a
# WRCFG / CFGSHIFTMASK and its consumer, and keep ttrv's two NOPs between a WRCFG of unpacker config and the UNPACR.

def SETC16(setc16_reg=0, setc16_value=0):
  """Write a ThreadConfig word (config, 0xB2). Replaces the whole word; ThreadConfig fields are at most 16 bits.

  setc16_reg   [23:16] ThreadConfig word index (cfg Space.THREAD).
  setc16_value [15:0]  New value of the word."""
  return tensix('SETC16', setc16_reg, setc16_value)

def RMWCIB0(Mask=0, Data=0, CfgRegAddr=0):
  """Update byte 0 of a Config word (config, 0xB3). Read-modify-write: only the masked bits change.

  Mask       [23:16] Bits of the byte to change.
  Data       [15:8]  Their new values.
  CfgRegAddr [7:0]   Config word index (cfg Space.CONFIG) in this thread's config bank.
  RMWCIB1 / 2 / 3 do the same for bytes 1 / 2 / 3, so a field spanning bytes takes one instruction per byte."""
  return tensix('RMWCIB0', Mask, Data, CfgRegAddr)

def RMWCIB1(Mask=0, Data=0, CfgRegAddr=0):
  """Update byte 1 (bits 15:8) of a Config word (config, 0xB4). Fields as RMWCIB0."""
  return tensix('RMWCIB1', Mask, Data, CfgRegAddr)

def RMWCIB2(Mask=0, Data=0, CfgRegAddr=0):
  """Update byte 2 (bits 23:16) of a Config word (config, 0xB5). Fields as RMWCIB0."""
  return tensix('RMWCIB2', Mask, Data, CfgRegAddr)

def RMWCIB3(Mask=0, Data=0, CfgRegAddr=0):
  """Update byte 3 (bits 31:24) of a Config word (config, 0xB6). Fields as RMWCIB0."""
  return tensix('RMWCIB3', Mask, Data, CfgRegAddr)

def WRCFG(GprAddress=0, wr128b=0, CfgReg=0):
  """Write a Config word from a Tensix GPR (config, 0xB0).

  GprAddress [23:16] Source GPR (6 bits).
  wr128b     [15]    0 writes one 32-bit word. 1 writes four aligned GPRs to four aligned Config words.
  CfgReg     [14:0]  Config word index (11 bits).
  If the GPR was just written by SETDMAREG or ADDDMAREG, put STALLWAIT(Stall.CFG, Wait.THCON) between them: NOPs do
  not order the scalar unit against the config unit on Blackhole."""
  return tensix('WRCFG', GprAddress, wr128b, CfgReg)

def RDCFG(GprAddress=0, CfgReg=0):
  """Read a Config word into a Tensix GPR (config, 0xB1). Cannot read ThreadConfig.

  GprAddress [23:16] Destination GPR (6 bits).
  CfgReg     [15:0]  Config word index. Only the low 8 bits are used, so words 0..255.
  It sees an RMWCIB or WRCFG the same thread issued just before it, with no STALLWAIT between (probed).
  The instructions right after must not read the GPR: STALLWAIT on Wait.CFGEXU first."""
  return tensix('RDCFG', GprAddress, CfgReg)

def CFGSHIFTMASK(disable_mask_on_old_val=0, operation=0, mask_width=0, right_cshift_amt=0, scratch_sel=0, CfgReg=0):
  """Combine a scratch word into a Config word (config, 0xB8). Blackhole only. It modifies a Config word in the
  instruction stream with no RISC involved and no GPR, so a REPLAY or MOP body can step an address by itself:
  CFGSHIFTMASK(1, 3, 31, 0, 0, base word) is base += scratch[0]. With M = the low mask_width + 1 bits and r the
  rotation: word = (old, or old & ~rotr(M, r)) OP rotr(scratch & M, r). All 8 operations, both mask settings and
  the rotation match that in 96 of 96 random cases (probed).

  disable_mask_on_old_val [23]    0 first clears the target bits the mask covers. 1 leaves the old value whole.
  operation               [22:20] How the value v is combined: 0 |= v, 1 &= v, 2 ^= v, 3 += v, 4 |= ~v, 5 &= ~v,
                                  6 ^= ~v, 7 -= v.
  mask_width              [19:15] The value is the scratch word's low mask_width + 1 bits...
  right_cshift_amt        [14:10] ...rotated right by this many bits (the mask rotates with it).
  scratch_sel             [9:8]   Which scratch word: 0..2 are cfg.GLOBAL.scratch[0..2] from any thread, 3 is
                                  scratch[issuing thread]: word 209 + TRISC number (probed on all three).
  CfgReg                  [7:0]   Config word index. Never a scratch word.
  2 cycles. Follow it with a NOP before an instruction that consumes the word.
  Probed recipe: a 14-instruction REPLAY body (reset Z, STALLWAIT, 4 UNPACR to SrcA, 4 to SrcB,
  STALLWAIT(Stall.CFG, Wait.UNPACK0), this instruction on the unpacker base, 2 NOPs) read 4 consecutive tiles
  correctly with no RISC involved."""
  return tensix('CFGSHIFTMASK', disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg)

# ---- scalar unit ----
#
# Each thread has 64 32-bit Tensix GPRs (MMIO at hw.REGFILE). These instructions compute in them, so a value such as
# an L1 address can be stepped and written to config (WRCFG) without the RISC. They take 3 or 4 cycles. On Blackhole
# they do not hold back the thread's other units: STALLWAIT on Wait.THCON before another unit reads the result.

def SETDMAREG(Payload_SigSelSize=0, Payload_SigSel=0, SetSignalsMode=0, RegIndex16b=0):
  """Set half of a Tensix GPR to an immediate (scalar, 0x45). The other half is kept.

  Payload_SigSelSize [23:22] The top 2 bits of the 16-bit immediate.
  Payload_SigSel     [21:8]  Its low 14 bits. So the immediate is word bits 23:8: encode it as value << 8.
  SetSignalsMode     [7]     0. (1 is a different instruction form that reads packer state into GPRs.)
  RegIndex16b        [6:0]   2 * gpr for the low half, 2 * gpr + 1 for the high half."""
  return tensix('SETDMAREG', Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b)

def ADDDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """Add Tensix GPRs (scalar, 0x58). GPR[result] = GPR[a] + (GPR[b] or a 6-bit immediate). tt-llk steps the packer
  output address with it inside a MOP: ADDDMAREG, STALLWAIT, WRCFG, NOP. The register + register form followed by
  STALLWAIT(Stall.CFG, Wait.THCON | Wait.UNPACK0) and WRCFG stepped an unpacker base correctly (probed).

  OpBisConst     [23]    1: OpBRegIndex is an unsigned immediate, not a register.
  ResultRegIndex [22:12] Result GPR (6 bits).
  OpBRegIndex    [11:6]  Right operand: GPR or immediate.
  OpARegIndex    [5:0]   Left operand GPR.
  The sum wraps at 32 bits; both the register and the immediate form are probed."""
  return tensix('ADDDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def SUBDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """Subtract Tensix GPRs (scalar, 0x59). GPR[result] = GPR[a] - (GPR[b] or a 6-bit immediate), wrapping at 32
  bits (probed, both forms). Fields as ADDDMAREG."""
  return tensix('SUBDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def MULDMAREG(OpBisConst=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """Multiply Tensix GPRs (scalar, 0x5A). GPR[result] = low 16 bits of GPR[a] times low 16 bits of (GPR[b] or a 6-bit
  immediate), unsigned, 32-bit result (probed). Fields as ADDDMAREG."""
  return tensix('MULDMAREG', OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex)

def SHIFTDMAREG(OpBisConst=0, OpSel=0, ResultRegIndex=0, OpBRegIndex=0, OpARegIndex=0):
  """Shift a Tensix GPR (scalar, 0x5C). GPR[result] = GPR[a] shifted by GPR[b] & 31 or by a 5-bit immediate.

  OpBisConst     [23]    1: OpBRegIndex is the immediate shift amount.
  OpSel          [22:18] 1 logical right. 0 left, and so is every other value tried (2, 3, 4) (probed).
  ResultRegIndex [17:12] Result GPR.
  OpBRegIndex    [11:6]  Shift amount: GPR or immediate.
  OpARegIndex    [5:0]   Value GPR."""
  return tensix('SHIFTDMAREG', OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex)

def LOADIND(SizeSel=0, OffsetIndex=0, AutoIncSpec=0, DataRegIndex=0, AddrRegIndex=0):
  """Load from L1 into a Tensix GPR (scalar, 0x49). Reads at L1 address GPR[addr] * 16 + offset, where the offset is a
  16-bit GPR half that can post-increment. It lets a value kept in L1 (a position, an address) reach config without
  the RISC.

  SizeSel      [23:22] 0 128 bits into the four GPRs at data & ~3, 1 32 bits (address aligned to 4), 2 16 bits,
                       3 8 bits. 2 and 3 write only the low bits and keep the rest of the GPR: clear it first.
  OffsetIndex  [21:14] Half-GPR holding the byte offset (2 * gpr, + 1 for the high half; 7 bits).
  AutoIncSpec  [13:12] Add 0, 2, 4 or 16 to the offset afterwards (codes 0..3).
  DataRegIndex [11:6]  Destination GPR.
  AddrRegIndex [5:0]   GPR holding the L1 address in 16-byte units.
  The GPR is written some cycles after the instruction completes: STALLWAIT on Wait.THCON before using it.
  Sizes, alignment and the four auto-increments all match this description (probed)."""
  return tensix('LOADIND', SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex)

def STOREIND(MemHierSel=0, SizeSel=0, RegSizeSel=0, OffsetIndex=0, AutoIncSpec=0, DataRegIndex=0, AddrRegIndex=0):
  """Store Tensix GPRs to L1, to MMIO, or into a Src bank (scalar, 0x66). Three forms, chosen by word bits 23:21
  (MemHierSel, SizeSel, RegSizeSel):

  MemHierSel=1                L1: writes at GPR[addr] * 16 + offset. (SizeSel, RegSizeSel) picks the size: (0, 0) 128
                              bits from the four GPRs at data & 0x3C, (0, 1) 16 bits, (1, 0) 32 bits, (1, 1) 8 bits.
                              The ISA docs swap the 16-bit and 32-bit codes. Four back-to-back stores all landed
                              exactly. An UNPACR issued right after a store, with no STALLWAIT, reads the new
                              data (300 of 300); one issued before it reads the old data (probed).
  MemHierSel=0, SizeSel=1     MMIO (RegSizeSel=0): writes the whole GPR at
                              0xFFB00000 + ((GPR[addr] + (offset >> 4)) & 0xFFFFC), so the offset's low 4 bits are
                              ignored (probed). Addresses below 0xFFB11000 are undefined.
  MemHierSel=0, SizeSel=0     Src: writes 4 BF16 datums, the halves of GPR[data & 0x3C] and the next GPR, into SrcA
                              (RegSizeSel=0) or SrcB (RegSizeSel=1) of the bank the unpacker owns. With
                              a = GPR[addr] + (offset >> 4): columns 4 * (a & 3) .. + 3, row a >> 2 for SrcB and
                              (a >> 2) - 4 for SrcA. Do not use it (probed, SrcA): the row and columns are as
                              stated, but the first of back-to-back stores is dropped and each low-half datum v
                              arrives as (v >> 8) | ((v & 0xFE) << 7). Only the high halves are exact.
  OffsetIndex  [20:14] Half-GPR holding the 16-bit offset (2 * gpr, + 1 for the high half).
  AutoIncSpec  [13:12] Add 0, 2, 4 or 16 to the offset afterwards (codes 0..3), in every form.
  DataRegIndex [11:6]  Data GPR.
  AddrRegIndex [5:0]   Address GPR: L1 address in 16-byte units, or the MMIO word offset."""
  return tensix('STOREIND', MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex)

def LOADREG(TdmaDataRegIndex=0, RegAddr=0):
  """Read an MMIO register into a Tensix GPR (scalar, 0x68). GPR = the 32-bit word at 0xFFB00000 + (RegAddr << 2).

  TdmaDataRegIndex [23:18] Destination GPR.
  RegAddr          [17:0]  Word offset from 0xFFB00000. Addresses below 0xFFB11000 are undefined.
  The GPR is written later: STALLWAIT on Wait.THCON before using it. A GPR written with STOREREG reads back through
  this (probed)."""
  return tensix('LOADREG', TdmaDataRegIndex, RegAddr)

def STOREREG(TdmaDataRegIndex=0, RegAddr=0):
  """Write a Tensix GPR to an MMIO register (scalar, 0x67). The 32-bit word at 0xFFB00000 + (RegAddr << 2) = GPR.
  This is the pack-done signal: STALLWAIT(Stall.THCON, Wait.PACK0) then STOREREG writes the register only once the
  packs before it have finished, for example to bump a circular-buffer counter with no RISC waiting for the packer.
  Without that STALLWAIT the write lands 13..24 cycles earlier, before the pack is done (probed).

  TdmaDataRegIndex [23:18] Source GPR.
  RegAddr          [17:0]  Word offset from 0xFFB00000. Addresses below 0xFFB11000 are undefined."""
  return tensix('STOREREG', TdmaDataRegIndex, RegAddr)

# ---- address counters ----
#
# Each thread has three sets of address counters (ADCs): unpacker 0, unpacker 1 and the packer. A set has two
# channels of X, Y, Z, W counters, each with a carry/reset copy (CR). Channel 0 addresses the input (L1 for an
# unpacker, Dst for the packer) and channel 1 the output (Src or Dst for an unpacker, L1 for the packer). X on
# channel 0 is the first datum and X on channel 1 the last datum, inclusive, of the range an instruction moves: for an
# unpacker datums of the L1 tile, for the packer columns of each Dst row. Nothing checks these counters. Three settings
# give wrong data with no error (probed): a packer channel-0 Y that is not a multiple of 4 packs fewer rows, a packer
# channel-1 X past 15 wraps mod 16 and shrinks every row, and an unpacker channel-1 X past x_dim - 1 reads on into
# the next tile and overwrites the start of Src.
# CntSetMask picks the sets: 1 unpacker 0, 2 unpacker 1, 4 packer.

def SETADC(CntSetMask=0, ChannelIndex=0, DimensionIndex=0, Value=0):
  """Set one address counter (ADC, 0x50). Sets the counter and its CR copy.

  CntSetMask     [23:21] 1 unpacker 0, 2 unpacker 1, 4 packer.
  ChannelIndex   [20]    Channel 0 or 1.
  DimensionIndex [19:18] 0 X, 1 Y, 2 Z, 3 W.
  Value          [17:0]  New value. Use 16 bits: a non-zero value in bits 17:16 redirects the write to another
                         thread's counters, which is unsupported."""
  return tensix('SETADC', CntSetMask, ChannelIndex, DimensionIndex, Value)

def SETADCXX(CntSetMask=0, x_end2=0, x_start=0):
  """Set both X counters (ADC, 0x5E). The datum range the next unpack or pack instructions move.

  CntSetMask [23:21] 1 unpacker 0, 2 unpacker 1, 4 packer.
  x_end2     [20:10] Channel 1 X: the last datum, count minus 1 (10 bits).
  x_start    [9:0]   Channel 0 X: the first datum."""
  return tensix('SETADCXX', CntSetMask, x_end2, x_start)

def SETADCXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=0):
  """Set X and Y counters (ADC, 0x51). Each selected counter and its CR copy get a 3-bit value.

  CntSetMask [23:21] 1 unpacker 0, 2 unpacker 1, 4 packer.
  Ch1_Y      [20:15] Channel 1 Y (3 bits).
  Ch1_X      [14:12] Channel 1 X.
  Ch0_Y      [11:9]  Channel 0 Y.
  Ch0_X      [8:6]   Channel 0 X.
  BitMask    [5:0]   Which to set: 1 Ch0 X, 2 Ch0 Y, 4 Ch1 X, 8 Ch1 Y.
  Leave channel-1 X alone (no BitMask bit 2): it is the last datum of the range. Clearing it makes the packer pack
  1 datum per row and makes every unpack return garbage, with no error (probed with mask 15). Reset the packer's
  counters with mask 11 (as ttrv does) and an unpacker's Y counters with mask 10."""
  return tensix('SETADCXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask)

def SETADCZW(CntSetMask=0, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=0):
  """Set Z and W counters (ADC, 0x54). As SETADCXY with Z for X and W for Y.

  BitMask [5:0] Which to set: 1 Ch0 Z, 2 Ch0 W, 4 Ch1 Z, 8 Ch1 W."""
  return tensix('SETADCZW', CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask)

def INCADCXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0):
  """Increment X and Y counters (ADC, 0x52). Adds each 3-bit value to its counter; the CR copies are not touched.
  Fields as SETADCXY, without a mask (0 leaves a counter alone). A change takes effect at the next new address.
  Packer (probed): Ch1_Y += n moves the L1 output by n * l1_y_stride. Ch0_X += k shifts the Dst read by k columns.
    Ch0_Y is the Dst row a PACR starts at, and a PACR reads from there to the end of its aligned 4-row group, rows
    Y .. Y | 3. So step Ch0_Y by 4 only: off a multiple of 4 each PACR reads 3, 2 or 1 rows, the address modifier's
    +4 keeps the misalignment, and a 16-PACR tile writes 48, 32 or 16 rows and leaves the rest empty.
  Unpacker (probed with y_dim=1, x_dim=1024): Ch0_Y += 1 reads the next tile."""
  return tensix('INCADCXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X)

def INCADCZW(CntSetMask=0, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0):
  """Increment Z and W counters (ADC, 0x55). Adds each value to its counter; the CR copies are not touched. Fields
  as SETADCZW, without a mask (0 leaves a counter alone). A change takes effect at the next new address. W has no
  address-modifier increment, so this (or SETADC) is how W steps.
  Packer (probed): Ch1_Z += n moves the L1 output by n * l1_z_stride and Ch1_W by n * l1_w_stride. Ch0_W += 1 steps
    the Dst read one tile, Ch0_Z += 4 steps it 4 faces. So INCADCZW(4, Ch1_Z=1, Ch0_W=1) after a tile's Last PACR
    moves both the output address and the Dst tile, with one l1_dest_addr write for the whole run: 8 FP32 tiles
    packed exactly, at 55 cycles a tile as the end op of a template-1 MOP, 66 from a REPLAY, 172 pushed by the RISC.
  Unpacker (probed with z_dim 1, 2 and 4): the L1 read position is base + (Z * x_dim * y_dim + W * x_dim * y_dim *
    z_dim) datums, so Ch0_Z += 1 steps one face and Ch0_W += 1 one whole tile, and the two add. A REPLAY of
    STALLWAIT, UNPACR, INCADCZW(1, Ch0_Z=1) read 4 consecutive single-face tiles correctly."""
  return tensix('INCADCZW', CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z)

def ADDRCRXY(CntSetMask=0, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=0):
  """Advance X and Y from their CR copies (ADC, 0x53). For each counter whose BitMask bit is set: CR += value, then
  counter = CR. With a value of 0 it restores the counter from its CR copy, undoing INCADCXY steps and
  address-modifier increments. BitMask 0 does nothing. Fields as SETADCXY. Probed for all four counters.
  Packer: Ch0_X is the first Dst column read (it accumulates across tiles) and Ch1_X the last, inclusive and mod 16.
    SETADCXX sets Ch1_X to 15, so adding k to it leaves k datums per row.
  Unpacker: Ch0_X is the first L1 datum read and Ch1_X the last, inclusive. Ch1_X past x_dim - 1 reads into the next
    tile and wraps into Src row 0.
  UNCERTAIN: in one unpacker run that moved Ch0_X, the contiguous read broke at datum 256. Not explained."""
  return tensix('ADDRCRXY', CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask)

def ADDRCRZW(CntSetMask=0, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=0):
  """Advance Z and W from their CR copies (ADC, 0x56). As ADDRCRXY, fields as SETADCZW: for each counter whose BitMask
  bit is set, CR += value, then counter = CR; BitMask 0 does nothing (probed). An INCADCZW followed by
  ADDRCRZW with value 0 snaps the counter back to its CR. ADDRCRZW(4, Ch1_Z=1, Ch0_W=1, BitMask=6) as a MOP end op
  steps the packer's output address and Dst tile like INCADCZW does (probed)."""
  return tensix('ADDRCRZW', CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask)

# ---- unpack, pack, mover ----

def UNPACR(Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=0,
           SetDatValid=0, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=0):
  """Unpack L1 into Src or Dst (unpack, 0x42). Moves the datum range channel-0 X .. channel-1 X of the selected
  unpacker's ADC, converting between the configured formats. ttrv issues
  UNPACR(i, AddrMode, 0, ctx, 0, 1, dvalid, 0, 0, 0, 0, 0, 1).

  Unpack_block_selection [23]    0 unpacker 0 (to SrcA, or straight to Dst), 1 unpacker 1 (to SrcB).
  AddrMode               [22:15] Counter steps applied afterwards, 2 bits each: bits 1:0 channel 0 Z (input), 3:2
                                 channel 0 Y, 5:4 channel 1 Z (output), 7:6 channel 1 Y. ttrv's 0x11 steps both Zs to
                                 the next face.
  CfgContextCntInc       [14:13] Keep 0. 1 is a different instruction form that only steps the context counter.
  CfgContextId           [12:10] Config context: which cfg.UNPACK[i] per-context fields apply (0..7; 0..1 for
                                 unpacker 1, higher ones hang). Formats and addresses switch per UNPACR with no
                                 reconfiguration, but the contexts of one stream must share a Src datum width
                                 (probed; see cfg.UnpackerCfg).
  AddrCntContextId       [9:8]   Whose ADC supplies X and Y: keep 0 for this thread's.
  OvrdThreadId           [7]     1 = use the per-context config. Always 1: the docs call the 0 form unsupported.
  SetDatValid            [6]     1 hands the filled bank to math afterwards and switches the unpacker to the other
                                 bank. It also records the output format as the format the FPU will use for the bank.
                                 Set it on the tile's last UNPACR: it is the only way to hand unpacked data over
                                 (UNPACR_NOP's Set_Dvalid form zero-fills the bank).
  srcb_bcast             [5]     1 fills SrcB row r from L1 row r & ~3, so each group of 4 rows repeats its first
                                 row (probed over all 64 rows).
  ZeroWrite2             [4]     1 writes zeros instead of the unpacked data (probed).
  AutoIncContextID       [3]     1 takes the context from the context counter and steps it. Keep 0: unsupported.
  RowSearch              [2]     Keep 0.
  SearchCacheFlush       [1]     Keep 0. 1 is a different instruction form.
  Last                   [0]     ttrv and tt-llk pass 1. 0 and 1 give the same data in the same time (probed).
  L1 address read: (base_addr[ctx] + offset_addr[ctx & 3] + 1) * 16, then past a BFP exponent section, plus the datum
  index (((W * z_dim + Z) * y_dim + Y) * x_dim + X) times the datum size, with X, Y, Z, W the channel-0 counters (low 8
  bits of Y, Z, W). There are no input strides.
  Consecutive tiles without the RISC rewriting the base per tile (all probed):
    - Let channel-0 Z keep counting past z_dim and reset only channel-1 Z per tile (SETADCZW BitMask=4). BF16: 4 tiles
      in 524 cycles against 708 with a base rewrite per tile. Not for BFP8 stored as [exponents][data] per tile: only
      tile 0 comes out right.
    - Step offset_addr with an RMWCIB pair per tile, with no extra stall. Any format; BFP8: 621 against 708.
    - Step base_addr itself inside a REPLAY body with CFGSHIFTMASK.
    - Step channel-0 Z with INCADCZW after each tile's UNPACRs, also inside a REPLAY.
  Hangs (probed): plain data with the context's disable_zero_compress=0, and BFP8 in L1 into a FLOAT16_B Src.
  Unpacker 0 writing Dst clobbers its SrcA bank. Before unpacker 0 fills SrcA again after an unpack to Dst, STALLWAIT
  on Wait.UNPACK0, or Dst rows leak into SrcA."""
  return tensix('UNPACR', Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId,
                OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last)

def UNPACR_NOP(Unpacker_Select=0, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=0, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0,
               Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=0):
  """Unpacker-ordered control action (unpack, 0x43). Runs in order with that unpacker's UNPACRs. Blackhole's encoding
  is its own; the Wormhole pages do not apply.

  Unpacker_Select  [23]    0 unpacker 0, 1 unpacker 1.
  Stream_Id        [22:16] Keep 0 (NoC overlay).
  Msg_Clr_Cnt      [15:12] Keep 0 (NoC overlay).
  Set_Dvalid       [11:8]  1 hands the bank to math afterwards, without resetting the Src row pointer. Only with
                           Unpack_Pop=1, which fills the bank first: with Unpack_Pop 0 or 2 the bank is never handed
                           over and the core hangs, across reloads, until a card reset (probed).
  Clr_to1_fmt_Ctrl [7:6]   Keep 0.
  Stall_Clr_Cntrl  [5]     1 waits on the unpacker's own bank like an UNPACR, 0 on the bank math is using.
  Bank_Clr_Ctrl    [4]     Keep 0 (both banks; races).
  Src_ClrVal_Ctrl  [3:2]   Fill value for mode 1: 0 zero, 1 negative infinity (SrcA only).
  Unpack_Pop       [1:0]   Mode: 1 clear Src, 2 do nothing for one unpacker slot. 0 and 3 are NoC overlay actions.
  Two forms are useful: (i, 0, 0, 0, 0, 0, 0, 0, 2) is an unpacker-ordered no-op between config writes, and
  (i, 0, 0, 1, 0, 0, 0, 0, 1) hands math a bank of zeros (of -inf / NaN with Src_ClrVal_Ctrl=1). The second one does
  not publish what was unpacked: the fill overwrites all 64 rows first (probed). ttrv's unpack.dvalid is this form,
  and no kernel uses it. To hand over unpacked data, set SetDatValid on the last UNPACR."""
  return tensix('UNPACR_NOP', Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl,
                Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop)

def PACR(*args, **fields):
  """Pack Dst into L1 (pack, 0x41). Reads up to four 16-datum Dst rows, converts them and appends them to the L1
  output. Formats, ReLU, edge masks, strides and the output address come from cfg.PACK.

  CfgContext     [23:21] Packer config context 0..3 (2 bits): which cfg.PACK.ctx[...] applies (output address,
                         formats, exponent section size, l1_acc, pack counters, Dst offset). All four work in one
                         stream, as long as their in_fmts have the same width (probed; see cfg.PackCtx).
  RowPadZero     [20:18] Zero padding of short rows. Keep 0.
  DstAccessMode  [17]    1 reads Dst rows 8 apart instead of adjacent. Keep 0.
  AddrMode       [16:15] Packer address-modifier slot (cfg.PACK_ADDR_MOD[0..3]) applied afterwards: steps Y / Z of
                         channel 0 (the Dst rows read) and channel 1 (the L1 output position).
  AddrCntContext [14:13] With OvrdThreadId: use that thread's ADC (0..2).
  ZeroWrite      [12]    1 packs zeros instead of reading Dst. With ReadIntfSel=0 it packs channel-1 X + 1 zeros.
  ReadIntfSel    [11:8]  Which of the 4 Dst rows at the current position to read, one bit per row. 0 means all four.
  OvrdThreadId   [7]     Keep 0.
  Concat         [6:4]   Keep 0 (compression).
  CtxtCtrl       [3:2]   1: take the context from the packer's context counter instead of CfgContext; the counter
                         steps 0, 1, 2, 3, 0 after each PACR with Last. 2: pack nothing and reset that counter
                         (both probed).
  Flush          [1]     Keep 0. Undefined on Blackhole once any PACR has run: the packer never goes idle.
  Last           [0]     1 ends the tile: flushes the output, and makes the next PACR compute a new output address.
  Output address. Only the first PACR after a Last (or after reset) computes it; the PACRs after it append. It is
    (l1_dest_addr + 1) * 16 + Y * l1_y_stride + Z * l1_z_stride + W * l1_w_stride, in bytes, with Y, Z, W the
    channel-1 counters and the strides multiples of 16 (probed for all three).
    Self-advance (probed, FP32 / BF16 / BFP8): write l1_dest_addr once, set l1_z_stride to the tile's size in L1, and
    give the tile's Last PACR an address-modifier slot with ydst_clear and zdst_incr=1. Each tile then lands after
    the one before with no address rewrite, 26..30 cycles a tile cheaper when the PACRs come from a MOP. zdst_clear
    returns to the base. For the Dst side, either the slot also has ysrc_clear and zsrc_clear and a SETADC sets
    channel-0 W to the tile index before each tile, or it has ysrc_incr=4 in place of ysrc_clear and the Dst rows
    keep counting into the next tile with no instruction between tiles.
    INCADCZW after the Last PACR does the same job in one instruction, stepping the output address and the Dst tile
    together, at 55 cycles a tile from a MOP against 50 for the address-modifier slot plus its SETADC.
    With converted output, do not change those counters or l1_dest_addr while a tile is being packed.
  A non-Last PACR can hold its output until the next PACR: a STALLWAIT on Wait.PACK0 after it may never finish. End
  every sequence with Last.
  A RISC pushing PACRs back to back is stalled until the packer drains, so a pushed loop is bound by the push rate.
  Do not ZEROACC or SFPSTORE into rows within about 3 instructions after the PACR that reads them."""
  return tensix('PACR', *args, **fields)

def XMOV(Mov_block_selection=0, Last=0):
  """Start the mover (mover, 0x40). An asynchronous copy or zero-fill in 16-byte units, set up in cfg.MOVER. It can
  zero an L1 region (to start an l1_acc accumulation) or copy L1 to L1 without a RISC loop.

  Both operands are 0. Wait for it with STALLWAIT on Wait.XMOV. Copy and zero-fill are exact, at about 11 and 14
  bytes per cycle (probed)."""
  return tensix('XMOV', Mov_block_selection, Last)

# ---- FPU (Matrix Unit) ----
#
# Latency: 5 cycles for MVMUL, ELW*, GAPOOL, GMPOOL; 4 for MOVA2D, MOVB2D, MOVB2A; 2 for MOVD2A; 1 for the rest.
# An 8-row Dst block an arithmetic instruction wrote cannot be read back by the FPU for 5 cycles (hardware stalls), so
# loop over at least 6 distinct blocks. The packer and the SFPU do not get that stall: STALLWAIT on Wait.MATH before
# PACR or SFPLOAD touches rows the FPU has just written.
#
# Shared operands. A Dst row operand is added to cfg.THREAD.dst_offset and the Dst RWC. clear_dvalid releases Src banks
# to the unpackers once the instruction is done. addr_mode names one of the 8 slots of cfg.ADDR_MOD, whose increments
# are applied to the SrcA / SrcB / Dst RWCs and the fidelity phase afterwards; slot 0 is kept all-zero.

def MVMUL(clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0):
  """Matrix multiply-accumulate (FPU, 0x26). Dst[8 x 16] += SrcB[8 x 16] @ SrcA[16 x 16]. A 32 x 32 tile product is a
  sequence of these. It always accumulates: ZEROACC the block first for a plain product.

  clear_dvalid [23:22] Src banks to release afterwards: 1 SrcA, 2 SrcB, 3 both.
  instr_mod19  [21:19] 0 normal. 1 uses a single SrcB row (RWC.SrcB & 0x3f) for the whole block and writes only Dst
                       rows +0, +2, +4, +6; read the results from rows +0, +4 or +6.
  addr_mode    [18:14] Address-modifier slot applied afterwards (0..7; only the low 3 bits are read).
  dst          [13:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC, then aligned down to 8. Keep bit 2
                       clear: with it set, rows 0..3 of the block are read raw even when ZEROACC'd.
  Rows: SrcB is the 8 rows at RWC.SrcB & 0x38, SrcA the 16 rows at RWC.SrcA & 0x30. There is no Src row operand.
  Fidelity: each instruction multiplies at most 5 bits of SrcA by 7 bits of SrcB, chosen by the fidelity phase (the
  fidelity RWC plus THREAD.fidelity_phase; bit 0 picks the SrcA part, bit 1 the SrcB part). One pass per phase, 1
  cycle each: phase 0 alone is the coarsest BF16 product, phases 0+1 are the usual choice, all four use every bit of
  both operands. Maximum error on random BF16 data in +-4 with 1 / 2 / 3 / 4 phases: 1.29 / 0.198 / 0.0088 / 0.0086
  (probed). An SrcB of ones or small integers needs only phases 0+1.
  Summation: even with all phases the 16 products of a column are added aligned to the largest one, keeping about 12
  bits below it. Terms of similar magnitude add exactly; terms 2^-8 .. 2^-11 of the largest can be off by up to 40%,
  and terms below about 2^-12 of it vanish (probed; the rounding rule is not modelled).
  Formats: the FPU works in the format the unpacker handed over with the SrcA bank, for both operands (probed for the
  elementwise ops). See cfg.MATH.srca_fmt."""
  return tensix('MVMUL', clear_dvalid, instr_mod19, addr_mode, dst)

def ELWADD(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise add (FPU, 0x28). Dst[8 x 16] = SrcA[8 x 16] + SrcB[8 x 16], or Dst += that.

  clear_dvalid  [23:22] Src banks to release afterwards: 1 SrcA, 2 SrcB, 3 both.
  dest_accum_en [21]    0 overwrites Dst, 1 adds the result to Dst.
  instr_mod19   [20:19] SrcB broadcast (isa.Broadcast): 0 none, 1 column 0 to every column, 2 one row to all 8 rows,
                        3 one scalar.
  addr_mode     [18:14] Address-modifier slot applied afterwards (0..7).
  dst           [13:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC, then aligned down to 8.
  Rows: SrcA is the 8 rows at RWC.SrcA & 0x38, SrcB the 8 rows at RWC.SrcB & 0x38.
  Needs fidelity phase 0. The format is the one handed over with the SrcA bank, for both operands (probed)."""
  return tensix('ELWADD', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def ELWSUB(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise subtract (FPU, 0x30). Dst[8 x 16] = SrcA[8 x 16] - SrcB[8 x 16], or Dst += that. Fields, rows and
  rules as ELWADD."""
  return tensix('ELWSUB', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def ELWMUL(clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0):
  """Elementwise multiply (FPU, 0x27). Dst[8 x 16] += SrcA[8 x 16] * SrcB[8 x 16], one pass per fidelity phase as for
  MVMUL. Fields and rows as ELWADD.

  dest_accum_en [21]  Ignored: ELWMUL always accumulates, Dst += SrcA * SrcB, with the bit 0 or 1 (probed). ZEROACC
                      the block first for a plain product."""
  return tensix('ELWMUL', clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst)

def GAPOOL(clear_dvalid=0, instr_mod19=0, pool_addr_mode=0, max_pool_index_en=0, dst=0):
  """Four-row matrix multiply-accumulate (FPU, 0x34). Dst[4 x 16] += SrcB[4 x 16] @ SrcA[16 x 16]: MVMUL with half the
  rows and half the throughput. With SrcB holding ones it sums the 16 SrcA rows of each column. The 4 Dst rows after
  the block are left alone (probed). Same dot-product datapath, precision and cost as MVMUL (probed): one
  instruction is one fidelity phase, and phase 0 alone sees 5 significant bits of SrcA and 7 of SrcB (1.9921875 * 3
  gave 5.8125). Run 2 phases for an all-ones or small-integer SrcB, which is what a column sum needs, and 3 or 4
  for arbitrary BF16 SrcB. The sum itself is then limited as described under MVMUL.

  clear_dvalid      [23:22] Src banks to release afterwards: 1 SrcA, 2 SrcB, 3 both.
  instr_mod19       [21:19] No effect, 0..7 (probed). The docs and tt-llk pass 1 (tt-llk: DIM_16X16).
  pool_addr_mode    [18:15] Address-modifier slot applied afterwards (0..7, in bits 17:15).
  max_pool_index_en [14]    Keep 0.
  dst               [13:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC, then aligned down to 4.
  Rows: SrcB is the first 4 rows of the 8-row block at RWC.SrcB & 0x38, SrcA the 16 rows at RWC.SrcA & 0x30."""
  return tensix('GAPOOL', clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst)

def GMPOOL(clear_dvalid=0, instr_mod19=0, pool_addr_mode=0, max_pool_index_en=0, dst=0):
  """Column-wise maximum (FPU, 0x33). For each column, the maximum over the 16 SrcA rows at RWC.SrcA & 0x30, max'ed
  with one Dst row: Dst[r] = max(Dst[r], column max). The other three rows of that 4-row Dst block are written 0
  (probed). No fidelity phases.

  clear_dvalid      [23:22] Src banks to release afterwards: 1 SrcA, 2 SrcB, 3 both.
  instr_mod19       [21:19] No effect (probed). The docs and tt-llk pass 1.
  pool_addr_mode    [18:15] Address-modifier slot applied afterwards (0..7, in bits 17:15).
  max_pool_index_en [14]    Keep 0. There is no argmax on Blackhole: the maximum is still right, but no index is
                            written (the low bits are 0 in a 32-bit Dst, untouched in a 16-bit one) (probed).
  dst               [13:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC, then aligned down to 4.
  SrcB scales the input: SrcA row i is multiplied by 2^(exponent of SrcB[RWC.SrcB & 0x38][i]) (probed with powers of
  two), so fill that SrcB row with 1.0 for a plain maximum. A ZEROACC'd Dst row reads as -inf here, so no explicit
  initialisation is needed."""
  return tensix('GMPOOL', clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst)

def MOVA2D(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move SrcA to Dst (FPU, 0x12). Waits for the SrcA bank, then copies 1 row or an aligned 8 rows of 16 columns.

  dest_32b_lo [23]    Keep 0. Writing only the low half of a 32-bit Dst datum corrupts data (TEN-4245).
  src         [22:17] SrcA row (6 bits), added to the SrcA RWC.
  addr_mode   [16:14] Address-modifier slot applied afterwards (0..7).
  instr_mod   [13:12] 0 moves one row, 2 moves 8 rows.
  dst         [11:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC.
  With cfg.MATH.fp32_dst_acc=1 the move writes 32-bit Dst datums. Use the 8-row form: the one-row form moves zeros
  for source rows 16..31 and 48..63, and is undefined with an odd addr_mode slot. The rows written must not be read for
  3 cycles; the FPU stalls by itself, PACR and SFPLOAD need a STALLWAIT on Wait.MATH."""
  return tensix('MOVA2D', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVB2D(dest_32b_lo=0, src=0, addr_mode=0, movb2d_instr_mod=0, dst=0):
  """Move SrcB to Dst (FPU, 0x13). Waits for the SrcB bank, then copies rows of 16 columns, optionally broadcasting.

  dest_32b_lo      [23]    Keep 0 (as MOVA2D).
  src              [22:17] SrcB row (6 bits), added to the SrcB RWC.
  addr_mode        [16:14] Address-modifier slot applied afterwards (0..7).
  movb2d_instr_mod [13:11] Flags: 4 moves an aligned 4 rows instead of one, 2 broadcasts one SrcB row to an aligned 8
                           Dst rows, 1 broadcasts column 0 to all 16 columns.
  dst              [10:0]  Dst row (10 bits), added to THREAD.dst_offset and the Dst RWC.
  The 32-bit Dst write and the 3-cycle read rule are as MOVA2D."""
  return tensix('MOVB2D', dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst)

def MOVD2A(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move Dst to SrcA (FPU, 0x08). Copies 1 row or an aligned 4 rows of 16 columns from Dst into the SrcA bank math
  owns, so a result can feed the next FPU instruction without a pack and unpack through L1.

  dest_32b_lo [23]    1 takes the low 16 bits of a 32-bit Dst datum. Normally 0.
  src         [22:17] SrcA row written (6 bits), added to the SrcA RWC. Must be a multiple of 4 for a 4-row move.
  addr_mode   [16:14] Address-modifier slot applied afterwards (0..7).
  instr_mod   [13:12] 0 moves one row, 2 moves 4 rows.
  dst         [11:0]  Dst row read (10 bits), added to THREAD.dst_offset and the Dst RWC.
  FP32 and BF16 Dst data arrive in SrcA as BF16 (or TF32), in the format the unpacker last handed over with that bank
  unless cfg.THREAD.disable_implied_srca=1 selects cfg.MATH.srca_fmt. Sixteen 4-row moves from an FP32 Dst followed by
  ELWADD were exact with disable_implied_srca 0 and 1 (probed). It does not wait for the bank:
  STALLWAIT(Stall.MATH, Wait.SRCA_VLD) first, or it races the unpacker."""
  return tensix('MOVD2A', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVD2B(dest_32b_lo=0, src=0, addr_mode=0, instr_mod=0, dst=0):
  """Move Dst to SrcB (FPU, 0x0A). As MOVD2A, into the SrcB bank math owns; wait on Wait.SRCB_VLD. The conversion
  format is still chosen by the SrcA format settings. For 3 cycles afterwards the FPU accepts only another MOVD2B.
  Exact, like MOVD2A (probed). tt-llk issues GATESRCRST after it; that does nothing (see "Not covered")."""
  return tensix('MOVD2B', dest_32b_lo, src, addr_mode, instr_mod, dst)

def MOVB2A(srca=0, addr_mode=0, instr_mod=0, srcb=0):
  """Move SrcB to SrcA (FPU, 0x0B). Waits for the SrcB bank (not SrcA), then copies 1 row or an aligned 4 rows.

  srca      [23:17] SrcA row written (6 bits), added to the SrcA RWC. Must be a multiple of 4 for a 4-row move.
  addr_mode [16:14] Address-modifier slot applied afterwards (0..7).
  instr_mod [13:12] 0 moves one row, 2 moves 4 rows.
  srcb      [11:0]  SrcB row read (6 bits), added to the SrcB RWC.
  A full 64-row copy is exact (probed). The docs list an erratum, SrcA rows first+4 .. first+7 of the same 16-row
  group coming out zeroed; 24 runs did not reproduce it (1-row and 4-row moves, with and without a STALLWAIT, right
  after an ELWADD). The docs also say it must not start exactly 3 cycles after an arithmetic instruction starts:
  STALLWAIT(Stall.MATH, Wait.MATH) first."""
  return tensix('MOVB2A', srca, addr_mode, instr_mod, srcb)

def TRNSPSRCB():
  """Transpose SrcB rows 16..31 (FPU, 0x16). Waits for the SrcB bank, then transposes in place the 16 x 16 block in
  rows 16..31 of the bank math owns; the other rows are untouched (probed). No operands. Nothing is
  needed after it before the FPU reads SrcB. The SrcB RWC fields are 4 bits, so reaching row 16 takes two INCRWC +8."""
  return tensix('TRNSPSRCB')

def ZEROACC(clear_mode=0, use_32_bit_mode=0, clear_zero_flags=0, addr_mode=0, where=0):
  """Mark Dst rows as zero (FPU, 0x10). No data is written: the rows are flagged undefined, and from then on the FPU
  reads them as 0 (GMPOOL as -inf) and the packer reads them as 0.

  clear_mode       [23:19] 0 one row, 1 one 16-row face, 2 half of Dst, 3 all of Dst. 4 and up are undefined.
  use_32_bit_mode  [18]    1 when Dst holds 32-bit rows (cfg.MATH.fp32_dst_acc), 0 for 16-bit rows.
  clear_zero_flags [17]    Keep 0. 1 does the opposite: it marks the rows defined again without writing them.
  addr_mode        [16:14] Address-modifier slot applied afterwards (0..7), in modes 0 and 1 only.
  where            [13:0]  Mode 0: Dst row. Mode 1: face index. Mode 2: bit 0 picks the upper half. 10 bits are used.
  The face index of mode 1 counts from the Dst half that THREAD.dst_offset points into, or from Dst row 0 when
  cfg.GLOBAL.zeroacc_abs_tile_mode=1 (probed).
  The SFPU must not SFPLOAD a row in this state, nor SFPSTORE into only some of its columns: store whole rows first.
  A ZEROACC in the same cycle as an SFPU or unpacker write to Dst wins, and that write's rows stay flagged."""
  return tensix('ZEROACC', clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where)

def ZEROSRC(zero_val=0, write_mode=0, bank_mask=0, src_mask=0):
  """Clear Src banks (FPU, 0x11). Sets all 64 rows of the selected SrcA / SrcB banks to 0.

  zero_val   [23:4] 0 writes zeros. 1 writes negative infinity to SrcA instead.
  write_mode [3]    Which single bank: 1 the one math owns, 0 the one the unpacker owns.
  bank_mask  [2]    1 clears both banks and ignores write_mode.
  src_mask   [1:0]  1 SrcA, 2 SrcB, 3 both.
  It does not wait for the unpackers: STALLWAIT on Wait.UNPACK0 / Wait.UNPACK1 first. Src contents and pointers survive
  a kernel reload, so the probes issue it at start (probed)."""
  return tensix('ZEROSRC', zero_val, write_mode, bank_mask, src_mask)

def CLEARDVALID(cleardvalid=0, reset=0):
  """Release Src banks to the unpackers (FPU, 0x36). Hands the selected banks math owns back to the unpackers and
  switches math to the other bank of each.

  cleardvalid [23:22] 1 SrcA, 2 SrcB, 3 both.
  reset       [21:0]  Bit 1: release the bank but keep reading it (no switch). Bit 0: reset the Src bank state. The docs
                      call the reset unsupported (nondeterministic hangs); boot issues it once on an idle tile.
  With cfg.THREAD.disable_clr_dvalid_a/b set, the switch happens but the bank stays with math (probed)."""
  return tensix('CLEARDVALID', cleardvalid, reset)

def SETRWC(clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=0):
  """Set math read/write counters (FPU, 0x37). Sets the selected SrcA, SrcB and Dst row counters, optionally resets
  the fidelity phase, and optionally releases Src banks.

  clear_ab_vld [23:22] Src banks to release: 1 SrcA, 2 SrcB, 3 both (as CLEARDVALID).
  rwc_cr       [21:18] 1 SrcA, 2 SrcB, 4 Dst: the value is added to that counter's carry/reset copy instead of
                       replacing the counter. 8: for Dst, add to the current counter instead.
  rwc_d        [17:14] Dst value (4 bits).
  rwc_b        [13:10] SrcB value (4 bits).
  rwc_a        [9:6]   SrcA value (4 bits).
  BitMask      [5:0]   Which to set: 1 SrcA, 2 SrcB, 4 Dst, 8 fidelity phase to 0. 15 with zero values resets all four.
                       16 sets the SFPU stack pointer instead, to (rwc_d & 3) << 8 | rwc_b << 4 | rwc_a.
  SFPU Dst addresses include the Dst RWC too: after FPU instructions that advance it, reset it before SFPLOAD or
  SFPSTORE, or they land that many rows off (probed)."""
  return tensix('SETRWC', clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask)

def INCRWC(rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0):
  """Increment math read/write counters (FPU, 0x38). Advances the SrcA, SrcB and Dst row counters.

  rwc_cr [23:18] 1 SrcA, 2 SrcB, 4 Dst: increment that counter's carry/reset copy and reload the counter from it.
                 With the bit clear only the counter itself advances.
  rwc_d  [17:14] Dst increment (4 bits).
  rwc_b  [13:10] SrcB increment (4 bits).
  rwc_a  [9:6]   SrcA increment (4 bits). A step of 16 or more takes several INCRWCs."""
  return tensix('INCRWC', rwc_cr, rwc_d, rwc_b, rwc_a)

# ---- SFPU (Vector Unit) ----
#
# An LReg holds 32 lanes of 32 bits: 4 rows of 8, covering the even or the odd columns of 4 consecutive Dst rows.
# Operands named lreg_* take isa.LReg numbers. Results are written only to L0..L7, and only in enabled lanes: a lane
# is enabled unless predication is on (SFPENCC) and its condition flag is clear.
# A destination of 12..15 does not execute the instruction: it records the instruction word as SFPLOADMACRO template
# (destination - 12) instead. SFPCONFIG and SFPLOADMACRO are the exceptions.
#
# Scheduling (measured on Blackhole A0 card 1 across 46 producers x 70 consumers, boop-docs/probes/model.py):
# The SFPU accepts one instruction per cycle. Only the MAD column has 2-cycle latency: SFPMAD, SFPMUL, SFPADD,
# SFPMULI, SFPADDI, SFPMUL24, SFPLUT, SFPLUTFP32. Everything else has 1-cycle latency.
# SFPSWAP (all modes) and SFPSHFT2 (modes 2, 3, 4) have 1-cycle latency but hold the issue slot an extra cycle
# (hardware auto-stalls the next non-SFPNOP SFPU op).
# Hardware stalls most RAW hazards after a 2-cycle MAD-column producer; it misses these readers, which need one
# SFPNOP (or any unrelated instruction) in between:
#   - SFPIADD register forms (mod1 & 1 == 0): VD read
#   - SFPSHFT register-shift form only (mod1 & 1 == 0; immediate forms are detected): VD read
#   - SFPAND / SFPOR with instr_mod1=1 (USE_VB): VB read
#   - SFPARECIP mode 1: VB read
#   - SFPSETEXP / SFPSETMAN / SFPSETSGN without the immediate flag: VD read
#   - SFPSWAP modes != 0 (mode 0 is safe): VC/VD compare read
#   - SFPSHFT2 modes 2..4 (VC, plus L1..L3 for mode 2) and modes 5..6 (VB)
#   - SFPCONFIG without immediate: L0 read
#   - SFPLOADI in UPPER / LOWER mode (8/10) and SFPLOAD in HI16_ONLY / LO16_ONLY mode (14/15) into the same register
#     (corrupts the whole register, not only the preserved half)
# WAW (2-cycle producer then 1-cycle writer to the same reg) needs nothing; the later write wins.
# None of this applies inside an SFPLOADMACRO sequence: there the delays are entirely the program's job, a regular
# instruction that lands on a busy sub-unit is silently dropped, and an SFPNOP must follow any SFPCONFIG that changes a
# template, a sequence, the macro control word, or DISABLE_BACKDOOR_LOAD.
# Note: L12..L14 and LaneConfig.DISABLE_BACKDOOR_LOAD carry over across kernel launches (firmware resets only L11/ENCC).
# Dst hand-off: after an FPU write to the same Dst rows, put 3 unrelated Tensix instructions or a
# STALLWAIT(Stall.SFPU, Wait.MATH) before SFPLOAD. An SFPSTORE within about 3 instructions after a PACR can overwrite
# rows that PACR has not read yet.

def SFPLOAD(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Load Dst into an LReg (SFPU, 0x70). Reads 32 values from Dst, converting from the selected storage format.

  lreg_ind       [23:20] Destination L0..L7. 8 and up load nothing and only apply the address modifier.
  instr_mod0     [19:16] Storage format (isa.SfpuFormat).
  sfpu_addr_mode [15:13] Address-modifier slot applied afterwards (0..7). It moves the RWCs but not the fidelity phase.
  dest_reg_addr  [12:0]  Dst address (10 bits), added to THREAD.dst_offset and the Dst RWC. Bits 9:2 pick an aligned
                         group of 4 rows, bit 1 picks the odd columns, bit 0 is unused.
  Lane n reads row (address & ~3) + n // 8, column 2 * (n % 8), plus 1 for the odd columns.
  The Dst RWC is part of the address: reset it (SETRWC) after FPU instructions that advance it (probed).
  Loading a row that ZEROACC flagged and nothing has written since is undefined."""
  return tensix('SFPLOAD', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPSTORE(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Store an LReg into Dst (SFPU, 0x72). Writes the enabled lanes into Dst in the selected storage format. Fields,
  addressing and lane layout as SFPLOAD; lreg_ind is the source and may be a constant register.

  FP32 and BF16 stores flush denormals to zero and BF16 / FP16 stores truncate. An FP32 store turns every value whose
  exponent field is 0 into +-0, which destroys small integers such as SFPLZ counts and SFPMUL24 products (probed):
  store integers and raw bits with SfpuFormat.INT32. An FP32 SFPLOAD is raw.
  A store marks all 4 rows of its group defined, including rows whose lanes are disabled: those then read as their old
  contents. So after ZEROACC, store whole rows (both column halves) before anything reads them."""
  return tensix('SFPSTORE', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPLOADI(lreg_ind=0, instr_mod0=0, imm16=0):
  """Load an immediate into an LReg (SFPU, 0x71). Broadcasts a 16-bit immediate to the enabled lanes.

  lreg_ind   [23:20] Destination L0..L7.
  instr_mod0 [19:16] isa.LoadImm: 0 BF16 bits into the high half (low half 0), 1 FP16 converted to FP32, 2 uint16
                     zero-extended, 4 int16 sign-extended, 8 replace the upper 16 bits, 10 replace the lower 16 bits.
  imm16      [15:0]  The 16-bit pattern.
  An exact FP32 or 32-bit constant is two instructions: UPPER then LOWER (or the reverse)."""
  return tensix('SFPLOADI', lreg_ind, instr_mod0, imm16)

def SFPLOADMACRO(lreg_ind=0, instr_mod0=0, sfpu_addr_mode=0, dest_reg_addr=0):
  """Load from Dst and launch a programmed sequence (SFPU, 0x93). Does an SFPLOAD, then runs up to one recorded
  instruction on each of the four other sub-units (simple, MAD, round, store) at programmed delays. This is the only
  way the SFPU runs more than one instruction per cycle.

  lreg_ind       [23:20] Sequence 0..3 in the high two bits, the low two bits of the destination LReg in the low two.
  instr_mod0     [19:16] Storage format of the load (isa.SfpuFormat).
  sfpu_addr_mode [15:13] Address-modifier slot applied after the load (0..7). A scheduled store does not apply one.
  dest_reg_addr  [12:0]  Dst address (10 bits) as SFPLOAD, except that bit 0 of the final address is bit 2 of the
                         destination LReg. If the offsets added to it are odd, the destination is off by 4.
  Programmed through SFPCONFIG:
    templates 0..3   one raw SFPU instruction word each (config_dest 0..3, or issue the instruction with
                     destination 12..15)
    sequences 0..3   one byte per sub-unit: byte 0 simple, 1 MAD, 2 round, 3 store (config_dest 4..7). In a byte,
                     bits 2:0 = 0 nothing, 2 SFPNOP, 3 SFPSTORE, 4..7 template 0..3; bits 5:3 = delay (0 = the cycle
                     after the SFPLOADMACRO); bit 6 = use LReg.LOAD_MACRO as that instruction's destination (or as the
                     store's source); bit 7 = the loaded register replaces the template's VB instead of its VC (for a
                     store: keep the template's source).
    control word     config_dest 8: bits 3:0 the store's format, bits 7:4 per sequence "store in the load's format",
                     bits 11:8 per sub-unit "delay counts SFPU instructions issued, not cycles".
  See the scheduling notes above: nothing inside a sequence is stalled for you."""
  return tensix('SFPLOADMACRO', lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr)

def SFPCONFIG(imm16_math=0, config_dest=0, instr_mod1=0):
  """Write SFPU configuration (SFPU, 0x91). Sets a programmable constant, the lane configuration, or SFPLOADMACRO
  state. The value is lanes 0..7 of L0 (replicated to all 32 lanes) unless the immediate flag is set.

  imm16_math  [23:8] Immediate value, with instr_mod1 bit 0. With instr_mod1 bit 3 it is a lane mask.
  config_dest [7:4]  0..3 SFPLOADMACRO template, 4..7 sequence, 8 macro control word, 11..14 the constant registers
                     L11..L14, 15 lane configuration. 9 and 10 are undefined.
  instr_mod1  [3:0]  1 use the immediate. 2 / 4 / 6 OR / AND / XOR the value into the control word or the lane
                     configuration instead of replacing it. 8 the immediate is a lane mask.
  A template is a 32-bit word, so it has to come from L0. The immediate reaches only the low 16 bits of a sequence
  (its simple and MAD bytes). Follow a change to SFPLOADMACRO state with an SFPNOP."""
  return tensix('SFPCONFIG', imm16_math, config_dest, instr_mod1)

def SFPNOP():
  """SFPU no-op (SFPU, 0x8F). Occupies one SFPU cycle. Used for the dependency gaps the hardware does not insert by
  itself (see the scheduling notes above) and as filler in SFPLOADMACRO sequences."""
  return tensix('SFPNOP')

def SFPMAD(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Multiply-add (SFPU, 0x84). VD = A * B + C in FP32. 2 cycles.

  lreg_src_a [23:16] A (4 bits used).
  lreg_src_b [15:12] B.
  lreg_src_c [11:8]  C.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   Flags: 1 negate A, 2 negate C, 4 take A's register number from the low 4 bits of L7 (per lane),
                     8 take the destination's register number from L7 the same way.
  Not an IEEE fused multiply-add: the product is partly rounded before the add. Denormal inputs count as zero and
  denormal results flush to zero. Rounds to nearest even. The two indirect flags make the stall logic assume every
  register is read / written, which costs stalls."""
  return tensix('SFPMAD', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPADD(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Floating-point add (SFPU, 0x85). SFPMAD with A = LReg.ONE: VD = B + C. Pass lreg_src_a=LReg.ONE. Fields, flags
  and timing as SFPMAD; instr_mod1=2 gives B - C."""
  return tensix('SFPADD', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPMUL(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Floating-point multiply (SFPU, 0x86). SFPMAD with C = LReg.ZERO: VD = A * B. Pass lreg_src_c=LReg.ZERO. Fields,
  flags and timing as SFPMAD; instr_mod1=1 gives -(A * B)."""
  return tensix('SFPMUL', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPADDI(imm16_math=0, lreg_dest=0, instr_mod1=0):
  """Add a BF16 immediate (SFPU, 0x75). VD = imm + VD, the immediate widened to FP32 (bits << 16). 2 cycles.

  imm16_math [23:8] BF16 bit pattern.
  lreg_dest  [7:4]  Input and output register.
  instr_mod1 [3:0]  Flags: 2 negate the VD input (imm - VD), 8 destination register number from L7. 1 and 4 are
                    reserved."""
  return tensix('SFPADDI', imm16_math, lreg_dest, instr_mod1)

def SFPMULI(imm16_math=0, lreg_dest=0, instr_mod1=0):
  """Multiply by a BF16 immediate (SFPU, 0x74). VD = imm * VD, the immediate widened to FP32 (bits << 16). 2 cycles.
  Saves the register and the SFPLOADI a constant multiply otherwise needs. Probed, including both flags.

  imm16_math [23:8] BF16 bit pattern.
  lreg_dest  [7:4]  Input and output register.
  instr_mod1 [3:0]  Flags: 2 negate the VD input, 8 destination register number from L7. 1 and 4 are reserved."""
  return tensix('SFPMULI', imm16_math, lreg_dest, instr_mod1)

def SFPMUL24(lreg_src_a=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """23-bit unsigned integer multiply (SFPU, 0x98). 2 cycles, timing as SFPMAD. Probed in both modes.

  lreg_src_a [23:16] A (4 bits used).
  lreg_src_b [15:12] B.
  lreg_src_c [11:8]  Must be LReg.ZERO.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   0: VD = the low 23 bits of A * B. 1: VD = (low 23 bits of A) * (low 23 bits of B) >> 23, the high
                     part of the 46-bit product. 4 / 8: A's / the destination's register number from L7.
  Store the result with SfpuFormat.INT32: an FP32 store zeroes values below 2^23."""
  return tensix('SFPMUL24', lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPLUT(lreg_ind=0, instr_mod0=0, dest_reg_addr=0):
  """Three-segment piecewise-linear function with 8-bit coefficients (SFPU, 0x73). VD = a * |L3| + b, the (a, b) pair
  chosen by |L3|: from L0 for [0, 1), L1 for [1, 2), L2 for 2 and up. 2 cycles, timing as SFPMAD. The multiply-add is
  fused (one rounding). Everything here matches hardware bit for bit, including both flags (probed).

  lreg_ind      [23:20] VD.
  instr_mod0    [19:16] Flags: 4 give the result the sign of L3, 8 destination register number from L7.
  dest_reg_addr [15:0]  Keep 0.
  a is bits 15:8 and b bits 7:0 of the chosen register. Each is sign, 3-bit exponent, 4-bit mantissa:
  +-(1 + m / 16) * 2^-e, so magnitudes 0.0078 .. 1.9375, and 0xFF means 0. SFPLUTFP32 is the precise version."""
  return tensix('SFPLUT', lreg_ind, instr_mod0, dest_reg_addr)

def SFPLUTFP32(lreg_dest=0, instr_mod1=0):
  """Piecewise-linear function of |L3| (SFPU, 0x95). VD = slope * |L3| + intercept, the pair chosen by which segment
  |L3| falls in. One instruction replaces a compare / select / multiply-add chain. 2 cycles, timing as SFPMAD.
  The multiply-add is fused: one rounding, so within 1 ULP of a separately rounded multiply and add. Segment choice
  and coefficient decoding match this table in every lane for modes 0, 2, 3 and their signed forms 4 and 6 (probed).

  lreg_dest  [23:4] VD in the low 4 bits (word bits 7:4). Word bits 19:16 must repeat instr_mod1: the stall logic
                    reads its copy there. So pass lreg_dest = VD | instr_mod1 << 12.
  instr_mod1 [3:0]  Table layout in the low 2 bits, plus 4 = give the result the sign of L3:
                      0   3 segments [0,1) [1,2) [2,inf), FP32 coefficients: slopes in L0..L2, intercepts in L4..L6.
                      2   6 segments split at 0.5, 1, 1.5, 2, 3, 16-bit coefficients: slopes in the halves of
                          L0..L2, intercepts in the halves of L4..L6; the low half is the lower segment.
                      3   as 2 with the last split at 4 instead of 3.
                      10  3 segments, 16-bit: slope in the high half and intercept in the low half of L0..L2.
                          Erratum (probed): the result goes to the register named by the low 4 bits of L7, and VD
                          is left unchanged.
  The 16-bit coefficients are FP16-like with a 10-bit mantissa, except that exponent 31 means 0.0 and exponent 0 is an
  ordinary exponent: encode zero with exponent 31."""
  return tensix('SFPLUTFP32', lreg_dest, instr_mod1)

def SFPARECIP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Approximate reciprocal or exponential (SFPU, 0x99). A coarse per-lane estimate, meant as the seed of a refinement.

  imm12_math [23:12] VB for mode 1.
  lreg_c     [11:8]  VC, the input.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   0: VD = about 1 / VC, sign kept. 1: the same on |VC|, but only in lanes where VB is negative.
                     2: about exp(|VC|) with VC's sign put back, usable for |VC| < 2.
  The reciprocal of 1.0 comes out as 0.99609375. Mode 2 on a negative input gives -exp(|x|), not exp(x): finish with a
  mode 1 reciprocal conditioned on the sign."""
  return tensix('SFPARECIP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPMOV(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Copy or negate (SFPU, 0x7C). VD = VC.

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 copy. 1 copy with bit 31 flipped (FP32 or sign-magnitude negate, not two's complement). 2 copy
                    to every lane, ignoring the condition flags. 8 read special state selected by VC; VC=9 reads and
                    advances the hardware PRNG."""
  return tensix('SFPMOV', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPABS(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Absolute value (SFPU, 0x7D). VD = |VC|.

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 two's-complement integer, 1 FP32.
  FP32 mode leaves a negative NaN negative. Integer mode leaves -2^31 unchanged."""
  return tensix('SFPABS', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPAND(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Bitwise AND (SFPU, 0x7E). VD = VD & VC, or VD = VB & VC.

  imm12_math [23:12] VB in the low 4 bits, with instr_mod1=1.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   0: the first input is VD. 1: the first input is VB."""
  return tensix('SFPAND', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPOR(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Bitwise OR (SFPU, 0x7F). VD = VD | VC, or VD = VB | VC. Fields as SFPAND."""
  return tensix('SFPOR', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPXOR(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Bitwise XOR (SFPU, 0x8D). VD = VD ^ VC. There is no VB form: the destination is always the first input.

  lreg_c    [11:8] VC.
  lreg_dest [7:4]  VD."""
  return tensix('SFPXOR', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPNOT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Bitwise NOT (SFPU, 0x80). VD = ~VC, bit-exact for every pattern including infinities and NaNs (probed).

  lreg_c    [11:8] VC.
  lreg_dest [7:4]  VD."""
  return tensix('SFPNOT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPLZ(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Count leading zeros (SFPU, 0x81). VD = number of leading zero bits of VC (32 for 0).

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  Flags: 4 clear bit 31 of VC first. 2 also set each lane's condition flag to "VC != 0". 8 invert
                    that flag (2 | 8 gives "VC == 0").
  All probed. Store the count with SfpuFormat.INT32: an FP32 store zeroes it."""
  return tensix('SFPLZ', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSHFT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Shift bits within each lane (SFPU, 0x7A). A positive amount shifts left, a negative one shifts right.

  imm12_math [23:12] Signed shift amount, as amount & 0xFFF, with instr_mod1 bit 0.
  lreg_c     [11:8]  VC: the shift amount in register mode, or the data with instr_mod1 bit 2.
  lreg_dest  [7:4]   VD: the result, and the data unless instr_mod1 bit 2 is set.
  instr_mod1 [3:0]   Flags: 1 shift by the immediate instead of by VC. 2 right shifts are arithmetic. 4 (with 1) shift
                     VC into VD instead of shifting VD in place. So 0 is VD <<= VC, 1 is VD <<= imm, 5 is
                     VD = VC >> imm logical and 7 the same arithmetic (the two ttrv uses)."""
  return tensix('SFPSHFT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSHFT2(imm12_math=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Move values between lanes, or shift bits (SFPU, 0x94).

  imm12_math [23:12] VB, or a signed 12-bit shift amount, depending on the mode.
  lreg_src_c [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   0 copy L1..L3 down into L0..L2 whole. 1 the same as a chained copy. 2 rotate and copy.
                     3 rotate right by one lane within each row of 8 (lane 7 wraps to lane 0). 4 shift right by one
                     lane within each row, zero fill. 5 shift bits by a register amount. 6 shift bits by the immediate.
  Modes 2, 3 and 4 take 2 cycles. ttrv reduces across lanes with mode 3, SFPADD and SFPTRANSP."""
  return tensix('SFPSHFT2', imm12_math, lreg_src_c, lreg_dest, instr_mod1)

def SFPIADD(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Integer add or subtract (SFPU, 0x79). 32-bit two's-complement arithmetic on the register bits.

  imm12_math [23:12] Signed immediate, as value & 0xFFF, with instr_mod1 bit 0.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD, also the second input in the register forms.
  instr_mod1 [3:0]   Low 2 bits: 0 VD = VC + VD, 1 VD = VC + imm, 2 VD = VC - VD. Without 4, each lane's condition
                     flag is set to "result is negative"; 8 inverts that. 4 leaves the flags alone."""
  return tensix('SFPIADD', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPCAST(lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Convert integers (SFPU, 0x90).

  lreg_src_c [23:8] VC (4 bits used).
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 sign-magnitude int32 to FP32, round to nearest even. 1 the same with stochastic rounding.
                    2 two's-complement absolute value (prefer SFPABS). 3 convert between two's complement and
                    sign-magnitude.
  The SFPU's float-to-int and int-to-float paths use sign-magnitude integers; SFPIADD and the shifts use two's
  complement. Convert with mode 3 when crossing."""
  return tensix('SFPCAST', lreg_src_c, lreg_dest, instr_mod1)

def SFP_STOCH_RND(rnd_mode=0, imm8_math=0, lreg_src_b=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Round to a narrower format (SFPU, 0x8E). VD = VC reduced in precision or converted to a small integer.

  rnd_mode   [23:21] 0 nearest (ties away from zero), 1 stochastic, 2 toward zero.
  imm8_math  [20:16] Right-shift amount for the int-to-int forms, with instr_mod1 bit 3.
  lreg_src_b [15:12] VB: the shift amount otherwise. For the float forms pass LReg.ZERO, or the stall logic waits on
                     whatever register number is here.
  lreg_src_c [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   Low 3 bits: 0 FP32 to FP16 precision, 1 FP32 to BF16 precision (the result stays an FP32 value
                     with the low mantissa bits cleared), 2 FP32 to uint8, 3 FP32 to int8, 6 FP32 to uint16,
                     7 FP32 to int16, 4 int32 to uint8, 5 int32 to int8. Bit 3: shift by the immediate.
  Integer results are sign-magnitude and saturate (255, +-127, 65535, +-32767). Float forms turn NaN into infinity
  and denormals and -0 into +0.
  Errata: stochastic mode is biased upward and can change values that were already exact. Toward-zero rounds away
  when every discarded bit is 1. Float to int with |x| < 0.5 always gives 0."""
  return tensix('SFP_STOCH_RND', rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1)

def SFPEXEXP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Extract the exponent (SFPU, 0x77). VD = the FP32 exponent field of VC as an integer.

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 exponent minus 127. 1 the raw biased exponent. 2 also set each lane's condition flag from the
                    sign of the result. 8 invert that flag."""
  return tensix('SFPEXEXP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPEXMAN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Extract the mantissa (SFPU, 0x78). VD = the 23 mantissa bits of VC as an integer; the top 8 bits are 0.

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 sets bit 23 (the hidden leading 1). 1 leaves it 0."""
  return tensix('SFPEXMAN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETEXP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Replace the exponent (SFPU, 0x82). VD = VC with a new exponent field; sign and mantissa of VC are kept.

  imm12_math [23:12] Biased exponent (8 bits), with instr_mod1=1.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   1 exponent from the immediate. 0 from the low 8 bits of the old VD. 2 from the exponent field of
                     the old VD."""
  return tensix('SFPSETEXP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETMAN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Replace the mantissa (SFPU, 0x83). VD = VC with a new mantissa; sign and exponent of VC are kept.

  imm12_math [23:12] With instr_mod1=1: the mantissa is this immediate << 11.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   1 mantissa from the immediate. 0 from the low 23 bits of the old VD. Both probed."""
  return tensix('SFPSETMAN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETSGN(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Replace the sign (SFPU, 0x89). VD = VC with a new sign bit; exponent and mantissa of VC are kept.

  imm12_math [23:12] The sign bit in bit 0, with instr_mod1=1.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   1 sign from the immediate. 0 from the sign of the old VD (copysign)."""
  return tensix('SFPSETSGN', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPDIVP2(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Scale by a power of two (SFPU, 0x76). VD = VC with its exponent field changed. 1 cycle and no constant
  register, against 2 cycles and a constant for a multiply.

  imm12_math [23:12] 8-bit exponent value.
  lreg_c     [11:8]  VC.
  lreg_dest  [7:4]   VD.
  instr_mod1 [3:0]   1: add the immediate to the exponent field, wrapping at 8 bits (2^n scaling; use 256 - n to
                     divide). Infinity and NaN pass through. 0: replace the exponent field with the immediate.
  All probed. The add does not treat 0.0 specially: 0 scaled by 2^n comes out as 2^(n - 127), not 0 (0.0 with 128
  gives 2.0), so guard zeros. A result whose exponent field wraps to 0 reads back as 0."""
  return tensix('SFPDIVP2', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSWAP(imm12_math=0, lreg_src_c=0, lreg_dest=0, instr_mod1=0):
  """Swap, or minimum and maximum together (SFPU, 0x92). Both registers are written. 2 cycles.

  lreg_src_c [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  0 swap. 1 VD = min, VC = max in every lane. 9 VD = max, VC = min. 2..8 do min/max with the
                    placement varying by row of 8 lanes: 2 rows 0,1 get min in VD; 3 rows 0,2; 4 rows 0,3; 5, 6, 7, 8
                    only row 0, 1, 2, 3.
  The order is the sign-magnitude integer order, which for FP32 is a total order: -NaN < -inf < ... < -0 < +0 < ...
  < +inf < +NaN. With destination-index tracking on in the lane configuration, the same swaps are applied to L4..L7,
  which is how argmin / argmax is built."""
  return tensix('SFPSWAP', imm12_math, lreg_src_c, lreg_dest, instr_mod1)

def SFPTRANSP(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Transpose registers against lane rows (SFPU, 0x8C). Row j of L[i] is exchanged with row i of L[j], for L0..L3
  and separately for L4..L7. Each 8-lane row moves whole; the 8 columns are not touched. All operands 0."""
  return tensix('SFPTRANSP', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPENCC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Turn predication on or off (SFPU, 0x8A). Controls whether the per-lane condition flags gate later SFPU writes,
  and sets the flags.

  imm12_math [23:12] Bit 0: the new predication enable, with instr_mod1 = 2. Bit 1: the new flag value, with 8.
  instr_mod1 [3:0]   1 toggle predication. 2 set predication from immediate bit 0. 8 set every flag to immediate bit 1;
                     without 8 every flag becomes true.
  ttrv opens a conditional with SFPENCC(1, 0, 0, 2) and closes it with SFPENCC(0, 0, 0, 2). Boot issues
  SFPENCC(3, 0, 0, 10)."""
  return tensix('SFPENCC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPSETCC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Set the condition flags from a register (SFPU, 0x7B). Each lane's flag becomes a test of VC.

  imm12_math [23:12] Bit 0: the flag value, with instr_mod1 = 1.
  lreg_c     [11:8]  VC.
  instr_mod1 [3:0]   0 VC < 0. 2 VC != 0. 4 VC >= 0. 6 VC == 0. 1 the immediate. 8 clear the flags."""
  return tensix('SFPSETCC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPGT(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Compare greater-than (SFPU, 0x97). Tests VD > VC per lane, in the sign-magnitude / FP32 total order (see
  SFPSWAP).

  lreg_c     [11:8] VC.
  lreg_dest  [7:4]  VD.
  instr_mod1 [3:0]  Flags: 1 set each lane's condition flag to the result. 8 write the result into VD as 0xFFFFFFFF
                    or 0. 2 AND the result into the flags on top of the predicate stack; 2 | 4 OR it in instead.
  Blackhole only. ttrv uses mode 1."""
  return tensix('SFPGT', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPLE(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Compare less-or-equal (SFPU, 0x96). Tests VD <= VC per lane. Fields and modes as SFPGT."""
  return tensix('SFPLE', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPPUSHC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Push the predicate state (SFPU, 0x87). Saves the condition flags and the predication enable on the 8-entry
  predicate stack, for a nested conditional. All operands 0."""
  return tensix('SFPPUSHC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPPOPC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Pop the predicate state (SFPU, 0x88).

  instr_mod1 [3:0]  0 pop: restore the flags and the predication enable. 1..12 leave the stack alone and combine the
                    flags with the ones on top of it. 13 invert the flags. 14 / 15 enable predication with all flags
                    true / false.
  Popping an empty stack is an error."""
  return tensix('SFPPOPC', imm12_math, lreg_c, lreg_dest, instr_mod1)

def SFPCOMPC(imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0):
  """Else (SFPU, 0x8B). Each lane's condition flag becomes "the enclosing condition holds and this one did not":
  the flags on top of the predicate stack AND NOT the current flags. With an empty stack it is a plain inversion.
  All operands 0."""
  return tensix('SFPCOMPC', imm12_math, lreg_c, lreg_dest, instr_mod1)
