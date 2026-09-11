"""Sweep evenly placed projection workers against an unchanged global checkpoint layout."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np
from examples import llama3_8b_fp8 as llama3

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--weights', default='weights/llama3-8b-fp8')
parser.add_argument('--device', type=int, default=1)
parser.add_argument('--output', default='validation/card1-worker-tuning.json')
args = parser.parse_args()
llama3.LLAMA_CORES = 117
runtime = llama3.Llama3Decode(args.weights, args.device, attention_cores=32)
record = json.loads(Path('validation/cpu-reference.json').read_text())
tokens = (record['prompt_ids'] + record['generated_ids'] + [9906] * 64)[:64]
originals = {name: getattr(runtime, name) for name in ('q_compact','k_compact','v_compact','gate','up','hidden','logits')}
all_cores = runtime.device.dram.cores
baseline = None
results = []
try:
  for count in (117, 112, 104, 96, 88, 80):
    cores = tuple(all_cores[i] for i in np.linspace(0, len(all_cores)-1, count, dtype=int))
    llama3.LLAMA_CORES = count
    runtime.lm_weight = replace(runtime.lm_weight, cores=cores)
    for layer in runtime.layers:
      for name, buffer in layer['weights'].items():
        if len(buffer.shape) == 2:
          layer['weights'][name] = replace(buffer, cores=cores)
    for name, width in (('q_compact',llama3.Q_PROJ_DIM),('k_compact',llama3.KV_PROJ_DIM),
                        ('v_compact',llama3.KV_PROJ_DIM),('gate',llama3.MLP_DIM),
                        ('up',llama3.MLP_DIM),('hidden',llama3.MLP_DIM),('logits',llama3.VOCAB_SIZE)):
      buffer = replace(originals[name], shape=(count, (width + count - 1)//count), cores=cores)
      assert buffer.size <= originals[name].size
      setattr(runtime, name, buffer)
    runtime.device._resident_programs.clear()
    runtime.device._param_templates.clear()
    runtime._build_programs()
    runtime.load_tokens(tokens)
    predictions, samples, hashes = [], [], {}
    for position in range(63):
      token, elapsed = runtime.decode(position, append=False)
      predictions.append(token)
      if position >= 16: samples.append(elapsed)
      if position in (0,15,31,32,62):
        compact = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
        logical = np.concatenate([row[:n] for row,n in zip(compact, runtime.lm_weight.item_counts)])
        hashes[str(position)] = hashlib.sha256(logical.tobytes()).hexdigest()
    if baseline is None: baseline = predictions, hashes
    result = {'projection_workers':count,'tok_s':1e6/statistics.mean(samples),
              'median_us':statistics.median(samples),'exact_match':(predictions,hashes)==baseline,
              'logit_sha256':hashes}
    results.append(result)
    Path(args.output).write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(result),flush=True)
    if not result['exact_match']: raise RuntimeError('worker layout changed numerical results')
finally:
  runtime.close()
