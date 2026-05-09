import json
import struct
from pathlib import Path

def bits(v, hi, lo=None):
  if lo is None: lo = hi
  return (v >> lo) & ((1 << (hi - lo + 1)) - 1)

def _sext(v, w): return v - (1 << w) if v & (1 << (w - 1)) else v

def _field(v, w):
  assert 0 <= v < (1 << w), f"{v} does not fit in {w} bits"
  return v

def _sfield(v, w):
  assert -(1 << (w - 1)) <= v < (1 << (w - 1)), f"{v} does not fit in signed {w} bits"
  return v & ((1 << w) - 1)

# field_name, lo_bit, width, signed?
_RV_FIELDS = {
  "R": (("rd", 7, 5, False), ("rs1", 15, 5, False), ("rs2", 20, 5, False)),
  "I": (("rd", 7, 5, False), ("rs1", 15, 5, False), ("imm", 20, 12, True)),
  "Ish": (("rd", 7, 5, False), ("rs1", 15, 5, False), ("shamt", 20, 5, False)),
  "S": (("rs1", 15, 5, False), ("rs2", 20, 5, False), ("imm", None, 12, True)),
  "B": (("rs1", 15, 5, False), ("rs2", 20, 5, False), ("imm", None, 13, True)),
  "U": (("rd", 7, 5, False), ("imm", 12, 20, False)),
  "J": (("rd", 7, 5, False), ("imm", None, 21, True)),
  "CSR": (("rd", 7, 5, False), ("rs1", 15, 5, False), ("csr", 20, 12, False)),
  "NONE": (),
}

_SPECIAL_IMM = {"S", "B", "U", "J"}
_IMM_WIDTH = {"S": 12, "B": 13, "U": 20, "J": 21}
_IMM_ARG = {fmt: (("imm", None, _IMM_WIDTH[fmt], False),) for fmt in _SPECIAL_IMM}

_RV_MASK = {
  "R": 0xFE00707F, "I": 0x0000707F, "Ish": 0xFE00707F,
  "S": 0x0000707F, "B": 0x0000707F, "U": 0x0000007F,
  "J": 0x0000007F, "CSR": 0x0000707F, "NONE": 0x0000007F,
}

_RV = [
  ('add',    0x00000033, 'R'),   ('sub',    0x40000033, 'R'),
  ('sll',    0x00001033, 'R'),   ('slt',    0x00002033, 'R'),
  ('sltu',   0x00003033, 'R'),   ('xor',    0x00004033, 'R'),
  ('srl',    0x00005033, 'R'),   ('sra',    0x40005033, 'R'),
  ('or',     0x00006033, 'R'),   ('and',    0x00007033, 'R'),
  ('mul',    0x02000033, 'R'),   ('mulh',   0x02001033, 'R'),
  ('mulhsu', 0x02002033, 'R'),   ('mulhu',  0x02003033, 'R'),
  ('div',    0x02004033, 'R'),   ('divu',   0x02005033, 'R'),
  ('rem',    0x02006033, 'R'),   ('remu',   0x02007033, 'R'),
  ('sh1add', 0x20002033, 'R'),   ('sh2add', 0x20004033, 'R'),
  ('sh3add', 0x20006033, 'R'),   ('zext_h', 0x08004033, 'R', 0xFFF0707F),
  ('min',    0x0A004033, 'R'),   ('minu',   0x0A005033, 'R'),
  ('max',    0x0A006033, 'R'),   ('maxu',   0x0A007033, 'R'),
  ('xnor',   0x40004033, 'R'),   ('orn',    0x40006033, 'R'),
  ('andn',   0x40007033, 'R'),   ('rol',    0x60001033, 'R'),
  ('ror',    0x60005033, 'R'),

  ('addi',   0x00000013, 'I'),   ('slti',   0x00002013, 'I'),
  ('sltiu',  0x00003013, 'I'),   ('xori',   0x00004013, 'I'),
  ('ori',    0x00006013, 'I'),   ('andi',   0x00007013, 'I'),
  ('clz',    0x60001013, 'Ish', 0xFFF0707F),
  ('ctz',    0x60101013, 'Ish', 0xFFF0707F),
  ('cpop',   0x60201013, 'Ish', 0xFFF0707F),
  ('sext_b', 0x60401013, 'Ish', 0xFFF0707F),
  ('sext_h', 0x60501013, 'Ish', 0xFFF0707F),
  ('orc_b',  0x28705013, 'Ish', 0xFFF0707F),
  ('rev8',   0x69805013, 'Ish', 0xFFF0707F),
  ('slli',   0x00001013, 'Ish'), ('srli',   0x00005013, 'Ish'),
  ('srai',   0x40005013, 'Ish'), ('rori',   0x60005013, 'Ish'),

  ('lb',     0x00000003, 'I'),   ('lh',     0x00001003, 'I'),
  ('lw',     0x00002003, 'I'),   ('lbu',    0x00004003, 'I'),
  ('lhu',    0x00005003, 'I'),   ('sb',     0x00000023, 'S'),
  ('sh',     0x00001023, 'S'),   ('sw',     0x00002023, 'S'),
  ('beq',    0x00000063, 'B'),   ('bne',    0x00001063, 'B'),
  ('blt',    0x00004063, 'B'),   ('bge',    0x00005063, 'B'),
  ('bltu',   0x00006063, 'B'),   ('bgeu',   0x00007063, 'B'),
  ('lui',    0x00000037, 'U'),   ('auipc',  0x00000017, 'U'),
  ('jal',    0x0000006F, 'J'),   ('jalr',   0x00000067, 'I'),

  ('csrrw',  0x00001073, 'CSR'), ('csrrs',  0x00002073, 'CSR'),
  ('csrrc',  0x00003073, 'CSR'), ('csrrwi', 0x00005073, 'CSR'),
  ('csrrsi', 0x00006073, 'CSR'), ('csrrci', 0x00007073, 'CSR'),
  ('fence',  0x0FF0000F, 'NONE', 0x0000007F),
]

