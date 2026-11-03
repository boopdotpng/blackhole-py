"""Probe: what does Blackhole's one-instruction BF16 tileize put in SrcA?

Unpacks one row-major 32x32 BF16 tile (row pitch WIDTH*2 bytes) with tileize
mode, copies all 64 SrcA rows to Dst, packs them as FP32 and prints, for every
Src row, which (row, col) of the input tile landed in its 16 columns.
Configuration knobs come from PROBE_* environment variables so variants can be
swept without editing the file.
"""
import os

import numpy as np

from asm import Asm
from tests.movement.unpacker import unpack as u
from tests.movement.unpacker.test_unpack import INPUT_A
from ttko.isa import Tensix as TT

OUTPUT_A = INPUT_A + 0x10000
WIDTH = int(os.environ.get('PROBE_WIDTH', '32'))


def env(name, default):
  return int(os.environ.get(name, str(default)), 0)


def copy_srca_64_rows(k, bank, release):
  move = TT.TTMOVA2D(0, 0, 2, 2, 0)
  u.configure_mop(k, u._mop_loop_words(
    1, 8, loop=move, last=move, outer_last=move,
    end0=TT.TTSETRWC(release, 0, 0, 0, 0, 3)))


def emit_deinterleave_pack(k, output_address):
  """Pack Dst rows 0,2,..,62 then 1,3,..,63: tt-llk's Blackhole tilize
  unswizzle. Each PACR reads two Dst rows through read interfaces 0+2 or 1+3."""
  u.sem_wait(k, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
  u.configure_packer(k, u.F32, source_format=u.F32, dst_fp32=True)
  u._set_thread_cfg(k, u.PACK_ADDRESS_MODIFIER + 0, 4 | 2 << 6)          # y_src += 4, y_dst += 2
  u._set_thread_cfg(k, u.PACK_ADDRESS_MODIFIER + 1, 0x20 | 0x20 << 6)    # clear y_src, y_dst
  u._set_pack_destination(k, 0, output_address)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
  k.write(u.PackCfg.DESTINATION_OFFSET, 0)
  u.stall(k, u.Stall.CFG, u.Wait.PACK0)
  megarow = int(os.environ.get('PROBE_MEGAROW', '0'))
  for half, sel in enumerate((0b0101, 0b1010)):
    for i in range(16):
      last_of_half = i == 15
      k.emit(TT.TTPACR(0, 0, 0, 1 if last_of_half else 0, 0, 0, sel, 0, megarow, 0, 0,
                       int(last_of_half and half == 1)))
  u.stall(k, u.Stall.SYNC, u.Wait.PACK0)
  u.pc_sync(k)


def describe(actual, codes):
  index = {int(c): i for i, c in enumerate(codes)}
  rows = (actual.view(np.uint32) >> 16).reshape(64, 16)
  out = []
  for r, row in enumerate(rows):
    cells = [index.get(int(x)) for x in row]
    cells = [None if c is None else (c // WIDTH, c % WIDTH) for c in cells]
    first, last = cells[0], cells[-1]
    contiguous = all(
      a is not None and b is not None and a[0] == b[0] and b[1] == a[1] + 1
      for a, b in zip(cells, cells[1:]))
    out.append(f'{r:2d}: {first}..{last}{"" if contiguous else "  (not contiguous)"}')
  return '\n'.join(out)


def test_probe(bh, monkeypatch):
  monkeypatch.setattr(u, '_configure_copy_mop', copy_srca_64_rows)
  codes = (np.arange(WIDTH * 32, dtype=np.uint32) % 0x3000 + 0x3000).astype(np.uint16)
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  cfg = lambda reg: u._engine_cfg(reg, 0)
  u.clear_sources(loader)
  u.configure_unpacker(loader, 0, INPUT_A, u.BF16, u.UnpackTarget.SRCA, commit=False)
  x_dim = env('PROBE_XDIM', 1024)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR), (0x10 | u.BF16) | x_dim << 16)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR) + 4, env('PROBE_YDIM', 1) | env('PROBE_ZDIM', 1) << 16)
  loader.write(cfg(u.UnpackCfg.X_DIMENSION), x_dim | x_dim << 16)
  shift = WIDTH * 2 // 16
  loader.write(cfg(u.UnpackCfg.OPTIONS), (0x20 | u.BF16) | 1 << 9 | shift << 16)
  if os.environ.get('PROBE_XY1') is not None:
    loader.write(cfg(u.UnpackCfg.ADDRESS_XY1), env('PROBE_XY1', 0))
  if os.environ.get('PROBE_ZW1') is not None:
    loader.write(cfg(u.UnpackCfg.ADDRESS_ZW1), env('PROBE_ZW1', 0))
  loader.emit(TT.TTSETC16(u.SRCA_SET, env('PROBE_SRCA_SET', 4)))
  observed = loader.reg()
  loader.read(observed, cfg(u.UnpackCfg.BASE))
  loader.write(u.UNPACK_CONFIG_SYNC, 0)
  # SETADCXY with Ch1_X in the mask would zero the x-end SETADCXX programs.
  loader.emit(TT.TTSETADCXY(1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCZW(1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCXX(1, x_dim - 1, 0))
  u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR)
  loader.emit(TT.TTUNPACR(0, env('PROBE_ADDRMODE', 1), 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1))
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0)
  loader.emit(u._srcb_dvalid())
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)
  u.emit_copy_src_to_dst(math, u.UnpackTarget.SRCA, 0, release=3, input_format=u.BF16)
  u.publish_dst(math)
  if os.environ.get('PROBE_DEINTERLEAVE') == '1':
    emit_deinterleave_pack(packer, OUTPUT_A)
  else:
    u.emit_pack_dst(packer, 0, OUTPUT_A, u.F32, source_format=u.F32, dst_fp32=True)
  u.finish_pack(packer)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: codes.tobytes(), OUTPUT_A: bytes(4096)})
  actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT_A, 4096), '<f4')
  print('\nSRC LAYOUT\n' + describe(actual, codes))
  raw = (actual.view(np.uint32) >> 16).reshape(64, 16)
  print('RAW')
  for r in range(int(os.environ.get('PROBE_RAWROWS', '4'))):
    print(r, ' '.join(f'{int(x):04x}' for x in raw[r]))


