import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

_data_json = ""
_disasm_dir: Path | None = None
_HTML = (Path(__file__).with_name("ui.html")).read_text()

class _Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    parsed = urlparse(self.path)
    if parsed.path == "/api/data":
      self._json(200, _data_json)
    elif parsed.path == "/api/disasm":
      self._serve_disasm(parsed.query)
    elif parsed.path == "/" or parsed.path == "/index.html":
      self._html(200, _HTML)
    else:
      self._json(404, '{"error":"not found"}')

  def _serve_disasm(self, query: str):
    if _disasm_dir is None:
      self._json(404, '{"error":"disassembly unavailable"}')
      return
    qs = parse_qs(query)
    prog = qs.get("program", [None])[0]
    core = qs.get("core", [None])[0]
    section = qs.get("section", [None])[0]
    filename = qs.get("filename", [None])[0]
    if prog is None:
      self._json(400, '{"error":"missing program"}')
      return
    base = _disasm_dir / f"program-{prog}"
    if core:
      base = base / "cores" / core.replace(",", "-")
    else:
      base = base / "global"
    if not base.is_dir():
      self._json(404, '{"error":"disassembly unavailable"}')
      return
    if section is not None:
      path = base / f"{section}.S"
      if not path.is_file():
        self._json(404, '{"error":"disassembly unavailable"}')
        return
      download_name = Path(filename).name if filename else path.name
      self.send_response(200)
      self.send_header("Content-Type", "text/plain; charset=utf-8")
      self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
      self.end_headers()
      self.wfile.write(path.read_bytes())
      return
    payload = {p.stem: p.read_text() for p in sorted(base.glob("*.S"))}
    self._json(200, json.dumps(payload))

  def _json(self, code, body):
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.end_headers()
    self.wfile.write(body.encode() if isinstance(body, str) else body)

  def _html(self, code, body):
    self.send_response(code)
    self.send_header("Content-Type", "text/html")
    self.end_headers()
    self.wfile.write(body.encode())

  def log_message(self, *_):
    pass

def serve(data: dict, port: int = 8000, disasm_dir: str | Path | None = None):
  global _data_json, _disasm_dir
  _data_json = json.dumps(data)
  _disasm_dir = Path(disasm_dir) if disasm_dir else None
  server = HTTPServer(("", port), _Handler)
  print(f"open profiler @ http://localhost:{port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()

if __name__ == "__main__":
  import sys

  path = sys.argv[1] if len(sys.argv) > 1 else "profiler_data.json"
  serve(json.loads(Path(path).read_text()))