def _rv_spec(row):
  name, base, fmt, *mask = row
  return mask[0] if mask else _RV_MASK[fmt], base, name, fmt

def _rv_args(mask, fmt):
  args = []
  for name, lo, width, signed in _RV_FIELDS[fmt]:
    if name == "imm" and fmt in _SPECIAL_IMM:
      continue
    # Fully masked operand fields are fixed by the table row itself. This keeps
    # encoders like clz/ctz/zext_h from exposing unused shamt/rs2 parameters.
    if (mask & (((1 << width) - 1) << lo)) != (((1 << width) - 1) << lo):
      args.append((name, lo, width, signed))
  return tuple(args)

def _bind(fields, values, kw):
  names = [name for name, *_ in fields]
  if len(values) > len(names):
    raise TypeError(f"expected at most {len(names)} positional args, got {len(values)}")
  out = dict(zip(names, values))
  for k, v in kw.items():
    if k not in names:
      raise TypeError(f"unexpected argument {k!r}")
    if k in out:
      raise TypeError(f"multiple values for {k!r}")
    out[k] = v
  missing = [name for name in names if name not in out]
  if missing:
    raise TypeError(f"missing arguments: {', '.join(missing)}")
  return out

def _enc_rv(base, mask, fmt, *values, **kw):
  args = _rv_args(mask, fmt)
  vals = _bind(args + _IMM_ARG.get(fmt, ()), values, kw)
  w = base
  match fmt:
    case "S":
      imm = _sfield(vals.pop("imm"), 12)
      w |= bits(imm, 4, 0) << 7 | bits(imm, 11, 5) << 25
    case "B":
      imm = _sfield(vals.pop("imm"), 13)
      w |= bits(imm, 11) << 7 | bits(imm, 4, 1) << 8 | bits(imm, 10, 5) << 25 | bits(imm, 12) << 31
    case "J":
      imm = _sfield(vals.pop("imm"), 21)
      w |= bits(imm, 19, 12) << 12 | bits(imm, 11) << 20 | bits(imm, 10, 1) << 21 | bits(imm, 20) << 31
    case "U":
      imm = vals.pop("imm")
      assert imm == (imm & 0xFFFFF000), f"{imm} is not a U-format immediate"
      w |= imm
  for fname, lo, width, signed in args:
    if fname not in vals:
      continue
    v = _sfield(vals[fname], width) if signed else _field(vals[fname], width)
    w |= v << lo
  return w & 0xFFFFFFFF

def _make_rv(base, mask, fmt):
  def enc(*args, **kw):
    return _enc_rv(base, mask, fmt, *args, **kw)
  return enc

for _row in _RV:
  _mask, _base, _name, _fmt = _rv_spec(_row)
  globals()[_name] = _make_rv(_base, _mask, _fmt)

