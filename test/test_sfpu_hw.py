"""Blackhole silicon verification for compiler/blackhole/sfpu.py."""
import os, struct, time, unittest
from types import SimpleNamespace
import numpy as np
from hw import cfg, isa
from compiler import UOp, dtypes
from compiler.blackhole.sfpu import SfpuRenderer, select_sfpu
from compiler.blackhole.specs import SfpLoadOp, SfpReduceLanes, SfpStoreOp
from compiler.isa.tensix import encode_tensix

L1_DONE = 0x1F000
L1_IN_BASE = 0x20000
L1_OUT_BASE = 0x30000
SEM_MATH_PACK = 1 << 1
SEM_UNPACK_DONE = 1 << 2
SEM_CFG_READY = 1 << 3
ADDR_MOD_STEP = 6  # dst += 2


class _Asm:
  def __init__(self): self.words: list[int] = []
  def rv(self, word: int): self.words.append(word)
  def tt(self, word: int): self.words.append(isa.inline(word))

  def li(self, rd: int, val: int):
    val &= 0xFFFFFFFF
    lo = val & 0xFFF
    if lo >= 0x800: lo -= 0x1000
    hi = ((val - lo) >> 12) & 0xFFFFF
    if hi:
      self.rv(isa.lui(rd=rd, imm=hi))
      if lo: self.rv(isa.addi(rd=rd, rs1=rd, imm=lo))
    else:
      self.rv(isa.addi(rd=rd, rs1=0, imm=lo))

  def store32(self, addr: int, val: int):
    self.li(5, addr)
    self.li(6, val)
    self.rv(isa.sw(rs1=5, rs2=6, imm=0))

  def store32_readback(self, addr: int, val: int):
    self.store32(addr, val)
    self.rv(isa.lw(rd=6, rs1=5, imm=0))
    self.rv(isa.andi(rd=6, rs1=6, imm=0))

  def drain(self):
    self.li(5, 0xFFE80004)
    self.rv(isa.sw(rs1=5, rs2=0, imm=0))
    self.rv(isa.lw(rd=6, rs1=5, imm=0))
    self.rv(isa.andi(rd=6, rs1=6, imm=0))

  def setc16(self, *sets):
    placed = cfg.words(sets)
    assert len(placed) == 1
    (word, val), = placed.items()
    self.tt(isa.SETC16(word=word, value=val))

  def rmw(self, *sets):
    by_byte: dict[tuple[int, int], tuple[int, int]] = {}
    for s in sets:
      assert s.field.space is cfg.Space.CONFIG
      for i in range(4):
        mask = (s.field.mask >> (8 * i)) & 0xFF
        if mask:
          m, v = by_byte.get((s.field.word, i), (0, 0))
          by_byte[(s.field.word, i)] = (m | mask, v | ((s.bits >> (8 * i)) & mask))
    for (word, i), (mask, v) in by_byte.items():
      self.tt((isa.RMWCIB0, isa.RMWCIB1, isa.RMWCIB2, isa.RMWCIB3)[i](mask=mask, data=v, word=word))

  def to_bytes(self) -> bytes:
    return struct.pack(f"<{len(self.words)}I", *self.words)


def _build_trisc0(num_inputs: int) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  u = cfg.UNPACK[0]
  a.tt(isa.SEMWAIT(stall=isa.Stall.UNPACK | isa.Stall.CFG | isa.Stall.SYNC, sems=SEM_CFG_READY, cond=isa.SemWait.STALL_ON_ZERO))
  a.drain()
  a.rmw(
    u.in_fmt(fp), u.uncompressed(1), u.y_dim(1), u.out_fmt(fp), u.transpose(0),
    *(f(1) for f in u.disable_zero_compress),
    u.context_in_fmt[0](fp), u.context_out_fmt[0](fp), u.override_fmt(1),
    u.row_stride(64), u.face_stride(1024), u.add_dst_addr_cntr(1),
    u.z_dim(4), u.x_dim(256), u.tile_x_dim[0](256), u.unpack_to_dst[0](1),
  )
  a.setc16(cfg.THREAD.srca_override_addr(0))
  for t in range(num_inputs):
    l1_addr = L1_IN_BASE + t * 4096
    a.rmw(u.dst_addr[0](64 + (t * 64) * 16))
    a.drain()
    a.store32_readback(cfg.TENSIX_CFG + 4 * u.base_addr[0].word, (l1_addr >> 4) - 1)
    a.tt(isa.SETADCXX(counters=1, x_end=255))
    a.tt(isa.SETADCZW(counters=1, mask=15))
    a.tt(isa.STALLWAIT(stall=isa.Stall.UNPACK, wait=isa.Wait.TRISC_CFG))
    for _ in range(4):
      a.tt(isa.UNPACR(steps=0x11, per_ctx=1, last=1))
    a.drain()
  a.tt(isa.SEMPOST(sems=SEM_UNPACK_DONE))
  return a.to_bytes()


