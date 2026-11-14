"""Local-only regressions for credential isolation and resolver scope."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import subprocess
import sys
import threading

import pytest

from noema_client.transport import default_http


@contextmanager
def server(handler):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_protocol_redirects_never_reach_target(status, method):
    target_requests = []
    source_requests = []

    class Target(BaseHTTPRequestHandler):
        def handle_request(self):
            target_requests.append(dict(self.headers))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        do_GET = do_POST = handle_request

        def log_message(self, *args):
            pass

    with server(Target) as target:
        class Redirect(BaseHTTPRequestHandler):
            def handle_request(self):
                source_requests.append(dict(self.headers))
                self.send_response(status)
                self.send_header("Location", target + "/stolen")
                self.end_headers()
                # A redirect body must not masquerade as a successful command.
                self.wfile.write(b'{"ok": true}')

            do_GET = do_POST = handle_request

            def log_message(self, *args):
                pass

        with server(Redirect) as source:
            result = default_http(
                method, source + "/protocol", {"command": "SYNTHETIC"} if method == "POST" else None,
                "synthetic-controller-secret",
                headers={"X-Noema-Admin-Token": "synthetic-admin-secret", "X-Noema-Seal": "synthetic-seal"},
            )

    assert len(source_requests) == 1
    assert source_requests[0]["Authorization"] == "Bearer synthetic-controller-secret"
    assert source_requests[0]["X-Noema-Admin-Token"] == "synthetic-admin-secret"
    assert target_requests == [], "Redirect must not forward any request or credentials"
    assert result["_http_status"] == status
    assert result["ok"] is False
    assert result["error"]["code"] == "HTTP_REDIRECT_REJECTED"


def run_fresh_python(script):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True)


def test_import_does_not_mutate_global_resolver():
    result = run_fresh_python("""
import socket
original = socket.getaddrinfo
import noema_client.transport
assert socket.getaddrinfo is original, 'transport import mutated socket.getaddrinfo'
""")
    assert result.returncode == 0, result.stderr


def test_import_preserves_explicit_ipv6_resolver_family():
    result = run_fresh_python("""
import socket
import noema_client.transport
results = socket.getaddrinfo('::1', 80, socket.AF_INET6, socket.SOCK_STREAM,
                             flags=socket.AI_NUMERICHOST)
assert results and all(result[0] == socket.AF_INET6 for result in results)
""")
    assert result.returncode == 0, result.stderr
