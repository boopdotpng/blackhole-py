"""Late expansion of allocated tile operations into per-core instructions."""
from dataclasses import replace
from hw import cfg, isa
from ..dtype import dtypes
from ..uop import Ops, UOp
from ..isa import vreg
from ..isa.rv32 import RVOps, X, X0, RA, LOCAL_BASE, DEFAULT_WGPR, rv_li, rv_arg, rv_label
from ..isa.tensix import BlackholeRenderer, tt_ins
from .specs import Space, UnpackOp, PackOp, SemOp, StallOp, SfpLoadOp, FpuOp, NocRead, NocGather, IndexTile, NocWrite, NocScatter, NocWait, CbOp, DstZero, MoveToDst
from .sfpu import select_sfpu
from .scalar import select_scalar
from .specs import NocMcastRead, NocMcastForward, McastWait, McastConsumed, McastRelease


FORMATS = {dtypes.fp32: cfg.DataFormat.FLOAT32, dtypes.bf16: cfg.DataFormat.FLOAT16_B,
           dtypes.bfp8: cfg.DataFormat.BFP8_B, dtypes.bfp4: cfg.DataFormat.BFP4_B, dtypes.i32: cfg.DataFormat.INT32, dtypes.u32: cfg.DataFormat.INT32}


def contiguous_group(operands, lanes, itemsize, axis):
  """Prove contiguous addresses and uniform validity for every lane in a run."""
  original = tuple(u.without_after for u in operands)
  ranges = list(dict.fromkeys(u for operand in original for u in operand.toposort() if u.op is Ops.RANGE))
  frozen = {u: UOp.variable(f"_gather_outer_{i}", u.vmin, u.vmax, u.dtype) for i, u in enumerate(ranges)}
  restore = {value: key for key, value in frozen.items()}
  operands = tuple(u.substitute(frozen) for u in original)
  def terms(u, scale, result):
    if u.op in (Ops.ADD, Ops.SUB):
      terms(u.src[0], scale, result)
      terms(u.src[1], scale if u.op is Ops.ADD else -scale, result)
    elif u.op is Ops.MUL and any(s.is_const for s in u.src):
      constant, value = u.src if u.src[0].is_const else reversed(u.src)
      terms(value, scale * constant.val, result)
    else: result[u] = result.get(u, 0) + scale
  placeholder = UOp.special(lanes, "gather_lane")
  for count in (16, 8, 4, 2):
    group = UOp.range(lanes // count, axis, "gather")
    within = UOp.range(count, axis + 1000, "within")
    base, valid = (u.substitute({placeholder: group * count}).simplify() for u in operands)
    offset, predicate = (u.substitute({placeholder: group * count + within}).simplify() for u in operands)
    if predicate is not valid: continue
    difference = {}
    terms(offset, 1, difference); terms(base, -1, difference); terms(within, -itemsize, difference)
    if all(coefficient == 0 for coefficient in difference.values()):
      return group, count, base.substitute(restore), valid.substitute(restore)
  group = UOp.range(lanes, axis, "gather")
  return group, 1, *(u.substitute({placeholder: group}) for u in original)


class Recipes:
  def __init__(self, role, cb_addrs, cb_depths=None, cb_pages=None):
    self.role, self.cb_addrs = role, cb_addrs
    self.cb_depths, self.cb_pages = cb_depths or {}, cb_pages or {}
    self.out = []
    self.thread = {}
    self.config = {}
    self.label_id = 0
    self.fixed_unpack = set()
    self.fixed_fpu_dtype = None
    self.cb_base = {}
    self.cb_word = {}

  def _load_cb_off(self, cb_id):
    reg = vreg(2_000_000 + self.label_id, dtypes.i32, DEFAULT_WGPR, name=f"cb{cb_id}_off")
    self.label_id += 1
    off = UOp.ins(RVOps.LW, (LOCAL_BASE, UOp.const(-512 + 4 * cb_id)), dtypes.i32, *reg)
    self.out.append(off)
    return off

  def cb_addr(self, cb_id):
    if self.cb_depths.get(cb_id, 1) <= 1: return self.cb_addrs[cb_id]
    if cb_id in self.cb_base: return self.cb_base[cb_id]
    return self.cb_addrs[cb_id] + self._load_cb_off(cb_id)

  def cb_word_addr(self, cb_id, offset=0):
    off16 = (offset // 16).simplify() if isinstance(offset, UOp) else offset // 16
    if self.cb_depths.get(cb_id, 1) <= 1:
      base16 = (self.cb_addrs[cb_id] >> 4) - 1
      return (base16 + off16).simplify() if isinstance(off16, UOp) else base16 + off16
    if cb_id in self.cb_word:
      w = self.cb_word[cb_id]
      return w if (isinstance(off16, int) and off16 == 0) or (isinstance(off16, UOp) and off16.is_const and off16.val == 0) else w + off16
    return (((self.cb_addr(cb_id) + offset) >> 4) - 1)

  def tt(self, instruction): self.out.append(tt_ins(instruction, role=self.role))

  def store(self, address, value, readback=False):
    value = value if isinstance(value, UOp) else UOp.const(value, dtypes.u32)
    address = UOp.const(address, dtypes.u32)
    self.out.append(UOp.ins(RVOps.SW, (address, value, UOp.const(0)), dtypes.void))
    if readback:
      loaded = self.load_word(address)
      # This dependency is a hardware completion fence, not a dead value.
      # Keep it explicit at every readback, including repeated loop drains.
      self.out += [loaded, UOp.ins(RVOps.ANDI, (loaded, UOp.const(0)), dtypes.u32, X0)]

  def drain(self): self.store(0xFFE80004, 0, readback=True)

  def call(self, address, values):
    for i, value in enumerate(values):
      value = value if isinstance(value, UOp) else UOp.const(value, dtypes.u32)
      self.out.append(UOp.ins(RVOps.ADDI, (value, UOp.const(0)), dtypes.u32, X[10 + i]))
    # Resident helpers follow the standard RV32 ABI. All caller-saved registers
    # are explicit clobbers, and argument registers are explicit live inputs.
    self.out.append(UOp.ins(RVOps.JALR, (X0, UOp.const(address), *X[10:10 + len(values)]), dtypes.u32,
                            RA, *X[6:8], *X[10:18], *X[28:32]))

  def noc(self, spec, operands):
    import fw
    niu = int(self.role == "ncrisc")
    if isinstance(spec, NocWait): return self.call(fw.FN_NOC_WAIT, (niu, spec.tid, int(spec.acked)))
    base = self.cb_addr(spec.cb_id)
    if isinstance(spec, NocWrite) and spec.blocks != (1, 1):
      _, row, col, *batch = operands
      mf, nf = spec.shape_faces
      batch_row = batch[0] * mf if batch else UOp.const(0)
      for r in range(spec.blocks[0]):
        for c in range(spec.blocks[1]):
          self.call(fw.FN_NOC_WRITE, (niu, rv_arg(spec.param_slot), rv_arg(spec.param_slot, high=True),
                    ((batch_row + row + r) * nf + col + c) * spec.nbytes, spec.nbytes,
                    base + (r * spec.blocks[1] + c) * spec.nbytes, spec.tid))
          call = self.out.pop()
          done = self.label()
          self.out += [UOp.ins(RVOps.BEQ, (done, (row + r < mf) & (col + c < nf), X0), dtypes.void), call, rv_label(done)]
      return
    offset = operands[0] if isinstance(spec, NocRead) else operands[1]
    self.call(fw.FN_NOC_READ if isinstance(spec, NocRead) else fw.FN_NOC_WRITE,
              (niu, rv_arg(spec.param_slot), rv_arg(spec.param_slot, high=True), offset,
               spec.nbytes, base, spec.tid))

  def label(self):
    key = UOp.const(self.label_id); self.label_id += 1
    return key

  def load_word(self, address):
    return UOp.ins(RVOps.LW, (address if isinstance(address, UOp) else UOp.const(address), UOp.const(0)), dtypes.u32)

  def write_word(self, address, value):
    address = address if isinstance(address, UOp) else UOp.const(address)
    value = value if isinstance(value, UOp) else UOp.const(value)
    self.out += [UOp.ins(RVOps.SW, (address, value, UOp.const(0)), dtypes.void), UOp.ins(RVOps.FENCE, (), dtypes.void)]

  def spin(self, address, minimum):
    # Keep the volatile load inside the backedge, rather than selecting it
    # as a reusable scalar expression outside the wait loop.
    address = address if isinstance(address, UOp) else UOp.const(address)
    self.out.append(address)
    key = self.label()
    loaded = self.load_word(address)
    self.out += [rv_label(key), loaded, UOp.ins(RVOps.BLTU, (key, loaded, minimum), dtypes.void),
                 UOp.ins(RVOps.FENCE, (), dtypes.void)]

  def mcast(self, op, operands):
    import fw
    seq = operands[-1]
    if isinstance(op, (McastWait, McastConsumed)):
      base = fw.MCAST_CTRL_BASE + op.ctrl_id * 256
      if isinstance(op, McastWait): self.spin(base + (seq % op.nslots) * 16, seq + 1)
      else:
        self.drain()
        self.write_word(base + 0x90, seq + 1)
      return
    spec = op if isinstance(op, NocMcastRead) else op.stream
    wx, wy = UOp.special(spec.gcols, "worker_x"), UOp.special(spec.grows, "worker_y")
    base = fw.MCAST_CTRL_BASE + spec.ctrl_id * 256
    slot = seq % spec.nslots
    at = slot * 16
    local = self.cb_addrs[spec.cb_id] + slot * spec.slot_stride
    length, me = (spec.gcols, wx) if spec.axis == "x" else (spec.grows, wy) if spec.axis == "y" else (1, UOp.const(0))
    if isinstance(op, McastRelease):
      self.spin(base + 0x90, seq + 1)
      done = self.label()
      target = ((seq + spec.nslots) % length) | (wy << 6) if spec.axis == "x" else wx | (((seq + spec.nslots) % length) << 6) if spec.axis == "y" else wx | (wy << 6)
      self.out.append(UOp.ins(RVOps.BEQ, (done, seq + spec.nslots < spec.total_slabs, X0), dtypes.void))
      self.call(fw.FN_NOC_INC, (1, base + 0x40 + at, target, 4))
      self.out.append(rv_label(done))
      self.call(fw.FN_NOC_WAIT, (1, 4, 0))
      return
    offset, face, limit = operands[:3] if isinstance(op, NocMcastRead) else (UOp.const(0),) * 3
    rect = (wy << 6) | ((spec.gcols - 1) << 12) | (wy << 18) if spec.axis == "x" else wx | (wx << 12) | ((spec.grows - 1) << 18)
    offsets = [(face + b < limit).where(offset + b * spec.strip_stride, 0) for b in range(spec.blocks)]
    done = self.label()
    self.out.append(UOp.ins(RVOps.BNE, (done, me, seq % length), dtypes.void))
    if isinstance(op, NocMcastRead):
      no_credit = self.label()
      self.out.append(UOp.ins(RVOps.BEQ, (no_credit, seq >= spec.nslots, X0), dtypes.void))
      need = self.load_word(base + 0x60 + at) + length
      self.out.append(need)
      self.spin(base + 0x40 + at, need)
      self.write_word(base + 0x60 + at, need)
      self.out.append(rv_label(no_credit))
      for b, off in enumerate(offsets):
        self.call(fw.FN_NOC_READ, (0, rv_arg(spec.param_slot), rv_arg(spec.param_slot, high=True), off,
                                  spec.strip_bytes, local + b * spec.strip_bytes, spec.tid_read))
      self.call(fw.FN_NOC_WAIT, (0, spec.tid_read, 1))
      if spec.axis == "y": self.write_word(base + 0x80, seq + 1)
    else: self.spin(base + 0x80, seq + 1)
    if spec.axis != "y" or isinstance(op, NocMcastForward):
      if spec.axis == "local": self.write_word(base + at, seq + 1)
      else:
        niu = int(spec.axis == "y")
        self.write_word(base + 0x20 + at, seq + 1)
        self.call(fw.FN_NOC_MCAST, (niu, local, local, rect, spec.blocks * spec.strip_bytes, spec.tid_mcast, 1))
        self.call(fw.FN_NOC_MCAST, (niu, base + 0x20 + at, base + at, rect, 4, spec.tid_mcast, 1))
        self.call(fw.FN_NOC_WAIT, (niu, spec.tid_mcast, 0))
    self.out.append(rv_label(done))

  def gather(self, spec, operands):
    import fw
    lane, count, offset, valid = contiguous_group(operands, spec.lanes, spec.itemsize, 10000 + self.label_id)
    self.label_id += 1
    base = self.cb_addr(spec.cb_id)
    address = base + lane * count * spec.itemsize
    zero, done = UOp.const(self.label_id), UOp.const(self.label_id + 1)
    self.label_id += 2
    self.out += [lane, address]
    indirect = {}
    layouts = {slot: (elements, m, n, size) for slot, elements, m, n, size in spec.index_layouts}
    for u in UOp.noop().after(offset, valid).toposort():
      if u.op is not Ops.LOAD: continue
      slot = u.src[0].src[0].arg.slot
      elements, m, n, size = layouts[slot]
      index = u.src[0].src[1].substitute(indirect)
      index = ((index >= 0) & (index < elements)).where(index, 0)
      row, col = index // n % m, index % n
      face = (index // (m * n) * ((m + 7) // 8) + row // 8) * ((n + 15) // 16) + col // 16
      byte_offset = (face * 128 + row % 8 * 16 + col % 16) * size
      scratch = fw.GATHER_INDEX
      self.call(fw.FN_NOC_READ, (0, rv_arg(slot), rv_arg(slot, high=True), byte_offset, size, scratch, spec.tid))
      self.call(fw.FN_NOC_WAIT, (0, spec.tid, 1))
      loaded = UOp.ins(RVOps.LW, (UOp.const(scratch), UOp.const(0)), u.dtype,
                       *vreg(3_000_000 + self.label_id, u.dtype, DEFAULT_WGPR))
      self.label_id += 1
      self.out.append(loaded)
      indirect[u] = loaded
    offset, valid = offset.substitute(indirect), valid.substitute(indirect)
    self.out.append(UOp.ins(RVOps.BEQ, (zero, valid, X0), dtypes.void))
    self.call(fw.FN_NOC_READ, (0, rv_arg(spec.param_slot), rv_arg(spec.param_slot, high=True),
                             offset, count * spec.itemsize, address, spec.tid))
    self.out += [UOp.ins(RVOps.JAL, (done,), dtypes.u32, X0), rv_label(zero)]
    self.out += [UOp.ins(RVOps.SH if spec.itemsize == 2 else RVOps.SW, (address, X0, UOp.const(i * spec.itemsize)), dtypes.void)
                 for i in range(count)]
    self.out.append(rv_label(done))
    self.call(fw.FN_NOC_WAIT, (0, spec.tid, 1))
    self.out.append(UOp.noop().end(lane))

  def scatter(self, spec, operands):
    import fw
    lane, count, offset, valid = contiguous_group(operands[1:], 128, spec.itemsize, 10000 + self.label_id)
    self.label_id += 1
    done = UOp.const(self.label_id); self.label_id += 1
    base = self.cb_addr(spec.cb_id)
    self.out.append(lane)
    self.call(fw.FN_NOC_WRITE, (1, rv_arg(spec.param_slot), rv_arg(spec.param_slot, high=True),
                              offset, count * spec.itemsize, base + lane * count * spec.itemsize, spec.tid))
    write_call = self.out.pop()
    self.out += [UOp.ins(RVOps.BEQ, (done, valid, X0), dtypes.void), write_call, rv_label(done)]
    self.call(fw.FN_NOC_WAIT, (1, spec.tid, 1))
    self.out.append(UOp.noop().end(lane))

  def index_tile(self, spec, operands):
    lane = UOp.range(128, 10000 + self.label_id, "index")
    self.label_id += 1
    base = self.cb_addr(spec.cb_id)
    value, valid = (u.substitute({UOp.special(128, "gather_lane"): lane}) for u in operands)
    self.out += [lane, UOp.ins(RVOps.SW, (base + lane * 4, valid.where(value, 0), UOp.const(0)), dtypes.void),
                 UOp.noop().end(lane)]

  def cb(self, spec):
    # Overlay stream registers hold 16-bit pushed/popped counters reset per
    # dispatch; multi-page CBs track private byte offsets in LOCAL_MEM (-512(gp)).
    base = 0xFFB40000 + (8 + spec.cb_id) * 0x1000
    depth = self.cb_depths.get(spec.cb_id, 1)
    self.out.append(rv_li(base, dtypes.u32, X[30]))
    if spec.kind == "reserve" and depth > 1:
      key = UOp.const(self.label_id); self.label_id += 1
      self.out += [rv_label(key),
                   UOp.ins(RVOps.LHU, (X[30], UOp.const(32)), dtypes.u32, X[31]),
                   UOp.ins(RVOps.LHU, (X[30], UOp.const(40)), dtypes.u32, X[29]),
                   UOp.ins(RVOps.SUB, (X[31], X[29]), dtypes.u32, X[31]),
                   UOp.ins(RVOps.SLLI, (X[31], UOp.const(16)), dtypes.u32, X[31]),
                   UOp.ins(RVOps.SRLI, (X[31], UOp.const(16)), dtypes.u32, X[31]),
                   UOp.ins(RVOps.ADDI, (X0, UOp.const(depth)), dtypes.u32, X[29]),
                   UOp.ins(RVOps.BGEU, (key, X[31], X[29]), dtypes.void)]
    elif spec.kind in ("reserve", "wait"):
      key = UOp.const(self.label_id); self.label_id += 1
      self.out += [rv_label(key),
                   UOp.ins(RVOps.LHU, (X[30], UOp.const(32)), dtypes.u32, X[31]),
                   UOp.ins(RVOps.LHU, (X[30], UOp.const(40)), dtypes.u32, X[29]),
                   UOp.ins(RVOps.BNE if spec.kind == "reserve" else RVOps.BEQ, (key, X[31], X[29]), dtypes.void)]
    elif spec.kind in ("push", "pop"):
      offset = UOp.const(32 if spec.kind == "push" else 40)
      self.out += [UOp.ins(RVOps.LHU, (X[30], offset), dtypes.u32, X[31]),
                   UOp.ins(RVOps.ADDI, (X[31], UOp.const(1)), dtypes.u32, X[31]),
                   UOp.ins(RVOps.FENCE, (), dtypes.void),
                   UOp.ins(RVOps.SW, (X[30], X[31], offset), dtypes.void)]
      if depth > 1:
        page = self.cb_pages[spec.cb_id]
        slot_off = UOp.const(-512 + 4 * spec.cb_id)
        keep = UOp.const(self.label_id); self.label_id += 1
        self.out += [UOp.ins(RVOps.LW, (LOCAL_BASE, slot_off), dtypes.u32, X[31]),
                     rv_li(page, dtypes.u32, X[29]),
                     UOp.ins(RVOps.ADD, (X[31], X[29]), dtypes.u32, X[31]),
                     rv_li(page * depth, dtypes.u32, X[29]),
                     UOp.ins(RVOps.BLTU, (keep, X[31], X[29]), dtypes.void),
                     UOp.ins(RVOps.ADDI, (X0, UOp.const(0)), dtypes.u32, X[31]),
                     rv_label(keep),
                     UOp.ins(RVOps.SW, (LOCAL_BASE, X[31], slot_off), dtypes.void)]
    else: raise ValueError(spec)
    self.out.append(UOp.ins(RVOps.FENCE, (), dtypes.void))
    if depth > 1:
      if spec.kind in ("reserve", "wait"):
        # Load the ring offset once when acquiring the slot so inner loops
        # (e.g. K-prefetched unpacks) reuse it with zero per-iteration overhead.
        off = self._load_cb_off(spec.cb_id)
        if self.role in ("trisc0", "trisc2"):
          word = UOp.const((self.cb_addrs[spec.cb_id] >> 4) - 1) + (off >> 4)
          self.out.append(word)
          self.cb_word[spec.cb_id] = word
        else:
          addr = UOp.const(self.cb_addrs[spec.cb_id]) + off
          self.out.append(addr)
          self.cb_base[spec.cb_id] = addr
      else:
        self.cb_base.pop(spec.cb_id, None)
        self.cb_word.pop(spec.cb_id, None)

  def setc(self, *sets):
    updates = {}
    for setting in sets:
      f = setting.field
      old = updates.get(f.word, self.thread.get(f.word, 0))
      updates[f.word] = (old & ~f.mask) | setting.bits
    for word, value in updates.items():
      if self.thread.get(word) != value: self.tt(isa.SETC16(word=word, value=value))
      self.thread[word] = value

  def rmw(self, *sets):
    updates = {}
    for setting in sets:
      f = setting.field
      if self.config.get(f) == setting.value: continue
      self.config[f] = setting.value
      for byte in range(4):
        mask = (f.mask >> (8 * byte)) & 255
        if not mask: continue
        m, v = updates.get((f.word, byte), (0, 0))
        updates[f.word, byte] = m | mask, (v & ~mask) | ((setting.bits >> (8 * byte)) & mask)
    for (word, byte), (mask, value) in updates.items():
      self.tt((isa.RMWCIB0, isa.RMWCIB1, isa.RMWCIB2, isa.RMWCIB3)[byte](word=word, mask=mask, data=value))

  def prologue(self):
    if self.role == "trisc1":
      fp = cfg.DataFormat.FLOAT32
      self.rmw(cfg.MATH.dst_fmt(fp), cfg.MATH.fp32_dst_acc(1), cfg.MATH.sfpu_fp32_acc(1), cfg.PACK.read_32b(1))
      self.setc(cfg.THREAD.sfpu_dst_fmt_en(1), cfg.THREAD.sfpu_dst_fmt(fp), cfg.THREAD.dst_offset(0))
      self.tt(isa.SEMINIT(max=1, init=1, sems=17))  # free input and output ownership tokens
      self.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait=isa.Wait.TRISC_CFG))
      self.tt(isa.SEMPOST(sems=8))
    elif self.role == "trisc0":
      self.tt(isa.SEMWAIT(stall=isa.Stall.UNPACK | isa.Stall.CFG | isa.Stall.SYNC, sems=8, cond=isa.SemWait.STALL_ON_ZERO))
      self.drain()

  def unpack(self, spec, offset=0):
    # Each input recipe establishes its complete configuration. The same
    # recipe can be reached after different formats at a loop backedge.
    self.config.clear()
    if spec.target in (Space.SRCA, Space.SRCB):
      return self.unpack_source(spec, offset)
    if spec.target is not Space.DST or spec.faces != 1 or spec.rows != 8:
      raise NotImplementedError(f"unpack recipe {spec}")
    # Keep SrcA in context 0 and direct Dst writes in context 1. Switching
    # one context between the two paths can leave SrcA holding stale data.
    u = cfg.UNPACK[0]
    fmt = FORMATS[spec.src_dtype]
    fp = fmt if spec.src_dtype.is_int else cfg.DataFormat.FLOAT32
    self.rmw(u.in_fmt(fmt), u.uncompressed(1), u.y_dim(1), u.out_fmt(fp), u.transpose(0),
             *(f(1) for f in u.disable_zero_compress), u.context_in_fmt[1](fmt), u.context_out_fmt[1](fp),
             u.override_fmt(1), u.row_stride(64), u.face_stride(512), u.add_dst_addr_cntr(1),
             u.z_dim(1), u.x_dim(128), u.tile_x_dim[1](128), u.unpack_to_dst[1](1),
             u.dst_addr[1](64 + spec.dst_slot * 8 * 16))
    self.setc(cfg.THREAD.srca_override_addr(0))
    self.drain()
    self.store(cfg.TENSIX_CFG + 4 * u.base_addr[1].word, self.cb_word_addr(spec.cb_id, offset), readback=True)
    self.tt(isa.SETADCXX(counters=1, x_end=127))
    self.tt(isa.SETADCZW(counters=1, mask=15))
    self.tt(isa.STALLWAIT(stall=isa.Stall.UNPACK, wait=isa.Wait.TRISC_CFG))
    self.tt(isa.UNPACR(ctx=1, steps=0x11, per_ctx=1, last=1))
    self.drain()

  def configure_unpack_source(self, spec):
    if not 1 <= spec.faces <= 4 or spec.src_dtype not in (dtypes.bf16, dtypes.bfp8, dtypes.bfp4): raise NotImplementedError(spec)
    index = 0 if spec.target is Space.SRCA else 1
    u, fmt = cfg.UNPACK[index], FORMATS[spec.src_dtype]
    n = spec.rows * 16
    size = 2 if spec.src_dtype is dtypes.bf16 else 1
    self.rmw(u.in_fmt(fmt), u.uncompressed(1), u.y_dim(1), u.out_fmt(fmt), u.transpose(int(spec.transpose)),
             *(f(1) for f in u.disable_zero_compress), u.context_in_fmt[0](fmt), u.context_out_fmt[0](fmt),
             u.override_fmt(1), u.row_stride(16 * size), u.face_stride(n * size), u.add_dst_addr_cntr(1),
             u.z_dim(1), u.x_dim(n), u.tile_x_dim[0](n), u.unpack_to_dst[0](0), u.dst_addr[0](64))
    if index == 0: self.setc(cfg.THREAD.srca_override_addr(1))

  def unpack_source(self, spec, offset=0):
    if spec.target not in self.fixed_unpack:
      self.configure_unpack_source(spec)
      self.drain()
    index = 0 if spec.target is Space.SRCA else 1
    u, n = cfg.UNPACK[index], spec.rows * 16
    stride = spec.face_stride or (n * 2 if spec.src_dtype is dtypes.bf16 else 16 + n * spec.src_dtype.bits // 8)
    for face in range(spec.faces):
      self.store(cfg.TENSIX_CFG + 4 * u.base_addr[0].word,
                 self.cb_word_addr(spec.cb_id, offset + face * stride), readback=True)
      self.tt(isa.SETADCXX(counters=1 << index, x_end=n - 1))
      self.tt(isa.SETADCZW(counters=1 << index, ch1_z=face, mask=15))
      self.tt(isa.STALLWAIT(stall=isa.Stall.UNPACK, wait=isa.Wait.TRISC_CFG))
      self.tt(isa.UNPACR(unpacker=index, steps=0x11, per_ctx=1, set_dvalid=int(face == spec.faces - 1), last=1))
      self.drain()

  def fpu(self, spec):
    if spec.op != "MVMUL" or spec.k_faces != 1 or not (1 <= spec.m_blocks <= 4 and 1 <= spec.n_blocks <= 4):
      raise NotImplementedError(spec)
    fmt = FORMATS[spec.src_dtype]
    if spec.src_dtype is not self.fixed_fpu_dtype:
      self.rmw(cfg.MATH.srca_fmt(fmt), cfg.MATH.srcb_fmt(FORMATS[dtypes.bf16]))
    if not spec.accumulate: self.tt(isa.ZEROACC(mode=3))
    self.tt(isa.SETRWC(mask=15))
    self.tt(isa.STALLWAIT(stall=isa.Stall.MATH, wait=isa.Wait.SRCA_VLD | isa.Wait.SRCB_VLD))
    for phase in range(spec.fidelity):
      for r in range(spec.m_blocks):
        for c in range(spec.n_blocks):
          last_c = c == spec.n_blocks - 1
          last_rc = last_c and r == spec.m_blocks - 1
          am = 7 if last_rc else 6 if last_c else 5
          self.tt(isa.MVMUL(dst=(spec.dst_slot + r * spec.n_blocks + c) * 8, addr_mod=am,
                            release=3 if last_rc and phase == spec.fidelity - 1 else 0))

  def pack(self, spec, offset=0):
    if spec.blocks != 1:
      for block in range(spec.blocks): self.pack(replace(spec, blocks=1, dst_slot=spec.dst_slot + block), offset + block * 128 * spec.dst_dtype.itemsize)
      return
    if spec.untilize: raise NotImplementedError(f"pack recipe {spec}")
    p, ctx = cfg.PACK, cfg.PACK.ctx[0]
    fmt = FORMATS[spec.dst_dtype]
    fp = fmt if spec.dst_dtype.is_int else cfg.DataFormat.FLOAT32
    size = 4  # Packer address strides describe FP32 Dst reads, not output bytes.
    self.rmw(ctx.disable_zero_compress(1), ctx.out_fmt(fmt), ctx.in_fmt(fp), ctx.exp_section_size(0),
             ctx.pack_per_xy_plane(0), ctx.pack_reads_per_xy_plane(2), p.y_stride(16 * size),
             p.z_stride(128 * size), p.w_stride(128 * size), p.edge_mask[0](0xFFFF))
    pm = cfg.PACK_ADDR_MOD
    self.setc(pm[0].ysrc_incr(4), pm[0].ydst_incr(4))
    self.setc(pm[1].ysrc_clear(1), pm[1].ydst_clear(1), pm[1].zsrc_clear(1))
    self.rmw(ctx.dst_target_offset(spec.dst_slot * 8))
    self.tt(isa.SETADC(counters=4, dim=3, value=0))
    address = self.cb_word_addr(spec.cb_id, offset)
    if isinstance(address, UOp):
      self.tt(isa.STALLWAIT(stall=isa.Stall.CFG, wait=isa.Wait.THCON | isa.Wait.PACK0))
      self.drain()
      self.store(cfg.TENSIX_CFG + 4 * ctx.l1_dest_addr.word, address | (2 << 30), readback=True)
    else:
      self.tt(isa.SETDMAREG(imm=address & 0xFFFF, half_reg=32))
      self.tt(isa.SETDMAREG(imm=2 << 14 | (address >> 16), half_reg=33))
      self.tt(isa.STALLWAIT(stall=isa.Stall.CFG, wait=isa.Wait.THCON | isa.Wait.PACK0))
      self.tt(isa.WRCFG(gpr=16, word=ctx.l1_dest_addr.word))
    self.tt(isa.SETADCXX(counters=4, x_end=15))
    self.tt(isa.SETADCXY(counters=4, mask=11))
    self.tt(isa.SETADCZW(counters=4, mask=5))
    self.tt(isa.STALLWAIT(stall=isa.Stall.CFG, wait=isa.Wait.PACK0))
    self.tt(isa.PACR())
    self.tt(isa.PACR(addr_mod=1, last=1))
    self.drain()

  def lower(self, stream):
    if not stream: return []
    self.prologue()
    # A source unit with one format throughout this core never needs its
    # format/geometry rewritten at a K-loop backedge. Establish it once,
    # retaining per-face address updates and handshakes below.
    unpacks = [u.ins_op for u in stream if u.is_ins and isinstance(u.ins_op, UnpackOp)]
    for target in (Space.SRCA, Space.SRCB):
      candidates = [spec for spec in unpacks if spec.target is target]
      if not candidates or target is Space.SRCA and any(spec.target is Space.DST for spec in unpacks): continue
      if len({(spec.src_dtype, spec.rows, spec.transpose, spec.faces) for spec in candidates}) == 1:
        self.configure_unpack_source(candidates[0])
        self.fixed_unpack.add(target)
    if self.fixed_unpack: self.drain()
    formats = {u.ins_op.src_dtype for u in stream if u.is_ins and isinstance(u.ins_op, FpuOp)}
    if len(formats) == 1:
      self.fixed_fpu_dtype = next(iter(formats))
      self.rmw(cfg.MATH.srca_fmt(FORMATS[self.fixed_fpu_dtype]), cfg.MATH.srcb_fmt(FORMATS[dtypes.bf16]))
    if formats:
      # MVMUL advances its own fidelity counter in issue order. This avoids
      # rewriting ThreadConfig and draining the FPU between every phase.
      self.setc(cfg.THREAD.fidelity_phase(0), cfg.ADDR_MOD[7].srca_incr(0), cfg.ADDR_MOD[7].srcb_incr(0),
                cfg.ADDR_MOD[7].srca_clear(1), cfg.ADDR_MOD[7].srcb_clear(1),
                cfg.ADDR_MOD[7].dst_incr(0), cfg.ADDR_MOD[7].fidelity_incr(1),
                cfg.ADDR_MOD[5].srca_incr(16), cfg.ADDR_MOD[5].srcb_incr(0), cfg.ADDR_MOD[5].dst_incr(0),
                cfg.ADDR_MOD[5].fidelity_incr(0), cfg.ADDR_MOD[6].srca_clear(1), cfg.ADDR_MOD[6].srca_incr(0),
                cfg.ADDR_MOD[6].srcb_incr(8), cfg.ADDR_MOD[6].dst_incr(0), cfg.ADDR_MOD[6].fidelity_incr(0))
    i = 0
    while i < len(stream):
      u = stream[i]
      if u.op is Ops.RANGE and u.arg.name == "fp" and self.role == "trisc1":
        end = next(j for j in range(i + 1, len(stream)) if stream[j].op is Ops.END and u in stream[j].src[1:])
        body = [n for n in stream[i + 1:end] if n.op is not Ops.CONST]
        # Constants are ordinary LREG values; the selector materializes the
        # ones needed by this expression, including constants hoisted by DAG scheduling.
        seen = set(body)
        constants = []
        for node in body:
          for s in node.src_without_body:
            if s.is_const and s not in seen: constants.append(s); seen.add(s)
        self.tt(isa.SETRWC(mask=15))
        self.out += [u, *select_sfpu([*constants, *body])]
        self.tt(isa.INCRWC(dst=2))
        self.out.append(UOp.noop().end(u))
        self.tt(isa.SETRWC(mask=15))
        i = end + 1
        continue
      spec = u.ins_op if u.is_ins else None
      if u.op in (Ops.RANGE, Ops.END):
        # A loop backedge may arrive with the state of its final recipe. Do
        # not elide a first-iteration write needed by later iterations.
        self.config.clear()
        self.thread.clear()
      if isinstance(spec, UnpackOp): self.unpack(spec, u.src_without_body[1] if len(u.src_without_body) > 1 else 0)
      elif isinstance(spec, PackOp): self.pack(spec, u.src_without_body[1] if len(u.src_without_body) > 1 else 0)
      elif isinstance(spec, FpuOp): self.fpu(spec)
      elif isinstance(spec, DstZero): self.tt(isa.ZEROACC(mode=3))
      elif isinstance(spec, MoveToDst):
        self.tt(isa.SETRWC(mask=15))
        self.tt(isa.MOVA2D(src=0, dst=spec.dst_slot * 8, rows=2))
        self.tt(isa.STALLWAIT(stall=isa.Stall.SYNC | isa.Stall.MATH | isa.Stall.SFPU, wait=isa.Wait.MATH))
        self.tt(isa.SETRWC(release=1, mask=15))
      elif isinstance(spec, NocScatter): self.scatter(spec, u.src_without_body)
      elif isinstance(spec, IndexTile): self.index_tile(spec, u.src_without_body)
      elif isinstance(spec, NocGather): self.gather(spec, u.src_without_body)
      elif isinstance(spec, (NocMcastRead, NocMcastForward, McastWait, McastConsumed, McastRelease)): self.mcast(spec, u.src_without_body)
      elif isinstance(spec, (NocRead, NocWrite, NocWait)): self.noc(spec, u.src_without_body)
      elif isinstance(spec, CbOp): self.cb(spec)
      elif isinstance(spec, SemOp):
        if spec.kind == "wait": self.tt(isa.SEMWAIT(stall=isa.Stall.SYNC, sems=1 << spec.sem_id, cond=isa.SemWait.STALL_ON_ZERO))
        elif spec.kind == "get": self.tt(isa.SEMGET(sems=1 << spec.sem_id))
        elif spec.kind == "post": self.tt(isa.SEMPOST(sems=1 << spec.sem_id))
        else: raise ValueError(spec)
      elif isinstance(spec, StallOp):
        self.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait={"math": isa.Wait.MATH | isa.Wait.SFPU, "pack": isa.Wait.PACK0}[spec.engine]))
      elif u.op not in (Ops.RANGE, Ops.END) and any(n.op is Ops.LOAD or n.op is Ops.SPECIAL and n.arg == "gather_lane" for n in u.toposort()):
        # These scalar expressions are templates consumed by gather(), which
        # replaces the lane placeholder with its local RISC-V loop counter.
        pass
      elif u.op is Ops.END: self.out.append(UOp.noop().end(*u.src[1:]))
      # Scalar address expressions are selected at their first recipe use.
      # Keeping their original DAG positions here can put a definition after
      # a newly inserted wait which already needs it (e.g. the ring slot).
      elif u.op is Ops.RANGE or u.is_ins: self.out.append(u)
      i += 1
    return self.out


def compile_core(stream, role, cb_addrs, cb_depths=None, cb_pages=None):
  return BlackholeRenderer().compile_core(select_scalar(Recipes(role, cb_addrs, cb_depths, cb_pages).lower(stream)), fix_sfpu=role == "trisc1")
