# =============================================================================
# TensixCoprocessor — the frontend. Aggregates shared state (Src/Dest/ADC/
# GPR/Semaphores/config), the three per-TRISC instruction frontends, and the
# three backend pipelines (unpack, math, pack) plus the cross-cutting ThCon
# and Sync units any thread can drive. Steps all three threads per cycle,
# enforces the WaitGate, and routes decoded instructions to the right unit.
# =============================================================================

from ..memory import Memory, INSTRN_BUF_T0, MOP_CFG_BASE
from dsl import decode_tensix

from .state import (
  SrcRegFile, DestRegFile, RWCState, AddrModState, ADCState, GPRFile,
  Semaphores,
)
from .frontend import TensixThread
from .thcon import ConfigUnit, ScalarUnit
from .sync import SyncUnit, MutexSet
from .math import FPU, SFPU
from .unpack import Unpacker, UnpackerState
from .pack import Packer
from .mover import Mover


_TRISC_THREAD = {'trisc0': 0, 'trisc1': 1, 'trisc2': 2}


class _PCBufFIFO:
  CAPACITY = 16

  def __init__(self):
    self._q = []

  def push(self, word):
    if len(self._q) >= self.CAPACITY:
      return False
    self._q.append(word & 0xFFFFFFFF)
    return True

  def pop(self):
    if not self._q:
      return None
    return self._q.pop(0)

  @property
  def empty(self):
    return not self._q


