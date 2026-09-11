"""Check downloaded tensors and lower the real runtime without device access."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ttko.device import Device
from examples.llama3_8b import Llama3Decode, LLAMA_CORES
from fw.consts import TensixL1
from llama_checkpoint import validate_checkpoint
from pcie import P100_DRAM_ENDPOINTS, P100_WORKER_CORES, P150_DRAM_ENDPOINTS
from ttko.program import Dram
from transformers import AutoTokenizer


def lower_runtime(endpoints, cores, attention_cores):
  device = Device.__new__(Device)
  device.dram = Dram(len(endpoints), cores, endpoints)
  device.pcie = SimpleNamespace(cores=cores)
  device.cq = SimpleNamespace(submit=lambda *a, **kw: None, noc=0, live=0)
  device.program_queue, device.read_queue = [], []
  device._resident_programs, device._param_templates = {}, {}
  device.capture_trace = lambda params: device._install_param_templates(tuple(device.program_queue), params)
  runtime = Llama3Decode.__new__(Llama3Decode)
  runtime.device, runtime.attention_cores = device, attention_cores
  runtime._allocate()
  runtime._build_programs()
  max_l1 = max(p._l1.next for p in runtime.programs.values())
  assert max_l1 <= TensixL1.DATA_BUFFER_SPACE_END
  assert device._param_template_next <= TensixL1.KERNEL_CACHE_END
  assert runtime.decode_launch_count == 163
  assert len(runtime.lm_weight.cores) == LLAMA_CORES
  assert runtime.lm_weight.addr != runtime.embedding_weight.addr
  return {'banks': len(endpoints), 'available_workers': len(cores), 'attention_workers': attention_cores,
          'decode_launches': runtime.decode_launch_count,
          'dram_bytes_per_bank': device.dram.allocator.next,
          'dram_total_reserved_bytes': device.dram.allocator.next * len(endpoints),
          'resident_kernel_and_template_end': device._param_template_next,
          'resident_arena_end': TensixL1.KERNEL_CACHE_END,
          'data_buffers_end': max_l1, 'data_arena_end': TensixL1.DATA_BUFFER_SPACE_END}


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--weights', default='weights/llama3-8b-bf16')
  parser.add_argument('--output', default='validation/preflight.json')
  parser.add_argument('--hash-weights', action='store_true')
  args = parser.parse_args()
  checkpoint = validate_checkpoint(args.weights)
  tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)
  prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': 'Hello!'}],
                                        tokenize=True, add_generation_prompt=True, return_dict=False)
  assert prompt[0] == 128000 and prompt[-1] == 271
  assert tokenizer.convert_tokens_to_ids('<|eot_id|>') == 128009
  result = {'hardware_accessed': False, 'tensor_count': len(checkpoint.tensors),
            'tensor_bytes': sum(t.nbytes for t in checkpoint.tensors.values()),
            'prompt_ids': prompt, 'topologies': []}
  with patch('pcie.PCIDevice.__init__', side_effect=AssertionError('preflight must never open a card')):
    for endpoints, cores in ((P100_DRAM_ENDPOINTS, P100_WORKER_CORES),
                             (P150_DRAM_ENDPOINTS, P100_WORKER_CORES),
                             (P150_DRAM_ENDPOINTS)):
      for workers in (8, 16, 32):
        record = lower_runtime(endpoints, cores, workers)
        result['topologies'].append(record)
        print(json.dumps(record), flush=True)
  if args.hash_weights:
    result['sha256'] = {}
    for path in sorted(Path(args.weights).glob('*.safetensors')):
      with path.open('rb') as stream:
        result['sha256'][path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
  Path(args.output).parent.mkdir(parents=True, exist_ok=True)
  Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
  print(f'PASS: {len(checkpoint.tensors)} BF16 tensors; all nine runtime configurations lower without a card.')
