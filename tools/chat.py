"""Minimal, decode-only Llama 3 8B web chat: python -m tools.chat."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock

from tokenizers.decoders import DecodeStream
from transformers import AutoTokenizer
from examples.llama3 import Llama3Decode, Llama3Kernels


class Chat:
  def __init__(self, device):
    self.device, self.runtime, self.tokenizer = device, None, None
    self.lock = Lock()
    self.cached_tokens = []

  def close(self):
    self.cached_tokens = []
    if self.runtime is not None:
      self.runtime.close()
      self.runtime = None

  def generate(self, dtype, messages):
    if dtype not in ('fp8', 'bf16'): raise ValueError('Choose 8B FP8 or BF16')
    if not isinstance(messages, list) or not messages: raise ValueError('Messages are required')
    for i, message in enumerate(messages):
      if (not isinstance(message, dict) or message.get('role') != ('user' if i % 2 == 0 else 'assistant')
          or not isinstance(message.get('content'), str) or not message['content'].strip()):
        raise ValueError('Expected alternating user and assistant messages')
    if len(messages) % 2 != 1: raise ValueError('The last message must be from the user')
    if self.runtime is None or self.runtime.kernels.dtype != dtype:
      yield {'status': f'Loading Llama 3 8B {dtype.upper()} into DRAM…'}
      self.close()
      kernels = Llama3Kernels('8b', dtype)
      self.tokenizer = AutoTokenizer.from_pretrained(kernels.checkpoint, local_files_only=True)
      self.runtime = Llama3Decode(device_index=self.device, kernels=kernels)
    runtime, tokenizer = self.runtime, self.tokenizer
    tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if not isinstance(tokens, list): tokens = tokens['input_ids']
    if tokens and isinstance(tokens[0], list): tokens = tokens[0]
    room = runtime.kernels.ROPE_CACHE_TOKENS - len(tokens)
    yield {'context': len(tokens), 'context_limit': runtime.kernels.ROPE_CACHE_TOKENS}
    if not tokens or room < 1: raise ValueError('Conversation exceeds the 8192-token context. Start a new chat.')
    # Cache only tokens actually consumed by decode, not its predicted next token.
    start = 0
    for cached, incoming in zip(self.cached_tokens, tokens[:-1]):
      if cached != incoming: break
      start += 1
    self.cached_tokens = self.cached_tokens[:start]
    yield {'status': f'Decoding {len(tokens) - start} new tokens ({start} cached)…'}
    try:
      runtime.load_tokens(tokens, start=start)
      for position in range(start, len(tokens)):
        last = position == len(tokens) - 1
        token, _ = runtime.decode(position, logits=last, append=last)
        self.cached_tokens.append(tokens[position])
      generated, emitted = [], 0
      decoder = DecodeStream(skip_special_tokens=True)
      status = 'Context full — start a new chat'
      for step in range(room):
        if token in runtime.kernels.EOS_TOKEN_IDS:
          status = 'Ready'
          break
        generated.append(token)
        delta = decoder.step(tokenizer.backend_tokenizer, token) or ''
        emitted += len(delta)
        yield {'delta': delta, 'context': len(tokens) + len(generated)}
        if step + 1 < room:
          consumed = token
          token, _ = runtime.decode(len(tokens) + step)
          self.cached_tokens.append(consumed)
      # Flush any final incomplete Unicode sequence once at the end.
      tail = tokenizer.decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)[emitted:]
      yield {'delta': tail, 'done': True, 'status': status,
             'context': len(tokens) + len(generated) + int(status == 'Ready')}
    except Exception:
      self.cached_tokens = []
      raise


class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path != '/': return self.send_error(404)
    body = Path(__file__).with_suffix('.html').read_bytes()
    self.send_response(200)
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.send_header('Content-Length', str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def do_POST(self):
    if self.path != '/chat': return self.send_error(404)
    try:
      size = int(self.headers.get('Content-Length', '0'))
      if not 0 < size <= 1_000_000: return self.send_error(413)
      data = json.loads(self.rfile.read(size))
      if not isinstance(data, dict): raise ValueError('Expected a JSON object')
    except (ValueError, UnicodeError):
      return self.send_error(400, 'Invalid request')
    chat = self.server.chat
    if not chat.lock.acquire(blocking=False): return self.send_error(409, 'Device busy; try again shortly')
    try:
      self.send_response(200)
      self.send_header('Content-Type', 'application/x-ndjson')
      self.send_header('Cache-Control', 'no-store')
      self.end_headers()
      try:
        for event in chat.generate(data.get('model'), data.get('messages')): self.event(event)
      except (BrokenPipeError, ConnectionResetError):
        pass
      except Exception as error:
        self.event({'error': str(error)})
    finally:
      chat.lock.release()

  def event(self, event):
    self.wfile.write((json.dumps(event) + '\n').encode())
    self.wfile.flush()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--host', default='0.0.0.0')
  parser.add_argument('--port', type=int, default=8000)
  args = parser.parse_args()
  with ThreadingHTTPServer((args.host, args.port), Handler) as server:
    server.chat = Chat(args.device)
    server.daemon_threads = False
    print(f'Chat: http://{args.host}:{args.port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
      with server.chat.lock: server.chat.close()


if __name__ == '__main__': main()
