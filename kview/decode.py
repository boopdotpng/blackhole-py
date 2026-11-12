"""Decode a kernel image into annotated rows for the reader.

Everything is derived from the .bin: RV32 and inline Tensix words are decoded, a constant/symbol propagation over the
control-flow graph (calls included) resolves register values, and every resolved address or stored value is named from
the Blackhole register maps (data/), fw/abi.h and the model's manifest.json.
"""
import json, re, struct
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
ISA = {int(k): v for k, v in json.loads((DATA / "isa.json").read_text()).items()}
ISA_BY_NAME = {v["name"]: (k, v) for k, v in ISA.items()}
REGS = json.loads((DATA / "tensix_regs.json").read_text())
FULL_REGS = json.loads((DATA / "registers_full.json").read_text())
TILE = json.loads((DATA / "tile_regs.json").read_text())
SFPU_REGS = json.loads((DATA / "sfpu_registers.json").read_text())
TILE_MODULES = {m["name"]: m["regs"] for m in TILE["regs"]}
MASK = 0xFFFFFFFF
L1_SIZE = 0x180000

def hx(n): return f"0x{n & MASK:x}"
def hex8(n): return f"0x{n & MASK:08x}"
def signed(n, bits): return n - (1 << bits) if n & (1 << (bits - 1)) else n
def f32(bits): return struct.unpack("<f", struct.pack("<I", bits & MASK))[0]
def fnum(x): return f"{x:.7g}"

# ---------------------------------------------------------------------------------------------------------------------
# Names

STALL = "TDMA SYNC PACK UNPACK XMOV THCON MATH CFG SFPU".split()
WAIT = "THCON UNPACK0 UNPACK1 PACK0 MATH SRCA_CLR SRCB_CLR SRCA_VLD SRCB_VLD XMOV TRISC_CFG SFPU CFGEXU".split()
WAIT_TEXT = ("ThCon idle", "unpacker 0 idle", "unpacker 1 idle", "packer idle", "math idle", "SrcA cleared", "SrcB cleared", "SrcA valid",
             "SrcB valid", "mover idle", "TRISC config idle", "SFPU idle", "config unit idle")
SEM = "FPU_SFPU MATH_PACK UNPACK_TO_DEST UNPACK_OPERAND_SYNC PACK_DONE UNPACK_SYNC UNPACK_MATH_DONE MATH_DONE".split()
DATA_FORMAT = {0: "Float32", 1: "Float16", 2: "Bfp8", 3: "Bfp4", 4: "Tf32", 5: "Float16_b (BF16)", 6: "Bfp8_b", 7: "Bfp4_b",
               8: "Int32", 9: "UInt16", 10: "Lf8 (FP8)", 11: "Bfp2", 14: "Int8", 15: "Bfp2_b"}
SFP_FMT = "configured FP16 BF16 FP32 INT32 INT8 UINT16 HI16 INT16 LO16 INT32_ALL ZERO INT32_SM INT8_COMP LO16_ONLY HI16_ONLY".split()
LOADI_MODE = {0: "BF16", 1: "FP16", 2: "UINT16", 4: "INT16", 8: "UPPER16", 10: "LOWER16"}
SFPCONFIG_DEST = {0: "macro instruction 0", 1: "macro instruction 1", 2: "macro instruction 2", 3: "macro instruction 3",
                  4: "macro sequence 0", 5: "macro sequence 1", 6: "macro sequence 2", 7: "macro sequence 3",
                  8: "macro control", 9: "PRNG state", 11: "L11", 12: "L12", 13: "L13", 14: "L14", 15: "lane config (L15)"}
LREG_CONST = {8: "0.8373", 9: "0", 10: "1", 11: "-1 (programmable)", 12: "L12 (programmable)", 13: "L13 (programmable)",
              14: "L14 (programmable)", 15: "lane id"}
RISC_ROLE = {"brisc": "BRISC · data movement, NoC 0", "ncrisc": "NCRISC · data movement, NoC 1",
             "trisc0": "TRISC0 · unpack thread", "trisc1": "TRISC1 · math thread", "trisc2": "TRISC2 · pack thread"}
GPR_NAMES = {
  "trisc0": {40: "FACE_DIM_16x16", 41: "FACE_DIM_8x16", 42: "FACE_DIM_4x16", 43: "FACE_DIM_2x16", 44: "FACE_DIM_1x16"},
  "trisc2": {4: "DEST_OFFSET_LO", 8: "DEST_OFFSET_HI", 16: "TILE_HEADER[0] (tile size / 16)", 17: "TILE_HEADER[1]",
             18: "TILE_HEADER[2]", 19: "TILE_HEADER[3]", 52: "EXP0_SEC_SIZE_BFP"},
}
MOP_SLOTS = ("outer loop count", "inner loop count", "start op", "end op 0", "end op 1", "loop op", "loop op 1 (alternates)",
             "last op, final outer iteration", "last op, other outer iterations")
MOP_SLOTS_T0 = ("unused by template 0", "flags (bit0: +B/skipB, bit1: +A1..A3)", "insn B", "insn A0", "insn A1", "insn A2",
                "insn A3", "skip A (zmask bit set)", "skip B (zmask bit set)")
# p150: NoC endpoints of each DRAM bank ([0] NoC 0 default, [1] NoC 1 default, [2] spare port)
DRAM_ENDPOINTS = (((17, 14), (17, 13), (17, 12)), ((17, 15), (17, 16), (17, 17)), ((17, 18), (17, 19), (17, 20)),
                  ((17, 21), (17, 22), (17, 23)), ((18, 14), (18, 13), (18, 12)), ((18, 17), (18, 16), (18, 15)),
                  ((18, 20), (18, 19), (18, 18)), ((18, 23), (18, 22), (18, 21)))
DEBUG_NOTES = {"soft_reset_0": "bit set = held in reset: 11 BRISC, 12-14 TRISC0-2, 18 NCRISC",
               "wall_clock_0": "reading latches the high word", "clk_gate_en": "clock gating per TDMA block"}

def coord_name(v):
  x, y = v & 0x3F, (v >> 6) & 0x3F
  for bank, ports in enumerate(DRAM_ENDPOINTS):
    if (x, y) in ports: return f"({x},{y}) DRAM bank {bank}"
  if (x, y) == (19, 24): return f"({x},{y}) PCIe / host"
  if (1 <= x <= 7 or 10 <= x <= 16) and 2 <= y <= 11: return f"({x},{y}) Tensix"
  return f"({x},{y})"

def bits_names(value, names, prefix=""):
  out = [prefix + n for i, n in enumerate(names) if value >> i & 1]
  return " | ".join(out) if out else "none"

def lreg(n, read=True):
  if n < 8: return f"L{n}"
  if read and n in LREG_CONST: return f"L{n}={LREG_CONST[n]}" if n < 12 or n == 15 else f"L{n}"
  return f"L{n}"

def noc_ctrl(v):
  parts = [("read", "atomic", "write", "write+atomic")[v & 3]]
  for bit, name in ((2, "byte-enable"), (3, "inline data"), (4, "response marked (acked)"), (5, "multicast"), (6, "VC linked"),
                    (8, "path reserve"), (9, "drop read ack"), (16, "multicast y-first"), (17, "include sender")):
    if v >> bit & 1: parts.append(name)
  if v >> 7 & 1: parts.append(f"static VC {v >> 13 & 7}")
  if v >> 27: parts.append(f"priority {v >> 27 & 15}")
  if not v >> 4 & 1 and v & 2: parts.append("posted")
  return ", ".join(parts)

# ---------------------------------------------------------------------------------------------------------------------
# Tensix decode

def cfg_fields(group, index, value=None, mask=None):
  fields = list(REGS[group].get(str(index), []))
  known = {f["name"] for f in fields}
  fields += [f for f in FULL_REGS[group].get(str(index), []) if f["name"] not in known]
  out = []
  for f in sorted(fields, key=lambda f: f["shift"]):
    bits = ((1 << f["size"]) - 1) << f["shift"]
    if mask is not None and not bits & mask: continue
    v = None if not isinstance(value, int) else (value & bits) >> f["shift"]
    out.append(dict(name=f["name"], value=v, lo=f["shift"], hi=f["shift"] + f["size"] - 1,
                    partial=mask is not None and mask & bits != bits, label=field_label(f["name"], v, f["size"])))
  return out

def field_label(name, v, size):
  if v is None: return ""
  if size == 4 and re.search(r"data_format|ALU_FORMAT_SPEC_REG\w*_val|SrcA_val|SrcB_val|Dstacc_val", name, re.I):
    return DATA_FORMAT.get(v, "")
  if re.search(r"Base_address|Base_cntx\d_address|L1_Dest_addr", name) and v:
    return f"L1 {hx((v + 1) << 4)} (stored as addr/16 - 1)"
  if size >= 8 and v > 9: return hx(v)
  return ""

def cfg_title(group, index):
  fields = cfg_fields(group, index)
  if not fields: return f"{group}[{index}]"
  names = [f["name"] for f in fields]
  prefix = names[0]
  for n in names[1:]:
    while not n.startswith(prefix): prefix = prefix[:-1]
  prefix = prefix.rstrip("_")
  if len(names) == 1 or len(prefix) < 6: prefix = names[0] if len(names) == 1 else prefix or names[0]
  return prefix

def cfg_name(group, index):
  title = cfg_title(group, index)
  return f"{group}[{index}]" + ("" if title.startswith(group + "[") else f" {title}")

