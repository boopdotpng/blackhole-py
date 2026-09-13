"""Host checks for the recovered multicast benchmark; --run validates silicon."""
import struct
import numpy as np
import pytest

from examples.matmul_peak import build, fp8_decode, fp8_encode, matrix_bytes, run, tile_bytes
from examples.matmul_peak_kernel import asm, kernel as k
from fw.consts import TensixL1
from pcie import P100_WORKER_CORES, P100_DRAM_ENDPOINTS
from cq import McastWrite, UnicastWrite
from program import GridProgram


def test_storage_face_order():
  values = np.arange(64*96, dtype=np.float32).reshape(64, 96)
  words = (values.view(np.uint32) >> 16).astype('<u2')
  expected = b''.join(words[y+fy:y+fy+16, x+fx:x+fx+16].tobytes()
                      for y in range(0,64,32) for x in range(0,96,32)
                      for fy in (0,16) for fx in (0,16))
  assert tile_bytes(values) == expected
  assert matrix_bytes(expected, 64, 96) == words.tobytes()


def test_fp8_rounding_saturation_and_flush():
  values = np.array([0., -0., 1., 1.0625, 1.1875, 448., 1000., -448., 2**-9, -2**-9, 2**-6])
  np.testing.assert_array_equal(fp8_encode(values), [0,128,56,56,58,126,126,254,0,128,8])
  np.testing.assert_array_equal(fp8_decode(np.array([8,56,126,254])), [2**-6,1.,448.,-448.])
  assert np.isnan(fp8_decode([127,255])).all()
  with pytest.raises(ValueError):
    fp8_encode([np.inf])


@pytest.mark.parametrize('dtype', ['bf16', 'fp8'])
@pytest.mark.parametrize('shape', [(8,16,16), (257,193,129), (5000,5000,5000)])
def test_padding_and_common_grid_program(dtype, shape):
  m,n,inner = shape
  run(m,n,inner,dtype=dtype)
  plan = k.plan_matmul(m,inner,n,list(P100_WORKER_CORES))
  assert plan.m_extent % 8 == 0 and plan.n_extent % 16 == 0 and plan.k_extent % 16 == 0
  assert m <= plan.m_extent*len(plan.rows) < m+8*len(plan.rows)
  assert n <= plan.n_extent*len(plan.cols) < n+16*len(plan.cols)
  assert inner <= plan.k_extent < inner+16
  program, commands, sources = build(plan,P100_DRAM_ENDPOINTS,output_noc='split')
  assert set(sources) == {'brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2'}
  assert isinstance(program, GridProgram)
  assert program.global_size == (len(plan.rows), len(plan.cols))
  for name, (base, image) in sources.items():
    assert 0x12000 <= base < base+len(image) <= asm.ARG_BASE
    assert len(image) % 4 == 0
    assert program.binary[base-program.base:base-program.base+len(image)] == image
    assert program.entries[name] == base
  assert commands[-1].cores == program.cores
  rank_writes = [c for c in commands if isinstance(c, UnicastWrite) and c.addr == TensixL1.GRID_RANK_BASE]
  assert len(rank_writes) == 1 and TensixL1.GRID_RANK_BASE % 16 == 0
  assert [struct.unpack('<2I', data) for data in rank_writes[0].data] == [
    (ri, ci) for ri in range(len(plan.rows)) for ci in range(len(plan.cols))]
  # No host-written per-core recipe tables or worker-slot jump instructions.
  writes = [c for c in commands if isinstance(c, (McastWrite, UnicastWrite))]
  assert not any(c.addr == asm.ARG_BASE or c.addr in TensixL1.WORKER_TEXT_BASE.values() for c in writes)
  for command in commands: command.lower()


