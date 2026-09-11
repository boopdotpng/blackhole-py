"""Source-preserving L1 -> FP32 Dst via runtime SFPU immediates.

This deliberately avoids direct UNPACR's documented whole-SrcA clobber.
"""
from asm import Asm
from isa import R, Reg, Tensix as TT, is_reg
from fw.consts import TensixMMIO
from tests.movement.unpacker import unpack as u


def _issue_or(k, instruction, bits):
  base, word = k.reg(2)
  k.li(base, instruction)
  k.or_(word, bits, base)
  k.write(TensixMMIO.INSTRN_BUF_BASE, word)


def unpack_dst(k: Asm, *, dst_slot: int, source: int, count: Reg, input_format=u.F32):
  """N=1..128 exact input elements -> one zero-filled FP32 Dst slot.

  TRISC1/math owns Dst; no inter-thread handoff inside. Clobbers L0,L7,
  CC state (returns all enabled), math address counters and FP32 configuration.
  Reads exactly N aligned FP32/BF16 words; requires no L1 or Dst scratch.
  All source allocations untouched. Four fixed runtime loops select SFPU lanes.
  """
  if type(dst_slot) is not int or not 0 <= dst_slot < 64: raise ValueError('Dst slot 0..63 required')
  if not is_reg(count): raise TypeError('runtime element count required')
  if input_format not in (u.BF16,u.F32): raise ValueError('BF16 or FP32 required')
  size=2 if input_format==u.BF16 else 4
  if source%size: raise ValueError('input must be naturally aligned')
  u.configure_fp32_dst(k,dst_slot//8)
  for register in (12,28,47): u._set_thread_cfg(k,register,0)
  k.emit(TT.TTSETRWC(0,0,0,0,0,0xF))
  for vector in range(4):
    k.emit(TT.TTSFPENCC(0,0,0,2))
    k.emit(TT.TTSFPLOADI(0,0,0))
    for lane in k.range(32):
      # SFPU L15 holds 2*lane. Equality picks exactly the RV loop lane.
      k.emit(TT.TTSFPENCC(3,0,0,10))
      negative, imm, logical, pointer, value, low, high = k.reg(7)
      k.slli(logical,lane,1)
      k.sub(negative,R.ZERO,logical)
      k.slli(imm,negative,20)
      k.srli(imm,imm,8)
      _issue_or(k,TT.TTSFPIADD(0,15,7,5),imm)
      k.emit(TT.TTSFPSETCC(0,7,0,6))
      k.addi(logical,logical,(vector//2)*64+vector%2)
      skip=k._new_label('zero_tail')
      k.bgeu(logical,count,skip)
      k.slli(pointer,logical,1 if size==2 else 2)
      k.li(value,source)
      k.add(pointer,pointer,value)
      k.read(value,pointer,bytes=size)
      if size==2:
        _issue_or(k,TT.TTSFPLOADI(0,0,0),value)
      else:
        k.srli(high,value,16)
        k.slli(low,value,16)
        k.srli(low,low,16)
        _issue_or(k,TT.TTSFPLOADI(0,0,0),high)
        _issue_or(k,TT.TTSFPLOADI(0,10,0),low)
      k.label(skip)
    k.emit(TT.TTSFPENCC(0,0,0,2))
    k.emit(TT.TTSFPSTORE(0,3,0,(dst_slot%8)*8+vector*2))
  u.stall(k,u.Stall.SYNC,u.Wait.SFPU)
  u.pc_sync(k)