def addr_mod_text(tcfg, sel):
  """What ADDR_MOD slot `sel` does, from the SETC16 writes seen so far in listing order."""
  parts = []
  ab, dst = tcfg.get(12 + sel), tcfg.get(28 + sel)
  if ab is None and dst is None: return None
  for reg, value in ((12 + sel, ab), (28 + sel, dst)):
    if value is None: continue
    for f in cfg_fields("thread_cfg", reg, value):
      short = f["name"].split("_")[-1]
      if f["value"]: parts.append(f"{short}={f['value']}")
  return ", ".join(parts) if parts else "no counter change"

def tt_decode(word, tcfg=None):
  info = ISA.get(word >> 24)
  if info is None: return dict(op=".tensix", args=[], gist=f"unknown Tensix opcode {hx(word >> 24)}", opcode=word >> 24, tword=word)
  name = info["name"]
  vals, args = {}, []
  for f in info["fields"]:
    v = (word >> f["lo"]) & ((1 << (f["hi"] - f["lo"] + 1)) - 1)
    vals[f["name"]] = v
    args.append([f["name"], v, ""])
  d = dict(op=name, args=args, opcode=word >> 24, tword=word)
  g = lambda n, default=0: vals.get(n, default)
  label = {}
  gist = ""
  if name.startswith("SFP"):
    for n, v in vals.items():
      if n.startswith("lreg"): label[n] = lreg(v, n not in ("lreg_dest", "lreg_ind"))
    D, C = lreg(g("lreg_dest"), False), lreg(g("lreg_c", g("lreg_src_c")))
    m1, imm12 = g("instr_mod1"), g("imm12_math")
    if name in ("SFPLOAD", "SFPSTORE", "SFPLOADMACRO"):
      fmt, a = SFP_FMT[g("instr_mod0")], g("dest_reg_addr")
      label["instr_mod0"] = fmt
      label["dest_reg_addr"] = f"Dst rows {a & ~3}..{(a & ~3) + 3}, {'odd' if a & 2 else 'even'} columns" if name != "SFPLOADMACRO" else ""
      where = f"Dst[{a}]"
      if name == "SFPLOAD": gist = f"L{g('lreg_ind')} ← {where} as {fmt}"
      elif name == "SFPSTORE": gist = f"{where} ← {lreg(g('lreg_ind'))} as {fmt}"
      else: gist = f"load {where} as {fmt}, then run macro sequence {g('lreg_ind') >> 2} (dest low bits {g('lreg_ind') & 3})"
      if (am := addr_mod_text(tcfg or {}, g("sfpu_addr_mode"))) is not None: label["sfpu_addr_mode"] = f"ADDR_MOD_{g('sfpu_addr_mode')}: {am}"
    elif name == "SFPLOADI":
      mode, imm, L = g("instr_mod0"), g("imm16"), f"L{g('lreg_ind')}"
      label["instr_mod0"] = LOADI_MODE.get(mode, "?")
      label["imm16"] = hx(imm)
      if mode == 0: gist = f"{L} ← {fnum(f32(imm << 16))} (BF16 {hx(imm)})"
      elif mode == 2: gist = f"{L} ← {imm} (uint16)"
      elif mode == 4: gist = f"{L} ← {signed(imm, 16)} (int16)"
      elif mode == 8: gist = f"{L}[31:16] ← {hx(imm)}"
      elif mode == 10: gist = f"{L}[15:0] ← {hx(imm)}"
      else: gist = f"{L} ← imm {hx(imm)} (mode {mode})"
    elif name in ("SFPMAD", "SFPMUL", "SFPADD", "SFPMUL24"):
      A, B, Cc = lreg(g("lreg_src_a") & 15), lreg(g("lreg_src_b")), lreg(g("lreg_src_c"))
      if m1 & 4: A = "L[L7]"
      Dd = "L[L7]" if m1 & 8 else D
      na, nc = ("-" if m1 & 1 else ""), ("- " if m1 & 2 else "+ ")
      if name == "SFPMUL" or (name == "SFPMAD" and g("lreg_src_c") == 9 and not m1 & 2): gist = f"{Dd} ← {na}{A} × {B}"
      elif name == "SFPADD" or (name == "SFPMAD" and g("lreg_src_a") == 10): gist = f"{Dd} ← {na}{B} {nc}{Cc}"
      else: gist = f"{Dd} ← {na}{A} × {B} {nc}{Cc}"
      if name == "SFPMUL24": gist += " (24-bit integer multiply)"
    elif name in ("SFPADDI", "SFPMULI"):
      imm = g("imm16_math"); label["imm16_math"] = f"BF16 {fnum(f32(imm << 16))}"
      gist = f"{D} ← {D} {'+' if name == 'SFPADDI' else '×'} {fnum(f32(imm << 16))}"
    elif name == "SFPMOV":
      gist = {0: f"{D} ← {C}", 1: f"{D} ← -{C}", 2: f"{D} ← {C} (all lanes, ignores predication)"}.get(m1, f"{D} ← special state {g('lreg_c')}" if m1 == 8 else f"{D} ← {C} (mode {m1})")
    elif name == "SFPABS": gist = f"{D} ← |{C}| ({'FP32' if m1 & 1 else 'integer'})"
    elif name == "SFPNOT": gist = f"{D} ← ~{C}"
    elif name == "SFPLZ": gist = f"{D} ← count leading zeros of {C}" + (f" (mod {m1})" if m1 else "")
    elif name in ("SFPAND", "SFPOR", "SFPXOR"):
      sym = {"SFPAND": "&", "SFPOR": "|", "SFPXOR": "^"}[name]
      gist = f"{D} ← {D} {sym} {C}"
    elif name == "SFPSHFT":
      s = signed(imm12, 12)
      if m1 & 1: gist = f"{D} ← {D} {'<<' if s >= 0 else '>>'} {abs(s)}" + (" (arithmetic)" if m1 & 2 else "")
      else: gist = f"{D} ← {D} shifted by {C} (+ left, - right)"
    elif name == "SFPSHFT2":
      gist = {0: "L0←L1, L1←L2, L2←L3, L3←0 (shift registers)", 1: "chained copy across L0-L3 lane groups",
              2: f"rotate {C} lanes right within groups, and copy", 3: f"{D} ← {C} with lanes rotated right by 1 within each group of 8",
              4: f"{D} ← {C} with lanes shifted right by 1 within each group of 8 (zero fill)",
              5: f"{D} ← {lreg(imm12 & 15)} bit-shifted by {C}", 6: f"{D} ← {C} bit-shifted by {signed(imm12, 12)}"}.get(m1, "")
    elif name == "SFPIADD":
      s = signed(imm12, 12)
      gist = f"{D} ← {C} + {s}" if m1 & 1 else f"{D} ← {C} - {D}" if m1 & 2 else f"{D} ← {C} + {D}"
      gist += " (integer" + ("" if m1 & 4 else ", sets flags: result " + (">= 0" if m1 & 8 else "< 0")) + ")"
    elif name == "SFPSWAP":
      gist = f"swap {D}, {C}" if m1 == 0 else f"{D} ← min({D},{C}), {C} ← max" if m1 == 1 else f"{D} ← max({D},{C}), {C} ← min" if m1 == 9 else f"min/max of {D}, {C} by lane subgroup (mode {m1})"
    elif name == "SFPEXMAN": gist = f"{D} ← mantissa of {C}" + ("" if m1 & 1 else " with hidden bit 23 set")
    elif name == "SFPEXEXP": gist = f"{D} ← exponent of {C}" + (" (biased)" if m1 & 1 else " (unbiased)") + (", sets flags from sign" if m1 & 2 else "")
    elif name == "SFPSETEXP": gist = f"{D} ← {C} with exponent {'= ' + str(imm12 & 255) if m1 & 1 else 'from ' + D}"
    elif name == "SFPSETMAN": gist = f"{D} ← {C} with mantissa {'= ' + hx(imm12) if m1 & 1 else 'from ' + D}"
    elif name == "SFPSETSGN": gist = f"{D} ← {C} with sign {'= ' + str(imm12 & 1) if m1 & 1 else 'from ' + D}"
    elif name == "SFPCAST":
      src = lreg(g("lreg_src_c") & 15)
      gist = {0: f"{D} ← float(sign-magnitude int {src})", 1: f"{D} ← float({src}), stochastic rounding", 2: f"{D} ← |{src}| (integer)",
              3: f"{D} ← {src} converted between two's complement and sign-magnitude"}.get(m1, "")
    elif name == "SFPARECIP": gist = {0: f"{D} ← 1 / {C} (approximate)", 1: f"{D} ← conditional reciprocal of {C}", 2: f"{D} ← exp({C}) (approximate)"}.get(m1, "")
    elif name == "SFPGT": gist = f"flags / {D} ← {D} > {C} (mod {m1})"
    elif name == "SFPLE": gist = f"flags / {D} ← {D} <= {C} (mod {m1})"
    elif name == "SFPSTOCHRND": gist = f"{D} ← round({lreg(g('lreg_src_c'))}) (rnd_mode {g('rnd_mode')}, mod {m1})"
    elif name == "SFPTRANSP": gist = "transpose L0-L3 and L4-L7 with their four lane groups"
    elif name == "SFPCONFIG":
      dest, imm = g("config_dest"), g("imm16_math")
      label["config_dest"] = SFPCONFIG_DEST.get(dest, "")
      src = f"{hx(imm)}" if m1 & 1 else "L0"
      gist = f"SFPU {SFPCONFIG_DEST.get(dest, 'config ' + str(dest))} ← {src}"
      if 11 <= dest <= 14 and m1 & 1: gist += f" ({fnum(f32(imm << 16))} as BF16)"
    elif name == "SFPENCC":
      gist = "lane predication: " + ("toggle enable" if m1 & 1 else f"enable = {imm12 & 1}" if m1 & 2 else "enable unchanged") + \
             (f", flags = {imm12 >> 1 & 1}" if m1 & 8 else ", flags = 1")
    elif name == "SFPNOP": gist = ""
  elif name == "STALLWAIT":
    label["stall_res"], label["wait_res"] = bits_names(g("stall_res"), STALL), bits_names(g("wait_res"), WAIT)
    until = [WAIT_TEXT[i] for i in range(len(WAIT_TEXT)) if g("wait_res") >> i & 1]
    gist = f"hold {label['stall_res']} instructions until " + (", ".join(until) if until else "nothing (no wait)")
  elif name in ("SEMWAIT", "SEMPOST", "SEMGET", "SEMINIT"):
    sems = bits_names(g("sem_sel"), SEM)
    label["sem_sel"] = sems
    if name == "SEMWAIT":
      label["stall_res"] = bits_names(g("stall_res"), STALL)
      cond = {1: "is zero", 2: "is at max"}.get(g("wait_sem_cond"), f"cond {g('wait_sem_cond')}")
      label["wait_sem_cond"] = cond
      gist = f"hold {label['stall_res']} instructions while semaphore {sems} {cond}"
    elif name == "SEMPOST": gist = f"semaphore {sems} += 1"
    elif name == "SEMGET": gist = f"semaphore {sems} -= 1"
    else: gist = f"init semaphore {sems}: max {g('max_value')}, value {g('init_value')}"
  elif name == "SETC16":
    reg, value = g("setc16_reg"), g("setc16_value")
    fields = cfg_fields("thread_cfg", reg, value)
    d["config"] = dict(group="thread_cfg", index=reg, bank="this thread", fields=fields, title=cfg_title("thread_cfg", reg))
    label["setc16_reg"] = cfg_title("thread_cfg", reg)
    gist = "; ".join(f"{f['name']} = {f['value']}" for f in fields if f["value"]) or f"{cfg_title('thread_cfg', reg)} = 0"
  elif name.startswith("RMWCIB"):
    shift = int(name[-1]) * 8
    reg, mask, data = g("CfgRegAddr"), g("Mask") << shift, g("Data") << shift
    fields = cfg_fields("cfg", reg, data, mask)
    d["config"] = dict(group="cfg", index=reg, bank="current state", fields=fields, title=cfg_title("cfg", reg), mask=mask)
    label["CfgRegAddr"] = cfg_title("cfg", reg)
    gist = "; ".join(f"{f['name']} = {f['value']}" + (f" ({f['label']})" if f["label"] else "") for f in fields) or f"cfg[{reg}] byte {shift // 8}: mask {hx(mask >> shift)} data {hx(data >> shift)}"
  elif name in ("WRCFG", "RDCFG"):
    reg = g("CfgReg", g("CfgRegAddr"))
    d["config"] = dict(group="cfg", index=reg, bank="current state", fields=cfg_fields("cfg", reg), title=cfg_title("cfg", reg))
    label["CfgReg"] = cfg_title("cfg", reg)
    gist = f"cfg[{reg}] {cfg_title('cfg', reg)} ← Tensix GPR {g('GprAddress')}" + (" (128-bit)" if g("wr128b") else "") if name == "WRCFG" else f"Tensix GPR {g('GprAddress')} ← cfg[{reg}]"
  elif name == "MOP":
    gist = "run MOP template 1 (nested loop from MOP_CFG)" if g("mop_type") else f"run MOP template 0 × {g('loop_count') + 1}, zmask lo {hx(g('zmask_lo16_or_loop_count'))}"
  elif name == "MOP_CFG": gist = f"MOP zmask[31:16] ← {hx(g('zmask_hi16'))}"
  elif name == "REPLAY":
    s, n = g("start_idx"), g("len")
    span = f"replay[{s}]" if n == 1 else f"replay[{s}..{s + n - 1}]"
    gist = (f"record next {n} instruction{'s' * (n != 1)} into {span}" + (" and execute them" if g("execute_while_loading") else ", not executed")) if g("load_mode") else f"play {span}"
  elif name in ("SETRWC", "INCRWC"):
    cr = g("rwc_cr")
    if name == "SETRWC":
      m = g("BitMask")
      sets = [f"{n}={v}" + ("+CR" if cr >> i & 1 else "") for i, (n, v) in enumerate((("SrcA", g("rwc_a")), ("SrcB", g("rwc_b")), ("Dst", g("rwc_d")))) if m >> i & 1]
      if m & 8: sets.append("fidelity=0")
      gist = "set counters " + (", ".join(sets) or "none")
      if g("clear_ab_vld"): gist += "; release " + ("SrcA", "SrcB", "SrcA+SrcB")[g("clear_ab_vld") - 1]
    else:
      incs = [f"{n}+={v}" + (" (via CR)" if cr >> i & 1 else "") for i, (n, v) in enumerate((("SrcA", g("rwc_a")), ("SrcB", g("rwc_b")), ("Dst", g("rwc_d")))) if v]
      gist = "advance counters " + (", ".join(incs) or "none")
  elif name in ("SETADCXX", "SETADCXY", "SETADCZW", "SETADC"):
    who = bits_names(g("CntSetMask"), ("unpacker 0", "unpacker 1", "packers"))
    label["CntSetMask"] = who
    if name == "SETADCXX": gist = f"{who}: X counters ch0 = {g('x_start')}, ch1 = {g('x_end2')} (last element)"
    elif name == "SETADC": gist = f"{who}: channel {g('ChannelIndex')} {'XYZW'[g('DimensionIndex')]} = {g('Value')}"
    else:
      dims = ("X", "Y") if name == "SETADCXY" else ("Z", "W")
      m = g("BitMask")
      sets = [f"ch{c}.{dm}={g(f'Ch{c}_{dm}')}" for i, (c, dm) in enumerate(((0, dims[0]), (0, dims[1]), (1, dims[0]), (1, dims[1]))) if m >> i & 1]
      gist = f"{who}: " + (", ".join(sets) or "nothing")
  elif name == "ZEROACC":
    mode = g("clear_mode") & 3
    gist = "clear Dst: " + ("one row", "16-row block", "half of Dst", "all of Dst")[mode] + (f" {g('where')}" if mode < 2 else "") + (" (32-bit)" if g("clear_mode") & 4 or g("use_32_bit_mode") else "")
  elif name in ("ELWMUL", "ELWADD", "ELWSUB", "MVMUL", "DOTPV", "GMPOOL", "GAPOOL", "MPOOL3S1", "APOOL3S1", "MFCONV3S1", "CONV3S1"):
    opx = {"ELWMUL": "SrcA × SrcB", "ELWADD": "SrcA + SrcB", "ELWSUB": "SrcA - SrcB", "MVMUL": "SrcB @ SrcA (8×16 @ 16×16)"}.get(name, name)
    acc = "+=" if name == "MVMUL" or g("dest_accum_en") else "←"
    gist = f"Dst[+{g('dst')}] {acc} {opx}"
    if name != "MVMUL" and g("instr_mod19"): gist += ", SrcB broadcast " + ("", "column 0", "row", "scalar")[g("instr_mod19") & 3]
    if g("clear_dvalid"): gist += "; release " + ("SrcA", "SrcB", "SrcA+SrcB")[g("clear_dvalid") - 1]
  elif name == "MOVA2D": gist = f"Dst[+{g('dst')}] ← SrcA[+{g('src')}], " + ("8 rows" if g("instr_mod") == 2 else "1 row")
  elif name == "MOVD2A": gist = f"SrcA[+{g('src')}] ← Dst[+{g('dst')}]"
  elif name == "MOVB2D": gist = f"Dst[+{g('dst')}] ← SrcB[+{g('src')}]"
  elif name == "MOVD2B": gist = f"SrcB[+{g('src')}] ← Dst[+{g('dst')}]"
  elif name == "UNPACR":
    target = "unpacker 1 → SrcB" if g("Unpack_block_selection") else "unpacker 0 → SrcA (or Dst)"
    am = g("AddrMode")
    inc = [f"{n}+={am >> s & 3}" for n, s in (("ch0.Z", 0), ("ch0.Y", 2), ("ch1.Z", 4), ("ch1.Y", 6)) if am >> s & 3]
    gist = f"unpack with {target}" + (", publish to math" if g("SetDatValid") else "") + (", zeros" if g("ZeroWrite2") else "") + (f"; then {', '.join(inc)}" if inc else "")
  elif name == "UNPACR_NOP":
    u = "SrcB" if g("Unpacker_Select") else "SrcA"
    gist = f"publish {u} bank to math (set dvalid)" if g("Set_Dvalid") and g("Unpack_Pop") else f"unpacker {g('Unpacker_Select')} control / source clear"
  elif name == "PACR":
    gist = "pack Dst → L1" + (" (zeros)" if g("ZeroWrite") else "") + f", packers mask {hx(g('ReadIntfSel'))}, ADC mod {g('AddrMode')}" + (", flush only" if g("Flush") else "") + (", last: finalize output" if g("Last") else "")
  elif name in ("NOP", "DMANOP"): gist = ""
  if "addr_mode" in vals and name not in ("UNPACR", "PACR") and (am := addr_mod_text(tcfg or {}, vals["addr_mode"] & 7)) is not None:
    label["addr_mode"] = f"ADDR_MOD_{vals['addr_mode'] & 7}: {am}"
  for a in args: a[2] = label.get(a[0], "")
  d["gist"] = gist
  return d

