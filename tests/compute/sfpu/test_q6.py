"""Blackhole Q6_K decode: compressed DRAM -> L1 -> unsigned unpack -> SFPU -> BF16 L1.

Run: PYTHONPATH=. ../.venv/bin/python -m pytest -qs tests/compute/sfpu/test_q6.py \
       --bh-hardware --bh-core=27

A batch contains 32 GGUF blocks (8192 weights). Loading a model transposes its
byte planes and widens only the 32 block multipliers: 6784 bytes, 6.625 bits/weight.
No RISC performs per-weight decoding. Each SFPU lane owns one independent block.
The hot loop is 8-9 vector instructions for 32 weights: two loads, bit extraction,
CAST, MAD (q*scale - 32*scale), STORE. MOP/Replay handles sixteen positions.

Measured on device 0 / worker 27: ~4110 cycles from L1, ~4910 from DRAM, including
unpack, decode, BF16 pack and final pack completion. MOP with two Dst output slots
was faster than direct Replay here. Timings exclude launch/model-load costs;
this is a single-core batch, not a whole-card bandwidth or inference benchmark.
No DRAM prefetch across batches or subsequent BF16 unpack/matmul is included.

Output is interleaved by SFPU lanes, not the original block-major GGUF order:
  offset(g, p, lane) = g*512 + (p//2)*64 + (lane//8)*16 + (lane%8)*2 + p%2
A consumer must accept this layout or explicitly transpose it. The producer is
not yet fused with a model kernel. BF16 packing uses native nearest/ties-away;
FP32 output is checked exactly (ignoring the sign of zero).

GGUF reference: ggml-org/llama.cpp, ggml/src/ggml-quants.c, dequantize_row_q6_K.
"""
from struct import pack, unpack
from random import Random

import pytest
from asm import Asm
from isa import R, Tensix as TT
from tests.movement.unpacker.unpack import (
  F32, BF16, UnpackTarget, UnpackCfg, Sem, SemWait, Stall, Wait,
  configure_unpacker, configure_fp32_dst, _engine_cfg, _set_thread_cfg,
  configure_mop, _mop_loop_words, load_replay, run_mop,
  configure_packer, PackCfg,
  _unpacr, _rmw_cfg_byte, sem_post, sem_wait, sem_get, stall, pc_sync, publish_dst,
)
from tests.movement.packer.pack import emit_pack_dst_to_cb, _configure_row_addressing, _configure_row_mop, _set_dst_position
from tests.movement.noc import InterleavedConfig, emit_interleaved_dram_to_l1
from tests.profiler import Profiler

INPUT, OUTPUT = 0x50000, 0x60000


def _unpack_bytes(k, address, count):
  configure_unpacker(k, 0, address, BF16, UnpackTarget.DST, commit=False)
  k.write(_engine_cfg(UnpackCfg.TILE_DESCRIPTOR, 0), 14 | 0x10)
  k.write(_engine_cfg(UnpackCfg.OPTIONS, 0), 0x20 | 14)
  k.write(_engine_cfg(UnpackCfg.ADDRESS_XY1, 0), 1 | 16 << 16)
  k.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, 0), 256)
  # UInt8 is format 14 plus SrcAUnsigned, not a five-bit format field.
  _rmw_cfg_byte(k, 0xFFEF0004, 1, 0x80, 0x80)
  k.write(0xFFE80034, 0)
  sem_wait(k, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(k, Sem.MATH_DONE)
  k.emit(TT.TTSETADCXX(1, min(count, 256) - 1, 0))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for _ in k.range(count//256):
    k.emit(_unpacr(0, to_dst=True))
    stall(k, Stall.UNPACK, Wait.UNPACK0)
  if count%256:
    k.emit(TT.TTSETADCXX(1, count%256 - 1, 0))
    k.emit(_unpacr(0, to_dst=True))
  stall(k, Stall.UNPACK, Wait.THCON | Wait.UNPACK0)
  sem_get(k, Sem.UNPACK_SYNC)
  pc_sync(k)
  sem_post(k, Sem.UNPACK_TO_DEST)


def _math_start(k):
  k.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(k, Stall.SYNC, Wait.MATH)
  sem_post(k, Sem.MATH_DONE)
  sem_wait(k, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(k, Sem.UNPACK_TO_DEST)
  configure_fp32_dst(k, 0)
  for register in (12, 28, 47): _set_thread_cfg(k, register, 0)
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTSFPENCC(0, 0, 0, 2))


def test_q6_byte_transport(bh):
  loader, math, packer = (Asm(r) for r in ('trisc0', 'trisc1', 'trisc2'))
  _unpack_bytes(loader, INPUT, 256)
  _math_start(math)
  for addr in range(0, 16, 2):
    math.emit(TT.TTSFPLOAD(0, 5, 0, addr))
    math.emit(TT.TTSFPCAST(0, 0, 0))
    math.emit(TT.TTSFPNOP())
    math.emit(TT.TTSFPSTORE(0, 3, 0, addr + 32))
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)
  count = packer.reg(); packer.li(count, 256)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, dst_element_offset=512, output_format=F32)
  bh.launch({k.role:k.lower() for k in (loader, math, packer)}, l1={INPUT:bytes(range(256)), OUTPUT:bytes(1088)})
  values = unpack('<256f', bh.read_l1(bh.core, OUTPUT, 1024))
  assert values == tuple(range(256)), values[:64]

