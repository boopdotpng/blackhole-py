#!/usr/bin/env python3
"""TRISC1-only SFPU instruction scaffold.

This is meant to be the boring, repeatable path for SFPU opcode bring-up:

  * no add1 dataflow
  * no BRISC/NCRISC/TRISC0/TRISC2 work
  * no pack, CB, NOC, or DRAM
  * hardcoded opcode specs by default
  * LReg semantic readback through SFPSTORE -> Dest -> L1

The first question each opcode answers is simple:

  * independent issue: how many cycles/op when there is no obvious RAW chain?
  * dependent chain: how many cycles/op when each op consumes the previous dst?
  * semantics: what are L0..L7 afterwards?

Potentially risky modes/macros are intentionally not in the default list.
"""

from __future__ import annotations

import argparse
import struct
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTNOP,
  TTSETRWC,
  TTSTALLWAIT,
  TTSFPABS,
  TTSFPADD,
  TTSFPADDI,
  TTSFPAND,
  TTSFPDIVP2,
  TTSFPEXEXP,
  TTSFPEXMAN,
  TTSFPIADD,
  TTSFPLZ,
  TTSFPMAD,
  TTSFPMOV,
  TTSFPMUL,
  TTSFPMULI,
  TTSFPNOT,
  TTSFPNOP,
  TTSFPOR,
  TTSFPSETEXP,
  TTSFPSETMAN,
  TTSFPSETSGN,
  TTSFPSHFT,
  TTSFPSTORE,
  TTSFPXOR,
  a2,
  a3,
  a4,
  a5,
  s2,
  s3,
  s4,
  t0,
  t1,
  zero,
)
from program import Dtype, Program  # noqa: E402
from ttk.math import Math  # noqa: E402
from ttk.sfpu import bf16_imm, sfpu_load_fp32_const  # noqa: E402
from ttk.tensix import MopCfg, Tensix, TensixMMIO, TensixStall, TensixWait  # noqa: E402


RESULT_BASE = 0x12D000
READBACK_BASE = RESULT_BASE + 0x1000
RESULT_MAGIC = 0x53464948  # "HIFS"
STATUS_STARTED = 0x1F500001
STATUS_DONE = 0x1F50D00D
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4

LREGS = 8
LANES = 32
ROWS_PER_LREG = 4
DEST_ROWS = LREGS * ROWS_PER_LREG
DEST_ROW_WORDS = 8
DEST_ROW_BYTES = DEST_ROW_WORDS * 4
READBACK_BYTES = DEST_ROWS * DEST_ROW_BYTES

SFPU_FMT_BF16 = 2
ADDR_MOD = 7
DBG_ARRAY_ID_DEST = 2
RISCV_DEBUG_REG_DBG_ARRAY_RD_EN = 0xFFB12060
RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD = 0xFFB12064
RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA = 0xFFB1206C

NOOP_MOP_CFG = MopCfg(loop_outer=1, loop_inner=1, template=[TTNOP()])

EmitFn = Callable[[object], int]


class SfpuInstrKernel(KernelBase, Tensix):
  pass


@dataclass(frozen=True)
class SfpuInstrSpec:
  name: str
  summary: str
  setup: EmitFn
  semantic: EmitFn
  dependent: EmitFn
  independent: EmitFn
  safe: bool = True


@dataclass(frozen=True)
class Record:
  name: str
  pattern: str
  iterations: int
  ops_per_iter: int
  cycles: int
  baseline_cycles: int

  @property
  def adjusted_cycles_per_op(self) -> float:
    denom = max(1, self.iterations * self.ops_per_iter)
    return (self.cycles - self.baseline_cycles) / denom


@dataclass(frozen=True)
class LatencySpec:
  name: str
  summary: str
  setup: EmitFn
  producer: EmitFn
  consumer: EmitFn
  old_value: float
  new_value: float
  safe: bool = True


def _emit_empty(_fw) -> int:
  return 0


def _setup_basic(fw) -> int:
  values = (1.0, 2.0, -3.0, 4.0, -0.5, 16.0, -16.0, 0.0)
  for lreg, value in enumerate(values):
    sfpu_load_fp32_const(fw, lreg, value)
  return 16


def _setup_bitwise(fw) -> int:
  values = (1.0, -0.0, 2.0, -2.0, -1.0, 4.0, -4.0, 1.0)
  for lreg, value in enumerate(values):
    sfpu_load_fp32_const(fw, lreg, value)
  return 16


def _nop(fw) -> int:
  fw.emit(TTSFPNOP())
  return 1


def _mov_semantic(fw) -> int:
  fw.emit(TTSFPMOV(0, 0, 7, 0))
  return 1


def _mov_dep(fw) -> int:
  fw.emit(TTSFPMOV(0, 0, 0, 0))
  return 1


def _mov_ind(fw) -> int:
  for dst in (0, 1, 2, 3, 4, 5, 6, 7):
    fw.emit(TTSFPMOV(0, 0, dst, 0))
  return 8


def _add_semantic(fw) -> int:
  fw.emit(TTSFPADD(10, 0, 1, 7, 0))
  return 1


def _add_dep(fw) -> int:
  fw.emit(TTSFPADD(10, 0, 1, 0, 0))
  return 1


def _add_ind(fw) -> int:
  for dst in (0, 2, 3, 4):
    fw.emit(TTSFPADD(10, 0, 1, dst, 0))
  return 4


def _mul_semantic(fw) -> int:
  fw.emit(TTSFPMUL(0, 1, 9, 7, 0))
  return 1


