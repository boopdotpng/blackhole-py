"""Card-0 verifier equality, rejected-cache recovery, and end-to-end speed."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from transformers import AutoTokenizer
from examples.llama3_speculative import SpeculativeDecode, generate

PROMPTS = [
  'Explain why the sky is blue.',
  'Write a Python function that returns the first n Fibonacci numbers, and explain it.',
  'Tell me a short story about a robot learning to paint.',
  'Print the phrase "The quick brown fox jumps over the lazy dog." twenty times, one per line. Do not add any introduction.',
  'Continue this sequence to 100, preserving the format: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,',
]


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--steps', type=int, default=128)
  parser.add_argument('--output', default='validation/card0-speculative.json')
  args = parser.parse_args()
  tokenizer = AutoTokenizer.from_pretrained('weights/llama3-8b-bf16', local_files_only=True)
  result = {'device':args.device, 'steps':args.steps, 'checks':[], 'benchmarks':[],
            'source_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                             ('examples/llama3_8b.py', 'examples/llama3_speculative.py', 'ttko/unpack.py', 'fw/consts.py')}}
  def save(): Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
  print('Loading card', args.device, flush=True)
  runtime = SpeculativeDecode('weights/llama3-8b-bf16', args.device)
  try:
    result['startup'] = runtime.profile
    result['verify_launch_count'] = runtime.verify_launch_count
    result['kernel_cache'] = runtime.verify_cache
    ids = tokenizer.encode('The sky appears blue because air molecules scatter short wavelengths of sunlight. '*80)[:514]
    selected = {0,1,30,31,32,33,62,63,64,65,126,127,128,129,254,255,256,257,510,511,512,513}
    expected, hashes = {}, {}
    runtime.load_tokens(ids)
    for pos in range(len(ids)):
      token, _ = runtime.decode(pos, append=False)
      expected[pos] = token
      if pos in selected: hashes[pos] = hashlib.sha256(runtime.device.read(runtime.logits)).hexdigest()
    times = []
    for pos in range(0, len(ids)-1, 2):
      start = time.perf_counter()
      tokens = runtime.verify(ids[:pos+1], ids[pos+1])
      times.append(time.perf_counter()-start)
      if tokens != (expected[pos],expected[pos+1]): raise RuntimeError(f'verifier mismatch at {pos}: {tokens}')
      for i in range(2):
        if pos+i not in selected: continue
        actual = hashlib.sha256(runtime.device.read(runtime.slots[i]['logits'])).hexdigest()
        record = {'position':pos+i, 'kind':'teacher_forced', 'token_equal':True, 'logits_exact':actual == hashes[pos+i]}
        result['checks'].append(record)
        print(record, flush=True)
        save()
        if not record['logits_exact']: raise RuntimeError(f'logits mismatch at {pos+i}')
    result['teacher_forced_tokens_checked'] = 2*len(times)
    result['verification_mean_ms'] = 1000*sum(times)/len(times)
    for pos in (30,31,32,62,63,64,126,127,128,254,255,256,510,511):
      # The teacher-forced sweep filled the true cache. Each iteration below
      # repairs its rejected position before the next iteration starts.
      wrong = (expected[pos]+1) % 128256
      first, _ = runtime.verify(ids[:pos+1], wrong)
      if first != expected[pos]: raise RuntimeError('draft leaked into earlier causal prediction')
      runtime.load_tokens(ids)
      token, _ = runtime.decode(pos+1, append=False)
      actual = hashlib.sha256(runtime.device.read(runtime.logits)).hexdigest()
      record = {'position':pos, 'kind':'rejected_cache_overwrite', 'token_equal':token == expected[pos+1],
                'logits_exact':actual == hashes[pos+1]}
      result['checks'].append(record)
      print(record, flush=True)
      save()
      if not record['token_equal'] or not record['logits_exact']: raise RuntimeError(str(record))
    save()
    for prompt in PROMPTS:
      prompt_ids = tokenizer.apply_chat_template([{'role':'user','content':prompt}], add_generation_prompt=True, return_dict=False)
      normal = generate(runtime,prompt_ids,args.steps,speculative=False,stop_eos=False)
      speculative = generate(runtime,prompt_ids,args.steps,stop_eos=False)
      row = {'prompt':prompt, 'prompt_ids':prompt_ids, 'baseline':normal, 'speculative':speculative,
             'exact_match':normal['tokens']==speculative['tokens'], 'speedup':normal['seconds']/speculative['seconds'],
             'text':tokenizer.decode(speculative['tokens'],skip_special_tokens=True)}
      result['benchmarks'].append(row)
      print(prompt, normal['tok_s'], speculative['tok_s'], row['speedup'], speculative['accepted'], '/', speculative['proposed'], flush=True)
      save()
      if not row['exact_match']: raise RuntimeError('generation mismatch')
  finally: runtime.close()


if __name__ == '__main__': main()