def tt_text(d): return ", ".join(f"{n}={v}" for n, v, _ in d["args"])

# ---------------------------------------------------------------------------------------------------------------------
# RV32 decode

def rv_decode(w, pc):
  op, rd, f3, a, b, f7 = w & 127, (w >> 7) & 31, (w >> 12) & 7, (w >> 15) & 31, (w >> 20) & 31, w >> 25
  imm = signed(w >> 20, 12)
  reg = lambda n: f"x{n}"
  def row(name, operands, **kw): return dict(kind="rv", op=name, operands=operands, **kw)
  if op in (0x37, 0x17): return row("lui" if op == 0x37 else "auipc", f"{reg(rd)}, {hx(w >> 12)}", rd=rd, imm=w & 0xFFFFF000)
  if op == 0x33:
    name = {(0, 0): "add", (0, 32): "sub", (0, 1): "mul", (5, 1): "divu", (7, 1): "remu", (3, 0): "sltu", (2, 0): "slt", (4, 5): "min", (7, 0): "and",
            (6, 0): "or", (4, 0): "xor", (1, 0): "sll", (5, 0): "srl", (5, 32): "sra", (4, 1): "div", (6, 1): "rem", (1, 1): "mulh", (3, 1): "mulhu"}.get((f3, f7))
    if name: return row(name, f"{reg(rd)}, {reg(a)}, {reg(b)}", rd=rd, rs1=a, rs2=b)
  if op == 0x13:
    name = {0: "addi", 2: "slti", 3: "sltiu", 7: "andi", 6: "ori", 4: "xori"}.get(f3)
    if f3 == 1 and f7 == 0: name, imm = "slli", b
    if f3 == 5 and f7 in (0, 32): name, imm = ("srai" if f7 else "srli"), b
    if name:
      if name == "addi" and a == 0: return row("li", f"{reg(rd)}, {imm}", rd=rd, rs1=a, imm=imm, base="addi")
      if name == "addi" and imm == 0: return row("mv", f"{reg(rd)}, {reg(a)}", rd=rd, rs1=a, imm=imm, base="addi")
      return row(name, f"{reg(rd)}, {reg(a)}, {imm}", rd=rd, rs1=a, imm=imm)
  if op == 3 and f3 in (0, 1, 2, 4, 5):
    return row({0: "lb", 1: "lh", 2: "lw", 4: "lbu", 5: "lhu"}[f3], f"{reg(rd)}, {imm}({reg(a)})", rd=rd, rs1=a, imm=imm, mem="r", width={0: 1, 1: 2, 2: 4, 4: 1, 5: 2}[f3])
  if op == 0x23 and f3 in (0, 1, 2):
    imm = signed(((w >> 25) << 5) | ((w >> 7) & 31), 12)
    return row({0: "sb", 1: "sh", 2: "sw"}[f3], f"{reg(b)}, {imm}({reg(a)})", rs1=a, rs2=b, imm=imm, mem="w", width=1 << f3)
  if op == 0x63 and f3 in (0, 1, 4, 5, 6, 7):
    imm = signed(((w >> 31) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 63) << 5) | (((w >> 8) & 15) << 1), 13)
    return row({0: "beq", 1: "bne", 4: "blt", 5: "bge", 6: "bltu", 7: "bgeu"}[f3], f"{reg(a)}, {reg(b)}, ", rs1=a, rs2=b, target=(pc + imm) & MASK, branch=True)
  if op == 0x6F:
    imm = signed(((w >> 31) << 20) | (((w >> 12) & 255) << 12) | (((w >> 20) & 1) << 11) | (((w >> 21) & 1023) << 1), 21)
    if rd == 0: return row("j", "", rd=0, target=(pc + imm) & MASK, jump=True)
    return row("call" if rd == 1 else "jal", "" if rd == 1 else f"{reg(rd)}, ", rd=rd, target=(pc + imm) & MASK, jump=True, call=True)
  if op == 0x67 and f3 == 0:
    if rd == 0 and a == 1 and imm == 0: return row("ret", "", rd=0, rs1=1, imm=0, jump=True, ret=True)
    return row("jalr", f"{reg(rd)}, {imm}({reg(a)})", rd=rd, rs1=a, imm=imm, jump=True, indirect=True)
  if op == 0x73 and f3 in (1, 2, 3): return row({1: "csrrw", 2: "csrrs", 3: "csrrc"}[f3], f"{reg(rd)}, {hx(w >> 20)}, {reg(a)}", rd=rd, rs1=a, csr=w >> 20)
  if op == 0x0F and f3 == 0: return row("fence", "")
  return dict(kind="rv", op=".word", operands=hex8(w), unknown=True)

