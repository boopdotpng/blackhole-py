"""OpenAI-compatible HTTP server over the batched engine (examples/engine.py): concurrent requests decode together, one
per state slot, new prompts prefill in chunks between decode steps, and a request whose prompt continues a slot's
cached tokens starts from them.

  python examples/serve.py --model nanbeige --slots 8 --context 16384 --port 8000

  curl localhost:8000/v1/chat/completions -H 'content-type: application/json' \\
    -d '{"messages": [{"role": "user", "content": "Hi"}], "stream": true}'

Endpoints: GET /v1/models, POST /v1/chat/completions (streaming or not; tools; reasoning returned as
`reasoning_content`), POST /v1/completions (raw prompt), GET /health. Chat prompts use the checkpoint's own chat template
(tokenizer_config.json). Nanbeige's XML tool calls (<tool_call><function=name><parameter=p>v</parameter>...) come back
as OpenAI `tool_calls`. Sampling: temperature, top_p, top_k, min_p, seed, max_tokens, stop. Defaults follow the
model card (Nanbeige: temperature 1.0 / top_p 0.95 with tools, 0.6 / 0.95 without)."""
import argparse, json, queue, re, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jinja2
from tokenizers import Tokenizer
from examples.engine import Engine, Sequence

THINK_OPEN, THINK_CLOSE, CALL_OPEN, CALL_CLOSE = "<think>", "</think>", "<tool_call>", "</tool_call>"


class Template:
  def __init__(self, folder):
    cfg = json.loads((folder / "tokenizer_config.json").read_text())
    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
    env.filters["tojson"] = lambda x, ensure_ascii=False, indent=None, separators=None, sort_keys=False: \
      json.dumps(x, ensure_ascii=ensure_ascii, indent=indent, separators=separators, sort_keys=sort_keys)
    def fail(message): raise ValueError(message)
    env.globals["raise_exception"] = fail
    self.template = env.from_string(cfg["chat_template"])
    self.special = {k: v if isinstance(v, str) else v.get("content", "") for k, v in cfg.items()
                    if k.endswith("_token") and isinstance(v, (str, dict))}

  def render(self, messages, tools=None, **kwargs):
    return self.template.render(messages=messages, tools=tools or None, add_generation_prompt=True, **self.special,
                                **kwargs)


class Detokenizer:
  """Incremental decoding that never splits a multi-byte character: decode a window that starts a few tokens back."""
  def __init__(self, tok): self.tok, self.ids, self.prefix, self.read = tok, [], 0, 0
  def add(self, token):
    self.ids.append(token)
    before = self.tok.decode(self.ids[self.prefix:self.read], skip_special_tokens=False)
    after = self.tok.decode(self.ids[self.prefix:], skip_special_tokens=False)
    if after.endswith("\ufffd"): return ""  # the token ends inside a character; wait for the rest
    self.read = len(self.ids)
    self.prefix = max(0, self.read - 6)
    return after[len(before):]


def held(text, marks):
  """How many characters at the end of text may be the start of one of marks."""
  return max((k for m in marks for k in range(1, len(m)) if text.endswith(m[:k])), default=0)


def parse_call(body, tools):
  """<function=name>\\n<parameter=p>\\nvalue\\n</parameter>...</function> -> (name, arguments JSON). Values keep their
  text unless the tool's schema types the parameter as non-string, then they are parsed as JSON when possible."""
  m = re.search(r"<function=([^>\n]+)>(.*?)(?:</function>|$)", body, re.S)
  if not m:  # JSON format: {"name": ..., "arguments": {...}}
    try: obj = json.loads(body)
    except json.JSONDecodeError: return None
    return obj.get("name", ""), json.dumps(obj.get("arguments", {}), ensure_ascii=False)
  name, inner = m.group(1).strip(), m.group(2)
  schema = next((t.get("function", t).get("parameters", {}) for t in tools or ()
                 if t.get("function", t).get("name") == name), {})
  props = schema.get("properties", {}) if isinstance(schema, dict) else {}
  args = {}
  for p in re.finditer(r"<parameter=([^>\n]+)>\n?(.*?)\n?</parameter>", inner, re.S):
    key, value = p.group(1).strip(), p.group(2)
    kind = props.get(key, {}).get("type", "string") if isinstance(props.get(key), dict) else "string"
    if kind != "string":
      try: value = json.loads(value)
      except json.JSONDecodeError: pass
    args[key] = value
  return name, json.dumps(args, ensure_ascii=False)


