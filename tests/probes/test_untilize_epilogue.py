"""Probe: FP32 tiles in L1 -> Dst (unpack-to-dest) -> row-major BF16 rows.

This is the matmul epilogue. It takes a 1xW subblock of FP32 accumulator tiles
(face-major, as the packer L1-accumulates them), copies them exactly into Dst,
then packs them untilized as BF16. Each PACR reads face-0 row r and face-1
row r through two read interfaces in strided Dst mode (interface 1 sits 16 rows
below interface 0), so one PACR is one 32-wide tile row. Z steps tiles, W
selects the bottom face pair, and Y walks rows. The output is 32 rows of
W*32 BF16 values at a configurable row pitch, compared bit-exactly with
round-to-nearest-even of the FP32 inputs.
"""
import os

import numpy as np

from asm import Asm
from tests.movement.unpacker import unpack as u
from tests.movement.unpacker.test_unpack import INPUT_A
from ttko.isa import Tensix as TT

OUTPUT = INPUT_A + 0x20000
WIDTH = int(os.environ.get('PROBE_SB_W', '4'))        # tiles in the subblock
PITCH = int(os.environ.get('PROBE_PITCH', str(WIDTH * 64)))  # output row bytes (>= WIDTH*64)


def rne_bf16(x):
  bits = x.view(np.uint32).astype(np.uint64)
  rounded = (bits + 0x7FFF + ((bits >> 16) & 1)) >> 16
  return rounded.astype(np.uint16)


def rna_bf16(x):
  """Round to nearest, ties away from zero: the packer's only deterministic mode."""
  bits = x.view(np.uint32).astype(np.uint64)
  return ((bits + 0x8000) >> 16).astype(np.uint16)


def face_major(tile):
  return np.concatenate([tile[r:r+16, c:c+16].ravel() for r in (0, 16) for c in (0, 16)])


def unpack_tiles_to_dst(k, address, ntiles):
  """Copy ntiles consecutive FP32 tiles from L1 into FP32 Dst tiles 0..ntiles-1,
  one 256-datum face per UNPACR (each drained before the next), then publish
  them to the packer through MATH_PACK."""
  u.load_replay(k, 0, (TT.TTUNPACR(0, 0x11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1),
                       TT.TTSTALLWAIT(u.Stall.UNPACK, u.Wait.UNPACK0)))
  for t in range(ntiles):
    u.configure_unpacker(k, 0, address + t * 4096, u.F32, u.UnpackTarget.DST, dst_tile=t)
    k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    k.emit(TT.TTSETADCXX(1, 255, 0))
    u.stall(k, u.Stall.UNPACK, u.Wait.TRISC_CFG)
    for _ in range(4): k.emit(TT.TTREPLAY(0, 2))
    u.stall(k, u.Stall.UNPACK, u.Wait.UNPACK0 | u.Wait.THCON)
    u.sem_get(k, u.Sem.UNPACK_SYNC)        # configure_unpacker's commit took it
    u.pc_sync(k)
  k.emit(TT.TTSETC16(u.SRCA_SET, 4))
  u.stall(k, u.Stall.SYNC, u.Wait.UNPACK0)
  u.sem_post(k, u.Sem.MATH_PACK)