# A one-time, lossless transpose of 32 GGUF blocks. Adjacent byte planes occupy
# even/odd Dst columns so one SFPLOAD gets the same byte from all 32 blocks.
def transpose_blocks(blocks):
  assert len(blocks) == 32 and all(len(b) == 210 for b in blocks)
  # Only the block multiplier is widened (FP16 -> FP32); all quantized bytes and
  # signed group scales are unchanged. 212 bytes/block versus GGUF's 210.
  blocks = [b[:208] + pack('<f', unpack('<e', b[208:])[0]) for b in blocks]
  data = bytearray(212*32)
  for byte in range(212):
    for lane, block in enumerate(blocks):
      index = byte//2*64 + lane//8*16 + lane%8*2 + byte%2
      data[index] = block[byte]
  return bytes(data)


def _unpack_blocks(k):
  _unpack_bytes(k, INPUT, 212*32)


def _decode_constants(k):
  # L6 = block's FP32 d; L7 = d * signed per-16 scale. All values are runtime data.
  k.emit(TT.TTSFPLOAD(6, 5, 0, 416))
  for byte in range(1, 4):
    k.emit(TT.TTSFPLOAD(2, 5, 0, (208+byte)*2))
    k.emit(TT.TTSFPSHFT(byte*8, 0, 2, 1))
    k.emit(TT.TTSFPOR(2, 6, 6, 1))
  k.emit(TT.TTSFPLOADI(2, 0, 0xC300))  # -128
  k.emit(TT.TTSFPMUL(6, 2, 9, 2, 0))
  k.emit(TT.TTSFPLOADI(4, 2, 15))
  k.emit(TT.TTSFPLOADI(5, 2, 48))
  _set_thread_cfg(k, 13, 0)
  _set_thread_cfg(k, 29, 2)  # STORE address mode 1 advances every Dst view by two rows.


def _decode_group(k, group, replay=False, output_row=448, prepared=False):
  if not prepared: _decode_constants(k)
  k.emit(TT.TTSFPLOAD(7, 5, 0, (192+group)*2))
  k.emit(TT.TTSFPLOADI(3, 2, 128))
  k.emit(TT.TTSFPXOR(0, 3, 7, 0))
  k.emit(TT.TTSFPCAST(7, 7, 0))
  k.emit(TT.TTSFPMAD(6, 7, 2, 7, 0))
  k.emit(TT.TTSFPLOADI(3, 0, 0xC200))  # -32
  k.emit(TT.TTSFPMUL(7, 3, 9, 3, 0))
  # All loads and stores advance together, so Replay needs no dynamic opcodes.
  start = len(k.items)
  for pos in range(1 if replay else 16):
    index = group*16 + pos
    half, within = divmod(index, 128)
    quadrant, lane = divmod(within, 32)
    ql = half*64 + (quadrant%2)*32 + lane
    qh = 128 + half*32 + lane
    k.emit(TT.TTSFPLOAD(0, 5, 0, ql*2))
    k.emit(TT.TTSFPLOAD(1, 5, 0, qh*2))
    if quadrant >= 2: k.emit(TT.TTSFPSHFT((-4)&4095, 0, 0, 1))
    else: k.emit(TT.TTSFPAND(4, 0, 0, 1))
    shift = 4-2*quadrant
    if shift: k.emit(TT.TTSFPSHFT(shift&4095, 0, 1, 1))
    k.emit(TT.TTSFPAND(5, 1, 1, 1))
    k.emit(TT.TTSFPOR(1, 0, 0, 1))
    k.emit(TT.TTSFPCAST(0, 0, 0))
    k.emit(TT.TTSFPMAD(0, 7, 3, 0, 0))
    k.emit(TT.TTSFPSTORE(0, 3, int(bool(replay)), output_row+pos*2))
  if replay:
    words = tuple(k.items[start:]); del k.items[start:]
    if replay == 'mop':
      load_replay(k, 0, words)
      configure_mop(k, _mop_loop_words(16, 1, start=TT.TTREPLAY(0, len(words), 0, 0)))
      run_mop(k)
    else:
      k.emit(TT.TTREPLAY(0, len(words), 1, 1))
      for word in words: k.emit(word)
      for _ in range(15): k.emit(TT.TTREPLAY(0, len(words), 0, 0))
    stall(k, Stall.SYNC, Wait.SFPU)
    k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))