def _x_R(w):   return dict(rd=bits(w,11,7), rs1=bits(w,19,15), rs2=bits(w,24,20))
def _x_I(w):   return dict(rd=bits(w,11,7), rs1=bits(w,19,15), imm=_sext(bits(w,31,20), 12))
def _x_Ish(w): return dict(rd=bits(w,11,7), rs1=bits(w,19,15), shamt=bits(w,24,20))
def _x_S(w):   return dict(rs1=bits(w,19,15), rs2=bits(w,24,20), imm=_sext(bits(w,11,7) | (bits(w,31,25)<<5), 12))
def _x_B(w):   return dict(rs1=bits(w,19,15), rs2=bits(w,24,20), imm=_sext((bits(w,11,8)<<1) | (bits(w,30,25)<<5) | (bits(w,7)<<11) | (bits(w,31)<<12), 13))
def _x_U(w):   return dict(rd=bits(w,11,7), imm=w & 0xFFFFF000)
def _x_J(w):   return dict(rd=bits(w,11,7), imm=_sext((bits(w,30,21)<<1) | (bits(w,20)<<11) | (bits(w,19,12)<<12) | (bits(w,31)<<20), 21))
def _x_CSR(w): return dict(rd=bits(w,11,7), rs1=bits(w,19,15), csr=bits(w,31,20))
def _x_NONE(w): return {}

_RV_EXTRACT = {'R':_x_R, 'I':_x_I, 'Ish':_x_Ish, 'S':_x_S, 'B':_x_B, 'U':_x_U, 'J':_x_J, 'CSR':_x_CSR, 'NONE':_x_NONE}
_RV_BY_OPCODE = {}
for _row in _RV:
  _m, _b, _n, _f = _rv_spec(_row)
  _RV_BY_OPCODE.setdefault(_b & 0x7F, []).append((_m, _b, _n, _f))

def decode_rv(word):
  w = word & 0xFFFFFFFF
  for mask, base, name, fmt in _RV_BY_OPCODE.get(w & 0x7F, ()):
    if (w & mask) == (base & mask):
      fields = _RV_EXTRACT[fmt](w)
      fields["word"] = w
      return name, fields
  return "UNKNOWN", {"word": w}

