import os
import unittest
import numpy as np

from compiler import UOp, dtypes, unpack_bundle
from compiler.blackhole.specs import Space, UnpackOp, PackOp, SfpLoadOp, SfpStoreOp, FpuOp, NocRead, NocWrite
from compiler.blackhole.pipeline import instruction, compile_tile_graph


def face_program(fn, src_dtype=dtypes.fp32, dst_dtype=dtypes.fp32):
  inputs = [instruction(UnpackOp(Space.DST, i, src_dtype=src_dtype, dst_slot=i)) for i in range(2)]
  fp = UOp.range(4, 0, "fp")
  a, b = [instruction(SfpLoadOp(i), u, fp, dtype=dtypes.fp32) for i, u in enumerate(inputs)]
  result = instruction(SfpStoreOp(0), fn(a, b), fp).end(fp)
  root = UOp.sink(instruction(PackOp(2, dst_dtype=dst_dtype), result))
  return compile_tile_graph(root, {0: 0x20000, 1: 0x20200, 2: 0x21000})


class TestTilePipeline(unittest.TestCase):
  def test_staged_footprints_only_emit_math_on_trisc1(self):
    from compiler import Tensor, lower_tensor, linearize_schedule
    from compiler.blackhole.lower import lower_kernel
    from compiler.isa.tensix import is_tensix_ins, tensix_op, TensixGroupOp
    call, = linearize_schedule(lower_tensor(Tensor.buffer("x", (1, 56, 1, 16), dtypes.bf16).softmax(-1)))
    program = lower_kernel(call.kernel, call.args).program
    for core in program.src[1].src:
      with self.subTest(role=core.arg):
        if core.arg in ("brisc", "ncrisc"):
          self.assertFalse(any(is_tensix_ins(u) for u in core.src))
        elif core.arg != "trisc1":
          self.assertFalse(any(tensix_op(u) in TensixGroupOp.SFPU | TensixGroupOp.Rwc | TensixGroupOp.FPU for u in core.src))

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_dram_matmul_k_loop_on_both_cards(self):
    import struct
    from device import Device
    nf, kf = 3, 9
    worker, k = UOp.special(nf, "worker_id"), UOp.range(kf, 0, "k")
    ra = instruction(NocRead(0, 0, 256), k * 256)
    rw = instruction(NocRead(1, 1, 512), (worker * kf + k) * 512)
    a = instruction(UnpackOp(Space.SRCB, 0, src_dtype=dtypes.bf16, dst_dtype=dtypes.bf16), ra)
    w = instruction(UnpackOp(Space.SRCA, 1, src_dtype=dtypes.bf16, dst_dtype=dtypes.bf16, rows=16, transpose=True), rw)
    product = instruction(FpuOp("MVMUL", accumulate=True), a, w, dtype=dtypes.fp32).end(k)
    packed = instruction(PackOp(2), product)
    sink = UOp.sink(instruction(NocWrite(2, 2, 512), packed, worker * 512))
    images = unpack_bundle(compile_tile_graph(sink, {0: 0x20000, 1: 0x20200, 2: 0x21000}).src[3].arg)
    rng = np.random.default_rng(99)
    a = rng.integers(-3, 4, (8, kf * 16)).astype(np.float32)
    w = rng.integers(-3, 4, (nf * 16, kf * 16)).astype(np.float32)
    a_bytes = (a.view(np.uint32) >> 16).astype(np.uint16).reshape(8, kf, 16).transpose(1, 0, 2).copy().tobytes()
    w_bytes = (w.view(np.uint32) >> 16).astype(np.uint16).reshape(nf, 16, kf, 16).transpose(0, 2, 1, 3).copy().tobytes()
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          addresses = [dev.alloc_dram(len(data)) for data in (a_bytes, w_bytes, bytes(nf * 512))]
          for address, data in zip(addresses, (a_bytes, w_bytes)): dev.dma.copyin(address, memoryview(data))
          dev.run(images, data={0x80: struct.pack("<3Q", *addresses)}, cores=dev.workers[:nf])
          dev.synchronize()
          data = bytearray(nf * 512)
          dev.dma.copyout(data, addresses[2])
          actual = np.frombuffer(data, dtype=np.float32).reshape(nf, 8, 16).transpose(1, 0, 2).reshape(8, nf * 16)
          np.testing.assert_array_equal(actual, a @ w.T)
        finally: dev.close()

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_dram_to_dram_silu_on_both_cards(self):
    import struct
    from device import Device
    worker = UOp.special(3, "worker_id")
    offset = worker * 512
    reads = [instruction(NocRead(i, i, 512), offset + 4032) for i in range(2)]
    inputs = [instruction(UnpackOp(Space.DST, i, dst_slot=i), reads[i]) for i in range(2)]
    fp = UOp.range(4, 0, "fp")
    a, b = [instruction(SfpLoadOp(i), u, fp, dtype=dtypes.fp32) for i, u in enumerate(inputs)]
    result = instruction(SfpStoreOp(0), a.silu() * b, fp).end(fp)
    packed = instruction(PackOp(2), result)
    sink = UOp.sink(instruction(NocWrite(2, 2, 512), packed, offset))
    images = unpack_bundle(compile_tile_graph(sink, {0: 0x20000, 1: 0x20200, 2: 0x21000}).src[3].arg)
    self.assertTrue(all(images[role] for role in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")))
    rng = np.random.default_rng(17)
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          addresses = [dev.alloc_dram(8192) for _ in range(3)]
          for _ in range(2):
            a, b = [rng.uniform(-3., 3., (3, 8, 16)).astype(np.float32) for _ in range(2)]
            for address, value in zip(addresses, (a, b)):
              dev.dma.copyin(address, memoryview(bytes(4032) + value.tobytes()))
            dev.run(images, data={0x80: struct.pack("<3Q", *addresses)}, cores=dev.workers[:3])
            dev.synchronize()
            data = bytearray(3 * 512)
            dev.dma.copyout(data, addresses[2])
            actual = np.frombuffer(data, dtype=np.float32).reshape(3, 8, 16)
            np.testing.assert_allclose(actual, a / (1. + np.exp(-a)) * b, rtol=3e-6, atol=2e-6)
        finally: dev.close()

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_mvmul_face_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(7)
    act = (rng.uniform(-1., 1., (8, 16)).astype(np.float32).view(np.uint32) & 0xFFFF0000).view(np.float32)
    cases = []
    for exact in (False, True):
      x = rng.integers(-3, 4, (8, 16)).astype(np.float32) if exact else act
      w = (rng.uniform(-1., 1., (16, 16)).astype(np.float32).view(np.uint32) & 0xFFFF0000).view(np.float32)
      if exact: w = rng.integers(-3, 4, (16, 16)).astype(np.float32)
      cases.append((dtypes.bf16, 3, x, w, (w.view(np.uint32) >> 16).astype(np.uint16).tobytes(), exact))
    for bits, dtype, fidelity in ((8, dtypes.bfp8, 2), (4, dtypes.bfp4, 1)):
      # A native 16x16 weight face: 16 shared row exponents then sign/magnitude mantissas.
      magnitude = rng.integers(0, 1 << (bits - 1), (16, 16), dtype=np.uint8)
      negative = rng.integers(0, 2, (16, 16), dtype=np.uint8)
      negative[magnitude == 0] = 0  # sign-only BFP encodings mean -infinity, not negative zero
      exponent = rng.integers(124, 130, 16, dtype=np.uint8)
      w = magnitude.astype(np.float32) * (1. - 2. * negative.astype(np.float32)) * np.exp2(exponent.astype(np.float32)[:, None] - 127 - (bits - 2))
      encoded = (magnitude | (negative << (bits - 1))).ravel()
      if bits == 4: encoded = encoded[::2] | (encoded[1::2] << 4)
      cases.append((dtype, fidelity, act, w, exponent.tobytes() + encoded.tobytes(), False))
    for index in (0, 1):
      dev = Device(index)
      try:
        for dtype, fidelity, x, w, packed, exact in cases:
          with self.subTest(card=index, dtype=dtype, exact=exact):
            a = instruction(UnpackOp(Space.SRCB, 0, src_dtype=dtypes.bf16, dst_dtype=dtypes.bf16))
            b = instruction(UnpackOp(Space.SRCA, 1, src_dtype=dtype, dst_dtype=dtype, rows=16, transpose=True))
            product = instruction(FpuOp("MVMUL", fidelity=fidelity, src_dtype=dtype), a, b, dtype=dtypes.fp32)
            root = UOp.sink(instruction(PackOp(2), product))
            images = unpack_bundle(compile_tile_graph(root, {0: 0x20000, 1: 0x20200, 2: 0x21000}).src[3].arg)
            dev.run(images, data={0x20000: (x.view(np.uint32) >> 16).astype(np.uint16).tobytes(),
                                  0x20200: packed}, cores=[dev.workers[0]])
            dev.synchronize()
            actual = np.frombuffer(dev.read_l1(0, 0x21000, 512), dtype=np.float32).reshape(8, 16)
            if exact: np.testing.assert_array_equal(actual, x @ w.T)
            else:
              # FPU phases multiply five SrcA and seven SrcB significand bits.
              # The specified reduced-fidelity modes omit the remaining terms.
              xh = (x.view(np.uint32) & 0xFFFE0000).view(np.float32)
              wh = (w.view(np.uint32) & 0xFFF80000).view(np.float32)
              expected = xh @ wh.T
              if fidelity > 1: expected += xh @ (w - wh).T
              if fidelity > 2: expected += (x - xh) @ wh.T
              # The matrix unit rounds internally even with FP32 Dst. Bound
              # rounding by the absolute dot product, also covering cancellation.
              error_bound = np.abs(x) @ np.abs(w).T * 2**-12 + 2e-6
              np.testing.assert_array_less(np.abs(actual - expected), error_bound)
      finally: dev.close()

  def test_compile_joint_dag(self):
    program = face_program(lambda a,b: a.silu() * b)
    images = unpack_bundle(program.src[3].arg)
    for role in ("trisc0", "trisc1", "trisc2"): self.assertGreater(len(images[role]), 0)

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_face_silu_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(123)
    a, b = [rng.uniform(-3., 3., (8, 16)).astype(np.float32) for _ in range(2)]
    images = unpack_bundle(face_program(lambda a,b: a.silu() * b).src[3].arg)
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          dev.run(images, data={0x20000: a.tobytes(), 0x20200: b.tobytes(), 0x21000: bytes(576)}, cores=[dev.workers[0]])
          dev.synchronize()
          actual = np.frombuffer(dev.read_l1(0, 0x21000, 512), dtype=np.float32).reshape(8, 16)
          np.testing.assert_allclose(actual, a / (1. + np.exp(-a)) * b, rtol=3e-6, atol=2e-6)
          self.assertEqual(dev.read_l1(0, 0x21200, 64), bytes(64))
        finally: dev.close()
