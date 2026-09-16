"""Limit concurrent DRAM writers without changing interleaved tensor storage."""
from ttko.isa import R, Tensix as TT
from ttko.registers import NcriscMailbox as NM
from .asm import SEM_BASE
from ttko.noc import NOC

DONE = SEM_BASE + 64
GATE = SEM_BASE + 80


def groups(plan, rows):
  if not rows:
    return [list(plan.cores())]
  return [[(x,y) for y in plan.rows[i:i+rows] for x in plan.cols]
          for i in range(0,len(plan.rows),rows)]


def wait_turn(fw, plan, rows):
  waves = groups(plan,rows)
  if len(waves) == 1:
    return
  ready = fw._new_label('writer_ready')
  fw.read8(R.T2,NM.MY_Y)
  for wave,cores in enumerate(waves):
    next_wave = fw._new_label('next_writer_wave')
    fw.li(R.T3,max(y for _,y in cores))
    fw.blt(R.T3,R.T2,next_wave)
    if wave:
      fw.li(R.T3,wave)
      fw.wait_sync_value(GATE,R.T3,actual=R.T4)
    fw.j(ready)
    fw.label(next_wave)
  fw.label(ready)


def finish(fw, plan, rows):
  from cq import rectangles
  waves = groups(plan,rows)
  if len(waves) == 1:
    return
  coordinator = plan.cores()[0]
  fw.li(R.A3,DONE)
  fw.li(R.A5,coordinator[0] | coordinator[1]<<6)
  fw.local_noc0_coord(R.A6,x_addr=NM.MY_X,y_addr=NM.MY_Y)
  fw.noc_atomic_inc(1,3,R.A3,R.A5,1,R.A6,a=R.T3,v=R.T4)
  done = fw._new_label('writer_finished')
  fw.bne(R.A5,R.A6,done)
  fw.noc_cmd_reg(1,0,NOC.REGS_START_ADDR + 0x18,0,addr=R.T0,tmp=R.T1)
  count = 0
  for wave in range(1,len(waves)):
    count += len(waves[wave-1])
    fw.li(R.T3,count)
    fw.wait_sync_value(DONE,R.T3,actual=R.T4)
    fw.write32(GATE,wave)
    fw.li(R.A0,GATE)
    for rect in rectangles(waves[wave]):
      # rectangles() returns inclusive start/end coordinates.
      (x0,y0),(x1,y1) = rect
      fw.noc_mcast_coord(R.A5,x0,y0,x1,y1,reverse=True)
      fw.li(R.T5,16)
      fw.noc_write(1,0,R.A0,R.A0,0,R.A5,R.T5,mcast=True,a=R.T1,v=R.T2)
  fw.label(done)
