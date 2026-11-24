"""End-to-end Blackhole p100a silicon verification for compiler/sfpu.py.

Runs compiled SFPU passes from `compile_sfpu()` directly on worker core 0 of a real Blackhole card:
  trisc1 configures FP32 Dst -> signals Sem 3
  trisc0 unpacks FP32 input tiles from L1 straight into Dst -> signals Sem 2
  trisc1 runs every CompiledSfpuPass (prologue + 32-footprint loop of body + epilogue) -> signals Sem 1
  trisc2 packs output Dst tile(s) back to L1 -> sets L1_DONE = 1
Host compares output tiles bit-for-bit / within tolerance against NumPy.
"""
import math, struct, time, unittest
import numpy as np
from hw import cfg, isa
from device import Device
from compiler import Ops, Space, UOp, compile_sfpu, compile_sfpu_loop, dtypes, mulacc

L1_DONE = 0x1F000
L1_IN_BASE = 0x20000
L1_OUT_BASE = 0x30000
SEM_MATH_PACK = 1 << 1
SEM_UNPACK_DONE = 1 << 2
SEM_CFG_READY = 1 << 3
ADDR_MOD_STEP = 6  # dst += 2


class _Asm:
  def __init__(self): self.words: list[int] = []
  def rv(self, name: str, **kw): self.words.append(isa.rv(name, **kw))
  def tt(self, word: int): self.words.append(isa.inline(word))

  def li(self, rd: int, val: int):
    val &= 0xFFFFFFFF
    lo = val & 0xFFF
    if lo >= 0x800: lo -= 0x1000
    hi = ((val - lo) >> 12) & 0xFFFFF
    if hi:
      self.rv("lui", rd=rd, imm=hi)
      if lo: self.rv("addi", rd=rd, rs1=rd, imm=lo)
    else:
      self.rv("addi", rd=rd, rs1=0, imm=lo)

  def store32(self, addr: int, val: int):
    self.li(5, addr)
    self.li(6, val)
    self.rv("sw", rs1=5, rs2=6, imm=0)

  def store32_readback(self, addr: int, val: int):
    self.store32(addr, val)
    self.rv("lw", rd=6, rs1=5, imm=0)
    self.rv("andi", rd=6, rs1=6, imm=0)

  def drain(self):
    # COPROCESSOR_DONE_CHECK (PC_BUF + 4): store, load, consume
    self.li(5, 0xFFE80004)
    self.rv("sw", rs1=5, rs2=0, imm=0)
    self.rv("lw", rd=6, rs1=5, imm=0)
    self.rv("andi", rd=6, rs1=6, imm=0)

  def setc16(self, *sets):
    placed = cfg.words(sets)
    assert len(placed) == 1
    (word, val), = placed.items()
    self.tt(isa.SETC16(word, val))

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
      self.tt(isa.tensix(f"RMWCIB{i}", mask, v, word))

  def to_bytes(self) -> bytes:
    return struct.pack(f"<{len(self.words)}I", *self.words)


def _build_trisc0(num_inputs: int) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  u = cfg.UNPACK[0]
  a.tt(isa.SEMWAIT(isa.Stall.UNPACK | isa.Stall.CFG | isa.Stall.SYNC, SEM_CFG_READY, isa.SemWait.STALL_ON_ZERO))
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
    a.tt(isa.SETADCXX(1, 255, 0))
    a.tt(isa.SETADCZW(1, 0, 0, 0, 0, 15))
    a.tt(isa.STALLWAIT(isa.Stall.UNPACK, isa.Wait.TRISC_CFG))
    for _ in range(4):
      a.tt(isa.UNPACR(Unpack_block_selection=0, AddrMode=0x11, CfgContextId=0, OvrdThreadId=1, Last=1))
    a.drain()
  a.tt(isa.SEMPOST(SEM_UNPACK_DONE))
  return a.to_bytes()


