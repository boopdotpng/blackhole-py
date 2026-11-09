"""Model-agnostic web chat: serves index.html and streams generated text as NDJSON.

A model plugs in with serve(): a tokenizer with chat(messages) -> ids and decode(ids) -> str, and
generate(ids, start, on_token) -> generated ids that reuses its KV cache for positions before start, calls
on_token(id) as each token arrives and stops after an EOS token or at the context limit. One request runs at a time.
The server remembers which ids the device has consumed, so a follow-up turn only decodes the new tokens.

  GET  /info  -> {"name": ..., "context": n}
  POST /chat {"messages": [{"role": "user", "content": ...}, ...]}  ->  one JSON event per line:
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
  def __init__(self, name, tokenizer, generate, context, eos):
    self.name, self.tok, self.generate, self.context, self.eos = name, tokenizer, generate, context, set(eos)
    self.lock, self.consumed = Lock(), []  # ids at the positions whose KV cache is valid

  def run(self, messages, emit):
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

  def reply(self, body:bytes, kind:str):
    self.send_response(200)
    self.send_header("Content-Type", kind)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self):
    chat = self.server.chat
    if self.path == "/": self.reply(PAGE.read_bytes(), "text/html; charset=utf-8")
    elif self.path == "/info": self.reply(json.dumps({"name": chat.name, "context": chat.context}).encode(), "application/json")
    else: self.send_error(404)

  def do_POST(self):
    if self.path != "/chat": return self.send_error(404)
    try:
      size = int(self.headers.get("Content-Length", "0"))
      if not 0 < size <= 1 << 20: return self.send_error(413)
      messages = json.loads(self.rfile.read(size)).get("messages")
    except (ValueError, AttributeError):
      return self.send_error(400, "invalid request")
    chat = self.server.chat
    if not chat.lock.acquire(blocking=False): return self.send_error(409, "busy with another request; try again shortly")
    try:
      self.send_response(200)
      self.send_header("Content-Type", "application/x-ndjson")
      self.send_header("Cache-Control", "no-store")
      self.end_headers()
      def emit(event):
        self.wfile.write(json.dumps(event).encode() + b"\n")
        self.wfile.flush()
      try: chat.run(messages, emit)
      except (BrokenPipeError, ConnectionResetError): pass  # the client left; generation stopped with it
      except Exception as e: emit({"error": str(e)})
    finally:
      chat.lock.release()

def serve(name, tokenizer, generate, context, eos, host="0.0.0.0", port=8000):
  """Serve one loaded model until interrupted."""
  with ThreadingHTTPServer((host, port), Handler) as server:
    server.chat = Chat(name, tokenizer, generate, context, eos)
    print(f"{name} chat on http://{host}:{port}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
