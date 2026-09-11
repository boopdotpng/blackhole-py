"""Sweep NoC partitions and attention workers while retaining uploaded weights."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from examples import llama3_8b_fp8 as llama3

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--weights', default='weights/llama3-8b-fp8')
parser.add_argument('--device', type=int, default=1)
parser.add_argument('--splits', type=int, nargs='+', default=[7, 3, 5, 10, 12, 14, 15, 1])
parser.add_argument('--output', default='validation/card1-tuning.json')
args = parser.parse_args()
runtime = llama3.Llama3Decode(args.weights, args.device)
record = json.loads(Path('validation/cpu-reference.json').read_text())
tokens = (record['prompt_ids'] + record['generated_ids'] + [9906] * 64)[:64]
results = []
baseline = None
try:
  variants = [(split, 16) for split in args.splits]
  for index in range(len(variants) + 2):
    if index == len(variants):
      best = max(results, key=lambda r:r['tok_s'])['noc_split_x']
      variants += [(best, 8), (best, 32)]
    split, workers = variants[index]
    llama3.PROJECTION_NOC_SPLIT_X = split
    runtime.attention_cores = workers
    runtime.device._resident_programs.clear()
    runtime.device._param_templates.clear()
    runtime._build_programs()
    runtime.load_tokens(tokens)
    predictions, samples, hashes = [], [], {}
    for position in range(63):
      token, elapsed = runtime.decode(position, append=False)
      predictions.append(token)
      if position >= 16: samples.append(elapsed)
      if position in (0, 15, 31, 32, 62):
        hashes[str(position)] = hashlib.sha256(runtime.device.read(runtime.logits)).hexdigest()
    if baseline is None: baseline = (predictions, hashes)
    result = {'noc_split_x':split, 'attention_workers':workers,
              'tok_s':1e6/statistics.mean(samples), 'median_us':statistics.median(samples),
              'exact_match':(predictions, hashes) == baseline, 'logit_sha256': hashes}
    results.append(result)
    Path(args.output).write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    if not result['exact_match']: raise RuntimeError('candidate changed reference outputs')
finally:
  runtime.close()