def _build_trisc1(passes) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  a.rmw(
    cfg.MATH.dst_fmt(fp), cfg.MATH.fp32_dst_acc(1), cfg.MATH.sfpu_fp32_acc(1),
    cfg.PACK.read_32b(1),
  )
  a.setc16(cfg.THREAD.sfpu_dst_fmt_en(1), cfg.THREAD.sfpu_dst_fmt(fp))
  a.setc16(cfg.THREAD.dst_offset(0))
  m = cfg.ADDR_MOD[ADDR_MOD_STEP]
  a.tt(isa.SETC16(m.words[0], 0))
  a.setc16(m.dst_incr(2))
  a.tt(isa.STALLWAIT(isa.Stall.SYNC, isa.Wait.TRISC_CFG))
  a.tt(isa.SEMPOST(SEM_CFG_READY))
  a.tt(isa.SEMWAIT(isa.Stall.MATH | isa.Stall.SYNC | isa.Stall.SFPU, SEM_UNPACK_DONE, isa.SemWait.STALL_ON_ZERO))

  pass_list = passes.passes if hasattr(passes, "passes") else passes
  for p in pass_list:
    a.tt(isa.SETRWC(BitMask=15))
    for w in p.prologue: a.tt(w)
    if p.footprints == 1:
      for w in p.body: a.tt(w)
    else:
      a.rv("addi", rd=5, rs1=0, imm=p.footprints)
      loop_start = len(a.words)
      for w in p.body: a.tt(w)
      a.rv("addi", rd=5, rs1=5, imm=-1)
      offset = (loop_start - len(a.words)) * 4
      a.rv("bne", rs1=5, rs2=0, imm=offset)
    a.tt(isa.SETRWC(BitMask=15))
    a.tt(isa.STALLWAIT(isa.Stall.SYNC, isa.Wait.SFPU))
    for w in p.epilogue: a.tt(w)

  a.tt(isa.STALLWAIT(isa.Stall.SYNC, isa.Wait.MATH | isa.Wait.SFPU))
  a.tt(isa.SEMPOST(SEM_MATH_PACK))
  return a.to_bytes()


def _build_trisc2(out_tiles: list[int]) -> bytes:
  a = _Asm()
  fp = cfg.DataFormat.FLOAT32
  p = cfg.PACK
  ctx = p.ctx[0]
  a.tt(isa.SEMWAIT(isa.Stall.TDMA | isa.Stall.PACK | isa.Stall.SYNC, SEM_MATH_PACK, isa.SemWait.STALL_ON_ZERO))
  a.rmw(
    ctx.disable_zero_compress(1), ctx.out_fmt(fp), ctx.in_fmt(fp), ctx.exp_section_size(0),
    ctx.pack_per_xy_plane(0), ctx.pack_reads_per_xy_plane(16),
    p.y_stride(16 * 4), p.z_stride(256 * 4), p.w_stride(1024 * 4),
    p.edge_mask[0](0xFFFF),
  )
  pm = cfg.PACK_ADDR_MOD
  a.setc16(pm[0].ysrc_incr(4), pm[0].ydst_incr(4))
  a.setc16(pm[1].ysrc_clear(1), pm[1].ydst_clear(1), pm[1].zsrc_clear(1))

  for idx, tile in enumerate(out_tiles):
    l1_out = L1_OUT_BASE + idx * 4096
    a.tt(isa.SETADC(CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=tile))
    # Set L1 dest address via SETDMAREG + WRCFG
    addr16 = (l1_out >> 4) - 1
    gpr = 16
    a.tt(isa.SETDMAREG(Payload_SigSelSize=0, Payload_SigSel=addr16 & 0xFFFF, RegIndex16b=2 * gpr))
    a.tt(isa.SETDMAREG(Payload_SigSelSize=2, Payload_SigSel=(addr16 >> 16) & 0xFFFF, RegIndex16b=2 * gpr + 1))
    a.tt(isa.STALLWAIT(isa.Stall.CFG, isa.Wait.THCON | isa.Wait.PACK0))
    a.tt(isa.WRCFG(gpr, 0, ctx.l1_dest_addr.word))
    a.tt(isa.SETADCXX(4, 15, 0))
    a.tt(isa.SETADCXY(4, 0, 0, 0, 0, 11))
    a.tt(isa.SETADCZW(4, 0, 0, 0, 0, 5))
    a.tt(isa.STALLWAIT(isa.Stall.CFG, isa.Wait.PACK0))
    for j in range(16):
      a.tt(isa.PACR(AddrMode=1 if j == 15 else 0, Last=int(j == 15)))
    a.tt(isa.STALLWAIT(isa.Stall.SYNC, isa.Wait.PACK0))

  a.drain()
  a.store32(L1_DONE, 1)
  a.rv("fence", imm=0xFF)
  return a.to_bytes()


