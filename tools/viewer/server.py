#!/usr/bin/env python3
"""Local, dependency-light test assembly viewer. Run with the repo's Python environment."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Lock
from urllib.parse import parse_qs, urlsplit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STATIC=HERE/'static'


class Backend:
    def __init__(self):
        self.lock=Lock(); self.pool=ThreadPoolExecutor(max_workers=2)
        self.catalog=None; self.stamp=None; self.cache={}

    def fingerprint(self):
        paths=list(ROOT.glob('*.py'))
        for directory in ('tests','firmware','ttko','examples','tools/viewer'):
            paths.extend((ROOT/directory).rglob('*.py'))
        paths.extend((HERE/'data').glob('*.json'))
        return hashlib.sha256(''.join(f'{p}:{p.stat().st_mtime_ns}:{p.stat().st_size}' for p in sorted(paths)).encode()).hexdigest()

    def worker(self,mode,case='tests'):
        with tempfile.TemporaryDirectory(prefix='bh-viewer-') as tmp:
            output=Path(tmp)/'capture.json'
            result=subprocess.run([sys.executable,str(HERE/'capture.py'),mode,'--case',case,'--output',str(output)],
                                  cwd=ROOT,capture_output=True,text=True,timeout=90)
            if result.returncode or not output.exists():
                raise RuntimeError((result.stdout+result.stderr)[-5000:] or 'Capture worker failed')
            data=json.loads(output.read_text())
            if mode=='catalog' and data['pytestExit'] not in (0,5):
                raise RuntimeError('Pytest collection failed:\n'+(result.stdout+result.stderr)[-5000:])
            return data

    def get_catalog(self):
        with self.lock:
            stamp=self.fingerprint()
            if self.catalog is None or stamp!=self.stamp:
                self.catalog=self.worker('catalog'); self.stamp=stamp; self.cache={}
            return dict(cases=self.catalog['cases'],context=self.catalog['context'],fingerprint=self.stamp)

    def get_case(self,nodeid,refresh=False):
        catalog=self.get_catalog()
        if nodeid not in {c['id'] for c in catalog['cases']}: raise ValueError('Unknown pytest case; refresh the case list')
        with self.lock:
            if refresh or nodeid not in self.cache: self.cache[nodeid]=self.pool.submit(self.worker,'capture',nodeid)
            future=self.cache[nodeid]
        result=future.result()
        return dict(result=result['results'][0] if result['results'] else None,context=result['context'],fingerprint=catalog['fingerprint'])


BACKEND=Backend()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlsplit(self.path)
        try:
            if url.path=='/api/catalog': return self.send_json(BACKEND.get_catalog())
            if url.path=='/api/case': return self.send_json(BACKEND.get_case(parse_qs(url.query).get('id',[''])[0],parse_qs(url.query).get('refresh')==['1']))
            if url.path=='/api/reference': return self.send_file(HERE/'data/instructions.json','application/json')
            files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/behavior.mjs':('behavior.mjs','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            if url.path in files:
                file,mime=files[url.path]; return self.send_file(STATIC/file,mime)
            self.send_json({'error':'Not found'},404)
        except ValueError as error: self.send_json({'error':str(error)},400)
        except subprocess.TimeoutExpired: self.send_json({'error':'Capture exceeded 90 seconds. The case may need a live device or external resources.'},504)
        except Exception as error: self.send_json({'error':str(error)},500)

    def send_file(self,path,mime): self.send_bytes(path.read_bytes(),mime)
    def send_json(self,data,status=200): self.send_bytes(json.dumps(data).encode(),'application/json',status)
    def send_bytes(self,data,mime,status=200):
        self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError): pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--host',default='127.0.0.1')
    args=parser.parse_args()
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'Blackhole test viewer: http://{args.host}:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close(); BACKEND.pool.shutdown(wait=False,cancel_futures=True)

if __name__=='__main__': main()