class Output:
  """Splits generated text into reasoning, content and tool calls as it streams. emit(kind, value) gets
  ('reasoning', str), ('content', str) or ('tool_call', (name, arguments))."""
  def __init__(self, emit, thinking, tools, stops):
    self.emit, self.tools, self.stops = emit, tools, [s for s in stops if s]
    self.mode = "reasoning" if thinking else "content"
    self.buf, self.content, self.calls, self.lead = "", "", 0, True
    self.stopped = False

  def feed(self, text, final=False):
    if self.stopped: return
    self.buf += text
    while self.buf:
      if self.mode == "reasoning":
        i = self.buf.find(THINK_CLOSE)
        if i < 0:
          keep = 0 if final else held(self.buf, [THINK_CLOSE])
          out, self.buf = self.buf[:len(self.buf) - keep], self.buf[len(self.buf) - keep:]
          if out: self.emit("reasoning", out)
          return
        if self.buf[:i]: self.emit("reasoning", self.buf[:i])
        self.buf, self.mode, self.lead = self.buf[i + len(THINK_CLOSE):], "content", True
      elif self.mode == "content":
        if self.lead:
          self.buf = self.buf.lstrip("\n")
          if not self.buf: return
          self.lead = False
        i = self.buf.find(CALL_OPEN) if self.tools else -1
        cut = len(self.buf) if i < 0 else i
        for s in self.stops:
          j = (self.content + self.buf[:cut]).find(s)
          if j >= 0:
            out = (self.content + self.buf)[len(self.content):j]
            if out: self.emit("content", out)
            self.stopped, self.buf = True, ""
            return
        if i < 0:
          keep = 0 if final else held(self.buf, ([CALL_OPEN] if self.tools else []) + self.stops)
          out, self.buf = self.buf[:len(self.buf) - keep], self.buf[len(self.buf) - keep:]
          if out: self.content += out; self.emit("content", out)
          return
        out = self.buf[:i].rstrip("\n") if self.calls == 0 else ""
        if out: self.content += out; self.emit("content", out)
        self.buf, self.mode = self.buf[i + len(CALL_OPEN):], "call"
      else:  # inside <tool_call>
        i = self.buf.find(CALL_CLOSE)
        if i < 0:
          if final:
            call = parse_call(self.buf.strip(), self.tools)
            if call: self.emit("tool_call", call); self.calls += 1
            self.buf = ""
          return
        call = parse_call(self.buf[:i].strip(), self.tools)
        if call: self.emit("tool_call", call); self.calls += 1
        self.buf, self.mode = self.buf[i + len(CALL_CLOSE):].lstrip("\n"), "content"
        self.lead = False