def reference(block, output_format=BF16):
  d = unpack('<e', block[208:])[0]
  scales = unpack('<16b', block[192:208])
  out = []
  for index in range(256):
    half, within = divmod(index, 128)
    quadrant, lane = divmod(within, 32)
    lo = block[half*64+(quadrant%2)*32+lane]
    hi = block[128+half*32+lane]
    q = ((lo >> (4 if quadrant>=2 else 0)) & 15) | (((hi>>(2*quadrant))&3)<<4)
    value = d * scales[index//16] * (q-32)
    bits = unpack('<I', pack('<f', value))[0]
    # The packer rounds halfway cases away from zero, not to even.
    out.append(bits if output_format == F32 else ((bits + 0x8000)>>16)&0xffff)
  return out


@pytest.mark.parametrize('group', range(16))
@pytest.mark.parametrize('output_format', (BF16, F32))
def test_q6_decode(bh, group, output_format):
  rng = Random(42)
  blocks = [rng.randbytes(192) + bytes((i*17+b*7)&255 for i in range(16)) + pack('<e', d)
            for b,d in enumerate([0., 2**-24, -2**-24, 2**-14, -0.125, 0.03125, 1., 65504.]*4)]
  loader, math, packer = (Asm(r) for r in ('trisc0', 'trisc1', 'trisc2'))
  _unpack_blocks(loader)
  _math_start(math)
  profile = Profiler(math)
  pc_sync(math)
  profile.record('decode')
  _decode_group(math, group, replay=True)
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  profile.record('decode')
  publish_dst(math)
  count = packer.reg(); packer.li(count, 512)
  emit_pack_dst_to_cb(packer, 7, OUTPUT, count, output_format=output_format)
  size = 2048 if output_format == F32 else 1024
  bh.launch({k.role:k.lower() for k in (loader, math, packer)},
            l1={INPUT:transpose_blocks(blocks), OUTPUT:b'\xa5'*(size+64)}, profiler=profile)
  words = unpack('<512I' if output_format == F32 else '<512H', bh.read_l1(bh.core, OUTPUT, size))
  assert bh.read_l1(bh.core, OUTPUT+size, 64) == b'\xa5'*64
  refs = [reference(b, output_format) for b in blocks]
  magnitude = 0x7fffffff if output_format == F32 else 0x7fff
  for pos in range(16):
    for lane in range(32):
      at = pos//2*64 + lane//8*16 + lane%8*2 + pos%2
      got, expected = words[at], refs[lane][group*16+pos]
      assert got == expected or got & magnitude == expected & magnitude == 0, (group,pos,lane,hex(got),hex(expected))

@pytest.mark.parametrize('row', (0, 64, 128, 256, 416))
def test_q6_large_transport(bh, row):
  data = bytes((i//64)%256 for i in range(6784))
  loader, math, packer = (Asm(r) for r in ('trisc0','trisc1','trisc2'))
  _unpack_blocks(loader)
  _math_start(math)
  math.emit(TT.TTSFPLOAD(0,5,0,row))
  math.emit(TT.TTSFPCAST(0,0,0))
  math.emit(TT.TTSFPNOP())
  math.emit(TT.TTSFPSTORE(0,3,0,448))
  publish_dst(math)
  count=packer.reg(); packer.li(count,64)
  emit_pack_dst_to_cb(packer,7,OUTPUT,count,output_format=F32)
  bh.launch({k.role:k.lower() for k in (loader,math,packer)},l1={INPUT:data})
  values=unpack('<64f',bh.read_l1(bh.core,OUTPUT,256))
  assert values[::2] == (row//4,)*32, values


@pytest.mark.parametrize('pipeline', (False, True))
@pytest.mark.parametrize('strategy', ('mop', 'replay'))
@pytest.mark.parametrize('dram', (False, True))
def test_q6_full_batch(bh, pipeline, strategy, dram):
  rng = Random(7)
  blocks = [rng.randbytes(208)+pack('<e', rng.uniform(-.2,.2)) for _ in range(32)]
  loader, math, packer = (Asm(r) for r in ('trisc0','trisc1','trisc2'))
  source = transpose_blocks(blocks)
  params, extra = (), []
  initialization = {OUTPUT:b'\xa5'*(16384+64), 0x70000:bytes(8)}
  if dram:
    buffer = bh.dram_buffer(len(source), initial=source)
    params = (buffer.address, len(source))
    reader = Asm('brisc')
    reader.wait(0x70000, 1, bytes=4)
    config = InterleavedConfig(bh.dram_coordinates(banks=1), INPUT, depth=1,
                               page_bytes=len(source), standalone=True)
    emit_interleaved_dram_to_l1(reader, config)
    reader.write(0x70004, 1)
    extra.append(reader)
    loader.wait(0x70004, 1, bytes=4)
  else: initialization[INPUT] = source
  _unpack_blocks(loader)
  profile = Profiler(math)
  profile.record('batch')
  if dram: math.write(0x70000, 1)
  # Published slots include the one currently being read by the packer.
  math.emit(TT.TTSEMINIT(2 if pipeline else 1, 0, 1 << Sem.MATH_PACK))
  _math_start(math)
  if strategy == "replay": _decode_constants(math)
  for group in range(16):
    sem_wait(math, Sem.MATH_PACK, SemWait.ON_MAX, Stall.SYNC | Stall.SFPU)
    _decode_group(math, group, replay=strategy, output_row=448+(32*(group%2) if pipeline else 0), prepared=strategy == "replay")
    publish_dst(math)
  # A separate completion token drains both slots before stopping the timer.
  sem_wait(math, 3, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, 3)
  pc_sync(math)
  profile.record('batch')

  configure_packer(packer, BF16)
  _configure_row_addressing(packer)
  _configure_row_mop(packer, 32, close=True)
  destination = packer.reg(); packer.li(destination, ((OUTPUT>>4)-1) | 0x80000000)
  for index in packer.range(16):
    sem_wait(packer, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.SYNC | Stall.PACK | Stall.CFG)
    pc_sync(packer)
    _set_dst_position(packer, 7, 0)
    if pipeline:
      even = packer._new_label("even_page")
      parity = packer.reg(); packer.andi(parity, index, 1)
      packer.beq(parity, R.ZERO, even)
      _set_dst_position(packer, 7, 512)
      packer.label(even)
    packer.write(PackCfg.L1_DESTINATION, destination)
    packer.write(PackCfg.DESTINATION_OFFSET, 0)
    packer.emit(TT.TTSETADCXX(4, 15, 0))
    run_mop(packer)
    stall(packer, Stall.SYNC, Wait.PACK0)
    pc_sync(packer)
    sem_get(packer, Sem.MATH_PACK)
    packer.addi(destination, destination, 64)
  sem_post(packer, 3)
  images = {k.role:k.lower() for k in (loader,math,packer,*extra)}
  cycles = []
  for _ in range(3):
    bh.launch(images, params=params, l1=initialization, profiler=profile)
    cycles.append(profile.last['batch'])
  values = unpack('<8192H', bh.read_l1(bh.core, OUTPUT, 16384))
  refs = [reference(b) for b in blocks]
  for group in range(16):
    for pos in range(16):
      for lane in range(32):
        at = group*512 + pos//2*64 + lane//8*16 + lane%8*2 + pos%2
        expected = refs[lane][group*16+pos]
        assert values[at] == expected or values[at]&0x7fff == expected&0x7fff == 0, (group,pos,lane,hex(values[at]),hex(expected))
  assert bh.read_l1(bh.core, OUTPUT+16384, 64) == b'\xa5'*64
  print(f"{strategy=} {pipeline=} {dram=}: {cycles} cycles / 8192 weights")