def _mul_dep(fw) -> int:
  fw.emit(TTSFPMUL(0, 1, 9, 0, 0))
  return 1


def _mul_ind(fw) -> int:
  for dst in (0, 2, 3, 4):
    fw.emit(TTSFPMUL(0, 1, 9, dst, 0))
  return 4


def _mad_semantic(fw) -> int:
  fw.emit(TTSFPMAD(0, 1, 2, 7, 0))
  return 1


def _mad_dep(fw) -> int:
  fw.emit(TTSFPMAD(0, 1, 2, 0, 0))
  return 1


def _mad_ind(fw) -> int:
  for dst in (0, 3, 4, 5):
    fw.emit(TTSFPMAD(0, 1, 2, dst, 0))
  return 4


def _addi_semantic(fw) -> int:
  fw.emit(TTSFPMOV(0, 0, 7, 0))
  fw.emit(TTSFPADDI(bf16_imm(1.0), 7, 0))
  return 2


def _addi_dep(fw) -> int:
  fw.emit(TTSFPADDI(bf16_imm(1.0), 0, 0))
  return 1


def _addi_ind(fw) -> int:
  for dst in (0, 1, 2, 3):
    fw.emit(TTSFPADDI(bf16_imm(1.0), dst, 0))
  return 4


def _muli_semantic(fw) -> int:
  fw.emit(TTSFPMOV(0, 0, 7, 0))
  fw.emit(TTSFPMULI(bf16_imm(2.0), 7, 0))
  return 2


def _muli_dep(fw) -> int:
  fw.emit(TTSFPMULI(bf16_imm(2.0), 0, 0))
  return 1


def _muli_ind(fw) -> int:
  for dst in (0, 1, 2, 3):
    fw.emit(TTSFPMULI(bf16_imm(2.0), dst, 0))
  return 4


def _abs_semantic(fw) -> int:
  fw.emit(TTSFPABS(0, 2, 7, 0))
  return 1


def _abs_dep(fw) -> int:
  fw.emit(TTSFPABS(0, 0, 0, 0))
  return 1


def _abs_ind(fw) -> int:
  for src, dst in ((0, 0), (2, 2), (4, 4), (6, 6)):
    fw.emit(TTSFPABS(0, src, dst, 0))
  return 4


def _setsgn_semantic(fw) -> int:
  fw.emit(TTSFPSETSGN(0, 2, 7, 0))
  return 1


def _setsgn_dep(fw) -> int:
  fw.emit(TTSFPSETSGN(0, 0, 0, 0))
  return 1


def _setsgn_ind(fw) -> int:
  for src, dst in ((0, 0), (2, 2), (4, 4), (6, 6)):
    fw.emit(TTSFPSETSGN(0, src, dst, 0))
  return 4


def _and_semantic(fw) -> int:
  fw.emit(TTSFPAND(0, 2, 7, 0))
  return 1


def _and_dep(fw) -> int:
  fw.emit(TTSFPAND(0, 2, 0, 0))
  return 1


def _and_ind(fw) -> int:
  for dst in (0, 3, 5, 7):
    fw.emit(TTSFPAND(0, 2, dst, 0))
  return 4


def _or_semantic(fw) -> int:
  fw.emit(TTSFPOR(0, 1, 7, 0))
  return 1


def _or_dep(fw) -> int:
  fw.emit(TTSFPOR(0, 1, 0, 0))
  return 1


def _or_ind(fw) -> int:
  for dst in (0, 2, 5, 7):
    fw.emit(TTSFPOR(0, 1, dst, 0))
  return 4


def _xor_semantic(fw) -> int:
  fw.emit(TTSFPXOR(0, 1, 7, 0))
  return 1


def _xor_dep(fw) -> int:
  fw.emit(TTSFPXOR(0, 1, 0, 0))
  return 1


def _xor_ind(fw) -> int:
  for dst in (0, 2, 5, 7):
    fw.emit(TTSFPXOR(0, 1, dst, 0))
  return 4


def _not_semantic(fw) -> int:
  fw.emit(TTSFPNOT(0, 0, 7, 0))
  return 1


def _not_dep(fw) -> int:
  fw.emit(TTSFPNOT(0, 0, 0, 0))
  return 1


def _not_ind(fw) -> int:
  for src, dst in ((0, 0), (2, 2), (5, 5), (7, 7)):
    fw.emit(TTSFPNOT(0, src, dst, 0))
  return 4


def _divp2_semantic(fw) -> int:
  fw.emit(TTSFPDIVP2(0xFFF, 1, 7, 1))
  return 1


def _divp2_dep(fw) -> int:
  fw.emit(TTSFPDIVP2(0xFFF, 0, 0, 1))
  return 1


def _divp2_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPDIVP2(0xFFF, src, dst, 1))
  return 4


def _setexp_semantic(fw) -> int:
  fw.emit(TTSFPSETEXP(128, 0, 7, 1))
  return 1


def _setexp_dep(fw) -> int:
  fw.emit(TTSFPSETEXP(128, 0, 0, 1))
  return 1


def _setexp_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPSETEXP(128, src, dst, 1))
  return 4


def _setman_semantic(fw) -> int:
  fw.emit(TTSFPSETMAN(0, 2, 7, 0))
  return 1


def _setman_dep(fw) -> int:
  fw.emit(TTSFPSETMAN(0, 0, 0, 0))
  return 1


def _setman_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPSETMAN(0, src, dst, 0))
  return 4


