# =============================================================================
# Public surface of the tensix package. The real entry point is
# TensixCoprocessor in coprocessor.py; everything else is re-exported here
# for tests that poke individual units / helpers directly.
# =============================================================================

from .state import (
  SrcBank, SrcRegFile, DestRegFile,
  RWCState, AddrModDescriptor, AddrModState,
  ADCCounter, ADCChannel, ADCUnit, ADCState,
  GPRFile, Semaphores,
)
from .frontend import (
  InstructionFIFO, MOPExpander, ReplayExpander, WaitGate, TensixThread,
  _is_nop, _instruction_block_bits,
  STALL_TDMA, STALL_SYNC, STALL_PACK, STALL_UNPACK, STALL_XMOV,
  STALL_THCON, STALL_MATH, STALL_CFG, STALL_SFPU, STALL_THREAD,
  COND_THCON, COND_UNPACK0, COND_UNPACK1, COND_PACK0, COND_MATH,
  COND_SRCA_CLR, COND_SRCB_CLR, COND_SRCA_VLD, COND_SRCB_VLD,
  COND_XMOV, COND_TRISC_CFG, COND_SFPU, COND_CFGEXU,
)
from .thcon import ConfigUnit, ScalarUnit
from .sync import SyncUnit, MutexSet
from .math import (
  FPU, SFPU,
  _19bit_to_float, _float_to_19bit, _dest_to_float, _float_to_dest,
  _NEG_INF_19BIT,
  _to_float, _to_bits, _sign, _exp, _mant, _is_neg,
  _bf16_to_fp32, _fp16_to_fp32,
  POS_INF, NEG_INF, CONST_0P8363, CONST_ONE,
)
from .unpack import Unpacker, _clear_src_bank
from .pack import Packer
from .coprocessor import TensixCoprocessor, HardwareState
from . import formats
from . import cfg_layout
