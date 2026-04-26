# =============================================================================
# Public surface for functional Tensix units and helpers.  The cycle-aware
# frontend lives in emu.tensix_core.
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
from .unpack import (
  Unpacker, UnpackerState, _clear_src_bank,
  # Format conversion functions and register-layout helpers (used by tests)
  _write_src_tf32, _write_src_bf16, _write_src_fp16,
  _write_dst_bf16, _write_dst_fp32, _write_dst_fp16,
  _bfp8_to_bf16, _bfp8a_to_fp16,
  _format_conversion,
  # DataFormat constants (re-exported for test convenience)
  FMT_FP32, FMT_FP16, FMT_BF16, FMT_TF32,
  FMT_BFP8, FMT_BFP8A, FMT_BFP4, FMT_BFP4A, FMT_BFP2, FMT_BFP2A,
  FMT_FP8, FMT_INT8, FMT_INT16, FMT_INT32,
  # Config address constants (used by test setup helpers)
  _THCON_SEC_BASE, _UNP_ADDR_CTRL_XY, _UNP_ADDR_CTRL_ZW, _UNP_BASE_REG_1,
)
from .pack import Packer
from .mover import Mover
from .tdma import TDMA
from . import formats
from . import cfg_layout
