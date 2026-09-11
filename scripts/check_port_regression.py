"""Check preservation of pre-port TP2 results, separately from numerical quality."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--report', type=Path, default=Path('validation/current/tp2-comparison.json'))
  args = parser.parse_args()
  root = Path(__file__).resolve().parents[1]
  original = json.loads((root / 'docs/forks/llama3-8b-fp8-tp2/validation/tp2-comparison-pack.json').read_text())
  current = json.loads(args.report.read_text())
  positions = 0
  for new_case, old_case in zip(current['cases'], original['cases'], strict=True):
    for field in ('prompt', 'history', 'baseline_tokens'):
      if new_case[field] != old_case[field]: raise AssertionError(f'changed {field}')
    for new_row, old_row in zip(new_case['comparisons'], old_case['comparisons'], strict=True):
      comparable = lambda row: {key: value for key, value in row.items() if key != 'seconds'}
      if comparable(new_row) != comparable(old_row):
        raise AssertionError(f'changed decisions or metrics at position {new_row["position"]}')
      positions += 1
  expected = json.loads((root / 'docs/merge/reference-logits.json').read_text())
  with np.load(args.report.with_suffix('.npz')) as arrays:
    actual = {key: hashlib.sha256(arrays[key].tobytes()).hexdigest() for key in arrays.files}
  if actual != expected: raise AssertionError('single-card reference logits changed')
  print(f'Preserved {positions} token decisions/metric rows and {len(expected)} reference logit arrays.')
  print('The inherited TP2 versus single-card 5% RMS quality threshold still fails; this checks port preservation only.')


if __name__ == '__main__': main()