def _exexp_semantic(fw) -> int:
  fw.emit(TTSFPEXEXP(0, 1, 7, 0))
  return 1


def _exexp_dep(fw) -> int:
  fw.emit(TTSFPEXEXP(0, 0, 0, 0))
  return 1


def _exexp_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPEXEXP(0, src, dst, 0))
  return 4


def _exman_semantic(fw) -> int:
  fw.emit(TTSFPEXMAN(0, 1, 7, 0))
  return 1


def _exman_dep(fw) -> int:
  fw.emit(TTSFPEXMAN(0, 0, 0, 0))
  return 1


def _exman_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPEXMAN(0, src, dst, 0))
  return 4


def _iadd_semantic(fw) -> int:
  fw.emit(TTSFPIADD(1, 0, 7, 1))
  return 1


def _iadd_dep(fw) -> int:
  fw.emit(TTSFPIADD(1, 0, 0, 1))
  return 1


def _iadd_ind(fw) -> int:
  for dst in (0, 1, 2, 3):
    fw.emit(TTSFPIADD(1, dst, dst, 1))
  return 4


def _shft_semantic(fw) -> int:
  fw.emit(TTSFPSHFT(1, 0, 7, 5))
  return 1


def _shft_dep(fw) -> int:
  fw.emit(TTSFPSHFT(1, 0, 0, 5))
  return 1


def _shft_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPSHFT(1, src, dst, 5))
  return 4


def _lz_semantic(fw) -> int:
  fw.emit(TTSFPLZ(0, 0, 7, 0))
  return 1


def _lz_dep(fw) -> int:
  fw.emit(TTSFPLZ(0, 0, 0, 0))
  return 1


def _lz_ind(fw) -> int:
  for src, dst in ((0, 0), (1, 1), (2, 2), (3, 3)):
    fw.emit(TTSFPLZ(0, src, dst, 0))
  return 4


def _lat_consume_l2_plus_two(fw) -> int:
  fw.emit(TTSFPADD(10, 2, 1, 7, 0))
  return 1


def _lat_consume_l2_mov(fw) -> int:
  fw.emit(TTSFPMOV(0, 2, 7, 0))
  return 1


def _lat_consume_l3_plus_two(fw) -> int:
  fw.emit(TTSFPADD(10, 3, 1, 7, 0))
  return 1


def _lat_consume_l4_plus_two(fw) -> int:
  fw.emit(TTSFPADD(10, 4, 1, 7, 0))
  return 1


def _lat_mov_producer(fw) -> int:
  fw.emit(TTSFPMOV(0, 0, 2, 0))
  return 1


def _lat_add_producer(fw) -> int:
  fw.emit(TTSFPADD(10, 0, 1, 2, 0))
  return 1


def _lat_mul_producer(fw) -> int:
  fw.emit(TTSFPMUL(0, 1, 9, 2, 0))
  return 1


def _lat_mad_producer(fw) -> int:
  fw.emit(TTSFPMAD(0, 1, 2, 3, 0))
  return 1


def _lat_addi_producer(fw) -> int:
  fw.emit(TTSFPADDI(bf16_imm(4.0), 2, 0))
  return 1


def _lat_muli_producer(fw) -> int:
  fw.emit(TTSFPMULI(bf16_imm(-1.0), 2, 0))
  return 1


def _lat_abs_producer(fw) -> int:
  fw.emit(TTSFPABS(0, 2, 2, 0))
  return 1


def _lat_abs_float_producer(fw) -> int:
  fw.emit(TTSFPABS(0, 2, 2, 1))
  return 1


def _lat_setsgn_copy_producer(fw) -> int:
  fw.emit(TTSFPSETSGN(0, 2, 4, 0))
  return 1


def _lat_setsgn_pos_producer(fw) -> int:
  fw.emit(TTSFPSETSGN(0, 2, 4, 1))
  return 1


def _lat_setsgn_neg_producer(fw) -> int:
  fw.emit(TTSFPSETSGN(1, 2, 4, 1))
  return 1


def _lat_and_producer(fw) -> int:
  fw.emit(TTSFPAND(0, 0, 2, 0))
  return 1


def _lat_or_producer(fw) -> int:
  fw.emit(TTSFPOR(0, 1, 2, 0))
  return 1


def _lat_xor_producer(fw) -> int:
  fw.emit(TTSFPXOR(0, 1, 2, 0))
  return 1


def _lat_not_producer(fw) -> int:
  fw.emit(TTSFPNOT(0, 2, 2, 0))
  return 1


def _lat_divp2_producer(fw) -> int:
  fw.emit(TTSFPDIVP2(0xFFF, 2, 2, 1))
  return 1


def _lat_setexp_producer(fw) -> int:
  fw.emit(TTSFPSETEXP(128, 0, 2, 1))
  return 1


def _lat_setman_producer(fw) -> int:
  fw.emit(TTSFPSETMAN(0, 2, 4, 0))
  return 1