class TensixCoprocessor:
  def __init__(self, l1: Memory = None):
    # Shared backend state. The 8 hardware semaphores live inside the
    # coprocessor (per emu-specs/semaphores.md); TRISC RISC-V cores reach
    # them through the PCBuf semaphore window, which the device wires to
    # this object.
    self.semaphores = Semaphores()
    self.gpr = GPRFile()
    self.srca = SrcRegFile("SrcA")
    self.srcb = SrcRegFile("SrcB")
    self.dest = DestRegFile()
    # Cross-cutting units (any thread can issue)
    self.sync = SyncUnit(self.semaphores)
    self.config_unit = ConfigUnit(self.gpr)
    self.scalar = ScalarUnit(self.gpr)
    self.mutexes = MutexSet()
    # L1 tile memory (shared with device; callers may inject a pre-populated
    # Memory for testing, or leave as None for non-unpack tests).
    self.l1 = l1 if l1 is not None else Memory()
    # Per-unpacker runtime state (SrcRow offsets, context counters)
    self.unpackers = [UnpackerState(), UnpackerState()]
    # Per-pipeline backends
    self.unpack = Unpacker(self.srca, self.srcb)       # T0 pipeline
    self.fpu    = FPU(self.srca, self.srcb, self.dest) # T1 pipeline (math)
    self.sfpu   = SFPU(self.dest)                      # T1 pipeline (math)
    # Per-thread address counters (must be created before wiring Packer)
    self.rwc = [RWCState() for _ in range(3)]
    self.addr_mod = AddrModState()
    self.adc = [ADCState() for _ in range(3)]
    # T2 pipeline: Packer wired to Dest, ConfigUnit, ADC (thread list), and L1
    self.packer = Packer(dest=self.dest, cfg=self.config_unit,
                         adc=self.adc, l1=self.l1)
    # Per-thread frontend pipelines
    self.threads = [TensixThread(i) for i in range(3)]
    # Tensix backend config register file (0xFFEF0000..0xFFEFFFFF).
    self.cfg = Memory()
    self.stream_regs = None
    # Mover / XMOV — DMA engine shared with the TDMA-RISC register block.
    # Operates on raw byte-addressed Memory: l1 is the tile L1 (shared with
    # the packer/unpacker path), cfg is the ADDR8-relative config Memory
    # (device.py mounts it at TENSIX_CFG_BASE so bus writes resolve to the
    # same relative offsets the Mover writes).  config_unit.cfg (the WRCFG
    # ADDR32 view) is a separate bank array, consulted by XMOV to read its
    # transfer parameters.
    self.mover = Mover(l1=self.l1, cfg=self.cfg)
    self.pcbuf_fifo = [_PCBufFIFO() for _ in range(3)]

  def attach_l1(self, l1):
    """Swap in a new L1 Memory.  Used by tests that want a fresh L1 between
    transfers.  Production callers should pass l1 through the constructor."""
    self.l1 = l1
    self.mover.l1 = l1

  def instrn_handler_for(self, role):
    if role == 'brisc':       return _InstrnHandler(self, _brisc_thread_of_addr)
    if role in _TRISC_THREAD: return _InstrnHandler(self, _const(_TRISC_THREAD[role]))
    return None  # ncrisc — no push capability

  def mop_handler_for(self, role):
    if role in _TRISC_THREAD: return _MopCfgHandler(self, _TRISC_THREAD[role])
    return None  # brisc/ncrisc — no MOP cfg access

  def push_instruction(self, thread_id, word):
    return self.threads[thread_id].fifo.push(word)

  def step(self):
    for thread in self.threads:
      self._step_thread(thread)

  def _step_thread(self, thread):
    insn = thread.next_instruction()
    if insn is None: return
    if thread.wait_gate.is_blocking(insn, self._hw_state(), thread.id): return
    self._dispatch(thread, insn)

  def _dispatch(self, thread, word):
    d = decode_tensix(word)
    rwc = self.rwc[thread.id]
    adc = self.adc[thread.id]
    match d.name:
      case 'NOP' | 'DMANOP': pass
      # ── Sync unit: mutexes, semaphores, stall/wait ──────────────────
      case 'ATGETM':
        if not self.mutexes.acquire(d.mutex_index, thread.id):
          thread.replay_instruction(word)  # block: put it back in the FIFO
          return
      case 'ATRELM':    self.mutexes.release(d.mutex_index, thread.id)
      case 'STALLWAIT': self.sync.execute_stallwait(thread.wait_gate, d)
      case 'SEMINIT':   self.sync.execute_seminit(d)
      case 'SEMPOST':   self.sync.execute_sempost(d)
      case 'SEMGET':    self.sync.execute_semget(d)
      case 'SEMWAIT':   self.sync.execute_semwait(thread.wait_gate, d)
      case 'STREAMWAIT':
        self.sync.execute_streamwait(thread.wait_gate, d,
                                     self.config_unit.thread_cfg, thread.id)
      # ── ThCon pipe: config + scalar (any thread) ────────────────────
      case 'WRCFG':   self.config_unit.execute_wrcfg(d, thread.id)
      case 'RDCFG':   self.config_unit.execute_rdcfg(d, thread.id)
      case 'SETC16':  self.config_unit.execute_setc16(d, thread.id)
      case 'RMWCIB0': self.config_unit.execute_rmwcib(d, byte_index=0)
      case 'RMWCIB1': self.config_unit.execute_rmwcib(d, byte_index=1)
      case 'CFGSHIFTMASK': self.config_unit.execute_cfgshiftmask(d, thread.id)
      case 'STREAMWRCFG':
        self.config_unit.execute_streamwrcfg(d, thread.id, self._read_stream_cfg)
      case 'REG2FLOP':     self.config_unit.execute_reg2flop(d, thread.id)
      case 'SETDMAREG':    self.scalar.execute_setdmareg(d, thread.id)
      case 'ADDDMAREG':    self.scalar.execute_adddmareg(d, thread.id)
      case 'MULDMAREG':    self.scalar.execute_muldmareg(d, thread.id)
      case 'BITWOPDMAREG': self.scalar.execute_bitwopdmareg(d, thread.id)
      case 'SHIFTDMAREG':  self.scalar.execute_shiftdmareg(d, thread.id)
      case 'CMPDMAREG':    self.scalar.execute_cmpdmareg(d, thread.id)
      # FLUSHDMA: in synchronous emulation the pipeline conditions (C0-C3)
      # are always idle, so the wait is a no-op. Kept as a named dispatch so
      # decode_tensix resolves to 'FLUSHDMA' rather than UNKNOWN_0x46.
      case 'FLUSHDMA':     pass
      # ── ADC (any thread can issue) ──────────────────────────────────
      case 'SETADC':   adc.execute_setadc(d)
      case 'SETADCXY': adc.execute_setadcxy(d)
      case 'SETADCZW': adc.execute_setadczw(d)
      case 'INCADCZW': adc.execute_incadczw(d)
      case 'SETADCXX': adc.execute_setadcxx(d)
      # ── T0 pipeline: unpack ─────────────────────────────────────────
      case 'UNPACR':     self.unpack.handle_unpacr(d, thread.id, self)
      case 'UNPACR_NOP': self.unpack.handle_unpacr_nop(d)
      # ── T1 pipeline: FPU / SFPU / RWC ───────────────────────────────
      case 'ZEROACC':     self.fpu.zeroacc(d)
      case 'ZEROSRC':     self.fpu.zerosrc(d)
      case 'MOVB2D':      self.fpu.movb2d(d, rwc)
      case 'TRNSPSRCB':   self.fpu.trnspsrcb(d)
      case 'SHIFTXA':     self.fpu.shiftxa(d)
      case 'SHIFTXB':     self.fpu.shiftxb(d)
      case 'MVMUL':       self.fpu.mvmul(d, rwc)
      case 'DOTPV':       self.fpu.dotpv(d, rwc)
      case 'GAPOOL':      self.fpu.gapool(d, rwc)
      case 'ELWADD':      self.fpu.elwadd(d, rwc)
      case 'GMPOOL':      self.fpu.gmpool(d, rwc)
      case 'CLEARDVALID': self.fpu.cleardvalid(d)
      case 'MOVD2A':      self.fpu.movd2a(d, rwc)
      case 'MOVD2B':      self.fpu.movd2b(d, rwc)
      case 'SETRWC':
        clear_ab = rwc.execute_setrwc(d)
        if clear_ab & 1: self.srca.release_from_fpu()
        if clear_ab & 2: self.srcb.release_from_fpu()
      case 'INCRWC':      rwc.execute_incrwc(d)
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
      case 'SFPLOADMACRO':
        self.sfpu.sfpload(d, rwc)
        # Functional shortcut for the common zero-delay simple sub-unit macro.
        if all(self.sfpu.lregs[d.lreg_ind][lane] == 0 for lane in range(1, 32)):
          recip = type('_SfpRecipD', (), {
            'lreg_c': d.lreg_ind, 'lreg_dest': d.lreg_ind, 'instr_mod1': 0
          })()
          self.sfpu.sfparecip(recip)
      case 'SFPLUTFP32':  self.sfpu.sfplutfp32(d)
      case 'SFPARECIP':   self.sfpu.sfparecip(d)
      case 'SFPTRANSP':   self.sfpu.sfptransp(d)
      case 'SFPNOP':      pass
      # ── T2 pipeline: pack ───────────────────────────────────────────
      case 'PACR':        self.packer.handle_pacr(d, thread.id)
      # ── Mover (XMOV) ────────────────────────────────────────────────
      # Parameters come from Tensix Backend Config, not the instruction
      # encoding.  ADDR32 mapping (cfg_defines.h, Blackhole):
      #   88: THCON_SEC0_REG6_Source_address
      #   89: THCON_SEC0_REG6_Destination_address
      #   90: THCON_SEC0_REG6_{Buffer_size[29:0], Transfer_direction[31:30]}
      # Per spec, size field is only 16 low bits of ADDR32 90.  Last/
      # Mov_block_selection (bits [23]/[0] in the instruction word) are
      # decoded but have no observable functional effect.
      case 'XMOV':
        cfg = self.config_unit
        sid = cfg._state_id(thread.id)
        if sid < cfg.NUM_STATES:
          src  = cfg.cfg[sid][88] << 4
          dst  = cfg.cfg[sid][89] << 4
          reg90 = cfg.cfg[sid][90]
          size = (reg90 & 0xFFFF) << 4
          direction = (reg90 >> 30) & 0x3
          self.mover.transfer(dst, src, size, direction)
      # Unknown opcodes: no-op (for functional emulation).
      case _: pass

  def _hw_state(self):
    return HardwareState(self.semaphores, self.srca, self.srcb)

  def _read_stream_cfg(self, stream_sel, stream_reg_addr):
    if self.stream_regs is None:
      return 0
    stream_id = stream_sel & 3
    addr = (stream_id * 4096) + ((stream_reg_addr & 0x3FF) * 4)
    return self.stream_regs.read32(addr)

  def write_mop_cfg(self, thread_id, reg_index, value):
    if 0 <= reg_index < 9:
      self.threads[thread_id].mop.cfg[reg_index] = value

  def read_pcbuf(self, thread_id, offset):
    # Resolves immediately in functional emulation (synchronous dispatch).
    return 0

  def brisc_read_pcbuf_base(self, thread_id):
    thread = self.threads[thread_id]
    ready = self.pcbuf_fifo[thread_id].empty and thread.fifo.empty
    return ready, 0


