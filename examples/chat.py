"""Chat in the terminal with any model in examples/, one model on the card at a time.
Each turn renders the whole conversation with the model's chat template and prefills it again (no KV reuse yet).
      python examples/chat.py --model llama3-1b
Commands: /model [name] lists or switches models (the old one is unloaded first), /clear starts over, /quit exits."""
import argparse, datetime, json, readline, sys, time  # noqa: F401  (readline gives input() line editing and history)
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ttrv import Device

WEIGHTS = ROOT / "weights"
DIM, RESET = "\033[2m", "\033[0m"

def _llama(name):
  def load(dev, ctx):
    from examples.llama3 import load
    return load(WEIGHTS / name, dev)
  return WEIGHTS / name, load, 8192  # the Llama kernels have a fixed 8192-token context

def _nanbeige(dev, ctx):
  from examples.nanbeige import Nanbeige, DEFAULT
  return Nanbeige(DEFAULT, dev, max_tokens=ctx)

def _qwen(dev, ctx):
  from examples.qwen38 import Qwen38, DEFAULT, METADATA
  return Qwen38(DEFAULT, METADATA, dev, ctx)

# name: (directory with tokenizer.json and tokenizer_config.json, loader(dev, ctx), default context)
MODELS = {
  "llama3-1b": _llama("llama3-1b"),
  "llama3-8b-bf16": _llama("llama3-8b-bf16"),
  "llama3-8b-bfp8": _llama("llama3-8b-bfp8"),
  "nanbeige4.3-33b": (WEIGHTS / "nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn", _nanbeige, 8192),
  "qwen3.8-27b": (Path.home() / "models/qwen3.8-27b/bf16", _qwen, 4096),
}

class Template:
  """The model's Hugging Face chat template, rendered the way transformers does."""
  def __init__(self, meta):
    import jinja2, jinja2.ext
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    cfg = json.loads((meta / "tokenizer_config.json").read_text())
    text = (meta / "chat_template.jinja").read_text() if (meta / "chat_template.jinja").exists() else cfg["chat_template"]
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=[jinja2.ext.loopcontrols])
    env.filters["tojson"] = lambda x, indent=None, **_: json.dumps(x, indent=indent, ensure_ascii=False)
    def raise_exception(msg): raise jinja2.exceptions.TemplateError(msg)
    env.globals.update(raise_exception=raise_exception, strftime_now=lambda f: datetime.datetime.now().strftime(f))
    self.template = env.from_string(text)
    token = lambda t: t["content"] if isinstance(t, dict) else (t or "")
    self.special = {"bos_token": token(cfg.get("bos_token")), "eos_token": token(cfg.get("eos_token"))}
  def __call__(self, messages, **kw): return self.template.render(messages=messages, add_generation_prompt=True, **self.special, **kw)

class Printer:
  """Prints a growing reply, the <think> block dimmed. Holds back a partial tag or a partial UTF-8 character."""
  def __init__(self, thinking): self.thinking, self.shown = thinking, 0
  def update(self, text, final=False):
    if not final: text = text.rstrip("�")
    while self.shown < len(text):
      tag = "</think>" if self.thinking else "<think>"
      end = text.find(tag, self.shown)
      stop = end if end >= 0 else len(text)
      if end < 0 and not final: stop -= max((i for i in range(1, len(tag)) if text.endswith(tag[:i])), default=0)
      if stop <= self.shown and end < 0: break
      chunk = text[self.shown:stop]
      if chunk: sys.stdout.write((DIM + chunk + RESET) if self.thinking else chunk)
      if end < 0: self.shown = stop
      else: self.shown, self.thinking = end + len(tag), not self.thinking
    sys.stdout.flush()

def answer(text):
  """The reply without its reasoning, as the conversation history keeps it."""
  return text.rsplit("</think>", 1)[-1].strip()

