"""Opt-in full-checkpoint regression; ordinary tests do not load 33B weights."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


# Greedy token IDs for "The capital of France is" matching the archived TTRV reference.
REFERENCE_IDS = [9965, 152361, 363, 5463, 290, 7582, 322, 14304]


@unittest.skipUnless(os.environ.get("BH_NANBEIGE") == "1", "set BH_NANBEIGE=1 for full-model inference")
class TestNanbeigeEndToEnd(unittest.TestCase):
  def test_reference_tokens_on_both_cards(self):
    root = Path(__file__).resolve().parents[1]
    for card in (0, 1):
      with self.subTest(card=card):
        result = subprocess.run([sys.executable, "examples/nanbeige.py", "--device", str(card),
                                 "--prompt", "The capital of France is", "--tokens", str(len(REFERENCE_IDS)), "--json"],
                                cwd=root, capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["layers"], 52)
        self.assertEqual(output["generated_ids"], REFERENCE_IDS)
        self.assertGreater(output["warm_tokens_per_second"], 0)