SPECS: dict[str, SfpuInstrSpec] = {
  "TTSFPNOP": SfpuInstrSpec("TTSFPNOP", "SFPU no-op", _setup_basic, _nop, _nop, _nop),
  "TTSFPMOV": SfpuInstrSpec("TTSFPMOV", "move LReg", _setup_basic, _mov_semantic, _mov_dep, _mov_ind),
  "TTSFPADD": SfpuInstrSpec("TTSFPADD", "fp add", _setup_basic, _add_semantic, _add_dep, _add_ind),
  "TTSFPMUL": SfpuInstrSpec("TTSFPMUL", "fp multiply", _setup_basic, _mul_semantic, _mul_dep, _mul_ind),
  "TTSFPMAD": SfpuInstrSpec("TTSFPMAD", "fp multiply-add", _setup_basic, _mad_semantic, _mad_dep, _mad_ind),
  "TTSFPADDI": SfpuInstrSpec("TTSFPADDI", "add bf16 immediate", _setup_basic, _addi_semantic, _addi_dep, _addi_ind),
  "TTSFPMULI": SfpuInstrSpec("TTSFPMULI", "multiply bf16 immediate", _setup_basic, _muli_semantic, _muli_dep, _muli_ind),
  "TTSFPABS": SfpuInstrSpec("TTSFPABS", "abs with instr_mod1=0 integer/two's-complement mode", _setup_basic, _abs_semantic, _abs_dep, _abs_ind),
  "TTSFPSETSGN": SfpuInstrSpec("TTSFPSETSGN", "copy existing destination sign onto source magnitude", _setup_basic, _setsgn_semantic, _setsgn_dep, _setsgn_ind),
  "TTSFPAND": SfpuInstrSpec("TTSFPAND", "bitwise AND, instr_mod1=0 destination-as-left-input mode", _setup_bitwise, _and_semantic, _and_dep, _and_ind, safe=False),
  "TTSFPOR": SfpuInstrSpec("TTSFPOR", "bitwise OR, instr_mod1=0 destination-as-left-input mode", _setup_bitwise, _or_semantic, _or_dep, _or_ind, safe=False),
  "TTSFPXOR": SfpuInstrSpec("TTSFPXOR", "bitwise XOR, instr_mod1=0 destination-as-left-input mode", _setup_bitwise, _xor_semantic, _xor_dep, _xor_ind, safe=False),
  "TTSFPNOT": SfpuInstrSpec("TTSFPNOT", "bitwise NOT of source LReg", _setup_bitwise, _not_semantic, _not_dep, _not_ind, safe=False),
  "TTSFPDIVP2": SfpuInstrSpec("TTSFPDIVP2", "adjust exponent by signed immediate; here divide by 2", _setup_basic, _divp2_semantic, _divp2_dep, _divp2_ind),
  "TTSFPSETEXP": SfpuInstrSpec("TTSFPSETEXP", "set exponent from immediate while preserving sign/mantissa", _setup_basic, _setexp_semantic, _setexp_dep, _setexp_ind),
  "TTSFPSETMAN": SfpuInstrSpec("TTSFPSETMAN", "copy mantissa from destination while taking sign/exponent from source", _setup_basic, _setman_semantic, _setman_dep, _setman_ind),
  "TTSFPEXEXP": SfpuInstrSpec("TTSFPEXEXP", "raw exponent extraction; BF16 semantic dump is not meaningful", _setup_basic, _exexp_semantic, _exexp_dep, _exexp_ind, safe=False),
  "TTSFPEXMAN": SfpuInstrSpec("TTSFPEXMAN", "raw mantissa extraction; BF16 semantic dump is not meaningful", _setup_basic, _exman_semantic, _exman_dep, _exman_ind, safe=False),
  "TTSFPIADD": SfpuInstrSpec("TTSFPIADD", "raw integer add; BF16 semantic dump is not meaningful", _setup_basic, _iadd_semantic, _iadd_dep, _iadd_ind, safe=False),
  "TTSFPSHFT": SfpuInstrSpec("TTSFPSHFT", "raw integer shift; BF16 semantic dump is not meaningful", _setup_basic, _shft_semantic, _shft_dep, _shft_ind, safe=False),
  "TTSFPLZ": SfpuInstrSpec("TTSFPLZ", "raw leading-zero count; BF16 semantic dump is not meaningful", _setup_basic, _lz_semantic, _lz_dep, _lz_ind, safe=False),
}