def run_sfpu_passes_on_silicon(
  dev: Device,
  passes,
  input_tiles: list[np.ndarray],
  out_tile_list: list[int],
) -> list[np.ndarray]:
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
    if time.monotonic() > deadline:
      raise TimeoutError("p100a SFPU kernel timed out")
    time.sleep(0.001)
  return [np.frombuffer(dev.read_l1(core, L1_OUT_BASE + idx * 4096, 4096), dtype=np.float32).copy()
          for idx in range(len(out_tile_list))]


def run_sfpu_on_silicon(
  dev: Device,
  fn,
  inputs: dict[str, np.ndarray],
  *,
  precision=dtypes.fp32,
  max_regs: int = 8,
  preserve_l11: bool = False,
  multi_out: bool = False,
  output_tiles=None,
) -> tuple[list[np.ndarray], object]:
  names = list(inputs.keys())
  dst_uops = {n: UOp.buffer(n, (1, 32, 32), dtypes.fp32).noc_read(0).unpack(Space.DST, dtypes.fp32) for n in names}
  dst_inputs = {dst_uops[n]: i for i, n in enumerate(names)}
  res = fn(**dst_uops)
  roots = list(res) if multi_out else [res]
  comp = compile_sfpu(
    roots, dst_inputs, precision=precision, max_regs=max_regs,
    output_tiles=output_tiles, preserve_l11=preserve_l11, addr_mode=ADDR_MOD_STEP,
  )
  out_tile_list = list(comp.root_tiles)

  data: dict[int, bytes] = {L1_DONE: struct.pack("<I", 0)}
  for i, n in enumerate(names):
    arr = np.ascontiguousarray(inputs[n], dtype=np.float32).reshape(1024)
    data[L1_IN_BASE + i * 4096] = arr.tobytes()

  images = {
    "brisc": b"",
    "trisc0": _build_trisc0(len(names)),
    "trisc1": _build_trisc1(comp),
    "trisc2": _build_trisc2(out_tile_list),
  }
  core = dev.workers[0]
  dev.run(images, data=data, cores=[core])
  deadline = time.monotonic() + 5.0
  while struct.unpack("<I", dev.read_l1(core, L1_DONE, 4))[0] != 1:
    if time.monotonic() > deadline:
      raise TimeoutError("p100a SFPU kernel timed out")
    time.sleep(0.001)

  outs = []
  for idx in range(len(out_tile_list)):
    raw = dev.read_l1(core, L1_OUT_BASE + idx * 4096, 4096)
    outs.append(np.frombuffer(raw, dtype=np.float32).copy())
  return outs, comp


