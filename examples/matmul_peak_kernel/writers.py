"""Limit concurrent DRAM writers without changing interleaved tensor storage."""
from .isa import *
from .mailbox import NcriscMailbox as NM
from .asm import SEM_BASE
from .noc import NOC

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
  fw.read8(t2,NM.MY_Y)
  for wave,cores in enumerate(waves):
    next_wave = fw._new_label('next_writer_wave')
    fw.li(t3,max(y for _,y in cores))
    fw.blt(t3,t2,next_wave)
    if wave:
      fw.li(t3,wave)
      fw.wait_sync_value(GATE,t3,actual=t4)
    fw.j(ready)
    fw.label(next_wave)
  fw.label(ready)


def finish(fw, plan, rows):
  from cq import rectangles
  waves = groups(plan,rows)
  if len(waves) == 1:
    return
  coordinator = plan.cores()[0]
  fw.li(a3,DONE)
  fw.li(a5,coordinator[0] | coordinator[1]<<6)
  fw.local_noc0_coord(a6,x_addr=NM.MY_X,y_addr=NM.MY_Y)
  fw.noc_atomic_inc(1,3,a3,a5,1,a6,a=t3,v=t4)
  done = fw._new_label('writer_finished')
  fw.bne(a5,a6,done)
  fw.noc_cmd_reg(1,0,NOC.REGS_START_ADDR + 0x18,0,addr=t0,tmp=t1)
  count = 0
  for wave in range(1,len(waves)):
    count += len(waves[wave-1])
    fw.li(t3,count)
    fw.wait_sync_value(DONE,t3,actual=t4)
    fw.write32(GATE,wave)
    fw.li(a0,GATE)
    for rect in rectangles(waves[wave]):
      # rectangles() returns inclusive start/end coordinates.
      (x0,y0),(x1,y1) = rect
      fw.noc_mcast_coord(a5,x0,y0,x1,y1,reverse=True)
      fw.li(t5,16)
      fw.noc_write(1,0,a0,a0,0,a5,t5,mcast=True,a=t1,v=t2)
  fw.label(done)