LATENCY_SPECS: dict[str, LatencySpec] = {
  "TTSFPMOV": LatencySpec(
    "TTSFPMOV", "producer MOV L0->L2; consumer L7=L2+L1", _setup_basic,
    _lat_mov_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=3.0,
  ),
  "TTSFPADD": LatencySpec(
    "TTSFPADD", "producer L2=L0+L1; consumer L7=L2+L1", _setup_basic,
    _lat_add_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=5.0,
  ),
  "TTSFPMUL": LatencySpec(
    "TTSFPMUL", "producer L2=L0*L1; consumer L7=L2+L1", _setup_basic,
    _lat_mul_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=4.0,
  ),
  "TTSFPMAD": LatencySpec(
    "TTSFPMAD", "producer L3=L0*L1+L2; consumer L7=L3+L1", _setup_basic,
    _lat_mad_producer, _lat_consume_l3_plus_two, old_value=6.0, new_value=1.0,
  ),
  "TTSFPADDI": LatencySpec(
    "TTSFPADDI", "producer L2=L2+4; consumer L7=L2+L1", _setup_basic,
    _lat_addi_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=3.0,
  ),
  "TTSFPMULI": LatencySpec(
    "TTSFPMULI", "producer L2=L2*(-1); consumer L7=L2+L1", _setup_basic,
    _lat_muli_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=5.0,
  ),
  "TTSFPABS": LatencySpec(
    "TTSFPABS", "alias for TTSFPABS_INT: producer L2=ABS mod1=0 integer abs on FP32(-3.0) bits; consumer L7=L2+L1", _setup_basic,
    _lat_abs_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=3.5,
  ),
  "TTSFPABS_INT": LatencySpec(
    "TTSFPABS_INT", "producer L2=ABS mod1=0 integer abs on FP32(-3.0) bits; consumer L7=L2+L1", _setup_basic,
    _lat_abs_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=3.5,
  ),
  "TTSFPABS_FLOAT": LatencySpec(
    "TTSFPABS_FLOAT", "producer L2=ABS mod1=1 float abs on -3.0; consumer L7=L2+L1", _setup_basic,
    _lat_abs_float_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=5.0,
  ),
  "TTSFPSETSGN_COPY": LatencySpec(
    "TTSFPSETSGN_COPY", "producer L4=sign(L4)|abs(L2) => -3.0; consumer L7=L4+L1", _setup_basic,
    _lat_setsgn_copy_producer, _lat_consume_l4_plus_two, old_value=1.5, new_value=-1.0,
  ),
  "TTSFPSETSGN_POS": LatencySpec(
    "TTSFPSETSGN_POS", "producer L4=+abs(L2) => +3.0; consumer L7=L4+L1", _setup_basic,
    _lat_setsgn_pos_producer, _lat_consume_l4_plus_two, old_value=1.5, new_value=5.0,
  ),
  "TTSFPSETSGN_NEG": LatencySpec(
    "TTSFPSETSGN_NEG", "producer L4=-abs(L2) => -3.0; consumer L7=L4+L1", _setup_basic,
    _lat_setsgn_neg_producer, _lat_consume_l4_plus_two, old_value=1.5, new_value=-1.0,
  ),
  "TTSFPAND": LatencySpec(
    "TTSFPAND", "producer L2=L2&L0 => +0.0; consumer MOV L2->L7", _setup_bitwise,
    _lat_and_producer, _lat_consume_l2_mov, old_value=2.0, new_value=0.0, safe=False,
  ),
  "TTSFPOR": LatencySpec(
    "TTSFPOR", "producer L2=L2|L1 => -2.0; consumer MOV L2->L7", _setup_bitwise,
    _lat_or_producer, _lat_consume_l2_mov, old_value=2.0, new_value=-2.0, safe=False,
  ),
  "TTSFPXOR": LatencySpec(
    "TTSFPXOR", "producer L2=L2^L1 => -2.0; consumer MOV L2->L7", _setup_bitwise,
    _lat_xor_producer, _lat_consume_l2_mov, old_value=2.0, new_value=-2.0, safe=False,
  ),
  "TTSFPNOT": LatencySpec(
    "TTSFPNOT", "producer L2=~L2 => approximately -2.0; consumer MOV L2->L7", _setup_bitwise,
    _lat_not_producer, _lat_consume_l2_mov, old_value=2.0, new_value=-1.9921875, safe=False,
  ),
  "TTSFPDIVP2": LatencySpec(
    "TTSFPDIVP2", "producer L2=L2/2 via exponent decrement; consumer L7=L2+L1", _setup_basic,
    _lat_divp2_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=0.5, safe=False,
  ),
  "TTSFPSETEXP": LatencySpec(
    "TTSFPSETEXP", "producer L2=setexp(L0, 128) => 2.0; consumer L7=L2+L1", _setup_basic,
    _lat_setexp_producer, _lat_consume_l2_plus_two, old_value=-1.0, new_value=4.0,
  ),
  "TTSFPSETMAN": LatencySpec(
    "TTSFPSETMAN", "producer L4=sign/exp(L2)|mantissa(L4) => -2.0; consumer L7=L4+L1", _setup_basic,
    _lat_setman_producer, _lat_consume_l4_plus_two, old_value=1.5, new_value=0.0,
  ),
}


def bf16_to_f32(bits: np.ndarray) -> np.ndarray:
  return (bits.astype("<u4") << 16).view("<f4")


def dst_decode_bf16(encoded: np.ndarray) -> np.ndarray:
  x = encoded.astype("<u2")
  exp = x & np.uint16(0x00FF)
  man = (x >> np.uint16(8)) & np.uint16(0x007F)
  sign = x & np.uint16(0x8000)
  return (sign | (exp << np.uint16(7)) | man).astype("<u2")


def result_size(spec_count: int) -> int:
  return HEADER_SIZE + spec_count * 2 * RECORD_SIZE


def debug_ranges(spec_count: int) -> tuple[tuple[int, int], ...]:
  return (
    (RESULT_BASE, result_size(spec_count)),
    (READBACK_BASE, READBACK_BYTES),
  )


def emit_header(fw: KernelBase, *, status: int, spec_count: int, iterations: int):
  values = (
    RESULT_MAGIC,
    1,
    status,
    spec_count,
    iterations,
    RESULT_BASE,
    result_size(spec_count),
    READBACK_BASE,
    READBACK_BYTES,
    LREGS,
    LANES,
    0,
    0,
    0,
    0,
    0,
  )
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  record_id: int,
  op_index: int,
  pattern_id: int,
  iterations: int,
  ops_per_iter: int,
  baseline_cycles,
  start_lo,
  end_lo,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE + record_id * RECORD_SIZE)
  values = (0x53464952, record_id, op_index, pattern_id, iterations, ops_per_iter)
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  fw.sw(start_lo, s2, 6 * 4)
  fw.sw(end_lo, s2, 7 * 4)
  fw.sub(t0, end_lo, start_lo)
  fw.sw(t0, s2, 8 * 4)
  fw.sw(baseline_cycles, s2, 9 * 4)
  for off in range(10, RECORD_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_drain(fw: SfpuInstrKernel):
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.SFPU))
  return fw.tensix_sync(1, tmp=t1)


