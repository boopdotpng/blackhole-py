"""Checks a batched backend (examples/engine.py) on one card: greedy outputs of concurrent prompts against the
single-sequence decoder, a follow-up turn that reuses the first turn's slot state, and decode step time by batch size.

  python examples/batch_check.py --model nanbeige
"""
import argparse, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tokenizers import Tokenizer
from ttrv import Device
from examples.engine import Engine, Sequence


def first_diff(a, b):
  return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None if len(a) == len(b) else min(len(a), len(b)))


def nanbeige(dev, slots, context):
  from examples.nanbeige import DEFAULT, Nanbeige
  from examples.nanbeige_batch import NanbeigeBatch, chat_prompt
  backend = NanbeigeBatch(DEFAULT, dev, slots=slots, context=context)
  tok = Tokenizer.from_file(str(DEFAULT.parent / "tokenizer.json"))
  def reference():
    with dev.phase("single"): model = Nanbeige(DEFAULT, dev, max_tokens=context, loaded=backend.loaded)
    def generate(ids, n):
      with dev.phase("single"): return list(model.generate(ids, n))
    return generate
  turn = lambda text, role: f"<|im_start|>{role}\n{text}<|im_end|>\n"
  return backend, tok, chat_prompt, reference, turn


def qwen(dev, slots, context):
  from examples.qwen38 import METADATA
  from examples.qwen38_batch import QwenBatch, chat_prompt
  backend = QwenBatch(dev, slots=slots, context=context)
  tok = Tokenizer.from_file(str(METADATA / "tokenizer.json"))
  def reference():  # the single-sequence model the backend stages prompts through
    def generate(ids, n): return list(backend.model.generate(ids, n))
    return generate
  turn = lambda text, role: f"<|im_start|>{role}\n{text}<|im_end|>\n"
  return backend, tok, chat_prompt, reference, turn


def inkling(dev, slots, context):
  from examples.inkling import DEFAULT, Inkling
  from examples.inkling_batch import InklingBatch, chat_prompt
  with dev.phase("inkling-single"): model = Inkling(dev, max_tokens=context, bfp4=True)
  backend = InklingBatch(dev, slots=slots, context=context, model=model)
  tok = Tokenizer.from_file(str(DEFAULT / "tokenizer.json"))
  def reference():  # the single-sequence decoder whose weights the backend shares
    def generate(ids, n):
      with dev.phase("inkling-single"): return list(model.generate(ids, n))
    return generate
  turn = lambda text, role: f"<|message_{'model' if role == 'assistant' else role}|><|content_text|>{text}<|end_message|>"
  return backend, tok, chat_prompt, reference, turn


MODELS = {"nanbeige": nanbeige, "qwen": qwen, "inkling": inkling}

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="nanbeige", choices=MODELS)
  ap.add_argument("--tokens", type=int, default=32)
  ap.add_argument("--slots", type=int, default=8)
  ap.add_argument("--context", type=int, default=2048)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--skip-reference", action="store_true")
  a = ap.parse_args()
  dev = Device(a.device)
  try:
    backend, tok, chat, reference, turn = MODELS[a.model](dev, a.slots, a.context)
    engine = Engine(backend)
    enc = lambda s: tok.encode(s, add_special_tokens=False).ids
    questions = ["Explain what a hash map is.", "Write a haiku about rain.", "List three prime numbers.",
                 "What is the capital of Australia, and why is it not Sydney?"]
    prompts = [enc(chat(q)) for q in questions]
    # 1. greedy, all prompts together
    seqs = [Sequence(p, a.tokens) for p in prompts]
    engine.run(seqs)
    generate = None if a.skip_reference else reference()
    failures = 0
    for i, (p, s) in enumerate(zip(prompts, seqs)):
      if generate is None:
        print(f"batch {i}: {tok.decode(s.out)[:70]!r}")
        continue
      ref = generate(p, a.tokens)[:len(s.out)]
      diff = first_diff(ref, s.out)
      print(f"greedy {i}: first difference at {diff} of {len(s.out)}  {tok.decode(s.out)[:60]!r}")
      if diff is not None:
        print(f"  reference: {tok.decode(ref)[:60]!r}")
        # margin of the batch's choice over the reference's token at the first difference
        ids = list(p) + s.out[:diff]
        probe = Sequence(ids, 1, on_token=None)
        logits = []
        backend_decode = backend.decode
        def capture(rows): out = backend_decode(rows); logits.append(out); return out
        backend.decode = capture
        engine.run([probe])
        backend.decode = backend_decode
        x = logits[-1][0]
        gap = x[s.out[diff]] - x[ref[diff]]
        failures += gap > 0.5  # wider than a bf16 rounding tie
        print(f"  logits at difference: batch token {x[s.out[diff]]:.3f}, reference token {x[ref[diff]]:.3f}"
              f" ({'tie' if gap <= 0.5 else 'MISMATCH'})")
    # 2. a second turn continues the first turn's slot (the prompt extends its cached tokens)
    first = seqs[0]
    follow = prompts[0] + first.out + enc("<|im_end|>\n" + turn("Now give an example in Python.", "user")[len(""):] +
                                          "<|im_start|>assistant\n<think>\n\n</think>\n\n")
    second = Sequence(follow, a.tokens)
    engine.run([second])
    print(f"follow-up: {second.cached} of {len(follow) - 1} prompt positions reused  {tok.decode(second.out)[:60]!r}")
    if generate is not None:
      ref = generate(follow, a.tokens)[:len(second.out)]
      diff = first_diff(ref, second.out)
      failures += diff is not None
      print(f"follow-up greedy: first difference at {diff} of {len(second.out)}")
    # 3. decode step time by live rows
    for n in (1, 4, 8, 16, 32, 64):
      if n > backend.slots: break
      rows = [(s, 100, 1000 + s) for s in range(n)]
      backend.decode(rows)
      t0 = time.perf_counter()
      for _ in range(5): backend.decode(rows)
      dt = (time.perf_counter() - t0) / 5
      print(f"{n:3d} rows: {dt * 1e3:7.1f} ms/step  {n / dt:7.1f} tok/s")
    print("FAIL" if failures else "ok")
  finally:
    dev.close()
