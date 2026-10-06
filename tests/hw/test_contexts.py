"""Hardware probe: are the four packer config sections contexts selected by PACR cfg_ctx?

All four sections get a full, distinct configuration (written with config.PackerContext), each with its own L1
destination. A PACR with cfg_ctx = N must write only OUTPUT[N]; the other three stay sentinel.

Run from blackhole-py (uses its bh fixture and helpers):
  cd ../blackhole-py && tt-device-queue run --device 0 --cwd "$PWD" -- \
    '../.venv/bin/python -m pytest -p tests.conftest ../blackhole-py-rewrite/tests/hw/test_contexts.py --bh-hardware -q'
"""
import sys, pathlib
from struct import pack, unpack
import pytest
from dataclasses import replace

REWRITE = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(REWRITE))  # after blackhole-py, which owns pcie.py
from config import PackerContext, UnpackerContext, DataFormat, Space, l1_addr
sys.path.append(str(pathlib.Path(__file__).resolve().parent)); from cfg_apply import apply
import tests.movement.unpacker.unpack as U

from asm import Asm
from firmware.consts import TensixL1, TensixMMIO
from ttko.isa import Tensix as TT
from tests.movement.packer.pack import _configure_row_addressing, _set_dst_position
from tests.movement.unpacker.unpack import (
  BF16, F32_TILE_BYTES, TILE_ELEMENTS, PackCfg, Sem, Stall, Wait,
  _mop_loop_words, _set_pack_destination, configure_mop, configure_packer, emit_direct_dst_math_handshake,
  emit_unpack_to_dst, pc_sync, run_mop, sem_get, sem_wait, stall, SemWait,
)

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
BF16_TILE = TILE_ELEMENTS * 2
OUTPUTS = tuple(INPUT + F32_TILE_BYTES + i * 0x1000 for i in range(4))
ROWS = TILE_ELEMENTS // 16

def _context(n):
  return PackerContext(
    context=n, l1_dest=l1_addr(OUTPUTS[n]) | 1 << 31, row_start_section_size=0, exp_section_size=4,
    disable_zero_compress=True, dst_format=DataFormat.FLOAT16_B, src_format=DataFormat.FLOAT16_B,  # packer input format is BF16 even for fp32 Dest (configure_packer)
    edge_mask=0xFFFF, reads_per_xy_plane=1, dest_row_offset=0)

def _pacr(ctx, *, close=False):
  return TT.TTPACR(ctx, 0, 0, int(close), 0, 0, 1, 0, 0, 0, 0, int(close))

