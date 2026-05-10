import struct
from collections.abc import Callable
from dataclasses import dataclass

CoreArgs = Callable[[int, int], list[int]]

@dataclass(frozen=True)
class Segment:
  addr: int
  data: bytes
  mcast: bool = True
  label: str = ""

def _bits(v, hi, lo=None):
  if lo is None: lo = hi
  return (v >> lo) & ((1 << (hi - lo + 1)) - 1)

def _sext(v, w): return v - (1 << w) if v & (1 << (w - 1)) else v

def _field(v, w):
  if not 0 <= v < (1 << w):
    raise ValueError(f"{v} does not fit in {w} bits")
  return v

def _sfield(v, w):
  if not -(1 << (w - 1)) <= v < (1 << (w - 1)):
    raise ValueError(f"{v} does not fit in signed {w} bits")
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
  ('srl',    0x00005033, 'R'),
  ('or',     0x00006033, 'R'),   ('and',    0x00007033, 'R'),
  ('mul',    0x02000033, 'R'),   ('mulhu',  0x02003033, 'R'),
  ('divu',   0x02005033, 'R'),   ('remu',   0x02007033, 'R'),
  ('sh1add', 0x20002033, 'R'),   ('sh2add', 0x20004033, 'R'),
  ('sh3add', 0x20006033, 'R'),   ('zext_h', 0x08004033, 'R', 0xFFF0707F),
  ('min',    0x0A004033, 'R'),   ('minu',   0x0A005033, 'R'),
  ('maxu',   0x0A007033, 'R'),

  ('addi',   0x00000013, 'I'),   ('sltiu',  0x00003013, 'I'),
  ('xori',   0x00004013, 'I'),
  ('ori',    0x00006013, 'I'),   ('andi',   0x00007013, 'I'),
  ('ctz',    0x60101013, 'Ish', 0xFFF0707F),
  ('sext_b', 0x60401013, 'Ish', 0xFFF0707F),
  ('sext_h', 0x60501013, 'Ish', 0xFFF0707F),
  ('slli',   0x00001013, 'Ish'), ('srli',   0x00005013, 'Ish'),
  ('srai',   0x40005013, 'Ish'),

  ('lw',     0x00002003, 'I'),   ('lbu',    0x00004003, 'I'),
  ('lhu',    0x00005003, 'I'),   ('sb',     0x00000023, 'S'),
  ('sh',     0x00001023, 'S'),   ('sw',     0x00002023, 'S'),
  ('beq',    0x00000063, 'B'),   ('bne',    0x00001063, 'B'),
  ('blt',    0x00004063, 'B'),   ('bge',    0x00005063, 'B'),
  ('bltu',   0x00006063, 'B'),   ('bgeu',   0x00007063, 'B'),
  ('lui',    0x00000037, 'U'),   ('auipc',  0x00000017, 'U'),
  ('jal',    0x0000006F, 'J'),   ('jalr',   0x00000067, 'I'),

  ('csrrs',  0x00002073, 'CSR'), ('csrrc',  0x00003073, 'CSR'),
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
      w |= _bits(imm, 4, 0) << 7 | _bits(imm, 11, 5) << 25
    case "B":
      imm = _sfield(vals.pop("imm"), 13)
      w |= _bits(imm, 11) << 7 | _bits(imm, 4, 1) << 8 | _bits(imm, 10, 5) << 25 | _bits(imm, 12) << 31
    case "J":
      imm = _sfield(vals.pop("imm"), 21)
      w |= _bits(imm, 19, 12) << 12 | _bits(imm, 11) << 20 | _bits(imm, 10, 1) << 21 | _bits(imm, 20) << 31
    case "U":
      imm = vals.pop("imm")
      if imm != (imm & 0xFFFFF000):
        raise ValueError(f"{imm} is not a U-format immediate")
      w |= imm
  for fname, lo, width, signed in args:
    if fname not in vals:
      continue
    v = _sfield(vals[fname], width) if signed else _field(vals[fname], width)
    w |= v << lo
  return w & 0xFFFFFFFF

_RV_SPECS = tuple(map(_rv_spec, _RV))
_RV_BY_NAME = {name: (base, mask, fmt) for mask, base, name, fmt in _RV_SPECS}