# Bound at registration time by `instrn_handler_for(role)`:
#   BRISC decodes the thread from the address (T0/T1/T2 = +0/+0x10000/+0x20000);
#   TRISCs always target their own thread.
def _brisc_thread_of_addr(addr): return (addr - INSTRN_BUF_T0) >> 16
def _const(x):
  def f(_addr): return x
  return f


class _InstrnHandler:
  def __init__(self, tensix, thread_of_addr):
    self.tensix = tensix
    self._thread = thread_of_addr

  def read8(self, addr):  return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val):  pass
  def write16(self, addr, val): pass
  def write32(self, addr, val): self.tensix.push_instruction(self._thread(addr), val)


class _MopCfgHandler:
  def __init__(self, tensix, thread):
    self.tensix = tensix
    self.thread = thread

  def read8(self, addr):  return 0
  def read16(self, addr): return 0
  def read32(self, addr): return 0
  def write8(self, addr, val):  pass
  def write16(self, addr, val): pass
  def write32(self, addr, val):
    reg_index = (addr - MOP_CFG_BASE) >> 2
    self.tensix.write_mop_cfg(self.thread, reg_index, val)


class HardwareState:
  __slots__ = ('semaphores', 'srca', 'srcb',
               'srca_unpack_bank_owner', 'srcb_unpack_bank_owner',
               'srca_fpu_bank_owner', 'srcb_fpu_bank_owner')

  def __init__(self, semaphores, srca, srcb):
    self.semaphores = semaphores
    self.srca = srca
    self.srcb = srcb
    # Functional emu: pipeline occupancy signals are idle (synchronous
    # completion). Only bank ownership matters.
    self.srca_unpack_bank_owner = srca.banks[srca.unpack_bank].allowed_client
    self.srcb_unpack_bank_owner = srcb.banks[srcb.unpack_bank].allowed_client
    self.srca_fpu_bank_owner = srca.banks[srca.fpu_bank].allowed_client
    self.srcb_fpu_bank_owner = srcb.banks[srcb.fpu_bank].allowed_client
