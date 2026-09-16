"""Queued-device decode benchmark with reproducible tokens and optional logits.

Run via tt-device-queue run --device 0 -- ../.venv/bin/python -m
 tools.bench_llama_decode --output /tmp/decode.json [--source old_llama3.py].
--replay uses the exact baseline token history, including generated tokens.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
from transformers import AutoTokenizer


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--source', type=Path)
  parser.add_argument('--model', default='8b', choices=('1b', '8b'))
  parser.add_argument('--dtype', default='fp8', choices=('bf16', 'fp8'))
  parser.add_argument('--lm-head-dtype', choices=('bf16', 'fp8'))
  parser.add_argument('--split-attention', action=argparse.BooleanOptionalAction, default=None)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--prompt', default='Write a story about a robot learning to paint.')
  parser.add_argument('--context', type=int, help='repeat prompt tokens to this prefix length')
  parser.add_argument('--steps', type=int, default=64)
  parser.add_argument('--replay', type=Path)
  parser.add_argument('--logits', action='store_true', help='save final-position logits beside JSON')
  parser.add_argument('--output', required=True, type=Path)
  args = parser.parse_args()
  if args.lm_head_dtype is not None: os.environ['LLAMA_LM_HEAD_DTYPE'] = args.lm_head_dtype
  if args.split_attention is not None: os.environ['LLAMA_SPLIT_ATTENTION'] = str(int(args.split_attention))
  if args.steps < 1: parser.error('steps must be positive')
  if args.source:
    spec = importlib.util.spec_from_file_location('llama_benchmark_source', args.source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
  else:
    import examples.llama3 as module
  kernels = module.Llama3Kernels(args.model, args.dtype)
  tokenizer = AutoTokenizer.from_pretrained(kernels.checkpoint, local_files_only=True)
  baseline = json.loads(args.replay.read_text()) if args.replay else None
  if baseline:
    if baseline['model'] != args.model or baseline['dtype'] != args.dtype:
      parser.error('replay model and dtype must match the baseline')
    prompt = baseline['prompt_ids']
    history = baseline.get('input_ids', prompt + baseline['generated_ids'])
    args.steps = len(baseline['generated_ids'])
  else:
    prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': args.prompt}], add_generation_prompt=True)
    if args.context:
      if args.context < 1: parser.error('context must be positive')
      prompt = (prompt * ((args.context + len(prompt) - 1) // len(prompt)))[:args.context]
    history = prompt
  if len(prompt) + args.steps >= kernels.ROPE_CACHE_TOKENS: parser.error('context exceeds cache')
  started = time.perf_counter()
  runtime = module.Llama3Decode(device_index=args.device, kernels=kernels)
  try:
    runtime.load_tokens(history)
    for position in range(len(prompt) - 1): runtime.decode(position, logits=False, append=False)
    predictions, wall_us, device_us = [], [], []
    for position in range(len(prompt) - 1, len(prompt) - 1 + args.steps):
      token, elapsed = runtime.decode(position, append=not bool(baseline))
      predictions.append(int(token))
      wall_us.append(float(elapsed))
      device_us.append(float(runtime.decode_trace.last_profile['device_us']) if 'device_us' in runtime.decode_trace.last_profile else None)
    result = dict(model=args.model, dtype=args.dtype, device=args.device,
                  source=str(args.source) if args.source else 'examples/llama3.py',
                  lm_head_dtype=getattr(kernels, 'LM_HEAD_DTYPE', module.DType.BF16).name.lower(),
                  split_attention=getattr(kernels, 'SPLIT_ATTENTION', False),
                  weight_page_tiles=getattr(kernels, 'WEIGHT_PAGE_TILES', 1),
                  prompt_ids=prompt, generated_ids=predictions,
                  input_ids=history if baseline else prompt + predictions,
                  mean_wall_us=float(np.mean(wall_us)), wall_us=wall_us,
                  mean_device_us=float(np.mean([value for value in device_us if value is not None])),
                  elapsed_s=time.perf_counter()-started, startup=runtime.profile)
    if baseline:
      result['prediction_agreement'] = float(np.mean(np.array(predictions) == baseline['generated_ids']))
    if args.logits:
      data = runtime.device.read(runtime.logits)
      values = runtime.logits.to_numpy(data) if isinstance(data, bytes) else np.asarray(data)
      values = np.concatenate([row[:count] for row, count in zip(values, runtime.lm_weight.item_counts)])
      np.save(args.output.with_suffix('.npy'), values)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('prompt_ids','generated_ids','input_ids','wall_us','startup')}, indent=2))
  finally:
    runtime.close()


if __name__ == '__main__': main()
