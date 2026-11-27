"""Opt-in compiler control-flow checks on both P150s: BH_HW=1 python3 -m pytest ..."""
import os
import struct
import time
import unittest

from compiler import BlackholeRenderer, Ops, RVOps, RV32Renderer, UOp, X, dtypes, to_program


@unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 to run on both cards")
class TestBackendHardware(unittest.TestCase):
  def test_buffer_roundtrip(self):
    import numpy as np
    from device import Device
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          values = np.arange(2051, dtype=np.float32)
          np.testing.assert_array_equal(dev.array(values).numpy(), values)
          np.testing.assert_array_equal(dev.array(values, dtypes.bf16).numpy(),
                                        ((values.view(np.uint32).astype(np.uint64) + 0x7FFF +
                                          ((values.view(np.uint32) >> 16) & 1)) >> 16).astype(np.uint16))
        finally: dev.close()

  def test_resident_noc_crosses_dram_stripes(self):
    import fw
    from device import Device
    from compiler.isa.rv32 import rv_li, X0, RA
    # Normal RV32 calls through the resident jump table, with no live
    # caller-saved values across calls. All constants are register allocated
    # and encoded through the compiler's instruction representation.
    def call(address, values):
      return [*(rv_li(value, dtypes.u32, X[10 + i]) for i, value in enumerate(values)),
              UOp.ins(RVOps.JALR, (X0, UOp.const(address)), dtypes.u32, RA)]
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          src, dst = dev.alloc_dram(8192), dev.alloc_dram(128)
          payload = bytes(i % 251 for i in range(8192))
          dev.dma.copyin(src, memoryview(payload))
          for role, niu in (("brisc", 0), ("ncrisc", 1)):
            stream = [*call(fw.FN_NOC_READ, (niu, src & 0xFFFFFFFF, src >> 32, 4032, 128, 0x20000, 0)),
                      *call(fw.FN_NOC_WAIT, (niu, 0, 1)),
                      *call(fw.FN_NOC_WRITE, (niu, dst & 0xFFFFFFFF, dst >> 32, 0, 128, 0x20000, 1)),
                      *call(fw.FN_NOC_WAIT, (niu, 1, 1))]
            _, code = BlackholeRenderer().compile_core(stream)
            dev.run({role: code}, cores=[dev.workers[0]])
            dev.synchronize()
            result = bytearray(128)
            dev.dma.copyout(result, dst)
            self.assertEqual(result, payload[4032:4160])
        finally: dev.close()

  def test_compiled_worker_loops_on_both_cards(self):
    from device import Device
    # Worker-local output, safely above firmware/code and below the L1 limit.
    output = UOp.const(0x20000, dtypes.u32)
    wid = UOp.special(140, "worker_id")
    a, b = UOp.range(3, 0, "a"), UOp.range(5, 1, "b")
    first = output.index(a).store(wid * 100 + a).end(a)
    second = output.index(b + 3).store(wid * 100 + b + 10).end(b)
    done = output.after(first, second).index(8).store(UOp.const(0x1234, dtypes.u32))
    ren = RV32Renderer()
    program = to_program(UOp.sink(done), ren)
    stream = list(program.src[1].src)
    self.assertIs(stream[-1].ins_op, RVOps.RET)
    # Device.run concatenates the park epilogue, rather than calling a function.
    code = ren.assemble(stream[:-1])
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          dev.run({"brisc": code}, data={0x20000: bytes(36)})
          dev.synchronize()
          deadline = time.monotonic() + 10
          for worker, core in enumerate(dev.workers):
            while True:
              values = struct.unpack("<9I", dev.read_l1(core, 0x20000, 36))
              if values[-1] == 0x1234: break
              if time.monotonic() > deadline: self.fail(f"card {index} worker {core} timed out: {values}")
            self.assertEqual(values[:-1], tuple(worker * 100 + i for i in (0, 1, 2, 10, 11, 12, 13, 14)))
          # Exercise every subordinate's completion byte, a second launch,
          # and a subset whose leader is not the device's first worker.
          fence = ren.assemble([UOp.ins(RVOps.FENCE, (), dtypes.void)])
          dev.run({role: fence for role in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")}, cores=dev.workers[3:6])
          dev.synchronize()
          self.assertEqual(dev.kernel_signal.value, 2)
        finally: dev.close()


if __name__ == "__main__": unittest.main()