# ---------------------------------------------------------------------------------------------------------------------
# Abstract values: int (known constant), str (symbolic expression), None (unknown)

def is_addr(v): return isinstance(v, int) and (0xE000 <= v < L1_SIZE or v >= 0xFFB00000)
def is_off(v): return isinstance(v, tuple)

def join(x, y):
  """Meet of two abstract values. Two nearby addresses become ("off", base): base plus a varying offset."""
  if x == y: return x
  if is_addr(x) and is_addr(y) and abs(x - y) < 0x40000: return ("off", min(x, y))
  if is_off(x) and is_addr(y) and abs(y - x[1]) < 0x40000: return x
  if is_off(y) and is_addr(x) and abs(x - y[1]) < 0x40000: return y
  return None

def show(v):
  if isinstance(v, int): return hx(v)
  if is_off(v): return f"{hx(v[1])} + …"
  return v

def sfmt(v):
  if is_off(v): return f"({hx(v[1])} + …)"
  if isinstance(v, int): return str(v) if v < 1024 else hx(v)
  return f"({v})" if " " in v and not (v.startswith("(") and v.endswith(")") and v.count("(") == 1) else v

def sexpr(a, op, b):
  if is_off(a) or is_off(b): return None
  if op == ">>" and isinstance(a, str) and isinstance(b, int) and (m := re.fullmatch(r"(.+) << (\d+)", a)) and int(m.group(2)) == b:
    return sexpr(m.group(1), "&", (1 << (32 - b)) - 1)  # zero-extension idiom
  text = f"{sfmt(a)} {op} {sfmt(b)}"
  return text if len(text) <= 56 else None

def transfer(row, state, pc):
  if row["kind"] != "rv": return state
  s = list(state)
  op = row.get("base", row["op"]); a = s[row.get("rs1", 0)]; b = s[row.get("rs2", 0)]; v = row.get("imm")
  r = None
  if row.get("unknown"): return [0] + [None] * 31
  if op == "lui": r = v
  elif op == "auipc": r = pc + v
  elif op in ("call", "jal", "jalr"): r = pc + 4
  elif row.get("mem") == "r": r = row.get("loaded")
  elif is_off(a) and op in ("addi", "add", "sub"): r = a
  elif is_off(b) and op == "add": r = b
  elif op == "add" and is_addr(a) and not isinstance(b, int): r = ("off", a)
  elif op == "add" and is_addr(b) and not isinstance(a, int): r = ("off", b)
  elif isinstance(a, int):
    if op == "addi": r = a + v
    elif op == "sltiu": r = int(a < (v & MASK))
    elif op == "slti": r = int(signed(a, 32) < v)
    elif op == "andi": r = a & v
    elif op == "ori": r = a | v
    elif op == "xori": r = a ^ v
    elif op == "slli": r = a << v
    elif op == "srli": r = a >> v
    elif op == "srai": r = signed(a, 32) >> v
    elif isinstance(b, int):
      if op == "add": r = a + b
      elif op == "sub": r = a - b
      elif op == "mul": r = a * b
      elif op == "divu": r = a // b if b else MASK
      elif op == "remu": r = a % b if b else a
      elif op == "min": r = min(signed(a, 32), signed(b, 32))
      elif op == "sltu": r = int(a < b)
      elif op == "and": r = a & b
      elif op == "or": r = a | b
      elif op == "xor": r = a ^ b
      elif op == "sll": r = a << (b & 31)
      elif op == "srl": r = a >> (b & 31)
    elif isinstance(b, str) and op in ("add", "mul", "and", "or"):
      r = b if (op == "add" and a == 0) else sexpr(b, {"add": "+", "mul": "*", "and": "&", "or": "|"}[op], a)
    elif isinstance(b, str) and op == "sub": r = sexpr(a, "-", b)
  elif isinstance(a, str):
    if op == "addi": r = a if v == 0 else sexpr(a, "+" if v > 0 else "-", abs(v))
    elif op == "andi": r = sexpr(a, "&", v) if v >= 0 else sexpr(a, "&", f"~{hx(~v)}")
    elif op == "ori": r = sexpr(a, "|", v & MASK)
    elif op == "slli": r = a if v == 0 else sexpr(a, "<<", v)
    elif op == "srli": r = a if v == 0 else sexpr(a, ">>", v)
    elif b is not None and op in ("add", "sub", "mul", "divu", "remu", "and", "or", "sll", "srl"):
      if op in ("add", "sub") and b == 0: r = a
      else: r = sexpr(a, {"add": "+", "sub": "-", "mul": "*", "divu": "/", "remu": "%", "and": "&", "or": "|", "sll": "<<", "srl": ">>"}[op], b)
  if row.get("rd"): s[row["rd"]] = (r & MASK) if isinstance(r, int) else r
  s[0] = 0
  return s

