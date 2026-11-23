"""Checks the prefix store (examples/kvstore.py): a conversation evicted from its slot by other requests continues from
its state restored out of host RAM, then out of SSD, and decodes the same greedy tokens as with the store off.

  python examples/offload_check.py --model nanbeige
"""
import argparse, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ttrv import Device
from examples.engine import Engine, Sequence
from examples.kvstore import PrefixStore
from examples.batch_check import MODELS, first_diff

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="nanbeige", choices=MODELS)
ap.add_argument("--tokens", type=int, default=24)
ap.add_argument("--device", type=int, default=0)
a = ap.parse_args()
dev = Device(a.device)
try:
  backend, tok, chat, _, turn = MODELS[a.model](dev, 2, 2048)
  enc = lambda s: tok.encode(s, add_special_tokens=False).ids
  first = enc(chat("Describe, in detail, how a refrigerator moves heat out of its interior."))
  others = [enc(chat(q)) for q in ("Name a famous bridge.", "What is 17 times 3?")]
  def conversation(store):
    engine = Engine(backend, store)
    for s in range(backend.slots): engine.held[s] = engine.held[s][:0]   # cold slots
    one = Sequence(first, a.tokens)
    engine.run([one])
    engine.run([Sequence(p, 4) for p in others])   # both slots go to other prompts: the conversation is evicted
    follow = first + one.out + enc("<|im_end|>\n" + turn("Summarize that in one sentence.", "user") +
                                   "<|im_start|>assistant\n<think>\n\n</think>\n\n")
    two = Sequence(follow, a.tokens)
    t0 = time.perf_counter()
    engine.run([two])
    return one.out, two, time.perf_counter() - t0, engine
  base_one, base_two, base_t, _ = conversation(None)
  def show(two):
    print(f"  baseline follow-up {tok.decode(base_two.out[:12])!r}\n  this follow-up     {tok.decode(two.out[:12])!r}")
  def margin(follow, x, y):
    """Logits of tokens x and y after the follow-up prompt, prefilled from scratch."""
    engine = Engine(backend)
    for s in range(backend.slots): engine.held[s] = engine.held[s][:0]
    seen = []
    decode = backend.decode
    backend.decode = lambda rows: seen.append(decode(rows)) or seen[-1]
    try: engine.run([Sequence(follow, 1)])
    finally: backend.decode = decode
    return seen[0][0][x], seen[0][0][y]
  print(f"no store: follow-up reused {base_two.cached} positions, {base_t:.2f}s")
  failures = 0
  with tempfile.TemporaryDirectory() as tmp:
    for name, store in (("ram", PrefixStore(8 << 30, 0, None, min_tokens=16)),
                        ("ssd", PrefixStore(0, 8 << 30, tmp, min_tokens=16))):
      one, two, t, engine = conversation(store)
      if store.spilling: store.spilling.join()
      diff = first_diff(base_one + base_two.out, one + two.out)
      if diff is not None:
        show(two)
        k = diff - len(one)
        bx, tx = margin(two.ids, base_two.out[k], two.out[k])
        print(f"  from scratch: baseline token {bx:.3f}, this token {tx:.3f}")
        failures += abs(bx - tx) > 0.5
      print(f"{name}: follow-up reused {two.cached} of {len(two.ids) - 1} positions in {t:.2f}s "
            f"(restore {engine.times['restore']:.3f}s, save {engine.times['save']:.3f}s); "
            f"greedy difference at {diff}; {store.summary()}")
    # 3. restart: a new store over the same directory finds the first run's entries (a new opencode session
    # sharing the system prompt): turn one is flushed at shutdown, the follow-up starts on cold slots.
    with tempfile.TemporaryDirectory() as tmp2:
      store = PrefixStore(1 << 30, 8 << 30, tmp2, min_tokens=16)
      engine = Engine(backend, store)
      for s in range(backend.slots): engine.held[s] = engine.held[s][:0]
      one = Sequence(first, a.tokens)
      engine.run([one])
      engine.flush()
      store = PrefixStore(1 << 30, 8 << 30, tmp2, min_tokens=16)
      engine = Engine(backend, store)
      for s in range(backend.slots): engine.held[s] = engine.held[s][:0]
      follow = first + one.out + enc("<|im_end|>\n" + turn("Summarize that in one sentence.", "user") +
                                     "<|im_start|>assistant\n<think>\n\n</think>\n\n")
      two = Sequence(follow, a.tokens)
      engine.run([two])
      diff = first_diff(base_one + base_two.out, one.out + two.out)
      failures += diff is not None or two.cached == 0
      print(f"restart: follow-up reused {two.cached} positions from a previous run's SSD entry; greedy difference "
            f"at {diff}; {store.summary()}")
  print("FAIL" if failures else "ok")
finally:
  dev.close()
