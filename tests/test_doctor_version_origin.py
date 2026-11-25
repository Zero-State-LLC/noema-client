from __future__ import annotations

from pathlib import Path
from typing import Any

from noema_client.client import NoemaClient
from noema_client.config import StoredCredential


def test_doctor_reports_worker_version_and_origin_match(tmp_path: Path) -> None:
    def fake_http(method: str, url: str, body: Any, headers: Any) -> dict[str, Any]:
        if url.endswith("/health"):
            return {"_http_status": 200, "ok": True}
        if url.endswith("/version"):
            return {"_http_status": 200, "worker_version_id": "d8d0cbdf-a724-4bf0-8321-65bcf9be980a"}
        return {"_http_status": 200, "protocol": "noema.v1", "endpoints": {}}

    client = NoemaClient(
        server="https://noema.guru",
        config_home=tmp_path,
        http=fake_http,
    )
    client._credential = StoredCredential(
        access_token="tok-1",
        server="https://noema.guru",
        player_id="player-1",
    )
    report = client.doctor()
    assert report["reachability"] == "ok"
    assert report["worker_version"] == "d8d0cbdf-a724-4bf0-8321-65bcf9be980a"
    assert report["credential_origin_ok"] is True
    assert isinstance(report["client_version"], str) and len(report["client_version"]) > 0


def test_doctor_flags_credential_origin_mismatch(tmp_path: Path) -> None:
    def fake_http(method: str, url: str, body: Any, headers: Any) -> dict[str, Any]:
        if url.endswith("/health"):
            return {"_http_status": 200, "ok": True}
        if url.endswith("/version"):
            return {"_http_status": 200, "version": "v-test"}
        return {"_http_status": 200, "protocol": "noema.v1", "endpoints": {}}

    client = NoemaClient(
        server="https://noema.guru",
        config_home=tmp_path,
        http=fake_http,
    )
    client._credential = StoredCredential(
        access_token="tok-1",
        server="https://evil.example",
        player_id="player-1",
    )
    report = client.doctor()
    assert report["credential_origin_ok"] is False
    assert report["credential_server"] == "https://evil.example"
    assert report["worker_version"] == "v-test"