# ---------------------------------------------------------------------------------------------------------------------
# Address naming

def parse_abi(path):
  """#defines of fw/abi.h (hex literals and simple sums/differences of earlier ones)."""
  out = {}
  try: text = Path(path).read_text()
  except OSError: return out
  for name, expr in re.findall(r"^#define (\w+)\s+(.+?)\s*(?:/\*.*)?$", text, re.M):
    expr = re.sub(r"\b[A-Z_][A-Z0-9_]*\b", lambda m: str(out.get(m.group(0), "__")), expr)
    if re.fullmatch(r"[\s0-9a-fA-FxX()+\-*]+", expr):
      try: out[name] = int(eval(expr))
      except Exception: pass
  return out

class Context:
  """Everything needed to name addresses in one kernel: its role, its program's params and the model's L1 layout."""
  def __init__(self, role, manifest=None, program=None, abi=None):
    self.role, self.manifest, self.program, self.abi = role, manifest or {}, program, abi or {}
    self.params = {}      # L1 address -> (name, 'uniform' | 'per-core')
    self.tables = []      # (lo, hi, program name)
    self.locals = {}      # local-RAM address -> name, filled in by CB inference
    m = self.manifest
    for pname, p in m.get("programs", {}).items():
      base = m["static_base"] + 0x40 * p["k"]
      self.tables.append((base, base + 0x40, pname))
      if pname == program:
        for i, n in enumerate(p["uniform"]): self.params[m["l1_param_base"] + 4 * i] = (n, "uniform")
        for j, n in enumerate(p["static"]): self.params[base + 4 * j] = (n, "per-core")

  def l1(self, addr):
    """(name, description) of an L1 address."""
    a, m = self.abi, self.manifest
    if addr in self.params:
      n, kind = self.params[addr]
      return f"param {n}", f"{kind} launch parameter" + (", sent with every EXEC" if kind == "uniform" else ", from this core's resident table")
    for lo, hi, pname in self.tables:
      if lo <= addr < hi: return f"{pname} per-core table + {hx(addr - lo)}", "resident per-core parameter table of another program"
    for p in m.get("persistent", []):
      if p["addr"] <= addr < p["addr"] + p["size"]:
        return f"{p['name']} + {hx(addr - p['addr'])}", f"persistent L1 region on core {tuple(p['core'])}, survives across launches"
    if a:
      fixed = (("GO_SIGNAL", 4, "launch word: byte 0 = 0x80 to launch, cleared when every RISC returns"),
               ("SUBORDINATE_SYNC", 4, "per-RISC run state bytes for ncrisc, trisc0-2"), ("LAUNCH", 0x40, "active-role bitmask of the launch"))
      for name, size, desc in fixed:
        if name in a and a[name] <= addr < a[name] + size: return name + (f" + {addr - a[name]}" if addr != a[name] else ""), desc
      for r in ("BRISC", "NCRISC", "TRISC0", "TRISC1", "TRISC2"):
        lo = a.get(f"FW_{r}")
        if lo is not None and lo <= addr < lo + a.get(f"FW_{r}_SIZE", 0): return f"FW_{r} + {hx(addr - lo)}", "resident firmware image"
      if "L1_PARAM_BASE" in a and a["L1_PARAM_BASE"] <= addr < a["L1_PARAM_BASE"] + a.get("PARAM_SIZE", 0x40):
        return f"L1_PARAM_BASE + {hx(addr - a['L1_PARAM_BASE'])}", "uniform launch parameters (unused slot in this program)"
      code = [(a.get(f"CODE_{r}"), r) for r in ("BRISC", "NCRISC", "TRISC0", "TRISC1", "TRISC2")] + [(a.get("CODE_END"), None)]
      if all(c[0] is not None for c in code):
        stride = a.get("SLOT_STRIDE", 0)
        for slot in (0, 1):
          for (lo, r), (hi, _) in zip(code, code[1:]):
            if lo + slot * stride <= addr < hi + slot * stride: return f"code slot {slot} {r} + {hx(addr - lo - slot * stride)}", "kernel image, execution slot"
    if m and addr >= m.get("l1_data_base", L1_SIZE) and addr < L1_SIZE: return f"L1 data {hx(addr)}", "kernel data area: circular buffers and scratch tiles"
    if addr < L1_SIZE: return f"L1 {hx(addr)}", ""
    return None

  def describe(self, addr):
    """dict(name, region, desc, type) for any 32-bit address, or None."""
    if addr < L1_SIZE:
      name, desc = self.l1(addr)
      return dict(name=name, region="L1", desc=desc, type="param" if addr in self.params else "l1")
    if 0xFFB00000 <= addr < 0xFFB02000:
      name = self.locals.get(addr)
      if name: return dict(name=name, region="local RAM", desc="kernel variable in this RISC's private memory", type="local")
      return dict(name=f"local[{hx(addr - 0xFFB00000)}]", region="local RAM", desc="this RISC's private memory (stack and kernel variables), not L1", type="local")
    if 0xFFB20000 <= addr < 0xFFB40000:
      niu, off = (addr - 0xFFB20000) >> 16, addr & 0xFFFF
      return self._noc(niu, off)
    if 0xFFB40000 <= addr < 0xFFB80000:
      stream, reg = (addr - 0xFFB40000) >> 12, (addr & 0xFFF) >> 2
      if 8 <= stream < 40 and reg in (8, 10):
        which = "tiles_acked" if reg == 8 else "tiles_received"
        return dict(name=f"CB{stream - 8}.{which}", region="NoC overlay", type="stream", cb=stream - 8,
                    desc=f"circular buffer {stream - 8} {'consumer' if reg == 8 else 'producer'} counter (overlay stream {stream}, reg {reg}); "
                         "16-bit wrapping tile count shared by all RISCs of the tile")
      return dict(name=f"stream{stream}.reg{reg}", region="NoC overlay", desc="overlay stream register", type="mmio")
    if 0xFFB80000 <= addr <= 0xFFB80020:
      i = (addr - 0xFFB80000) >> 2
      return dict(name=f"MOP_CFG[{i}]", region="Tensix", desc=f"MOP template word {i}: {MOP_SLOTS[i]} (template 1) / {MOP_SLOTS_T0[i]} (template 0)",
                  type="mop.count" if i < 2 else "mop.insn", index=i)
    if 0xFFE00000 <= addr < 0xFFE00100:
      i = (addr - 0xFFE00000) >> 2
      alias = GPR_NAMES.get(self.role, {}).get(i)
      return dict(name=f"GPR[{i}]" + (f" {alias}" if alias else ""), region="Tensix", desc="Tensix GPR of this thread (operand for WRCFG / DMA-register instructions)", type="gpr")
    for base, n in ((0xFFE40000, 0), (0xFFE50000, 1), (0xFFE60000, 2)):
      if base <= addr < base + 0x1000:
        return dict(name="INSTRN_BUF" + (str(n) if n else ""), region="Tensix", desc="a store here pushes one instruction to " + ("this RISC's Tensix thread" if not n else f"Tensix thread {n}"), type="instr")
    if 0xFFE80000 <= addr < 0xFFE81000:
      off = addr - 0xFFE80000
      if off == 4: return dict(name="PC_BUF.tensix_sync", region="Tensix", desc="reading blocks this RISC until its Tensix thread has drained every queued instruction", type="sync")
      if off == 8: return dict(name="PC_BUF.mop_sync", region="Tensix", desc="reading blocks this RISC until the MOP expander is idle", type="sync")
      if 0x20 <= off < 0x40:
        i = (off - 0x20) >> 2
        return dict(name=f"semaphore[{i}] {SEM[i]}", region="Tensix", desc="Tensix semaphore value as seen from RISC-V", type="sem")
      return dict(name=f"PC_BUF + {hx(off)}", region="Tensix", desc="", type="mmio")
    if 0xFFEF0000 <= addr < 0xFFEF0DB0:
      off = addr - 0xFFEF0000
      if off < 0xA80:
        bank, index = off // 0x380, (off % 0x380) // 4
        return dict(name=cfg_name("cfg", index), region="Tensix config", type="cfg", group="cfg", index=index,
                    bank=("state 0", "state 1", "state 2")[bank], desc=f"backend configuration word {index}, {('state 0', 'state 1', 'state 2')[bank]}")
      index, thread = ((off - 0xA80) % 0x110) // 4, (off - 0xA80) // 0x110
      return dict(name=cfg_name("thread_cfg", index), region="Tensix config", type="cfg", group="thread_cfg", index=index,
                  bank=f"thread {thread}", desc=f"per-thread configuration word {index}, thread {thread}")
    for region in TILE["address_map"]:
      base, limit = int(region["base"], 0), int(region["limit"], 0)
      if base <= addr <= limit and base >= 0xFF000000:
        for reg in TILE_MODULES.get(region["name"], []):
          if int(reg["offset"], 0) == addr - base:
            return dict(name=f"{region['name']}.{reg['name']}", region=region["name"], desc=DEBUG_NOTES.get(reg["name"], ""), type="mmio")
        return dict(name=f"{region['name']} + {hx(addr - base)}", region=region["name"], desc="", type="mmio")
    return None

  def _noc(self, niu, off):
    region = f"NoC {niu} NIU"
    if off < 0x2000 and off % 0x800 < 0x70:
      buf, r = off // 0x800, off % 0x800
      names = {0x00: ("TARG_ADDR_LO", "noc.addr", "target address, low 32 bits. Writes: local source. Reads/atomics: remote address"),
               0x04: ("TARG_ADDR_MID", "noc.mid", "target address bits 35:32"),
               0x08: ("TARG_COORD", "noc.coord", "target NoC coordinate x | y << 6. Writes: this tile. Reads/atomics: remote endpoint"),
               0x0C: ("RET_ADDR_LO", "noc.addr", "return address, low 32 bits. Writes: remote destination. Reads: local destination"),
               0x10: ("RET_ADDR_MID", "noc.mid", "return address bits 35:32"),
               0x14: ("RET_COORD", "noc.coord", "return NoC coordinate. Writes: remote endpoint (multicast: rectangle start/end). Reads: this tile"),
               0x18: ("PACKET_TAG", "noc.tag", "transaction id << 10"), 0x1C: ("CTRL", "noc.ctrl", "command flags"),
               0x20: ("AT_LEN_BE", "noc.len", "byte length of the copy (atomics: operation encoding)"),
               0x24: ("AT_LEN_BE_1", "noc.raw", "upper byte-enable word"), 0x28: ("AT_DATA", "noc.raw", "inline / atomic operand data"),
               0x2C: ("BRCST_EXCLUDE", "noc.raw", "multicast exclusion rows/columns"),
               0x40: ("CMD_CTRL", "noc.cmd", "write 1 to send the staged command; reads nonzero while the command buffer is busy"),
               0x44: ("NODE_ID", "noc.raw", "this node's id"), 0x60: ("CLEAR_OUTSTANDING_REQ_CNT", "noc.raw", ""),
               0x64: ("CMD_BUF_AVAIL", "noc.raw", ""), 0x68: ("CMD_BUF_OVFL", "noc.raw", "")}
      if r in names:
        n, t, desc = names[r]
        return dict(name=f"NOC{niu}.cmd{buf}.{n}", region=region, desc=f"command buffer {buf}: {desc}", type=t, niu=niu, buf=buf)
    if 0x240 <= off < 0x280:
      return dict(name=f"NOC{niu}.REQS_OUTSTANDING[tid {(off - 0x240) >> 2}]", region=region, type="noc.status", niu=niu, tid=(off - 0x240) >> 2, status="outstanding",
                  desc="reads and acked writes of this transaction id still in flight; 0 = every response has arrived")
    if 0x280 <= off < 0x2C0:
      return dict(name=f"NOC{niu}.WRITE_REQS_OUTGOING[tid {(off - 0x280) >> 2}]", region=region, type="noc.status", niu=niu, tid=(off - 0x280) >> 2, status="outgoing",
                  desc="writes of this transaction id not yet sent out of L1; 0 = the source buffer can be reused")
    for reg in TILE_MODULES["noc_regs"]:
      if int(reg["offset"], 0) == off and "array_size" not in reg:
        extra = "this tile's logical NoC coordinate, x | y << 6" if reg["name"] == "noc_id_logical" else ""
        return dict(name=f"NOC{niu}.{reg['name'].removeprefix('noc_').upper()}", region=region, desc=extra, type="noc.id" if extra else "mmio", niu=niu)
    return dict(name=f"NOC{niu} + {hx(off)}", region=region, desc="", type="mmio", niu=niu)

