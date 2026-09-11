"""Compare BS=1 prefill and subsequent decode against sequential ingestion."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from examples.llama3_8b import Llama3Decode


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=1)
  parser.add_argument('--weights', default='weights/llama3-8b-bf16')
  parser.add_argument('--chunk-size', type=int, choices=range(1, 9), default=4)
  parser.add_argument('--lengths', type=int, nargs='+', default=[1, 4, 5, 31, 32, 33, 65, 3])
  parser.add_argument('--decode-steps', type=int, default=4)
  parser.add_argument('--output', default='validation/prefill.json')
  args = parser.parse_args()
  if args.decode_steps < 1 or any(n < 1 or n + args.decode_steps >= 8192 for n in args.lengths):
    parser.error('lengths must be positive and leave room for the requested decode steps')
  from transformers import AutoTokenizer
  tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)
  seed = tokenizer.encode('The capital of France is Paris. Explain why the sky is blue. ')
  runtime = Llama3Decode(args.weights, args.device)
  results = []
  try:
    for count in args.lengths:
      ids = (seed * ((count + len(seed) - 1) // len(seed)))[:count]
      runtime.load_tokens(ids)
      started = time.perf_counter()
      for position in range(count):
        expected, _ = runtime.decode(position, logits=position == count-1, append=position == count-1)
      baseline_s = time.perf_counter() - started
      reference = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
      continuation = [runtime.decode(position)[0] for position in range(count, count + args.decode_steps)]
      started = time.perf_counter()
      actual, _ = runtime.prefill(ids, chunk_size=args.chunk_size)
      prefill_s = time.perf_counter() - started
      logits = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
      following = [runtime.decode(position)[0] for position in range(count, count + args.decode_steps)]
      item = {'prompt_tokens': count, 'baseline_prompt_s': baseline_s, 'prefill_total_s': prefill_s,
              'prefill': runtime._prefill.profile, 'expected_first': expected, 'actual_first': actual,
              'expected_continuation': continuation, 'actual_continuation': following,
              'logits_equal': bool(np.array_equal(reference, logits)),
              'logit_pcc': float(np.corrcoef(reference.ravel(), logits.ravel())[0, 1]),
              'logit_max_error': float(np.max(np.abs(reference-logits)))}
      results.append(item)
      print(json.dumps(item), flush=True)
      Path(args.output).parent.mkdir(parents=True, exist_ok=True)
      Path(args.output).write_text(json.dumps({'device': args.device, 'chunk_size': args.chunk_size,
                                              'results': results}, indent=2) + '\n')
      if expected != actual or continuation != following or not item['logits_equal']:
        raise AssertionError('prefill differs from sequential BF16 decode')
  finally:
    runtime.close()


if __name__ == '__main__': main()
