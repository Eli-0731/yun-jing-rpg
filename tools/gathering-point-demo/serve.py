"""Local static server for the creek demo (repo root as web root, 127.0.0.1 only).
    uv run --no-project python tools/gathering-point-demo/serve.py [--port 8765] [--capture DIR]
Open http://127.0.0.1:8765/tools/gathering-point-demo/
--capture DIR also accepts POST /__capture?name=<file>.png (a canvas PNG) and saves it in DIR; used only for
the walkthrough screenshots. This server never answers /gather: without ?server= the demo stays 本機演示.
"""
import argparse,re
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs

ROOT=Path(__file__).resolve().parents[2]

class Handler(SimpleHTTPRequestHandler):
    capture=None
    def do_POST(self):
        u=urlparse(self.path);name=parse_qs(u.query).get('name',[''])[0]
        if u.path!='/__capture' or not self.capture or not re.fullmatch(r'[\w\-]{1,80}\.png',name):
            self.send_error(404);return
        data=self.rfile.read(int(self.headers.get('Content-Length','0')))
        if not data.startswith(b'\x89PNG'):self.send_error(400,'not a PNG');return
        self.capture.mkdir(parents=True,exist_ok=True);(self.capture/name).write_bytes(data)
        self.send_response(204);self.end_headers()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);ap.add_argument('--capture');a=ap.parse_args()
    Handler.capture=Path(a.capture).resolve() if a.capture else None
    Handler.extensions_map={**Handler.extensions_map,'.glb':'model/gltf-binary','.js':'text/javascript'}
    srv=ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(ROOT)))
    print(f'serving {ROOT} on http://127.0.0.1:{a.port}/tools/gathering-point-demo/'+(f'  (captures -> {Handler.capture})' if Handler.capture else ''),flush=True)
    srv.serve_forever()