def _x_R(w):   return dict(rd=_bits(w,11,7), rs1=_bits(w,19,15), rs2=_bits(w,24,20))
def _x_I(w):   return dict(rd=_bits(w,11,7), rs1=_bits(w,19,15), imm=_sext(_bits(w,31,20), 12))
def _x_Ish(w): return dict(rd=_bits(w,11,7), rs1=_bits(w,19,15), shamt=_bits(w,24,20))
def _x_S(w):   return dict(rs1=_bits(w,19,15), rs2=_bits(w,24,20), imm=_sext(_bits(w,11,7) | (_bits(w,31,25)<<5), 12))
def _x_B(w):   return dict(rs1=_bits(w,19,15), rs2=_bits(w,24,20), imm=_sext((_bits(w,11,8)<<1) | (_bits(w,30,25)<<5) | (_bits(w,7)<<11) | (_bits(w,31)<<12), 13))
def _x_U(w):   return dict(rd=_bits(w,11,7), imm=w & 0xFFFFF000)
def _x_J(w):   return dict(rd=_bits(w,11,7), imm=_sext((_bits(w,30,21)<<1) | (_bits(w,20)<<11) | (_bits(w,19,12)<<12) | (_bits(w,31)<<20), 21))
def _x_CSR(w): return dict(rd=_bits(w,11,7), rs1=_bits(w,19,15), csr=_bits(w,31,20))
def _x_NONE(w): return {}

_RV_EXTRACT = {'R':_x_R, 'I':_x_I, 'Ish':_x_Ish, 'S':_x_S, 'B':_x_B, 'U':_x_U, 'J':_x_J, 'CSR':_x_CSR, 'NONE':_x_NONE}
_RV_BY_OPCODE = {
  opcode: [spec for spec in _RV_SPECS if (spec[1] & 0x7F) == opcode]
  for opcode in {base & 0x7F for _, base, _, _ in _RV_SPECS}
}

