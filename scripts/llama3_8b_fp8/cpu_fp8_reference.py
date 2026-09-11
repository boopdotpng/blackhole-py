"""CPU emulation of the downloaded static FP8 checkpoint; no accelerator access.

FP8 linear operands are decoded to FP32 only for CPU GEMM. Outputs, residuals,
attention, embeddings and the LM head use the checkpoint's BF16 contract.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding
from llama_checkpoint import validate_checkpoint

class FP8Linear(nn.Module):
  def __init__(self, weight, input_scale, weight_scale):
    super().__init__()
    self.register_buffer('weight', weight)
    self.input_scale, self.weight_scale = input_scale, weight_scale
  def forward(self, x):
    operand = (x.float()/self.input_scale).clamp(-448,448).to(torch.float8_e4m3fn).float()
    # Blackhole native operands flush subnormals; their contribution is tiny
    # with this checkpoint's calibrated scales.
    operand = torch.where(operand.abs()<2**-6, 0., operand)
    weight = self.weight.float()
    weight = torch.where(weight.abs()<2**-6, 0., weight)
    return (F.linear(operand,weight)*self.input_scale*self.weight_scale).to(x.dtype)


def main():
  parser=argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--weights',default='weights/llama3-8b-fp8')
  parser.add_argument('--output',default='validation/published-fp8-cpu-logits.npz')
  parser.add_argument('--threads',type=int,default=8)
  args=parser.parse_args()
  torch.set_num_threads(args.threads)
  checkpoint=validate_checkpoint(args.weights)
  config=AutoConfig.from_pretrained(args.weights,local_files_only=True)
  if hasattr(config,'quantization_config'): del config.quantization_config
  config._attn_implementation='eager'
  with torch.device('meta'):
    model=AutoModelForCausalLM.from_config(config,dtype=torch.bfloat16,attn_implementation='eager')
  scales={name:float(np.frombuffer(checkpoint.load(name)[1],dtype='<f4')[0]) for name in checkpoint.tensors if name.endswith(('.input_scale','.weight_scale'))}
  for name,info in checkpoint.tensors.items():
    if name in scales: continue
    data=bytearray(checkpoint.load(name)[1])
    dtype=torch.float8_e4m3fn if info.dtype=='F8_E4M3' else torch.bfloat16
    weight=torch.frombuffer(data,dtype=dtype).reshape(info.shape)
    module_name=name.removesuffix('.weight')
    if dtype is torch.float8_e4m3fn:
      parent,leaf=module_name.rsplit('.',1)
      setattr(model.get_submodule(parent),leaf,FP8Linear(weight,scales[module_name+'.input_scale'],scales[module_name+'.weight_scale']))
    else:
      model.get_submodule(module_name).weight=nn.Parameter(weight,requires_grad=False)
  model.model.rotary_emb=LlamaRotaryEmbedding(config,device='cpu')
  tokenizer=AutoTokenizer.from_pretrained('weights/llama3-8b-fp8',local_files_only=True)
  text='The sky appears blue because air molecules scatter short wavelengths of sunlight more strongly than long wavelengths. '
  ids=tokenizer.encode(text*50,add_special_tokens=True)[:256]
  positions=[0,1,7,15,31,32,63,64,127,128,255]
  print('Loaded CPU reference',flush=True)
  model.eval()
  with torch.inference_mode():
    output=model(torch.tensor([ids]),use_cache=False).logits[0].float()
  arrays={str(p):output[p].numpy().copy() for p in positions}
  np.savez(args.output,**arrays)
  baseline=np.load('validation/bf16-logits.npz')
  rows=[{'position':p,'token':int(arrays[str(p)].argmax()),'pcc_to_bf16':float(np.corrcoef(arrays[str(p)],baseline[str(p)])[0,1])} for p in positions]
  Path(args.output).with_suffix('.json').write_text(json.dumps(rows,indent=2)+'\n')
  print(json.dumps(rows,indent=2),flush=True)

if __name__=='__main__':main()
