"""Loopback-only HTTP view over the same snapshot returned to agents."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit, parse_qs

from .sources import now, snapshot

WEB = Path(__file__).parent / 'web'


def shared(saved, failure):
    """Every reader of an older snapshot learns that a later refresh failed, not only the one who asked."""
    if failure is None:
        return saved
    at = failure['failed_at'][:19].replace('T', ' ')
    note = f"The last refresh failed at {at} UTC: {failure['error']} This snapshot is older."
    return {**saved, 'refresh_failed': failure, 'attention': [note, *saved.get('attention', [])]}


def make_server(config, port=7871):
    lock = threading.Lock()
    saved = failure = None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal saved, failure
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            host = self.headers.get('Host')
            origin = self.headers.get('Origin')
            if host not in allowed or (origin and origin not in {f'http://{h}' for h in allowed}) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.reply(403, b'Local access only.', 'text/plain')
                return
            parsed = urlsplit(self.path)
            if parsed.path == '/api/snapshot':
                with lock:
                    status, value = 200, None
                    if saved is None or parse_qs(parsed.query).get('refresh') == ['1']:
                        try:
                            saved, failure = snapshot(config), None
                        except (OSError, ValueError, KeyError) as error:
                            failure = {'failed_at': now(), 'error': str(error)}
                            status, value = 503, failure
                    body = json.dumps(value or shared(saved, failure), ensure_ascii=False).encode()
                self.reply(status, body, 'application/json')
                return
            files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
            if parsed.path not in files:
                self.reply(404, b'Not found.', 'text/plain')
                return
            filename, kind = files[parsed.path]
            self.reply(200, (WEB / filename).read_bytes(), kind)

        def reply(self, status, body, kind):
            self.send_response(status)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
