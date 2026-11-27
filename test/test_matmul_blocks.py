"""Multi-face source ownership and Dst addressing, independent of multicast."""
import os
import struct
import numpy as np
import pytest

from compiler import UOp, dtypes, unpack_bundle
from compiler.blackhole.pipeline import instruction, compile_tile_graph
from compiler.blackhole.specs import Space, UnpackOp, FpuOp, PackOp, NocRead


@pytest.mark.skipif(os.environ.get("BH_HW") != "1", reason="set BH_HW=1 for both P150 cards")
@pytest.mark.parametrize("card", (0, 1))
def test_multiblock(card):
  from device import Device
  rng = np.random.default_rng(42)
  dev = Device(card)
  try:
    for bm, bn in ((1, 1), (2, 2), (4, 4), (2, 4), (4, 2)):
      for dtype, fidelity in ((dtypes.bf16, 3), (dtypes.bfp8, 2), (dtypes.bfp4, 1)):
        for exact in (True, False):
          kf = 3
          a = rng.integers(-3, 4, (bm, kf, 8, 16)).astype(np.float32)
          if not exact: a = (rng.uniform(-1, 1, a.shape).astype(np.float32).view(np.uint32) & 0xFFFF0000).view(np.float32)
          a_bytes = (a.view(np.uint32) >> 16).astype(np.uint16).tobytes()
          if dtype is dtypes.bf16:
            w = rng.integers(-3, 4, (bn, kf, 16, 16)).astype(np.float32)
            if not exact: w = (rng.uniform(-1, 1, w.shape).astype(np.float32).view(np.uint32) & 0xFFFF0000).view(np.float32)
            w_bytes = (w.view(np.uint32) >> 16).astype(np.uint16).tobytes()
            wsize = 512
          else:
            bits = dtype.bits
            mag = rng.integers(0, 8 if exact else 1 << (bits - 1), (bn, kf, 16, 16), dtype=np.uint8)
            sign = rng.integers(0, 2, mag.shape, dtype=np.uint8)
            sign[mag == 0] = 0
            exponent = np.full((bn, kf, 16), 127 + bits - 2, np.uint8) if exact else rng.integers(124, 130, (bn, kf, 16), dtype=np.uint8)
            w = mag.astype(np.float32) * (1 - 2 * sign.astype(np.float32)) * np.exp2(exponent.astype(np.float32)[..., None] - 127 - bits + 2)
            code = (mag | sign << (bits - 1)).reshape(bn, kf, 256)
            if bits == 4: code = code[..., ::2] | code[..., 1::2] << 4
            w_bytes = np.concatenate((exponent, code), axis=-1).tobytes()
            wsize = 16 + 256 * bits // 8
          kr = UOp.range(kf, 0, "k")
          ar = instruction(NocRead(0, 0, len(a_bytes)), UOp.const(0))
          wr = instruction(NocRead(1, 1, len(w_bytes)), UOp.const(0))
          au = instruction(UnpackOp(Space.SRCB, 0, src_dtype=dtypes.bf16, faces=bm, face_stride=kf * 256), ar, kr * 256)
          wu = instruction(UnpackOp(Space.SRCA, 1, src_dtype=dtype, rows=16, faces=bn, face_stride=kf * wsize), wr, kr * wsize)
          result = instruction(FpuOp("MVMUL", m_blocks=bm, n_blocks=bn, src_dtype=dtype, fidelity=fidelity, accumulate=True), au, wu).end(kr)
          cbs = {0: 0x20000, 1: 0x24000, **{2 + i: 0x30000 + i * 512 for i in range(bm * bn)}}
          for i in range(bm * bn): result = instruction(PackOp(2 + i, dst_slot=i), result)
          images = unpack_bundle(compile_tile_graph(UOp.sink(result), cbs).src[3].arg)
          addresses = [dev.alloc_dram(len(blob)) for blob in (a_bytes, w_bytes)]
          for address, blob in zip(addresses, (a_bytes, w_bytes)): dev.dma.copyin(address, memoryview(blob))
          dev.run(images, data={0x80: struct.pack("<2Q", *addresses)}, cores=dev.workers[:1])
          dev.synchronize()
          got = np.frombuffer(dev.read_l1(0, 0x30000, bm * bn * 512), np.float32).reshape(bm, bn, 8, 16).transpose(0, 2, 1, 3).reshape(bm * 8, bn * 16)
          a = a.transpose(0, 2, 1, 3).reshape(bm * 8, kf * 16)
          w = w.transpose(0, 3, 1, 2).reshape(bn * 16, kf * 16)
          if exact: np.testing.assert_array_equal(got, a @ w.T, err_msg=str((bm, bn, dtype)))
          else:
            ah, wh = [(v.view(np.uint32) & mask).view(np.float32) for v, mask in ((a, 0xFFFE0000), (w, 0xFFF80000))]
            expected = ah @ wh.T
            if fidelity > 1: expected += ah @ (w - wh).T
            if fidelity > 2: expected += (a - ah) @ wh.T
            # Each K step rounds the accumulated Dst, unlike a single face.
            np.testing.assert_array_less(abs(got - expected), abs(a) @ abs(w).T * kf * 2**-12 + 2e-6,
                                         err_msg=str((bm, bn, dtype)))
  finally: dev.close()
