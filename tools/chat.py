"""Minimal, decode-only Llama 3 8B web chat: python -m tools.chat."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock

from transformers import AutoTokenizer
from examples.llama3 import Llama3Decode, Llama3Kernels


class Chat:
  def __init__(self, device):
    self.device, self.runtime, self.tokenizer = device, None, None
    self.lock = Lock()

  def close(self):
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
      yield {'status': f'Loading 8B {dtype.upper()}…'}
      self.close()
      kernels = Llama3Kernels('8b', dtype)
      self.tokenizer = AutoTokenizer.from_pretrained(kernels.checkpoint, local_files_only=True)
      self.runtime = Llama3Decode(device_index=self.device, kernels=kernels)
    runtime, tokenizer = self.runtime, self.tokenizer
    tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if not isinstance(tokens, list): tokens = tokens['input_ids']
    if tokens and isinstance(tokens[0], list): tokens = tokens[0]
    room = runtime.kernels.ROPE_CACHE_TOKENS - len(tokens)
    if not tokens or room < 1: raise ValueError('Conversation exceeds the 8192-token context. Start a new chat.')
    yield {'status': f'Decoding {len(tokens)} conversation tokens…'}
    runtime.load_tokens(tokens)
    for position in range(len(tokens)):
      last = position == len(tokens) - 1
      token, _ = runtime.decode(position, logits=last, append=last)
    generated = []
    limit = min(512, room)
    for step in range(limit):
      if token in runtime.kernels.EOS_TOKEN_IDS:
        yield {'done': True, 'status': 'Ready'}
        return
      generated.append(token)
      yield {'text': tokenizer.decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)}
      if step + 1 < limit: token, _ = runtime.decode(len(tokens) + step)
    yield {'done': True, 'status': 'Response limit reached (512 tokens)' if room > 512 else 'Context full — start a new chat'}


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
  parser.add_argument('--host', default='127.0.0.1')
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
