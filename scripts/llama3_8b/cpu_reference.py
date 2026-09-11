"""Run a short Transformers reference on CPU; never opens a Blackhole card."""
import argparse
import json
from pathlib import Path
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from llama_checkpoint import validate_checkpoint

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--weights', default='weights/llama3-8b-bf16')
  parser.add_argument('--prompt', default='What is the capital of France? Answer in one short sentence.')
  parser.add_argument('--steps', type=int, default=12)
  parser.add_argument('--threads', type=int, default=8)
  parser.add_argument('--output', default='validation/cpu-reference.json')
  args = parser.parse_args()
  if args.steps < 1: parser.error('--steps must be positive')
  validate_checkpoint(args.weights)
  torch.set_num_threads(args.threads)
  tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)
  inputs = tokenizer.apply_chat_template([{'role': 'user', 'content': args.prompt}],
                                        add_generation_prompt=True, return_tensors='pt', return_dict=True)
  started = time.perf_counter()
  model = AutoModelForCausalLM.from_pretrained(args.weights, local_files_only=True,
                                              dtype=torch.bfloat16, attn_implementation='eager')
  model.eval()
  with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=args.steps, do_sample=False,
                            eos_token_id=[128001, 128009], pad_token_id=128255)
  count = inputs['input_ids'].shape[1]
  result = {'backend': 'Transformers CPU BF16 (not Blackhole validation)',
            'prompt': args.prompt, 'prompt_ids': inputs['input_ids'][0].tolist(),
            'generated_ids': output[0, count:].tolist(),
            'text': tokenizer.decode(output[0, count:], skip_special_tokens=True),
            'elapsed_s': time.perf_counter() - started, 'torch': torch.__version__}
  Path(args.output).parent.mkdir(parents=True, exist_ok=True)
  Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
  print(json.dumps(result, indent=2))
