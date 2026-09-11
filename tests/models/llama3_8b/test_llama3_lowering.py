from tests.models.topology import P150_WORKER_CORES
"""CPU-only checks that full decode kernels and templates fit worker L1."""

from itertools import product
from types import SimpleNamespace
import unittest

from ttko.device import Device
from examples.llama3_8b import Llama3Decode, LLAMA_CORES
from fw.consts import TensixL1
from pcie import P100_DRAM_ENDPOINTS, P100_WORKER_CORES
from pcie import P150_DRAM_ENDPOINTS
from ttko.program import Dram


class DecodeResidencyTest(unittest.TestCase):
  def test_supported_topologies(self):
    for (endpoints, cores), attention_cores in product((
      (P100_DRAM_ENDPOINTS, P100_WORKER_CORES),
      (P150_DRAM_ENDPOINTS, P100_WORKER_CORES),
      (P150_DRAM_ENDPOINTS, P150_WORKER_CORES),
    ), (8, 16, 32)):
      with self.subTest(banks=len(endpoints), workers=len(cores), attention_cores=attention_cores):
        # Use the real allocator, lowering, relocation and template builder.
        # Only the hardware transport is replaced; no device is opened.
        device = Device.__new__(Device)
        device.dram = Dram(len(endpoints), cores, endpoints)
        device.pcie = SimpleNamespace(cores=cores)
        device.cq = SimpleNamespace(submit=lambda *a, **kw: None, noc=0, live=0)
        device.program_queue, device.read_queue = [], []
        device._resident_programs, device._param_templates = {}, {}
        device.capture_trace = lambda params: device._install_param_templates(
          tuple(device.program_queue), params,
        )
        runtime = Llama3Decode.__new__(Llama3Decode)
        runtime.device = device
        runtime.attention_cores = attention_cores
        runtime._allocate()
        self.assertNotEqual(runtime.lm_storage.addr, runtime.embedding_weight.addr)
        self.assertEqual(len(runtime.lm_storage.cores), 1)
        self.assertEqual(len(runtime.lm_weight.cores), LLAMA_CORES)
        self.assertEqual(runtime.lm_storage.addr, runtime.lm_weight.addr)
        self.assertEqual(runtime.lm_storage.physical_tiles, 128256 * 4)
        runtime._build_programs()
        self.assertLessEqual(device._param_template_next, TensixL1.KERNEL_CACHE_END)
        self.assertEqual(runtime.decode_launch_count, 163)
        self.assertEqual(len(runtime.programs["attention"].cores), attention_cores)
        for program in runtime.programs.values():
          self.assertLessEqual(program._l1.next, TensixL1.DATA_BUFFER_SPACE_END)


if __name__ == "__main__":
  unittest.main()