def TTINSN(imm32):
  assert imm32 < 0xC0000000, f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}"
  return ((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF

def _simple_fields(c_name="lreg_c"):
  return [
    ("imm12_math", 12, 12),
    (c_name, 8, 4),
    ("lreg_dest", 4, 4),
    ("instr_mod1", 0, 4),
  ]

def _mad_fields():
  return [
    ("lreg_src_a", 16, 4),
    ("lreg_src_b", 12, 4),
    ("lreg_src_c", 8, 4),
    ("lreg_dest", 4, 4),
    ("instr_mod1", 0, 4),
  ]

_TENSIX_DECODE = {
  0x01: ("mop", [("mop_type", 23, 1), ("loop_count", 16, 7), ("zmask_lo16_or_loop_count", 0, 16)]),
  0x02: ("nop", []),
  0x03: ("mop_cfg", [("zmask_hi16", 0, 16)]),
  0x04: ("replay", [("start_idx", 14, 10), ("len", 4, 10), ("execute_while_loading", 1, 1), ("load_mode", 0, 1)]),
  0x08: ("movd2a", [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("instr_mod", 12, 2), ("dst", 0, 12)]),
  0x0A: ("movd2b", [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("instr_mod", 12, 2), ("dst", 0, 12)]),
  0x10: ("zeroacc", [("clear_mode", 19, 5), ("use_32_bit_mode", 18, 1), ("clear_zero_flags", 17, 1), ("addr_mode", 14, 3), ("where", 0, 14)]),
  0x11: ("zerosrc", [("zero_val", 4, 20), ("write_mode", 3, 1), ("bank_mask", 2, 1), ("src_mask", 0, 2)]),
  0x12: ("mova2d", [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("instr_mod", 12, 2), ("dst", 0, 12)]),
  0x13: ("movb2d", [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("movb2d_instr_mod", 11, 3), ("dst", 0, 11)]),
  0x14: ("trnspsrca", []),
  0x15: ("rareb", []),
  0x16: ("trnspsrcb", []),
  0x17: ("shiftxa", [("shift_mode", 0, 2), ("log2_amount2", 2, 22)], [("raw", 0, 24)]),
  0x18: ("shiftxb", [("shift_row", 0, 10), ("rot_shift", 10, 4), ("addr_mode", 14, 3)], [("raw", 0, 24)]),
  0x21: ("clrexphist", []),
  0x22: ("conv3s1", [("clear_dvalid", 22, 2), ("rotate_weights", 17, 5), ("addr_mode", 14, 3), ("dst", 0, 14)]),
  0x23: ("conv3s2", [("clear_dvalid", 22, 2), ("rotate_weights", 17, 5), ("addr_mode", 14, 3), ("dst", 0, 14)]),
  0x24: ("mfconv3s1", [("clear_dvalid", 22, 2), ("rotate_weights", 17, 5), ("addr_mode", 14, 3), ("dst", 0, 14)]),
  0x25: ("apool3s1", [("clear_dvalid", 22, 2), ("pool_addr_mode", 15, 7), ("index_en", 14, 1), ("dst", 0, 14)]),
  0x26: ("mvmul", [("clear_dvalid", 22, 2), ("instr_mod19", 19, 3), ("addr_mode", 14, 3), ("dst", 0, 10)], [("broadcast_srcb", 19, 1)]),
  0x27: ("elwmul", [("clear_dvalid", 22, 2), ("dest_accum_en", 21, 1), ("instr_mod19", 19, 2), ("addr_mode", 14, 2), ("dst", 0, 14)]),
  0x28: ("elwadd", [("clear_dvalid", 22, 2), ("dest_accum_en", 21, 1), ("instr_mod19", 19, 2), ("addr_mode", 14, 2), ("dst", 0, 14)]),
  0x29: ("dotpv", [("clear_dvalid", 22, 2), ("dest_accum_en", 21, 1), ("instr_mod19", 19, 2), ("addr_mode", 14, 2), ("dst", 0, 14)]),
  0x2A: ("mpool3s2", [("clear_dvalid", 22, 2), ("pool_addr_mode", 15, 7), ("index_en", 14, 1), ("dst", 0, 14)]),
  0x30: ("elwsub", [("clear_dvalid", 22, 2), ("dest_accum_en", 21, 1), ("instr_mod19", 19, 2), ("addr_mode", 14, 2), ("dst", 0, 14)]),
  0x31: ("mpool3s1", [("clear_dvalid", 22, 2), ("pool_addr_mode", 15, 7), ("index_en", 14, 1), ("dst", 0, 14)]),
  0x32: ("apool3s2", [("clear_dvalid", 22, 2), ("pool_addr_mode", 15, 7), ("index_en", 14, 1), ("dst", 0, 14)]),
  0x33: ("gmpool", [("clear_dvalid", 22, 2), ("instr_mod19", 19, 3), ("pool_addr_mode", 15, 4), ("max_pool_index_en", 14, 1), ("dst", 0, 14)]),
  0x34: ("gapool", [("clear_dvalid", 22, 2), ("instr_mod19", 19, 3), ("pool_addr_mode", 15, 4), ("max_pool_index_en", 14, 1), ("dst", 0, 14)]),
  0x35: ("gatesrcrst", [("reset_srcb_gate_control", 1, 1), ("reset_srca_gate_control", 0, 1)]),
  0x36: ("cleardvalid", [("clear_dvalid", 22, 2), ("reset", 0, 22)], [("cleardvalid", 22, 2)]),
  0x37: ("setrwc", [("clear_ab_vld", 22, 2), ("rwc_cr", 18, 4), ("rwc_d", 14, 4), ("rwc_b", 10, 4), ("rwc_a", 6, 4), ("BitMask", 0, 6)]),
  0x38: ("incrwc", [("rwc_cr", 18, 3), ("rwc_d", 14, 4), ("rwc_b", 10, 4), ("rwc_a", 6, 4)]),
  0x40: ("xmov", [("Mov_block_selection", 23, 1), ("Last", 0, 1)]),
  0x41: ("pacr", [("CfgContext", 21, 3), ("RowPadZero", 18, 3), ("DstAccessMode", 17, 1), ("AddrMode", 15, 2), ("AddrCntContext", 13, 2), ("ZeroWrite", 12, 1), ("ReadIntfSel", 8, 4), ("OvrdThreadId", 7, 1), ("Concat", 4, 3), ("CtxtCtrl", 2, 2), ("Flush", 1, 1), ("Last", 0, 1)]),
  0x42: ("unpacr", [("Unpack_block_selection", 23, 1), ("AddrMode", 15, 8), ("CfgContextCntInc", 13, 2), ("CfgContextId", 10, 3), ("AddrCntContextId", 8, 2), ("OvrdThreadId", 7, 1), ("SetDatValid", 6, 1), ("srcb_bcast", 5, 1), ("ZeroWrite2", 4, 1), ("AutoIncContextID", 3, 1), ("RowSearch", 2, 1), ("SearchCacheFlush", 1, 1), ("Last", 0, 1)]),
  0x43: ("unpacr_nop", [("Unpacker_Select", 23, 1), ("Stream_Id", 16, 7), ("Msg_Clr_Cnt", 12, 4), ("Set_Dvalid", 8, 4), ("Clr_to1_fmt_Ctrl", 6, 2), ("Stall_Clr_Cntrl", 5, 1), ("Bank_Clr_Ctrl", 4, 1), ("Src_ClrVal_Ctrl", 2, 2), ("Unpack_Pop", 0, 2)]),
  0x45: ("setdmareg", [("Payload_SigSelSize", 22, 2), ("Payload_SigSel", 8, 14), ("SetSignalsMode", 7, 1), ("RegIndex16b", 0, 7)]),
  0x46: ("flushdma", [("ConditionMask", 0, 4)]),
  0x48: ("reg2flop", [("SizeSel", 22, 2), ("ThConCfgIndex", 8, 7), ("InputReg", 0, 6)]),
  0x4B: ("tbufcmd", []),
  0x50: ("setadc", [("CntSetMask", 21, 3), ("ChannelIndex", 20, 1), ("DimensionIndex", 18, 2), ("Value", 0, 18)]),
  0x51: ("setadcxy", [("CntSetMask", 21, 3), ("Ch1_Y", 15, 6), ("Ch1_X", 12, 3), ("Ch0_Y", 9, 3), ("Ch0_X", 6, 3), ("BitMask", 0, 6)]),
  0x54: ("setadczw", [("CntSetMask", 21, 3), ("Ch1_W", 15, 6), ("Ch1_Z", 12, 3), ("Ch0_W", 9, 3), ("Ch0_Z", 6, 3), ("BitMask", 0, 6)]),
  0x55: ("incadczw", [("CntSetMask", 21, 3), ("Ch1_W", 15, 6), ("Ch1_Z", 12, 3), ("Ch0_W", 9, 3), ("Ch0_Z", 6, 3)]),
  0x58: ("adddmareg", [("OpBisConst", 23, 1), ("ResultRegIndex", 12, 11), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]),
  0x5A: ("muldmareg", [("OpBisConst", 23, 1), ("ResultRegIndex", 12, 11), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]),
  0x5B: ("bitwopdmareg", [("OpBisConst", 23, 1), ("OpSel", 18, 5), ("ResultRegIndex", 12, 6), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]),
  0x5C: ("shiftdmareg", [("OpBisConst", 23, 1), ("Mode", 18, 5), ("ResultRegIndex", 12, 6), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)], [("OpSel", 18, 5)]),
  0x5D: ("cmpdmareg", [("OpBisConst", 23, 1), ("OpSel", 18, 5), ("ResultRegIndex", 12, 6), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]),
  0x5E: ("setadcxx", [("CntSetMask", 21, 3), ("x_end2", 10, 11), ("x_start", 0, 10)]),
  0x60: ("dmanop", []),
  0x67: ("storereg", [("TdmaDataRegIndex", 18, 6), ("RegAddr", 0, 18)]),
  0x70: ("sfpload", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("sfpu_addr_mode", 13, 3), ("dest_reg_addr", 0, 13)]),
  0x71: ("sfploadi", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("imm16", 0, 16)]),
  0x72: ("sfpstore", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("sfpu_addr_mode", 13, 3), ("dest_reg_addr", 0, 13)]),
  0x73: ("sfplut", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("dest_reg_addr", 0, 16)]),
  0x74: ("sfpmuli", [("imm16_math", 8, 16), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x75: ("sfpaddi", [("imm16_math", 8, 16), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x76: ("sfpdivp2", _simple_fields()),
  0x77: ("sfpexexp", _simple_fields()),
  0x78: ("sfpexman", _simple_fields()),
  0x79: ("sfpiadd", _simple_fields()),
  0x7A: ("sfpshft", _simple_fields()),
  0x7B: ("sfpsetcc", _simple_fields()),
  0x7C: ("sfpmov", _simple_fields()),
  0x7D: ("sfpabs", _simple_fields()),
  0x7E: ("sfpand", _simple_fields()),
  0x7F: ("sfpor", _simple_fields()),
  0x80: ("sfpnot", _simple_fields()),
  0x81: ("sfplz", _simple_fields()),
  0x82: ("sfpsetexp", _simple_fields()),
  0x83: ("sfpsetman", _simple_fields()),
  0x84: ("sfpmad", _mad_fields()),
  0x85: ("sfpadd", _mad_fields()),
  0x86: ("sfpmul", _mad_fields()),
  0x87: ("sfppushc", _simple_fields()),
  0x88: ("sfppopc", _simple_fields()),
  0x89: ("sfpsetsgn", _simple_fields()),
  0x8A: ("sfpencc", _simple_fields()),
  0x8B: ("sfpcompc", _simple_fields()),
  0x8C: ("sfptransp", [("imm12_math", 12, 12), ("lreg_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x8D: ("sfpxor", _simple_fields()),
  0x8E: ("sfpstochrnd", [("rnd_mode", 21, 3), ("imm8_math", 16, 8), ("lreg_src_b", 12, 4), ("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x8F: ("sfpnop", []),
  0x90: ("sfpcast", [("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x91: ("sfpconfig", [("imm16_math", 8, 16), ("config_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x92: ("sfpswap", _simple_fields("lreg_src_c")),
  0x93: ("sfploadmacro", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("sfpu_addr_mode", 13, 3), ("dest_reg_addr", 0, 13)]),
  0x94: ("sfpshft2", _simple_fields("lreg_src_c")),
  0x95: ("sfplutfp32", [("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x96: ("sfple", _simple_fields()),
  0x97: ("sfpgt", _simple_fields()),
  0x98: ("sfpmul24", _mad_fields()),
  0x99: ("sfparecip", _simple_fields()),
  0xA0: ("atgetm", [("mutex_index", 0, 24)]),
  0xA1: ("atrelm", [("mutex_index", 0, 24)]),
  0xA2: ("stallwait", [("stall_res", 15, 9), ("wait_res", 0, 15)]),
  0xA3: ("seminit", [("max_value", 20, 4), ("init_value", 16, 4), ("sem_sel", 2, 8)]),
  0xA4: ("sempost", [("sem_sel", 2, 8)]),
  0xA5: ("semget", [("sem_sel", 2, 8)]),
  0xA6: ("semwait", [("stall_res", 15, 9), ("sem_sel", 2, 8), ("wait_sem_cond", 0, 2)]),
  0xA7: ("streamwait", [("stall_res", 15, 9), ("target_value", 4, 10), ("target_sel", 3, 1), ("wait_stream_sel", 0, 2)]),
  0xB0: ("wrcfg", [("GprAddress", 16, 6), ("wr128b", 15, 1), ("CfgReg", 0, 11)]),
  0xB1: ("rdcfg", [("GprAddress", 16, 6), ("CfgReg", 0, 11)]),
  0xB2: ("setc16", [("setc16_reg", 16, 8), ("setc16_value", 0, 16)]),
  0xB3: ("rmwcib0", [("Mask", 16, 8), ("Data", 8, 8), ("CfgRegAddr", 0, 8)]),
  0xB4: ("rmwcib1", [("Mask", 16, 8), ("Data", 8, 8), ("CfgRegAddr", 0, 8)]),
  0xB5: ("rmwcib2", [("Mask", 16, 8), ("Data", 8, 8), ("CfgRegAddr", 0, 8)]),
  0xB6: ("rmwcib3", [("Mask", 16, 8), ("Data", 8, 8), ("CfgRegAddr", 0, 8)]),
  0xB7: ("streamwrcfg", [("stream_id_sel", 21, 2), ("StreamRegAddr", 11, 10), ("CfgReg", 0, 11)]),
  # Decode aliases preserve the multiple names used by the config-unit code.
  0xB8: ("cfgshiftmask", [("mask_mode", 23, 1), ("alu_mode", 20, 3), ("mask_width", 15, 5), ("rotate_amt", 10, 5), ("scratch_index", 8, 2), ("cfg_index", 0, 8)], [("disable_mask_on_old_val", 23, 1), ("operation", 20, 3), ("right_cshift_amt", 10, 5), ("scratch_sel", 8, 2), ("CfgReg", 0, 8)]),
  0xC0: ("wrcfg32", [("GprAddress", 18, 6), ("CfgReg", 0, 11)]),
}

def _tt_spec(spec):
  name, fields, *aliases = spec
  return name, tuple(fields), tuple(aliases[0]) if aliases else ()

_TENSIX = {op: _tt_spec(spec) for op, spec in _TENSIX_DECODE.items()}

def _enc_tensix(op, fields, *values, **kw):
  vals = _bind(fields, values, kw)
  w = op << 24
  for fname, shift, width in fields:
    w |= _field(vals[fname], width) << shift
  return w & 0xFFFFFFFF

def _make_tt(op, fields):
  def enc(*args, **kw):
    return _enc_tensix(op, fields, *args, **kw)
  return enc

for _op, (_name, _fields, _aliases) in _TENSIX.items():
  globals()[f"tt_{_name}"] = _make_tt(_op, _fields)

def decode_tensix(word):
  w = word & 0xFFFFFFFF
  op = (w >> 24) & 0xFF
  spec = _TENSIX.get(op)
  if spec is None:
    return f"UNKNOWN_0x{op:02X}", {"word": w, "raw_params": w & 0xFFFFFF}
  name, fields, aliases = spec
  vals = {fname: (w >> shift) & ((1 << width) - 1) for fname, shift, width in fields + aliases}
  vals["word"] = w
  return name, vals

zero, ra, sp, gp, tp, t0, t1, t2, s0, s1 = range(10)
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = range(28, 32)
fp = s0

nop    = lambda: addi(zero, zero, 0)
li     = lambda rd, imm: addi(rd, zero, imm)
mv     = lambda rd, rs: addi(rd, rs, 0)
not_   = lambda rd, rs: xori(rd, rs, -1)
neg    = lambda rd, rs: sub(rd, zero, rs)
seqz   = lambda rd, rs: sltiu(rd, rs, 1)
snez   = lambda rd, rs: sltu(rd, zero, rs)
beqz   = lambda rs, imm: beq(rs, zero, imm)
bnez   = lambda rs, imm: bne(rs, zero, imm)
blez   = lambda rs, imm: bge(zero, rs, imm)
bgez   = lambda rs, imm: bge(rs, zero, imm)
bltz   = lambda rs, imm: blt(rs, zero, imm)
bgtz   = lambda rs, imm: blt(zero, rs, imm)
j      = lambda imm: jal(zero, imm)
jr     = lambda rs: jalr(zero, rs, 0)
ret    = lambda: jalr(zero, ra, 0)
zext_b = lambda rd, rs: andi(rd, rs, 0xFF)

def li32(rd, imm):
  imm &= 0xFFFFFFFF
  imm_s = imm if imm < 0x80000000 else imm - 0x100000000
  hi = (imm_s + 0x800) & 0xFFFFF000
  hi_s = hi if hi < 0x80000000 else hi - 0x100000000
  lo = imm_s - hi_s
  if hi == 0:
    return [addi(rd, zero, lo)]
  return [lui(rd, hi), addi(rd, rd, lo)]

L1_SIZE = 0x00180000
BRISC_FW_BASE = 0x003840
NCRISC_FW_BASE = 0x005440
TRISC0_FW_BASE = 0x005A40
TRISC1_FW_BASE = 0x006040
TRISC2_FW_BASE = 0x006A40
BRISC_PROGRAM_BASE = 0x005460
NCRISC_PROGRAM_BASE = 0x006170
TRISC0_PROGRAM_BASE = 0x006990
TRISC1_PROGRAM_BASE = 0x007110
TRISC2_PROGRAM_BASE = 0x007D60
KERNEL_CONFIG_BASE = 0x0086B0
LDM_BASE = 0xFFB00000

PROGRAM_LAYOUTS = {
  "firmware.brisc":  (BRISC_FW_BASE,  BRISC_FW_BASE,  BRISC_PROGRAM_BASE),
  "firmware.ncrisc": (NCRISC_FW_BASE, NCRISC_FW_BASE, NCRISC_PROGRAM_BASE),
  "firmware.trisc0": (TRISC0_FW_BASE, TRISC0_FW_BASE, TRISC0_PROGRAM_BASE),
  "firmware.trisc1": (TRISC1_FW_BASE, TRISC1_FW_BASE, TRISC1_PROGRAM_BASE),
  "firmware.trisc2": (TRISC2_FW_BASE, TRISC2_FW_BASE, TRISC2_PROGRAM_BASE),
  "program.brisc":   (BRISC_PROGRAM_BASE,  BRISC_PROGRAM_BASE,  KERNEL_CONFIG_BASE),
  "program.ncrisc":  (NCRISC_PROGRAM_BASE, NCRISC_PROGRAM_BASE, KERNEL_CONFIG_BASE),
  "program.trisc0":  (TRISC0_PROGRAM_BASE, TRISC0_PROGRAM_BASE, KERNEL_CONFIG_BASE),
  "program.trisc1":  (TRISC1_PROGRAM_BASE, TRISC1_PROGRAM_BASE, KERNEL_CONFIG_BASE),
  "program.trisc2":  (TRISC2_PROGRAM_BASE, TRISC2_PROGRAM_BASE, KERNEL_CONFIG_BASE),
}

class Program:
  def __init__(self, base=None, upload_base=None, upload_limit=None, kind=None, segments=None):
    layout = PROGRAM_LAYOUTS.get(kind)
    if layout:
      layout_base, layout_upload, layout_limit = layout
      if base is None: base = layout_base
      if upload_base is None: upload_base = layout_upload
      if upload_limit is None: upload_limit = layout_limit
    elif kind is not None and "." in kind and base is None:
      raise ValueError(f"unknown program layout {kind!r}")

    if base is None:
      base = 0
    self.upload_base = base if upload_base is None else upload_base
    self.upload_limit = upload_limit
    self.kind = kind
    self.base = base
    self.items = []
    self.labels = {}
    self.segments = list(segments or [])

  @staticmethod
  def decode(data=None, bin_file="", base=None, upload_base=None, upload_limit=None, kind=None):
    if bin_file:
      path = Path(bin_file)
      if path.suffix == ".json":
        manifest = json.loads(path.read_text())
        p = Program(base=0 if base is None else base, upload_base=upload_base, upload_limit=upload_limit, kind=kind)
        text_base = None
        for seg in manifest["segments"]:
          data = (path.parent / seg["bin"]).read_bytes()
          memsz = int(seg.get("memsz", len(data)))
          if len(data) < memsz:
            data += b"\0" * (memsz - len(data))
          paddr = int(seg["paddr"], 0)
          if text_base is None and "X" in seg.get("perms", ""):
            text_base = paddr
          p.segment(
            paddr, data,
            vaddr=int(seg.get("vaddr", seg["paddr"]), 0),
            memsz=memsz,
            flags=int(seg.get("flags", 0)),
            perms=seg.get("perms", ""),
          )
        if base is None and text_base is not None:
          p.base = text_base
          p.upload_base = text_base if upload_base is None else upload_base
        p.validate()
        return p
      data = path.read_bytes()
    if data is None:
      raise TypeError("decode() needs bytes-like data or bin_file")
    if len(data) % 4:
      raise ValueError(f"byte length {len(data)} not a multiple of 4")
    p = Program(base=base, upload_base=upload_base, upload_limit=upload_limit, kind=kind)
    p.emit(*struct.unpack(f"<{len(data)//4}I", bytes(data)))
    p.segment(p.upload_base, bytes(data))
    p.validate()
    return p

  @property
  def pc(self):
    return self.base + 4 * len(self.items)

  def emit(self, *insns):
    self.items.extend(insns)
    return self

  def word(self, value):
    return self.emit(value)

  def segment(self, paddr, data, *, vaddr=None, memsz=None, flags=0, perms=""):
    self.segments.append({
      "paddr": paddr,
      "vaddr": paddr if vaddr is None else vaddr,
      "data": bytes(data),
      "memsz": len(data) if memsz is None else memsz,
      "flags": flags,
      "perms": perms,
    })
    return self

  def label(self, name):
    self.labels[name] = self.pc
    return self

  def fixup(self, fn):
    self.items.append((self.pc, fn))
    return self

  def beq(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: beq(rs1, rs2, labels[label] - pc))

  def bne(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: bne(rs1, rs2, labels[label] - pc))

  def blt(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: blt(rs1, rs2, labels[label] - pc))

  def bge(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: bge(rs1, rs2, labels[label] - pc))

  def bltu(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: bltu(rs1, rs2, labels[label] - pc))

  def bgeu(self, rs1, rs2, label):
    return self.fixup(lambda labels, pc: bgeu(rs1, rs2, labels[label] - pc))

  def bnez(self, rs, label):
    return self.bne(rs, zero, label)

  def beqz(self, rs, label):
    return self.beq(rs, zero, label)

  def j(self, label):
    return self.fixup(lambda labels, pc: j(labels[label] - pc))

  def jal(self, rd, label):
    return self.fixup(lambda labels, pc: jal(rd, labels[label] - pc))

  def li(self, rd, imm):
    return self.emit(*li32(rd, imm))

  def resolve(self):
    out = []
    for item in self.items:
      if isinstance(item, tuple) and len(item) == 2 and callable(item[1]):
        pc, fn = item
        out.append(fn(self.labels, pc))
      else:
        out.append(item)
    return out

  def pack(self):
    return b"".join((w & 0xFFFFFFFF).to_bytes(4, "little") for w in self.resolve())

  def _flat_segment(self):
    data = self.pack()
    return {
      "paddr": self.upload_base,
      "vaddr": self.base,
      "data": data,
      "memsz": len(data),
      "flags": 5,
      "perms": "RX",
    }

  def validate(self):
    for seg in self.segments or [self._flat_segment()]:
      paddr = seg["paddr"]
      size = seg.get("memsz", len(seg["data"]))
      if size < len(seg["data"]):
        raise ValueError(f"segment at 0x{paddr:x} has memsz smaller than data")
      if self.upload_limit is None:
        continue
      if paddr >= LDM_BASE:
        continue
      start, end = paddr, paddr + size
      if start < self.upload_base or end > self.upload_limit:
        raise ValueError(
          f"segment 0x{start:x}..0x{end:x} exceeds upload range "
          f"0x{self.upload_base:x}..0x{self.upload_limit:x}"
        )
    return self

  def uploads(self):
    return [(seg["paddr"], seg["data"]) for seg in self.pt_loads()]

  def pt_loads(self):
    self.validate()
    return self.segments or [self._flat_segment()]
