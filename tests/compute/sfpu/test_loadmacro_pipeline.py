"""Explicit vs scheduled load/multiply/store, with full-Dst oracle guards."""
import pytest
from ttko.isa import Tensix as TT
from tests.operation_pocs.sfpu_movement.test_operations import fixture, finish
from tests.operation_pocs.sfpu_movement import emitters as sf
from tests.movement.unpacker import unpack as u


@pytest.mark.parametrize('schedule',('explicit','macro_serial','macro_pipeline','explicit_replay','macro_replay'))
def test_scale_pipeline(bh,request,schedule):
    loader,math,packer,profile,initial=fixture()
    initial=[(-1 if i%3 else 1) * (i%257 + .125) for i in range(len(initial))]
    sf.loadi(math,6,2.)
    if not schedule.startswith('explicit'):
        math.emit(TT.TTSFPCONFIG(0,15,1))
        math.emit(TT.TTSFPNOP())
        math.emit(TT.TTSFPMUL(6,0,9,12,0))
        # MAD t+1, store t+3. Four rotating registers avoid overwriting an
        # earlier macro's value before its delayed store has consumed it.
        math.emit(TT.TTSFPLOADI(0,8,0x1300))
        math.emit(TT.TTSFPLOADI(0,10,0x8400))
        math.emit(TT.TTSFPCONFIG(0,4,0))
        math.emit(TT.TTSFPCONFIG(3,8,1))
    sf.drain(math)
    u.pc_sync(math)
    profile.record('scale')
    replay=schedule.endswith('_replay')
    body=[]
    for row in range(0,8 if replay else 512,2):
        reg=(row//2)%4
        address=0 if replay else row
        if schedule.startswith('explicit'):
            body.extend((TT.TTSFPLOAD(reg,3,0,address),
                         TT.TTSFPMUL(6,reg,9,reg,0),
                         TT.TTSFPNOP(),TT.TTSFPSTORE(reg,3,0,address)))
        else:
            body.append(TT.TTSFPLOADMACRO(reg,3,0,address))
            if schedule=='macro_serial':body.extend([TT.TTSFPNOP()]*3)
        if replay:body.append(TT.TTINCRWC(0,2,0,0))
    if replay:
        u.load_replay(math,0,body)
        play=TT.TTREPLAY(0,len(body),0,0)
        u.configure_mop(math,u._mop_loop_words(1,64,loop=play,last=play))
        u.run_mop(math)
    else:
        for word in body:math.emit(word)
    for _ in range(4):math.emit(TT.TTSFPNOP())
    sf.drain(math)
    u.pc_sync(math)
    profile.record('scale')
    math.emit(TT.TTSETRWC(0,0,0,0,0,15))
    expected=[v*2 for v in initial]
    finish(bh,request,(loader,math,packer),profile,initial,expected,
           'scale:'+schedule,{'scale':256},elements=len(initial))
