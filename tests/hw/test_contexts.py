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
from config import PackerContext, PackCommonCfg, UnpackerContext, DataFormat, Space, l1_addr
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
    reads_per_xy_plane=1, dest_row_offset=0)

def _pacr(ctx, *, close=False):
  return TT.TTPACR(ctx, 0, 0, int(close), 0, 0, 1, 0, 0, 0, 0, int(close))

def _images(ctx, write_contexts=True, *, trisc0=None, edit=None, extra=()):
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
  if extra: apply(k, *extra)
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

def _unpack_with_context(ctx, step="full", base=None):
  """blackhole-py's unpack-to-Dest, but context ctx gets its own L1 base and the UNPACR selects ctx."""
  original_cfg, original_unpacr = U.configure_unpacker, U._unpacr
  def configure(k, *a, **kw):
    original_cfg(k, *a, **kw)
    if step == "plain": return
    apply(k, UnpackerContext(unpacker=0, context=ctx, l1_base=l1_addr(SOURCES[ctx]), dest_address=64, tile_x_dim=256,
                             offset_address=0, shift_amount=0, disable_zero_compress=True, to_dest=True))
    # no second PC_UNPACK_SYNC commit here: a kernel that commits twice hangs the next launch on this core.
    # Blackhole Auto TTSync already orders these RISC config writes before the UNPACR.
  def unpacr(engine, *, to_dst=False):  # blackhole-py already sets multi-context mode (OvrdThreadId) with context 0
    word = original_unpacr(engine, to_dst=to_dst)  # keep ttko's TensixWord type: Asm.emit treats plain ints as RISC-V
    return type(word)(int(word) | (ctx << 10 if step == "full" else 0))
  U.configure_unpacker, U._unpacr = configure, unpacr
  try:
    k = Asm("trisc0"); size = k.reg(); k.li(size, F32_TILE_BYTES)
    U.emit_unpack_to_dst(k, SOURCES[0] if base is None else base, size, 0, 0)  # context 0 keeps SOURCES[0]
  finally:
    U.configure_unpacker, U._unpacr = original_cfg, original_unpacr
  return k

@pytest.mark.parametrize("ctx", range(8))
def test_unpacr_cfg_ctx_selects_unpacker_context(bh, ctx):
  l1 = {SOURCES[c]: pack(f"<{TILE_ELEMENTS}I", *_source_words(c)) for c in range(8)}
  bh.launch(_images(0, write_contexts=False, trisc0=_unpack_with_context(ctx)), l1={**l1, OUTPUTS[0]: b"\xA5" * BF16_TILE})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
  source = (got[0] - 0x3F80) // TILE_ELEMENTS
  print(f"unpacker cfg_ctx={ctx}: data came from source {source}")  # every context has its own L1 base
  assert got == tuple(w >> 16 for w in _source_words(ctx))

@pytest.mark.parametrize("ctx,step", [(c, s) for c in range(8) for s in ("plain", "apply", "full")])
def test_unpack_context_steps(bh, ctx, step):
  l1 = {SOURCES[c]: pack(f"<{TILE_ELEMENTS}I", *_source_words(c)) for c in range(8)}
  bh.launch(_images(0, write_contexts=False, trisc0=_unpack_with_context(ctx, step)), l1={**l1, OUTPUTS[0]: b"\xA5" * BF16_TILE})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
  sources = [c for c in range(8) if got == tuple(w >> 16 for w in _source_words(c))]
  print(f"\nSTEP ctx{ctx}/{step}: {sources or hex(got[0])}", flush=True)

@pytest.mark.parametrize("uploads", ["one", "all"])
def test_unpack_plain_uploads(bh, uploads):
  srcs = range(1) if uploads == "one" else range(8)
  l1 = {SOURCES[c]: pack(f"<{TILE_ELEMENTS}I", *_source_words(c)) for c in srcs}
  bh.launch(_images(0, write_contexts=False, trisc0=_unpack_with_context(0, "plain")), l1={**l1, OUTPUTS[0]: b"\xA5" * BF16_TILE})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
  assert got == tuple(w >> 16 for w in _source_words(0))

def test_unpack_source_address(bh):
  """Which L1 addresses work as an unpack source with blackhole-py's unpack-to-Dest (no context changes)?"""
  report = []
  for base in (INPUT, INPUT + 0x8000, INPUT + 0x10000, INPUT + 0x20000):
    words = _source_words(1)
    bh.launch(_images(0, write_contexts=False, trisc0=_unpack_with_context(0, "plain", base)),
              l1={base: pack(f"<{TILE_ELEMENTS}I", *words), OUTPUTS[0]: b"\xA5" * BF16_TILE})
    got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[0], BF16_TILE))
    report.append(f"{base:#x}: {'ok' if got == tuple(w >> 16 for w in words) else f'first={got[0]:#x}'}")
  print("SOURCE " + " | ".join(report))

# ***** which packer section registers follow cfg_ctx *****

