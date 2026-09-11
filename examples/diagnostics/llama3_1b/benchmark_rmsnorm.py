"""Same-history RMSNorm A/B/B/A decode comparison on one explicitly chosen card."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import time
import numpy as np
from examples import llama3_1b as llama3
from transformers import AutoTokenizer


def main():
  os.environ['LLAMA_RMSNORM'] = 'hybrid'
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, required=True)
  parser.add_argument('--baseline', default='validation/rmsnorm_baseline.json')
  parser.add_argument('--reference', default='validation/rmsnorm_reference.py')
  parser.add_argument('--weights', required=True)
  parser.add_argument('--output', default='validation/rmsnorm_abba.json')
  args = parser.parse_args()
  baseline = json.loads(Path(args.baseline).read_text())
  tokenizer = AutoTokenizer.from_pretrained('weights/llama3-1b', local_files_only=True)
  prompt = tokenizer.apply_chat_template(
    [{'role': 'user', 'content': baseline['prompts'][0]}],
    tokenize=True, add_generation_prompt=True)
  if not isinstance(prompt, list): prompt = prompt['input_ids']
  teacher = baseline['optimized'][0]['generated_tokens']
  spec = importlib.util.spec_from_file_location('rmsnorm_reference', args.reference)
  reference = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(reference)
  report = {'device': args.device, 'steps': len(teacher),
            'prompt_tokens': len(prompt), 'attention_cores': baseline['attention_cores'],
            'order': ['reference', 'hybrid', 'hybrid', 'reference'],
            'teacher_tokens': teacher, 'runs': [],
            'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (Path(args.reference), Path(llama3.__file__),
                           Path('examples/rmsnorm_hybrid.py'))}}
  references = {}
  for kind in report['order']:
    module = reference if kind == 'reference' else llama3
    runtime = module.Llama3Decode(args.weights, args.device,
                                 attention_cores=baseline['attention_cores'])
    samples, tokens, accuracy = [], [], []
    try:
      runtime.load_tokens(prompt + teacher)
      for position in range(len(prompt)-1):
        runtime.decode(position, logits=False, append=False)
      for step in range(len(teacher)):
        position = len(prompt)-1+step
        start = time.perf_counter_ns()
        token, _ = runtime.decode(position, append=False)
        samples.append((time.perf_counter_ns()-start)/1e3)
        tokens.append(token)
        if step in (0, 31, 63, len(teacher)-1):
          raw = runtime.device.read(runtime.logits)
          logits = (np.frombuffer(raw, dtype='<u2').astype(np.uint32) << 16).view(np.float32).astype(np.float64)
          if not np.all(np.isfinite(logits)): raise AssertionError('nonfinite logits')
          if kind == 'reference' and step not in references:
            references[step] = logits
          ref = references[step]
          delta = logits-ref
          accuracy.append({'step': step,
            'cosine': float(np.dot(logits, ref)/(np.linalg.norm(logits)*np.linalg.norm(ref))),
            'relative_l2': float(np.linalg.norm(delta)/np.linalg.norm(ref)),
            'max_absolute': float(np.max(np.abs(delta)))})
      run = {'kind': kind, 'tok_s': len(samples)*1e6/sum(samples),
             'median_us': statistics.median(samples), 'decode_us': samples,
             'tokens': tokens, 'matching_teacher_predictions': sum(a==b for a,b in zip(tokens,teacher)),
             'sampled_logits': accuracy}
      report['runs'].append(run)
      print(kind, f"{run['tok_s']:.3f} tok/s",
            f"teacher predictions {run['matching_teacher_predictions']}/{len(teacher)}",
            f"min cosine {min(a['cosine'] for a in accuracy):.8f}", flush=True)
    finally:
      runtime.close()
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
  for kind in ('reference', 'hybrid'):
    values = [r['tok_s'] for r in report['runs'] if r['kind']==kind]
    print(kind, 'mean tok/s', statistics.mean(values), flush=True)


if __name__ == '__main__':
  main()