def test_untilize_epilogue(bh):
  rng = np.random.default_rng(1)
  tiles = rng.standard_normal((WIDTH, 32, 32)).astype(np.float32)
  if os.environ.get('PROBE_EXACT') == '1':   # unique BF16-exact values: layout only
    codes = np.arange(WIDTH * 1024, dtype=np.uint32).reshape(32, WIDTH * 32)
    tiles = np.stack(np.split(((codes + 0x3c00) << 16).view(np.float32), WIDTH, axis=1))
  bits = tiles.view(np.uint32)
  # Exact BF16 ties (low half 0x8000) with both kept-bit parities, and some
  # values just above/below a tie.
  if os.environ.get('PROBE_EXACT') == '1': bits = bits.copy()
  bits[:, 0, :8] = (bits[:, 0, :8] & 0xFFFF0000) | 0x8000
  bits[:, 1, :8] = (bits[:, 1, :8] & 0xFFFE0000) | 0x18000
  bits[:, 2, :8] = (bits[:, 2, :8] & 0xFFFF0000) | 0x8001
  bits[:, 3, :8] = (bits[:, 3, :8] & 0xFFFF0000) | 0x7FFF
  src = b''.join(face_major(t).tobytes() for t in tiles)

  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  math.emit(TT.TTSEMINIT(1, 0, 1 << u.Sem.MATH_PACK))
  u.configure_fp32_dst(math, 0)
  # Strided Dst reads (interface i at +16 rows) need Dst address remap and
  # 32-bit swizzle, set before anything writes Dst.
  math.write(u.CFG_BASE + 220 * 4, int(os.environ.get('PROBE_REMAP', '3')))
  u.pc_sync(math)
  u.sem_post(math, u.Sem.UNPACK_TO_DEST)
  u.sem_wait(loader, u.Sem.UNPACK_TO_DEST, u.SemWait.ON_ZERO, u.Stall.UNPACK)
  unpack_tiles_to_dst(loader, INPUT_A, WIDTH)

  # --- pack: untilize into row-major BF16
  u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
  # BF16 intermediate: the early (Dst-read) conversion rounds FP32 -> BF16.
  u.configure_packer(packer, u.BF16, source_format=u.BF16, dst_fp32=True)
  # With remap/swizzle on, packer Dst addressing counts 32-bit rows in 32-byte
  # units: Y one row, Z one tile (64 rows), W two faces (32 rows).
  packer.write(u.PackCfg.ADDRESS_XY, 32 << 16)
  packer.write(u.PackCfg.ADDRESS_ZW, 2048 | 1024 << 16)
  u._set_thread_cfg(packer, u.PACK_ADDRESS_MODIFIER + 0, 1 << 12)            # z += 1: next tile
  u._set_thread_cfg(packer, u.PACK_ADDRESS_MODIFIER + 1, 1 | 2 << 12)       # y += 1, z = 0: next row
  pacr = lambda mode, last: TT.TTPACR(0, 0, 1, mode, 0, 0, 0b0011, 0, 0, 0, 0, last)
  u.configure_mop(packer, u._mop_loop_words(
    16, WIDTH, loop=pacr(0, 0), last=pacr(1, 1), outer_last=pacr(1, 1),
    end0=TT.TTREPLAY(0, 4)))
  u.load_replay(packer, 0, (
    TT.TTADDDMAREG(0, 12, 12, 14), TT.TTSTALLWAIT(u.Stall.CFG, u.Wait.THCON),
    TT.TTWRCFG(12, 0, (int(u.PackCfg.L1_DESTINATION) - u.CFG_BASE) >> 2), TT.TTNOP()))
  u._set_pack_destination(packer, 0, OUTPUT)                    # also leaves GPR12 = dest - 1
  packer.write(0xFFE00000 + 14 * 4, PITCH // 16)               # GPR14: row pitch / 16
  packer.emit(TT.TTSETADCXX(4, 15, 0))
  packer.write(u.PackCfg.DESTINATION_OFFSET, 0)
  for half in (0, 1):
    packer.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB))
    packer.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    packer.emit(TT.TTSETADC(4, 0, 3, half))
    u.stall(packer, u.Stall.CFG, u.Wait.PACK0 | u.Wait.THCON)
    u.run_mop(packer)
  u.stall(packer, u.Stall.SYNC, u.Wait.PACK0)
  u.sem_get(packer, u.Sem.MATH_PACK)
  u.pc_sync(packer)

  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: src, OUTPUT: bytes(32 * PITCH)})
  raw = np.frombuffer(bh.read_l1(bh.core, OUTPUT, 32 * PITCH), '<u2').reshape(32, PITCH // 2)
  got = raw[:, :WIDTH * 32]
  full = np.concatenate(list(tiles), axis=1)
  want = rna_bf16(full)
  print('\nRNE vs ties-away differ at', int(np.sum(rne_bf16(full) != want)), 'values; device == RNE at', int(np.sum(got == rne_bf16(full))), 'of', got.size)
  bad = np.argwhere(got != want)
  if len(bad) and os.environ.get('PROBE_EXACT') == '1':
    lut = {int(v): (r, c) for (r, c), v in np.ndenumerate(want)}
    print(f'\n{len(bad)} layout mismatches')
    for r in (0, 1, 15, 16, 17, 31):
      print(f'row {r}:', [lut.get(int(x), hex(int(x))) for x in got[r, ::16]])
  elif len(bad):
    r, c = bad[0]
    print(f'\n{len(bad)} mismatches; first at row {r} col {c}: got {got[r, c]:04x} want {want[r, c]:04x}'
          f' (fp32 {np.concatenate(list(tiles), axis=1).view(np.uint32)[r, c]:08x})')
    print('row 0 got ', ' '.join(f'{x:04x}' for x in got[0, :8]))
    print('row 0 want', ' '.join(f'{x:04x}' for x in want[0, :8]))
    trunc = (np.concatenate(list(tiles), axis=1).view(np.uint32) >> 16).astype(np.uint16)
    print('matches truncation:', bool(np.array_equal(got, trunc)))
    f = np.concatenate(list(tiles), axis=1).view(np.uint32)
    diff = got.astype(np.int32) - want.astype(np.int32)
    print('diff histogram (got - rne, in ulps):', dict(zip(*np.unique(diff, return_counts=True))))
    print('agree with truncation:', float(np.mean(got == trunc)))
    # Hypotheses: truncate to TF32 (low 13 bits dropped) and then RNE / truncate to BF16.
    tf32 = (f & 0xFFFFE000).astype(np.uint32)
    print('agree with rne(tf32 trunc):', float(np.mean(got == rne_bf16(tf32.view(np.float32)))))
    for sh in (8, 10, 12, 13, 14, 15):
      keep = (f >> sh) << sh
      print(f'agree with rne(trunc {sh} low bits):', float(np.mean(got == rne_bf16(keep.astype(np.uint32).view(np.float32)))))
    half_away = ((f.astype(np.uint64) + 0x8000) >> 16).astype(np.uint16)
    print('agree with round-half-up on magnitude:', float(np.mean(got == half_away)))
    rows_ok = [int(np.mean(got[r] == trunc[r]) * 100) for r in range(32)]
    print('per-row % equal to truncation:', rows_ok)
    full = np.concatenate(list(tiles), axis=1)
    tr = (full.view(np.uint32) >> 16).astype(np.uint16)
    lut = {}
    for (rr, cc), v in np.ndenumerate(tr): lut.setdefault(int(v), (rr, cc))
    print('row 16 got maps to', [lut.get(int(x)) for x in got[16, :4]], 'row 17 ->', [lut.get(int(x)) for x in got[17, :4]], 'row 1 ->', [lut.get(int(x)) for x in got[1, :4]], 'col 32.. of row 0 ->', [lut.get(int(x)) for x in got[0, 32:36]])
    for r, c in bad[:6]:
      print(f'  ({r},{c}) fp32 {f[r,c]:08x} got {got[r,c]:04x} rne {want[r,c]:04x}')
  assert not len(bad)


def test_unpack_to_dst_plain(bh):
  """Control: the same unpack-to-dest, packed back as FP32 tiles."""
  rng = np.random.default_rng(1)
  tiles = rng.standard_normal((WIDTH, 32, 32)).astype(np.float32)
  src = b''.join(face_major(t).tobytes() for t in tiles)
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  math.emit(TT.TTSEMINIT(1, 0, 1 << u.Sem.MATH_PACK))
  u.configure_fp32_dst(math, 0)
  unpack_tiles_to_dst(loader, INPUT_A, WIDTH)
  for t in range(WIDTH):
    u.emit_pack_dst(packer, t, OUTPUT + t * 4096, u.F32, configure=t == 0, wait_for_dst=t == 0)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: src, OUTPUT: bytes(WIDTH * 4096)})
  got = np.frombuffer(bh.read_l1(bh.core, OUTPUT, WIDTH * 4096), '<f4')
  want = np.frombuffer(src, '<f4')
  print('\nplain match per tile:', [bool(np.array_equal(got[t*1024:(t+1)*1024], want[t*1024:(t+1)*1024])) for t in range(WIDTH)])
  assert np.array_equal(got, want)
