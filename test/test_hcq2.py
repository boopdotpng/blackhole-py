"""CPU and hardware tests for the minimal HCQ2 Command Processor, resident workers, rangeify cache, and TinyJit."""
import os
import struct
import threading
import time
import unittest
from unittest import mock

import fw
from compiler import Tensor, TinyJit, Variable, dtypes
from compiler.blackhole.hcq import ComputeQueue, pack_phys_rect
from compiler.blackhole.runtime import canonicalize_graph, compile_schedule


class _FakeHost:
  def __init__(self, size=1 << 20, noc_addr=0x40000000):
    self.mem = bytearray(size)
    self.noc_addr = noc_addr


class _FakeDevice:
  def __init__(self):
    self.host = _FakeHost()
    self.heap = 64
    self.kernel_sequence = 0
    self.submitted = []

  def alloc_host(self, size, align=64):
    off = (self.heap + align - 1) & ~(align - 1)
    self.heap = off + size
    return off

  def submit_cp(self, addr, nbytes):
    self.submitted.append((addr, nbytes))


class TestHCQ2CPU(unittest.TestCase):
  def test_firmware_builds_and_pack_kernel(self):
    cp = fw.cp_image(8)
    worker, pcs = fw.worker_images(8)
    self.assertLessEqual(len(cp), fw.CP_BRISC_SIZE)
    self.assertLessEqual(fw.WORKER_FW_BASE + len(worker), fw.WORKER_FW_END)
    self.assertEqual(pcs["brisc"], fw.WORKER_FW_BASE)
    blob, key = fw.pack_kernel({"brisc": b"\x13\x00\x00\x00", "trisc1": b"\x13\x00\x00\x00"}, cb_mask=0x3)
    self.assertEqual(len(blob) % 64, 0)
    self.assertNotEqual(key, 0)
    offs = struct.unpack_from("<6I", blob, 0)
    self.assertEqual(offs[0], fw.PROG_HDR_BYTES)
    self.assertEqual(offs[1], 0)
    self.assertEqual(offs[2], 0)
    self.assertGreater(offs[3], offs[0])
    self.assertEqual(offs[4], 0)
    self.assertEqual(offs[5], 0x3)
    self.assertEqual(blob[offs[0] + 4:offs[0] + 12], fw.RET_STUB)
    self.assertEqual(blob[offs[3] + 4:offs[3] + 12], fw.RET_STUB)

  def test_compute_queue_encoding_and_patching(self):
    dev = _FakeDevice()
    q = ComputeQueue()
    args_rel = q.alloc_args(struct.pack("<2Q", 0x1111, 0x2222))
    r0 = pack_phys_rect(((1, 2), (7, 11)))
    r1 = pack_phys_rect((10, 3))
    q.wait(0x50000000, 7)
    q.timestamp(0x50000010)
    q.exec(0x80001000, 512, 0xCAFEBABE, [r0, r1], 71, args_rel)
    q.exec_barrier()
    q.signal(0x50000020, 0)
    cb = q.build(dev)
    self.assertEqual(cb.cmd_bytes, 5 * 64)
    self.assertEqual(cb.args_bytes, 128)
    cb.patch_arg_u64(0, 0xAAAABBBBCCCCDDDD)
    cb.patch_arg_u32(8, 42)
    self.assertEqual(struct.unpack_from("<2Q", dev.host.mem, cb.args_off), (0xAAAABBBBCCCCDDDD, 42))
    seq = cb.submit()
    self.assertEqual(seq, 1)
    self.assertEqual(dev.submitted, [(cb.cmd_addr, 5 * 64)])
    # Verify PKT_EXEC args_addr was link-patched and PKT_SIGNAL value was runtime-patched.
    exec_w = struct.unpack_from("<16I", dev.host.mem, cb.cmd_off + 2 * 64)
    self.assertEqual(exec_w[0], fw.PKT_EXEC)
    self.assertEqual(exec_w[6] | (exec_w[7] << 32), cb.args_addr)
    self.assertEqual(exec_w[8], 71)
    self.assertEqual(exec_w[9], (128 << 8) | 2)
    self.assertEqual(exec_w[10:12], (r0, r1))
    sig_w = struct.unpack_from("<16I", dev.host.mem, cb.cmd_off + 4 * 64)
    self.assertEqual(sig_w[0], fw.PKT_SIGNAL)
    self.assertEqual(sig_w[4] | (sig_w[5] << 32), 1)

  def test_rangeify_schedule_cache_hits_across_buffers_and_vars(self):
    compile_schedule.cache_clear()
    table = Tensor.buffer("rope_table", (32, 16), dtypes.bf16)
    w = Tensor.buffer("w_test", (16, 16), dtypes.bf16)
    sp = Variable("start_pos", 1, 15)
    t0 = Tensor([[1.0] * 16], dtype=dtypes.bf16)
    t1 = Tensor([[2.0] * 16], dtype=dtypes.bf16)
    g0 = ((t0 @ w.T).contiguous() + table[sp.bind(3):sp.bind(3) + 1]).uop
    g1 = ((t1 @ w.T).contiguous() + table[sp.bind(9):sp.bind(9) + 1]).uop
    c0, ext0, v0 = canonicalize_graph(g0)
    c1, ext1, v1 = canonicalize_graph(g1)
    self.assertIs(c0, c1)
    self.assertEqual(len(ext0), len(ext1))
    self.assertEqual(v0[sp], 3)
    self.assertEqual(v1[sp], 9)

    import compiler.blackhole.runtime as rt
    with mock.patch.object(rt, "lower_tensor", wraps=rt.lower_tensor) as spy:
      s0 = compile_schedule(c0, 138, (13, 10), 8)
      s1 = compile_schedule(c1, 138, (13, 10), 8)
      self.assertIs(s0, s1)
      self.assertEqual(spy.call_count, 1)


