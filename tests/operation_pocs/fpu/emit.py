"""Allocation-scoped FPU recipes; fixture transport is deliberately separate."""
from ttko.isa import Tensix as TT
from tests.movement.unpacker.unpack import (
    _set_thread_cfg, _mop_loop_words, configure_mop, load_replay, run_mop,
    stall, pc_sync, Stall, Wait,
)

OPS = ('elwadd', 'elwsub', 'elwmul', 'mvmul', 'gapool', 'gmpool',
       'zero', 'a2d', 'b2d', 'd2a', 'd2b')


def prepare(k, op, a, b, dst, *, broadcast=0, accumulate=True, fidelity=2, repeats=16, fp32=True):
    """Configure one repeated operation. Slots: A/B 0..7, FP32 Dst 0..63.

    Caller configures formats and owns valid math source banks. Dst addresses
    are relative to tile zero. Returns instruction words for review/reuse.
    Modifier 0 is stationary; 1 increments fidelity; 2 resets fidelity.
    """
    if op not in OPS: raise ValueError(op)
    if not (0 <= a < 8 and 0 <= b < 8 and 0 <= dst < (64 if fp32 else 128)): raise ValueError('slot')
    if op in ('mvmul', 'gapool', 'gmpool') and a % 2: raise ValueError('A pair alignment')
    if broadcast not in range(4) or fidelity not in (1, 2): raise ValueError('mode')
    if op not in ('elwadd', 'elwsub') and not accumulate: raise ValueError('accumulation is intrinsic')
    _set_thread_cfg(k, 1, 0)
    _set_thread_cfg(k, 11, 0)
    for index, phase in ((0, 0), (1, 1 << 13), (2, 1 << 15)):
        _set_thread_cfg(k, 12 + index, 0)
        _set_thread_cfg(k, 28 + index, phase)
        _set_thread_cfg(k, 47 + index, 0)
    k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    if op.startswith('elw') or op in ('mvmul', 'gapool', 'gmpool'):
        for _ in range(a): k.emit(TT.TTINCRWC(0, 0, 0, 8))
        for _ in range(b): k.emit(TT.TTINCRWC(0, 0, 8, 0))
    d = dst * 8
    def word(mod):
        if op in ('elwadd', 'elwsub'): return getattr(TT, 'TT' + op.upper())(0, int(accumulate), broadcast, mod, d)
        if op == 'elwmul': return TT.TTELWMUL(0, 0, broadcast, mod, d)
        if op == 'mvmul': return TT.TTMVMUL(0, 0, mod, d)
        if op == 'gapool': return TT.TTGAPOOL(0, 0, mod, 0, d)
        if op == 'gmpool': return TT.TTGMPOOL(0, 1, mod, 0, d)
    if op in ('elwmul', 'mvmul', 'gapool') and fidelity == 2:
        words = (word(1), word(2))
    elif op in ('elwadd', 'elwsub', 'elwmul', 'mvmul', 'gapool', 'gmpool'):
        words = (word(0),)
    elif op == 'zero':
        # Eight single-row invalidations: 16-row ZEROACC would exceed ownership.
        words = tuple(TT.TTZEROACC(0, int(fp32), 0, 0, d + row) for row in range(8))
    elif op == 'a2d': words = (TT.TTMOVA2D(0, a * 8, 0, 2, d),)
    elif op == 'b2d': words = tuple(TT.TTMOVB2D(0, b * 8 + row, 0, 4, d + row) for row in (0, 4))
    else:
        fn, slot = (TT.TTMOVD2A, a) if op == 'd2a' else (TT.TTMOVD2B, b)
        words = tuple(fn(0, slot * 8 + row, 0, 2, d + row) for row in (0, 4))
    load_replay(k, 0, words)
    replay = TT.TTREPLAY(0, len(words), 0, 0)
    configure_mop(k, _mop_loop_words(1, repeats, loop=replay, last=replay))
    return words


def execute(k):
    """Run prepared operation batch and drain FPU through PC synchronization."""
    run_mop(k)
    stall(k, Stall.SYNC, Wait.MATH)
    pc_sync(k)
