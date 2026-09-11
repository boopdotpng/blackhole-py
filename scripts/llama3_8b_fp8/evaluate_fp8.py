"""Fixed-workload throughput and teacher-forced logit comparison on card 1."""
import argparse
import json
import os
from pathlib import Path
import statistics
import time
import numpy as np


def main():
  parser=argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--mode', choices=('bf16','fp8'), required=True)
  parser.add_argument('--weights', type=Path)
  parser.add_argument('--steps', type=int, nargs='+', default=[64,256])
  parser.add_argument('--output',type=Path,required=True)
  parser.add_argument('--logits-output',type=Path)
  parser.add_argument('--reference',type=Path,default=Path('validation/bf16-logits.npz'))
  args=parser.parse_args()
  os.environ['LLAMA_WEIGHT_DTYPE']='bf16' if args.mode=='bf16' else 'fp8'
  os.environ['LLAMA_ATTENTION_DTYPE']='fp8' if args.mode=='fp8-attention' else 'bf16'
  if args.mode == 'bf16':
    from examples.llama3_8b import Llama3Decode, LLAMA_CORES, PROJECTION_NOC_SPLIT_X
    from ttko import DType
    ATTENTION_DTYPE, FP8_FIDELITY = DType.BF16, None
  else:
    from examples.llama3_8b_fp8 import Llama3Decode, LLAMA_CORES, PROJECTION_NOC_SPLIT_X, FP8_FIDELITY, ATTENTION_DTYPE
  from examples.diagnostics.llama3_8b_fp8.benchmark_llama3 import DEFAULT_PROMPTS
  from transformers import AutoTokenizer
  tokenizer=AutoTokenizer.from_pretrained('weights/llama3-8b-fp8',local_files_only=True)
  text='The sky appears blue because air molecules scatter short wavelengths of sunlight more strongly than long wavelengths. '
  ids=tokenizer.encode(text*50,add_special_tokens=True)[:256]
  positions={0,1,7,15,31,32,63,64,127,128,255}
  weights = str(args.weights or ('weights/llama3-8b-bf16' if args.mode=='bf16' else 'weights/llama3-8b-fp8'))
  result={'checkpoint':weights, 'fidelity':os.environ.get('LLAMA_FP8_FIDELITY','1'), 'mode':args.mode,'device':1,'teacher_forced':[],'benchmarks':[]}
  measured={}
  result.update(projection_cores=LLAMA_CORES,noc_split_x=PROJECTION_NOC_SPLIT_X,attention_dtype=ATTENTION_DTYPE.name,reference=str(args.reference))
  refs={} if args.mode=='bf16' else dict(np.load(args.reference))
  def save(): args.output.write_text(json.dumps(result,indent=2)+'\n')
  print('Loading',args.mode,flush=True)
  runtime=Llama3Decode(weights,1)
  try:
    result['startup']=runtime.profile
    result['launches_per_token']=runtime.decode_launch_count
    result['dram_reserved_bytes']=runtime.device.dram.allocator.next*runtime.device.dram.banks
    runtime.load_tokens(ids)
    for position in range(len(ids)):
      token,elapsed=runtime.decode(position,append=False)
      if position not in positions: continue
      compact=runtime.logits.to_numpy(runtime.device.read(runtime.logits))
      logits=np.concatenate([row[:n] for row,n in zip(compact,runtime.lm_weight.item_counts)])
      measured[str(position)]=logits.copy()
      row={'position':position,'token':token,'decode_us':elapsed,'finite':bool(np.isfinite(logits).all())}
      if not row['finite']: raise RuntimeError('nonfinite logits')
      if args.mode=='bf16': refs[str(position)]=logits
      else:
        reference=refs[str(position)]
        row.update(pcc=float(np.corrcoef(logits,reference)[0,1]),rmse=float(np.sqrt(np.mean((logits-reference)**2))),reference_token=int(reference.argmax()))
      result['teacher_forced'].append(row); print(row,flush=True); save()
    if args.mode=='bf16': np.savez(args.reference,**refs)
    if args.logits_output: np.savez(args.logits_output,**measured)
    prompts=list(DEFAULT_PROMPTS)+['What is the capital of France? Answer in one short sentence.']
    for steps in args.steps:
      for prompt in prompts:
        prompt_ids=tokenizer.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,return_dict=False)
        runtime.load_tokens(prompt_ids)
        for position in range(len(prompt_ids)-1): runtime.decode(position,logits=False,append=False)
        samples,tokens=[],[]
        for step in range(steps):
          started=time.perf_counter_ns(); token,_=runtime.decode(len(prompt_ids)-1+step)
          samples.append((time.perf_counter_ns()-started)/1000);tokens.append(token)
        row={'prompt':prompt,'steps':steps,'tok_s':1e6/statistics.mean(samples),'median_us':statistics.median(samples),'decode_us':samples,'tokens':tokens,'text':tokenizer.decode(tokens,skip_special_tokens=True)}
        result['benchmarks'].append(row);print(f'{steps} steps {row["tok_s"]:.2f} tok/s: {prompt}\n{row["text"][:240]}',flush=True);save()
  finally: runtime.close()

if __name__=='__main__':main()