def emit_lregs_to_l1(fw: SfpuInstrKernel):
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  for lreg in range(LREGS):
    fw.emit(TTSFPSTORE(lreg, SFPU_FMT_BF16, ADDR_MOD, lreg * ROWS_PER_LREG))
  fw.emit(TTSFPNOP())
  emit_drain(fw)
  return emit_dest_rows_to_l1(fw)


def emit_dest_rows_to_l1(fw: SfpuInstrKernel):
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 1)
  for row in range(DEST_ROWS):
    for sel in range(DEST_ROW_WORDS):
      cmd = (DBG_ARRAY_ID_DEST << 16) | (sel << 12) | row
      fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, cmd)
      fw.delay_cycles(5)
      fw.read32(t1, RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA)
      fw.write32(READBACK_BASE + row * DEST_ROW_BYTES + sel * 4, t1)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 0)
  return fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)


def emit_store_l7_to_gap_band(fw: SfpuInstrKernel, gap: int):
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  fw.emit(TTSFPSTORE(7, SFPU_FMT_BF16, ADDR_MOD, gap * ROWS_PER_LREG))
  fw.emit(TTSFPNOP())
  return emit_drain(fw)


def emit_loop(fw: SfpuInstrKernel, emit_body: EmitFn, *, iterations: int):
  fw.li(s4, iterations)
  loop = fw._new_label("sfpu_instr_loop")
  done = fw._new_label("sfpu_instr_loop_done")
  fw.label(loop)
  fw.beq(s4, zero, done)
  emit_body(fw)
  fw.addi(s4, s4, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def build_kernel(specs: list[SfpuInstrSpec], *, iterations: int, semantic_op: SfpuInstrSpec | None) -> SfpuInstrKernel:
  fw = SfpuInstrKernel()
  fw.math = Math(fw)
  fw.data = {"dest_offset_id": 0xFFB00080}

  emit_header(fw, status=STATUS_STARTED, spec_count=len(specs), iterations=iterations)
  fw.zero_words(READBACK_BASE, READBACK_BYTES // 4)
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=NOOP_MOP_CFG)
  emit_drain(fw)

  harness.read_wall_clock(fw, a2, a3)
  emit_loop(fw, _emit_empty, iterations=iterations)
  emit_drain(fw)
  harness.read_wall_clock(fw, a4, a5)
  fw.sub(s3, a4, a2)

  record_id = 0
  for op_index, spec in enumerate(specs):
    for pattern_id, emit_body in enumerate((spec.dependent, spec.independent)):
      spec.setup(fw)
      emit_drain(fw)
      harness.read_wall_clock(fw, a2, a3)
      emit_loop(fw, emit_body, iterations=iterations)
      emit_drain(fw)
      harness.read_wall_clock(fw, a4, a5)
      emit_record(
        fw,
        record_id=record_id,
        op_index=op_index,
        pattern_id=pattern_id,
        iterations=iterations,
        ops_per_iter=emit_body(_CountingEmitter()),
        baseline_cycles=s3,
        start_lo=a2,
        end_lo=a4,
      )
      record_id += 1

  if semantic_op is not None:
    semantic_op.setup(fw)
    semantic_op.semantic(fw)
    emit_lregs_to_l1(fw)

  emit_header(fw, status=STATUS_DONE, spec_count=len(specs), iterations=iterations)
  return fw.ret()


class _CountingEmitter:
  def emit(self, _inst):
    return None


def build_program(specs: list[SfpuInstrSpec], *, iterations: int, semantic_op: SfpuInstrSpec | None) -> Program:
  empty = KernelBase()
  prog = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=empty,
    trisc1=build_kernel(specs, iterations=iterations, semantic_op=semantic_op),
    trisc2=empty,
    num_cores=1,
  )
  prog.name = "microbench_sfpu_instr"
  return prog


def build_latency_kernel(spec: LatencySpec, *, min_gap: int, max_gap: int) -> SfpuInstrKernel:
  fw = SfpuInstrKernel()
  fw.math = Math(fw)
  fw.data = {"dest_offset_id": 0xFFB00080}

  gap_count = max_gap - min_gap + 1
  emit_header(fw, status=STATUS_STARTED, spec_count=0, iterations=gap_count)
  fw.zero_words(READBACK_BASE, READBACK_BYTES // 4)
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=NOOP_MOP_CFG)
  emit_drain(fw)

  for gap_index, gap in enumerate(range(min_gap, max_gap + 1)):
    spec.setup(fw)
    emit_drain(fw)
    spec.producer(fw)
    for _ in range(gap):
      fw.emit(TTSFPNOP())
    spec.consumer(fw)
    emit_drain(fw)
    emit_store_l7_to_gap_band(fw, gap_index)

  emit_dest_rows_to_l1(fw)
  emit_header(fw, status=STATUS_DONE, spec_count=0, iterations=gap_count)
  return fw.ret()


def build_latency_program(spec: LatencySpec, *, min_gap: int, max_gap: int) -> Program:
  empty = KernelBase()
  prog = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=empty,
    trisc1=build_latency_kernel(spec, min_gap=min_gap, max_gap=max_gap),
    trisc2=empty,
    num_cores=1,
  )
  prog.name = f"microbench_sfpu_latency_{spec.name}"
  return prog


