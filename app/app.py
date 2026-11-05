"""Tiny HTTP service for the lab (standard library only, no dependencies)."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = os.environ.get("APP_VERSION", "dev")


def health():
    return {"status": "ok", "version": VERSION}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps(health()).encode()
            content_type = "application/json"
        else:
            body = b"Hello from the DevOps prep lab\n"
            content_type = "text/plain"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Listening on {host}:{port}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()
