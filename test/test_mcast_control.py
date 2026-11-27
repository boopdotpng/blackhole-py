"""Execute emitted sender control flow with hostile caller-register clobbers."""
import struct
import pytest
import fw
from compiler import Tensor, dtypes, lower_tensor, linearize_schedule, unpack_bundle
from compiler.blackhole.lower import lower_kernel
from test.test_isa import run_rv32


def test_sender_addresses_and_credit_gates(monkeypatch):
  monkeypatch.setenv("BH_MCAST", "1")
  a, w = Tensor.buffer("a", (64, 79), dtypes.bf16), Tensor.buffer("w", (256, 79), dtypes.bf16)
  call, = linearize_schedule(lower_tensor(a.matmul(w.T, dtype=dtypes.fp32)))
  kernel = lower_kernel(call.kernel, call.args)
  code = unpack_bundle(kernel.program.src[3].arg)["brisc"] + struct.pack("<I", 0x8067)
  a_slot, w_slot = call.args.index(a.uop), call.args.index(w.uop)
  for credit in (100, 0):
    for wx, wy in ((0, 0), (1, 0), (0, 1), (3, 1)):
      mem = bytearray(0x210000)
      struct.pack_into("<II", mem, fw.WORKER_X, wx, wy)
      for i in range(len(call.args)): struct.pack_into("<II", mem, fw.ARG_BASE + i * 8, (i + 1) * 0x1000000, 0x8C000000)
      for stream in range(2):
        for slot in range(2): struct.pack_into("<I", mem, fw.MCAST_CTRL_BASE + stream * 256 + 0x40 + slot * 16, credit)
      reads = []
      def resident(address, registers):
        if address not in (fw.FN_NOC_READ, fw.FN_NOC_WAIT, fw.FN_NOC_MCAST): return False
        if address == fw.FN_NOC_READ:
          niu, lo, hi, off, size, local, tid = registers[10:17]
          assert niu == 0 and hi == 0x8C000000 and tid == 0
          reads.append((lo // 0x1000000 - 1, off, size, local))
        for i in (6, 7, *range(10, 18), *range(28, 32)): registers[i] = 0xBAD00000 + i
        registers[1] = 0xFFFFFFFC
        return True
      if credit:
        run_rv32(code, {3: 0x200000}, mem, on_call=resident)
        expected = []
        for seq in range(5):
          if wx == seq % 4:
            expected += [(a_slot, ((wy * 4 + b) * 5 + seq) * 256, 256, 0x20000 + seq % 2 * 1024 + b * 256) for b in range(4)]
          if wy == seq % 2:
            expected += [(w_slot, ((wx * 4 + b) * 5 + seq) * 512, 512, 0x21000 + seq % 2 * 2048 + b * 512) for b in range(4)]
        assert reads == expected, (wx, wy)
      else:
        with pytest.raises(RuntimeError, match="exceeded max_steps"):
          run_rv32(code, {3: 0x200000}, mem, max_steps=5000, on_call=resident)
        assert all((offset // size) % 5 < 2 for _, offset, size, _ in reads), (wx, wy, reads)
