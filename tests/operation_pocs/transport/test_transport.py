"""Raw transport correctness and retained seven-sample cycle evidence."""
import json
import os
from statistics import median
from struct import pack
from pathlib import Path
import pytest
from asm import Asm
from firmware.consts import TensixL1
from tests.profiler import Profiler
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.transport.ops import pack_exact

BASE = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT = BASE
OUTPUT = BASE + 0x9000
SCRATCH = BASE + 0xA000
OBSERVE = BASE + 0xB000


def runtime(k, index=0):
  value = k.reg()
  k.read(value, TensixL1.PARAM_BASE + index * 4)
  return value


def pack_images(slot, fmt):
  loader, math, packer = [Asm(role) for role in ('trisc0', 'trisc1', 'trisc2')]
  for tile in range(8):
    size = loader.reg()
    loader.li(size, 4096)
    u.emit_unpack_to_dst(loader, INPUT + tile * 4096, size, tile, 0)
    u.sem_post(math, u.Sem.MATH_DONE)
    u.sem_wait(math, u.Sem.UNPACK_TO_DEST, u.SemWait.ON_ZERO, u.Stall.SYNC)
    u.sem_get(math, u.Sem.UNPACK_TO_DEST)
  u.publish_dst(math)
  u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
  u.pc_sync(packer)
  profile = Profiler(packer)
  count = runtime(packer)
  profile.record('empty')
  profile.record('empty')
  profile.record('pack complete')
  pack_exact(packer, dst_slot=slot, output=OUTPUT, count=count, scratch=SCRATCH, output_format=fmt, profile=profile)
  profile.record('pack complete')
  # Observe all Dst only after operation completes; no intervening writes.
  for tile in range(8):
    u.emit_pack_dst(packer, tile, OBSERVE + tile * 4096, u.F32, wait_for_dst=False, configure=(tile == 0))
  return {k.role: k.lower() for k in (loader, math, packer)}, profile


def evidence(bh, operation, fmt, slot, n, samples):
  record = dict(operation=operation, dtype=fmt, slot=slot, N=n, K=1,
                samples=samples, min=min(samples), median=median(samples), max=max(samples),
                device=os.getenv('TRANSPORT_DEVICE', 'see queue metadata'), core=str(bh.core),
                job=os.getenv('TT_QUEUE_JOB_ID', 'see queue logs'), warmup=1)
  print('TRANSPORT_JSON ' + json.dumps(record))


@pytest.mark.parametrize('slot', [0, 31, 63])
@pytest.mark.parametrize('fmt', [u.BF16, u.F32])
def test_pack_all_prefixes(bh, slot, fmt):
  images, profile = pack_images(slot, fmt)
  words = [((0x3F00 + i % 128) << 16) | ((i * 1031) & 0xFFFF) for i in range(8192)]
  source = pack('<8192I', *words)
  lengths = [int(x) for x in os.getenv('TRANSPORT_LENGTHS', ','.join(map(str, range(1,129)))).split(',')]
  for n in lengths:
    values = words[slot*128:slot*128+n]
    expected = pack(f'<{n}H', *[((x+0x8000)>>16) for x in values]) if fmt == u.BF16 else pack(f'<{n}I', *values)
    samples, controls, copies = [], [], []
    for iteration in range(8):
      bh.launch(images, params=(n,), l1={INPUT:source, OUTPUT-64:b'\xA5'*704,
                SCRATCH-64:b'\xA5'*704, OBSERVE:b'\xA5'*32768}, profiler=profile)
      actual = bh.read_l1(bh.core, OUTPUT-64, 704)
      assert actual == b'\xA5'*64 + expected + b'\xA5'*(640-len(expected))
      assert bh.read_l1(bh.core, SCRATCH-64, 64) == b'\xA5'*64
      assert bh.read_l1(bh.core, SCRATCH+576, 64) == b'\xA5'*64
      assert bh.read_l1(bh.core, OBSERVE, 32768) == source
      if iteration:
        samples.append(profile.last['pack complete'])
        controls.append(profile.last['empty'])
        copies.append(profile.last['exact final copy'])
    evidence(bh, 'pack exact', fmt, slot, n, samples)
    evidence(bh, 'marker control', fmt, slot, n, controls)
    evidence(bh, 'exact final copy', fmt, slot, n, copies)