def test_buffers_and_output_noc_are_runtime_values():
  run(257, 193, 129)
  plan = k.plan_matmul(257, 129, 193, list(P100_WORKER_CORES))
  bundles = []
  for noc in ('split', '0', '1'):
    program, commands, _ = build(plan, P100_DRAM_ENDPOINTS, 0x1000, 0x2000, 0x3000, output_noc=noc)
    bundles.append(program.binary)
    table, = [c.data for c in commands if isinstance(c, McastWrite) and c.addr == TensixL1.PARAM_BASE]
    assert struct.unpack('<5I', table[:20]) == (0x1000, 0x2000, 0x3000, len(P100_DRAM_ENDPOINTS), 2 if noc == 'split' else int(noc))
  assert bundles[0] == bundles[1] == bundles[2]
  changed, _, _ = build(plan, P100_DRAM_ENDPOINTS, 0x4000, 0x5000, 0x6000)
  assert changed.binary == bundles[0]



@pytest.mark.parametrize('kwargs', [{'subblock':(4,2)}, {'block_k':-1}, {'dtype':'lofi'}, {'output_noc':'2'}])
def test_reject_unsupported_configuration(kwargs):
  with pytest.raises(ValueError):
    run(32,32,32,**kwargs)


@pytest.mark.parametrize('rows,cols', [((2,), (1,)), ((2,), (1, 2, 10)), ((2, 3), (1,)),
                                     ((2, 3), (1, 2, 10)), ((2, 3), (10, 11))])
def test_on_core_argument_tables_match_reference(bh, rows, cols):
  from examples.matmul_peak_kernel.args import emit_args
  from ttko.asm import Asm
  from fw.consts import KERNEL_ROLES
  from pcie import TLBWindow
  from program import Program
  run(64, 64, 64)  # reset benchmark format/tuning globals to BF16 defaults
  device = bh.device
  cores = [(x, y) for y in rows for x in cols]
  assert set(cores) <= set(device.cores)
  plan = k.plan_matmul(64, 64, 64, cores)
  asm.CONTEXT = {'cbs': [], 'endpoints': device.pcie.dram_endpoints, 'address': 0x12000}
  sources = {}
  for role in KERNEL_ROLES:
    if role in ('brisc', 'ncrisc'):
      fw = k.MatmulKernel(role=role)
      emit_args(fw, plan, reader=role == 'brisc')
    else:
      fw = Asm(role)
      fw.base = asm.CONTEXT['address']
    image = fw.lower()
    sources[role] = (fw.base, image)
    asm.CONTEXT['address'] = (fw.base + len(image) + 63) & -64
  program = GridProgram(sources, rows=plan.rows, cols=plan.cols)
  topology = struct.pack('<128I', *(plan.rows + (0,)*(64-len(plan.rows)) + plan.cols + (0,)*(64-len(plan.cols))))
  for a, b, c in ((0x1000, 0x2000, 0x3000), (0x4000, 0x5000, 0x6000)):
    banks = len(device.pcie.dram_endpoints)
    device.cq.submit(program.commands(params=(a, b, c, banks, 2), l1={asm.GRID_BASE: topology}), timeout=bh.timeout)
    with TLBWindow(device.pcie.fd, program.cores[0]) as window:
      for ri, y in enumerate(plan.rows):
        for ci, x in enumerate(plan.cols):
          window.target(0, (x, y))
          assert struct.unpack('<2I', window.read(TensixL1.GRID_RANK_BASE, 8)) == (ri, ci)
          reader, writer = k.reader_args(plan, a, (x, y), banks), k.writer_args(plan, b, c, (x, y), banks)
          assert struct.unpack(f'<{len(reader)}I', window.read(asm.ARG_BASE, len(reader)*4)) == tuple(reader)
          assert struct.unpack(f'<{len(writer)}I', window.read(asm.ARG_BASE+128, len(writer)*4)) == tuple(writer)
    # Switching back to an ordinary launch must restore fixed worker entries.
    direct = Program({core: {} for core in program.cores})
    device.cq.submit(direct.commands(), timeout=bh.timeout)
