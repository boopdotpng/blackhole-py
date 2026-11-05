"""Greedy chat generation from the command line: ``python -m examples.llama3 --help``."""

from pathlib import Path
import argparse
import time

import numpy as np

from examples.llama3.config import Llama3Config
from examples.llama3.runtime import Llama3Decode


def generate(cfg, prompt="The capital of France is", steps=None, *, safetensor_path=None,
             tokenizer_path=None, profile=False, device_index=0, attention_cores=None):
  """Stream a greedy chat reply. The prompt runs through decode one token at a time."""
  safetensor_path = cfg.checkpoint if safetensor_path is None else safetensor_path
  if tokenizer_path is None:
    checkpoint_path = Path(safetensor_path)
    tokenizer_path = checkpoint_path.parent if checkpoint_path.is_file() else checkpoint_path
  if steps is not None and steps < 1:
    raise ValueError("steps must be positive")
  from transformers import AutoTokenizer, TextStreamer

  tokenizer = AutoTokenizer.from_pretrained(str(Path(tokenizer_path)), local_files_only=True)
  if tokenizer.chat_template is None:
    raise ValueError("the Instruct tokenizer is missing its chat template")
  prompt_ids = tokenizer.apply_chat_template(
    ({"role": "user", "content": prompt},),
    tokenize=True, add_generation_prompt=True,
  )
  # Newer transformers return a BatchEncoding instead of a flat ID list.
  if not isinstance(prompt_ids, list):
    prompt_ids = prompt_ids["input_ids"]
    if prompt_ids and isinstance(prompt_ids[0], list): prompt_ids = prompt_ids[0]
  if not prompt_ids:
    raise ValueError("prompt tokenization produced no tokens")
  max_steps = cfg.max_tokens - len(prompt_ids)
  if max_steps < 1:
    raise ValueError("prompt leaves no room for decode generation")
  if steps is None:
    steps = max_steps
  elif steps > max_steps:
    raise ValueError("prompt plus generation exceeds the 8192-token cache")

  runtime = Llama3Decode(cfg, device_index, safetensor_path=safetensor_path, attention_cores=attention_cores)
  generation_seconds = 0.0
  generation_profiles = []
  generated = []
  stream_us = 0.0
  streamer = TextStreamer(
    tokenizer, skip_prompt=False, skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
  )

  def timed_decode(position, **options):
    nonlocal generation_seconds
    token_started = time.perf_counter_ns()
    read_before = runtime.host_result_read_us
    token, replay_wall_us = runtime.decode(position, **options)
    full_wall_us = (time.perf_counter_ns() - token_started) / 1e3
    generation_seconds += full_wall_us / 1e6
    generation_profiles.append({
      **runtime.decode_trace.last_profile,
      "replay_wall_us": replay_wall_us,
      "result_read_us": runtime.host_result_read_us - read_before,
      "full_wall_us": full_wall_us,
    })
    return token

  try:
    # Prompt: every token but the last only fills the KV cache.
    prompt_started = time.perf_counter()
    runtime.load_tokens(prompt_ids)
    for position in range(len(prompt_ids) - 1):
      runtime.decode(position, logits=False, append=False)
    next_token = timed_decode(len(prompt_ids) - 1, logits=True, append=True)
    prompt_seconds = time.perf_counter() - prompt_started

    # Generation: each decode consumes the previous greedy token.
    for step in range(steps):
      generated.append(next_token)
      stream_started = time.perf_counter_ns()
      streamer.put(np.asarray([next_token], dtype=np.int64))
      stream_us += (time.perf_counter_ns() - stream_started) / 1e3
      if next_token in cfg.eos_token_ids or step + 1 == steps: break
      next_token = timed_decode(len(prompt_ids) + step, logits=True)
    streamer.end()
  finally:
    runtime.close()

  if generation_profiles:
    print(f"{len(generation_profiles) / generation_seconds:.2f} decode tok/s")
  if profile:
    _print_profile(runtime.profile, prompt_seconds, len(prompt_ids), generation_profiles, stream_us / max(1, len(generated)))


