from .memory import Memory, L1_BASE, L1_END, LDM_BASE
from .router import Router
from .dsl import decode_rv

M32 = 0xFFFFFFFF
def _sext(v, b): return v - (1 << b) if v & (1 << (b-1)) else v

class Core:
  ROLE = None          # 'brisc' | 'ncrisc' | 'trisc0' | 'trisc1' | 'trisc2'
  LDM_SIZE = 0
  PIPELINES = frozenset()

  def __init__(self, l1=None, pc=0):
    self.l1 = l1 or Memory()
    self.ldm = Memory()
    self.mem = Router(default=Memory())
    self.mem.register(L1_BASE, L1_END, self.l1)
    if self.LDM_SIZE:
      self.mem.register(LDM_BASE, LDM_BASE + self.LDM_SIZE - 1,
                        self.ldm, offset=LDM_BASE)
    self.regs = [0] * 32
    self.csrs = {}  # CSR register file (sparse)
    self.pc = pc
    self.in_reset = True

  def _wr(self, rd, val):
    if rd != 0: self.regs[rd] = val & M32

  def load(self, addr, insns):
    for i, insn in enumerate(insns): self.mem.write32(addr + i*4, int(insn))

  def step(self):
    word = self.mem.read32(self.pc)
    pc = self.pc
    self.pc = (pc + 4) & M32
    d = decode_rv(word)
    rd, rs1, imm, shamt = d.rd, d.rs1, d.imm, d.shamt
    v1, v2 = self.regs[d.rs1], self.regs[d.rs2]
    match d.name:
      # RV32I R-type
      case 'ADD':    self._wr(rd, v1 + v2)
      case 'SUB':    self._wr(rd, v1 - v2)
      case 'SLL':    self._wr(rd, v1 << (v2 & 0x1F))
      case 'SLT':    self._wr(rd, 1 if _sext(v1,32) < _sext(v2,32) else 0)
      case 'SLTU':   self._wr(rd, 1 if v1 < v2 else 0)
      case 'XOR':    self._wr(rd, v1 ^ v2)
      case 'SRL':    self._wr(rd, v1 >> (v2 & 0x1F))
      case 'SRA':    self._wr(rd, _sext(v1,32) >> (v2 & 0x1F))
      case 'OR':     self._wr(rd, v1 | v2)
      case 'AND':    self._wr(rd, v1 & v2)
      # M extension
      case 'MUL':    self._wr(rd, v1 * v2)
      case 'MULH':   self._wr(rd, (_sext(v1,32) * _sext(v2,32)) >> 32)
      case 'MULHSU': self._wr(rd, (_sext(v1,32) * v2) >> 32)
      case 'MULHU':  self._wr(rd, (v1 * v2) >> 32)
      case 'DIV':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        if s2 == 0: self._wr(rd, M32)
        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, s1)
        else:
          q = abs(s1) // abs(s2)
          if (s1 < 0) != (s2 < 0): q = -q
          self._wr(rd, q)
      case 'DIVU':   self._wr(rd, v1 // v2 if v2 else M32)
      case 'REM':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        if s2 == 0: self._wr(rd, v1)
        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, 0)
        else:
          r = abs(s1) % abs(s2)
          if s1 < 0: r = -r
          self._wr(rd, r)
      case 'REMU':   self._wr(rd, v1 % v2 if v2 else v1)
      # Zba
      case 'SH1ADD': self._wr(rd, (v1 << 1) + v2)
      case 'SH2ADD': self._wr(rd, (v1 << 2) + v2)
      case 'SH3ADD': self._wr(rd, (v1 << 3) + v2)
      # Zbb R-type
      case 'ZEXT_H': self._wr(rd, v1 & 0xFFFF)
      case 'MIN':    self._wr(rd, min(_sext(v1,32), _sext(v2,32)))
      case 'MINU':   self._wr(rd, min(v1, v2))
      case 'MAX':    self._wr(rd, max(_sext(v1,32), _sext(v2,32)))
      case 'MAXU':   self._wr(rd, max(v1, v2))
      case 'XNOR':   self._wr(rd, ~(v1 ^ v2))
      case 'ORN':    self._wr(rd, v1 | ~v2)
      case 'ANDN':   self._wr(rd, v1 & ~v2)
      case 'ROL':
        sh = v2 & 0x1F
        self._wr(rd, (v1 << sh) | (v1 >> (32 - sh)))
      case 'ROR':
        sh = v2 & 0x1F
        self._wr(rd, (v1 >> sh) | (v1 << (32 - sh)))
      # RV32I I-type ALU
      case 'ADDI':   self._wr(rd, v1 + imm)
      case 'SLTI':   self._wr(rd, 1 if _sext(v1,32) < imm else 0)
      case 'SLTIU':  self._wr(rd, 1 if v1 < (imm & M32) else 0)
      case 'XORI':   self._wr(rd, v1 ^ (imm & M32))
      case 'ORI':    self._wr(rd, v1 | (imm & M32))
      case 'ANDI':   self._wr(rd, v1 & (imm & M32))
      case 'SLLI':   self._wr(rd, v1 << shamt)
      case 'SRLI':   self._wr(rd, v1 >> shamt)
      case 'SRAI':   self._wr(rd, _sext(v1,32) >> shamt)
      # Zbb I-type unary
      case 'CLZ':    self._wr(rd, 32 - v1.bit_length())
      case 'CTZ':    self._wr(rd, (v1 & -v1).bit_length() - 1 if v1 else 32)
      case 'CPOP':   self._wr(rd, bin(v1).count('1'))
      case 'SEXT_B': self._wr(rd, _sext(v1 & 0xFF, 8))
      case 'SEXT_H': self._wr(rd, _sext(v1 & 0xFFFF, 16))
      case 'RORI':   self._wr(rd, (v1 >> shamt) | (v1 << (32 - shamt)))
      case 'ORC_B':
        r = 0
        for j in range(4): r |= (0xFF if (v1 >> j*8) & 0xFF else 0) << j*8
        self._wr(rd, r)
      case 'REV8':
        self._wr(rd, ((v1&0xFF)<<24)|((v1>>8&0xFF)<<16)|((v1>>16&0xFF)<<8)|(v1>>24&0xFF))
      # Loads
      case 'LB':     self._wr(rd, _sext(self.mem.read8((v1 + imm) & M32), 8))
      case 'LH':     self._wr(rd, _sext(self.mem.read16((v1 + imm) & M32), 16))
      case 'LW':     self._wr(rd, self.mem.read32((v1 + imm) & M32))
      case 'LBU':    self._wr(rd, self.mem.read8((v1 + imm) & M32))
      case 'LHU':    self._wr(rd, self.mem.read16((v1 + imm) & M32))
      # Stores
      case 'SB':     self.mem.write8((v1 + imm) & M32, v2)
      case 'SH':     self.mem.write16((v1 + imm) & M32, v2)
      case 'SW':     self.mem.write32((v1 + imm) & M32, v2)
      # Branches
      case 'BEQ' | 'BNE' | 'BLT' | 'BGE' | 'BLTU' | 'BGEU':
        s1, s2 = _sext(v1, 32), _sext(v2, 32)
        taken = {'BEQ': v1==v2, 'BNE': v1!=v2, 'BLT': s1<s2,
                 'BGE': s1>=s2, 'BLTU': v1<v2, 'BGEU': v1>=v2}[d.name]
        if taken: self.pc = (pc + imm) & M32
      # Upper-immediate / jumps
      case 'LUI':    self._wr(rd, imm)
      case 'AUIPC':  self._wr(rd, (pc + imm) & M32)
      case 'JAL':    self._wr(rd, (pc + 4) & M32); self.pc = (pc + imm) & M32
      case 'JALR':   self._wr(rd, (pc + 4) & M32); self.pc = (v1 + imm) & 0xFFFFFFFE
      # CSR (rs1 holds zimm for *I variants)
      case 'CSRRW' | 'CSRRS' | 'CSRRC' | 'CSRRWI' | 'CSRRSI' | 'CSRRCI':
        src = v1 if d.name in ('CSRRW','CSRRS','CSRRC') else rs1
        old = self.csrs.get(d.csr, 0)
        self._wr(rd, old)
        if d.name in ('CSRRW','CSRRWI'):     self.csrs[d.csr] = src & M32
        elif src != 0 and d.name in ('CSRRS','CSRRSI'): self.csrs[d.csr] = (old | src) & M32
        elif src != 0 and d.name in ('CSRRC','CSRRCI'): self.csrs[d.csr] = (old & ~src) & M32
      case 'FENCE':  pass
      case _:        pass  # UNKNOWN / TTINSN-encoded / illegal: no-op
    if self.pc == pc: return False
    return True

  def run(self, n=10_000):
    for i in range(n):
      if not self.step(): return i + 1
    return n

class BRISC(Core):
  ROLE = 'brisc';  LDM_SIZE = 0x2000; PIPELINES = frozenset({0, 1, 2})
class NCRISC(Core):
  ROLE = 'ncrisc'; LDM_SIZE = 0x2000; PIPELINES = frozenset()
class TRISC0(Core):
  ROLE = 'trisc0'; LDM_SIZE = 0x1000; PIPELINES = frozenset({0})
class TRISC1(Core):
  ROLE = 'trisc1'; LDM_SIZE = 0x1000; PIPELINES = frozenset({1})
class TRISC2(Core):
  ROLE = 'trisc2'; LDM_SIZE = 0x1000; PIPELINES = frozenset({2})
