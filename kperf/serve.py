#!/usr/bin/env python3
"""kperf: a viewer for Blackhole kernel profiles (bundles written by `python -m kperf.collect`).

  python kperf/serve.py [--port 8140] [--host 0.0.0.0] [--kview-port 8137] [--no-kview]

Standard library and numpy. Code regions link into kview, which this starts alongside unless something already listens on
--kview-port (or --no-kview). Bundles (kperf/bundle.py) are sent as stored, gzip and all, and the browser inflates them.
"""
import argparse, atexit, ctypes, json, re, signal, socket, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from kperf import bundle as kbundle
from kperf.findings import findings  # recomputed on load, so improved rules apply to old bundles
STATIC, BUNDLES = HERE / "static", HERE / "bundles"
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}
SUMMARY = ("model", "model_name", "kernel", "layer", "position", "created", "launches", "card")

_cache, _lock = {}, threading.Lock()
def cached(kind, path, fn):
  """fn(path), memoized until the file changes."""
  st = path.stat(); key = (kind, path)
  with _lock: hit = _cache.get(key)
  if hit and hit[0] == (st.st_mtime_ns, st.st_size): return hit[1]
  val = fn(path)
  with _lock: _cache[key] = ((st.st_mtime_ns, st.st_size), val)
  return val

def bundles():
  out = []
  for p in sorted(BUNDLES.glob("*.kperf"), key=lambda p: -p.stat().st_mtime):
    try: h = cached("head", p, kbundle.read_header)
    except (OSError, ValueError, EOFError): continue
    out.append(dict(name=p.stem, median=h["launch"]["median"], **{k: h.get(k) for k in SUMMARY}))
  return out

def bundle_path(name):
  if not re.fullmatch(r"[\w.\-]+", name): raise ValueError("bad bundle name")
  return BUNDLES / f"{name}.kperf"

class Handler(BaseHTTPRequestHandler):
  kview_port = 8137
  def log_message(self, *a): pass

  def send(self, body, ctype="application/json", status=200, headers=()):
    if not isinstance(body, bytes): body = json.dumps(body).encode()
    self.send_response(status)
    self.send_header("Content-Type", ctype)
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    for k, v in headers: self.send_header(k, v)
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self):
    url = urlsplit(self.path)
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    try:
      if url.path == "/api/bundles": return self.send(dict(bundles=bundles(), kview_port=self.kview_port))
      if url.path == "/api/bundle":  # the stored gzip stream; the browser undoes Content-Encoding
        return self.send(bundle_path(q["name"]).read_bytes(), "application/octet-stream", headers=[("Content-Encoding", "gzip")])
      if url.path == "/api/findings":
        return self.send(cached("findings", bundle_path(q["name"]), lambda p: findings(kbundle.read(p))))
      name = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
      path = (STATIC / name).resolve()
      if STATIC not in path.parents or not path.is_file(): return self.send(dict(error="not found"), status=404)
      return self.send(path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))
    except (KeyError, ValueError, OSError, EOFError) as e:
      return self.send(dict(error=f"{type(e).__name__}: {e}"), status=400)

def start_kview(host, port):
  """kview/serve.py as a child that dies with us; None if the port is taken (kview probably already runs there)."""
  with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0: return None
  def die_with_parent():  # Linux PR_SET_PDEATHSIG: kview gets SIGTERM even if we are SIGKILLed
    try: ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM)
    except (OSError, AttributeError): pass
  p = subprocess.Popen([sys.executable, str(HERE.parent / "kview" / "serve.py"), "--port", str(port), "--host", host],
                       preexec_fn=die_with_parent)
  atexit.register(p.terminate)
  signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # run atexit on a plain kill too
  return p

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--port", type=int, default=8140)
  ap.add_argument("--host", default="0.0.0.0")
  ap.add_argument("--kview-port", type=int, default=8137)
  ap.add_argument("--no-kview", action="store_true", help="do not start kview")
  a = ap.parse_args()
  Handler.kview_port = a.kview_port
  kv = None if a.no_kview else start_kview(a.host, a.kview_port)
  print(f"kperf on http://{a.host}:{a.port}  ({len(bundles())} bundles in {BUNDLES}); kview on :{a.kview_port}"
        f"{' (started)' if kv else ' (not started)' if a.no_kview else ' (already running)'}", flush=True)
  try: ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
  except KeyboardInterrupt: pass

if __name__ == "__main__": main()