# ---------------------------------------------------------------------------------------------------------------------
# Disassembly

def decode_words(image):
  rows = []
  for pc in range(0, len(image) - len(image) % 4, 4):
    w = int.from_bytes(image[pc:pc + 4], "little")
    if w & 3 != 3:
      row = dict(kind="tt", tword=((w >> 2) | (w << 30)) & MASK)
    else: row = rv_decode(w, pc)
    row.update(pc=pc, word=w)
    rows.append(row)
  return rows

def function_bodies(rows, entries):
  n, bodies = len(rows), {}
  for e in entries:
    seen, stack = set(), [e // 4]
    while stack:
      i = stack.pop()
      if i in seen or not 0 <= i < n: continue
      seen.add(i); r = rows[i]
      if r.get("ret") or r.get("indirect"): continue
      if r.get("call"): stack.append(i + 1); continue
      if "target" in r: stack.append(r["target"] // 4)
      if not r.get("jump"): stack.append(i + 1)
    bodies[e] = seen
  return bodies

def analyse(rows, ctx):
  """Forward constant/symbol propagation over the CFG. Returns the state before each row (None = unreachable)."""
  n = len(rows)
  entries = sorted({r["target"] for r in rows if r.get("call") and r["target"] < n * 4})
  bodies = function_bodies(rows, [0] + entries)
  clob = {e: {rows[i]["rd"] for i in bodies[e] if rows[i].get("rd")} | {1} for e in entries}
  calls = {e: {rows[i]["target"] for i in bodies[e] if rows[i].get("call")} & set(entries) for e in entries}
  changed = True
  while changed:
    changed = False
    for e in entries:
      for c in calls[e]:
        if not clob[c] <= clob[e]: clob[e] |= clob[c]; changed = True
  init = [0, None, "sp"] + [None] * 29
  states = [None] * n
  if not n: return states, entries, bodies, clob
  states[0] = init
  queue, pending = deque([0]), {0}
  def push(j, edge):
    if not 0 <= j < n: return
    old = states[j]
    merged = edge if old is None else [join(x, y) for x, y in zip(old, edge)]
    if old != merged:
      states[j] = merged
      if j not in pending: queue.append(j); pending.add(j)
  while queue:
    i = queue.popleft(); pending.discard(i)
    row, st = rows[i], states[i]
    if row["kind"] == "rv" and row.get("mem") == "r":
      base = st[row["rs1"]]
      row["loaded"] = None
      if isinstance(base, int) and row["width"] == 4:
        addr = (base + row["imm"]) & MASK
        if addr in ctx.params: row["loaded"] = ctx.params[addr][0]
        elif 0xFFB00000 <= addr < 0xFFB02000: row["loaded"] = f"local[{hx(addr - 0xFFB00000)}]"
    out = transfer(row, st, row["pc"])
    if row.get("ret") or row.get("indirect"): continue
    if row.get("call"):
      push(row["target"] // 4, out)
      after = list(out)
      for r in clob.get(row["target"], range(1, 32)): after[r] = None
      push(i + 1, after)
      continue
    if "target" in row: push(row["target"] // 4, out)
    if not row.get("jump"): push(i + 1, out)
  return states, entries, bodies, clob

def name_function(rows, body, ctx, states):
  """A readable title for a subroutine, from what it touches."""
  ctrl = tag = length = niu = None
  status, params, table, copies = [], [], False, 0
  for i in sorted(body):
    r, st = rows[i], states[i]
    if st is None: continue
    if r.get("op") == "auipc": table = True
    if not r.get("mem"): continue
    base = st[r["rs1"]]
    if not isinstance(base, int):
      copies += 1; continue
    addr = (base + r["imm"]) & MASK
    d = ctx.describe(addr) or {}
    t = d.get("type", "")
    if t == "param" and r["mem"] == "r": params.append(ctx.params[addr][0])
    if t.startswith("noc"): niu = d.get("niu", niu)
    if t == "noc.status" and r["mem"] == "r": status.append((d["status"], d["tid"]))
    if r["mem"] == "w":
      v = st[r["rs2"]]
      if t == "noc.ctrl" and isinstance(v, int): ctrl = v
      if t == "noc.tag" and isinstance(v, int): tag = v >> 10
      if t == "noc.len": length = v
  if ctrl is not None:
    kind = "atomic increment" if ctrl & 1 else ("multicast write" if ctrl >> 5 & 1 else "write") if ctrl & 2 else "read"
    title = f"NoC {niu} {kind}"
    if tag is not None: title += f", tid {tag}"
    if isinstance(length, int) and not ctrl & 1: title += f", {length} B"
    elif isinstance(length, str) and not ctrl & 1: title += f", {length} B"
    return title, ("noc_" + kind.split()[0])
  if params and table: return f"DRAM tile address of {params[0]}", "dram_tile"
  if status and len(body) <= 10:
    what, tid = status[0]
    return (f"wait until NoC {niu} tid {tid} " + ("writes have left L1" if what == "outgoing" else "responses have arrived")), "noc_wait"
  if copies >= 2 and len(body) <= 16: return "copy words in L1", "copy"
  return None, "sub"

def infer_cbs(rows, states, ctx):
  """Circular-buffer state lives in local RAM as {pointer, count}. Tie each pair to its CB index and L1 base."""
  first_store, cb_of = {}, {}
  recent = deque(maxlen=10)
  for r, st in zip(rows, states):
    if st is None or not r.get("mem"): continue
    base = st[r["rs1"]]
    if not isinstance(base, int): continue
    addr = (base + r["imm"]) & MASK
    if 0xFFB00000 <= addr < 0xFFB02000:
      if r["mem"] == "w" and addr not in first_store: first_store[addr] = st[r["rs2"]]
      recent.append(addr)
    elif 0xFFB48000 <= addr < 0xFFB68000 and (addr & 0xFFF) in (0x20, 0x28):
      cb, producer = ((addr - 0xFFB48000) >> 12), (addr & 0xFFF) == 0x28
      # push_back writes state+4 then tiles_received; pop_front writes state+4 then tiles_acked;
      # reserve_back reads state+4 then tiles_acked; wait_front reads state+4 then tiles_received
      role = producer if r["mem"] == "w" else not producer
      for a in reversed(recent):
        if first_store.get(a) == 0 and is_addr(first_store.get(a - 4)) and a - 4 not in cb_of and a not in cb_of:
          cb_of.setdefault(a - 4, (cb, role)); break
      recent.clear()
  cbs = {}
  for state, (cb, producer) in cb_of.items():
    side = "wr" if producer else "rd"
    ctx.locals[state] = f"cb{cb}.{side}_ptr"
    ctx.locals[state + 4] = f"cb{cb}.tiles_{'pushed' if producer else 'popped'}"
    cbs.setdefault(cb, {})["base"] = first_store[state]
    cbs[cb].setdefault("sides", []).append("producer" if producer else "consumer")
  for addr, v in first_store.items():  # pointer/count pairs whose CB index was not identified
    if addr not in ctx.locals and is_addr(v) and v < L1_SIZE and first_store.get(addr + 4) == 0:
      ctx.locals[addr] = f"cb@{hx(v)}.ptr"; ctx.locals[addr + 4] = f"cb@{hx(v)}.count"
  return cbs

def value_note(d, v, width, ctx, tcfg):
  """Explain a value being stored to the address described by d. Returns (text, extra-detail)."""
  t = d["type"]
  if isinstance(v, str): return v, {}
  if is_off(v): return f"{ctx.l1(v[1])[0] if v[1] < L1_SIZE else hx(v[1])} + …", {}
  if v is None: return "runtime value", {}
  if t == "noc.coord":
    if v >> 12: return f"{hx(v)} = rectangle {coord_name(v & 0xFFF)} .. {coord_name(v >> 12)}", {}
    return f"{hx(v)} = {coord_name(v)}", {}
  if t == "noc.tag": return f"{hx(v)} = tid {v >> 10}", {}
  if t == "noc.ctrl": return f"{hx(v)} = {noc_ctrl(v)}", {}
  if t == "noc.len": return (f"{hx(v)} = increment wrapping at bit 31, if the command is atomic" if v == 0x107C else f"{v} bytes"), {}
  if t == "noc.cmd": return "1 = send the staged command" if v == 1 else hx(v), {}
  if t == "noc.addr": return (hx(v) + (f" = {ctx.l1(v)[0]}" if v < L1_SIZE and v >= 0x10 else "")), {}
  if t in ("instr", "mop.insn") and width == 4:
    e = tt_decode(v, tcfg)
    return (f"{e['op']}: {e['gist']}" if e["gist"] else f"{e['op']} {tt_text(e)}".strip()), dict(embedded=e)
  if t == "mop.count": return str(v), {}
  if t == "stream": return f"{v} tiles", {}
  if t == "local":
    return (hx(v) + (f" = {ctx.l1(v)[0]}" if 0x800 <= v < L1_SIZE else "")), {}
  if t == "gpr": return f"{hx(v)} ({v})", {}
  return hx(v) if v > 9 else str(v), {}

def disassemble(image, ctx):
  rows = decode_words(image)
  states, entries, bodies, clob = analyse(rows, ctx)
  cbs = infer_cbs(rows, states, ctx)
  n = len(rows)
  rename = lambda s: re.sub(r"local\[0x([0-9a-f]+)\]", lambda m: ctx.locals.get(0xFFB00000 + int(m.group(1), 16), m.group(0)), s) if isinstance(s, str) else s

  # labels: functions, branch targets, data tables
  labels = {}
  owner = {}
  for e in [0] + entries:
    for i in bodies[e]: owner.setdefault(i, e)
  funcs = {}
  for e in entries:
    title, kind = name_function(rows, bodies[e], ctx, states)
    live, defined = [], set()
    for i in sorted(bodies[e]):
      r = rows[i]
      if r["kind"] != "rv": continue
      for k in ("rs1", "rs2"):
        if k in r and r[k] not in defined and r[k] not in (0, 1, 2) and r[k] not in live and not (r.get("op") in ("li", "lui", "auipc")): live.append(r[k])
      if r.get("rd"): defined.add(r["rd"])
    funcs[e] = dict(pc=e, name=f"sub_{e:x}", title=title, kind=kind, args=live, size=len(bodies[e]), callers=[])
    labels[e] = funcs[e]["name"]
  for r in rows:
    if "target" in r and not r.get("call") and r["target"] < n * 4 and states[r["pc"] // 4] is not None: labels.setdefault(r["target"], f"loc_{r['target']:x}")

  # data: unreachable words. Tables are found through the auipc that addresses them.
  tables = {}
  for i, r in enumerate(rows):
    st = states[i]
    if st is None or r.get("op") != "addi" or i == 0: continue
    v = transfer(r, st, r["pc"])[r["rd"]]
    if rows[i - 1].get("op") == "auipc" and isinstance(v, int) and v % 4 == 0 and v // 4 < n and states[v // 4] is None:
      tables[v] = r["pc"]
      labels.setdefault(v, f"tbl_{v:x}")
  out = []
  tcfg, mopcfg, replay = {}, {}, {}
  recording = None  # [slot, remaining, execute]
  pending_loadi = {}
  table_at = None
  for i, r in enumerate(rows):
    st = states[i]
    pc = r["pc"]
    o = dict(pc=pc, word=r["word"], kind=r["kind"], ann=[], fn=owner.get(i, -1))
    if pc in labels: o["label"] = labels[pc]
    if pc in funcs: o["func"] = funcs[pc]
    if st is None:  # data
      if pc in tables: table_at = (pc, 0)
      lo, hi = r["word"] & 0xFFFF, r["word"] >> 16
      o.update(kind="data", op=".half", operands=f"{hx(lo)}, {hx(hi)}")
      if table_at:
        idx = (pc - table_at[0]) // 2
        o["ann"].append(["note", f"[{idx}] {coord_name(lo)}   [{idx + 1}] {coord_name(hi)}"])
        o["detail"] = dict(table=dict(start=table_at[0], ref=tables.get(table_at[0]), entries=[[idx, lo, coord_name(lo)], [idx + 1, hi, coord_name(hi)]]))
      out.append(o); recording = None
      continue
    table_at = None
    if r["kind"] == "tt":
      d = tt_decode(r["tword"], tcfg)
      o.update(op=d["op"], args=d["args"], opcode=d["opcode"], tword=d["tword"])
      if d["gist"]: o["ann"].append(["gist", d["gist"]])
      if "config" in d: o["config"] = d["config"]; o["sym"] = f"{d['config']['group']}:{d['config']['index']}"
      vals = {a[0]: a[1] for a in d["args"]}
      name = d["op"]
      if name == "SETC16": tcfg[vals["setc16_reg"]] = vals["setc16_value"]
      if recording and name not in ("MOP", "MOP_CFG"):
        slot, remaining, execute = recording
        replay[slot % 32] = r["tword"]
        o["ann"].append(["note", f"→ replay[{slot % 32}]" + ("" if execute else ", not executed here")])
        o["rec"] = slot % 32
        recording = [slot + 1, remaining - 1, execute] if remaining > 1 else None
      elif name == "REPLAY":
        if vals["load_mode"]: recording = [vals["start_idx"], vals["len"] or 64, bool(vals["execute_while_loading"])]
        else: o["expand"] = expand_replay(vals["start_idx"], vals["len"], replay, tcfg)
      elif name == "MOP":
        o["expand"] = expand_mop(r["tword"], mopcfg, replay, tcfg)
      elif name == "SFPLOADI":
        L, mode, imm = vals["lreg_ind"], vals["instr_mod0"], vals["imm16"]
        prev = pending_loadi.get(L)
        if mode in (8, 10) and prev and prev[0] in (8, 10) and prev[0] != mode and prev[2] == i - 1:
          full = (imm << 16 | prev[1]) if mode == 8 else (prev[1] << 16 | imm)
          o["ann"].append(["val", f"L{L} = {hex8(full)} = {fnum(f32(full))} as FP32, {full} as int"])
        pending_loadi[L] = (mode, imm, i)
      out.append(o)
      continue
    # RISC-V
    recording = None if r.get("branch") or r.get("jump") else recording
    o.update(op=r["op"], operands=r.get("operands", ""))
    after = transfer(r, st, pc)
    known = {}
    for key in ("rs1", "rs2"):
      if key in r and r[key] and st[r[key]] is not None: known[f"x{r[key]}"] = show(rename(st[r[key]]))
    if known: o["regs"] = known
    if "target" in r:
      o["target"] = r["target"]
      tl = labels.get(r["target"])
      o["tlabel"] = tl or hx(r["target"])
      if r.get("call") and r["target"] in funcs:
        f = funcs[r["target"]]
        f["callers"].append(pc)
        o["call"] = True
        if f["title"]: o["ann"].append(["call", f["title"]])
        args = [f"x{a} = {show(rename(st[a]))}" for a in f["args"] if st[a] is not None]
        if args: o["ann"].append(["val", ", ".join(args)])
      elif r.get("branch"):
        a, b = st[r["rs1"]], st[r["rs2"]]
        sym = {"beq": "==", "bne": "!=", "blt": "<", "bge": ">=", "bltu": "<", "bgeu": ">="}[r["op"]]
        lhs = sfmt(rename(a)) if a is not None and r["rs1"] else f"x{r['rs1']}" if r["rs1"] else "0"
        rhs = sfmt(rename(b)) if b is not None and r["rs2"] else f"x{r['rs2']}" if r["rs2"] else "0"
        if isinstance(a, int) and a > 1023: lhs += f" ({a})" if a < 100000 else ""
        if isinstance(b, int) and b > 1023: rhs += f" ({b})" if b < 100000 else ""
        if (a is not None and r["rs1"]) or (b is not None and r["rs2"]): o["ann"].append(["note", f"if {lhs} {sym} {rhs}"])
        o["back"] = r["target"] <= pc
      elif r.get("jump"): o["back"] = r["target"] <= pc
    if r.get("ret"): o["ret"] = True
    rd = r.get("rd")
    if rd and not r.get("jump") and not r.get("mem"):
      v = after[rd]
      if isinstance(v, int):
        d = ctx.describe(v) if v >= 0xFF000000 else None
        nxt = rows[i + 1] if i + 1 < n else {}
        partial = r["op"] in ("lui", "auipc") and nxt.get("op") in ("addi",) and nxt.get("rs1") == rd and nxt.get("rd") == rd
        if partial: o["dim"] = True
        elif not (r["op"] == "li" and v < 10):
          text = f"x{rd} = {hex8(v)}"
          if d: text += f"  {d['name']}"; o["sym"] = sym_key(v, d)
          elif v in ctx.params: text += f"  &{ctx.params[v][0]}"; o["sym"] = "param:" + ctx.params[v][0]
          elif v in tables: text += f"  table {labels[v]}"; o["target"] = v; o["tlabel"] = labels[v]
          elif 10 <= v < 100000 and r["op"] != "li": text += f"  ({v})"
          elif v >= 0x80000000 and v < 0xFF000000: text += f"  ({signed(v, 32)})"
          o["ann"].append(["val", text])
        o["value"] = v
      elif is_off(v): o["ann"].append(["val", f"x{rd} = {show(v)}"])
      elif isinstance(v, str) and r["op"] != "mv": o["ann"].append(["val", f"x{rd} = {rename(v)}"])
      elif isinstance(v, str): o["ann"].append(["val", f"= {rename(v)}"])
    if r.get("mem"):
      base = st[r["rs1"]]
      write = r["mem"] == "w"
      val = st[r["rs2"]] if write else None
      if write and r["width"] < 4 and isinstance(val, int): val &= (1 << 8 * r["width"]) - 1
      val = rename(val)
      if isinstance(base, int):
        addr = (base + r["imm"]) & MASK
        d = ctx.describe(addr) or dict(name=hex8(addr), region="?", desc="", type="mmio")
        o["addr"] = addr
        o["sym"] = sym_key(addr, d)
        o["mem"] = dict(rw=r["mem"], addr=addr, name=d["name"], region=d["region"], desc=d["desc"], width=r["width"])
        if write:
          text, extra = value_note(d, val, r["width"], ctx, tcfg)
          o["ann"].append(["store", d["name"], text])
          o["mem"]["value"] = show(val) if not isinstance(val, int) else val & MASK
          if "embedded" in extra:
            e = extra["embedded"]
            o["embedded"] = dict(op=e["op"], args=e["args"], opcode=e["opcode"], tword=e["tword"], gist=e["gist"])
            if d["type"] == "instr":
              ev = {a[0]: a[1] for a in e["args"]}
              if e["op"] == "MOP": o["expand"] = expand_mop(e["tword"], mopcfg, replay, tcfg)
              elif e["op"] == "REPLAY" and not ev["load_mode"]: o["expand"] = expand_replay(ev["start_idx"], ev["len"], replay, tcfg)
              elif e["op"] == "SETC16": tcfg[ev["setc16_reg"]] = ev["setc16_value"]
          if d["type"] in ("mop.insn", "mop.count"): mopcfg[d["index"]] = val if isinstance(val, int) else None
          if d["type"] == "cfg":
            shift = (addr % 4) * 8; mask = ((1 << 8 * r["width"]) - 1) << shift
            fields = cfg_fields(d["group"], d["index"], (val << shift) & mask if isinstance(val, int) else None, None if r["width"] == 4 else mask)
            o["config"] = dict(group=d["group"], index=d["index"], bank=d["bank"], fields=fields, title=cfg_title(d["group"], d["index"]))
            if isinstance(val, int):
              nz = [f"{f['name']} = {f['value']}" + (f" ({f['label']})" if f["label"] else "") for f in fields if f["value"]]
              if nz and len(fields) > 1 or (nz and fields[0]["label"]): o["ann"].append(["field", "; ".join(nz)])
        else:
          o["ann"].append(["load", d["name"]])
          if d["type"] == "sync": o["ann"].append(["note", "wait for Tensix to drain" if "tensix" in d["name"] else "wait for MOP expander"])
      elif is_off(base):
        d = ctx.describe(base[1]) or dict(name=hex8(base[1]), region="?", desc="", type="mmio")
        nm = f"{d['name']} + …"
        o["sym"] = sym_key(base[1], d)
        o["mem"] = dict(rw=r["mem"], addr=base[1], approx=True, name=nm, region=d["region"], desc=d["desc"], width=r["width"])
        if write: o["ann"].append(["store", nm, show(val) if val is not None else "runtime value"]); o["mem"]["value"] = show(val)
        else: o["ann"].append(["load", nm])
      else:
        expr = None
        if isinstance(base, str):
          b = rename(base)
          expr = b if r["imm"] == 0 else f"{sfmt(b)} {'+' if r['imm'] > 0 else '-'} {abs(r['imm'])}"
        o["mem"] = dict(rw=r["mem"], expr=expr, width=r["width"])
        if expr and write: o["ann"].append(["store", f"[{expr}]", show(val) if val is not None else "runtime value"])
        elif expr: o["ann"].append(["load", f"[{expr}]"])
        elif write and val is not None: o["ann"].append(["note", f"stores {show(val)}"])
    out.append(o)
  if cbs:
    for cb in cbs.values(): cb["sides"] = sorted(set(cb["sides"]))
  return dict(rows=out, funcs=sorted(funcs.values(), key=lambda f: f["pc"]), cbs={str(k): v for k, v in sorted(cbs.items())}, size=len(image),
              locals={hx(a - 0xFFB00000): nme for a, nme in sorted(ctx.locals.items())})

def sym_key(addr, d):
  t = d.get("type", "")
  if t == "cfg": return f"{d['group']}:{d['index']}"
  if t == "param": return "param:" + d["name"].removeprefix("param ")
  return f"a:{addr:x}"

def brief(word, tcfg):
  e = tt_decode(word, tcfg)
  return dict(op=e["op"], text=tt_text(e), gist=e["gist"])

def expand_replay(start, length, replay, tcfg):
  items = []
  for s in range(start, start + (length or 64)):
    w = replay.get(s % 32)
    items.append(dict(slot=s % 32, **(brief(w, tcfg) if w is not None else dict(op="?", text="not recorded above", gist=""))))
  return dict(kind="replay", items=items)

def expand_mop(word, cfg, replay, tcfg):
  """Instruction sequence a MOP expands to, using the MOP_CFG words stored earlier in listing order (ttsim's expander)."""
  NOP = 0x02000000
  if any(cfg.get(i) is None for i in range(9)):
    return dict(kind="mop", unknown=True, items=[], note="MOP_CFG is not fully known at this point (set at runtime or in another path)")
  c = [cfg[i] for i in range(9)]
  seq = []
  if word >> 23 & 1:
    outer, inner = c[0], c[1]
    flip = 0
    if c[6] != NOP: flip = c[5] ^ c[6]; inner *= 2
    for it in range(min(outer, 64)):
      if c[2] != NOP: seq.append(c[2])
      for j in range(inner):
        if j + 1 < inner: seq.append(c[5] ^ (flip if j & 1 else 0))
        elif it + 1 < outer: seq.append(c[8])
        else: seq.append(c[7])
      if c[3] != NOP:
        seq.append(c[3])
        if c[4] != NOP: seq.append(c[4])
    note = f"template 1: {outer} outer × {inner} inner"
  else:
    count, zmask, flags = (word >> 16 & 127) + 1, word & 0xFFFF, c[1]
    for it in range(count):
      if zmask >> it & 1: seq += [c[7]] + ([c[8]] if flags & 1 else [])
      else: seq += [c[3]] + (c[4:7] if flags & 2 else []) + ([c[2]] if flags & 1 else [])
    note = f"template 0: {count} iteration{'s' * (count != 1)}, zmask {hx(zmask)} (high 16 bits from MOP_CFG instruction not tracked)"
  items, total = [], 0
  for w in seq:
    b = brief(w, tcfg)
    if b["op"] == "REPLAY" and not w & 1:
      sub = expand_replay(w >> 14 & 0x3FF, w >> 4 & 0x3FF, replay, tcfg)["items"]
      b["sub"] = sub; total += len(sub)
    else: total += 1
    if items and items[-1]["op"] == b["op"] and items[-1]["text"] == b["text"]: items[-1]["times"] = items[-1].get("times", 1) + 1
    else: items.append(b)
  return dict(kind="mop", items=items, note=note, total=total)
