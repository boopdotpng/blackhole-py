"""Hardware probe: does unpacker 1 (SrcB) have usable config contexts beyond 0 and 1?

Every context c gets its own L1 source (distinct BF16 values). UNPACR on unpacker 1 selects cfg_ctx = ctx; math moves
SrcB into Dest with MOVB2D and the packer writes Dest out as FP32. The output tells us which source the unpacker read.
Path copied from blackhole-py tests/movement/unpacker/test_dst_paths.py (srcB), which passes on hardware.

  cd ../blackhole-py && tt-device-queue run --device 0 --cwd "$PWD" -- \
    '../.venv/bin/python -m pytest -p tests.conftest ../blackhole-py-rewrite/tests/hw/test_unpacker1_contexts.py --bh-hardware -q -s'
"""
import sys, pathlib
from struct import pack, unpack
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # after blackhole-py, which owns pcie.py
from config import Bank, CFG_BASE, CFG_DUAL_WRITE, GLOBAL_CFG_BASE, UnpackerCfg, UnpackerContext, l1_addr
sys.path.append(str(pathlib.Path(__file__).resolve().parent)); from cfg_apply import apply

class AnyUnpackerContext(UnpackerContext):  # config.py stops unpacker 1 at context 1; the registers for 2..7 still exist
  def index(self): return self.context

from asm import Asm, Cond
from ttko.isa import Tensix as TT
from firmware.consts import TensixL1
from tests.movement.unpacker.unpack import (
  BF16, F32, UnpackCfg, _engine_cfg, UnpackTarget, Sem, SemWait, Stall, Wait, _set_thread_cfg,
  _unpacr, _mop_loop_words, configure_unpacker, configure_mop, run_mop,
  stall, sem_wait, sem_get, sem_post, pc_sync, publish_dst, emit_pack_dst, finish_pack, configure_fp32_dst,
)

ELEMENTS = 1024
OUTPUT = TensixL1.DATA_BUFFER_SPACE_BASE
SOURCES = tuple(TensixL1.DATA_BUFFER_SPACE_BASE + 0x10000 + c * 0x1000 for c in range(8))
SENTINEL = b"\xA5" * (ELEMENTS * 4 + 64)

def source_words(c): return [(0x3F80 + c * ELEMENTS + i) << 16 for i in range(ELEMENTS)]  # exact in BF16, distinct per c

RESETS = {  # SETC16 values written to ThreadCfg[41] (UNPACK_MISC_CFG) before the UNPACR; bit 4 / bit 12 = CfgContextCntReset_0 / _1
  "none": (), "pulse1": (1 << 12, 0), "hold1": (1 << 12,), "pulse0": (1 << 4, 0), "pulse_both": (1 << 4 | 1 << 12, 0), "hold_both": (1 << 4 | 1 << 12,)}

