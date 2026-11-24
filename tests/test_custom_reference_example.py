import http.server
import json
import threading
import urllib.error

import pytest

from examples.custom_http_ws_reference import (
    emit_psr1_enrollment_receipt,
    fetch_json_no_redirect,
    probe_server,
)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/version":
            body = json.dumps({"worker_version_id": "test-ver", "world_id": "world.test"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/ready":
            body = json.dumps({"ready": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://evil.example/")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def test_probe_server_and_refuse_redirect() -> None:
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f"http://127.0.0.1:{port}"
        res = probe_server(origin)
        assert res["worker_version_id"] == "test-ver"
        assert res["world_id"] == "world.test"
        assert res["ready"] is True

        receipt = emit_psr1_enrollment_receipt(operator_org="external-lab", origin=origin)
        assert receipt["receipt_type"] == "psr1_tier3_enrollment"
        assert receipt["operator_tier"] == 3
        assert receipt["client_package"] == "noema-client==0.1.24"
        assert receipt["enrollment_route"] == "device-code:/connect"
        assert receipt["integration_style"] == "custom-http-ws"
        assert receipt["worker_version_id"] == "test-ver"

        with pytest.raises(urllib.error.HTTPError):
            fetch_json_no_redirect(origin, "/redirect")
    finally:
        server.shutdown()
        server.server_close()
