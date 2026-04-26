from __future__ import annotations

from dataclasses import dataclass

from .resources import Resource


@dataclass(frozen=True)
class OpTiming:
  unit: Resource
  latency: int
  issue_interval: int = 1
  deterministic: bool = True
  note: str = ""


RV_DEFAULT = OpTiming(Resource.RV_EX, 1)

RV_TIMING = {
  "MUL": OpTiming(Resource.RV_EX, 2, note="EX1+EX2"),
  "MULH": OpTiming(Resource.RV_EX, 2, note="EX1+EX2"),
  "MULHSU": OpTiming(Resource.RV_EX, 2, note="EX1+EX2"),
  "MULHU": OpTiming(Resource.RV_EX, 2, note="EX1+EX2"),
  "DIV": OpTiming(Resource.RV_EX, 8, deterministic=False, note="docs: 2 fast path, 6-33 otherwise"),
  "DIVU": OpTiming(Resource.RV_EX, 8, deterministic=False, note="docs: 2 fast path, 6-33 otherwise"),
  "REM": OpTiming(Resource.RV_EX, 8, deterministic=False, note="docs: 2 fast path, 6-33 otherwise"),
  "REMU": OpTiming(Resource.RV_EX, 8, deterministic=False, note="docs: 2 fast path, 6-33 otherwise"),
}


TENSIX_DEFAULT_BY_UNIT = {
  Resource.TENSIX_SYNC: OpTiming(Resource.TENSIX_SYNC, 1),
  Resource.TENSIX_CFG: OpTiming(Resource.TENSIX_CFG, 1),
  Resource.TENSIX_THCON: OpTiming(Resource.TENSIX_THCON, 1),
  Resource.TENSIX_UNPACK: OpTiming(Resource.TENSIX_UNPACK, 2, note="UNPACR uncompressed setup minimum"),
  Resource.TENSIX_MATH: OpTiming(Resource.TENSIX_MATH, 1),
  Resource.TENSIX_SFPU: OpTiming(Resource.TENSIX_SFPU, 1),
  Resource.TENSIX_PACK: OpTiming(Resource.TENSIX_PACK, 1),
  Resource.TENSIX_MOVER: OpTiming(Resource.TENSIX_MOVER, 1),
}