class Chat:
  def __init__(self, args):
    self.args, self.dev, self.model, self.name = args, None, None, None
    self.messages = [{"role": "system", "content": args.system}] if args.system else []

  def load(self, name):
    from tokenizers import Tokenizer
    meta, loader, ctx = MODELS[name]
    self.unload()
    print(f"{DIM}loading {name} on card {self.args.device}...{RESET}", flush=True)
    start = time.perf_counter()
    self.dev = Device(self.args.device)
    self.ctx = self.args.context or ctx
    self.model = loader(self.dev, self.ctx)
    self.tok, self.template, self.name = Tokenizer.from_file(str(meta / "tokenizer.json")), Template(meta), name
    print(f"{DIM}loaded {name} in {time.perf_counter() - start:.1f}s, {self.ctx} token context{RESET}")

  def unload(self):
    if self.dev is not None:
      self.model = None
      # closing with work in flight leaves the card unable to boot in the next process, until tt-smi -r
      try: self.dev.synchronize(timeout=60)
      finally: self.dev.close()
      self.dev = None

  def prompt(self):
    """Token ids for the conversation, dropping the oldest turns until a reply has room."""
    kw = {} if self.args.think else {"enable_thinking": False}
    while True:
      rendered = self.template(self.messages, **kw)
      ids = self.tok.encode(rendered, add_special_tokens=False).ids
      if len(ids) + 64 <= self.ctx: return ids, rendered
      first = 1 if self.messages and self.messages[0]["role"] == "system" else 0
      if len(self.messages) - first <= 1: raise ValueError(f"message is {len(ids)} tokens, the context is {self.ctx}")
      del self.messages[first:first + 2]

  def turn(self, text):
    self.messages.append({"role": "user", "content": text})
    try: ids, rendered = self.prompt()
    except ValueError as e:
      self.messages.pop()
      return print(f"error: {e}")
    printer = Printer(thinking=rendered.rstrip().endswith("<think>"))
    out, start = [], time.perf_counter()
    gen = self.model.generate(ids, min(self.args.max_tokens, self.ctx - len(ids) + 1))
    try:
      for token in gen:
        if not out: first = time.perf_counter()
        out.append(token)
        printer.update(self.tok.decode(out, skip_special_tokens=False))
    except KeyboardInterrupt:
      gen.close()
      print(f"{DIM} [stopped]{RESET}", end="")
    end = time.perf_counter()
    # Llama keeps a step in flight past EOS: let it land before the next prompt overwrites its history
    self.dev.synchronize(timeout=60)
    text = self.tok.decode(out, skip_special_tokens=False)
    printer.update(text, final=True)
    self.messages.append({"role": "assistant", "content": answer(text)})
    stats = f"{len(ids)} prompt tokens"
    if out: stats += f", first token in {first - start:.2f}s"
    if len(out) > 1: stats += f", {len(out)} tokens at {(len(out) - 1) / (end - first):.1f} tok/s"
    print(f"\n{DIM}[{stats}]{RESET}\n")

  def command(self, line):
    cmd, _, arg = line.partition(" ")
    if cmd == "/model":
      if not arg:
        for name, (meta, *_) in MODELS.items():
          print(f"{'*' if name == self.name else ' '} {name}{'' if meta.exists() else '  (missing)'}")
      elif arg not in MODELS: print(f"unknown model {arg}, one of: {', '.join(MODELS)}")
      else: self.load(arg)
    elif cmd == "/clear":
      self.messages = self.messages[:1] if self.messages and self.messages[0]["role"] == "system" else []
      print(f"{DIM}cleared{RESET}")
    elif cmd in ("/quit", "/exit"): raise EOFError
    else: print("commands: /model [name], /clear, /quit")

  def run(self):
    self.load(self.args.model)
    print(f"{DIM}/model [name] switches models, /clear starts over, Ctrl-C stops a reply, Ctrl-D quits{RESET}\n")
    while True:
      try: line = input(f"{self.name}> ").strip()
      except (EOFError, KeyboardInterrupt): return print()
      if not line: continue
      try:
        if line.startswith("/"): self.command(line)
        else: self.turn(line)
      except EOFError: return

if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--model", default="llama3-1b", choices=list(MODELS))
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--context", type=int, help="context length for Nanbeige and Qwen (Llama is fixed at 8192)")
  ap.add_argument("--max-tokens", type=int, default=1024, help="longest reply")
  ap.add_argument("--system", help="system prompt")
  ap.add_argument("--no-think", dest="think", action="store_false", help="ask templates that support it to skip reasoning")
  chat = Chat(ap.parse_args())
  try: chat.run()
  finally: chat.unload()