class TestSfpuSilicon(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.dev = Device(0)

  @classmethod
  def tearDownClass(cls):
    cls.dev.close()

  def test_silu_mul_fp32_bf16_and_4reg_spill(self):
    rng = np.random.default_rng(10)
    a = rng.standard_normal(1024).astype(np.float32) * 3.0
    b = rng.standard_normal(1024).astype(np.float32)
    a[0], a[1], a[2] = -100.0, 0.0, 100.0
    ref = (a / (1.0 + np.exp(-np.clip(a, -80.0, 80.0)))) * b

    # FP32 8-reg
    [out_f32], c1 = run_sfpu_on_silicon(self.dev, lambda a, b: a.silu() * b, {"a": a, "b": b}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_f32, ref, rtol=3e-5, atol=1e-5)

    # BF16 precision (fast exp_l0 path)
    [out_bf16], c2 = run_sfpu_on_silicon(self.dev, lambda a, b: a.silu() * b, {"a": a, "b": b}, precision=dtypes.bf16)
    np.testing.assert_allclose(out_bf16, ref, rtol=2e-2, atol=2e-2)

    # FP32 forced 4-reg Dst pass-splitting
    [out_4r], c3 = run_sfpu_on_silicon(
      self.dev, lambda a, b: a.silu() * b, {"a": a, "b": b}, precision=dtypes.fp32, max_regs=4,
    )
    self.assertGreaterEqual(len(c3.passes), 2)
    np.testing.assert_allclose(out_4r, ref, rtol=3e-5, atol=1e-5)

  def test_all_transcendentals_on_silicon(self):
    rng = np.random.default_rng(20)
    pos = np.exp(rng.uniform(-6.0, 6.0, 1024)).astype(np.float32)
    signed = np.where(rng.random(1024) < 0.5, -pos, pos).astype(np.float32)
    xs = np.linspace(-10.0, 10.0, 1024, dtype=np.float32)
    xs[0], xs[1], xs[2] = -150.0, -126.5, 0.0

    [out_exp2], _ = run_sfpu_on_silicon(self.dev, lambda x: x.exp2(), {"x": xs})
    np.testing.assert_allclose(out_exp2, np.exp2(xs), rtol=2e-6, atol=1e-35)

    [out_rcp], _ = run_sfpu_on_silicon(self.dev, lambda x: x.recip(), {"x": signed})
    np.testing.assert_allclose(out_rcp, 1.0 / signed, rtol=2e-6, atol=0.0)

    [out_rsq], _ = run_sfpu_on_silicon(self.dev, lambda x: x.rsqrt(), {"x": pos})
    np.testing.assert_allclose(out_rsq, 1.0 / np.sqrt(pos), rtol=2e-6, atol=0.0)

    pos0 = pos.copy()
    pos0[0] = 0.0
    [out_sq], _ = run_sfpu_on_silicon(self.dev, lambda x: x.sqrt(), {"x": pos0})
    np.testing.assert_allclose(out_sq, np.sqrt(pos0), rtol=2e-6, atol=0.0)
    self.assertEqual(out_sq[0], 0.0)

    [out_log2], _ = run_sfpu_on_silicon(self.dev, lambda x: x.log2(), {"x": pos})
    np.testing.assert_allclose(out_log2, np.log2(pos), rtol=2e-5, atol=2e-5)

    angles = rng.uniform(-5000.0, 5000.0, 1024).astype(np.float32)
    [out_sin], _ = run_sfpu_on_silicon(self.dev, lambda x: x.sin(), {"x": angles})
    np.testing.assert_allclose(out_sin, np.sin(angles.astype(np.float64)), rtol=2e-6, atol=2e-6)

    mild = rng.standard_normal(1024).astype(np.float32) * 2.0
    [out_gelu], _ = run_sfpu_on_silicon(self.dev, lambda x: x.gelu(), {"x": mild})
    c = math.sqrt(2.0 / math.pi)
    ref_gelu = 0.5 * mild * (1.0 + np.tanh(c * (mild + 0.044715 * mild ** 3)))
    np.testing.assert_allclose(out_gelu, ref_gelu, rtol=2e-4, atol=1e-4)

  def test_where_predication_and_multi_output_swap_on_silicon(self):
    rng = np.random.default_rng(30)
    a = rng.standard_normal(1024).astype(np.float32)
    b = rng.standard_normal(1024).astype(np.float32)
    c = rng.standard_normal(1024).astype(np.float32)
    b[::7] = a[::7]  # exact equality cases

    [out_lt], _ = run_sfpu_on_silicon(self.dev, lambda a, b: (a < b).where(a + 1.0, b), {"a": a, "b": b})
    np.testing.assert_allclose(out_lt, np.where(a < b, a + 1.0, b), rtol=1e-6, atol=1e-6)

    [out_and], _ = run_sfpu_on_silicon(self.dev, lambda a, b, c: ((a < b) & (b < c)).where(a, 0.0), {"a": a, "b": b, "c": c})
    np.testing.assert_allclose(out_and, np.where((a < b) & (b < c), a, 0.0), rtol=1e-6, atol=1e-6)

    [out_eq], _ = run_sfpu_on_silicon(self.dev, lambda a, b, c: a.eq(b).where(c, a), {"a": a, "b": b, "c": c})
    np.testing.assert_allclose(out_eq, np.where(a == b, c, a), rtol=1e-6, atol=1e-6)

    # UOp.lane_id() < 16 -> rows 0, 1 of every 4-row group in each 16x16 face
    [out_lane], _ = run_sfpu_on_silicon(self.dev, lambda a: (UOp.lane_id() < 16).where(a, 0.0), {"a": a})
    row_in_face = (np.arange(1024) % 256) // 16
    np.testing.assert_allclose(out_lane, np.where((row_in_face % 4) < 2, a, 0.0), rtol=1e-6, atol=1e-6)

    # Bug #1 silicon test: multi-output swapping Dst tiles [1, 0] with early output
    [o0, o1], _ = run_sfpu_on_silicon(
      self.dev, lambda a, b: [a + 1.0, b + 2.0], {"a": a, "b": b}, multi_out=True, output_tiles=[1, 0],
    )
    np.testing.assert_allclose(o0, a + 1.0, rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(o1, b + 2.0, rtol=1e-6, atol=1e-6)

  def test_fp32_predicate_in_fast_math(self):
    # The BF16 exp2 approximation crosses x near x=0.64. A gate can then
    # select a completely different value even if exp2 itself is within tolerance.
    a = np.linspace(0.60, 0.68, 1024, dtype=np.float32)
    [out], _ = run_sfpu_on_silicon(self.dev, lambda a: ((-a).exp2() < a).where(a, -a),
                                   {"a": a}, precision=dtypes.bf16)
    np.testing.assert_array_equal(out, np.where(np.exp2(-a) < a, a, -a))

  def test_lane_id_layout(self):
    [out], _ = run_sfpu_on_silicon(self.dev, lambda: UOp.lane_id().cast(dtypes.fp32), {})
    # Packed output consists of four 16x16 faces in TL, TR, BL, BR order.
    logical = out.reshape(2, 2, 16, 16).transpose(0, 2, 1, 3).reshape(32, 32)
    rows, cols = np.indices((32, 32))
    np.testing.assert_array_equal(logical, 8 * (rows % 4) + (cols % 16) // 2)

  def test_prompt_rope_step(self):
    # shared/prompt_rope.ttrv rounds a*c first, then fuses b*d+product.
    a, b, c, d = np.random.default_rng(81).uniform(-2, 2, (4, 1024)).astype(np.float32)
    [out], comp = run_sfpu_on_silicon(self.dev, lambda a, b, c, d: mulacc(b, d, a*c).cast(dtypes.bf16),
                                       dict(zip("abcd", (a, b, c, d))))
    fp = (b.astype(np.float64)*d + a*c).astype(np.float32).view(np.uint32)
    rounded = ((fp + 0x7fff + ((fp >> 16) & 1)) >> 16) << 16
    np.testing.assert_array_equal(out.view(np.uint32), rounded)
    self.assertEqual(len(comp.passes), 1)
    self.assertEqual(len(comp.passes[0].body), 8)

  def test_integer_keys(self):
    words = np.array([0x80000000, 0xbf800000, 0, 0x40000000, 0xff000000, 0x7f000000], dtype=np.uint32)
    a, b = (np.resize(x, 1024) for x in (np.repeat(words, words.size), np.tile(words, words.size)))
    for dt, np_dt in ((dtypes.i32, np.int32), (dtypes.u32, np.uint32)):
      def expr(a, b):
        x, y = a.bitcast(dt), b.bitcast(dt)
        return [(x < y).where(a + 0.25, b - 0.25), x.minimum(y).bitcast(dtypes.fp32)]
      outs, _ = run_sfpu_on_silicon(self.dev, expr, {"a": a.view(np.float32), "b": b.view(np.float32)}, multi_out=True)
      x, y = a.view(np_dt), b.view(np_dt)
      np.testing.assert_array_equal(outs[0], np.where(x < y, a.view(np.float32) + 0.25, b.view(np.float32) - 0.25))
      np.testing.assert_array_equal(outs[1].view(np.uint32), np.minimum(x, y).view(np.uint32))

  def test_duplicate_output_after_swap(self):
    a = np.arange(1024, dtype=np.float32)
    for slots in ([1, 0, 2], [None, 0, 2]):
      outs, comp = run_sfpu_on_silicon(self.dev, lambda a, b: (a, b, a), {"a": a, "b": -a},
                                        multi_out=True, output_tiles=slots)
      self.assertEqual(comp.root_tiles[1:], (0, 2))
      for actual, expected in zip(outs, (a, -a, a), strict=True):
        np.testing.assert_array_equal(actual, expected)

  def test_parallel_copy_cycle_with_two_registers(self):
    data = np.random.default_rng(90).uniform(-1, 1, (4, 1024)).astype(np.float32)
    outputs, comp = run_sfpu_on_silicon(self.dev, lambda **inputs: tuple(inputs.values()), dict(zip("abcd", data)),
                                        multi_out=True, output_tiles=[1, 2, 3, 0], max_regs=2)
    np.testing.assert_array_equal(outputs, data)
    self.assertEqual(comp.passes[0].peak_regs, 2)

  def test_deep_multi_pass_spill_on_silicon(self):
    rng = np.random.default_rng(40)
    a = rng.standard_normal(1024).astype(np.float32) * 0.5
    b = rng.standard_normal(1024).astype(np.float32) * 0.5

    def expr(a, b):
      def leaf(x, k):
        return (x + float(k) * 0.13).exp2() * (x + float(k) * 0.27 + 2.0).recip()
      t0 = leaf(a, 1) + leaf(b, 2)
      t1 = leaf(a + 0.5, 3) + leaf(b - 0.5, 4)
      t2 = leaf(a * 0.7, 5) + leaf(b * 1.3, 6)
      return (t0 * t1 + t2) * (t0 - t2)

    def ref_fn(a, b):
      def leaf(x, k):
        return np.exp2(x + float(k) * 0.13) / (x + float(k) * 0.27 + 2.0)
      t0 = leaf(a, 1) + leaf(b, 2)
      t1 = leaf(a + 0.5, 3) + leaf(b - 0.5, 4)
      t2 = leaf(a * 0.7, 5) + leaf(b * 1.3, 6)
      return (t0 * t1 + t2) * (t0 - t2)

    [out], comp = run_sfpu_on_silicon(self.dev, expr, {"a": a, "b": b})
    self.assertGreaterEqual(len(comp.passes), 2)
    np.testing.assert_allclose(out, ref_fn(a, b), rtol=5e-5, atol=5e-5)

  def test_reduce_lanes_row8_and_all_on_silicon(self):
    rng = np.random.default_rng(101)
    x_raw = rng.uniform(-2.0, 2.0, 1024).astype(np.float32)
    # 4 faces of 16x16; within each face, 4 row-groups of 4 rows x 8 even/odd pairs
    faces = x_raw.reshape(4, 4, 4, 8, 2)  # (face, rg, lane_row, lane_col, odd)
    for op, np_fn in ((Ops.ADD, np.sum), (Ops.MAX, np.max)):
      for scope in ("row8", "all"):
        with self.subTest(op=op.name, scope=scope):
          [out], _ = run_sfpu_on_silicon(self.dev, lambda x: x.reduce_lanes(op, scope), {"x": x_raw})
          axis = 3 if scope == "row8" else (2, 3)
          ref = np.broadcast_to(np_fn(faces, axis=axis, keepdims=True), faces.shape).reshape(1024)
          np.testing.assert_allclose(out, ref, rtol=1e-5, atol=1e-5)

  def test_decode_rmsnorm_pinned_lreg_on_silicon(self):
    rng = np.random.default_rng(102)
    x0 = rng.standard_normal(1024).astype(np.float32)
    x1 = rng.standard_normal(1024).astype(np.float32)
    gamma = rng.uniform(0.5, 1.5, 1024).astype(np.float32)
    eps = 1e-5

    # Stage 1: pinned L0 accumulator across 2 tiles (x0 in Dst[0], x1 in Dst[1])
    r = UOp.range(2, axis=0, name="t")
    x_u = UOp.buffer("x", (2, 32, 32), dtypes.fp32).noc_read(r).unpack(Space.DST, dtypes.fp32)
    g_u = UOp.buffer("g", (1, 32, 32), dtypes.fp32).noc_read(0).unpack(Space.DST, dtypes.fp32)
    acc = (x_u * x_u).reduce(r, op=Ops.ADD, space=Space.LREG)
    lp0 = compile_sfpu_loop(acc, {x_u: 0}, addr_mode=ADDR_MOD_STEP)
    lp1 = compile_sfpu_loop(acc, {x_u: 1}, reg_carries={0: 0}, addr_mode=ADDR_MOD_STEP)

    # Stage 2: 1-shot LReg reduce_lanes + rsqrt (runs ONCE in L0, zero Dst loads/stores)
    inv_rms = (acc.reduce_lanes(Ops.ADD, "all") * (1.0 / 2048.0) + eps).rsqrt()
    rms_stage = compile_sfpu(inv_rms, reg_inputs=lp0.reg_carries, reg_outputs={inv_rms: 0})
    self.assertEqual(rms_stage.passes[0].footprints, 1)

    # Stage 3: rms_apply with read-only pinned L0 across all 32 footprints
    out_u = x_u * inv_rms * g_u
    apply_stage = compile_sfpu(
      out_u, {x_u: 0, g_u: 2}, reg_inputs={inv_rms: 0}, output_tiles={out_u: 0}, addr_mode=ADDR_MOD_STEP,
    )

    passes = [*lp0.init_passes, *lp0.body_passes, *lp1.body_passes, *rms_stage.passes, *apply_stage.passes]
    [out] = run_sfpu_passes_on_silicon(self.dev, passes, [x0, x1, gamma], [0])
    ref = x0 / np.sqrt(np.mean(np.concatenate([x0, x1]) ** 2) + eps) * gamma
    np.testing.assert_allclose(out, ref, rtol=1e-5, atol=1e-5)

  def test_dst_accumulator_dual_carry_on_silicon(self):
    rng = np.random.default_rng(103)
    tiles = [rng.uniform(-2.0, 2.0, 1024).astype(np.float32) for _ in range(3)]
    r = UOp.range(3, axis=0, name="t")
    x_u = UOp.buffer("x", (3, 32, 32), dtypes.fp32).noc_read(r).unpack(Space.DST, dtypes.fp32)
    s_out, m_out = r.loop((UOp.const(dtypes.fp32, 0.0), UOp.const(dtypes.fp32, -math.inf)), lambda s, m: (s + x_u, m.maximum(x_u)), spaces=(Space.DST, Space.DST))
    # Pin carried Dst[3] (sum) and Dst[4] (max) across all 3 iterations (input tiles sit in Dst[0..2])
    lp_iter = [
      compile_sfpu_loop(s_out, {x_u: t}, dst_carries={0: 3, 1: 4}, addr_mode=ADDR_MOD_STEP)
      for t in range(3)
    ]
    passes = [*lp_iter[0].init_passes, *(p for lp in lp_iter for p in lp.body_passes)]
    out_sum, out_max = run_sfpu_passes_on_silicon(self.dev, passes, tiles, [3, 4])
    np.testing.assert_allclose(out_sum, tiles[0] + tiles[1] + tiles[2], rtol=1e-5, atol=1e-5)
    np.testing.assert_array_equal(out_max, np.maximum(np.maximum(tiles[0], tiles[1]), tiles[2]))

  def test_prologue_l0_preserved_with_sfpconfig_on_silicon(self):
    rng = np.random.default_rng(104)
    x = rng.uniform(-3.0, 3.0, 1024).astype(np.float32)
    x_u = UOp.buffer("x", (1, 32, 32), dtypes.fp32).noc_read(0).unpack(Space.DST, dtypes.fp32)
    scale_init = UOp.const(dtypes.fp32, 1.75)
    scale_u = scale_init.carry(UOp.range(1, axis=0), space=Space.LREG)
    init_scale = compile_sfpu(scale_init, reg_outputs={scale_init: 0}, footprints=1)
    y_u = x_u.sin() * scale_u
    body_stage = compile_sfpu(
      y_u, {x_u: 0}, reg_inputs={scale_u: 0}, output_tiles={y_u: 0}, addr_mode=ADDR_MOD_STEP,
    )
    self.assertIn("SFPCONFIG", [isa.tensix_decode(w)[0] for w in body_stage.passes[0].prologue])
    [out] = run_sfpu_passes_on_silicon(self.dev, [*init_scale.passes, *body_stage.passes], [x], [0])
    np.testing.assert_allclose(out, np.sin(x) * 1.75, rtol=1e-5, atol=1e-5)


if __name__ == "__main__":
  unittest.main()