TENSIX_TIMING = {
  # Sync unit
  "ATGETM": OpTiming(Resource.TENSIX_SYNC, 1, deterministic=False, note="contention can add 0-2 cycles"),
  "ATRELM": OpTiming(Resource.TENSIX_SYNC, 1),
  "STALLWAIT": OpTiming(Resource.TENSIX_SYNC, 1, note="plus wait-gate one-cycle release lag"),
  "SEMINIT": OpTiming(Resource.TENSIX_SYNC, 1),
  "SEMPOST": OpTiming(Resource.TENSIX_SYNC, 1),
  "SEMGET": OpTiming(Resource.TENSIX_SYNC, 1),
  "SEMWAIT": OpTiming(Resource.TENSIX_SYNC, 1, note="plus wait-gate one-cycle release lag"),
  "STREAMWAIT": OpTiming(Resource.TENSIX_SYNC, 1, note="stream visibility can add delay"),

  # Configuration unit
  "SETC16": OpTiming(Resource.TENSIX_CFG, 1, note="ThreadConfig group: up to 1/thread/cycle"),
  "WRCFG": OpTiming(Resource.TENSIX_CFG, 2),
  "WRCFG32": OpTiming(Resource.TENSIX_CFG, 2),
  "RDCFG": OpTiming(Resource.TENSIX_CFG, 2, deterministic=False, note=">=2 plus GPR contention"),
  "RMWCIB0": OpTiming(Resource.TENSIX_CFG, 1),
  "RMWCIB1": OpTiming(Resource.TENSIX_CFG, 1),
  "RMWCIB2": OpTiming(Resource.TENSIX_CFG, 1),
  "RMWCIB3": OpTiming(Resource.TENSIX_CFG, 1),
  "CFGSHIFTMASK": OpTiming(Resource.TENSIX_CFG, 2, issue_interval=2, note="not pipelined"),
  "STREAMWRCFG": OpTiming(Resource.TENSIX_CFG, 5, deterministic=False, note=">=5 plus NoC overlay contention"),
  "REG2FLOP": OpTiming(Resource.TENSIX_CFG, 2, deterministic=False, note="usually 2"),

  # Scalar / ThCon
  "SETDMAREG": OpTiming(Resource.TENSIX_THCON, 1),
  "ADDDMAREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note="3 or 4 depending GPR grouping"),
  "MULDMAREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note="3 or 4 depending GPR grouping"),
  "BITWOPDMAREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note="3 or 4 depending GPR grouping"),
  "SHIFTDMAREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note="3 or 4 depending GPR grouping"),
  "CMPDMAREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note="3 or 4 depending GPR grouping"),
  "STOREREG": OpTiming(Resource.TENSIX_THCON, 3, deterministic=False, note=">=3 if memory busy"),
  "FLUSHDMA": OpTiming(Resource.TENSIX_THCON, 2, deterministic=False, note=">=2 until selected conditions clear"),

  # Unpacker
  "UNPACR": OpTiming(Resource.TENSIX_UNPACK, 2, deterministic=False, note="2-cycle uncompressed setup plus format drain"),
  "UNPACR_NOP": OpTiming(Resource.TENSIX_UNPACK, 1),

  # Matrix / FPU. MVMUL is set to 16 per project calibration.
  "MVMUL": OpTiming(Resource.TENSIX_MATH, 16),
  "DOTPV": OpTiming(Resource.TENSIX_MATH, 5),
  "GAPOOL": OpTiming(Resource.TENSIX_MATH, 5),
  "ELWADD": OpTiming(Resource.TENSIX_MATH, 5),
  "GMPOOL": OpTiming(Resource.TENSIX_MATH, 5),
  "ZEROACC": OpTiming(Resource.TENSIX_MATH, 1),
  "ZEROSRC": OpTiming(Resource.TENSIX_MATH, 1),
  "TRNSPSRCB": OpTiming(Resource.TENSIX_MATH, 1),
  "SHIFTXA": OpTiming(Resource.TENSIX_MATH, 1),
  "SHIFTXB": OpTiming(Resource.TENSIX_MATH, 2, issue_interval=2),
  "SETRWC": OpTiming(Resource.TENSIX_MATH, 1),
  "INCRWC": OpTiming(Resource.TENSIX_MATH, 1),
  "CLEARDVALID": OpTiming(Resource.TENSIX_MATH, 1),
  "MOVD2A": OpTiming(Resource.TENSIX_MATH, 2),
  "MOVA2D": OpTiming(Resource.TENSIX_MATH, 4),
  "MOVB2D": OpTiming(Resource.TENSIX_MATH, 4),
  "MOVB2A": OpTiming(Resource.TENSIX_MATH, 4),
  "MOVD2B": OpTiming(Resource.TENSIX_MATH, 4),

  # SFPU 2-cycle group
  "SFPADDI": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPADD": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPMAD": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPMUL": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPMULI": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPLUT": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPLUTFP32": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPMUL24": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPSWAP": OpTiming(Resource.TENSIX_SFPU, 2),
  "SFPSHFT2": OpTiming(Resource.TENSIX_SFPU, 2),

  # Packer / mover
  "PACR": OpTiming(Resource.TENSIX_PACK, 1, deterministic=False, note="accept 1/cycle; completion format-dependent"),
  "XMOV": OpTiming(Resource.TENSIX_MOVER, 1, deterministic=False, note="1 cycle once mover can start"),
}


def rv_timing(name: str) -> OpTiming:
  return RV_TIMING.get(name, RV_DEFAULT)


def tensix_timing(name: str, fallback_unit: Resource) -> OpTiming:
  return TENSIX_TIMING.get(name, TENSIX_DEFAULT_BY_UNIT.get(fallback_unit, OpTiming(fallback_unit, 1)))
