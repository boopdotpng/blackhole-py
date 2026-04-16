"""RV32IMZba/Zbb core emulator for Tenstorrent Blackhole Tensix tiles."""
from .memory import Memory, AddressMap

def _sext(val, bits):
    if val & (1 << (bits - 1)): return val - (1 << bits)
    return val

M32 = 0xFFFFFFFF

class Core:
    """RV32I base core. Subclass to set LDM_SIZE and PIPELINES."""
    LDM_SIZE = 0
    PIPELINES = frozenset()

    def __init__(self, l1=None, pc=0):
        self.l1 = l1 or Memory()
        self.ldm = Memory()
        self.mem = AddressMap(self.l1, self.ldm, self.LDM_SIZE)
        self.regs = [0] * 32
        self.csrs = {}  # CSR register file (sparse)
        self.pc = pc

    def _wr(self, rd, val):
        if rd != 0: self.regs[rd] = val & M32

    def read8(self, addr):     return self.mem.read8(addr)
    def write8(self, addr, v): self.mem.write8(addr, v)
    def read16(self, addr):     return self.mem.read16(addr)
    def write16(self, addr, v): self.mem.write16(addr, v)
    def read32(self, addr):     return self.mem.read32(addr)
    def write32(self, addr, v): self.mem.write32(addr, v)

    def load(self, addr, insns):
        for i, insn in enumerate(insns): self.write32(addr + i*4, int(insn))

    def step(self):
        word = self.read32(self.pc)
        if word == 0: return False
        if word & 0b11 != 0b11:
            self.pc = (self.pc + 4) & M32; return True
        pc = self.pc
        self.pc = (pc + 4) & M32
        opcode = word & 0x7F
        rd, funct3 = (word >> 7) & 0x1F, (word >> 12) & 0x7
        rs1, rs2, funct7 = (word >> 15) & 0x1F, (word >> 20) & 0x1F, (word >> 25) & 0x7F
        v1, v2 = self.regs[rs1], self.regs[rs2]
        imm_i = _sext((word >> 20) & 0xFFF, 12)
        imm_s = _sext(((word >> 7) & 0x1F) | (((word >> 25) & 0x7F) << 5), 12)
        imm_b = _sext((((word>>8)&0xF)<<1) | (((word>>25)&0x3F)<<5)
                      | (((word>>7)&1)<<11) | (((word>>31)&1)<<12), 13)
        imm_u = word & 0xFFFFF000
        imm_j = _sext((((word>>21)&0x3FF)<<1) | (((word>>20)&1)<<11)
                      | (((word>>12)&0xFF)<<12) | (((word>>31)&1)<<20), 21)
        match opcode:
            case 0x33:  # R-type ALU
                match (funct3, funct7):
                    # RV32I base
                    case (0, 0x00): self._wr(rd, v1 + v2)                           # ADD
                    case (0, 0x20): self._wr(rd, v1 - v2)                           # SUB
                    case (1, 0x00): self._wr(rd, v1 << (v2 & 0x1F))                # SLL
                    case (2, 0x00): self._wr(rd, 1 if _sext(v1,32) < _sext(v2,32) else 0)  # SLT
                    case (3, 0x00): self._wr(rd, 1 if v1 < v2 else 0)              # SLTU
                    case (4, 0x00): self._wr(rd, v1 ^ v2)                           # XOR
                    case (5, 0x00): self._wr(rd, v1 >> (v2 & 0x1F))                # SRL
                    case (5, 0x20): self._wr(rd, _sext(v1,32) >> (v2 & 0x1F))      # SRA
                    case (6, 0x00): self._wr(rd, v1 | v2)                           # OR
                    case (7, 0x00): self._wr(rd, v1 & v2)                           # AND
                    # M extension
                    case (0, 0x01): self._wr(rd, v1 * v2)                           # MUL
                    case (1, 0x01): self._wr(rd, (_sext(v1,32) * _sext(v2,32)) >> 32)  # MULH
                    case (2, 0x01): self._wr(rd, (_sext(v1,32) * v2) >> 32)        # MULHSU
                    case (3, 0x01): self._wr(rd, (v1 * v2) >> 32)                  # MULHU
                    case (4, 0x01):                                                 # DIV
                        s1, s2 = _sext(v1, 32), _sext(v2, 32)
                        if s2 == 0: self._wr(rd, M32)
                        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, s1)
                        else:
                            q = abs(s1) // abs(s2)
                            if (s1 < 0) != (s2 < 0): q = -q
                            self._wr(rd, q)
                    case (5, 0x01): self._wr(rd, v1 // v2 if v2 else M32)          # DIVU
                    case (6, 0x01):                                                 # REM
                        s1, s2 = _sext(v1, 32), _sext(v2, 32)
                        if s2 == 0: self._wr(rd, v1)
                        elif s1 == -0x80000000 and s2 == -1: self._wr(rd, 0)
                        else:
                            r = abs(s1) % abs(s2)
                            if s1 < 0: r = -r
                            self._wr(rd, r)
                    case (7, 0x01): self._wr(rd, v1 % v2 if v2 else v1)            # REMU
                    # Zba
                    case (2, 0x10): self._wr(rd, (v1 << 1) + v2)                   # SH1ADD
                    case (4, 0x10): self._wr(rd, (v1 << 2) + v2)                   # SH2ADD
                    case (6, 0x10): self._wr(rd, (v1 << 3) + v2)                   # SH3ADD
                    # Zbb
                    case (4, 0x04): self._wr(rd, v1 & 0xFFFF)                      # ZEXT.H
                    case (4, 0x05): self._wr(rd, min(_sext(v1,32), _sext(v2,32)))  # MIN
                    case (5, 0x05): self._wr(rd, min(v1, v2))                      # MINU
                    case (6, 0x05): self._wr(rd, max(_sext(v1,32), _sext(v2,32)))  # MAX
                    case (7, 0x05): self._wr(rd, max(v1, v2))                      # MAXU
                    # Zbb bit manipulation
                    case (4, 0x20): self._wr(rd, ~(v1 ^ v2))                       # XNOR
                    case (6, 0x20): self._wr(rd, v1 | ~v2)                         # ORN
                    case (7, 0x20): self._wr(rd, v1 & ~v2)                         # ANDN
                    case (1, 0x30):                                                 # ROL
                        sh = v2 & 0x1F
                        self._wr(rd, (v1 << sh) | (v1 >> (32 - sh)))
                    case (5, 0x30):                                                 # ROR
                        sh = v2 & 0x1F
                        self._wr(rd, (v1 >> sh) | (v1 << (32 - sh)))
            case 0x13:  # I-type ALU
                shamt = (word >> 20) & 0x1F
                match funct3:
                    case 0: self._wr(rd, v1 + imm_i)                               # ADDI
                    case 1:
                        match (funct7, shamt):
                            case (0x30, 0): self._wr(rd, 32 - v1.bit_length())     # CLZ
                            case (0x30, 1):                                         # CTZ
                                self._wr(rd, (v1 & -v1).bit_length() - 1 if v1 else 32)
                            case (0x30, 2): self._wr(rd, bin(v1).count('1'))        # CPOP
                            case (0x30, 4): self._wr(rd, _sext(v1 & 0xFF, 8))      # SEXT.B
                            case (0x30, 5): self._wr(rd, _sext(v1 & 0xFFFF, 16))   # SEXT.H
                            case _: self._wr(rd, v1 << shamt)                       # SLLI
                    case 2: self._wr(rd, 1 if _sext(v1,32) < imm_i else 0)         # SLTI
                    case 3: self._wr(rd, 1 if v1 < (imm_i & M32) else 0)           # SLTIU
                    case 4: self._wr(rd, v1 ^ (imm_i & M32))                       # XORI
                    case 5:
                        match funct7:
                            case 0x00: self._wr(rd, v1 >> shamt)                    # SRLI
                            case 0x20: self._wr(rd, _sext(v1,32) >> shamt)          # SRAI
                            case 0x30:                                               # RORI
                                self._wr(rd, (v1 >> shamt) | (v1 << (32 - shamt)))
                            case 0x14:                                               # ORC.B
                                r = 0
                                for j in range(4): r |= (0xFF if (v1 >> j*8) & 0xFF else 0) << j*8
                                self._wr(rd, r)
                            case 0x34:                                               # REV8
                                self._wr(rd, ((v1&0xFF)<<24)|((v1>>8&0xFF)<<16)|((v1>>16&0xFF)<<8)|(v1>>24&0xFF))
                    case 6: self._wr(rd, v1 | (imm_i & M32))                       # ORI
                    case 7: self._wr(rd, v1 & (imm_i & M32))                       # ANDI
            case 0x03:  # loads
                addr = (v1 + imm_i) & M32
                match funct3:
                    case 0: self._wr(rd, _sext(self.read8(addr), 8))                # LB
                    case 1: self._wr(rd, _sext(self.read16(addr), 16))              # LH
                    case 2: self._wr(rd, self.read32(addr))                         # LW
                    case 4: self._wr(rd, self.read8(addr))                          # LBU
                    case 5: self._wr(rd, self.read16(addr))                         # LHU
            case 0x23:  # stores
                addr = (v1 + imm_s) & M32
                match funct3:
                    case 0: self.write8(addr, v2)                                   # SB
                    case 1: self.write16(addr, v2)                                  # SH
                    case 2: self.write32(addr, v2)                                  # SW
            case 0x63:  # branches
                s1, s2 = _sext(v1, 32), _sext(v2, 32)
                taken = False
                match funct3:
                    case 0: taken = (v1 == v2)                                      # BEQ
                    case 1: taken = (v1 != v2)                                      # BNE
                    case 4: taken = (s1 < s2)                                       # BLT
                    case 5: taken = (s1 >= s2)                                      # BGE
                    case 6: taken = (v1 < v2)                                       # BLTU
                    case 7: taken = (v1 >= v2)                                      # BGEU
                if taken: self.pc = (pc + imm_b) & M32
            case 0x37: self._wr(rd, imm_u)                                          # LUI
            case 0x17: self._wr(rd, (pc + imm_u) & M32)                            # AUIPC
            case 0x6F:                                                              # JAL
                self._wr(rd, (pc + 4) & M32); self.pc = (pc + imm_j) & M32
            case 0x67:                                                              # JALR
                self._wr(rd, (pc + 4) & M32); self.pc = (v1 + imm_i) & 0xFFFFFFFE
            case 0x73:                                                              # SYSTEM
                if funct3 != 0:                                                 # CSR instructions
                    csr = (word >> 20) & 0xFFF
                    old = self.csrs.get(csr, 0)
                    src = v1 if funct3 <= 3 else rs1                            # reg vs imm form
                    match funct3 & 3:
                        case 1: new = src                                       # CSRRW / CSRRWI
                        case 2: new = old | src                                 # CSRRS / CSRRSI
                        case 3: new = old & ~src                                # CSRRC / CSRRCI
                        case _: new = old
                    self._wr(rd, old)
                    if not ((funct3 & 3) >= 2 and rs1 == 0):                    # CSRRS/CSRRC with rs1=0: read-only
                        self.csrs[csr] = new & M32
            case 0x0F: pass                                                         # FENCE
        if self.pc == pc: return False
        return True

    def run(self, n=10_000):
        for i in range(n):
            if not self.step(): return i + 1
        return n

class BRISC(Core):
    LDM_SIZE = 0x2000; PIPELINES = frozenset({0, 1, 2})
class NCRISC(Core):
    LDM_SIZE = 0x2000; PIPELINES = frozenset()
class TRISC0(Core):
    LDM_SIZE = 0x1000; PIPELINES = frozenset({0})
class TRISC1(Core):
    LDM_SIZE = 0x1000; PIPELINES = frozenset({1})
class TRISC2(Core):
    LDM_SIZE = 0x1000; PIPELINES = frozenset({2})