def _build_trisc1(passes) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  a.rmw(cfg.MATH.dst_fmt(fp), cfg.MATH.fp32_dst_acc(1), cfg.MATH.sfpu_fp32_acc(1), cfg.PACK.read_32b(1))
  a.setc16(cfg.THREAD.sfpu_dst_fmt_en(1), cfg.THREAD.sfpu_dst_fmt(fp))
  a.setc16(cfg.THREAD.dst_offset(0))
  m = cfg.ADDR_MOD[ADDR_MOD_STEP]
  a.tt(isa.SETC16(word=m.words[0]))
  a.setc16(m.dst_incr(2))
  a.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait=isa.Wait.TRISC_CFG))
  a.tt(isa.SEMPOST(sems=SEM_CFG_READY))
  a.tt(isa.SEMWAIT(stall=isa.Stall.MATH | isa.Stall.SYNC | isa.Stall.SFPU, sems=SEM_UNPACK_DONE, cond=isa.SemWait.STALL_ON_ZERO))

  for p in passes:
    a.tt(isa.SETRWC(mask=15))
    for w in p.prologue: a.tt(w)
    if p.footprints == 1:
      for w in p.body: a.tt(w)
    else:
      a.rv(isa.addi(rd=5, rs1=0, imm=p.footprints))
      loop_start = len(a.words)
      for w in p.body: a.tt(w)
      a.rv(isa.addi(rd=5, rs1=5, imm=-1))
      a.rv(isa.bne(rs1=5, rs2=0, imm=(loop_start - len(a.words)) * 4))
    a.tt(isa.SETRWC(mask=15))
    a.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait=isa.Wait.SFPU))
    for w in p.epilogue: a.tt(w)

  a.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait=isa.Wait.MATH | isa.Wait.SFPU))
  a.tt(isa.SEMPOST(sems=SEM_MATH_PACK))
  return a.to_bytes()


def _build_trisc2(out_tiles: list[int]) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  p = cfg.PACK
  ctx = p.ctx[0]
  a.tt(isa.SEMWAIT(stall=isa.Stall.TDMA | isa.Stall.PACK | isa.Stall.SYNC, sems=SEM_MATH_PACK, cond=isa.SemWait.STALL_ON_ZERO))
  a.rmw(
    ctx.disable_zero_compress(1), ctx.out_fmt(fp), ctx.in_fmt(fp), ctx.exp_section_size(0),
    ctx.pack_per_xy_plane(0), ctx.pack_reads_per_xy_plane(16),
    p.y_stride(16 * 4), p.z_stride(256 * 4), p.w_stride(1024 * 4), p.edge_mask[0](0xFFFF),
  )
  pm = cfg.PACK_ADDR_MOD
  a.setc16(pm[0].ysrc_incr(4), pm[0].ydst_incr(4))
  a.setc16(pm[1].ysrc_clear(1), pm[1].ydst_clear(1), pm[1].zsrc_clear(1))

  for idx, tile in enumerate(out_tiles):
    l1_out = L1_OUT_BASE + idx * 4096
    a.tt(isa.SETADC(counters=4, dim=3, value=tile))
    addr16 = (l1_out >> 4) - 1
    gpr = 16
    a.tt(isa.SETDMAREG(imm=addr16 & 0xFFFF, half_reg=2 * gpr))
    a.tt(isa.SETDMAREG(imm=2 << 14 | (addr16 >> 16) & 0xFFFF, half_reg=2 * gpr + 1))
    a.tt(isa.STALLWAIT(stall=isa.Stall.CFG, wait=isa.Wait.THCON | isa.Wait.PACK0))
    a.tt(isa.WRCFG(gpr=gpr, word=ctx.l1_dest_addr.word))
    a.tt(isa.SETADCXX(counters=4, x_end=15))
    a.tt(isa.SETADCXY(counters=4, mask=11))
    a.tt(isa.SETADCZW(counters=4, mask=5))
    a.tt(isa.STALLWAIT(stall=isa.Stall.CFG, wait=isa.Wait.PACK0))
    for j in range(16):
      a.tt(isa.PACR(addr_mod=1 if j == 15 else 0, last=int(j == 15)))
    a.tt(isa.STALLWAIT(stall=isa.Stall.SYNC, wait=isa.Wait.PACK0))

  a.drain()
  a.store32(L1_DONE, 1)
  a.rv(isa.fence())
  return a.to_bytes()


def run_sfpu_passes_on_silicon(dev, passes, input_tiles: list[np.ndarray], out_tile_list: list[int]) -> list[np.ndarray]:
  data: dict[int, bytes] = {L1_DONE: struct.pack("<I", 0)}
  for i, arr in enumerate(input_tiles):
    data[L1_IN_BASE + i * 4096] = np.ascontiguousarray(arr, dtype=np.float32).reshape(1024).tobytes()
  images = {
    "brisc": b"",
    "trisc0": _build_trisc0(len(input_tiles)),
    "trisc1": _build_trisc1(passes),
    "trisc2": _build_trisc2(out_tile_list),
  }
  core = dev.workers[0]
  dev.run(images, data=data, cores=[core])
  deadline = time.monotonic() + 5.0
  while struct.unpack("<I", dev.read_l1(core, L1_DONE, 4))[0] != 1:
    if time.monotonic() > deadline: raise TimeoutError("SFPU kernel timed out")
    time.sleep(0.001)
  return [np.frombuffer(dev.read_l1(core, L1_OUT_BASE + idx * 4096, 4096), dtype=np.float32).copy()
          for idx in range(len(out_tile_list))]