# name: (edit applied to context 1, extra configs). Packing uses cfg_ctx=1; row-set mapping 0 sends every row to mask 0.
VARIANTS = {"control": (None, ()),
            "ctx1 dest_row_offset=32": (lambda c: replace(c, dest_row_offset=32), ()),
            "ctx1 counters=0": (lambda c: replace(c, reads_per_xy_plane=0), ()),
            "ctx1 counters=16": (lambda c: replace(c, reads_per_xy_plane=16), ()),
            "ctx0 counters=0": (None, (PackerContext(context=0, reads_per_xy_plane=0),)),
            "ctx0 counters=16": (None, (PackerContext(context=0, reads_per_xy_plane=16),)),
            "edge mask 1 = 0": (None, (PackCommonCfg(edge_mask_1=0),)),
            "edge mask 0 = 0": (None, (PackCommonCfg(edge_mask_0=0),))}

@pytest.mark.parametrize("variant", VARIANTS)
def test_packer_section_fields_follow_cfg_ctx(bh, variant):
  words = [0x3F800000 + (i << 16) for i in range(TILE_ELEMENTS)]
  edit, extra = VARIANTS[variant]
  bh.launch(_images(1, edit=edit, extra=extra), l1={INPUT: pack(f"<{TILE_ELEMENTS}I", *words), **{o: b"\xA5" * BF16_TILE for o in OUTPUTS}})
  raw = bh.read_l1(bh.core, OUTPUTS[1], BF16_TILE)
  got = unpack(f"<{TILE_ELEMENTS}H", raw)
  rows = [None if got[r * 16] == 0xA5A5 else (got[r * 16] - 0x3F80) // 16 if got[r * 16] else 0 for r in range(ROWS)]
  print(f"packer variant {variant}: first rows {rows[:6]} last {rows[-3:]} intact={got == tuple(w >> 16 for w in words)}")
  expected_rows = {"ctx1 dest_row_offset=32": list(range(32, 64)) + [0] * 32,  # per context, in Dest rows (rows past the tile are zero)
                   "edge mask 0 = 0": [0] * ROWS}.get(variant, list(range(ROWS)))  # edge masks follow the row set, not cfg_ctx
  assert rows == expected_rows

# ***** do the pack counters follow cfg_ctx? *****
#
# reads_per_xy_plane is the wrap point of the packer's tile position generator (ISA doc Packers/EdgeMasking.md), whose Y
# picks each row's entry in the row-set mapping, which picks the edge mask. The probes above map every row to mask 0, so
# the counter was invisible. Here row Y=0 gets mask 0 (keep) and Y=1..15 get mask 1 (zero): the surviving rows are spaced
# reads_per_xy_plane apart, which tells us whose counter the packer used.

EDGE_PROBE = PackCommonCfg(edge_mask_0=0xFFFF, edge_mask_1=0, edge_mask_2=0, edge_mask_3=0, row_set_select_0=0,
                           row_set_mapping_0=0x55555554)  # 2 bits per Y: Y=0 -> mask 0, Y=1..15 -> mask 1

COUNTER_CASES = {  # name: (PACR cfg_ctx, ctx0 reads_per_xy_plane, ctx1 reads_per_xy_plane)
  "pack ctx0, ctx0=4 ctx1=2": (0, 4, 2),
  "pack ctx1, ctx0=1 ctx1=1": (1, 1, 1),
  "pack ctx1, ctx0=4 ctx1=2": (1, 4, 2),
  "pack ctx1, ctx0=2 ctx1=4": (1, 2, 4),
  "pack ctx1, ctx0=8 ctx1=1": (1, 8, 1),
  "pack ctx1, ctx0=1 ctx1=8": (1, 1, 8),
}

@pytest.mark.parametrize("case", COUNTER_CASES)
def test_pack_counters_follow_cfg_ctx(bh, case):
  ctx, r0, r1 = COUNTER_CASES[case]
  words = [0x3F800000 + (i << 16) for i in range(TILE_ELEMENTS)]
  extra = (PackerContext(context=0, reads_per_xy_plane=r0), PackerContext(context=1, reads_per_xy_plane=r1), EDGE_PROBE)
  bh.launch(_images(ctx, extra=extra), l1={INPUT: pack(f"<{TILE_ELEMENTS}I", *words), **{o: b"\xA5" * BF16_TILE for o in OUTPUTS}})
  got = unpack(f"<{TILE_ELEMENTS}H", bh.read_l1(bh.core, OUTPUTS[ctx], BF16_TILE))
  kept = [r for r in range(ROWS) if got[r * 16: r * 16 + 16] == tuple(w >> 16 for w in words[r * 16: r * 16 + 16])]
  zeroed = [r for r in range(ROWS) if not any(got[r * 16: r * 16 + 16])]
  print(f"\nCOUNTERS {case}: kept rows {kept[:10]}{'...' if len(kept) > 10 else ''} ({len(kept)} kept, {len(zeroed)} zeroed)", flush=True)
  assert len(kept) + len(zeroed) == ROWS, "rows neither intact nor zeroed"
  period = {tuple(range(0, ROWS, p)): p for p in (1, 2, 4, 8, 16)}.get(tuple(kept))
  print(f"COUNTERS {case}: period {period}  (ctx0 says {r0}, ctx1 says {r1})", flush=True)
  assert period == (r0, r1)[ctx]  # hardware: the counters PACR uses are those of its cfg_ctx