def _hw_cards():
  if (dev := os.environ.get("BH_DEVICE")) is not None: return (int(dev),)
  return (0, 1)


@unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 to run on both cards")
class TestHCQ2Hardware(unittest.TestCase):
  def test_wait_signal_timestamp_packets(self):
    from device import Device, Signal
    for card in _hw_cards():
      with self.subTest(card=card):
        dev = Device(card)
        try:
          gate_off = dev.alloc_host(64, align=64)
          ts0_off = dev.alloc_host(64, align=64)
          ts1_off = dev.alloc_host(64, align=64)
          done_off = dev.alloc_host(64, align=64)
          struct.pack_into("<Q", dev.host.mem, gate_off, 0)
          struct.pack_into("<2Q", dev.host.mem, ts0_off, 0, 0)
          struct.pack_into("<2Q", dev.host.mem, ts1_off, 0, 0)
          struct.pack_into("<Q", dev.host.mem, done_off, 0)
          done = Signal(dev.host, done_off)

          q = ComputeQueue()
          q.timestamp(dev.host.noc_addr + ts0_off)
          q.wait(dev.host.noc_addr + gate_off, 5)
          q.timestamp(dev.host.noc_addr + ts1_off)
          q.signal(dev.host.noc_addr + done_off, 99)
          cb = q.build(dev)
          cb.submit(signal_timeline=False)

          time.sleep(0.01)
          self.assertEqual(done.value, 0)
          struct.pack_into("<Q", dev.host.mem, gate_off, 5)
          done.wait(99, timeout=5.0)
          t0 = struct.unpack_from("<Q", dev.host.mem, ts0_off + 8)[0]
          t1 = struct.unpack_from("<Q", dev.host.mem, ts1_off + 8)[0]
          self.assertGreater(t0, 0)
          self.assertGreater(t1, t0)
        finally: dev.close()

  def test_l1_program_cache_hit_and_eviction(self):
    from device import Device
    from compiler import BlackholeRenderer, RVOps, UOp, X, dtypes as dt
    from compiler.isa.rv32 import rv_li, X0
    ren = BlackholeRenderer()
    for card in _hw_cards():
      with self.subTest(card=card):
        dev = Device(card)
        try:
          # Build > CODE_CACHE_END - CODE_CACHE_BASE of distinct kernels (each ~8 KiB padded with NOPs)
          # to force at least one full L1 program cache wrap + eviction + icache invalidation.
          n_kernels = 18
          nops = [UOp.ins(RVOps.ADDI, (X0, UOp.const(0)), dt.u32, X0)] * 2000
          progs = []
          for k in range(n_kernels):
            val = 0x1000 + k
            stream = [*nops, rv_li(0x20000, dt.u32, X[6]), rv_li(val, dt.u32, X[7]),
                      UOp.ins(RVOps.SW, (X[6], X[7], UOp.const(0)), dt.void)]
            _, code = ren.compile_core(stream, fix_sfpu=False)
            progs.append(({"brisc": code}, val))
          # Run all distinct kernels (forces eviction), then replay kernel 0 (reload after eviction) and kernel 0 again (hit).
          for images, expected in [*progs, progs[0], progs[0]]:
            dev.run(images, cores=[dev.workers[0]])
            dev.synchronize()
            got = struct.unpack("<I", dev.read_l1(dev.workers[0], 0x20000, 4))[0]
            self.assertEqual(got, expected)
        finally: dev.close()

  def test_batched_realize_and_tinyjit(self):
    import numpy as np
    from device import Device
    for card in _hw_cards():
      with self.subTest(card=card):
        dev = Device(card)
        try:
          w1_np = (np.arange(32 * 16, dtype=np.float32).reshape(32, 16) / 64.0 - 2.0)
          w2_np = (np.arange(16 * 32, dtype=np.float32).reshape(16, 32) / 64.0 - 1.5)
          bias_np = (np.arange(32 * 16, dtype=np.float32).reshape(32, 16) / 128.0)
          w1 = Tensor(w1_np, dtype=dtypes.bf16)
          w2 = Tensor(w2_np, dtype=dtypes.bf16)
          bias = Tensor(bias_np, dtype=dtypes.bf16)
          sp = Variable("pos", 1, 15)

          @TinyJit
          def step(x: Tensor, pos: Variable) -> Tensor:
            h = (x @ w1.T).silu().contiguous()
            return (h @ w2.T).contiguous() + bias[pos:pos + 1]

          step.device = dev
          for i, pos in enumerate((2, 5, 9, 13)):
            x_np = np.full((1, 16), 0.25 * (i + 1), dtype=np.float32)
            out = step(Tensor(x_np, dtype=dtypes.bf16), sp.bind(pos)).numpy(device=dev)
            h_ref = x_np @ w1_np.T
            h_ref = h_ref / (1.0 + np.exp(-h_ref))
            ref = h_ref @ w2_np.T + bias_np[pos:pos + 1]
            np.testing.assert_allclose(out, ref, rtol=5e-2, atol=5e-2)
        finally: dev.close()

  def test_multi_depth_ring_wraparound(self):
    """Exercise depth=3 ring CB wraparound (>10 tiles/core) across map, matmul, and fused SwiGLU."""
    import numpy as np
    from device import Device
    rng = np.random.default_rng(7)
    for card in _hw_cards():
      with self.subTest(card=card):
        dev = Device(card)
        try:
          # > 139 * 10 tiles so every worker wraps depth=3 ring CBs multiple times.
          x_map = rng.standard_normal((16, 139 * 16 * 6)).astype(np.float32) * 0.5
          y_map = rng.standard_normal(x_map.shape).astype(np.float32) * 0.5
          out_map = (Tensor(x_map, dtype=dtypes.bf16) + Tensor(y_map, dtype=dtypes.bf16) * 2.0).numpy(device=dev)
          np.testing.assert_allclose(out_map, x_map + y_map * 2.0, rtol=2e-2, atol=2e-2)

          # Fused SwiGLU (gate.silu() * up) with N = 139 * 16 * 6 = 13344 (>10 tiles/core across 2 weight CBs + 2 act CBs + out CB)
          k, n = 256, 139 * 16 * 5
          a_np = (rng.standard_normal((1, k)) * 0.25).astype(np.float32)
          wg_np = (rng.standard_normal((n, k)) * 0.25).astype(np.float32)
          wu_np = (rng.standard_normal((n, k)) * 0.25).astype(np.float32)
          a = Tensor(a_np, dtype=dtypes.bf16)
          wg = Tensor(wg_np, dtype=dtypes.bf16)
          wu = Tensor(wu_np, dtype=dtypes.bf16)
          out_swiglu = ((a @ wg.T).silu() * (a @ wu.T)).numpy(device=dev)
          g_ref = a_np @ wg_np.T
          ref_swiglu = (g_ref / (1.0 + np.exp(-g_ref))) * (a_np @ wu_np.T)
          np.testing.assert_allclose(out_swiglu, ref_swiglu, rtol=5e-2, atol=5e-2)
        finally: dev.close()


if __name__ == "__main__": unittest.main()
