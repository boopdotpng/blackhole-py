"""Greedy acceptance, rejection, EOS and context accounting without hardware."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from examples.llama3_speculative import generate, lookup
from examples.llama3_8b import EOS_TOKEN_IDS, ROPE_CACHE_TOKENS


class FakeRuntime:
  def __init__(self, continuation):
    self.continuation = continuation
    self.uploads = 0
    self.verified = []
  def load_tokens(self, tokens):
    self.history = list(tokens)
    self.uploads += 1
  def prefill(self, tokens):
    self.load_tokens(tokens)
  def decode(self, position, **kwargs):
    token = self.continuation[position]
    if kwargs.get('append', True):
      self.history = self.history[:position+1] + [token]
    return token, 0
  def verify(self, history, draft):
    self.verified.append((list(history), draft))
    pos = len(history)-1
    return self.continuation[pos], self.continuation[pos+1]


class SpeculativeTest(unittest.TestCase):
  def test_lookup_longest_recent_suffix(self):
    self.assertIsNone(lookup([1, 2, 3]))
    self.assertEqual(lookup([1, 2, 3, 1, 2, 4, 1, 2], min_ngram=2), 4)
    self.assertEqual(lookup([1, 2, 3, 4, 2, 9, 1, 2], min_ngram=2), 3)
    self.assertIsNone(lookup([1, 2, 3, 1, 2]))
    self.assertEqual(lookup([1, 2, 3, 4, 1, 2, 3]), 4)

  def test_accept_reject_and_bonus(self):
    for draft in (10, 99):
      with self.subTest(draft=draft), patch('examples.llama3_speculative.lookup', return_value=draft):
        r = FakeRuntime([10, 20, 30, 40, 50, 60])
        result = generate(r, [1], 5)
        self.assertEqual(result['tokens'], [10, 20, 30, 40, 50])
        self.assertEqual(result['accepted'], int(draft == 10))
        self.assertLessEqual(len(result['tokens']), 5)

  def test_eos_draft_and_bonus(self):
    eos = min(EOS_TOKEN_IDS)
    for continuation in ([eos, 20], [10, eos]):
      with patch('examples.llama3_speculative.lookup', return_value=continuation[0]):
        result = generate(FakeRuntime(continuation), [1], 5)
        self.assertEqual(result['tokens'], continuation[:continuation.index(eos)+1])

  def test_baseline_does_not_upload_per_token(self):
    r = FakeRuntime([10, 20, 30])
    result = generate(r, [1], 3, speculative=False)
    self.assertEqual(result['tokens'], [10, 20, 30])
    self.assertEqual(r.uploads, 1)

  def test_bounds(self):
    for ids, steps in (([], 1), ([1], 0), ([1], ROPE_CACHE_TOKENS)):
      with self.assertRaises(ValueError): generate(FakeRuntime([]), ids, steps)

  def test_prefill_leaves_last_token_unconsumed(self):
    from examples.llama3_speculative import SpeculativeDecode
    for length in (1, 2, 3, 4, 5, 31, 32, 33):
      with self.subTest(length=length):
        consumed = []
        runtime = SpeculativeDecode.__new__(SpeculativeDecode)
        runtime.load_tokens = lambda tokens: None
        runtime._verify_positions = lambda pos: consumed.extend((pos, pos+1))
        runtime.decode = lambda pos, **kw: consumed.append(pos)
        runtime.prefill(list(range(length)))
        self.assertEqual(consumed, list(range(length-1)))

  def test_verifier_residency(self):
    from ttko.device import Device
    from ttko.program import Dram
    from pcie import P150_DRAM_ENDPOINTS, P100_WORKER_CORES
    from fw.consts import TensixL1
    from examples.llama3_speculative import SpeculativeDecode
    d = Device.__new__(Device)
    d.dram = Dram(len(P150_DRAM_ENDPOINTS), P100_WORKER_CORES, P150_DRAM_ENDPOINTS)
    d.pcie = SimpleNamespace(cores=P100_WORKER_CORES)
    d.cq = SimpleNamespace(submit=lambda *a, **kw: None, noc=0, live=0)
    d.program_queue, d.read_queue = [], []
    d._resident_programs, d._param_templates = {}, {}
    def capture(params):
      result = d._install_param_templates(tuple(d.program_queue), params)
      d.program_queue.clear()
      return result
    d.capture_trace = capture
    runtime = SpeculativeDecode.__new__(SpeculativeDecode)
    runtime.device, runtime.attention_cores = d, 32
    runtime._allocate()
    runtime._build_programs()
    self.assertEqual(runtime.decode_launch_count, 163)
    self.assertEqual(runtime.verify_launch_count, 679)
    self.assertLessEqual(d._param_template_next, TensixL1.KERNEL_CACHE_END)
    for p in runtime.verify_programs.values():
      self.assertLessEqual(p._l1.next, TensixL1.DATA_BUFFER_SPACE_END)


if __name__ == '__main__': unittest.main()
