"""Model-agnostic web chat: serves index.html and streams generated text as NDJSON.

Models plug in with serve(): load(key) -> (tokenizer, generate, context, eos, close) for one of the listed models.
The tokenizer has chat(messages) -> ids and decode(ids) -> str; generate(ids, start, on_token) -> generated ids reuses
its KV cache for positions before start, calls on_token(id) as each token arrives and stops after an EOS token or at
the context limit; close() unloads the model. No model is loaded until the page picks one, one model is loaded at a
time and one request runs at a time.
The server remembers which ids the device has consumed, so a follow-up turn only decodes the new tokens.

  GET  /info  -> {"models": {key: name}, "model": loaded key or null, "context": n}
  POST /load {"model": key}  -> the new /info after unloading the current model and loading that one, or {"error": message}
  POST /chat {"model": key, "messages": [{"role": "user", "content": ...}, ...]}  ->  one JSON event per line:
    {"context": n, "cached": n}     tokens in this request, and how many reuse the KV cache
    {"delta": text}                 generated text, in order
    {"done": true, "stats": {...}}  tokens, tok_s (decode), prefill_ms (to the first token), cached, stop
    {"error": message}
"""
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

PAGE = Path(__file__).with_name("index.html")

class Chat:
  def __init__(self, models, load):
    self.models, self._load, self.lock = models, load, Lock()
    self.key = self.tok = self.generate = self.context = self.close = None

  def info(self): return {"models": self.models, "model": self.key, "context": self.context}

  def load(self, key):
    if key not in self.models: raise ValueError(f"unknown model {key!r}")
    if key == self.key: return
    self.unload()
    print(f"loading {self.models[key]}", flush=True)
    self.tok, self.generate, self.context, eos, self.close = self._load(key)
    self.eos, self.consumed, self.key = set(eos), [], key  # consumed: ids at the positions whose KV cache is valid

  def unload(self):
    close, self.key, self.tok, self.generate, self.context, self.close = self.close, None, None, None, None, None
    if close: close()

  def run(self, model, messages, emit):
    if self.key is None: raise ValueError("no model is loaded; select one first")
    if model != self.key:  # a chat stays with the model it started on
      raise ValueError(f"{self.models.get(model, 'this chat model')} is no longer loaded; start a new chat")
    if not isinstance(messages, list) or len(messages) % 2 != 1 or not all(
        isinstance(m, dict) and m.get("role") == ("user", "assistant")[i % 2] and isinstance(m.get("content"), str)
        and m["content"].strip() for i, m in enumerate(messages)):
      raise ValueError("expected alternating user and assistant messages, ending with the user's")
    ids = self.tok.chat(messages)
    if len(ids) >= self.context: raise ValueError(f"the conversation fills the {self.context}-token context; start a new chat")
    start = next((i for i, (a, b) in enumerate(zip(self.consumed, ids[:-1])) if a != b), min(len(self.consumed), len(ids) - 1))
    emit({"context": len(ids), "cached": start, "context_limit": self.context})

    gen, times, sent = [], [time.perf_counter()], ""
    def on_token(token):  # between positions: stream the text once it decodes to whole characters
      nonlocal sent
      times.append(time.perf_counter())
      if token in self.eos: return
      gen.append(token)
      text = self.tok.decode(gen)
      if not text.endswith("�") and len(text) > len(sent): emit({"delta": text[len(sent):]}); sent = text
    self.consumed = []  # an interrupted request leaves positions after start overwritten
    out = self.generate(ids, start, on_token)
    self.consumed = ids + out[:-1]  # the last token was produced, not consumed
    if tail := self.tok.decode(gen)[len(sent):]: emit({"delta": tail})
    decode_s = times[-1] - times[1]
    emit({"done": True, "context": len(ids) + len(out), "stats": dict(
      tokens=len(out), cached=start, prefill_ms=1e3 * (times[1] - times[0]),
      tok_s=(len(out) - 1) / decode_s if decode_s > 0 else None,
      stop="eos" if out and out[-1] in self.eos else "context")})

class Handler(BaseHTTPRequestHandler):
  def log_message(self, *args): pass

  def reply(self, body, kind="application/json"):
    if not isinstance(body, bytes): body = json.dumps(body).encode()
    self.send_response(200)
    self.send_header("Content-Type", kind)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self):
    chat = self.server.chat
    if self.path == "/": self.reply(PAGE.read_bytes(), "text/html; charset=utf-8")
    elif self.path == "/info": self.reply(chat.info())
    else: self.send_error(404)

  def do_POST(self):
    if self.path not in ("/chat", "/load"): return self.send_error(404)
    try:
      size = int(self.headers.get("Content-Length", "0"))
      if not 0 < size <= 1 << 20: return self.send_error(413)
      body = json.loads(self.rfile.read(size))
      model, messages = body.get("model"), body.get("messages")
    except (ValueError, AttributeError):
      return self.send_error(400, "invalid request")
    chat = self.server.chat
    if not chat.lock.acquire(blocking=False): return self.reply({"error": "busy with another request; try again shortly"})
    try:
      if self.path == "/load":
        try: chat.load(model)
        except Exception as e: return self.reply({"error": f"{type(e).__name__}: {e}", **chat.info()})
        return self.reply(chat.info())
      self.send_response(200)
      self.send_header("Content-Type", "application/x-ndjson")
      self.send_header("Cache-Control", "no-store")
      self.end_headers()
      def emit(event):
        self.wfile.write(json.dumps(event).encode() + b"\n")
        self.wfile.flush()
      try: chat.run(model, messages, emit)
      except (BrokenPipeError, ConnectionResetError): pass  # the client left; generation stopped with it
      except Exception as e: emit({"error": str(e)})
    finally:
      chat.lock.release()

def serve(models, load, host="0.0.0.0", port=8000):
  """Serve the models ({key: name}) until interrupted. None is loaded until the page picks one; then one at a time."""
  chat = Chat(models, load)
  try:
    with ThreadingHTTPServer((host, port), Handler) as server:
      server.chat = chat
      print(f"chat on http://{host}:{port}", flush=True)
      try: server.serve_forever()
      except KeyboardInterrupt: pass
  finally:
    chat.unload()