def make_handler(state):
  engine, tok, template, name, defaults = state["engine"], state["tok"], state["template"], state["name"], state["defaults"]

  class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *args): pass

    def send_json(self, code, obj):
      body = json.dumps(obj, ensure_ascii=False).encode()
      self.send_response(code)
      self.send_header("content-type", "application/json")
      self.send_header("content-length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)

    def error(self, code, message, kind="invalid_request_error"):
      self.send_json(code, {"error": {"message": message, "type": kind}})

    def do_GET(self):
      if self.path.rstrip("/") in ("/v1/models", "/models"):
        return self.send_json(200, {"object": "list", "data": [{"id": name, "object": "model", "owned_by": "blackhole-py",
                                                                 "max_model_len": engine.cap}]})
      if self.path.rstrip("/") == "/health":
        live = sum(s is not None for s in engine.owner)
        return self.send_json(200, {"status": "ok", "live": live, "waiting": len(engine.waiting) + engine.inbox.qsize(),
                                    "steps": engine.steps, "stats": dict(engine.stats),
                                    "seconds": {k: round(v, 3) for k, v in engine.times.items()},
                                    "offload": engine.store.summary() if engine.store else None})
      self.error(404, f"no route {self.path}")

    def do_OPTIONS(self):
      self.send_response(204)
      for h, v in (("access-control-allow-origin", "*"), ("access-control-allow-headers", "*"),
                   ("access-control-allow-methods", "GET, POST, OPTIONS"), ("content-length", "0")):
        self.send_header(h, v)
      self.end_headers()

    def do_POST(self):
      path = self.path.rstrip("/")
      try:
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
      except (ValueError, json.JSONDecodeError):
        return self.error(400, "the body is not JSON")
      try:
        if path in ("/v1/chat/completions", "/chat/completions"): return self.complete(body, chat=True)
        if path in ("/v1/completions", "/completions"): return self.complete(body, chat=False)
      except (ValueError, TypeError, KeyError, jinja2.TemplateError) as e:
        return self.error(400, str(e))
      self.error(404, f"no route {self.path}")

    def complete(self, body, chat):
      tools = body.get("tools") if chat and body.get("tool_choice") != "none" else None
      kwargs = dict(body.get("chat_template_kwargs") or {})
      thinking = kwargs.get("enable_thinking", body.get("reasoning_effort") not in ("none", "minimal"))
      kwargs["enable_thinking"] = thinking
      kwargs.setdefault("preserve_thinking", bool(tools))
      if chat:
        messages = body["messages"]
        for m in messages:  # tool call arguments arrive as JSON text; the template wants objects
          for c in m.get("tool_calls") or ():
            f = c.get("function", {})
            if isinstance(f.get("arguments"), str):
              try: f["arguments"] = json.loads(f["arguments"])
              except json.JSONDecodeError: pass
        prompt = template.render(messages, tools, **kwargs)
      else:
        prompt, thinking = body["prompt"], False
        if isinstance(prompt, list): prompt = prompt[0]
      ids = tok.encode(prompt, add_special_tokens=False).ids
      d = defaults(bool(tools), thinking)
      room = engine.cap - len(ids)
      if room < 1: return self.error(400, f"the prompt has {len(ids)} tokens; the context is {engine.cap}",
                                     "context_length_exceeded")
      max_new = min(room, int(body.get("max_completion_tokens") or body.get("max_tokens") or room))
      stops = body.get("stop") or []
      if isinstance(stops, str): stops = [stops]
      temperature = body.get("temperature")
      seq = Sequence(ids, max_new, temperature=d["temperature"] if temperature is None else float(temperature),
                     top_p=float(body.get("top_p") if body.get("top_p") is not None else d["top_p"]),
                     top_k=int(body.get("top_k") or 0), min_p=float(body.get("min_p") or 0), seed=body.get("seed"))
      events = queue.Queue()
      detok = Detokenizer(tok)
      parts = {"reasoning": [], "content": [], "tool_call": []}
      def emit(kind, value):
        parts[kind].append(value)
        events.put((kind, value))
      out = Output(emit, thinking, tools, stops)
      def on_token(s, token):
        out.feed(detok.add(token))
        return out.stopped
      begin = time.perf_counter()
      def on_done(s):
        out.feed("", final=True)
        took = time.perf_counter() - begin
        t = s.timings
        ttft = t.get("first token", t["done"]) - t["submitted"]
        decode = t["done"] - t.get("first token", t["done"])
        print(f"{time.strftime('%H:%M:%S')} prompt {len(ids)} (cached {s.cached}) -> {len(s.out)} tokens, "
              f"{s.finish_reason}, {took:.1f}s, first token {ttft:.2f}s, "
              f"{max(len(s.out) - 1, 0) / max(decode, 1e-9):.1f} tok/s"
              + (f" ({type(s.error).__name__}: {s.error})" if getattr(s, "error", None) else ""), file=sys.stderr, flush=True)
        events.put(("done", s.finish_reason))
      seq.on_token, seq.on_done = on_token, on_done
      ident = ("chatcmpl-" if chat else "cmpl-") + uuid.uuid4().hex[:24]
      created = int(time.time())
      engine.submit(seq)
      stream = bool(body.get("stream"))
      usage = lambda: {"prompt_tokens": len(ids), "completion_tokens": len(seq.out),
                       "total_tokens": len(ids) + len(seq.out), "prompt_tokens_details": {"cached_tokens": seq.cached}}
      if not stream:
        while True:
          kind, value = events.get()
          if kind == "done": break
        reason = "tool_calls" if parts["tool_call"] else ("length" if value == "length" else "stop")
        if value == "error": return self.error(500, str(getattr(seq, "error", "engine error")), "server_error")
        content = "".join(parts["content"])
        if chat:
          message = {"role": "assistant", "content": content or (None if parts["tool_call"] else "")}
          if parts["reasoning"]: message["reasoning_content"] = "".join(parts["reasoning"])
          if parts["tool_call"]:
            message["tool_calls"] = [{"id": "call_" + uuid.uuid4().hex[:24], "type": "function",
                                      "function": {"name": n, "arguments": a}} for n, a in parts["tool_call"]]
          choice = {"index": 0, "message": message, "finish_reason": reason}
        else:
          choice = {"index": 0, "text": content, "finish_reason": reason}
        return self.send_json(200, {"id": ident, "object": "chat.completion" if chat else "text_completion",
                                    "created": created, "model": name, "choices": [choice], "usage": usage()})
      self.send_response(200)
      self.send_header("content-type", "text/event-stream")
      self.send_header("cache-control", "no-cache")
      self.send_header("connection", "close")
      self.end_headers()
      self.close_connection = True
      def send(delta=None, reason=None, extra=None):
        if chat: choice = {"index": 0, "delta": delta or {}, "finish_reason": reason}
        else: choice = {"index": 0, "text": (delta or {}).get("content", ""), "finish_reason": reason}
        chunk = {"id": ident, "object": "chat.completion.chunk" if chat else "text_completion", "created": created,
                 "model": name, "choices": [choice], **(extra or {})}
        self.wfile.write(b"data: " + json.dumps(chunk, ensure_ascii=False).encode() + b"\n\n")
        self.wfile.flush()
      calls = 0
      try:
        if chat: send({"role": "assistant", "content": ""})
        while True:
          kind, value = events.get()
          if kind == "done": break
          if kind == "reasoning": send({"reasoning_content": value})
          elif kind == "content": send({"content": value})
          else:
            send({"tool_calls": [{"index": calls, "id": "call_" + uuid.uuid4().hex[:24], "type": "function",
                                  "function": {"name": value[0], "arguments": value[1]}}]})
            calls += 1
        reason = "tool_calls" if calls else ("length" if value == "length" else "stop")
        extra = {"usage": usage()} if (body.get("stream_options") or {}).get("include_usage") else None
        send(None, reason, extra)
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
      except (BrokenPipeError, ConnectionResetError):
        seq.cancel()

  return Handler


def nanbeige(dev, a):
  from examples.nanbeige import DEFAULT
  from examples.nanbeige_batch import NanbeigeBatch
  backend = NanbeigeBatch(a.checkpoint or DEFAULT, dev, slots=a.slots, context=a.context)
  # the model card's settings for agentic and for chat use
  defaults = lambda tools, thinking: {"temperature": 1.0 if tools else 0.6, "top_p": 0.95}
  return backend, (a.checkpoint or DEFAULT).parent, "nanbeige4.3-33b", defaults


def qwen(dev, a):
  from examples.qwen38 import DEFAULT, METADATA
  from examples.qwen38_batch import QwenBatch
  backend = QwenBatch(dev, slots=a.slots, context=a.context, checkpoint=a.checkpoint or DEFAULT)
  # the model card's recommended sampling: thinking and non-thinking
  defaults = lambda tools, thinking: {"temperature": 0.6 if thinking else 0.7, "top_p": 0.95 if thinking else 0.8,
                                      "top_k": 20}
  return backend, METADATA, "qwen3.8-27b", defaults


MODELS = {"nanbeige": nanbeige, "qwen": qwen}


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--model", default="nanbeige", choices=MODELS)
  ap.add_argument("--checkpoint", type=Path, help="override the model's default checkpoint")
  ap.add_argument("--name", default=None, help="model id reported to clients")
  ap.add_argument("--slots", type=int, default=0, help="concurrent sequences; 0: as many as DRAM holds")
  ap.add_argument("--context", type=int, default=8192, help="positions per slot")
  ap.add_argument("--host", default="127.0.0.1")
  ap.add_argument("--port", type=int, default=8000)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--cold", action="store_true", help="skip capturing prompt graphs at startup")
  ap.add_argument("--offload-ram", type=float, default=8, help="GB of host RAM for evicted prefix states")
  ap.add_argument("--offload-ssd", type=float, default=64, help="GB of SSD for prefix states (kept across restarts)")
  ap.add_argument("--offload-dir", type=Path, default=Path.home() / ".cache/blackhole-py/prefixes")
  a = ap.parse_args()
  from ttrv import Device
  from examples.kvstore import PrefixStore
  import signal
  def stop(*_): raise KeyboardInterrupt
  signal.signal(signal.SIGTERM, stop)   # a terminated server still saves its slot states
  dev = Device(a.device)
  engine = None
  try:
    t0 = time.perf_counter()
    backend, folder, name, defaults = MODELS[a.model](dev, a)
    store = PrefixStore(int(a.offload_ram * 2**30), int(a.offload_ssd * 2**30), a.offload_dir)
    if hasattr(backend, "warm") and not a.cold: backend.warm()
    engine = Engine(backend, store)
    tok = Tokenizer.from_file(str(folder / "tokenizer.json"))
    template = Template(folder)
    print(f"{name}: {engine.slots} slots x {engine.cap} positions, loaded in {time.perf_counter() - t0:.0f}s",
          file=sys.stderr)
    engine.start()
    state = dict(engine=engine, tok=tok, template=template, name=a.name or name, defaults=defaults)
    server = ThreadingHTTPServer((a.host, a.port), make_handler(state))
    server.daemon_threads = True
    print(f"serving http://{a.host}:{a.port}/v1 as {state['name']!r}", file=sys.stderr)
    server.serve_forever()
  except KeyboardInterrupt: pass
  finally:
    if engine is not None:
      print("saving slot states...", file=sys.stderr)
      engine.flush()
    dev.close()


if __name__ == "__main__":
  main()
