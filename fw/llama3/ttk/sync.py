from enum import IntEnum

from isa import R, Tensix as TT
from fw.consts import TensixMMIO


class Stall(IntEnum):
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF


class Wait(IntEnum):
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (
    1 << x for x in range(13)
  )


class SemWait(IntEnum):
  STALL_ON_ZERO, STALL_ON_MAX = 1, 2


class Sem:
  FPU_SFPU, MATH_PACK, UNPACK_TO_DEST, UNPACK_OPERAND_SYNC = range(4)
  PACK_DONE, UNPACK_SYNC, UNPACK_MATH_DONE, MATH_DONE = range(4, 8)

  @staticmethod
  def mask(index: int):
    if not 0 <= index < 8:
      raise ValueError(f"Tensix semaphore index out of range: {index}")
    return 1 << index


def stall(kernel, resources: int, wait_for: int):
  kernel.emit(TT.TTSTALLWAIT(int(resources), int(wait_for)))
  return kernel


def sem_wait(kernel, semaphore: int, condition: SemWait, resources: int):
  kernel.emit(TT.TTSEMWAIT(int(resources), Sem.mask(semaphore), int(condition)))
  return kernel


def sem_post(kernel, semaphore: int):
  kernel.emit(TT.TTSEMPOST(Sem.mask(semaphore)))
  return kernel


def sem_get(kernel, semaphore: int):
  kernel.emit(TT.TTSEMGET(Sem.mask(semaphore)))
  return kernel


def _sync(kernel, address):
  with kernel.scope():
    pointer, value = kernel.reg(2)
    kernel.li(pointer, address); kernel.sw(R.ZERO, pointer, 0); kernel.lw(value, pointer, 0)
    kernel.and_(R.ZERO, R.ZERO, value)
  return kernel


def sync(kernel): return _sync(kernel, TensixMMIO.PC_BUF_SYNC)
def mop_sync(kernel): return _sync(kernel, TensixMMIO.PC_BUF_MOP_SYNC)
