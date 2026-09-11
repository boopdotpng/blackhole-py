"""CPU logit checks through context 512, then fixed-length hardware benchmarks."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import statistics
import time
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from examples import llama3_8b as llama3
from examples.diagnostics.llama3_8b.benchmark_llama3 import DEFAULT_PROMPTS, WEIGHT_BYTES_PER_TOKEN


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=1)
  parser.add_argument('--output', default='validation/card1-final.json')
  args = parser.parse_args()
  torch.set_num_threads(8)
  tokenizer = AutoTokenizer.from_pretrained('weights/llama3-8b-bf16', local_files_only=True)
  text = 'The sky appears blue because air molecules scatter short wavelengths of sunlight more strongly than long wavelengths. '
  ids = tokenizer.encode(text * 70, add_special_tokens=True)[:512]
  positions = [0, 1, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255, 256, 511]
  print('Computing CPU reference through 512 tokens', flush=True)
  model = AutoModelForCausalLM.from_pretrained('weights/llama3-8b-bf16', local_files_only=True,
                                              dtype=torch.bfloat16, attn_implementation='eager').eval()
  with torch.inference_mode():
    logits = model(torch.tensor([ids]), use_cache=False).logits[0]
    references = {p:logits[p].float().numpy().copy() for p in positions}
  del model, logits
  gc.collect()
  result = {'device':args.device, 'projection_workers':llama3.LLAMA_CORES,
            'weight_bytes_per_token':WEIGHT_BYTES_PER_TOKEN,
            'source_sha256':hashlib.sha256(Path(llama3.__file__).read_bytes()).hexdigest(),
            'cpu_logit_checks':[], 'generation_benchmarks':[]}
  def save(): Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
  print('Loading card weights', flush=True)
  runtime = llama3.Llama3Decode('weights/llama3-8b-bf16', args.device)
  try:
    result['attention_workers'] = runtime.attention_cores
    result['available_workers'] = len(runtime.device.dram.cores)
    result['startup'] = runtime.profile
    result['dram_bytes_per_bank'] = runtime.device.dram.allocator.next
    runtime.load_tokens(ids)
    for position in range(512):
      token, _ = runtime.decode(position, append=False)
      if position not in references: continue
      compact = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
      actual = np.concatenate([row[:n] for row,n in zip(compact, runtime.lm_weight.item_counts)])
      reference = references[position]
      pcc = float(np.corrcoef(actual, reference)[0,1])
      record = {'position':position, 'pcc':pcc, 'rmse':float(np.sqrt(np.mean((actual-reference)**2))),
                'card_token':token, 'cpu_token':int(reference.argmax())}
      result['cpu_logit_checks'].append(record)
      print(json.dumps(record), flush=True)
      save()
      if not pcc > 0.99: raise RuntimeError(f'CPU logit correlation failed at {position}: {pcc}')
    for steps in (64,512):
      for prompt in DEFAULT_PROMPTS:
        prompt_ids = tokenizer.apply_chat_template([{'role':'user','content':prompt}],
                                                  add_generation_prompt=True, return_dict=False)
        runtime.load_tokens(prompt_ids)
        for position in range(len(prompt_ids)-1): runtime.decode(position, logits=False, append=False)
        samples, generated, hashes = [], [], {}
        for step in range(steps):
          position = len(prompt_ids)-1+step
          started = time.perf_counter_ns()
          token, _ = runtime.decode(position)
          samples.append((time.perf_counter_ns()-started)/1e3)
          generated.append(token)
          if step in (0,steps-1) or position % 32 in (0,31):
            hashes[str(position)] = hashlib.sha256(runtime.device.read(runtime.logits)).hexdigest()
        rate = 1e6/statistics.mean(samples)
        record = {'prompt':prompt, 'prompt_tokens':len(prompt_ids), 'steps':steps,
                  'tok_s':rate, 'median_us':statistics.median(samples), 'decode_us':samples,
                  'generated_tokens':generated, 'logit_sha256':hashes,
                  'text':tokenizer.decode(generated, skip_special_tokens=True),
                  'weight_bandwidth_GB_s':rate*WEIGHT_BYTES_PER_TOKEN/1e9}
        result['generation_benchmarks'].append(record)
        print(f'{steps} tokens, {rate:.3f} tok/s: {prompt}', flush=True)
        save()
  finally:
    runtime.close()
  for steps in (64,512):
    runs = [r for r in result['generation_benchmarks'] if r['steps']==steps]
    elapsed = sum(sum(r['decode_us']) for r in runs)
    result[f'aggregate_{steps}_tok_s'] = len(runs)*steps*1e6/elapsed
  save()


if __name__ == '__main__': main()
