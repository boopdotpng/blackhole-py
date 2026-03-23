"""Local HTTP API for the Blackhole debug session."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from debug.session import DebugSession


class _DebugHTTPServer(ThreadingHTTPServer):
  def __init__(self, server_address, session: DebugSession):
    super().__init__(server_address, _Handler)
    self.session = session


class _Handler(BaseHTTPRequestHandler):
  server: _DebugHTTPServer

  def do_GET(self):
    parsed = urlparse(self.path)
    if parsed.path == "/status":
      self._json(200, self.server.session.snapshot())
      return
    if parsed.path == "/events":
      qs = parse_qs(parsed.query)
      since = int(qs.get("since", ["0"])[0])
      self._json(200, {"events": self.server.session.events_since(since)})
      return
    if parsed.path == "/events/stream":
      self._sse(parsed.query)
      return
    self._json(404, {"error": "not found"})

  def do_POST(self):
    parsed = urlparse(self.path)
    body = self._read_json_body()
    if parsed.path == "/command":
      command = body.get("command")
      args = body.get("args") or {}
      if not isinstance(command, str):
        self._json(400, {"error": "missing string command"})
        return
      self._json(200, self.server.session.execute(command, args))
      return
    if parsed.path == "/shutdown":
      payload = self.server.session.execute("shutdown_session")
      self._json(200, payload)
      return
    self._json(404, {"error": "not found"})

  def _read_json_body(self) -> dict:
    length = int(self.headers.get("Content-Length", "0"))
    if length == 0:
      return {}
    raw = self.rfile.read(length)
    if not raw:
      return {}
    return json.loads(raw.decode())

  def _json(self, code: int, body: dict):
    encoded = json.dumps(body).encode()
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(encoded)))
    self.end_headers()
    self.wfile.write(encoded)

  def _sse(self, query: str):
    qs = parse_qs(query)
    since = int(qs.get("since", ["0"])[0])
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("Connection", "keep-alive")
    self.end_headers()
    self.wfile.flush()
    try:
      while True:
        events = self.server.session.wait_for_events(since=since, timeout=1.0)
        for event in events:
          since = max(since, event["seq"])
          payload = json.dumps(event)
          self.wfile.write(f"id: {event['seq']}\n".encode())
          self.wfile.write(b"event: debug\n")
          self.wfile.write(f"data: {payload}\n\n".encode())
        self.wfile.write(b": keep-alive\n\n")
        self.wfile.flush()
        if self.server.session.wait_for_shutdown(timeout=0.0):
          return
    except (BrokenPipeError, ConnectionResetError):
      return

  def log_message(self, *_):
    pass


def serve(session: DebugSession, host: str = "127.0.0.1", port: int = 0):
  server = _DebugHTTPServer((host, port), session)
  actual_host, actual_port = server.server_address
  print(json.dumps({
    "ready": True,
    "mode": "debug-server",
    "host": actual_host,
    "port": actual_port,
    "status_url": f"http://{actual_host}:{actual_port}/status",
    "events_url": f"http://{actual_host}:{actual_port}/events/stream",
  }))
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()
  try:
    session.wait_for_shutdown()
  finally:
    server.shutdown()
    thread.join(timeout=5.0)
    server.server_close()
