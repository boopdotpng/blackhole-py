from ..dsl import decode_tensix


class TRISC1Decoder:
  def __init__(self, coproc):
    self.coproc = coproc
    self.fpu = coproc.fpu
    self.sfpu = coproc.sfpu

  def dispatch(self, word, thread):
    d = decode_tensix(word)
    rwc = self.coproc.rwc[thread.id]
    match d.name:
      # ── FPU: Matrix Unit ──────────────────────────────────────────
      case 'ZEROACC':     self.fpu.zeroacc(d)
      case 'ZEROSRC':     self.fpu.zerosrc(d)
      case 'MOVB2D':      self.fpu.movb2d(d, rwc)
      case 'TRNSPSRCB':   self.fpu.trnspsrcb(d)
      case 'MVMUL':       self.fpu.mvmul(d, rwc)
      case 'ELWADD':      self.fpu.elwadd(d, rwc)
      case 'GMPOOL':      self.fpu.gmpool(d, rwc)
      case 'CLEARDVALID': self.fpu.cleardvalid(d)
      case 'MOVD2A':      self.fpu.movd2a(d, rwc)
      case 'MOVD2B':      self.fpu.movd2b(d, rwc)
      # ── RWC: Read-Write Counters ────────────────────────────────
      case 'SETRWC':
        clear_ab = rwc.execute_setrwc(d)
        if clear_ab & 1: self.coproc.srca.release_from_fpu()
        if clear_ab & 2: self.coproc.srcb.release_from_fpu()
      case 'INCRWC':      rwc.execute_incrwc(d)
      # ── SFPU: Vector Unit ──────────────────────────────────────
      case 'SFPLOAD':     self.sfpu.sfpload(d, rwc)
      case 'SFPLOADI':    self.sfpu.sfploadi(d)
      case 'SFPSTORE':    self.sfpu.sfpstore(d, rwc)
      case 'SFPMULI':     self.sfpu.sfpmuli(d)
      case 'SFPADDI':     self.sfpu.sfpaddi(d)
      case 'SFPDIVP2':    self.sfpu.sfpdivp2(d)
      case 'SFPEXEXP':    self.sfpu.sfpexexp(d)
      case 'SFPEXMAN':    self.sfpu.sfpexman(d)
      case 'SFPSETEXP':   self.sfpu.sfpsetexp(d)
      case 'SFPIADD':     self.sfpu.sfpiadd(d)
      case 'SFPMUL24':    self.sfpu.sfpmul24(d)
      case 'SFPSHFT':     self.sfpu.sfpshft(d)
      case 'SFPSHFT2':    self.sfpu.sfpshft2(d)
      case 'SFPSETCC':    self.sfpu.sfpsetcc(d)
      case 'SFPGT':       self.sfpu.sfpgt(d)
      case 'SFPMOV':      self.sfpu.sfpmov(d)
      case 'SFPABS':      self.sfpu.sfpabs(d)
      case 'SFPSETSGN':   self.sfpu.sfpsetsgn(d)
      case 'SFPAND':      self.sfpu.sfpand(d)
      case 'SFPOR':       self.sfpu.sfpor(d)
      case 'SFPNOT':      self.sfpu.sfpnot(d)
      case 'SFPLZ':       self.sfpu.sfplz(d)
      case 'SFPXOR':      self.sfpu.sfpxor(d)
      case 'SFPMAD':      self.sfpu.sfpmad(d)
      case 'SFPADD':      self.sfpu.sfpadd(d)
      case 'SFPMUL':      self.sfpu.sfpmul(d)
      case 'SFPPUSHC':    self.sfpu.sfppushc(d)
      case 'SFPPOPC':     self.sfpu.sfppopc(d)
      case 'SFPENCC':     self.sfpu.sfpencc(d)
      case 'SFPCOMPC':    self.sfpu.sfpcompc(d)
      case 'SFPSTOCHRND': self.sfpu.sfpstochrnd(d)
      case 'SFPCAST':     self.sfpu.sfpcast(d)
      case 'SFPCONFIG':   self.sfpu.sfpconfig(d)
      case 'SFPSWAP':     self.sfpu.sfpswap(d)
      case 'SFPLOADMACRO':self.sfpu.sfpload(d, rwc)
      case 'SFPLUTFP32':  self.sfpu.sfplutfp32(d)
      case 'SFPARECIP':   self.sfpu.sfparecip(d)
      case 'SFPNOP':      pass
      case _: return False
    return True
