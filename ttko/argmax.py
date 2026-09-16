"""BF16 argmax scan in FP32 Dst: 32 ordered-key/index candidates.

Caller owns Dst, initializes address modifiers to zero, and drains before
observing the result. L0/L4 hold winning keys/physical indices. This preserves
first-logical-index ties for either face-tiled or sequential input. NaNs are
outside the logit contract. Finish 32 candidates on RISC-V, choosing the lower
logical index for equal keys. Key >> 15 is the scalar sortable BF16 key.
"""
from ttko.isa import Tensix as TT


def scan_bf16(k, tiles, *, tilized=True):
    if not 1 <= tiles <= 8:
        raise ValueError('argmax owns 1..8 FP32 Dst tiles')
    k.emit(TT.TTSFPENCC(0, 0, 0, 2))
    k.emit(TT.TTSFPLOADI(0, 2, 0))
    k.emit(TT.TTSFPLOADI(4, 2, 0))
    k.emit(TT.TTSFPLOADI(3, 8, 0x8000))
    k.emit(TT.TTSFPLOADI(3, 10, 0))
    k.emit(TT.TTSFPCONFIG(12, 15, 1))  # index swap + capture on SFPLOAD
    # Traversal must be increasing in logical index within each lane, including
    # across the left/right faces, so equal positive keys retain the first ID.
    rows = ([face + row + col for face in (0, 32) for row in range(0, 16, 4)
             for col in (0, 2, 16, 18)] if tilized else list(range(0, 64, 2)))
    for tile in range(tiles):
        for row in rows:
            k.emit(TT.TTSFPLOAD(1, 3, 0, tile * 64 + row))
            # Monotonic nonnegative integer key. BF16 has sixteen zero low
            # bits, so dropping bit zero loses no ordering information.
            k.emit(TT.TTSFPSHFT((-31) & 4095, 1, 2, 7))
            k.emit(TT.TTSFPOR(0, 3, 2, 0))
            k.emit(TT.TTSFPXOR(0, 2, 1, 0))
            k.emit(TT.TTSFPSHFT(4095, 1, 1, 1))
            k.emit(TT.TTSFPSWAP(0, 0, 1, 1))
            k.emit(TT.TTSFPNOP())
    # TEN-2932 forbids most arithmetic writes to L4..L7 in index mode.
    k.emit(TT.TTSFPCONFIG(0, 15, 1))


def physical_to_logical(k, index, result, *, tilized):
    if not tilized:
        k.mv(result, index)
        return
    with k.scope():
        temp = k.reg()
        k.andi(result, index, -1024)
        k.andi(temp, index, 512)
        k.or_(result, result, temp)
        k.andi(temp, index, 256)
        k.srli(temp, temp, 4)
        k.or_(result, result, temp)
        k.andi(temp, index, 240)
        k.slli(temp, temp, 1)
        k.or_(result, result, temp)
        k.andi(temp, index, 15)
        k.or_(result, result, temp)


def load_bf16(program, address, tiles):
    """Copy full L1 tiles to FP32 Dst for scan_bf16, preserving signed zero.

    Use one full-tile unpack per source bank, with an explicit math handshake.
    The face-streaming copy path cannot supply the full-register-row reads used
    here. The caller makes the L1 input ready before entering the unpack stream.
    """
    from firmware.consts import TensixMMIO
    from ttko import DType
    from ttko.mop import LoopTemplate
    from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_post, sem_wait, stall, sync
    from ttko.unpack import UnpackTarget, _unpacr

    if not 1 <= tiles <= 8:
        raise ValueError('argmax owns 1..8 FP32 Dst tiles')
    program.fpu.dst.require_fp32()
    loader, math, unpack = program.trisc0, program.trisc1, program.unpack
    program.fpu._wait_for_dst()
    program.fpu._configure_dst(0)
    program.fpu._rmw_cfg_byte(TensixMMIO.CFG_BASE + 8, 0, 1, 1)
    for register in (12, 28, 47): program.fpu._set_thread_cfg(register, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    for tile in range(tiles):
        sem_wait(loader, Sem.MATH_DONE, SemWait.STALL_ON_ZERO, Stall.UNPACK)
        sem_get(loader, Sem.MATH_DONE)
        for target in (UnpackTarget.SRCA, UnpackTarget.SRCB):
            unpack._configure_l1(DType.BF16, target, address + tile * 2048, None,
                                 commit=False, configure_mop=False)
        unpack._commit_config(TensixMMIO.CFG_BASE + 0x130)
        loader.emit(TT.TTSETADCXX(3, 1023, 0))
        loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
        stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
        unpack._mop.configure(LoopTemplate(outer=1, inner=1,
            start=_unpacr(0), loop=_unpacr(1), last=_unpacr(1), outer_last=_unpacr(1)))
        unpack._mop.run()
        stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
        sem_get(loader, Sem.UNPACK_SYNC)
        sync(loader)
        sem_post(loader, Sem.UNPACK_TO_DEST)

        stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
        sem_post(math, Sem.MATH_DONE)
        sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.STALL_ON_ZERO, Stall.SYNC)
        sem_get(math, Sem.UNPACK_TO_DEST)
        stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
        for row in range(0, 64, 8):
            math.emit(TT.TTMOVA2D(0, row, 0, 2, tile * 64 + row))
        math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
        stall(math, Stall.SYNC, Wait.MATH)
    stall(math, Stall.SFPU, Wait.MATH)
