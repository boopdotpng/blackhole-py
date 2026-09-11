from dataclasses import replace
import numpy as np
import pytest

from ttko import DType
from ttko.program import Const, Dram, Program
from ttko.device import Device
from ttko.layout import convert
from fw.consts import TensixL1


def test_layout_kernel_lowering():
  for dtype in (DType.BF16, DType.FP8, DType.F32):
    buffer = Dram().buffer('layout', dtype, (3, 1057), axis=0)
    for inverse in (False, True):
      images = convert(buffer, buffer, inverse=inverse).lower()
      assert all(len(roles['brisc']) <= TensixL1.WORKER_TEXT_SIZE['brisc'] for roles in images.values())


def test_raw_host_padding():
  buffer = Dram().buffer('raw', DType.U32, (3, 1057), axis=0, tilized=False)
  data = np.arange(3 * 1057, dtype='<u4').tobytes()
  assert buffer.unpad_data(buffer.pad_data(data)) == data
  assert buffer.pad_data(data)[:1057 * 4] == data[:1057 * 4]


def test_model_runtime_hardware(request):
  if not request.config.getoption('--bh-hardware'): pytest.skip('requires Blackhole')
  device = Device(request.config.getoption('--bh-device'))
  try:
    device.init_device()
    for dtype in (DType.BF16, DType.FP8, DType.F32):
      b = device.dram.buffer('layout', dtype, (3, 1057), axis=0)
      data = bytes((i % 251 for i in range(3 * 1057 * dtype.itemsize)))
      device.write(b, data)
      assert device.read(b) == data
      assert device.read(b) == data
      physical_view = replace(b, shape=(b.physical_tiles * 1024,), axis=None,
                              cores=(b.cores[0],), tilized=False, global_address=True)
      raw = np.frombuffer(b.pad_data(data), dtype=f'V{dtype.itemsize}')
      expected = raw.reshape(-1, 2, 16, 2, 16).transpose(0, 1, 3, 2, 4).tobytes()
      assert device.read(physical_view) == expected
    # Exercise the enlarged parameter template and resident kernel path.
    params = tuple(Const(f'p{i}', i + 100) for i in range(24))
    p = Program((device.cores[0],), *params)
    reg = p.brisc.reg()
    p.brisc.read(reg, p.param_addr(params[-1]))
    p.brisc.write(TensixL1.DATA_BUFFER_SPACE_BASE, reg)
    device.cache_kernels((p,))
    device.queue(p)
    trace = device.capture_trace(runtime_params=('p23',))
    trace.replay({'p23': 0x12345678})
    from pcie import TLBWindow
    with TLBWindow(device.pcie.fd, device.cores[0]) as window:
      window.target(0)
      assert int.from_bytes(window.read(TensixL1.DATA_BUFFER_SPACE_BASE, 4), 'little') == 0x12345678
  finally:
    device.close()
