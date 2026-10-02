# tiny logging reverse proxy: :11435 -> :11434, appends request bodies to sniff.jsonl
import http.server, urllib.request, json, sys
class H(http.server.BaseHTTPRequestHandler):
    def _fwd(self):
        n=int(self.headers.get('content-length') or 0); body=self.rfile.read(n) if n else None
        with open('sniff.jsonl','a') as f: f.write(json.dumps({"method":self.command,"path":self.path,"body":body.decode() if body else None})+"\n")
        req=urllib.request.Request("http://127.0.0.1:11434"+self.path, data=body, method=self.command, headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','content-length')})
        try: r=urllib.request.urlopen(req, timeout=600); code=r.status; data=r.read(); hdrs=r.headers
        except urllib.error.HTTPError as e: code=e.code; data=e.read(); hdrs=e.headers
        self.send_response(code)
        for k,v in hdrs.items():
            if k.lower() not in ('transfer-encoding','content-length','connection'): self.send_header(k,v)
        self.send_header('content-length',str(len(data))); self.end_headers(); self.wfile.write(data)
    do_GET=do_POST=do_DELETE=_fwd
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(("127.0.0.1",11435),H).serve_forever()