def _ttinsn(imm32):
  if imm32 >= 0xC0000000:
    raise ValueError(f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}")
  return ((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF

def _ops(start, names, fields):
  return {start + i: (name, fields) for i, name in enumerate(names.split())}

_SIMPLE_FIELDS = [("imm12_math", 12, 12), ("lreg_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]
_SIMPLE_SRC_C_FIELDS = [("imm12_math", 12, 12), ("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]
_MAD_FIELDS = [("lreg_src_a", 16, 4), ("lreg_src_b", 12, 4), ("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]
_MOVD_FIELDS = [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("instr_mod", 12, 2), ("dst", 0, 12)]
_CONV3_FIELDS = [("clear_dvalid", 22, 2), ("rotate_weights", 17, 5), ("addr_mode", 14, 3), ("dst", 0, 14)]
_POOL3_FIELDS = [("clear_dvalid", 22, 2), ("pool_addr_mode", 15, 7), ("index_en", 14, 1), ("dst", 0, 14)]
_ELW_FIELDS = [("clear_dvalid", 22, 2), ("dest_accum_en", 21, 1), ("instr_mod19", 19, 2), ("addr_mode", 14, 2), ("dst", 0, 14)]
_GPOOL_FIELDS = [("clear_dvalid", 22, 2), ("instr_mod19", 19, 3), ("pool_addr_mode", 15, 4), ("max_pool_index_en", 14, 1), ("dst", 0, 14)]
_DMA_AB_FIELDS = [("OpBisConst", 23, 1), ("ResultRegIndex", 12, 11), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]
_DMA_OP_FIELDS = [("OpBisConst", 23, 1), ("OpSel", 18, 5), ("ResultRegIndex", 12, 6), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)]
_MUTEX_FIELDS = [("mutex_index", 0, 24)]
_SFP_LOAD_FIELDS = [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("sfpu_addr_mode", 13, 3), ("dest_reg_addr", 0, 13)]
_SFP_IMM16_FIELDS = [("imm16_math", 8, 16), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]
_RMWCIB_FIELDS = [("Mask", 16, 8), ("Data", 8, 8), ("CfgRegAddr", 0, 8)]

_TENSIX_DECODE = {
  0x01: ("mop", [("mop_type", 23, 1), ("loop_count", 16, 7), ("zmask_lo16_or_loop_count", 0, 16)]),
  0x02: ("nop", []),
  0x03: ("mop_cfg", [("zmask_hi16", 0, 16)]),
  0x04: ("replay", [("start_idx", 14, 10), ("len", 4, 10), ("execute_while_loading", 1, 1), ("load_mode", 0, 1)]),
  0x08: ("movd2a", _MOVD_FIELDS),
  0x0A: ("movd2b", _MOVD_FIELDS),
  0x10: ("zeroacc", [("clear_mode", 19, 5), ("use_32_bit_mode", 18, 1), ("clear_zero_flags", 17, 1), ("addr_mode", 14, 3), ("where", 0, 14)]),
  0x11: ("zerosrc", [("zero_val", 4, 20), ("write_mode", 3, 1), ("bank_mask", 2, 1), ("src_mask", 0, 2)]),
  0x12: ("mova2d", _MOVD_FIELDS),
  0x13: ("movb2d", [("dest_32b_lo", 23, 1), ("src", 17, 6), ("addr_mode", 14, 3), ("movb2d_instr_mod", 11, 3), ("dst", 0, 11)]),
  0x14: ("trnspsrca", []),
  0x15: ("rareb", []),
  0x16: ("trnspsrcb", []),
  0x17: ("shiftxa", [("shift_mode", 0, 2), ("log2_amount2", 2, 22)], [("raw", 0, 24)]),
  0x18: ("shiftxb", [("shift_row", 0, 10), ("rot_shift", 10, 4), ("addr_mode", 14, 3)], [("raw", 0, 24)]),
  0x21: ("clrexphist", []),
  0x22: ("conv3s1", _CONV3_FIELDS),
  0x23: ("conv3s2", _CONV3_FIELDS),
  0x24: ("mfconv3s1", _CONV3_FIELDS),
  0x25: ("apool3s1", _POOL3_FIELDS),
  0x26: ("mvmul", [("clear_dvalid", 22, 2), ("instr_mod19", 19, 3), ("addr_mode", 14, 3), ("dst", 0, 10)], [("broadcast_srcb", 19, 1)]),
  0x27: ("elwmul", _ELW_FIELDS),
  0x28: ("elwadd", _ELW_FIELDS),
  0x29: ("dotpv", _ELW_FIELDS),
  0x2A: ("mpool3s2", _POOL3_FIELDS),
  0x30: ("elwsub", _ELW_FIELDS),
  0x31: ("mpool3s1", _POOL3_FIELDS),
  0x32: ("apool3s2", _POOL3_FIELDS),
  0x33: ("gmpool", _GPOOL_FIELDS),
  0x34: ("gapool", _GPOOL_FIELDS),
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
  0x58: ("adddmareg", _DMA_AB_FIELDS),
  0x5A: ("muldmareg", _DMA_AB_FIELDS),
  0x5B: ("bitwopdmareg", _DMA_OP_FIELDS),
  0x5C: ("shiftdmareg", [("OpBisConst", 23, 1), ("Mode", 18, 5), ("ResultRegIndex", 12, 6), ("OpBRegIndex", 6, 6), ("OpARegIndex", 0, 6)], [("OpSel", 18, 5)]),
  0x5D: ("cmpdmareg", _DMA_OP_FIELDS),
  0x5E: ("setadcxx", [("CntSetMask", 21, 3), ("x_end2", 10, 11), ("x_start", 0, 10)]),
  0x60: ("dmanop", []),
  0x67: ("storereg", [("TdmaDataRegIndex", 18, 6), ("RegAddr", 0, 18)]),
  0x70: ("sfpload", _SFP_LOAD_FIELDS),
  0x71: ("sfploadi", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("imm16", 0, 16)]),
  0x72: ("sfpstore", _SFP_LOAD_FIELDS),
  0x73: ("sfplut", [("lreg_ind", 20, 4), ("instr_mod0", 16, 4), ("dest_reg_addr", 0, 16)]),
  0x74: ("sfpmuli", _SFP_IMM16_FIELDS),
  0x75: ("sfpaddi", _SFP_IMM16_FIELDS),
  0x8C: ("sfptransp", _SIMPLE_FIELDS),
  0x8E: ("sfpstochrnd", [("rnd_mode", 21, 3), ("imm8_math", 16, 8), ("lreg_src_b", 12, 4), ("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x8F: ("sfpnop", []),
  0x90: ("sfpcast", [("lreg_src_c", 8, 4), ("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x91: ("sfpconfig", [("imm16_math", 8, 16), ("config_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0x93: ("sfploadmacro", _SFP_LOAD_FIELDS),
  0x95: ("sfplutfp32", [("lreg_dest", 4, 4), ("instr_mod1", 0, 4)]),
  0xA0: ("atgetm", _MUTEX_FIELDS),
  0xA1: ("atrelm", _MUTEX_FIELDS),
  0xA2: ("stallwait", [("stall_res", 15, 9), ("wait_res", 0, 15)]),
  0xA3: ("seminit", [("max_value", 20, 4), ("init_value", 16, 4), ("sem_sel", 2, 8)]),
  0xA4: ("sempost", [("sem_sel", 2, 8)]),
  0xA5: ("semget", [("sem_sel", 2, 8)]),
  0xA6: ("semwait", [("stall_res", 15, 9), ("sem_sel", 2, 8), ("wait_sem_cond", 0, 2)]),
  0xA7: ("streamwait", [("stall_res", 15, 9), ("target_value", 4, 10), ("target_sel", 3, 1), ("wait_stream_sel", 0, 2)]),
  0xB0: ("wrcfg", [("GprAddress", 16, 6), ("wr128b", 15, 1), ("CfgReg", 0, 11)]),
  0xB1: ("rdcfg", [("GprAddress", 16, 6), ("CfgReg", 0, 11)]),
  0xB2: ("setc16", [("setc16_reg", 16, 8), ("setc16_value", 0, 16)]),
  0xB3: ("rmwcib0", _RMWCIB_FIELDS),
  0xB4: ("rmwcib1", _RMWCIB_FIELDS),
  0xB5: ("rmwcib2", _RMWCIB_FIELDS),
  0xB6: ("rmwcib3", _RMWCIB_FIELDS),
  0xB7: ("streamwrcfg", [("stream_id_sel", 21, 2), ("StreamRegAddr", 11, 10), ("CfgReg", 0, 11)]),
  # Decode aliases preserve the multiple names used by the config-unit code.
  0xB8: ("cfgshiftmask", [("mask_mode", 23, 1), ("alu_mode", 20, 3), ("mask_width", 15, 5), ("rotate_amt", 10, 5), ("scratch_index", 8, 2), ("cfg_index", 0, 8)], [("disable_mask_on_old_val", 23, 1), ("operation", 20, 3), ("right_cshift_amt", 10, 5), ("scratch_sel", 8, 2), ("CfgReg", 0, 8)]),
  0xC0: ("wrcfg32", [("GprAddress", 18, 6), ("CfgReg", 0, 11)]),
}
_TENSIX_DECODE.update(_ops(0x76, "sfpdivp2 sfpexexp sfpexman sfpiadd sfpshft sfpsetcc sfpmov sfpabs sfpand sfpor sfpnot sfplz sfpsetexp sfpsetman", _SIMPLE_FIELDS))
_TENSIX_DECODE.update(_ops(0x84, "sfpmad sfpadd sfpmul", _MAD_FIELDS))
_TENSIX_DECODE.update(_ops(0x87, "sfppushc sfppopc sfpsetsgn sfpencc sfpcompc", _SIMPLE_FIELDS))
_TENSIX_DECODE[0x8D] = ("sfpxor", _SIMPLE_FIELDS)
_TENSIX_DECODE.update({0x92: ("sfpswap", _SIMPLE_SRC_C_FIELDS), 0x94: ("sfpshft2", _SIMPLE_SRC_C_FIELDS)})
_TENSIX_DECODE.update({0x96: ("sfple", _SIMPLE_FIELDS), 0x97: ("sfpgt", _SIMPLE_FIELDS), 0x98: ("sfpmul24", _MAD_FIELDS), 0x99: ("sfparecip", _SIMPLE_FIELDS)})

zero, ra, sp, gp, tp, t0, t1, t2, s0, s1 = range(10)
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = range(28, 32)
fp = s0

def _u32(v):
  return (v & 0xFFFFFFFF).to_bytes(4, "little")

_LOCAL_DATA = {
  "brisc": b"",
  "ncrisc": b"\0" * 40,
  "trisc0": b"\0" * 4,
  "trisc1": bytes([4]) * 32 + _u32(5) * 32 + _u32(5) * 32,
  "trisc2": bytes([16]) * 32 + bytes([4]) * 32 + b"\0" * 32 + bytes([5]) * 32 + bytes([5]) * 32,
}

class Kernel:
  _RV_BY_NAME = _RV_BY_NAME
  _TENSIX = {
    op: (spec[0], tuple(spec[1]), tuple(spec[2]) if len(spec) > 2 else ())
    for op, spec in _TENSIX_DECODE.items()
  }
  _TENSIX_BY_NAME = {name: (op, fields) for op, (name, fields, _aliases) in _TENSIX.items()}

  def __init__(
    self, *, kind, base=None, upload_base=None,
    rtas: CoreArgs | None = None, crtas: list[int] | None = None,
    local_data=None,
  ):
    if kind not in _LOCAL_DATA:
      raise ValueError(f"unknown kernel kind {kind!r}")
    if base is None:
      base = 0
    self.upload_base = base if upload_base is None else upload_base
    self.base = base
    self.items = []
    self.labels = {}
    self.rtas = rtas
    self.crtas = [] if crtas is None else crtas
    self.kind = kind
    self.local_data = local_data

  @classmethod
  def _riscv_word(cls, name, *values, **kw):
    try:
      base, mask, fmt = cls._RV_BY_NAME[name]
    except KeyError as exc:
      raise ValueError(f"unknown RISC-V instruction {name!r}") from exc
    return _enc_rv(base, mask, fmt, *values, **kw)

  @classmethod
  def decode_rv(cls, word):
    w = word & 0xFFFFFFFF
    for mask, base, name, fmt in _RV_BY_OPCODE.get(w & 0x7F, ()):
      if (w & mask) == (base & mask):
        fields = _RV_EXTRACT[fmt](w)
        fields["word"] = w
        return name, fields
    return "UNKNOWN", {"word": w}

  @classmethod
  def _tensix_word(cls, name, *values, **kw):
    try:
      op, fields = cls._TENSIX_BY_NAME[name]
    except KeyError as exc:
      raise ValueError(f"unknown Tensix instruction {name!r}") from exc
    vals = _bind(fields, values, kw)
    w = op << 24
    for fname, shift, width in fields:
      w |= _field(vals[fname], width) << shift
    return w & 0xFFFFFFFF

  @classmethod
  def decode_tensix(cls, word):
    w = word & 0xFFFFFFFF
    op = (w >> 24) & 0xFF
    spec = cls._TENSIX.get(op)
    if spec is None:
      return f"UNKNOWN_0x{op:02X}", {"word": w, "raw_params": w & 0xFFFFFF}
    name, fields, aliases = spec
    vals = {fname: (w >> shift) & ((1 << width) - 1) for fname, shift, width in fields + aliases}
    vals["word"] = w
    return name, vals

  def ttinsn(self, imm32):
    return self.emit(_ttinsn(imm32))

  def _rv_emit(self, name, *args, **kw):
    if kw:
      return self.emit(self._riscv_word(name, *args, **kw))
    if name in {"beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"} and args and isinstance(args[-1], str):
      label = args[-1]
      operands = args[:-1]
      self.items.append((self.pc, lambda labels, pc: self._riscv_word(name, *operands, labels[label] - pc)))
      return self
    return self.emit(self._riscv_word(name, *args))

  def __getattr__(self, name):
    if name.startswith("tt_"):
      opname = name[3:]
      if opname in self._TENSIX_BY_NAME:
        return lambda *args, **kw: self.emit(self._tensix_word(opname, *args, **kw))
    if name in {"and", "or"}:
      raise AttributeError(name)
    opname = {"and_": "and", "or_": "or"}.get(name, name)
    if opname in self._RV_BY_NAME:
      return lambda *args, **kw: self._rv_emit(opname, *args, **kw)
    raise AttributeError(name)

  @staticmethod
  def decode(data=None, bin_file="", *, kind, base=None, upload_base=None):
    if bin_file:
      with open(bin_file, "rb") as f:
        data = f.read()
    if data is None:
      raise TypeError("decode() needs bytes-like data or bin_file")
    if len(data) % 4:
      raise ValueError(f"byte length {len(data)} not a multiple of 4")
    k = Kernel(kind=kind, base=base, upload_base=upload_base)
    k.emit(*struct.unpack(f"<{len(data)//4}I", bytes(data)))
    return k

  @property
  def pc(self):
    return self.base + 4 * len(self.items)

  def emit(self, *insns):
    self.items.extend(insns)
    return self

  def rta(self, *values):
    if len(values) != 1 or not callable(values[0]):
      raise TypeError("rta() expects one callable: f(core_x, core_y) -> list[int]")
    self.rtas = values[0]
    return self

  def crta(self, *values):
    self.crtas = list(values[0]) if len(values) == 1 and isinstance(values[0], (list, tuple)) else list(values)
    return self

  def label(self, name):
    self.labels[name] = self.pc
    return self

  def _pack(self):
    words = []
    for item in self.items:
      if isinstance(item, tuple) and len(item) == 2 and callable(item[1]):
        pc, fn = item
        words.append(fn(self.labels, pc))
      else:
        words.append(item)
    return b"".join((w & 0xFFFFFFFF).to_bytes(4, "little") for w in words)

  def _local_data(self):
    if self.local_data is not None:
      return bytes(self.local_data)
    return _LOCAL_DATA[self.kind]

  def compile(self) -> list[Segment]:
    text = self._pack()
    local_data = self._local_data()
    segments = []
    if text:
      segments.append(Segment(self.upload_base, text, label="text"))
    if local_data:
      segments.append(Segment(self.upload_base + len(text), local_data, label="local_data"))
    return segments