def _select_expr(fn):
  a = UOp.ins(SfpLoadOp(0), (), dtypes.fp32, role="trisc1")
  b = UOp.ins(SfpLoadOp(8), (), dtypes.fp32, role="trisc1")
  store = UOp.ins(SfpStoreOp(0), (fn(a, b),), dtypes.void, role="trisc1")
  return select_sfpu(store.toposort())


@unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
class TestSfpuSilicon(unittest.TestCase):
  def test_transcendental_ranges(self):
    from device import Device
    rng = np.random.default_rng(7)
    signed = np.tile(rng.uniform(-20., 20., 128).astype(np.float32), 8)
    positive = np.tile(np.geomspace(1e-5, 1e5, 128).astype(np.float32), 8)
    masked = np.tile(np.linspace(-128., 8., 128).astype(np.float32), 8)
    masked[0] = -np.inf
    cases = [(lambda a, b: a.silu(), signed, signed / (1. + np.exp(-signed))),
             (lambda a, b: a.exp2(), masked, np.exp2(masked)),
             (lambda a, b: a.sqrt(), positive, np.sqrt(positive)),
             (lambda a, b: a.recip(), signed, 1. / signed),
             (lambda a, b: a.sin(), signed * 50., np.sin(signed * 50.))]
    for index in (0, 1):
      dev = Device(index)
      try:
        for fn, values, expected in cases:
          words = tuple(encode_tensix(u, SfpuRenderer()) for u in _select_expr(fn))
          passes = [SimpleNamespace(prologue=(), body=(*words, isa.INCRWC(dst=2)), epilogue=(), footprints=4)]
          with self.subTest(card=index, fn=fn):
            actual = run_sfpu_passes_on_silicon(dev, passes, [values, values], [0])[0]
            np.testing.assert_allclose(actual[:128], expected[:128], rtol=3e-6, atol=2e-6)
            dev.synchronize()
      finally: dev.close()

  def test_face_expressions_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(42)
    a = rng.uniform(.2, 3., 1024).astype(np.float32)
    b = rng.uniform(-2., 2., 1024).astype(np.float32)
    cases = [(lambda a, b: a + b, a + b), (lambda a, b: a * b - 2.0, a * b - 2.0),
             (lambda a, b: a.recip(), 1. / a),
             (lambda a, b: (a < b).where(a, b), np.where(a < b, a, b)),
             (lambda a, b: a.exp2(), np.exp2(a)), (lambda a, b: a.sqrt(), np.sqrt(a)),
             (lambda a, b: a.sin(), np.sin(a)), (lambda a, b: a.silu(), a / (1. + np.exp(-a))),
             (lambda a, b: a.log2(), np.log2(a)),
             (lambda a, b: a.cast(dtypes.i32).cast(dtypes.fp32), np.trunc(a)),
             (lambda a, b: a.cast(dtypes.bf16).cast(dtypes.fp32),
              ((a.view(np.uint32) + 0x7FFF + ((a.view(np.uint32) >> 16) & 1)) & 0xFFFF0000).view(np.float32)),
             (lambda a, b: a.silu() * b, (a / (1. + np.exp(-a))) * b)]
    for op in ("add", "max"):
      expected = a.copy()
      for start in (0, 64):
        for parity in (0, 1):
          indices = np.arange(start + parity, start + 64, 2)
          expected[indices] = np.sum(a[indices]) if op == "add" else np.max(a[indices])
      cases.append((lambda a, b, op=op: UOp.ins(SfpReduceLanes(op), (a,), dtypes.fp32, role="trisc1"), expected))
    denom = a.copy()
    for start in (0, 64):
      for parity in (0, 1):
        indices = np.arange(start + parity, start + 64, 2)
        denom[indices] = np.sqrt(np.mean(a[indices] ** 2) + 1e-5)
    cases.append((lambda a, b: a * (UOp.ins(SfpReduceLanes("add"), (a * a,), dtypes.fp32, role="trisc1") / 32. + 1e-5).rsqrt(), a / denom))
    for index in (0, 1):
      dev = Device(index)
      try:
        for fn, expected in cases:
          words = tuple(encode_tensix(u, SfpuRenderer()) for u in _select_expr(fn))
          passes = [SimpleNamespace(prologue=(), body=(*words, isa.INCRWC(dst=2)), epilogue=(), footprints=4)]
          with self.subTest(card=index, fn=fn):
            actual = run_sfpu_passes_on_silicon(dev, passes, [a, b], [0])[0]
            np.testing.assert_allclose(actual[:128], expected[:128], rtol=2e-6, atol=2e-6)
            dev.synchronize()
      finally: dev.close()


if __name__ == "__main__":
  unittest.main()
