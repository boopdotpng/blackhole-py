import unittest
from hw import isa
from hw.sfpu_lat import SfpuError as SfpuCompileError
from compiler import UOp, dtypes, fix_sfpu_hazards, sfpu_hazards, verify_sfpu_words
from compiler.blackhole.sfpu import SfpuRenderer, select_sfpu
from compiler.blackhole.specs import SfpLoadOp, SfpStoreOp
from compiler.isa.tensix import encode_tensix


def _select_expr(fn):
  a = UOp.ins(SfpLoadOp(0), (), dtypes.fp32, role="trisc1")
  b = UOp.ins(SfpLoadOp(8), (), dtypes.fp32, role="trisc1")
  store = UOp.ins(SfpStoreOp(0), (fn(a, b),), dtypes.void, role="trisc1")
  return select_sfpu(store.toposort())


class TestSfpuHazardModel(unittest.TestCase):
  def test_measured_undetected_hazards_and_safe_pairs(self):
    mad_l0 = isa.SFPMAD(a=1, b=2, c=3)  # 2-cycle write to L0

    # Every undetected RAW hazard measured on Blackhole A0 card 1
    bad_consumers = [
      ("IADD reg VD",       isa.SFPIADD(src=1, mode=4)),
      ("SHFT reg VD",       isa.SFPSHFT(src=1)),
      ("AND USE_VB",        isa.SFPAND(src=1, dest=2, mode=1)),
      ("OR USE_VB",         isa.SFPOR(src=1, dest=2, mode=1)),
      ("SETEXP non-imm VD", isa.SFPSETEXP(src=1, mode=2)),
      ("SETMAN non-imm VD", isa.SFPSETMAN(src=1)),
      ("SETSGN non-imm VD", isa.SFPSETSGN(src=1)),
      ("ARECIP mode 1 VB",  isa.SFPARECIP(src=1, dest=2, mode=1)),
      ("SWAP mode 1 VD",    isa.SFPSWAP(src=1, mode=1)),
      ("SHFT2 mode 3 VC",   isa.SFPSHFT2(dest=1, mode=3)),
      ("SHFT2 mode 6 VB",   isa.SFPSHFT2(src=1, dest=2, mode=6)),
      ("CONFIG non-imm L0", isa.SFPCONFIG(target=12)),
      ("LOADI LOWER L0",    isa.SFPLOADI(mode=isa.LoadImm.LOWER, imm=0x1234)),
      ("LOAD LO16_ONLY L0", isa.SFPLOAD(format=isa.SfpuFormat.LO16_ONLY)),
    ]
    for label, cons in bad_consumers:
      with self.subTest(label=label):
        hz = sfpu_hazards([mad_l0, cons])
        self.assertEqual(len(hz), 1, f"expected hazard for {label}")
        self.assertEqual(hz[0][1][0], "stale")
        fixed = fix_sfpu_hazards([mad_l0, cons])
        self.assertEqual(len(fixed), 3)
        self.assertEqual(fixed[1], isa.SFPNOP())
        self.assertEqual(sfpu_hazards(fixed), [])

    # Safe pairs (hardware stalls or no dependency) must NOT get spurious SFPNOPs
    safe_pairs = [
      ("MAD -> MAD",          [mad_l0, isa.SFPMAD(b=1, c=2, dest=3)]),
      ("MAD -> SHFT imm",     [mad_l0, isa.SFPSHFT(imm=3, dest=1, mode=5)]),
      ("MAD -> SWAP mode 0",  [mad_l0, isa.SFPSWAP(dest=1)]),
      ("MAD -> LOADI FLOATB", [mad_l0, isa.SFPLOADI(mode=isa.LoadImm.FLOATB, imm=0x3F80)]),
      ("LOADI FLOATB->LOWER", [isa.SFPLOADI(mode=isa.LoadImm.FLOATB, imm=0x3F80), isa.SFPLOADI(mode=isa.LoadImm.LOWER, imm=0x1234)]),
      ("SWAP -> ADD",         [isa.SFPSWAP(src=1, mode=1), isa.SFPADD(a=10, c=1, dest=2)]),
      ("SHFT2 -> ADD",        [isa.SFPSHFT2(src=1, mode=3), isa.SFPADD(a=10, c=1, dest=2)]),
    ]
    for label, stream in safe_pairs:
      with self.subTest(label=label):
        self.assertEqual(sfpu_hazards(stream), [], f"unexpected hazard for {label}")
        self.assertEqual(fix_sfpu_hazards(stream), stream)

  def test_verify_rejects_backdoor_and_illegal_writes(self):
    # VD >= 12 on non-CONFIG/LOADMACRO becomes a silent backdoor template write
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPSTORE(lreg=12, format=isa.SfpuFormat.FP32)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPTRANSP(dest=12)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPGT(dest=12, mode=1)])
    # Writing read-only L9/L10 fails
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPMOV(dest=9)])
    # Storing L9 (0.0) or L10 (1.0) is safe (VD < 12)
    verify_sfpu_words([isa.SFPSTORE(lreg=9, format=isa.SfpuFormat.FP32)])

  def test_loop_wraparound_hazard_detection_and_fix(self):
    # Body starts with IADD reg reading L0 and ends with MAD writing L0: safe once, stale on 2nd iteration
    body = [isa.SFPIADD(src=1, mode=4), isa.SFPMAD(a=1, b=2, c=3)]
    self.assertEqual(sfpu_hazards(body), [])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words(body, is_loop=True)
    fixed = fix_sfpu_hazards(body, is_loop=True)
    self.assertEqual(fixed[-1], isa.SFPNOP())
    verify_sfpu_words(fixed, is_loop=True)


class TestSfpuSelection(unittest.TestCase):
  def test_selected_words(self):
    for fn in (lambda a, b: a + b, lambda a, b: a * b - 2.0, lambda a, b: a.recip(),
               lambda a, b: a.exp2(), lambda a, b: a.sqrt(), lambda a, b: a.sin(), lambda a, b: a.silu()):
      words = [encode_tensix(u, SfpuRenderer()) for u in _select_expr(fn)]
      verify_sfpu_words(words, is_loop=True)


if __name__ == "__main__":
  unittest.main()


def test_spilled_constrained_loads():
  from compiler.isa import rdef
  from compiler.isa.tensix import TensixOps, LREGS
  loads = [UOp.ins(SfpLoadOp(i), (), dtypes.fp32, role="trisc1") for i in range(8)]
  value = sum(loads[1:], loads[0])
  store = UOp.ins(SfpStoreOp(8), (value,), dtypes.void, role="trisc1")
  stream = select_sfpu([*loads, *(u for u in store.toposort() if u not in loads)])
  reads = [u for u in stream if u.is_ins and getattr(u.ins_op, 'op', None) is TensixOps.SFPLOAD]
  assert any(u.ins_op.addr >= 448 for u in reads)
  assert all(rdef(u, SfpuRenderer()) in LREGS[:4] for u in reads if u.ins_op.addr < 448)