def parse_records(blob: bytes, specs: list[SfpuInstrSpec]) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[2] != STATUS_DONE:
    raise RuntimeError(f"kernel did not finish, status=0x{header[2]:08x}")
  records: list[Record] = []
  for record_id in range(len(specs) * 2):
    off = HEADER_SIZE + record_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != 0x53464952:
      raise RuntimeError(f"record {record_id}: bad magic 0x{words[0]:08x}")
    pattern = "dependent" if words[3] == 0 else "independent"
    records.append(Record(
      name=specs[words[2]].name,
      pattern=pattern,
      iterations=words[4],
      ops_per_iter=words[5],
      cycles=words[8],
      baseline_cycles=words[9],
    ))
  return records


def decode_lreg_lanes(raw: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  words = np.frombuffer(raw, dtype="<u4").reshape(DEST_ROWS, DEST_ROW_WORDS)
  halfwords = words.view("<u2").reshape(DEST_ROWS, DEST_ROW_WORDS * 2)
  encoded = np.empty((LREGS, LANES), dtype="<u2")
  for lreg in range(LREGS):
    base = lreg * ROWS_PER_LREG
    for lane in range(LANES):
      row = base + lane // 8
      col = (lane & 7) * 2
      encoded[lreg, lane] = halfwords[row, col]
  bits = dst_decode_bf16(encoded)
  return encoded, bits, bf16_to_f32(bits)


def clear_results(device: Device, core: tuple[int, int], spec_count: int):
  harness.clear_window(device, core, debug_ranges(spec_count))


def run_once(device: Device, core: tuple[int, int], specs: list[SfpuInstrSpec], *, iterations: int, semantic_op: SfpuInstrSpec | None):
  clear_results(device, core, len(specs))
  device.run(build_program(specs, iterations=iterations, semantic_op=semantic_op))
  result_blob = harness.read_window(device, core, RESULT_BASE, result_size(len(specs)))
  lreg_blob = None
  if semantic_op is not None:
    lreg_blob = harness.read_window(device, core, READBACK_BASE, READBACK_BYTES)
  return parse_records(result_blob, specs), lreg_blob


def run_latency(device: Device, core: tuple[int, int], spec: LatencySpec, *, min_gap: int, max_gap: int) -> bytes:
  clear_results(device, core, 0)
  device.run(build_latency_program(spec, min_gap=min_gap, max_gap=max_gap))
  header_blob = harness.read_window(device, core, RESULT_BASE, result_size(0))
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, header_blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[2] != STATUS_DONE:
    raise RuntimeError(f"latency kernel did not finish, status=0x{header[2]:08x}")
  return harness.read_window(device, core, READBACK_BASE, READBACK_BYTES)


def format_records(records: list[Record]) -> str:
  lines = [
    "| op | pattern | ops/iter | raw cyc/iter | adj cyc/op | baseline/iter |",
    "|---|---|---:|---:|---:|---:|",
  ]
  for record in records:
    cycles_per_iter = record.cycles / max(1, record.iterations)
    baseline_per_iter = record.baseline_cycles / max(1, record.iterations)
    lines.append(
      f"| {record.name} | {record.pattern} | {record.ops_per_iter} | "
      f"{cycles_per_iter:.3f} | {record.adjusted_cycles_per_op:.3f} | {baseline_per_iter:.3f} |"
    )
  return "\n".join(lines)


def print_lregs(raw: bytes, *, full: bool):
  encoded, bits, vals = decode_lreg_lanes(raw)
  shown = LANES if full else 8
  print("Semantic LReg dump after selected op")
  for lreg in range(LREGS):
    val_text = ", ".join(f"{float(v):.7g}" for v in vals[lreg, :shown])
    bit_text = ", ".join(f"{int(b):04x}" for b in bits[lreg, :shown])
    dst_text = ", ".join(f"{int(b):04x}" for b in encoded[lreg, :shown])
    suffix = "" if full else ", ..."
    print(f"L{lreg}: values=[{val_text}{suffix}] bf16=[{bit_text}{suffix}] dst16=[{dst_text}{suffix}]")


def print_latency(raw: bytes, spec: LatencySpec, *, min_gap: int, max_gap: int):
  _encoded, bits, vals = decode_lreg_lanes(raw)
  print(f"Latency sweep for {spec.name}")
  print(f"  {spec.summary}")
  print(f"  old={spec.old_value:.7g} new={spec.new_value:.7g}")
  print("| gap SFPNOPs | observed | bf16 | classification |")
  print("|---:|---:|---:|---|")
  first_new = None
  for gap_index, gap in enumerate(range(min_gap, max_gap + 1)):
    observed = float(vals[gap_index, 0])
    bit = int(bits[gap_index, 0])
    if np.isclose(observed, spec.new_value, rtol=0, atol=0):
      classification = "new"
      if first_new is None:
        first_new = gap
    elif np.isclose(observed, spec.old_value, rtol=0, atol=0):
      classification = "old"
    else:
      classification = "other"
    print(f"| {gap} | {observed:.7g} | 0x{bit:04x} | {classification} |")
  if first_new is None:
    print("minimum gap: not found")
  else:
    print(f"minimum gap: {first_new} SFPNOP issue slot(s) between producer and consumer")


def select_specs(text: str | None, *, all_ops: bool, risky: bool) -> list[SfpuInstrSpec]:
  if text:
    names = [part.strip() for part in text.split(",") if part.strip()]
  elif all_ops:
    names = [name for name, spec in SPECS.items() if spec.safe or risky]
  else:
    names = ["TTSFPNOP", "TTSFPMOV", "TTSFPADD", "TTSFPMUL"]
  unknown = sorted(set(names) - set(SPECS))
  if unknown:
    raise ValueError(f"unknown --ops entries: {', '.join(unknown)}")
  unsafe = [name for name in names if not SPECS[name].safe]
  if unsafe and not risky:
    raise ValueError(f"risky --ops entries require --risky: {', '.join(unsafe)}")
  return [SPECS[name] for name in names]


def print_inventory():
  print("implemented opcode specs:")
  for spec in SPECS.values():
    tag = "" if spec.safe else " [risky]"
    print(f"  {spec.name}{tag}: {spec.summary}")
  print("\nimplemented RAW-latency probes:")
  for spec in LATENCY_SPECS.values():
    tag = "" if spec.safe else " [risky]"
    print(f"  {spec.name}{tag}: {spec.summary}")
  print("\nnot in scaffold yet: load/store mode matrix, LUTs, CC stack/enable ops, stochastic rounding, loadmacro, casts/config.")


def build_only(
  specs: list[SfpuInstrSpec],
  *,
  iterations: int,
  semantic_op: SfpuInstrSpec | None,
  latency_spec: LatencySpec | None,
  min_gap: int,
  max_gap: int,
):
  prog = build_latency_program(latency_spec, min_gap=min_gap, max_gap=max_gap) if latency_spec else build_program(
    specs, iterations=iterations, semantic_op=semantic_op,
  )
  trisc1_bytes = sum(len(seg.data) for seg in prog.trisc1.compile())
  print(f"build ok: specs={len(specs)} iterations={iterations} trisc1_bytes={trisc1_bytes}")


def main() -> int:
  parser = argparse.ArgumentParser(description="TRISC1-only SFPU instruction microbench scaffold.")
  parser.add_argument("--ops", default=None, help=f"comma-separated ops; known: {','.join(SPECS)}")
  parser.add_argument("--all", action="store_true", help="run all implemented safe specs")
  parser.add_argument("--iters", type=int, default=4096)
  parser.add_argument("--repeat", type=int, default=1)
  parser.add_argument("--semantic", default=None, help="also dump LRegs after this single op")
  parser.add_argument("--latency", default=None, help=f"run RAW latency sweep for one op; known: {','.join(LATENCY_SPECS)}")
  parser.add_argument("--min-gap", type=int, default=1, help="minimum SFPNOP gap for --latency; gap 0 can be risky")
  parser.add_argument("--max-gap", type=int, default=5, help="maximum SFPNOP gap for --latency; max 7")
  parser.add_argument("--gap", type=int, default=None, help="run exactly one SFPNOP gap for --latency")
  parser.add_argument("--full", action="store_true", help="print all 32 lanes for semantic dump")
  parser.add_argument("--build-only", action="store_true")
  parser.add_argument("--list", action="store_true")
  parser.add_argument("--risky", action="store_true", help="allow probes that have timed out or are not yet known-safe")
  parser.add_argument("--core", type=harness.parse_core, default=None)
  args = parser.parse_args()

  if args.list:
    print_inventory()
    return 0
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.repeat <= 0:
    raise ValueError("--repeat must be positive")
  if args.gap is not None:
    args.min_gap = args.gap
    args.max_gap = args.gap
  if not 0 <= args.min_gap <= args.max_gap < LREGS:
    raise ValueError(f"--min-gap/--max-gap must satisfy 0 <= min <= max <= {LREGS - 1}")
  if (args.max_gap - args.min_gap + 1) > LREGS:
    raise ValueError(f"--max-gap must be in [0, {LREGS - 1}]")

  specs = select_specs(args.ops, all_ops=args.all, risky=args.risky)
  semantic_op = None
  if args.semantic:
    if args.semantic not in SPECS:
      raise ValueError(f"unknown --semantic op {args.semantic!r}")
    semantic_op = SPECS[args.semantic]
  latency_spec = None
  if args.latency:
    if args.latency not in LATENCY_SPECS:
      raise ValueError(f"unknown --latency op {args.latency!r}")
    latency_spec = LATENCY_SPECS[args.latency]
    if not latency_spec.safe and not args.risky:
      raise ValueError(f"risky --latency op {args.latency!r} requires --risky")

  if args.build_only:
    build_only(
      specs,
      iterations=args.iters,
      semantic_op=semantic_op,
      latency_spec=latency_spec,
      min_gap=args.min_gap,
      max_gap=args.max_gap,
    )
    return 0

  if latency_spec is not None:
    with harness.open_device() as device:
      core = args.core or device.cores[0]
      for rep in range(args.repeat):
        raw = run_latency(device, core, latency_spec, min_gap=args.min_gap, max_gap=args.max_gap)
        print(f"repeat {rep + 1}/{args.repeat}")
        print_latency(raw, latency_spec, min_gap=args.min_gap, max_gap=args.max_gap)
    return 0

  all_records: list[Record] = []
  last_lregs = None
  with harness.open_device() as device:
    core = args.core or device.cores[0]
    for rep in range(args.repeat):
      records, lregs = run_once(device, core, specs, iterations=args.iters, semantic_op=semantic_op)
      all_records.extend(records)
      last_lregs = lregs
      print(f"repeat {rep + 1}/{args.repeat}")
      print(format_records(records))

  if args.repeat > 1:
    print("\nall repeats")
    print(format_records(all_records))
  if last_lregs is not None:
    print()
    print_lregs(last_lregs, full=args.full)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
