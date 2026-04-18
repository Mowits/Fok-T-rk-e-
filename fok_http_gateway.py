#!/usr/bin/env python3
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 8877
FOK_TEXT_HOST = "127.0.0.1"
FOK_TEXT_PORT = 8766


def send_to_fok_text(text: str):
    payload = (json.dumps({"text": text}, ensure_ascii=True) + "\n").encode("utf-8")
    with socket.create_connection((FOK_TEXT_HOST, FOK_TEXT_PORT), timeout=3) as s:
        s.sendall(payload)


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(n) if n > 0 else b""
        if u.path != "/text":
            return self._json(404, {"ok": False, "error": "not_found"})
        try:
            ct = (self.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                obj = json.loads(body.decode("utf-8") or "{}")
                text = (obj.get("text") or "").strip()
            else:
                text = body.decode("utf-8").strip()
            if not text:
                return self._json(400, {"ok": False, "error": "empty_text"})
            send_to_fok_text(text)
            return self._json(200, {"ok": True})
        except Exception as e:
            return self._json(500, {"ok": False, "error": str(e)})


def main():
    print(f"[HTTP-GW] http://{HOST}:{PORT} -> {FOK_TEXT_HOST}:{FOK_TEXT_PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
