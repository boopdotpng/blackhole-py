"""FP8 and BF16 matmul: FP32 Dst and L1 partials, including cancellation across
K blocks, and the epilogue's row-major BF16 output (rounded to nearest, ties
away from zero)."""
import numpy as np
import pytest

from examples import matmul_peak as m
from cq import McastWrite, Run, rectangles


def run_case(bh, monkeypatch, a, b, *, block_k=1, subblock=(1, 4), dtype="fp8", fidelity=None):
  k = m.k
  for name, value in dict(INPUT_DTYPE=k.DType.FP8 if dtype == "fp8" else k.DType.BF16,
                          INPUT_TILE_BYTES=1024 if dtype == "fp8" else 2048,
                          FIDELITY=fidelity or (1 if dtype == "fp8" else 4),
                          ROW_MOP=dtype == "fp8",
                          SUPPORTED_IN0_BLOCK_WS=(block_k,),
                          SUPPORTED_OUT_SUBBLOCK_H=subblock[0],
                          SUPPORTED_OUT_SUBBLOCK_W=subblock[1], WRITER_WAVE_ROWS=0).items():
    monkeypatch.setattr(k, name, value)
  rows, inner = a.shape
  columns = b.shape[1]
  plan = k.plan_matmul(rows, inner, columns, [bh.core])
  shape = (plan.mt*32, plan.kt*32, plan.nt*32)
  buffers, quantized = [], []
  for values, padded_shape in ((a, shape[:2]), (b, shape[1:])):
    if dtype == "fp8":
      codes = m.fp8_encode(values)
      quantized.append(m.fp8_decode(codes))
    else:
      codes = (values.view(np.uint32) >> 16).astype(np.uint16)
      quantized.append((codes.astype(np.uint32) << 16).view(np.float32))
    padded_shape = (padded_shape[0], k.input_dram_columns(padded_shape[1]))
    padded = np.zeros(padded_shape, dtype=codes.dtype)
    padded[:values.shape[0], :values.shape[1]] = codes
    buffer = bh.device.alloc_interleaved_dram(padded.nbytes, page_size=k.INPUT_TILE_BYTES)
    bh.device.write_dram(buffer, padded.tobytes())
    buffers.append(buffer)
  columns_out = m.epilogue.output_columns(plan)
  output = bh.device.alloc_interleaved_dram(shape[0]*columns_out*2, page_size=2048)
  bh.device.write_dram(output, b'\xa5'*output.size)
  program, commands, _ = m.build(plan, bh.device.pcie.dram_endpoints,
                                 buffers[0].address, buffers[1].address, output.address)
  # Reusing the same L1 partials must overwrite block zero on each invocation.
  for iteration in range(2):
    print('ITERATION', iteration, flush=True)
    try:
      bh.device.cq.submit(commands if iteration == 0 else (
        McastWrite(rectangles(program.cores), m.asm.SEM_BASE, bytes(128)), Run(program.cores)), timeout=10)
    except TimeoutError:
      m.dump_timeout(bh.device, program.cores)
      from pcie import TLBWindow
      with TLBWindow(bh.device.pcie.fd, bh.core) as win:
        win.target(0xffa00000, bh.core)
        def wr(addr, value): win.write(addr-0xffa00000, value)
        def rd(addr): return int.from_bytes(win.read(addr-0xffa00000,4),'little')
        groups={}
        for daisy, sigs in ((1,range(14)), (6,(9,)), (14,range(8))):
          for sig in sigs:
            vals=[]
            for sel in range(4):
              wr(0xffb12054,(1<<29)|(sel<<25)|(daisy<<16)|sig)
              vals.append(rd(0xffb1205c))
            groups[f'{daisy}:{sig}']=vals
        import json
        open('/tmp/bf16_debug_bus.json','w').write(json.dumps(groups))
        open('/tmp/hung_actual.bin','wb').write(program.binary)
        for rid in (1,2,3):
          def dw(reg,val):
            wr(0xffb12084,val); wr(0xffb12080,0x80010000+(rid<<17)+reg); wr(0xffb12080,0)
          def dr(reg):
            wr(0xffb12080,0x80000000+(rid<<17)+reg); wr(0xffb12080,0)
            return rd(0xffb1208c)
          dw(1,0x80000001)
          regs=[]
          for reg in range(33):
            dw(2,reg); dw(1,0x80000008); regs.append(hex(dr(4)))
          print('HALTED',rid,regs,flush=True)
      print('ENTRIES',program.entries,flush=True)
      print('PHASE', np.frombuffer(bh.read_l1(bh.core,k.PASS_BASE+96,12), '<u4'))
      raise
    codes = np.frombuffer(bh.device.read_dram(output), '<u2')[:shape[0]*columns_out].reshape(shape[0], columns_out)
    actual = (codes[:rows, :columns].astype(np.uint32) << 16).view(np.float32)
    yield actual.copy(), quantized[0] @ quantized[1]


@pytest.mark.parametrize('dtype', ('fp8', 'bf16'))
@pytest.mark.parametrize('inner', (32, 64, 96, 257))
@pytest.mark.parametrize('subblock', ((1, 4), (1, 2)))
def test_fp32_matmul_blocks_and_edges(bh, monkeypatch, inner, subblock, dtype):
  rng = np.random.default_rng(123)
  a = rng.uniform(-1, 1, (65, inner)).astype(np.float32)
  b = rng.uniform(-1, 1, (inner, 129)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, subblock=subblock, dtype=dtype):
    assert np.isfinite(actual).all()
    # BF16 output rounding alone gives ~1.1e-3 relative L2; MVMUL's internal
    # accumulation is close to, not exactly, FP32 on cancelling sums.
    error = np.linalg.norm(actual - reference) / np.linalg.norm(reference)
    assert error < 0.003, error


@pytest.mark.parametrize('dtype', ('fp8', 'bf16'))
def test_fp32_preserves_small_partials(bh, monkeypatch, dtype):
  # Exact E4M3 inputs: 2048 + 2048*(1/64)^2 - 2048 = 0.5.
  # FP16 partial accumulation loses the small term while the running sum is 2048.
  a = np.ones((32, 6144), dtype=np.float32)
  b = np.ones((6144, 128), dtype=np.float32)
  a[:, 2048:4096] = 1/64
  b[2048:4096] = 1/64
  b[4096:] = -1
  for actual, _ in run_case(bh, monkeypatch, a, b, block_k=8, dtype=dtype):
    np.testing.assert_array_equal(actual, np.full_like(actual, .5))


def test_fp32_exceeds_fp16_range(bh, monkeypatch):
  a = np.full((32, 64), 448, dtype=np.float32)
  b = np.full((64, 128), 448, dtype=np.float32)
  for actual, _ in run_case(bh, monkeypatch, a, b):
    np.testing.assert_array_equal(actual, np.full_like(actual, 64*448*448))


@pytest.mark.parametrize('columns', (385, 1024))
@pytest.mark.parametrize('fast', (False, True))
@pytest.mark.parametrize('fidelity', (2, 4))
def test_bf16_readers_accumulation_and_relaunch(bh, monkeypatch, fast, fidelity, columns):
  monkeypatch.setattr(m.k, 'FAST_READS', fast)
  rng = np.random.default_rng(814)
  a = rng.uniform(-1, 1, (65, 401)).astype(np.float32)
  b = rng.uniform(-1, 1, (401, columns)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, dtype='bf16', block_k=6, fidelity=fidelity):
    assert np.isfinite(actual).all()
    error = np.linalg.norm(actual-reference) / np.linalg.norm(reference)
    assert error < (0.003 if fidelity == 4 else 0.01), error
