"""Exact greedy prompt-lookup speculation with a weight-sharing Blackhole verifier."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import time

from examples import llama3_8b as base
from ttko.program import Const, DType, Program
from ttko.cb import CB
from ttko.shard import specialize
from ttko.sync import Sem, SemWait, Stall, sem_wait


def _projection(xs, weight, outputs, count, rotation, noc):
  """Read each weight row once; retain it until both dot products finish."""
  if any(x.tilized != weight.tilized for x in xs):
    raise ValueError("projection weights and activations must have the same element order")
  tiles = xs[0].shape[1] // 1024
  tokens = tuple(replace(x, name=x.name + '_token', shape=(x.shape[1],), axis=None) for x in xs)
  start = Const('row_start', weight.item_starts)
  p = Program(weight.cores, *tokens, weight, start, *outputs, fp32_dst=True)
  weights = p.cb(DType.BF16, depth=2 * tiles)
  scalar = p.cb(DType.BF16, depth=2)
  inputs = tuple(p.l1(tiles * 2048, alignment=16) for _ in xs)
  results = tuple(p.l1(output.tiles_per_item * 2048, alignment=16) for output in outputs)
  for token, address in zip(tokens, inputs):
    p.brisc.noc_at(noc).read_tiles(token, tuple((i, address + i * 2048) for i in range(tiles)))
  base._projection_read_weights(p, ((weight, outputs[0], count),), (start,),
                                (rotation,), noc, weights, tiles)
  p.unpack.prepare_l1_pair_formats(DType.BF16)
  for _ in p.trisc0.range(count):
    # A row divides the ring depth, so the retained row never wraps inside it.
    CB.wait_front(p.trisc0, weights, tiles)
    for address in inputs:
      for i in range(tiles):
        p.unpack.move_l1_pair(weights, address + i * 2048, configure_format=False,
                              tile_offset=i, pop=False)
    CB.pop_front(p.trisc0, weights, tiles)
  base._projection_dot_math(p, ((weight, outputs[0], count * len(xs)),), tiles)
  p.pack._configure(scalar, True, True)
  for _ in p.trisc2.range(count * len(xs)):
    sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
    p.pack._move_acquired(scalar, 0, True, configure=False)
    p.pack._release_dst()
  for output, address in zip(outputs, results):
    base._zero_l1_words(p.ncrisc, address, output.tiles_per_item * 512)
  for row in p.ncrisc.range(count):
    for address in results:
      CB.wait_front(p.ncrisc, scalar)
      with p.ncrisc.scope():
        source, value, offset, target = p.ncrisc.reg(4, exclude=row)
        CB.get_read_ptr(p.ncrisc, scalar, source)
        p.ncrisc.read(value, source, bytes=2)
        base._tile_offset(p.ncrisc, row, offset)
        p.ncrisc.li(target, address)
        p.ncrisc.add(target, target, offset)
        p.ncrisc.write(target, value, bytes=2)
      CB.pop_front(p.ncrisc, scalar)
  for output, address in zip(outputs, results):
    for i in range(output.tiles_per_item):
      with p.ncrisc.scope():
        target, coordinate = p.ncrisc.noc_at(1-noc)._dram_tile(output, i)
        p.ncrisc.noc_at(1-noc).write(address + i * 2048, target, coordinate, 2048, posted=False)
  return p


def projection(xs, weight, outputs):
  keys = tuple((count, (start * weight.tiles_per_item) % weight.banks if weight.banks == 8 else None,
                int(core[0] >= base.PROJECTION_NOC_SPLIT_X))
               for count, start, core in zip(weight.item_counts, weight.item_starts, weight.cores))
  return specialize(lambda key: _projection(xs, weight, outputs, *key), weight.cores, keys)


def _rename_constants(program, names):
  # Kernels address slots, so renaming their host lookup keys needs no re-lowering.
  program.params = {names.get(name, name): replace(param, name=names[name]) if name in names else param
                    for name, param in program.params.items()}
  program._param_slots = {program.params[names.get(param.name, param.name)]: slot
                          for param, slot in program._param_slots.items()}
  return program


class SpeculativeDecode(base.Llama3Decode):
  """Two consecutive positions share projection reads; each has causal attention."""
  def _build_programs(self):
    device = self.device
    self._create_programs()
    names = ('x_a', 'x_b', 'normalized', 'q_compact', 'k_compact', 'v_compact',
             'context', 'gate', 'up', 'hidden', 'hidden_dense', 'logits')
    self.slots = [{name: getattr(self, name) for name in names}]
    second = {}
    for name in names:
      b = getattr(self, name)
      second[name] = device.dram.buffer(b.name + '_verify1', b.dtype, b.shape, axis=b.axis,
                                      cores=b.cores, global_address=b.global_address, tilized=b.tilized)
    self.slots.append(second)
    w = self.layers[0]['weights']
    self.verify_programs = {}
    def add(name, p):
      self.verify_programs[name] = p
      return p
    for i, s in enumerate(self.slots):
      rename = {'token_pos':f'position_{i}', 'start_pos':f'position_{i}',
                'kv_blocks':f'blocks_{i}', 'valid_columns':f'tail_{i}'}
      add(f'embedding{i}', _rename_constants(base.decode_embedding(self.token_history, self.embedding_weight, s['x_a']), rename))
      add(f'norm{i}', base.rmsnorm(s['x_a'], w['input_norm'], s['normalized']))
      add(f'attention{i}', _rename_constants(base.gqa_attention_fused(
        self.q_heads, self.layers[0]['key_cache'], self.layers[0]['value_cache'], s['context'],
        rope_inputs=(s['q_compact'], s['k_compact'], s['v_compact'], self.cos, self.sin),
        attention_cores=self.attention_cores), rename))
      add(f'residual{i}', base.decode_projection_residual(s['q_compact'], s['x_a'], s['x_b']))
      add(f'swiglu{i}', base.decode_swiglu(s['gate'], s['up'], s['hidden']))
      add(f'dense{i}', base.decode_compact_to_dense(s['hidden'], s['hidden_dense']))
      add(f'argmax{i}', base.decode_argmax(s['logits'], self.token_history, device.cq.noc + device.cq.live))
    for name, src, dst, weight in (
      ('q','normalized','q_compact',w['q']), ('k','normalized','k_compact',w['k']),
      ('v','normalized','v_compact',w['v']), ('o','context','q_compact',w['o']),
      ('gate','normalized','gate',w['gate']), ('up','normalized','up',w['up']),
      ('down','hidden_dense','q_compact',w['down']), ('lm','normalized','logits',self.lm_weight)):
      add(name, projection(tuple(s[src] for s in self.slots), weight, tuple(s[dst] for s in self.slots)))
    self.verify_cache = device.cache_kernels((*self.programs.values(), *self.verify_programs.values()))
    self._capture_decode_trace()
    def queue(name, params=None): device.queue(self.verify_programs[name], params=params)
    for i in range(2): queue(f'embedding{i}')
    for layer in self.layers:
      actual = layer['weights']
      for i in range(2): queue(f'norm{i}', {w['input_norm']:actual['input_norm']})
      for name in ('q','k','v'): queue(name, {w[name]:actual[name]})
      for i in range(2):
        queue(f'attention{i}', {self.layers[0]['key_cache']:layer['key_cache'],
                                self.layers[0]['value_cache']:layer['value_cache']})
      queue('o', {w['o']:actual['o']})
      for i, s in enumerate(self.slots):
        queue(f'residual{i}')
        queue(f'norm{i}', {s['x_a']:s['x_b'], w['input_norm']:actual['post_norm']})
      for name in ('gate','up'): queue(name, {w[name]:actual[name]})
      for i in range(2):
        queue(f'swiglu{i}')
        queue(f'dense{i}')
      queue('down', {w['down']:actual['down']})
      for i, s in enumerate(self.slots): queue(f'residual{i}', {s['x_a']:s['x_b'], s['x_b']:s['x_a']})
    for i in range(2): queue(f'norm{i}', {w['input_norm']:self.final_norm})
    queue('lm')
    for i in range(2): queue(f'argmax{i}', {'write_pos':i + 1, 'write_token':0})
    self.verify_launch_count = len(device.program_queue)
    self.verify_trace = device.capture_trace(tuple(f'{name}_{i}' for i in range(2) for name in ('position', 'blocks', 'tail')))

  def verify(self, history, draft):
    """Consume last committed token plus draft; return both greedy predictions.

    The cache before the final history token must already contain that prefix.
    Entries after the accepted prefix are logically invalid. The next call
    overwrites them, and each attention launch masks all later positions.
    """
    if not history or len(history) + 1 >= base.ROPE_CACHE_TOKENS:
      raise ValueError('verification needs two available input positions')
    self.load_tokens([*history, draft])
    return self._verify_positions(len(history) - 1)

  def _verify_positions(self, position):
    params = {f'{name}_{i}':value for i in range(2) for name, value in
              (('position', position+i), ('blocks', (position+i)//32+1), ('tail',(position+i)%32+1))}
    self.verify_trace.replay(params)
    return tuple(struct.unpack('<I', self.device.pcie.sysmem.read(self.device.cq.live+(i+1)*16, 4))[0]
                 for i in range(2))

  def prefill(self, tokens):
    """Populate the prompt cache in pairs, leaving its last token for decode."""
    self.load_tokens(tokens)
    position = 0
    while position + 1 < len(tokens) - 1:
      self._verify_positions(position)
      position += 2
    if position < len(tokens) - 1:
      self.decode(position, logits=False, append=False)


def lookup(history, max_ngram=4, min_ngram=3):
  """Propose the continuation of the longest, most recent matching suffix."""
  if not 1 <= min_ngram <= max_ngram:
    raise ValueError('ngram bounds must satisfy 1 <= min <= max')
  for n in range(min(max_ngram, len(history)-1), min_ngram-1, -1):
    suffix = history[-n:]
    for j in range(len(history)-n-1, -1, -1):
      if history[j:j+n] == suffix: return history[j+n]
  return None


def generate(runtime, prompt_ids, steps, *, speculative=True, stop_eos=True, min_ngram=3):
  if not prompt_ids or steps < 1 or len(prompt_ids)+steps > base.ROPE_CACHE_TOKENS:
    raise ValueError('prompt and positive generation length must fit the cache')
  if not 1 <= min_ngram <= 4: raise ValueError('min_ngram must be in 1..4')
  history = list(prompt_ids)
  prefill_started = time.perf_counter()
  if speculative:
    runtime.prefill(history)
  else:
    runtime.load_tokens(history)
    for pos in range(len(history)-1): runtime.decode(pos, logits=False, append=False)
  prefill_seconds = time.perf_counter() - prefill_started
  generated, proposed, accepted, rounds = [], 0, 0, 0
  dirty = False
  started = time.perf_counter()
  while len(generated) < steps:
    draft = lookup(history, min_ngram=min_ngram) if speculative and steps-len(generated) >= 2 else None
    if draft is None:
      # A previous verifier did not append its corrected/bonus token on device.
      if dirty: runtime.load_tokens(history)
      token, _ = runtime.decode(len(history)-1)
      tokens = [token]
      dirty = False
    else:
      first, bonus = runtime.verify(history, draft)
      proposed += 1
      accepted += int(first == draft)
      tokens = [first, bonus] if first == draft else [first]
      dirty = True
    rounds += 1
    for token in tokens:
      history.append(token)
      generated.append(token)
      if stop_eos and token in base.EOS_TOKEN_IDS: break
    if stop_eos and generated[-1] in base.EOS_TOKEN_IDS: break
  seconds = time.perf_counter()-started
  return {'tokens':generated, 'seconds':seconds, 'tok_s':len(generated)/seconds,
          'proposed':proposed, 'accepted':accepted, 'rounds':rounds,
          'prefill_seconds':prefill_seconds, 'min_ngram':min_ngram}


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--weights', default='weights/llama3-8b-bf16')
  parser.add_argument('--prompt', default='Explain why the sky is blue.')
  parser.add_argument('--steps', type=int, default=128)
  parser.add_argument('--min-ngram', type=int, choices=(1,2,3,4), default=3,
                      help='minimum matched suffix; 3 avoids weak single-token proposals')
  parser.add_argument('--benchmark', action='store_true', help='compare fixed-length greedy and speculative runs')
  parser.add_argument('--output')
  args = parser.parse_args()
  from transformers import AutoTokenizer
  tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)
  ids = tokenizer.apply_chat_template([{'role':'user','content':args.prompt}], add_generation_prompt=True, return_dict=False)
  print('Loading 8B weights and compiling verifier on card', args.device, flush=True)
  runtime = SpeculativeDecode(args.weights, args.device)
  try:
    result = {'device':args.device, 'prompt':args.prompt, 'prompt_ids':ids}
    if args.benchmark:
      result['baseline'] = generate(runtime, ids, args.steps, speculative=False, stop_eos=False)
      print('Baseline:', result['baseline']['tok_s'], 'tok/s', flush=True)
    result['speculative'] = generate(runtime, ids, args.steps, stop_eos=not args.benchmark, min_ngram=args.min_ngram)
    result['text'] = tokenizer.decode(result['speculative']['tokens'], skip_special_tokens=True)
    if args.benchmark:
      result['exact_match'] = result['baseline']['tokens'] == result['speculative']['tokens']
      result['speedup'] = result['speculative']['tok_s']/result['baseline']['tok_s']
    if args.output: Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    if args.benchmark and not result['exact_match']: raise RuntimeError('greedy token mismatch')
  finally: runtime.close()


if __name__ == '__main__': main()