def _print_profile(startup, prompt_seconds, prompt_tokens, samples, stream_us_per_token):
  ms = lambda seconds: f"{seconds * 1e3:9.2f} ms"
  print(f"startup total          {ms(startup['startup_total_s'])}")
  print(f"  device init          {ms(startup['device_init_s'])}")
  print(f"  weight prepare       {ms(startup['weight_prepare_s'])}")
  print(f"  host read/stage      {ms(startup['weight_stage_s'])}")
  upload_gb = startup["dram_upload_bytes"] / 1e9
  upload_s = startup["weight_upload_total_s"]
  print(f"  full weight upload   {ms(upload_s)}  "
        f"({upload_gb:.3f} GB, {upload_gb / upload_s:.2f} GB/s, includes prepare/stage)")
  print(f"  upload wait/submit   {startup['upload_wait_s'] * 1e3:9.2f} / "
        f"{startup['upload_submit_s'] * 1e3:.2f} ms (overlapped transfers)")
  print(f"  program build        {ms(startup['program_build_s'])}")
  print(f"prompt decode          {ms(prompt_seconds)}  ({prompt_tokens} tokens)")
  if not samples: return
  average = lambda *names: sum(sample[name] for sample in samples for name in names) / len(samples)
  device_us, full_wall_us = average("device_us"), average("full_wall_us")
  print(f"generated-token average ({len(samples)} replays)")
  print(f"  device/CQ interval   {device_us:9.2f} us")
  print(f"  host replay wall     {average('replay_wall_us'):9.2f} us")
  print(f"  token readback       {average('result_read_us'):9.2f} us")
  print(f"  full decode call     {full_wall_us:9.2f} us")
  print(f"  wall - device        {full_wall_us - device_us:9.2f} us")
  print(f"  runtime encode/patch {average('runtime_encode_us', 'runtime_patch_us'):9.2f} us")
  print(f"  CQ event/doorbell    {average('event_patch_us', 'queue_slot_wait_us', 'doorbell_us'):9.2f} us")
  print(f"  completion tail      {average('descriptor_drain_us'):9.2f} us")
  print(f"  text streaming       {stream_us_per_token:9.2f} us/token")


def main(argv=None):
  parser = argparse.ArgumentParser(description="Llama 3 batch-1 greedy decode on Blackhole.")
  parser.add_argument('--model', choices=('1b', '8b'), default='1b')
  parser.add_argument('--dtype', choices=('bf16', 'fp8'), default='bf16',
                      help='checkpoint weight format; FP8 supports 8B only')
  parser.add_argument('--lm-head-dtype', choices=('bf16', 'fp8'),
                      help='8B FP8 only: optionally quantize the LM head per row (may change greedy tokens)')
  parser.add_argument('--split-attention', action=argparse.BooleanOptionalAction, default=None,
                      help='8B BF16 attention: split long sequences across four workers per KV head')
  parser.add_argument('--prompt', default='The capital of France is',
                      help='generate from this prompt (an empty prompt is valid)')
  parser.add_argument('--steps', type=int, help='generation cap; default runs until EOS/context limit')
  parser.add_argument('--safetensor', help='checkpoint file/directory; defaults to weights/llama3-<model>[-<dtype>]')
  parser.add_argument('--tokenizer', help='tokenizer directory; defaults to the checkpoint path')
  parser.add_argument('--device', type=int, default=0, help='Tenstorrent device index (default: 0)')
  parser.add_argument('--attention-cores', type=int, choices=(8, 16, 32),
                      help='default: 16 for 1B, 32 for 8B')
  parser.add_argument('--profile', action='store_true', help='print startup, upload, device, and host timing')
  args = parser.parse_args(argv)
  try:
    cfg = Llama3Config.create(args.model, args.dtype, lm_head_dtype=args.lm_head_dtype,
                              split_attention=args.split_attention)
    if args.steps is not None and args.steps < 1:
      raise ValueError('steps must be positive')
  except ValueError as error:
    parser.error(str(error))
  generate(cfg, args.prompt, args.steps, safetensor_path=args.safetensor, tokenizer_path=args.tokenizer,
           profile=args.profile, device_index=args.device, attention_cores=args.attention_cores)
