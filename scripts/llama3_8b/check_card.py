"""Teacher-forced CPU comparison and card kernel attribution in one session."""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from examples.diagnostics.llama3_8b.profile_llama3 import ProfileRuntime, profile

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=int, default=1)
parser.add_argument('--output', default='validation/card1-initial-check.json')
args = parser.parse_args()
torch.set_num_threads(8)
record = json.loads(Path('validation/cpu-reference.json').read_text())
ids = record['prompt_ids'] + record['generated_ids']
print('Loading CPU model', flush=True)
model = AutoModelForCausalLM.from_pretrained('weights/llama3-8b-bf16', local_files_only=True, dtype=torch.bfloat16, attn_implementation='eager').eval()
with torch.inference_mode():
  cpu_logits = model(torch.tensor([ids])).logits[0].float().numpy()
del model
print('Loading card', flush=True)
runtime = ProfileRuntime('weights/llama3-8b-bf16', args.device)
print(f'Card has {len(runtime.device.pcie.cores)} worker cores, {runtime.device.dram.banks} DRAM banks', flush=True)
results = []
try:
  runtime.load_tokens(ids)
  for position in range(len(ids) - 1):
    token, elapsed = runtime.decode(position, append=False)
    if position < len(record['prompt_ids']) - 1: continue
    packed = runtime.logits.to_numpy(runtime.device.read(runtime.logits))
    logits = np.concatenate([row[:count] for row, count in zip(packed, runtime.lm_weight.item_counts)])
    ref = cpu_logits[position]
    top = lambda x: np.argsort(x)[-5:][::-1].tolist()
    result = {'position':position, 'card_token':token, 'cpu_token':int(ref.argmax()),
              'card_top5': top(logits), 'cpu_top5':top(ref),
              'pcc':float(np.corrcoef(logits,ref)[0,1]), 'rmse':float(np.sqrt(np.mean((logits-ref)**2))),
              'max_error':float(np.max(np.abs(logits-ref))), 'decode_us':elapsed}
    results.append(result); print(json.dumps(result), flush=True)
  Path(args.output).write_text(json.dumps(results, indent=2)+'\n')
  # Reuse the loaded runtime in the existing profiler, avoiding another upload.
  import examples.diagnostics.llama3_8b.profile_llama3 as profiling
  profiling.ProfileRuntime = lambda *a, **kw: runtime
  output = profile(argparse.Namespace(safetensor='weights/llama3-8b-bf16', device=args.device, attention_cores=32, contexts=[32,128]))
  Path('validation/card1-initial-profile.json').write_text(json.dumps(output, indent=2)+'\n')
finally:
  runtime.close()
