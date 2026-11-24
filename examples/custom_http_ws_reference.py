#!/usr/bin/env python3
"""Minimal non-first-party HTTP reference client for PSR-1 adapter-style #2.

Uses only the Python standard library to demonstrate origin-bound, no-redirect
discovery against a NOEMA server (/version and /ready).
"""

from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        raise urllib.error.HTTPError(req.full_url, code, f"Refused redirect to {newurl}", headers, fp)


def fetch_json_no_redirect(origin: str, path: str, timeout: float = 10.0) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid server origin: {origin!r}")
    url = f"{parsed.scheme}://{parsed.netloc}{path}"
    opener = urllib.request.build_opener(_NoRedirectHandler)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "noema-psr1-ref/0.1"})
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def probe_server(origin: str = "https://noema.guru") -> dict[str, Any]:
    version = fetch_json_no_redirect(origin, "/version")
    ready = fetch_json_no_redirect(origin, "/ready")
    return {
        "origin": origin,
        "worker_version_id": version.get("worker_version_id"),
        "world_id": version.get("world_id"),
        "ready": ready.get("ready", ready.get("ok")),
    }


def emit_psr1_enrollment_receipt(
    *,
    operator_org: str,
    origin: str = "https://noema.guru",
    first_observe_ok: bool = True,
) -> dict[str, Any]:
    probe = probe_server(origin)
    return {
        "receipt_type": "psr1_tier3_enrollment",
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operator_tier": 3,
        "operator_org": operator_org,
        "server_origin": origin,
        "worker_version_id": probe["worker_version_id"],
        "world_id": probe["world_id"],
        "client_package": "noema-client==0.1.24",
        "enrollment_route": "device-code:/connect",
        "integration_style": "custom-http-ws",
        "first_observe_ok": first_observe_ok,
    }


if __name__ == "__main__":
    print(json.dumps(probe_server(), indent=2))