def _images(ctx, write_contexts=True, *, trisc0=None, edit=None):
  if trisc0 is None:
    trisc0 = Asm("trisc0")
    size = trisc0.reg(); trisc0.li(size, F32_TILE_BYTES)
    emit_unpack_to_dst(trisc0, INPUT, size, 0, 0)

  trisc1 = Asm("trisc1")
  emit_direct_dst_math_handshake(trisc1, 0)

  k = Asm("trisc2")
  sem_wait(k, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
  configure_packer(k, BF16)
  _configure_row_addressing(k)
  _set_pack_destination(k, 0, OUTPUTS[0])
  stall(k, Stall.CFG, Wait.THCON | Wait.PACK0)
  for n in range(4 if write_contexts else 0):
    c = _context(n) if edit is None or n != 1 else edit(_context(n))
    for (space, _, addr), (value, _) in c.writes().items():
      assert space is Space.SHARED
      k.write(TensixMMIO.CFG_BASE + 4 * addr, value)
  _set_dst_position(k, 0, 0)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  configure_mop(k, _mop_loop_words(1, ROWS, loop=_pacr(ctx), last=_pacr(ctx, close=True)))
  stall(k, Stall.CFG, Wait.PACK0)
  run_mop(k)
  stall(k, Stall.SYNC, Wait.PACK0)
  pc_sync(k)
  sem_get(k, Sem.MATH_PACK)
  return {"trisc0": trisc0.lower(), "trisc1": trisc1.lower(), "trisc2": k.lower()}

@pytest.mark.parametrize("ctx", range(4))
def test_pacr_cfg_ctx_selects_packer_section(bh, ctx):
  words = [0x3F800000 + (i << 16) for i in range(TILE_ELEMENTS)]  # exact in BF16
  source = pack(f"<{TILE_ELEMENTS}I", *words)
  expected = pack(f"<{TILE_ELEMENTS}H", *(w >> 16 for w in words))
  sentinel = b"\xA5" * BF16_TILE
  bh.launch(_images(ctx), l1={INPUT: source, **{o: sentinel for o in OUTPUTS}})
  got = [bh.read_l1(bh.core, o, BF16_TILE) for o in OUTPUTS]
  written = [i for i, g in enumerate(got) if g != sentinel]
  assert written == [ctx], f"cfg_ctx={ctx} wrote outputs {written}"
  assert got[ctx] == expected

def test_baseline_row_pack_unique_pattern(bh):
  """Control: context 0 with blackhole-py's own config only; every Dest row lands once, in order."""
  words = [0x3F800000 + (i << 16) for i in range(TILE_ELEMENTS)]
  bh.launch(_images(0, write_contexts=False), l1={INPUT: pack(f"<{TILE_ELEMENTS}I", *words), OUTPUTS[0]: b"\xA5" * BF16_TILE})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
  rows = [(got[r * 16] - 0x3F80) // 16 for r in range(ROWS)]
  print("baseline source row per output row:", rows)
  assert rows == list(range(ROWS))


# ***** unpacker contexts *****

SOURCES = tuple(TensixL1.DATA_BUFFER_SPACE_BASE + 0x10000 + c * 0x1000 for c in range(8))

def _source_words(c): return [0x3F800000 + ((c * TILE_ELEMENTS + i) << 16) for i in range(TILE_ELEMENTS)]

def _unpack_with_context(ctx):
  """blackhole-py's unpack-to-Dest, but context ctx gets its own L1 base and the UNPACR selects ctx."""
  original_cfg, original_unpacr = U.configure_unpacker, U._unpacr
  def configure(k, *a, **kw):
    original_cfg(k, *a, **kw)
    apply(k, UnpackerContext(unpacker=0, context=ctx, l1_base=l1_addr(SOURCES[ctx]), dest_address=64, tile_x_dim=256,
                             offset_address=0, shift_amount=0, disable_zero_compress=True, to_dest=True))
    observed = k.reg(); k.read(observed, U._engine_cfg(U.UnpackCfg.BASE, 0)); k.write(U.UNPACK_CONFIG_SYNC, 0)
  def unpacr(engine, *, to_dst=False):  # blackhole-py already sets multi-context mode (OvrdThreadId) with context 0
    return int(original_unpacr(engine, to_dst=to_dst)) | ctx << 10
  U.configure_unpacker, U._unpacr = configure, unpacr
  try:
    k = Asm("trisc0"); size = k.reg(); k.li(size, F32_TILE_BYTES)
    U.emit_unpack_to_dst(k, SOURCES[0], size, 0, 0)  # context 0 keeps SOURCES[0]
  finally:
    U.configure_unpacker, U._unpacr = original_cfg, original_unpacr
  return k

@pytest.mark.skip(reason="probe bug: context 0 returns zeros, and context 2 hung the card; fix before running")
@pytest.mark.parametrize("ctx", [0, 1, 2, 5, 7])
def test_unpacr_cfg_ctx_selects_unpacker_context(bh, ctx):
  l1 = {SOURCES[c]: pack(f"<{TILE_ELEMENTS}I", *_source_words(c)) for c in range(8)}
  bh.launch(_images(0, write_contexts=False, trisc0=_unpack_with_context(ctx)), l1={**l1, OUTPUTS[0]: b"\xA5" * BF16_TILE})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
  source = (got[0] - 0x3F80) // TILE_ELEMENTS
  print(f"unpacker cfg_ctx={ctx}: data came from source {source}")
  assert got == tuple(w >> 16 for w in _source_words(ctx))

# ***** which packer section registers follow cfg_ctx *****

VARIANTS = {"control": lambda c: c, "dest_row_offset=32": lambda c: replace(c, dest_row_offset=32),
            "counters=0": lambda c: replace(c, reads_per_xy_plane=0), "edge_mask=0": lambda c: replace(c, edge_mask=0)}

@pytest.mark.skip(reason="not run yet: queued behind the unpacker probe fix")
@pytest.mark.parametrize("variant", VARIANTS)
def test_packer_section_fields_follow_cfg_ctx(bh, variant):
  words = [0x3F800000 + (i << 16) for i in range(TILE_ELEMENTS)]
  bh.launch(_images(1, edit=VARIANTS[variant]), l1={INPUT: pack(f"<{TILE_ELEMENTS}I", *words), **{o: b"\xA5" * BF16_TILE for o in OUTPUTS}})
  raw = bh.read_l1(bh.core, OUTPUTS[1], BF16_TILE)
  got = unpack(f"<{TILE_ELEMENTS}H", raw)
  rows = [None if got[r * 16] == 0xA5A5 else (got[r * 16] - 0x3F80) // 16 if got[r * 16] else 0 for r in range(ROWS)]
  print(f"packer variant {variant}: first rows {rows[:6]} last {rows[-3:]} intact={got == tuple(w >> 16 for w in words)}")
