"""8x16 MVMUL fringes; source banks retain their four-face storage layout."""
from ttko.isa import R, Tensix as TT
from ttko.registers import Stall, Wait, DType


def emit_subblock(fw, plan):
  fw.edge_shapes = set()
  done = fw._new_label('edge_body_done')

  def body(m, n, width):
    for inner in range(plan.in0_block_w):
      kk = max(0, min(32, width - inner*32))
      if not kk:
        continue
      for row in range(plan.out_subblock_h):
        mm = max(0, min(32, m - row*32))
        if not mm:
          continue
        for col in range(plan.out_subblock_w):
          nn = max(0, min(32, n - col*32))
          if not nn:
            continue
          tile = row*plan.out_subblock_w + col
          fw.mv(R.T1,R.T3)
          if tile:
            fw.addi(R.T1,R.T1,tile*64)
          fw.write32(0xFFE40000,R.T1)
          shape = (mm,nn,kk)
          if shape == (32,32,32):
            fw.emit(TT.TTMOP(1,0,0))
          elif 0 in shape:
            fw.jal(R.RA,'edge_empty')
          else:
            fw.edge_shapes.add(shape)
            fw.jal(R.RA,'edge_' + '_'.join(map(str,shape)))
        fw.emit(TT.TTSETRWC(2,0,0,0,0,15))
    fw.j(done)

  axes = ((R.S4,plan.m_extent,plan.out_subblock_h*32,plan.in0_num_subblocks),
          (R.S5,plan.n_extent,plan.out_subblock_w*32,plan.in1_num_subblocks),
          (R.S6,plan.k_extent,plan.in0_block_w*32,plan.num_blocks))
  def choose(axis, shape):
    if axis == 3:
      body(*shape)
      return
    reg,extent,block,count = axes[axis]
    full,tail = divmod(extent,block)
    if full >= count:
      choose(axis+1,shape+[block])
    elif not full:
      choose(axis+1,shape+[tail])
    else:
      normal = fw._new_label('normal_extent')
      fw.li(R.T0,full)
      fw.blt(reg,R.T0,normal)
      choose(axis+1,shape+[tail])
      fw.label(normal)
      choose(axis+1,shape+[block])
  choose(0,[])
  fw.label(done)


def emit_functions(fw, plan):
  from . import kernel as k
  shapes = fw.edge_shapes
  fw.label('edge_empty')
  # Even an empty product must consume the unpacker's SrcA bank handoff.
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, Wait.SRCA_VLD | Wait.SRCB_VLD))
  fw.emit(TT.TTSETRWC(1, 0, 0, 0, 0, 15))
  fw.jalr(R.ZERO, R.RA, 0)
  for m, n, inner in sorted(shapes):
    fw.label(f'edge_{m}_{n}_{inner}')
    if (m,n,inner) == (32,32,32):
      fw.emit(TT.TTMOP(1, 0, 0))
    else:
      fw.emit(TT.TTSETRWC(0,0,0,0,0,15))
      current_a = current_b = 0
      for kk in range(0,inner,16):
        for nn in range(0,n,16):
          for mm in range(0,m,8):
            a = (kk//16)*32 + (nn//16)*16
            b = (mm//16)*32 + (kk//16)*16 + mm%16
            dst = (mm//16)*32 + (nn//16)*16 + mm%16
            reset_a, reset_b = a < current_a, b < current_b
            if reset_a or reset_b:
              fw.emit(TT.TTSETRWC(0,0,0,0,0,int(reset_a) | int(reset_b)<<1))
              if reset_a: current_a = 0
              if reset_b: current_b = 0
            da,db = a-current_a,b-current_b
            while da or db:
              sa,sb = min(15,da),min(15,db)
              fw.emit(TT.TTINCRWC(0,0,sb,sa))
              da -= sa; db -= sb
            if k.INPUT_DTYPE != DType.FP8:
              fw.emit(TT.TTMVMUL(addr_mode=3,dst=dst))
            fw.emit(TT.TTMVMUL(addr_mode=7,dst=dst))
            current_a,current_b = a,b+8
      fw.emit(TT.TTSETRWC(1, 0, 0, 0, 0, 15))
    fw.jalr(R.ZERO, R.RA, 0)
