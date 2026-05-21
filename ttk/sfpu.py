from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import Enum

from dsl import (
  TTINCRWC,
  TTSETRWC,
  TTSFPADD,
  TTSFPLOAD,
  TTSFPLOADI,
  TTSFPSTORE,
  a5,
  t0,
  t1,
  zero,
)
from ttk.tensix import TensixRegs


# Semantic SFPU tile helpers. These intentionally describe the operation first
# and leave replay/MOP compression as a later lowering choice.
class SfpuScalarOp(Enum):
  ADD = "add"


@dataclass(frozen=True)
class SfpuTileWalk:
  faces: int = 4
  groups_per_face: int = 8
  load_store_addr_mod: int = 7
  face_advance: int = 4


def fp32_bits(value: float) -> int:
  return struct.unpack("<I", struct.pack("<f", value))[0]


def _tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


def write_tensix_instr_word(fw, word: int | object, *, tmp_addr=t0, tmp_val=t1):
  fw.write32(TensixRegs.INSTRN_BUF_BASE, _tt_raw(word), tmp_addr=tmp_addr, tmp_val=tmp_val)


def load_lreg_fp32(fw, lreg: int, bits: int, *, tmp_addr=t0, tmp_val=t1):
  write_tensix_instr_word(fw, TTSFPLOADI(lreg, 10, bits & 0xFFFF), tmp_addr=tmp_addr, tmp_val=tmp_val)
  write_tensix_instr_word(fw, TTSFPLOADI(lreg, 8, bits >> 16), tmp_addr=tmp_addr, tmp_val=tmp_val)


def scalar_add_iteration(
  *,
  value_lreg: int = 0,
  scalar_lreg: int = 1,
  dst_lreg: int = 0,
  addr_mod: int = 7,
) -> tuple[object, ...]:
  return (
    TTSFPLOAD(value_lreg, 0, addr_mod, 0),
    TTSFPADD(10, value_lreg, scalar_lreg, dst_lreg, 0),
    TTSFPSTORE(dst_lreg, 0, addr_mod, 0),
    TTINCRWC(0, 2, 0, 0),
  )


def emit_scalar_add_face(fw, groups: int = 8, *, loop_reg=a5, walk: SfpuTileWalk = SfpuTileWalk()):
  loop = fw._new_label("sfpu_scalar_add")
  done = fw._new_label("sfpu_scalar_add_done")
  fw.li(loop_reg, groups)
  fw.label(loop)
  fw.beq(loop_reg, zero, done)
  fw.emit(*scalar_add_iteration(addr_mod=walk.load_store_addr_mod))
  fw.addi(loop_reg, loop_reg, -1)
  fw.j(loop)
  fw.label(done)


def emit_traced_scalar_add_face(
  fw,
  groups: int = 8,
  *,
  loop_reg=a5,
  walk: SfpuTileWalk = SfpuTileWalk(),
  breadcrumb_addr: int,
  breadcrumb_prefix: str,
):
  loop = fw._new_label("sfpu_scalar_add")
  done = fw._new_label("sfpu_scalar_add_done")
  fw.li(loop_reg, groups)
  fw.label(loop)
  fw.beq(loop_reg, zero, done)
  load, add, store, incr = scalar_add_iteration(addr_mod=walk.load_store_addr_mod)
  fw.emit(load)
  fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:load")
  fw.emit(add)
  fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:add")
  fw.emit(store)
  fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:store")
  fw.emit(incr)
  fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:incrwc")
  fw.addi(loop_reg, loop_reg, -1)
  fw.j(loop)
  fw.label(done)


def emit_scalar_tile_op(
  fw,
  op: SfpuScalarOp,
  scalar_bits: int,
  *,
  scalar_lreg: int = 1,
  walk: SfpuTileWalk = SfpuTileWalk(),
  groups_per_face: int | None = None,
  breadcrumb_addr: int | None = None,
  breadcrumb_prefix: str | None = None,
):
  if op is not SfpuScalarOp.ADD:
    raise NotImplementedError(f"unsupported SFPU scalar op {op}")

  groups = walk.groups_per_face if groups_per_face is None else groups_per_face
  for face in range(walk.faces):
    if breadcrumb_addr is not None and breadcrumb_prefix is not None:
      fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:face{face}_enter")
    load_lreg_fp32(fw, scalar_lreg, scalar_bits)
    if breadcrumb_addr is not None and breadcrumb_prefix is not None:
      fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:face{face}_const_loaded")
      emit_traced_scalar_add_face(
        fw,
        groups,
        walk=walk,
        breadcrumb_addr=breadcrumb_addr,
        breadcrumb_prefix=f"{breadcrumb_prefix}:face{face}",
      )
    else:
      emit_scalar_add_face(fw, groups, walk=walk)
    if breadcrumb_addr is not None and breadcrumb_prefix is not None:
      fw.breadcrumb(breadcrumb_addr, f"{breadcrumb_prefix}:face{face}_done")
    fw.emit(
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
    )
