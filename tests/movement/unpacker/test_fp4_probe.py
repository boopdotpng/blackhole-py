"""8x16 packed E2M1 bit-pattern probe; this does not implement an FP4 dtype.

Run with -s to retain FP4_PROBE observations. BFP4's forced exponent lets the
unpacker consume exactly 64 payload bytes, without a tile exponent header.
Source snapshots and multiply-by-one use separate launches of the same loader.
"""
import json
import math
import struct

import pytest

from asm import Asm
from fw.consts import TensixL1
from isa import Tensix as TT
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.fpu.emit import prepare, execute
from tests.operation_pocs.fpu.observation import emit_pack_dst_to_cb


BFP4 = 7  # Hardware BFP4_b: sign + three magnitude bits, eight-bit exponent.
INPUT_A = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_B = INPUT_A + 4096
OUTPUT = INPUT_B + 4096
E2M1 = (0., .5, 1., 1.5, 2., 3., 4., 6.)
# Every row includes every code, with different permutations to expose ordering.
CODES = tuple((column + 3 * row) % 16 for row in range(8) for column in range(16))
PACKED = bytes(CODES[i] | CODES[i + 1] << 4 for i in range(0, 128, 2))


def e2m1(code):
    return (-1 if code & 8 else 1) * E2M1[code & 7]


def bf16(values):
    return b''.join(struct.pack('<H', struct.unpack('<I', struct.pack('<f', v))[0] >> 16) for v in values)


def images(bank, exponent, operation, *, control=False):
    loader, compute, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
    u.clear_sources(loader)
    for engine, address in enumerate((INPUT_A, INPUT_B)):
        target = (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB)[engine]
        u.configure_unpacker(loader, engine, address, u.BF16, target, commit=False)
        if engine == bank and not control:
            # Start from the tested BF16 transport; change only the format and
            # forced exponent. Register strides remain 16-bit expanded values.
            loader.write(u._engine_cfg(u.UnpackCfg.TILE_DESCRIPTOR, engine),
                         BFP4 | 0x10 | ((128 if engine else 0) << 16))
            loader.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine), 0x20 | BFP4)
            loader.write(u._engine_cfg(u.UnpackCfg.OPTIONS, engine) + 4, 0x103)
            loader.write(u.ADDR_MISC[engine], exponent | (0x100 if engine == 0 else 0))
        loader.write(u._engine_cfg(u.UnpackCfg.X_DIMENSION, engine), 128 | 128 << 16)
    observed = loader.reg()
    loader.read(observed, u._engine_cfg(u.UnpackCfg.BASE, 0))
    loader.write(u.UNPACK_CONFIG_SYNC, 0)
    loader.emit(TT.TTSETADCXX(3, 127, 0))
    loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR | u.Wait.SRCB_CLR)
    u.configure_mop(loader, u._mop_loop_words(
        1, 1, start=u._unpacr(0), loop=u._unpacr(1),
        last=u._unpacr(1), outer_last=u._unpacr(1)))
    u.run_mop(loader)
    u.stall(loader, u.Stall.UNPACK, u.Wait.UNPACK0 | u.Wait.UNPACK1)
    u.sem_get(loader, u.Sem.UNPACK_SYNC)
    u.pc_sync(loader)

    u.sem_wait(compute, u.Sem.MATH_PACK, u.SemWait.ON_MAX, u.Stall.SYNC)
    u.configure_fp32_dst(compute, 0)
    u.stall(compute, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
    if operation == 'snapshot':
        # Observe native BF16 source bits; avoid MOVA/B2D's TF32 interpretation
        # when FP32 Dst is enabled. The packer writes the BF16 bits unchanged.
        u._rmw_cfg_byte(compute, u.PackCfg.ALU_FORMAT, 3, 0x20, 0)
        for reg in (12, 28, 47): u._set_thread_cfg(compute, reg, 0)
        compute.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
        if bank == 0:
            compute.emit(TT.TTMOVA2D(0, 0, 0, 2, 0))
        else:
            for row in (0, 4): compute.emit(TT.TTMOVB2D(0, row, 0, 4, row))
        u.stall(compute, u.Stall.SYNC, u.Wait.MATH)
        u.pc_sync(compute)
    else:
        compute.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
        u.stall(compute, u.Stall.SYNC, u.Wait.MATH)
        prepare(compute, 'elwmul', 0, 0, 0, fidelity=2, repeats=1)
        execute(compute)
    compute.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
    u.publish_dst(compute)
    count = packer.reg()
    packer.li(count, 128)
    emit_pack_dst_to_cb(packer, 0, OUTPUT, count,
                        output_format=u.BF16 if operation == 'snapshot' else u.F32)
    return {k.role: k.lower() for k in (loader, compute, packer)}


def run(bh, bank, exponent, operation, *, control=False):
    operand = bf16(map(e2m1, CODES)) if control else PACKED
    # Distinct padding catches payload overreads affecting the 128 observations.
    operands = [bf16([1.] * 128), bf16([1.] * 128)]
    operands[bank] = operand
    data = {address: payload + b'\xa5' * 256
            for address, payload in zip((INPUT_A, INPUT_B), operands)}
    data[OUTPUT] = b'\xa5' * 576
    bh.launch(images(bank, exponent, operation, control=control), l1=data)
    size = 256 if operation == 'snapshot' else 512
    raw = bh.read_l1(bh.core, OUTPUT, size)
    assert bh.read_l1(bh.core, OUTPUT + size, 576 - size) == b'\xa5' * (576 - size)
    for address, payload in data.items():
        if address != OUTPUT: assert bh.read_l1(bh.core, address, len(payload)) == payload
    if operation == 'snapshot':
        return tuple(struct.unpack('<f', struct.pack('<I', bits << 16))[0]
                     for bits in struct.unpack('<128H', raw))
    return struct.unpack('<128f', raw)


@pytest.mark.parametrize('bank', (0, 1), ids=('srca', 'srcb'))
@pytest.mark.parametrize('exponent', (128, 129))
def test_raw_fp4_probe(bh, bank, exponent):
    control = tuple(map(e2m1, CODES))
    assert run(bh, bank, exponent, 'snapshot', control=True) == control
    assert run(bh, bank, exponent, 'multiply', control=True) == control
    snapshot = run(bh, bank, exponent, 'snapshot')
    product = run(bh, bank, exponent, 'multiply')
    expected = tuple((-math.inf if code == 8 else
                      (-1 if code & 8 else 1) * (code & 7) * 2. ** (exponent - 129))
                     for code in CODES)
    record = dict(core=list(bh.core), bank=bank, exponent=exponent,
                  packed_hex=PACKED.hex(), codes=list(CODES[:16]),
                  e2m1=list(control[:16]), snapshot=list(snapshot[:16]),
                  multiply_by_one=list(product[:16]))
    # JSON strings for non-finite values keep the record valid JSON.
    for key in ('snapshot', 'multiply_by_one'):
        record[key] = [value if math.isfinite(value) else str(value) for value in record[key]]
    print('FP4_PROBE ' + json.dumps(record, sort_keys=True))
    assert snapshot == expected
    assert product == expected