# ---------------------------------------------------------------------------
# Throughput: N row-major tiles -> panel-ordered BF16 tiles, all three TRISCs
# running concurrently with two Dst slots in flight.

STAMPS = INPUT_A + 0x60000      # 3 threads x (start, end) u32
TP_OUT = INPUT_A + 0x30000


def stamp(k, slot):
  t = k.reg()
  k.read(t, 0xFFB121F0)
  k.write(STAMPS + slot * 4, t)


def test_tilize_throughput(bh, monkeypatch):
  monkeypatch.setattr(u, '_configure_copy_mop', copy_srca_64_rows)
  n = env('PROBE_TILES', 16)
  pitch_tiles = env('PROBE_PITCH_TILES', 1)        # 1: tiles stored back to back
  width = 32 * pitch_tiles
  rng = np.random.default_rng(0)
  # Distinct-ish BF16 values; avoid NaN/Inf/denormal encodings.
  codes = rng.integers(0x3000, 0x4F00, size=(n // pitch_tiles if pitch_tiles > 1 else n, 32, width), dtype=np.uint16)
  if pitch_tiles == 1:
    tiles = [codes[i] for i in range(n)]
    src = codes.tobytes()
    tile_offset = lambda i: i * 2048
  else:
    rows = codes.reshape(-1, width)                  # (n/pitch_tiles*32, width)
    tiles = [rows[(i // pitch_tiles) * 32:(i // pitch_tiles) * 32 + 32, (i % pitch_tiles) * 32:(i % pitch_tiles) * 32 + 32] for i in range(n)]
    src = rows.tobytes()
    tile_offset = lambda i: (i // pitch_tiles) * 32 * width * 2 + (i % pitch_tiles) * 64
  out_base = TP_OUT
  slots = env('PROBE_SLOTS', 2)
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))

  # --- unpack thread
  cfg = lambda reg: u._engine_cfg(reg, 0)
  u.clear_sources(loader)
  u.configure_unpacker(loader, 0, INPUT_A, u.BF16, u.UnpackTarget.SRCA, commit=False)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR), (0x10 | u.BF16) | 1024 << 16)
  loader.write(cfg(u.UnpackCfg.TILE_DESCRIPTOR) + 4, 1 | 1 << 16)
  loader.write(cfg(u.UnpackCfg.X_DIMENSION), 1024 | 1024 << 16)
  loader.write(cfg(u.UnpackCfg.OPTIONS), (0x20 | u.BF16) | 1 << 9 | (width * 2 // 16) << 16)
  loader.emit(TT.TTSETC16(u.SRCA_SET, 4))
  observed = loader.reg()
  loader.read(observed, cfg(u.UnpackCfg.BASE))
  loader.write(u.UNPACK_CONFIG_SYNC, 0)
  loader.emit(TT.TTSETADCXY(1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCZW(1, 0, 0, 0, 0, 15))
  loader.emit(TT.TTSETADCXX(1, 1023, 0))
  stamp(loader, 0)
  for i in range(n):
    jj, block = i % pitch_tiles, i // pitch_tiles
    # Tile column offset in X (ch0 start, ch1 end); row block in Y, which
    # steps XDim=1024 datums, so one 32-row block of width W is W/32 steps.
    loader.emit(TT.TTSETADC(1, 0, 0, 32 * jj))
    loader.emit(TT.TTSETADC(1, 1, 0, 32 * jj + 1023))
    loader.emit(TT.TTSETADC(1, 0, 1, block * pitch_tiles))
    loader.emit(TT.TTUNPACR(0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1))
    loader.emit(u._srcb_dvalid())
  u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0)
  u.pc_sync(loader)
  stamp(loader, 1)
  # Leave the unpacker counters zeroed: later raw tests assume Y = Z = W = 0.
  loader.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 0xF))
  loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  u.sem_get(loader, u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)

  # --- math thread: Src rows -> Dst slot (i % 2), FP32 Dst
  math.emit(TT.TTSEMINIT(slots, 0, 1 << u.Sem.MATH_PACK))
  u._set_thread_cfg(math, 0, 0)
  dst16 = env('PROBE_DST16', 0)
  u._rmw_cfg_byte(math, u.CFG_BASE + 4, 3, 0x20, 0 if dst16 else 0x20)
  for register, value in ((u.CFG_BASE + 14 * 4, 8), (u.CFG_BASE + 30 * 4, 8), (u.CFG_BASE + 49 * 4, 0)):
    u._set_thread_cfg(math, (register - u.CFG_BASE) >> 2, value)
  copy_srca_64_rows(math, u.UnpackTarget.SRCA, 3)
  stamp(math, 2)
  for i in range(n):
    u.sem_wait(math, u.Sem.MATH_PACK, u.SemWait.ON_MAX, u.Stall.SYNC | u.Stall.MATH | u.Stall.SFPU)
    u.stall(math, u.Stall.CFG, u.Wait.MATH | u.Wait.SFPU)
    u._set_thread_cfg(math, 1, (i % slots) * 64)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    u.run_mop(math)
    u.publish_dst(math)
  u.pc_sync(math)
  stamp(math, 3)
  # Leave the math Dst offset as later raw tests expect it.
  u._set_thread_cfg(math, 1, 0)
  u.pc_sync(math)

  # --- pack thread: de-interleave each Dst slot into panel order, BF16 out
  if dst16:
    u.configure_packer(packer, u.BF16, source_format=u.BF16, dst_fp32=False)
  else:
    u.configure_packer(packer, u.BF16, source_format=u.F32, dst_fp32=True)
  u._set_thread_cfg(packer, u.PACK_ADDRESS_MODIFIER + 0, 4 | 2 << 6)
  u._set_thread_cfg(packer, u.PACK_ADDRESS_MODIFIER + 1, 0x20 | 0x20 << 6)
  packer.write(u.PackCfg.DESTINATION_OFFSET, 0)
  u.load_replay(packer, 0, [
    TT.TTPACR(0, 0, 0, 1 if j == 15 else 0, 0, 0, sel, 0, 0, 0, 0, 0)
    for half, sel in enumerate((0b0101, 0b1010)) for j in range(16)][:31])
  u._set_pack_destination(packer, 0, out_base)
  packer.emit(TT.TTSETADCXX(4, 15, 0))
  stamp(packer, 4)
  for i in range(n):
    u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
    packer.emit(TT.TTSETADC(4, 0, 3, i % slots))          # Dst slot via W (one 64-row tile)
    packer.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xA))
    packer.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
    packer.emit(TT.TTREPLAY(0, 31, 0, 0))
    packer.emit(TT.TTPACR(0, 0, 0, 1, 0, 0, 0b1010, 0, 0, 0, 0, int(i == n - 1)))
    u.stall(packer, u.Stall.SYNC, u.Wait.PACK0)
    u.sem_get(packer, u.Sem.MATH_PACK)
  u.pc_sync(packer)
  stamp(packer, 5)
  packer.emit(TT.TTSEMINIT(1, 0, 1 << u.Sem.MATH_PACK))   # restore the one-slot default
  packer.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xF))
  packer.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
  u.pc_sync(packer)

  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT_A: src, TP_OUT: bytes(n * 2048), STAMPS: bytes(32)})
  out = np.frombuffer(bh.read_l1(bh.core, TP_OUT, n * 2048), '<u2').reshape(n, 2, 32, 16)
  t = np.frombuffer(bh.read_l1(bh.core, STAMPS, 24), '<u4').astype(np.int64)
  for i in range(n):
    want = np.stack([tiles[i][:, :16], tiles[i][:, 16:]])
    np.testing.assert_array_equal(out[i], want, err_msg=f'tile {i}')
  spans = {'unpack': t[1] - t[0], 'math': t[3] - t[2], 'pack': t[5] - t[4]}
  total = max(t[1], t[3], t[5]) - min(t[0], t[2], t[4])
  print(f'\nTIMING n={n} pitch_tiles={pitch_tiles} slots={slots} dst16={dst16}: ' + ', '.join(f'{k}={v} ({v / n:.1f}/tile)' for k, v in spans.items())
        + f'; overall {total} cycles = {total / n:.1f} cycles/tile')
