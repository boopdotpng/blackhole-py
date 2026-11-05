"""Probe: which DRAM -> L1 NoC read alignments copy bytes correctly on Blackhole?

Background for BFP blocks of 272 / 544 bytes packed into 1088-byte DRAM pages:

* device.py only routes DRAM buffers through the CQ DramCopy path when the
  page size is a multiple of 64 (otherwise it falls back to PCIe TLB copies).
  That is a host-side choice, not a device rule.
* tt-metal's Blackhole noc_parameters.h sets NOC_DRAM_READ_ALIGNMENT_BYTES 64
  and NOC_L1_{READ,WRITE}_ALIGNMENT_BYTES 16.
* tt-isa-documentation (WormholeB0/NoC/Alignment.md; Blackhole says "similar,
  not identical") states the rule as congruence, not absolute alignment: a
  read from DRAM into L1 needs SrcAddress % 32 == DstAddress % 32, else
  UndefinedBehavior.  Blackhole NoC flits are 64 bytes (vs 32 on Wormhole),
  which suggests mod 64 there.

Each case issues one NoC read from a DRAM bank into sentinel-filled L1 with a
chosen (src % 64, dst % 64, length) and reports whether the destination holds
the source bytes, whether anything outside it was written, and, if wrong,
which byte shift explains the data.  Run with -s for PROBE_NOC records.

Observed on card 1 (all cases, one read each):
* correct  <=>  src % 64 == dst % 64.  Absolute alignment is irrelevant
  (16/32/48 phases and 100-byte lengths work); congruence mod 32 is not
  enough, and neither is a 64-byte-aligned DRAM source on its own.
* a phase mismatch never hangs and never writes outside [dst, dst+len); the
  bytes arrive shifted by the phase difference (64-byte flits keep their low
  address bits), i.e. silent corruption.
"""
import json
import struct

import pytest

from asm import Asm
from firmware.consts import TensixL1
from ttko.isa import R
from tests.movement.noc import (
  NIU0, NIU_CONFIG, LOGICAL_NODE_ID, STATUS, REQUESTS_OUTSTANDING, RESPONSE_MARKED,
  TID, _initialize_command, _submit, _wait_command_ready, _wait_zero,
)

L1_SLOT = TensixL1.DATA_BUFFER_SPACE_BASE + 0x1000   # 64-byte aligned
SLOT_BYTES = 0x1000
SENTINEL = 0xA5
DRAM_BYTES = 8192
# 16-bit little-endian counter: any byte shift is identifiable.
PATTERN = b''.join(struct.pack('<H', i ^ 0x5A5A) for i in range(DRAM_BYTES // 2))

# name: (src offset in DRAM buffer, dst offset in L1 slot, length)
CASES = {
  # Congruent mod 64.
  'aligned_1088': (0, 0, 1088),
  'mod64_16_272': (272, 16, 272),        # second 272 B block of a 1088 B page
  'mod64_32_544': (544, 32, 544),        # second 544 B block
  'mod64_48_272': (816, 48, 272),        # fourth 272 B block
  'len100_aligned': (0, 0, 100),         # length not a multiple of 16
  'len100_mod64_16': (272, 16, 100),
  # Congruent mod 32, not mod 64 (the Wormhole rule would allow this).
  'mod32_only_0_32': (64, 32, 256),
  'mod32_only_16_48': (272, 48, 272),
  # Not congruent mod 32: undefined per the ISA document.
  'src_aligned_dst16': (0, 16, 272),     # satisfies tt-metal's "DRAM read 64 B aligned"
  'src16_dst_aligned': (272, 0, 272),    # e.g. reading block 1 to an aligned CB slot
  'src16_dst32': (272, 32, 272),
}


def read_kernel(dram_address, dram_coordinate, dst, length):
  k = Asm('brisc')
  niu, command, coordinate, local = k.reg(4)
  k.li(niu, NIU0)
  k.li(command, NIU0)                    # NoC 0, command buffer 0
  k.li(local, NIU0 + NIU_CONFIG + LOGICAL_NODE_ID)
  k.lw(local, local)
  k.slli(local, local, 20)
  k.srli(local, local, 20)
  _wait_zero(k, niu, STATUS + REQUESTS_OUTSTANDING + TID * 4)
  _initialize_command(k, command, RESPONSE_MARKED, TID)
  source, target, count = k.reg(3)
  k.li(source, dram_address)
  k.li(coordinate, dram_coordinate)
  k.li(target, dst)
  k.li(count, length)
  _submit(k, command, source_address=source, source_coordinate=coordinate,
          target_address=target, target_coordinate=local, byte_count=count)
  _wait_command_ready(k, command)
  _wait_zero(k, niu, STATUS + REQUESTS_OUTSTANDING + TID * 4)
  k.fence()
  return {'brisc': k.lower()}


@pytest.fixture(scope='module')
def dram(bh):
  buffer = bh.dram_buffer(DRAM_BYTES, bank=0, initial=PATTERN)
  return buffer, bh.dram_coordinates(0, banks=1)[0]


@pytest.mark.parametrize('name', CASES)
def test_dram_to_l1_read_alignment(bh, dram, name):
  buffer, coordinate = dram
  src_off, dst_off, length = CASES[name]
  src = buffer.address + src_off
  dst = L1_SLOT + dst_off
  assert buffer.address % 64 == 0
  bh.launch(read_kernel(src, coordinate, dst, length),
            l1={L1_SLOT: bytes([SENTINEL]) * SLOT_BYTES})
  got = bh.read_l1(bh.core, L1_SLOT, SLOT_BYTES)
  want = PATTERN[src_off:src_off + length]
  body = got[dst_off:dst_off + length]
  outside = [i for i, x in enumerate(got) if not dst_off <= i < dst_off + length and x != SENTINEL]
  shift = None
  if body != want:
    # Which source offset (relative to the requested one) does each written byte come from?
    for d in range(-64, 65):
      lo = max(0, -d - src_off)
      if PATTERN[src_off + d + lo:src_off + d + length] == body[lo:] and lo < length:
        shift = d
        break
  record = dict(case=name, src_mod64=src % 64, dst_mod64=dst % 64, length=length,
                congruent_mod32=src % 32 == dst % 32, congruent_mod64=src % 64 == dst % 64,
                correct=body == want, wrong_bytes=sum(x != y for x, y in zip(body, want)),
                first_wrong=next((i for i, (x, y) in enumerate(zip(body, want)) if x != y), None),
                explained_by_src_shift=shift,
                writes_outside=[hex(L1_SLOT + i) for i in outside[:4]], n_writes_outside=len(outside))
  print('PROBE_NOC ' + json.dumps(record))
  assert record['correct'] == record['congruent_mod64']
  assert not outside