def images(ctx, *, configure_ctx=True, also_sec0=False, mode="cfg_ctx", reset=None, wrap_cfg=(), then_non_log2=None, bank_state=None):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  configure_unpacker(loader, 1, SOURCES[0], F32, UnpackTarget.SRCB)
  loader.write(_engine_cfg(UnpackCfg.OPTIONS, 1), 0x20 | BF16)
  loader.write(_engine_cfg(UnpackCfg.ADDRESS_XY1, 1), 2 | 32 << 16)
  loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, 1), 512)
  loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, 1) + 4, 2048)
  # no second commit: the pc_sync after configure_mop orders these config writes before the UNPACR (Auto TTSync is off)
  if configure_ctx:  # the same per-context state configure_unpacker gives contexts 0/1, plus this context's source
    apply(loader, AnyUnpackerContext(unpacker=1, context=ctx, l1_base=l1_addr(SOURCES[ctx]), dest_address=0, tile_x_dim=256,
                                  offset_address=0, shift_amount=0, disable_zero_compress=True, to_dest=False))
  if also_sec0:  # does unpacker 1 with cfg_ctx >= 2 read unpacker 0's THCON section instead?
    apply(loader, UnpackerContext(unpacker=0, context=ctx, l1_base=l1_addr(SOURCES[ctx]), dest_address=0, tile_x_dim=256,
                                  offset_address=0, shift_amount=0, disable_zero_compress=True, to_dest=False))
  if reset is not None:  # counter probe: every context gets its own source, so the output names the counter value (0, 1, or >= 2)
    for c in range(8):
      apply(loader, AnyUnpackerContext(unpacker=1, context=c, l1_base=l1_addr(SOURCES[c]), dest_address=0, tile_x_dim=256,
                                       offset_address=0, shift_amount=0, disable_zero_compress=True, to_dest=False))
    apply(loader, UnpackerCfg(unpacker=1, context_count=3))
    for value in RESETS[reset]: loader.emit(TT.TTSETC16(41, value))
  if bank_state is not None:  # copy bank 0 into both banks, then move context 1 to source 1 in bank 1 only
    ptr, end, word, dst = loader.reg(4)
    loader.li(ptr, CFG_BASE); loader.li(end, CFG_BASE + 4 * GLOBAL_CFG_BASE)
    skip = loader.reg(); loader.li(skip, CFG_BASE + 4 * 4)  # STATE_RESET_EN: any write zeroes words 0..179 of the bank
    with loader.loop(Cond(ptr, "<u", end)):
      skipped = loader._new_label("skip_state_reset")
      loader.beq(ptr, skip, skipped)
      loader.read(word, ptr); loader.addi(dst, ptr, CFG_DUAL_WRITE - CFG_BASE); loader.write(dst, word)
      loader.label(skipped)
      loader.addi(ptr, ptr, 4)
    apply(loader, AnyUnpackerContext(unpacker=1, context=1, l1_base=l1_addr(SOURCES[1]), bank=Bank.B1))
    loader.emit(TT.TTSETC16(0, bank_state))  # CFG_STATE_ID of the unpack thread
  if mode == "offset":  # ThreadCfg CfgContextOffset_1 (unpack1_context) is added to UNPACR's context number
    loader.emit(TT.TTSETC16(41, ctx << 8))
  if mode == "counter":  # let the counter run over 8 contexts, and reset it (CfgContextCntReset_1 pulse)
    apply(loader, UnpackerCfg(unpacker=1, context_count=3))
    loader.emit(TT.TTSETC16(41, 1 << 12))
    loader.emit(TT.TTSETC16(41, 0))
  loader.emit(TT.TTSETADCXX(2, ELEMENTS - 1, 0))
  loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  word = _unpacr(1)
  word = type(word)(int(word) | (ctx << 10 if mode == "cfg_ctx" else 1 << 3 if mode == "counter" else 0))
  configure_mop(loader, _mop_loop_words(1, 1, start=word))
  pc_sync(loader)

  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  configure_fp32_dst(math, 0)
  _set_thread_cfg(math, 14, 4 << 8)
  _set_thread_cfg(math, 30, 4)
  _set_thread_cfg(math, 49, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  move = TT.TTMOVB2D(0, 0, 2, 4, 0)
  configure_mop(math, _mop_loop_words(1, ELEMENTS // 64, loop=move, last=move))
  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  stall(math, Stall.MATH, Wait.SRCB_VLD)
  run_mop(math)
  math.emit(TT.TTSETRWC(2, 0, 0, 0, 0, 0xF))
  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  publish_dst(math)

  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  pc_sync(loader)
  if wrap_cfg:  # candidate wrap fields stay set for the whole kernel; the increment should then force the counter to 0
    apply(loader, *wrap_cfg)
    loader.emit(TT.TTUNPACR(1, 0, 1))
    if then_non_log2 is not None:  # after the reset increment lands, widen the wrap (word 73+48 bits 9-11 = byte 1 bits 1-3)
      stall(loader, Stall.CFG, Wait.UNPACK1)
      loader.emit(TT.TTRMWCIB1(0x0E, then_non_log2 << 1, 73 + 48))
  if mode == "counter":
    for _ in range(ctx): loader.emit(TT.TTUNPACR(1, 0, 1))  # UNPACR (increment context counter) on unpacker 1
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK1)
  if bank_state is not None: loader.emit(TT.TTSETC16(0, 0))
  sem_get(loader, Sem.UNPACK_SYNC)
  sem_post(loader, Sem.UNPACK_TO_DEST)
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)

  emit_pack_dst(packer, 0, OUTPUT, F32)
  finish_pack(packer)
  return {k.role: k.lower() for k in (loader, math, packer)}

def run(bh, ctx, **kw):
  l1 = {SOURCES[c]: pack(f"<{ELEMENTS}I", *source_words(c)) for c in range(8)}
  bh.launch(images(ctx, **kw), l1={**l1, OUTPUT: SENTINEL})
  got = unpack(f"<{ELEMENTS}I", bh.read_l1(bh.core, OUTPUT, ELEMENTS * 4))
  hits = [c for c in range(8) if list(got) == source_words(c)]
  first = [hex(g >> 16) for g in got[:4]]
  return hits, first

def test_baseline_srcb_path(bh):
  hits, first = run(bh, 0, configure_ctx=False)
  print(f"\nUNP1 baseline (blackhole-py config, ctx 0): source {hits} first {first}", flush=True)
  assert hits == [0]

@pytest.mark.parametrize("ctx", range(8))
def test_unpacker1_cfg_ctx(bh, ctx):
  hits, first = run(bh, ctx)
  print(f"\nUNP1 cfg_ctx={ctx}: source {hits} first {first}", flush=True)
  if ctx < 2: assert hits == [ctx]
  else: assert hits == [] and first == ["0x0"] * 4  # hardware: no hang, SrcB data never reaches Dest

@pytest.mark.parametrize("ctx", (1, 2, 3, 5))
def test_unpacker1_cfg_ctx_with_sec0(bh, ctx):
  hits, first = run(bh, ctx, also_sec0=True)
  print(f"\nUNP1+SEC0 cfg_ctx={ctx}: source {hits} first {first}", flush=True)
  assert hits == ([ctx] if ctx < 2 else [])

@pytest.mark.parametrize("ctx", range(8))
def test_unpacker1_context_offset(bh, ctx):
  hits, first = run(bh, ctx, mode="offset")
  print(f"\nUNP1 offset={ctx}: source {hits} first {first}", flush=True)
  assert hits == ([ctx] if ctx < 2 else [])

def counter_value(hits, first):
  return 0 if hits == [0] else 1 if hits == [1] else ">=2" if first == ["0x0"] * 4 else f"?{first}"

@pytest.mark.parametrize("reset", list(RESETS))
def test_unpacker1_counter_reset(bh, reset):
  """These reset writes land while the unpackers are idle, so they are ignored and the counter keeps counting across
  launches. The reset only takes effect while the unpacker is active (see the recipe by ThreadCfg in config.py)."""
  seen = [counter_value(*run(bh, 0, mode="counter", reset=reset, configure_ctx=False)) for _ in range(5)]
  print(f"\nCOUNTER reset={reset}: counter per launch {seen}", flush=True)

WRAP_FIELDS = {
  "unp0 context_count=0": (UnpackerCfg(unpacker=0, context_count=0),),
  "unp1 non_log2=0": (UnpackerCfg(unpacker=1, context_count_non_log2=0, context_count_non_log2_en=True),),
  "unp1 non_log2=1": (UnpackerCfg(unpacker=1, context_count_non_log2=1, context_count_non_log2_en=True),),
  "unp0 non_log2=0": (UnpackerCfg(unpacker=0, context_count_non_log2=0, context_count_non_log2_en=True),),
}

@pytest.mark.parametrize("field", list(WRAP_FIELDS))
def test_unpacker1_counter_wrap_field(bh, field):
  """Counter wrap: non_log2 + 1 when context_count_non_log2_en is set, else 1 << context_count. Unpacker 0's fields do not
  affect unpacker 1's counter."""
  seen = [counter_value(*run(bh, 0, mode="counter", reset="none", configure_ctx=False, wrap_cfg=WRAP_FIELDS[field])) for _ in range(5)]
  print(f"\nCOUNTER wrap field {field}: counter per launch {seen}", flush=True)

RESET = (UnpackerCfg(unpacker=1, context_count_non_log2=0, context_count_non_log2_en=True),)  # wrap at 1: an increment zeroes it

@pytest.mark.parametrize("increments", range(8))
def test_unpacker1_counter_after_reset(bh, increments):
  """Reset (wrap at 1 + increment), wrap at 8, then n increments: the counter selects context n, deterministically."""
  seen = [counter_value(*run(bh, increments, mode="counter", reset="none", configure_ctx=False, wrap_cfg=RESET, then_non_log2=7))
          for _ in range(3)]
  print(f"\nCOUNTER reset + {increments} increments: {seen}", flush=True)
  assert seen == [increments if increments < 2 else ">=2"] * 3
